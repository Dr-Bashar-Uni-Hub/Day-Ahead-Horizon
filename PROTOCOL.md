# Study Protocol (pre-registration, version 1.0 — FROZEN)

**Working title:** Does lockdown intensity break forecast calibration? Cross-country evidence on prediction-interval reliability for load, solar generation and net load during the 2020 shift

**Author:** Bashar ALHAJAHMAD (sole author)
**Status:** Frozen. Binding from the timestamp of the `protocol-v1.0` tag in https://github.com/Dr-Bashar-Uni-Hub/Day-Ahead-Horizon. No forecast metric for the 2020 test period was computed before that tag.

---

## 1. Background and relation to prior work

Prediction intervals for load and renewable generation are increasingly produced with conformal methods, including adaptive conformal inference (ACI). Their coverage guarantee assumes exchangeability, which a structural shift such as the 2020 COVID-19 restrictions violates. Separate literatures have (a) applied conformal and adaptive conformal methods to load or solar forecasting and (b) linked COVID-19 policy stringency to electricity consumption. This study connects the two. It asks whether the *reliability of uncertainty estimates* degrades in proportion to policy intensity across countries, and which recalibration strategies repair it.

**Relation to the author's related manuscript.** A separate manuscript by the same author, currently under review at the *International Journal of Green Energy*, evaluates **point** forecasters (LSTM, Transformers, PatchTST, DLinear) for German and Austrian load and solar at direct 1/6/24-hour horizons, with input-degradation and fallback analyses. The present study differs in its output (prediction intervals), forecast setting (day-ahead issuance), research questions (calibration under shift, dose–response, net load), and country set (15 systems). It will cite that manuscript and will reuse none of its results.

**Novelty check.** Before the manuscript is written, a documented literature search (databases, query strings, dates, inclusion criteria) will be run. It will verify that no prior study relates prediction-interval calibration of load, solar or net load forecasts to policy stringency across countries. Novelty statements will be qualified by that search.

## 2. Research questions and pre-specified hypotheses

| ID | Question | Prediction |
|---|---|---|
| RQ1 | Does daily miscoverage of statically calibrated intervals rise with OxCGRT stringency, after controlling for country, weekday and season? | H1a: β > 0 for load. H1b: β > 0 for net load. H1c (**negative control**): solar β is not distinguishable from 0 and is smaller than the load β. H1d (**placebo year**): the 2019 pseudo-treatment β is not distinguishable from 0. |
| RQ2 | Which recalibration strategy restores nominal coverage fastest after onset, and at what width cost? | H2: rolling-window conformal and ACI recover faster than static conformal, at the cost of wider intervals during the transition. No ordering between rolling and ACI is predicted. |
| RQ3 | For net load, does direct calibration outperform combining component intervals? Does load–solar error dependence change under the shift? | H3: direct calibration attains nominal coverage with narrower intervals than component combination. No directional prediction for the dependence change. |
| RQ4 | What is the operational cost of miscoverage? | Descriptive; no hypothesis. |

## 3. Data

- **Electricity data:** Open Power System Data, *Data Package Time Series*, version 2020-10-06, hourly, `time_series_60min_singleindex.csv`, SHA-256 prefix `6a7f2bc571314cbf`. Series: `{CC}_load_actual_entsoe_transparency`, `{CC}_solar_generation_actual`. Window: 2015-01-01 00:00 to 2020-09-30 23:00 UTC.
- **Policy data:** OxCGRT `OxCGRT_compact_national_v1.csv` (SHA-256 prefix `fa5c95fa8f5e3865`), variable `StringencyIndex_Average`, national totals (`Jurisdiction == NAT_TOTAL`).
- **Country inclusion rule (applied mechanically):** national code; both series present; missing fraction ≤ 1% for each series over the window; mean solar ≥ 1% of mean load; OxCGRT national data available. Result: **15 countries**: AT, BE, BG, CH, CZ, DE, DK, ES, FR, GB (GB_GBN), GR, PT, RO, SI, SK. The audit is in `audit/01_country_inclusion.csv`.
- **Net load:** load − solar, defined only where both are observed.
- **Cleaning:** no outlier removal and no target imputation. Feature series only are forward-filled for gaps ≤ 3 h. Rows with remaining missing features or missing targets are excluded from fitting and evaluation, and the counts are reported (`audit/01_split_counts.csv`).

## 4. Forecast setting

- **Day-ahead issuance:** forecasts are issued at 11:00 UTC on day D−1 for the 24 hours of day D (UTC), a lead time of 13–36 h. The information set contains observations up to the 10:00–11:00 UTC hour of D−1.
- **Features (per target hour, for both load and solar inputs):** values at lags 48, 72 and 168 h; the last observed value; the mean of the last 24 available hours; hour, weekday and day-of-year (cyclical); national holiday indicators for D and D−1 (Python `holidays` package). No weather inputs.
- **Splits by target date:** train 2015-01-15 to 2018-12-31; calibration 2019; test 2020-01-01 to 2020-09-30.

## 5. Point and quantile models

The models are deliberately simple. The study concerns calibration, not architecture.

- **M0 Seasonal naive:** the value at lag 168 h.
- **M1 Ridge (primary point model):** the features above plus hour-of-day interactions with the lag and last-value features; one model per target and country. The penalty is chosen from a log grid of 15 values (10⁻⁴ to 10³) by calibration-period RMSE; the final model is fitted on the training period only. It is deterministic.
- **M2 LightGBM (secondary):** point (L2) and quantile objectives, early stopping on the calibration period, fixed hyperparameters (learning rate 0.05, 63 leaves, subsample 0.8, colsample 0.8), seed 1. A sensitivity analysis uses seeds 1, 7, 21.

## 6. Interval methods (nominal coverage 80%, 90% and 95%; 90% is primary)

- **I1 Static split conformal:** absolute residuals of M1 on the calibration period, grouped by hour of day (24 groups). Each group uses the finite-sample quantile ⌈(n+1)(1−α)⌉/n. Intervals are symmetric. Solar lower bounds are clipped at 0.
- **I2 Rolling conformal:** as I1, using the most recent 28 days of residuals that are available at issuance (delayed feedback respected).
- **I3 ACI (Gibbs & Candès):** α_{t+1} = α_t + γ(α − err_t), with each error used only once it is revealed at an issuance time. γ is selected from {0.001, 0.005, 0.01, 0.05} by 90% interval score on July–December 2019, with January–June 2019 as the initial calibration set.
- **I4 CQR:** M2 quantile models at α/2 and 1−α/2, conformalized on the calibration period.
- **I5 Raw quantile regression:** M2 quantiles, uncalibrated.
- **Net load (RQ3):** N1 *direct*: point forecast ŷ_load − ŷ_solar, calibrated as I1–I3 on net-load residuals. N2 *component combination*: [L_load − U_solar, U_load − L_solar].
- **Solar daylight mask:** an hour is evaluated if the calibration-period mean solar for that country × month × hour is ≥ 1% of the country's calibration-period maximum. The mask is fixed before any test data are used.

## 7. Outcomes and metrics

- **Primary outcome:** the country-day miscoverage rate at 90%, i.e. the fraction of evaluated hours on day d with the observation outside the I1 interval.
- **Secondary:** empirical coverage, mean width, interval (Winkler) score, pinball loss (I4/I5), coverage by hour of day, recovery time.
- **Recovery time:** days from each country's onset (first day with stringency ≥ 50) until the 14-day rolling coverage first returns within ±2.5 percentage points of nominal and stays there for 14 days. If it does not happen by 30 September 2020, the result is reported as censored.
- **Operational (RQ4):** shortfall energy Σ max(0, y − U) and excess headroom Σ max(0, U − y), at the 90% and 95% upper bounds, normalized per GWh of load.

## 8. Statistical analysis

- **RQ1 (primary):** country-day panel regression over the 2020 test period, run separately for load, solar and net load:
  miscov_{c,d} = β·Stringency_{c,d} + country FE + weekday FE + f(day-of-year) + ε.
  Specification A uses f = first-order Fourier terms. Specification B (stricter) adds calendar-month fixed effects, so that identification comes from cross-country differences within a month. Inference uses a wild cluster bootstrap by country (15 clusters, Webb weights, 9,999 replications), reporting two-sided p-values and 95% confidence intervals. α = 0.05; no multiplicity adjustment is made for the three targets, because H1c is a negative control and is not counted as a test of the main claim.
- **Placebo year (H1d):** the full pipeline is rerun with train 2015-01-15 to 2017-12-31, calibration 2018 and test January–September 2019. Each country's 2020 stringency series is assigned to the same calendar dates of 2019, and the same model is estimated.
- **Event study:** mean miscoverage by days relative to onset (−28 to +90), pooled across countries with country-specific pre-onset baselines.
- **RQ2–RQ4:** descriptive, with country-level paired comparisons between methods (Wilcoxon signed-rank tests over 15 countries) reported alongside effect sizes.
- **Interpretation rule:** a "dose–response" claim requires H1a, H1c and H1d all to hold under Specification A. If H1c or H1d fails, the result is reported as a shift-associated calibration loss that is not specific to policy.

## 9. Robustness and sensitivity (pre-specified)

- LightGBM (M2) instead of ridge as the point model for I1–I3.
- Nominal levels of 80% and 95%.
- An alternative onset threshold of stringency ≥ 40.
- Excluding each country in turn (leave-one-country-out β).

## 10. Deviations and post hoc analyses

The only permitted changes after the freeze are bug fixes. Each one is logged in `DEVIATIONS.md` with the date, the reason and its effect on results. Any analysis not listed in this protocol is labelled **post hoc** in the manuscript and the supplement.

## 11. Known limitations (declared in advance)

- The data end in September 2020, so there is no second wave.
- With 15 clusters, cross-country inference is modest.
- Stringency partly coincides with season; the placebo year and Specification B address this.
- There are no weather inputs.
- A single data source (OPSD / ENTSO-E) is used.
- Results describe associations; stringency is not randomly assigned.

## 12. Reproducibility

All code is in `src/`, run in numbered order. Every random seed is fixed. Input data are verified by SHA-256 before use. The derived datasets are regenerated from public sources and are not redistributed.
