# AI 시스템

이 디렉터리는 SmartEvacGuide의 AI 파트 전체입니다. 모듈별 설계 근거와 성능 지표는 [최상위 README](../README.md#ai-시스템-ai)를 참고하세요.

## 구성

- **재난 감지** `disaster_detector.py` — 온도·CO₂ 복합 임계값 + 진동 센서
- **혼잡도 분석** `main.py` — YOLOv8n(320×320) 실시간 인원 카운팅
- **경로 최적화** `route_optimizer_score_Q.py` / `train_qlearning.py` / `rl_environment.py` — Q-Learning 정책
- **폴백 경로 최적화** `route_optimizer.py` — Q-테이블 로드 실패 시 규칙 기반 동작
- **oneM2M 연동** `setup_resources.py`, `config.py`

## 빠른 실행

```bash
pip install -r requirements.txt

export TINYIOT_API_KEY="발급받은_API_키"
export TINYIOT_AUTH_LECTURE="LCT_XXXXXXXX"
export TINYIOT_AUTH_CREATOR="sjuXXXXXXXX"

python setup_resources.py    # 최초 1회
python test_connection.py
python main.py               # 라즈베리파이
```

PC에서는 `train_qlearning.py`(재학습)와 `test_score_ai.py`(시나리오 검증)로 로직만 확인할 수 있습니다.
