"""Download only the View2Risk audit inputs; reuse verified existing samples/full sets."""
from pathlib import Path,PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
import zipfile

WORK=Path(__file__).resolve().parent
ROOT=WORK.parent
EXISTING=Path('/data/whereami/math/view2risk_261025')
PY='/data/whereami/math/tools/gdown/bin/python'
GDOWN='/data/whereami/math/tools/gdown/bin/gdown'
START=time.time()

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)

def hashfile(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        for member in infos:
            p=PurePosixPath(member.filename)
            assert not p.is_absolute() and '..' not in p.parts and '\\' not in member.filename
            assert not stat.S_ISLNK(member.external_attr>>16)
        bad=z.testzip();assert bad is None,bad
        return dict(path=str(path),bytes=path.stat().st_size,SHA256=hashfile(path),zip_crc_passed=True,
            members=len(infos),uncompressed_bytes=sum(x.file_size for x in infos))

def download(name,url):
    dest=ROOT/name;status=WORK/(name+'.status.json');mark=WORK/(name+'.verified.json')
    if mark.exists():
        proof=json.loads(mark.read_text())
        if dest.exists() and dest.stat().st_size==proof['bytes']:return proof
    log=WORK/(name+'.log')
    with log.open('a') as f:
        child=subprocess.Popen([GDOWN,'--no-cookies','--timeout','30','--retries','2','--continue',url,'-O',str(dest)],stdout=f,stderr=subprocess.STDOUT)
        while child.poll() is None:
            parts=list(ROOT.glob(name+'*'))
            size=sum(p.stat().st_size for p in parts if p.is_file())
            write(status,dict(state='downloading',url=url,path=str(dest),local_bytes_including_partial=size,elapsed_s=time.time()-START))
            time.sleep(5)
        if child.returncode:
            write(status,dict(state='failed',url=url,returncode=child.returncode,log=str(log)))
            raise RuntimeError(f'{name} download failed; see {log}')
    write(status,dict(state='checking_archive',path=str(dest)))
    proof=dict(verify_zip(dest),source_url=url,official_checksum_available=False)
    write(mark,proof);write(status,dict(state='verified',**proof));return proof

def extract(path,target):
    marker=target/'extraction_complete.json'
    if marker.exists():return json.loads(marker.read_text())
    assert not target.exists(),'Keep partial extraction intact; inspect before resuming'
    target.mkdir(parents=True)
    with zipfile.ZipFile(path) as z:
        for member in z.infolist():
            rel=PurePosixPath(member.filename)
            assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in member.filename
            assert not stat.S_ISLNK(member.external_attr>>16)
            out=target.joinpath(*rel.parts)
            assert out.resolve().is_relative_to(target.resolve())
            if member.is_dir():out.mkdir(parents=True,exist_ok=True)
            else:
                out.parent.mkdir(parents=True,exist_ok=True)
                with z.open(member) as source,out.open('xb') as sink:shutil.copyfileobj(source,sink,1024*1024)
    proof=dict(state='extracted',archive=str(path),archive_SHA256=hashfile(path),target=str(target),members=len(z.infolist()))
    write(marker,proof);return proof

def main():
    WORK.mkdir(exist_ok=True)
    write(WORK/'status.json',dict(state='collecting',scope='View2Risk Data Audit MD inputs, no analysis rerun or model training',start_utc=START))
    assert shutil.disk_usage(ROOT).free>100*1024**3
    manifest=json.loads((ROOT/'logs/root_list_261026.json').read_text())
    def locate(name,portion):
        matches=[r for r in manifest if Path(r['path']).name==name and portion in r['path']]
        assert len(matches)==1,matches
        return matches[0]['url']
    images='V2X-Seq-SPD-infrastructure-side-image.zip';tfd='V2X-Seq-TFD-Example.zip'
    urls={images:locate(images,'Full Dataset'),tfd:locate(tfd,'Example')}
    # R full annotations already downloaded and independently CRC checked on this date.
    annotation=ROOT/'V2X-Seq-SPD.zip'
    recorded=json.loads((ROOT/'logs/spd_verified_261026.json').read_text())
    assert recorded['zip_crc_passed'] and hashfile(annotation)==recorded['sha256']
    meta=extract(annotation,ROOT/'raw/spd_full')
    data_root=ROOT/'raw/spd_full/V2X-Seq-SPD'
    info=json.loads((data_root/'infrastructure-side/data_info.json').read_text())
    assert len(info)==11275
    expected={PurePosixPath(r['image_path']).name for r in info}
    packages=[]
    # Prior IMPTC files are reused; original archive markers retain official checksums.
    for name in ['spd_example','imptc_samples',*[f'imptc_set_{i:02d}' for i in range(1,6)]]:
        p=EXISTING/'data/raw'/name;marker=p/'extraction_complete.json';assert marker.exists()
        m=json.loads(marker.read_text())
        if name.startswith('imptc_'):
            assert m['archive']['verified_official_md5']
            archive=Path(m['archive']['path']);assert archive.stat().st_size==m['archive']['bytes']
        packages.append(dict(name=name,status='existing_verified_package_reused',raw_root=str(p),prior_verification_marker=str(marker)))
    write(WORK/'required_inputs.json',dict(reused=packages,download=urls,already_downloaded_annotations=str(annotation),
        excluded_from_this_MD_scope=['DAIR-V2X 2022 datasets','SPD vehicle images','SPD full raw LiDAR','SPD unlabeled test package','TFD full split archives'],
        reason='Paired infrastructure annotations and calibration suffice for R statistics; infrastructure images support required visual QC. IMPTC Full Sequence contains trajectories/context. TFD Example is optional comparison input.'))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={name:pool.submit(download,name,url) for name,url in urls.items()}
        completed={name:future.result() for name,future in futures.items()}
    write(WORK/'status.json',dict(state='extracting_and_linking',archives_verified=completed))
    # Normalize only the newly acquired images into the documented data_info layout.
    # Original ZIP member path and output mapping are recorded; image bytes are unchanged.
    output=data_root/'infrastructure-side/image';output.mkdir(exist_ok=True)
    mapping=[]
    with zipfile.ZipFile(ROOT/images) as z:
        candidates={}
        for item in z.infolist():
            if item.is_dir() or not item.filename.lower().endswith('.jpg'):continue
            name=PurePosixPath(item.filename).name
            assert name not in candidates,'Duplicate image basename in archive'
            candidates[name]=item
        missing=sorted(expected-set(candidates))
        write(WORK/'image_membership.json',dict(expected=len(expected),archive_images=len(candidates),missing=missing))
        assert not missing,'Image ZIP does not cover full annotation metadata; investigate rather than silently dropping frames'
        for name in sorted(expected):
            entry=candidates[name];dest=output/name
            if dest.exists():raise RuntimeError(f'Preserve existing image {dest}; resume needs CRC review')
            with z.open(entry) as source,dest.open('xb') as sink:shutil.copyfileobj(source,sink,1024*1024)
            with dest.open('rb') as f:assert f.read(2)==b'\xff\xd8',name
            mapping.append(dict(archive_member=entry.filename,output=str(dest),bytes=entry.file_size,source_zip_crc32=entry.CRC))
    write(WORK/'image_extraction_mapping.json',mapping)
    tfd_raw=extract(ROOT/tfd,ROOT/'raw/tfd_example')
    # Check all required full-SPD metadata paths and image paths against actual extraction.
    missing=[]
    keys=['image_path','calib_camera_intrinsic_path','calib_virtuallidar_to_camera_path','calib_virtuallidar_to_world_path','label_camera_std_path','label_lidar_std_path']
    for frame in info:
        for key in keys:
            path=data_root/'infrastructure-side'/frame[key]
            if not path.is_file():missing.append(dict(frame_id=frame['frame_id'],key=key,path=str(path)))
    assert not missing,missing[:5]
    validation=dict(passed=True,infra_frames=len(info),infra_sequences=len({r['sequence_id'] for r in info}),image_paths_found=len(expected),
        metadata_path_checks=len(info)*len(keys),missing_required_paths=missing,annotations_archive_SHA256=recorded['sha256'],
        additional_archives=completed,original_analysis_results_modified=False,pilot_inputs_and_splits_unchanged=True,
        GPU_used=False,existing_packages=packages,tfd=tfd_raw,elapsed_s=time.time()-START)
    write(WORK/'validation.json',validation)
    write(WORK/'status.json',dict(state='complete',validation=str(WORK/'validation.json'),elapsed_s=time.time()-START))
    with (ROOT/'README.md').open('a') as f:
        f.write('\n\n## View2Risk MD 필요 자료 수집 — 261026\n\n')
        f.write('상태와 입력 목록은 collection_261026/status.json, required_inputs.json, validation.json을 확인한다.\n')
        f.write('SPD 전체 주석·calibration·timestamp와 인프라 이미지의 연결을 검증했다. 새 raw 경로는 raw/spd_full/V2X-Seq-SPD/. TFD Example은 raw/tfd_example/. IMPTC Samples 및 Full Set01–05는 기존 view2risk_261025/data/raw/를 재사용한다.\n')
        f.write('기존 sample audit 및 R/Q pilot 결과는 수정하거나 다시 학습하지 않았다. ZIP SHA256/CRC는 다운로드 무결성 기록이며 별도 공식 publisher checksum 검증과 구분한다.\n')
    print(json.dumps(validation),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        write(WORK/'status.json',dict(state='failed',error_type=type(exc).__name__,error=str(exc),partial_files_preserved=True))
        raise
