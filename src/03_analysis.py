"""Step 03 - evaluation metrics and pre-specified analyses (PROTOCOL §7-§8) for ridge-based methods.
RQ1 panel (Spec A/B, wild cluster bootstrap), placebo year, event study, recovery time (RQ2),
net-load direct vs component combination (RQ3), operational shortfall/excess (RQ4)."""
import json, numpy as np, pandas as pd
R = "/tmp/proj/results"; OUT = "/tmp/proj/results/analysis"
import os; os.makedirs(OUT, exist_ok=True)
COUNTRIES = json.load(open("/tmp/proj/audit/01_config.json"))["countries"]
ISO3 = {"AT":"AUT","BE":"BEL","BG":"BGR","CH":"CHE","CZ":"CZE","DE":"DEU","DK":"DNK","ES":"ESP","FR":"FRA",
        "GB_GBN":"GBR","GR":"GRC","PT":"PRT","RO":"ROU","SI":"SVN","SK":"SVK"}
LEVELS = [80, 90, 95]; METHODS = ["I1", "I2", "I3"]; B = 9999; RNG = np.random.default_rng(20261023)

ox = pd.read_csv("/tmp/proj/data/OxCGRT_compact_national_v1.csv", low_memory=False,
                 usecols=["CountryCode", "Jurisdiction", "Date", "StringencyIndex_Average"])
ox = ox[ox.Jurisdiction == "NAT_TOTAL"].copy()
ox["date"] = pd.to_datetime(ox.Date.astype(str), format="%Y%m%d")
ox = ox[(ox.date >= "2020-01-01") & (ox.date <= "2020-09-30")]

def stringency(country, setup):
    s = ox[ox.CountryCode == ISO3[country]].set_index("date").StringencyIndex_Average
    s = s.reindex(pd.date_range("2020-01-01", "2020-09-30")).ffill().fillna(0.0)
    if setup == "placebo":                       # same calendar dates in 2019; 29 Feb dropped
        s = s[~((s.index.month == 2) & (s.index.day == 29))]
        s.index = s.index.map(lambda d: d.replace(year=2019))
    return s

def load(country, setup):
    o = pd.read_parquet(f"{R}/{setup}_{country}.parquet")
    o["target_time"] = pd.to_datetime(o.target_time, utc=True)
    return o[o.part == "test"].copy()

def bounds(o, v, m, L):
    pc = "p_solar_clip" if v == "solar" else f"p_{v}"
    hw = o[f"hw_{m}_{v}_{L}"]; lo, hi = o[pc] - hw, o[pc] + hw
    if v == "solar": lo = lo.clip(lower=0)
    return lo, hi

def evalmask(o, v):
    m = o[f"y_{v}"].notna() & o[f"hw_I1_{v}_90"].notna()
    return m & o.daylight if v == "solar" else m

# ---------------- country-day miscoverage panel ----------------
def panel(setup, v, m="I1", L=90):
    rows = []
    for c in COUNTRIES:
        o = load(c, setup); e = evalmask(o, v); lo, hi = bounds(o, v, m, L)
        miss = ((o[f"y_{v}"] < lo) | (o[f"y_{v}"] > hi)).astype(float)[e]
        day = o.target_time.dt.tz_convert(None).dt.normalize()[e]
        g = miss.groupby(day).agg(["mean", "size"]).rename(columns={"mean": "miscov", "size": "n_hours"})
        g["stringency"] = stringency(c, setup).reindex(g.index).values
        g["country"] = c; rows.append(g.reset_index(names="date"))
    p = pd.concat(rows, ignore_index=True)
    p["dow"] = p.date.dt.dayofweek; p["month"] = p.date.dt.month
    doy = p.date.dt.dayofyear - 1
    p["doy_s"], p["doy_c"] = np.sin(2*np.pi*doy/365.25), np.cos(2*np.pi*doy/365.25)
    return p

def fe_matrix(p, spec):
    parts = [pd.get_dummies(p.country, drop_first=False, dtype=float),
             pd.get_dummies(p.dow, prefix="dow", drop_first=True, dtype=float), p[["doy_s", "doy_c"]]]
    if spec == "B": parts.append(pd.get_dummies(p.month, prefix="m", drop_first=True, dtype=float))
    return pd.concat(parts, axis=1).values

def wild_cluster(p, spec):
    """beta on stringency; CR1 SE; WCR bootstrap p-value and WCU percentile-t 95% CI (Webb 6-point weights)."""
    y, s, cl = p.miscov.values, p.stringency.values, p.country.values
    Z = fe_matrix(p, spec); P = Z @ np.linalg.pinv(Z)
    yt, st = y - P @ y, s - P @ s
    N, K = len(y), np.linalg.matrix_rank(Z) + 1
    groups = [np.where(cl == g)[0] for g in np.unique(cl)]; G = len(groups)
    adj = G / (G - 1) * (N - 1) / (N - K)
    def est(yv):
        b = st @ yv / (st @ st); e = yv - b * st
        meat = sum((st[ix] @ e[ix]) ** 2 for ix in groups)
        return b, np.sqrt(adj * meat) / (st @ st)
    b, se = est(yt); t = b / se
    webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    W = webb[RNG.integers(0, 6, size=(B, G))]
    wobs = np.empty((B, N))
    for gi, ix in enumerate(groups): wobs[:, ix] = W[:, [gi]]
    tr = np.empty(B); tu = np.empty(B); er = yt; eu = yt - b * st
    for i in range(B):
        bb, ss = est(er * wobs[i]); tr[i] = bb / ss                 # restricted: H0 beta=0
        bb, ss = est(b * st + eu * wobs[i]); tu[i] = (bb - b) / ss  # unrestricted for CI
    pval = np.mean(np.abs(tr) >= abs(t))
    lo, hi = b - np.quantile(tu, 0.975) * se, b - np.quantile(tu, 0.025) * se
    return dict(beta=b, se_cr1=se, t=t, p_wcr=pval, ci_lo=lo, ci_hi=hi, n_obs=N, n_clusters=G)

rq1 = []
panels = {}
for setup in ("main", "placebo"):
    for v in ("load", "solar", "net"):
        p = panel(setup, v); panels[(setup, v)] = p
        p.to_csv(f"{OUT}/panel_{setup}_{v}.csv", index=False)
        for spec in ("A", "B"):
            r = wild_cluster(p, spec); r.update(setup=setup, target=v, spec=spec,
                                                 beta_per_10pts_pp=r["beta"] * 10 * 100)
            rq1.append(r); print("RQ1", setup, v, spec, {k: round(r[k], 5) for k in ("beta", "p_wcr", "ci_lo", "ci_hi")}, flush=True)
pd.DataFrame(rq1).to_csv(f"{OUT}/rq1_panel_regressions.csv", index=False)

# ---------------- onset, event study ----------------
onset = {c: stringency(c, "main").ge(50).idxmax() for c in COUNTRIES}
onset40 = {c: stringency(c, "main").ge(40).idxmax() for c in COUNTRIES}
pd.DataFrame({"onset50": onset, "onset40": onset40}).to_csv(f"{OUT}/onset_dates.csv")
ev = []
for v in ("load", "solar", "net"):
    p = panels[("main", v)].copy()
    p["rel"] = [(d - onset[c]).days for d, c in zip(p.date, p.country)]
    base = p[p.rel < 0].groupby("country").miscov.mean()
    p["miscov_vs_pre"] = p.miscov - p.country.map(base)
    e = p[(p.rel >= -28) & (p.rel <= 90)].groupby("rel").agg(miscov=("miscov", "mean"), vs_pre=("miscov_vs_pre", "mean"),
                                                              n=("country", "nunique")).reset_index()
    e["target"] = v; ev.append(e)
pd.concat(ev).to_csv(f"{OUT}/event_study.csv", index=False)

# ---------------- coverage tables, recovery (RQ2), operational (RQ4) ----------------
cov, rec, ops = [], [], []
for c in COUNTRIES:
    o = load(c, "main"); day = o.target_time.dt.tz_convert(None).dt.normalize()
    for v in ("load", "solar", "net"):
        e = evalmask(o, v); y = o[f"y_{v}"]
        for m in METHODS:
            for L in LEVELS:
                lo, hi = bounds(o, v, m, L); a = 1 - L / 100
                inside = ((y >= lo) & (y <= hi))[e]
                isc = ((hi - lo) + 2/a*(lo - y)*(y < lo) + 2/a*(y - hi)*(y > hi))[e]
                pre = (day < onset[c])[e]
                cov.append(dict(country=c, target=v, method=m, level=L, coverage=inside.mean(),
                                coverage_pre=inside[pre].mean(), coverage_post=inside[~pre].mean(),
                                width=(hi - lo)[e].mean(), interval_score=isc.mean(), n=int(e.sum())))
                if L in (90, 95):
                    gwh = o.y_load[e].sum() / 1000
                    ops.append(dict(country=c, target=v, method=m, level=L,
                                    shortfall_MWh_per_GWh=((y - hi).clip(lower=0))[e].sum() / gwh,
                                    excess_MWh_per_GWh=((hi - y).clip(lower=0))[e].sum() / gwh))
                if L == 90:
                    dc = inside.groupby(day[e]).agg(["sum", "size"])
                    dc = dc.reindex(pd.date_range(dc.index.min(), "2020-09-30"), fill_value=0)
                    roll = dc["sum"].rolling(14).sum() / dc["size"].rolling(14).sum()
                    for name, on in (("onset50", onset[c]), ("onset40", onset40[c])):
                        ok = (roll - 0.90).abs() <= 0.025
                        stay = ok[::-1].rolling(14).min()[::-1] == 1   # in band for d..d+13
                        cand = stay[(stay.index >= on) & stay]
                        rec.append(dict(country=c, target=v, method=m, onset=name,
                                        recovery_days=(cand.index[0] - on).days if len(cand) else np.nan,
                                        censored=len(cand) == 0))
pd.DataFrame(cov).to_csv(f"{OUT}/coverage_width_score.csv", index=False)
pd.DataFrame(rec).to_csv(f"{OUT}/rq2_recovery.csv", index=False)
pd.DataFrame(ops).to_csv(f"{OUT}/rq4_operational.csv", index=False)

# ---------------- RQ3 net load: direct (N1) vs component combination (N2), dependence ----------------
rq3, dep = [], []
for c in COUNTRIES:
    o = load(c, "main"); y = o.y_net; e = evalmask(o, "net")
    for m in METHODS:
        for L in LEVELS:
            a = 1 - L / 100
            lo1, hi1 = bounds(o, "net", m, L)
            ll, hl = bounds(o, "load", m, L); ls, hs = bounds(o, "solar", m, L)
            lo2, hi2 = ll - hs, hl - ls
            for name, lo, hi in (("N1_direct", lo1, hi1), ("N2_combination", lo2, hi2)):
                isc = ((hi - lo) + 2/a*(lo - y)*(y < lo) + 2/a*(y - hi)*(y > hi))[e]
                rq3.append(dict(country=c, method=m, level=L, approach=name,
                                coverage=((y >= lo) & (y <= hi))[e].mean(), width=(hi - lo)[e].mean(), interval_score=isc.mean()))
    full = pd.read_parquet(f"{R}/main_{c}.parquet")
    for part in ("cal", "test"):
        q = full[(full.part == part) & full.daylight].dropna(subset=["y_load", "y_solar"])
        rl, rs = q.y_load - q.p_load, q.y_solar - q.p_solar_clip
        dep.append(dict(country=c, part=part, spearman_load_solar_resid=rl.corr(rs, method="spearman"), n=len(q)))
pd.DataFrame(rq3).to_csv(f"{OUT}/rq3_netload.csv", index=False)
pd.DataFrame(dep).to_csv(f"{OUT}/rq3_dependence.csv", index=False)
print("STEP 03 COMPLETE")
