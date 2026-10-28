"""Step 4. Render header.png, the 1200 by 630 social card, with matplotlib.
Run: FONT_DIR=/path/to/fonts python3 code/04_header.py
"""
from figlib import *

L = layers()
SA, RA = L[("sun", "ann", "9120")], L[("rainfall", "ann", "9120")]
fig = plt.figure(figsize=(6, 3.15), dpi=200)
ax = fig.add_axes([.555, .0, .45, 1]); mapax(ax, biv_rgb(SA, RA, R["breaks"]["sun3"], R["breaks"]["rain3"]), xlim=(-30, 680), ylim=(-20, 1230))
fig.text(.055, .86, "DATA STUDY  ·  CLIMATE  ·  UK 1991 TO 2020", family=MONO, fontsize=6.2, color=MUT)
fig.text(.05, .80, "Sun", fontproperties=DISP, fontsize=40, color=SUN, va="top")
fig.text(.05, .58, "and rain", fontproperties=DISP, fontsize=40, color=RAIN, va="top")
U = R["uk"]
fig.text(.055, .375, f"Every square kilometre of the UK by sunshine\nand rainfall: {U['sun_max']:,.0f} hours of sun a year at\n"
         f"Dungeness, {U['sun_min']:,.0f} on Ben Nevis. And the UK is\n{U['sun_chg_pct']:.1f}% sunnier than it was in 1961 to 1990.",
         family=SER, fontsize=8.4, color=FG, va="top", linespacing=1.12)
fig.text(.055, .06, "Dr Tristan Hotham · Independent researcher", family=MONO, fontsize=6, color=MUT)
lg = fig.add_axes([.455, .62, .1, .2]); biv_legend(lg, words=False)
fig.text(.455, .58, "sun →", family=MONO, fontsize=5.5, color=MUT)
fig.text(.44, .66, "rain →", family=MONO, fontsize=5.5, color=MUT, rotation=90)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=200)
print("header.png written")
