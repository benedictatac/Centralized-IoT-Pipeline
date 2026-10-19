# single source of truth for every normal and anomalous value range
# the training data (random_data_generator) and the simulator both read from here,
# so changing a range once updates both and they can never drift apart

#region time of day (hours, 0-24)
DAY_START_HOUR = 8.0
DAY_END_HOUR = 22.0 # night is DAY_END_HOUR -> 24 and 0 -> DAY_START_HOUR
#endregion

#region thermostat (Celsius), each range is (low, high)
DAY_TEMP_C = (20.0, 24.0)
NIGHT_TEMP_C = (17.0, 20.0)
ANOMALY_TEMP_C = (50.0, 100.0)
#endregion

#region speaker (Decibel)
SPEAKER_NORMAL_DB = (30.0, 70.0)
SPEAKER_ANOMALY_DB = (110.0, 130.0)
#endregion

#region camera (kmPerHour)
CAMERA_NORMAL_KMH = (0.0, 5.0)
CAMERA_ANOMALY_KMH = (60.0, 120.0)
#endregion

# share of readings that should be anomalous, matches the Detector's contamination
DEFAULT_ANOMALY_RATE = 0.05
