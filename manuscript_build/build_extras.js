// requires head.js helpers (P, H1, H2, B, CAP, TABLE, runs, F, pct, J, etc.)
const SX = JSON.parse(fs.readFileSync("/tmp/proj/supp_numbers.json"));
const cc = c => c.replace("_GBN", "");
const STY = { default: { document: { run: { font: "Times New Roman", size: 22 } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: "Times New Roman" }, paragraph: { outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, italics: true, font: "Times New Roman" }, paragraph: { outlineLevel: 1 } },
    { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, font: "Times New Roman" }, paragraph: { outlineLevel: 2 } }] };
const NUM = { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
                                                    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1200, hanging: 360 } } } }] }] };
const PAGE = { page: { size: { width: 11906, height: 16838 }, margin: { top: 1418, bottom: 1418, left: 1418, right: 1418 } } };
const footer = { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] }) };
const save = (children, file) => Packer.toBuffer(new Document({ styles: STY, numbering: NUM, sections: [{ properties: PAGE, footers: footer, children }] }))
  .then(b => { fs.writeFileSync("/tmp/proj/manuscript/" + file, b); console.log("written", file); });

// simple markdown -> docx (headings, bullets, pipe tables, paragraphs)
function md(text, shift = 1) {
  const out = []; const lines = text.split("\n"); let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (/^\s*$/.test(l)) { i++; continue; }
    if (l.startsWith("|")) {
      const rows = []; while (i < lines.length && lines[i].startsWith("|")) { if (!/^\|[\s\-|]+\|$/.test(lines[i])) rows.push(lines[i].split("|").slice(1, -1).map(s => s.trim())); i++; }
      const n = rows[0].length; const w = Array(n).fill(Math.floor(9000 / n));
      out.push(TABLE(rows[0], rows.slice(1), w)); out.push(new Paragraph({ children: [] })); continue;
    }
    const h = l.match(/^(#+)\s+(.*)/);
    if (h) { const lv = Math.min(h[1].length + shift - 1, 3); out.push(new Paragraph({ heading: [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3][lv - 1], children: runs(h[2]) })); i++; continue; }
    const b = l.match(/^(\s*)[-*]\s+(.*)/);
    if (b) { out.push(new Paragraph({ numbering: { reference: "bul", level: b[1].length >= 2 ? 1 : 0 }, children: runs(b[2].replace(/`/g, "")), spacing: { after: 60 } })); i++; continue; }
    out.push(new Paragraph({ children: runs(l.replace(/`/g, "")), spacing: { after: 100 } })); i++;
  }
  return out;
}

// ======================= SUPPLEMENTARY MATERIAL =======================
const X = [];
X.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: "Supplementary Material", bold: true, size: 30 })] }));
X.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: runs("*Forecast calibration under pandemic regime shifts: pre-registered evidence from two COVID-19 waves across 15 European power systems* — B. ALHAJAHMAD") }));
X.push(P("Contents: S1 documented literature search; S2 protocol deviations, implementation clarifications and post hoc analyses; S3 sensitivity analyses of the pre-registered test (Table S3); S4 recovery times (Table S4); S5 per-system coverage (Table S5); S6 per-system point accuracy and selected hyperparameters (Table S6); S7 load–solar residual dependence (Table S7); S8 operational cost by method (Table S8); S9 first-wave sensitivity excluding two series with data errors (Table S9; post hoc); S10 second-wave extension: data consistency, quality rules, full results, monthly coverage and tightening events (Tables S10a–S10d); S11 further post hoc analyses after a second AI-generated pre-review (Tables S11a–S11e). Code and data for every table are in the public repository (tag protocol-v1.0 and subsequent commits)."));
X.push(H1("S1. Documented literature search"));
X.push(...md(SX.searchlog.replace(/^# .*\n/, ""), 2));
X.push(H1("S2. Deviations, implementation clarifications and post hoc analyses"));
X.push(P("This section reproduces the repository's DEVIATIONS.md. Entries D (administrative), C (clarifications fixed before 2020 results were inspected), V (verification), L (limitations) and P (post hoc analyses) are distinguished."));
X.push(...md(SX.deviations.replace(/^# .*\n/, ""), 2));

X.push(H1("S3. Sensitivity analyses of the pre-registered test"));
X.push(CAP("**Table S3a.** Pre-specified sensitivity analyses (PROTOCOL §9): stringency coefficient in percentage points of miscoverage per 10 stringency points, Specification A, wild cluster bootstrap."));
const lab = a => ({ ridge_I1_80: "Ridge, static SCP, 80%", ridge_I1_95: "Ridge, static SCP, 95%" }[a] || a.replace("M2_seed", "LightGBM seed ").replace("_I1_90", ", static SCP, 90%"));
X.push(TABLE(["Analysis", "Test year", "Target", "Effect [95% CI]", "p"],
  SX.sens.map(r => [lab(r.analysis), r.setup === "main" ? "2020" : "2019 placebo", r.target, `${F(1000*r.beta,2)} [${F(1000*r.ci_lo,2)}, ${F(1000*r.ci_hi,2)}]`, r.p_wcr === 0 ? "< 0.0001" : F(r.p_wcr, 4)]),
  [2900, 1300, 1100, 2500, 1200]));
X.push(P(""));
X.push(CAP("**Table S3b.** Leave-one-country-out stringency coefficients (Specification A, 2020, percentage points per 10 stringency points)."));
const sys = [...new Set(SX.loco.map(r => r.dropped))];
X.push(TABLE(["System dropped", "Load", "Net load", "Solar"], sys.map(c => [c, ...["load", "net", "solar"].map(t => F(SX.loco.find(r => r.dropped === c && r.target === t).beta, 2))]), [2700, 2100, 2100, 2100]));

X.push(H1("S4. Recovery times"));
X.push(CAP("**Table S4.** Days from onset until the 14-day rolling coverage of 90% intervals re-entered ±2.5 points of nominal and stayed there for 14 days (onset = first day with stringency ≥ 50). “c” = censored (criterion not met by 30 September 2020)."));
const rec = SX.rec.filter(r => r.onset === "onset50");
const rr = (c, t, m) => { const r = rec.find(x => x.country === c && x.target === t && x.method === m); return r.censored ? "c" : F(r.recovery_days, 0); };
X.push(TABLE(["System", "Load SCP", "Load roll.", "Load ACI", "Net SCP", "Net roll.", "Net ACI", "Solar SCP", "Solar roll.", "Solar ACI"],
  [...new Set(rec.map(r => r.country))].map(c => [cc(c), ...["load", "net", "solar"].flatMap(t => ["I1", "I2", "I3"].map(m => rr(c, t, m)))]),
  [1000, 900, 900, 900, 900, 900, 900, 900, 900, 900]));

X.push(H1("S5. Per-system coverage"));
X.push(CAP("**Table S5.** Coverage (%) of 90% intervals before and after onset, and mean width (MW), by system and method (load)."));
const cv = (c, m, k) => SX.cov_country.find(r => r.country === c && r.target === "load" && r.method === m)[k];
X.push(TABLE(["System", "SCP pre", "SCP post", "Rolling pre", "Rolling post", "ACI pre", "ACI post", "ACI width"],
  [...new Set(SX.cov_country.map(r => r.country))].map(c => [cc(c), pct(cv(c,"I1","coverage_pre")), pct(cv(c,"I1","coverage_post")), pct(cv(c,"I2","coverage_pre")), pct(cv(c,"I2","coverage_post")), pct(cv(c,"I3","coverage_pre")), pct(cv(c,"I3","coverage_post")), F(cv(c,"I3","width"),0)]),
  [1200, 1100, 1100, 1150, 1150, 1100, 1100, 1100]));

X.push(H1("S6. Point accuracy and selected hyperparameters"));
X.push(CAP("**Table S6.** Test-period RMSE (MW) of ridge, LightGBM (seed 1) and weekly seasonal-naive forecasts; ridge penalty selected on the calibration year; ACI step size γ selected on July–December 2019."));
X.push(TABLE(["System", "Load ridge", "Load LGBM", "Load naive", "Solar ridge", "Solar LGBM", "Solar naive", "α load", "α solar", "γ load/solar/net"],
  [...new Set(SX.acc.map(r => r.country))].map(c => { const a = t => SX.acc.find(r => r.country === c && r.target === t); const m = SX.meta.find(r => r.country === c);
    return [cc(c), F(a("load").ridge,0), F(a("load").lgbm_s1,0), F(a("load").naive,0), F(a("solar").ridge,0), F(a("solar").lgbm_s1,0), F(a("solar").naive,0), Number(m.ridge_alpha.load).toExponential(0), Number(m.ridge_alpha.solar).toExponential(0), `${m.aci_gamma.load}/${m.aci_gamma.solar}/${m.aci_gamma.net}`]; }),
  [800, 850, 850, 850, 850, 850, 850, 800, 800, 1350]));

X.push(H1("S7. Load–solar residual dependence"));
X.push(CAP("**Table S7.** Spearman correlation between load and solar ridge residuals in daylight hours, calibration year (2019) and test period (2020)."));
X.push(TABLE(["System", "2019", "2020", "n (2020)"], [...new Set(SX.dep.map(r => r.country))].map(c => { const g = p => SX.dep.find(r => r.country === c && r.part === p);
  return [cc(c), F(g("cal").spearman_load_solar_resid, 3), F(g("test").spearman_load_solar_resid, 3), g("test").n]; }), [2700, 2100, 2100, 2100]));

X.push(H1("S8. Operational cost by method"));
X.push(CAP("**Table S8.** Median over systems of shortfall energy above the upper bound and excess headroom (MWh per GWh of load), whole test period."));
X.push(TABLE(["Target", "Method", "Level (%)", "Shortfall", "Excess headroom"],
  SX.ops.map(r => [r.target, { I1: "Static SCP", I2: "Rolling SCP", I3: "ACI" }[r.method], r.level, F(r.shortfall_MWh_per_GWh, 2), F(r.excess_MWh_per_GWh, 1)]), [1700, 2000, 1500, 1900, 1900]));

const E = J.E; const ef = r => `${F(r.beta10,2)} [${F(r.lo10,2)}, ${F(r.hi10,2)}]`;
X.push(H1("S9. First-wave sensitivity excluding CH and SK (post hoc)"));
X.push(P("The raw OPSD series contain a Slovak load value of 2,170,811 MW on 8 August 2020 (nine hours above 10 GW) and a definition break in the Swiss solar series in 2020 (maximum 1,821 MW against 300–330 MW in 2018–2019), which also contaminates Swiss load forecasts through the lagged solar inputs. Table S9 repeats the key first-wave analyses without these two systems (13 clusters)."));
X.push(CAP("**Table S9.** First wave, 13 systems: stringency coefficient (percentage points per 10 stringency points) with 95% wild-cluster-bootstrap CIs, and permutation p-values (4,999 draws)."));
X.push(TABLE(["Analysis", "Load", "Net load"], [
  ["Spec. A (pre-registered specification)", `${F(1000*E.s13.A_load.beta,2)} [${F(1000*E.s13.A_load.ci_lo,2)}, ${F(1000*E.s13.A_load.ci_hi,2)}], p ${E.s13.A_load.p_wcr===0?"< 0.0001":F(E.s13.A_load.p_wcr,4)}`, "–"],
  ["Spec. C (date fixed effects)", `${F(1000*E.s13.C_load.beta,2)} [${F(1000*E.s13.C_load.ci_lo,2)}, ${F(1000*E.s13.C_load.ci_hi,2)}], p ${F(E.s13.C_load.p_wcr,3)}`, `${F(1000*E.s13.C_net.beta,2)} [${F(1000*E.s13.C_net.ci_lo,2)}, ${F(1000*E.s13.C_net.ci_hi,2)}], p ${F(E.s13.C_net.p_wcr,3)}`],
  ["Permutation p (Spec. A)", F(E.s13.perm_load,3), F(E.s13.perm_net,3)]], [3600, 2700, 2700]));
X.push(H1("S10. Second-wave extension (protocol-extension-v1.1)"));
X.push(P("Data from 1 October 2020 were obtained from the Energy-Charts public API (Fraunhofer ISE) and spliced to OPSD at that date. The tagged extension file names the ENTSO-E API; see deviation E1 in Section S2. The untagged 5% exclusion rule is reported as a sensitivity analysis only."));
X.push(CAP("**Table S10a.** Q0 consistency check, January 2019 – September 2020: Energy-Charts versus OPSD (median absolute hourly difference as % of the OPSD mean; ratio of means; correlation). Systems above 1% are flagged; under the tagged rule they remain in the analysis."));
X.push(TABLE(["System", "Variable", "Median abs. diff. (%)", "Ratio of means", "Correlation", "Flag"],
  E.q0.map(r => [cc(r.system), r.var, F(r.median_abs_diff_pct, 2), F(r.ratio_mean, 3), F(r.corr, 3), r.median_abs_diff_pct > 1 ? "flag" : ""]), [1300, 1200, 1900, 1600, 1500, 1000]));
X.push(P(""));
X.push(CAP("**Table S10b.** Quality rules: values removed by Q1 (above 3 × training-period 99.9th percentile) and solar series excluded by Q2 (extension maximum > 2.5 × 2019 maximum)."));
X.push(TABLE(["System", "Q1 load removed", "Q1 solar removed", "Q2 solar excluded"], E.audit.map(r => [cc(r.country), r.Q1_load_removed, r.Q1_solar_removed, r.Q2_solar_excluded ? "yes" : "no"]), [2250, 2250, 2250, 2250]));
X.push(P(""));
X.push(CAP("**Table S10c.** Second-wave results, all specifications (percentage points per 10 stringency points, 95% CI, p)."));
const er = r => `${ef(r)}, p ${F(r.p,3)}`;
X.push(TABLE(["Specification", "Load", "Net load", "Solar"], [
  ["E-C (primary)", er(E.EC_load), er(E.EC_net), er(E.EC_solar)], ["E-C + country trends", er(E.ECtrend_load), er(E.ECtrend_net), er(E.ECtrend_solar)],
  ["Specification A", er(E.A_load), er(E.A_net), er(E.A_solar)], ["E-C pooled Jan 2020 – Jun 2021", er(E.pooled_EC_load), er(E.pooled_EC_net), er(E.pooled_EC_solar)],
  ["No quality rules", er(E.noQ_EC_load), er(E.noQ_EC_net), er(E.noQ_EC_solar)], ["5% rule (CH, SI; AT solar excluded)", er(E.rule5_EC_load), er(E.rule5_EC_net), er(E.rule5_EC_solar)],
  ["Permutation p (E-C, 4,999 draws)", "0.426", "0.660", "–"]], [2600, 2150, 2150, 2100]));
X.push(P(""));
X.push(CAP("**Table S10d.** Monthly coverage (%) of 90% load intervals, mean over systems, January 2020 – June 2021."));
const months = [...new Set(E.month.map(r => r.month))];
X.push(TABLE(["Month", "Static SCP", "Rolling SCP", "ACI"], months.map(m => [m, ...["I1", "I2", "I3"].map(k => pct(E.month.find(r => r.target === "load" && r.method === k && r.month === m).coverage))]), [2250, 2250, 2250, 2250]));
X.push(P(`Tightening events (increase of at least 20 stringency points within 14 days, at least 8 weeks apart): ${E.events}. Mean change in load miscoverage relative to the 14 days before the event: −1.0 (days 0–13), −1.1 (days 14–27) and +1.8 percentage points (days 28–42).`));

const P8 = J.P8; const fr2 = r => `${F(r.beta10,2)} [${F(r.lo10,2)}, ${F(r.hi10,2)}], p ${r.p===0?"< 0.0001":F(r.p,3)}`;
X.push(H1("S11. Further post hoc analyses (second AI-generated pre-review)"));
X.push(CAP("**Table S11a.** Harmonized first wave (Q1/Q2 applied to January–September 2020): stringency coefficient (pp per 10 points)."));
X.push(TABLE(["Specification", "Load", "Net load", "Solar"], [["Spec. A", fr2(P8.harm_A_load), fr2(P8.harm_A_net), fr2(P8.harm_A_solar)], ["Spec. C (date FE)", fr2(P8.harm_C_load), fr2(P8.harm_C_net), fr2(P8.harm_C_solar)],
  ["Permutation p (Spec. A)", F(P8.harm_perm_load.p_perm,3), F(P8.harm_perm_net.p_perm,3), "–"]], [2400, 2250, 2250, 2100]));
X.push(P(""));
X.push(CAP("**Table S11b.** Second wave, leave-one-country-out E-C (B = 1,999): estimate [95% CI], p."));
const sysL = P8.loco_load.map(r => r.dropped);
X.push(TABLE(["System omitted", "Load", "Net load"], sysL.map(c => [cc(c), fr2(P8.loco_load.find(r => r.dropped === c)), (P8.loco_net.find(r => r.dropped === c) ? fr2(P8.loco_net.find(r => r.dropped === c)) : "– (no solar)")]), [2200, 3400, 3400]));
X.push(P(""));
X.push(CAP("**Table S11c.** Updated deployment (monthly refit, 365-day out-of-sample conformal scores): stringency coefficients and load coverage by period."));
X.push(TABLE(["Specification", "Load", "Net load", "Solar"], [["Wave 1, Spec. A", fr2(P8.U_w1A_load), fr2(P8.U_w1A_net), fr2(P8.U_w1A_solar)], ["Wave 1, Spec. C", fr2(P8.U_w1C_load), fr2(P8.U_w1C_net), fr2(P8.U_w1C_solar)], ["Wave 2, E-C", fr2(P8.U_w2C_load), fr2(P8.U_w2C_net), fr2(P8.U_w2C_solar)]], [2400, 2250, 2250, 2100]));
X.push(TABLE(["Period", "Load coverage (%)", "Mean width (MW)"], P8.U_cov.filter(r => r.target === "load").map(r => [r.window, pct(r.coverage), F(r.width, 0)]), [3000, 3000, 3000]));
X.push(P(""));
X.push(CAP("**Table S11d.** Directional exposure by period (wave 1, 90%, load; medians over systems, MWh per GWh of load): energy below the lower bound, energy above the upper bound, and share of misses below the lower bound."));
X.push(TABLE(["Method", "Period", "Below lower", "Above upper", "Share of misses below"], P8.down_window.filter(r => r.target === "load").map(r => [{I1:"Static SCP",I2:"Rolling SCP",I3:"ACI"}[r.method], r.window, F(r.below,2), F(r.above,2), F(100*r.share_below,0) + "%"]), [1800, 1600, 1800, 1800, 2000]));
X.push(P(""));
X.push(CAP("**Table S11e.** CQR coverage (%) by period (90%) and recovery-time summary (systems meeting the recovery criterion out of 15; median days among them)."));
X.push(TABLE(["Target", "Before onset", "Weeks 0–4", "Weeks 5–8", "After week 8"], ["load", "solar"].map(t => [t, ...["pre", "w0-4", "w5-8", "after w8"].map(w => pct(P8.cqr_window.find(r => r.target === t && r.window === w).coverage))]), [1800, 1800, 1800, 1800, 1800]));
X.push(TABLE(["Target", "Method", "Recovered (of 15)", "Median days"], P8.recovery.map(r => [r.target, {I1:"Static SCP",I2:"Rolling SCP",I3:"ACI"}[r.method], r.recovered, F(r.median_days, 0)]), [2250, 2250, 2250, 2250]));
save(X, "Supplementary_Material_EPSR.docx");

// ======================= HIGHLIGHTS =======================
save([new Paragraph({ children: [new TextRun({ text: "Highlights", bold: true, size: 28 })], spacing: { after: 200 } }),
  ...["Two pre-registered tests of interval calibration in 15 European power systems.",
      "Intervals failed at the 2020 onset, mostly by over-forecasting demand.",
      "Second-wave test found no evidence that lockdown stringency drives miscoverage.",
      "No method kept nominal coverage at onset; rolling recalibration came closest.",
      "Direct adaptive calibration gave the narrowest nominal net-load intervals."].map(h => B(h))], "Highlights_EPSR.docx");

// ======================= COVER LETTER =======================
const CL = [];
const L_ = t => new Paragraph({ children: runs(t), spacing: { after: 160, line: 300 }, alignment: AlignmentType.JUSTIFIED });
CL.push(L_("Bashar ALHAJAHMAD"));
CL.push(L_("Department of Computer Engineering, Faculty of Engineering, Siirt University, Siirt, Türkiye · bashar.ahmad@siirt.edu.tr · ORCID 0009-0009-3455-7206"));
CL.push(L_("[Date]"));
CL.push(L_("The Editor-in-Chief, *Electric Power Systems Research*"));
CL.push(L_("Dear Editor,"));
CL.push(L_("I am pleased to submit the manuscript **“Forecast calibration under pandemic regime shifts: pre-registered evidence from two COVID-19 waves across 15 European power systems”** for consideration as a Full Length Article in *Electric Power Systems Research*."));
CL.push(L_("Operators size reserves and schedule flexibility from forecast uncertainty, yet the conformal prediction intervals now widely used for load and renewable forecasts assume that the future resembles the calibration period. The manuscript uses the COVID-19 restrictions across 15 European power systems to test, in two pre-registered designs, whether day-ahead interval calibration failed in proportion to policy stringency, with solar generation as a negative control and 2019 as a placebo year. It compares static, rolling and adaptive conformal intervals, conformalized quantile regression and raw quantile regression, and two routes to net-load intervals, and translates miscoverage into shortfall and headroom energy."));
CL.push(L_("The principal findings are: (i) at the March 2020 onset, load and net-load intervals lost calibration sharply, mostly through over-forecasting, and no interval method maintained nominal coverage — rolling recalibration came closest during the transition, while adaptive conformal inference balanced coverage and width best among the ridge-based intervals; (ii) a first pre-registered test found an association with stringency but could not separate intensity from the common timing of restrictions; (iii) a second pre-registered test using the staggered restrictions of October 2020 to June 2021 found no evidence that stringency drives miscoverage, robust to omitting individual systems and to monthly model retraining, although its pre-registered verdict is inconclusive and a harmonized first-wave analysis leaves open an intensity effect for net load at onset; and (iv) direct adaptive calibration of net load gave the narrowest intervals at nominal coverage. The findings are more consistent with an initial regime-transition shock than with a persistent relationship between stringency and miscoverage, and they bear directly on how calibration should be monitored — in size and direction — at the onset of abrupt regime changes."));
CL.push(L_("**Transparency.** Both analysis plans were frozen and tagged in a public repository before the relevant data were analysed (protocol-v1.0) or downloaded (protocol-extension-v1.1). The manuscript reports both pre-registered tests and their interpretation rules unchanged, and labels all other analyses as post hoc. Some of these were added after AI-generated pre-reviews of two earlier drafts (ChatGPT); one revealed data errors in two national series, which led me to withdraw an interim interpretation and pre-register the second-wave test, and a later one led me to qualify the title and conclusions and to correct statements on method performance and operational exposure. The extension used a different public data source than the tagged file names, which is disclosed with its consequences. The full history is documented in the deviations log (Supplementary Section S2). All data are public, and code, protocols and derived results are available at https://github.com/Dr-Bashar-Uni-Hub/Day-Ahead-Horizon."));
CL.push(L_("**Related manuscript.** A separate manuscript of mine, “Fallback strategy matters more than architecture: A reliability-oriented evaluation of deep learning forecasters for solar generation and electrical load”, is currently under review at the *International Journal of Green Energy*. It evaluates deep-learning point forecasters for German and Austrian load and solar under input degradation. The present submission differs in its output (prediction intervals rather than point forecasts), forecast setting (day-ahead issuance), research question (calibration under a regime change), methods and country set (15 systems), and reuses none of its results. It is cited in the manuscript, and I am happy to provide a copy on request."));
CL.push(L_("**Declarations.** This manuscript is original, has not been published previously and is not under consideration elsewhere. I am the sole author and declare no competing interests; the work received no specific funding. In line with the journal's policy, the manuscript contains a declaration of the use of generative AI: Claude (Anthropic) for assistance with analysis code, literature searches and drafting, and ChatGPT (OpenAI) for AI-generated pre-reviews of two earlier drafts. I reviewed all content and take full responsibility for it."));
CL.push(L_("Thank you for considering this submission. I look forward to hearing from you."));
CL.push(L_("Sincerely,"));
CL.push(L_("Bashar ALHAJAHMAD"));
save(CL, "Cover_Letter_EPSR.docx");
