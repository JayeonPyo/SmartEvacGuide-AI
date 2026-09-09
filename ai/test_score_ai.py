#!/usr/bin/env python3
"""
점수 기반 AI 테스트 스크립트
다양한 시나리오에서 경로 선택 확인
"""

import sys
sys.path.append('/home/seslab/Desktop/green_AI')

from route_optimizer import RouteOptimizer
from disaster_detector import DisasterDetector

def test_scenario(name, disaster_type, disaster_loc, crowd, user_loc):
    """시나리오 테스트"""
    print("\n" + "=" * 70)
    print(f"테스트: {name}")
    print("=" * 70)
    
    # 재난 정보 구성
    disaster_info = {
        'type': disaster_type,
        'location': disaster_loc,
        'severity': 'high' if disaster_type != 'safe' else 'none',
        'room1_fire': False,
        'room2_fire': disaster_type == 'fire' and disaster_loc == 'room2',
        'earthquake': disaster_type == 'earthquake' and disaster_loc == 'room1'
    }
    
    # AI 경로 선택
    optimizer = RouteOptimizer()
    route_id = optimizer.select_optimal_route(disaster_info, crowd, user_loc)
    
    print(f"\n선택된 경로: {route_id}")
    route_info = optimizer.get_route_info(route_id)
    print(f"경로명: {route_info['route_name']}")
    print(f"설명: {route_info['route_description']}")

def main():
    print("=" * 70)
    print("점수 기반 AI 경로 선택 시스템 테스트")
    print("=" * 70)
    
    # 테스트 시나리오들
    scenarios = [
        # (이름, 재난타입, 재난위치, 혼잡도, 사용자위치)
        ("정상 + 여유", "safe", None, 1, "room1"),
        ("정상 + 혼잡", "safe", None, 5, "room1"),
        ("화재(방2) + 방2 사용자 + 여유", "fire", "room2", 1, "room2"),
        ("화재(방2) + 방2 사용자 + 혼잡", "fire", "room2", 5, "room2"),
        ("화재(방2) + 방1 사용자 + 여유", "fire", "room2", 1, "room1"),
        ("화재(방2) + 방1 사용자 + 혼잡", "fire", "room2", 5, "room1"),
        ("지진(방1) + 방1 사용자 + 여유", "earthquake", "room1", 1, "room1"),
        ("지진(방1) + 방1 사용자 + 혼잡", "earthquake", "room1", 5, "room1"),
        ("지진(방1) + 방2 사용자 + 여유", "earthquake", "room1", 1, "room2"),
        ("계단앞 + 여유", "safe", None, 1, "hallway"),
        ("계단앞 + 혼잡", "safe", None, 5, "hallway"),
    ]
    
    for scenario in scenarios:
        test_scenario(*scenario)
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    main()