# Day-Ahead-Horizon: forecast calibration under pandemic regime shifts (15 European power systems)

Pre-registered study. Read in this order: `PROTOCOL.md` (tag `protocol-v1.0`, commit f722990), `PROTOCOL_EXTENSION.md` (tag `protocol-extension-v1.1`, commit c0f2a76; Energy-Charts revision at 6255311), `DEVIATIONS.md` (all deviations, clarifications and post hoc analyses).

## Inputs (not redistributed)
OPSD Time Series 2020-10-06 (`time_series_60min_singleindex.csv`), OxCGRT `OxCGRT_compact_national_v1.csv`, Energy-Charts `public_power` downloads (`colab_phase3_energycharts_download.py`). SHA-256 prefixes: PROTOCOL.md §3 and `audit/E0_extension_hashes.txt`.

## Scripts (run in order)
| Script | Status | Content |
|---|---|---|
| 01_build_data.py | pre-registered | inclusion rule, day-ahead features, splits |
| 02_ridge_intervals.py | pre-registered | ridge, static/rolling SCP, ACI (main + 2019 placebo) |
| 03_analysis.py | pre-registered | RQ1 panels, wild cluster bootstrap, RQ2–RQ4 |
| 04_lightgbm_sensitivity.py | pre-registered | LightGBM, CQR, raw QR, §9 sensitivity |
| 05_figures.py, 05b_placebo_event_figure.py | figures / post hoc P1 | figures; 2019 event study |
| 06*, 06b, 06c, 06d | post hoc P2–P5 | date FE, permutation, transition windows, coverage by window |
| 07_graphical_abstract.py | figure | graphical abstract |
| 08, 08b | post hoc P7 | first wave without CH and SK |
| E1_extension_pipeline.py | extension (pre-registered) | splice, Q1/Q2, frozen models, intervals 2020-01..2021-06 |
| E2_extension_analysis.py, E2b_perm_net.py | extension (pre-registered §5) | primary E-C, secondary, sensitivity, descriptives |
| 09, 10 | post hoc P8 | harmonized wave 1, directional exposure, CQR by window, LOCO |
| 11, 12 | post hoc P8 | updated-deployment benchmark (audited for leakage, P9) |

Results are in `results/`, logs and audits in `audit/`, the literature search log in `literature/SEARCH_LOG.md`, and the manuscript build scripts in `manuscript_build/`.
