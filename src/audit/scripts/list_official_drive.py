"""List only the publicly shared official download folder; no authentication."""
from pathlib import Path
import json
import re
import requests
ROOT=Path(__file__).resolve().parents[1]
def listing(identifier):
    url='https://drive.google.com/drive/folders/'+identifier
    r=requests.get(url,timeout=45);r.raise_for_status()
    (ROOT/'docs'/('drive_'+identifier+'.html')).write_text(r.text)
    text=re.sub(r'\\x([0-9a-fA-F]{2})',lambda m:chr(int(m[1],16)),r.text).replace('\\/','/')
    rows=[]
    for m in re.finditer(r'\["([\w-]{20,})",\["[^"\]]+"\],"([^"\n]+)","([^"\n]+)"',text):
        rows.append(dict(id=m[1],name=m[2],mime=m[3],parent=identifier))
    unique={r['id']:r for r in rows}
    return list(unique.values())
if __name__=='__main__':
    import sys
    identifier=sys.argv[1] if len(sys.argv)>1 else '1LPpQYZLs15GFz1kRYOZz3hcK6wQr6pvo'
    rows=listing(identifier)
    (ROOT/'docs'/('drive_'+identifier+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))
