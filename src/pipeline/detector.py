import numpy as np
from sklearn.ensemble import IsolationForest
from src.pipeline.random_data_generator import random_data_generator


class Detector:

    #contamination = expected share of anomalies. random_data_generator() makes 19 hot readings out of 400 (~4.75%),
    #so 0.05 matches the data; 0.1 forced the model to flag ~20 extra normal readings as anomalies
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.is_trained = False

    def train(self, X: np.ndarray = None) -> None: #train the input array taken from the random data generator 
        if X is None: # array in this case is empty
            X = random_data_generator() # we populate it 
        self.model.fit(X)   #if it is not empty, we fit
                            # fit in this case does not modify the data, used only for training data
        self.is_trained = True   # this would mean it is then trained 


    #we give the readings a score
    def score(self, readings) -> np.ndarray: #outputs an np array
        if not self.is_trained:
            raise RuntimeError("Detector must be trained before scoring readings.")

        readings = np.asarray(readings) 
        if readings.ndim == 1: #if the array is 1 dimensional, we 
            readings = readings.reshape(1, -1) # convert into a 2D matrix with 1 row and automatically calculated columns 

        ##
        #after using reshape
        #calculates the amount of columns in that 1D turning it into 2D
        #readings = readings.reshape(1, -1)
        # print(readings)        # Output: [[21.5, 22.0, 21.8, 22.3, 21.9]]
        # print(readings.shape)  # Output: (1, 5)
        # print(readings.ndim)   # Output: 2
        ##

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

