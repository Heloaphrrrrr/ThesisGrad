# Huong Dan Chay End-to-End Do An

Tai lieu nay danh cho may chua cai gi san. Muc tieu la:

- chay duoc pipeline tu dau den cuoi
- quan sat tung buoc trong pipeline
- thu inject loi de kiem tra he thong bat loi va de xuat sua
- neu can, chay them phien PostgreSQL

## 1. Yeu cau toi thieu

Can cai 4 thu sau:

- Git
- Python 3.12 hoac moi hon
- PostgreSQL 18 neu muon chay phien database
- PowerShell tren Windows

Neu chua co Python tren PATH, co the mo PowerShell va kiem tra:

```powershell
python --version
```

Neu chua co PostgreSQL, co the bo qua phan PostgreSQL luc dau va chay phien CSV truoc.

## 2. Lay ma nguon

Giai nen hoac clone repo vao mot thu muc, sau do mo PowerShell tai thu muc goc:

```powershell
cd C:\Users\ACER\OneDrive\Desktop\DoAnTN
```

Neu may thầy khac duong dan, chi can dung dung duong dan thu muc goc cua repo.

## 3. Cai thu vien Python

Tao moi truong ao va cai dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Neu PowerShell chan viec activate, chay tam:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\.venv\Scripts\Activate.ps1
```

## 4. Chay nhanh khong can PostgreSQL

Day la cach ngan nhat de thay toan bo pipeline:

```powershell
python -m app.cli `
  --source csv `
  --input data\customer_shopping_data.csv `
  --config configs\ecommerce_config.yaml `
  --output outputs\teacher_csv_run `
  --report `
  --profile-runtime `
  --apply-fixes
```

Ket qua se nam trong:

- `outputs\teacher_csv_run\detected_issues.csv`
- `outputs\teacher_csv_run\fix_recommendations.csv`
- `outputs\teacher_csv_run\dataset_profile.csv`
- `outputs\teacher_csv_run\final_report.csv`
- `outputs\teacher_csv_run\fixed_transactions.csv`

Day la duong chay dung de:

- quan sat pipeline
- xem so issue phat hien
- xem goi y sua
- xem thoi gian tung stage
- kiem tra phan `apply-fixes`

## 5. Thu inject loi

He thong da co san 2 cach de tao du lieu loi ma khong can sua tay tung dong.

### Cach 1: Tu sinh dirty data tu du lieu sach

Chay lenh sau:

```powershell
python -m app.cli `
  --source csv `
  --input data\customer_shopping_data.csv `
  --config configs\ecommerce_config.yaml `
  --output outputs\teacher_seeded_dirty `
  --seed-dirty `
  --seed-rate 0.2
```

Lenh nay se tao ra:

- `outputs\teacher_seeded_dirty\seeded_dirty_data.csv`
- `outputs\teacher_seeded_dirty\seeded_dirty_labels.csv`

Sau do chay pipeline tren file dirty vua tao:

```powershell
python -m app.cli `
  --source csv `
  --input outputs\teacher_seeded_dirty\seeded_dirty_data.csv `
  --config configs\ecommerce_config.yaml `
  --output outputs\teacher_seeded_run `
  --report `
  --profile-runtime `
  --apply-fixes
```

### Cach 2: Tu chinh CSV bang tay

Neu muon thu cong, thay co the mo file CSV, sua mot vai dong thanh:

- gia tri thieu
- gia tri sai mien
- gia tri bat thuong lon hon rat nhieu so voi dong xung quanh

Sau do chay lai lenh pipeline o muc 4.

## 6. Chay voi PostgreSQL

Phan nay danh cho truong hop muon dung database lam nguon du lieu chuan va noi luu ket qua.

### 6.1 Tao database

Mo PostgreSQL va tao mot database, vi du:

```sql
CREATE DATABASE doantn;
```

Neu dung user `postgres`, co the giu nguyen, con khong thi thay connection string o buoc sau.

### 6.2 Tao schema

Chay file schema:

```powershell
$env:PGPASSWORD='Triweio_123'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h localhost -p 5432 -U postgres -d doantn -v ON_ERROR_STOP=1 -f 'sql\postgresql_schema.sql'
```

Neu may khac duong dan PostgreSQL, thay lai duong dan `psql.exe`.

### 6.3 Nap du lieu vao PostgreSQL

Co 2 cach:

1. Cach de nhat la dung du lieu CSV sach hien co trong repo va nap vao DB bang script cua du an.
2. Neu muon dung du lieu Excel, chay script chuyen doi:

```powershell
python scripts\import_ecommerce_data.py --input data\customer_shopping_data.xlsx --output-dir outputs\ecommerce_import
```

Script nay tao 4 file CSV trung gian:

- `customers.csv`
- `products.csv`
- `shopping_malls.csv`
- `transactions.csv`

Sau do can nap cac bang nay vao DB theo schema tuong ung. Neu can giai phap nhanh cho buoi bao ve, CSV mode o muc 4 van la cach chat nhat de chay end-to-end ngay lap tuc.

### 6.4 Chay pipeline tu PostgreSQL

Khi DB da co du lieu:

```powershell
python -m app.cli `
  --source postgres `
  --connection-uri "postgresql://postgres:Triweio_123@localhost:5432/doantn" `
  --config configs\ecommerce_config.yaml `
  --output outputs\teacher_pg_run `
  --report `
  --profile-runtime `
  --apply-fixes
```

## 7. Quan sat pipeline

Khi chay `--profile-runtime`, chuong trinh se in thoi gian cho cac stage chinh:

- `load_config`
- `read_source`
- `prepare_input`
- `validate_columns`
- `run_pipeline`
- `build_reports`
- `write_outputs`
- `apply_fixes`
- `write_fixed_output`

Day la cach nhanh nhat de thay:

- pipeline dang cham o dau
- co phan nao la bottleneck khong
- thoi gian co on khong

## 8. Output can xem

Sau khi chay xong, can xem 5 file nay:

- `detected_issues.csv`
- `fix_recommendations.csv`
- `dataset_profile.csv`
- `final_report.csv`
- `fixed_transactions.csv`

Y nghia:

- `detected_issues`: cac loi phat hien duoc
- `fix_recommendations`: goi y sua
- `dataset_profile`: thong ke du lieu
- `fixed_transactions`: du lieu sau khi sua
- `final_report`: tom tat tong quan

## 9. Neu thay muon test he thong bat loi

Nen test 3 tinh huong:

1. Thieu cot
   - xoa mot cot bat buoc trong CSV
   - pipeline phai bao loi ro rang

2. Sai dinh dang ngay
   - doi `invoice_date` thanh gia tri khong hop le
   - pipeline phai bao loi parse ngay

3. Loi anomaly / invalid / missing
   - dung `--seed-dirty`
   - pipeline phai phat hien issue va de xuat sua

## 10. Loi thuong gap

- `python is not recognized`
  - Python chua cai hoac chua add vao PATH

- `ModuleNotFoundError`
  - chua cai dependency bang `pip install -r requirements.txt`

- `psql is not recognized`
  - chua cai PostgreSQL hoac duong dan `psql.exe` khac

- Loi parse `invoice_date`
  - du lieu dau vao co gia tri ngay sai dinh dang
  - can dung file raw sach hon hoac sua du lieu dau vao

- `Missing required columns`
  - file CSV dau vao khong co dung bo cot can thiet

## 11. Cach trinh bay voi giang vien

Neu thay hoi vai tro cua PostgreSQL, co the noi ngan gon:

> PostgreSQL la noi luu du lieu chuan va ket qua cleaning. AI khong chay trong database, ma doc du lieu tu PostgreSQL hoac CSV, xu ly o pipeline ben ngoai, roi ghi ket qua tro lai database.

Neu thay hoi ve inject loi:

> He thong co the tao dirty data tu du lieu sach bang `--seed-dirty`, sau do chay lai pipeline de kiem tra detector va recommender.

