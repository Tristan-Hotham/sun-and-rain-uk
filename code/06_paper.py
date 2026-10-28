"""Step 6. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Sun_and_Rain_UK.tex and compile it with xelatex (figures from step 5).
Run: python3 code/06_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Sun_and_Rain_UK"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "$-$")
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


S = R["classes"]["share"]
lab = ["Dull", "Middling sun", "Sunny"]
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Share of the UK's land in each of the nine classes, 1991 to 2020 (terciles of the land on each axis). "
      "If sunshine and rainfall were independent, every cell would be 11.1\\%.}\\label{tab:classes}"
      "\\begin{tabular}{lrrr}\\toprule & " + " & ".join(lab) + "\\\\\\midrule\n" +
      "".join(f"{['Dry', 'Middling rain', 'Wet'][r]} & " + " & ".join(f"{S[r][c] * 100:.1f}\\%" for c in range(3)) + "\\\\\n" for r in (2, 1, 0)) +
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for r in R["regions"]:
    nm = ("\\textbf{" + tex(r["name"]) + "}") if r["level"] == "nation" else ("\\quad " + tex(r["name"]))
    rows += f"{nm} & {r['area_km2']:,} & {r['sun6190']:,.0f} & {r['sun']:,.0f} & +{r['sun_chg_pct']:.1f} & {r['rain6190']:,.0f} & {r['rain']:,.0f} & +{r['rain_chg_pct']:.1f}\\\\\n"
    if r["name"] == "Northern Ireland": rows += "\\midrule\n"
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Mean annual sunshine (hours) and rainfall (mm) of the 1 km squares of each nation and English region, "
      "1961 to 1990 and 1991 to 2020, with percentage change.}\\label{tab:regions}"
      "\\begin{tabular}{lrrrrrrr}\\toprule & Area & \\multicolumn{3}{c}{Sunshine (h)} & \\multicolumn{3}{c}{Rainfall (mm)}\\\\"
      " & km\\textsuperscript{2} & 1961 to 90 & 1991 to 2020 & \\% & 1961 to 90 & 1991 to 2020 & \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
T = R["towns"]
def col(lst, key): return [f"{tex(t['name'])} ({t[key]:,})" for t in lst[:8]]
cols = [col(T["sunniest"], "sun"), col(T["dullest"], "sun"), col(T["wettest"], "rain"), col(T["driest"], "rain")]
body = "".join(f"{k + 1} & " + " & ".join(c[k] for c in cols) + "\\\\\n" for k in range(8))
TT = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The sunniest, dullest, wettest and driest UK towns of 15,000 or more (GeoNames), 1991 to 2020: "
      "annual sunshine in hours and rainfall in mm, the mean of the 3 km block around each town.}\\label{tab:towns}"
      "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{rllll}\\toprule & Sunniest & Dullest & Wettest & Driest\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_CLASSES}}", TC).replace("{{TABLE_REGIONS}}", TR).replace("{{TABLE_TOWNS}}", TT)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print("\n".join(l for l in open(os.path.join(OUT, NAME + ".log"), errors="ignore") if l.startswith("!"))[:2000])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
os.remove(os.path.join(OUT, NAME + ".pdf"))
print("paper written", r.returncode)
