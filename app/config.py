from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ColumnRule:
    dtype: str  # "id", "numeric", "categorical", "date"
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    use_for_detection: bool = True
    use_for_recommendation: bool = True
    severity_if_missing: str = "medium"
    severity_if_invalid: str = "high"


@dataclass
class PipelineConfig:
    table_name: str
    id_column: str
    rules: Dict[str, ColumnRule]

    contamination: float = 0.08
    n_estimators: int = 200
    max_samples: int = 256
    random_state: int = 42

    knn_neighbors: int = 5
    feature_z_threshold: float = 2.5

    conservative_confidence_threshold: float = 0.85

    issue_output_columns: List[str] = field(default_factory=lambda: [
        "issue_id",
        "row_id",
        "column_name",
        "issue_type",
        "current_value",
        "suggested_value",
        "confidence",
        "severity",
        "severity_score",
        "reason",
        "source_method",
        "can_auto_fix",
        "created_at",
    ])


def build_default_config() -> PipelineConfig:
    return PipelineConfig(
        table_name="bank_transactions",
        id_column="transaction_id",
        rules={
            "transaction_id": ColumnRule(
                dtype="id",
                required=True,
                use_for_detection=False,
                use_for_recommendation=False,
            ),
            "date": ColumnRule(
                dtype="date",
                required=True,
                use_for_detection=False,
                use_for_recommendation=False,
                severity_if_missing="high",
            ),
            "domain": ColumnRule(
                dtype="categorical",
                required=True,
                allowed_values=[
                    "RESTAURANT",
                    "INVESTMENTS",
                    "RETAIL",
                    "INTERNATIONAL",
                    "PUBLIC",
                    "MEDICAL",
                    "EDUCATION",
                ],
                severity_if_missing="medium",
                severity_if_invalid="medium",
            ),
            "location": ColumnRule(
                dtype="categorical",
                required=True,
                severity_if_missing="medium",
                severity_if_invalid="medium",
            ),
            "value": ColumnRule(
                dtype="numeric",
                required=True,
                min_value=0,
                severity_if_missing="high",
                severity_if_invalid="high",
            ),
            "transaction_count": ColumnRule(
                dtype="numeric",
                required=True,
                min_value=0,
                severity_if_missing="high",
                severity_if_invalid="high",
            ),
            "avg_transaction_value": ColumnRule(
                dtype="numeric",
                required=False,
                min_value=0,
                use_for_detection=True,
                use_for_recommendation=True,
            ),
        },
    )