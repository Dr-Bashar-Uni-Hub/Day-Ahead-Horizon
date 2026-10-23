s = open('content3.js').read()
def rep(old, new):
    global s
    assert old in s, "NOT FOUND: " + old[:90]
    s = s.replace(old, new)
def between(a, b, new):
    global s
    i, j = s.index(a), s.index(b); s = s[:i] + new + s[j:]
# helpers available in JS
rep('const P2 = (t, o = {}) => P(cite(t), o);', '''const P2 = (t, o = {}) => P(cite(t), o);
const P8 = J.P8; const fr = r => `${F(r.beta10,2)} [${F(r.lo10,2)}, ${F(r.hi10,2)}]`;
const DW = (m, w) => P8.down_window.find(r => r.target === "load" && r.method === m && r.window === w);
const CQW = (t, w) => P8.cqr_window.find(r => r.target === t && r.window === w).coverage;
const UC = w => P8.U_cov.find(r => r.target === "load" && r.window === w);
const RC = (t, m) => P8.recovery.find(r => r.target === t && r.method === m);''')
# 1 title
rep('"A one-off onset shock: pre-registered evidence from two COVID-19 waves on the calibration of day-ahead prediction intervals for load, solar generation and net load in 15 European power systems"',
    '"Forecast calibration under pandemic regime shifts: pre-registered evidence from two COVID-19 waves across 15 European power systems"')
# 2 abstract
between('C.push(P(`Conformal prediction intervals for electricity load', 'C.push(P2("**Keywords:**', '''C.push(P2(`Conformal prediction intervals for electricity load and renewable generation assume that the future resembles the calibration period, an assumption broken by abrupt regime changes. Using the COVID-19 restrictions as a natural experiment, two pre-registered tests examined whether the calibration of day-ahead intervals failed in proportion to policy stringency across 15 European power systems. Ridge and gradient-boosting forecasts issued at 11:00 UTC for the next day were wrapped in static, rolling and adaptive conformal intervals and in conformalized quantile regression. At the first-wave onset, calibration failed sharply, mostly through over-forecasting: in the first four weeks, static 90% intervals covered ${pct(W("load","I1","w0-4"))}% of load hours and no method reached nominal coverage. The pre-registered first-wave association with stringency (${F(1000*L.beta,1)} percentage points of miscoverage per 10 stringency points for load) could not separate intensity from the common timing of restrictions. A second pre-registered test exploited the staggered restrictions of October 2020 to June 2021 with country and date fixed effects: the load estimate was ${F(J.E.EC_load.beta10,2)} (95% CI ${F(J.E.EC_load.lo10,2)} to ${F(J.E.EC_load.hi10,2)}), robust to excluding any single country and to monthly model retraining, but the pre-registered verdict was inconclusive. A harmonized post hoc first-wave analysis showed some evidence of an intensity association for net load. The findings are more consistent with an initial regime-transition shock than with a persistent relationship between stringency and miscoverage. Rolling recalibration came closest to nominal coverage at onset, adaptive conformal inference offered the best overall balance of coverage and width, and direct adaptive calibration gave the narrowest nominal net-load intervals.`));
''')
# 3 highlights
rep('''["Two pre-registered tests of interval calibration in 15 European power systems.",
 "Load and net-load intervals lost calibration at the 2020 onset; not seasonal.",
 "Second-wave test found no evidence that lockdown stringency drives miscoverage.",
 "No method kept nominal coverage at onset; adaptive conformal came closest.",
 "Direct adaptive calibration gave the narrowest nominal net-load intervals."]''',
'''["Two pre-registered tests of interval calibration in 15 European power systems.",
 "Intervals failed at the 2020 onset, mostly by over-forecasting demand.",
 "Second-wave test found no evidence that lockdown stringency drives miscoverage.",
 "No method kept nominal coverage at onset; rolling recalibration came closest.",
 "Direct adaptive calibration gave the narrowest nominal net-load intervals."]''')
# 4 intro contribution (i)
rep('evidence that day-ahead load and net-load intervals lost calibration through an onset shock shared across systems, which seasonal and placebo comparisons do not explain',
    'evidence that day-ahead load and net-load intervals lost calibration at the onset of the first wave, mostly through over-forecasting, in a pattern that seasonal and placebo comparisons argue against attributing to the spring calendar')
rep('(ii) a confirmatory second-wave test that found no evidence of a policy-intensity effect;', '(ii) a confirmatory second-wave test that found no evidence of a policy-intensity effect, with an inconclusive pre-registered verdict, complemented by harmonized, influence and model-retraining analyses;')
# 5 pre-registration: commit hashes + second pre-review
rep('Because these analyses could not resolve the intensity question, a second protocol',
    'The protocol is tagged at commit f722990 (23 October 2026, 13:32 UTC+3). Because these analyses could not resolve the intensity question, a second protocol')
rep('before any electricity data after 30 September 2020 were downloaded (Section 4.5).',
    'before any electricity data after 30 September 2020 were downloaded (commit c0f2a76, 23 October 2026, 17:52 UTC+3; Section 4.5). A second AI-generated pre-review of a later draft prompted the further post hoc analyses in Section 4.6.')
# 6 methods 4.6
rep('C.push(H1("5. Results"));', '''C.push(H2("4.6 Further post hoc analyses"));
C.push(P2("Four analyses, added after the second pre-review, test the robustness of both waves. (i) A **harmonized first-wave analysis** repeats the first-wave tests on the series cleaned by the extension's quality rules (Q1, Q2), so that both waves are evaluated under the same data policy; the pre-registered first-wave analysis is reported unchanged. (ii) A **leave-one-country-out analysis** repeats the second-wave primary specification 15 times, each time without one system (wild cluster bootstrap with 1,999 replications). (iii) An **updated-deployment benchmark** refits the ridge models at the start of each month on all data available at issuance, with the originally selected penalty, and builds split-conformal intervals from the out-of-sample residuals of the preceding 365 days; it contrasts a maintained forecaster with the frozen one. (iv) **Directional exposure** separates energy below the lower bound, Σmax(0, L − y), from energy above the upper bound by period relative to onset."));

C.push(H1("5. Results"));''')
# 7 harmonized wave 1 paragraph at end of 5.3 timing paragraph
rep('which motivated the second-wave test in Section 5.4.`));', '''which motivated the second-wave test in Section 5.4. Under the harmonized data policy of Section 4.6, the first-wave date-fixed-effects estimate was ${F(P8.harm_C_load.beta10,2)} for load (95% CI ${F(P8.harm_C_load.lo10,2)} to ${F(P8.harm_C_load.hi10,2)}; p = ${F(P8.harm_C_load.p,2)}; permutation p = ${F(P8.harm_perm_load.p_perm,2)}) and ${F(P8.harm_C_net.beta10,2)} for net load (95% CI ${F(P8.harm_C_net.lo10,2)} to ${F(P8.harm_C_net.hi10,2)}; p = ${F(P8.harm_C_net.p,3)}; permutation p = ${F(P8.harm_perm_net.p_perm,3)}). With consistently cleaned data, the first wave therefore shows some evidence of an intensity association for net load, although it is post hoc and uncorrected for the number of tests.`));''')
# 8 solar / seasonal wording
rep('The load and net-load transition in 2020 is therefore not a spring artefact', 'These comparisons argue against attributing the 2020 load and net-load transition to the spring calendar, although they cannot exclude every seasonal influence')
rep('Taken together, the evidence indicates that calibration failed through a one-off onset shock rather than in proportion to policy intensity.', 'Taken together, the evidence is more consistent with an initial regime-transition shock than with a persistent relationship between stringency and miscoverage.')
# 9 Table 4 rows + LOCO / retraining paragraph in 5.4
rep('  ["Pre-registered verdict", "Inconclusive", "–", "Null (as predicted)"]], [3300, 1950, 1950, 1800]));',
    '''  ["Post hoc: updated deployment (monthly refit)", fr(P8.U_w2C_load), fr(P8.U_w2C_net), fr(P8.U_w2C_solar)],
  ["Post hoc: leave-one-country-out range of estimates", `${F(Math.min(...P8.loco_load.map(r=>r.beta10)),2)} to ${F(Math.max(...P8.loco_load.map(r=>r.beta10)),2)}`, `${F(Math.min(...P8.loco_net.map(r=>r.beta10)),2)} to ${F(Math.max(...P8.loco_net.map(r=>r.beta10)),2)}`, "–"],
  ["Pre-registered verdict", "Inconclusive", "–", "Null (as predicted)"]], [3300, 1950, 1950, 1800]));''')
rep('the intervals widen to include it.`));', '''the intervals widen to include it. The null does not depend on any single system: omitting each in turn gave load estimates between ${F(Math.min(...P8.loco_load.map(r=>r.beta10)),2)} and ${F(Math.max(...P8.loco_load.map(r=>r.beta10)),2)} (smallest p = ${F(Math.min(...P8.loco_load.map(r=>r.p)),2)}) and no interval above zero. Nor does it depend on the frozen models: with monthly retraining (Section 4.6), the second-wave load estimate was ${F(P8.U_w2C_load.beta10,2)} (95% CI ${F(P8.U_w2C_load.lo10,2)} to ${F(P8.U_w2C_load.hi10,2)}), an interval whose upper bound lies below the practical-null threshold, although this benchmark is post hoc and not binding. Retraining did not prevent the onset failure: updated intervals covered ${pct(UC("w0-4").coverage)}% of load hours in the first four weeks after onset, against ${pct(UC("pre").coverage)}% before it.`));''')
# 10 RQ2 paragraph fixes
rep('ACI recovered fastest, reaching ${pct(W("load","I3","w5-8"))}% in weeks 5–8, and over the whole test period it achieved',
    'Rolling SCP thus came closest to nominal coverage during the transition. ACI reached ${pct(W("load","I3","w5-8"))}% in weeks 5–8 and met the recovery criterion in more systems (${RC("load","I3").recovered} of 15 for load, against ${RC("load","I1").recovered} for static and ${RC("load","I2").recovered} for rolling SCP), but not faster among those that recovered (median ${F(RC("load","I3").median_days,0)} days against ${F(RC("load","I1").median_days,0)} for static SCP); over the whole test period it achieved')
rep('Rolling SCP came closest to nominal in the first weeks but over-covered afterwards', 'Rolling SCP over-covered after the transition')
rep('`${pct(r.coverage_post)} (all post)`', '`${pct(CQW(tg, "after w8"))}`')
rep('t4.push([{ load: "Load", solar: "Solar" }[tg], MN[m], pct(r.coverage_pre), "–", "–",', 't4.push([{ load: "Load", solar: "Solar" }[tg], MN[m], m === "I4_CQR" ? pct(CQW(tg, "pre")) : pct(r.coverage_pre), m === "I4_CQR" ? pct(CQW(tg, "w0-4")) : "–", m === "I4_CQR" ? pct(CQW(tg, "w5-8")) : "–",')
rep('''`${pct(CQW(tg, "after w8"))}`''', '''m === "I4_CQR" ? pct(CQW(tg, "after w8")) : `${pct(r.coverage_post)} (all post)`''')
# 11 operational section rewrite
between('C.push(H2("5.7 Operational cost (RQ4)"));', 'C.push(H1("6. Discussion"));', '''C.push(H2("5.7 Operational exposure (RQ4)"));
const o = (t, m) => J.rq4.find(r => r.target === t && r.method === m && r.level === 90);
C.push(P2(`Shortfall energy above the upper bound and excess headroom are energy-based proxies for reserve exposure, not monetary costs. Over the whole test period, the median shortfall above the upper 90% bound was ${F(o("load","I1").shortfall_MWh_per_GWh,2)} MWh per GWh of load for static SCP, ${F(o("load","I3").shortfall_MWh_per_GWh,2)} for ACI and ${F(o("load","I2").shortfall_MWh_per_GWh,2)} for rolling SCP, against excess headroom of ${F(o("load","I1").excess_MWh_per_GWh,1)}, ${F(o("load","I3").excess_MWh_per_GWh,1)} and ${F(o("load","I2").excess_MWh_per_GWh,1)} MWh per GWh. The transition was dominated by over-forecasting (post hoc, Section 4.6): in the first four weeks after onset, ${F(100*DW("I1","w0-4").share_below,0)}% of static-interval misses fell below the lower bound, energy below the lower bound rose from ${F(DW("I1","pre").below,2)} to ${F(DW("I1","w0-4").below,2)} MWh per GWh, and energy above the upper bound fell from ${F(DW("I1","pre").above,2)} to ${F(DW("I1","w0-4").above,2)}. Rolling SCP and ACI limited the downward exposure in weeks 0–4 to ${F(DW("I2","w0-4").below,2)} and ${F(DW("I3","w0-4").below,2)} MWh per GWh. The onset risk for operators was therefore excess upward reserve and unanticipated downward imbalance, not unsecured upward imbalance.`));

''')
# 12 discussion 6.1 extra + 6.2 wording
rep('the defensible statement is that there is no evidence of an intensity effect, not that there is none.',
    'the defensible statement is that there is no evidence of an intensity effect in the second wave, not that there is none. The harmonized first-wave analysis adds a caveat: with consistently cleaned data, net-load miscoverage at onset was associated with stringency even after removing common timing, so an intensity effect during the initial transition cannot be excluded. The second-wave null held when individual systems were omitted and when the models were retrained monthly, so it is not an artefact of a single system or of model drift.')
rep('when errors exceed the calibration distribution and no static or slowly adapting rule has caught up.', 'when errors exceed the calibration distribution and no static or slowly adapting rule has caught up. In 2020 the errors were mainly downward, so the exposure was excess upward reserve and unanticipated downward imbalance; another regime change could act in the opposite direction.')
rep("ACI's nominal average coverage coexisted with 84.8% coverage in the first month.", "ACI's nominal average coverage coexisted with 84.8% coverage in the first month, while rolling recalibration, which reacted fastest, reached 87.4%.")
# 13 limitations
rep('All data come from a single source, ENTSO-E via OPSD, whose known quality issues [@hirth18] were not cleaned.',
    'The pre-registered first-wave analysis used the OPSD series without cleaning, and known ENTSO-E data-quality issues [@hirth18] affected two systems; harmonized post hoc analyses address this, but both data sources ultimately rely on ENTSO-E reporting.')
rep('The first-wave robustness analyses were added after an AI-generated pre-review and were not pre-registered; the second-wave test was.',
    'The robustness analyses in Sections 4.4 and 4.6 were added after two AI-generated pre-reviews and were not pre-registered; the second-wave test was.')
# 14 conclusion
between('C.push(H1("7. Conclusion"));', 'C.push(H1("Declarations"));', '''C.push(H1("7. Conclusion"));
C.push(P2("Across 15 European power systems, day-ahead load and net-load prediction intervals lost calibration sharply in the weeks after the March 2020 onset of COVID-19 restrictions, mostly because demand fell below the forecasts. A first pre-registered test found an association with policy stringency but could not separate intensity from the common timing of restrictions. A second pre-registered test, using the staggered restrictions of the second wave, found no evidence that stringency drives miscoverage, a result robust to omitting individual systems and to monthly retraining; its pre-registered verdict was nevertheless inconclusive, and a harmonized post hoc analysis of the first wave left open an intensity effect for net load at onset. The findings are more consistent with an initial regime-transition shock than with a persistent relationship between stringency and miscoverage. No interval method kept nominal coverage at onset: rolling recalibration came closest during the transition, adaptive conformal inference offered the best overall balance of coverage and width, direct adaptive calibration was the better route to net-load intervals, and solar intervals required season-aware calibration regardless of policy. Uncertainty estimates for power systems should be monitored on short windows, recalibrated quickly at the onset of a regime change, and checked for the direction as well as the size of their errors."));

''')
# 15 AI declaration
rep('and ChatGPT (OpenAI) to obtain an AI-generated pre-review of an earlier draft, which prompted the post hoc analyses described in Section 3.3.',
    'and ChatGPT (OpenAI) to obtain AI-generated pre-reviews of two earlier drafts, which prompted the post hoc analyses described in Sections 4.4 and 4.6.')
rep('"/tmp/proj/manuscript/Manuscript_EPSR_v3.docx"', '"/tmp/proj/manuscript/Manuscript_EPSR_v4.docx"')
open('content4.js', 'w').write(s); print("edits applied")
