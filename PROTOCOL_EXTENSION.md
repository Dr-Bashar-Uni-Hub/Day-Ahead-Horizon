# Extension Protocol: Second-Wave Test of Policy Intensity (pre-registration v1.1)

**Status:** Binding once committed and tagged `protocol-extension-v1.1` in https://github.com/Dr-Bashar-Uni-Hub/Day-Ahead-Horizon. **No electricity data after 30 September 2020 may be downloaded or inspected before this tag exists.**

**Relation to protocol-v1.0.** The main protocol is unchanged. This extension was designed *after* the first-wave results were known. Its hypotheses are therefore informed by those results, which is stated openly; the analysis of the new data, however, is confirmatory. The motivation is that in March 2020 all 15 systems tightened restrictions within about ten days of each other. Analyses that remove this common timing (date fixed effects, permutation of stringency series) could not separate an intensity effect from the timing:
- 15 systems: date-FE p = 0.63 (load) and 0.35 (net load); permutation p = 0.38 and 0.25;
- 13 systems, excluding two series with data errors: date-FE p = 0.15 and 0.06; permutation p = 0.06 and 0.04.

The autumn 2020 – spring 2021 restrictions varied more in timing and intensity across countries, which provides the variation needed for identification.

## 1. Question and hypotheses

Does the miscoverage of day-ahead prediction intervals rise with policy stringency once shocks common to all systems are removed?

| ID | Hypothesis (primary specification E-C, §5) |
|---|---|
| E-H1 (primary) | The stringency coefficient for **load** miscoverage of static 90% intervals is positive. |
| E-H2 | The stringency coefficient for **net load** is positive. |
| E-H3 (negative control) | The stringency coefficient for **solar** is not distinguishable from zero. |

**Interpretation rule (fixed in advance; three possible outcomes, judged on load):**
- **Intensity effect supported:** the 95% CI for the load coefficient lies above 0 and E-H3 holds.
- **Intensity effect rejected (practical null):** the upper bound of the 95% CI is below 0.5 percentage points per 10 stringency points, about one-third of the first-wave Specification A estimate (1.57).
- **Inconclusive:** any other result.

The paper will report the outcome in these words, whichever it is.

## 2. Data

- **Electricity:** Energy-Charts public API of Fraunhofer ISE (endpoint `public_power`, series "Load" and "Solar"; no registration required), downloaded for the 15 systems of protocol-v1.0, covering 1 January 2019 – 1 July 2021. Sub-hourly series are averaged to hourly values in UTC. Energy-Charts compiles its European series largely from ENTSO-E; its "Load" definition may differ from the OPSD/ENTSO-E series, which the consistency check Q0 quantifies. OPSD data (protocol-v1.0) are used up to 30 September 2020; the Energy-Charts download is used from 1 October 2020. Earlier Energy-Charts data are downloaded only for the consistency check in §3. A system whose Energy-Charts series is unavailable, or fails Q0 by more than 5% of mean load, is excluded from the extension, and the reason is reported.
- **Policy:** OxCGRT `StringencyIndex_Average`, national, the same file and SHA-256 as protocol-v1.0.
- **Extension test window:** 1 October 2020 – 30 June 2021. A system whose data end earlier (e.g. Great Britain after Brexit-related reporting changes) is kept for the days available and the coverage is reported.

## 3. Data quality rules (mechanical, applied to all systems before any metric is computed)

- **Q0 consistency:** for January 2019 – September 2020, compare the Energy-Charts download with OPSD. A system is flagged if the median absolute hourly difference exceeds 1% of its mean load (or of mean daylight solar). Flagged systems remain in the analysis, and the flag is reported.
- **Q1 spikes:** any load or solar value above 3 × that system's training-period (2015–2018) 99.9th percentile is set to missing, for targets and features alike.
- **Q2 definition breaks:** a solar series whose maximum in the extension window exceeds 2.5 × its 2019 maximum is excluded from solar and net-load analyses. The load analysis of that system then uses load lags only.
- The number of values removed and the systems excluded under each rule are reported. Results without Q1–Q2 are reported as a sensitivity analysis.

## 4. Forecasting and intervals (unchanged deployment)

The models and calibration of protocol-v1.0 are used **without refitting**: ridge M1 trained on 2015-01-15 – 2018-12-31, conformal scores from 2019, and the ACI step sizes as selected. Static SCP, rolling SCP and ACI are computed exactly as in protocol-v1.0 and its clarifications C1–C8, with features built from the combined series. This represents a forecaster deployed before the pandemic and left in operation. National holidays are taken from the `holidays` package for 2020–2021.

## 5. Statistical analysis

- **Outcome:** country-day miscoverage of static 90% intervals, as in protocol-v1.0 (solar evaluated in daylight hours, using the 2019 daylight mask).
- **E-C (primary):** miscoverage on same-day stringency with **country and date fixed effects**, so that identification comes only from differences between countries on the same day.
- **Inference:** wild cluster bootstrap by country (Webb weights, 9,999 replications); two-sided α = 0.05.
- **Secondary analyses:**
  - (i) E-C plus country-specific linear time trends;
  - (ii) permutation inference reassigning whole national stringency series across countries within the window (4,999 draws, seed 7);
  - (iii) Specification A of protocol-v1.0 on the extension window;
  - (iv) the same analyses pooled over January 2020 – June 2021;
  - (v) a stacked event study of **tightening events**: within-country increases of at least 20 stringency points within 14 days, with windows from −14 to +42 days;
  - (vi) coverage of SCP, rolling SCP and ACI by month.
- **Multiplicity:** E-H1 is the single primary test. All other results are reported with effect sizes and confidence intervals.

## 6. Deviations

Any departure from this extension protocol is logged in `DEVIATIONS.md` (prefix E). Any analysis not listed here is labelled post hoc.

## 7. Known limitations (declared in advance)

- The frozen models will drift further from 2019 conditions. Date and country fixed effects absorb common and level drift, and secondary analysis (i) absorbs linear country-specific drift.
- Vaccination, weather and economic recovery co-vary with stringency over time; date fixed effects remove only their common component.
- With 13–15 clusters, power to detect small effects is limited, which the three-outcome interpretation rule acknowledges.
- The Energy-Charts data may differ from the OPSD processing; §3 Q0 quantifies this, and the 5% rule in §2 excludes systems with large discrepancies.
