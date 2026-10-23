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

## V1 — 2026-10-23 — Verification note (no change)
The RQ1 sensitivity estimates using LightGBM (seed 1) as point model were nearly equal to the ridge 80% estimates (e.g. load 0.002502 vs 0.002499). An independent recomputation from the separate result files confirmed that they derive from different intervals (mean daily miscoverage 14.7% vs 25.0% for load). The near-equality is coincidental; no code error was found. No change was made.

## L1 — 2026-10-23 — Limitation noted while executing I4 (as specified)
LightGBM early stopping (§5) and CQR conformalization (§6) both use the calibration year, as the protocol specifies. Reusing the same data makes the CQR calibration mildly optimistic. This is reported as a limitation; the analysis is unchanged.

## P1–P6 — 2026-10-23 — Post hoc analyses (NOT pre-registered; added after results were seen)
Each is labelled post hoc in the manuscript and supplement.
- **P1 (event-study shape, `05b`):** decomposition of load miscoverage by period relative to onset; 2019 placebo-year event study with 2020 onset dates mapped to 2019. Motivation: Fig. 3 showed a transient pattern and a rise in the solar control.
- **P2–P5 (`06`, `06b`, `06c`, `06d`):** added after an external pre-review (a large-language-model "editor" assessment supplied by the author) questioned the dose–response interpretation, common temporal shocks and evidence for ACI during the transition.
  - P2: Specification C with country and date fixed effects (wild cluster bootstrap, Webb weights, 9,999 reps).
  - P3: permutation inference reassigning national stringency series across countries (4,999 draws, seed 7).
  - P4: transition-window model (Spec A plus indicators for weeks 0–4 and 5–8 after onset; CR1 cluster-robust SE).
  - P5: coverage by period (pre-onset, weeks 0–4, weeks 5–8, after week 8) for I1–I3.
- **P6 (consequence):** the manuscript's central claim was revised from a policy dose–response to a common transition shock, with the author's agreement, because P2–P4 showed no evidence that cross-country differences in stringency explain miscoverage. The pre-registered test (RQ1) and its interpretation rule are reported unchanged.
- **Note on files:** the first run of `06` timed out after printing Spec C and the load permutation; these were re-run to files (`06c`, `06d`) and reproduced the printed values.

## P7 — 2026-10-23 — Post hoc sensitivity excluding CH and SK (first wave)
Inspection of the raw OPSD series showed data errors: one SK load value of 2,170,811 MW on 2020-08-08 (typical load ~3,100 MW; nine hours above 10 GW in total), and a break in the CH solar series in 2020 (maximum 1,821 MW against 300–330 MW in 2018–2019; median ~1 MW to 26 MW), which also contaminates CH load forecasts through the lagged solar inputs. Re-running the key analyses on 13 systems (`08`, `08b`) left the pre-registered Spec A result unchanged (load 1.56, p < 0.0001). Analyses removing common timing became borderline: date FE load 1.14 (p = 0.15), net 1.49 (p = 0.06); permutation load p = 0.06, net p = 0.04. Consequence: the claim "not related to policy intensity" was withdrawn as unsupported, with the author's agreement, and the second-wave extension was pre-registered (`PROTOCOL_EXTENSION.md`, tag `protocol-extension-v1.1`).

## E1 — 2026-10-23 — Extension: data source and tagged file version
The ENTSO-E API token could not be obtained without a waiting period, so the data were downloaded from the Energy-Charts public API (Fraunhofer ISE), which compiles ENTSO-E data. A revised protocol naming Energy-Charts was prepared, but the file committed under the tag `protocol-extension-v1.1` (commit c0f2a76, 2026-10-23T17:52:46+03:00) is the earlier version naming the ENTSO-E API. Hypotheses, primary specification, interpretation rule, data-quality rules Q0–Q2 and secondary analyses are identical in both versions. Only the rules in the tagged file were applied as binding. The additional rule of the untagged revision (exclude systems differing from OPSD by more than 5%, i.e. CH and SI, and AT solar) is reported as a sensitivity analysis only. The revised (Energy-Charts) protocol text was committed to the main branch at 6255311 (2026-10-23T17:59:14+03:00), seven minutes after the tag; the tag itself was not moved. The download took place after both commits (archive timestamp 2026-10-23T16:31Z = 19:31+03:00). File hashes are in `audit/E0_extension_hashes.txt`; the Q0 results are in `audit/E1_Q0_consistency.csv`.

## E2 — 2026-10-23 — Extension: empty rolling windows (bug fix)
After Q1 removed CH solar values exceeding three times the training-period 99.9th percentile (1,920 hours), some 28-day rolling windows for CH solar contained no residuals, and the conformal quantile function failed. The function now returns a missing half-width for an empty window. Effect: none for any non-empty window; verified by exact reproduction of the protocol-v1.0 forecasts and intervals for January–September 2020 (maximum absolute difference 0.0).

## E3 — 2026-10-23 — Extension: order of Q1 and Q2
The protocol does not fix the order of Q1 and Q2. Q1 was applied first and Q2 was evaluated on the cleaned series. Result: Q2 excluded the CH solar series, the only definition break found.

## P8 — 2026-10-23 — Further post hoc analyses after a second AI-generated pre-review (ChatGPT, supplied by the author)
- **(a) Harmonized first wave (`09`):** first-wave tests repeated on the series cleaned by extension rules Q1/Q2. Spec A unchanged (load 1.66, p < 0.0001). Date FE: load 0.99 (CI −0.32 to 2.26, p = 0.16; permutation p = 0.08); net load 1.38 (CI 0.06 to 2.71, p = 0.046; permutation p = 0.037).
- **(b) Shortfall/headroom and directional exposure by period (`09`, `10`):** in weeks 0–4 after onset, 88% of static-interval misses fell below the lower bound. This **corrects the v3 statement** that shortfall was concentrated in the transition weeks: shortfall above the upper bound fell, while energy below the lower bound rose.
- **(c) CQR coverage by period (`09`)** and the recovery-time summary. This **corrects the v3 statements** that ACI "came closest" at onset (rolling SCP did) and "recovered fastest" (ACI recovered in more systems but not faster).
- **(d) Second-wave leave-one-country-out (`10`; B = 1,999):** load estimates −0.94 to −0.25, smallest p = 0.25; no CI above zero.
- **(e) Updated-deployment benchmark (`11`, `12`):** monthly expanding-window ridge refit (original penalties); split conformal on out-of-sample residuals of the preceding 365 days. Wave 2 E-C: load −0.86 (CI −2.16 to 0.45); wave 1 date FE: load 0.66 (p = 0.25), net 0.93 (p = 0.15).
- **Consequence (agreed with the author):** title and claim reworded to "more consistent with an initial regime-transition shock than with a persistent stringency–miscoverage relationship"; the wave 2 verdict is reported as inconclusive; the possibility of a wave-1 net-load intensity effect is stated; the v3 errors listed above are corrected.

## P9 — 2026-10-23 — Leakage audit of the updated-deployment benchmark (no change to results)
An automated audit of `11_posthoc_retrained.py` confirmed the following: every monthly model is trained only on target hours before the information cut-off of its first issuance; no lagged input lies after the issuance information time; and conformal score windows end at that time and contain only out-of-sample residuals. Two non-forecast look-aheads are disclosed: (i) the ridge penalties were selected on 2019, as in protocol-v1.0, and 2019 residuals enter the early-2020 score windows; (ii) rule Q2 decided the exclusion of CH solar using the maximum over the whole extension window, a data-cleaning decision not available in real time.
