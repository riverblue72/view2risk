"""Independent persisted-table vs all original pedestrian rows and SPD labels checks."""
from pathlib import Path
from collections import Counter
import json,hashlib,math,sys,platform
import numpy as np
import pandas as pd
from PIL import Image
from common import ROOT,js,sha
def main():
    rp=ROOT/'reports';r=json.loads((rp/'spd_metrics.json').read_text());q=json.loads((rp/'imptc_metrics.json').read_text())
    rdf=pd.read_parquet(ROOT/'data/processed/spd_pedestrian_pairs.parquet');qdf=pd.read_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet')
    assert len(rdf)==r['matched_pairs']==253 and rdf.track_uid.nunique()==9
    assert not rdf.duplicated(['sequence_id','frame_id','track_id']).any()
    infra=next((ROOT/'data/raw/spd_example').glob('**/infrastructure-side/data_info.json')).parent
    info=json.loads((infra/'data_info.json').read_text());by_frame={f['frame_id']:f for f in info}
    for frame,g in rdf.groupby('frame_id'):
        f=by_frame[frame];a=json.loads((infra/f['label_camera_std_path']).read_text());b=json.loads((infra/f['label_lidar_std_path']).read_text())
        aa={x['track_id']:x for x in a if x['type'].lower()=='pedestrian'};bb={x['track_id']:x for x in b if x['type'].lower()=='pedestrian'}
        assert set(g.track_id)==set(aa)&set(bb)
        W=np.array(json.loads((infra/f['calib_virtuallidar_to_world_path']).read_text())['rotation'])
        for _,row in g.iterrows():
            x=np.array([aa[row.track_id]['3d_location'][k] for k in 'xyz']);y=np.array([bb[row.track_id]['3d_location'][k] for k in 'xyz'])
            np.testing.assert_allclose(row[['camera_label_x','camera_label_y','camera_label_z']].to_numpy(float),x,atol=1e-12)
            np.testing.assert_allclose(row[['lidar_label_x','lidar_label_y','lidar_label_z']].to_numpy(float),y,atol=1e-12)
            np.testing.assert_allclose(row[['dx','dy','dz']].to_numpy(float),W@(x-y),atol=1e-10)
            assert row.camera_timestamp==int(f['image_timestamp']) and row.lidar_timestamp==int(f['pointcloud_timestamp'])
    assert math.isclose(float(np.sqrt(np.mean(rdf.dx**2+rdf.dy**2))),r['RMSE_world_horizontal_xy_m'],abs_tol=1e-12)
    assert qdf.sequence_id.nunique()==q['sequences'] and len(qdf)==q['pedestrian_observations'] and qdf.track_uid.nunique()==q['pedestrian_tracks']
    assert set(qdf.dataset_source)=={'imptc_set_01'}
    assert not qdf.duplicated(['sequence_id','track_id','ts_us','source_row_key']).any()
    assert qdf.strict_documented_valid_status2.sum()==q['strict_status2_observations']
    assert qdf.ped_signal.isna().all(),'Do not invent a spatially matched pedestrian signal'
    groups={uid:g.sort_values('source_index') for uid,g in qdf.groupby('track_uid',sort=False)}
    n=tracks=0;raw_class=Counter()
    for p in (ROOT/'data/raw/imptc_set_01').glob('**/vrus/*/track.json'):
        j=json.loads(p.read_text());raw_class[j['overview']['class_id']]+=1
        if j['overview']['class_id']!=0:continue
        uid=p.parents[2].name+'/'+p.parent.name;g=groups[uid];v=list(j['track_data'].values())
        assert len(g)==len(v);n+=len(v);tracks+=1
        np.testing.assert_array_equal(g.ts_us.to_numpy(),np.array([int(x['ts']) for x in v],dtype=np.int64))
        np.testing.assert_allclose(g[['x','y','z']].to_numpy(),np.array([x['coordinates'] for x in v]),rtol=0,atol=1e-12)
        np.testing.assert_allclose(g.speed_reported_mps.to_numpy(),np.array([x['velocity']/3.6 for x in v]),rtol=0,atol=1e-12)
        np.testing.assert_array_equal(g.status.to_numpy(),np.array([x['status'] for x in v]))
        np.testing.assert_array_equal(g.source_type.to_numpy(),np.array([x['source_type'] for x in v]))
    assert n==len(qdf) and tracks==qdf.track_uid.nunique()==403
    for report in ['spd_raw_integrity.json','imptc_raw_integrity.json']:
        proof=json.loads((rp/report).read_text());assert proof['passed']
        for p,h in proof['hashes'].items():assert sha(p)==h
    manifest=json.loads((ROOT/'docs/spd_local_source_manifest.json').read_text())
    for name,v in manifest['files'].items():
        p=ROOT/'data/raw/spd_example'/name;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
    official=json.loads((ROOT/'docs/zenodo_record.json').read_text())
    for package in ['imptc_samples','imptc_set_01']:
        m=json.loads((ROOT/'data/raw'/package/'extraction_complete.json').read_text())['archive'];ref=next(f for f in official['files'] if f['key']==m['name'])
        assert m['verified_official_md5'] and m['md5']==ref['checksum'].split(':')[1] and Path(m['path']).stat().st_size==ref['size']
    required=['dataset_inventory.csv','spd_schema_report.md','imptc_schema_report.md','r_quality_report.md','q_quality_report.md','factor_decision_table.csv','data_audit_summary.md','data_dictionary.csv','data_funnel.csv']
    for f in required:assert (rp/f).is_file() and (rp/f).stat().st_size>0
    pictures=list((rp/'figures').glob('*.png'))
    assert len(list((rp/'figures').glob('spd_case_*.png')))==8 and len(list((rp/'figures').glob('imptc_case_*.png')))==6
    for p in pictures:
        with Image.open(p) as im:im.verify()
    assert not r['final_R_estimated'] and not q['final_R_Q_estimated'] and not q['model_training']
    js(ROOT/'validation.json',dict(passed=True,scope='SPD Example + canonical IMPTC FullSet01 audit; Samples separate',SPD_pairs=len(rdf),SPD_track_groups=9,
       IMPTC_sequences=q['sequences'],IMPTC_pedestrian_tracks=tracks,IMPTC_observations=n,IMPTC_status2_observations=int(qdf.strict_documented_valid_status2.sum()),
       all_processed_positions_timestamps_speeds_labels_compared_to_raw=True,all_pedestrian_rows_preserved=True,source_hashes_unchanged=True,
       official_Zenodo_checksums_verified=True,local_SPD_4011_file_SHA_verified=True,no_sample_full_duplicate_pooling=True,plots_validated=len(pictures),
       no_final_R_Q_or_Kalman_training_or_G95=True,deferred=['full SPD expansion: official source quota','per-track pedestrian signal spatial assignment','complete/partial crossing labels','optional TFD reproduction']))
    js(rp/'environment.json',dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,platform=platform.platform()))
    artifacts=[p for folder in [ROOT/'scripts',rp,ROOT/'data/processed'] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    artifacts.extend([ROOT/'README.md',ROOT/'plan.md',ROOT/'validation.json'])
    js(ROOT/'artifact_sha256.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(artifacts)})
    print((ROOT/'validation.json').read_text(),flush=True)
if __name__=='__main__':main()
