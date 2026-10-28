"""Step 1. Read the HadUK-Grid 1 km normals in place and write the page's compact grids, place lists and tables.

Writes (nothing here is a full-resolution copy of the NetCDF files; the page grids are 8-bit quantised PNGs):
  data/grid/ann9120.png   annual 1991 to 2020: R sunshine, G rainfall, B mean daily maximum temperature
  data/grid/ann6190.png   annual 1961 to 1990: R sunshine, G rainfall
  data/grid/change.png    1961 to 1990 to 1991 to 2020: R sunshine change %, G rainfall change %
  data/grid/m01.png ... m12.png  monthly 1991 to 2020: R sunshine, G rainfall, B maximum temperature
  data/grid/regions.png   region code of every land cell (see data/regions_key.json)
  data/grid/meta.json     crop window and decoding constants used by the page
  data/coast_bng.json     Natural Earth land outside the grid (Ireland, France), in BNG km, for context
  data/places_search.json OS Open Names cities, towns and villages, plus GeoNames Northern Ireland towns
  data/towns.csv, data/towns_page.json   climate of every GeoNames UK town of 15,000+ and every OS Open Names town
  data/cells_5km.csv      5 km averages of every layer, for reuse
Run: python3 code/01_prepare.py
"""
import io, json, os, zipfile
import numpy as np, pandas as pd
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from pyproj import Transformer
import haduk as H

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
OSN = os.environ.get("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
GEON = os.environ.get("GEONAMES", "/home/claude/hist/_data13/cities15000.zip")
NE = os.environ.get("NE_DIR", "/home/claude/hist/_data3/ne/geojson")
G = os.path.join(ROOT, "data", "grid"); os.makedirs(G, exist_ok=True)
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

L = H.all_layers()
SA, RA = L[("sun", "ann", "9120")], L[("rainfall", "ann", "9120")]
SA6, RA6 = L[("sun", "ann", "6190")], L[("rainfall", "ann", "6190")]
SM, RM, TM = L[("sun", "mon", "9120")], L[("rainfall", "mon", "9120")], L[("tasmax", "mon", "9120")]
land = ~np.isnan(SA)
for a in (RA, SA6, RA6, SM[0], RM[0], TM[0]):
    assert (~np.isnan(a) == land).all()
TA = TM.mean(0)
print("land cells", land.sum())

# crop window (with a 2 km margin)
rows, cols = np.where(land)
r0, r1, c0, c1 = rows.min() - 2, rows.max() + 3, cols.min() - 2, cols.max() + 3
W, Hh = c1 - c0, r1 - r0
win = lambda a: np.flipud(a[r0:r1, c0:c1])   # image row 0 = north


def png(name, chans):
    img = np.zeros((Hh, W, 3), np.uint8)
    for i, c in enumerate(chans):
        if c is not None:
            img[..., i] = np.where(win(land), win(np.nan_to_num(c)), 0).astype(np.uint8)
    Image.fromarray(img, "RGB").save(os.path.join(G, name), optimize=True)


png("ann9120.png", [H.q_sun_a(SA), H.q_rain_a(RA), H.q_tmax(TA)])
png("ann6190.png", [H.q_sun_a(SA6), H.q_rain_a(RA6), None])
dS, dR = (SA / SA6 - 1) * 100, (RA / RA6 - 1) * 100
png("change.png", [H.q_change(dS), H.q_change(dR), None])
for m in range(12):
    png(f"m{m + 1:02d}.png", [H.q_sun_m(SM[m]), H.q_rain_m(RM[m]), H.q_tmax(TM[m])])

# ---- regions: Northern Ireland is the land component containing Belfast (plus nearby islets); elsewhere the region
# of the nearest OS Open Names populated place (English regions, Scotland, Wales).
osn = pd.read_csv(OSN, sep="\t", dtype=str, keep_default_na=False)
for c in ("x", "y", "lat", "lon"): osn[c] = osn[c].astype(float)
# English form first where OS gives a Gaelic or Welsh name plus an English one; the other form is kept for search
eng = (osn.lang2 == "eng") & osn.lang1.isin(["gla", "cym"])
osn["show"] = np.where(eng, osn.name2, osn.name1)
osn["alt"] = np.where(eng, osn.name1, osn.name2)
osn["cty"] = [(c or d).split(" - ")[-1] for c, d in zip(osn.county, osn.district)]
pp = osn[osn.type == "populatedPlace"].reset_index(drop=True)
lab, nlab = ndimage.label(land)
_bx, _by = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform(-5.93, 54.597)  # Belfast
bel = lab[int(_by / 1000 - H.Y0), int(_bx / 1000 - H.X0)]
assert bel > 0
ni = lab == bel
dist_ni, idx_ni = ndimage.distance_transform_edt(~ni, return_indices=True)
yy, xx = np.where(land)
cx, cy = (xx + H.X0 + .5) * 1000, (yy + H.Y0 + .5) * 1000
tree = cKDTree(pp[["x", "y"]].values)
dgb, ig = tree.query(np.c_[cx, cy])
is_ni = ni[yy, xx] | ((dist_ni[yy, xx] < dgb / 1000) & (dist_ni[yy, xx] < 15))
REG = ["North East", "North West", "Yorkshire and the Humber", "East Midlands", "West Midlands", "East of England",
       "London", "South East", "South West", "Wales", "Scotland", "Northern Ireland"]
NATION = {r: ("England" if i < 9 else r) for i, r in enumerate(REG)}
regname = np.where(is_ni, "Northern Ireland", pp.region.values[ig])
regname = np.where(regname == "Eastern", "East of England", regname)
bad = set(regname) - set(REG)
assert not bad, bad
code = np.zeros(land.shape, np.uint8)
code[yy, xx] = [REG.index(r) + 1 for r in regname]
Image.fromarray(win(code), "L").save(os.path.join(G, "regions.png"), optimize=True)
json.dump({"codes": REG, "nation": NATION}, open(os.path.join(ROOT, "data", "regions_key.json"), "w"), indent=1)

meta = {"x0_km": int(c0 + H.X0), "y_top_km": int(r1 + H.Y0), "width": int(W), "height": int(Hh),
        "note": "pixel (i, j): easting = x0_km + i + 0.5 km, northing = y_top_km - j - 0.5 km",
        "decode": {"sun_m": "(v-1)*1.2", "rain_m": "exp(ln15+(v-1)/254*(ln800-ln15))", "tmax": "(v-1)/8-5",
                   "sun_a": "600+(v-1)*6", "rain_a": "exp(ln400+(v-1)/254*(ln6000-ln400))", "change": "(v-127)/4"},
        "files": ["ann9120.png", "ann6190.png", "change.png", "regions.png"] + [f"m{m:02d}.png" for m in range(1, 13)]}
json.dump(meta, open(os.path.join(G, "meta.json"), "w"), indent=1)

# quantisation error check (reported in results)
def deq_err():
    e = {}
    e["sun_a"] = float(np.nanmax(np.abs(600 + (H.q_sun_a(SA) - 1) * 6 - SA)))
    e["rain_a_pct"] = float(np.nanmax(np.abs(np.exp(H.RAIN_A[0] + (H.q_rain_a(RA) - 1) / 254 * (H.RAIN_A[1] - H.RAIN_A[0])) / RA - 1)) * 100)
    e["sun_m"] = float(np.nanmax(np.abs((H.q_sun_m(SM) - 1) * 1.2 - SM)))
    e["rain_m_pct"] = float(np.nanmax(np.abs(np.exp(H.RAIN_M[0] + (H.q_rain_m(RM) - 1) / 254 * (H.RAIN_M[1] - H.RAIN_M[0])) / RM - 1)) * 100)
    e["tmax"] = float(np.nanmax(np.abs((H.q_tmax(TM) - 1) / 8 - 5 - TM)))
    return e
json.dump(deq_err(), open(os.path.join(ROOT, "data", "grid", "quant_err.json"), "w"))

# ---- context coastline: Natural Earth land, projected to BNG km, clipped to the window, simplified
from shapely.geometry import shape, box, mapping
from shapely.ops import transform as shp_transform
tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
ne = json.load(open(os.path.join(NE, "ne_10m_land.geojson")))
clip = box(-6.5, 49.0, 5.0, 61.5)
win_bng = box((c0 + H.X0) * 1000 - 150000, (r0 + H.Y0) * 1000 - 50000, (c1 + H.X0) * 1000 + 150000, (r1 + H.Y0) * 1000 + 50000)
feats = []
for f in ne["features"]:
    g = shape(f["geometry"])
    if not g.intersects(box(-12, 48, 5, 62)): continue
    g = g.intersection(box(-12, 48, 5, 62))
    g = shp_transform(lambda x, y, z=None: tr.transform(x, y), g).intersection(win_bng).simplify(400)
    if g.is_empty: continue
    g = shp_transform(lambda x, y, z=None: (np.round(np.asarray(x) / 1000, 1), np.round(np.asarray(y) / 1000, 1)), g)
    feats.append(mapping(g))
json.dump(feats, open(os.path.join(ROOT, "data", "coast_bng.json"), "w"), separators=(",", ":"))


# ---- values at a point: mean of land cells within 1.5 km (the 3 by 3 block around it); falls back to the nearest land cell
lx, ly = np.where(land.T)  # x index, y index of land cells
ltree = cKDTree(np.c_[lx, ly])


def at(xm, ym):
    i = int(np.floor(xm / 1000 - H.X0)); j = int(np.floor(ym / 1000 - H.Y0))
    blk = [(a, b) for a in range(i - 1, i + 2) for b in range(j - 1, j + 2) if 0 <= a < H.NX and 0 <= b < H.NY and land[b, a]]
    if not blk:
        d, k = ltree.query([i, j]); blk = [(lx[k], ly[k])]
    A = np.array(blk); ii, jj = A[:, 0], A[:, 1]
    o = {"sun": SA[jj, ii].mean(), "rain": RA[jj, ii].mean(), "sun6190": SA6[jj, ii].mean(), "rain6190": RA6[jj, ii].mean(),
         "region": REG[int(np.bincount(code[jj, ii]).argmax()) - 1]}
    for m in range(12):
        o[f"sun_{MON[m]}"] = SM[m, jj, ii].mean(); o[f"rain_{MON[m]}"] = RM[m, jj, ii].mean(); o[f"tmax_{MON[m]}"] = TM[m, jj, ii].mean()
    return o


# GeoNames UK towns of 15,000 or more (not sections of other places)
with zipfile.ZipFile(GEON) as z:
    gn = pd.read_csv(io.BytesIO(z.read("cities15000.txt")), sep="\t", header=None, dtype=str, keep_default_na=False, quoting=3)
gn.columns = ["id", "name", "ascii", "alt", "lat", "lon", "fcl", "fcode", "cc", "cc2", "a1", "a2", "a3", "a4", "pop", "elev", "dem", "tz", "mod"]
gn = gn[(gn.cc == "GB") & (gn.fcode != "PPLX")].copy()
gn = gn[~gn.name.isin(["Londonderry County Borough"])]  # duplicate of Derry
for c in ("lat", "lon", "pop"): gn[c] = gn[c].astype(float)
gx, gy = tr.transform(gn.lon.values, gn.lat.values); gn["x"], gn["y"] = gx, gy
gn = gn[(gn.x > (c0 + H.X0) * 1000) & (gn.y > (r0 + H.Y0) * 1000)]

rows_out = []
for _, r in gn.iterrows():
    rows_out.append({"name": r["name"], "source": "GeoNames", "kind": "Town 15,000+", "county": "", "population": int(r["pop"]),
                     "lat": round(r.lat, 5), "lon": round(r.lon, 5), "e": round(r.x), "n": round(r.y), **at(r.x, r.y)})
ost = osn[(osn.type == "populatedPlace") & osn.local_type.isin(["City", "Town"])]
for _, r in ost.iterrows():
    rows_out.append({"name": r.show, "source": "OS Open Names", "kind": r.local_type, "county": r.cty, "population": None,
                     "lat": r.lat, "lon": r.lon, "e": round(r.x), "n": round(r.y), **at(r.x, r.y)})
T = pd.DataFrame(rows_out)
num = T.select_dtypes("float").columns
T[num] = T[num].round(1)
T["nation"] = T.region.map(NATION)
T.to_csv(os.path.join(ROOT, "data", "towns.csv"), index=False)
print("towns", (T.source == "GeoNames").sum(), (T.source != "GeoNames").sum())

# page version: compact rows
P = []
for _, r in T.iterrows():
    P.append([r["name"], r.county if isinstance(r.county, str) else "", 1 if r.source == "GeoNames" else 0, int(r.population) if pd.notna(r.population) else 0, round(r.e / 1000, 1), round(r.n / 1000, 1),
              REG.index(r.region), round(r.sun), round(r.rain), round(r.sun6190), round(r.rain6190)]
             + [round(r[f"sun_{m}"]) for m in MON] + [round(r[f"rain_{m}"]) for m in MON] + [round(r[f"tmax_{m}"], 1) for m in MON])
json.dump({"cols": ["name", "county", "big", "pop", "e_km", "n_km", "region", "sun", "rain", "sun6190", "rain6190", "sun12...", "rain12...", "tmax12..."],
           "rows": P}, open(os.path.join(ROOT, "data", "towns_page.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# place search list: OS cities, towns, villages (GB) and GeoNames Northern Ireland towns
S = osn[(osn.type == "populatedPlace") & osn.local_type.isin(["City", "Town", "Village"])]
srch = [[r.show, r.cty, round(r.x / 1000, 2), round(r.y / 1000, 2), {"City": 2, "Town": 1, "Village": 0}[r.local_type]] + ([r.alt] if r.alt else []) for r in S.itertuples()]
for r in gn[gn.a1 == "NIR"].itertuples():
    srch.append([r.name, "Northern Ireland", round(r.x / 1000, 2), round(r.y / 1000, 2), 1])
json.dump(srch, open(os.path.join(ROOT, "data", "places_search.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("search places", len(srch))

# 5 km averages for reuse
k = 5
ny5, nx5 = H.NY // k, H.NX // k
def agg(a):
    b = a[:ny5 * k, :nx5 * k].reshape(ny5, k, nx5, k)
    with np.errstate(invalid="ignore"):
        return np.nanmean(b, axis=(1, 3))
import warnings
warnings.simplefilter("ignore", RuntimeWarning)
cnt = land[:ny5 * k, :nx5 * k].reshape(ny5, k, nx5, k).sum(axis=(1, 3))
jj, ii = np.where(cnt > 0)
C = pd.DataFrame({"e_km": H.X0 + ii * k + k / 2, "n_km": H.Y0 + jj * k + k / 2, "land_km2": cnt[jj, ii]})
reg5 = np.zeros((ny5, nx5), int)
cb = code[:ny5 * k, :nx5 * k].reshape(ny5, k, nx5, k).transpose(0, 2, 1, 3).reshape(ny5, nx5, k * k)
for j, i in zip(jj, ii):
    v = cb[j, i]; v = v[v > 0]; reg5[j, i] = np.bincount(v).argmax()
C["region"] = [REG[reg5[j, i] - 1] for j, i in zip(jj, ii)]
for nm, a in (("sun_1991_2020", SA), ("rain_1991_2020", RA), ("sun_1961_1990", SA6), ("rain_1961_1990", RA6)):
    C[nm] = agg(a)[jj, ii].round(1)
for m in range(12):
    C[f"sun_{MON[m]}"] = agg(SM[m])[jj, ii].round(1)
for m in range(12):
    C[f"rain_{MON[m]}"] = agg(RM[m])[jj, ii].round(1)
for m in range(12):
    C[f"tmax_{MON[m]}"] = agg(TM[m])[jj, ii].round(2)
C.to_csv(os.path.join(ROOT, "data", "cells_5km.csv"), index=False)
print("5 km cells", len(C))
for f in sorted(os.listdir(G)):
    print(f, os.path.getsize(os.path.join(G, f)))
