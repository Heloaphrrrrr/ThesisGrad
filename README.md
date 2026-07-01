# AI-Assisted Data Cleaning for E-Commerce Data

Đây là đồ án xây dựng một hệ thống hỗ trợ phát hiện và làm sạch dữ liệu cho bài toán `customer shopping / e-commerce`.  
Hệ thống kết hợp:

- `rule-based validation` cho lỗi rõ ràng như thiếu dữ liệu, sai miền giá trị, sai định dạng.
- `Isolation Forest` để phát hiện bản ghi bất thường theo ngữ cảnh.
- `KNN / nearest neighbors` để gợi ý giá trị phù hợp cho các cột phân loại.
- `PostgreSQL` để lưu dữ liệu chuẩn hóa, log lỗi và kết quả làm sạch.

## 1. Mục tiêu

Mục tiêu của đồ án là thiết kế một pipeline có thể:

1. Đọc dữ liệu giao dịch.
2. Chuẩn hóa tên cột và kiểu dữ liệu.
3. Tách dữ liệu thành các bảng quan hệ hợp lý.
4. Phát hiện lỗi dữ liệu bằng cả luật và AI.
5. Sinh báo cáo lỗi và gợi ý sửa.
6. Ghi kết quả vào PostgreSQL để dễ kiểm tra và trình bày.

## 2. Dataset

File nguồn:

```text
data/customer_shopping_data.xlsx
```

Các cột gốc:

```text
INVOICE_NO
CUSTOM_ID
GENDER
AGE
CATEGORY
QUANTITY
PRICE
PAYMENT_METHOD
INVOICE_DATE
SHOPPING_MALL
```

Cột sau khi chuẩn hóa:

```text
invoice_no
customer_id
gender
age
category
quantity
price
payment_method
invoice_date
shopping_mall
```

## 3. Thiết kế dữ liệu

Đồ án chuẩn hóa dữ liệu thành 4 bảng chính:

- `customers`
- `products`
- `shopping_malls`
- `transactions`

Ý nghĩa:

- `customers`: lưu thông tin khách hàng.
- `products`: danh mục sản phẩm, trong phạm vi đồ án đại diện theo `category`.
- `shopping_malls`: thông tin trung tâm mua sắm.
- `transactions`: bảng fact trung tâm, liên kết với 3 bảng còn lại.

Khóa chính và khóa ngoại:

- `transactions.invoice_no` là khóa chính.
- `transactions.customer_id` tham chiếu `customers.customer_id`.
- `transactions.product_id` tham chiếu `products.product_id`.
- `transactions.mall_id` tham chiếu `shopping_malls.mall_id`.

## 4. Feature engineering

Để phục vụ phát hiện bất thường và gợi ý sửa, hệ thống sinh thêm các feature:

```text
unit_price
age_group
invoice_year
invoice_month
invoice_day
day_of_week
is_weekend
base_unit_price_by_category
price_deviation_from_category
mall_popularity_score
price_band
quantity_band
```

Các feature này giúp hệ thống hiểu được ngữ cảnh giao dịch, ví dụ:

- `unit_price = price / quantity`
- `price_deviation_from_category`: độ lệch giá so với mức điển hình của cùng category
- `mall_popularity_score`: mức độ phổ biến của trung tâm mua sắm

## 5. Kiến trúc xử lý

Pipeline chính:

```text
Raw data / PostgreSQL
    -> Normalize columns
    -> Prepare derived features
    -> Rule-based validation
    -> Clean reference set
    -> Isolation Forest
    -> Feature contribution analysis
    -> KNN recommendation
    -> Issue report / fix recommendation
    -> PostgreSQL output tables
```

Hệ thống đi theo hướng hybrid:

- Lỗi rõ ràng thì xử lý bằng rule.
- Lỗi bất thường theo ngữ cảnh thì dùng AI/ML.
- Lỗi numeric bất thường được báo cáo để review thủ công, không sửa bừa.

## 6. Các bảng phục vụ data cleaning

Schema còn có các bảng hỗ trợ:

- `staging_customer_shopping_raw`
- `cleaning_runs`
- `detected_issues`
- `fix_recommendations`
- `cleaning_actions`
- `dataset_profile`
- `fixed_transactions`

Mục đích:

- lưu dữ liệu thô trước khi chuẩn hóa
- lưu lỗi phát hiện được
- lưu gợi ý sửa
- lưu thống kê dữ liệu
- lưu dữ liệu sau khi sửa

## 7. Công nghệ sử dụng

- Python
- Pandas
- scikit-learn
- PostgreSQL
- SQLAlchemy

## 8. Cách chạy

### Chạy từ CSV

```bash
python -m app.cli \
  --source csv \
  --input data/customer_shopping_data.csv \
  --config configs/ecommerce_config.yaml \
  --apply-fixes \
  --profile-runtime
```

### Chạy từ PostgreSQL

```bash
python -m app.cli \
  --source postgres \
  --connection-uri postgresql://user:password@localhost:5432/dbname \
  --config configs/ecommerce_config.yaml \
  --apply-fixes \
  --profile-runtime
```

## 9. Kết quả đã kiểm chứng

Đã kiểm tra thành công:

- sample CSV 1.000 dòng
- full CSV 99.457 dòng
- ghi output vào các bảng:
  - `detected_issues`
  - `fix_recommendations`
  - `dataset_profile`
  - `fixed_transactions`
  - `final_report`

Benchmark full CSV sau tối ưu:

- `run_pipeline`: khoảng `485.83s`
- tổng thời gian: khoảng `492s`

Kết luận từ benchmark:

- I/O đã ổn.
- Bottleneck chính nằm ở phần `run_pipeline`, tức phần detect / recommend / explain.

## 10. Các file quan trọng

- `app/cli.py`: entrypoint chạy pipeline.
- `app/services/pipeline_service.py`: luồng phát hiện lỗi và gợi ý sửa.
- `app/detectors/anomaly_detector.py`: phát hiện anomaly.
- `app/detectors/feature_contribution.py`: xác định cột nghi ngờ.
- `app/recommenders/*.py`: sinh gợi ý sửa.
- `scripts/import_ecommerce_data.py`: chuẩn hóa và tách dữ liệu e-commerce.
- `sql/postgresql_schema.sql`: schema PostgreSQL chính.
- `configs/ecommerce_config.yaml`: config cho pipeline e-commerce.
