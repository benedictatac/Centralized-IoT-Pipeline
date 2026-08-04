from src.pipeline.processor import process_message
from src.models.baseModel import Device
import pytest
import json
import uuid
from datetime import datetime


class FakeMqttMsg:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload


def make_msg(data: dict) -> FakeMqttMsg:
    payload = json.dumps(data).encode("utf-8")
    return FakeMqttMsg(topic="test/topic", payload=payload)


@pytest.fixture
def valid_payload():
    return {
        "device_id": str(uuid.uuid4()),
        "device_name": "Test Thermostat",
        "device_type": "Thermostat",
        "timestamp": datetime.now().isoformat(),
        "readings": [
            {"metric": "Temperature", "unit": "Celsius", "value": 22.5}
        ]
    }


def test_valid_json_payload(valid_payload):
    msg = make_msg(valid_payload)
    result = process_message(msg)
    assert result is not None
    assert isinstance(result, Device)


def test_missing_field_returns_none(valid_payload):
    del valid_payload["device_type"]
    msg = make_msg(valid_payload)
    result = process_message(msg)
    assert result is None


def test_invalid_metric_returns_none(valid_payload):
    valid_payload["readings"][0]["metric"] = "banana"
    msg = make_msg(valid_payload)
    result = process_message(msg)
    assert result is None


def test_invalid_unit_returns_none(valid_payload):
    valid_payload["readings"][0]["unit"] = "banana"
    msg = make_msg(valid_payload)
    result = process_message(msg)
    assert result is None


def test_random_bytes_returns_none():
    msg = FakeMqttMsg(topic="test/topic", payload=b'\x00\x01\xff\xfe')
    result = process_message(msg)
    assert result is None


def test_empty_payload_returns_none():
    msg = FakeMqttMsg(topic="test/topic", payload=None)
    result = process_message(msg)
    assert result is None


def test_invalid_json_returns_none():
    msg = FakeMqttMsg(topic="test/topic", payload=b'not valid json{{{')
    result = process_message(msg)
    assert result is None