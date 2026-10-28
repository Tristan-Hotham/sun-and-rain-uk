"""Shared drawing helpers for the header, the paper and blog figures, and the Reddit collage (matplotlib).

Reads the HadUK-Grid files in place (haduk.py) and the outputs of steps 1 and 2. Fonts: FONT_DIR holding Fraunces,
Source Serif 4 and IBM Plex Mono (from github.com/google/fonts); otherwise matplotlib's defaults are used.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
import pandas as pd
import haduk as H
import palette

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
DISP = None
if os.path.isdir(FD):
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
        if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
    DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, CTX, SEA = "#F7F4EC", "#1E1B22", "#665F68", "#DED7C8", "#E9E4D8", "#F7F4EC"
SUN, RAIN, PLUM = "#D97A16", "#24808A", "#3E1C47"
plt.rcParams.update({"font.family": SER, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.facecolor": BG, "figure.facecolor": BG, "axes.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
COAST = json.load(open(os.path.join(ROOT, "data", "coast_bng.json")))
EXT = [H.X0, H.X0 + H.NX, H.Y0, H.Y0 + H.NY]
_L = None


def layers():
    global _L
    if _L is None: _L = H.all_layers()
    return _L


def hexrgb(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255


def biv_rgb(sun, rain, bs, br, n=3, hl=None, fade="#D4CFC7"):
    """RGBA image (rows south to north, as the grid) of bivariate classes."""
    P = palette.grid(n)
    cs = np.digitize(np.nan_to_num(sun, nan=-1), bs); cr = np.digitize(np.nan_to_num(rain, nan=-1), br)
    img = np.zeros(sun.shape + (4,))
    for r in range(n):
        for s in range(n):
            m = (cr == r) & (cs == s)
            img[m, :3] = hexrgb(P[r][s]) if (hl is None or hl == (r, s)) else hexrgb(fade)
    img[..., 3] = ~np.isnan(sun)
    return img


def context(ax, fc=CTX):
    for g in COAST:
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ax.add_patch(Polygon(np.array(poly[0]), closed=True, fc=fc, ec="none", zorder=0))


def mapax(ax, img, xlim=(-10, 660), ylim=(0, 1225), ctx=True):
    ax.set_facecolor(SEA)
    if ctx: context(ax)
    ax.imshow(img, origin="lower", extent=EXT, interpolation="nearest", zorder=1)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect(1); ax.axis("off")


TOWNS = pd.read_csv(os.path.join(ROOT, "data", "towns.csv"))


def town(nm):
    m = TOWNS[TOWNS.name == nm].sort_values("source")
    return m.iloc[0]


def label_towns(ax, names, fs=9, dx=6, color=FG, halo=BG, offsets=None):
    import matplotlib.patheffects as pe
    offsets = offsets or {}
    for nm in names:
        t = town(nm); x, y = t.e / 1000, t.n / 1000
        ox, oy, ha = offsets.get(nm, (dx, 0, "left"))
        ax.plot([x], [y], "o", ms=3, color=color, zorder=5)
        ax.text(x + ox, y + oy, nm.replace("Kingston upon Hull", "Hull").replace("Newcastle upon Tyne", "Newcastle"), family=MONO, fontsize=fs, color=color,
                va="center", ha=ha, zorder=6, path_effects=[pe.withStroke(linewidth=2.5, foreground=halo)])


def biv_legend(ax, n=3, size=1.0, fs=9, words=True, hl=None):
    P = palette.grid(n)
    for r in range(n):
        for s in range(n):
            ax.add_patch(plt.Rectangle((s, r), .96, .96, fc=P[r][s], ec=FG if hl == (r, s) else "none", lw=1.5))
    ax.set_xlim(-.1, n); ax.set_ylim(-.1, n); ax.set_aspect(1); ax.axis("off")
    if words:
        kw = dict(family=MONO, fontsize=fs, color=FG)
        ax.text(-.15, 0.45, "dull and\ndry", ha="right", va="center", **kw)
        ax.text(n + .1, 0.45, "sunny and\ndry", ha="left", va="center", **kw)
        ax.text(-.15, n - .55, "dull and\nwet", ha="right", va="center", **kw)
        ax.text(n + .1, n - .55, "sunny and\nwet", ha="left", va="center", **kw)
        ax.annotate("", xy=(n, -.35), xytext=(0, -.35), arrowprops=dict(arrowstyle="->", color=MUT, lw=1), annotation_clip=False)
        ax.text(n / 2, -.55, "more sunshine", ha="center", va="top", family=MONO, fontsize=fs - 1, color=MUT)
