"""Step 7. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 code/07_release.py
"""
import importlib.util, json, os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "03_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
b.check()
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--"): assert bad not in vis, bad
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
U = R["uk"]
meta = dict(
    title="Sun and rain: the UK's sunshine against its rainfall",
    slug="sun-and-rain-uk",
    excerpt=(f"Every square kilometre of the UK by sunshine and rainfall at once: sunny and dry, dull and wet, and the rare places that are both sunny and wet. "
             f"Since 1961 to 1990 the country has become {U['sun_chg_pct']:.1f}% sunnier and {U['rain_chg_pct']:.1f}% wetter."),
    seo_description=f"An interactive 1 km map of UK sunshine against rainfall: from {U['sun_max']:,.0f} hours at Dungeness to {U['sun_min']:,.0f} on Ben Nevis, then and now.",
    tags=["climate", "sunshine", "rainfall", "Met Office", "HadUK-Grid", "maps", "UK weather", "data"],
    header_alt=(f"Title card reading 'Sun and rain' in marigold and teal on pale paper, with a nine-colour key and a map of the UK at 1 km: marigold across the "
                f"south and east of England, teal over the Scottish Highlands and Welsh hills, aubergine in Cornwall and Devon. Text: {U['sun_max']:,.0f} hours of sun a year "
                f"at Dungeness, {U['sun_min']:,.0f} on Ben Nevis, and the UK is {U['sun_chg_pct']:.1f}% sunnier than it was in 1961 to 1990."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in ("—", "–", "--"): assert bad not in str(v)
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Sun_and_Rain_UK"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("Spearman's $\\rho$", "Spearman's rho").replace("$-$", "-").replace("``", "\"").replace("''", "\"")
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="Sun and Rain: The United Kingdom's Sunshine Against Its Rainfall at 1 km, 1961 to 2020",
    description_html=(f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/sun-and-rain-uk/. Data and code: https://github.com/Tristan-Hotham/sun-and-rain-uk. "
                      "Blog post: to follow.</p><p>Contains Met Office data © Crown copyright 2026 and OS data © Crown copyright and database right 2026, "
                      "Open Government Licence v3. The derived data files are released under the Open Government Licence v3; the paper and other material under CC BY 4.0; the code under MIT.</p>"),
    keywords=["sunshine", "rainfall", "climate normals", "HadUK-Grid", "bivariate map", "United Kingdom", "brightening", "coastal climate", "Met Office", "open data"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/sun-and-rain-uk", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/sun-and-rain-uk/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://catalogue.ceda.ac.uk/uuid/789b3065d74a4c948ab05d33556c86d0", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://download.geonames.org/export/dump/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
for f in os.listdir(Z):
    if f != "meta.json": os.remove(os.path.join(Z, f))
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["towns.csv", "regions.csv", "coast_bands.csv", "cells_5km.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "sun-and-rain-uk_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data", "data/grid"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"sun-and-rain-uk/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"sun-and-rain-uk/{f}")
words = len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t, flags=re.S)).split())
print("release files written; post words:", words)
