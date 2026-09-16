# SmartEvacGuide - AI 기반 재난 발생 건물 대피 경로 안내 서비스

![Award](https://img.shields.io/badge/%EC%A0%9C1%ED%9A%8C%20IoT%20%ED%94%8C%EB%9E%AB%ED%8F%BC%20%EA%B0%9C%EB%B0%9C%EC%9E%90%20%EC%B1%8C%EB%A6%B0%EC%A7%80-%EC%B5%9C%EC%9A%B0%EC%88%98%EC%83%81-FFB300)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8n-mAP%2090.1%25-00A67E)
![RL](https://img.shields.io/badge/Q--Learning-5000%20episodes-7C4DFF)
![oneM2M](https://img.shields.io/badge/oneM2M-tinyIoT-0277BD)

> 🏆 **제1회 사물인터넷 플랫폼 활용 개발자 챌린지 최우수상 수상작**
> Team **IoT 요정단** · Sejong University SESLAB

[English version → README.en.md](README.en.md)

화재·지진·건물 붕괴 상황에서 센서 데이터와 카메라 영상을 실시간으로 분석해 **재난을 선제적으로 감지하고, 사용자 위치와 혼잡도에 맞는 최적 대피 경로를 안내**하는 oneM2M 표준 기반 IoT 서비스입니다. 라즈베리파이 위의 온디바이스 AI가 판단을 수행하고, 결과는 tinyIoT(oneM2M) 서버를 거쳐 모바일 앱과 Unity 디지털 트윈으로 동시에 전달됩니다.

---

## 수상

**제1회 사물인터넷 플랫폼 활용 개발자 챌린지 (AI x IoT 오픈 플랫폼 챌린지) - 최우수상**

---

## 담당 파트

이 저장소의 **AI 시스템 전체(`ai/`)** 를 제가 단독으로 설계·개발했습니다.

| 항목 | 내용 |
|---|---|
| 재난 감지 모듈 | 온도·CO₂ 복합 임계값 분석, 진동(지진) 센서 연동 로직 설계 |
| 혼잡도 분석 | YOLOv8n 커스텀 학습(100 epochs) 및 라즈베리파이 실시간 추론 파이프라인 구현 |
| 경로 최적화 | Q-Learning 기반 정책 학습, 대피 시뮬레이션 환경(보상 함수) 직접 설계 |
| 시스템 통합 | tinyIoT(oneM2M) 리소스 설계, 센서 폴링 / 결과 업로드 연동, MJPEG 스트리밍 서버 |

`mobile-app/`, `unity-digital-twin/` 은 프로젝트 전체 구조를 보여주기 위해 함께 정리한 팀원 결과물입니다.

---

## 시스템 아키텍처


<img width="1376" height="768" alt="image" src="https://github.com/user-attachments/assets/f4597d14-aff1-48ba-a80b-444956597f14" />

**데이터 흐름 (2초 주기 폴링)**

1. Arduino가 온도·습도·CO₂·진동값을 tinyIoT `Sensors` 컨테이너로 전송
2. 라즈베리파이 AI가 `Sensors/*/la` 를 조회 → 재난 판정
3. Pi Camera 프레임을 YOLOv8n으로 추론 → 실시간 인원 수(혼잡도) 산출
4. 재난 유형 + 혼잡도 + 사용자 위치를 상태로 Q-테이블 조회 → 최적 경로 ID(1-6) 결정
5. 판정 결과를 `Result`, `Detection` 컨테이너로 업로드 → 앱·디지털 트윈이 폴링해 즉시 반영

---

## AI 시스템 (`ai/`)

### 1. 재난 감지 - `disaster_detector.py`

단일 센서 오탐을 줄이기 위해 **온도와 CO₂를 동시에 만족할 때만** 화재로 판정합니다.

| 재난 | 판정 조건 | 기본 임계값 |
|---|---|---|
| 화재 | 온도 > `FIRE_TEMP_THRESHOLD` **AND** CO₂ > `FIRE_CO2_THRESHOLD` | 40 ℃ / 400 ppm |
| 지진·붕괴 | 진동 센서 이벤트 발생 | `EarthquakeStatus == yes` |
| 정상 | 위 조건 모두 미해당 | - |

판정 결과는 재난 유형·위치·심각도를 담은 dict로 반환되어 경로 최적화 모듈의 상태 입력이 됩니다.

### 2. 혼잡도 분석 - `main.py`, `camera_test.py`

Pi Camera(Picamera2) 프레임을 YOLOv8n으로 추론해 검출된 사람 수를 혼잡도로 사용합니다. 라즈베리파이 CPU에서 실시간 처리가 가능하도록 입력 해상도를 320×320으로 낮추고 경량 모델을 채택했습니다. 디버깅용 MJPEG 스트리밍 서버(포트 5000)를 함께 띄워 브라우저에서 추론 화면을 확인할 수 있습니다.

| 지표 | 값 |
|---|---|
| 학습 epochs | 100 |
| mAP | 90.1 % |
| Precision / Recall | 88.5 % / 91.2 % |
| 추론 속도 | 10.5 ms/frame (CPU) |
| 평균 신뢰도 | 85 % 이상 |
| 혼잡 기준 | 0-2명 여유 / 3명 이상 혼잡 |

### 3. 경로 최적화 - `train_qlearning.py`, `rl_environment.py`, `route_optimizer_score_Q.py`

경로 선택을 강화학습 문제로 정의하고 Q-Learning으로 정책을 학습했습니다.

- **상태 (State)** - `(재난 유형, 인원 수, 사용자 위치)`
- **행동 (Action)** - 경로 1-6 (방1/방2/복도 × 중앙계단/외부계단), 현재 위치에서 갈 수 없는 경로는 마스킹
- **보상 (Reward)** - 안전도 + 소요시간 + 혼잡도의 합

| 보상 항목 | 설계 |
|---|---|
| 안전도 | 기본 +10, 재난 발생 구역 출발 −5, 재난 시 중앙계단 경유 −3, 위치 불일치 −20 |
| 소요시간 | `-base_time / 10` (경로별 기준 소요시간 15-40초) |
| 혼잡도 | 중앙계단은 3명 이상일 때 `-(7 + (n-3)×2)`, 여유 시 +3 / 외부계단은 패널티 완만, 여유 시 +4 |

`learning_rate=0.15`, `discount=0.95`, `epsilon=0.15` 로 5,000 에피소드를 학습해 `q_table.pkl` 로 저장하며, 런타임에는 학습된 Q값이 가장 큰 경로를 선택합니다. Q-테이블 로드에 실패하면 **규칙 기반 최적화기(`route_optimizer.py`)로 자동 폴백**해 서비스가 중단되지 않도록 설계했습니다.

### 4. oneM2M 연동 - `setup_resources.py`, `config.py`

tinyIoT 서버에 AE와 컨테이너 계층을 생성하고, 센서 조회 / 결과 업로드를 담당합니다.

```
SmartEvacGuide (AE)
├── Sensors    ─ Temperature · Humidity · CO2 · EarthquakeStatus · ClientPosition
├── Result     ─ Room1FireStatus · Room2FireStatus · EarthquakeStatus · StairsPassable · RouteSelection
└── Detection  ─ CrowdCount
```

### 파일 구성

| 파일 | 역할 |
|---|---|
| `main.py` | 메인 루프 - 센서 폴링, YOLO 추론, 재난 판정, 경로 결정, 결과 업로드, MJPEG 스트리밍 |
| `disaster_detector.py` | 센서 기반 재난 감지 |
| `route_optimizer.py` | 규칙 기반 경로 선택 (폴백) |
| `route_optimizer_score_Q.py` | Q-테이블 기반 경로 선택 (기본) |
| `rl_environment.py` | 대피 시뮬레이션 환경 및 보상 함수 |
| `train_qlearning.py` | Q-Learning 학습·평가 스크립트 |
| `setup_resources.py` | tinyIoT AE / 컨테이너 최초 1회 생성 |
| `test_connection.py` | 서버 연결 및 CRUD 점검 |
| `test_score_ai.py` | 11개 시나리오 경로 선택 검증 |
| `camera_test.py` | 카메라·YOLO 단독 점검 |
| `best_final.pt` | 학습된 YOLOv8n 가중치 |
| `q_table.pkl` | 학습된 Q-테이블 |

---

## 실행 방법

### AI 시스템

```bash
cd ai
pip install -r requirements.txt

# tinyIoT 인증 정보 (하드코딩 대신 환경변수로 주입)
export TINYIOT_API_KEY="발급받은_API_키"
export TINYIOT_AUTH_LECTURE="LCT_XXXXXXXX"
export TINYIOT_AUTH_CREATOR="sjuXXXXXXXX"

python setup_resources.py    # 최초 1회 - AE·컨테이너 생성
python test_connection.py    # 서버 연결 확인
python main.py               # 라즈베리파이에서 실행
```

- 라이브 추론 화면: `http://<라즈베리파이_IP>:5000/stream.mjpg`
- `main.py`, `camera_test.py` 는 `picamera2` 가 필요해 라즈베리파이에서만 동작합니다. PC에서는 아래 스크립트로 로직만 검증할 수 있습니다.

```bash
python train_qlearning.py    # Q-Learning 재학습 (5,000 에피소드)
python test_score_ai.py      # 시나리오별 경로 선택 검증
```

### 모바일 앱

Android Studio로 `mobile-app/` 을 열고, `TinyIoTApi.kt` 의 `API_KEY` / `LECTURE` / `CREATOR` 를 발급받은 값으로 교체한 뒤 빌드합니다.

---

## 팀 구성

| 이름 | 소속 | 담당 |
|---|---|---|
| **표자연** | 정보보호학과 | **AI 시스템 전체** (재난 감지 · YOLOv8 혼잡도 분석 · Q-Learning 경로 최적화 · oneM2M 연동) |
| 오예진 | 정보보호학과 | 모바일 앱 |
| 박시우 | 사이버국방학과 | 하드웨어 · 센서 |
| 김민석 | 사이버국방학과 | 하드웨어 · 센서 |
| 이하민 | 컴퓨터공학과 | Unity 디지털 트윈 |

---

## 저장소 구성

```
.
├── ai/                    # AI 시스템 (담당 파트)
├── mobile-app/            # Android 앱 - oneM2M 폴링, 평면도 기반 경로 시각화
├── unity-digital-twin/    # Unity 디지털 트윈 (원본 저장소 링크)
└── docs/                  # 발표자료
```

## 향후 확장 방향

- **보안 강화** - oneM2M ACP(Access Control Policy) 기반 세분화된 접근 제어 적용
- **관제 확장** - 다중 건물·복합 단지 통합 모니터링, 웹 기반 관리자 대시보드
- **UX 강화** - AR 기반 대피 경로 오버레이 안내

## 기술 스택

`Python` `PyTorch` `Ultralytics YOLOv8` `OpenCV` `Q-Learning` `Picamera2` `Raspberry Pi` `Arduino UNO R4 WiFi` `oneM2M / tinyIoT` `Kotlin` `Android` `Unity`

---

> 공개 저장소이므로 tinyIoT 인증 정보는 모두 플레이스홀더로 대체되어 있습니다. 실행 전 본인의 발급 정보로 교체하세요.
