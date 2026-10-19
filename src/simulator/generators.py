# one function per device type that returns a NORMAL reading
# every function takes the same (hour, rng) arguments so they can all be called the same way through NORMAL_GENERATORS.
# rng is passed in (instead of using the global random module) so tests can seed it and get repeatable values

import random
from typing import Callable
from src.models.baseModel import DeviceType
from src.utilities import ranges


#share of camera readings where nothing is moving
CAMERA_IDLE_PROBABILITY = 0.9


#hour matters here: 23 C is normal at 2 PM but unusual at 3 AM in the training data
def thermostat_normal(hour: float, rng: random.Random) -> float:
    if ranges.DAY_START_HOUR <= hour < ranges.DAY_END_HOUR:
        return round(rng.uniform(*ranges.DAY_TEMP_C), 2)
    return round(rng.uniform(*ranges.NIGHT_TEMP_C), 2)


#hour is unused, kept so every generator has the same signature
def lightbulb_normal(hour: float, rng: random.Random) -> float:
    return rng.choice((0.0, 1.0)) # off / on


def speaker_normal(hour: float, rng: random.Random) -> float:
    return round(rng.uniform(*ranges.SPEAKER_NORMAL_DB), 2)


#most of the time nothing moves in front of the camera, otherwise something slow like a person walking
def camera_normal(hour: float, rng: random.Random) -> float:
    if rng.random() < CAMERA_IDLE_PROBABILITY:
        return 0.0
    return round(rng.uniform(*ranges.CAMERA_NORMAL_KMH), 2)


NORMAL_GENERATORS: dict[DeviceType, Callable[[float, random.Random], float]] = {
    DeviceType.THERMOSTAT: thermostat_normal,
    DeviceType.LIGHTBULB: lightbulb_normal,
    DeviceType.SPEAKER: speaker_normal,
    DeviceType.CAMERA: camera_normal,
}


# out-of-range values, same (hour, rng) signature as the normal generators

def thermostat_anomaly(hour: float, rng: random.Random) -> float:
    return round(rng.uniform(*ranges.ANOMALY_TEMP_C), 2)


def speaker_anomaly(hour: float, rng: random.Random) -> float:
    return round(rng.uniform(*ranges.SPEAKER_ANOMALY_DB), 2)


def camera_anomaly(hour: float, rng: random.Random) -> float:
    return round(rng.uniform(*ranges.CAMERA_ANOMALY_KMH), 2)


#no LightBulb: a 0/1 state has no out-of-range value
ANOMALY_GENERATORS: dict[DeviceType, Callable[[float, random.Random], float]] = {
    DeviceType.THERMOSTAT: thermostat_anomaly,
    DeviceType.SPEAKER: speaker_anomaly,
    DeviceType.CAMERA: camera_anomaly,
}


#returns (value, is_anomaly). is_anomaly is the ground truth that goes into the anomaly log
def generate_value(device_type: DeviceType, hour: float, anomaly_rate: float, rng: random.Random) -> tuple[float, bool]:
    #always drawn (even for LightBulb), so the random sequence doesn't depend on which device types are in the fleet
    roll = rng.random()
    #rng.random() is in [0.0, 1.0): rate 0 can never be anomalous, rate 1 always is
    if roll < anomaly_rate and device_type in ANOMALY_GENERATORS:
        return ANOMALY_GENERATORS[device_type](hour, rng), True
    return NORMAL_GENERATORS[device_type](hour, rng), False
