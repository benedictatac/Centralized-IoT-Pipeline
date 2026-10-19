# simulator entry point: every tick it publishes one reading per fleet device to the broker
# run from the repo root so .env is found: python -m src.simulator.main --help

import csv
import random
import time
from datetime import datetime
from pathlib import Path
from uuid import UUID
import click
from src.models.baseModel import DeviceType
from src.simulator.builder import build_payload, build_topic
from src.simulator.clock import SimulatedClock
from src.simulator.fleet import load_fleet
from src.simulator.generators import generate_value
from src.simulator.publisher import create_publisher, publish
from src.utilities import ranges


#region anomaly log
# ground truth: every anomaly the simulator injects is written here,
# later compared with the alerts the detector raised to measure how many it caught

#main.py -> simulator -> src -> repo root, built from this module's location like FLEET_PATH
ANOMALY_LOG_PATH = Path(__file__).resolve().parents[2] / "simulator_anomalies.csv"
ANOMALY_LOG_COLUMNS = ["timestamp", "device_id", "device_type", "value"]


class AnomalyLog:

    def __init__(self, path: Path = ANOMALY_LOG_PATH):
        #append so earlier runs are kept, the header is only written when the file is new or empty
        is_new = not path.exists() or path.stat().st_size == 0
        self.file = open(path, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        if is_new:
            self.writer.writerow(ANOMALY_LOG_COLUMNS)
            self.file.flush()

    #timestamp should be the simulated time sent in the message, so log rows match the stored readings
    def record(self, timestamp: datetime, device_id: UUID, device_type: DeviceType, value: float) -> None:
        self.writer.writerow([timestamp.isoformat(), str(device_id), device_type.value, value])
        #flush every row so nothing is lost if the simulator is stopped with Ctrl+C
        self.file.flush()

    def close(self) -> None:
        self.file.close()

    #lets the main loop use "with AnomalyLog() as log:" so the file is always closed
    def __enter__(self) -> "AnomalyLog":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
#endregion anomaly log


#region main loop

#often enough to see the simulated time moving, without flooding the console
PROGRESS_EVERY_TICKS = 10
#how long the shutdown waits for the broker to confirm the last message
PUBLISH_WAIT_TIMEOUT = 5


@click.command()
@click.option("--interval", type=click.FloatRange(min=0.01), default=1.0, show_default=True,
              help="Real seconds between ticks.")
@click.option("--anomaly-rate", type=click.FloatRange(0, 1), default=ranges.DEFAULT_ANOMALY_RATE, show_default=True,
              help="Chance that a message is anomalous.")
@click.option("--speed", type=click.FloatRange(min=1), default=720.0, show_default=True,
              help="Simulated seconds per real second.")
@click.option("--duration", type=click.FloatRange(min=0), default=0.0, show_default=True,
              help="Real seconds to run, 0 runs until Ctrl+C.")
@click.option("--seed", type=int, default=None,
              help="Fixed seed for repeatable runs.")
def run(interval: float, anomaly_rate: float, speed: float, duration: float, seed: int | None) -> None:
    """Publish simulated smart home readings to the MQTT broker."""
    fleet = load_fleet()
    clock = SimulatedClock(speed)
    #one generator for the whole run, so the same --seed always produces the same values
    rng = random.Random(seed)
    client = create_publisher()

    sent = 0
    anomalies = 0
    #latest MQTTMessageInfo, the shutdown waits on it so the last messages aren't lost
    last_info = None
    #monotonic like the clock, so a system clock change can't cut the run short or stretch it
    real_start = time.monotonic()
    tick = 0

    run_length = "until Ctrl+C" if duration == 0 else f"{duration}s"
    print(f"Simulating {len(fleet)} devices: interval {interval}s, speed x{speed}, "
          f"anomaly rate {anomaly_rate}, duration {run_length}, seed {seed}")

    with AnomalyLog() as log:
        try:
            while duration == 0 or time.monotonic() - real_start < duration:
                #read once per tick, so every device in the tick shares the same timestamp and day/night range
                timestamp = clock.now()
                hour = clock.hour()

                for entry in fleet:
                    value, is_anomaly = generate_value(entry.device_type, hour, anomaly_rate, rng)
                    payload = build_payload(entry, value, timestamp)
                    last_info = publish(client, build_topic(entry), payload)
                    sent += 1

                    if is_anomaly:
                        log.record(timestamp, entry.device_id, entry.device_type, value)
                        anomalies += 1

                tick += 1
                if tick % PROGRESS_EVERY_TICKS == 0:
                    print(f"[{timestamp:%Y-%m-%d %H:%M} simulated] sent {sent}, anomalies {anomalies}")

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nCtrl+C received, stopping the simulator...")
        finally:
            #loop_stop() alone does not guarantee queued messages were sent, so wait for the broker to confirm the last one
            if last_info is not None:
                try:
                    last_info.wait_for_publish(timeout=PUBLISH_WAIT_TIMEOUT)
                    if not last_info.is_published():
                        print(f"Broker did not confirm the last message within {PUBLISH_WAIT_TIMEOUT}s, it may be lost")
                #raised instead of waiting when the last publish failed outright, e.g. the connection was down
                except (ValueError, RuntimeError) as e:
                    print(f"Last message could not be confirmed: {e}")
            #disconnect ends the network thread, loop_stop then waits for it to finish
            client.disconnect()
            client.loop_stop()

    #LightBulbs can never be anomalous, so the actual rate sits below --anomaly-rate (1 of 5 devices: 5% x 4/5 = 4%)
    rate = anomalies / sent if sent else 0.0
    print(f"Sent {sent} messages, injected {anomalies} anomalies, actual rate {rate:.2%}")
    print(f"Anomaly log: {ANOMALY_LOG_PATH}")
#endregion main loop


if __name__ == "__main__":
    run()
