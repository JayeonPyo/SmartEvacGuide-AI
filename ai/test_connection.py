#!/usr/bin/env python3
"""
새 TinyIoT 서버 연결 테스트
"""

import requests
from config import *

def test_connection():
    print("=" * 70)
    print("TinyIoT 서버 연결 테스트")
    print(f"서버: {TINYIOT_URL}")
    print("=" * 70)
    
    headers = {
        'X-API-KEY': API_KEY,
        'X-AUTH-CUSTOM-LECTURE': AUTH_LECTURE,
        'X-AUTH-CUSTOM-CREATOR': AUTH_CREATOR,
        'X-M2M-Origin': ORIGIN_ID,
        'X-M2M-RVI': '2a',
        'Accept': 'application/json'
    }
    
    # 1. CSE 접근 테스트
    print("\n[1] CSE 접근 테스트...")
    try:
        url = f"{TINYIOT_URL}/{CSE_BASE}"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"CSE 접근 성공")
        else:
            print(f" CSE 접근 실패: {r.status_code}")
            print(f"   응답: {r.text}")
    except Exception as e:
        print(f"예외: {e}")
    
    # 2. AE 접근 테스트
    print("\n[2] AE 접근 테스트...")
    try:
        url = f"{TINYIOT_URL}/{CSE_BASE}/{AE_NAME}"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            print(f" AE '{AE_NAME}' 접근 성공")
        elif r.status_code == 404:
            print(f"⚠️ AE '{AE_NAME}' 존재하지 않음")
            print(f"   setup_resources_new.py 실행 필요")
        else:
            print(f"❌ AE 접근 실패: {r.status_code}")
            print(f"   응답: {r.text}")
    except Exception as e:
        print(f"❌ 예외: {e}")
    
    # 3. Temperature 센서 테스트 (POST)
    print("\n[3] 센서 데이터 전송 테스트...")
    try:
        url = f"{TINYIOT_URL}/{CSE_BASE}/{AE_NAME}/Sensors/Temperature"
        headers['Content-Type'] = 'application/json; ty=4'
        payload = {
            "m2m:cin": {
                "con": "25",
                "lbl": ["test"]
            }
        }
        r = requests.post(url, headers=headers, json=payload, timeout=5)
        if r.status_code == 201:
            print(f"✅ 데이터 전송 성공")
        elif r.status_code == 404:
            print(f"⚠️ Temperature 컨테이너 없음")
            print(f"   setup_resources_new.py 실행 필요")
        else:
            print(f" 데이터 전송 실패: {r.status_code}")
            print(f"   응답: {r.text}")
    except Exception as e:
        print(f"예외: {e}")
    
    # 4. 데이터 조회 테스트 (GET)
    print("\n[4] 센서 데이터 조회 테스트...")
    try:
        url = f"{TINYIOT_URL}/{CSE_BASE}/{AE_NAME}/Sensors/Temperature/la"
        headers['Content-Type'] = 'application/json'
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f" 데이터 조회 성공")
            print(f"   값: {data['m2m:cin']['con']}")
        else:
            print(f" 데이터 조회 실패: {r.status_code}")
            print(f"   응답: {r.text}")
    except Exception as e:
        print(f"예외: {e}")
    
    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)

if __name__ == "__main__":
    test_connection()