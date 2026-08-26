import numpy as np
from sklearn.ensemble import IsolationForest

from src.pipeline.random_data_generator import random_data_generator


class Detector:

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.is_trained = False

    def train(self, X: np.ndarray = None) -> None:
        if X is None:
            X = random_data_generator()
        self.model.fit(X)
        self.is_trained = True

    def score(self, readings) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Detector must be trained before scoring readings.")

        readings = np.asarray(readings)
        if readings.ndim == 1:
            readings = readings.reshape(1, -1)

        # score_samples: higher = more normal, so negate for an anomaly score
        # where higher means more anomalous.
        return -self.model.score_samples(readings)

    def predict(self, readings) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Detector must be trained before predicting readings.")

        readings = np.asarray(readings)
        if readings.ndim == 1:
            readings = readings.reshape(1, -1)

        return self.model.predict(readings)  # 1 = normal, -1 = anomaly


if __name__ == '__main__':
    detector = Detector()
    detector.train()

    sample_readings = random_data_generator()[:20]
    print("Anomaly scores:", detector.score(sample_readings))

