# View2Risk — FINAL_UQ_SYSTEM

최종 품질 점검판 `release_qa_20261110`. 서버 `<private-server-path>`를 그대로 유지했다.

- Viewer: GitHub Pages `/view2risk/final/` · 정적 사전 계산 데모.
- 구성: DD-MDN Q + IMPTC/inD → PedPy 기술 분석 → SPD Train R_proxy / FilterPy → 기존 Babylon.js.
- 17개 사례, 153개 origin, 8조건, 1,224개 저장 결과. 실제 관측으로 1초/4초 갱신, 각 예측의 horizon은 4초.
- 원본 IMPTC 공식 전체 Test 120,871 windows 결과는 변경 없이 보존했다.
- 새 모델·신규 자료·GPU 잡·기능 확장 없음. inD 전처리 오류의 동일 조건 CPU 재검사만 수행.

## 상태

| 구성 | 판정 | 범위 |
|---|---|---|
| 공식 IMPTC/inD checkpoint 실제 추론 | PASSED | 동일 checkpoint/seed, no training |
| PedPy·FilterPy·FFBS·좌표 및 단위 | PASSED | 구현 정합성; 물리 R–Q 식별 증명 아님 |
| inD 팔레트·ensemble metadata 정정 | PASSED | 원본 전처리 호환성 복구, GT/조건 유지 |
| Babylon Results·Methodology | PASSED | 요청한 6개 순서, Coverage+면적+NLL |
| R+Q Clean 회복 | LIMITATION | 두 데이터셋 모두 회복 못함 |
| 완료확률 Calibration | LIMITATION | 미실행, Simulation-only |
| inD semantic Exit | BLOCKED | 미확정, 완료확률 미계산 |

상세 판정은 `FINAL_RELEASE_CHECK.md`, 수치는 `FINAL_RESULTS.md`, 수식·출처는 `METHODOLOGY.md`를 참조한다. 브라우저 최종 검사 여부는 release check가 기준이다.

## 보존

변경 전 코드/설정/웹/결과/사례: `reports/release_qa_20261110/before/`. 기존 N00/N01/N02·22개 GPU 실험·Survival·GT v1·팀원 GitHub·Babylon v3·Rerun·raw data·weights는 수정하지 않았다. 최종 사이트의 메인 모델은 DD-MDN이다.

## 공개 정적 실행

저장소 루트에서 `python3 -m http.server 8000 --directory docs`를 실행하고 `/final/`을 연다. GitHub Pages에서는 main/docs의 `/final/`을 제공한다. 기존 private 서버와 독립적이며 API·체크포인트가 필요 없다.

## 비공개 자료

서버는 loopback에만 bind한다. inD 원본 CSV·지도·복원 가능한 궤적과 단계별 사례 그림/JSON은 외부 공개하지 않는다. 승인 사용자 SSH 터널의 private API만 사용한다. 공개 호스팅/원본 GitHub 업로드는 하지 않았다. 발표 자료는 허가 범위의 집계 수치와 비복원성 그림으로 제한한다.

## 출처·환경

- DD-MDN: https://github.com/kav-institute/ddmdn · 논문: https://arxiv.org/abs/2602.11214
- PedPy: https://github.com/PedestrianDynamics/PedPy
- FilterPy: https://github.com/rlabbe/filterpy
- inD Tools: https://github.com/ika-rwth-aachen/drone-dataset-tools
- SPD: https://github.com/AIR-THU/DAIR-V2X-Seq
- inD 라이선스/데이터: https://levelxdata.com/ind-dataset/

DD-MDN commit `0726eb14babe78349da03a4d8bdf34fb91612ebc`. inD Tools commit `719cf28be4ae0c2a82314176e0712d636a3854ec`. 라이브러리 버전: torch 2.9.1, numpy 2.2.6, pandas 2.3.3, scipy 1.17.0, shapely 2.2.0, pedpy 1.5.1, filterpy 2.0.0, contourpy 1.3.3. 자세한 source/hash는 `reports/environment.json` 및 checkpoint JSON에 보존한다.

## 공개 릴리스 범위

본 문서의 기존 연구 수치·방법은 보존한다. 공개판은 IMPTC 3개 허가된 비상업 예제와 집계만 제공하며 inD의 개인 궤적·지도는 포함하지 않는다. private API 기반 서버를 공개한 것이 아니다.
