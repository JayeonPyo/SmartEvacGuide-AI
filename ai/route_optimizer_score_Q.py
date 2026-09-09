"""
Route Optimizer - 강화학습 버전
Q-Learning으로 학습된 정책 사용
"""

from collections import defaultdict
import pickle
import os

# 경로 정의 (config.py 없어도 동작)
ROUTES = {
    1: {"name": "방1→중앙계단", "start": "room1", "via": "central_stairs", "base_time": 25},
    2: {"name": "방1→외부계단", "start": "room1", "via": "external_stairs", "base_time": 40},
    3: {"name": "방2→중앙계단", "start": "room2", "via": "central_stairs", "base_time": 20},
    4: {"name": "방2→외부계단", "start": "room2", "via": "external_stairs", "base_time": 30},
    5: {"name": "계단앞→중앙계단", "start": "hallway", "via": "central_stairs", "base_time": 15},
    6: {"name": "계단앞→외부계단", "start": "hallway", "via": "external_stairs", "base_time": 25}
}
CROWD_CONGESTED = 3

class RouteOptimizer:
    def __init__(self, use_rl=True):
        """
        경로 최적화
        
        Args:
            use_rl: True면 강화학습, False면 점수 기반
        """
        self.routes = ROUTES
        self.use_rl = use_rl
        
        if use_rl:
            # Q-테이블 로드
            self.q_table = self._load_q_table()
            if self.q_table:
                print("[AI] RouteOptimizer 초기화 (강화학습 기반)")
            else:
                print("[AI] Q-테이블 로드 실패, 점수 기반으로 전환")
                self.use_rl = False
        
        if not use_rl:
            # 점수 기반 가중치
            self.weights = {
                'safety': 0.5,
                'distance': 0.3,
                'crowd': 0.2
            }
            print("[AI] RouteOptimizer 초기화 (점수 기반)")
    
    def _load_q_table(self):
        """Q-테이블 로드"""
        # 여러 경로 시도
        possible_paths = [
            './q_table.pkl',  # 현재 폴더
            '/home/seslab/Desktop/green_AI/q_table.pkl',  # 라즈베리파이
            'q_table.pkl'  # 상대 경로
        ]
        
        for filepath in possible_paths:
            if not os.path.exists(filepath):
                continue
            
            try:
                with open(filepath, 'rb') as f:
                    q_table = pickle.load(f)
                print(f"[RL] Q-테이블 로드 성공: {filepath} ({len(q_table)} 상태)")
                return defaultdict(lambda: defaultdict(float), q_table)
            except Exception as e:
                print(f"[RL] Q-테이블 로드 실패 ({filepath}): {e}")
                continue
        
        print(f"[RL] Q-테이블 파일을 찾을 수 없음")
        return None
    
    def select_optimal_route(self, disaster_info, crowd_count, user_location="room1"):
        """
        최적 경로 선택
        
        Returns:
            int: 경로 ID (1-6)
        """
        if self.use_rl:
            return self._select_with_rl(disaster_info, crowd_count, user_location)
        else:
            return self._select_with_score(disaster_info, crowd_count, user_location)
    
    def _select_with_rl(self, disaster_info, crowd_count, user_location):
        """강화학습 기반 선택"""
        # 상태 구성
        state = (disaster_info['type'], crowd_count, user_location)
        
        # 가능한 경로
        valid_routes = [rid for rid, r in self.routes.items() 
                       if r['start'] == user_location]
        
        # Q값 가져오기
        q_values = {route: self.q_table[state][route] 
                   for route in valid_routes}
        
        # 최대 Q값 선택
        best_route = max(q_values, key=q_values.get)
        
        print(f"\n[RL 선택] 재난:{disaster_info['type']} 혼잡:{crowd_count}명 위치:{user_location}")
        print(f"[Q값] ", end="")
        for route, q in sorted(q_values.items()):
            print(f"경로{route}:{q:.2f} ", end="")
        print(f"\n선택: 경로 {best_route}")
        
        return best_route
    
    def _select_with_score(self, disaster_info, crowd_count, user_location):
        """점수 기반 선택 (백업)"""
        # ... (기존 점수 기반 코드와 동일)
        # 여기는 기존 route_optimizer_score_based.py 코드 사용
        
        # 간단 버전 (혼잡도만)
        print(f"\n[점수 기반] 재난:{disaster_info['type']} 혼잡:{crowd_count}명 위치:{user_location}")
        
        is_congested = (crowd_count >= CROWD_CONGESTED)
        
        if user_location == "room1":
            return 2 if is_congested else 1
        elif user_location == "room2":
            return 4 if is_congested else 3
        else:  # hallway
            return 6 if is_congested else 5
    
    def get_route_info(self, route_id):
        """경로 상세 정보"""
        route = self.routes[route_id]
        return {
            'route_id': route_id,
            'route_name': route['name'],
            'route_description': route['description']
        }