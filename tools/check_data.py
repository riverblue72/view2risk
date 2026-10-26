#!/usr/bin/env python3
"""Check downloaded input cohorts and recompute Q metrics from saved forecasts."""
from pathlib import Path
import argparse,json
import pandas as pd
import numpy as np

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=Path('workspace'))
    args=parser.parse_args();root=args.workspace.expanduser().resolve();base=root/'full_rq_261026'
    p=pd.read_parquet(base/'data/processed/spd_pedestrian_pairs.parquet',columns=['dx','dy','track_uid'])
    q=pd.read_parquet(base/'data/processed/imptc_pedestrian_tracks.parquet',columns=['track_uid','sequence_id'])
    assert len(p)==10109 and p.track_uid.nunique()==233
    assert len(q)==1710765 and q.track_uid.nunique()==1920 and q.sequence_id.nunique()==264
    forecasts=pd.read_parquet(base/'data/imptc_cv_residuals.parquet',columns=['model','horizon_s','error_m','covered90','covered95','area95_m2'])
    assert len(forecasts)==2124624
    rows=[]
    for (model,horizon),g in forecasts.groupby(['model','horizon_s']):
        rows.append(dict(model=model,horizon_s=horizon,predictions=len(g),RMSE_m=float(np.sqrt(np.mean(g.error_m.to_numpy()**2))),
            MAE_m=float(g.error_m.mean()),coverage90=float(g.covered90.mean()),coverage95=float(g.covered95.mean()),mean_area95_m2=float(g.area95_m2.mean())))
    result=pd.DataFrame(rows)
    reference=pd.read_csv(base/'reports/q_overall_metrics.csv')
    matched=result.merge(reference,on=['model','horizon_s'],suffixes=('_new','_reference'),validate='one_to_one')
    for metric in ['RMSE_m','MAE_m','coverage90','coverage95','mean_area95_m2']:
        np.testing.assert_allclose(matched[metric+'_new'],matched[metric+'_reference'],rtol=1e-10,atol=1e-12,equal_nan=True)
    result.to_csv(root/'team_check.csv',index=False,encoding='utf-8-sig',na_rep='N/A')
    print(result.to_string(index=False))
    print(json.dumps(dict(passed=True,SPD_pairs=len(p),SPD_pair_RMSE_m=float(np.sqrt((p.dx**2+p.dy**2).mean())),
        IMPTC_observations=len(q),IMPTC_tracks=q.track_uid.nunique(),Q_predictions=len(forecasts),saved_Q_metrics_reproduced=True)))

if __name__=='__main__':main()
