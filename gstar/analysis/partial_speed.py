"""보완 분석: 횡단을 끝까지 관측하지 못한 보행자의 속도 추정 → 예상 소요시간 → G*(p) 재계산.

속도 추정 (완료자·미완료자 동일 방법):
  횡단보도 위 관측 구간 [first_map_ts, last_map_ts]의 궤적 점을 횡단보도 축 방향으로 투영하고
  v_axis = |s(끝) - s(처음)| / (관측 시간). 관측 2s 이상, 축 방향 이동 2m 이상인 경우만 사용.
예상 소요시간: T_hat = L / v_axis.
"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minipq

WS, REPO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
rng = np.random.default_rng(261102)
MIN_OBS_S, MIN_DIST_M, KR_ENTRY_S = 2.0, 2.0, 7.0
P_REPORT = [0.50, 0.85, 0.90, 0.95]

ev = pd.DataFrame(minipq.read(f"{WS}/view2risk/runs/audit_261026/data/crossing_events.parquet"))
ev = ev[ev.config == "base"].copy()
geo = pd.read_csv(f"{REPO}/results/audit_261026/geometry.csv", encoding="utf-8-sig").set_index("signal_group")
tr = pd.DataFrame(minipq.read(f"{WS}/full_rq_261026/data/processed/imptc_pedestrian_tracks.parquet",
                              ["track_uid", "ts_us", "x", "y", "status"]))
tr = tr[tr.status == 2]
by_track = {k: g.sort_values("ts_us") for k, g in tr.groupby("track_uid")}

def axis_speed(r):
    g = geo.loc[r.signal_group]; x = by_track.get(r.track_uid)
    if x is None: return (np.nan, np.nan, np.nan)
    w = x[(x.ts_us >= r.first_map_ts_us) & (x.ts_us <= r.last_map_ts_us)]
    if len(w) < 2: return (np.nan, np.nan, np.nan)
    s = (w.x - g.center_x_m) * g.axis_x + (w.y - g.center_y_m) * g.axis_y
    dt = (w.ts_us.iloc[-1] - w.ts_us.iloc[0]) / 1e6; ds = abs(s.iloc[-1] - s.iloc[0])
    return (dt, ds, ds / dt if dt > 0 else np.nan)

ev["obs_s"], ev["axis_dist_m"], ev["v_axis"] = zip(*[axis_speed(r) for r in ev.itertuples()])
ev["L_m"] = ev.signal_group.map(geo.length_m)
ev["usable"] = (ev.obs_s >= MIN_OBS_S) & (ev.axis_dist_m >= MIN_DIST_M) & (ev.v_axis < 3.5)
ev["v_gate"] = np.where(ev.classification == "complete_rule", ev.L_m / ev.duration_s, np.nan)
ev["T_hat_s"] = ev.L_m / ev.v_axis

# 1) 속도 비교 (같은 방법 v_axis 기준)
from scipy.stats import mannwhitneyu
cmp_rows = []
for grp in ["f1", "f2", "f3"]:
    base = ev[(ev.signal_group == grp) & (ev.classification == "complete_rule") & ev.usable]
    for cls in ["complete_rule", "partial_censored", "partial_missing_landing", "returned_same_side"]:
        x = ev[(ev.signal_group == grp) & (ev.classification == cls)]
        u = x[x.usable]
        row = {"signal_group": grp, "class": cls, "events": len(x), "usable": len(u),
               "v_axis_median": u.v_axis.median(), "v_axis_p15": u.v_axis.quantile(.15), "v_axis_p05": u.v_axis.quantile(.05),
               "share_below_1.0mps_pct": 100 * (u.v_axis < 1.0).mean() if len(u) else np.nan,
               "obs_s_median": x.obs_s.median()}
        if cls != "complete_rule" and len(u) >= 5:
            row["mannwhitney_p_vs_complete"] = mannwhitneyu(u.v_axis, base.v_axis).pvalue
        cmp_rows.append(row)
cmp = pd.DataFrame(cmp_rows)
# 완료자의 v_axis 와 v_gate 차이 (방법 차이 점검)
c_all = ev[(ev.classification == "complete_rule") & ev.usable]
method_ratio = (c_all.v_axis / c_all.v_gate).describe()

# 2) G* 재계산: A 완료만 / B +중도절단 예상 / C +중도절단+도착확인부족 예상
def boot_q(df, col, B=1000):
    dates = df.recording_date.unique(); g = {d: df[df.recording_date == d][col].values for d in dates}
    qs = [np.quantile(np.concatenate([g[d] for d in rng.choice(dates, len(dates))]), P_REPORT) for _ in range(B)]
    return np.percentile(qs, [2.5, 97.5], axis=0)

rows = []
for grp in ["f1", "f2", "f3"]:
    e = ev[ev.signal_group == grp]
    comp = e[e.classification == "complete_rule"].assign(T=lambda d: d.duration_s)
    imp_c = e[(e.classification == "partial_censored") & e.usable].assign(T=lambda d: d.T_hat_s)
    imp_l = e[(e.classification == "partial_missing_landing") & e.usable].assign(T=lambda d: d.T_hat_s)
    for name, df in [("A_완료자만", comp), ("B_완료+중도절단(추정)", pd.concat([comp, imp_c])),
                     ("C_완료+중도절단+도착확인부족(추정)", pd.concat([comp, imp_c, imp_l]))]:
        q = np.quantile(df["T"], P_REPORT); lo, hi = boot_q(df, "T")
        r = {"signal_group": grp, "scenario": name, "n": len(df)}
        for i, p in enumerate(P_REPORT):
            r[f"T_p{int(p*100)}_s"] = round(q[i], 2); r[f"T_p{int(p*100)}_ci"] = f"{lo[i]:.1f}–{hi[i]:.1f}"
            r[f"Gstar_p{int(p*100)}_s"] = round(KR_ENTRY_S + q[i], 2)
        rows.append(r)
gs = pd.DataFrame(rows)

ev.drop(columns=["source_path"]).to_csv(f"{OUT}/partial_speed_events.csv", index=False, encoding="utf-8-sig")
cmp.to_csv(f"{OUT}/partial_speed_compare.csv", index=False, encoding="utf-8-sig")
gs.to_csv(f"{OUT}/gstar_with_partial.csv", index=False, encoding="utf-8-sig")

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Noto Sans CJK KR"; plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
for a, grp in zip(ax, ["f1", "f2", "f3"]):
    for cls, col, lab in [("complete_rule", "#212529", "완료"), ("partial_censored", "#d9480f", "중도절단"),
                          ("partial_missing_landing", "#2a6fdb", "도착확인부족")]:
        v = np.sort(ev[(ev.signal_group == grp) & (ev.classification == cls) & ev.usable].v_axis)
        if len(v): a.step(v, np.arange(1, len(v) + 1) / len(v) * 100, where="post", color=col, label=f"{lab} (n={len(v)})")
    a.axvline(1.0, color="gray", ls="--", lw=.8); a.axvline(0.8, color="gray", ls=":", lw=.8)
    a.set(title=f"{grp} (L={geo.length_m[grp]:.1f}m)", xlabel="횡단보도 축 방향 속도 (m/s)", xlim=(0, 3)); a.legend(fontsize=8)
ax[0].set_ylabel("누적 비율 (%)")
fig.suptitle("완료자 vs 미완료자 속도 분포 (같은 방법: 축 방향 이동거리 ÷ 관측시간, 회색 선 = 1.0 / 0.8 m/s)")
fig.tight_layout(); fig.savefig(f"{OUT}/partial_speed_compare.png", dpi=150)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(cmp.round(3).to_string()); print("v_axis/v_gate (complete):", method_ratio.round(3).to_dict())
print(gs.to_string())
