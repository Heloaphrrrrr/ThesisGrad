from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class IssueRecord:
    row_id: Any
    column_name: str
    issue_type: str  # "missing", "invalid", "anomaly"
    current_value: Any
    anomaly_score: Optional[float]
    suggested_value: Any
    reason: str
    source_method: str


@dataclass
class ModelResult:
    row_id: Any
    is_anomaly: int
    raw_score: float
    decision_score: float