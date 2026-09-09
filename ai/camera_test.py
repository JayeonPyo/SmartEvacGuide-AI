#!/usr/bin/env python3
import time
import os
from datetime import datetime
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import numpy as np

# ==================== 설정 (Config) ====================
#
MODEL_PATH = "/home/seslab/Desktop/green_AI/best_final.pt"
SAVE_DIR = "/home/seslab/Desktop/green_AI/test_images"

# 저장 폴더 생성
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print("=" * 60)
print("🚀 Green Sentinel - Picamera2 SSH Mode (No GUI)")
print("=" * 60)

# 1. YOLO 모델 로드
try:
    model = YOLO(MODEL_PATH)
    print(" YOLO 모델 로드 성공")
except Exception as e:
    print(f" 모델 로드 실패: {e}")
    exit(1)

# 2. Picamera2 초기화 (지난 프로젝트 방식 활용)
try:
    picam2 = Picamera2()
    # 고해상도 설정 및 AI 분석 최적화
    config = picam2.create_video_configuration(main={"size": (1920, 1080)})
    picam2.configure(config)
    picam2.start()
    print("카메라(Picamera2) 시작 성공")
except Exception as e:
    print(f"카메라 초기화 실패: {e}")
    exit(1)

print("\n3초마다 사진을 찍어 YOLO로 분석합니다. (Ctrl+C로 종료)")

try:
    while True:
        # 프레임 캡처 (Raw Array)
        frame = picam2.capture_array()
        
        # 3. 채널 변환 (중요: 4채널 RGBA -> 3채널 BGR)
        # YOLOv8은 3채널 이미지를 기대하므로 변환이 필수입니다.
        if frame.shape[2] == 4:
            # RGBA를 BGR로 변환하여 OpenCV 및 YOLO 호환성 확보
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        elif frame.shape[2] == 3:
            # RGB인 경우 BGR로 순서 변경
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 4. YOLO 추론 (이미지 크기 조정 및 신뢰도 설정)
        results = model(frame, imgsz=320, conf=0.4, verbose=False)
        person_count = len(results[0].boxes)
        
        # 5. 결과 시각화 (Bounding Box 그리기)
        annotated_frame = results[0].plot()
        
        # 6. 파일 저장
        timestamp = datetime.now().strftime('%H%M%S')
        save_path = f"{SAVE_DIR}/detect_{timestamp}.jpg"
        cv2.imwrite(save_path, annotated_frame)
        
        print(f"📸 [{datetime.now().strftime('%H:%M:%S')}] 저장 완료: {save_path} ({person_count}명 감지)")
        
        # 3초 대기
        time.sleep(3)

except KeyboardInterrupt:
    print("\n사용자에 의해 중단되었습니다.")
finally:
    # 자원 해제
    picam2.stop()
    print(" 카메라를 안전하게 종료합니다.")