# Documented literature search (novelty check, PROTOCOL §1)

Search engine: web search (general web, incl. arXiv, publisher sites, Google-Scholar-indexed repositories). Date: 2026-10-23.

| # | Query | Purpose | Relevant hits (verified) |
|---|---|---|---|
| 1 | conformal prediction load forecasting distribution shift COVID-19 coverage | conformal + COVID shift | Lee (2026), arXiv 2601.00908 — COVID-19 as a natural experiment for conformal coverage loss in 8 *supply-chain* tasks (not energy). Gibbs & Candès line (JMLR 25, DtACI) uses COVID case counts. |
| 2 | adaptive conformal inference probabilistic load forecasting electricity prediction intervals | ACI in energy | ACI applied to regional load (Mamba-ACI, Knowledge-Based Systems 2025); hour-ahead PV ACI (Sci. Rep. 2026; Energies 19(6):1495); Zaffran et al. ICML 2022 (French prices). Single-system method papers. |
| 3 | net load probabilistic forecast load minus solar joint prediction intervals conformal dependence | net-load intervals | Microgrid stepwise CQR (Energies 19(10):2297); LV-network conformal MLP (SmartGridComm 2024); Browell & Fasiolo (2021) regional net load. None national-scale cross-country under shift. |
| 4 | COVID-19 lockdown stringency index electricity load forecast error European countries cross-country | stringency–electricity link | Stringency vs consumption in 23 EU countries (panel); Werth et al. (2021) 16 countries; Obst et al. (2021) adaptive point forecasting France. These study consumption *levels* or point accuracy, not interval calibration. |
| 5 | prediction interval coverage stringency index electricity forecasting conformal countries | direct novelty check | No study relating interval calibration to policy stringency found. |
| 6 | probabilistic day-ahead load forecasting during COVID-19 lockdown prediction intervals quantile | closest prior work | **de Vilmarest, Browell, Fasiolo, Goude & Wintenberger (2024), IEEE TPWRS 39(2):4154–4163, doi:10.1109/TPWRS.2023.3310280** — adaptive (Kalman + online quantile regression) probabilistic net-load/load forecasting, GB regions and 7 US cities incl. COVID period; full text read. IEEE DataPort post-COVID day-ahead competition entries (point/quantile). |

## Conclusion of the novelty check
Prior work shows (i) conformal/adaptive intervals for single energy systems, (ii) adaptive probabilistic load forecasting through COVID (de Vilmarest et al. 2024), and (iii) stringency effects on consumption levels. No retrieved study tests whether **interval miscoverage scales with policy stringency across countries**, uses **solar as a negative control** and a **placebo year**, or compares **direct vs component-combined net-load intervals** at national scale under the shift. Novelty statements in the manuscript will be phrased "to our knowledge, based on a documented search".

## Limitations of the search
General web search, not a systematic database search (Scopus/WoS not accessible from this environment). Recommendation for the author: repeat queries 5 and 6 in Scopus before submission and append results here.

## Round 2 — reference verification and literature expansion (2026-10-23)
Each reference in the manuscript was checked against a publisher page, repository record, DOI landing page or bibliographic index. Queries (general web search):
- OxCGRT Hale 2021 Nature Human Behaviour; Wiese 2019 OPSD Applied Energy; Gibbs & Candès NeurIPS 2021; Romano et al. CQR NeurIPS 2019; Webb 2023 Canadian Journal of Economics; Werth et al. 2021 Applied Energy; Ke et al. LightGBM NeurIPS 2017.
- Hong & Fan 2016 IJF tutorial review; van der Meer et al. 2018 RSER; Barber et al. 2023 Annals of Statistics; Tibshirani et al. covariate shift; Bucksteeg et al. 2016 reserve sizing; Narajewski & Ziel 2020; Farrokhabadi et al. 2022 OAJPE; Xu & Xie ICML 2021.
Verified **indirectly** (through the reference list of a peer-reviewed paper read in full, de Vilmarest et al. 2024, or of arXiv:1910.00454): Gneiting & Raftery 2007; Zaffran et al. 2022 (pages); Obst et al. 2021; Browell & Fasiolo 2021; Hong et al. 2020; Álvarez et al. 2021; Ruan et al. 2020; Bucksteeg et al. 2016; Bruninx & Delarue 2014. **The author should confirm these nine directly before submission.**
