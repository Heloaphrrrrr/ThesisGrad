# Đề cương mô tả đồ án

## Dùng AI phát hiện dữ liệu sai lệch, thiếu, bất thường trong cơ sở dữ liệu

### Hướng tiếp cận: AI-assisted Data Cleaning System

---

## 1. Mục tiêu đồ án

Đồ án hướng tới xây dựng một hệ thống hỗ trợ kiểm tra chất lượng dữ liệu và làm sạch dữ liệu trong cơ sở dữ liệu.

Tên đề tài:

> **Dùng AI phát hiện dữ liệu sai lệch, thiếu, bất thường trong cơ sở dữ liệu (làm sạch dữ liệu)**

Hệ thống không chỉ phát hiện các lỗi đơn giản như dữ liệu bị thiếu hoặc sai định dạng, mà còn phát hiện các bản ghi bất thường khó mô tả bằng các luật cố định.

Định hướng của đồ án là xây dựng một hệ thống **AI-assisted data cleaning**, tức là kết hợp giữa:

- Rule-based validation cho các lỗi rõ ràng.
- AI/ML cho các lỗi bất thường khó định nghĩa bằng luật.
- Cơ chế báo cáo, giải thích và gợi ý xử lý lỗi.

---

## 2. Phân loại lỗi dữ liệu

Trong đồ án, dữ liệu lỗi được chia thành 3 nhóm chính:

| Nhóm lỗi | Ý nghĩa                                                       | Ví dụ                                              |
| -------- | ------------------------------------------------------------- | -------------------------------------------------- |
| Missing  | Dữ liệu bị thiếu                                              | `payment_method = NULL`                            |
| Invalid  | Dữ liệu có tồn tại nhưng sai luật                             | `quantity = -5`, `category = "Tech"`               |
| Anomaly  | Dữ liệu không sai luật nhưng bất thường theo phân bố/ngữ cảnh | `category = Books`, `quantity = 1`, `price = 5000` |

Cách phân loại này giúp hệ thống xử lý đúng bản chất từng loại lỗi, thay vì cố dùng một phương pháp duy nhất cho mọi trường hợp.

---

## 3. Dataset dự kiến

Dataset được chọn theo hướng **e-commerce / customer shopping**, vì đây là lĩnh vực có dữ liệu dạng bảng rõ ràng, dễ hiểu, có nhiều kiểu dữ liệu và phù hợp để tích hợp vào PostgreSQL.

Nguồn dữ liệu đầu vào hiện tại là file giao dịch mua sắm khách hàng với các cột gốc:

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

Với flow thiết kế database, dataset sẽ được xử lý theo các bước:

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

### 3.1 Đọc dataset và chuẩn hóa tên cột

Các cột gốc trong file Excel đang ở dạng uppercase:

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

Sau khi chuẩn hóa về chuẩn snake_case để dùng trong PostgreSQL và pipeline Python:

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

Lưu ý:

- `CUSTOM_ID` được đổi thành `customer_id` để thống nhất ngữ nghĩa.
- Toàn bộ tên cột được đưa về lowercase và snake_case.
- Đây là bước quan trọng vì pipeline data cleaning, feature engineering và SQL schema đều nên dùng cùng một chuẩn tên cột.

### 3.2 Xác định kiểu dữ liệu từng cột

Sau khi chuẩn hóa, kiểu dữ liệu logic của từng cột được xác định như sau:

| Cột              | Kiểu dữ liệu logic | Vai trò |
| ---------------- | ------------------ | ------- |
| `invoice_no`     | text               | Mã giao dịch |
| `customer_id`    | text               | Mã khách hàng |
| `gender`         | categorical        | Thuộc tính khách hàng |
| `age`            | integer            | Tuổi khách hàng |
| `category`       | categorical        | Nhóm sản phẩm |
| `quantity`       | integer            | Số lượng mua |
| `price`          | numeric            | Tổng giá trị giao dịch |
| `payment_method` | categorical        | Phương thức thanh toán |
| `invoice_date`   | date               | Ngày giao dịch |
| `shopping_mall`  | categorical        | Nơi phát sinh giao dịch |

### 3.3 Xác định khóa chính và khóa ngoại

Từ dataset gốc có thể xác định:

- `invoice_no` là khóa chính tự nhiên của giao dịch.
- `customer_id` là khóa định danh khách hàng.
- `category` có thể được ánh xạ sang dimension sản phẩm.
- `shopping_mall` có thể được ánh xạ sang dimension địa điểm mua sắm.

Theo đó:

- `transactions.invoice_no` là khóa chính.
- `transactions.customer_id` là khóa ngoại tới `customers`.
- `transactions.product_id` là khóa ngoại tới `products`.
- `transactions.mall_id` là khóa ngoại tới `shopping_malls`.

### 3.4 Tách bảng theo mức hợp lý

Để phù hợp hơn với yêu cầu thiết kế cơ sở dữ liệu và dễ áp dụng AI theo ngữ cảnh, dữ liệu sẽ không chỉ được giữ ở dạng một bảng phẳng. Thay vào đó, đồ án sẽ chuẩn hóa dataset thành **4 bảng nghiệp vụ**:

```text
customers
products
shopping_malls
transactions
```

Ý nghĩa của từng bảng:

- `customers`: thông tin khách hàng như `customer_id`, `gender`, `age`.
- `products`: nhóm sản phẩm, trong dataset hiện tại được biểu diễn theo `category`.
- `shopping_malls`: thông tin trung tâm mua sắm.
- `transactions`: bảng giao dịch trung tâm, liên kết tới 3 bảng còn lại qua khóa ngoại.

Vì dataset gốc chưa có từng sản phẩm chi tiết theo SKU, bảng `products` trong phạm vi đồ án sẽ được hiểu là **bảng danh mục sản phẩm / product category dimension**. Đây là một giả định thiết kế hợp lý cho bài toán học thuật, đồng thời vẫn đủ ngữ cảnh để phục vụ anomaly detection.

Dataset này phù hợp với đồ án vì có thể biểu diễn rõ cả ba loại lỗi:

- Thiếu dữ liệu: thiếu `payment_method`, `category`, `shopping_mall`.
- Sai dữ liệu: `quantity < 1`, `age > 120`, `payment_method` ngoài danh sách hợp lệ.
- Bất thường: giá trị `price` không phù hợp với `category`, `quantity`, hoặc bối cảnh mua sắm.

---

## 3.5 Feature engineering phục vụ AI

Ngoài các cột gốc, hệ thống sẽ tạo thêm một số feature phát sinh để phục vụ phát hiện bất thường và gợi ý xử lý lỗi.

Các feature quan trọng gồm:

```text
unit_price
age_group
invoice_year
invoice_month
day_of_week
is_weekend
base_unit_price_by_category
price_deviation_from_category
mall_popularity_score
price_band
quantity_band
```

Trong đó:

- `unit_price = price / quantity`: hỗ trợ phát hiện giao dịch có giá bất thường.
- `age_group`: gom nhóm tuổi để tăng tính ổn định cho dữ liệu hành vi.
- `invoice_year`, `invoice_month`, `day_of_week`, `is_weekend`: bổ sung ngữ cảnh thời gian.
- `base_unit_price_by_category`: đơn giá tham chiếu theo từng nhóm sản phẩm.
- `price_deviation_from_category`: độ lệch so với mức giá điển hình của cùng category.
- `mall_popularity_score`: mức độ phổ biến của trung tâm mua sắm dựa trên số giao dịch.
- `price_band`, `quantity_band`: nhóm hóa dữ liệu số để hỗ trợ phân tích và recommendation.

Các feature này không thay thế dữ liệu gốc, mà được dùng như lớp ngữ cảnh bổ sung cho:

- Rule-based validation nâng cao.
- Isolation Forest phát hiện anomaly.
- KNN tìm giao dịch sạch tương tự để gợi ý cho các cột categorical.

---

## 4. Vì sao không dùng AI cho tất cả lỗi?

Không phải mọi lỗi dữ liệu đều nên xử lý bằng AI.

Các lỗi như:

```text
price = NULL
quantity = -5
payment_method = "Paypal"
category = "Tech"
```

là các lỗi có quy tắc rõ ràng. Những lỗi này nên được phát hiện bằng rule-based validation vì cách này:

- Nhanh hơn.
- Chính xác hơn.
- Dễ giải thích hơn.
- Phù hợp với ràng buộc trong cơ sở dữ liệu.

AI được sử dụng cho các trường hợp khó hơn, ví dụ dữ liệu không sai luật nhưng bất thường theo ngữ cảnh.

Ví dụ:

```text
category = Books
quantity = 1
price = 5000
```

Dòng dữ liệu này không vi phạm rule cơ bản vì:

```text
category hợp lệ
quantity > 0
price > 0
```

Tuy nhiên, nếu so với các giao dịch cùng nhóm `Books`, giá trị `price = 5000` có thể là bất thường. Đây là trường hợp phù hợp để dùng mô hình AI phát hiện anomaly.

---

## 5. Kiến trúc tổng thể hệ thống

Pipeline xử lý dữ liệu được đề xuất như sau:

```text
Raw Data / PostgreSQL
        ↓
Data Loading
        ↓
Normalize Database & Feature Engineering
        ↓
Rule-based Detection
(Missing + Invalid)
        ↓
Clean Reference Set
        ↓
Isolation Forest
(Anomaly Detection)
        ↓
Feature Contribution
(Xác định cột nghi ngờ)
        ↓
KNN-based Categorical Suggestion
        ↓
Issue Report / Fix Recommendation
        ↓
PostgreSQL Output Tables
```

Hệ thống được thiết kế theo hướng hybrid:

- Missing và invalid được xử lý bằng rule-based validation.
- Anomaly được phát hiện bằng Isolation Forest.
- KNN được dùng để tìm các bản ghi tương tự, nhưng chỉ phục vụ gợi ý cho dữ liệu categorical/text.
- Numeric anomaly chỉ được báo cáo và đưa về manual review, không tự động sửa thành một con số cụ thể.
- Dữ liệu giao dịch được lấy từ bảng `transactions` và join ngữ cảnh từ `customers`, `products`, `shopping_malls` trước khi đưa vào pipeline AI.

---

## 6. Vai trò của rule-based validation

Rule-based validation được dùng để phát hiện các lỗi có quy tắc rõ ràng.

Ví dụ rule:

```text
age phải nằm trong khoảng 0–120
quantity phải >= 1
price phải >= 0
category phải thuộc danh sách hợp lệ
payment_method phải thuộc danh sách hợp lệ
invoice_date phải đúng định dạng ngày
```

Các lỗi phát hiện bằng rule sẽ được ghi nhận vào bảng lỗi. Đồng thời, các dòng có lỗi rõ ràng sẽ bị loại khỏi tập dữ liệu tham chiếu dùng để huấn luyện mô hình anomaly.

Điều này giúp mô hình AI không học trực tiếp từ dữ liệu bẩn hoàn toàn.

---

## 7. Vai trò của Isolation Forest

Isolation Forest được dùng để phát hiện dữ liệu bất thường.

Đây là mô hình học không giám sát, không cần label khi huấn luyện.

Ý tưởng chính:

> Một điểm dữ liệu bất thường thường ít xuất hiện và khác biệt với phần lớn dữ liệu, nên dễ bị cô lập hơn trong quá trình phân tách ngẫu nhiên.

Trong hệ thống này, Isolation Forest được huấn luyện trên tập dữ liệu tương đối sạch, được tạo ra sau khi rule-based validation đã loại bỏ các dòng missing và invalid rõ ràng.

Quy trình:

```text
Raw data
→ Rule-based scan missing/invalid
→ Clean reference set
→ Train Isolation Forest
→ Detect anomaly trên toàn dataset
```

Như vậy, hệ thống không đi ngược quy trình Data Science. Nó vẫn có bước tiền xử lý trước khi huấn luyện mô hình anomaly.

---

## 8. Vai trò của Feature Contribution

Isolation Forest chỉ cho biết một dòng có bất thường hay không. Tuy nhiên, nó không trực tiếp chỉ ra cột nào gây ra bất thường.

Vì vậy, hệ thống cần thêm bước feature contribution.

Mục tiêu của bước này là trả lời câu hỏi:

> Dòng này bất thường do cột nào?

Ví dụ:

```text
Dòng A bị phát hiện là anomaly.

Sau khi so sánh với các bản ghi tương tự:
- category bình thường
- quantity bình thường
- price lệch mạnh

→ Cột nghi ngờ: price
```

Bước này giúp hệ thống có khả năng giải thích tốt hơn, thay vì chỉ báo chung chung rằng một dòng dữ liệu bị bất thường.

---

## 9. Vai trò của KNN

KNN trong đồ án không được dùng như KNN classifier có giám sát.

KNN được dùng theo nghĩa **Nearest Neighbors**, tức là tìm các bản ghi sạch tương tự với bản ghi đang xét.

Tuy nhiên, theo định hướng hiện tại, KNN **không dùng để gợi ý sửa dữ liệu số**.

KNN chỉ được dùng để gợi ý cho các cột categorical/text có ngữ nghĩa rõ ràng:

```text
category
payment_method
shopping_mall
```

Ví dụ:

```text
payment_method bị thiếu
→ tìm các giao dịch tương tự
→ đa số hàng xóm có payment_method = Credit Card
→ suggested_value = Credit Card
```

Với các cột numeric như:

```text
age
quantity
price
unit_price
```

hệ thống chỉ phát hiện lỗi và báo cáo, không tự động gợi ý sửa thành một con số cụ thể.

---

## 10. Nguyên tắc xử lý dữ liệu số

Một nguyên tắc quan trọng của hệ thống là:

> Không dùng KNN để tự động gợi ý sửa các giá trị số.

Lý do là dữ liệu số thường không có ngữ nghĩa đủ chắc chắn để khẳng định phải sửa thành một giá trị cụ thể.

Ví dụ:

```text
category = Books
quantity = 1
price = 5000
```

Hệ thống có thể phát hiện đây là anomaly, nhưng không nên tự động sửa `price` thành một số khác.

Output hợp lý là:

```text
column_name = price
issue_type = anomaly
current_value = 5000
suggested_value = NULL
recommended_action = manual_review
reason = Price is anomalous compared with similar transactions.
```

Cách xử lý này giúp tránh việc hệ thống “bịa” ra một con số sửa lỗi không có đủ cơ sở nghiệp vụ.

---

## 11. Issue schema thống nhất

Mỗi lỗi được phát hiện sẽ được xuất ra theo một schema thống nhất.

Schema đề xuất:

```text
issue_id
row_id
column_name
issue_type
current_value
suggested_value
confidence
severity
severity_score
reason
source_method
recommended_action
can_auto_fix
created_at
```

Ý nghĩa:

| Trường             | Ý nghĩa                           |
| ------------------ | --------------------------------- |
| issue_id           | Mã lỗi                            |
| row_id             | Mã dòng dữ liệu                   |
| column_name        | Cột bị lỗi                        |
| issue_type         | missing, invalid hoặc anomaly     |
| current_value      | Giá trị hiện tại                  |
| suggested_value    | Giá trị gợi ý nếu có              |
| confidence         | Độ tin cậy                        |
| severity           | Mức độ nghiêm trọng               |
| reason             | Lý do phát hiện lỗi               |
| source_method      | Phương pháp phát hiện             |
| recommended_action | Hành động đề xuất                 |
| can_auto_fix       | Có cho phép tự động sửa hay không |
| created_at         | Thời điểm phát hiện               |

Schema này giúp dễ lưu kết quả vào PostgreSQL và dễ sinh báo cáo.

---

## 12. Confidence và Severity

### 12.1 Confidence

Confidence thể hiện mức độ tin cậy của kết quả phát hiện hoặc gợi ý.

Với categorical recommendation bằng KNN:

```text
confidence = số hàng xóm đồng thuận / tổng số hàng xóm
```

Ví dụ 5 hàng xóm gần nhất có `payment_method`:

```text
Credit Card
Credit Card
Cash
Credit Card
Debit Card
```

Gợi ý là `Credit Card`, xuất hiện 3/5 lần:

```text
confidence = 3 / 5 = 0.6
```

Với invalid do rule rõ ràng, confidence có thể là 1.0 vì lỗi được xác định trực tiếp bằng luật.

---

### 12.2 Severity

Severity thể hiện mức độ nghiêm trọng của lỗi.

Ví dụ:

| Lỗi                      | Severity    |
| ------------------------ | ----------- |
| `payment_method` missing | medium      |
| `quantity = -5`          | high        |
| `price` anomaly          | medium/high |
| `invoice_no` missing     | high        |

Severity giúp người dùng ưu tiên xử lý các lỗi quan trọng trước.

---

## 13. Cơ chế apply fixes

Hệ thống không tự động sửa toàn bộ dữ liệu.

Các chế độ xử lý dự kiến:

```text
--report
--apply-fixes --mode conservative
--apply-fixes --mode auto
```

Trong đó:

- `--report`: chỉ quét lỗi và xuất báo cáo.
- `conservative`: chỉ sửa các lỗi có confidence cao và thuộc cột được phép recommend.
- `auto`: tự động áp dụng các gợi ý hợp lệ.
- Numeric data không được auto-fix.

Các cột được phép auto-fix chỉ gồm:

```text
category
payment_method
shopping_mall
```

Các cột số như `age`, `quantity`, `price`, `unit_price` luôn đưa về manual review nếu có lỗi.

---

## 14. Tích hợp PostgreSQL

Dataset e-commerce phù hợp để tích hợp vào PostgreSQL vì có cấu trúc dạng bảng rõ ràng.

Thay vì chỉ dùng một bảng chính, đồ án sẽ thiết kế cơ sở dữ liệu theo hướng chuẩn hóa thành **4 bảng nghiệp vụ**:

```text
customers
products
shopping_malls
transactions
```

Trong đó:

- `transactions` là bảng fact trung tâm.
- `customers`, `products`, `shopping_malls` là các bảng dimension cung cấp ngữ cảnh cho giao dịch.

Thiết kế này giúp:

- Dễ mô hình hóa quan hệ khóa chính, khóa ngoại trong PostgreSQL.
- Phù hợp hơn với cách trình bày ERD và thiết kế database của đồ án.
- Giúp feature engineering rõ ràng hơn khi join dữ liệu từ nhiều chiều ngữ cảnh.
- Tạo điều kiện để AI phát hiện anomaly theo từng nhóm như `category`, `mall`, `age_group`.

### 14.1 Schema PostgreSQL đề xuất

Schema được chia thành 3 lớp:

- `dimension/fact tables`: `customers`, `products`, `shopping_malls`, `transactions`
- `staging table`: `staging_customer_shopping_raw`
- `data cleaning tables`: `cleaning_runs`, `detected_issues`, `fix_recommendations`, `cleaning_actions`, `dataset_profile`, `fixed_transactions`

Thiết kế này cho phép:

- Import dữ liệu thô vào staging trước khi chuẩn hóa.
- Chuyển dữ liệu sạch sang mô hình e-commerce chuẩn hóa.
- Lưu vết toàn bộ quá trình phát hiện lỗi, gợi ý sửa và áp dụng fix.

### 14.2 SQL CREATE TABLE

File SQL tạo schema được đặt tại:

```text
sql/postgresql_schema.sql
```

File này bao gồm:

- Định nghĩa 4 bảng e-commerce chính.
- Ràng buộc `PRIMARY KEY`, `FOREIGN KEY`, `CHECK`.
- Một số index cơ bản cho bảng `transactions`.
- Các bảng phục vụ data cleaning và audit.

### 14.3 Script import dữ liệu

Script import được đặt tại:

```text
scripts/import_ecommerce_data.py
```

Script này thực hiện:

- Đọc file Excel nguồn.
- Chuẩn hóa tên cột.
- Suy ra feature như `unit_price`, `age_group`, `invoice_month`, `day_of_week`.
- Tách dữ liệu thành 4 bảng `customers`, `products`, `shopping_malls`, `transactions`.
- Xuất ra các file CSV trung gian để nạp vào PostgreSQL bằng `COPY`.

Sau khi dữ liệu đã nằm trong PostgreSQL, CLI của pipeline có thể đọc trực tiếp từ schema e-commerce bằng config:

```text
configs/ecommerce_config.yaml
```

Ví dụ chạy:

```bash
python -m app.cli \
  --source postgres \
  --connection-uri postgresql://user:password@localhost:5432/dbname \
  --config configs/ecommerce_config.yaml \
  --report
```

Các bảng output của hệ thống vẫn giữ riêng:

```text
detected_issues
fix_recommendations
dataset_profile
fixed_transactions
```

Về lâu dài, hệ thống có thể mở rộng theo hướng:

```text
staging_transactions
clean_transactions
detected_issues
cleaning_logs
```

Với dữ liệu lớn, hệ thống không nhất thiết quét toàn bộ database bằng Python mỗi lần. Có thể tối ưu bằng:

- PostgreSQL constraints.
- Staging table.
- Incremental scan.
- Batch processing.
- Index hoặc partial index.
- Trigger cho các rule đơn giản.

Như vậy, phần rule-based có thể được đẩy xuống tầng cơ sở dữ liệu để tăng hiệu năng, còn AI tập trung vào anomaly detection.

---

## 15. Có cần label hay không?

Isolation Forest và KNN trong hệ thống không cần label để huấn luyện.

Tuy nhiên, label vẫn cần thiết để đánh giá hệ thống.

Cách làm:

```text
clean_data
→ inject missing / invalid / anomaly
→ dirty_data + dirty_labels
→ run pipeline
→ detected_issues
→ compare detected_issues with dirty_labels
```

Label không đưa vào model train. Label chỉ dùng để đánh giá kết quả phát hiện.

Các metric đánh giá:

```text
precision
recall
f1-score
```

Trong đó:

- Precision cho biết trong các lỗi hệ thống báo, bao nhiêu lỗi là đúng.
- Recall cho biết trong các lỗi thật sự tồn tại, hệ thống phát hiện được bao nhiêu.
- F1-score cân bằng giữa precision và recall.

---

## 16. Đồ án có phải manual tool không?

Đồ án không phải manual tool thuần túy.

Hệ thống có sử dụng AI ở phần phát hiện dữ liệu bất thường và phân tích các bản ghi theo ngữ cảnh.

Tuy nhiên, hệ thống cũng không cố dùng AI cho mọi loại lỗi. Các lỗi rõ ràng như missing và invalid được xử lý bằng rule-based validation để đảm bảo tính chính xác và khả năng giải thích.

Có thể định vị hệ thống là:

> **Hybrid AI-assisted data cleaning system**

Trong đó:

```text
Rule-based → xử lý lỗi rõ ràng
Isolation Forest → phát hiện anomaly
KNN → hỗ trợ gợi ý categorical/text
Manual review → xử lý numeric anomaly
```

---

## 17. Ưu tiên thiết kế

Thứ tự ưu tiên của hệ thống:

```text
1. Explainability
2. Trustworthy fixes
3. Recall
4. Speed
```

Giải thích:

- **Explainability**: hệ thống phải giải thích được tại sao một dòng bị lỗi.
- **Trustworthy fixes**: không sửa dữ liệu bừa, đặc biệt là numeric data.
- **Recall**: cố gắng phát hiện nhiều lỗi, nhưng không đánh đổi quá mạnh với false positive.
- **Speed**: tối ưu sau khi pipeline đúng và đáng tin cậy.

---

## 18. Kết luận

Đồ án được định hướng là một hệ thống **AI-assisted data cleaning** cho dữ liệu trong cơ sở dữ liệu.

Hệ thống kết hợp rule-based và AI để xử lý các loại lỗi khác nhau:

- Missing và invalid được xử lý bằng rule-based validation.
- Anomaly được phát hiện bằng Isolation Forest.
- KNN được dùng để hỗ trợ gợi ý cho dữ liệu categorical/text.
- Numeric anomaly chỉ được báo cáo và yêu cầu manual review.

Cách tiếp cận hybrid này phù hợp với bài toán làm sạch dữ liệu thực tế, vì vừa đảm bảo tính tin cậy, vừa khai thác được khả năng phát hiện bất thường của AI.
