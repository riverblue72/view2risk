"""Readable handoff and strict diagnostic denominators, after raw/table verification."""
from pathlib import Path
import datetime,json
import numpy as np
import pandas as pd
from common import ROOT,js,sha,csvw,table
def main():
    rp=ROOT/'reports';proof=json.loads((ROOT/'validation.json').read_text());assert proof['passed']
    r=json.loads((rp/'spd_metrics.json').read_text());q=json.loads((rp/'imptc_metrics.json').read_text())
    df=pd.read_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet')
    fractions=dict(valid_status2_fraction=q['strict_status2_observations']/q['pedestrian_observations'],gap_interval_fraction=q['gap_count']/q['dt_s']['n'],
                   position_speed_gt5_fraction=q['position_speed_gt5_observations']/q['pedestrian_observations'])
    js(rp/'quality_fractions.json',fractions)
    strict=df.strict_documented_valid_status2 & df.finite_coordinates
    same_track=df.track_uid.eq(df.track_uid.shift())
    adjacent=same_track & df.dt.gt(0) & df.dt.le(.06)
    interval_valid=strict & strict.shift(fill_value=False) & adjacent
    events=[]
    for kind,values in [('stop',[.2,.3,.5]),('acceleration',[.3,.5,1.]),('deceleration',[.3,.5,1.]),('turn',[30.,45.,60.])]:
        for threshold in values:
            mask=(df.speed_reported_mps.lt(threshold)&strict) if kind=='stop' else (df.accel_proxy.gt(threshold)&interval_valid) if kind=='acceleration' else (df.accel_proxy.lt(-threshold)&interval_valid) if kind=='deceleration' else (df.heading_rate_deg_s.abs().gt(threshold)&interval_valid&df.speed_from_position_mps.gt(.2)&df.speed_from_position_mps.shift().gt(.2))
            start=mask & (~mask.shift(fill_value=False)|~adjacent)
            restart=(~mask)&mask.shift(fill_value=False)&interval_valid if kind=='stop' else pd.Series(False,index=df.index)
            events.append(dict(candidate=kind,threshold=threshold,valid_observations=int(mask.sum()),episodes=int(start.sum()),restarts=int(restart.sum()),
                               tracks=int(df.loc[mask,'track_uid'].nunique()),sequences=int(df.loc[mask,'sequence_id'].nunique()),
                               status_policy='2 only; dynamic derivatives require valid adjacent intervals',final_behavior_truth=False))
    csvw(rp/'imptc_strict_event_sensitivity.csv',events)
    text=f'''# View2Risk 데이터 감사 — 먼저 읽기

서버 작업 폴더: `/data/whereami/math/view2risk_261025/`

**SPD Example과 IMPTC Samples·Full Set 01을 확보하고, 정제 테이블·품질 감사·R/Q 조건 후보표를 만들었다.** 원본 데이터는 보존했다. 모델 학습, Kalman 튜닝, 최종 R/Q 행렬, 예측 Monte Carlo, G95 계산은 하지 않았다.

| 분석 범위 | 시퀀스 | 보행자 트랙 | 관측 또는 라벨 pair |
|---|---:|---:|---:|
| SPD Example | 1 | 9 | 253 pairs |
| IMPTC Samples, 별도 감사 | 4 | 61 | 56,374 observations |
| IMPTC Full Set 01, 본 감사 | {q['sequences']} | {q['pedestrian_tracks']} | {q['pedestrian_observations']:,} observations |

SPD는 기존 로컬 프로젝트의 Example을 가져와 4,011개 파일의 SHA256을 서버와 대조했다. IMPTC 압축파일 두 개는 Zenodo 공식 MD5를 검증했다. Samples와 Full에 겹치는 트랙은 독립 표본으로 합산하지 않았다. 일부 겹친 export의 수치가 달라 본 감사는 Full Set 01만 사용하고 Samples 결과는 따로 보존했다.

**R 쪽 결과:** paired annotation의 수평 위치 차이 RMSE는 **{r['RMSE_world_horizontal_xy_m']:.4f} m**다. 기존 HTML의 약 0.19 m와 일치하지만, 검출기 예측 오차나 확정된 R은 아니다. 단일 시퀀스의 9트랙에 제한되어 거리·가림별 정식 R 추정은 보류했다. 제공 camera 변환의 비정규 직교성과 시각차도 기록했다.

**Q 쪽 결과:** status=2인 관측은 **{q['strict_status2_observations']:,}개 ({100*fractions['valid_status2_fraction']:.2f}%)**다. 유효 관측이 연속 10초 이상인 트랙은 **{q['strict_continuity_counts']['10']}개**다. 60ms 초과 간격은 {q['gap_count']}개이며 전체 간격의 {100*fractions['gap_interval_fraction']:.5f}%다. 위치 차분 속력이 5m/s를 넘는 {q['position_speed_gt5_observations']}개 관측은 삭제하지 않고 의심 flag로 남겼다.

속력·가감속·정지/재출발·방향 변화·주변 인원수는 다음 단계의 진단 후보로 남겼다. `imptc_strict_event_sensitivity.csv`는 status=2와 인접 유효 간격만 사용하는 임계값 민감도 표다. 이것도 행동 참값이나 순수 Q를 뜻하지 않는다. 센서 출처는 R/Q 혼입을 구분하기 위한 통제 변수로 보존했다.

**남은 한계:** SPD 전체 데이터 확대는 공식 Drive 한도 때문에 미실행이다. IMPTC의 f1/f2/f3 신호는 시간 매칭까지 했지만, 각 보행자가 어느 횡단보도·신호에 해당하는지는 아직 확정하지 않았다. 완전/부분 횡단 수는 N/A다. 선택 사항인 TFD 재분석도 하지 않았다.

먼저 볼 파일:

- `reports/data_audit_summary.md`: 전체 근거와 조건 후보 결정
- `reports/factor_decision_table.csv`: 후보 유지·보류·제외 사유
- `reports/data_dictionary.csv`: 단위·좌표계·결측 설명
- `data/processed/spd_pedestrian_pairs.parquet`
- `data/processed/imptc_pedestrian_tracks.parquet`
- `reports/figures/`: SPD 8사례, IMPTC 6궤적과 분포 그림
- `validation.json`: 원본과 정제 테이블의 독립 비교 결과

전체 보행자 위치·시각·속력·상태를 원본과 대조했고 검증이 통과했다. 실제 사람의 교차 시퀀스 identity는 없으므로 트랙 수를 독립적인 사람 수로 해석하지 않는다. SPD와 IMPTC의 조건을 다른 교차로로 이전할 때의 검증은 다음 단계에 필요하다.
'''
    (ROOT/'README.md').write_text(text)
    js(rp/'audit_config.json',dict(scope='data/schema/quality and candidate audit only',timestamp_unit='microsecond UNIX epoch, verified actual samples',
          imptc_main_package='imptc_set_01',sample_package_separate=True,strict_valid_status=2,gap_seconds=.06,signal_backward_asof_tolerance_s=1.2,
          weather_backward_asof_tolerance_s=12,nearby_radius_m=5,source_tracks_never_silently_dropped=True,
          event_thresholds='sensitivity grids, not final classes',R_definition='paired annotation discrepancy, not detector error',Q_definition='diagnostic proxies, not separated process noise',
          pure_R_Q_identified=False,Kalman_training=False,G95=False,download_or_import_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    inventory=pd.read_csv(rp/'dataset_inventory.csv')
    inventory['download_or_import_date_utc']=[datetime.datetime.fromtimestamp((ROOT/'data/raw'/name/'extraction_complete.json').stat().st_mtime,datetime.timezone.utc).isoformat() for name in inventory.dataset]
    inventory.to_csv(rp/'dataset_inventory.csv',index=False)
    # Reindex presentation/strict-proxy additions; the independently verified original tables are unchanged.
    artifacts=[p for folder in [ROOT/'scripts',rp,ROOT/'data/processed'] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    artifacts.extend([ROOT/'README.md',ROOT/'plan.md',ROOT/'validation.json'])
    js(ROOT/'artifact_sha256.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(artifacts)})
    print('Readable handoff and strict denominators finalized',flush=True)
if __name__=='__main__':main()
