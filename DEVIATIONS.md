# Deviations and implementation clarifications

Each entry: date, type, description, effect on results.

## D1 — 2026-10-23 — Administrative (no effect on analysis)
The files tagged `protocol-v1.0` (commit f722990, 2026-10-23T13:32:32+03:00) were uploaded from the pre-freeze package, so the header and status line of `PROTOCOL.md` (and the title line of `README.md`) still read "draft v0.9 — NOT YET FROZEN". Every other line of the protocol is identical to the intended frozen version. A follow-up commit corrects only these lines. **The analysis plan contained in the tagged commit is the binding protocol.** Effect on results: none.

## C1–C8 — 2026-10-23 — Implementation clarifications (details the protocol did not fix; set before inspecting any 2020 result)
- **C1 (I3 ACI):** one α_t is shared across hours. Scores are the fixed calibration-period |residuals| of the target hour's group. Each error updates α_t once, at the first issuance (D−1 11:00 UTC) after the target hour is observed. Hours with a missing observation give no update.
- **C2 (I3 ACI):** the quantile level 1−α_t is clipped to [0, 1]; at 1 the largest calibration score is used.
- **C3 (I3 ACI):** γ is tuned separately per country and target at 90% and reused for 80% and 95%. Note for reporting: the selected γ was the smallest grid value (0.001) for most country–target pairs.
- **C4 (stringency):** OxCGRT gaps are forward-filled; days before the first OxCGRT record are set to 0.
- **C5 (ridge, departure):** hour-of-day interactions were applied to all ten lag/last/mean24 features (the protocol names "lag and last-value features", i.e. eight). Hour-of-day and weekday indicators were also added to the design. Effect: the model is slightly richer than specified; no result was inspected before this choice.
- **C6 (net load):** the net-load point forecast uses the zero-clipped solar forecast.
- **C7 (bootstrap):** when no bootstrap statistic exceeds the observed one, p is reported as < 1/9,999.
- **C8 (recovery):** "returns and stays for 14 days" is implemented as: the first day on or after onset such that the 14-day rolling coverage is within ±2.5 pp of nominal on that day and on each of the next 13 days.
