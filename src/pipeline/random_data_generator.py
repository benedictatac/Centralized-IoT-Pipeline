import numpy as np

# Set seed for reproducible data generation
np.random.seed(42)

# 1. Day Readings (200 samples) 
# Hours: 8 to 22 
# Temp: 20°C to 24°C
day_hours = np.random.uniform(8.0, 22.0, 200)
day_temps = np.random.uniform(20.0, 24.0, 200)
X_day = np.column_stack((day_hours, day_temps))

# 2. Night Readings (200 samples)
# Hours: 22 to 24 OR 0 to 8 
# Temp: 17°C to 20°C
night_hours = np.random.choice(
    [np.random.uniform(22.0, 24.0), np.random.uniform(0.0, 8.0)], 
    size=200
)
night_temps = np.random.uniform(17.0, 20.0, 200)
X_night = np.column_stack((night_hours, night_temps))

# 3. Combined Feature Matrix X
X = np.vstack((X_day, X_night))

# Shuffle to break block ordering
np.random.shuffle(X)

# Ready for model.fit(X) 
# Column 0: Time of Day (Float hours, e.g., 14.5 = 2:30 PM)
# Column 1: Temperature Value (°C)
print(f"X shape: {X.shape}")
print("First 5 samples [Hour, Temp]:")
print(X[:5])