from config import *

class DisasterDetector:
    def __init__(self):
        print("[AI] DisasterDetector 초기화")
    
    def detect(self, sensor_data):
        """
        sensor_data: {'temperature': float, 'co2': float, 'earthquake': int}
        """
        temp = sensor_data.get('temperature', 25)
        co2 = sensor_data.get('co2', 400)
        earthquake = sensor_data.get('earthquake', 0)
        
        # 임계값 판단
        room2_fire = (temp > FIRE_TEMP_THRESHOLD and co2 > FIRE_CO2_THRESHOLD)
        room1_fire = False
        earthquake_detected = (earthquake > 0)
        
        # 재난 상태 결정
        if room2_fire:
            disaster_type = 'fire'
            disaster_location = 'room2'
            severity = 'high'
        elif earthquake_detected:
            disaster_type = 'earthquake'
            disaster_location = 'room1'
            severity = 'high'
        else:
            disaster_type = 'safe'
            disaster_location = None
            severity = 'none'
        
        return {
            'type': disaster_type,
            'location': disaster_location,
            'severity': severity,
            'room1_fire': room1_fire,
            'room2_fire': room2_fire,
            'earthquake': earthquake_detected,
            'details': {
                'temperature': temp,
                'co2': co2,
                'earthquake_sensor': earthquake
            }
        }