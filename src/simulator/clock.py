# a clock that runs faster than real time
# the detector uses hour of day as an input, so a real-time run would only ever cover an hour or so.
# at speed 720, 1 real minute = 12 simulated hours, so a few real minutes cover full days and nights

import time
from datetime import datetime, timedelta, timezone
from typing import Callable


class SimulatedClock:

    def __init__(self, speed: float, start: datetime | None = None, time_source: Callable[[], float] = time.monotonic):
        if speed <= 0:
            raise ValueError(f"speed must be greater than 0, got {speed}")
        self.speed = speed

        #start defaults to "now" at construction time (a datetime.now() default argument would be frozen at import)
        if start is None:
            start = datetime.now(timezone.utc)
        #same rule as Device.timestamp: naive is assumed to be UTC, anything else is converted to UTC
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        self.start = start.astimezone(timezone.utc)

        #monotonic never jumps when the computer's clock changes (NTP sync, manual change, DST),
        #so the elapsed real time is always correct. time_source can be swapped for a fake in tests
        self.time_source = time_source
        self.real_start = time_source()

    def now(self) -> datetime:
        elapsed_real = self.time_source() - self.real_start
        return self.start + timedelta(seconds=elapsed_real * self.speed)

    #decimal hour of the simulated time, e.g. 14.5 for 2:30 PM, same format as column 0 of random_data_generator()
    def hour(self) -> float:
        current = self.now()
        midnight = current.replace(hour=0, minute=0, second=0, microsecond=0)
        return (current - midnight).total_seconds() / 3600
