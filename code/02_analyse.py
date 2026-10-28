"""Step 2. Every statistic used on the page, in the paper, the blog and the collage, written to data/results.json.
Also writes data/regions.csv (region and nation summaries) and data/coast_bands.csv.
Reads the HadUK-Grid files in place (see haduk.py) and the outputs of step 1.
Run: python3 code/02_analyse.py
"""
import json, os, warnings
import numpy as np, pandas as pd
from PIL import Image
from scipy import ndimage, stats
from scipy.spatial import cKDTree
import haduk as H
import palette

warnings.simplefilter("ignore", RuntimeWarning)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
OSN = os.environ.get("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
SEAS = {"winter": [11, 0, 1], "spring": [2, 3, 4], "summer": [5, 6, 7], "autumn": [8, 9, 10]}

L = H.all_layers()
SA, RA = L[("sun", "ann", "9120")], L[("rainfall", "ann", "9120")]
SA6, RA6 = L[("sun", "ann", "6190")], L[("rainfall", "ann", "6190")]
SM, RM, TM = L[("sun", "mon", "9120")], L[("rainfall", "mon", "9120")], L[("tasmax", "mon", "9120")]
land = ~np.isnan(SA)
gm = json.load(open(os.path.join(ROOT, "data", "grid", "meta.json")))
key = json.load(open(os.path.join(ROOT, "data", "regions_key.json")))
REG, NATION = key["codes"], key["nation"]
# regions.png is in the cropped, north-up window; put it back on the full grid
rimg = np.array(Image.open(os.path.join(ROOT, "data", "grid", "regions.png")))
code = np.zeros(land.shape, np.uint8)
c0 = gm["x0_km"] - H.X0; r1 = gm["y_top_km"] - H.Y0
code[r1 - gm["height"]:r1, c0:c0 + gm["width"]] = np.flipud(rimg)
assert ((code > 0) == land).all()
yy, xx = np.where(land)
s, r, s6, r6 = SA[land], RA[land], SA6[land], RA6[land]
reg = np.array(REG)[code[land] - 1]
nat = np.array([NATION[x] for x in REG])[code[land] - 1]
N = int(land.sum())
R = {}
rd = lambda v, k=1: float(round(float(v), k))

# ---- places for naming cells
osn = pd.read_csv(OSN, sep="\t", dtype=str, keep_default_na=False)
for c in ("x", "y"): osn[c] = osn[c].astype(float)
pp = osn[osn.type == "populatedPlace"].reset_index(drop=True)
tree_all = cKDTree(pp[["x", "y"]].values)
tw = pp[pp.local_type.isin(["City", "Town", "Village"])].reset_index(drop=True)
_eng = (tw.lang2 == "eng") & tw.lang1.isin(["gla", "cym"])
tw["name1"] = np.where(_eng, tw.name2, tw.name1)
tw["county"] = [(c or d).split(" - ")[-1] for c, d in zip(tw.county, tw.district)]
tree_tw = cKDTree(tw[["x", "y"]].values)
T = pd.read_csv(os.path.join(ROOT, "data", "towns.csv"))
ni_t = T[(T.region == "Northern Ireland")]
tree_ni = cKDTree(ni_t[["e", "n"]].values)


def name_cell(i, j):
    """Nearest OS Open Names village, town or city to the centre of cell (x index i, y index j)."""
    x, y = (i + H.X0 + .5) * 1000, (j + H.Y0 + .5) * 1000
    regn = REG[code[j, i] - 1]
    if regn == "Northern Ireland":
        d, k = tree_ni.query([x, y]); t = ni_t.iloc[k]
        return {"near": t["name"], "county": "Northern Ireland", "km": rd(d / 1000), "e_km": rd(x / 1000), "n_km": rd(y / 1000), "region": regn}
    d, k = tree_tw.query([x, y]); t = tw.iloc[k]
    return {"near": t.name1, "county": t.county or t.district, "km": rd(d / 1000), "e_km": rd(x / 1000), "n_km": rd(y / 1000), "region": regn}


# ---- 1. headline means
R["meta"] = {"cells": N, "area_km2": N, "periods": ["1961 to 1990", "1991 to 2020"], "version": "HadUK-Grid v1.3.2.ceda",
             "quant_err": json.load(open(os.path.join(ROOT, "data", "grid", "quant_err.json")))}
R["uk"] = {"sun": rd(s.mean(), 0), "rain": rd(r.mean(), 0), "sun6190": rd(s6.mean(), 0), "rain6190": rd(r6.mean(), 0),
           "sun_chg_pct": rd((s.mean() / s6.mean() - 1) * 100), "rain_chg_pct": rd((r.mean() / r6.mean() - 1) * 100),
           "sun_chg_h": rd(s.mean() - s6.mean(), 0), "rain_chg_mm": rd(r.mean() - r6.mean(), 0),
           "sun_min": rd(s.min(), 0), "sun_max": rd(s.max(), 0), "rain_min": rd(r.min(), 0), "rain_max": rd(r.max(), 0),
           "sun_ratio": rd(s.max() / s.min(), 1), "rain_ratio": rd(r.max() / r.min(), 1),
           "sun_p10": rd(np.percentile(s, 10), 0), "sun_p90": rd(np.percentile(s, 90), 0),
           "rain_p10": rd(np.percentile(r, 10), 0), "rain_p90": rd(np.percentile(r, 90), 0),
           "sun_median": rd(np.median(s), 0), "rain_median": rd(np.median(r), 0)}
for k, a, f in (("sunniest", SA, np.nanargmax), ("dullest", SA, np.nanargmin), ("wettest", RA, np.nanargmax), ("driest", RA, np.nanargmin)):
    j, i = np.unravel_index(f(a), a.shape)
    R["uk"][k] = {**name_cell(i, j), "sun": rd(SA[j, i], 0), "rain": rd(RA[j, i], 0)}
# the driest square is a lone coastal cell at the mouth of the Tees; also report the driest square more than 50 km from it
_d = R["uk"]["driest"]
far = np.hypot(xx + H.X0 + .5 - _d["e_km"], yy + H.Y0 + .5 - _d["n_km"]) > 50
k = np.argmin(np.where(far, r, np.inf)); R["uk"]["driest_other"] = {**name_cell(xx[k], yy[k]), "sun": rd(s[k], 0), "rain": rd(r[k], 0)}
nb = RA[int(_d["n_km"] - .5 - H.Y0) - 1:int(_d["n_km"] - .5 - H.Y0) + 2, int(_d["e_km"] - .5 - H.X0) - 1:int(_d["e_km"] - .5 - H.X0) + 2]
R["uk"]["driest"]["neighbours_mean"] = rd(np.nanmean(nb), 0)
rho = stats.spearmanr(s, r)[0]
R["uk"]["rho_sun_rain"] = rd(rho, 2)
R["uk"]["rho_sun_rain_6190"] = rd(stats.spearmanr(s6, r6)[0], 2)

# ---- 2. regions and nations
rows = []
for grp, lab in (("nation", nat), ("region", reg)):
    for g in (["England", "Scotland", "Wales", "Northern Ireland"] if grp == "nation" else REG):
        m = lab == g
        if grp == "region" and NATION[g] != "England": continue
        rows.append({"level": grp, "name": g, "area_km2": int(m.sum()), "sun": rd(s[m].mean(), 0), "rain": rd(r[m].mean(), 0),
                     "sun6190": rd(s6[m].mean(), 0), "rain6190": rd(r6[m].mean(), 0),
                     "sun_chg_pct": rd((s[m].mean() / s6[m].mean() - 1) * 100), "rain_chg_pct": rd((r[m].mean() / r6[m].mean() - 1) * 100),
                     "sun_chg_h": rd(s[m].mean() - s6[m].mean(), 0),
                     "share_sunnier": rd((s[m] > s6[m]).mean(), 3), "share_wetter": rd((r[m] > r6[m]).mean(), 3)})
RG = pd.DataFrame(rows)
RG.to_csv(os.path.join(ROOT, "data", "regions.csv"), index=False)
R["regions"] = rows
eng_reg = RG[RG.level == "region"]
R["region_rank"] = {"sun": list(eng_reg.sort_values("sun", ascending=False).name), "sun_chg": list(eng_reg.sort_values("sun_chg_pct", ascending=False).name)}
NR = RG[RG.level == "nation"].set_index("name")
R["nation"] = {n: NR.loc[n].drop("level").to_dict() for n in NR.index}

# ---- 3. bivariate classes with tercile breaks (and quartiles for the 4 by 4 option)
def breaks(v, n): return [rd(np.percentile(v, 100 * k / n), 0) for k in range(1, n)]
R["breaks"] = {"sun3": breaks(s, 3), "rain3": breaks(r, 3), "sun4": breaks(s, 4), "rain4": breaks(r, 4)}
b_s, b_r = R["breaks"]["sun3"], R["breaks"]["rain3"]
cs, cr = np.digitize(s, b_s), np.digitize(r, b_r)
joint = np.zeros((3, 3))
for a in range(3):
    for b in range(3):
        joint[a, b] = ((cr == a) & (cs == b)).mean()
R["classes"] = {"share": [[rd(joint[a, b], 3) for b in range(3)] for a in range(3)], "note": "share[rain class][sun class], 0 = lowest"}
CORN = {"sunny_dry": (0, 2), "sunny_wet": (2, 2), "dull_dry": (0, 0), "dull_wet": (2, 0), "middle": (1, 1)}
for k, (a, b) in CORN.items():
    m = (cr == a) & (cs == b)
    vc = pd.Series(reg[m]).value_counts()
    R["classes"][k] = {"share": rd(m.mean(), 3), "km2": int(m.sum()),
                       "top_regions": [{"region": x, "share": rd(n / m.sum(), 3)} for x, n in vc.head(4).items()]}
R["palette"] = {"3": palette.grid(3), "4": palette.grid(4), "corners": palette.CORNERS}

# towns in classes (GeoNames 15,000+)
G = T[T.source == "GeoNames"].copy()
G["cs"] = np.digitize(G.sun, b_s); G["cr"] = np.digitize(G.rain, b_r)
R["towns_n"] = int(len(G)); R["towns_pop"] = int(G.population.sum())
R["os_towns_n"] = int((T.source != "GeoNames").sum())
R["town_classes"] = {}
for k, (a, b) in CORN.items():
    m = (G.cr == a) & (G.cs == b)
    R["town_classes"][k] = {"n": int(m.sum()), "pop_share": rd(G.population[m].sum() / G.population.sum(), 3),
                            "biggest": [{"name": x.name, "pop": int(x.population), "sun": int(round(x.sun)), "rain": int(round(x.rain))}
                                        for x in G[m].sort_values("population", ascending=False).head(6).itertuples()]}
R["town_classes"]["land_vs_people"] = "share of land vs share of people in towns of 15,000+"


def trow(x): return {"name": x["name"], "region": x["region"], "pop": int(x["population"]), "sun": int(round(x["sun"])), "rain": int(round(x["rain"])),
                     "sun6190": int(round(x["sun6190"])), "rain6190": int(round(x["rain6190"])), "sun_chg_pct": rd((x["sun"] / x["sun6190"] - 1) * 100)}


R["towns"] = {"sunniest": [trow(x) for _, x in G.sort_values("sun", ascending=False).head(10).iterrows()],
              "dullest": [trow(x) for _, x in G.sort_values("sun").head(10).iterrows()],
              "wettest": [trow(x) for _, x in G.sort_values("rain", ascending=False).head(10).iterrows()],
              "driest": [trow(x) for _, x in G.sort_values("rain").head(10).iterrows()]}
G["chg"] = G.sun / G.sun6190 - 1
R["towns"]["gained"] = [trow(x) for _, x in G.sort_values("chg", ascending=False).head(10).iterrows()]
R["towns"]["lost"] = [trow(x) for _, x in G.sort_values("chg").head(5).iterrows()]
R["towns"]["share_sunnier"] = rd((G.chg > 0).mean(), 3)
big = G[G.population >= 250000].sort_values("sun", ascending=False)
R["towns"]["cities250k"] = [trow(x) for _, x in big.iterrows()]
for nm in ["London", "Manchester", "Glasgow", "Cardiff", "Belfast", "Edinburgh", "Birmingham", "Brighton", "Bournemouth", "Fort William", "Aberdeen", "Swansea", "Plymouth", "Norwich"]:
    m = T[(T.name == nm)].sort_values("source")
    if len(m):
        x = m.iloc[0]
        R.setdefault("town_lookup", {})[nm] = {"sun": int(round(x.sun)), "rain": int(round(x.rain)), "sun6190": int(round(x.sun6190)),
                                              "rain6190": int(round(x.rain6190)), "sun_chg_pct": rd((x.sun / x.sun6190 - 1) * 100),
                                              "class": [int(np.digitize(x.rain, b_r)), int(np.digitize(x.sun, b_s))],
                                              "sun_m": [int(round(x[f"sun_{m}"])) for m in MON], "rain_m": [int(round(x[f"rain_{m}"])) for m in MON],
                                              "tmax_m": [rd(x[f"tmax_{m}"]) for m in MON]}
O = T[T.source != "GeoNames"]
R["os_towns"] = {"sunniest": [{"name": x.name, "county": x.county, "sun": int(round(x.sun))} for x in O.sort_values("sun", ascending=False).head(5).itertuples()],
                 "wettest": [{"name": x.name, "county": x.county, "rain": int(round(x.rain))} for x in O.sort_values("rain", ascending=False).head(5).itertuples()],
                 "driest": [{"name": x.name, "county": x.county, "rain": int(round(x.rain))} for x in O.sort_values("rain").head(5).itertuples()],
                 "dullest": [{"name": x.name, "county": x.county, "sun": int(round(x.sun))} for x in O.sort_values("sun").head(5).itertuples()]}

# ---- 4. then and now
d = s / s6 - 1; dr = r / r6 - 1
R["change"] = {"share_sunnier": rd((d > 0).mean(), 3), "share_sunnier5": rd((d > .05).mean(), 3), "share_duller": rd((d < 0).mean(), 3),
               "share_wetter": rd((dr > 0).mean(), 3), "share_wetter5": rd((dr > .05).mean(), 3), "share_drier": rd((dr < 0).mean(), 3),
               "sun_pct_p10": rd(np.percentile(d, 10) * 100), "sun_pct_p90": rd(np.percentile(d, 90) * 100),
               "sun_pct_max": rd(d.max() * 100), "sun_pct_min": rd(d.min() * 100),
               "rain_pct_p10": rd(np.percentile(dr, 10) * 100), "rain_pct_p90": rd(np.percentile(dr, 90) * 100),
               "sunnier_and_wetter": rd(((d > 0) & (dr > 0)).mean(), 3), "sunnier_and_drier": rd(((d > 0) & (dr < 0)).mean(), 3),
               "duller_and_wetter": rd(((d < 0) & (dr > 0)).mean(), 3), "duller_and_drier": rd(((d < 0) & (dr < 0)).mean(), 3),
               "rho_change": rd(stats.spearmanr(d, dr)[0], 2)}
j, i = np.unravel_index(np.nanargmax(SA / SA6), SA.shape); R["change"]["max_cell"] = {**name_cell(i, j), "pct": rd((SA[j, i] / SA6[j, i] - 1) * 100)}
j, i = np.unravel_index(np.nanargmin(SA / SA6), SA.shape); R["change"]["min_cell"] = {**name_cell(i, j), "pct": rd((SA[j, i] / SA6[j, i] - 1) * 100)}
# hours of sunshine above 1,600 a year: area then and now
for th in (1500, 1600, 1700):
    R["change"][f"area_over_{th}"] = [int((s6 > th).sum()), int((s > th).sum())]
# latitude bands (northings) of change
bands = []
for lo in range(0, 1250, 100):
    m = (yy + H.Y0 >= lo) & (yy + H.Y0 < lo + 100)
    if m.sum() > 500:
        bands.append({"n_from": lo, "n_to": lo + 100, "km2": int(m.sum()), "sun_chg_pct": rd((s[m].mean() / s6[m].mean() - 1) * 100),
                      "rain_chg_pct": rd((r[m].mean() / r6[m].mean() - 1) * 100), "sun": rd(s[m].mean(), 0)})
R["change"]["by_northing"] = bands
# terciles of then, used for both periods: how much land moved into the sunniest class
cs6 = np.digitize(s6, b_s)
R["change"]["top_sun_class_area"] = [int((cs6 == 2).sum()), int((cs == 2).sum())]
R["change"]["breaks_6190"] = {"sun3": breaks(s6, 3), "rain3": breaks(r6, 3)}

# ---- 5. coast: Great Britain only (Northern Ireland has a land border with cells outside the grid)
gb = land & (code != REG.index("Northern Ireland") + 1)
dist = ndimage.distance_transform_edt(gb)  # km to the nearest non-GB cell (sea), cell centres
dg = dist[gb]; sg, rg = SA[gb], RA[gb]
edges = [0, 2, 5, 10, 20, 40, 80, 200]
cb = []
for a, b in zip(edges[:-1], edges[1:]):
    m = (dg > a) & (dg <= b)
    cb.append({"from_km": a, "to_km": b, "km2": int(m.sum()), "sun": rd(sg[m].mean(), 0), "rain": rd(rg[m].mean(), 0)})
pd.DataFrame(cb).to_csv(os.path.join(ROOT, "data", "coast_bands.csv"), index=False)
top1 = sg >= np.percentile(s, 99)
top5 = sg >= np.percentile(s, 95)
R["coast"] = {"bands": cb, "sun_coast2": cb[0]["sun"], "sun_inland20": rd(sg[dg > 20].mean(), 0),
              "coast_premium_pct": rd((cb[0]["sun"] / sg[dg > 20].mean() - 1) * 100),
              "top1_within5": rd((dg[top1] <= 5).mean(), 3), "land_within5": rd((dg <= 5).mean(), 3),
              "top5_within5": rd((dg[top5] <= 5).mean(), 3),
              "top1_regions": [{"region": x, "share": rd(n / top1.sum(), 3)} for x, n in pd.Series(reg[gb[land]][top1]).value_counts().head(3).items()],
              "top1_threshold": rd(np.percentile(s, 99), 0)}
# within each nation, coast premium
R["coast"]["by_nation"] = {}
for nn in ["England", "Scotland", "Wales"]:
    mm = (nat[gb[land]] == nn)
    R["coast"]["by_nation"][nn] = {"coast2": rd(sg[mm & (dg <= 2)].mean(), 0), "inland20": rd(sg[mm & (dg > 20)].mean(), 0)}

R["coast"]["bands_nation"] = {}
for nn in ["England", "Scotland", "Wales"]:
    mm = (nat[gb[land]] == nn); out = []
    for a_, b_ in zip(edges[:-1], edges[1:]):
        q = mm & (dg > a_) & (dg <= b_)
        out.append(rd(sg[q].mean(), 0) if q.sum() >= 200 else None)
    R["coast"]["bands_nation"][nn] = out

# ---- where the rare corners are: most common counties of their squares (nearest OS village, town or city)
for k in ("sunny_wet", "dull_dry"):
    a_, b_ = CORN[k]
    m = (cr == a_) & (cs == b_)
    _, kk = tree_tw.query(np.c_[(xx[m] + H.X0 + .5) * 1000, (yy[m] + H.Y0 + .5) * 1000])
    cty = pd.Series(np.where(reg[m] == "Northern Ireland", "Northern Ireland", tw.county.values[kk])).value_counts()
    R["classes"][k]["top_counties"] = [{"county": c, "share": rd(n / m.sum(), 3)} for c, n in cty.head(5).items()]

# ---- 6. months and seasons
mon = []
for m in range(12):
    mon.append({"month": MONL[m], "sun": rd(SM[m][land].mean(), 0), "rain": rd(RM[m][land].mean(), 0), "tmax": rd(TM[m][land].mean()),
                **{f"sun_{n}": rd(SM[m][land][nat == n].mean(), 0) for n in ["England", "Scotland", "Wales", "Northern Ireland"]},
                **{f"rain_{n}": rd(RM[m][land][nat == n].mean(), 0) for n in ["England", "Scotland", "Wales", "Northern Ireland"]}})
R["months"] = mon
sunm = SM[:, land]; rainm = RM[:, land]; tm = TM[:, land]
best = sunm.argmax(0); wet = rainm.argmax(0); dry = rainm.argmin(0)
R["month_stats"] = {"sunniest_month_uk": MONL[int(np.argmax([x["sun"] for x in mon]))], "dullest_month_uk": MONL[int(np.argmin([x["sun"] for x in mon]))],
                    "wettest_month_uk": MONL[int(np.argmax([x["rain"] for x in mon]))], "driest_month_uk": MONL[int(np.argmin([x["rain"] for x in mon]))],
                    "sunniest_month_share": {MONL[k]: rd((best == k).mean(), 3) for k in range(12) if (best == k).any()},
                    "wettest_month_share": {MONL[k]: rd((wet == k).mean(), 3) for k in range(12) if (wet == k).any()},
                    "driest_month_share": {MONL[k]: rd((dry == k).mean(), 3) for k in range(12) if (dry == k).any()},
                    "dec_sun_max": rd(sunm[11].max(), 0), "dec_sun_min": rd(sunm[11].min(), 0), "jun_sun_max": rd(sunm[5].max(), 0), "jun_sun_min": rd(sunm[5].min(), 0)}
j, i = np.unravel_index(np.nanargmin(SM[11]), SA.shape); R["month_stats"]["dec_dullest"] = {**name_cell(i, j), "sun": rd(SM[11, j, i], 0)}
j, i = np.unravel_index(np.nanargmax(SM[11]), SA.shape); R["month_stats"]["dec_sunniest"] = {**name_cell(i, j), "sun": rd(SM[11, j, i], 0)}
j, i = np.unravel_index(np.nanargmax(SM[5]), SA.shape); R["month_stats"]["jun_sunniest"] = {**name_cell(i, j), "sun": rd(SM[5, j, i], 0)}
sea = {}
for k, ms in SEAS.items():
    ss = sunm[ms].sum(0); rr = rainm[ms].sum(0)
    sea[k] = {"sun": rd(ss.mean(), 0), "rain": rd(rr.mean(), 0), "sun_max": rd(ss.max(), 0), "sun_min": rd(ss.min(), 0),
              "rain_max": rd(rr.max(), 0), "rain_min": rd(rr.min(), 0), "rho": rd(stats.spearmanr(ss, rr)[0], 2)}
R["seasons"] = sea
R["seasons"]["winter_rain_share"] = rd(rainm[[11, 0, 1]].sum() / rainm.sum(), 3)
R["seasons"]["summer_sun_share"] = rd(sunm[[5, 6, 7]].sum() / sunm.sum(), 3)
# the wetter the place, the more of its rain falls in winter
wr = rainm[[11, 0, 1]].sum(0) / rainm.sum(0)
R["seasons"]["winter_share_dry_tercile"] = rd(wr[cr == 0].mean(), 3)
R["seasons"]["winter_share_wet_tercile"] = rd(wr[cr == 2].mean(), 3)

# ---- 7. pleasant months (mean daily maximum in a band; default 18 to 27 C, as in the world map)
pl = {}
for lo, hi in ((18, 27), (20, 27), (15, 25), (16, 27)):
    n = ((tm >= lo) & (tm <= hi)).sum(0)
    pl[f"{lo}_{hi}"] = {"hist": [int((n == k).sum()) for k in range(13)], "share_zero": rd((n == 0).mean(), 3), "max": int(n.max()), "mean": rd(n.mean(), 2)}
R["pleasant"] = pl
R["pleasant"]["tmax_july_max"] = rd(tm[6].max()); R["pleasant"]["tmax_july_min"] = rd(tm[6].min())
j, i = np.unravel_index(np.nanargmax(TM[6]), SA.shape); R["pleasant"]["warmest_july"] = {**name_cell(i, j), "tmax": rd(TM[6, j, i])}
R["pleasant"]["london_months_18"] = int(sum(1 for v in R["town_lookup"]["London"]["tmax_m"] if 18 <= v <= 27))

json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: R[k] for k in ("uk", "change", "coast", "month_stats", "seasons", "classes")}, indent=1)[:9000])
