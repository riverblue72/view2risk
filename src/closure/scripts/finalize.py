"""MD-by-MD completion evidence and organized server-only deliverables."""
from pathlib import Path
import json,hashlib,os,time,sys,platform
ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT.parents[1]
BASE=Path('/data/whereami/math/full_rq_261026')
OLD=Path('/data/whereami/math/view2risk_261025')
import numpy as np
import pandas as pd
from PIL import Image

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def csv(df,name):df.to_csv(ROOT/'reports'/name,index=False,encoding='utf-8-sig',na_rep='N/A')
def js(name,obj):(ROOT/'reports'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else x.tolist())+'\n')
def table(df):
    f=df.copy().fillna('N/A');return '\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in [list(f.columns),['---']*len(f.columns),*f.itertuples(index=False,name=None)])

def checklist():
    rows=[]
    for number,line in enumerate((ROOT/'docs/View2Risk_Data_Audit_Plan.md').read_text().splitlines(),1):
        if not line.startswith('- [ ]'):continue
        task=line[6:].strip();status='완료';note=''
        if '성공·실패·중복' in task:evidence=BASE/'reports/spd_metrics.json'
        elif 'camera_timestamp' in task:evidence=BASE/'reports/spd_frame_inventory.csv'
        elif '좌표계가 실제로 동일' in task:
            evidence=ROOT/'reports/calibration_validation.json';status='검사완료_원인제약잔존';note='공식 K 규약 확인, world roundtrip 확인. 카메라 변환행렬 nonrigidity 원인은 미해결; 원본 교정 안 함.'
        elif '오차 벡터' in task:evidence=BASE/'models/r_pair_proxy_params.json'
        elif '자기상관' in task:evidence=BASE/'reports/r_fixed_time_autocorrelation.csv'
        elif '거리·가림·bbox' in task:evidence=ROOT/'reports/r_conditions.csv'
        elif '오류 사례' in task:evidence=ROOT/'reports/calibration_cases.csv'
        elif '1/2/5/10' in task:evidence=BASE/'reports/continuity_count_comparison.json'
        elif '타임스탬프' in task:evidence=BASE/'reports/imptc_raw_integrity.json'
        elif '`status`' in task:evidence=BASE/'reports/imptc_full_condition_support.csv'
        elif '원본 제공 속력' in task:evidence=ROOT/'reports/quality_flags.csv'
        elif 'ID 스위치' in task:
            evidence=ROOT/'reports/quality_flags.csv';note='급점프·불일치 의심 플래그; 독립 ID-switch 정답 없음. 모든 원시 행 유지.'
        elif '평균 속력' in task:evidence=ROOT/'figures/q_quality.png'
        elif '정지·감속' in task:evidence=BASE/'reports/imptc_strict_event_sensitivity.csv'
        elif '영상/지도' in task:evidence=ROOT/'figures/provider_compare_01.png'
        elif '보행자 신호·날씨' in task:evidence=ROOT/'data/imptc_signal_join.parquet'
        elif '완전히 통과' in task or '횡단보도 영역' in task:
            evidence=ROOT/'reports/crossing_counts.csv';status='완료_규칙기반';note='지도 양 끝 landing+연속 관측 기준. 독립 manual GT가 아닌 operational labels.'
        elif '전체 Pedestrian' in task:evidence=BASE/'reports/full_population_inventory.json'
        elif '보행자 트랙 수' in task:evidence=BASE/'reports/full_population_inventory.json'
        elif '공식 링크' in task:evidence=OLD/'reports/dataset_inventory.csv'
        elif '라이선스' in task:
            evidence=OLD/'reports/source_provenance.json';note='출처 및 제공 문서 확인. 코드 라이선스를 데이터 재배포 허가로 간주하지 않음.'
        elif '폴더 구조·파일' in task:evidence=OLD/'reports/dataset_inventory.csv'
        elif 'HTML' in task:evidence=ROOT/'reports/preliminary_claims.csv'
        elif 'SPD `data_info`' in task:evidence=OLD/'reports/spd_schema_report.md'
        elif 'IMPTC `track_data`' in task:evidence=OLD/'reports/imptc_schema_report.md'
        elif '위치·시간·ID' in task:evidence=BASE/'data/processed/imptc_pedestrian_tracks.parquet'
        elif '문서 예제' in task:evidence=OLD/'pilot_rq_261025/reports/schema_mismatch.md'
        elif 'R용 유효' in task:evidence=ROOT/'reports/calibration_validation.json'
        elif 'Q용 유효' in task:evidence=BASE/'reports/q_validity_funnel.csv'
        elif '조건 후보별' in task:evidence=ROOT/'reports/r_conditions.csv'
        elif '전체 데이터' in task:evidence=BASE/'reports/full_population_inventory.json'
        elif 'R에서 채택' in task or 'Q에서 채택' in task or 'B는 개인별' in task or '범위 축소' in task:
            evidence=ROOT/'reports/decisions.csv';note='현재 진단/통제 변수와 다음 단계 우선 후보를 결정; Test로 조건부 모델을 선정하지 않음.'
        elif '컬럼 목록과 단위' in task:evidence=ROOT/'reports/columns.csv'
        else:raise AssertionError(f'Unmapped checklist task: {task}')
        assert evidence.exists(), str(evidence)
        rows.append(dict(plan='View2Risk_Data_Audit_Plan.md',line=number,task=task,status=status,evidence=str(evidence),note=note))
    assert len(rows)==37
    pilot=OLD/'pilot_rq_261025/reports'
    for task,name in [('현재 샘플 범위 및 유효 구간','pilot_summary.md'),('R 추정·꼬리·시간 상관·제약','01_r_pilot.md'),
       ('Q 1초/3초·단위·관측 잡음 민감도','02_q_pilot.md'),('홀드아웃 포함률·영역·실패 사례','03_validation.md'),
       ('가능성 판정 및 통합 주장 보류','pilot_summary.md'),('실행·입력·버전·seed·hash','pilot_summary.md')]:
        assert (pilot/name).exists()
        rows.append(dict(plan='View2Risk_RQ_Pilot_Next_Step_261025.md',line=np.nan,task=task,status='기존완료_보존',evidence=str(pilot/name),note='원래4시퀀스 샘플 실험 보존. 전체 확장판은 별도 날짜/교차로 묶음 검증.'))
    result=pd.DataFrame(rows);csv(result,'checklist.csv');return result

def main():
    checks={n:json.loads((ROOT/'reports'/n).read_text()) for n in ['crossing_validation.json','calibration_validation.json','quality_validation.json','tfd_validation.json','remaining_validation.json','review_validation.json']}
    assert all(v['passed'] for v in checks.values())
    for p,h in json.loads((BASE/'manifest.json').read_text()).items():assert sha(BASE/p)==h,p
    prior_inputs=json.loads((BASE/'input_sha256.json').read_text())
    for p,h in prior_inputs.items():assert sha(Path(p))==h,p
    frozen=json.loads((ROOT/'execution_freeze.json').read_text())['sha256']
    for p,h in frozen.items():assert sha(Path(p))==h,p
    # New raw calibration and context hashes are checked again after all analysis.
    raw_hashes=json.loads((ROOT/'reports/calibration_sources.json').read_text())
    raw_hashes.update(checks['crossing_validation.json']['source_signal_SHA256'])
    for p,h in raw_hashes.items():assert sha(Path(p))==h,p
    events=pd.read_csv(ROOT/'reports/crossings.csv');tracks=pd.read_csv(ROOT/'reports/tracks.csv')
    all_events=pd.read_csv(ROOT/'reports/crossing_sensitivity_events.csv')
    full=events[events.classification=='complete_rule']
    assert len(full)==846 and full.track_uid.nunique()==787
    assert len(tracks)==1920 and tracks.track_uid.nunique()==1920
    assert len(events)==1415 and not events.event_id.duplicated().any()
    geo=pd.read_csv(ROOT/'reports/geometry.csv')
    projection=pd.read_csv(ROOT/'reports/projection.csv')
    flags=pd.read_csv(ROOT/'reports/quality_flags.csv')
    group=full.groupby('signal_group').agg(complete_events=('event_id','size'),track_groups=('track_uid','nunique'),sequences=('sequence_id','nunique'),dates=('recording_date','nunique')).reset_index()
    group=group.merge(geo[['signal_group','length_m','width_m']],validate='one_to_one')
    csv(group,'crossing_full.csv')
    signal=full.groupby(['entry_signal_code','signal_transition_within_1s']).agg(events=('event_id','size'),tracks=('track_uid','nunique')).reset_index()
    signal['interpretation']='recorded signal at derived entry, not verified violation label';csv(signal,'entry_signal.csv')
    sensitivity=all_events[all_events.classification=='complete_rule'].groupby('config').agg(events=('event_id','size'),tracks=('track_uid','nunique'),sequences=('sequence_id','nunique'),dates=('recording_date','nunique')).reset_index()
    csv(sensitivity,'sensitivity.csv')
    decisions=pd.read_csv(BASE/'reports/factor_decision_table.csv')
    decisions['audit_update']='기존 품질 감사 결론 유지'
    decisions['next_stage_role']='diagnostic_only_or_hold_as_original_plan'
    for i,row in decisions.iterrows():
        if row.component=='R':
            decisions.loc[i,'audit_update']='공식 K 투영 규약 확인; 조건별 표본·잔차 표 보완'
            decisions.loc[i,'next_stage_role']='first_conditional_candidate_distance' if row.factor=='distance' else 'retain_occlusion_control' if row.factor=='occlusion' else 'bbox_redundancy_check' if row.factor=='bbox_size' else 'hold_sparse_truncation_strata' if row.factor=='truncation' else 'timing_QC_control'
        elif row.factor=='pedestrian_signal':
            decisions.loc[i,'audit_update']='공식 도식과 지도 topology·origin 연결, 공간/시간 join 저장; 독립 survey GT 아님'
            decisions.loc[i,'next_stage_role']='spatial_temporal_audit_complete_but_excluded_from_current_Q_predictors'
        elif row.factor=='completed_crossing':
            decisions.loc[i,'audit_update']='complete_rule846회/787트랙; 미완료 접촉379트랙; 접촉없음754트랙'
            decisions.loc[i,'next_stage_role']='operational_complete_partial_labels_available_independent_GT_pending'
        elif row.factor in ['current_speed','acceleration_deceleration','stop_restart','heading_change']:
            decisions.loc[i,'audit_update']='기존 행동 후보 임계값 유지; 후보별 지원 수/잔차 진단 존재'
            decisions.loc[i,'next_stage_role']='retain_for_next_conditional_Q_design_no_GT_behavior_claim'
        elif row.factor=='sensor_source':decisions.loc[i,'next_stage_role']='required_stratification_control'
        elif row.component=='B':decisions.loc[i,'next_stage_role']='initial_speed_prior_only_not_separate_UQ_module'
        elif row.factor=='weather':decisions.loc[i,'next_stage_role']='support_audit_only_not_current_predictor'
    csv(decisions,'decisions.csv')
    columns=pd.read_csv(BASE/'reports/data_dictionary.csv')
    csv(columns,'source_columns.csv')
    derived=pd.DataFrame([
       ('event_id','string','config:sequence/track:component:first_map_ts_us','unique event key; not unique person'),
       ('classification','category','complete_rule / partial_censored / partial_missing_landing / returned_same_side / other uncertain','operational rule, not independent GT'),
       ('signal_group','category','f1/f2/f3','official diagram + semantic geometry/origin, manually registered'),
       ('entry_signal_code','provider_code','4 green /10 red /other provider codes /N/A','previous recorded signal within1.5s; 1Hz granularity'),
       ('signal_transition_within_1s','bool','true/false','transition near derived entry; red does not establish legal violation'),
       ('entry_ts_s / exit_ts_s','UTC_epoch_seconds','s','interpolated gate crossing within contiguous status2 segment'),
       ('duration_s','seconds','s','derived exit-entry, no G95 model fitted'),
       ('retained_polygon_fraction','fraction','0..1','fraction inside buffered crosswalk rectangle between gates'),
       ('crosswalk_map_fraction','fraction','0..1','mapped crosswalk points between gates'),
       ('primary_class','category','has_complete_rule /touch_without_complete /no_accepted_map_touch','mutually exclusive per sequence-track; counts sum1920'),
       ('length_m / width_m','metres','m','PCA rectangle0.5-99.5% map quantiles, not surveyed lane length'),
       ('inside_bbox_pct','percent','0..100','annotation center projection consistency, not detector/calibration GT accuracy'),
       ('q_velocity_increment_proxy_native2_per_s3','native_units_squared_per_seconds_cubed','mean dv^2/(2dt)','TFD diagnostic; not original q≈.05 estimator or separated process noise'),
       ('flag_*','bool','true/false','retained quality suspicion, not established ID switch'),
    ],columns=['field','type_or_unit','definition','limitation']);csv(derived,'columns.csv')
    checklist_df=checklist()
    result=[]
    for label,value in tracks.groupby('primary_class').size().items():
        result.append(dict(topic='IMPTC_crossing',measure=label,value=int(value),unit='sequence_track_group',interpretation='mutually_exclusive_base_rule'))
    for label,value in events.groupby('classification').size().items():
        result.append(dict(topic='IMPTC_crossing',measure=label,value=int(value),unit='episode',interpretation='one track can have multiple crossing episodes'))
    for row in geo.itertuples():
        result.append(dict(topic='geometry',measure=row.signal_group+'_length',value=row.length_m,unit='m',interpretation='PCA_of_official_semantic_map_not_survey_GT'))
    for row in projection[projection.annotation=='camera'].itertuples():
        result.append(dict(topic='SPD_projection',measure=row.projection,value=row.inside_bbox_pct,unit='percent',interpretation='annotation_consistency_not_independent_accuracy'))
    csv(pd.DataFrame(result),'result.csv')
    # Descriptive, non-predictive entry counts: no signal legality/behavior GT.
    summary=f'''# View2Risk MD 추가 감사 결과 — 261026

**전체 공개 시퀀스로 남은 관측 가능 항목을 추가 실행했다.** 기존 R/Q 모델·예측·결과는 보존했다. 핵심 추가분은 공식 지도 기반 완전/부분 횡단 분류, f1/f2/f3 공간·시간 연결, 공식 SPD K 투영 규약 확인, 조건별 R 분포와 전 행 품질 플래그다.

## 1. 횡단 완료/부분 관측

IMPTC Full01–05의 1,920트랙·1,710,765관측을 그대로 유지했다. 기준 설정의 트랙 분류는 서로 배타적이다.

{table(pd.read_csv(ROOT/'reports/track_counts.csv'))}

`has_complete_rule`: 최소1회의 완료 규칙을 만족. `touch_without_complete`: 횡단보도 접촉은 있으나 완료 규칙 미충족이며, 부분 관측·landing 부족·되돌아감 등을 포함한다. `no_accepted_map_touch`: 유효 status2 관측에서0.25m 지도 매칭 기준 접촉 없음. 세 트랙 수 합은1,920이다.

완료 이벤트는 **846회 /787트랙**이다. 트랙별 개수와 이벤트 개수는 다르며, 같은 트랙이 여러 횡단보도를 지날 수 있다.

{table(group)}

## 2. 사전에 정한 완료 규칙과 민감도

공식 지면 지도 crosswalk 점을 연결 성분으로 나눈 뒤 PCA 축의0.5~99.5% 경계를 사용했다. 전체 원본의 `status=2`, 유한 좌표, `0<dt<=0.060s` 연속 구간만 완료 여부를 판별한다. 기본 기준은 양 끝 경계 밖0.25m, 폭 여유0.75m, 시작/끝 landing의 sidewalk/curb 지도 매칭0.25m 이내 및0.12초 지속이다. landing 검색은 해당 이벤트 앞뒤3초, 끝단4m 범위다.

반대편 양 끝의 관측이 있고, 진입~이탈 사이95% 이상이 여유 포함 횡단보도 직사각형에 있으며,50% 이상이 crosswalk 지도점이고,5m/s 초과 급점프가 없으면 `complete_rule`이다. 같은 쪽 복귀는 `returned_same_side`, 시작/끝 관측이 잘리면 `partial_censored`, landing 근거 부족은 `partial_missing_landing`이다. 불충족/이상 사례는 삭제하지 않고 분류해 남긴다. 모든 설정과 샘플링 seed는 집계 전 protocol.json에 고정했다.

{table(sensitivity)}

이 수치는 **공식 지도와 기록 궤적에 적용한 운영 규칙에 따른 분류**다. 독립적인 사람이 표시한 완전 횡단 정답이나 분류 정확도는 아니다. 일부 시각적으로 완전해 보이는 경로도 landing 관측이 짧으면 보수적으로 미완료에 남는다. 포함률·모델 점수·G95를 좋게 만들기 위해 경계를 조정하지 않았다.

## 3. 신호 그룹의 공간·시간 연결

[공식 신호 도식](https://github.com/kav-institute/imptc-dataset/blob/main/images/traffic_light_signal_groups.jpg), [좌표 원점 설명](https://github.com/kav-institute/imptc-dataset#coordinate-system), [공식 지면 분류](https://github.com/kav-institute/imptc-dataset/blob/main/data_formats/ground_plane.md)를 대조했다. 긴 횡단보도와 원점의 위치, 양쪽 짧은 횡단보도 topology로 component1=f2, component2=f1, component3=f3를 연결했다. 도식에서 수동 선택한 중심3개+원점으로 아핀 등록 시 중심 RMSE2.02px이며,6개 그룹 순열 중 다음 후보15.41px보다 일관됐다. 이는 연결 근거이며 측량 정밀도 검증은 아니다. `map_signal_registration.png`, `registration_alternatives.csv`에 근거를 남겼다.

신호는 미래를 보지 않는 backward join으로 마지막 기록을 사용하고1.5초보다 오래되면 결측 처리했다. 횡단보도 밖의 관측에는 가장 가까운 신호를 강제 배정하지 않았다. 공간·시간 연결 Parquet은 data/imptc_signal_join.parquet이다.

완료 이벤트의 진입 시점 신호:

{table(signal)}

신호 기록은1Hz이고 진입 시점도 지도 경계 보간값이다. ±1초 내 전환 여부를 별도로 표시했다. **빨간색 기록에서 진입한 이벤트를 검증된 신호 위반 정답으로 취급하지 않는다.** 이번 작업은 연결 감사이며, 신호/날씨를 기존 Q 예측 변수에 추가하거나 모델을 다시 맞추지 않았다.

## 4. SPD calibration 추가 점검

공식 DAIR-V2X [영상 시각화 도우미](https://github.com/AIR-THU/DAIR-V2X/blob/main/tools/visualize/vis_utils.py)의 `get_cam_calib_intrinsic`는 `cam_K`를3×4 형태에 넣는다. 해당 함수만 AST로 읽어21프레임에서 직접 실행하고 우리 K 구성과 정확히 일치함을 확인했다. 모든11,275프레임의 이미지 크기와 intrinsic width/height도 일치했다.

{table(projection[['annotation','projection','pairs','inside_bbox_pct']])}

K 방식은 기존 계산과 일치했다. 제공 P, 추가 plumb_bob distortion, 카메라 행렬을 강제로 SO(3)화하는 대안은 진단용으로만 대조했다. 어느 것도 원본이나 기존 투영/모델에 적용하지 않았다. 이 결과는 주석 중심과 공유2Dbox의 일관성이고 독립 calibration 오차율이 아니다.

제공 카메라 변환행렬11,275개 모두 정규직교 회전 조건을 만족하지 않았다. 일반 역행렬 roundtrip 최대 오차는{checks['calibration_validation.json']['general_inverse_roundtrip_max_m']:.3g}m이나, 전치행렬을 역으로 오용하면 복원 오차 p95={checks['calibration_validation.json']['transpose_inverse_error_p95_m']:.3f}m이다. **K/P 사용 규약은 정리했지만 nonrigidity의 생성 원인은 공개 자료에서 확인하지 못했다.** 공급자 보정 정답 없이 행렬을 임의로 고치지 않았다. R은 계속 paired annotation discrepancy proxy다.

## 5. 조건별 R, Q 품질과 변수 인계

거리·bbox·시각차 사분위와 가림·절단 수준18개 층에 대해 관측·트랙 그룹·시퀀스·교차로 수, 잔차 RMSE/median/p95, track-macro RMSE, 편향/공분산을 추가했다(`r_conditions.csv`). 거리4구간의 RMSE는 약0.167/0.211/0.284/0.452m였다. 이는 여러 장소·트랙이 섞인 기술통계이고 거리의 인과 효과나 조건부 모델 향상 증거는 아니다.

기존 행동 임계값별 지원 수와 예측 진단을 보존했다. 전 관측 품질 플래그를 새 Parquet으로 내보냈다. 위치 차분 속력5m/s 초과104관측/5트랙,20m/s 초과0관측,0초 이하 또는60ms 초과 interval11개다. ID switch 의심을 위한 감사 플래그이지 ID-switch 정답은 아니다. B의 트랙 평균 속력과 트랙 내 표준편차 그림도 분리했다.

인계 결정: R은 거리 조건을 다음 조건부 설계의 우선 후보, 가림은 통제/진단 변수로 유지한다. bbox는 거리와 중복 점검, 절단은 희소 층 때문에 보류한다. Q의 속도·가감속·정지/재출발·방향 변화는 진단 후보로 유지하고 source_type은 통제한다. B는 초기 속도 사전분포 후보이며 별도 UQ 모듈로 만들지 않는다. 신호는 공간/시간 연결까지 확보했지만 현재 예측 모델에서는 제외한다. 채택 여부는 데이터 인계/설계 역할이며 Test를 본 뒤 조건부 모델 우수성을 선정한 것이 아니다. 세부 컬럼/단위는 source_columns.csv와 columns.csv, 결정은 decisions.csv다.

## 6. TFD와 기존 HTML 수치

TFD Example 단일 infrastructure view만 사용했다. 겹친 클립에서 같은 city/intersection/id/timestamp 관측을 한 번만 가중해16,739고유 관측,16,016유효 인접 increment의 속도벡터·위치 차분 일관성을 추가 점검했다. source ID를 실제 독립 사람으로 세지 않았다.

`q_velocity_increment_proxy = mean((Δvx²+Δvy²)/(2Δt))`의 사이트별 진단을 명시적 산식/단위 가정과 함께 저장했다. 이 값은 관측 잡음과 분리한 Q도, 기존 HTML의 q≈.05 재현도 아니다. 기존 HTML에는 q의 추정기·Δt 방식·68구간/4완전 횡단 선정 규칙이 없고, 찾아본 원래 PoC 스크립트에도 해당 q 계산은 없었다. 숫자만 맞춰 재현했다고 주장하지 않았다. `preliminary_claims.csv`에 재현 가능/불가와 근거를 분리했다. 원래 분석 코드를 확보해야 정확한 과거 수치 재현이 가능하다.

## 7. MD 항목별 완료 근거와 실제 남은 제약

`checklist.csv`는 원본 감사 MD의 체크박스37개와 파일럿 보고 필수6개를 각각 결과 파일에 연결한다. 실제 가능한 추가 집계/검사는 수행했고, 원본 데이터 수정·기존 보고서 덮어쓰기 없이 결과를 추가했다. 이전 '전부 완료'를 물리 참값 식별까지 완료했다는 뜻으로 읽으면 안 된다.

- 횡단/신호: 추가 데이터가 없어 못 한다고 남겨두지 않고, 공식 geometry로 운영 규칙과 공간/시간 연결을 만들었다. 독립 수동 GT는 여전히 없다.
- Calibration: 공식 K 규약 확인과 원본 행렬 수치 검사는 완료. 행렬 nonrigidity 원인은 공급자 설명/독립 보정 없이 확정 불가다.
- 과거 q≈.05: 원래 코드·산식이 없어 동일 수치의 정확 재현은 불가. 재현 가능한 대체 진단을 별도로 제공했다.
- G95·신호 최적화·통합 순수 R/Q 주장은 MD 범위 밖이며 실행하지 않았다.

## 8. 파일과 재현

바로 볼 표는 result.csv, crossing_full.csv, crossing_counts.csv, tracks.csv, signal.csv, projection.csv, r_conditions.csv, decisions.csv, checklist.csv다. 원시 행/ID를 가진 신규 Parquet은 data/에 있다.

검증: execution_freeze.json의 사전 프로토콜/소스/입력 해시, 기존 full manifest119항목, 기존 샘플 입력·결과 해시, 이번에 읽은 raw calibration·신호 해시를 다시 대조했다. 양 끝 반대 방향/양의 시간/영역 보존/인과적 신호 연결을 확인하고,22개 층화 사례의 원시 JSON 좌표·status·시각을 독립 재조회했다. 별도의 제공 topview와4사례를 대조하는 그림도 저장했다. 같은 처리 계통의 정보라 독립 GT 정확도를 증명하지는 않는다.

CPU 실행: sbatch run.sh → sbatch run_remaining.sh → sbatch run_review.sh → python scripts/finalize.py. 이 명령은 기존 모델 학습 명령이 아니다. Python/버전·코드/결과 해시는 environment.json 및 manifest.json에 기록했다. 완료 디렉터리는 새 분석으로 덮어쓰지 않는다.
'''
    (ROOT/'reports/summary.md').write_text(summary)
    (ROOT/'README.md').write_text('# View2Risk MD 추가 감사 — 261026\n\n먼저 reports/summary.md와 reports/result.csv를 확인한다.\n기존 R/Q 모델/예측/보고서는 보존한 채 geometry·신호·calibration·조건별 잔차·품질 플래그를 추가했다.\n완료/제약 근거는 reports/checklist.csv, 프로토콜은 protocol.json, 검증은 reports/validation.json이다.\n')
    verified_figures=0
    for p in (ROOT/'figures').glob('*.png'):
        with Image.open(p) as im:im.verify()
        verified_figures+=1
    environment=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),numpy=np.__version__,pandas=pd.__version__,seed=42,CPU_only=True)
    (ROOT/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    validation=dict(passed=True,original_full_manifest_entries_verified=119,prior_sample_input_result_hashes_verified=len(prior_inputs),
       raw_calibration_and_signal_files_verified=len(raw_hashes),source_freeze_entries_verified=len(frozen),
       full_events=846,full_track_groups=787,total_track_groups=1920,total_observations_retained=1710765,
       audit_checkboxes_with_evidence=37,pilot_required_report_items_preserved=6,
       source_JSON_case_checks=22,provider_topview_comparisons=4,verified_figures=verified_figures,
       source_data_modified=False,prior_models_refit=False,prior_predictions_modified=False,
       independent_crossing_GT=False,camera_nonrigidity_cause_resolved=False,original_q005_reproduced=False,G95_computed=False)
    js('validation.json',validation)
    (ROOT/'status.json').write_text(json.dumps(dict(state='complete',audit_phase_completed=True,independent_physical_GT_claimed=False,finished_utc=time.time(),report=str(ROOT/'reports/summary.md')),indent=2)+'\n')
    # Add links within the catalog; no relocation or replacement of raw data.
    def link(dest,src):
        p=CATALOG/dest;p.parent.mkdir(parents=True,exist_ok=True)
        if p.is_symlink():assert p.resolve()==src.resolve()
        elif p.exists():raise AssertionError(str(p))
        else:p.symlink_to(os.path.relpath(src,p.parent),target_is_directory=src.is_dir())
    link('results/audit_261026',ROOT/'reports')
    link('reports/audit_261026',ROOT/'reports')
    link('code/audit_261026',ROOT/'scripts')
    link('figures/audit_261026',ROOT/'figures')
    link('data/derived/audit_261026',ROOT/'data')
    catalog_readme=CATALOG/'README.md'
    text=catalog_readme.read_text()
    marker='## MD 추가 감사 — 261026'
    if marker not in text:
        text+='\n'+marker+'\n\n[추가 보고서](reports/audit_261026/summary.md) · [핵심 CSV](results/audit_261026/result.csv) · [MD 항목별 근거](results/audit_261026/checklist.csv)\n\n공식 geometry 기반 완료/부분 횡단·신호 공간/시간 연결, SPD 투영 규약, 조건별 R와 전 행 품질 플래그를 보완했다. 기존 R/Q 결과는 results/261026/에 보존했다.\n'
        catalog_readme.write_text(text)
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and not any(x in p.parts for x in ['tmp','__pycache__']) and p.suffix!='.log':
            files.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)))
    pd.DataFrame(files).to_csv(ROOT/'reports/files.csv',index=False,encoding='utf-8-sig')
    manifest={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ['tmp','__pycache__']) and p.suffix!='.log' and p.name!='manifest.json'}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    # The catalog itself intentionally changes; freeze its current, regular files.
    cm={str(p.relative_to(CATALOG)):sha(p) for p in CATALOG.rglob('*') if p.is_file() and not p.is_symlink()
        and not any(parent.is_symlink() for parent in p.parents if parent!=CATALOG)
        and not any(x in p.parts for x in ['tmp','__pycache__']) and p.suffix!='.log' and p!=CATALOG/'catalog_manifest.json'}
    (CATALOG/'catalog_manifest.json').write_text(json.dumps(cm,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(validation),flush=True)

if __name__=='__main__':main()
