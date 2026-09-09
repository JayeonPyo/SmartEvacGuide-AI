"""
강화학습 환경 - 대피 시뮬레이터
"""

import random
import numpy as np

# PC 테스트용 간단 설정
CROWD_CONGESTED = 3

ROUTES = {
    1: {"name": "방1→중앙계단", "start": "room1", "via": "central_stairs", "base_time": 25},
    2: {"name": "방1→외부계단", "start": "room1", "via": "external_stairs", "base_time": 40},
    3: {"name": "방2→중앙계단", "start": "room2", "via": "central_stairs", "base_time": 20},
    4: {"name": "방2→외부계단", "start": "room2", "via": "external_stairs", "base_time": 30},
    5: {"name": "계단앞→중앙계단", "start": "hallway", "via": "central_stairs", "base_time": 15},
    6: {"name": "계단앞→외부계단", "start": "hallway", "via": "external_stairs", "base_time": 25}
}

class EvacuationEnv:
    def __init__(self):
        """대피 환경 초기화"""
        self.disaster_types = ['safe', 'fire', 'earthquake']
        self.locations = ['room1', 'room2', 'hallway']
        self.routes = ROUTES
        
        self.reset()
    
    def reset(self):
        """새 에피소드 시작"""
        # 랜덤 상황 생성
        self.disaster = random.choice(self.disaster_types)
        self.disaster_loc = None
        
        if self.disaster == 'fire':
            self.disaster_loc = 'room2'
        elif self.disaster == 'earthquake':
            self.disaster_loc = 'room1'
        
        self.crowd = random.randint(0, 5)  # 0-5명 (실제 상황 반영)
        self.location = random.choice(self.locations)
        
        return self._get_state()
    
    def _get_state(self):
        """현재 상태 반환"""
        return (self.disaster, self.crowd, self.location)
    
    def step(self, route_id):
        """
        경로 선택 후 결과 반환
        
        Args:
            route_id: 선택한 경로 (1-6)
        
        Returns:
            reward: 보상 (높을수록 좋음)
            done: 에피소드 종료 여부
        """
        route = self.routes[route_id]
        
        # 보상 계산
        reward = 0
        
        # [1] 안전도 보상
        safety_reward = self._calculate_safety_reward(route_id, route)
        
        # [2] 시간 보상 (빠를수록 좋음)
        time_penalty = -route['base_time'] / 10  # 시간이 짧을수록 패널티 적음
        
        # [3] 혼잡도 보상
        crowd_reward = self._calculate_crowd_reward(route_id, route)
        
        # 총 보상
        reward = safety_reward + time_penalty + crowd_reward
        
        # 에피소드 종료
        done = True
        
        return reward, done
    
    def _calculate_safety_reward(self, route_id, route):
        """안전도 보상"""
        reward = 10  # 기본 보상
        
        # 위치 불일치 큰 패널티
        if self.location != route['start']:
            return -20
        
        # 재난 상황 패널티
        if self.disaster == 'fire' and self.disaster_loc == 'room2':
            if route['start'] == 'room2':
                reward -= 5  # 화재 지역 출발
            if route['via'] == 'central_stairs':
                reward -= 3  # 중앙계단은 연기 위험
        
        elif self.disaster == 'earthquake' and self.disaster_loc == 'room1':
            if route['start'] == 'room1':
                reward -= 5  # 지진 지역 출발
            if route['via'] == 'central_stairs':
                reward -= 3  # 건물 내부 위험
        
        return reward
    
    def _calculate_crowd_reward(self, route_id, route):
        """혼잡도 보상 - 3명 기준 명확화"""
        reward = 0
        
        # 혼잡 여부 판단 (3명 기준)
        is_congested = (self.crowd >= CROWD_CONGESTED)
        
        # 중앙계단은 혼잡 영향 큼
        if route['via'] == 'central_stairs':
            if is_congested:
                # 3명 이상: 큰 패널티 (3명=7점, 4명=9점, 5명=11점)
                penalty = 7 + (self.crowd - 3) * 2
                reward -= penalty
            else:
                # 0-2명: 보너스 (여유함)
                reward += 3
        
        # 외부계단은 혼잡 영향 적음
        else:
            if is_congested:
                # 3명 이상: 작은 패널티
                penalty = 2 + (self.crowd - 3)
                reward -= penalty
            else:
                # 0-2명: 더 큰 보너스 (외부는 항상 좋음)
                reward += 4
        
        return reward
    
    def get_valid_routes(self):
        """현재 위치에서 가능한 경로"""
        valid = []
        for route_id, route in self.routes.items():
            if route['start'] == self.location:
                valid.append(route_id)
        return valid


# 테스트
if __name__ == "__main__":
    env = EvacuationEnv()
    
    print("=== 환경 테스트 ===")
    for i in range(3):
        state = env.reset()
        print(f"\n에피소드 {i+1}")
        print(f"상태: 재난={state[0]} 혼잡={state[1]}명 위치={state[2]}")
        
        valid_routes = env.get_valid_routes()
        print(f"가능 경로: {valid_routes}")
        
        for route_id in valid_routes:
            reward, done = env.step(route_id)
            print(f"  경로{route_id}: 보상={reward:.1f}")