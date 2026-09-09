#!/usr/bin/env python3
"""
Green Sentinel - TinyIoT Resource Setup
Updated for new server
최초 1회만 실행
"""

import requests
from config import *

def create_ae(parent_url, ae_name):
    headers = {
        'X-API-KEY': API_KEY,
        'X-AUTH-CUSTOM-LECTURE': AUTH_LECTURE,
        'X-AUTH-CUSTOM-CREATOR': AUTH_CREATOR,
        'X-M2M-Origin': ORIGIN_ID,
        'X-M2M-RVI': '2a',
        'Accept': 'application/json',
        'Content-Type': 'application/json; ty=2',
        'X-M2M-RI': f"create_ae_{ae_name}",
    }
    payload = {"m2m:ae": {"rn": ae_name, "api": "N.iot-fairy.smart-evac", "rr": True}}
    
    try:
        r = requests.post(parent_url, headers=headers, json=payload, timeout=5)
        if r.status_code in [201, 409]:
            print(f" AE '{ae_name}' {'생성' if r.status_code == 201 else '이미 존재'}")
            return True
        print(f"AE 생성 실패: {r.status_code}")
        print(f"   응답: {r.text}")
        return False
    except Exception as e:
        print(f" 예외: {e}")
        return False

def create_container(parent_url, container_name, labels=None):
    headers = {
        'X-API-KEY': API_KEY,
        'X-AUTH-CUSTOM-LECTURE': AUTH_LECTURE,
        'X-AUTH-CUSTOM-CREATOR': AUTH_CREATOR,
        'X-M2M-Origin': ORIGIN_ID,
        'X-M2M-RVI': '2a',
        'Accept': 'application/json',
        'Content-Type': 'application/json; ty=3',
        'X-M2M-RI': f"create_cnt_{container_name}",
    }
    container_payload = {"rn": container_name}
    if labels:
        container_payload["lbl"] = labels
    payload = {"m2m:cnt": container_payload}
    
    try:
        r = requests.post(parent_url, headers=headers, json=payload, timeout=5)
        if r.status_code in [201, 409]:
            print(f"  '{container_name}' {'생성' if r.status_code == 201 else '존재'}")
            return True
        return False
    except:
        return False

def main():
    print("=" * 70)
    print("Smart Evac Guide 리소스 설정")
    print(f"서버: {TINYIOT_URL}")
    print("=" * 70)
    
    cse_url = f"{TINYIOT_URL}/{CSE_BASE}"
    ae_url = f"{cse_url}/{AE_NAME}"
    
    # AE 생성
    print("\n[1] AE 생성...")
    if not create_ae(cse_url, AE_NAME):
        return
    
    # Sensors 폴더
    print("\n[2] Sensors 생성...")
    create_container(ae_url, "Sensors")
    sensors_url = f"{ae_url}/Sensors"
    
    sensors = ["Temperature", "Humidity", "CO2", "EarthquakeStatus", "ClientPosition"]
    for s in sensors:
        create_container(sensors_url, s)
    
    # Result 폴더
    print("\n[3] Result 생성...")
    create_container(ae_url, "Result")
    result_url = f"{ae_url}/Result"
    
    results = ["Room1FireStatus", "Room2FireStatus", "EarthquakeStatus", 
               "StairsPassable", "RouteSelection"]
    for r in results:
        create_container(result_url, r)
    
    # Detection 폴더
    print("\n[4] Detection 생성...")
    create_container(ae_url, "Detection")
    detection_url = f"{ae_url}/Detection"
    create_container(detection_url, "CrowdCount")
    
    print("\n" + "=" * 70)
    print("설정 완료!")
    print("=" * 70)

if __name__ == "__main__":
    main()