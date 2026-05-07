from app.config import PipelineConfig, ColumnRule


class RuleEngine:
    """
    Quản lý rule của từng column.
    File này giúp các detector/recommender không phải truy cập trực tiếp config quá nhiều.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config

    def get_rule(self, column_name: str) -> ColumnRule:
        if column_name not in self.config.rules:
            raise KeyError(f"Column '{column_name}' does not exist in config rules.")
        return self.config.rules[column_name]

    def get_required_columns(self) -> list[str]:
        return [
            col for col, rule in self.config.rules.items()
            if rule.required
        ]

    def get_detection_columns(self) -> list[str]:
        return [
            col for col, rule in self.config.rules.items()
            if rule.use_for_detection and col != self.config.id_column
        ]

    def get_recommendation_columns(self) -> list[str]:
        return [
            col for col, rule in self.config.rules.items()
            if rule.use_for_recommendation and col != self.config.id_column
        ]