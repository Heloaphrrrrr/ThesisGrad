import pandas as pd
from pathlib import Path


labels_path = Path("outputs/seeded_dirty_labels.csv")
detected_path = Path("outputs/detected_issues.csv")
report_output_path = Path("outputs/evaluation_report.csv")


labels = pd.read_csv(labels_path)
detected = pd.read_csv(detected_path)


# Chuẩn hóa tên cột cho labels
labels = labels.rename(columns={
    "row_id": "row_id",
    "column_name": "column_name",
    "issue_type": "issue_type",
})


# Key để so sánh một lỗi
label_keys = labels[["row_id", "column_name", "issue_type"]].drop_duplicates()
detected_keys = detected[["row_id", "column_name", "issue_type"]].drop_duplicates()


label_keys["is_true_issue"] = 1
detected_keys["is_detected"] = 1


merged = label_keys.merge(
    detected_keys,
    on=["row_id", "column_name", "issue_type"],
    how="outer"
)


tp = ((merged["is_true_issue"] == 1) & (merged["is_detected"] == 1)).sum()
fn = ((merged["is_true_issue"] == 1) & (merged["is_detected"] != 1)).sum()
fp = ((merged["is_true_issue"] != 1) & (merged["is_detected"] == 1)).sum()


precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = (
    2 * precision * recall / (precision + recall)
    if (precision + recall) > 0
    else 0
)


rows = [
    {"metric": "true_positive", "value": tp},
    {"metric": "false_positive", "value": fp},
    {"metric": "false_negative", "value": fn},
    {"metric": "precision", "value": round(precision, 4)},
    {"metric": "recall", "value": round(recall, 4)},
    {"metric": "f1_score", "value": round(f1, 4)},
]


# Đánh giá theo từng loại lỗi
for issue_type in sorted(set(labels["issue_type"]).union(set(detected["issue_type"]))):
    l = label_keys[label_keys["issue_type"] == issue_type]
    d = detected_keys[detected_keys["issue_type"] == issue_type]

    l = l.copy()
    d = d.copy()

    l["is_true_issue"] = 1
    d["is_detected"] = 1

    m = l.merge(
        d,
        on=["row_id", "column_name", "issue_type"],
        how="outer"
    )

    tp_i = ((m["is_true_issue"] == 1) & (m["is_detected"] == 1)).sum()
    fn_i = ((m["is_true_issue"] == 1) & (m["is_detected"] != 1)).sum()
    fp_i = ((m["is_true_issue"] != 1) & (m["is_detected"] == 1)).sum()

    precision_i = tp_i / (tp_i + fp_i) if (tp_i + fp_i) > 0 else 0
    recall_i = tp_i / (tp_i + fn_i) if (tp_i + fn_i) > 0 else 0
    f1_i = (
        2 * precision_i * recall_i / (precision_i + recall_i)
        if (precision_i + recall_i) > 0
        else 0
    )

    rows.extend([
        {"metric": f"{issue_type}_tp", "value": tp_i},
        {"metric": f"{issue_type}_fp", "value": fp_i},
        {"metric": f"{issue_type}_fn", "value": fn_i},
        {"metric": f"{issue_type}_precision", "value": round(precision_i, 4)},
        {"metric": f"{issue_type}_recall", "value": round(recall_i, 4)},
        {"metric": f"{issue_type}_f1_score", "value": round(f1_i, 4)},
    ])


report = pd.DataFrame(rows)
report.to_csv(report_output_path, index=False)

print("=== EVALUATION COMPLETED ===")
print(report)
print(f"Saved to: {report_output_path}")