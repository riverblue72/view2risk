#!/usr/bin/env python3
"""Download real GitHub Release data, restore original bytes, verify SHA256."""
from pathlib import Path,PurePosixPath
import argparse,json,hashlib,urllib.request,urllib.error,time,shutil,tarfile,os

BASE='https://github.com/riverblue72/view2risk/releases/download/data-261026/'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def safe(root,relative):
    rel=PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts:raise RuntimeError(f'Unsafe relative path: {relative}')
    p=root.joinpath(*rel.parts).resolve()
    if not p.is_relative_to(root.resolve()):raise RuntimeError(f'Path outside workspace: {relative}')
    return p

def download(url,path,size,digest):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size>=size:
        if path.stat().st_size==size and sha(path)==digest:return
        path.unlink()
    for attempt in range(5):
        offset=path.stat().st_size if path.exists() else 0
        headers={'User-Agent':'View2Risk-data-downloader'}
        if offset:headers['Range']=f'bytes={offset}-'
        try:
            req=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req,timeout=120) as response:
                append=offset and response.status==206
                if append and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                    raise RuntimeError('Unexpected resume range')
                with path.open('ab' if append else 'wb') as f:
                    shutil.copyfileobj(response,f,4*1024*1024)
            if path.stat().st_size==size and sha(path)==digest:return
            if path.exists():path.unlink()
            raise RuntimeError('Size or SHA256 mismatch')
        except Exception as error:
            if attempt==4:raise RuntimeError(f'Download failed: {url}: {error}') from error
            time.sleep(min(15,2**attempt))

def extract(archive,workspace):
    with tarfile.open(archive,'r:*') as tar:
        for member in tar:
            dest=safe(workspace,member.name)
            if member.isdir():dest.mkdir(parents=True,exist_ok=True);continue
            if not member.isfile():raise RuntimeError(f'Unsupported archive member: {member.name}')
            source=tar.extractfile(member);assert source is not None
            if dest.exists():
                expected=hashlib.sha256()
                for block in iter(lambda:source.read(8*1024*1024),b''):expected.update(block)
                if dest.stat().st_size!=member.size or sha(dest)!=expected.hexdigest():
                    raise RuntimeError(f'Refusing to replace a different existing file: {dest}')
                continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            temp=dest.with_name(dest.name+'.extracting')
            with temp.open('wb') as f:shutil.copyfileobj(source,f,4*1024*1024)
            assert temp.stat().st_size==member.size
            temp.replace(dest)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset',choices=['analysis','raw','all'],default='analysis')
    parser.add_argument('--output',type=Path,default=Path('workspace'))
    parser.add_argument('--keep-parts',action='store_true')
    parser.add_argument('--manifest',help='Local JSON or URL, primarily for offline verification')
    args=parser.parse_args();root=args.output.expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    if args.manifest and not args.manifest.startswith(('https://','http://')):
        manifest=json.loads(Path(args.manifest).read_text())
    else:
        url=args.manifest or BASE+'data_manifest.json'
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'View2Risk-data-downloader'}),timeout=60) as r:
                manifest=json.load(r)
        except urllib.error.HTTPError as error:
            raise SystemExit(f'Data release unavailable ({error.code}). Check https://github.com/riverblue72/view2risk/releases/tag/data-261026')
    selected=[f for f in manifest['files'] if args.preset=='all' or f['group']==args.preset]
    print(f'{len(selected)} files; {sum(f["bytes"] for f in selected)/1e9:.3f} GB of exact restored bytes',flush=True)
    for item in selected:
        dest=safe(root,item['restore_relative_path']);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():
            if dest.stat().st_size!=item['bytes'] or sha(dest)!=item['sha256']:
                raise RuntimeError(f'Existing destination differs from release: {dest}')
            print('Verified existing '+item['filename'],flush=True)
        else:
            paths=[]
            for part in item['parts']:
                p=safe(root/'.parts',part['name'])
                print(f'Downloading {part["name"]}: {part["bytes"]/1e6:.1f} MB',flush=True)
                download(part['url'],p,part['bytes'],part['sha256']);paths.append(p)
            temp=dest.with_name(dest.name+'.assembling')
            h=hashlib.sha256()
            with temp.open('wb') as out:
                for p in paths:
                    with p.open('rb') as stream:
                        for block in iter(lambda:stream.read(8*1024*1024),b''):
                            h.update(block);out.write(block)
            if temp.stat().st_size!=item['bytes'] or h.hexdigest()!=item['sha256']:
                raise RuntimeError(f'Restored original checksum mismatch: {item["filename"]}')
            temp.replace(dest)
            if not args.keep_parts:
                for p in paths:p.unlink()
            print('Restored and SHA256 verified '+item['filename'],flush=True)
        if item.get('extraction_layout')=='workspace':
            extract(dest,root);print('Extracted workspace files from '+item['filename'],flush=True)
    (root/'data_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Complete. Raw source archives remain unchanged; analysis tables are ready to read.',flush=True)

if __name__=='__main__':main()
