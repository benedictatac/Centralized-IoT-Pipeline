# the simulator's fleet, clock, generators and builder are pure functions, so none of these tests need a broker, database or Redis

import random
from datetime import timedelta
import pytest
from src.models.baseModel import Device, DeviceType
from src.simulator.builder import build_payload, build_topic
from src.simulator.clock import SimulatedClock
from src.simulator.fleet import load_fleet
from src.simulator.generators import ANOMALY_GENERATORS, generate_value, thermostat_normal
from src.utilities import ranges
from tests.unit_tests.conftest import DAYTIME

#region members

SEED = 42
DRAWS = 1000
DAY_HOUR = 14.0
NIGHT_HOUR = 3.0

#every normal range a device type can produce, an anomaly has to fall outside all of them
NORMAL_RANGES = {
    DeviceType.THERMOSTAT: [ranges.DAY_TEMP_C, ranges.NIGHT_TEMP_C],
    DeviceType.SPEAKER: [ranges.SPEAKER_NORMAL_DB],
    DeviceType.CAMERA: [ranges.CAMERA_NORMAL_KMH],
}

#endregion


#stands in for time.monotonic, so the test decides exactly how much real time has passed
class FakeTimeSource:
    def __init__(self, start: float = 100.0):
        self.current = start

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def in_range(value: float, value_range: tuple[float, float]) -> bool:
    low, high = value_range
    return low <= value <= high


#region testCases

def test_load_fleet_returns_five_unique_uuid4_devices():
    fleet = load_fleet()

    assert len(fleet) == 5
    assert len({entry.device_id for entry in fleet}) == 5
    assert all(entry.device_id.version == 4 for entry in fleet)


def test_thermostat_normal_during_day_stays_in_day_range():
    rng = random.Random(SEED)

    for _ in range(DRAWS):
        assert in_range(thermostat_normal(DAY_HOUR, rng), ranges.DAY_TEMP_C)


def test_thermostat_normal_at_night_stays_in_night_range():
    rng = random.Random(SEED)

    for _ in range(DRAWS):
        assert in_range(thermostat_normal(NIGHT_HOUR, rng), ranges.NIGHT_TEMP_C)


@pytest.mark.parametrize("device_type", list(ANOMALY_GENERATORS), ids=lambda device_type: device_type.value)
def test_anomaly_values_fall_outside_normal_ranges(device_type):
    rng = random.Random(SEED)
    anomaly = ANOMALY_GENERATORS[device_type]

    for _ in range(DRAWS):
        value = anomaly(DAY_HOUR, rng)
        assert not any(in_range(value, normal) for normal in NORMAL_RANGES[device_type])


def test_generate_value_with_rate_0_is_never_anomalous():
    rng = random.Random(SEED)

    for device_type in DeviceType:
        for _ in range(DRAWS):
            _, is_anomaly = generate_value(device_type, DAY_HOUR, 0.0, rng)
            assert is_anomaly is False


@pytest.mark.parametrize("device_type", [DeviceType.THERMOSTAT, DeviceType.SPEAKER, DeviceType.CAMERA],
                         ids=lambda device_type: device_type.value)
def test_generate_value_with_rate_1_is_always_anomalous(device_type):
    rng = random.Random(SEED)

    for _ in range(DRAWS):
        _, is_anomaly = generate_value(device_type, DAY_HOUR, 1.0, rng)
        assert is_anomaly is True


#a 0/1 state has no out-of-range value, so even rate 1 can't make a LightBulb anomalous
def test_generate_value_with_rate_1_never_flags_lightbulb():
    rng = random.Random(SEED)

    for _ in range(DRAWS):
        _, is_anomaly = generate_value(DeviceType.LIGHTBULB, DAY_HOUR, 1.0, rng)
        assert is_anomaly is False


#the processor validates with the same model, so a payload that passes here is one the pipeline accepts
def test_build_payload_passes_device_validation_for_every_fleet_entry():
    for entry in load_fleet():
        device = Device.model_validate_json(build_payload(entry, 1.0, DAYTIME))

        assert device.device_id == entry.device_id
        assert device.device_type == entry.device_type
        assert device.timestamp == DAYTIME
        assert device.readings[0].value == 1.0


def test_build_topic_starts_with_home_and_ends_with_device_id():
    for entry in load_fleet():
        topic = build_topic(entry)

        assert topic.startswith("home/")
        assert topic.endswith(str(entry.device_id))


def test_simulated_clock_at_speed_720_moves_12_minutes_per_real_second():
    fake_time = FakeTimeSource()
    clock = SimulatedClock(speed=720, start=DAYTIME, time_source=fake_time)

    fake_time.advance(1)

    assert clock.now() == DAYTIME + timedelta(minutes=12)

#endregion testCases
