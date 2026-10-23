"""POST HOC (P7): sensitivity excluding CH and SK, whose raw ENTSO-E series contain data errors
(SK load spike of 2,170,811 MW on 2020-08-08; CH solar reporting break in 2020: max 1,821 MW vs 300-330 MW in 2018-19)."""
import json, numpy as np, pandas as pd
exec(open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0])
COUNTRIES = [c for c in COUNTRIES if c not in ("CH", "SK")]
onset = {c: stringency(c, "main").ge(50).idxmax() for c in COUNTRIES}
res = {"countries": COUNTRIES}
for setup in ("main", "placebo"):
    for v in ("load", "net", "solar"):
        p = panel(setup, v)
        for spec in ("A", "B"):
            r = wild_cluster(p, spec); res[f"{setup}_{v}_{spec}"] = r
            print(setup, v, spec, "beta*1000 %.2f [%.2f, %.2f] p %.4f" % (1000*r["beta"], 1000*r["ci_lo"], 1000*r["ci_hi"], r["p_wcr"]), flush=True)
        q = p.copy(); Zc = pd.concat([pd.get_dummies(q.country, dtype=float), pd.get_dummies(q.date.dt.strftime("%Y%m%d"), prefix="d", drop_first=True, dtype=float)], axis=1).values
        fe_orig = fe_matrix; globals()["fe_matrix"] = lambda pp, s: Zc
        r = wild_cluster(q, "C"); globals()["fe_matrix"] = fe_orig; res[f"{setup}_{v}_C"] = r
        print(setup, v, "C", "beta*1000 %.2f [%.2f, %.2f] p %.4f" % (1000*r["beta"], 1000*r["ci_lo"], 1000*r["ci_hi"], r["p_wcr"]), flush=True)
# window model + coverage by window
for v in ("load", "net"):
    p = panel("main", v); p["rel"] = [(d - onset[c]).days for d, c in zip(p.date, p.country)]
    p["w04"] = ((p.rel >= 0) & (p.rel <= 27)).astype(float); p["w58"] = ((p.rel >= 28) & (p.rel <= 59)).astype(float)
    Z = fe_matrix(p, "A"); X = np.column_stack([p.stringency, p.w04, p.w58]); P = Z @ np.linalg.pinv(Z)
    Xt = X - P @ X; yt = p.miscov.values - P @ p.miscov.values; b = np.linalg.lstsq(Xt, yt, rcond=None)[0]; e = yt - Xt @ b
    G = [np.where(p.country.values == g)[0] for g in COUNTRIES]; XtX = np.linalg.inv(Xt.T @ Xt)
    meat = sum(np.outer(Xt[ix].T @ e[ix], Xt[ix].T @ e[ix]) for ix in G); se = np.sqrt(np.diag(XtX @ meat @ XtX * len(G) / (len(G) - 1)))
    res[f"window_{v}"] = dict(zip(["stringency", "weeks0_4", "weeks5_8"], zip(b, se)))
    print("window", v, "str*1000 %.2f (%.2f) w04 %.3f (%.3f) w58 %.3f (%.3f)" % (1000*b[0], 1000*se[0], b[1], se[1], b[2], se[2]), flush=True)
rows = []
for c in COUNTRIES:
    o = load(c, "main"); day = o.target_time.dt.tz_convert(None).dt.normalize(); rel = (day - onset[c]).dt.days
    win = pd.cut(rel, [-999, -1, 27, 59, 999], labels=["pre", "w0-4", "w5-8", "after w8"])
    for v in ("load", "net", "solar"):
        e = evalmask(o, v); y = o[f"y_{v}"]
        for m in ("I1", "I2", "I3"):
            lo, hi = bounds(o, v, m, 90); ins = (y >= lo) & (y <= hi)
            rows.append(dict(country=c, target=v, method=m, window="all", coverage=ins[e].mean(), width=(hi - lo)[e].mean()))
            for w in win.cat.categories:
                k = e & (win == w); rows.append(dict(country=c, target=v, method=m, window=w, coverage=ins[k].mean(), width=np.nan))
cw = pd.DataFrame(rows).groupby(["target", "method", "window"])[["coverage", "width"]].mean().reset_index()
res["coverage"] = cw.to_dict("records"); print(cw[cw.window.isin(["all", "w0-4", "w5-8"])].round(3).to_string())
json.dump(res, open(f"{OUT}/posthoc_exclude_CH_SK.json", "w"), default=float, indent=1)
print("DONE")
