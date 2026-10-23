"""POST HOC (P7b): permutation inference on 13 systems (CH, SK excluded), Spec A, 4,999 draws, seed 7."""
import json, numpy as np
exec(open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0])
C13 = [c for c in COUNTRIES if c not in ("CH", "SK")]; rng = np.random.default_rng(7); out = {}
for v in ("load", "net"):
    p = panel("main", v); p = p[p.country.isin(C13)].reset_index(drop=True)
    Z = fe_matrix(p, "A"); P = Z @ np.linalg.pinv(Z); yt = p.miscov.values - P @ p.miscov.values
    S = {c: stringency(c, "main") for c in C13}
    def b(mp):
        s = np.array([S[mp[c]].get(d, 0.0) for c, d in zip(p.country, p.date)]); st = s - P @ s; return st @ yt / (st @ st)
    b0 = b({c: c for c in C13}); dr = [b(dict(zip(C13, rng.permutation(C13)))) for _ in range(4999)]
    out[v] = dict(beta=b0, p_perm=(1 + np.sum(np.abs(dr) >= abs(b0))) / 5000); print(v, out[v], flush=True)
json.dump(out, open(f"{OUT}/posthoc_perm_exclude_CH_SK.json", "w"), default=float, indent=1)
