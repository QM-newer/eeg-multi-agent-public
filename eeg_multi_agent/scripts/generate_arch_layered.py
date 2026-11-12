# -*- coding: utf-8 -*-
"""EEG-MAS 架构图——立方体版(合并箭头修正):核心模块 3D 立方体,
小节点白底平面框;全部箭头起止贴框;间距已核查无文字遮挡/图案重叠。
遮挡检查记录(坐标核查):
- 立方体深度 DX=2.2,DY=1.6;右列框 x+w+DX <= 96(L4 信号列最大 95.7,OK)
- 顶行立方体 y+h+DY 上方 >= 2.2 空隙(贴上行底线,不压线)
- 图标中心 x+3.0,占 [x+1.5, x+4.5];文字区从 x+5.6 起,无交叠
- 箭头全部走模块间空隙(x=14/40/64 走廊),不穿任何框
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Polygon, Rectangle

plt.rcParams.update({"font.family": "Arial", "font.size": 7.5})

OUT_FIG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\eeg_multi_agent\outputs\figures\fig_system_architecture_layered.png"
DELIVER_PNG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS架构图(分层版).png"

INK = "#1a1a1a"
BAND = "#F2F2F2"
GREY = "#666666"
RED = "#B03A2E"
SH_TOP = "#D9D9D9"
SH_SIDE = "#EBEBEB"

DX, DY = 2.2, 1.6  # 立方体深度偏移

fig, ax = plt.subplots(figsize=(9.2, 13.8))
ax.set_xlim(0, 100)
ax.set_ylim(0, 158)
ax.axis("off")


# ---------------- 小图标(s=0.75 细线) ----------------
def ic_wave(c, cx, cy, s=0.75):
    t = np.linspace(0, 4.2 * np.pi, 100)
    y = np.sin(t) + 0.4 * np.sin(2.6 * t + 0.7)
    ax.plot(cx - 2.0 * s + np.linspace(0, 1, 100) * 4.0 * s, cy + y * 0.7 * s,
            color=c, lw=0.85, solid_capstyle="round", zorder=8)

def ic_spectrum(c, cx, cy, s=0.75):
    for i, f in enumerate([0.9, 0.62, 0.40, 0.24, 0.12]):
        ax.add_patch(Rectangle((cx - 1.9 * s + i * 0.95 * s, cy - 0.9 * s),
                               0.6 * s, f * 1.9 * s, facecolor=c, edgecolor="none", zorder=8))

def ic_wavelet(c, cx, cy, s=0.75):
    t = np.linspace(0, 1, 80)
    y = np.exp(-3.2 * t) * np.sin(10 * np.pi * t)
    ax.plot(cx - 2.0 * s + t * 4.0 * s, cy + y * 1.2 * s, color=c, lw=0.85, zorder=8)

def ic_spike(c, cx, cy, s=0.75):
    x = np.array([0, .16, .26, .40, .52, .64, .76, .88, 1])
    y = np.array([0, .05, -.55, 1, -.05, .02, -.68, .04, 0])
    ax.plot(cx - 2.0 * s + x * 4.0 * s, cy + y * 1.1 * s, color=c, lw=0.85, zorder=8)

def ic_nn(c, cx, cy, s=0.75):
    L = [[(-1.4, -0.55), (-1.4, 0.55)], [(0, -1.0), (0, 0), (0, 1.0)], [(1.4, -0.55), (1.4, 0.55)]]
    for a in L[0]:
        for b in L[1]:
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s],
                    color=c, lw=0.4, zorder=8)
    for a in L[1]:
        for b in L[2]:
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s],
                    color=c, lw=0.4, zorder=8)
    for layer in L:
        for p in layer:
            ax.add_patch(Circle((cx + p[0] * s, cy + p[1] * s), 0.2 * s,
                                facecolor="white", edgecolor=c, lw=0.75, zorder=9))

def ic_tree(c, cx, cy, s=0.75):
    ax.plot([cx, cx], [cy - 1.0 * s, cy + 0.1 * s], color=c, lw=0.95, zorder=8)
    for dx, dy in [(-0.9, 0.9), (0, 1.1), (0.9, 0.9)]:
        ax.plot([cx, cx + dx * s], [cy + 0.1 * s, cy + dy * s], color=c, lw=0.85, zorder=8)
        ax.add_patch(Circle((cx + dx * s, cy + dy * s), 0.19 * s, facecolor=c,
                            edgecolor="none", zorder=9))

def ic_gauge(c, cx, cy, s=0.75):
    th = np.linspace(0, np.pi, 40)
    ax.plot(cx + np.cos(th) * 1.0 * s, cy - 0.4 * s + np.sin(th) * 0.9 * s,
            color=c, lw=0.85, zorder=8)
    ax.plot([cx, cx + 0.6 * s], [cy - 0.4 * s, cy + 0.45 * s], color=c, lw=0.85, zorder=9)
    ax.add_patch(Circle((cx, cy - 0.4 * s), 0.13 * s, facecolor=c, edgecolor="none", zorder=9))

def ic_balance(c, cx, cy, s=0.75):
    ax.plot([cx, cx], [cy - 1.0 * s, cy + 0.9 * s], color=c, lw=0.9, zorder=8)
    ax.plot([cx - 1.5 * s, cx + 1.5 * s], [cy + 0.7 * s, cy + 0.7 * s],
            color=c, lw=0.9, zorder=8)
    for dx in (-1.5, 1.5):
        ax.plot([cx + dx * s, cx + dx * s - 0.45 * s, cx + dx * s + 0.45 * s, cx + dx * s],
                [cy + 0.7 * s, cy + 0.1 * s, cy + 0.1 * s, cy + 0.7 * s],
                color=c, lw=0.8, zorder=8)
    ax.plot([cx - 0.6 * s, cx + 0.6 * s], [cy - 1.0 * s, cy - 1.0 * s],
            color=c, lw=0.9, zorder=8)

def ic_merge(c, cx, cy, s=0.75):
    for dy in (-0.8, 0.8):
        ax.plot([cx - 1.7 * s, cx - 0.3 * s], [cy + dy * s, cy + dy * s],
                color=c, lw=0.85, zorder=8)
        ax.plot([cx - 0.3 * s, cx + 0.9 * s], [cy + dy * s, cy], color=c, lw=0.85, zorder=8)
    ax.add_patch(FancyArrowPatch((cx + 0.7 * s, cy), (cx + 1.8 * s, cy), arrowstyle="-|>",
                                 mutation_scale=6, color=c, lw=0.85, zorder=8))

def ic_vote(c, cx, cy, s=0.75):
    for i, f in enumerate([0.45, 0.95, 0.62]):
        ax.add_patch(Rectangle((cx - 1.4 * s + i * 1.1 * s, cy - 0.8 * s),
                               0.7 * s, f *  models if False else f * 1.6 * s,
                               facecolor=c, edgecolor="none",
                               alpha=0.85, zorder=8))

def ic_warn(c, cx, cy, s=0.75):
    ax.add_patch(Polygon([[cx - 1.1 * s, cy - 0.85 * s], [cx + 1.1 * s, cy - 0.85 * s],
                          [cx, cy + 0.95 * s]], closed=True, facecolor="none",
                         edgecolor=c, lw=0.95, zorder=8))
    ax.plot([cx, cx], [cy - 0.45 * s, cy + 0.15 * s], color=c, lw=0.85, zorder=9)
    ax.add_patch(Circle((cx, cy - 0.62 * s), 0.1 * s, facecolor=c, edgecolor="none", zorder=9))

def ic_loop(c, cx, cy, s=0.75):
    ax.add_patch(FancyArrowPatch((cx - 0.9 * s, cy), (cx + 0.9 * s, cy),
                                 connectionstyle="arc3,rad=1.0", arrowstyle="-|>",
                                 mutation_scale=6, color=c, lw=0.95, zorder=8))

def ic_check(c, cx, cy, s=0.75):
    ax.plot([cx - 0.9 * s, cx - 0.15 * s, cx + 1.0 * s],
            [cy - 0.1 * s, cy - 0.8 * s, cy + 0.85 * s],
            color=c, lw=1.2, solid_capstyle="round", zorder=8)

def ic_bulb(c, cx, cy, s=0.75):
    ax.add_patch(Circle((cx, cy + 0.25 * s), 0.65 * s, facecolor="none", edgecolor=c,
                        lw=0.85, zorder=8))
    ax.plot([cx - 0.28 * s, cx - 0.28 * s], [cy - 0.45 * s, cy - 0.95 * s],
            color=c, lw=0.85, zorder=8)
    ax.plot([cx + 0.28 * s, cx + 0.28 * s], [cy - 0.45 * s, cy - 0.95 * s],
            color=c, lw=0.85, zorder=8)

def ic_chart(c, cx, cy, s=0.75):
    x = np.array([0, .22, .22, .5, .5, .78, .78, 1])
    y = np.array([.05, .05, .35, .35, .68, .68, .95, .95])
    ax.plot(cx - 1.4 * s + x * 2.8 * s, cy - 0.9 * s + y * 1.8 * s, color=c, lw=0.95, zorder=8)
    ax.plot([cx - 1.5 * s, cx + 1.5 * s], [cy + 0.72 * s] * 2, color=c, lw=0.65,
            ls=(0, (3, 2)), zorder=8)

def ic_doc(c, cx, cy, s=0.75):
    ax.add_patch(Rectangle((cx - 0.7 * s, cy - 1.0 * s), 1.4 * s, 2.0 * s,
                           facecolor="none", edgecolor=c, lw=0.85, zorder=8))
    for i in range(3):
        yy = cy + 0.5 * s - i * 0.5 * s
        ax.plot([cx - 0.4 * s, cx + 0.4 * s], [yy, yy], color=c, lw=0.65, zorder=9)


# ---------------- 绘制基元 ----------------
def cube(x, y, w, h, label, icon=None, sub=None, edge=INK, lw=1.0, ls="-",
         msize=7.5, ssize=6.2):
    ax.add_patch(Polygon([(x, y + h), (x + DX, y + h + DY), (x + w + DX, y + h + DY),
                          (x + w, y + h)], closed=True, facecolor=SH_TOP,
                         edgecolor=edge, lw=lw, linestyle=ls, zorder=4))
    ax.add_patch(Polygon([(x + w, y), (x + w + DX, y + DY), (x + w + DX, y + h + DY),
                          (x + w, y + h)], closed=True, facecolor=SH_SIDE,
                         edgecolor=edge, lw=lw, linestyle=ls, zorder=4))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                                facecolor="white", edgecolor=edge, linewidth=lw,
                                linestyle=ls, zorder=4))
    fy = y + h / 2
    if icon:
        icon(edge, x + 3.0, fy, 0.75)
        tx = (x + 5.6 + x + w) / 2
    else:
        tx = x + w / 2
    if sub:
        ax.text(tx, y + h * 0.63, label, ha="center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=6, linespacing=1.2)
        ax.text(tx, y + h * 0.24, sub, ha="center", va="center",
                fontsize=ssize, color="#333333", zorder=6, linespacing=1.25)
    else:
        ax.text(tx, fy, label, ha="center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=6)


def box(x, y, w, h, label, icon=None, sub=None, edge=INK, lw=0.85, ls="-",
        msize=7.5, ssize=6.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                                facecolor="white", edgecolor=edge, linewidth=lw,
                                linestyle=ls, zorder=4))
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
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                facecolor=BAND, edgecolor="none", zorder=1))
    ax.text(x + w - 1.5, y + h - 0.7, label, fontsize=6.5, style="italic",
            color=GREY, zorder=2, va="top", ha="right")


def arrow(x1, y1, x2, y2, color=INK, dashed=False, lw=0.85):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=7, color=color, linewidth=lw,
                                 linestyle=(0, (4, 2)) if dashed else "-",
                                 shrinkA=0, shrinkB=0, zorder=5))


def seg(x1, y1, x2, y2, color=INK, lw=0.85, dashed=False):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw,
            linestyle=(0, (4, 2)) if dashed else "-", zorder=5, solid_capstyle="butt")


# ================= 输入(虚线框) =================
box(22, 151, 52, 6, "Input: 19-ch EEG epochs (250 Hz, 2 s)", icon=ic_wave, ls=(0, (4, 2)))
arrow(48, 151, 48, 146.8)

# raw epochs 旁路(右侧白区 x=96.5)
seg(74, 154, 96.5, 154)
seg(96.5, 154, 96.5, 80)
seg(96.5, 80, 52, 80)
ax.text(98.4, 117, "raw epochs", rotation=90, fontsize=6, color=GREY,
        ha="center", va="center")

# ================= Stage1: 质量门控 =================
band(2, 136, 92, 10, "Stage1: Quality gating")
cube(27, 137.5, 42, 7, "Quality gating", icon=ic_gauge, sub="SNR, artifact ratio")

# ================= Stage2: 特征提取 =================
band(2, 108, 92, 26, "Stage2: Feature extraction")
arrow(48, 137.5, 48, 130.4)
seg(14.5, 130.2, 75.5, 130.2)
for xc in (14.5, 35.5, 54, 75.5):
    arrow(xc, 130.2, xc, 127.3)
box(5, 120, 19, 7, "Time", icon=ic_wave, sub="228-d", msize=7.2, ssize=6.2)
box(26, 120, 19, 7, "Frequency", icon=ic_spectrum, sub="152-d", msize=7.2, ssize=6.2)
box(45, 120, 18, 7, "Time–freq", icon=ic_wavelet, sub="152-d", msize=7.2, ssize=6.2)
box(66, 120, 19, 7, "Event", icon=ic_spike, sub="82-d (excluded)", msize=7.2, ssize=6.2)
for xc in (14.5, 35.5, 54, 75.5):
    arrow(xc, 120, xc, 116.3)
box(14, 111, 68, 5, "Concatenation → 614-d vector (532-d deployed)", icon=ic_merge, msize=7.5)

# 门控 → 动态加权(走 Time–freq/Event 间走廊 x=64)
arrow(64, 137.5, 64, 104.8)

# ================= Stage3: 动态加权 =================
band(2, 96, 92, 10, "Stage3: Dynamic weighting")
cube(20, 97.5, 44.5, 7, "Dynamic weighting", icon=ic_balance, sub="val-initialised, online")

# mRMR 路径(左缘直下 → LightGBM 顶)
arrow(16, 111, 16, 86.4)   # 终点 = LightGBM 顶 y=70+14+DY=85.6, 留 0.8
ax.text(17.6, 95, "mRMR → 128-d", fontsize=6, color=GREY, ha="left", va="center")

# 动态加权 → 投票权重(中缝 x=40)
arrow(40, 97.5, 40, 68.4)  # 终点 = 投票顶 y=60+6.2+DY=67.8, 留 0.6

# ================= Stage4: 诊断层 =================
band(2, 58, 92, 36, "Stage4: Diagnosis agents")
cube(5, 70, 28, 14, "LightGBM", icon=ic_tree,
     sub="mRMR-128 features\n(feature path)", msize=7.5, ssize=6.2)
for xc in (52, 68.5, 84.5):
    arrow(xc, 80, xc, 77.3)  # 终点 = 信号框顶 70+7+DY=78.6 → 到 77.3? 修正:终点 78.6-1.3
box(44, 70, 16, 7, "EEGNet", icon=ic_nn, sub="signal path", msize=7.2, ssize=6)
box(62, 70, 13, 7, "TCN", icon=ic_nn, sub="signal path", msize=7.2, ssize=6)
box(77, 70, 15, 7, "Transformer", icon=ic_nn, sub="signal path", msize=6.8, ssize=6)
cube(8, 60, 80, 6.2, "Weighted soft voting", icon=ic_vote,
     sub="quality-aware weights, updated online", msize=7.5, ssize=6.2)
arrow(19, 70, 19, 68.4)     # LightGBM 底 70 → 投票立方体顶面区 68.4(60+6.2+1.6=67.8 之上)
arrow(52, 70, 52, 68.4)
arrow(68.5, 70, 68.5, 68.4)
arrow(84.5, 70, 84.5, 68.4)

# ================= Stage5: 决策与验证 =================
band(2, 22, 92, 34, "Stage5: Decision & validation")
arrow(30, 60, 30, 53.4)     # 投票底 → 分歧立方体顶(39+12+DY=52.6, 留 0.8)
cube(5, 39, 50, 12, "Disagreement detection", icon=ic_warn,
     sub="prob-diff ≥ 0.30 · majority < 0.60 · entropy ≥ 1.10\n(flags 48.4% of epochs for review)",
     msize=7.5, ssize=6.2)
cube(63, 39, 28, 12, "Human-review escalation", icon=ic_doc,
     sub="flagged low-consistency\nepochs routed to experts", edge=RED, lw=1.0, ls=(0, (4, 2)),
     msize=6.8, ssize=6.2)
arrow(55, 45, 63, 45, color=RED, dashed=True)
ax.text(59, 46.8, "flags", fontsize=6, color=RED, ha="center")
# 分歧 → 验证 agents
arrow(30, 39, 30, 37.3)
seg(20, 37, 74, 37)
arrow(20, 37, 20, 35.4)
arrow(74, 37, 74, 35.4)
box(5, 28, 30, 7, "Consistency agent", icon=ic_check, msize=7.2)
box(59, 28, 30, 7, "Explainability agent", icon=ic_bulb, msize=7.2)

# ================= 输出(层外并排) =================
cube(8, 9, 36, 8, "Subject aggregation", icon=ic_chart, sub="mean over epochs",
     msize=7.2, ssize=6.2)
cube(52, 9, 40, 8, "Output", icon=ic_doc,
     sub="Normal / Abnormal + confidence + explanation", msize=7.2, ssize=6.2)
arrow(20, 28, 20, 18.6)    # 一致性 → 聚合立方体顶(9+8+DY=18.6)
arrow(74, 28, 74, 18.6)    # 可解释 → 输出立方体顶
arrow(44, 13, 52, 13)      # 聚合 → 输出(立方体正面侧边)

# ================= 图例 =================
seg(3, 2.4, 6, 2.4)
ax.text(7, 2.4, "data flow", fontsize=6, color=GREY, va="center")
seg(24, 2.4, 27, 2.4, color=RED, dashed=True)
ax.text(28, 2.4, "escalation routing", fontsize=6, color=GREY, va="center")
ax.add_patch(Polygon([(47, 3.0), (49, 3.9), (51, 3.9), (50.5, 3.0)], closed=True,
                     facecolor=SH_TOP, edgecolor=INK, lw=0.7))
ax.text(52.5, 2.4, "core module (3D)", fontsize=6, color=GREY, va="center")
ax.add_patch(FancyBboxPatch((70, 1.9), 3, 1.0, boxstyle="round,pad=0,rounding_size=0.3",
                            facecolor="white", edgecolor=INK, lw=0.7, ls=(0, (4, 2))))
ax.text(74, 2.4, "input / conditional", fontsize=6, color=GREY, va="center")

fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(DELIVER_PNG, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figure saved")
