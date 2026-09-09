import os

# config.py (Green Sentinel 전용)
TINYIOT_URL = "https://onem2m.iotcoss.ac.kr"
CSE_BASE = "tinyIoT" 
AE_NAME = "SmartEvacGuide"
ORIGIN_ID = "CAdmin"

API_KEY = os.getenv("TINYIOT_API_KEY", "")
AUTH_LECTURE = os.getenv("TINYIOT_AUTH_LECTURE", "")
AUTH_CREATOR = os.getenv("TINYIOT_AUTH_CREATOR", "")

MODEL_PATH = os.getenv("MODEL_PATH", "./best_final.pt")  # YOLOv8 weights
STREAMING_PORT = 5000 # 웹 브라우저에서 볼 포트

FIRE_TEMP_THRESHOLD = 40      # 화재 판단: 40도 이상
FIRE_CO2_THRESHOLD = 400     # 화재 판단: 1000ppm 이상

# 3명 이상 혼잡
CROWD_CONGESTED = 3

ROUTES = {
    1: {"name": "방1→중앙계단", "description": "방1에서 중앙계단 이용"},
    2: {"name": "방1→외부계단", "description": "방1에서 외부계단(우회) 이용"},
    3: {"name": "방2→중앙계단", "description": "방2에서 중앙계단 이용"},
    4: {"name": "방2→외부계단", "description": "방2에서 외부계단(우회) 이용"},
    5: {"name": "계단앞→중앙계단", "description": "복도에서 중앙계단 이용"},
    6: {"name": "계단앞→외부계단", "description": "복도에서 외부계단(우회) 이용"}
}

LOCATION_MAP = {"1": "room1", "2": "room2", "3": "hallway"}
SENSOR_POLL_INTERVAL = 2