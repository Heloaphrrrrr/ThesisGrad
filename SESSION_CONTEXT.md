# Session Context

## Mục tiêu hiện tại

Đồ án đang được chuyển sang hướng **e-commerce / customer shopping** để phục vụ:

- thiết kế cơ sở dữ liệu PostgreSQL theo mô hình chuẩn hóa
- áp dụng pipeline **AI-assisted data cleaning**
- giữ được flow rõ ràng cho báo cáo và triển khai

Flow đã thống nhất:

```text
1. Đọc dataset
2. Chuẩn hóa tên cột
3. Xác định kiểu dữ liệu từng cột
4. Xác định khóa chính / khóa ngoại
5. Tách bảng theo mức hợp lý
6. Thiết kế schema PostgreSQL
7. Viết SQL CREATE TABLE
8. Viết script import dữ liệu
9. Thiết kế thêm các bảng phục vụ data cleaning
```

## Dataset đang dùng

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

Tên cột chuẩn hóa:

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

## Thiết kế e-commerce đã chốt

### 4 bảng nghiệp vụ chính

- `customers`
- `products`
- `shopping_malls`
- `transactions`

### Ý nghĩa

- `customers`: lưu thông tin khách hàng
- `products`: dimension sản phẩm, hiện tại đại diện theo `category`
- `shopping_malls`: dimension địa điểm mua sắm
- `transactions`: bảng fact giao dịch trung tâm

### Khóa

- `transactions.invoice_no` là khóa chính
- `transactions.customer_id` tham chiếu `customers.customer_id`
- `transactions.product_id` tham chiếu `products.product_id`
- `transactions.mall_id` tham chiếu `shopping_malls.mall_id`

## Feature engineering đã thống nhất

Các feature phục vụ AI/data cleaning:

- `unit_price`
- `age_group`
- `invoice_year`
- `invoice_month`
- `invoice_day`
- `day_of_week`
- `is_weekend`
- `base_unit_price_by_category`
- `price_deviation_from_category`
- `mall_popularity_score`
- `price_band`
- `quantity_band`

## File đã sửa / thêm

### Tài liệu

- `README.md`
  - đã cập nhật toàn bộ phần dataset theo hướng e-commerce
  - đã mô tả flow 9 bước
  - đã mô tả schema PostgreSQL
  - đã mô tả script import
  - đã mô tả cách chạy pipeline với PostgreSQL

### Schema và import

- `sql/postgresql_schema.sql`
  - chứa 4 bảng chính
  - có thêm bảng staging và data cleaning

- `scripts/import_ecommerce_data.py`
  - đọc file Excel
  - chuẩn hóa cột
  - sinh feature
  - tách dữ liệu thành 4 bảng
  - export CSV trung gian

### Pipeline

- `app/config.py`
  - thêm `source_query`

- `app/app_settings.py`
  - load `source_query` từ YAML

- `app/data_access/postgresql_source.py`
  - hỗ trợ đọc từ query join thay vì chỉ `SELECT * FROM table`

- `app/utils.py`
  - thêm `add_ecommerce_derived_features()`
  - thêm `prepare_input_dataframe()`

- `app/cli.py`
  - thêm `--source postgres`
  - thêm `--connection-uri`
  - giữ tương thích với `--source csv`

### Config mới

- `configs/ecommerce_config.yaml`
  - chứa `source_query` join từ:
    - `transactions`
    - `customers`
    - `products`
    - `shopping_malls`
  - chứa rules cho pipeline e-commerce

## Các bảng data cleaning đã có trong schema

- `staging_customer_shopping_raw`
- `cleaning_runs`
- `detected_issues`
- `fix_recommendations`
- `cleaning_actions`
- `dataset_profile`
- `fixed_transactions`

## Cách chạy pipeline sau này

### Chạy từ PostgreSQL

```bash
python -m app.cli \
  --source postgres \
  --connection-uri postgresql://user:password@localhost:5432/dbname \
  --config configs/ecommerce_config.yaml \
  --report
```

### Chạy từ CSV

```bash
python -m app.cli \
  --source csv \
  --input path/to/file.csv \
  --config configs/ecommerce_config.yaml \
  --report
```

Lưu ý:

- config e-commerce phù hợp nhất khi dataframe đầu vào có các cột đã chuẩn hóa theo thiết kế hiện tại
- nếu chạy từ CSV raw thì nên đi qua script import hoặc bước chuẩn hóa trước

## Tình trạng kiểm tra

Đã kiểm tra:

- cú pháp Python của các file mới/sửa: `syntax_ok`
- logic cấu hình và wiring CLI/PostgreSQL đã nối xong

Chưa kiểm tra end-to-end:

- chưa chạy thực tế với PostgreSQL thật
- chưa test import thật vào database
- chưa test output `detected_issues`, `recommendations`, `dataset_profile` trên schema mới

## Việc nên làm ở buổi chiều

Ưu tiên đề xuất:

1. Tạo file SQL hoặc script để load CSV trung gian vào PostgreSQL
2. Chạy import thật từ `customer_shopping_data.xlsx`
3. Chạy pipeline trên PostgreSQL bằng `configs/ecommerce_config.yaml`
4. Kiểm tra output:
   - `detected_issues`
   - `recommendations`
   - `dataset_profile`
   - `fixed_transactions`
5. Nếu cần, chỉnh tiếp rule hoặc feature cho anomaly detection

## Ghi chú quan trọng

- Repo hiện vẫn còn dấu vết logic cũ theo hướng bank dataset, nhưng pipeline đã được mở rộng để hỗ trợ e-commerce
- `products` hiện là category dimension, chưa phải SKU-level product
- Đây là quyết định phù hợp với phạm vi đồ án hiện tại

## Cập nhật buổi tối 2026-06-29

### Việc đã làm hôm nay

- Đã xác nhận thông tin PostgreSQL thực tế:
  - host: `localhost`
  - port: `5432`
  - username: `postgres`
  - database: `doantn`

- Đã kiểm tra kết nối PostgreSQL thành công với database thật.

- Đã kiểm tra dataset nguồn:
  - file: `data/customer_shopping_data.xlsx`
  - đọc được bằng Python/pandas

- Đã xác định lỗi quan trọng trong flow cũ:
  1. `invoice_date` bị parse sai do dùng `dayfirst=False`
  2. `PostgresDataSource.write()` dùng `if_exists="replace"` làm vỡ schema/FK
  3. `dataset_profile` lỗi ghi PostgreSQL do `numpy.int64 / numpy.float64 / numpy.bool_`
  4. lệch tên bảng output giữa schema và code:
     - `recommendations` vs `fix_recommendations`
     - `fixed_data` vs `fixed_transactions`
  5. DB thật đã từng bị chạy pipeline cũ nên một số bảng output bị trôi schema

### Các file đã sửa hôm nay

- `scripts/import_ecommerce_data.py`
- `app/utils.py`
- `app/data_access/postgresql_source.py`
- `app/cli.py`
- `sql/postgresql_schema.sql`
- `sql/littlemigration.sql`
- `docs/windows_postgres_notes.md`

### Nội dung patch chính

- Tạo helper parse ngày e-commerce thống nhất:
  - `parse_ecommerce_invoice_date(..., dayfirst=True)`

- Sửa import script để:
  - parse `invoice_date` đúng với dataset hiện tại
  - giữ `invoice_date_raw` để debug
  - raise lỗi rõ ràng nếu còn date parse fail

- Sửa PostgreSQL write layer để:
  - không `replace` các bảng schema cố định
  - clear dữ liệu rồi `append`
  - sanitize toàn bộ numpy scalar trước khi ghi
  - map đúng tên bảng output
  - ghi đúng shape cho:
    - `detected_issues`
    - `fix_recommendations`
    - `dataset_profile`
    - `fixed_transactions`

- Sửa `app/cli.py` để ghi đúng bảng:
  - `fix_recommendations`
  - `fixed_transactions`

- Sửa schema `detected_issues.source_method` từ `VARCHAR(32)` lên `VARCHAR(64)`
  vì giá trị thực tế của anomaly method dài hơn 32 ký tự.

### Các file tài liệu đã tạo hôm nay

- `docs/end_to_end_manual_run.md`
  - hướng dẫn chạy manual end-to-end

- `describe.md`
  - mô tả ý tưởng đồ án, flow, công nghệ, hướng tối ưu sau này

- `explain.md`
  - giải thích vai trò các bảng trong database

- `erd_text.md`
  - mô tả ERD dạng text để đưa vào báo cáo

### Trạng thái database hiện tại

Đã kiểm tra database `doantn` hiện có 12 bảng:

- `cleaning_actions`
- `cleaning_runs`
- `customers`
- `dataset_profile`
- `detected_issues`
- `final_report`
- `fix_recommendations`
- `fixed_transactions`
- `products`
- `shopping_malls`
- `staging_customer_shopping_raw`
- `transactions`

Số dòng tại thời điểm kiểm tra cuối:

- `customers`: `99457`
- `products`: `8`
- `shopping_malls`: `11`
- `transactions`: `99457`
- `staging_customer_shopping_raw`: `99457`
- `detected_issues`: có dữ liệu sample test
- `fix_recommendations`: có dữ liệu sample test
- `dataset_profile`: có dữ liệu sample test
- `fixed_transactions`: `99457`

Lưu ý:

- Kết quả `detected_issues`, `fix_recommendations`, `dataset_profile` hiện là từ sample run `LIMIT 1000`
  dùng để xác nhận luồng ghi PostgreSQL sau patch.

- Full pipeline trên toàn bộ gần 100k dòng vẫn có thể chạy rất lâu và đã bị timeout trong môi trường làm việc hôm nay.
  Nghĩa là phần lỗi schema/ghi DB đã được xử lý, nhưng phần performance/full run ngày mai vẫn cần xử lý thủ công và theo dõi thêm.

### Điều đã xác nhận chạy được

- `transform_dataset(...)` chạy đúng:
  - `customers = 99457`
  - `products = 8`
  - `shopping_malls = 11`
  - `transactions = 99457`

- `compileall` cho `app` và `scripts` chạy được

- Sample pipeline đọc từ PostgreSQL với `LIMIT 1000` chạy được và ghi đúng vào các bảng:
  - `detected_issues`
  - `fix_recommendations`
  - `dataset_profile`
  - `fixed_transactions`
  - `final_report`

- Không còn tạo bảng rác:
  - `recommendations`
  - `fixed_data`

## Ngày mai cần làm gì

### Mục tiêu buổi sáng

Mục tiêu sáng mai là chạy manual end-to-end theo tài liệu đã chuẩn bị, kiểm tra output thật và chốt phần có thể đưa vào báo cáo.

### Trình tự nên làm

1. Đọc lại file:
   - `SESSION_CONTEXT.md`
   - `docs/end_to_end_manual_run.md`

2. Kiểm tra DB hiện tại:
   - nếu cần sạch hoàn toàn thì cân nhắc tạo lại DB hoặc xóa dữ liệu cũ trước khi chạy full
   - nếu giữ DB hiện tại thì ít nhất nên chạy lại:
     - `sql/postgresql_schema.sql`
     - `sql/littlemigration.sql`

3. Chạy lại import:
   - từ `data/customer_shopping_data.xlsx`
   - nạp lại `staging_customer_shopping_raw`, `customers`, `products`, `shopping_malls`, `transactions`

4. Kiểm tra số lượng import:
   - `customers = 99457`
   - `products = 8`
   - `shopping_malls = 11`
   - `transactions = 99457`

5. Chạy sample pipeline trước:
   - `LIMIT 1000`
   - để xác nhận flow vẫn ổn trong buổi sáng mai

6. Sau đó mới chạy full pipeline:
   - `python -m app.cli --source postgres ... --apply-fixes`

7. Kiểm tra output sau full run:
   - `detected_issues`
   - `fix_recommendations`
   - `dataset_profile`
   - `fixed_transactions`
   - `final_report`

8. Nếu full run tiếp tục quá lâu:
   - không quay lại sửa các lỗi cũ đã patch rồi
   - tập trung đánh giá đây là vấn đề performance/model runtime
   - có thể chốt báo cáo dựa trên sample run + import full nếu cần

### Nếu sáng mai chỉ muốn tiếp tục nhanh

Chỉ cần bắt đầu bằng câu:

```text
Đọc SESSION_CONTEXT.md và tiếp tục từ bước chạy manual end-to-end
```

hoặc:

```text
Bắt đầu step 1 theo end_to_end_manual_run.md
```

là có thể tiếp tục ngay.
## Cap nhat ngay 2026-06-30

### Viec da xac nhan hom nay

- Da ra soat lai workspace sau khi khong `resume` duoc goal Codex cu.
- Da xac nhan tien trinh khong mat, vi artefact chinh van con trong repo:
  - `SESSION_CONTEXT.md`
  - `docs/end_to_end_manual_run.md`
  - `docs/run_import_postgres.py`
  - `docs/run_pipeline_full.py`
  - `docs/explainDTB.md`
- Da xac nhan sample dirty input con ton tai:
  - `outputs/e2e_dirty/ecommerce_dirty_sample.csv`
  - `outputs/e2e_dirty/ecommerce_dirty_labels.csv`

### End-to-end da chay hom nay

Da chay thanh cong pipeline end-to-end tren sample CSV bang lenh:

```powershell
python -m app.cli --source csv --input outputs/e2e_dirty/ecommerce_dirty_sample.csv --config configs/ecommerce_config.yaml --output outputs/e2e_dirty/run_20260630_9h15 --apply-fixes --report
```

### Output sinh ra

Thu muc output:

```text
outputs/e2e_dirty/run_20260630_9h15
```

Các file da sinh ra:

- `dataset_profile.csv`
- `detected_issues.csv`
- `final_report.csv`
- `fixed_transactions.csv`
- `fix_recommendations.csv`

### Ket qua chinh cua lan chay sample

- `total_issues = 417`
- `issue_type_anomaly = 395`
- `issue_type_invalid = 15`
- `issue_type_missing = 7`
- `fixable_rate = 0.9976`

Luu y:

- Sample dirty khong chi chua 14 loi co trong labels, ma con phat sinh them nhieu anomaly thong ke tren toan bo sample.
- Vi vay tong so issue pipeline phat hien lon hon so dong trong file labels la binh thuong.

### Phat hien quan trong ve file labels

Da kiem tra va xac nhan:

- Dong `I127711` co trong `outputs/e2e_dirty/ecommerce_dirty_sample.csv`
- Nhung khong co trong `outputs/e2e_dirty/ecommerce_dirty_labels.csv`

Dong `I127711` hien la dirty row duoc them sau buoc sinh labels hoac duoc chen tay, nen labels hien tai khong con la ground truth hoan chinh cho toan bo sample.

Pipeline da phat hien nhieu loi cho `I127711`, gom:

- `quantity`: missing
- `price`: missing
- `invoice_date`: missing
- `gender`: invalid
- `category`: invalid
- `payment_method`: invalid
- `shopping_mall`: invalid

### Y nghia hien tai cua file labels

`outputs/e2e_dirty/ecommerce_dirty_labels.csv` hien chi nen duoc xem la:

- ground truth cho bo loi dirty goc duoc seed tu dong
- khong phai ground truth day du cho toan bo `ecommerce_dirty_sample.csv`

### Viec nen lam ngay mai

Uu tien test tiep:

1. Quyet dinh cach dung labels:
   - hoac cap nhat labels de them `I127711`
   - hoac giu nguyen labels cu va xem `I127711` la test thu cong ngoai bo ground truth
2. Neu muon danh gia detector/recommender:
   - so sanh `detected_issues.csv` voi `ecommerce_dirty_labels.csv`
   - tinh precision / recall tren bo 14 loi goc
3. Sau do co the test tiep flow PostgreSQL full end-to-end neu can

### Cau nhac de mo lai nhanh ngay mai

Chi can bat dau bang mot trong cac cau sau:

```text
Doc SESSION_CONTEXT.md va tiep tuc test bo sample dirty
```

hoac:

```text
Kiem tra labels cu va them ground truth cho I127711
```
