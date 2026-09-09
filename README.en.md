# SmartEvacGuide — AI-Driven Evacuation Route Guidance for Buildings in Disaster

> Submission to the 1st IoT Platform Developer Challenge (AI x IoT Open Platform Challenge)
> Team **IoT 요정단** · Sejong University, SESLAB

[한국어 → README.md](README.md)

An oneM2M-based IoT service that analyzes sensor and camera data in real time to **detect fires, earthquakes and structural collapse early, and guide occupants along the safest evacuation route** given their location and current crowding. On-device AI on a Raspberry Pi makes the decisions; results flow through a tinyIoT (oneM2M) server to both an Android app and a Unity digital twin.

---

## My Contribution

I designed and built the **entire AI system (`ai/`)** on my own.

| Area | Work |
|---|---|
| Disaster detection | Composite temperature + CO₂ thresholding, vibration (earthquake) sensor integration |
| Crowd analysis | Custom YOLOv8n training (100 epochs) and a real-time inference pipeline on Raspberry Pi |
| Route optimization | Q-Learning policy training with a hand-designed evacuation simulator and reward function |
| System integration | oneM2M resource design on tinyIoT, sensor polling / result upload, MJPEG streaming server |

`mobile-app/` and `unity-digital-twin/` are teammates' deliverables, included to show the full system.

---

## Architecture

```
   [ Field Hardware ]              [ oneM2M Platform ]            [ Applications ]

  Arduino UNO R4 WiFi                                              ┌──────────────┐
   ├ DHT (temp/humidity) ┐                                     ┌──▶│  Mobile App  │
   ├ CO2 sensor        ──┤                tinyIoT (IN-CSE)     │   │  (Android)   │
   └ Vibration sensor  ──┤             ┌────────────────────┐  │   └──────────────┘
                         ├── HTTP ────▶│ AE: SmartEvacGuide │──┤
  Raspberry Pi           │             │  ├ Sensors   (CNT) │  │   ┌──────────────┐
   ├ Pi Camera           │             │  ├ Result    (CNT) │  └──▶│ Unity        │
   └ On-Device AI ───────┘             │  └ Detection (CNT) │      │ Digital Twin │
       (YOLOv8 + Q-Learning)           └────────────────────┘      └──────────────┘
```

**Pipeline (2-second polling loop)**

1. Arduino publishes temperature, humidity, CO₂ and vibration readings to the tinyIoT `Sensors` containers.
2. The Raspberry Pi AI reads `Sensors/*/la` and classifies the disaster state.
3. Pi Camera frames are run through YOLOv8n to count people in real time.
4. `(disaster, crowd, location)` is looked up in the learned Q-table to pick the optimal route (1–6).
5. Results are posted back to the `Result` and `Detection` containers, which the app and digital twin poll.

---

## AI System (`ai/`)

### 1. Disaster detection — `disaster_detector.py`

To suppress single-sensor false positives, fire is declared **only when temperature and CO₂ both exceed their thresholds**.

| Event | Condition | Default threshold |
|---|---|---|
| Fire | temp > `FIRE_TEMP_THRESHOLD` **AND** CO₂ > `FIRE_CO2_THRESHOLD` | 40 °C / 400 ppm |
| Earthquake / collapse | Vibration sensor event | `EarthquakeStatus == yes` |
| Safe | Neither of the above | — |

### 2. Crowd analysis — `main.py`, `camera_test.py`

Pi Camera (Picamera2) frames are inferred with YOLOv8n and the person count is used as the crowding signal. Input resolution is reduced to 320×320 and a lightweight model is used so that inference runs in real time on the Raspberry Pi CPU. An MJPEG streaming server (port 5000) exposes the live view for debugging.

| Metric | Value |
|---|---|
| Training epochs | 100 |
| mAP | 90.1 % |
| Precision / Recall | 88.5 % / 91.2 % |
| Inference speed | 10.5 ms/frame (CPU) |
| Mean confidence | ≥ 85 % |
| Crowding rule | 0–2 people clear / 3+ congested |

### 3. Route optimization — `train_qlearning.py`, `rl_environment.py`, `route_optimizer_score_Q.py`

Route selection is framed as a reinforcement learning problem solved with Q-Learning.

- **State** — `(disaster type, crowd count, user location)`
- **Action** — routes 1–6 (room1 / room2 / hallway × central stairs / external stairs), masked to those reachable from the current location
- **Reward** — safety + travel time + crowding

| Term | Design |
|---|---|
| Safety | Base +10; −5 for starting inside the affected zone; −3 for central stairs during a disaster; −20 for a location mismatch |
| Travel time | `-base_time / 10` (route baselines 15–40 s) |
| Crowding | Central stairs: `-(7 + (n-3)×2)` when ≥3 people, +3 when clear. External stairs: milder penalty, +4 when clear |

Trained for 5,000 episodes with `learning_rate=0.15`, `discount=0.95`, `epsilon=0.15`, and persisted to `q_table.pkl`. At runtime the route with the highest Q-value wins. If the Q-table cannot be loaded, the system **falls back automatically to the rule-based optimizer** (`route_optimizer.py`) so guidance never stops.

### 4. oneM2M integration — `setup_resources.py`, `config.py`

```
SmartEvacGuide (AE)
├── Sensors    ─ Temperature · Humidity · CO2 · EarthquakeStatus · ClientPosition
├── Result     ─ Room1FireStatus · Room2FireStatus · EarthquakeStatus · StairsPassable · RouteSelection
└── Detection  ─ CrowdCount
```

### File map

| File | Role |
|---|---|
| `main.py` | Main loop — sensor polling, YOLO inference, detection, route decision, result upload, MJPEG streaming |
| `disaster_detector.py` | Sensor-based disaster detection |
| `route_optimizer.py` | Rule-based route selection (fallback) |
| `route_optimizer_score_Q.py` | Q-table based route selection (default) |
| `rl_environment.py` | Evacuation simulator and reward function |
| `train_qlearning.py` | Q-Learning training and evaluation |
| `setup_resources.py` | One-time tinyIoT AE / container provisioning |
| `test_connection.py` | Server connectivity and CRUD check |
| `test_score_ai.py` | 11-scenario route selection validation |
| `camera_test.py` | Standalone camera + YOLO check |
| `best_final.pt` | Trained YOLOv8n weights |
| `q_table.pkl` | Learned Q-table |

---

## Running it

```bash
cd ai
pip install -r requirements.txt

export TINYIOT_API_KEY="your_api_key"
export TINYIOT_AUTH_LECTURE="LCT_XXXXXXXX"
export TINYIOT_AUTH_CREATOR="sjuXXXXXXXX"

python setup_resources.py    # once — create AE and containers
python test_connection.py    # verify connectivity
python main.py               # run on the Raspberry Pi
```

Live inference view: `http://<raspberry-pi-ip>:5000/stream.mjpg`

`main.py` and `camera_test.py` require `picamera2` and therefore only run on the Raspberry Pi. On a PC you can still validate the logic:

```bash
python train_qlearning.py    # retrain the Q-table (5,000 episodes)
python test_score_ai.py      # scenario-by-scenario route validation
```

For the Android app, open `mobile-app/` in Android Studio and replace the `API_KEY` / `LECTURE` / `CREATOR` placeholders in `TinyIoTApi.kt`.

---

## Team

| Name | Department | Role |
|---|---|---|
| **Jayeon Pyo** | Information Security | **Entire AI system** (detection · YOLOv8 crowd analysis · Q-Learning routing · oneM2M integration) |
| Yejin O | Information Security | Mobile app |
| Siwoo Park | Cyber Defense | Hardware · sensors |
| Minseok Kim | Cyber Defense | Hardware · sensors |
| Hamin Lee | Computer Engineering | Unity digital twin |

## Repository layout

```
.
├── ai/                    # AI system (my part)
├── mobile-app/            # Android app — oneM2M polling, floor-plan route visualization
├── unity-digital-twin/    # Unity digital twin (link to the original repository)
└── docs/                  # Presentation deck
```

## Future work

- **Security** — fine-grained oneM2M ACP (Access Control Policy) enforcement
- **Scale** — multi-building and complex-wide monitoring, web-based admin dashboard
- **UX** — AR overlay for evacuation guidance

## Stack

`Python` `PyTorch` `Ultralytics YOLOv8` `OpenCV` `Q-Learning` `Picamera2` `Raspberry Pi` `Arduino UNO R4 WiFi` `oneM2M / tinyIoT` `Kotlin` `Android` `Unity`

---

> ⚠️ All tinyIoT credentials in this public repository have been replaced with placeholders. Substitute your own before running.
