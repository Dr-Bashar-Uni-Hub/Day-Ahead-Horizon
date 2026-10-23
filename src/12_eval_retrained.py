"""POST HOC (P8c evaluation): updated-deployment intervals (method U) - wave 1 Spec A/C and wave 2 E-C, plus coverage by window."""
import json, sys, numpy as np, pandas as pd
sys.argv = ["x", "none"]; exec(open("/tmp/proj/src/E2_extension_analysis.py").read().split('if __name__ == "__main__":')[0])
audit = pd.read_csv(f"{R}/ext_audit_all.csv"); excl = tuple(audit.loc[audit.Q2_solar_excluded, "country"]); res = {}
T = "../ext_retrain/retrain"
for v in ("load", "net", "solar"):
    p1 = panel(T, v, C15, "2020-01-01", "2020-09-30", method="U", excl_solar=excl); p2 = panel(T, v, C15, "2020-10-01", "2021-06-30", method="U", excl_solar=excl)
    res[f"U_w1A_{v}"] = wild(p1, "A"); res[f"U_w1C_{v}"] = wild(p1, "C"); res[f"U_w2C_{v}"] = wild(p2, "C")
    print(v, "wave1 A", {k: round(res[f'U_w1A_{v}'][k], 3) for k in ('beta10','lo10','hi10','p')}, "| wave1 C", {k: round(res[f'U_w1C_{v}'][k], 3) for k in ('beta10','lo10','hi10','p')},
          "| wave2 E-C", {k: round(res[f'U_w2C_{v}'][k], 3) for k in ('beta10','lo10','hi10','p')}, flush=True)
on = {c: stringency(c).loc[:"2020-09-30"].ge(50).idxmax() for c in C15}; rows = []
for c in C15:
    o = pd.read_parquet(f"/tmp/proj/results/ext_retrain/retrain_{c}.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True); o = o[o.part == "test"]
    rel = (o.target_time.dt.tz_convert(None).dt.normalize() - on[c]).dt.days
    w = pd.cut(rel, [-999, -1, 27, 59, 200, 9999], labels=["pre", "w0-4", "w5-8", "Jun-Sep 2020", "wave 2"])
    for v in ("load", "net"):
        y = o[f"y_{v}"]; hw = o[f"hw_U_{v}_90"]; ins = (y >= o[f"p_{v}"] - hw) & (y <= o[f"p_{v}"] + hw); e = y.notna() & hw.notna()
        for wn in w.cat.categories: rows.append(dict(country=c, target=v, window=wn, coverage=ins[e & (w == wn)].mean(), width=(2 * hw)[e & (w == wn)].mean()))
cw = pd.DataFrame(rows).groupby(["target", "window"])[["coverage", "width"]].mean().reset_index(); res["U_cov"] = cw.to_dict("records"); print(cw.round(3).to_string(index=False))
json.dump(res, open("/tmp/proj/results/analysis/posthoc_retrained.json", "w"), default=float, indent=1)
