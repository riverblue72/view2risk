# View2Risk data release — 261026

The server's existing source archives are distributed without changing their bytes. Files over the GitHub asset limit are split into ordered byte ranges; concatenation restores the original archive SHA256. No compression/re-encoding of those raw archives was performed.

`spd_example_261026.tar` preserves files of the existing extracted SPD Example directory. `analysis_261026.tar` preserves analysis tables and supporting code/configuration/report files at their workspace-relative paths. These two TAR containers are newly packaged; their member bytes are unchanged.

IMPTC: Hetzel, Reichert, Reitberger, Doll and Sick, https://zenodo.org/records/14811016 (v1.0), dataset CC-BY-NC-4.0 https://creativecommons.org/licenses/by-nc/4.0/. This is a noncommercial research data release with attribution. Upstream repository software has separate terms. Retain attribution and applicable dataset conditions.

SPD/TFD: AIR-THU/DAIR-V2X-Seq, Yu et al., CVPR2023, https://github.com/AIR-THU/DAIR-V2X-Seq and https://arxiv.org/abs/2305.05938. Provider's dataset terms remain applicable; this release does not grant a new blanket dataset license.

Raw/processed source rows, IDs and timestamps are retained. Derived R/Q/crossing labels are research proxies with limitations documented in the reports, not independent physical ground truth. TFD coverage is Example-only. Raw SPD release covers the acquired annotations/calibrations and infrastructure images, not unacquired full LiDAR or vehicle images. IMPTC includes all acquired Full Sequence Sets01–05 and Samples.
