"""Step 5. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png, 1520 px wide).
Run: FONT_DIR=/path/to/fonts python3 code/05_figures.py
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from figlib import *

PAPER = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAPER, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
L = layers()
SA, RA = L[("sun", "ann", "9120")], L[("rainfall", "ann", "9120")]
SA6, RA6 = L[("sun", "ann", "6190")], L[("rainfall", "ann", "6190")]
SM, RM, TM = L[("sun", "mon", "9120")], L[("rainfall", "mon", "9120")], L[("tasmax", "mon", "9120")]
BS, BR = R["breaks"]["sun3"], R["breaks"]["rain3"]
land = ~np.isnan(SA)
MONS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def save(fig, name, blog=True, paper=True):
    if paper: fig.savefig(os.path.join(PAPER, "f_" + name + ".png"), dpi=200)
    if blog: fig.savefig(os.path.join(BLOG, "b_" + name + ".png"), dpi=200)
    plt.close(fig)


# 1. the bivariate map
def fig_map():
    fig = plt.figure(figsize=(7.6, 9.6))
    ax = fig.add_axes([0, 0, .72, 1]); mapax(ax, biv_rgb(SA, RA, BS, BR), xlim=(-10, 660), ylim=(0, 1225))
    label_towns(ax, ["London", "Birmingham", "Manchester", "Glasgow", "Edinburgh", "Cardiff", "Belfast", "Newcastle upon Tyne", "Inverness",
                     "Fort William", "Plymouth", "Norwich", "Aberdeen", "Swansea", "Lerwick", "Stornoway", "Folkestone"], fs=8.5,
                offsets={"Glasgow": (-6, 0, "right"), "Swansea": (-6, 0, "right"), "Fort William": (-6, 0, "right"), "Stornoway": (-6, 0, "right"),
                         "Norwich": (-6, 0, "right"), "Folkestone": (-6, -12, "right")})
    lg = fig.add_axes([.76, .70, .15, .14]); biv_legend(lg, fs=8.5)
    t = fig.add_axes([.75, .05, .24, .6]); t.axis("off")
    C = R["classes"]
    rows = [("sunny and dry", C["sunny_dry"]["share"], palette.grid(3)[0][2]), ("dull and wet", C["dull_wet"]["share"], palette.grid(3)[2][0]),
            ("sunny and wet", C["sunny_wet"]["share"], palette.grid(3)[2][2]), ("dull and dry", C["dull_dry"]["share"], palette.grid(3)[0][0])]
    t.text(0, 1, "SHARE OF\nTHE LAND", family=MONO, fontsize=9, color=MUT, va="top")
    for k, (nm, v, c) in enumerate(rows):
        y = .86 - k * .16
        t.add_patch(plt.Rectangle((0, y - .045), .1, .07, fc=c, ec=MUT, lw=.4, transform=t.transAxes))
        t.text(.14, y, f"{v * 100:.1f}%" if v < .05 else f"{v * 100:.0f}%", fontproperties=DISP, fontsize=17, color=FG, va="center")
        t.text(.14, y - .065, nm, family=MONO, fontsize=8.5, color=FG, va="center")
    t.text(0, .2, "Terciles of the UK's\n1 km squares, 1991 to\n2020: each row and\ncolumn of the key is\na third of the land.", family=MONO, fontsize=8, color=MUT, va="top")
    save(fig, "map")


# 2. density of squares with the breaks and towns
def fig_density():
    fig, ax = plt.subplots(figsize=(7.6, 5.6)); fig.subplots_adjust(left=.11, right=.97, top=.97, bottom=.12)
    s, r = SA[land], RA[land]
    P = palette.grid(3)
    xs = [700, *BS, 2050]; ys = [440, *BR, 5000]
    for i in range(3):
        for j in range(3):
            ax.add_patch(plt.Rectangle((xs[j], ys[i]), xs[j + 1] - xs[j], ys[i + 1] - ys[i], fc=P[i][j], ec="none", alpha=.85, zorder=0))
    ax.hexbin(s, r, gridsize=(90, 60), yscale="log", bins="log", cmap="Greys", mincnt=1, linewidths=0, alpha=.7, zorder=1)
    ax.set_yscale("log"); ax.yaxis.set_minor_formatter(plt.NullFormatter()); ax.set_xlim(700, 2050); ax.set_ylim(440, 5000)
    ax.set_yticks([500, 700, 1000, 1500, 2000, 3000, 4000]); ax.set_yticklabels(["500", "700", "1,000", "1,500", "2,000", "3,000", "4,000"])
    ax.set_xticks([800, 1000, 1200, 1400, 1600, 1800, 2000]); ax.set_xticklabels([f"{v:,}" for v in [800, 1000, 1200, 1400, 1600, 1800, 2000]])
    ax.set_xlabel("Sunshine, hours a year", family=MONO, fontsize=10); ax.set_ylabel("Rainfall, mm a year (log scale)", family=MONO, fontsize=10)
    for v in BS: ax.axvline(v, color=FG, lw=.8, ls=(0, (4, 3)))
    for v in BR: ax.axhline(v, color=FG, lw=.8, ls=(0, (4, 3)))
    off = {"Fort William": (10, 0), "Folkestone": (-10, 0), "Southend-on-Sea": (-10, 0), "Swansea": (10, 0), "Inverness": (10, 0), "London": (10, 0),
           "Belfast": (-10, 0), "Glasgow": (10, 8), "Manchester": (10, 0), "Rhondda": (10, 0), "Edinburgh": (10, 0), "Plymouth": (10, 0)}
    for nm, (dx, dy) in off.items():
        t = town(nm)
        ax.plot(t.sun, t.rain, "o", ms=5, mfc=BG, mec=FG, mew=1.2, zorder=4)
        ax.text(t.sun + dx, t.rain, nm, family=MONO, fontsize=8.5, ha="left" if dx > 0 else "right", va="center", zorder=5,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])
    save(fig, "density")


# 3. then and now, with the 1991 to 2020 breaks
def fig_thennow():
    fig = plt.figure(figsize=(7.6, 5.4))
    for k, (s, r, t) in enumerate(((SA6, RA6, "1961 to 1990"), (SA, RA, "1991 to 2020"))):
        ax = fig.add_axes([.0 + k * .42, .02, .42, .88]); mapax(ax, biv_rgb(s, r, BS, BR), xlim=(-10, 660), ylim=(0, 1225))
        ax.set_title(t, family=MONO, fontsize=11, color=FG)
    lg = fig.add_axes([.86, .58, .1, .14]); biv_legend(lg, fs=7)
    a = R["change"]["top_sun_class_area"]
    fig.text(.845, .45, f"Sunniest class\n(over {BS[1]:,.0f} h)\n\n{a[0]:,} km²\nthen\n\n{a[1]:,} km²\nnow", family=MONO, fontsize=8.5, color=FG, va="top")
    save(fig, "thennow")


# 5. sunshine change map (diverging)
def fig_changemap():
    d = (SA / SA6 - 1) * 100
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cm = LinearSegmentedColormap.from_list("c", ["#2E8C96", "#F4F0E6", "#F0902A", "#7A2E1A"])
    fig = plt.figure(figsize=(7.6, 8.4))
    ax = fig.add_axes([0, 0, .8, 1]); ax.set_facecolor(SEA); context(ax)
    im = ax.imshow(np.ma.masked_invalid(d), origin="lower", extent=EXT, cmap=cm, norm=TwoSlopeNorm(0, -8, 20), interpolation="nearest", zorder=1)
    ax.set_xlim(-10, 660); ax.set_ylim(0, 1225); ax.set_aspect(1); ax.axis("off")
    label_towns(ax, ["Newcastle upon Tyne", "Sheffield", "London", "Glasgow", "Belfast", "Cardiff", "Plymouth", "Inverness"], fs=8.5,
                offsets={"Glasgow": (-6, 0, "right")})
    cax = fig.add_axes([.8, .35, .025, .4]); cb = fig.colorbar(im, cax=cax); cb.outline.set_visible(False)
    cb.set_ticks([-8, -4, 0, 5, 10, 15, 20]); cb.ax.set_yticklabels(["−8%", "−4%", "0", "+5%", "+10%", "+15%", "+20%"], family=MONO, fontsize=8.5)
    fig.text(.78, .79, "Change in annual\nsunshine, 1961 to 1990\nto 1991 to 2020", family=MONO, fontsize=9, color=FG)
    save(fig, "changemap")


# 6. coast
def fig_coast():
    C = R["coast"]; b = C["bands"]
    labs = [f"{x['from_km']} to {x['to_km']}" if x["to_km"] < 100 else "80+" for x in b]
    fig, ax = plt.subplots(figsize=(7.6, 4.4)); fig.subplots_adjust(left=.1, right=.86, top=.95, bottom=.16)
    for nn, c in (("England", SUN), ("Wales", PLUM), ("Scotland", RAIN)):
        v = [np.nan if q is None else q for q in C["bands_nation"][nn]]
        ax.plot(range(len(v)), v, "-o", color=c, lw=2.5, ms=6)
        last = max(i for i, q in enumerate(v) if not np.isnan(q))
        ax.text(last + .15, v[last], nn, family=MONO, fontsize=10, color=c, va="center", fontweight="bold")
    ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, family=MONO, fontsize=9)
    ax.set_xlabel("Distance from the sea, km", family=MONO, fontsize=10); ax.set_ylabel("Sunshine, hours a year", family=MONO, fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}")); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
    save(fig, "coast")


# 7. months by nation
def fig_months():
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.8)); fig.subplots_adjust(left=.08, right=.98, top=.88, bottom=.12, wspace=.25)
    for ax, k, t in ((axs[0], "sun", "Sunshine, hours"), (axs[1], "rain", "Rainfall, mm")):
        for nn, c in (("England", SUN), ("Wales", PLUM), ("Scotland", RAIN), ("Northern Ireland", MUT)):
            ax.plot(range(12), [m[f"{k}_{nn}"] for m in R["months"]], "-o", color=c, lw=2, ms=3.5, label=nn)
        ax.set_xticks(range(12)); ax.set_xticklabels(MONS, family=MONO, fontsize=9); ax.set_title(t, family=MONO, fontsize=10, loc="left")
        ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True); ax.set_ylim(0, None)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, prop={"family": MONO, "size": 8.5}, loc="upper center", ncol=4, bbox_to_anchor=(.5, 1.0))
    fig.subplots_adjust(top=.82)
    save(fig, "months", blog=False)


for f in (fig_map, fig_density, fig_thennow, fig_changemap, fig_coast, fig_months):
    f(); print(f.__name__)
