# R/Q 결과 CSV — 261026

먼저 [result.csv](result.csv)를 연다. R 주석 차이 기술통계1행과 Q의4모델×2시점8행을 담았다.

- [q.csv](q.csv): 예측 micro, 트랙/시퀀스/날짜 macro, 날짜 cluster bootstrap95% CI.
- [r.csv](r.csv): 전체 주석쌍 편향/공분산과 교차로 bootstrap CI.
- [r_eval.csv](r_eval.csv): 교차로 제외 검증의 pair-micro/site-macro.
- [data.csv](data.csv): 전체 입력과 실제 평가 대상 개수.
- [map.csv](map.csv): 지면 지도와 제공 코드의 같은-source 일치율.
- [factors.csv](factors.csv), [columns.csv](columns.csv): 요인 판단과 컬럼 사전.
- `details/`: 추가 집계표. 관측/트랙별 원시 예측은 GitHub에 포함하지 않는다.
- [files.csv](files.csv): 이 폴더의 CSV 목록.

새 요약표 `*_pct`는0~100%, 거리 `_m`, 영역/공분산 `_m2`, 시간 `_s`다. `details/`와 `map.csv`에는 원본0~1 비율을 유지한 컬럼이 있으므로 이름과 데이터 사전을 확인한다. N/A는 해당 없음이다.

R RMSE는 주석 간 차이 기술통계다. Q는 탐색적 날짜 묶음5-fold OOF이며 물리 참값이 아니다. Q의 CI는 고정 OOF 예측에 조건부인 날짜 단위 bootstrap이고 macro 지표의 CI가 아니다. R 기술통계 CI는6교차로 bootstrap이다. Deterministic CV의 확률영역은 N/A다.
