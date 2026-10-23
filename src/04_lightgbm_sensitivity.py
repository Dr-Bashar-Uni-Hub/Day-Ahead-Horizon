"""Step 04 - PROTOCOL §5 M2 (LightGBM), §6 I4 (CQR) and I5 (raw QR), §9 sensitivity analyses:
(a) M2 as point model for I1-I3 (seeds 1, 7, 21), (b) RQ1 at 80% and 95%, (c) onset-40 event study."""
import json, sys, numpy as np, pandas as pd, lightgbm as lgb, warnings; warnings.filterwarnings("ignore")
src2 = open("/tmp/proj/src/02_ridge_intervals.py").read().split('if __name__')[0]; exec(src2)
src3 = open("/tmp/proj/src/03_analysis.py").read().split("rq1 = []")[0]; exec(src3)
onset = {c: stringency(c, "main").ge(50).idxmax() for c in COUNTRIES}
onset40 = {c: stringency(c, "main").ge(40).idxmax() for c in COUNTRIES}
R4 = "/tmp/proj/results/lgbm"; os.makedirs(R4, exist_ok=True)
FEAT = LAGF + CAL + ["hour", "dow"]
QUANTS = {80: (0.10, 0.90), 90: (0.05, 0.95), 95: (0.025, 0.975)}
P = dict(n_estimators=5000, learning_rate=0.05, num_leaves=63, subsample=0.8, subsample_freq=1,
         colsample_bytree=0.8, verbose=-1, n_jobs=1)

def fit(Xtr, ytr, Xca, yca, seed, obj="regression", alpha=None):
    kw = dict(P, random_state=seed, objective=obj)
    if alpha is not None: kw["alpha"] = alpha
    m = lgb.LGBMRegressor(**kw).fit(Xtr, ytr, eval_set=[(Xca, yca)], callbacks=[lgb.early_stopping(100, verbose=False)])
    return m

def run_country(c):
    S = SETUPS["main"]
    d = pd.read_parquet(f"{D}/dayahead_{c}.parquet"); d["target_time"] = pd.to_datetime(d.target_time, utc=True)
    d = d[d.feat_ok].copy()
    tr, ca, te = (in_range(d.target_time, *S[k]) for k in ("train", "cal", "test"))
    base = pd.read_parquet(f"{R}/main_{c}.parquet"); base["target_time"] = pd.to_datetime(base.target_time, utc=True)
    out = base[["target_time", "hour", "part", "daylight", "y_load", "y_solar", "y_net", "issue_day"]].copy()
    sel = (ca | te).values
    assert np.array_equal(d.loc[sel, "target_time"].values, out.target_time.values)
    X = d[FEAT].values
    for v in ("load", "solar"):
        ok = d[f"y_{v}"].notna().values
        a = (X[tr.values & ok], d.loc[tr & ok, f"y_{v}"].values, X[ca.values & ok], d.loc[ca & ok, f"y_{v}"].values)
        for seed in (1, 7, 21):
            out[f"p_{v}_s{seed}"] = fit(*a, seed).predict(X[sel])
        for L, (ql, qh) in QUANTS.items():
            out[f"qlo_{v}_{L}"] = fit(*a, 1, "quantile", ql).predict(X[sel])
            out[f"qhi_{v}_{L}"] = fit(*a, 1, "quantile", qh).predict(X[sel])
    out.to_parquet(f"{R4}/main_{c}_raw.parquet", index=False)
    return out

def intervals_from_point(out, seed):
    """I1-I3 with M2 point forecasts (same procedures as step 02)."""
    o = out.copy()
    o["p_load"] = o[f"p_load_s{seed}"]; o["p_solar_clip"] = o[f"p_solar_s{seed}"].clip(lower=0)
    o["p_net"] = o.p_load - o.p_solar_clip
    for v in ("load", "solar", "net"):
        pc = "p_solar_clip" if v == "solar" else f"p_{v}"
        o[f"ar_{v}"] = (o[f"y_{v}"] - o[pc]).abs()
    o["reveal_time"] = (o.target_time + pd.Timedelta(hours=1)).dt.tz_convert(None)
    test_mask = o.part == "test"; cal = o[o.part == "cal"]
    test_days = sorted(o.loc[test_mask, "issue_day"].unique())
    meta = json.load(open(f"{R}/main_meta.json")); gam = {m["country"]: m["aci_gamma"] for m in meta}
    for v in ("load", "solar", "net"):
        for L in (0.80, 0.90, 0.95):
            tag = f"{v}_{int(L*100)}"
            o[f"hw_I1_{tag}"] = o.hour.map(static_halfwidth(cal, f"ar_{v}", L))
            rh = rolling_halfwidth(o, f"ar_{v}", L, test_days); hw2 = np.full(len(o), np.nan)
            for i in np.where(test_mask)[0]: hw2[i] = rh[o.issue_day.iat[i]][o.hour.iat[i]]
            o[f"hw_I2_{tag}"] = hw2
            scal = {h: g[f"ar_{v}"].values for h, g in cal.groupby("hour")}
            st = o.loc[test_mask, ["hour", f"ar_{v}", "issue_day", "reveal_time"]].rename(columns={f"ar_{v}": "absres"})
            col = np.full(len(o), np.nan); col[np.where(test_mask)[0]] = run_aci(scal, st, L, gam[o.attrs["country"]][v])
            o[f"hw_I3_{tag}"] = col
    return o.drop(columns=["reveal_time"])

if __name__ == "__main__":
    step = sys.argv[1]
    if step == "fit":
        for c in COUNTRIES:
            if os.path.exists(f"{R4}/main_{c}_raw.parquet"): print("skip", c); continue
            run_country(c); print("fitted", c, flush=True)
    if step == "intervals":
        for c in COUNTRIES:
            out = pd.read_parquet(f"{R4}/main_{c}_raw.parquet"); out["target_time"] = pd.to_datetime(out.target_time, utc=True)
            for seed in (1, 7, 21):
                out.attrs["country"] = c
                o = intervals_from_point(out, seed); o["part"] = out.part.values
                o.to_parquet(f"{R4}/m2s{seed}_{c}.parquet", index=False)
            print("intervals", c, flush=True)
    if step == "analyse":
        res = []
        # (b) RQ1 at 80/95 with ridge I1 ; (a) RQ1 with M2-based I1 for seeds 1,7,21
        for L in (80, 95):
            for v in ("load", "solar", "net"):
                for setup in ("main", "placebo"):
                    r = wild_cluster(panel(setup, v, "I1", L), "A"); r.update(analysis=f"ridge_I1_{L}", setup=setup, target=v); res.append(r)
                    print(r["analysis"], setup, v, round(r["beta"], 5), round(r["p_wcr"], 4), flush=True)
        for seed in (1, 7, 21):
            R_backup = R; R = R4
            _load = load
            def load(country, setup, seed=seed):
                o = pd.read_parquet(f"{R4}/m2s{seed}_{country}.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True)
                return o[o.part == "test"].copy()
            for v in ("load", "solar", "net"):
                r = wild_cluster(panel("main", v, "I1", 90), "A"); r.update(analysis=f"M2_seed{seed}_I1_90", setup="main", target=v); res.append(r)
                print(r["analysis"], v, round(r["beta"], 5), round(r["p_wcr"], 4), flush=True)
            load = _load; R = R_backup
        pd.DataFrame(res).to_csv(f"{OUT}/sensitivity_rq1.csv", index=False)
        # I4 CQR and I5 raw QR evaluation (load, solar)
        rows = []
        for c in COUNTRIES:
            o = pd.read_parquet(f"{R4}/main_{c}_raw.parquet"); o["target_time"] = pd.to_datetime(o.target_time, utc=True)
            day = o.target_time.dt.tz_convert(None).dt.normalize()
            for v in ("load", "solar"):
                y = o[f"y_{v}"]
                for L in (80, 90, 95):
                    a = 1 - L / 100; lo, hi = o[f"qlo_{v}_{L}"], o[f"qhi_{v}_{L}"]
                    cm = (o.part == "cal") & y.notna()
                    E = np.maximum(lo - y, y - hi)[cm].values
                    Q = cq(E, L / 100)
                    for name, l_, h_ in (("I5_rawQR", lo, hi), ("I4_CQR", lo - Q, hi + Q)):
                        if v == "solar": l_ = l_.clip(lower=0)
                        e = (o.part == "test") & y.notna() & ((o.daylight) if v == "solar" else True)
                        pre = day < onset[c]
                        isc = ((h_ - l_) + 2/a*(l_ - y)*(y < l_) + 2/a*(y - h_)*(y > h_))
                        rows.append(dict(country=c, target=v, method=name, level=L, coverage=((y >= l_) & (y <= h_))[e].mean(),
                                         coverage_pre=((y >= l_) & (y <= h_))[e & pre].mean(), coverage_post=((y >= l_) & (y <= h_))[e & ~pre].mean(),
                                         width=(h_ - l_)[e].mean(), interval_score=isc[e].mean()))
        pd.DataFrame(rows).to_csv(f"{OUT}/i4_i5_quantile_methods.csv", index=False)
        # M2 point accuracy vs ridge vs naive (context)
        acc = []
        for c in COUNTRIES:
            o = pd.read_parquet(f"{R4}/main_{c}_raw.parquet"); b = pd.read_parquet(f"{R}/main_{c}.parquet")
            t = (o.part == "test").values
            for v in ("load", "solar"):
                y = o[f"y_{v}"].values[t]; m = ~np.isnan(y)
                rm = lambda p: float(np.sqrt(np.nanmean((p[m] - y[m]) ** 2)))
                acc.append(dict(country=c, target=v, ridge=rm(b[f"p_{v}" if v == "load" else "p_solar_clip"].values[t]),
                                naive=rm(b[f"naive_{v}"].values[t]),
                                lgbm_s1=rm(o[f"p_{v}_s1"].values[t] if v == "load" else np.clip(o[f"p_{v}_s1"].values[t], 0, None))))
        pd.DataFrame(acc).to_csv(f"{OUT}/point_accuracy_test.csv", index=False)
        # (c) onset-40 event study
        ev = []
        for v in ("load", "solar", "net"):
            p = pd.read_csv(f"{OUT}/panel_main_{v}.csv", parse_dates=["date"])
            p["rel"] = [(d - onset40[c]).days for d, c in zip(p.date, p.country)]
            base = p[p.rel < 0].groupby("country").miscov.mean(); p["vs_pre"] = p.miscov - p.country.map(base)
            e = p[(p.rel >= -28) & (p.rel <= 90)].groupby("rel").vs_pre.mean().reset_index(); e["target"] = v; ev.append(e)
        pd.concat(ev).to_csv(f"{OUT}/event_study_onset40.csv", index=False)
        print("STEP 04 COMPLETE")
