"""Collect remaining official Full Sequence sets without changing existing analyses."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import json,os,time,traceback
import requests
from download import ROOT,hashes,write,extract

STATUS=ROOT/'reports/full_download'
def collect(name):
    info=next(x for x in json.loads((ROOT/'docs/zenodo_record.json').read_text())['files'] if x['key']==name+'.tar.gz')
    size=info['size'];url=info['links']['self'];dest=ROOT/'data/downloads'/info['key']
    parts=ROOT/'data/downloads'/(name+'_parts');parts.mkdir(exist_ok=True)
    chunk=32*1024*1024;count=(size+chunk-1)//chunk;started=time.time()
    def part(i):
        first=i*chunk;last=min(size-1,first+chunk-1);p=parts/f'{i:04d}.part';required=last-first+1
        if p.exists() and p.stat().st_size==required:return
        for attempt in range(6):
            try:
                existing=p.stat().st_size if p.exists() else 0
                assert existing<required
                start=first+existing
                r=requests.get(url,params={'audit_part':i},headers={'Range':f'bytes={start}-{last}'},stream=True,timeout=(30,120))
                if r.status_code==429:
                    time.sleep(min(60,int(r.headers.get('Retry-After','20'))));r.raise_for_status()
                r.raise_for_status()
                assert r.status_code==206 and r.headers.get('Content-Range')==f'bytes {start}-{last}/{size}'
                with p.open('ab') as f:
                    for block in r.iter_content(2*1024*1024):
                        if block:f.write(block)
                assert p.stat().st_size==required
                return
            except (requests.RequestException,AssertionError,OSError):
                if attempt==5:raise
                time.sleep(min(30,2**(attempt+1)))
    if not dest.exists():
        write(STATUS/(name+'.json'),dict(state='downloading',expected_bytes=size,chunks=count,chunks_complete=0))
        with ThreadPoolExecutor(max_workers=4) as pool:
            for done,f in enumerate(as_completed([pool.submit(part,i) for i in range(count)]),1):
                f.result()
                if done%4==0 or done==count:
                    write(STATUS/(name+'.json'),dict(state='downloading',expected_bytes=size,bytes=sum(p.stat().st_size for p in parts.glob('*.part')),chunks=count,chunks_complete=done,elapsed_seconds=time.time()-started))
                    print(name+' '+str(done)+'/'+str(count),flush=True)
        merged=dest.with_suffix('.merge')
        with merged.open('wb') as output:
            for i in range(count):
                with (parts/f'{i:04d}.part').open('rb') as f:
                    for block in iter(lambda:f.read(8*1024*1024),b''):output.write(block)
        assert merged.stat().st_size==size
        hs=hashes(merged);assert hs['md5']==info['checksum'].split(':')[1]
        os.replace(merged,dest)
    hs=hashes(dest);assert dest.stat().st_size==size and hs['md5']==info['checksum'].split(':')[1]
    item=dict(state='downloaded',name=dest.name,path=str(dest),url=url,bytes=size,verified_official_md5=True,downloaded_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**hs)
    write(ROOT/'reports/downloads'/(dest.name+'.json'),item)
    write(STATUS/(name+'.json'),dict(state='extracting',bytes=size,official_MD5_verified=True))
    result=extract(item,name)
    write(STATUS/(name+'.json'),dict(state='complete',official_MD5_verified=True,archive=item,members=result['members'],uncompressed_bytes=result['uncompressed_bytes'],elapsed_seconds=time.time()-started))
    return result

def safe(name):
    try:return collect(name)
    except BaseException as e:
        write(STATUS/(name+'.json'),dict(state='failed',error_type=type(e).__name__,error=str(e)));traceback.print_exc();return dict(dataset=name,state='failed',error=str(e))
def main():
    names=['imptc_set_02','imptc_set_03','imptc_set_04','imptc_set_05']
    write(STATUS/'collection_status.json',dict(state='running',datasets=names,existing_Set01_audit_preserved=True,models_trained=False))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(safe,names))
    success=all(r.get('complete') for r in results)
    write(STATUS/'collection_status.json',dict(state='complete' if success else 'partial_failure',datasets=names,results=results,existing_Set01_audit_preserved=True,models_trained=False))
if __name__=='__main__':main()
