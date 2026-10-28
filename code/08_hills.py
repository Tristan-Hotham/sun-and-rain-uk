"""Hill shading for the interactive map: a 500 m shaded-relief layer on the page grid.

Elevation: AWS Terrain Tiles (Mapzen/Tilezen terrarium, zoom 10, about 100 m),
sampled at 250 m on the British National Grid and averaged to 500 m.
Output: data/grid/hill.png, greyscale plus alpha, twice the page grid in each
direction. White is flat ground; darker is slopes turned away from a light in the
north west. Sea and land outside the HadUK grid are transparent. The page lays
it over the colours with a multiply blend, so its strength is a CSS opacity.
"""
import json, os, sys
import numpy as np
from PIL import Image
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, "/home/claude/hist/within-sight/code")
from dem import DEM  # noqa: E402

GM = json.load(open(os.path.join(ROOT, "data", "grid", "meta.json")))
W, H, X0, YT = GM["width"], GM["height"], GM["x0_km"] * 1000.0, GM["y_top_km"] * 1000.0
F = 4            # 250 m samples
OUT = 2          # 500 m output
dem = DEM()
tr = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

step = 1000.0 / F
xs = X0 + (np.arange(W * F) + 0.5) * step
elev = np.zeros((H * OUT, W * OUT), np.float32)
CH = 40  # page rows per chunk
for j0 in range(0, H, CH):
    j1 = min(H, j0 + CH)
    ys = YT - (np.arange(j0 * F, j1 * F) + 0.5) * step
    E, N = np.meshgrid(xs, ys)
    lon, lat = tr.transform(E.ravel(), N.ravel())
    z = dem.elev(np.asarray(lat), np.asarray(lon)).reshape(E.shape)
    z = np.maximum(z, 0)
    b = F // OUT
    z = z.reshape((j1 - j0) * OUT, b, W * OUT, b).mean(axis=(1, 3))
    elev[j0 * OUT:j1 * OUT] = z
print("elevation", float(elev.max()))

# shaded relief, several lights from the north west quarter, 5x vertical exaggeration
cell = 1000.0 / OUT
zf = 5.0
gy, gx = np.gradient(elev * zf, cell)      # rows run south, so gy is d/d(south)
dzdx, dzdy = gx, -gy                       # east, north
slope = np.arctan(np.hypot(dzdx, dzdy))
aspect = np.arctan2(-dzdx, -dzdy)          # direction the slope faces, from north, clockwise
alt = np.radians(45)
shade = np.zeros_like(elev)
for az, w in ((315, .6), (270, .2), (0, .2)):
    a = np.radians(az)
    shade += w * (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(a - aspect))
flat = np.sin(alt)
v = np.clip(shade / flat, 0, 1) ** 1.6
L = (25 + 230 * v).astype(np.uint8)

land = np.asarray(Image.open(os.path.join(ROOT, "data", "grid", "ann9120.png")).convert("RGBA"))[..., 0] > 0
land2 = np.repeat(np.repeat(land, OUT, 0), OUT, 1)
A = np.where(land2, 255, 0).astype(np.uint8)
L[~land2] = 255
Image.fromarray(np.dstack([L, A]), "LA").save(os.path.join(ROOT, "data", "grid", "hill.png"), optimize=True)
print("hill.png", os.path.getsize(os.path.join(ROOT, "data", "grid", "hill.png")))
