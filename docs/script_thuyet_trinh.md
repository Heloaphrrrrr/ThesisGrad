# KỊCH BẢN THUYẾT TRÌNH VÀ DEMO ĐỒ ÁN

## 1. Mục tiêu của buổi trình bày

Tên đề tài:

**Dùng AI phát hiện dữ liệu sai lệch, thiếu và bất thường trong cơ sở dữ liệu (làm sạch dữ liệu).**

Tên tiếng Anh:

**AI-Based Detection of Missing, Invalid, and Anomalous Data in Databases for Data Cleaning.**

Thông điệp chính cần trình bày:

> Đồ án xây dựng một pipeline làm sạch dữ liệu lai, kết hợp luật nghiệp vụ để phát hiện missing, invalid và lỗi liên trường với mô hình Isolation Forest không giám sát để phát hiện bất thường. Hệ thống có thể đọc dữ liệu từ CSV hoặc PostgreSQL, sinh khuyến nghị, áp dụng các sửa đổi đủ tin cậy và lưu riêng kết quả để không làm mất dữ liệu gốc.

## 2. Chuẩn bị trước khi gặp giảng viên

Mở sẵn các chương trình sau:

1. Visual Studio Code tại thư mục `C:\Users\ACER\OneDrive\Desktop\DoAnTN`.
2. Một terminal PowerShell trong Visual Studio Code.
3. pgAdmin và database `doantn`, nếu muốn trình bày phần PostgreSQL.
4. Excel để mở nhanh các tệp CSV đầu vào và đầu ra.
5. Báo cáo Word hoặc PDF tại đúng trang có sơ đồ pipeline, Isolation Forest và kết quả thực nghiệm.

Không nên chạy trực tiếp hai tệp sau trong buổi demo:

- `sql/postgresql_schema.sql`, vì đây là script tạo toàn bộ schema.
- `sql/littlemigration.sql`, vì script này xóa và tạo lại một số bảng cleaning.

Không nên chạy bộ dữ liệu đầy đủ 99.457 dòng trước mặt giảng viên. Phần này có thể mất vài phút. Demo trực tiếp nên sử dụng sample 2.000 dòng, còn kết quả full được trình bày từ thư mục `outputs/Danh_gia_hieu_nang`.

Thư mục dự phòng đã được tạo sẵn:

```text
outputs/demo_thuyet_trinh
```

Nếu lệnh demo gặp lỗi ngoài ý muốn, có thể mở các kết quả trong thư mục này và tiếp tục trình bày.

## 3. Kịch bản thuyết trình đề xuất

### 3.1. Mở đầu

Lời trình bày:

> Kính thưa thầy, đề tài của em tập trung xây dựng một hệ thống hỗ trợ phát hiện và làm sạch dữ liệu giao dịch. Hệ thống không sử dụng AI cho tất cả các loại lỗi. Những lỗi có quy tắc rõ ràng như thiếu dữ liệu, sai miền giá trị và không nhất quán giữa các trường được phát hiện bằng luật nghiệp vụ. AI, cụ thể là Isolation Forest, được sử dụng cho những bất thường khó biểu diễn bằng luật cố định.

Nếu thầy hỏi vì sao không dùng Excel:

> Với một tệp nhỏ và xử lý một lần, Excel có thể tìm ô trống hoặc giá trị sai đơn giản nhanh hơn. Mục tiêu của hệ thống là tự động hóa quy trình có thể chạy lặp lại trên CSV hoặc PostgreSQL, lưu vết kết quả, tạo khuyến nghị và phát hiện thêm các bất thường thống kê mà bộ lọc Excel cố định khó mô tả.

### 3.2. Trình bày kiến trúc tổng quát

Lời trình bày:

> Pipeline bắt đầu từ dữ liệu CSV hoặc PostgreSQL. Dữ liệu được chuẩn hóa kiểu dữ liệu và tạo các feature dẫn xuất. Hệ thống sau đó chạy ba nhóm kiểm tra dựa trên luật, gồm missing, invalid và cross-field. Các dòng tương đối sạch được dùng làm tập tham chiếu cho Isolation Forest. Sau khi phát hiện dòng bất thường, hệ thống xác định cột đóng góp, đề xuất giá trị thay thế, tính confidence và chỉ tự động áp dụng các trường hợp đạt ngưỡng cấu hình.

Luồng rút gọn:

```text
CSV/PostgreSQL
    -> Chuẩn hóa dữ liệu
    -> Tạo feature
    -> Missing/Invalid/Cross-field bằng luật
    -> Tạo tập tham chiếu tương đối sạch
    -> Isolation Forest phát hiện anomaly
    -> Xác định cột đóng góp
    -> Sinh khuyến nghị và confidence
    -> Áp dụng sửa theo chế độ
    -> Xuất báo cáo và dữ liệu sau làm sạch
```

### 3.3. Giải thích dữ liệu kiểm thử và file labels

Mở hai tệp:

```powershell
Start-Process "outputs\e2e_dirty\ecommerce_dirty_sample.csv"
Start-Process "outputs\e2e_dirty\ecommerce_dirty_labels.csv"
```

Lời trình bày:

> Bộ sample hiện có 2.000 dòng. Một số lỗi được chủ động chèn vào để tạo tình huống kiểm thử có kiểm soát. File `ecommerce_dirty_sample.csv` là đầu vào của pipeline. File `ecommerce_dirty_labels.csv` chỉ ghi lại vị trí và giá trị của các lỗi đã chèn để đối chiếu sau khi chạy, hoàn toàn không được đưa vào quá trình huấn luyện Isolation Forest.

Kiểm tra số dòng và số nhãn:

```powershell
$sample = Import-Csv "outputs\e2e_dirty\ecommerce_dirty_sample.csv"
$labels = Import-Csv "outputs\e2e_dirty\ecommerce_dirty_labels.csv"
"Sample rows: $($sample.Count)"
"Seeded labels: $($labels.Count)"
$labels | Group-Object issue_type | Select-Object Name, Count | Format-Table -AutoSize
```

Kết quả hiện tại:

```text
Sample rows: 2000
Seeded labels: 36

anomaly: 4
invalid: 24
missing: 8
```

Lời nhấn mạnh:

> File labels là ground truth của thí nghiệm, không phải nhãn huấn luyện. Isolation Forest vẫn là mô hình học không giám sát.

### 3.4. Trình bày cấu hình

Mở `configs/ecommerce_config.yaml` trong Visual Studio Code và chỉ vào hai nhóm cấu hình:

1. Các luật của từng cột như `required`, `allowed_values`, `min_value` và `max_value`.
2. Cấu hình mô hình và sửa tự động.

Có thể hiển thị nhanh bằng PowerShell:

```powershell
Select-String -Path "configs\ecommerce_config.yaml" -Pattern "contamination|n_estimators|random_state|anomaly_segment_column|min_anomaly_segment_size|conservative_confidence_threshold"
```

Thông số hiện tại:

```text
contamination: 0.08
n_estimators: 200
random_state: 42
anomaly_segment_column: category
min_anomaly_segment_size: 500
conservative_confidence_threshold: 0.80
```

Lời trình bày:

> `contamination` là tỷ lệ bất thường kỳ vọng dùng để xác định ngưỡng của Isolation Forest. `n_estimators` là số cây cô lập. `random_state` giúp kết quả có thể tái lập. Ngưỡng `0.80` không phải ngưỡng phát hiện bất thường mà là ngưỡng confidence để chế độ conservative quyết định có tự động áp dụng khuyến nghị hay không.

### 3.5. Chạy pipeline trực tiếp

Đưa terminal về thư mục gốc:

```powershell
Set-Location "C:\Users\ACER\OneDrive\Desktop\DoAnTN"
```

Kiểm tra môi trường:

```powershell
python --version
python -c "import pandas, numpy, sklearn, sqlalchemy; print('pandas', pandas.__version__); print('numpy', numpy.__version__); print('scikit-learn', sklearn.__version__); print('SQLAlchemy', sqlalchemy.__version__)"
```

Chạy demo chính bằng một lệnh:

```powershell
python -m app.cli --source csv --input outputs/e2e_dirty/ecommerce_dirty_sample.csv --config configs/ecommerce_config.yaml --output outputs/demo_thuyet_trinh --apply-fixes --mode conservative --report --profile-runtime
```

Trong thời gian chờ, trình bày:

> Lệnh này đọc sample CSV, dùng cấu hình thương mại điện tử, chạy toàn bộ pipeline, áp dụng những sửa đổi đạt confidence từ 0,80 trở lên theo chế độ conservative, in báo cáo và ghi thời gian từng giai đoạn. File labels không xuất hiện trong câu lệnh, chứng minh nhãn không được dùng để huấn luyện hoặc phát hiện.

Kết quả đã kiểm tra gần nhất:

```text
total_issues: 269
issue_type_anomaly: 229
issue_type_invalid: 32
issue_type_missing: 8
average_confidence: 0.1676
fixable_rate: 0.9591
run_pipeline: khoảng 16 giây
```

Giải thích 269 issue không đồng nghĩa có 269 dòng chắc chắn sai:

> Hệ thống lưu issue ở cấp dòng và cột. Một dòng bất thường có thể tạo nhiều issue tại nhiều cột. Ngoài 36 lỗi được chủ động chèn, Isolation Forest còn sinh các ứng viên bất thường tự nhiên trong sample. Các anomaly này là đối tượng cần xem xét, không được khẳng định đều là lỗi thật.

### 3.6. Trình bày các đầu ra

Liệt kê các tệp kết quả:

```powershell
Get-ChildItem "outputs\demo_thuyet_trinh" | Select-Object Name, Length | Format-Table -AutoSize
```

Ý nghĩa:

```text
detected_issues.csv       Danh sách lỗi và bất thường phát hiện được
fix_recommendations.csv   Các giá trị được khuyến nghị
final_report.csv          Thống kê tổng hợp
dataset_profile.csv       Hồ sơ chất lượng theo từng cột
fixed_transactions.csv    Dữ liệu sau khi áp dụng sửa
```

Xem thống kê theo loại issue:

```powershell
Import-Csv "outputs\demo_thuyet_trinh\detected_issues.csv" | Group-Object issue_type | Select-Object Name, Count | Format-Table -AutoSize
```

Xem các khuyến nghị đạt ngưỡng sửa conservative:

```powershell
Import-Csv "outputs\demo_thuyet_trinh\detected_issues.csv" | Where-Object { [double]$_.confidence -ge 0.8 -and $_.can_auto_fix -eq "True" -and $_.suggested_value -ne "" } | Select-Object -First 20 row_id,column_name,issue_type,current_value,suggested_value,confidence,severity,source_method | Format-Table -AutoSize
```

Kết quả hiện tại có 28 khuyến nghị đủ điều kiện:

```text
missing: 4
invalid: 24
```

Lưu ý khi trình bày:

> `fixable_rate` cho biết tỷ lệ issue mà hệ thống có khả năng tạo khuyến nghị, không phải tỷ lệ đã tự động sửa. Ở chế độ conservative, chỉ 28 khuyến nghị có giá trị đề xuất, được phép tự sửa và đạt confidence từ 0,80 trở lên.

### 3.7. So sánh trước và sau làm sạch

Hiển thị ba bản ghi trước khi sửa:

```powershell
Import-Csv "outputs\e2e_dirty\ecommerce_dirty_sample.csv" | Where-Object { $_.invoice_no -in @("I123119","I334856","I139441") } | Select-Object invoice_no,gender,age,category,quantity,price | Format-Table -AutoSize
```

Hiển thị ba bản ghi sau khi sửa:

```powershell
Import-Csv "outputs\demo_thuyet_trinh\fixed_transactions.csv" | Where-Object { $_.invoice_no -in @("I123119","I334856","I139441") } | Select-Object invoice_no,gender,age,category,quantity,price | Format-Table -AutoSize
```

Ba trường hợp minh họa:

```text
I123119: quantity thiếu -> 1
I334856: gender Femal -> Female
I139441: age 150 -> 120
```

Xem căn cứ ra quyết định:

```powershell
Import-Csv "outputs\demo_thuyet_trinh\detected_issues.csv" | Where-Object { $_.row_id -in @("I123119","I334856","I139441") } | Select-Object row_id,column_name,issue_type,current_value,suggested_value,confidence,can_auto_fix | Format-Table -AutoSize
```

Lời trình bày:

> Hệ thống không sửa mọi anomaly. Ví dụ những khuyến nghị có confidence thấp hơn 0,80 vẫn được ghi vào báo cáo để người dùng tham khảo nhưng không được áp dụng trong chế độ conservative. Điều này giúp hạn chế thay đổi dữ liệu đúng do mô hình chỉ nghi ngờ là bất thường.

### 3.8. Đối chiếu với file labels

Chạy lệnh:

```powershell
python -c "import pandas as pd; l=pd.read_csv('outputs/e2e_dirty/ecommerce_dirty_labels.csv'); d=pd.read_csv('outputs/demo_thuyet_trinh/detected_issues.csv'); k=['row_id','column_name','issue_type']; m=l.merge(d[k].drop_duplicates(),on=k,how='left',indicator=True); print(m.groupby(['issue_type','_merge'],observed=False).size()); print('Matched:',(m['_merge']=='both').sum(),'of',len(m))"
```

Kết quả đã kiểm tra:

```text
anomaly: 4/4
invalid: 24/24
missing: 8/8
Matched: 36 of 36
```

Lời trình bày:

> Trong lần chạy hiện tại, hệ thống tìm lại được toàn bộ 36 lỗi đã chủ động chèn. Tuy nhiên, kết quả này chỉ phản ánh khả năng nhận ra bộ lỗi tổng hợp hiện tại. Nó không có nghĩa hệ thống đạt độ chính xác tuyệt đối trên mọi dữ liệu thực tế. Các anomaly phát hiện thêm vẫn cần được đánh giá theo ngữ cảnh nghiệp vụ.

### 3.9. Trình bày PostgreSQL

Trong pgAdmin, mở:

```text
Servers
    -> PostgreSQL
    -> Databases
    -> doantn
    -> Schemas
    -> public
    -> Tables
```

Lời trình bày:

> Database được thiết kế trước dựa trên cấu trúc và ý nghĩa nghiệp vụ của dữ liệu. Ứng dụng không tự thiết kế database. PostgreSQL gồm nhóm staging, nhóm nghiệp vụ và nhóm kết quả data cleaning. Ứng dụng Python đọc dữ liệu bằng câu truy vấn đã cấu hình, xử lý bằng pipeline và ghi kết quả vào các bảng riêng.

Mở Query Tool và chạy:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Kiểm tra số dòng nghiệp vụ:

```sql
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'shopping_malls', COUNT(*) FROM shopping_malls
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;
```

Xem dữ liệu:

```sql
SELECT *
FROM customers
LIMIT 10;
```

Xem kết quả phát hiện nếu database đã có dữ liệu:

```sql
SELECT
    row_id,
    column_name,
    issue_type,
    current_value,
    suggested_value,
    confidence,
    can_auto_fix
FROM detected_issues
ORDER BY confidence DESC NULLS LAST
LIMIT 20;
```

Không cần chạy pipeline PostgreSQL trực tiếp trong buổi demo. Nếu thầy yêu cầu, sử dụng mẫu lệnh sau sau khi thay thông tin kết nối:

```powershell
$env:DATABASE_URL = "postgresql://postgres:Triweio_123@localhost:5432/doantn"
python -m app.cli --source postgres --connection-uri "$env:DATABASE_URL" --config configs/ecommerce_config.yaml --apply-fixes --mode conservative --report --profile-runtime
```

Cảnh báo:

> Lệnh PostgreSQL sẽ ghi lại các bảng kết quả cleaning và có thể mất nhiều thời gian do xử lý toàn bộ dữ liệu. Chỉ chạy khi database đã được kiểm tra và giảng viên thực sự yêu cầu.

### 3.10. Trình bày kết quả trên bộ dữ liệu đầy đủ

Không chạy lại trực tiếp. Mở kết quả có sẵn:

```powershell
Get-ChildItem "outputs\Danh_gia_hieu_nang" | Select-Object Name, Length | Format-Table -AutoSize
Import-Csv "outputs\Danh_gia_hieu_nang\final_report.csv" | Format-Table -AutoSize
```

Lời trình bày:

> Hệ thống đã được chạy thử trên bộ dữ liệu đầy đủ 99.457 giao dịch. Phần này dùng để đánh giá khả năng xử lý dữ liệu lớn hơn. Khi demo trực tiếp, em chọn sample 2.000 dòng để bảo đảm thời gian trình bày, nhưng quy trình xử lý của hai lần chạy là giống nhau.

Không so sánh trực tiếp số issue của sample dirty với bộ dữ liệu full, vì hai bộ dữ liệu phục vụ hai mục tiêu khác nhau:

- Sample dirty dùng để kiểm tra các lỗi đã chủ động tạo.
- Full data dùng để đánh giá khả năng xử lý và phát hiện bất thường trên dữ liệu thực.

## 4. Kết luận trình bày

Lời kết:

> Kết quả của đồ án là một pipeline làm sạch dữ liệu lai và có khả năng tái sử dụng. Luật nghiệp vụ đảm nhiệm các trường hợp rõ ràng và cần tính giải thích cao. Isolation Forest hỗ trợ phát hiện các mẫu bất thường chưa được mô tả trước. Hệ thống không tự động sửa tất cả kết quả AI mà sử dụng confidence và chế độ xử lý để kiểm soát rủi ro. Dữ liệu gốc được giữ lại, còn issue, khuyến nghị, hồ sơ chất lượng và dữ liệu sau sửa được lưu riêng để có thể kiểm tra và truy vết.

## 5. Câu hỏi phản biện có thể gặp

### Đây có phải mô hình hybrid không?

> Có. Hybrid ở đây là sự kết hợp giữa rule-based validation và học máy không giám sát, không phải sự kết hợp giữa supervised learning và unsupervised learning.

### Mô hình có giám sát hay không giám sát?

> Isolation Forest là mô hình không giám sát. Mô hình không nhận nhãn đúng hoặc sai trong quá trình huấn luyện.

### Tại sao lại có file labels?

> Labels là nhật ký các lỗi được chủ động chèn để đánh giá sau khi pipeline chạy. File này không được truyền vào mô hình.

### Tại sao missing và invalid không dùng AI?

> Đây là các lỗi có định nghĩa rõ ràng. Sử dụng luật sẽ chính xác, nhanh và dễ giải thích hơn. AI được dành cho anomaly, là nhóm khó biểu diễn bằng luật cố định.

### Tại sao không dùng Excel?

> Excel phù hợp với dữ liệu nhỏ và xử lý một lần. Hệ thống tập trung vào chạy lặp lại, tự động hóa, xử lý từ database, lưu vết kết quả và phát hiện bất thường thống kê.

### 269 issue có nghĩa là 269 dữ liệu sai không?

> Không. Issue được ghi ở cấp dòng và cột. Một dòng có thể có nhiều issue. Anomaly là ứng viên cần kiểm tra, không phải kết luận chắc chắn là sai.

### Tại sao average confidence thấp nhưng fixable rate cao?

> Fixable rate cho biết hệ thống có thể đưa ra khuyến nghị, còn confidence thể hiện độ chắc chắn. Chế độ conservative chỉ áp dụng khuyến nghị có confidence từ 0,80 trở lên.

### Contamination 0,08 có nghĩa gì?

> Đây là tỷ lệ bất thường kỳ vọng giúp Isolation Forest đặt ngưỡng quyết định. Nó không có nghĩa 8% dữ liệu chắc chắn sai.

### Database được tạo tự động từ CSV phải không?

> Không. CSV được khảo sát để xác định yêu cầu, sau đó schema PostgreSQL được thiết kế và khởi tạo trước. Ứng dụng chỉ đọc, chuẩn hóa, nạp và xử lý dữ liệu theo schema đã có.

### AI có chạy bên trong PostgreSQL không?

> Không. Ứng dụng Python dùng SQLAlchemy để truy vấn dữ liệu từ PostgreSQL, chạy mô hình trong tầng ứng dụng rồi ghi kết quả trở lại database.

### Hệ thống có ghi đè dữ liệu gốc không?

> Không. Kết quả sau sửa được lưu trong `fixed_transactions` hoặc tệp `fixed_transactions.csv`, nhờ đó có thể đối chiếu với dữ liệu ban đầu.

## 6. Bảng lệnh demo nhanh

### Bước 1: Vào project

```powershell
Set-Location "C:\Users\ACER\OneDrive\Desktop\DoAnTN"
```

### Bước 2: Kiểm tra sample và labels

```powershell
$sample = Import-Csv "outputs\e2e_dirty\ecommerce_dirty_sample.csv"; $labels = Import-Csv "outputs\e2e_dirty\ecommerce_dirty_labels.csv"; "Sample: $($sample.Count)"; "Labels: $($labels.Count)"; $labels | Group-Object issue_type | Select-Object Name,Count | Format-Table -AutoSize
```

### Bước 3: Chạy pipeline

```powershell
python -m app.cli --source csv --input outputs/e2e_dirty/ecommerce_dirty_sample.csv --config configs/ecommerce_config.yaml --output outputs/demo_thuyet_trinh --apply-fixes --mode conservative --report --profile-runtime
```

### Bước 4: Xem tổng hợp

```powershell
Import-Csv "outputs\demo_thuyet_trinh\final_report.csv" | Format-Table -AutoSize
```

### Bước 5: Xem các sửa đổi đủ confidence

```powershell
Import-Csv "outputs\demo_thuyet_trinh\detected_issues.csv" | Where-Object { [double]$_.confidence -ge 0.8 -and $_.can_auto_fix -eq "True" -and $_.suggested_value -ne "" } | Select-Object -First 20 row_id,column_name,issue_type,current_value,suggested_value,confidence | Format-Table -AutoSize
```

### Bước 6: So sánh trước và sau

```powershell
Import-Csv "outputs\e2e_dirty\ecommerce_dirty_sample.csv" | Where-Object { $_.invoice_no -in @("I123119","I334856","I139441") } | Select-Object invoice_no,gender,age,category,quantity,price | Format-Table -AutoSize
Import-Csv "outputs\demo_thuyet_trinh\fixed_transactions.csv" | Where-Object { $_.invoice_no -in @("I123119","I334856","I139441") } | Select-Object invoice_no,gender,age,category,quantity,price | Format-Table -AutoSize
```

### Bước 7: Đối chiếu labels

```powershell
python -c "import pandas as pd; l=pd.read_csv('outputs/e2e_dirty/ecommerce_dirty_labels.csv'); d=pd.read_csv('outputs/demo_thuyet_trinh/detected_issues.csv'); k=['row_id','column_name','issue_type']; m=l.merge(d[k].drop_duplicates(),on=k,how='left',indicator=True); print(m.groupby(['issue_type','_merge'],observed=False).size()); print('Matched:',(m['_merge']=='both').sum(),'of',len(m))"
```

## 7. Phương án xử lý sự cố

Nếu lệnh chạy bị lỗi:

1. Không dành thời gian sửa lỗi trước mặt giảng viên.
2. Nói rằng kết quả của lần chạy gần nhất đã được lưu để bảo đảm khả năng truy vết.
3. Mở `outputs/demo_thuyet_trinh`.
4. Trình bày `final_report.csv`, `detected_issues.csv` và `fixed_transactions.csv`.

Nếu pgAdmin không kết nối:

1. Trình bày ERD trong báo cáo.
2. Mở `sql/postgresql_schema.sql` để chỉ ra các bảng và khóa ngoại.
3. Tiếp tục demo bằng CSV vì pipeline hỗ trợ độc lập cả hai nguồn.

Nếu Excel mở chậm:

```powershell
Import-Csv "outputs\demo_thuyet_trinh\final_report.csv" | Format-Table -AutoSize
```

Nếu được yêu cầu chạy full data:

> Em xin trình bày kết quả full đã chạy sẵn vì thời gian thực thi dài hơn thời lượng demo. Lệnh và pipeline hoàn toàn giống với sample, chỉ thay đổi đường dẫn đầu vào.

## 8. Checklist cuối cùng

- Kiểm tra Python chạy được.
- Kiểm tra sample có 2.000 dòng.
- Kiểm tra labels có 36 dòng.
- Kiểm tra thư mục `outputs/demo_thuyet_trinh` còn đủ năm tệp.
- Mở sẵn `configs/ecommerce_config.yaml`.
- Mở sẵn hình pipeline và ERD trong báo cáo.
- Không chạy schema hoặc migration khi chưa sao lưu.
- Không gọi anomaly là lỗi chắc chắn.
- Không nói AI được dùng để tìm ô trống.
- Nhấn mạnh rule-based kết hợp Isolation Forest không giám sát.
- Nhấn mạnh labels chỉ dùng đánh giá.
- Nhấn mạnh dữ liệu gốc không bị ghi đè.
