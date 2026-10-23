"""POST HOC (P8, after a second AI-generated pre-review): (a) harmonized first wave: Jan-Sep 2020 tests on the
quality-ruled extension files (Q1/Q2 applied); (b) shortfall/headroom by transition window; (c) CQR coverage by
window; (d) recovery-time comparison summary."""
import json, sys, numpy as np, pandas as pd
sys.argv = ["x", "none"]; exec(open("/tmp/proj/src/E2_extension_analysis.py").read().split('if __name__ == "__main__":')[0])
OUTP = "/tmp/proj/results/analysis"; res = {}
audit = pd.read_csv(f"{R}/ext_audit_all.csv"); excl = tuple(audit.loc[audit.Q2_solar_excluded, "country"])
# (a) harmonized first wave
for v in ("load", "net", "solar"):
    p = panel("ext", v, C15, "2020-01-01", "2020-09-30", excl_solar=excl)
    res[f"harm_A_{v}"] = wild(p, "A"); res[f"harm_C_{v}"] = wild(p, "C")
    print("harmonized wave1", v, "A", {k: round(res[f'harm_A_{v}'][k], 4) for k in ('beta10', 'lo10', 'hi10', 'p')}, "| C", {k: round(res[f'harm_C_{v}'][k], 4) for k in ('beta10', 'lo10', 'hi10', 'p')}, flush=True)
    if v != "solar": res[f"harm_perm_{v}"] = perm(p, "A"); print("   perm A", res[f"harm_perm_{v}"], flush=True)
# onset dates
on = {c: stringency(c).loc[:"2020-09-30"].ge(50).idxmax() for c in C15}
def win(day, c):
    rel = (day - on[c]).dt.days; return pd.cut(rel, [-999, -1, 27, 59, 999], labels=["pre", "w0-4", "w5-8", "after w8"])
# (b) shortfall / headroom by window (protocol-v1.0 results, 90%, load and net)
rows = []
for c in C15:
    o = pd.read_parquet(f"/tmp/proj/results/main_{c}.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True); o = o[o.part == "test"]
    day = o.target_time.dt.tz_convert(None).dt.normalize(); w = win(day, c)
    for v in ("load", "net"):
        y = o[f"y_{v}"]; e = y.notna()
        for m in ("I1", "I2", "I3"):
            hi = o[f"p_{v}"] + o[f"hw_{m}_{v}_90"]
            for wn in w.cat.categories:
                k = e & (w == wn); gwh = o.y_load[k].sum() / 1000
                rows.append(dict(country=c, target=v, method=m, window=wn, shortfall=((y - hi).clip(lower=0))[k].sum() / gwh, excess=((hi - y).clip(lower=0))[k].sum() / gwh))
ops = pd.DataFrame(rows).groupby(["target", "method", "window"])[["shortfall", "excess"]].median().reset_index()
res["ops_window"] = ops.to_dict("records"); print(ops[ops.target == "load"].round(2).to_string(index=False))
# (c) CQR coverage by window (load, solar)
exec(open("/tmp/proj/src/02_ridge_intervals.py").read().split("def qlevel")[0].split("def cq")[1].join(["def cq", ""]) if False else "")
def cq(scores, level):
    s = np.sort(scores[~np.isnan(scores)]); n = len(s); k = int(np.ceil((n + 1) * level)) - 1; return s[min(max(k, 0), n - 1)]
rows = []
for c in C15:
    o = pd.read_parquet(f"/tmp/proj/results/lgbm/main_{c}_raw.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True)
    for v in ("load", "solar"):
        y = o[f"y_{v}"]; lo, hi = o[f"qlo_{v}_90"], o[f"qhi_{v}_90"]; cm = (o.part == "cal") & y.notna()
        Q = cq(np.maximum(lo - y, y - hi)[cm].values, 0.90); l2, h2 = lo - Q, hi + Q
        if v == "solar": l2 = l2.clip(lower=0)
        t = o[o.part == "test"].index; tt = o.loc[t]; day = tt.target_time.dt.tz_convert(None).dt.normalize(); w = win(day, c)
        e = y.loc[t].notna() & (tt.daylight if v == "solar" else True); ins = (y.loc[t] >= l2.loc[t]) & (y.loc[t] <= h2.loc[t])
        for wn in w.cat.categories: rows.append(dict(country=c, target=v, window=wn, coverage=ins[e & (w == wn)].mean()))
cqr = pd.DataFrame(rows).groupby(["target", "window"]).coverage.mean().reset_index(); res["cqr_window"] = cqr.to_dict("records"); print(cqr.round(3).to_string(index=False))
# (d) recovery summary
rc = pd.read_csv(f"{OUTP}/rq2_recovery.csv"); rc = rc[rc.onset == "onset50"]
rs = rc.groupby(["target", "method"]).agg(median_days=("recovery_days", "median"), recovered=("censored", lambda x: int((~x).sum()))).reset_index()
res["recovery"] = rs.to_dict("records"); print(rs.to_string(index=False))
json.dump(res, open(f"{OUTP}/posthoc_review2.json", "w"), default=float, indent=1)
