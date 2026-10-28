"""The bivariate palette used everywhere (page, figures, collage). Four corners, interpolated in CIELAB.

Corners (sunshine across, rainfall up):
  dull and dry   pale paper   (the palest)
  sunny and dry  marigold     (warm)
  dull and wet   deep teal    (cool)
  sunny and wet  aubergine    (the darkest)
"""
import numpy as np

CORNERS = {"dull_dry": "#F4F0E6", "sunny_dry": "#F0902A", "dull_wet": "#2E8C96", "sunny_wet": "#3E1C47"}


def _srgb2lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def _lin2srgb(c): return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
WP = np.array([0.95047, 1.0, 1.08883])


def hex2lab(h):
    rgb = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    xyz = M @ _srgb2lin(rgb) / WP
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def lab2hex(lab):
    L, a, b = lab
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    f = np.array([fx, fy, fz])
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * WP
    rgb = np.clip(_lin2srgb(np.linalg.solve(M, xyz)), 0, 1)
    return "#" + "".join(f"{int(round(v * 255)):02X}" for v in rgb)


def grid(n):
    """n by n colours; grid[r][s] with r = rain class (0 = driest) and s = sun class (0 = dullest)."""
    c = {k: hex2lab(v) for k, v in CORNERS.items()}
    out = []
    for r in range(n):
        v = r / (n - 1); row = []
        for s in range(n):
            u = s / (n - 1)
            lab = (1 - u) * (1 - v) * c["dull_dry"] + u * (1 - v) * c["sunny_dry"] + (1 - u) * v * c["dull_wet"] + u * v * c["sunny_wet"]
            row.append(lab2hex(lab))
        out.append(row)
    return out


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(8, 4))
    for ax, n in zip(axs, (3, 4)):
        g = grid(n); print(n, g)
        for r in range(n):
            for s in range(n):
                ax.add_patch(plt.Rectangle((s, r), 1, 1, fc=g[r][s]))
        ax.set_xlim(0, n); ax.set_ylim(0, n); ax.set_aspect(1); ax.set_xlabel("sun"); ax.set_ylabel("rain")
    fig.savefig("/home/claude/hist/sun-and-rain-uk/work/pal.png", dpi=80)
