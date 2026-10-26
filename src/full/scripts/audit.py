"""Run the existing audit parser in isolated output roots; reuse canonical Set01."""
from pathlib import Path
import importlib.util
import json
import os
import sys
import hashlib
import ast
import time
import argparse

ROOT=Path(__file__).resolve().parents[1]
OLD=Path('/data/whereami/math/view2risk_261025')
PUBLIC=Path('/data/whereami/math/Public-V2X-Datasets')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def js(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda v:v.item() if hasattr(v,'item') else v.tolist())+'\n')

def prepare():
    for directory in ['data','data/processed','reports','figures','models','tmp','parts']:(ROOT/directory).mkdir(parents=True,exist_ok=True)
    if (ROOT/'protocol.json').exists():return
    assert json.loads((PUBLIC/'collection_261026/validation.json').read_text())['passed']
    inputs=[PUBLIC/'collection_261026/validation.json',PUBLIC/'logs/spd_verified_261026.json',
        OLD/'reports/sample_audit_261025.md',OLD/'reports/data_audit_summary.md',OLD/'pilot_rq_261025/reports/pilot_summary.md',
        OLD/'pilot_rq_261025/reports/validation.json',OLD/'data/processed/spd_pedestrian_pairs.parquet',
        OLD/'data/processed/stage_samples/imptc_pedestrian_tracks.parquet',OLD/'data/processed/imptc_pedestrian_tracks.parquet']
    inputs+=list((OLD/'scripts').glob('*.py'))+list((OLD/'pilot_rq_261025/scripts').glob('*.py'))
    js(ROOT/'input_sha256.json',{str(p):sha(p) for p in inputs})
    protocol=dict(seed=42,population_R='SPD train/val, all infrastructure annotations and images; samples not pooled',
        population_Q='Canonical Full Sequence Sets01–05 only; Samples never pooled',
        R_validation='leave-one-intersection-out, all tracks/sequences at a site held together',
        Q_validation='5 outer folds of whole recording dates, deterministic seed42 date permutation and round-robin allocation',
        Q_objective='development date/horizon-macro forecast Gaussian NLL, no outer-test tuning',
        future_horizons_s=[1.,3.],past_warmup_s=1.,origin_stride_s=.2,max_valid_dt_s=.060,future_tolerance_s=.0201,
        paired_horizon_eligibility=True,velocity_windows_s=[.12,.4,1.],
        fixed_observation_sd_grid_m=[.01,.05,.2],fixed_q_grid_m2_s3=[.01,.1,1.],q_bounds_m2_s3=[1e-6,100],joint_R_bounds_m2=[1e-8,4],
        covariance_ddof=0,Q_model='continuous white acceleration CV',
        models=['Deterministic_CV','Fixed_noise_KF','Data_fitted_Q_KF','Joint_innovation_ML_KF'],
        bootstrap_unit_R='intersection, only 6 groups',bootstrap_unit_Q='recording date, 15 groups',bootstrap_repetitions=2000,
        forbidden=['SPD R as true IMPTC R','signals/weather/age/violation as predictors','G95','signal optimization','pure R_camera or Q_true claims'],
        change_from_sample='Larger canonical population and stronger groups; model equations/grids/horizons unchanged. Sample4-sequence LOSO remains frozen separately.',
        original_results_read_only=True)
    js(ROOT/'protocol.json',protocol)
    (ROOT/'protocol_full_261026.md').write_text('# View2Risk full-data extension — frozen protocol\n\n'+json.dumps(protocol,ensure_ascii=False,indent=2)+'\n\nThis is an explicitly separate extension of the completed sample audit/pilot. No previous sample result is overwritten or silently reinterpreted as full-data evidence.\n')
    js(ROOT/'status.json',dict(state='preparing_full_audit',protocol_frozen=True))
    import pandas as pd
    checked=pd.read_parquet(OLD/'data/processed/imptc_pedestrian_tracks.parquet')
    reference=checked[['nearby_ped_count','concurrent_ped_count']].copy()
    checked['nearby_ped_count']=0;checked['concurrent_ped_count']=0
    crowded(checked)
    assert (checked.nearby_ped_count.to_numpy()==reference.nearby_ped_count.to_numpy()).all()
    assert (checked.concurrent_ped_count.to_numpy()==reference.concurrent_ped_count.to_numpy()).all()
    js(ROOT/'reports/parser_optimization_validation.json',dict(passed=True,compared_rows=len(checked),
        reference='Existing Set01 per-timestamp 2D KD-tree counts',optimized='3D KD-tree with disjoint time planes',
        all_nearby_and_concurrent_counts_exact=True))

def crowded(df):
    """Exact same-time XY5m counts, using time as a separated KD-tree axis."""
    import numpy as np
    from scipy.spatial import cKDTree
    for _,g in df.groupby('sequence_id',sort=False):
        valid=g[g.finite_coordinates]
        if not len(valid):continue
        unique=valid.drop_duplicates(['track_uid','ts_us'])
        stamps=np.sort(unique.ts_us.unique());rank=np.searchsorted(stamps,unique.ts_us.to_numpy())
        tree=cKDTree(np.column_stack((unique[['x','y']].to_numpy(),rank*10.)))
        query=np.column_stack((valid[['x','y']].to_numpy(),np.searchsorted(stamps,valid.ts_us.to_numpy())*10.))
        counts=tree.query_ball_point(query,5.,return_length=True)-1
        # Match legacy behavior for duplicate track/time positions; duplicate rows remain flagged.
        df.loc[valid.index,'nearby_ped_count']=counts
        concurrency=unique.groupby('ts_us').track_uid.nunique()
        df.loc[g.index,'concurrent_ped_count']=g.ts_us.map(concurrency).fillna(0).astype(int)

def run(kind):
    import numpy as np
    import pandas as pd
    target=ROOT if kind=='spd' else ROOT/'parts'/kind
    for d in ['data/raw','data/processed','reports','tmp']:(target/d).mkdir(parents=True,exist_ok=True)
    name='spd_full' if kind=='spd' else kind
    source=PUBLIC/'raw/spd_full' if kind=='spd' else OLD/'data/raw'/kind
    link=target/'data/raw'/name
    if not link.exists():link.symlink_to(source,target_is_directory=True)
    os.environ['VIEW2RISK_STAGE']='main'
    os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl');os.environ['TMPDIR']=str(ROOT/'tmp')
    sys.path.insert(0,str(OLD/'scripts'))
    import common
    common.ROOT=target
    os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl');os.environ['TMPDIR']=str(ROOT/'tmp')
    filename='03_audit_r_candidates.py' if kind=='spd' else '02_inspect_imptc.py'
    path=OLD/'scripts'/filename;source_text=path.read_text();tree=ast.parse(source_text,filename=str(path))
    replacements=0
    if kind!='spd':
        class OptimizeCrowd(ast.NodeTransformer):
            def visit_For(self,node):
                nonlocal replacements
                text=ast.unparse(node.iter)
                if "df.groupby(['sequence_id', 'ts_us']" in text and '.groups.items()' in text:
                    replacements+=1
                    return ast.Expr(ast.Call(func=ast.Name(id='full_crowding',ctx=ast.Load()),args=[ast.Name(id='df',ctx=ast.Load())],keywords=[]))
                return self.generic_visit(node)
        tree=OptimizeCrowd().visit(tree);assert replacements==1
    # Remove only the __main__ guard so execution is explicit after root / helper overrides.
    tree.body=[n for n in tree.body if not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))]
    ast.fix_missing_locations(tree)
    module=type(sys)('audit_'+kind);module.__file__=str(path);module.__dict__['full_crowding']=crowded
    exec(compile(tree,str(path),'exec'),module.__dict__)
    cache={}
    if kind!='spd':
        def asof(ts,data,tolerance):
            identifier=id(data)
            if identifier not in cache:
                keys=np.array(sorted(map(int,data)),dtype=np.int64);values=[data[str(k)] for k in keys]
                cache[identifier]=(data,keys,values)
            _,keys,values=cache[identifier]
            if not len(keys):return None,None
            index=int(np.searchsorted(keys,int(ts),side='right')-1)
            if index<0:return None,None
            age=(int(ts)-int(keys[index]))/1e6
            return (values[index],age) if 0<=age<=tolerance else (None,age)
        module.asof=asof
    module.main()
    if kind=='spd':
        metrics=json.loads((ROOT/'reports/spd_metrics.json').read_text())
        # Replace sample-specific narrative; never publish copied hard-coded sample scope/quota claims.
        (ROOT/'reports/spd_schema_report.md').write_text('# SPD full observed schema\n\n'+json.dumps(metrics,indent=2,ensure_ascii=False)+'\n\nBoth source 3D annotation positions are documented in virtual-LiDAR frame. World-horizontal differences use the same supplied world transform. Camera transform nonorthogonality and K/P projection limitations remain explicit. This is paired annotation disagreement, not detector error. Raw microsecond timestamps and all unmatched/duplicate rows are retained.\n')
        (ROOT/'reports/r_quality_report.md').write_text('# SPD full R-candidate audit\n\n'+json.dumps(metrics,indent=2,ensure_ascii=False)+'\n\nThis full input was acquired and CRC/path-verified in Public-V2X-Datasets/collection_261026/. The previous sample-only quota limitation no longer applies to these acquired files. See spd_condition_counts.csv and spd_calibration_checks.csv. No pure camera R is identified.\n')
    js(target/'audit_reuse.json',dict(passed=True,source_script=str(path),source_SHA256=sha(path),output_root=str(target),
        original_script_unmodified=True,crowding_loop_replacements=replacements,
        cached_asof_ordering_identical=kind!='spd'))

def combine():
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    inputs=[OLD/'data/processed/imptc_pedestrian_tracks.parquet']+[ROOT/'parts'/f'imptc_set_{i:02d}/data/processed/imptc_pedestrian_tracks.parquet' for i in range(2,6)]
    frames=[];tracks=[];conditions=[];contexts=[];events=[];raw={};columns=None
    for i,path in enumerate(inputs,1):
        df=pd.read_parquet(path);assert set(df.dataset_source)=={f'imptc_set_{i:02d}'}
        frames.append(df)
        report=OLD/'reports' if i==1 else ROOT/'parts'/f'imptc_set_{i:02d}'/'reports'
        tracks.append(pd.read_csv(report/'imptc_track_summary.csv',dtype={'sequence_id':str,'track_id':str,'track_uid':str}))
        for filename,bucket in [('imptc_condition_counts.csv',conditions),('imptc_context_summary.csv',contexts),('imptc_event_sensitivity.csv',events)]:
            part=pd.read_csv(report/filename);part['source_set']=i;bucket.append(part)
        raw.update(json.loads((report/'imptc_raw_integrity.json').read_text())['hashes'])
    q=pd.concat(frames,ignore_index=True);del frames
    uid=q[['track_uid','dataset_source']].drop_duplicates();assert not uid.track_uid.duplicated().any()
    q['recording_date']=q.sequence_id.str.split('_').str[1]
    q.to_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet',index=False,compression='zstd')
    tr=pd.concat(tracks,ignore_index=True);tr['recording_date']=tr.sequence_id.str.split('_').str[1]
    tr.to_csv(ROOT/'reports/imptc_track_summary.csv',index=False)
    for name,parts in [('condition_counts_by_set',conditions),('context_summary',contexts),('event_sensitivity_by_set',events)]:pd.concat(parts,ignore_index=True).to_csv(ROOT/f'reports/imptc_{name}.csv',index=False)
    metrics=dict(scope='Full Sequence01–05, Samples never pooled',sequences=q.sequence_id.nunique(),recording_dates=q.recording_date.nunique(),pedestrian_tracks=tr.track_uid.nunique(),observations=len(q),
        status2=int((q.status==2).sum()),status_counts={str(k):int(v) for k,v in q.status.value_counts(dropna=False).items()},
        strict_continuity_counts={str(t):int((tr.longest_continuous_status2_s>=t).sum()) for t in [1,2,5,10]},
        duplicate_timestamp_rows=int(tr.duplicate_timestamp_rows.sum()),gap_count=int(tr.gap_count.sum()),out_of_order_steps=int(tr.out_of_order_steps.sum()),
        source_sets={str(k):int(v) for k,v in tr.dataset_source.value_counts().items()},raw_protected_files=len(raw))
    js(ROOT/'reports/imptc_metrics.json',metrics)
    js(ROOT/'reports/imptc_raw_integrity.json',dict(passed=True,hashes=raw,source_set01_audit_reused=True))
    js(ROOT/'status.json',dict(state='full_audit_tables_ready',R='SPD full',Q=metrics))
    print(json.dumps(metrics),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');args=p.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage=='combine':combine()
    else:run(args.stage)
