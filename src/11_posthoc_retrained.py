"""POST HOC (P8c): updated-deployment benchmark (see 10_ docstring)."""
import json, sys, numpy as np, pandas as pd
exec(open("/tmp/proj/src/E1_extension_pipeline.py").read().split('if __name__ == "__main__":')[0])
OUTU = "/tmp/proj/results/ext_retrain"; os.makedirs(OUTU, exist_ok=True)
alphas = pd.read_csv("/tmp/proj/results/ext/ext_audit_all.csv").set_index("country")
for c in MAP:
    if os.path.exists(f"{OUTU}/retrain_{c}.parquet"): continue
    s, audit = combined(c, True); d = features(c, s)
    lagf_full = [f"{v}_{k}" for v in ("load", "solar") for k in ("lag48", "lag72", "lag168", "last", "mean24")]
    globals()["LAGF"] = [x for x in lagf_full if not (audit["Q2_solar_excluded"] and x.startswith("solar"))]
    d = d[d[LAGF].notna().all(1)].reset_index(drop=True); X = design(d); t = d.target_time
    months = pd.date_range("2019-01-01", "2021-06-01", freq="MS", tz="UTC"); pred = {v: np.full(len(d), np.nan) for v in ("load", "solar")}
    for M in months:                                       # model for month M uses data with target time < start of M minus 1 day (issuance constraint)
        cut = M - pd.Timedelta(days=1); tr = (t >= pd.Timestamp("2015-01-15", tz="UTC")) & (t < cut); te = (t >= M) & (t < M + pd.offsets.MonthBegin(1))
        for v in ("load", "solar"):
            ok = d[f"y_{v}"].notna().values; a = float(alphas.loc[c, f"alpha_{v}"])
            Xtr = X[tr.values & ok]; mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1; ym = d.loc[tr & ok, f"y_{v}"].mean()
            m = Ridge(alpha=a).fit((Xtr - mu) / sd, d.loc[tr & ok, f"y_{v}"].values - ym)
            pred[v][te.values] = m.predict((X[te.values] - mu) / sd) + ym
    o = d[["target_time", "hour", "y_load", "y_solar", "y_net"]].copy(); o["p_load"] = pred["load"]; o["p_solar_clip"] = np.clip(pred["solar"], 0, None)
    o["p_net"] = o.p_load - o.p_solar_clip; o = o[o.target_time >= pd.Timestamp("2019-01-01", tz="UTC")].reset_index(drop=True)
    cal = o[o.target_time < pd.Timestamp("2020-01-01", tz="UTC")]; mx = cal.y_solar.max(); mm = cal.assign(m=cal.target_time.dt.month).groupby(["m", "hour"]).y_solar.mean()
    o["daylight"] = [mm.get((mm_, h), 0) >= 0.01 * mx for mm_, h in zip(o.target_time.dt.month, o.hour)]
    for v in ("load", "solar", "net"):
        pc = "p_solar_clip" if v == "solar" else f"p_{v}"; ar = (o[f"y_{v}"] - o[pc]).abs(); o[f"hw_U_{v}_90"] = np.nan
        days = pd.date_range("2020-01-01", "2021-06-30", freq="D", tz="UTC"); ser = pd.Series(ar.values, index=o.target_time)
        for D in days:                                     # scores: out-of-sample residuals of preceding 365 days available at issuance
            end = D - pd.Timedelta(days=1) + pd.Timedelta(hours=10); w = ser[(ser.index > end - pd.Timedelta(days=365)) & (ser.index <= end)]
            q = {h: cq(w.values[w.index.hour == h], 0.90) for h in range(24)}
            sel = (o.target_time >= D) & (o.target_time < D + pd.Timedelta(days=1)); o.loc[sel, f"hw_U_{v}_90"] = o.loc[sel, "hour"].map(q).values
    o["part"] = np.where(o.target_time >= pd.Timestamp("2020-01-01", tz="UTC"), "test", "cal")
    o.to_parquet(f"{OUTU}/retrain_{c}.parquet", index=False); print("retrained", c, flush=True)
