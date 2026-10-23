"""E2 - protocol-extension-v1.1 §5. Primary: E-C (country + date FE), window 2020-10-01..2021-06-30,
wild cluster bootstrap (Webb, 9,999). Secondary (i)-(vi). Sensitivities: no Q1/Q2; untagged 5% rule."""
import json, sys, numpy as np, pandas as pd
R = "/tmp/proj/results/ext"; OUT = "/tmp/proj/results/ext/analysis"; import os; os.makedirs(OUT, exist_ok=True)
C15 = ["AT","BE","BG","CH","CZ","DE","DK","ES","FR","GB_GBN","GR","PT","RO","SI","SK"]
ISO3 = {"AT":"AUT","BE":"BEL","BG":"BGR","CH":"CHE","CZ":"CZE","DE":"DEU","DK":"DNK","ES":"ESP","FR":"FRA","GB_GBN":"GBR","GR":"GRC","PT":"PRT","RO":"ROU","SI":"SVN","SK":"SVK"}
ox = pd.read_csv("/tmp/proj/data/OxCGRT_compact_national_v1.csv", low_memory=False, usecols=["CountryCode","Jurisdiction","Date","StringencyIndex_Average"])
ox = ox[ox.Jurisdiction == "NAT_TOTAL"]; ox["date"] = pd.to_datetime(ox.Date.astype(str), format="%Y%m%d")
def stringency(c):
    s = ox[ox.CountryCode == ISO3[c]].set_index("date").StringencyIndex_Average
    return s.reindex(pd.date_range("2020-01-01", "2021-06-30")).ffill().fillna(0.0)
B = 9999; WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])

def panel(tag, v, countries, start, end, method="I1", excl_solar=()):
    rows = []
    for c in countries:
        if v in ("solar", "net") and c in excl_solar: continue
        o = pd.read_parquet(f"{R}/{tag}_{c}.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True)
        o = o[(o.part == "test") & (o.target_time >= pd.Timestamp(start, tz="UTC")) & (o.target_time <= pd.Timestamp(end, tz="UTC") + pd.Timedelta(hours=23))]
        pc = "p_solar_clip" if v == "solar" else f"p_{v}"; hw = o[f"hw_{method}_{v}_90"]
        lo, hi = o[pc] - hw, o[pc] + hw
        if v == "solar": lo = lo.clip(lower=0)
        e = o[f"y_{v}"].notna() & hw.notna(); e = e & o.daylight if v == "solar" else e
        miss = ((o[f"y_{v}"] < lo) | (o[f"y_{v}"] > hi)).astype(float)[e]
        day = o.target_time.dt.tz_convert(None).dt.normalize()[e]
        g = miss.groupby(day).mean().rename("miscov").to_frame(); g["stringency"] = stringency(c).reindex(g.index).values; g["country"] = c
        rows.append(g.reset_index(names="date"))
    p = pd.concat(rows, ignore_index=True); p["dow"] = p.date.dt.dayofweek; p["month"] = p.date.dt.to_period("M").astype(str)
    doy = p.date.dt.dayofyear - 1; p["doy_s"], p["doy_c"] = np.sin(2*np.pi*doy/365.25), np.cos(2*np.pi*doy/365.25)
    p["t"] = (p.date - p.date.min()).dt.days / 365.25
    return p

def Z_of(p, spec):
    parts = [pd.get_dummies(p.country, dtype=float)]
    if spec in ("C", "Ctrend"): parts.append(pd.get_dummies(p.date.dt.strftime("%Y%m%d"), prefix="d", drop_first=True, dtype=float))
    if spec == "Ctrend": parts.append(pd.get_dummies(p.country, dtype=float).mul(p.t, axis=0).add_prefix("tr_"))
    if spec == "A": parts += [pd.get_dummies(p.dow, prefix="w", drop_first=True, dtype=float), p[["doy_s", "doy_c"]]]
    return pd.concat(parts, axis=1).values

def wild(p, spec, seed=20261023):
    rng = np.random.default_rng(seed); Z = Z_of(p, spec); P = Z @ np.linalg.pinv(Z)
    y, s = p.miscov.values, p.stringency.values; yt, st = y - P @ y, s - P @ s
    groups = [np.where(p.country.values == g)[0] for g in p.country.unique()]; G = len(groups); N = len(y); K = np.linalg.matrix_rank(Z) + 1
    adj = G / (G - 1) * (N - 1) / (N - K)
    def est(yv):
        b = st @ yv / (st @ st); e = yv - b * st
        return b, np.sqrt(adj * sum((st[ix] @ e[ix]) ** 2 for ix in groups)) / (st @ st)
    b, se = est(yt); t = b / se; W = WEBB[rng.integers(0, 6, size=(B, G))]; wobs = np.empty((B, N))
    for gi, ix in enumerate(groups): wobs[:, ix] = W[:, [gi]]
    tr, tu = np.empty(B), np.empty(B); eu = yt - b * st
    for i in range(B):
        bb, ss = est(yt * wobs[i]); tr[i] = bb / ss
        bb, ss = est(b * st + eu * wobs[i]); tu[i] = (bb - b) / ss
    return dict(beta10=1000*b, lo10=1000*(b - np.quantile(tu, .975)*se), hi10=1000*(b - np.quantile(tu, .025)*se), p=float(np.mean(np.abs(tr) >= abs(t))), n=N, G=G)

def perm(p, spec="C", draws=4999, seed=7):
    rng = np.random.default_rng(seed); Z = Z_of(p, spec); P = Z @ np.linalg.pinv(Z); yt = p.miscov.values - P @ p.miscov.values
    cs = list(p.country.unique()); S = {c: stringency(c) for c in cs}
    def b(mp):
        s = np.array([S[mp[c]].get(d, 0.0) for c, d in zip(p.country, p.date)]); st = s - P @ s; return st @ yt / (st @ st)
    b0 = b({c: c for c in cs}); dr = np.array([b(dict(zip(cs, rng.permutation(cs)))) for _ in range(draws)])
    return dict(beta10=1000*b0, p_perm=float((1 + np.sum(np.abs(dr) >= abs(b0))) / (draws + 1)))

def verdict(r_load, r_solar):
    if r_load["lo10"] > 0 and r_solar["p"] >= 0.05: return "Intensity effect supported"
    if r_load["hi10"] < 0.5: return "Intensity effect rejected (practical null)"
    return "Inconclusive"

if __name__ == "__main__":
    step = sys.argv[1]; res = {}
    audit = pd.read_csv(f"{R}/ext_audit_all.csv"); excl = tuple(audit.loc[audit.Q2_solar_excluded, "country"])
    W0, W1 = "2020-10-01", "2021-06-30"
    if step == "primary":
        for v in ("load", "net", "solar"):
            p = panel("ext", v, C15, W0, W1, excl_solar=excl); p.to_csv(f"{OUT}/panel_ext_{v}.csv", index=False)
            res[f"EC_{v}"] = wild(p, "C"); print("E-C", v, res[f"EC_{v}"], flush=True)
        res["verdict"] = verdict(res["EC_load"], res["EC_solar"]); res["Q2_excluded_solar"] = list(excl)
        print("VERDICT (pre-registered rule):", res["verdict"], flush=True)
    if step == "secondary":
        for v in ("load", "net", "solar"):
            p = pd.read_csv(f"{OUT}/panel_ext_{v}.csv", parse_dates=["date"])
            res[f"ECtrend_{v}"] = wild(p, "Ctrend"); res[f"A_{v}"] = wild(p, "A")
            print(v, "Ctrend", res[f"ECtrend_{v}"], "| A", res[f"A_{v}"], flush=True)
            pp = panel("ext", v, C15, "2020-01-01", W1, excl_solar=excl); res[f"pooled_EC_{v}"] = wild(pp, "C"); print(v, "pooled E-C", res[f"pooled_EC_{v}"], flush=True)
    if step == "perm":
        for v in ("load", "net"):
            p = pd.read_csv(f"{OUT}/panel_ext_{v}.csv", parse_dates=["date"]); res[f"perm_{v}"] = perm(p, "C"); print("perm", v, res[f"perm_{v}"], flush=True)
    if step == "sens":
        for v in ("load", "net", "solar"):
            p = panel("ext_noQ", v, C15, W0, W1); res[f"noQ_EC_{v}"] = wild(p, "C"); print("noQ", v, res[f"noQ_EC_{v}"], flush=True)
            keep = [c for c in C15 if c not in ("CH", "SI")]
            ex5 = tuple(set(excl) | {"AT"}) if v in ("solar", "net") else excl
            p = panel("ext", v, keep, W0, W1, excl_solar=ex5); res[f"rule5_EC_{v}"] = wild(p, "C"); print("5%-rule", v, res[f"rule5_EC_{v}"], flush=True)
    if step == "descriptive":
        rows = []
        for c in C15:
            o = pd.read_parquet(f"{R}/ext_{c}.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True); o = o[o.part == "test"]
            mon = o.target_time.dt.to_period("M").astype(str)
            for v in ("load", "net", "solar"):
                if v in ("solar", "net") and c in excl: continue
                pc = "p_solar_clip" if v == "solar" else f"p_{v}"; e = o[f"y_{v}"].notna(); e = e & o.daylight if v == "solar" else e
                for m in ("I1", "I2", "I3"):
                    hw = o[f"hw_{m}_{v}_90"]; lo, hi = o[pc] - hw, o[pc] + hw
                    ins = ((o[f"y_{v}"] >= lo) & (o[f"y_{v}"] <= hi))
                    for mo, g in ins[e].groupby(mon[e]): rows.append(dict(country=c, target=v, method=m, month=mo, coverage=g.mean()))
        cm = pd.DataFrame(rows); cm.to_csv(f"{OUT}/coverage_by_month.csv", index=False)
        print(cm.groupby(["target", "method", "month"]).coverage.mean().unstack("month").round(3).to_string())
        # (v) stacked event study of tightening events (>= +20 points within 14 days)
        ev = []
        for v in ("load", "net"):
            p = pd.read_csv(f"{OUT}/panel_ext_{v}.csv", parse_dates=["date"]); k = 0
            for c in C15:
                s = stringency(c).loc[W0:W1]; inc = s - s.shift(14); cand = inc[inc >= 20].index
                last = None
                for d in cand:
                    if last is not None and (d - last).days < 56: continue
                    last = d; k += 1; q = p[p.country == c].copy(); q["rel"] = (q.date - d).dt.days; q = q[(q.rel >= -14) & (q.rel <= 42)]
                    base = q[q.rel < 0].miscov.mean(); q["vs"] = q.miscov - base; q["event"] = f"{c}_{d.date()}"; q["target"] = v; ev.append(q)
            print(v, "tightening events:", k)
        evd = pd.concat(ev); evd.to_csv(f"{OUT}/tightening_events.csv", index=False)
        print(evd.groupby(["target", pd.cut(evd.rel, [-15, -1, 13, 27, 42])]).vs.agg(["mean", "count"]).round(3))
    json.dump(res, open(f"{OUT}/E2_{step}.json", "w"), default=float, indent=1)
