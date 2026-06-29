# ERD Text Description

Tài liệu này mô tả sơ đồ quan hệ dữ liệu của đồ án dưới dạng text, để dễ đưa vào báo cáo khi chưa cần vẽ ERD bằng hình.

## 1. Ý tưởng ERD tổng quát

Hệ thống được chia thành 3 lớp dữ liệu chính:

1. Lớp dữ liệu nguồn và staging
2. Lớp dữ liệu nghiệp vụ e-commerce
3. Lớp dữ liệu phục vụ data cleaning và output

Luồng tổng quát:

```text
Excel source
   ->
staging_customer_shopping_raw
   ->
customers / products / shopping_malls / transactions
   ->
detected_issues / fix_recommendations / dataset_profile / fixed_transactions / final_report
```

## 2. Các thực thể chính

### 2.1. `customers`

Khóa chính:
- `customer_id`

Thuộc tính:
- `gender`
- `age`
- `age_group`
- `customer_segment`

Ý nghĩa:
- mỗi dòng là một khách hàng
- là bảng dimension khách hàng

### 2.2. `products`

Khóa chính:
- `product_id`

Thuộc tính:
- `category`
- `base_unit_price`
- `price_band`

Ý nghĩa:
- là bảng dimension sản phẩm
- trong phạm vi hiện tại, một `product` đại diện cho một `category`

### 2.3. `shopping_malls`

Khóa chính:
- `mall_id`

Thuộc tính:
- `shopping_mall`
- `mall_tier`
- `mall_popularity_score`

Ý nghĩa:
- là bảng dimension địa điểm mua sắm

### 2.4. `transactions`

Khóa chính:
- `invoice_no`

Khóa ngoại:
- `customer_id` -> `customers.customer_id`
- `product_id` -> `products.product_id`
- `mall_id` -> `shopping_malls.mall_id`

Thuộc tính:
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
- đây là bảng fact trung tâm
- mỗi dòng tương ứng một giao dịch mua sắm

## 3. Quan hệ giữa các bảng nghiệp vụ

### 3.1. `customers` và `transactions`

Quan hệ:

```text
customers (1) ----- (N) transactions
```

Giải thích:
- một khách hàng có thể phát sinh nhiều giao dịch
- mỗi giao dịch chỉ thuộc về một khách hàng

### 3.2. `products` và `transactions`

Quan hệ:

```text
products (1) ----- (N) transactions
```

Giải thích:
- một loại sản phẩm / category có thể xuất hiện trong nhiều giao dịch
- mỗi giao dịch gắn với một `product_id`

### 3.3. `shopping_malls` và `transactions`

Quan hệ:

```text
shopping_malls (1) ----- (N) transactions
```

Giải thích:
- một trung tâm mua sắm có thể có nhiều giao dịch
- mỗi giao dịch diễn ra tại một mall cụ thể

## 4. Bảng staging

### 4.1. `staging_customer_shopping_raw`

Khóa chính:
- `row_number`

Thuộc tính:
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

Vai trò trong ERD:
- không phải bảng nghiệp vụ chính
- là nơi lưu dữ liệu thô trước khi chuẩn hóa
- hỗ trợ trace nguồn dữ liệu

Quan hệ logic:

```text
staging_customer_shopping_raw
   -> chuẩn hóa / transform
   -> customers
   -> products
   -> shopping_malls
   -> transactions
```

## 5. Bảng phục vụ data cleaning

### 5.1. `cleaning_runs`

Khóa chính:
- `run_id`

Thuộc tính:
- `run_mode`
- `source_name`
- `started_at`
- `finished_at`
- `status`
- `notes`

Vai trò:
- lưu metadata của từng lần chạy cleaning pipeline

### 5.2. `detected_issues`

Khóa chính:
- `issue_id`

Khóa ngoại:
- `run_id` -> `cleaning_runs.run_id`

Thuộc tính:
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

Vai trò:
- lưu danh sách lỗi hoặc điểm bất thường được hệ thống phát hiện

Quan hệ:

```text
cleaning_runs (1) ----- (N) detected_issues
```

### 5.3. `fix_recommendations`

Khóa chính:
- `recommendation_id`

Khóa ngoại:
- `issue_id` -> `detected_issues.issue_id`

Thuộc tính:
- `row_id`
- `table_name`
- `column_name`
- `suggested_value`
- `confidence`
- `approved`
- `applied_at`

Vai trò:
- lưu gợi ý sửa lỗi tương ứng với từng issue

Quan hệ:

```text
detected_issues (1) ----- (N) fix_recommendations
```

Giải thích:
- một issue có thể có một hoặc nhiều gợi ý sửa
- hiện tại logic hệ thống chủ yếu sinh một hướng gợi ý chính

### 5.4. `cleaning_actions`

Khóa chính:
- `action_id`

Khóa ngoại:
- `issue_id` -> `detected_issues.issue_id`

Thuộc tính:
- `invoice_no`
- `table_name`
- `column_name`
- `old_value`
- `new_value`
- `action_type`
- `action_status`
- `action_by`
- `action_at`

Vai trò:
- lưu lịch sử hành động sửa lỗi

Quan hệ:

```text
detected_issues (1) ----- (N) cleaning_actions
```

## 6. Bảng output sau cleaning

### 6.1. `dataset_profile`

Khóa chính:
- `profile_id`

Khóa ngoại:
- `run_id` -> `cleaning_runs.run_id`

Thuộc tính:
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
- `profiled_at`

Vai trò:
- tổng hợp chất lượng dữ liệu theo cột

Quan hệ:

```text
cleaning_runs (1) ----- (N) dataset_profile
```

### 6.2. `fixed_transactions`

Khóa chính:
- `invoice_no`

Khóa ngoại:
- `invoice_no` -> `transactions.invoice_no`
- `customer_id` -> `customers.customer_id`
- `product_id` -> `products.product_id`
- `mall_id` -> `shopping_malls.mall_id`

Thuộc tính:
- gần giống `transactions`
- có thêm `fixed_at`

Vai trò:
- lưu phiên bản giao dịch sau khi hệ thống áp dụng các sửa lỗi đủ điều kiện

Quan hệ:

```text
transactions (1) ----- (1) fixed_transactions
```

Giải thích:
- mỗi giao dịch gốc có thể tương ứng với một phiên bản fixed
- đây là output cuối cùng để dùng trong phân tích hoặc mô hình phía sau

### 6.3. `final_report`

Khóa chính:
- không thiết kế PK rõ ràng theo nghĩa nghiệp vụ

Thuộc tính:
- `metric`
- `value`

Vai trò:
- lưu kết quả tổng hợp cuối cùng sau mỗi lần chạy
- dùng cho báo cáo nhanh hoặc dashboard tóm tắt

## 7. Mô tả ERD bằng text ngắn gọn

Có thể mô tả sơ đồ quan hệ chính như sau:

```text
customers (customer_id PK)
    1 ----- N
transactions (invoice_no PK, customer_id FK, product_id FK, mall_id FK)
    N ----- 1
products (product_id PK)

transactions
    N ----- 1
shopping_malls (mall_id PK)

transactions (invoice_no PK)
    1 ----- 1
fixed_transactions (invoice_no PK/FK)

cleaning_runs (run_id PK)
    1 ----- N
detected_issues (issue_id PK, run_id FK)

detected_issues
    1 ----- N
fix_recommendations (recommendation_id PK, issue_id FK)

detected_issues
    1 ----- N
cleaning_actions (action_id PK, issue_id FK)

cleaning_runs
    1 ----- N
dataset_profile (profile_id PK, run_id FK)
```

## 8. Cách trình bày phần này trong báo cáo

Nếu đưa vào báo cáo, có thể tóm tắt:

- `transactions` là fact table trung tâm
- `customers`, `products`, `shopping_malls` là các dimension table
- `staging_customer_shopping_raw` là bảng dữ liệu raw
- `detected_issues`, `fix_recommendations`, `cleaning_actions`, `dataset_profile` là các bảng hỗ trợ quá trình data cleaning
- `fixed_transactions` là dữ liệu đầu ra sau làm sạch

Đây là một điểm mạnh của đồ án vì hệ thống không chỉ dừng ở thiết kế database bán hàng, mà còn mở rộng sang quản lý chất lượng dữ liệu và lưu vết quá trình làm sạch.

## 9. Kết luận

ERD của đồ án thể hiện hai lớp giá trị:

1. Giá trị nghiệp vụ:
- mô hình hóa bài toán e-commerce theo hướng dữ liệu quan hệ

2. Giá trị nghiên cứu / kỹ thuật:
- tích hợp thêm lớp phát hiện lỗi, gợi ý sửa lỗi và đầu ra dữ liệu đã làm sạch

Nhờ đó, đồ án có thể được trình bày như một hệ thống hoàn chỉnh hơn một bài thiết kế database thông thường.
