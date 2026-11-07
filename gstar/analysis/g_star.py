"""View2Risk — 횡단보도별 보행 완료시간 기반 필요 보행시간 G*(p) 분석 (v0).

입력 (get_data.py --preset analysis 로 받은 workspace):
  view2risk/runs/audit_261026/data/crossing_events.parquet   횡단 이벤트 (base 규칙)
  full_rq_261026/data/processed/imptc_pedestrian_tracks.parquet  신호 f1/f2/f3, 날씨, 주변 보행자
  full_rq_261026/data/spd_pair_residuals.parquet             V2X-Seq SPD 위치 차이 (R 시나리오)
  results/audit_261026/geometry.csv (repo)                   횡단보도 길이

사용: python g_star.py <workspace> <repo> <outdir>
"""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minipq

WS, REPO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(261102)
P_GRID = np.round(np.arange(0.50, 0.991, 0.01), 2)
P_REPORT = [0.50, 0.85, 0.90, 0.95]
KR_ENTRY_S = 7.0          # 국내 공식의 보행 진입시간 (매뉴얼 값 확인 필요)
KR_SPEED = {"일반 1.0m/s": 1.0, "보호구역 0.8m/s": 0.8}

def rd(path, cols=None):
    return pd.DataFrame(minipq.read(path, cols))

# ---------------- 1. 입력 ----------------
ev = rd(f"{WS}/view2risk/runs/audit_261026/data/crossing_events.parquet")
ev = ev[ev.config == "base"].copy()
geo = pd.read_csv(f"{REPO}/results/audit_261026/geometry.csv", encoding="utf-8-sig")
L = dict(zip(geo.signal_group, geo.length_m))
tr = rd(f"{WS}/full_rq_261026/data/processed/imptc_pedestrian_tracks.parquet",
        ["sequence_id", "track_uid", "ts_us", "signal_age_s", "signal_f1", "signal_f2", "signal_f3",
         "weather_name", "nearby_ped_count", "concurrent_ped_count"])

# ---------------- 2. 신호 타임라인 → 녹색 시작/종료 ----------------
tr["rec_ts"] = (tr.ts_us / 1e6 - tr.signal_age_s).round(1)
tl = (tr.dropna(subset=["signal_f1"]).groupby(["sequence_id", "rec_ts"])
      [["signal_f1", "signal_f2", "signal_f3"]].first().reset_index().sort_values(["sequence_id", "rec_ts"]))
phases = []
for (seq), g in tl.groupby("sequence_id"):
    t = g.rec_ts.values
    for grp in ["f1", "f2", "f3"]:
        c = g[f"signal_{grp}"].values
        cur = None
        for i in range(1, len(t)):
            gap = t[i] - t[i-1]
            if gap > 1.5:                       # 기록 끊김 → 진행 중 phase 무효
                cur = None; continue
            if c[i-1] == 10 and c[i] == 4:
                cur = {"sequence_id": seq, "signal_group": grp, "onset": (t[i-1] + t[i]) / 2, "end": np.nan}
                phases.append(cur)
            elif c[i-1] == 4 and c[i] == 10 and cur is not None:
                cur["end"] = (t[i-1] + t[i]) / 2; cur = None
        # cur 이 끝까지 열린 채 남으면 end=NaN (시퀀스 종료로 미관측)
ph = pd.DataFrame(phases)
ph["green_s"] = ph.end - ph.onset
ph["phase_id"] = np.arange(len(ph))

# 주기 (같은 그룹의 연속 onset 간격, 기록 연속 구간 안에서만)
cyc = ph.sort_values(["sequence_id", "signal_group", "onset"]).groupby(["sequence_id", "signal_group"]).onset.diff()
ph["cycle_s"] = cyc.values if False else np.nan
ph = ph.sort_values(["sequence_id", "signal_group", "onset"]).reset_index(drop=True)
ph["cycle_s"] = ph.groupby(["sequence_id", "signal_group"]).onset.diff()
ph.loc[ph.cycle_s > 200, "cycle_s"] = np.nan

# ---------------- 3. 이벤트에 phase 연결 ----------------
comp = ev[ev.classification == "complete_rule"].copy()
cens = ev[ev.classification == "partial_censored"].copy()
cens["obs_s"] = (cens.last_map_ts_us - cens.first_map_ts_us) / 1e6
cens["t_ref"] = cens.first_map_ts_us / 1e6

def attach(df, tcol):
    out = []
    for r in df.itertuples():
        cand = ph[(ph.sequence_id == r.sequence_id) & (ph.signal_group == r.signal_group) & (ph.onset <= getattr(r, tcol))]
        if len(cand) == 0: out.append((np.nan, np.nan)); continue
        c = cand.iloc[-1]
        ok = np.isnan(c.end) or getattr(r, tcol) <= c.end
        out.append((c.phase_id, c.onset) if ok else (np.nan, np.nan))
    df["phase_id"], df["onset"] = zip(*out)
    return df

comp = attach(comp, "entry_ts_s")
comp["L_m"] = comp.signal_group.map(L)
comp["speed_mps"] = comp.L_m / comp.duration_s
comp["D_s"] = comp.entry_ts_s - comp.onset
comp["C_s"] = comp.exit_ts_s - comp.onset
cens = attach(cens, "t_ref")

# 진입 시점의 날씨·주변 보행자
tr_idx = tr.sort_values("ts_us")
def at_entry(r):
    x = tr_idx[tr_idx.track_uid == r.track_uid]
    if len(x) == 0: return (None, np.nan, np.nan)
    i = np.searchsorted(x.ts_us.values, r.entry_ts_s * 1e6); i = min(max(i, 0), len(x) - 1)
    y = x.iloc[i]; return (y.weather_name, y.nearby_ped_count, y.concurrent_ped_count)
comp["weather"], comp["nearby_ped"], comp["concurrent_ped"] = zip(*[at_entry(r) for r in comp.itertuples()])

# ---------------- 4. Kaplan–Meier 분위수 ----------------
def km(t, e):
    t = np.asarray(t, float); e = np.asarray(e, bool)
    o = np.argsort(t); t, e = t[o], e[o]
    ut = np.unique(t[e]); S = 1.0; xs, Fs = [], []
    for u in ut:
        n_risk = np.sum(t >= u); d = np.sum((t == u) & e)
        S *= 1 - d / n_risk; xs.append(u); Fs.append(1 - S)
    return np.array(xs), np.array(Fs)

def km_q(t, e, ps):
    xs, Fs = km(t, e)
    return np.array([xs[np.searchsorted(Fs, p - 1e-12)] if Fs.size and Fs[-1] >= p - 1e-12 else np.nan for p in ps])

def date_boot(df, fn, B=1000):
    dates = df.recording_date.unique(); res = []
    groups = {d: df[df.recording_date == d] for d in dates}
    for _ in range(B):
        pick = rng.choice(dates, len(dates), replace=True)
        res.append(fn(pd.concat([groups[d] for d in pick])))
    return np.nanpercentile(np.array(res), [2.5, 97.5], axis=0)

rows, curves = [], []
for grp in ["f1", "f2", "f3"]:
    c = comp[comp.signal_group == grp]; z = cens[cens.signal_group == grp]
    dd = pd.concat([pd.DataFrame({"t": c.duration_s, "e": True, "recording_date": c.recording_date}),
                    pd.DataFrame({"t": z.obs_s.clip(lower=0.04), "e": False, "recording_date": z.recording_date})])
    fn = lambda d: km_q(d.t, d.e, P_GRID)
    q_km = fn(dd); q_naive = np.quantile(c.duration_s, P_GRID)
    lo, hi = date_boot(dd, fn)
    for p, a, b, l, h in zip(P_GRID, q_km, q_naive, lo, hi):
        curves.append({"signal_group": grp, "p": p, "dur_km_s": a, "dur_complete_only_s": b, "dur_ci_lo": l, "dur_ci_hi": h})
    # 녹색 시작 기준 완료시간 C (첫 진입 무리: D ≤ 7s, 녹색 진입, phase 연결된 이벤트)
    cw = c[(c.entry_signal_code == 4) & c.onset.notna()]
    first = cw[cw.D_s <= KR_ENTRY_S]
    gs = ph[(ph.signal_group == grp)].green_s.dropna(); cy = ph[(ph.signal_group == grp)].cycle_s.dropna()
    row = {"signal_group": grp, "L_m": L[grp], "complete_events": len(c), "censored_events": len(z),
           "green_entry_with_onset": len(cw), "first_wave_D_le_7s": len(first),
           "speed_median_mps": c.speed_mps.median(), "speed_p15_mps": c.speed_mps.quantile(0.15),
           "D_median_s": cw.D_s.median(), "D_p85_s": cw.D_s.quantile(0.85),
           "observed_green_median_s": gs.median(), "observed_green_n": len(gs),
           "observed_cycle_median_s": cy.median(), "observed_cycle_n": len(cy),
           "KR_formula_1.0_s": KR_ENTRY_S + L[grp] / 1.0, "KR_formula_0.8_s": KR_ENTRY_S + L[grp] / 0.8}
    for p in P_REPORT:
        k = int(np.where(np.isclose(P_GRID, p))[0][0])
        row[f"dur_p{int(p*100)}_km_s"] = q_km[k]
        row[f"dur_p{int(p*100)}_ci"] = f"{lo[k]:.1f}–{hi[k]:.1f}"
        row[f"dur_p{int(p*100)}_complete_only_s"] = q_naive[k]
        row[f"Gstar_p{int(p*100)}_s"] = KR_ENTRY_S + q_km[k]
        row[f"C_firstwave_p{int(p*100)}_s"] = first.C_s.quantile(p) if len(first) >= 20 else np.nan
    rows.append(row)
res = pd.DataFrame(rows); cur = pd.DataFrame(curves)

# ---------------- 5. 카메라 오차(R) 시나리오 ----------------
spd = rd(f"{WS}/full_rq_261026/data/spd_pair_residuals.parquet", ["dx", "dy", "model_eligible"])
spd = spd[spd.model_eligible.astype(bool)] if spd.model_eligible.notna().any() else spd
R = np.cov(np.vstack([spd.dx, spd.dy]), ddof=0)
sig_axis = float(np.sqrt(np.trace(R) / 2))
emp = np.concatenate([spd.dx.values, spd.dy.values])
emp_trim = emp[np.abs(emp) <= np.quantile(np.abs(emp), 0.99)]
def sim(kind, reps=300):
    out = {}
    for grp in ["f1", "f2", "f3"]:
        c = comp[comp.signal_group == grp]; v = c.speed_mps.values; d0 = c.duration_s.values
        qs = []
        for _ in range(reps):
            if kind == "gauss": e1, e2 = rng.normal(0, sig_axis, (2, len(v)))
            elif kind == "emp": e1, e2 = rng.choice(emp, (2, len(v)))
            else: e1, e2 = rng.choice(emp_trim, (2, len(v)))
            qs.append(np.quantile(d0 + (e1 - e2) / v, P_REPORT))
        base = np.quantile(d0, P_REPORT); qs = np.array(qs)
        out[grp] = {f"p{int(p*100)}": {"shift_mean_s": float(qs[:, i].mean() - base[i]),
                                         "shift_p95_abs_s": float(np.quantile(np.abs(qs[:, i] - base[i]), 0.95))}
                    for i, p in enumerate(P_REPORT)}
        out[grp]["event_time_noise_sd_s"] = float(np.std(((e1 - e2) / v)))
    return out
sens = {"R_cov_m2": R.tolist(), "sigma_axis_m": sig_axis,
        "gauss": sim("gauss"), "empirical_full": sim("emp"), "empirical_trim99": sim("trim")}

# ---------------- 6. 보조 변수: 날씨·군집 ----------------
aux = []
for grp in ["f1", "f2", "f3"]:
    c = comp[comp.signal_group == grp]
    for w, x in c.groupby("weather"):
        aux.append({"signal_group": grp, "factor": "weather", "level": w, "n": len(x), "dates": x.recording_date.nunique(),
                    "speed_median": x.speed_mps.median(), "dur_p85": x.duration_s.quantile(0.85)})
    b = pd.cut(c.nearby_ped, [-1, 0, 2, 100], labels=["0명", "1–2명", "3명+"])
    for lv, x in c.groupby(b, observed=True):
        aux.append({"signal_group": grp, "factor": "nearby_ped_5m", "level": str(lv), "n": len(x), "dates": x.recording_date.nunique(),
                    "speed_median": x.speed_mps.median(), "dur_p85": x.duration_s.quantile(0.85)})
aux = pd.DataFrame(aux)
spear = comp[["speed_mps", "nearby_ped"]].corr(method="spearman").iloc[0, 1]

# ---------------- 7. Trade-off (보행자 측 실측 + 차량 측 가정 시나리오) ----------------
LOST_S = 4.0
cyc_all = ph.cycle_s.dropna().median()
to = []
for grp in ["f1", "f2", "f3"]:
    k = cur[cur.signal_group == grp]
    for r in k.itertuples():
        G = KR_ENTRY_S + r.dur_km_s
        g = max(cyc_all - G - LOST_S, 1.0); lam = g / cyc_all
        for y in [0.2, 0.3, 0.4]:
            x = y / lam
            d1 = 0.5 * cyc_all * (1 - lam) ** 2 / (1 - min(1, x) * lam)
            to.append({"signal_group": grp, "p": r.p, "G_s": G, "unfinished_pct": 100 * (1 - r.p),
                       "flow_ratio_y_assumed": y, "cycle_s": cyc_all, "veh_green_s": g, "veh_x": x, "veh_uniform_delay_s": d1})
to = pd.DataFrame(to)

# ---------------- 8. 저장 ----------------
comp.drop(columns=["source_path"]).to_csv(f"{OUT}/events_complete.csv", index=False, encoding="utf-8-sig")
ph.to_csv(f"{OUT}/green_phases.csv", index=False, encoding="utf-8-sig")
res.to_csv(f"{OUT}/gstar_by_crosswalk.csv", index=False, encoding="utf-8-sig")
cur.to_csv(f"{OUT}/duration_quantile_curve.csv", index=False, encoding="utf-8-sig")
aux.to_csv(f"{OUT}/aux_factors.csv", index=False, encoding="utf-8-sig")
to.to_csv(f"{OUT}/tradeoff.csv", index=False, encoding="utf-8-sig")
json.dump({"camera_R_sensitivity": sens, "spearman_speed_vs_nearby": spear, "median_cycle_s": cyc_all,
           "phases": len(ph), "phases_with_end": int(ph.end.notna().sum())},
          open(f"{OUT}/summary.json", "w"), ensure_ascii=False, indent=1, default=float)

# ---------------- 9. 그림 ----------------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Noto Sans CJK KR"; plt.rcParams["axes.unicode_minus"] = False
COL = {"f1": "#2a6fdb", "f2": "#d9480f", "f3": "#2b8a3e"}
fig, ax = plt.subplots(2, 2, figsize=(13, 10))
a = ax[0, 0]
for grp in ["f1", "f2", "f3"]:
    c = comp[comp.signal_group == grp]; z = cens[cens.signal_group == grp]
    xs, Fs = km(np.r_[c.duration_s, z.obs_s.clip(lower=0.04)], np.r_[np.ones(len(c)), np.zeros(len(z))])
    a.step(xs, Fs * 100, where="post", color=COL[grp], label=f"{grp} (L={L[grp]:.1f}m, KM)")
    a.step(np.sort(c.duration_s), np.arange(1, len(c) + 1) / len(c) * 100, where="post", color=COL[grp], ls=":", alpha=.6)
for p in [85, 95]: a.axhline(p, color="gray", lw=.6, ls="--")
a.set(xlabel="횡단 소요시간 (s)", ylabel="완료한 보행자 비율 (%)", title="① 횡단 소요시간 분포 (실선 KM, 점선 완료 이벤트만)", xlim=(0, 30)); a.legend()
a = ax[0, 1]
for grp in ["f1", "f2", "f3"]:
    k = cur[cur.signal_group == grp]
    a.plot(k.p * 100, KR_ENTRY_S + k.dur_km_s, color=COL[grp], label=f"{grp} G*(p)")
    a.fill_between(k.p * 100, KR_ENTRY_S + k.dur_ci_lo, KR_ENTRY_S + k.dur_ci_hi, color=COL[grp], alpha=.15)
    a.axhline(KR_ENTRY_S + L[grp] / 1.0, color=COL[grp], ls="--", lw=1)
    a.axhline(KR_ENTRY_S + L[grp] / 0.8, color=COL[grp], ls=":", lw=1)
a.set(xlabel="p (녹색 안에 완료해야 하는 보행자 비율, %)", ylabel="필요 보행시간 G* = 7s + Q_p(소요시간) (s)",
      title="② G*(p)와 국내 공식 (--: 1.0m/s, ··: 0.8m/s), 음영=날짜 bootstrap 95%CI"); a.legend()
a = ax[1, 0]
for grp in ["f1", "f2", "f3"]:
    k = to[(to.signal_group == grp) & (to.flow_ratio_y_assumed == 0.3)]
    a.plot(k.veh_uniform_delay_s, k.unfinished_pct, color=COL[grp], marker=".", ms=3, label=f"{grp}")
    for p in [0.85, 0.95]:
        r = k[np.isclose(k.p, p)].iloc[0]; a.annotate(f"{grp} p={p:.2f}", (r.veh_uniform_delay_s, r.unfinished_pct), fontsize=7, xytext=(4, 4 + 10 * ["f1", "f2", "f3"].index(grp)), textcoords="offset points")
a.set(xlabel=f"교차 방향 차량 균일지연 (s/대) — 가정: 주기 {cyc_all:.0f}s, q/s=0.3, 손실 {LOST_S:.0f}s",
      ylabel="녹색 안에 못 끝내는 보행자 (%)", title="③ Trade-off (차량 측은 가정값 시나리오)"); a.legend()
a = ax[1, 1]
kinds = [("gauss", "Gaussian R"), ("empirical_trim99", "경험분포(상위1% 제외)"), ("empirical_full", "경험분포(전체)")]
w = 0.25
for j, (kind, nm) in enumerate(kinds):
    a.bar(np.arange(3) + (j - 1) * w, [sens[kind][g]["p85"]["shift_mean_s"] for g in ["f1", "f2", "f3"]], w, label=nm,
          color=["#868e96", "#495057", "#212529"][j])
a.set_xticks(range(3)); a.set_xticklabels([f"{g} (L={L[g]:.1f}m)" for g in ["f1", "f2", "f3"]])
a.set(ylabel="Q_0.85 변화 (s)", title="④ V2X-Seq 수준 위치 오차를 넣었을 때 85% 분위수 변화 (s)"); a.legend(fontsize=8)
a.axhline(0, color="k", lw=.6)
fig.tight_layout(); fig.savefig(f"{OUT}/gstar_overview.png", dpi=150)
print(res.T.to_string()); print(json.dumps({k: sens[k] for k in ["sigma_axis_m"]}, default=float))
for kind in ["gauss", "empirical_trim99", "empirical_full"]:
    print(kind, {g: round(sens[kind][g]["p85"]["shift_mean_s"], 3) for g in ["f1", "f2", "f3"]},
          {g: round(sens[kind][g]["p95"]["shift_mean_s"], 3) for g in ["f1", "f2", "f3"]})
print(aux.to_string()); print("spearman", spear, "cycle", cyc_all, "phases", len(ph), ph.end.notna().sum())
print(ph.groupby("signal_group")[["green_s", "cycle_s"]].describe().T)
