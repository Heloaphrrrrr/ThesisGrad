# End-to-End Manual Run Guide

Tài liệu này tổng hợp các bước cần làm để chạy toàn bộ flow e-commerce / PostgreSQL theo trạng thái code hiện tại.

## 1. Thông tin môi trường

- Project root: `C:\Users\ACER\OneDrive\Desktop\DoAnTN`
- Database: `doantn`
- Host: `localhost`
- Port: `5432`
- Username: `postgres`
- Password: `Triweio_123`
- Connection URI:

```text
postgresql://postgres:Triweio_123@localhost:5432/doantn
```

## 2. Chuẩn bị terminal

Mở PowerShell tại thư mục project:

```powershell
cd C:\Users\ACER\OneDrive\Desktop\DoAnTN
```

Kiểm tra Python:

```powershell
python --version
```

Nếu dùng virtual environment riêng thì activate trước khi chạy các lệnh còn lại.

## 3. Cài dependencies nếu máy chưa có

```powershell
pip install -r requirements.txt
```

Nếu đã cài từ trước thì có thể bỏ qua.

## 4. Kiểm tra kết nối PostgreSQL

Nếu `psql` không có trong `PATH`, dùng trực tiếp:

```powershell
$env:PGPASSWORD='Triweio_123'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h localhost -p 5432 -U postgres -d doantn -c "SELECT current_database(), current_user;"
```

Kết quả mong muốn:

```text
doantn | postgres
```

## 5. Tạo schema chính

Chạy schema đầy đủ:

```powershell
$env:PGPASSWORD='Triweio_123'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h localhost -p 5432 -U postgres -d doantn -v ON_ERROR_STOP=1 -f 'sql\postgresql_schema.sql'
```

Lưu ý:
- Nếu database đang có sẵn bảng từ lần chạy cũ, lệnh trên có thể báo `relation already exists`.
- Nếu muốn làm sạch hoàn toàn trước khi tạo lại schema, nên tự chủ động drop database hoặc xóa các bảng cũ trước khi chạy lại.

## 6. Chạy little migration nếu schema output đã từng bị lệch

File này dùng để khôi phục đúng shape các bảng output PostgreSQL nếu trước đó pipeline cũ đã `replace` bảng và làm trôi schema.

Chạy bằng Python:

```powershell
@'
from pathlib import Path
from sqlalchemy import create_engine

sql_text = Path('sql/littlemigration.sql').read_text(encoding='utf-8')
engine = create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')
with engine.begin() as conn:
    raw = conn.connection
    with raw.cursor() as cur:
        cur.execute(sql_text)
print('migration_ok')
'@ | python -
```

Khi nào nên chạy:
- Khi trước đó đã chạy pipeline cũ và DB đang có các bảng như `recommendations`
- Khi bảng `detected_issues`, `dataset_profile`, `fix_recommendations` bị sai cột
- Khi muốn reset lại phần output tables về đúng schema patch mới

## 7. Kiểm tra file input

Dataset nguồn hiện tại:

```text
data/customer_shopping_data.xlsx
```

Kiểm tra file tồn tại:

```powershell
Get-ChildItem -LiteralPath 'data\customer_shopping_data.xlsx'
```

## 8. Chạy bước transform/import mức file

Script này đọc Excel, chuẩn hóa cột, parse `invoice_date` với `dayfirst=True`, sinh feature và tách thành 4 bảng logic.

Chạy:

```powershell
python scripts/import_ecommerce_data.py --input data/customer_shopping_data.xlsx --output-dir outputs/ecommerce_import
```

Kết quả:
- Sinh các file CSV trung gian trong `outputs/ecommerce_import`
- Đây là bước tốt để xác nhận data transform hoạt động trước khi import DB

Nếu script báo `ValueError` về `invoice_date`:
- Có nghĩa là vẫn còn giá trị ngày không parse được
- Script sẽ in sample các dòng lỗi để bạn kiểm tra

## 9. Import dữ liệu vào PostgreSQL

Hiện project chưa có một CLI import DB riêng hoàn chỉnh, nên cách thực tế là chạy Python inline để:
- đọc Excel
- transform đúng logic hiện tại
- nạp vào:
  - `staging_customer_shopping_raw`
  - `customers`
  - `products`
  - `shopping_malls`
  - `transactions`

Chạy:

```powershell
@'
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from scripts.import_ecommerce_data import (
    normalize_columns,
    transform_dataset,
)

input_path = Path('data/customer_shopping_data.xlsx')
raw_df = pd.read_excel(input_path)
tables = transform_dataset(input_path)

uri = 'postgresql://postgres:Triweio_123@localhost:5432/doantn'
engine = create_engine(uri)

staging_raw = normalize_columns(raw_df).copy()
staging_raw = staging_raw[
    [
        'invoice_no',
        'customer_id',
        'gender',
        'age',
        'category',
        'quantity',
        'price',
        'payment_method',
        'invoice_date',
        'shopping_mall',
    ]
]
staging_raw = staging_raw.astype(object).where(pd.notna(staging_raw), None)
staging_raw['source_file'] = str(input_path)

with engine.begin() as conn:
    conn.execute(text('DELETE FROM staging_customer_shopping_raw'))
    conn.execute(text('DELETE FROM transactions'))
    conn.execute(text('DELETE FROM customers'))
    conn.execute(text('DELETE FROM products'))
    conn.execute(text('DELETE FROM shopping_malls'))

    staging_raw.to_sql('staging_customer_shopping_raw', conn, if_exists='append', index=False)
    tables['customers'].to_sql('customers', conn, if_exists='append', index=False)
    tables['products'].to_sql('products', conn, if_exists='append', index=False)
    tables['shopping_malls'].to_sql('shopping_malls', conn, if_exists='append', index=False)
    tables['transactions'].to_sql('transactions', conn, if_exists='append', index=False)

    conn.execute(text("SELECT setval(pg_get_serial_sequence('products','product_id'), COALESCE((SELECT MAX(product_id) FROM products), 1), true)"))
    conn.execute(text("SELECT setval(pg_get_serial_sequence('shopping_malls','mall_id'), COALESCE((SELECT MAX(mall_id) FROM shopping_malls), 1), true)"))

print({k: len(v) for k, v in tables.items()})
'@ | python -
```

Số lượng mong muốn:

```text
customers: 99457
products: 8
shopping_malls: 11
transactions: 99457
```

## 10. Kiểm tra số lượng bản ghi sau import

```powershell
@'
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')
with engine.begin() as conn:
    for table in ['staging_customer_shopping_raw', 'customers', 'products', 'shopping_malls', 'transactions']:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()
        print(table, count)
'@ | python -
```

## 11. Chạy pipeline từ PostgreSQL

Lệnh chuẩn:

```powershell
python -m app.cli --source postgres --connection-uri "postgresql://postgres:Triweio_123@localhost:5432/doantn" --config configs/ecommerce_config.yaml --apply-fixes
```

Ý nghĩa:
- Đọc từ PostgreSQL qua `source_query` trong config
- Chạy data cleaning pipeline
- Ghi output về PostgreSQL
- Nếu có fix tự động hợp lệ theo mode `conservative`, sẽ materialize sang `fixed_transactions`

Lưu ý thực tế:
- Dataset gần 100k dòng nên có thể chạy khá lâu
- Nếu terminal timeout hoặc môi trường dừng giữa chừng, nên chạy lại sau khi đã apply `sql/littlemigration.sql`

## 12. Các bảng output mong muốn sau pipeline

Sau khi chạy thành công, các bảng cần có trong DB:

- `detected_issues`
- `fix_recommendations`
- `dataset_profile`
- `fixed_transactions`
- `cleaning_actions`
- `final_report`

Không nên còn bảng rác cũ:

- `recommendations`
- `fixed_data`

## 13. Kiểm tra output sau pipeline

Kiểm tra danh sách bảng:

```powershell
python -c "from sqlalchemy import create_engine, inspect; insp=inspect(create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')); print(sorted(insp.get_table_names()))"
```

Kiểm tra số lượng output:

```powershell
@'
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')
with engine.begin() as conn:
    for table in ['detected_issues', 'fix_recommendations', 'dataset_profile', 'fixed_transactions', 'cleaning_actions', 'final_report']:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()
        print(table, count)
'@ | python -
```

Xem sample issue:

```powershell
@'
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')
df = pd.read_sql('SELECT * FROM detected_issues LIMIT 20', engine)
print(df)
'@ | python -
```

Xem sample recommendations:

```powershell
@'
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')
df = pd.read_sql('SELECT * FROM fix_recommendations LIMIT 20', engine)
print(df)
'@ | python -
```

Xem dataset profile:

```powershell
@'
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('postgresql://postgres:Triweio_123@localhost:5432/doantn')
df = pd.read_sql('SELECT * FROM dataset_profile ORDER BY profile_id LIMIT 50', engine)
print(df)
'@ | python -
```

## 14. Nếu pipeline full chạy lâu hoặc bị timeout

Bạn có thể test nhanh trên sample nhỏ trước khi chạy full:

```powershell
@'
from app.app_settings import load_config_from_yaml
from app.data_access.postgresql_source import PostgresDataSource
from app.services.pipeline_service import DataCleaningPipelineService
from app.services.report_service import ReportService
from app.services.fix_service import FixService
from app.utils import prepare_input_dataframe, ensure_columns_exist

config = load_config_from_yaml('configs/ecommerce_config.yaml')
query = config.source_query.strip() + '\nLIMIT 1000'
source = PostgresDataSource(
    'postgresql://postgres:Triweio_123@localhost:5432/doantn',
    config.table_name,
    query=query,
)
df = prepare_input_dataframe(source.read(), config.id_column)
ensure_columns_exist(df, list(config.rules.keys()))

issues_df = DataCleaningPipelineService(config).run(df)
report_service = ReportService()
recommendations_df = report_service.build_recommendations(issues_df)
summary_df = report_service.build_summary(issues_df)
profile_df = report_service.build_dataset_profile(df, issues_df)
fixed_df = FixService(config).apply_fixes(df=df, issues_df=issues_df, mode='conservative')

source.write(issues_df, 'detected_issues')
source.write(recommendations_df, 'fix_recommendations')
source.write(summary_df, 'final_report')
source.write(profile_df, 'dataset_profile')
source.write(fixed_df, 'fixed_transactions')

print('sample_pipeline_ok', len(df), len(issues_df))
'@ | python -
```

Nếu sample này chạy được nhưng full run quá lâu:
- Vấn đề chủ yếu là thời gian xử lý model/anomaly detection
- Không còn là lỗi schema/parse date/ghi PostgreSQL như trước

## 15. Checklist chạy chuẩn

Thứ tự nên làm:

1. `pip install -r requirements.txt`
2. kiểm tra PostgreSQL connect được
3. chạy `sql/postgresql_schema.sql`
4. chạy `sql/littlemigration.sql`
5. chạy `python scripts/import_ecommerce_data.py ...`
6. chạy import vào PostgreSQL
7. kiểm tra số lượng bảng `customers/products/shopping_malls/transactions`
8. chạy `python -m app.cli --source postgres ... --apply-fixes`
9. kiểm tra `detected_issues`, `fix_recommendations`, `dataset_profile`, `fixed_transactions`, `final_report`

## 16. Files liên quan quan trọng

- Schema chính: `sql/postgresql_schema.sql`
- Migration nhỏ: `sql/littlemigration.sql`
- Import transform: `scripts/import_ecommerce_data.py`
- PostgreSQL write logic: `app/data_access/postgresql_source.py`
- Pipeline CLI: `app/cli.py`
- Config e-commerce: `configs/ecommerce_config.yaml`

## 17. Ghi chú cuối

Sau patch hiện tại:
- parse ngày đã thống nhất `dayfirst=True`
- pipeline không còn ghi vào bảng rác `recommendations` hoặc `fixed_data`
- `dataset_profile` đã được sanitize trước khi ghi PostgreSQL
- `detected_issues` không còn bị `replace` theo kiểu phá FK như trước

Nếu sau này bạn thay schema output thêm lần nữa, nhớ cập nhật đồng thời:
- `sql/postgresql_schema.sql`
- `sql/littlemigration.sql`
- mapping/shape trong `app/data_access/postgresql_source.py`
