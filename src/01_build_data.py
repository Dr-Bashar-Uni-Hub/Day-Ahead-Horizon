"""Step 01 - country inclusion, day-ahead feature construction, chronological splits.
Computes NO forecast metrics and NO statistics of 2020 targets beyond row counts."""
import re, json, hashlib, numpy as np, pandas as pd, holidays
OPSD = "/mnt/user-data/uploads/time_series_60min_singleindex.csv"
OX   = "/tmp/proj/data/OxCGRT_compact_national_v1.csv"
OUT  = "/tmp/proj/data"; AUD = "/tmp/proj/audit"
START, END = pd.Timestamp("2015-01-01", tz="UTC"), pd.Timestamp("2020-09-30 23:00", tz="UTC")
MAX_MISSING_FRAC, MIN_SOLAR_SHARE = 0.01, 0.01        # pre-specified inclusion rule
ISSUE_HOUR = 11                                       # forecasts issued D-1 11:00 UTC
LAST_INFO_HOUR = 10                                   # last complete hour available at issuance
FFILL_LIMIT = 3                                       # feature-only gap filling (hours); targets never filled
SPLITS = {"train": ("2015-01-15", "2018-12-31"), "cal": ("2019-01-01", "2019-12-31"), "test": ("2020-01-01", "2020-09-30")}
ISO3 = {"AT":"AUT","BE":"BEL","BG":"BGR","CH":"CHE","CZ":"CZE","DE":"DEU","DK":"DNK","EE":"EST","ES":"ESP","FI":"FIN",
        "FR":"FRA","GB_GBN":"GBR","GR":"GRC","HU":"HUN","IE":"IRL","IT":"ITA","LT":"LTU","LV":"LVA","NL":"NLD","NO":"NOR",
        "PL":"POL","PT":"PRT","RO":"ROU","SE":"SWE","SI":"SVN","SK":"SVK","HR":"HRV","LU":"LUX","RS":"SRB","ME":"MNE","CY":"CYP"}
HOL = {"GB_GBN": "GB"}

raw = pd.read_csv(OPSD, parse_dates=["utc_timestamp"], low_memory=False)
raw = raw[(raw.utc_timestamp >= START) & (raw.utc_timestamp <= END)].set_index("utc_timestamp")
assert raw.index.is_unique and len(raw) == int((END - START) / pd.Timedelta("1h")) + 1
ox = pd.read_csv(OX, low_memory=False)
ox = ox[ox.Jurisdiction == "NAT_TOTAL"]

# ---------- 1. inclusion audit (national codes only: two letters, or GB_GBN) ----------
cands = sorted({m.group(1) for c in raw.columns if (m := re.match(r"^([A-Z]{2}|GB_GBN)_load_actual_entsoe_transparency$", c))})
rows = []
for c in cands:
    lc, sc = f"{c}_load_actual_entsoe_transparency", f"{c}_solar_generation_actual"
    r = dict(country=c, has_solar=sc in raw)
    r["load_missing_frac"] = raw[lc].isna().mean()
    r["solar_missing_frac"] = raw[sc].isna().mean() if r["has_solar"] else np.nan
    r["solar_share"] = raw[sc].mean() / raw[lc].mean() if r["has_solar"] else np.nan
    r["oxcgrt"] = ISO3.get(c) in set(ox.CountryCode)
    r["included"] = bool(r["has_solar"] and r["load_missing_frac"] <= MAX_MISSING_FRAC and
                         r["solar_missing_frac"] <= MAX_MISSING_FRAC and r["solar_share"] >= MIN_SOLAR_SHARE and r["oxcgrt"])
    rows.append(r)
inc = pd.DataFrame(rows); inc.to_csv(f"{AUD}/01_country_inclusion.csv", index=False)
countries = inc.loc[inc.included, "country"].tolist()
print("Included countries:", len(countries), countries)

# ---------- 2. day-ahead features ----------
def cyc(x, p): return np.sin(2*np.pi*x/p), np.cos(2*np.pi*x/p)
split_rows = []
for c in countries:
    s = pd.DataFrame({"load": raw[f"{c}_load_actual_entsoe_transparency"],
                      "solar": raw[f"{c}_solar_generation_actual"]})
    s["net"] = s.load - s.solar
    f = s[["load", "solar"]].ffill(limit=FFILL_LIMIT)           # features only
    hcal = holidays.country_holidays(HOL.get(c, c), years=range(2014, 2021))
    rec = []
    days = pd.date_range("2015-01-15", "2020-09-30", freq="D", tz="UTC")
    for D in days:
        info_end = D - pd.Timedelta(days=1) + pd.Timedelta(hours=LAST_INFO_HOUR)
        last = f.loc[info_end]; last24 = f.loc[info_end - pd.Timedelta(hours=23): info_end].mean()
        for h in range(24):
            t = D + pd.Timedelta(hours=h); r = {"target_time": t, "hour": h}
            for v in ["load", "solar"]:
                for L in (48, 72, 168):
                    r[f"{v}_lag{L}"] = f[v].get(t - pd.Timedelta(hours=L), np.nan)
                r[f"{v}_last"] = last[v]; r[f"{v}_mean24"] = last24[v]
            for v in ["load", "solar", "net"]: r[f"y_{v}"] = s[v].get(t, np.nan)
            rec.append(r)
    d = pd.DataFrame(rec)
    d["dow"] = d.target_time.dt.dayofweek
    d["hour_sin"], d["hour_cos"] = cyc(d.hour, 24)
    d["dow_sin"], d["dow_cos"] = cyc(d.dow, 7)
    d["doy_sin"], d["doy_cos"] = cyc(d.target_time.dt.dayofyear - 1, 365.25)
    d["holiday"] = d.target_time.dt.date.map(lambda x: x in hcal).astype(int)
    d["holiday_prev"] = (d.target_time - pd.Timedelta(days=1)).dt.date.map(lambda x: x in hcal).astype(int)
    d["split"] = None
    for k, (a, b) in SPLITS.items():
        m = (d.target_time >= pd.Timestamp(a, tz="UTC")) & (d.target_time <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(hours=23))
        d.loc[m, "split"] = k
    feat = [x for x in d.columns if x.endswith(("lag48", "lag72", "lag168", "_last", "_mean24"))]
    d["feat_ok"] = d[feat].notna().all(1)
    d["country"] = c
    d.to_parquet(f"{OUT}/dayahead_{c}.parquet", index=False)
    for k in SPLITS:
        q = d[d.split == k]
        split_rows.append(dict(country=c, split=k, rows=len(q), feat_missing=int((~q.feat_ok).sum()),
                               y_load_missing=int(q.y_load.isna().sum()), y_solar_missing=int(q.y_solar.isna().sum())))
    print(f"  {c}: {len(d)} rows")
pd.DataFrame(split_rows).to_csv(f"{AUD}/01_split_counts.csv", index=False)
json.dump(dict(countries=countries, rule=dict(max_missing=MAX_MISSING_FRAC, min_solar_share=MIN_SOLAR_SHARE),
               issue_hour_utc=ISSUE_HOUR, last_info_hour=LAST_INFO_HOUR, ffill_limit=FFILL_LIMIT, splits=SPLITS),
          open(f"{AUD}/01_config.json", "w"), indent=2)
