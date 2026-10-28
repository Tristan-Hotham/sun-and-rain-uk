"""r/dataisbeautiful collage: reddit/sunny_wet_or_both.png (2400 x 3000), light paper with the project's own bivariate palette.
Every number comes from ../data/results.json; the maps are drawn from the HadUK-Grid files read in place (code/haduk.py).
Run from this folder: FONT_DIR=/path/to/fonts python3 collage.py
"""
import os, sys
OUTDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(OUTDIR, "..", "code"))
import numpy as np
from figlib import *
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

BGC = "#F5F2EA"
L = layers()
SA, RA = L[("sun", "ann", "9120")], L[("rainfall", "ann", "9120")]
SA6, RA6 = L[("sun", "ann", "6190")], L[("rainfall", "ann", "6190")]
BS, BR = R["breaks"]["sun3"], R["breaks"]["rain3"]
P = palette.grid(3)
U, C, CH = R["uk"], R["classes"], R["change"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BGC)
fig.text(0.045, 0.972, "Is your bit of the UK", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.045, 0.924, "sunny,", fontproperties=DISP, fontsize=50, color=P[0][2], va="top")
fig.text(0.268, 0.924, "wet,", fontproperties=DISP, fontsize=50, color=P[2][0], va="top")
fig.text(0.418, 0.924, "or both?", fontproperties=DISP, fontsize=50, color=P[2][2], va="top")
fig.text(0.045, 0.862, f"Every one of the UK's {R['meta']['cells']:,} square kilometres, coloured by its yearly sunshine and its yearly\n"
         "rainfall at the same time. Met Office 1 km averages for 1991 to 2020; each third of the land is one step of the key.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.15)

# hero map
ax = fig.add_axes([-0.02, 0.255, 0.62, 0.555]); ax.set_facecolor(BGC)
context(ax, fc="#E8E3D8")
ax.imshow(biv_rgb(SA, RA, BS, BR), origin="lower", extent=EXT, interpolation="nearest", zorder=1)
ax.set_xlim(-10, 660); ax.set_ylim(0, 1225); ax.set_aspect(1); ax.axis("off")
import matplotlib.patheffects as pe
def note(txt, xy, xyt, ha="left"):
    ax.annotate(txt, xy=xy, xytext=xyt, family=MONO, fontsize=10.5, color=FG, ha=ha, va="center", zorder=8,
                arrowprops=dict(arrowstyle="-", color=FG, lw=.8), path_effects=[pe.withStroke(linewidth=3, foreground=BGC)])
note(f"Ben Nevis:\n{U['sun_min']:,.0f} h of sun", (216.6, 771.3), (5, 700), ha="left")
note(f"Dungeness: {U['sun_max']:,.0f} h", (609.5, 117.5), (500, 30), ha="center")
note(f"Borrowdale:\n{U['rain_max']:,.0f} mm of rain", (322.5, 510.5), (250, 440), ha="center")
note("Moray Firth:\ndull and dry", (275, 855), (440, 960), ha="left")
note("Cornwall:\nsunny and wet", (175, 50), (40, 160), ha="center")

# key with words
lg = fig.add_axes([0.66, 0.655, 0.16, 0.125]); biv_legend(lg, fs=11)
fig.text(0.64, 0.795, "THE KEY", family=MONO, fontsize=11, color=MUT)

# headline numbers
tx = fig.add_axes([0.62, 0.255, 0.36, 0.37]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
items = [
    (f"{C['sunny_dry']['share'] * 100:.0f}%", P[0][2], f"of the land is sunny and dry, mostly East\nAnglia and the south east. {C['dull_wet']['share'] * 100:.0f}% is dull\nand wet, three quarters of it in Scotland."),
    (f"{C['sunny_wet']['share'] * 100:.1f}%", P[2][2], f"is both sunny and wet: Cornwall, Devon\nand south west Wales. Dull and dry is\nrarer still, {C['dull_dry']['share'] * 100:.1f}%, by the Moray Firth."),
    (f"{R['coast']['top1_within5'] * 100:.0f}%", P[1][2], f"of the sunniest 1% of squares are within\n5 km of the sea, against {R['coast']['land_within5'] * 100:.0f}% of the land."),
    (f"+{U['sun_chg_pct']:.1f}%", SUN, f"more sunshine than in 1961 to 1990, and\n{U['rain_chg_pct']:.1f}% more rain. {CH['sunnier_and_wetter'] * 100:.0f}% of the land got both."),
]
for i, (big, c, txt) in enumerate(items):
    y = .99 - i * .255
    tx.text(0, y, big, fontproperties=DISP, fontsize=38, color=c, va="top")
    tx.text(0, y - .115, txt, family=SER, fontsize=12.5, color=FG, va="top", linespacing=1.08)

# small multiples: then, now, change
fig.text(0.045, 0.238, "THEN AND NOW, WITH THE SAME BREAKS", family=MONO, fontsize=11, color=MUT)
a = CH["top_sun_class_area"]
for k, (s, r, t) in enumerate(((SA6, RA6, "1961 to 1990"), (SA, RA, "1991 to 2020"))):
    m = fig.add_axes([0.02 + k * 0.31, 0.07, 0.3, 0.122]); m.set_facecolor(BGC)
    context(m, fc="#E8E3D8"); m.imshow(biv_rgb(s, r, BS, BR), origin="lower", extent=EXT, interpolation="nearest", zorder=1)
    m.set_xlim(-10, 660); m.set_ylim(0, 1225); m.set_aspect(1); m.axis("off")
    fig.text(0.17 + k * 0.31, 0.226, t, family=MONO, fontsize=12.5, color=FG, ha="center", va="top")
    fig.text(0.17 + k * 0.31, 0.208, f"sunniest class: {a[k]:,} km²", family=MONO, fontsize=10.5, color=P[0][2] if k else MUT, ha="center", va="top")
d = (SA / SA6 - 1) * 100
cm = LinearSegmentedColormap.from_list("c", ["#2E8C96", "#F4F0E6", "#F0902A", "#7A2E1A"])
m = fig.add_axes([0.66, 0.07, 0.3, 0.122]); m.set_facecolor(BGC); context(m, fc="#E8E3D8")
m.imshow(np.ma.masked_invalid(d), origin="lower", extent=EXT, cmap=cm, norm=TwoSlopeNorm(0, -8, 20), interpolation="nearest", zorder=1)
m.set_xlim(-10, 660); m.set_ylim(0, 1225); m.set_aspect(1); m.axis("off")
fig.text(0.81, 0.226, "Change in sunshine", family=MONO, fontsize=12.5, color=FG, ha="center", va="top")
fig.text(0.81, 0.208, f"England +{R['nation']['England']['sun_chg_pct']:.1f}%, N. Ireland +{R['nation']['Northern Ireland']['sun_chg_pct']:.1f}%", family=MONO, fontsize=10.5, color=SUN, ha="center", va="top")

fig.text(0.045, 0.048, "Data: Met Office HadUK-Grid v1.3.2 1 km thirty-year averages (contains Met Office data © Crown copyright 2026, Open Government\n"
         "Licence v3). Classes at the terciles of the land: 1,310 and 1,526 hours of sun, 817 and 1,231 mm of rain. Gridded values are interpolated\n"
         "between stations; part of the change may come from new instruments. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9.6, color=MUT, va="top", linespacing=1.45)
assert BS == [1310.0, 1526.0] and BR == [817.0, 1231.0]  # quoted in the footer
fig.savefig(os.path.join(OUTDIR, "sunny_wet_or_both.png"), dpi=200, facecolor=BGC)
print("collage written")
