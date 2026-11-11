"""Allowlisted static export. Only licensed IMPTC cached outputs, never inD."""
import argparse,copy,gzip,hashlib,json
from pathlib import Path

def read(p):
 b=Path(p).read_bytes();return json.loads(gzip.decompress(b) if str(p).endswith('.gz') else b)
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
def export(source,target):
 source=Path(source);target=Path(target);idx=read(source/'outputs/inference_index.json');metrics=read(source/'outputs/final_results.json');cases=[];provenance=[]
 for n,cw in enumerate(['f1','f2','f3'],1):
  e=next(x for x in idx['cases'] if x['dataset']=='IMPTC' and x['crosswalk']==cw);path=source/'private/cases'/e['file'];c=read(path);assert c['dataset']=='IMPTC';pid=f'imptc-{n:02d}'
  out={k:copy.deepcopy(c[k]) for k in ['dataset','location','crosswalk','direction','observation_end_elapsed_s','actual_observations','neighbors','forecasts','attempts']};out.update(event_id=pid,sequence=pid,track_uid='target',origin0_s=0,split='fixed official-Test demonstration subset',data_kind='actual_precomputed_DDMDN_output',license='CC-BY-NC-4.0',source='https://zenodo.org/records/14811016',display_context='schematic scene; not original camera map')
  for i,other in enumerate(out['neighbors']):other['id']=f'neighbor-{i+1}'
  for p in out['forecasts']:
   p['origin_s']=p['elapsed_s'];p['conditions']={k:v for k,v in p['conditions'].items() if k in ['clean','noisy','rq']}
   for r in p['conditions'].values():
    allowed=['hypotheses_xy','hypothesis_confidence_scores','hypothesis_score_sum','hypothesis_scores_are_probabilities','anchor_weights','regions','coverage','area_m2','metrics','future_times_s','representative_speed_mps','exit','posterior_history_samples']
    kept={k:r[k] for k in allowed};inp=r['input'];kept['input']={k:inp[k] for k in ['translation','observed_xy','source_velocity_mps']};kept['input'].update(origin_s=p['elapsed_s'],history_times_s=[p['elapsed_s']-.9+j*.1 for j in range(10)],latest_input_source_ts=p['elapsed_s'],timestamp_note='display-relative clock, not original acquisition timestamp');r.clear();r.update(kept)
  write(target/'assets/data/demos'/f'{pid}.json',out);cases.append(dict(file=f'assets/data/demos/{pid}.json',event_id=pid,dataset='IMPTC',location=cw,sequence=pid,crosswalk=cw,track_uid='target'))
  provenance.append(dict(id=pid,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_dataset='IMPTC v1.0',license='CC-BY-NC-4.0',kind='actual_precomputed_DDMDN_output',forecast_origins=[p['elapsed_s'] for p in out['forecasts']],checkpoint_sha256=metrics['checkpoints']['imptc']['sha256']))
 write(target/'assets/data/inference.json',dict(cases=cases,geometry=idx['geometry'],model='Official DD-MDN IMPTC Full pretrained',provenance=dict(commit='0726eb14babe78349da03a4d8bdf34fb91612ebc',weight_sha256=metrics['checkpoints']['imptc']['sha256']),public_notice='Noncommercial IMPTC derived demonstration; inD replay excluded'))
 # Positive allowlist of aggregates. No raw case IDs, states or acquisition timestamps.
 official=metrics['official'];safe_off={k:official[k] for k in ['sample_count','horizon_s','ADE_top1_m','FDE_top1_m','minADE20_m','minFDE20_m','coverage','loss_sample_weighted']}
 safe_metrics={k:metrics[k] for k in ['position_comparison','exit_evaluation','subgroups','pedpy','limitations']};safe_metrics.update(official=safe_off,R_proxy={k:metrics['R_proxy'][k] for k in ['train_fit','all_data_descriptive','q_filter_m2_s3']},checkpoints={ds:dict(sha256=v['sha256'],status=v['status']) for ds,v in metrics['checkpoints'].items()},quality_review=None)
 write(target/'assets/data/results.json',safe_metrics)
 exp=read(source.parent/'r_uq_final_20261110/outputs/summary.json');frozen=read(source.parent/'r_uq_final_20261110/configs/frozen_calibration.json');write(target/'assets/data/exploratory.json',dict(summary=exp,calibration=frozen,status='Exploratory only; no default predictor replacement'))
 write(target/'assets/data/provenance.json',dict(demos=provenance,exclusions=['inD raw trajectories/maps','checkpoints','private APIs','credentials'],coordinate_precision='original cached float values; timestamps anonymized to relative display clock',attribution='Hetzel, Reichert, Reitberger, Doll and Sick; IMPTC v1.0 DOI 10.5281/zenodo.14811016',license='https://creativecommons.org/licenses/by-nc/4.0/'))
 print('Exported three IMPTC-only static demos and aggregates')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--target',required=True);a=p.parse_args();export(a.source,a.target)
