"""POST HOC: event study in the 2019 placebo year (2020 onset dates mapped to 2019) for comparison with 2020."""
import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
A="/tmp/proj/results/analysis"; F="/tmp/proj/figures"
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":300,"savefig.bbox":"tight"})
COL={"load":"#1f4e79","solar":"#d08c00","net":"#7a2e8e"}; LAB={"load":"Load","net":"Net load","solar":"Solar (negative control)"}
on=pd.read_csv(f"{A}/onset_dates.csv",index_col=0,parse_dates=["onset50"]).onset50
out=[]; fig,axs=plt.subplots(1,2,figsize=(7.4,3.1),sharey=True)
for ax,setup,yr in ((axs[0],"main",2020),(axs[1],"placebo",2019)):
    for v in ("load","net","solar"):
        p=pd.read_csv(f"{A}/panel_{setup}_{v}.csv",parse_dates=["date"])
        o={c:d.replace(year=yr) for c,d in on.items()}
        p["rel"]=[(d-o[c]).days for d,c in zip(p.date,p.country)]
        base=p[p.rel<0].groupby("country").miscov.mean(); p["vs"]=p.miscov-p.country.map(base)
        e=p[(p.rel>=-28)&(p.rel<=90)].groupby("rel").vs.mean()
        out.append(e.rename(f"{setup}_{v}"))
        ax.plot(e.index,100*e.rolling(7,center=True,min_periods=4).mean(),color=COL[v],lw=1.5,label=LAB[v])
    ax.axhline(0,color="grey",lw=0.6); ax.axvline(0,color="k",ls="--",lw=0.8)
    ax.set_title("(a) 2020" if yr==2020 else "(b) 2019 placebo (2020 onset dates)",fontsize=9); ax.set_xlabel("Days relative to onset")
axs[0].set_ylabel("Change in miscoverage vs. pre-onset (pp)"); axs[0].legend(frameon=False,fontsize=7,loc="upper left")
fig.savefig(f"{F}/fig3_event_study.png"); plt.close()
d=pd.concat(out,axis=1); d.to_csv(f"{A}/posthoc_event_study_2020_vs_2019.csv")
for s in ("main","placebo"):
    for v in ("load","solar"):
        x=d[f"{s}_{v}"]; print(s,v,"days 0-27: %.3f  days 28-59: %.3f  days 60-90: %.3f"%(x.loc[0:27].mean(),x.loc[28:59].mean(),x.loc[60:90].mean()))
