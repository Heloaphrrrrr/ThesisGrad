from abc import ABC, abstractmethod


class BaseRecommender(ABC):
    @abstractmethod
    def recommend(self, *args, **kwargs):
        raise NotImplementedError