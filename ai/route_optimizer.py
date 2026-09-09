from config import *

class RouteOptimizer:
    def __init__(self):
        print("[AI] RouteOptimizer 초기화: 복도 최적화 모드")
    
    def select_optimal_route(self, disaster_info, crowd_count, user_location="room1"):
        disaster_type = disaster_info.get('type', 'safe')
        disaster_loc = disaster_info.get('location', '')
        is_congested = (crowd_count >= CROWD_CONGESTED) # 3명 기준

        # 1. 방 1 사용자
        if user_location == "room1":
            if (disaster_type == 'earthquake' and disaster_loc == 'room1') or is_congested:
                return 2
            return 1
        # 2. 방 2 사용자
        elif user_location == "room2":
            if (disaster_type == 'fire' and disaster_loc == 'room2') or is_congested:
                return 4
            return 3
        # 3. 복도(hallway) 사용자 
        else:
            if is_congested:
                return 6
            return 5