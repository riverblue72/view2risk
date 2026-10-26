# 데이터 받기 — 원본 그대로

[GitHub 데이터 Release](https://github.com/riverblue72/view2risk/releases/tag/data-261026)에서 서버 데이터를 받을 수 있다. 전체 복원 크기는 **22,604,243,602바이트(약22.60GB)**다. 원본 압축10개는 바이트를 바꾸지 않았고, 큰 파일만1GiB 바이트 조각으로 나눴다. 다운로더가 원래 파일로 합친 뒤 SHA256을 검증한다.

## 바로 분석하기

```bash
git clone https://github.com/riverblue72/view2risk.git
cd view2risk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tools/get_data.py --preset analysis --output ./workspace
python tools/check_data.py --workspace ./workspace
```

약699MB의 analysis TAR를 받아 full/sample 정제 Parquet·개별 예측·집계 근거·모델 파라미터·실험 지원파일289개를 원래 작업 폴더 구조로 푼다. `check_data.py`는 실제1,710,765관측/1,920트랙과2,124,624예측을 읽고 기존 Q 지표를 다시 집계해 일치 여부를 확인한다. 모델 재학습이나 원본 재가공은 필요 없다.

## 서버의 원본까지 전부 받기

```bash
python tools/get_data.py --preset all --output ./workspace
```

원본만 받으려면 `--preset raw`를 사용한다. 원본 ZIP/TAR.GZ는 서버에서 보관하던 상대 위치로 복원된다. 신규 analysis/Example TAR는 작업 경로로 자동 추출하며, 공급자의 원본 ZIP/TAR.GZ는 압축 그대로 보존한다. 원시 파서를 다시 실행하려면 원본 계획의 폴더 구조에 맞춰 원본 압축을 해제한다. 원본 압축 해제 시에는22.6GB 다운로드 용량 외에 추가 디스크 공간이 필요하다.

## 실제 파일 목록

| 파일 | 데이터 | 원본 바이트 | GiB | 업로드 조각 |
| --- | --- | --- | ---: | ---: |
| V2X-Seq-SPD.zip | SPD_annotations | 원본 압축 그대로 | 0.218 | 1 |
| V2X-Seq-SPD-infrastructure-side-image.zip | SPD_infrastructure_images | 원본 압축 그대로 | 3.316 | 4 |
| V2X-Seq-TFD-Example.zip | TFD_Example | 원본 압축 그대로 | 0.266 | 1 |
| imptc_samples.tar.gz | IMPTC_Samples | 원본 압축 그대로 | 0.324 | 1 |
| imptc_set_01.tar.gz | IMPTC_Full01 | 원본 압축 그대로 | 2.555 | 3 |
| imptc_set_02.tar.gz | IMPTC_Full02 | 원본 압축 그대로 | 2.300 | 3 |
| imptc_set_03.tar.gz | IMPTC_Full03 | 원본 압축 그대로 | 2.672 | 3 |
| imptc_set_04.tar.gz | IMPTC_Full04 | 원본 압축 그대로 | 3.328 | 4 |
| imptc_set_05.tar.gz | IMPTC_Full05 | 원본 압축 그대로 | 4.754 | 5 |
| imptc_ground_plane.zip | IMPTC_semantic_map | 원본 압축 그대로 | 0.011 | 1 |
| spd_example_261026.tar | SPD_original_Example_directory | 기존 파일 바이트 보존 TAR 포장 | 0.658 | 1 |
| analysis_261026.tar | all_analysis_tables_and_support | 기존 파일 바이트 보존 TAR 포장 | 0.651 | 1 |

SPD는 확보한 전체 주석·보정정보와 인프라 이미지, 원래 Example을 포함한다. IMPTC Samples와 Full01–05 전부 및 지면 지도를 포함한다. TFD는 기존에 확보한 Example이다. 받지 않았던 전체 LiDAR·차량 이미지·Full TFD를 추가했다고 주장하지 않는다.

IMPTC와 샘플/Full 데이터는 중복 가능성이 있으므로 서로 합쳐 새로운 독립 사람 수로 세지 않는다. 원본 데이터와 정제 데이터는 별도로 보존하며, 이미 분석한 cohort/filter 규칙을 임의로 바꾸지 않는다.

[파일/조각 manifest](../reproducibility/data_manifest.json) · [원본 SHA256](../reproducibility/DATA_SHA256SUMS) · [출처와 데이터 조건](NOTICE_DATA.md)

GitHub 일반 clone에는 코드와 집계표가 들어 있고 실제 대용량 바이트는 Releases 자산으로 제공된다. 다운로드는 Python 표준 라이브러리만 사용하며 계정 키가 필요 없다. 중단된 조각은 재개하고, SHA256이 다른 기존 원본 파일은 덮어쓰지 않는다.
