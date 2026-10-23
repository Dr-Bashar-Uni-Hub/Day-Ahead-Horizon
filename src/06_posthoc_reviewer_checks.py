"""POST HOC (added after an external pre-review): (a) coverage by post-onset window per method,
(b) Spec C with date fixed effects (common temporal shocks), (c) country-permutation inference,
(d) transition-window regression (level vs transition)."""
import numpy as np, pandas as pd, json
exec(open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0])
onset = {c: stringency(c, "main").ge(50).idxmax() for c in COUNTRIES}
out = {}
# (a) coverage by window
rows = []
for c in COUNTRIES:
    o = load(c, "main"); day = o.target_time.dt.tz_convert(None).dt.normalize(); rel = (day - onset[c]).dt.days
    win = pd.cut(rel, [-999, -1, 27, 59, 999], labels=["pre", "w0-4", "w5-8", "after w8"])
    for v in ("load", "net", "solar"):
        e = evalmask(o, v); y = o[f"y_{v}"]
        for m in ("I1", "I2", "I3"):
            lo, hi = bounds(o, v, m, 90); inside = ((y >= lo) & (y <= hi))
            for w in win.cat.categories:
                k = e & (win == w); rows.append(dict(country=c, target=v, method=m, window=w, coverage=inside[k].mean()))
cw = pd.DataFrame(rows).groupby(["target", "method", "window"]).coverage.agg(["mean", "min"]).round(3)
cw.to_csv(f"{OUT}/posthoc_coverage_by_window.csv"); print(cw.unstack("window")["mean"].loc[["load","net","solar"]])
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
# (c) permutation inference: reassign whole stringency series across countries (Spec A), 4999 draws
src = open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0]; exec(src)   # restore fe_matrix
rng = np.random.default_rng(7)
for v in ("load", "net", "solar"):
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
# (d) transition windows: does the stringency level still matter once onset windows are controlled?
for v in ("load", "net"):
    p = panel("main", v); p["rel"] = [(d - onset[c]).days for d, c in zip(p.date, p.country)]
    p["w04"] = ((p.rel >= 0) & (p.rel <= 27)).astype(float); p["w58"] = ((p.rel >= 28) & (p.rel <= 59)).astype(float)
    Z = fe_matrix(p, "A"); X = np.column_stack([p.stringency, p.w04, p.w58]); P = Z @ np.linalg.pinv(Z)
    Xt = X - P @ X; yt = p.miscov.values - P @ p.miscov.values
    b = np.linalg.lstsq(Xt, yt, rcond=None)[0]; e = yt - Xt @ b
    G = [np.where(p.country.values == g)[0] for g in COUNTRIES]; XtX = np.linalg.inv(Xt.T @ Xt)
    meat = sum(np.outer(Xt[ix].T @ e[ix], Xt[ix].T @ e[ix]) for ix in G); V = XtX @ meat @ XtX * 15 / 14
    se = np.sqrt(np.diag(V)); out[f"window_{v}"] = dict(zip(["stringency", "weeks0_4", "weeks5_8"], zip(b, se)))
    print("Window model", v, "stringency*1000 %.2f (se %.2f) | weeks0-4 %.3f (se %.3f) | weeks5-8 %.3f (se %.3f)" % (1000*b[0], 1000*se[0], b[1], se[1], b[2], se[2]))
json.dump(out, open(f"{OUT}/posthoc_reviewer_checks.json", "w"), default=float, indent=1)
