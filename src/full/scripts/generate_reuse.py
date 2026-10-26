"""Copy unchanged scientific kernels from the verified sample pilot, with provenance."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OLD=Path('/data/whereami/math/view2risk_261025/pilot_rq_261025/scripts')
targets={'pilot.py':['clean','normstats','gauss_stats','kf','slope','metrics','metric_table'],
         'verify_interpret.py':['reference_filter']}
header='import numpy as np\nimport pandas as pd\nfrom numba import njit\nfrom scipy.stats import chi2\nLEVELS={90:float(chi2.ppf(.90,2)),95:float(chi2.ppf(.95,2))}\n'
segments=[];proof=[]
for filename,names in targets.items():
    source=(OLD/filename).read_text();lines=source.splitlines()
    for node in ast.parse(source).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:
            start=min([node.lineno]+[d.lineno for d in node.decorator_list])-1
            text='\n'.join(lines[start:node.end_lineno])+'\n'
            segments.append(text);proof.append(dict(source=str(OLD/filename),function=node.name,SHA256=hashlib.sha256(text.encode()).hexdigest()))
(ROOT/'scripts/reused_math.py').write_text(header+'\n\n'+'\n\n'.join(segments))
(ROOT/'reports/kernel_reuse.json').write_text(json.dumps(proof,indent=2)+'\n')
