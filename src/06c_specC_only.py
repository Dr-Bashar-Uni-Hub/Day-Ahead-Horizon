"""POST HOC (added after an external pre-review): (a) coverage by post-onset window per method,
(b) Spec C with date fixed effects (common temporal shocks), (c) country-permutation inference,
(d) transition-window regression (level vs transition)."""
import numpy as np, pandas as pd, json
exec(open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0])
onset = {c: stringency(c, "main").ge(50).idxmax() for c in COUNTRIES}
out = {}
# (b) Spec C: date FE (identification only from cross-country differences on the same day)
def wc_dateFE(p):
    q = p.copy(); parts = [pd.get_dummies(q.country, dtype=float), pd.get_dummies(q.date.dt.strftime("%Y%m%d"), prefix="d", drop_first=True, dtype=float)]
    Z = pd.concat(parts, axis=1).values
    globals()["fe_matrix"] = lambda pp, spec: Z
    return wild_cluster(q, "C")
for setup in ("main", "placebo"):
    for v in ("load", "net", "solar"):
        r = wc_dateFE(panel(setup, v)); out[f"specC_{setup}_{v}"] = r
        print("SpecC", setup, v, "beta*1000 %.2f CI [%.2f, %.2f] p %.4f" % (1000*r["beta"], 1000*r["ci_lo"], 1000*r["ci_hi"], r["p_wcr"]))
json.dump(out, open(f"{OUT}/posthoc_specC_dateFE.json", "w"), default=float, indent=1)
