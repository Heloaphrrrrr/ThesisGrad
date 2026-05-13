from __future__ import annotations

from pathlib import Path
import yaml

from app.config import PipelineConfig, ColumnRule, build_default_config


def load_config_from_yaml(path: str | None) -> PipelineConfig:
    if path is None:
        return build_default_config()

    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    model_cfg = raw.get("model", {})
    columns_cfg = raw.get("columns", {})

    rules = {}

    for col, rule_data in columns_cfg.items():
        rules[col] = ColumnRule(
            dtype=rule_data["dtype"],
            required=rule_data.get("required", False),
            min_value=rule_data.get("min_value"),
            max_value=rule_data.get("max_value"),
            allowed_values=rule_data.get("allowed_values"),
            use_for_detection=rule_data.get("use_for_detection", True),
            use_for_recommendation=rule_data.get("use_for_recommendation", True),
            severity_if_missing=rule_data.get("severity_if_missing", "medium"),
            severity_if_invalid=rule_data.get("severity_if_invalid", "high"),
        )

    return PipelineConfig(
        table_name=raw["table_name"],
        id_column=raw["id_column"],
        rules=rules,
        contamination=model_cfg.get("contamination", 0.08),
        n_estimators=model_cfg.get("n_estimators", 200),
        max_samples=model_cfg.get("max_samples", 256),
        random_state=model_cfg.get("random_state", 42),
        knn_neighbors=model_cfg.get("knn_neighbors", 5),
        feature_z_threshold=model_cfg.get("feature_z_threshold", 2.5),
        conservative_confidence_threshold=model_cfg.get(
            "conservative_confidence_threshold", 0.85
        ),
    )