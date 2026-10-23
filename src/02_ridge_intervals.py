"""Step 02 - M0/M1 point forecasts and interval methods I1-I3, N1-N2 (PROTOCOL §5-6).
Setups: 'main' (train 2015-01-15..2018, cal 2019, test 2020-01..09) and
        'placebo' (train 2015-01-15..2017, cal 2018, test 2019-01..09) (PROTOCOL §8)."""
import json, sys, numpy as np, pandas as pd
from sklearn.linear_model import Ridge
D = "/tmp/proj/data"; R = "/tmp/proj/results"
import os; os.makedirs(R, exist_ok=True)
COUNTRIES = json.load(open("/tmp/proj/audit/01_config.json"))["countries"]
LEVELS = [0.80, 0.90, 0.95]
GAMMAS = [0.001, 0.005, 0.01, 0.05]
SETUPS = {"main":    dict(train=("2015-01-15", "2018-12-31"), cal=("2019-01-01", "2019-12-31"), test=("2020-01-01", "2020-09-30")),
          "placebo": dict(train=("2015-01-15", "2017-12-31"), cal=("2018-01-01", "2018-12-31"), test=("2019-01-01", "2019-09-30"))}
LAGF = [f"{v}_{k}" for v in ("load", "solar") for k in ("lag48", "lag72", "lag168", "last", "mean24")]
CAL = ["hour_sin", "hour_cos", "dow_sin", "dow_cos", "doy_sin", "doy_cos", "holiday", "holiday_prev"]

def in_range(t, a, b):
    return (t >= pd.Timestamp(a, tz="UTC")) & (t <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(hours=23))

def design(d):
    H = np.eye(24)[d.hour.values]
    X = d[LAGF + CAL].values
    inter = np.concatenate([H * d[[c]].values for c in LAGF], 1)
    dow = np.eye(7)[d.dow.values]
    return np.concatenate([X, H, dow, inter], 1)

def fit_ridge(Xtr, ytr, Xcal, ycal):
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1
    Z = lambda X: (X - mu) / sd
    ym = ytr.mean(); best = None
    for a in np.logspace(-4, 3, 15):
        m = Ridge(alpha=a).fit(Z(Xtr), ytr - ym)
        r = np.sqrt(np.mean((m.predict(Z(Xcal)) + ym - ycal) ** 2))
        if best is None or r < best[0]: best = (r, a, m)
    _, a, m = best
    return (lambda X: m.predict(Z(X)) + ym), a

def cq(scores, level):
    """finite-sample split-conformal quantile ceil((n+1)level)/n"""
    s = np.sort(scores[~np.isnan(scores)]); n = len(s)
    k = int(np.ceil((n + 1) * level)) - 1
    return s[min(max(k, 0), n - 1)]

def qlevel(scores, q):
    s = np.sort(scores[~np.isnan(scores)]); n = len(s)
    q = min(max(q, 0.0), 1.0)                     # clarification C2: clip to [0,1]
    return s[min(int(np.ceil(q * (n + 1))) - 1 if q > 0 else 0, n - 1)]

def static_halfwidth(cal_df, col, level):
    return {h: cq(g[col].values, level) for h, g in cal_df.groupby("hour")}

def rolling_halfwidth(full, col, level, test_days):
    """I2: last 28 days of |residuals| available at issuance (target time <= D-1 10:00 UTC), by hour."""
    s = full.set_index("target_time")[col]
    out = {}
    for D in test_days:
        end = D - pd.Timedelta(days=1) + pd.Timedelta(hours=10)
        w = s[(s.index > end - pd.Timedelta(days=28)) & (s.index <= end)]
        hrs = w.index.hour
        out[D] = {h: cq(w.values[hrs == h], level) for h in range(24)}
    return out

def run_aci(scores_by_hour, err_stream, level, gamma):
    """I3 (Gibbs & Candes): one alpha shared across hours, scores = fixed calibration |residuals| by hour.
    err_stream: DataFrame sorted by target_time with columns hour, absres, issue_day, reveal_time.
    Errors update alpha only once revealed at an issuance (clarification C1)."""
    alpha_t = 1 - level; target_a = 1 - level
    days = sorted(err_stream.issue_day.unique())
    pending = []; hw = np.empty(len(err_stream)); idx = 0
    revealed_ptr = 0
    es = err_stream.reset_index(drop=True)
    rows_by_day = {d: g for d, g in es.groupby("issue_day", sort=True)}
    order_reveal = es.sort_values("reveal_time").index.values
    reveal_times = es.reveal_time.values[order_reveal]
    halfwidth = np.full(len(es), np.nan); covered_known = {}
    for D in days:
        issue_time = np.datetime64((D - pd.Timedelta(days=1) + pd.Timedelta(hours=11)).tz_convert(None))
        while revealed_ptr < len(order_reveal) and reveal_times[revealed_ptr] <= issue_time:
            j = order_reveal[revealed_ptr]
            if not np.isnan(halfwidth[j]) and not np.isnan(es.absres.values[j]):   # missing targets give no feedback
                err = float(es.absres.values[j] > halfwidth[j])
                alpha_t = alpha_t + gamma * (target_a - err)
            revealed_ptr += 1
        g = rows_by_day[D]
        for j, h in zip(g.index, g.hour.values):
            halfwidth[j] = qlevel(scores_by_hour[h], 1 - alpha_t)
    return halfwidth

def interval_score(y, lo, hi, a):
    return (hi - lo) + (2 / a) * (lo - y) * (y < lo) + (2 / a) * (y - hi) * (y > hi)

def process(country, setup):
    S = SETUPS[setup]
    d = pd.read_parquet(f"{D}/dayahead_{country}.parquet")
    d["target_time"] = pd.to_datetime(d.target_time, utc=True)
    d = d[d.feat_ok].copy()
    tr, ca, te = (in_range(d.target_time, *S[k]) for k in ("train", "cal", "test"))
    X = design(d)
    out = d.loc[ca | te, ["target_time", "hour", "y_load", "y_solar", "y_net"]].copy()
    out["part"] = np.where(ca[ca | te], "cal", "test")
    alphas = {}
    for v in ("load", "solar"):
        ok = d[f"y_{v}"].notna().values
        f, a = fit_ridge(X[tr.values & ok], d.loc[tr & ok, f"y_{v}"].values, X[ca.values & ok], d.loc[ca & ok, f"y_{v}"].values)
        out[f"p_{v}"] = f(X[(ca | te).values]); alphas[v] = a
        out[f"naive_{v}"] = d.loc[ca | te, f"{v}_lag168"].values
    out["p_solar_clip"] = out.p_solar.clip(lower=0)
    out["p_net"] = out.p_load - out.p_solar_clip
    # daylight mask from calibration year only
    c = out[out.part == "cal"]; mx = c.y_solar.max()
    mm = c.assign(m=c.target_time.dt.month).groupby(["m", "hour"]).y_solar.mean()
    out["daylight"] = [mm.get((m, h), 0) >= 0.01 * mx for m, h in zip(out.target_time.dt.month, out.hour)]
    for v in ("load", "solar", "net"):
        pc = "p_solar_clip" if v == "solar" else f"p_{v}"
        out[f"ar_{v}"] = (out[f"y_{v}"] - out[pc]).abs()
    out["issue_day"] = out.target_time.dt.floor("D")
    out["reveal_time"] = (out.target_time + pd.Timedelta(hours=1)).dt.tz_convert(None)
    test_days = sorted(out.loc[out.part == "test", "issue_day"].unique())
    cal = out[out.part == "cal"]; test_mask = out.part == "test"
    gam = {}
    for v in ("load", "solar", "net"):
        pc = "p_solar_clip" if v == "solar" else f"p_{v}"
        for L in sorted(LEVELS, key=lambda x: x != 0.90):   # 90% first: gamma is tuned at 90%
            tag = f"{v}_{int(L*100)}"
            # I1 static
            sh = static_halfwidth(cal, f"ar_{v}", L)
            out[f"hw_I1_{tag}"] = out.hour.map(sh)
            # I2 rolling (test days only)
            rh = rolling_halfwidth(out, f"ar_{v}", L, test_days)
            hw2 = np.full(len(out), np.nan)
            ti = np.where(test_mask)[0]
            for i in ti:
                hw2[i] = rh[out.issue_day.iat[i]][out.hour.iat[i]]
            out[f"hw_I2_{tag}"] = hw2
            # I3 ACI: gamma tuned on Jul-Dec of cal year with Jan-Jun as initial calibration (90% only, reused for all levels)
            if L == 0.90:
                yr = cal.target_time.dt.year.iloc[0]
                h1 = cal[cal.target_time < pd.Timestamp(f"{yr}-07-01", tz="UTC")]
                h2 = cal[cal.target_time >= pd.Timestamp(f"{yr}-07-01", tz="UTC")].dropna(subset=[f"ar_{v}"])
                sc1 = {h: g[f"ar_{v}"].values for h, g in h1.groupby("hour")}
                ev = h2 if v != "solar" else h2[h2.daylight]
                best = None
                for gmm in GAMMAS:
                    hw = run_aci(sc1, h2[["hour", f"ar_{v}", "issue_day", "reveal_time"]].rename(columns={f"ar_{v}": "absres"}), 0.90, gmm)
                    s = pd.Series(hw, index=h2.index).loc[ev.index]
                    y = ev[f"y_{v}"].values; p = ev[pc].values
                    lo = p - s.values; lo = np.maximum(lo, 0) if v == "solar" else lo
                    isc = np.nanmean(interval_score(y, lo, p + s.values, 0.10))
                    if best is None or isc < best[0]: best = (isc, gmm)
                gam[v] = best[1]
            scal = {h: g[f"ar_{v}"].values for h, g in cal.groupby("hour")}
            stream = out.loc[test_mask, ["hour", f"ar_{v}", "issue_day", "reveal_time"]].rename(columns={f"ar_{v}": "absres"})
            stream = stream.fillna({"absres": np.nan})
            hw3 = run_aci(scal, stream, L, gam[v])
            col = np.full(len(out), np.nan); col[np.where(test_mask)[0]] = hw3
            out[f"hw_I3_{tag}"] = col
    out.attrs = {}
    meta = dict(country=country, setup=setup, ridge_alpha=alphas, aci_gamma=gam)
    out.drop(columns=["reveal_time"]).to_parquet(f"{R}/{setup}_{country}.parquet", index=False)
    return meta

if __name__ == "__main__":
    setup = sys.argv[1]
    metas = []
    for c in COUNTRIES:
        metas.append(process(c, setup)); print(setup, c, metas[-1], flush=True)
    json.dump(metas, open(f"{R}/{setup}_meta.json", "w"), indent=1, default=float)
