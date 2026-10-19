# Bug-Fix Report: Centralized IoT Pipeline

**Date:** 2026-10-18
**Result:** test suite went from **0 tests run (collection aborted with 2 errors)** → **23 passed**.

Each fix below follows the same layout:

- **What:** the problem, in one sentence
- **Where:** the file(s) and code that changed
- **Why:** the root cause, and what actually went wrong at runtime
- **How:** the change itself, with a before/after
- **Verified:** how the fix was proven to work

---

## Summary

| # | Problem | Files changed |
|---|---------|---------------|
| 1 | The MQTT listener was handed the wrong callback, so nothing was ever stored | `src/pipeline/entry_point.py` |
| 2 | Enum objects were sent to `String` database columns | `src/pipeline/storage.py` |
| 3 | Enums broke `json.dumps`, and the Redis password was never used | `src/pipeline/cache.py`, `docker-compose.yml` |
| 4 | Naive and timezone-aware datetimes were mixed | `src/models/baseModel.py`, `src/models/database.py`, **new** `alembic/versions/5363ecee3e70_use_timezone_aware_timestamps.py` |
| 5 | Test fixtures and assertions were broken | `tests/unit_tests/*`, `tests/integration_tests/*`, `pyproject.toml`, **new** `tests/unit_tests/test_cache.py`, **new** `tests/integration_tests/__init__.py` |
| 6 | The dashboard crashed while printing | `src/pipeline/dashboard.py` |
| 7 | Small cleanups | `src/pipeline/Helper_Config.py`, `docker/mosquitto/data/randomData.json`, `src/pipeline/detector.py` |

### Things you need to run yourself

These steps touch your live services, so they were **not** run for you:

1. **Apply the timezone migration (fix 4)** to Postgres:
   ```bash
   alembic upgrade head
   ```
2. **Recreate the Redis container (fix 3)** so it starts with the new `--requirepass` flag:
   ```bash
   docker compose up -d redis
   ```
3. **Install the new dev dependency (fix 5).** It's already installed in `venv`; CI picks it up automatically from `pyproject.toml`:
   ```bash
   pip install -e ".[dev]"
   ```

---

## 1. `entry_point.py`: the wrong function was handed to the listener

**What:** Messages were received and validated, but never written to Postgres or Redis.

**Where:** `src/pipeline/entry_point.py`, inside `main()`, where the `Client` is constructed.

**Why:** `main()` defines a closure called `handle_message`. It validates the message *and then* schedules `store_device()` on the asyncio loop. But the client was given `process_message` instead:

```
paho network thread                      asyncio loop
───────────────────                      ────────────
on_message(msg)
  └─ message_handler(msg)
       BEFORE: process_message(msg) ──► returns a Device to paho … which throws it away ✗
       AFTER:  handle_message(msg)
                 ├─ process_message(msg)  → Device
                 └─ run_coroutine_threadsafe(store_device(device), loop) ──► Postgres + Redis ✓
```

`process_message` only *returns* a `Device`. paho ignores callback return values, so every valid message was silently dropped. No error was ever printed, which is why this bug was hard to spot.

**How:**

```python
# before
client = Client(settings.mqtt_host, settings.mqtt_port, PLACEHOLDER_CLIENT_ID,process_message, settings)

# after
# handle_message (not process_message) so the validated device actually gets stored + cached
client = Client(settings.mqtt_host, settings.mqtt_port, PLACEHOLDER_CLIENT_ID, handle_message, settings)
```

`handle_message` is also the right callback because of threading. paho calls `on_message` from its own background thread (`loop_start()`). `asyncio.run_coroutine_threadsafe` is the safe way to hand async work from that thread to the main event loop.

**Verified:** A scratch harness patched `Client`, ran `main()`, and called the captured handler from a separate thread (the way paho does). Output: `handler passed to Client: handle_message` and `devices that reached store_device: 1`.

---

## 2. `storage.py`: enums were sent to the database instead of text

**What:** Inserting a device or a reading failed, because Python `Enum` objects were passed to `String` columns.

**Where:** `src/pipeline/storage.py`, in `upsert_device()` (`device_type`) and `insert_readings()` (`metric`, `unit`).

**Why:** The Pydantic model stores `device.device_type` as `DeviceType.THERMOSTAT`, an enum *object*, not the string `"Thermostat"`. The SQLAlchemy columns are `String`, and `String` doesn't know how to convert an enum. So the object reaches the database driver unchanged, and the driver rejects it:

```
(sqlite3.ProgrammingError) Error binding parameter 3: type 'DeviceType' is not supported
```

asyncpg/Postgres fails the same way: it expects a `str` and gets a `DeviceType`.

**How:** Use each enum's `.value` at the storage boundary:

```python
# before
new_device = DeviceDB(device_id = device.device_id, device_type = device.device_type, device_name = device.device_name)
...
metric=reading.metric,
unit=reading.unit,

# after
# .value -> the column is a String, so store "Thermostat" and not the DeviceType enum object
new_device = DeviceDB(device_id = device.device_id, device_type = device.device_type.value, device_name = device.device_name)
...
metric=reading.metric.value,
unit=reading.unit.value,
```

*Alternative considered:* adding `model_config = ConfigDict(use_enum_values=True)` to the Pydantic models. That would make the *whole app* see strings instead of enums, which breaks existing comparisons like `device.device_type == DeviceType.CAMERA`. Converting only where data leaves Python for the database keeps the enums' type safety everywhere else.

**Verified:** I added `test_store_event_saves_enums_as_text`, which runs `store_event()` against a real SQL driver (in-memory SQLite). It fails on the original code and passes on the fixed code. The stored row reads back as `'Thermostat' / 'Temperature' / 'Celsius'`.

---

## 3. `cache.py`: enums broke JSON, and the Redis password was missing

### 3a. Enum objects broke `json.dumps`

**What:** `upsert_data()` crashed before anything reached Redis.

**Where:** `src/pipeline/cache.py`, in `upsert_data()`.

**Why:** `reading.model_dump()` (default `mode="python"`) keeps the `Metric` and `Unit` enum objects, and the standard `json` module can't serialize them:

```
TypeError: Object of type Metric is not JSON serializable
```

**How:** Pydantic v2's `mode="json"` dumps every field as a JSON-safe type, so enums become their string values:

```python
# before
value = json.dumps([reading.model_dump() for reading in device.readings])

# after
#mode="json" turns the Metric/Unit enums into their string values, json.dumps can't serialize Enum objects
value = json.dumps([reading.model_dump(mode="json") for reading in device.readings])
```

Cached value now: `[{"metric": "Temperature", "unit": "Celsius", "value": 21.5}]`

### 3b. The Redis password was never used

**What:** `Settings` loads `RDS_PASSWORD`, but the Redis client never passed it. The Redis container didn't require a password either.

**Where:** `src/pipeline/cache.py` (the client) and `docker-compose.yml` (the server).

**Why:** Both sides had to change together:

- If only the *client* sends a password, Redis rejects it with `ERR AUTH <password> called without any password configured for the default user`, because the server has no password set.
- If only the *server* requires one, the client gets `NOAUTH Authentication required`.

**How:**

```python
# cache.py, before
conn = redis.Redis(host = settings.rds_host, port = settings.rds_port,decode_responses=True)

# cache.py, after
#password authenticates as the "default" redis user (set by --requirepass in docker-compose.yml)
conn = redis.Redis(host = settings.rds_host, port = settings.rds_port, password = settings.rds_password, decode_responses=True)
```

```yaml
# docker-compose.yml, before
command: redis-server --appendonly yes
# docker-compose.yml, after
command: redis-server --appendonly yes --requirepass ${RDS_PASSWORD}
```

`--requirepass` sets the password for Redis's built-in `default` user. That's why only `password=` is passed, not `username=settings.rds_user`. Sending a custom username would fail unless you also created that user with a Redis ACL.

**Side note (encoding):** `cache.py` was saved in Windows-1252, not UTF-8. Its em dash (`—`) in the comment on line 7 was byte `0x97`, which blocked editing the file. The file was converted to UTF-8; the character and the CRLF line endings are unchanged.

**Verified:**
- The connection pool now carries the password from settings.
- `docker compose config --quiet` validates the compose file.
- The new test `test_upsert_data_writes_readings_as_json` mocks Redis and checks the key, the JSON value and the 24h expiry. It fails on the original code and passes on the fixed code.

---

## 4. Timezones: naive and timezone-aware datetimes were mixed

**What:** One part of the code used timezone-*aware* datetimes and another used *naive* ones. They met at the database, where the driver can't mix them.

**Where:**

| Location | Before | Problem |
|---|---|---|
| `storage.py` → `updated_at = datetime.now(timezone.utc)` | **aware** | written into a `TIMESTAMP` (naive) column |
| `database.py` → all `DateTime` columns | **naive** (`TIMESTAMP WITHOUT TIME ZONE`) | can't hold an offset |
| `Device.timestamp` from MQTT payloads | **either**, depending on the payload | `"…Z"` gives aware; `"2026-10-31 23:59:00"` gives naive |
| test fixtures → `datetime.now()` | **naive** | didn't match what the app produces |

**Why:** This is what asyncpg's encoders actually do (from `asyncpg/pgproto/codecs/datetime.pyx`):

- **`TIMESTAMP` column + aware datetime** → `obj - pg_epoch_datetime` raises
  `TypeError: can't subtract offset-naive and offset-aware datetimes`.
  So **every repeat message from a known device crashed** in `upsert_device`. The same happened for any payload whose timestamp had an offset.
- **`TIMESTAMPTZ` column + naive datetime** → `obj.astimezone(utc)` treats the naive value as **the machine's local time**, so it's silently shifted by the local UTC offset. That's why changing only the columns would not have been enough.

**How:** The whole app now uses one convention: **timezone-aware UTC**.

1. **Model.** `src/models/baseModel.py` normalizes every incoming timestamp. Naive values are assumed to already be UTC; values with an offset are converted to UTC:
   ```python
   #every timestamp leaves this model as timezone-aware UTC so it matches the TIMESTAMPTZ columns
   #naive timestamps (no offset in the payload) are assumed to already be UTC
   @field_validator("timestamp")
   @classmethod
   def normalize_to_utc(cls, value: datetime) -> datetime:
       if value.tzinfo is None:
           return value.replace(tzinfo=timezone.utc)
       return value.astimezone(timezone.utc)
   ```
   | Payload timestamp | Stored as |
   |---|---|
   | `2026-10-18 10:00:00` | `2026-10-18T10:00:00+00:00` |
   | `2026-10-18T10:00:00Z` | `2026-10-18T10:00:00+00:00` |
   | `2026-10-18T12:00:00+02:00` | `2026-10-18T10:00:00+00:00` |

2. **Database columns.** In `src/models/database.py`, `DateTime` became `DateTime(timezone=True)` (`TIMESTAMPTZ`) for `devices.created_at`, `devices.updated_at`, `readings.timestamp` and `readings.created_at`. `storage.py`'s existing `datetime.now(timezone.utc)` is now correct as written.

3. **Migration.** The new file `alembic/versions/5363ecee3e70_use_timezone_aware_timestamps.py` (revises `b7bf0dddacb1`) converts the live tables:
   ```sql
   ALTER TABLE devices  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING "created_at" AT TIME ZONE 'UTC';
   ALTER TABLE devices  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING "updated_at" AT TIME ZONE 'UTC';
   ALTER TABLE readings ALTER COLUMN timestamp  TYPE TIMESTAMP WITH TIME ZONE USING "timestamp"  AT TIME ZONE 'UTC';
   ALTER TABLE readings ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING "created_at" AT TIME ZONE 'UTC';
   ```
   `USING … AT TIME ZONE 'UTC'` tells Postgres to read the existing naive rows as UTC (the Postgres Docker image's default timezone), so existing data isn't shifted. `downgrade()` reverses it.

4. **Test fixtures and `randomData.json`** now use aware UTC values (see fixes 5 and 7).

**Contract to keep in mind:** devices that send a timestamp *without* an offset are treated as sending UTC. If a device sends local time, it should include the offset (for example `+02:00`).

**Verified:**
- `alembic upgrade b7bf0dddacb1:5363ecee3e70 --sql` renders the four statements above (offline, no database touched), and the downgrade renders cleanly too.
- The models' Postgres DDL now emits `TIMESTAMP WITH TIME ZONE`.
- New tests `test_naive_timestamp_is_treated_as_utc` and `test_offset_timestamp_is_converted_to_utc` pass.
- The migration has **not** been run against your live database; see "Things you need to run yourself".

---

## 5. Tests: the fixtures and assertions themselves were broken

**What:** The suite couldn't even be collected. Once that was fixed, several tests asserted against the wrong values or exercised the wrong code.

**Where and why**, problem by problem:

| # | File | Problem | Fix |
|---|------|---------|-----|
| a | `integration_tests/conftest.py` | `@pytest.fixture(session = "session")`: `session` isn't a valid argument, so **collection crashed** with `TypeError` | `@pytest_asyncio.fixture` (it's an `async def` generator) |
| b | `integration_tests/conftest.py` | `db_session(async_engine)` asked for a fixture named `async_engine`, but the engine fixture was called `mock_engine` | Renamed the engine fixture to `async_engine` and removed the unused `async_session_factory` |
| c | `integration_tests/` | No `__init__.py`, so pytest registered its conftest as the top-level module **`conftest`**. `from conftest import …` in the unit tests then loaded the *integration* conftest. This was the second collection crash. | Added `tests/integration_tests/__init__.py` |
| d | `unit_tests/conftest.py` | `FILE_PATH` was built with `parent.parent` = `tests/`, so it pointed at `tests/docker/...`, which doesn't exist | `parent.parent.parent` = repo root |
| e | `unit_tests/conftest.py` | `create_device_obj` called `device.delete()` at teardown. Pydantic models have no `.delete()` (they aren't DB rows), so it raised `AttributeError` | Plain `return device` |
| f | `unit_tests/conftest.py` + `test_pydantic_base_model.py` | The fixture built its device with a fresh `uuid.uuid4()` / `datetime.now()`, and the test compared against *another* fresh `uuid4()` / `now()`. These can never be equal, so `test_create_valid_device` could never pass. | One set of fixed constants (`DEVICEID`, `DAYTIME`, …) lives in `conftest.py`. The fixture builds from them and the test imports them, so the asserts didn't need to change. |
| g | `test_pydantic_base_model.py` | `test_invalid_readingunit` changed `["value"]`, so it was a copy of `test_invalid_readingvalue` and `unit` was never tested | Changed to `["unit"]` |
| h | `test_pydantic_base_model.py` | `import docker.mosquitto.data` imported a data folder as a namespace package. It's useless, and it breaks if the `docker` pip package is installed. There were also several other unused imports. | Removed |
| i | `unit_tests/conftest.py` | `mock_engine` / `mock_db_session` were `async def` with a **sync** engine and session. The storage functions `await session.execute(...)`, which a sync session can't do. | Async engine (`sqlite+aiosqlite:///:memory:`) + `AsyncSession`, via `@pytest_asyncio.fixture` |
| j | `test_storage.py` | Four separate bugs: (1) `@pytest.mark.asyncio` on a plain `def`; (2) fixtures **called directly** (`mock_engine()`), which pytest forbids; (3) `upsert_device(...)` not awaited, so the test checked a coroutine object; (4) the sync session problem from (i) | Rewritten as `async def` tests that *request* fixtures as arguments and `await` the calls. Also added two regression tests for fix 2. |
| k | `test_endpoints.py` | Called `/events?device_id=…`, but `/events` has no `device_id` parameter and ignores it. The `device_id` assertion only passed because the mock returned that ID anyway. | Calls `/events/{device_id}`, the route that actually filters by device |
| l | `test_endpoints.py`, `test_mqtt_processor.py` | `from tests.unit_tests.conftest import mock_client / valid_payload`. pytest discovers conftest fixtures automatically, and importing them registers a second copy | Removed the imports |
| m | `unit_tests/conftest.py` | `datetime.now()` (naive) in `valid_payload` and `mock_client` | `datetime.now(timezone.utc)` / the fixed `DAYTIME` |
| n | `pyproject.toml` | Both conftests use `sqlite+aiosqlite`, but `aiosqlite` was never declared, so CI couldn't run them | Added `aiosqlite >= 0.20.0` to `[dev]` |

**Why the DB fixtures are function-scoped:** With pytest-asyncio, each test runs on its own event loop by default. A *session-scoped* async engine would be created on a different loop than the tests that use it, and aiosqlite fails with "attached to a different loop" errors. An in-memory SQLite database takes milliseconds to create, so each test simply gets a brand-new one. Isolation comes for free, and nothing needs to be rolled back.

**Example (j), before and after:**

```python
# before
@pytest.mark.asyncio
def test_upsert_device(create_device_obj):
    engine = mock_engine()                       # calling a fixture directly
    session = mock_db_session(engine)
    device_serialized = upsert_device(create_device_obj, session)   # never awaited
    assert isinstance(device_serialized, DeviceDB)                  # it's a coroutine

# after
@pytest.mark.asyncio
async def test_upsert_device(create_device_obj, mock_db_session):
    device_serialized = await upsert_device(create_device_obj, mock_db_session)
    assert isinstance(device_serialized, DeviceDB)
    assert device_serialized.device_type == "Camera" # enum value, not DeviceType.CAMERA
```

**New tests added** (as regression tests for the other fixes):

| Test | Guards fix |
|---|---|
| `test_storage.py::test_store_event_saves_enums_as_text` | 2 |
| `test_storage.py::test_store_event_twice_updates_existing_device` | 2 (the update branch of `upsert_device`) |
| `test_cache.py::test_upsert_data_writes_readings_as_json` (new file) | 3 |
| `test_pydantic_base_model.py::test_naive_timestamp_is_treated_as_utc` | 4 |
| `test_pydantic_base_model.py::test_offset_timestamp_is_converted_to_utc` | 4 |

**Verified:** `pytest` → **23 passed**. As a check, I temporarily restored the original `storage.py` and `cache.py`: all 4 storage/cache tests failed, and they passed again with the fixed files.

---

## 6. `dashboard.py`: crashes in the printout

**What:** `python -m src.pipeline.dashboard` crashed before printing anything useful.

**Where:** `src/pipeline/dashboard.py`, in `create_dashboard()` and `main()`.

**Why:** There were four bugs; the first three crash or would crash, the fourth printed wrong numbers:

| Line (before) | Problem |
|---|---|
| `score_total = np.hstack()` | `hstack` needs arrays to stack → `TypeError: hstack() missing 1 required positional argument: 'tup'`. The result wasn't used anyway. |
| `{[1,].min():.2f}` | `[1,]` is a Python **list** literal, not `scores` → `AttributeError: 'list' object has no attribute 'min'` |
| `scores = detector.train(X)` | `train()` returns `None`, so `scores` was `None` and `scores.min()` would crash next. `scores[1,]` would only have picked one score anyway. |
| `create_dashboard(X, scores, labels)` | `X` has 400 rows, but `labels` only covers the first 50. "Total samples: 400" didn't match the anomaly and normal counts (which summed to 50). |

**How:**

```python
# before
score_total = np.hstack()
...
print(f"Score Range                 : {[1,].min():.2f} - {scores[1,].max():.2f}")
...
scores = detector.train(X)
labels = detector.predict(sample_we_want)
create_dashboard(X, scores, labels)

# after
print(f"Score Range                 : {scores.min():.2f} - {scores.max():.2f}") # scores is 1D, one score per sample
...
scores = detector.score(sample_we_want) # train() returns None, score() returns the anomaly scores
labels = detector.predict(sample_we_want)
create_dashboard(sample_we_want, scores, labels) # same rows the scores/labels were computed on
```

The redundant second `detector.train(X)` call went away because that line now calls `score()`.

**Verified:**

```
DashBoard for data inspection
**************************************************
Total number of samples     : 50
Total number of anomalies   : 4
Total number of normal      : 46
Hour Range                  : 0.65 - 23.97
Temperature Range           : 17.22 - 94.53
Score Range                 : 0.42 - 0.72
```

*Not done:* the per-row table (`Idx  Hour  Temp  Score  Status`, anomalies first) from the planning comment at the top of the file. It was never implemented, so it wasn't a crash, and it's left for you.

---

## 7. Small cleanups

### 7a. `Helper_Config.py`

**What:** `CreateValidDevice()` could never succeed, and the file carried six unused imports.

**Where:** `src/pipeline/Helper_Config.py`

**Why:**
- It passed `device_uuid=`, but the field is `device_id`. Pydantic ignores unknown keyword arguments by default, so the UUID was **silently dropped**, and validation then failed with `device_id: Field required`.
- `from multiprocessing import Value` (an accidental IDE auto-import), `enum`, `pydantic`, `UUID, uuid4`, `config.Settings` and four model names were imported but never used. This module is imported by `entry_point.py` and `alembic/env.py`, so dead imports here make those files look like they depend on more than they do.

**How:**
```python
# before
from multiprocessing import Value
from src.models.baseModel import BaseModel, Device, DeviceType, Metric, Unit, Reading
from uuid import UUID, uuid4
import enum
import pydantic
import json
from pathlib import Path
from config import Settings
...
device = Device(device_type = deviceType, device_uuid = deviceUUID, ...)

# after
from src.models.baseModel import Device, Reading
import json
from pathlib import Path
...
#field is device_id: pydantic silently ignored device_uuid and then failed with "device_id Field required"
device = Device(device_type = deviceType, device_id = deviceUUID, ...)
```
Nothing else imported those names (checked with a repo-wide search), so removing them is safe.

### 7b. `docker/mosquitto/data/randomData.json`

**What:** The sample payload failed validation with 3 errors.

**Why:** It used enum **names** (`"CAMERA"`, `"TEMPERATURE"`, `"CELSIUS"`), but Pydantic validates against enum **values** (`"Camera"`, `"Temperature"`, `"Celsius"`). It also had a `"status": "ACTIVE"` field that `Device` doesn't define (the old `DeviceStatus` enum is commented out), and a timestamp with no timezone.

**How:**
```jsonc
// before
"device_type": "CAMERA",            "timestamp": "2026-10-31 23:59:00",   "status": "ACTIVE",
"metric": "TEMPERATURE", "unit":  "CELSIUS"

// after
"device_type": "Camera",            "timestamp": "2026-10-31T23:59:00Z",  (status removed)
"metric": "Temperature", "unit": "Celsius"
```

**Verified:** `test_device_creation_with_jsonFile_valid` passes. Before fix 5d it never reached this file; after 5d it failed on the data until this fix.

### 7c. `contamination` in `detector.py`

**What:** IsolationForest was told to expect 10% anomalies, but the training data contains about 5%.

**Where:** `src/pipeline/detector.py`, the default `contamination` in `Detector.__init__`.

**Why:** `contamination` isn't a sensitivity knob. It tells IsolationForest *what share of the data to flag*: the model puts its threshold so that exactly that fraction is labelled `-1`. `random_data_generator()` (seeded with 42) produces **19 hot readings (50–100 °C) out of 400 = 4.75%**. The comment said "10% based on data numbers", but the 10% (`p=[0.9, 0.1]`) only applies to the 200 *day* rows, not the whole dataset. At 0.1 the model had to flag 40 readings, so 21 of them were normal.

**How:**
```python
# before
def __init__(self, contamination: float = 0.1, random_state: int = 42): #setting contamination rate to 10% based on data numbers

# after
#contamination = expected share of anomalies. random_data_generator() makes 19 hot readings out of 400 (~4.75%),
#so 0.05 matches the data; 0.1 forced the model to flag ~20 extra normal readings as anomalies
def __init__(self, contamination: float = 0.05, random_state: int = 42):
```

**Verified** (trained and predicted on the full 400 samples):

| contamination | flagged | real anomalies caught | false alarms |
|---|---|---|---|
| 0.10 (before) | 40 | 19 / 19 | **21** |
| 0.05 (after)  | 20 | 19 / 19 | **1** |

---

## Noticed but not changed (outside the 7 items)

These are things I noticed while fixing the above. I left them alone to keep the change set to what you asked for:

- **`tests/test_connections.py`** (manual smoke script). It reads the Redis host from `RDS_NAME` instead of `RDS_HOST`, its default port is `6739` (typo for `6379`), and it sends no password, so it now fails `AUTH` because Redis requires one (fix 3).
- **`cache.py`**: `set()` followed by `expire()` takes two round trips, and the key has no expiry between them. `await conn.set(key, value, ex=86400)` does both atomically.
- **Your in-progress `AlertDB`** (uncommitted changes in `database.py`, left as you had them) has no Alembic migration yet. Generate one after `5363ecee3e70` so it chains correctly.
- **Schema drift:** migration `b7bf0dddacb1` creates `devices.device_name` as `NOT NULL`, but the model says `nullable=True`.
- **`ReadingResponse.alerts = Field(..., nullable=True)`** causes the one remaining pytest warning (a Pydantic deprecation; `nullable` isn't a `Field` argument in v2).
- **`random_data_generator()`** is annotated `-> ArrayType` (from the `array` module), but it returns an `np.ndarray`. Also, `day_hours_outliers` aren't outliers: they're drawn from the same 8–22 h range. The real outliers come from `day_mask`.
- **`entry_point.py`**: several unused imports (including `sqlalchemy.orm.session`, which the local `session` variable shadows), an unused `created_client` variable, and no `loop_stop()` / `disconnect()` on Ctrl+C.
- **`upsert_device`** doesn't update `device_name` when a known device sends a new name.
- **Redis password visibility:** passing `--requirepass ${RDS_PASSWORD}` on the command line makes it visible in `docker inspect`. That's fine for local development; for production, put it in a mounted `redis.conf` or use Docker secrets.
