# Mobile App (Android)

oneM2M(tinyIoT) 서버를 실시간 폴링해 센서 값과 재난 판정 결과를 표시하고, AI가 선택한 대피 경로를 평면도 위에 시각화하는 Android 앱입니다.

## 주요 기능

- 실시간 센서 카드 UI — Temperature / Humidity / CO2 / CrowdCount
- 상태 카드 — Room1FireStatus / Room2FireStatus / EarthquakeStatus / StairsPassable
- 경로 시각화 — `RouteSelection` 값에 따라 평면도 위 경로 자동 갱신
- 이벤트 알림 — 화재 상태가 `yes`로 바뀌면 즉시 경보 팝업

담당: 오예진 (정보보호학과)

## 빌드

Android Studio로 이 디렉터리를 열고, `app/src/main/java/com/example/iotchallenge/TinyIoTApi.kt` 의 `API_KEY` / `LECTURE` / `CREATOR` 플레이스홀더를 발급받은 값으로 교체한 뒤 빌드합니다.
