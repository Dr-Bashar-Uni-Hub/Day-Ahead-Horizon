# Day-Ahead-Horizon: calibration under shift — load, solar and net load (15 European systems)

Pre-registration and code. Read `PROTOCOL.md` first.

Order of execution:
1. `src/01_build_data.py` — country inclusion, day-ahead features, splits (no forecast metrics)

Inputs (not redistributed): OPSD Time Series 2020-10-06 (`time_series_60min_singleindex.csv`)
and OxCGRT `OxCGRT_compact_national_v1.csv`; SHA-256 prefixes are listed in PROTOCOL.md §3.
