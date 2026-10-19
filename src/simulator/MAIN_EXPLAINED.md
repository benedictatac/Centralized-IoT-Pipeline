# `main.py` in plain English

**File:** `src/simulator/main.py`

## In one sentence

`main.py` pretends to be a house full of smart devices. Every second, each device sends a short report to the message broker, and once in a while a report contains a weird value on purpose.

---

## The big picture: a post office

| Real thing | Post office version |
|---|---|
| **Mosquitto** (the MQTT broker) | The post office |
| **A message** (the payload) | A letter: *"I'm the Kitchen Speaker, it's 14:05, my volume is 52 dB."* |
| **The topic**, e.g. `home/Speaker/fd6dfa73-...` | The address on the envelope |
| **The pipeline** (listener) | The person who collects all mail addressed to `home/...` and files it in the database |
| **`main.py`** | The person writing and posting all the letters |

---

## The helpers it uses

`main.py` doesn't do everything itself. It uses small helpers from the other files in this folder:

| Helper | File | What it does |
|---|---|---|
| The device list | `fleet.py` + `fleet.json` | 5 pretend devices, each with a fixed ID |
| The fast clock | `clock.py` | Makes time run 720× faster: 1 real second = 12 pretend minutes |
| The value makers | `generators.py` | Picks a normal value, or sometimes a weird one |
| The letter writer | `builder.py` | Turns a value into the JSON message and its topic |
| The mailbox | `publisher.py` | Connects to the broker and sends the messages |

---

## What happens when you run it

```
 GET READY ──► REPEAT EVERY TICK ──► STOP ──► CLEAN UP ──► PRINT SUMMARY
                 (until time is up
                  or you press Ctrl+C)
```

### 1. Get ready

- Load the 5 devices.
- Start the fast clock.
- Create the random number maker. If you gave a `--seed`, it produces the same numbers every run.
- Connect to the broker under the name `iot-simulator`. It is **not** `Client-ID`, because the broker would kick the pipeline off if two clients used the same name.
- Open the anomaly log (`simulator_anomalies.csv`).
- Set both counters (`sent` and `anomalies`) to 0.

### 2. Every tick (once per `--interval` seconds)

1. **Look at the clock once.** All 5 devices in this tick share the same pretend time.
2. **For each device:**
   - make a value (normal, or weird on purpose)
   - wrap it in a message
   - send it to the broker
   - add 1 to `sent`
3. **If the value was weird on purpose:** write a line in the CSV and add 1 to `anomalies`.
4. **Every 10 ticks:** print a progress line.
5. **Sleep** until the next tick.

### 3. Stop

The loop stops when `--duration` runs out, or when you press **Ctrl+C**. Either way, it moves on to clean up. Ctrl+C is not treated as a crash.

### 4. Clean up (always happens)

1. **Wait for the last receipt.** Messages are sent by a helper running in the background. If the program quit right away, the last few messages might still be waiting to go out and would be lost. So it waits up to 5 seconds for the broker to confirm *"got it"* for the last message.
2. **Say goodbye to the broker** (`disconnect`), then **stop the background helper** (`loop_stop`).
3. **Close the CSV file.**

### 5. Print a summary

How many messages were sent, how many weird values were injected, and the actual rate.

---

## What you'll see

```
Connecting to host: 'localhost' on port: 1883
Simulating 5 devices: interval 1.0s, speed x720.0, anomaly rate 0.05, duration 60.0s, seed 42
Simulator connected to broker as 'iot-simulator'
[2026-10-19 20:58 simulated] sent 50, anomalies 2
[2026-10-19 22:58 simulated] sent 100, anomalies 3
[2026-10-20 00:58 simulated] sent 150, anomalies 4
[2026-10-20 02:58 simulated] sent 200, anomalies 5
[2026-10-20 04:58 simulated] sent 250, anomalies 6
[2026-10-20 06:59 simulated] sent 300, anomalies 9
Sent 300 messages, injected 9 anomalies, actual rate 3.00%
Anomaly log: C:\...\Centralized-IoT-Pipeline\simulator_anomalies.csv
```

Notice that the pretend time jumps **2 hours** every 10 real seconds. That's the fast clock at work.

---

## The anomaly log: the answer key

`simulator_anomalies.csv` lists every weird value the simulator injected **on purpose**. Later you can compare it with the alerts the detector raised, to see how many it caught.

```
timestamp,device_id,device_type,value
2026-10-19T20:22:20.405401+00:00,52c6ac30-8169-4ab8-b13d-5ecf78c9cedf,Thermostat,65.77
2026-10-20T04:46:53.525401+00:00,fd6dfa73-dd28-497f-be6c-eeb0f52fbac9,Speaker,116.72
```

- Each row is saved straight away, so pressing Ctrl+C never loses a row.
- New runs **add to the end** of the file. The header is only written once. Delete the file if you want a fresh answer key.

---

## Why is the rate about 4% and not 5%?

The light bulb is only **on (1)** or **off (0)**, so it has no "weird" value. That means only 4 of the 5 devices can ever be weird:

> 5% × 4/5 = **4%**

A short run can land a bit above or below that (3% in the example above). It's like rolling dice: with more messages, the rate gets closer to 4%.

---

## The options

You can change how it behaves without editing any code:

| Option | Default | In plain words |
|---|---|---|
| `--interval` | `1.0` | Real seconds between ticks (minimum 0.01) |
| `--anomaly-rate` | `0.05` | Chance a message is weird, from 0 (never) to 1 (always) |
| `--speed` | `720` | How much faster pretend time runs (minimum 1 = real time) |
| `--duration` | `0` | Real seconds to run. `0` means "until I press Ctrl+C" |
| `--seed` | none | Pick a number to get the same values every run |

Always run it **from the repo root**, so it can find your `.env` settings:

```bash
python -m src.simulator.main --help                           # list the options
python -m src.simulator.main --duration 60 --seed 42          # 1-minute demo, repeatable values
python -m src.simulator.main                                  # run until Ctrl+C
python -m src.simulator.main --anomaly-rate 0.5               # lots of weird values
python -m src.simulator.main --interval 0.1                   # 10 ticks per second
```

A bad value is refused before anything starts. For example, `--anomaly-rate 2` prints `Error: Invalid value for '--anomaly-rate': 2.0 is not in the range 0<=x<=1.`

---

## Common problems

| What you see | Why | Fix |
|---|---|---|
| `ConnectionRefusedError` right away | The broker isn't running | `docker compose up -d` |
| A settings error about missing `db_user` and similar fields | It was started outside the repo root, so `.env` wasn't found | `cd` to the repo root first |
| The same `--seed` gives the same values but different times | The pretend clock always starts at *right now* | Expected. Only the values repeat |
| Timestamps in the future | The pretend clock runs ahead of real time | Expected. 60 real seconds = 12 pretend hours |

---

## Tiny glossary

- **Tick:** one round in which every device sends one message.
- **Anomaly:** a value that is weird on purpose, e.g. a thermostat reading 80 °C.
- **Broker:** the post office (Mosquitto) that passes messages along.
- **Topic:** the address a message is sent to, e.g. `home/Thermostat/<device id>`.
- **QoS 1:** "send it with a receipt". The broker confirms every message it gets.
- **Seed:** a starting number for the random number maker. The same seed gives the same "random" values.
