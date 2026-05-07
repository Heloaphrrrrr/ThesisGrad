from sklearn.preprocessing import LabelEncoder


class SimpleLabelEncoder:
    def __init__(self):
        self.encoder = LabelEncoder()

    def fit(self, series):
        self.encoder.fit(series.astype(str))

    def transform(self, series):
        return self.encoder.transform(series.astype(str))

    def fit_transform(self, series):
        return self.encoder.fit_transform(series.astype(str))