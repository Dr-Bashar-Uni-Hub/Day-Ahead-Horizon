"""Graphical abstract (final): overall title, three panels (design, wave-1 calibration failure, wave-2 intensity test)."""
import json, pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
e=pd.read_csv("results/analysis/posthoc_event_study_2020_vs_2019.csv",index_col=0); J=json.load(open("manuscript_numbers.json"))
fig=plt.figure(figsize=(14,5.9)); gs=fig.add_gridspec(1,3,width_ratios=[0.8,1.3,1.15],wspace=0.75,top=0.82)
fig.suptitle("Forecast calibration under pandemic regime shifts",fontsize=16,weight="bold",y=0.985)
a0=fig.add_subplot(gs[0]); a0.axis("off"); a0.set_title("1. Study design",fontsize=12,weight="bold",loc="left")
L=[("15 European power systems",True),("Day-ahead load, solar and",False),("net-load intervals",False),("",False),
   ("Wave 1 | 2020",True),("• Policy stringency",False),("• Solar negative control",False),("• 2019 placebo",False),("",False),
   ("Wave 2 | 2020–2021",True),("• Staggered restrictions",False),("• Country + date fixed effects",False),("",False),("Both tests pre-registered",True)]
for i,(t,b) in enumerate(L): a0.text(0,0.97-0.071*i,t,fontsize=10.5,va="top",weight="bold" if b else None)
a1=fig.add_subplot(gs[1])
for col,c,l in (("main_load","#1f4e79","Load 2020"),("main_solar","#d08c00","Solar 2020 (negative control;\nseasonal, also rises in spring 2019)"),("placebo_load","#8fa9c4","Load 2019 placebo")):
    s=e[col].rolling(7,center=True,min_periods=4).mean()*100; a1.plot(s.index,s.values,color=c,lw=2.2,label=l,ls="--" if "placebo" in col else "-")
a1.axvline(0,color="k",ls=":",lw=1); a1.axvspan(0,27,color="grey",alpha=0.1); a1.axhline(0,color="grey",lw=0.6)
a1.set_ylim(-10,33)
a1.set_xlabel("Days from restriction onset"); a1.set_ylabel("Δ miscoverage, 90% intervals (pp)")
a1.set_title("2. Wave 1: calibration failure around onset",fontsize=12,weight="bold",loc="left"); a1.legend(frameon=False,fontsize=8.5,loc="upper left")
a2=fig.add_subplot(gs[2]); r1=[x for x in J["rq1"] if x["setup"]=="main" and x["target"]=="load" and x["spec"]=="A"][0]; E=J["E"]
rows=[("Wave 1, pre-registered\n(cannot separate timing)",1000*r1["beta"],1000*r1["ci_lo"],1000*r1["ci_hi"],"#1f4e79"),
      ("Wave 2, pre-registered\n(date fixed effects)",E["EC_load"]["beta10"],E["EC_load"]["lo10"],E["EC_load"]["hi10"],"#c0504d"),
      ("Wave 2, no quality rules\n(sensitivity)",E["noQ_EC_load"]["beta10"],E["noQ_EC_load"]["lo10"],E["noQ_EC_load"]["hi10"],"#e6a19f")]
for i,(l,b_,lo,hi,c) in enumerate(rows): a2.errorbar(b_,2-i,xerr=[[b_-lo],[hi-b_]],fmt="o",color=c,ms=7,lw=2,capsize=4)
a2.axvline(0,color="grey",lw=0.8); a2.text(0.05,2.55,"no association",fontsize=8,color="grey")
a2.set_yticks([2,1,0]); a2.set_yticklabels([r[0] for r in rows],fontsize=8.5); a2.set_ylim(-0.8,2.75)
a2.set_xlabel("Load miscoverage, pp per 10 stringency points")
a2.text(0.0,-0.17,"Points = estimates; bars = 95% confidence intervals.\nWave 2 pre-registered verdict: inconclusive.",transform=a2.transAxes,fontsize=8,style="italic",va="top")
a2.set_title("3. Intensity effect not confirmed in Wave 2",fontsize=12,weight="bold",loc="left")
fig.savefig("figures/graphical_abstract.png",dpi=300,bbox_inches="tight")
