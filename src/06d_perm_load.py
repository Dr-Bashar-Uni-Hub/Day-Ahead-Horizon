"""POST HOC (added after an external pre-review): (a) coverage by post-onset window per method,
(b) Spec C with date fixed effects (common temporal shocks), (c) country-permutation inference,
(d) transition-window regression (level vs transition)."""
import numpy as np, pandas as pd, json
exec(open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0])
onset = {c: stringency(c, "main").ge(50).idxmax() for c in COUNTRIES}
out = {}
# (c) permutation inference: reassign whole stringency series across countries (Spec A), 4999 draws
src = open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0]; exec(src)   # restore fe_matrix
rng = np.random.default_rng(7)
for v in ("load",):
    p = panel("main", v); Z = fe_matrix(p, "A"); P = Z @ np.linalg.pinv(Z)
    yt = p.miscov.values - P @ p.miscov.values
    S = {c: stringency(c, "main") for c in COUNTRIES}
    def beta_for(mapping):
        s = np.array([S[mapping[c]].get(d, 0.0) for c, d in zip(p.country, p.date)]); st = s - P @ s
        return st @ yt / (st @ st)
    b0 = beta_for({c: c for c in COUNTRIES}); draws = []
    for _ in range(4999):
        perm = rng.permutation(COUNTRIES); draws.append(beta_for(dict(zip(COUNTRIES, perm))))
    pv = (1 + np.sum(np.abs(draws) >= abs(b0))) / 5000
    out[f"perm_{v}"] = dict(beta=b0, p_perm=pv); print("Permutation", v, "beta*1000 %.2f p_perm %.4f" % (1000*b0, pv))
json.dump(out, open(f"{OUT}/posthoc_perm_load_rerun.json", "w"), default=float, indent=1)
