# =====================================================================
# EXTENSION (protocol-extension-v1.1) — DATA DOWNLOAD ONLY (no key needed)
# Source: Energy-Charts public API (Fraunhofer ISE), endpoint public_power.
# Run ONLY AFTER the tag protocol-extension-v1.1 exists on GitHub.
# Computes NO forecast metrics. Normal CPU runtime is enough.
# =====================================================================
import os, time, json, requests
import pandas as pd
from google.colab import drive
drive.mount("/content/drive")
OUT = "/content/drive/MyDrive/Day-Ahead-Horizon_extension"; os.makedirs(OUT, exist_ok=True)

SYSTEMS = ["at", "be", "bg", "ch", "cz", "de", "dk", "es", "fr", "uk", "gr", "pt", "ro", "si", "sk"]  # 'uk' = Great Britain on Energy-Charts (also tries 'gb')
MONTHS = pd.date_range("2019-01-01", "2021-07-01", freq="MS")

def fetch(country, start, end):
    url = "https://api.energy-charts.info/public_power"
    for attempt in range(8):                      # the service is sometimes unavailable: retry with back-off
        try:
            r = requests.get(url, params={"country": country, "start": start, "end": end}, timeout=60)
            if r.status_code == 200: return r.json()
            err = f"HTTP {r.status_code}"
        except Exception as e:
            err = type(e).__name__
        time.sleep(min(10 * (attempt + 1), 60))
    raise RuntimeError(err)

log = []
for cc in SYSTEMS:
    tries = [cc, "gb"] if cc == "uk" else [cc]
    for code in tries:
        frames = []; ok = True; shown = False
        for a, b in zip(MONTHS[:-1], MONTHS[1:]):
            try:
                js = fetch(code, a.strftime("%Y-%m-%d"), (b - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
            except Exception as e:
                log.append(dict(system=code, month=str(a.date()), error=str(e))); print("  FAILED", code, a.date(), e); continue
            if not shown:
                print(code, "keys:", list(js.keys())[:6], "| series:", [p.get("name") for p in js.get("production_types", [])][:25]); shown = True
            t = pd.to_datetime(js["unix_seconds"], unit="s", utc=True)
            d = {p["name"]: p["data"] for p in js.get("production_types", []) if p.get("name") in ("Load", "Solar")}
            if d: frames.append(pd.DataFrame(d, index=t))
        if frames:
            df = pd.concat(frames); df = df[~df.index.duplicated()].sort_index().apply(pd.to_numeric, errors="coerce").resample("1h").mean()
            df.to_csv(f"{OUT}/{cc}_energycharts.csv")
            log.append(dict(system=cc, code=code, first=str(df.index.min()), last=str(df.index.max()), hours=len(df),
                            cols="|".join(df.columns), load_missing=int(df.get("Load", pd.Series(dtype=float)).isna().sum()),
                            solar_missing=int(df.get("Solar", pd.Series(dtype=float)).isna().sum())))
            print(f"{cc}: {df.index.min().date()} -> {df.index.max().date()}  columns={list(df.columns)}  hours={len(df)}"); break
pd.DataFrame(log).to_csv(f"{OUT}/download_log.csv", index=False)
print("\nDone. Saved to", OUT, "— zip that folder and send it back, together with this printed output.")
