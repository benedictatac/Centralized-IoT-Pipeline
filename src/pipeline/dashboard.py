import numpy as np

from src.pipeline.detector import Detector
from src.pipeline.random_data_generator import random_data_generator


def render_dashboard(X: np.ndarray, scores: np.ndarray, labels: np.ndarray) -> None:
    total = len(X)
    anomaly_count = int(np.sum(labels == -1))
    normal_count = total - anomaly_count

    print("=" * 60)
    print("ANOMALY DETECTION DASHBOARD")
    print("=" * 60)
    print(f"Total readings : {total}")
    print(f"Normal         : {normal_count} ({normal_count / total:.1%})")
    print(f"Anomalies      : {anomaly_count} ({anomaly_count / total:.1%})")
    print(f"Hour  range    : {X[:, 0].min():.2f} - {X[:, 0].max():.2f}")
    print(f"Temp  range    : {X[:, 1].min():.2f} - {X[:, 1].max():.2f}")
    print(f"Score range    : {scores.min():.3f} - {scores.max():.3f}")
    print("-" * 60)
    print(f"{'Idx':>4} {'Hour':>7} {'Temp':>7} {'Score':>8}  Status")
    print("-" * 60)

    order = np.argsort(scores)[::-1]  # most anomalous first
    for i in order:
        is_anomaly = labels[i] == -1
        status = "ANOMALY" if is_anomaly else "normal"
        marker = "*" if is_anomaly else " "
        print(f"{i:>4} {X[i, 0]:>7.2f} {X[i, 1]:>7.2f} {scores[i]:>8.3f}  {marker} {status}")

    print("=" * 60)


def main(sample_size: int = 50) -> None:
    X = random_data_generator()

    detector = Detector()
    detector.train(X)

    sample = X[:sample_size]
    scores = detector.score(sample)
    labels = detector.predict(sample)

    render_dashboard(sample, scores, labels)


if __name__ == "__main__":
    main()
