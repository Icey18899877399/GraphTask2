# gen_figures.py
# 在 实验2 文件夹下运行：python gen_figures.py
# 需要安装：pip install Pillow matplotlib

from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

# ========== 1. BMP 转 PNG ==========
for name in ['b8gray', 'Ise', 'd']:
    bmp = name + '.bmp'
    png = name + '.png'
    if os.path.exists(bmp):
        img = Image.open(bmp)
        img.save(png)
        print(f'{bmp} -> {png}')
    else:
        print(f'[WARN] {bmp} not found, skip')

# ========== 2. 读取 txt 数据 ==========
def read_float(path):
    x, y = [], []
    with open(path) as f:
        for line in f:
            parts = line.strip().split('\t')
            x.append(int(parts[0]))
            y.append(float(parts[1]))
    return np.array(x), np.array(y)

def read_int(path):
    x, y = [], []
    with open(path) as f:
        for line in f:
            parts = line.strip().split('\t')
            x.append(int(parts[0]))
            y.append(int(parts[1]))
    return np.array(x), np.array(y)

# ========== 3. 绘制直方图 ==========
hist_plots = [
    ('Hs.txt',  'fig_Hs.png',  'Hs (Source Image Histogram)',    'steelblue'),
    ('Hdd.txt', 'fig_Hdd.png', 'Hdd (Target Histogram, y=sin(x))', 'coral'),
    ('Hse.txt', 'fig_Hse.png', 'Hse (Equalized Image Histogram)', 'teal'),
    ('Hd.txt',  'fig_Hd.png',  'Hd (Specified Image Histogram)',  'purple'),
]

for txt, png, title, color in hist_plots:
    if not os.path.exists(txt):
        print(f'[WARN] {txt} not found, skip')
        continue
    x, y = read_float(txt)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(x, y, width=1, color=color, edgecolor='none')
    ax.set_xlabel('Gray Level')
    ax.set_ylabel('Probability')
    ax.set_title(title)
    ax.set_xlim(-1, 256)
    plt.tight_layout()
    plt.savefig(png, dpi=150)
    plt.close()
    print(f'{txt} -> {png}')

# ========== 4. 绘制变换函数 ==========
trans_plots = [
    ('Tse.txt', 'fig_Tse.png', 'Tse (Equalization Transform)',                'green'),
    ('Td.txt',  'fig_Td.png',  'Td (Specification Transform)',                'darkred'),
    ('Tde.txt', 'fig_Tde.png', 'Tde (Equalization Transform of Specified Image)', 'navy'),
]

for txt, png, title, color in trans_plots:
    if not os.path.exists(txt):
        print(f'[WARN] {txt} not found, skip')
        continue
    x, y = read_int(txt)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(x, y, color=color, linewidth=1.2)
    ax.set_xlabel('Input Gray Level')
    ax.set_ylabel('Output Gray Level')
    ax.set_title(title)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    plt.tight_layout()
    plt.savefig(png, dpi=150)
    plt.close()
    print(f'{txt} -> {png}')

print('\nDone! All figures generated.')