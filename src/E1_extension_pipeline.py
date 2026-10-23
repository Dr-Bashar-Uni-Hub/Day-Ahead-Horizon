"""E1 - protocol-extension-v1.1: combine OPSD (<= 2020-09-30) with Energy-Charts (>= 2020-10-01),
apply Q1 (spikes) and Q2 (solar definition breaks), rebuild day-ahead features, refit the deterministic
ridge models exactly as protocol-v1.0 (train 2015-01-15..2018, penalty on 2019), and compute I1/I2/I3
for a continuous deployment from 2020-01-01 to 2021-06-30. Computes no regression results."""
import json, sys, numpy as np, pandas as pd, holidays, warnings; warnings.filterwarnings("ignore")
src2 = open("/tmp/proj/src/02_ridge_intervals.py").read().split("if __name__")[0]; exec(src2)
_cq_orig = cq
def cq(scores, level):            # extension: an empty window (all targets removed by Q1) yields a missing half-width
    sc = np.asarray(scores, float)
    return np.nan if sc.size == 0 or np.isnan(sc).all() else _cq_orig(sc, level)
MAP = {"AT":"at","BE":"be","BG":"bg","CH":"ch","CZ":"cz","DE":"de","DK":"dk","ES":"es","FR":"fr","GB_GBN":"uk","GR":"gr","PT":"pt","RO":"ro","SI":"si","SK":"sk"}
HOL = {"GB_GBN": "GB"}
OUTE = "/tmp/proj/results/ext"; os.makedirs(OUTE, exist_ok=True)
opsd = pd.read_csv("/mnt/user-data/uploads/time_series_60min_singleindex.csv", parse_dates=["utc_timestamp"], low_memory=False).set_index("utc_timestamp")
opsd = opsd["2015-01-01":"2020-09-30 23:00"]
IDX = pd.date_range("2015-01-01", "2021-06-30 23:00", freq="1h", tz="UTC")

def combined(c, apply_q=True):
    ec = pd.read_csv(f"/tmp/proj/data/ext/{MAP[c]}_energycharts.csv", index_col=0, parse_dates=True); ec.index = pd.to_datetime(ec.index, utc=True)
    s = pd.DataFrame(index=IDX)
    for v, oc, ecc in (("load", f"{c}_load_actual_entsoe_transparency", "Load"), ("solar", f"{c}_solar_generation_actual", "Solar")):
        a = opsd[oc].reindex(IDX); b = ec[ecc].reindex(IDX)
        s[v] = a.where(IDX < pd.Timestamp("2020-10-01", tz="UTC"), b)
    audit = dict(country=c)
    if apply_q:
        tr = s["2015-01-15":"2018-12-31"]
        for v in ("load", "solar"):                                   # Q1 spikes
            thr = 3 * tr[v].quantile(0.999); bad = s[v] > thr
            audit[f"Q1_{v}_removed"] = int(bad.sum()); s.loc[bad, v] = np.nan
        m19 = s.loc["2019", "solar"].max(); mext = s.loc["2020-10-01":, "solar"].max()   # Q2 definition break
        audit["Q2_solar_excluded"] = bool(mext > 2.5 * m19); audit["solar_max_2019"] = m19; audit["solar_max_ext"] = mext
    else:
        audit["Q2_solar_excluded"] = False
    return s, audit

def features(c, s):
    s = s.copy(); s["net"] = s.load - s.solar
    f = s[["load", "solar"]].ffill(limit=3)
    hcal = holidays.country_holidays(HOL.get(c, c), years=range(2014, 2022))
    days = pd.date_range("2015-01-15", "2021-06-30", freq="D", tz="UTC"); rec = []
    fl, fs = f.load.to_dict(), f.solar.to_dict()
    for D in days:
        ie = D - pd.Timedelta(days=1) + pd.Timedelta(hours=10)
        w = f.loc[ie - pd.Timedelta(hours=23): ie]; m24 = w.mean()
        for h in range(24):
            t = D + pd.Timedelta(hours=h); r = {"target_time": t, "hour": h}
            for v, dd in (("load", fl), ("solar", fs)):
                for L in (48, 72, 168): r[f"{v}_lag{L}"] = dd.get(t - pd.Timedelta(hours=L), np.nan)
                r[f"{v}_last"] = dd.get(ie, np.nan); r[f"{v}_mean24"] = m24[v]
            for v in ("load", "solar", "net"): r[f"y_{v}"] = s[v].get(t, np.nan)
            rec.append(r)
    d = pd.DataFrame(rec); d["dow"] = d.target_time.dt.dayofweek
    d["hour_sin"], d["hour_cos"] = np.sin(2*np.pi*d.hour/24), np.cos(2*np.pi*d.hour/24)
    d["dow_sin"], d["dow_cos"] = np.sin(2*np.pi*d.dow/7), np.cos(2*np.pi*d.dow/7)
    doy = d.target_time.dt.dayofyear - 1; d["doy_sin"], d["doy_cos"] = np.sin(2*np.pi*doy/365.25), np.cos(2*np.pi*doy/365.25)
    d["holiday"] = d.target_time.dt.date.map(lambda x: x in hcal).astype(int)
    d["holiday_prev"] = (d.target_time - pd.Timedelta(days=1)).dt.date.map(lambda x: x in hcal).astype(int)
    return d

def run(c, apply_q=True, tag="ext"):
    s, audit = combined(c, apply_q); d = features(c, s)
    global LAGF
    lagf_full = [f"{v}_{k}" for v in ("load", "solar") for k in ("lag48", "lag72", "lag168", "last", "mean24")]
    LAGF = [x for x in lagf_full if not (audit["Q2_solar_excluded"] and x.startswith("solar"))]   # Q2: load lags only
    d["feat_ok"] = d[LAGF].notna().all(1); d = d[d.feat_ok].reset_index(drop=True)
    tr = in_range(d.target_time, "2015-01-15", "2018-12-31"); ca = in_range(d.target_time, "2019-01-01", "2019-12-31")
    te = in_range(d.target_time, "2020-01-01", "2021-06-30")
    X = design(d); out = d.loc[ca | te, ["target_time", "hour", "y_load", "y_solar", "y_net"]].copy()
    out["part"] = np.where(ca[ca | te], "cal", "test")
    for v in ("load", "solar"):
        ok = d[f"y_{v}"].notna().values
        f_, a = fit_ridge(X[tr.values & ok], d.loc[tr & ok, f"y_{v}"].values, X[ca.values & ok], d.loc[ca & ok, f"y_{v}"].values)
        out[f"p_{v}"] = f_(X[(ca | te).values]); audit[f"alpha_{v}"] = a
    out["p_solar_clip"] = out.p_solar.clip(lower=0); out["p_net"] = out.p_load - out.p_solar_clip
    cal = out[out.part == "cal"]; mx = cal.y_solar.max(); mm = cal.assign(m=cal.target_time.dt.month).groupby(["m", "hour"]).y_solar.mean()
    out["daylight"] = [mm.get((m, h), 0) >= 0.01 * mx for m, h in zip(out.target_time.dt.month, out.hour)]
    for v in ("load", "solar", "net"):
        pc = "p_solar_clip" if v == "solar" else f"p_{v}"; out[f"ar_{v}"] = (out[f"y_{v}"] - out[pc]).abs()
    out["issue_day"] = out.target_time.dt.floor("D"); out["reveal_time"] = (out.target_time + pd.Timedelta(hours=1)).dt.tz_convert(None)
    gam = {m["country"]: m["aci_gamma"] for m in json.load(open("/tmp/proj/results/main_meta.json"))}[c]
    tm = out.part == "test"; days = sorted(out.loc[tm, "issue_day"].unique()); cal = out[out.part == "cal"]
    for v in ("load", "solar", "net"):
        out[f"hw_I1_{v}_90"] = out.hour.map(static_halfwidth(cal, f"ar_{v}", 0.90))
        rh = rolling_halfwidth(out, f"ar_{v}", 0.90, days); hw2 = np.full(len(out), np.nan)
        for i in np.where(tm)[0]: hw2[i] = rh[out.issue_day.iat[i]][out.hour.iat[i]]
        out[f"hw_I2_{v}_90"] = hw2
        scal = {h: g[f"ar_{v}"].values for h, g in cal.groupby("hour")}
        st = out.loc[tm, ["hour", f"ar_{v}", "issue_day", "reveal_time"]].rename(columns={f"ar_{v}": "absres"})
        col = np.full(len(out), np.nan); col[np.where(tm)[0]] = run_aci(scal, st, 0.90, gam[v]); out[f"hw_I3_{v}_90"] = col
    out.drop(columns=["reveal_time"]).to_parquet(f"{OUTE}/{tag}_{c}.parquet", index=False)
    return audit

if __name__ == "__main__":
    tag = sys.argv[1]; apply_q = tag != "ext_noQ"
    cs = sys.argv[2].split(",") if len(sys.argv) > 2 else list(MAP)
    audits = []
    for c in cs:
        a = run(c, apply_q, tag); audits.append(a); print(tag, c, {k: a[k] for k in a if k.startswith(("Q", "alpha"))}, flush=True)
    pd.DataFrame(audits).to_csv(f"{OUTE}/{tag}_audit_{'_'.join(cs) if len(cs) < 15 else 'all'}.csv", index=False)
