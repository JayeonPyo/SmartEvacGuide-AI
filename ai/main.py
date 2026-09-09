import io
import logging
import socketserver
from http import server
from threading import Condition, Thread
import requests
import json
import time
import cv2
import numpy as np
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from ultralytics import YOLO

# 설정 및 모듈 임포트
import config
from disaster_detector import DisasterDetector
from route_optimizer import RouteOptimizer

# ==================== MJPEG 스트리밍 서버 클래스 ====================
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()
    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    output_instance = None
    def do_GET(self):
        if self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with StreamingHandler.output_instance.condition:
                        StreamingHandler.output_instance.condition.wait()
                        frame = StreamingHandler.output_instance.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception:
                pass
        else:
            self.send_error(404)
            self.end_headers()

# ==================== 메인 AI 시스템 클래스 ====================
class SmartEvacGuide:
    def __init__(self):
        print("[AI] 시스템 초기화 시작 (Picamera2 모드)")
        
        # DisasterDetector 변수 강제 주입 (NameError 방지용 안전장치)
        import disaster_detector
        disaster_detector.FIRE_TEMP_THRESHOLD = getattr(config, 'FIRE_TEMP_THRESHOLD', 40)
        disaster_detector.FIRE_CO2_THRESHOLD = getattr(config, 'FIRE_CO2_THRESHOLD', 1000)

        self.disaster_detector = DisasterDetector()
        self.route_optimizer = RouteOptimizer()
        
        # YOLO 모델 로드
        model_path = getattr(config, 'MODEL_PATH', 'best.pt')
        print(f"[AI] YOLO 모델 로딩: {model_path}")
        self.yolo_model = YOLO(model_path)
        
        # Picamera2 설정
        self.camera = Picamera2()
        cam_config = self.camera.create_video_configuration(
            main={"size": (1280, 720)}, 
            lores={"size": (640, 480)}
        )
        self.camera.configure(cam_config)
        self.camera.start()
        
        # 스트리밍 서버 가동
        self.output = StreamingOutput()
        self.camera.start_encoder(JpegEncoder(), FileOutput(self.output), name="lores")
        StreamingHandler.output_instance = self.output
        self.start_streaming_server()
        
        # TinyIoT 주소 설정
        self.ae_url = f"{config.TINYIOT_URL}/{config.CSE_BASE}/{config.AE_NAME}"
        self.current_crowd = 0

    def start_streaming_server(self):
        def run_server():
            port = getattr(config, 'STREAMING_PORT', 5000)
            address = ('', port)
            httpd = socketserver.ThreadingTCPServer(address, StreamingHandler)
            httpd.serve_forever()
        Thread(target=run_server, daemon=True).start()

    def _get_headers(self):
        return {
            'X-API-KEY': config.API_KEY, 
            'X-AUTH-CUSTOM-LECTURE': config.AUTH_LECTURE,
            'X-AUTH-CUSTOM-CREATOR': config.AUTH_CREATOR, 
            'X-M2M-Origin': config.ORIGIN_ID,
            'X-M2M-RVI': '2a', 'Accept': 'application/json'
        }

    def get_sensor_data(self):
        headers = self._get_headers()
        try:
            r_t = requests.get(f"{self.ae_url}/Sensors/Temperature/la", headers=headers, timeout=2)
            r_c = requests.get(f"{self.ae_url}/Sensors/CO2/la", headers=headers, timeout=2)
            r_e = requests.get(f"{self.ae_url}/Sensors/EarthquakeStatus/la", headers=headers, timeout=2)
            
            temp = float(r_t.json()['m2m:cin']['con']) if r_t.status_code == 200 else 25
            co2 = float(r_c.json()['m2m:cin']['con']) if r_c.status_code == 200 else 400
            
            # [수정] "true"/"false" 문자열 및 불리언 처리
            eq = 0
            if r_e.status_code == 200:
                con_val = str(r_e.json()['m2m:cin']['con']).lower()
                # "true"이면 1000(지진 발생), 아니면 0(정상)
                eq = 1000 if con_val == "yes" else 0
            
            return {'temperature': temp, 'co2': co2, 'earthquake': eq}
        except Exception:
            return {'temperature': 25, 'co2': 400, 'earthquake': 0}

    def get_user_location(self):
        """실시간 ClientPosition 조회"""
        headers = self._get_headers()
        try:
            r = requests.get(f"{self.ae_url}/Sensors/ClientPosition/la", headers=headers, timeout=2)
            if r.status_code == 200:
                pos_code = str(r.json()['m2m:cin']['con'])
                return config.LOCATION_MAP.get(pos_code, "room1")
        except Exception:
            pass
        return "room1"

    def get_crowd_count(self):
        try:
            frame_raw = self.camera.capture_array("main")
            frame_bgr = frame_raw[:, :, :3]
            results = self.yolo_model(frame_bgr, imgsz=320, conf=0.4, verbose=False)
            return len(results[0].boxes)
        except Exception:
            return self.current_crowd


    
    def save_results(self, disaster_info, route_id, crowd_count):
        headers = self._get_headers()
        headers['Content-Type'] = 'application/json; ty=4' # ty=4: ContentInstance
        
        # 전송할 데이터와 URL 매핑
        payloads = {
            f"{self.ae_url}/Result/Room1FireStatus": "yes" if disaster_info['room1_fire'] else "no",
            f"{self.ae_url}/Result/Room2FireStatus": "yes" if disaster_info['room2_fire'] else "no",
            f"{self.ae_url}/Result/EarthquakeStatus": "yes" if disaster_info['earthquake'] else "no",
            f"{self.ae_url}/Result/RouteSelection": str(route_id) if disaster_info['type'] != 'safe' else "0",
            f"{self.ae_url}/Detection/CrowdCount": str(crowd_count)
        }

        print("\n[서버 전송 시도...]")
        for url, value in payloads.items():
            try:
                data = {"m2m:cin": {"con": value}}
                response = requests.post(url, headers=headers, json=data, timeout=3)
                
                if response.status_code == 201:
                    print(f" ✅ {url.split('/')[-1]}: 성공 ({value})")
                else:
                    # 서버가 왜 거절했는지 출력
                    print(f" ❌ {url.split('/')[-1]}: 실패! (코드: {response.status_code})")
                    print(f"    ㄴ 서버 메시지: {response.text}")
            except Exception as e:
                print(f" ❌ {url.split('/')[-1]}: 연결 에러 ({e})")

    def run(self):
        print("\n" + "=" * 60 + "\nSmart Evac Guide 가동 시작 (True/False 지진값 대응)\n" + "=" * 60)
        try:
            poll_interval = getattr(config, 'SENSOR_POLL_INTERVAL', 2)
            while True:
                sensor_data = self.get_sensor_data()
                self.current_crowd = self.get_crowd_count()
                user_location = self.get_user_location()
                
                disaster_info = self.disaster_detector.detect(sensor_data)
                
                if disaster_info['type'] == 'safe':
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 상태:정상 | 위치:{user_location} | 인원:{self.current_crowd}명")
                    self.save_results(disaster_info, 0, self.current_crowd)
                else:
                    route_id = self.route_optimizer.select_optimal_route(disaster_info, self.current_crowd, user_location)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 {disaster_info['type'].upper()}! | 위치:{user_location} | 경로:{route_id}")
                    self.save_results(disaster_info, route_id, self.current_crowd)
                
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            if hasattr(self, 'camera'):
                self.camera.stop()

if __name__ == "__main__":
    SmartEvacGuide().run()