"""Generate publication-quality figures for LZW coding experiment (Task 3)."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# --- Muted academic palette ---
C_BLUE   = "#3C6E9C"
C_RED    = "#B8503B"
C_GREEN  = "#4E8D6E"
C_GOLD   = "#C49A3C"
C_DARK   = "#2D3436"
C_GRAY   = "#7F8C8D"
C_LGRAY  = "#ECF0F1"
C_MGRAY  = "#BDC3C7"

plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "font.size": 10,
    "axes.edgecolor": C_MGRAY,
    "axes.linewidth": 0.6,
    "axes.labelcolor": C_DARK,
    "axes.labelsize": 11,
    "text.color": C_DARK,
    "xtick.color": C_DARK,
    "ytick.color": C_DARK,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
})


def _label(ax, text, x=-0.02, y=1.05):
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=12, fontweight="bold", va="bottom", ha="right")


def image_panel():
    """(a) Is  (b) Id — side-by-side with zoom insets."""
    src = np.array(Image.open(ROOT / "b8gray.bmp").convert("L"))
    dec = np.array(Image.open(ROOT / "Id.bmp").convert("L"))

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.2))
    fig.subplots_adjust(wspace=0.06)

    # zoom region (row, col)
    zy, zx, zs = 400, 350, 260

    for ax, img, label, tag_color in [
        (axes[0], src, "(a)", C_BLUE),
        (axes[1], dec, "(b)", C_GREEN),
    ]:
        ax.imshow(img, cmap="gray", vmin=0, vmax=255, interpolation="bilinear")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.4)
            spine.set_color(C_MGRAY)

        # zoom inset
        rect = Rectangle((zx, zy), zs, zs, linewidth=1.0,
                          edgecolor=C_RED, facecolor="none", linestyle="-")
        ax.add_patch(rect)

        axins = ax.inset_axes([0.58, 0.02, 0.40, 0.40])
        axins.imshow(img[zy:zy+zs, zx:zx+zs], cmap="gray",
                     vmin=0, vmax=255, interpolation="bilinear")
        axins.set_xticks([])
        axins.set_yticks([])
        for spine in axins.spines.values():
            spine.set_linewidth(0.8)
            spine.set_color(C_RED)

        _label(ax, label)

    fig.savefig(FIG / "fig_input_decoded.png")
    plt.close(fig)


def histogram_panel():
    """Normalized gray-level histogram of the source image."""
    img = Image.open(ROOT / "b8gray.bmp").convert("L")
    hist = np.array(img.histogram(), dtype=float)
    probs = hist / hist.sum()

    fig, ax = plt.subplots(figsize=(5.5, 3.0))

    levels = np.arange(256)
    ax.fill_between(levels, probs, color=C_BLUE, alpha=0.7, linewidth=0)
    ax.plot(levels, probs, color=C_BLUE, linewidth=0.6, alpha=0.9)

    ax.set_xlim(0, 255)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Gray level")
    ax.set_ylabel("Probability")
    ax.xaxis.set_major_locator(ticker.FixedLocator([0, 64, 128, 192, 255]))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.4f"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.savefig(FIG / "fig_histogram_source.png")
    plt.close(fig)


def metrics_panel():
    """Horizontal bar chart: LZW bpp vs. entropy."""
    labels  = [r"$\mathrm{bpp_{code}}$",
               r"$\mathrm{bpp_{file}}$",
               r"$H(I_s)$"]
    values  = [5.596430, 5.600275, 7.528544]
    colors  = [C_BLUE, C_GREEN, C_RED]

    fig, ax = plt.subplots(figsize=(5.5, 2.4))

    y_pos = np.arange(len(labels))[::-1]
    bars = ax.barh(y_pos, values, height=0.48, color=colors,
                   edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(val + 0.12, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=9, color=C_DARK)

    ax.set_xlim(0, 9)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel("bits / pixel")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(left=False)

    fig.savefig(FIG / "fig_metrics.png")
    plt.close(fig)


def difference_panel():
    """Pixel-value correlation density plot proving lossless reconstruction."""
    src = np.array(Image.open(ROOT / "b8gray.bmp").convert("L")).ravel()
    dec = np.array(Image.open(ROOT / "Id.bmp").convert("L")).ravel()

    fig, ax = plt.subplots(figsize=(4.0, 3.8))

    # 2D histogram — mask zeros so background stays white
    h, xedges, yedges = np.histogram2d(src, dec, bins=256,
                                        range=[[0, 255], [0, 255]])
    h_masked = np.ma.masked_where(h.T == 0, np.log10(h.T + 1))

    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "density", [C_LGRAY, C_BLUE, C_GREEN, C_GOLD], N=256)
    cmap.set_bad("white")

    ax.imshow(h_masked, origin="lower", extent=[0, 255, 0, 255],
              cmap=cmap, aspect="equal", interpolation="nearest")

    # y=x reference
    ax.plot([0, 255], [0, 255], color=C_RED, linewidth=0.5,
            linestyle="--", alpha=0.6)

    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    ax.set_xlabel(r"$I_s$ pixel value")
    ax.set_ylabel(r"$I_d$ pixel value")
    ax.xaxis.set_major_locator(ticker.FixedLocator([0, 64, 128, 192, 255]))
    ax.yaxis.set_major_locator(ticker.FixedLocator([0, 64, 128, 192, 255]))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.savefig(FIG / "fig_difference.png")
    plt.close(fig)


if __name__ == "__main__":
    image_panel()
    histogram_panel()
    metrics_panel()
    difference_panel()
    print("Done.")
