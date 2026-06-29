# Explain Database Tables

Tài liệu này giải thích vai trò của các bảng hiện có trong database `doantn`, để dễ dùng cho báo cáo hoặc thuyết trình.

## 1. Nhìn tổng quát

Database hiện tại có thể chia thành 4 nhóm chính:

1. Bảng dữ liệu nghiệp vụ chính
2. Bảng staging / dữ liệu đầu vào thô
3. Bảng phục vụ data cleaning
4. Bảng output / kết quả sau khi chạy pipeline

Mục tiêu của cách chia này là:

- dữ liệu gốc và dữ liệu xử lý được tách rõ
- dễ mô tả flow của hệ thống
- thuận tiện khi trình bày phần database design trong đồ án

## 2. Nhóm bảng dữ liệu nghiệp vụ chính

Đây là các bảng mô tả bài toán e-commerce sau khi dữ liệu đã được chuẩn hóa và tách theo mô hình quan hệ.

### 2.1. `customers`

Vai trò:
- lưu thông tin khách hàng

Các cột chính:
- `customer_id`
- `gender`
- `age`
- `age_group`
- `customer_segment`

Ý nghĩa:
- mỗi khách hàng xuất hiện một lần
- bảng này đóng vai trò dimension khách hàng
- các cột như `age_group` và `customer_segment` giúp tăng giá trị phân tích dữ liệu

### 2.2. `products`

Vai trò:
- lưu dimension sản phẩm

Các cột chính:
- `product_id`
- `category`
- `base_unit_price`
- `price_band`

Ý nghĩa:
- trong phạm vi đồ án hiện tại, `products` chưa đi đến mức SKU thật
- mỗi `product` hiện đại diện cho một `category`
- bảng này được dùng để chuẩn hóa thông tin sản phẩm và hỗ trợ feature engineering

### 2.3. `shopping_malls`

Vai trò:
- lưu dimension địa điểm mua sắm

Các cột chính:
- `mall_id`
- `shopping_mall`
- `mall_tier`
- `mall_popularity_score`

Ý nghĩa:
- chuẩn hóa tên trung tâm mua sắm
- phục vụ phân tích theo địa điểm
- có thêm thông tin suy diễn như độ phổ biến hoặc nhóm quy mô mall

### 2.4. `transactions`

Vai trò:
- là bảng giao dịch trung tâm

Các cột chính:
- `invoice_no`
- `customer_id`
- `product_id`
- `mall_id`
- `quantity`
- `price`
- `payment_method`
- `invoice_date`
- `unit_price`
- `invoice_year`
- `invoice_month`
- `invoice_day`
- `day_of_week`
- `is_weekend`
- `quantity_band`
- `price_deviation_from_category`

Ý nghĩa:
- đây là bảng fact quan trọng nhất
- mỗi dòng là một giao dịch mua sắm
- bảng này liên kết với:
  - `customers`
  - `products`
  - `shopping_malls`
- ngoài dữ liệu gốc còn có thêm nhiều feature dẫn xuất để phục vụ cleaning và phân tích

## 3. Nhóm bảng staging / dữ liệu đầu vào thô

### 3.1. `staging_customer_shopping_raw`

Vai trò:
- lưu dữ liệu raw trước khi chuẩn hóa hoàn toàn

Các cột chính:
- `invoice_no`
- `customer_id`
- `gender`
- `age`
- `category`
- `quantity`
- `price`
- `payment_method`
- `invoice_date`
- `shopping_mall`
- `source_file`
- `imported_at`

Ý nghĩa:
- đây là điểm lưu dấu dữ liệu gốc được import từ file nguồn
- giúp truy vết nếu có lỗi khi transform hoặc import
- hỗ trợ đối chiếu giữa dữ liệu thô và dữ liệu đã chuẩn hóa trong các bảng nghiệp vụ

## 4. Nhóm bảng phục vụ data cleaning

Đây là phần quan trọng làm nên bản chất AI-assisted data cleaning của đồ án.

### 4.1. `cleaning_runs`

Vai trò:
- ghi nhận từng lần chạy cleaning pipeline

Các cột chính:
- `run_id`
- `run_mode`
- `source_name`
- `started_at`
- `finished_at`
- `status`
- `notes`

Ý nghĩa:
- giống như lịch sử chạy hệ thống
- nếu mở rộng tiếp, bảng này rất hữu ích để audit và so sánh các lần cleaning

### 4.2. `detected_issues`

Vai trò:
- lưu các lỗi hoặc điểm bất thường mà pipeline phát hiện

Các cột chính:
- `issue_id`
- `row_id`
- `table_name`
- `column_name`
- `issue_type`
- `current_value`
- `suggested_value`
- `confidence`
- `severity`
- `severity_score`
- `reason`
- `source_method`
- `recommended_action`
- `can_auto_fix`
- `created_at`

Ý nghĩa:
- đây là bảng quan trọng nhất của phần data cleaning
- nó cho biết:
  - lỗi nằm ở dòng nào
  - cột nào có vấn đề
  - loại lỗi là gì
  - mức độ nghiêm trọng ra sao
  - hệ thống đề xuất sửa thế nào

Các loại lỗi thường gặp:
- missing
- invalid
- anomaly

### 4.3. `fix_recommendations`

Vai trò:
- lưu các gợi ý sửa lỗi được sinh ra từ pipeline

Các cột chính:
- `recommendation_id`
- `issue_id`
- `row_id`
- `table_name`
- `column_name`
- `suggested_value`
- `confidence`
- `approved`
- `applied_at`

Ý nghĩa:
- nếu `detected_issues` trả lời câu hỏi “lỗi ở đâu”
- thì `fix_recommendations` trả lời câu hỏi “nên sửa như thế nào”

### 4.4. `cleaning_actions`

Vai trò:
- lưu lịch sử hành động sửa lỗi

Các cột chính:
- `action_id`
- `issue_id`
- `invoice_no`
- `table_name`
- `column_name`
- `old_value`
- `new_value`
- `action_type`
- `action_status`
- `action_by`
- `action_at`

Ý nghĩa:
- dùng để audit các hành động fix
- hiện tại bảng này chưa có dữ liệu, nhưng rất hợp lý nếu sau này mở rộng chế độ semi-auto hoặc manual review

## 5. Nhóm bảng output / kết quả sau pipeline

Đây là nhóm bảng thể hiện đầu ra có thể dùng để báo cáo, trình bày hoặc phân tích tiếp.

### 5.1. `dataset_profile`

Vai trò:
- mô tả chất lượng dữ liệu theo từng cột

Các cột chính:
- `table_name`
- `column_name`
- `missing_count`
- `missing_rate`
- `unique_count`
- `min_value`
- `max_value`
- `issue_count`
- `anomaly_count`
- `invalid_count`

Ý nghĩa:
- cho cái nhìn tổng hợp về chất lượng dataset
- rất phù hợp để đưa vào báo cáo hoặc dashboard

### 5.2. `fixed_transactions`

Vai trò:
- lưu phiên bản dữ liệu giao dịch sau khi áp dụng các fix đủ điều kiện

Các cột chính:
- gần giống bảng `transactions`
- có thêm `fixed_at`

Ý nghĩa:
- đây là đầu ra “đã làm sạch”
- có thể dùng thay cho `transactions` trong phân tích tiếp theo nếu muốn làm việc trên dữ liệu đã được chỉnh sửa

### 5.3. `final_report`

Vai trò:
- lưu báo cáo tóm tắt sau khi chạy pipeline

Các cột chính:
- `metric`
- `value`

Ý nghĩa:
- bảng này khá gọn
- thường chứa các chỉ số như:
  - tổng số lỗi
  - số lỗi theo loại
  - tỷ lệ fix được
  - các thống kê tổng hợp khác

## 6. Cách các bảng liên kết với nhau

Quan hệ nghiệp vụ chính:

- `transactions.customer_id` -> `customers.customer_id`
- `transactions.product_id` -> `products.product_id`
- `transactions.mall_id` -> `shopping_malls.mall_id`

Quan hệ trong phần data cleaning:

- `fix_recommendations.issue_id` -> `detected_issues.issue_id`
- `cleaning_actions.issue_id` -> `detected_issues.issue_id`

Điều này cho thấy đồ án không chỉ lưu dữ liệu giao dịch, mà còn lưu cả vòng đời của quá trình phát hiện lỗi và đề xuất sửa lỗi.

## 7. Tóm tắt vai trò từng nhóm

### Nhóm nghiệp vụ

- `customers`
- `products`
- `shopping_malls`
- `transactions`

Đây là phần mô hình dữ liệu e-commerce chính.

### Nhóm staging

- `staging_customer_shopping_raw`

Đây là nơi lưu dữ liệu gốc trước khi chuẩn hóa hoàn toàn.

### Nhóm cleaning

- `cleaning_runs`
- `detected_issues`
- `fix_recommendations`
- `cleaning_actions`

Đây là phần phục vụ cho quá trình phát hiện và quản lý lỗi dữ liệu.

### Nhóm output

- `dataset_profile`
- `fixed_transactions`
- `final_report`

Đây là phần đầu ra cuối cùng để đánh giá chất lượng dữ liệu và sử dụng dữ liệu đã làm sạch.

## 8. Kết luận

Thiết kế database hiện tại cho thấy đồ án đi theo hướng khá rõ ràng:

- tách dữ liệu nghiệp vụ khỏi dữ liệu raw
- có phần riêng cho data cleaning
- có phần output riêng cho báo cáo và dữ liệu đã sửa

Đây là một điểm mạnh khi trình bày đồ án, vì bạn có thể chứng minh rằng hệ thống không chỉ “đọc file và kiểm tra lỗi”, mà thực sự có:

- mô hình dữ liệu
- pipeline làm sạch
- cơ chế lưu kết quả
- khả năng mở rộng cho audit và tối ưu sau này
