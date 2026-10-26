"""Reuse immutable audit outputs for a sample-only handoff; no downloads or fitting."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RP = ROOT / 'reports'
SP = RP / 'stage_samples'


def table(frame):
    frame = frame.fillna('N/A')
    rows = [[str(v).replace('|', '/') for v in frame.columns]]
    rows += [['---'] * len(frame.columns)]
    rows += [[str(v).replace('|', '/') for v in row] for row in frame.itertuples(index=False, name=None)]
    return '\n'.join('| ' + ' | '.join(row) + ' |' for row in rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inputs = [RP / 'spd_metrics.json', SP / 'imptc_metrics.json',
              RP / 'spd_condition_counts.csv', SP / 'imptc_condition_counts.csv',
              SP / 'imptc_event_sensitivity.csv',
              ROOT / 'data/processed/spd_pedestrian_pairs.parquet',
              ROOT / 'data/processed/stage_samples/imptc_pedestrian_tracks.parquet']
    before = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    r = json.loads(inputs[0].read_text())
    q = json.loads(inputs[1].read_text())
    rdf, qdf = [pd.read_parquet(p) for p in inputs[-2:]]
    assert len(rdf) == r['matched_pairs'] == 253
    assert rdf.track_uid.nunique() == r['distinct_pedestrian_track_groups'] == 9
    assert len(qdf) == q['pedestrian_observations'] == 56374
    assert qdf.track_uid.nunique() == q['pedestrian_tracks'] == 61
    assert qdf.sequence_id.nunique() == q['sequences'] == 4
    assert int((qdf.status == 2).sum()) == q['strict_status2_observations'] == 54314
    rc = pd.read_csv(inputs[2])
    qc = pd.read_csv(inputs[3])
    events = pd.read_csv(inputs[4])
    source_rows = qc[qc.condition == 'source_type'][['value', 'observations', 'tracks', 'sequences', 'strict_status2']]
    conditions = qc[qc.condition.isin(['weather_name', 'signal_f1', 'signal_f2', 'signal_f3'])]
    factors = pd.DataFrame([
        ['R', '거리·가림·bbox 크기·절단', 9, 1, '필드 보존 / 조건부 R 추정 보류', '단일 시퀀스, 주석·시각·좌표 변환 영향 혼재'],
        ['R', '센서 시각차', 9, 1, '품질 점검 변수 유지', '동기화된 모델 예측 오차로 해석하지 않음'],
        ['Q', '속력·가감속·정지/재출발·방향 변화', 61, 4, '진단 후보 유지', '관측·추적 잡음 포함, 순수 Q 아님'],
        ['Q', '주변 보행자 수', 61, 4, '진단 후보 유지', '동시 관측된 트랙의 XY 5m 반경, 실제 혼잡도 정답 아님'],
        ['Q/R', '센서 출처·status', 61, 4, '층화·통제 변수 유지', '관측 방식 변화와 움직임 변화 혼입 점검'],
        ['Q', '보행 신호', 61, 4, '개별 트랙 적용 보류', 'f1/f2/f3 시간 매칭 가능, 횡단보도별 공간 배정 미검증'],
        ['Q', '날씨', 61, 4, '조건 효과 추정 보류', '샘플의 관측된 weather_name은 sunny_cloudy 한 종류'],
        ['B', '트랙별 평균 속력', 61, 4, '초기 속도 사전분포 후보', '장면 간 동일 사람 ID 없음, 개인 고유 속도로 확정하지 않음'],
        ['Outcome', '완전/부분 횡단·완료 시간', 61, 4, '현재 N/A', '검증된 진입/출구 영역 및 신호 공간 매핑 필요'],
    ], columns=['축', '요소', '전체 트랙 수', '시퀀스 수', '판정', '근거·한계'])
    sections = [
        '# View2Risk 샘플 분석 — 261025',
        '**결론: `View2Risk_Data_Audit_Plan.md`의 데이터 구조 확인·품질 감사·R/Q 후보 선정은 샘플로 진행 가능하며, 아래 결과는 기존 샘플 분석 산출물로 확인했다.** 조건 효과의 정식 추정과 교차로 간 일반화는 별도 검증이 필요하다.',
        '이 문서는 **V2X-Seq SPD Example + IMPTC Samples만** 사용한다. 기존 Set 01 중심 `data_audit_summary.md`와 구분하며, Full Set 01–05는 표와 통계에 포함하지 않았다. 샘플/Full의 일부 겹친 수치 export도 혼합하지 않았다. 원본과 기존 결과는 수정하지 않고 이 문서와 검증 기록만 추가했다.',
        '## 1. 분석 범위와 표본',
        '| 데이터 | 시퀀스 | 프레임 | 보행자 트랙 | 관측 / pair |\n| --- | ---: | ---: | ---: | ---: |\n'
        f'| V2X-Seq SPD Example | {r["sequences"]} | {r["frames"]} | {r["distinct_pedestrian_track_groups"]} | {r["matched_pairs"]} pairs |\n'
        f'| IMPTC Samples | {q["sequences"]} | 해당 없음 | {q["pedestrian_tracks"]} | {q["pedestrian_observations"]:,} observations |',
        '트랙은 시퀀스 안의 ID 그룹이다. 프레임/관측을 독립 표본으로 세지 않으며 트랙 수를 서로 다른 실제 사람 수로 보장하지 않는다. SPD는 단일 교차로의 단일 시퀀스다.',
        'SPD 원본: `../data/raw/spd_example/V2X-Seq-SPD-Example/` (기존 로컬 Example에서 복사, 4,011개 파일 SHA256 전송 검증). IMPTC: `../data/raw/imptc_samples/` (공식 Zenodo 압축파일 MD5 검증). 라이선스·출처 상세는 `source_provenance.json`을 참조한다.',
        '## 2. V2X 샘플: 매칭·시간·좌표·R 후보',
        f'- Camera/virtual-LiDAR Pedestrian 주석 각각 253개. 동일 프레임·클래스·track ID 매칭 **253/253 (100%)**, 미대응/중복 0개.\n'
        f'- timestamp는 UNIX epoch **마이크로초**. 카메라−LiDAR 시각차는 프레임 기준 중앙값 **{1000*r["timestamp_gap_s"]["median"]:.3f} ms**, signed p95 **{1000*r["timestamp_gap_s"]["p95"]:.3f} ms**, 범위 **{1000*r["timestamp_gap_s"]["min"]:.3f}~{1000*r["timestamp_gap_s"]["max"]:.3f} ms**.\n'
        '- 양쪽 3D 주석은 문서상 같은 virtual-LiDAR 좌표계다. supplied world 변환을 적용해 수평 XY 차이를 계산했고, 시각차를 보상하지 않은 진단값으로 기록했다.',
        f'| 수평 위치 차이 지표 | 값 (m) |\n| --- | ---: |\n| RMSE | {r["RMSE_world_horizontal_xy_m"]:.6f} |\n'
        f'| 거리 중앙값 | {r["discrepancy_norm_m"]["median"]:.6f} |\n| 거리 p95 | {r["discrepancy_norm_m"]["p95"]:.6f} |\n'
        f'| 거리 최대 | {r["discrepancy_norm_m"]["max"]:.6f} |\n| dx 평균 / 표준편차 | {r["dx_m"]["mean"]:.6f} / {r["dx_m"]["std"]:.6f} |\n'
        f'| dy 평균 / 표준편차 | {r["dy_m"]["mean"]:.6f} / {r["dy_m"]["std"]:.6f} |',
        f'트랙 군집 bootstrap RMSE 95% 구간은 {r["RMSE_track_cluster_bootstrap95"][0]:.6f}–{r["RMSE_track_cluster_bootstrap95"][1]:.6f} m다. 단일 시퀀스 안의 불확실성만 반영하며 교차로 간 일반화 구간은 아니다.',
        '**이 값은 두 주석의 차이이며 카메라 모델의 예측 오차나 최종 R 행렬이 아니다.** 양쪽은 모든 pair에서 동일한 2D bbox를 공유한다. 센서 시각차·주석·좌표 변환 영향을 분리할 수 없다.',
        f'제공 virtual-LiDAR→camera 행렬은 {r["camera_nonrigid_calibration_frames"]}프레임에서 직교 회전 조건을 만족하지 않았다(max |RᵀR−I|={r["max_camera_orthogonality_error"]:.6f}). 전치행렬 대신 일반 역변환을 사용했다. K 투영 bbox 포함률은 camera {100*r["projection_K_camera_bbox_fraction"]:.2f}%, LiDAR {100*r["projection_K_lidar_bbox_fraction"]:.2f}%이고 제공 P 투영은 모두 0%여서 해석 제약을 남겼다. 임의 calibration 보정은 하지 않았다.',
        '조건별 관측/트랙 수와 위치 차이:',
        table(rc),
        '조건 그룹에 같은 트랙이 반복 포함될 수 있으므로 그룹별 트랙 수를 더해 전체 트랙 수로 해석하면 안 된다. 거리 구간도 약 80–88 m에 제한된다. 시간 자기상관과 군집 효과는 `spd_fixed_time_autocorrelation.csv`, `spd_autocorrelation.csv`가 존재하는 경우 해당 산출물을 참조한다.',
        '## 3. IMPTC 샘플: 연속성·속력·Q 후보',
        f'모든 {q["pedestrian_observations"]:,}행을 보존했다. status=2 유효 관측 **{q["strict_status2_observations"]:,}개 ({100*q["strict_status2_observations"]/q["pedestrian_observations"]:.2f}%)**, status=1은 2,060개다. 유한 좌표 {q["finite_coordinates"]:,}개, 중복 시각 {q["duplicate_timestamp_rows"]}개, 역순 {q["out_of_order_steps"]}개, 60 ms 초과 gap {q["gap_count"]}개다.',
        table(pd.DataFrame([{'최소 연속 관측 (s)': k, 'status=2 유효 트랙 수': v} for k, v in q['strict_continuity_counts'].items()])),
        '연속성은 status=2인 유한 좌표와 0<dt≤60 ms인 구간의 지속시간으로 계산한다. 모든 status를 허용하면 10초 이상은 55트랙이지만 위 표의 유효 트랙 49개와 분모가 다르다.',
        f'시각 간격 중앙값 {q["dt_s"]["median"]:.6f} s, 트랙 길이 중앙값 {q["track_duration_s"]["median"]:.3f} s. 속력은 원본 scalar km/h를 /3.6하여 m/s로 변환했다. 좌표는 IMPTC 교차로 로컬 XYZ(m)이며 SPD world와 같은 좌표계가 아니다.',
        f'보고 속력 평균 {q["speed_reported_mps"]["mean"]:.4f} m/s, 중앙값 {q["speed_reported_mps"]["median"]:.4f} m/s. 보고 속력−위치 차분 속력의 표준편차 {q["speed_reported_minus_position_mps"]["std"]:.7f} m/s. 두 값은 같은 추적 처리의 결과일 수 있어 독립 참값 검증이 아니다. 위치 차분 속력 >5 m/s 의심 사례는 {q["position_speed_gt5_observations"]}개다.',
        '센서 출처별 표본 (0=LiDAR, 1=fusion, 2=camera):', table(source_rows),
        f'신호 시간 조인 결측 **{100*q["signal_temporal_missing_fraction"]:.4f}%**, 날씨 결측 **{100*q["weather_temporal_missing_fraction"]:.4f}%**. f1/f2/f3는 최대 1.2초, 날씨는 최대 12초의 backward-asof 허용 오차를 사용했다. 개별 트랙에 적용되는 신호의 공간 매핑은 미검증이다.',
        table(conditions),
        f'트랙별 평균 속력의 평균/표준편차는 {q["between_track_mean_speed_mps"]["mean"]:.4f}/{q["between_track_mean_speed_mps"]["std"]:.4f} m/s이고, 트랙 내부 속력 표준편차의 평균은 {q["within_track_speed_std_mps"]["mean"]:.4f} m/s다. 트랙 간 차이(B)와 내부 변동을 구분했다.',
        '가감속·정지·재출발·방향 전환의 임계값 민감도는 아래 기존 표를 재사용한다. 이 표는 기존 all-status 탐색 결과이며 status=2만의 검증된 행동 정답이 아니다. 최종 이벤트 기준이나 순수 Q로 확정하지 않는다.',
        table(events),
        '지도와 XY 궤적은 기존 그림에 나란히 표시했다. 검증된 world→image 매핑이 없어 정합된 궤적 중첩이라고 주장하지 않는다. 완전/부분 횡단 수는 N/A다.',
        '## 4. 샘플 기준 후보 결정', table(factors),
        '표의 트랙 수는 데이터 전체의 지원 규모다. 각 조건 수준의 실제 트랙·시퀀스 수는 위 조건표를 따른다. 채택 여부의 최종 판단은 다음 단계 held-out 검증에서 해야 한다.',
        '## 5. MD 지시서 수행 범위',
        '| 지시서 작업 | 샘플 기준 상태 |\n| --- | --- |\n| A. 샘플 확보·출처·파일 무결성 | 완료. SPD는 파일별 전송 SHA256, IMPTC는 공식 MD5 검증 |\n| B. 실제 스키마·단위·ID·좌표 확인 및 Parquet | 완료 |\n| C. 매칭·연속성·분포·조건별 표본·대표 사례 | 완료. 미검증 공간 매핑은 명시적으로 보류 |\n| D. 후보 유지/보류 및 인계 목록 | 이 문서에 샘플 기준으로 정리 |\n| 조건부 R 정식 추정·Q 모델 확정 | 현재 샘플 감사 범위 밖 |\n| 완전 횡단·개별 보행 신호 공간 배정 | 미검증, N/A |\n| TFD 선택 재분석 | 미실행 |',
        '## 6. 서버 결과 위치',
        '기준 폴더: `/data/whereami/math/view2risk_261025/`',
        '- 이 문서: `reports/sample_audit_261025.md`\n'
        '- SPD 정제표: `data/processed/spd_pedestrian_pairs.parquet`\n'
        '- IMPTC **샘플** 정제표: `data/processed/stage_samples/imptc_pedestrian_tracks.parquet`\n'
        '- SPD 근거: `reports/spd_metrics.json`, `reports/spd_schema_report.md`, `reports/r_quality_report.md`, `reports/spd_condition_counts.csv`\n'
        '- IMPTC 샘플 근거/데이터 사전: `reports/stage_samples/`\n'
        '- SPD 그림: `reports/figures/` 중 SPD 파일. IMPTC 샘플 그림: `reports/stage_samples/figures/`\n'
        '- 이 문서의 표본 수 대조·입력 해시: `reports/sample_audit_261025.validation.json`',
        '**주의: `data/processed/imptc_pedestrian_tracks.parquet` 및 루트 `reports/factor_decision_table.csv`는 기존 Full Set 01 감사 결과다. 샘플 전용 인계에는 위 stage_samples 경로와 이 문서의 후보표를 사용한다.**',
        '이번 문서 생성은 기존 표 재사용 및 표본 수 대조만 수행했다. 모델 학습, Kalman 튜닝, 최종 R/Q, Monte Carlo, G95 계산은 수행하지 않았다. 원본 로컬 계획 MD와 서버 `plan.md`, 기존 결과를 수정하지 않았다.',
    ]
    output = RP / 'sample_audit_261025.md'
    assert not output.exists(), 'Preserve any existing report; choose a new name.'
    output.write_text('\n\n'.join(sections) + '\n')
    assert all(digest(ROOT / p) == h for p, h in before.items())
    result = dict(passed=True, scope='SPD Example + IMPTC Samples ONLY',
                  SPD_pairs=len(rdf), SPD_tracks=rdf.track_uid.nunique(),
                  IMPTC_observations=len(qdf), IMPTC_tracks=qdf.track_uid.nunique(),
                  IMPTC_status2=int((qdf.status == 2).sum()),
                  reused_inputs_unchanged=True, source_sha256=before,
                  report_sha256=digest(output), models_trained=False)
    (RP / 'sample_audit_261025.validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=True, report=str(output), bytes=output.stat().st_size)))


if __name__ == '__main__':
    main()
