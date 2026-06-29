# Describe Project Flow

## 1. Ý tưởng của đồ án

Đồ án này xây dựng một hệ thống **AI-assisted data cleaning** cho dữ liệu e-commerce.

Thay vì chỉ lưu dữ liệu và kiểm tra thủ công, hệ thống hướng tới việc:

- chuẩn hóa dữ liệu giao dịch mua sắm
- thiết kế cơ sở dữ liệu PostgreSQL theo hướng tách bảng hợp lý
- phát hiện dữ liệu bất thường, thiếu, sai định dạng hoặc không hợp lệ
- đưa ra gợi ý sửa lỗi
- hỗ trợ tạo ra một phiên bản dữ liệu đã được làm sạch để phục vụ phân tích hoặc mô hình AI

Ý tưởng cốt lõi là kết hợp:

- **database design**
- **data preprocessing**
- **machine learning cho anomaly detection**
- **pipeline tự động hóa**

để tạo thành một flow xử lý dữ liệu rõ ràng, có thể mở rộng và phù hợp với phạm vi đồ án tốt nghiệp.

## 2. Flow tổng thể của đồ án

Flow hiện tại có thể hiểu theo các bước sau:

1. Nhận dữ liệu đầu vào từ file Excel dataset e-commerce.
2. Chuẩn hóa tên cột và kiểu dữ liệu.
3. Parse và làm giàu dữ liệu, ví dụ:
   - `unit_price`
   - `age_group`
   - `invoice_year`
   - `invoice_month`
   - `invoice_day`
   - `day_of_week`
   - `is_weekend`
   - `quantity_band`
4. Thiết kế lại dữ liệu theo mô hình quan hệ và tách thành các bảng:
   - `customers`
   - `products`
   - `shopping_malls`
   - `transactions`
5. Import dữ liệu đã chuẩn hóa vào PostgreSQL.
6. Đọc dữ liệu từ PostgreSQL bằng `source_query` join các bảng nghiệp vụ.
7. Chạy pipeline phát hiện lỗi dữ liệu:
   - missing values
   - invalid values
   - cross-field inconsistency
   - anomaly detection
8. Sinh báo cáo và ghi kết quả ra các bảng output:
   - `detected_issues`
   - `fix_recommendations`
   - `dataset_profile`
   - `fixed_transactions`
   - `final_report`
9. Dùng các output này để phục vụ:
   - đánh giá chất lượng dữ liệu
   - giải thích các lỗi phát hiện được
   - hỗ trợ bước phân tích hoặc huấn luyện mô hình sau này

## 3. Ý nghĩa thiết kế e-commerce

Dataset gốc ban đầu chỉ là một bảng phẳng, nhưng đồ án chuyển nó sang tư duy gần với hệ thống thực tế hơn:

- `customers` lưu thông tin khách hàng
- `products` đóng vai trò dimension sản phẩm, hiện đang đại diện theo `category`
- `shopping_malls` lưu dimension địa điểm mua sắm
- `transactions` là bảng fact trung tâm

Cách làm này có lợi ở ba điểm:

- dữ liệu rõ ràng hơn về mặt mô hình
- dễ mở rộng khi thêm nghiệp vụ mới
- thuận lợi hơn cho việc truy vấn, làm sạch dữ liệu và trình bày báo cáo

## 4. Công nghệ đang sử dụng

### Ngôn ngữ và runtime

- `Python 3`

### Xử lý dữ liệu

- `pandas`
- `numpy`

### Machine learning / phát hiện bất thường

- `scikit-learn`

Hiện tại pipeline đang dùng hướng anomaly detection dựa trên mô hình như `Isolation Forest` kết hợp với feature analysis để xác định cột nghi ngờ.

### Database

- `PostgreSQL`
- `SQLAlchemy`
- `psycopg2-binary`

### Cấu hình và vận hành

- `YAML` để cấu hình pipeline
- `CLI` Python để chạy pipeline

### Dữ liệu đầu vào

- `Excel (.xlsx)`
- có thể mở rộng sang `CSV`

## 5. Phần AI / Data Cleaning trong đồ án

Điểm đáng chú ý của đồ án không chỉ là import dữ liệu vào database, mà là xây dựng một pipeline có khả năng:

- phát hiện dữ liệu bị thiếu
- phát hiện giá trị nằm ngoài miền hợp lệ
- phát hiện bất thường theo phân phối dữ liệu
- gợi ý cách sửa
- sinh bản dữ liệu đã fix ở mức tự động có kiểm soát

Điều này giúp đồ án đi xa hơn một bài ETL thông thường, và tiến gần hơn đến một hệ thống hỗ trợ chất lượng dữ liệu bằng AI.

## 6. Chuẩn bị tinh thần để thêm thuật toán tối ưu

Phần hiện tại mới là nền tảng tốt để phát triển tiếp. Nếu muốn đồ án mạnh hơn, cần chuẩn bị tinh thần là sẽ còn bổ sung thêm thuật toán và chiến lược tối ưu.

Các hướng có thể phát triển:

- tối ưu tốc độ xử lý với dataset lớn
- cải thiện chất lượng anomaly detection
- thêm thuật toán recommendation tốt hơn cho việc sửa lỗi
- thêm rule engine mạnh hơn cho kiểm tra nghiệp vụ
- thêm scoring để đánh giá mức độ nghiêm trọng của lỗi chính xác hơn
- thêm logging, tracking và versioning cho từng lần cleaning

Một số hướng thuật toán có thể cân nhắc sau này:

- `Local Outlier Factor (LOF)`
- `One-Class SVM`
- clustering-based anomaly detection
- statistical profiling nâng cao
- rule-based hybrid với ML
- similarity matching / nearest-neighbor recommendation

Ngoài thuật toán, còn có thể tối ưu ở mức hệ thống:

- batch processing
- incremental processing
- tối ưu query PostgreSQL
- index phù hợp cho các bảng output
- giảm việc xử lý toàn bộ dataset mỗi lần chạy

Nói ngắn gọn: phần hiện tại đã là một bộ khung khá ổn, nhưng để đồ án thực sự mạnh và thuyết phục hơn, cần sẵn sàng mở rộng thêm thuật toán và tối ưu hiệu năng trong các bước tiếp theo.

## 7. Tóm tắt định hướng

Đồ án này có thể được mô tả ngắn gọn như sau:

> Xây dựng một hệ thống hỗ trợ làm sạch dữ liệu e-commerce bằng Python, PostgreSQL và machine learning, với mục tiêu chuẩn hóa dữ liệu, phát hiện lỗi, gợi ý sửa lỗi và tạo đầu ra phục vụ phân tích dữ liệu thông minh hơn.

Đây là hướng phù hợp vì vừa có:

- thiết kế cơ sở dữ liệu
- xử lý dữ liệu
- lập trình pipeline
- ứng dụng AI/ML
- khả năng mở rộng nghiên cứu tiếp
