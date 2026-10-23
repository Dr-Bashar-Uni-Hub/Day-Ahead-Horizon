"""POST HOC (P8): (a) second-wave leave-one-country-out E-C (B=1,999); (b) downward exposure Σmax(0, L-y) by window;
(c) updated-deployment benchmark: ridge refit monthly on all data up to the previous month end (expanding window,
original penalty), intervals = split conformal on out-of-sample residuals of the preceding 365 days (by hour),
evaluated Jan 2020 - Jun 2021 with E-C (wave 2) and Spec A/C (wave 1)."""
import json, sys, numpy as np, pandas as pd
sys.argv = ["x", "none"]; exec(open("/tmp/proj/src/E2_extension_analysis.py").read().split('if __name__ == "__main__":')[0])
OUTP = "/tmp/proj/results/analysis"; res = {}; step = sys.argv_step if hasattr(sys, "argv_step") else None
audit = pd.read_csv(f"{R}/ext_audit_all.csv"); excl = tuple(audit.loc[audit.Q2_solar_excluded, "country"])
B_FULL = B
# (a) LOCO
globals()["B"] = 1999
for v in ("load", "net"):
    p = pd.read_csv(f"{OUT}/panel_ext_{v}.csv", parse_dates=["date"]); out = []
    for c in p.country.unique():
        r = wild(p[p.country != c].reset_index(drop=True), "C"); r["dropped"] = c; out.append(r)
    res[f"loco_{v}"] = out; d = pd.DataFrame(out)
    print("LOCO", v, "beta range [%.2f, %.2f]; min p %.3f; any CI above 0: %s; max upper %.2f" % (d.beta10.min(), d.beta10.max(), d.p.min(), bool((d.lo10 > 0).any()), d.hi10.max()), flush=True)
globals()["B"] = B_FULL
# (b) downward exposure by window (wave 1, protocol-v1.0 results)
on = {c: stringency(c).loc[:"2020-09-30"].ge(50).idxmax() for c in C15}; rows = []
for c in C15:
    o = pd.read_parquet(f"/tmp/proj/results/main_{c}.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True); o = o[o.part == "test"]
    rel = (o.target_time.dt.tz_convert(None).dt.normalize() - on[c]).dt.days; w = pd.cut(rel, [-999, -1, 27, 59, 999], labels=["pre", "w0-4", "w5-8", "after w8"])
    for v in ("load", "net"):
        y = o[f"y_{v}"]; e = y.notna()
        for m in ("I1", "I2", "I3"):
            lo = o[f"p_{v}"] - o[f"hw_{m}_{v}_90"]; hi = o[f"p_{v}"] + o[f"hw_{m}_{v}_90"]
            for wn in w.cat.categories:
                k = e & (w == wn); gwh = o.y_load[k].sum() / 1000
                rows.append(dict(country=c, target=v, method=m, window=wn, below=((lo - y).clip(lower=0))[k].sum() / gwh,
                                 above=((y - hi).clip(lower=0))[k].sum() / gwh, share_below=float(((y < lo) & k).sum() / max(((y < lo) | (y > hi))[k].sum(), 1))))
dn = pd.DataFrame(rows).groupby(["target", "method", "window"])[["below", "above", "share_below"]].median().reset_index()
res["down_window"] = dn.to_dict("records"); print(dn[dn.target == "load"].round(3).to_string(index=False), flush=True)
json.dump(res, open(f"{OUTP}/posthoc_loco_down.json", "w"), default=float, indent=1)
