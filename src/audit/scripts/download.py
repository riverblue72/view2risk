"""Official-source resumable downloads, checksum and safe archive extraction."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import argparse
import hashlib
import json
import os
import tarfile
import time
import zipfile
import requests

ROOT=Path(__file__).resolve().parents[1]
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');os.replace(tmp,p)
def hashes(p):
    a,b=hashlib.md5(),hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):a.update(block);b.update(block)
    return dict(md5=a.hexdigest(),sha256=b.hexdigest())
class Form(HTMLParser):
    def __init__(self):super().__init__();self.action=None;self.params={}
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='form':self.action=d.get('action')
        if tag=='input' and d.get('name'):self.params[d['name']]=d.get('value','')
def response(session,url,headers=None):
    r=session.get(url,headers=headers or {},stream=True,timeout=(30,120));r.raise_for_status()
    if 'text/html' in r.headers.get('Content-Type',''):
        text=r.text;form=Form();form.feed(text)
        if form.action and form.params.get('id'):
            r=session.get(form.action,params=form.params,headers=headers or {},stream=True,timeout=(30,120));r.raise_for_status()
        if 'text/html' in r.headers.get('Content-Type',''):
            raise RuntimeError('Public download returned HTML rather than archive: '+r.text[:1600])
    return r
def fetch(name,url,md5=None,size=None):
    dest=ROOT/'data/downloads'/name;status=ROOT/'reports/downloads'/(name+'.json')
    if dest.exists():
        hs=hashes(dest)
        assert not md5 or hs['md5']==md5
        return dict(name=name,path=str(dest),bytes=dest.stat().st_size,url=url,verified_official_md5=bool(md5),**hs)
    part=dest.with_suffix(dest.suffix+'.part');session=requests.Session()
    begin=time.time();last=0
    for attempt in range(4):
        try:
            start=part.stat().st_size if part.exists() else 0
            r=response(session,url,{'Range':f'bytes={start}-'} if start else {})
            append=bool(start and r.status_code==206)
            if not append:start=0
            total=size or (start+int(r.headers.get('Content-Length',0)))
            with part.open('ab' if append else 'wb') as f:
                for block in r.iter_content(2*1024*1024):
                    if not block:continue
                    f.write(block);start+=len(block)
                    if time.time()-last>10:
                        write(status,dict(state='downloading',name=name,bytes=start,expected_bytes=total,url=url,elapsed_seconds=time.time()-begin));last=time.time()
            if size:assert part.stat().st_size==size
            hs=hashes(part)
            if md5:assert hs['md5']==md5,('MD5 mismatch',name,hs['md5'],md5)
            if not (tarfile.is_tarfile(part) or zipfile.is_zipfile(part)):raise ValueError('Not a valid tar/zip archive')
            os.replace(part,dest)
            result=dict(state='downloaded',name=name,path=str(dest),url=url,bytes=dest.stat().st_size,verified_official_md5=bool(md5),downloaded_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**hs)
            write(status,result);return result
        except (requests.RequestException,OSError) as e:
            write(status,dict(state='retrying',name=name,attempt=attempt+1,error=str(e)))
            if attempt==3:raise
            time.sleep(2*(attempt+1))
def extract(item,subdir):
    dest=ROOT/'data/raw'/subdir;marker=dest/'extraction_complete.json'
    if marker.exists():return json.loads(marker.read_text())
    dest.mkdir(parents=True,exist_ok=True);p=Path(item['path']);listing=[]
    def safe(name):
        target=(dest/name).resolve();assert target==dest.resolve() or dest.resolve() in target.parents,('Unsafe archive path',name)
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            for x in z.infolist():safe(x.filename);listing.append(dict(path=x.filename,bytes=x.file_size))
            assert z.testzip() is None
            z.extractall(dest)
    else:
        with tarfile.open(p) as t:
            for x in t.getmembers():
                safe(x.name)
                if x.issym() or x.islnk():raise ValueError('Archive links need explicit review: '+x.name)
                if not (x.isfile() or x.isdir()):raise ValueError('Unexpected special archive member')
                listing.append(dict(path=x.name,bytes=x.size))
            t.extractall(dest,filter='data')
    write(ROOT/'reports/downloads'/(subdir+'_archive_listing.json'),listing)
    result=dict(complete=True,archive=item,members=len(listing),uncompressed_bytes=sum(x['bytes'] for x in listing),raw_root=str(dest))
    write(marker,result);print(json.dumps(result),flush=True);return result
def one(which):
    try:
        if which=='spd_example':
            try:
                item=fetch('spd_example.zip','https://drive.usercontent.google.com/download?id=1gjOmGEBMcipvDzu2zOrO9ex_OscUZMYY&export=download&confirm=t')
            except RuntimeError as e:
                # Separately published official Example file in the official full-data folder.
                write(ROOT/'reports/downloads/spd_primary_link_unavailable.json',dict(error=str(e),fallback_official_folder='https://drive.google.com/drive/folders/1VMs8ZHkXSmASBbLNjBcvEQP6wZWJO_ZY'))
                item=fetch('spd_example.zip','https://drive.usercontent.google.com/download?id=1lyl1gdrbfDI-sTQq7EoU-SkdBcWJqFn7&export=download&confirm=t')
        elif which=='spd_full_metadata':
            item=fetch('spd_full_metadata.zip','https://drive.usercontent.google.com/download?id=1SuJOyI3G8MstCY-EHS5tbWvaMh2iZuef&export=download&confirm=t')
        else:
            name={'imptc_samples':'imptc_samples.tar.gz','imptc_set_01':'imptc_set_01.tar.gz'}[which]
            info=next(f for f in json.loads((ROOT/'docs/zenodo_record.json').read_text())['files'] if f['key']==name)
            item=fetch(name,info['links']['self'],info['checksum'].split(':')[1],info['size'])
        return extract(item,which)
    except BaseException as e:
        write(ROOT/'reports/downloads'/(which+'_error.json'),dict(state='failed',error_type=type(e).__name__,error=str(e)))
        print(which+' FAILED '+str(e),flush=True);return dict(dataset=which,failed=True,error=str(e))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('datasets',nargs='+',choices=['spd_example','spd_full_metadata','imptc_samples','imptc_set_01']);a=p.parse_args()
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,a.datasets))
    write(ROOT/'reports/download_run.json',results)
