"""E2b - protocol-extension-v1.1 §5 (ii) for net load: permutation of national stringency series, E-C, 4,999 draws, seed 7."""
import json, sys
sys.argv = ["x", "none"]; exec(open("/tmp/proj/src/E2_extension_analysis.py").read().split('if __name__ == "__main__":')[0])
p = pd.read_csv(f"{OUT}/panel_ext_net.csv", parse_dates=["date"]); r = perm(p, "C"); print("perm net", r, flush=True)
json.dump({"perm_net": r}, open(f"{OUT}/E2_perm_net.json", "w"), default=float, indent=1)
