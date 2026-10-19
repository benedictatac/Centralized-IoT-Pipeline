import numpy as np
from src.pipeline.detector import Detector
from src.pipeline.random_data_generator import random_data_generator


# Following this dashboard from my own mind
#DASHBOARD
#============================================================
# Total Readings: 
# Normal: 
# Anomalies: 
# Hour Range
# Temp Range:
# Score Range: 
#=============================================================
# Idx       Hour        Temp        Score       Status
#loop here so that anomalies are at the top and normal after



def create_dashboard(X: np.ndarray, scores: np.ndarray, labels: np.ndarray) -> None: 
    total_len = len(X)
    anomaly_count = int(np.sum(labels == -1)) #total anomaly count
    normal_count = int(np.sum(labels == 1))

    print("DashBoard for data inspection")
    print("*"*50)
    print(f"Total number of samples     : {total_len}") 
    print(f"Total number of anomalies   : {anomaly_count}")
    print(f"Total number of normal      : {normal_count}")
    print(f"Hour Range                  : {X[:,0].min():.2f} - {X[:,0].max():.2f}") # we want all rows for only the first column this basically will have the hours from morning to night
    print(f"Temperature Range           : {X[:,1].min():.2f} - {X[:,1].max():.2f}")
    print(f"Score Range                 : {scores.min():.2f} - {scores.max():.2f}") # scores is 1D, one score per sample
def main(sample_size =50) -> None:
    X = random_data_generator()

    detector = Detector()
    detector.train(X)

    sample_we_want = X[:sample_size]
    scores = detector.score(sample_we_want) # train() returns None, score() returns the anomaly scores
    labels = detector.predict(sample_we_want)
    create_dashboard(sample_we_want, scores, labels) # same rows the scores/labels were computed on


if __name__ == '__main__':
    main()
    
