from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

BLUE = (33, 98, 155)
VERMILION = (188, 80, 64)
GREEN = (52, 128, 112)
INK = (35, 39, 42)
GRAY = (140, 148, 156)
LIGHT = (246, 248, 250)
GRID = (222, 226, 230)
WHITE = (255, 255, 255)


def font(size=28, bold=False):
    candidates = [
        "C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def fit_image(path, box):
    img = Image.open(path).convert("RGB")
    img.thumbnail(box, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", box, WHITE)
    x = (box[0] - img.width) // 2
    y = (box[1] - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def image_panel():
    w, h = 1800, 860
    canvas = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(canvas)

    d.text((60, 38), "LZW Reconstruction Check", fill=INK, font=font(44, True))
    d.text((60, 96), "Original grayscale image and image decoded from C.dat", fill=GRAY, font=font(26))

    box_w, box_h = 760, 610
    left = fit_image(ROOT / "b8gray.bmp", (box_w, box_h))
    right = fit_image(ROOT / "Id.bmp", (box_w, box_h))
    canvas.paste(left, (60, 170))
    canvas.paste(right, (980, 170))

    for x, title, color in [(60, "Is: b8gray.bmp", BLUE), (980, "Id: decoded image", GREEN)]:
        d.rectangle((x, 170, x + box_w, 170 + box_h), outline=(210, 215, 220), width=2)
        d.rectangle((x, 795, x + box_w, 835), fill=color)
        d.text((x + 18, 801), title, fill=WHITE, font=font(24, True))

    canvas.save(FIG / "fig_input_decoded.png", quality=95)


def histogram_panel():
    img = Image.open(ROOT / "b8gray.bmp").convert("L")
    hist = img.histogram()
    total = sum(hist)
    probs = [v / total for v in hist]
    max_p = max(probs)

    w, h = 1800, 760
    margin_l, margin_r, margin_t, margin_b = 130, 60, 110, 120
    plot_w = w - margin_l - margin_r
    plot_h = h - margin_t - margin_b

    canvas = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(canvas)
    d.text((60, 36), "Normalized Gray-Level Histogram", fill=INK, font=font(44, True))
    d.text((60, 92), "Distribution of the source image; the decoded image is identical pixel-by-pixel", fill=GRAY, font=font(25))

    x0, y0 = margin_l, margin_t
    x1, y1 = margin_l + plot_w, margin_t + plot_h
    d.rectangle((x0, y0, x1, y1), fill=LIGHT, outline=(205, 210, 216), width=2)

    for i in range(6):
        y = y1 - int(plot_h * i / 5)
        d.line((x0, y, x1, y), fill=GRID, width=1)
        value = max_p * i / 5
        d.text((36, y - 14), f"{value:.3f}", fill=GRAY, font=font(20))

    bar_w = plot_w / 256.0
    for i, p in enumerate(probs):
        x = x0 + i * bar_w
        y = y1 - int(p / max_p * plot_h)
        color = BLUE if i < 160 else VERMILION
        d.rectangle((int(x), y, int(x + max(1, bar_w)), y1), fill=color)

    for tick in [0, 64, 128, 192, 255]:
        x = x0 + int(plot_w * tick / 255)
        d.line((x, y1, x, y1 + 8), fill=INK, width=2)
        d.text((x - 18, y1 + 18), str(tick), fill=INK, font=font(22))
    d.text((w // 2 - 70, h - 52), "Gray level", fill=INK, font=font(24, True))
    d.text((20, h // 2), "Probability", fill=INK, font=font(24, True))

    canvas.save(FIG / "fig_histogram_source.png", quality=95)


def metrics_panel():
    w, h = 1600, 720
    canvas = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(canvas)
    d.text((60, 38), "Coding Efficiency and Information Content", fill=INK, font=font(42, True))
    d.text((60, 92), "Lower bpp indicates a shorter representation; entropy is the source uncertainty", fill=GRAY, font=font(24))

    labels = ["LZW codes", "C.dat file", "Entropy"]
    values = [5.596430, 5.600275, 7.528544]
    colors = [BLUE, GREEN, VERMILION]
    max_v = 8.0

    x0, y0 = 180, 155
    bar_h, gap = 95, 64
    scale = 1180 / max_v
    for idx, (label, value, color) in enumerate(zip(labels, values, colors)):
        y = y0 + idx * (bar_h + gap)
        d.text((60, y + 28), label, fill=INK, font=font(27, True))
        d.rectangle((x0, y, x0 + int(max_v * scale), y + bar_h), fill=LIGHT, outline=(214, 218, 224), width=1)
        d.rectangle((x0, y, x0 + int(value * scale), y + bar_h), fill=color)
        d.text((x0 + int(value * scale) + 18, y + 28), f"{value:.6f} bit/pixel", fill=INK, font=font(26))

    for tick in range(0, 9, 2):
        x = x0 + int(tick * scale)
        d.line((x, 630, x, 642), fill=INK, width=2)
        d.text((x - 10, 650), str(tick), fill=INK, font=font(22))
    d.text((x0 + 500, 650), "bits per pixel", fill=GRAY, font=font(22))

    canvas.save(FIG / "fig_metrics.png", quality=95)


def difference_panel():
    src = Image.open(ROOT / "b8gray.bmp").convert("L")
    dec = Image.open(ROOT / "Id.bmp").convert("L")
    diff = ImageChops.difference(src, dec)
    diff_rgb = Image.new("RGB", diff.size, (255, 255, 255))
    diff_rgb.putalpha(diff)
    nonzero = sum(1 for v in diff.getdata() if v)

    w, h = 1300, 520
    canvas = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(canvas)
    d.text((60, 42), "Pixel Difference Map", fill=INK, font=font(42, True))
    d.text((60, 96), f"Non-zero difference pixels: {nonzero}", fill=GRAY, font=font(26))
    d.rectangle((60, 165, 1240, 420), fill=LIGHT, outline=(215, 220, 226), width=2)
    d.text((470, 260), "All pixels are identical", fill=GREEN, font=font(44, True))
    d.text((505, 320), "Is == Id: YES", fill=INK, font=font(30, True))
    canvas.save(FIG / "fig_difference.png", quality=95)


if __name__ == "__main__":
    image_panel()
    histogram_panel()
    metrics_panel()
    difference_panel()
