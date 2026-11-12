# -*- coding: utf-8 -*-
"""EEG-MAS 架构图——紧凑版修订:1) 泳道灰底条改虚线框;2) 全部箭头垂直/水平走线、
箭头贴目标框边;3) 旁路线走泳道外白区;4) 标签避让重算,无遮挡。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle, Polygon

plt.rcParams.update({"font.family": "Arial", "font.size": 7.5})

OUT_FIG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\eeg_multi_agent\outputs\figures\fig_system_architecture_ref_compact.png"
DELIVER_PNG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS架构图(紧凑版).png"

INK = "#1a1a1a"
GREY = "#666666"
RED = "#B03A2E"

fig, ax = plt.subplots(figsize=(8.6, 10.4))
ax.set_xlim(0, 97)
ax.set_ylim(0, 116)
ax.axis("off")


# ---------------- 小图标(s=0.75 细线) ----------------
def ic_wave(c, cx, cy, s=0.75):
    t = np.linspace(0, 4.2 * np.pi, 100)
    y = np.sin(t) + 0.4 * np.sin(2.6 * t + 0.7)
    ax.plot(cx - 2.0 * s + np.linspace(0, 1, 100) * 4.0 * s, cy + y * 0.7 * s,
            color=c, lw=0.85, solid_capstyle="round", zorder=7)

def ic_spectrum(c, cx, cy, s=0.75):
    for i, f in enumerate([0.9, 0.62, 0.40, 0.24, 0.12]):
        ax.add_patch(Rectangle((cx - 1.9 * s + i * 0.95 * s, cy - 0.9 * s),
                               0.6 * s, f * 1.9 * s, facecolor=c, edgecolor="none", zorder=7))

def ic_wavelet(c, cx, cy, s=0.75):
    t = np.linspace(0, 1, 80)
    y = np.exp(-3.2 * t) * np.sin(10 * np.pi * t)
    ax.plot(cx - 2.0 * s + t * 4.0 * s, cy + y * 1.2 * s, color=c, lw=0.85, zorder=7)

def ic_spike(c, cx, cy, s=0.75):
    x = np.array([0, .16, .26, .40, .52, .64, .76, .88, 1])
    y = np.array([0, .05, -.55, 1, -.05, .02, -.68, .04, 0])
    ax.plot(cx - 2.0 * s + x * 4.0 * s, cy + y * 1.1 * s, color=c, lw=0.85, zorder=7)

def ic_nn(c, cx, cy, s=0.75):
    L = [[(-1.4, -0.55), (-1.4, 0.55)], [(0, -1.0), (0, 0), (0, 1.0)], [(1.4, -0.55), (1.4, 0.55)]]
    for a in L[0]:
        for b in L[1]:
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s],
                    color=c, lw=0.4, zorder=7)
    for a in L[1]:
        for b in L[2]:
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s],
                    color=c, lw=0.4, zorder=7)
    for layer in L:
        for p in layer:
            ax.add_patch(Circle((cx + p[0] * s, cy + p[1] * s), 0.2 * s,
                                facecolor="white", edgecolor=c, lw=0.75, zorder=8))

def ic_tree(c, cx, cy, s=0.75):
    ax.plot([cx, cx], [cy - 1.0 * s, cy + 0.1 * s], color=c, lw=0.95, zorder=7)
    for dx, dy in [(-0.9, 0.9), (0, 1.1), (0.9, 0.9)]:
        ax.plot([cx, cx + dx * s], [cy + 0.1 * s, cy + dy * s], color=c, lw=0.85, zorder=7)
        ax.add_patch(Circle((cx + dx * s, cy + dy * s), 0.19 * s, facecolor=c,
                            edgecolor="none", zorder=8))

def ic_gauge(c, cx, cy, s=0.75):
    th = np.linspace(0, np.pi, 40)
    ax.plot(cx + np.cos(th) * 1.0 * s, cy - 0.4 * s + np.sin(th) * 0.9 * s,
            color=c, lw=0.85, zorder=7)
    ax.plot([cx, cx + 0.6 * s], [cy - 0.4 * s, cy + 0.45 * s], color=c, lw=0.85, zorder=8)
    ax.add_patch(Circle((cx, cy - 0.4 * s), 0.13 * s, facecolor=c, edgecolor="none", zorder=8))

def ic_weights(c, cx, cy, s=0.75):
    ax.plot([cx - 1.6 * s, cx + 1.6 * s], [cy, cy], color=c, lw=0.85, zorder=7)
    for dx, dy in [(-1.0, 0.4), (0.3, -0.4), (1.3, 0.4)]:
        ax.plot([cx + dx * s, cx + dx * s], [cy - 0.9 * s, cy + 0.9 * s],
                color=c, lw=0.75, zorder=7)
        ax.add_patch(Circle((cx + dx * s, cy + dy * s), 0.22 * s, facecolor="white",
                            edgecolor=c, lw=0.75, zorder=8))

def ic_merge(c, cx, cy, s=0.75):
    for dy in (-0.8, 0.8):
        ax.plot([cx - 1.7 * s, cx - 0.3 * s], [cy + dy * s, cy + dy * s],
                color=c, lw=0.85, zorder=7)
        ax.plot([cx - 0.3 * s, cx + 0.9 * s], [cy + dy * s, cy], color=c, lw=0.85, zorder=7)
    ax.add_patch(FancyArrowPatch((cx + 0.7 * s, cy), (cx + 1.8 * s, cy), arrowstyle="-|>",
                                 mutation_scale=6, color=c, lw=0.85, zorder=7))

def ic_vote(c, cx, cy, s=0.75):
    for i, f in enumerate([0.45, 0.95, 0.62]):
        ax.add_patch(Rectangle((cx - 1.4 * s + i * 1.1 * s, cy - 0.8 * s),
                               0.7 * s, f * 1.6 * s, facecolor=c, edgecolor="none",
                               alpha=0.85, zorder=7))

def ic_warn(c, cx, cy, s=0.75):
    ax.add_patch(Polygon([[cx - 1.1 * s, cy - 0.85 * s], [cx + 1.1 * s, cy - 0.85 * s],
                          [cx, cy + 0.95 * s]], closed=True, facecolor="none",
                         edgecolor=c, lw=0.95, zorder=7))
    ax.plot([cx, cx], [cy - 0.45 * s, cy + 0.15 * s], color=c, lw=0.85, zorder=8)
    ax.add_patch(Circle((cx, cy - 0.62 * s), 0.1 * s, facecolor=c, edgecolor="none", zorder=8))

def ic_loop(c, cx, cy, s=0.75):
    ax.add_patch(FancyArrowPatch((cx - 0.9 * s, cy), (cx + 0.9 * s, cy),
                                 connectionstyle="arc3,rad=1.0", arrowstyle="-|>",
                                 mutation_scale=6, color=c, lw=0.95, zorder=7))

def ic_check(c, cx, cy, s=0.75):
    ax.plot([cx - 0.9 * s, cx - 0.15 * s, cx + 1.0 * s],
            [cy - 0.1 * s, cy - 0.8 * s, cy + 0.85 * s],
            color=c, lw=1.2, solid_capstyle="round", zorder=7)

def ic_bulb(c, cx, cy, s=0.75):
    ax.add_patch(Circle((cx, cy + 0.25 * s), 0.65 * s, facecolor="none", edgecolor=c,
                        lw=0.85, zorder=7))
    ax.plot([cx - 0.28 * s, cx - 0.28 * s], [cy - 0.45 * s, cy - 0.95 * s],
            color=c, lw=0.85, zorder=7)
    ax.plot([cx + 0.28 * s, cx + 0.28 * s], [cy - 0.45 * s, cy - 0.95 * s],
            color=c, lw=0.85, zorder=7)

def ic_chart(c, cx, cy, s=0.75):
    x = np.array([0, .22, .22, .5, .5, .78, .78, 1])
    y = np.array([.05, .05, .35, .35, .68, .68, .95, .95])
    ax.plot(cx - 1.4 * s + x * 2.8 * s, cy - 0.9 * s + y * 1.8 * s, color=c, lw=0.95, zorder=7)
    ax.plot([cx - 1.5 * s, cx + 1.5 * s], [cy + 0.72 * s] * 2, color=c, lw=0.65,
            ls=(0, (3, 2)), zorder=7)

def ic_doc(c, cx, cy, s=0.75):
    ax.add_patch(Rectangle((cx - 0.7 * s, cy - 1.0 * s), 1.4 * s, 2.0 * s,
                           facecolor="none", edgecolor=c, lw=0.85, zorder=7))
    for i in range(3):
        yy = cy + 0.5 * s - i * 0.5 * s
        ax.plot([cx - 0.4 * s, cx + 0.4 * s], [yy, yy], color=c, lw=0.65, zorder=8)


# ---------------- 基础绘制 ----------------
def box(x, y, w, h, label, icon=None, sub=None, edge=INK, lw=0.9, ls="-",
        msize=7.5, ssize=6.2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=edge,
                           linewidth=lw, linestyle=ls, zorder=4))
    if icon:
        icon(edge, x + 3.0, y + h / 2, 0.75)
        tx = (x + 5.6 + x + w) / 2
    else:
        tx = x + w / 2
    if sub:
        ax.text(tx, y + h * 0.63, label, ha="center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=6)
        ax.text(tx, y + h * 0.24, sub, ha="center", va="center",
                fontsize=ssize, color="#333333", zorder=6, linespacing=1.25)
    else:
        ax.text(tx, y + h / 2, label, ha="center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=6)


def band(x, y, w, h, label):
    """泳道:虚线边框、无填充;标签在框外左上。"""
    ax.add_patch(Rectangle((x, y), w, h, facecolor="none", edgecolor="#999999",
                           linewidth=0.8, linestyle=(0, (5, 3)), zorder=1))
    ax.text(x + 0.3, y + h + 0.6, label, fontsize=6.5, style="italic", color=GREY,
            zorder=2, va="bottom", ha="left")


def arrow(x1, y1, x2, y2, color=INK, dashed=False, lw=0.85):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=7, color=color, linewidth=lw,
                                 linestyle=(0, (4, 2)) if dashed else "-",
                                 shrinkA=0, shrinkB=0, zorder=5))


def seg(x1, y1, x2, y2, color=INK, lw=0.85, dashed=False):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw,
            linestyle=(0, (4, 2)) if dashed else "-", zorder=5, solid_capstyle="butt")


# ================= 输入 =================
box(24, 109, 48, 5, "Input: 19-ch EEG epochs (250 Hz, 2 s)", icon=ic_wave)
arrow(38, 109, 25, 102.7)                       # → quality gating 框顶

# raw epochs 旁路(全部走泳道外白区 x=90)
seg(72, 111.5, 90, 111.5)
seg(90, 111.5, 90, 60)
ax.text(92.6, 86, "raw epochs", rotation=90, fontsize=6, color=GREY,
        ha="center", va="center")

# ================= 协调层 =================
band(2, 95, 86, 8, "Coordination layer")
box(5, 96.5, 40, 6, "Quality gating", icon=ic_gauge, sub="SNR, artifact ratio")
box(48, 96.5, 36, 6, "Dynamic weighting", icon=ic_weights, sub="val-initialised, online")
arrow(45, 99.5, 48, 99.5)

# ================= 特征层 =================
band(2, 72, 86, 20, "Feature layer")
arrow(66, 96.5, 66, 89.7)                       # weighting → 分配线
seg(13, 89.5, 76, 89.5)
for xc in (13, 34, 55, 76):
    arrow(xc, 89.5, xc, 87.2)
box(4, 81, 18, 6, "Time", icon=ic_wave, sub="228-d", msize=7.2, ssize=6.2)
box(25, 81, 18, 6, "Frequency", icon=ic_spectrum, sub="152-d", msize=7.2, ssize=6.2)
box(46, 81, 18, 6, "Time–freq", icon=ic_wavelet, sub="152-d", msize=7.2, ssize=6.2)
box(67, 81, 18, 6, "Event", icon=ic_spike, sub="82-d", msize=7.2, ssize=6.2)
for xc in (13, 34, 55, 76):
    arrow(xc, 81, xc, 79.2)
box(16, 74, 48, 5, "Concatenation → 614-d", icon=ic_merge)

# ================= 诊断层 =================
band(2, 40, 86, 27.5, "Diagnosis layer")
arrow(40, 74, 20, 67.2)                         # concat → LightGBM
ax.text(32, 71.8, "mRMR → 128-d", fontsize=6, color=GREY, va="center")
box(4, 56, 32, 11, "LightGBM", icon=ic_tree,
    sub="mRMR-128 features\n(feature path)", msize=7.5, ssize=6.2)
# 信号旁路分支
seg(48, 60, 90, 60)
for xc in (48, 64, 79):
    arrow(xc, 60, xc, 58.2)
box(40, 51.5, 16, 6, "EEGNet", icon=ic_nn, sub="signal path", msize=7.2, ssize=6)
box(58, 51.5, 13, 6, "TCN", icon=ic_nn, sub="signal path", msize=7.2, ssize=6)
box(73, 51.5, 13, 6, "Transformer", icon=ic_nn, sub="signal path", msize=6.8, ssize=6)
# 融合
box(10, 42.5, 72, 6, "Weighted soft voting", icon=ic_vote,
    sub="stacking meta-learner, weights updated online", msize=7.5, ssize=6.2)
arrow(20, 56, 20, 48.7)
arrow(48, 51.5, 48, 48.7)
arrow(64, 51.5, 64, 48.7)
arrow(79, 51.5, 79, 48.7)

# ================= 分歧检测 + 二次仲裁 =================
box(4, 29.5, 56, 10, "Disagreement detection", icon=ic_warn,
    sub="prob-diff ≥ 0.30 · majority < 0.60 · entropy ≥ 1.099\n(calibrated trigger rate: 39.7%)",
    msize=7.5, ssize=6.2)
arrow(32, 42.5, 32, 39.7)                       # 融合 → 分歧(垂直)
box(66, 29.5, 22, 10, "Second-pass arbitration", icon=ic_loop,
    sub="attention-weighted\nconsensus", edge=RED, lw=1.0, ls=(0, (4, 2)),
    msize=6.8, ssize=6.2)
arrow(60, 34.5, 66, 34.5, color=RED, dashed=True)
ax.text(63, 36.3, "trigger", fontsize=6, color=RED, ha="center")
seg(88, 34.5, 91, 34.5, color=RED, dashed=True)
seg(91, 34.5, 91, 45.5, color=RED, dashed=True)
arrow(91, 45.5, 82.3, 45.5, color=RED, dashed=True)
ax.text(86.5, 47, "refine", fontsize=6, color=RED, ha="center")

# ================= 验证层 =================
band(2, 16, 86, 10, "Validation layer")
arrow(32, 29.5, 32, 26.2)                       # 分歧 → 验证(垂直)
seg(18, 26, 74, 26)
arrow(18, 26, 18, 23.2)
arrow(74, 26, 74, 23.2)
box(4, 17, 30, 6, "Consistency agent", icon=ic_check, msize=7.2)
box(58, 17, 30, 6, "Explainability agent", icon=ic_bulb, msize=7.2)

# ================= 输出(并排) =================
box(4, 7, 38, 6, "Subject aggregation", icon=ic_chart, sub="p90 over epochs",
    msize=7.2, ssize=6.2)
box(56, 7, 36, 6, "Output", icon=ic_doc, sub="Normal/Abnormal + explanation",
    msize=7.2, ssize=6.2)
arrow(19, 17, 19, 13.2)
arrow(73, 17, 74, 13.2)
arrow(42, 10, 56, 10)

# ================= 图例 =================
seg(2, 2.5, 5, 2.5)
ax.text(6, 2.5, "data flow", fontsize=6, color=GREY, va="center")
seg(20, 2.5, 23, 2.5, color=RED, dashed=True)
ax.text(24, 2.5, "arbitration feedback", fontsize=6, color=GREY, va="center")
ax.add_patch(Rectangle((46, 1.9), 3, 1.2, facecolor="none", edgecolor="#999999",
                       lw=0.8, linestyle=(0, (5, 3))))
ax.text(50.5, 2.5, "system layer", fontsize=6, color=GREY, va="center")

fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(DELIVER_PNG, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figure saved")
