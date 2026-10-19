# loads the fixed list of simulated devices from fleet.json

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
from src.models.baseModel import DeviceType, Metric, Unit


#built from this module's own location (not the current working directory),
#so it resolves to src/simulator/fleet.json no matter where the simulator is started from
FLEET_PATH = Path(__file__).resolve().parent / "fleet.json"


#one simulated device, holding real enums/UUID instead of the raw strings from the json
@dataclass(frozen=True)
class FleetDevice:
    device_id: UUID
    device_name: str
    device_type: DeviceType
    metric: Metric
    unit: Unit


def parse_device(entry: dict) -> FleetDevice:
    #UUID() and the enum constructors raise ValueError on anything that isn't a valid value,
    #so a typo like "Thermostatt" stops the simulator here instead of producing bad messages later
    device_id = UUID(entry["device_id"])
    #Device.device_id is UUID4, any other version would only be rejected later by the pipeline
    if device_id.version != 4:
        raise ValueError(f"device_id {device_id} is not a version 4 UUID")

    return FleetDevice(
        device_id=device_id,
        device_name=entry["device_name"],
        device_type=DeviceType(entry["device_type"]),
        metric=Metric(entry["metric"]),
        unit=Unit(entry["unit"]),
    )


def load_fleet() -> list[FleetDevice]:
    with open(FLEET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    fleet = []
    for position, entry in enumerate(data["fleetOfDevices"]):
        #name the broken entry, a bare "'Thermostatt' is not a valid DeviceType" is hard to trace back
        where = f"fleet.json entry {position} ({entry.get('device_name', 'no name')})"
        try:
            fleet.append(parse_device(entry))
        except KeyError as e:
            raise ValueError(f"{where}: missing field {e}") from e
        except ValueError as e:
            raise ValueError(f"{where}: {e}") from e
    return fleet
