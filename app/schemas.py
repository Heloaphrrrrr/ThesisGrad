from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Optional
import uuid


@dataclass
class IssueRecord:
    issue_id: str
    row_id: Any
    column_name: str
    issue_type: str  # missing | invalid | anomaly
    current_value: Any
    suggested_value: Any
    confidence: float
    severity: str  # low | medium | high | critical
    severity_score: float
    reason: str
    source_method: str
    can_auto_fix: bool
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


def make_issue_id() -> str:
    return str(uuid.uuid4())


@dataclass
class DatasetProfile:
    row_count: int
    column_count: int
    missing_rate_per_column: dict
    unique_count_per_column: dict
    numeric_min: dict
    numeric_max: dict