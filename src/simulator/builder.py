# turns a fleet entry, a value and a timestamp into the MQTT payload and its topic

from datetime import datetime
from src.models.baseModel import Device, Reading
from src.simulator.fleet import FleetDevice


#built through the same Device model the processor validates with, so the simulator and the pipeline share one contract.
#a bad payload raises pydantic.ValidationError here, at the source, instead of being silently dropped by the processor
def build_payload(entry: FleetDevice, value: float, timestamp: datetime) -> str:
    reading = Reading(metric=entry.metric, unit=entry.unit, value=value)

    device = Device(
        device_type=entry.device_type,
        device_id=entry.device_id,
        device_name=entry.device_name,
        timestamp=timestamp,
        readings=[reading],
    )
    #model_dump_json writes enums as their values ("Thermostat"), the UUID as a string and the timestamp as ISO 8601
    return device.model_dump_json()


#e.g. home/Thermostat/62301949-c0f9-4afa-abe9-fc198a41b813, matched by the listener's "home/#" subscription
def build_topic(entry: FleetDevice) -> str:
    return f"home/{entry.device_type.value}/{entry.device_id}"
