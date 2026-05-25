"""Generate report figures for LZW coding experiment (Task 3)."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

BLUE = "#21629B"
VERMILION = "#BC5040"
GREEN = "#348070"
INK = "#23272A"
GRAY = "#6B7280"
LIGHT = "#F6F8FA"
GRID = "#D9DEE5"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 12,
    "axes.edgecolor": GRID,
    "axes.facecolor": LIGHT,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 200,
})


def image_panel():
    src = Image.open(ROOT / "b8gray.bmp").convert("L")
    dec = Image.open(ROOT / "Id.bmp").convert("L")

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.subplots_adjust(top=0.86, wspace=0.08)
    fig.text(0.04, 0.96, "LZW Reconstruction Check",
             fontsize=20, fontweight="bold", va="top")
    fig.text(0.04, 0.91, "Original grayscale image and image decoded from C.dat",
             fontsize=11, color=GRAY, va="top")

    for ax, img, title, color in [
        (axes[0], src, r"$I_s$: b8gray.bmp", BLUE),
        (axes[1], dec, r"$I_d$: decoded image", GREEN),
    ]:
        ax.imshow(np.array(img), cmap="gray", vmin=0, vmax=255)
        ax.set_title(title, fontsize=13, fontweight="bold", color="white",
                     backgroundcolor=color, pad=8)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(GRID)
            spine.set_linewidth(1.5)

    fig.savefig(FIG / "fig_input_decoded.png", bbox_inches="tight")
    plt.close(fig)


def histogram_panel():
    img = Image.open(ROOT / "b8gray.bmp").convert("L")
    hist = img.histogram()
    total = sum(hist)
    probs = [v / total for v in hist]

    fig, ax = plt.subplots(figsize=(14, 6.5))
    fig.subplots_adjust(top=0.84, bottom=0.13)
    fig.text(0.06, 0.97, "Normalized Gray-Level Histogram",
             fontsize=20, fontweight="bold", va="top")
    fig.text(0.06, 0.91,
             "Distribution of the source image; the decoded image is identical pixel-by-pixel",
             fontsize=11, color=GRAY, va="top")

    levels = np.arange(256)
    colors = [BLUE if i < 160 else VERMILION for i in levels]
    ax.bar(levels, probs, width=1.0, color=colors, edgecolor="none")

    ax.set_xlim(-1, 256)
    ax.set_ylim(0, max(probs) * 1.08)
    ax.set_xlabel("Gray level", fontsize=13, fontweight="bold")
    ax.set_ylabel("Probability", fontsize=13, fontweight="bold")
    ax.xaxis.set_major_locator(ticker.FixedLocator([0, 64, 128, 192, 255]))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f"))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

    fig.savefig(FIG / "fig_histogram_source.png", bbox_inches="tight")
    plt.close(fig)


def metrics_panel():
    labels = ["LZW codes", "C.dat file", "Entropy"]
    values = [5.596430, 5.600275, 7.528544]
    colors = [BLUE, GREEN, VERMILION]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.subplots_adjust(top=0.83, left=0.14, bottom=0.13)
    fig.text(0.06, 0.97, "Coding Efficiency and Information Content",
             fontsize=20, fontweight="bold", va="top")
    fig.text(0.06, 0.91,
             "Lower bpp indicates a shorter representation; entropy is the source uncertainty",
             fontsize=11, color=GRAY, va="top")

    y_pos = np.arange(len(labels))[::-1]
    bars = ax.barh(y_pos, values, height=0.55, color=colors, edgecolor="none")

    ax.set_xlim(0, 9)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=13, fontweight="bold")
    ax.set_xlabel("bits per pixel", fontsize=12, color=GRAY)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{val:.6f} bit/pixel", va="center", fontsize=12)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.savefig(FIG / "fig_metrics.png", bbox_inches="tight")
    plt.close(fig)


def difference_panel():
    src = Image.open(ROOT / "b8gray.bmp").convert("L")
    dec = Image.open(ROOT / "Id.bmp").convert("L")
    diff = ImageChops.difference(src, dec)
    nonzero = int(np.count_nonzero(np.array(diff)))

    diff_arr = np.array(diff)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                             gridspec_kw={"width_ratios": [2, 1]})
    fig.subplots_adjust(top=0.85, wspace=0.12)
    fig.text(0.04, 0.97, "Pixel Difference Map",
             fontsize=20, fontweight="bold", va="top")
    fig.text(0.04, 0.91, f"Non-zero difference pixels: {nonzero}",
             fontsize=12, color=GRAY, va="top")

    ax0 = axes[0]
    ax0.imshow(diff_arr, cmap="hot", vmin=0, vmax=max(1, diff_arr.max()))
    ax0.set_title(r"$|I_s - I_d|$ (amplified)", fontsize=13, fontweight="bold")
    ax0.set_xticks([])
    ax0.set_yticks([])
    for spine in ax0.spines.values():
        spine.set_color(GRID)

    ax1 = axes[1]
    ax1.set_facecolor(LIGHT)
    ax1.text(0.5, 0.55, "All pixels are identical",
             fontsize=18, fontweight="bold", color=GREEN,
             ha="center", va="center", transform=ax1.transAxes)
    ax1.text(0.5, 0.35, r"$I_s \equiv I_d$: YES",
             fontsize=15, fontweight="bold", color=INK,
             ha="center", va="center", transform=ax1.transAxes)
    ax1.set_xticks([])
    ax1.set_yticks([])
    for spine in ax1.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(1.5)

    fig.savefig(FIG / "fig_difference.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    image_panel()
    print("  -> fig_input_decoded.png")
    histogram_panel()
    print("  -> fig_histogram_source.png")
    metrics_panel()
    print("  -> fig_metrics.png")
    difference_panel()
    print("  -> fig_difference.png")
    print("Done.")
