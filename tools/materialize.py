#!/usr/bin/env python3
"""Create the original stage layout under a new workspace, rebasing paths only."""
from pathlib import Path
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--workspace',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1]
workspace=args.workspace.expanduser().resolve()
if workspace==Path('/data/whereami/math'):
    raise SystemExit('Choose a NEW workspace; do not overwrite the completed server experiments.')
layout={'audit':'view2risk_261025','pilot':'view2risk_261025/pilot_rq_261025',
        'full':'full_rq_261026','closure':'view2risk/runs/audit_261026',
        'download':'Public-V2X-Datasets/collection_261026'}
count=0
for stage,target in layout.items():
    for source in sorted((repo/'src'/stage).rglob('*')):
        if not source.is_file():continue
        dest=workspace/target/source.relative_to(repo/'src'/stage)
        content=source.read_text().replace('/data/whereami/math',str(workspace))
        if dest.exists() and dest.read_text()!=content:
            raise SystemExit(f'Refusing to overwrite different existing file: {dest}')
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content)
        count+=1
print(f'Prepared {count} files under {workspace}; no dataset/model execution performed.')
