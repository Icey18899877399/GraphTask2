"""Generate clean publication-style figures for the Task 3 LZW experiment."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image


ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# Muted academic palette.
C_BLUE = "#2F6690"
C_GREEN = "#3A7D63"
C_RED = "#B24C3E"
C_DARK = "#222222"
C_GRID = "#D9DDE2"


plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "font.size": 8.5,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "axes.linewidth": 0.55,
        "axes.edgecolor": C_DARK,
        "axes.labelcolor": C_DARK,
        "xtick.color": C_DARK,
        "ytick.color": C_DARK,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.major.width": 0.55,
        "ytick.major.width": 0.55,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    }
)


def load_gray(name: str) -> np.ndarray:
    return np.asarray(Image.open(ROOT / name).convert("L"))


def panel_label(ax, label: str, dark: bool = True) -> None:
    face = "black" if dark else "white"
    text = "white" if dark else C_DARK
    ax.text(
        0.02,
        0.98,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
        color=text,
        bbox=dict(boxstyle="square,pad=0.18", facecolor=face, edgecolor="none", alpha=0.66),
    )


def clean_image_axis(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_linewidth(0.45)
        spine.set_color(C_DARK)


def choose_crop(img: np.ndarray, size: int = 260) -> tuple[int, int, int]:
    h, w = img.shape
    y = min(max(h // 4, 0), max(h - size, 0))
    x = min(max(w // 4, 0), max(w - size, 0))
    return y, x, min(size, h, w)


def image_panel() -> None:
    """Source and decoded image with one unobtrusive zoom inset."""
    src = load_gray("b8gray.bmp")
    dec = load_gray("Id.bmp")
    zy, zx, zs = choose_crop(src)

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.35), constrained_layout=True)
    for ax, img, label, title in zip(
        axes,
        [src, dec],
        ["(a)", "(b)"],
        [r"$I_s$", r"$I_d$"],
    ):
        ax.imshow(img, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_title(title, pad=3)
        clean_image_axis(ax)
        panel_label(ax, label)

        ax.add_patch(Rectangle((zx, zy), zs, zs, fill=False, edgecolor=C_RED, linewidth=0.85))
        inset = ax.inset_axes([0.62, 0.04, 0.34, 0.34])
        inset.imshow(img[zy : zy + zs, zx : zx + zs], cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        clean_image_axis(inset)
        for spine in inset.spines.values():
            spine.set_color(C_RED)
            spine.set_linewidth(0.85)

    fig.savefig(FIG / "fig_input_decoded.png")
    plt.close(fig)


def histogram_panel() -> None:
    """Normalized source-image histogram with necessary ticks only."""
    img = load_gray("b8gray.bmp")
    hist = np.bincount(img.ravel(), minlength=256).astype(float)
    prob = hist / hist.sum()
    x = np.arange(256)

    fig, ax = plt.subplots(figsize=(5.2, 2.75), constrained_layout=True)
    ax.bar(x, prob, width=1.0, color=C_BLUE, alpha=0.82, linewidth=0)
    ax.plot(x, prob, color=C_BLUE, linewidth=0.6)

    ax.set_xlim(0, 255)
    ax.set_ylim(0, prob.max() * 1.10)
    ax.set_xlabel("Gray level")
    ax.set_ylabel("Probability")
    ax.xaxis.set_major_locator(ticker.FixedLocator([0, 64, 128, 192, 255]))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(4))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f"))
    ax.grid(axis="y", color=C_GRID, linewidth=0.45, alpha=0.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.savefig(FIG / "fig_histogram_source.png")
    plt.close(fig)


def metrics_panel() -> None:
    """Compact comparison of LZW bpp and source entropy."""
    labels = [r"$\mathrm{bpp}_{code}$", r"$\mathrm{bpp}_{file}$", r"$H(I_s)$"]
    values = np.array([5.596430, 5.600275, 7.528544])
    colors = [C_BLUE, C_GREEN, C_RED]
    y = np.arange(len(labels))[::-1]

    fig, ax = plt.subplots(figsize=(5.2, 2.25), constrained_layout=True)
    bars = ax.barh(y, values, height=0.46, color=colors, edgecolor="none")

    for bar, value in zip(bars, values):
        ax.text(
            value + 0.09,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            ha="left",
            fontsize=8.2,
            color=C_DARK,
        )

    ax.set_xlim(0, 8.4)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("bits / pixel")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.grid(axis="x", color=C_GRID, linewidth=0.45, alpha=0.75)
    ax.tick_params(axis="y", length=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    fig.savefig(FIG / "fig_metrics.png")
    plt.close(fig)


def difference_panel() -> None:
    """Crop comparison plus residual histogram.

    A pure difference image is uninformative for a lossless result because it is
    entirely black. The third panel instead shows the residual distribution:
    all samples should concentrate at zero.
    """
    src = load_gray("b8gray.bmp")
    dec = load_gray("Id.bmp")
    diff = np.abs(src.astype(np.int16) - dec.astype(np.int16))
    zy, zx, zs = choose_crop(src)

    src_crop = src[zy : zy + zs, zx : zx + zs]
    dec_crop = dec[zy : zy + zs, zx : zx + zs]

    total = diff.size
    nonzero = int(np.count_nonzero(diff))
    max_delta = int(diff.max())
    mse = float(np.mean(diff.astype(np.float64) ** 2))

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.2, 2.45),
        gridspec_kw={"width_ratios": [1.0, 1.0, 1.08]},
        constrained_layout=True,
    )

    for ax, crop, title, label in [
        (axes[0], src_crop, r"$I_s$ crop", "(a)"),
        (axes[1], dec_crop, r"$I_d$ crop", "(b)"),
    ]:
        ax.imshow(crop, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_title(title, pad=3)
        clean_image_axis(ax)
        panel_label(ax, label)

    ax = axes[2]
    bins = np.arange(-0.5, 256.5, 1.0)
    counts, _, _ = ax.hist(diff.ravel(), bins=bins, color=C_BLUE, alpha=0.82, linewidth=0)
    ax.set_yscale("log")
    ax.set_xlim(-1, 8)
    ax.set_ylim(0.8, max(total * 1.7, 10))
    ax.set_title("Residual distribution", pad=3)
    ax.set_xlabel(r"$|I_s-I_d|$")
    ax.set_ylabel("Pixels")
    ax.xaxis.set_major_locator(ticker.FixedLocator([0, 2, 4, 6, 8]))
    ax.yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
    ax.grid(axis="y", color=C_GRID, linewidth=0.45, alpha=0.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    panel_label(ax, "(c)", dark=False)

    ax.text(
        0.97,
        0.92,
        "\n".join(
            [
                rf"$\max\Delta={max_delta}$",
                rf"$N_{{\Delta>0}}={nonzero}$",
                rf"$\mathrm{{MSE}}={mse:.0f}$",
            ]
        ),
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=C_DARK,
        bbox=dict(boxstyle="round,pad=0.28", facecolor="white", edgecolor=C_GRID, linewidth=0.6),
    )

    if counts[0] > 0:
        ax.annotate(
            "all pixels",
            xy=(0, counts[0]),
            xytext=(2.2, total * 0.72),
            ha="left",
            va="center",
            fontsize=8,
            arrowprops=dict(arrowstyle="-", color=C_DARK, linewidth=0.55),
        )

    fig.savefig(FIG / "fig_difference.png")
    plt.close(fig)


if __name__ == "__main__":
    image_panel()
    histogram_panel()
    metrics_panel()
    difference_panel()
    print(f"Figures saved to: {FIG}")
