"""Step 3. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json, so the page cannot drift from the
analysis. Facts the template states in words are checked against the data below. The results and the grid window are
embedded; the grids (data/grid/*.png), towns and place names are fetched by the page.
Run: python3 code/03_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
GM = json.load(open(os.path.join(ROOT, "data", "grid", "meta.json")))


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "−")
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


def check():
    """Facts the page, paper and blog state in words."""
    U = R["uk"]
    assert U["sunniest"]["near"] == "Dungeness" and U["dullest"]["region"] == "Scotland"
    assert abs(U["dullest"]["e_km"] - 216.6) < 1 and abs(U["dullest"]["n_km"] - 771.3) < 1  # Ben Nevis summit, NN 166 712
    assert U["wettest"]["near"] == "Rosthwaite" and U["wettest"]["county"] == "Cumberland"  # Borrowdale
    assert U["driest_other"]["county"] == "Kent" and U["driest_other"]["near"] == "Bay View" and U["driest_other"]["rain"] < 500  # Isle of Sheppey
    assert U["driest"]["county"] == "Redcar and Cleveland" and U["driest"]["neighbours_mean"] > U["driest"]["rain"] + 80
    C = R["classes"]
    assert [x["region"] for x in C["sunny_dry"]["top_regions"][:3]] == ["East of England", "South East", "East Midlands"]
    assert C["dull_wet"]["top_regions"][0]["region"] == "Scotland"
    assert [x["county"] for x in C["sunny_wet"]["top_counties"][:4]] == ["Cornwall", "Devon", "Carmarthenshire", "Pembrokeshire"]
    assert [x["county"] for x in C["dull_dry"]["top_counties"][:2]] == ["Highland", "Moray"]
    TC = R["town_classes"]
    assert TC["sunny_wet"]["biggest"][0]["name"] == "Swansea" and [x["name"] for x in TC["dull_dry"]["biggest"]] == ["Inverness"]
    assert {"Rochdale", "Greenock", "Rossendale"} <= {x["name"] for x in TC["dull_wet"]["biggest"]}
    assert "London" in [x["name"] for x in TC["sunny_dry"]["biggest"]]
    assert R["coast"]["top1_regions"][0]["region"] == "South East"
    N = R["nation"]
    assert max(N, key=lambda n: N[n]["sun_chg_pct"]) == "England" and min(N, key=lambda n: N[n]["sun_chg_pct"]) == "Northern Ireland"
    assert R["region_rank"]["sun_chg"][:2] == ["North East", "East Midlands"]
    assert R["regions"][4]["name"] == "North East" and R["regions"][7]["name"] == "East Midlands"
    assert [t["name"] for t in R["towns"]["gained"][:3]] == ["Ashington", "Blyth", "Bedlington"]
    c250 = R["towns"]["cities250k"]
    assert len(c250) == 30 and c250[13]["name"] == "Sheffield" and c250[0]["name"] == "Southend-on-Sea" and c250[-1]["name"] == "Belfast"
    MS = R["month_stats"]
    assert MS["sunniest_month_uk"] == "May" and MS["dullest_month_uk"] == "December" and MS["wettest_month_uk"] == "December"
    assert MS["dec_sunniest"]["near"] == "Ventnor" and MS["dec_dullest"]["county"] == "Shetland Islands"
    ws = MS["wettest_month_share"]
    assert sorted(ws, key=lambda k: -ws[k])[:4] == ["December", "October", "November", "January"]
    assert R["pleasant"]["warmest_july"]["region"] == "London"
    T = R["towns"]
    assert [t["name"] for t in T["sunniest"][:3]] == ["Folkestone", "Sandown", "Dover"]
    assert T["dullest"][0]["name"] == "Fort William" == T["wettest"][0]["name"] and T["wettest"][1]["name"] == "Rhondda"
    assert T["driest"][0]["name"] == "Southend-on-Sea" and R["os_towns"]["sunniest"][0]["name"] == "Ventnor"
    assert R["uk"]["driest_other"]["rain"] < 500


if __name__ == "__main__":
    check()
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    slim = {k: v for k, v in R.items() if k not in ("os_towns",)}
    html = html.replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*GRIDMETA*/", json.dumps({k: GM[k] for k in ("x0_km", "y_top_km", "width", "height")}))
    import pandas as pd
    T = pd.read_csv(os.path.join(ROOT, "data", "towns.csv"))
    want = ["London", "Birmingham", "Manchester", "Leeds", "Newcastle upon Tyne", "Glasgow", "Edinburgh", "Aberdeen", "Inverness", "Fort William",
            "Cardiff", "Swansea", "Plymouth", "Norwich", "Belfast", "Derry", "Southampton", "Dover", "Penzance", "Lerwick", "Stornoway",
            "Liverpool", "Kingston upon Hull", "Carlisle", "Aberystwyth", "Oban", "Ventnor"]
    cities = []
    for nm in want:
        m = T[T.name == nm].sort_values("source")
        assert len(m), nm
        r = m.iloc[0]; cities.append([nm.replace(" upon Tyne", "").replace("Kingston upon Hull", "Hull"), round(r.e / 1000, 1), round(r.n / 1000, 1)])
    html = html.replace("/*CITIES*/", json.dumps(cities))
    assert "{{" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    # strings the script writes into the page
    js = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    for q in re.findall(r'"([^"\n]{12,})"|`([^`]{12,})`', js):
        for t in q:
            assert "—" not in t and "–" not in t, t
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
