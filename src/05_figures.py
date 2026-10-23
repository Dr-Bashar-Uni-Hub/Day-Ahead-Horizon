"""Step 05 - manuscript figures (300 dpi). Uses only saved result files."""
import json, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
A = "/tmp/proj/results/analysis"; F = "/tmp/proj/figures"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.dpi": 300, "savefig.bbox": "tight"})
COL = {"load": "#1f4e79", "solar": "#d08c00", "net": "#7a2e8e"}
exec(open("/tmp/proj/src/03_analysis.py").read().split("def load(")[0].split("ox = pd.read_csv")[0])
src = open("/tmp/proj/src/03_analysis.py").read(); exec(src[src.index("ox = pd.read_csv"):src.index("def load(")])
C = json.load(open("/tmp/proj/audit/01_config.json"))["countries"]
on = pd.read_csv(f"{A}/onset_dates.csv", index_col=0, parse_dates=["onset50"]).onset50

# Fig 2 - stringency trajectories
fig, ax = plt.subplots(figsize=(7, 3))
for c in C:
    s = stringency(c, "main"); ax.plot(s.index, s.values, lw=0.9, alpha=0.75, label=c.replace("_GBN", ""))
ax.axhline(50, color="k", ls=":", lw=0.8); ax.text(pd.Timestamp("2020-01-05"), 52, "onset threshold (50)", fontsize=7)
ax.set_ylabel("OxCGRT stringency index"); ax.set_xlim(pd.Timestamp("2020-01-01"), pd.Timestamp("2020-09-30"))
ax.legend(ncol=8, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.22))
fig.savefig(f"{F}/fig2_stringency.png"); plt.close()

# Fig 3 - event study (static I1, 90%) with mean stringency
ev = pd.read_csv(f"{A}/event_study.csv")
st = []
for c in C:
    s = stringency(c, "main"); s.index = (s.index - on[c]).days; st.append(s)
st = pd.concat(st, axis=1).mean(1).loc[-28:90]
fig, ax = plt.subplots(figsize=(7, 3.2))
for v in ("load", "net", "solar"):
    e = ev[ev.target == v].set_index("rel").vs_pre.rolling(7, center=True, min_periods=4).mean()
    ax.plot(e.index, 100 * e.values, color=COL[v], lw=1.6, label={"load": "Load", "net": "Net load", "solar": "Solar (negative control)"}[v])
ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="k", ls="--", lw=0.8)
ax.axvspan(0, 27, color="grey", alpha=0.08); ax.axvspan(28, 59, color="grey", alpha=0.04)
ax.set_xlabel("Days relative to onset (stringency ≥ 50)"); ax.set_ylabel("Change in miscoverage vs. pre-onset (pp)")
ax2 = ax.twinx(); ax2.plot(st.index, st.values, color="k", lw=0.8, ls=":"); ax2.set_ylabel("Mean stringency (dotted)"); ax2.set_ylim(0, 100)
ax2.spines["top"].set_visible(False); ax.legend(frameon=False, fontsize=7.5, loc="upper right")
fig.savefig(f"{F}/fig3_event_study.png"); plt.close()

# Fig 4 - RQ1 coefficients: main/placebo, spec A/B, plus sensitivity
r = pd.read_csv(f"{A}/rq1_panel_regressions.csv"); s = pd.read_csv(f"{A}/sensitivity_rq1.csv")
rows = []
for _, x in r.iterrows(): rows.append((f"{'2020' if x.setup=='main' else '2019 placebo'}, Spec {x.spec}, 90%", x.target, x.beta, x.ci_lo, x.ci_hi))
for _, x in s.iterrows():
    lab = {"ridge_I1_80": "Ridge, 80%", "ridge_I1_95": "Ridge, 95%"}.get(x.analysis, x.analysis.replace("M2_seed", "LightGBM seed ").replace("_I1_90", ", 90%"))
    if x.setup == "placebo": lab = "2019 placebo, " + lab
    rows.append((lab, x.target, x.beta, x.ci_lo, x.ci_hi))
d = pd.DataFrame(rows, columns=["lab", "target", "b", "lo", "hi"])
labs = list(dict.fromkeys(d.lab)); fig, axs = plt.subplots(1, 3, figsize=(7.2, 4.6), sharey=True)
for ax, v in zip(axs, ("load", "net", "solar")):
    q = d[d.target == v].set_index("lab").reindex(labs)
    y = np.arange(len(labs))[::-1]
    ax.errorbar(1000 * q.b, y, xerr=[1000 * (q.b - q.lo), 1000 * (q.hi - q.b)], fmt="o", ms=3.5, color=COL[v], ecolor=COL[v], lw=1)
    ax.axvline(0, color="grey", lw=0.7); ax.set_title({"load": "Load", "net": "Net load", "solar": "Solar (control)"}[v], fontsize=9)
axs[0].set_yticks(np.arange(len(labs))[::-1]); axs[0].set_yticklabels(labs, fontsize=7)
fig.supxlabel("Percentage points of miscoverage per 10 stringency points", fontsize=8.5)
fig.savefig(f"{F}/fig4_rq1_coefficients.png"); plt.close()

# Fig 5 - coverage pre/post onset and width by method (90%)
cv = pd.read_csv(f"{A}/coverage_width_score.csv"); qm = pd.read_csv(f"{A}/i4_i5_quantile_methods.csv")
cv = pd.concat([cv[cv.level == 90], qm[qm.level == 90]])
name = {"I1": "Static SCP", "I2": "Rolling SCP", "I3": "ACI", "I4_CQR": "CQR", "I5_rawQR": "Raw QR"}
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.8), sharey=True)
for ax, v in zip(axs, ("load", "net", "solar")):
    g = cv[cv.target == v].groupby("method")[["coverage_pre", "coverage_post"]].mean()
    g = g.reindex([m for m in name if m in g.index]); x = np.arange(len(g))
    ax.bar(x - 0.18, 100 * g.coverage_pre, 0.36, color="#b0b7c3", label="Before onset")
    ax.bar(x + 0.18, 100 * g.coverage_post, 0.36, color=COL[v], label="After onset")
    ax.axhline(90, color="k", ls="--", lw=0.8); ax.set_ylim(60, 100)
    ax.set_xticks(x); ax.set_xticklabels([name[m] for m in g.index], rotation=35, ha="right", fontsize=7.5)
    ax.set_title({"load": "Load", "net": "Net load", "solar": "Solar (daylight)"}[v], fontsize=9)
axs[0].set_ylabel("Empirical coverage (%)"); axs[0].legend(frameon=False, fontsize=7, loc="lower left")
fig.savefig(f"{F}/fig5_coverage_by_method.png"); plt.close()

# Fig 6 - net load: direct vs component combination (I1 and I3, 90%)
n = pd.read_csv(f"{A}/rq3_netload.csv"); n = n[n.level == 90]
fig, axs = plt.subplots(1, 2, figsize=(7, 3))
for ax, m in zip(axs, ("I1", "I3")):
    p = n[n.method == m].pivot(index="country", columns="approach", values=["width", "coverage"])
    ax.scatter(p[("width", "N2_combination")], p[("width", "N1_direct")], c=100 * p[("coverage", "N1_direct")], cmap="viridis", vmin=80, vmax=95, s=28)
    lim = [p["width"].min().min() * 0.9, p["width"].max().max() * 1.05]; ax.plot(lim, lim, "k:", lw=0.8)
    ax.set_xlabel("Width, component combination (MW)"); ax.set_ylabel("Width, direct (MW)"); ax.set_title(name[m], fontsize=9)
sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(80, 95)); fig.colorbar(sm, ax=axs, label="Direct coverage (%)", shrink=0.85)
fig.savefig(f"{F}/fig6_netload.png"); plt.close()
print("figures done")
