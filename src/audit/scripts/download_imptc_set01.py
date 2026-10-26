"""Parallel public HTTP ranges; official full Set01 MD5 remains the acceptance gate."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import json,os,time,re
import requests
from download import ROOT,hashes,write,extract

def main():
    info=next(f for f in json.loads((ROOT/'docs/zenodo_record.json').read_text())['files'] if f['key']=='imptc_set_01.tar.gz')
    size=info['size'];url=info['links']['self'];dest=ROOT/'data/downloads'/info['key'];parts=ROOT/'data/downloads/set01_parts';parts.mkdir(exist_ok=True)
    status=ROOT/'reports/downloads/imptc_set_01_parallel.json';begin=time.time();chunk=32*1024*1024
    def get(i):
        start=i*chunk;end=min(size-1,start+chunk-1);p=parts/f'{i:04d}.part';expected=end-start+1
        if p.exists() and p.stat().st_size==expected:return i
        for attempt in range(5):
            try:
                existing=p.stat().st_size if p.exists() else 0
                assert existing<expected
                first=start+existing
                r=requests.get(url,params={'audit_part':i},headers={'Range':f'bytes={first}-{end}'},stream=True,timeout=(30,120))
                r.raise_for_status();assert r.status_code==206
                assert r.headers['Content-Range']==f'bytes {first}-{end}/{size}',r.headers.get('Content-Range')
                with p.open('ab') as f:
                    for block in r.iter_content(2*1024*1024):
                        if block:f.write(block)
                assert p.stat().st_size==expected
                return i
            except (requests.RequestException,AssertionError,OSError):
                if attempt==4:raise
                time.sleep(min(30,2**(attempt+1)))
    count=(size+chunk-1)//chunk
    if not dest.exists():
        done=0
        with ThreadPoolExecutor(max_workers=6) as pool:
            for f in as_completed([pool.submit(get,i) for i in range(count)]):
                f.result();done+=1
                if done%4==0 or done==count:
                    write(status,dict(state='downloading',chunks_complete=done,chunks=count,bytes=sum(p.stat().st_size for p in parts.glob('*.part')),expected_bytes=size,elapsed_seconds=time.time()-begin))
                    print(f'Set01 chunks {done}/{count}',flush=True)
        temp=dest.with_suffix('.merge')
        with temp.open('wb') as out:
            for i in range(count):
                with (parts/f'{i:04d}.part').open('rb') as f:
                    for block in iter(lambda:f.read(8*1024*1024),b''):out.write(block)
        assert temp.stat().st_size==size
        hs=hashes(temp);assert hs['md5']==info['checksum'].split(':')[1]
        os.replace(temp,dest)
    hs=hashes(dest);assert hs['md5']==info['checksum'].split(':')[1]
    item=dict(state='downloaded',name=dest.name,path=str(dest),url=url,bytes=size,verified_official_md5=True,**hs)
    write(ROOT/'reports/downloads'/(dest.name+'.json'),item)
    extract(item,'imptc_set_01');write(status,dict(state='complete',bytes=size,verified_official_md5=True,elapsed_seconds=time.time()-begin))
if __name__=='__main__':
    try:main()
    except BaseException as e:
        write(ROOT/'reports/downloads/imptc_set_01_parallel_error.json',dict(state='failed',error_type=type(e).__name__,error=str(e)));raise
