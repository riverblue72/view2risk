"""시간대·요일별 보행자·신호 분석 (IMPTC, 현지시각 Europe/Berlin).
입력: out/events_complete.csv, out/green_phases.csv (g_star.py 결과), crossing_events (base), 궤적 시퀀스 시간.
"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minipq
WS, OUT = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(261105)
TZ = "Europe/Berlin"
BANDS = [(6, 10, "아침 7–9시"), (10, 14, "점심 11–13시"), (14, 18, "오후 15–17시")]
WD = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금"}
def band(h):
    for a, b, n in BANDS:
        if a <= h < b: return n
    return None

e = pd.read_csv(f"{OUT}/events_complete.csv")
ph = pd.read_csv(f"{OUT}/green_phases.csv")
ev = pd.DataFrame(minipq.read(f"{WS}/view2risk/runs/audit_261026/data/crossing_events.parquet"))
ev = ev[ev.config == "base"]
tr = pd.DataFrame(minipq.read(f"{WS}/full_rq_261026/data/processed/imptc_pedestrian_tracks.parquet", ["sequence_id", "ts_us", "recording_date"]))

def loc(ts_s): return pd.to_datetime(ts_s, unit="s", utc=True).dt.tz_convert(TZ)
e["t"] = loc(e.entry_ts_s); e["hour"] = e.t.dt.hour; e["wd"] = e.t.dt.dayofweek.map(WD); e["band"] = e.hour.map(band)
ev["t"] = loc(ev.first_map_ts_us / 1e6); ev["band"] = ev.t.dt.hour.map(band); ev["wd"] = ev.t.dt.dayofweek.map(WD)
ph["t"] = loc(ph.onset); ph["band"] = ph.t.dt.hour.map(band); ph["wd"] = ph.t.dt.dayofweek.map(WD)
seq = tr.groupby("sequence_id").agg(t0=("ts_us", "min"), t1=("ts_us", "max"), date=("recording_date", "first"))
seq["hours"] = (seq.t1 - seq.t0) / 3.6e9; seq["t"] = loc(seq.t0 / 1e6)
seq["band"] = seq.t.dt.hour.map(band); seq["wd"] = seq.t.dt.dayofweek.map(WD)

# 속도는 횡단보도 길이 영향을 없애려고 L/T 사용, 소요시간은 횡단보도별 중앙값 대비 비율로도 봄
e["dur_ratio"] = e.duration_s / e.groupby("signal_group").duration_s.transform("median")
e["red_entry"] = e.entry_signal_code == 10

def boot(df, fn, B=1000):
    dates = df.recording_date.unique()
    if len(dates) < 2: return (np.nan, np.nan)
    g = {d: df[df.recording_date == d] for d in dates}
    v = [fn(pd.concat([g[d] for d in rng.choice(dates, len(dates))])) for _ in range(B)]
    return tuple(np.nanpercentile(v, [2.5, 97.5]))

def summarize(key, order):
    rows = []
    for k in order:
        x = e[e[key] == k]; s = seq[seq[key] == k]; p = ph[ph[key] == k]; c = ev[ev[key] == k]
        if len(s) == 0: continue
        lo, hi = boot(x, lambda d: d.speed_mps.median()) if len(x) else (np.nan, np.nan)
        rlo, rhi = boot(x, lambda d: d.dur_ratio.quantile(.85)) if len(x) else (np.nan, np.nan)
        rows.append({key: k, "기록_시간_h": round(s.hours.sum(), 2), "촬영일수": s.date.nunique(), "완료_횡단": len(x),
                     "시간당_완료횡단": round(len(x) / s.hours.sum(), 1),
                     "중앙속도_mps": round(x.speed_mps.median(), 3), "중앙속도_CI": f"{lo:.2f}–{hi:.2f}",
                     "하위15%속도_mps": round(x.speed_mps.quantile(.15), 3),
                     "소요시간85%_대비중앙값": round(x.dur_ratio.quantile(.85), 3), "소요비율_CI": f"{rlo:.2f}–{rhi:.2f}",
                     "적색진입_pct": round(100 * x.red_entry.mean(), 1) if len(x) else np.nan,
                     "주변보행자≥1_pct": round(100 * (x.nearby_ped >= 1).mean(), 1) if len(x) else np.nan,
                     "비_pct": round(100 * (x.weather == "light_rain").mean(), 1) if len(x) else np.nan,
                     "f1f3_녹색중앙_s": p[p.signal_group.isin(["f1", "f3"])].green_s.median(),
                     "f2_녹색중앙_s": p[p.signal_group == "f2"].green_s.median(),
                     "주기중앙_s": p.cycle_s.median(), "녹색phase수": len(p),
                     "미완료비율_pct": round(100 * (c.classification != "complete_rule").mean(), 1)})
    return pd.DataFrame(rows)

tb = summarize("band", [b[2] for b in BANDS])
wd = summarize("wd", list(WD.values()))
# 횡단보도 × 시간대 G*(85%) (완료 기준, 표본 30 이상)
gx = []
for (cw, b), x in e.dropna(subset=["band"]).groupby(["signal_group", "band"]):
    if len(x) < 30: gx.append({"signal_group": cw, "band": b, "n": len(x), "Gstar85_s": np.nan, "CI": "표본<30"}); continue
    lo, hi = boot(x, lambda d: 7 + d.duration_s.quantile(.85))
    gx.append({"signal_group": cw, "band": b, "n": len(x), "dates": x.recording_date.nunique(),
               "Gstar85_s": round(7 + x.duration_s.quantile(.85), 2), "CI": f"{lo:.1f}–{hi:.1f}"})
gx = pd.DataFrame(gx)
# 시간대와 날짜가 얼마나 겹치는지 (교란 점검)
conf = e.groupby(["recording_date", "band"]).size().unstack(fill_value=0)

tb.to_csv(f"{OUT}/time_band_summary.csv", index=False, encoding="utf-8-sig")
wd.to_csv(f"{OUT}/weekday_summary.csv", index=False, encoding="utf-8-sig")
gx.to_csv(f"{OUT}/gstar_by_crosswalk_band.csv", index=False, encoding="utf-8-sig")
conf.to_csv(f"{OUT}/date_by_band_counts.csv", encoding="utf-8-sig")

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Noto Sans CJK KR"; plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(1, 3, figsize=(15, 4.3))
for a, df, key, ttl in [(ax[0], tb, "band", "시간대"), (ax[1], wd, "wd", "요일")]:
    m = df["중앙속도_mps"]; ci = df["중앙속도_CI"].str.split("–", expand=True).astype(float)
    a.errorbar(range(len(df)), m, yerr=[m - ci[0], ci[1] - m], fmt="o", color="#2a6fdb", capsize=4)
    for i, r in df.reset_index(drop=True).iterrows():
        a.annotate(f"n={r['완료_횡단']}\n{r['촬영일수']}일", (i, r["중앙속도_mps"]), xytext=(8, -4), textcoords="offset points", fontsize=8, color="#555")
    a.set_xticks(range(len(df))); a.set_xticklabels(df[key]); a.set_ylim(1.2, 1.8)
    a.set(title=f"{ttl}별 보행 중앙속도 (날짜 bootstrap 95% CI)", ylabel="m/s")
a = ax[2]
w = 0.35
a.bar(np.arange(len(tb)) - w / 2, tb["시간당_완료횡단"], w, color="#868e96", label="시간당 완료 횡단 (건/h)")
a2 = a.twinx(); a2.plot(range(len(tb)), tb["적색진입_pct"], "o-", color="#d9480f", label="적색 진입 비율 (%)")
a.set_xticks(range(len(tb))); a.set_xticklabels(tb["band"]); a.set_title("시간대별 횡단량과 적색 진입 비율")
a.set_ylabel("건/h"); a2.set_ylabel("%"); a.legend(loc="upper left", fontsize=8); a2.legend(loc="upper right", fontsize=8)
fig.tight_layout(); fig.savefig(f"{OUT}/time_weekday.png", dpi=150)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(tb.T.to_string()); print(wd.T.to_string()); print(gx.to_string()); print(conf.to_string())
