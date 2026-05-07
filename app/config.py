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

    issue_output_columns: List[str] = field(default_factory=lambda: [
        "row_id",
        "column_name",
        "issue_type",
        "current_value",
        "anomaly_score",
        "suggested_value",
        "reason",
        "source_method",
    ])


def build_default_config() -> PipelineConfig:
    return PipelineConfig(
        table_name="employees",
        id_column="employee_id",
        rules={
            "employee_id": ColumnRule(
                dtype="id",
                required=True,
                use_for_detection=False,
                use_for_recommendation=False,
            ),
            "age": ColumnRule(
                dtype="numeric",
                required=True,
                min_value=18,
                max_value=65,
            ),
            "salary": ColumnRule(
                dtype="numeric",
                required=True,
                min_value=3_000_000,
                max_value=200_000_000,
            ),
            "years_experience": ColumnRule(
                dtype="numeric",
                required=True,
                min_value=0,
                max_value=45,
            ),
            "department": ColumnRule(
                dtype="categorical",
                required=True,
                allowed_values=["HR", "IT", "Finance", "Marketing", "Sales", "Operations"],
            ),
            "city": ColumnRule(
                dtype="categorical",
                required=True,
                allowed_values=["HCM", "HN", "DN", "CT", "HP"],
            ),
            "performance_score": ColumnRule(
                dtype="numeric",
                required=True,
                min_value=0,
                max_value=100,
            ),
        },
    )