"""Shared helpers: read the HadUK-Grid 1 km climate normals in place (never copied), and the page's quantisation.

HadUK-Grid v1.3.2.ceda (Met Office; Hollis, McCarthy, Kendon and Legg 2026), Open Government Licence v3.
Files are NetCDF4 (HDF5), read with h5py. The grid is the British National Grid (OSGB 1936), 1 km cells,
900 columns (eastings -200 to 700 km) by 1450 rows (northings -200 to 1250 km); row 0 is the SOUTH edge.
"""
import os
import numpy as np
import h5py

DATA = os.environ.get("HADUK_DIR", "/home/claude/hist/_data13/haduk")
FILES = {
    ("sun", "ann", "9120"): "sun_hadukgrid_uk_1km_ann-30y_199101-202012.nc",
    ("sun", "ann", "6190"): "sun_hadukgrid_uk_1km_ann-30y_196101-199012.nc",
    ("rainfall", "ann", "9120"): "rainfall_hadukgrid_uk_1km_ann-30y_199101-202012.nc",
    ("rainfall", "ann", "6190"): "rainfall_hadukgrid_uk_1km_ann-30y_196101-199012.nc",
    ("sun", "mon", "9120"): "sun_hadukgrid_uk_1km_mon-30y_199101-202012.nc",
    ("rainfall", "mon", "9120"): "rainfall_hadukgrid_uk_1km_mon-30y_199101-202012.nc",
    ("tasmax", "mon", "9120"): "tasmax_hadukgrid_uk_1km_mon-30y_199101-202012.nc",
}
X0, Y0, NX, NY = -200, -200, 900, 1450  # km, lower-left corner of cell (0, 0)


def read(var, kind, period):
    """Return a float32 array (n, 1450, 900) with NaN outside the land mask."""
    with h5py.File(os.path.join(DATA, FILES[(var, kind, period)]), "r") as h:
        a = h[var][:].astype(np.float32)
        x = h["projection_x_coordinate"][:]; y = h["projection_y_coordinate"][:]
        if kind == "mon":
            assert list(h["month_number"][:]) == list(range(1, 13))
    assert x[0] == -199500 and y[0] == -199500 and a.shape[1:] == (NY, NX)
    a[a > 1e19] = np.nan
    return a


def all_layers():
    L = {}
    for k in FILES:
        a = read(*k)
        L[k] = a[0] if k[1] == "ann" else a
    return L


# ---- page quantisation (8-bit, 0 = no data). The page decodes with the inverse formulas in its script. ----
RAIN_M = (np.log(15.0), np.log(800.0))     # monthly rain, log scale, 15 to 800 mm
RAIN_A = (np.log(400.0), np.log(6000.0))   # annual rain, log scale, 400 to 6000 mm


def q_sun_m(v): return 1 + np.round(np.clip(v, 0, 300) / 1.2)
def q_rain_m(v): return 1 + np.round((np.log(np.clip(v, 15, 800)) - RAIN_M[0]) / (RAIN_M[1] - RAIN_M[0]) * 254)
def q_tmax(v): return 1 + np.round((np.clip(v, -5, 26.5) + 5) * 8)
def q_sun_a(v): return 1 + np.round((np.clip(v, 600, 2124) - 600) / 6)
def q_rain_a(v): return 1 + np.round((np.log(np.clip(v, 400, 6000)) - RAIN_A[0]) / (RAIN_A[1] - RAIN_A[0]) * 254)
def q_change(pct): return 1 + np.round(np.clip(pct, -31.5, 31.5) * 4 + 126)
