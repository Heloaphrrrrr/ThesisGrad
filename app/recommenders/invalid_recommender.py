import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from app.config import PipelineConfig
from app.utils import clamp_confidence
from .base_recommender import BaseRecommender


class InvalidRecommender(BaseRecommender):
    _MIN_STRING_SIMILARITY = 0.45

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._categorical_model_cache = {}

    def _get_categorical_model(self, column_name: str, allowed_values: list):
        cache_key = (column_name, tuple(map(str, allowed_values)))
        cached = self._categorical_model_cache.get(cache_key)
        if cached is not None:
            return cached

        canonical_values = [str(value) for value in allowed_values]
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            lowercase=True,
            strip_accents="unicode",
        )
        allowed_vectors = vectorizer.fit_transform(canonical_values)
        model = NearestNeighbors(
            n_neighbors=min(self.config.knn_neighbors, len(canonical_values)),
            metric="cosine",
        )
        model.fit(allowed_vectors)

        cached = (canonical_values, vectorizer, model)
        self._categorical_model_cache[cache_key] = cached
        return cached

    def _recommend_categorical(
        self,
        value,
        column_name: str,
        allowed_values: list,
    ) -> tuple:
        normalized_value = str(value).strip()
        if not normalized_value:
            return None, 0.0

        canonical_values, vectorizer, model = self._get_categorical_model(
            column_name,
            allowed_values,
        )
        query_vector = vectorizer.transform([normalized_value])
        distances, indices = model.kneighbors(query_vector)

        best_similarity = max(0.0, 1.0 - float(distances[0][0]))
        if best_similarity < self._MIN_STRING_SIMILARITY:
            return None, 0.0

        second_similarity = 0.0
        if len(distances[0]) > 1:
            second_similarity = max(0.0, 1.0 - float(distances[0][1]))

        # A clear gap from the second-nearest canonical value increases confidence.
        separation = max(0.0, best_similarity - second_similarity)
        confidence = clamp_confidence(best_similarity + 0.25 * separation)
        suggested = allowed_values[int(indices[0][0])]
        return suggested, confidence

    def recommend(self, value, column_name: str) -> tuple:
        rule = self.config.rules[column_name]

        if rule.dtype == "numeric":
            if pd.notna(value):
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    return None, 0.0

                if rule.min_value is not None and numeric_value < rule.min_value:
                    return rule.min_value, 1.0

                if rule.max_value is not None and numeric_value > rule.max_value:
                    return rule.max_value, 1.0

        if rule.dtype == "categorical" and rule.allowed_values:
            if value is not None and pd.notna(value):
                return self._recommend_categorical(
                    value=value,
                    column_name=column_name,
                    allowed_values=rule.allowed_values,
                )

            return None, 0.0

        return None, 0.0
