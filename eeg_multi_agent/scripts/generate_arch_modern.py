# -*- coding: utf-8 -*-
"""EEG-MAS 架构图——顶会插图风格(参考 RAG 攻击论文图:浅色圆角模块+图标化+虚线分组)。
内容与论文当前版本一致:614-d、mRMR-128、三规则(39.7%)、p90。同步更新 Word 说明文档。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Polygon

plt.rcParams.update({"font.family": "Arial", "font.size": 8})

OUT_FIG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\eeg_multi_agent\outputs\figures\fig_system_architecture_modern.png"
DELIVER_PNG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS架构图(顶会风格版).png"
DELIVER_DOCX = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS系统架构图说明.docx"

# draw.io 柔和配色
BLUE_F, BLUE_E = "#DAE8FC", "#6C8EBF"
YELL_F, YELL_E = "#FFF2CC", "#D6B656"
GREE_F, GREE_E = "#D5E8D4", "#82B366"
ORAN_F, ORAN_E = "#FFE6CC", "#D79B00"
RED_F, RED_E = "#F8CECC", "#B85450"
GRAY_F, GRAY_E = "#F5F5F5", "#999999"
INK = "#333333"

fig, ax = plt.subplots(figsize=(14, 8.8))
ax.set_xlim(0, 140)
ax.set_ylim(0, 88)
ax.axis("off")

# ---------------- 图标库 ----------------
def icon_wave(ax, cx, cy, w, h, c):
    t = np.linspace(0, 4.4 * np.pi, 120)
    y = np.sin(t) + 0.4 * np.sin(2.7 * t + 0.8)
    ax.plot(cx - w / 2 + np.linspace(0, 1, 120) * w, cy + y * h * 0.26,
            color=c, lw=1.1, solid_capstyle="round", zorder=6)

def icon_spectrum(ax, cx, cy, w, h, c):
    for i, f in enumerate([0.9, 0.62, 0.42, 0.28, 0.16]):
        ax.add_patch(Rectangle((cx - w * 0.30 + i * w * 0.15, cy - h * 0.30),
                               w * 0.11, h * f * 0.72, facecolor=c, edgecolor="none", zorder=6))

def icon_tf(ax, cx, cy, w, h, c):
    t = np.linspace(0, 1, 90)
    y = np.exp(-3 * t) * np.sin(11 * np.pi * t)
    ax.plot(cx - w / 2 + t * w, cy + y * h * 0.30, color=c, lw=1.1, zorder=6)

def icon_event(ax, cx, cy, w, h, c):
    x = np.array([0, .18, .28, .40, .50, .62, .72, .84, 1])
    y = np.array([0, 0, -.55, 1, 0, 0, -.70, 0, 0])
    ax.plot(cx - w / 2 + x * w, cy + y * h * 0.26, color=c, lw=1.1, zorder=6)

def icon_nn(ax, cx, cy, w, h, c):
    xs = [0.12, 0.5, 0.88]
    layers = [[0.22, 0.78], [0.10, 0.5, 0.90], [0.22, 0.78]]
    pos = {}
    for li, ys in enumerate(layers):
        for yi, yy in enumerate(ys):
            pos[(li, yi)] = (cx - w / 2 + xs[li] * w, cy - h * 0.30 + yy * h * 0.60)
    for a in range(2):
        for b in range(3):
            ax.plot([pos[(0, a)][0], pos[(1, b)][0]], [pos[(0, a)][1], pos[(1, b)][1]],
                    color=c, lw=0.55, alpha=0.8, zorder=6)
    for b in range(3):
        for cc in range(2):
            ax.plot([pos[(1, b)][0], pos[(2, cc)][0]], [pos[(1, b)][1], pos[(2, cc)][1]],
                    color=c, lw=0.55, alpha=0.8, zorder=6)
    for p in pos.values():
        ax.add_patch(Circle(p, h * 0.052, facecolor="white", edgecolor=c, lw=1.0, zorder=7))

def icon_tree(ax, cx, cy, w, h, c):
    ax.plot([cx, cx], [cy - h * 0.34, cy + h * 0.02], color=c, lw=1.3, zorder=6)
    for dx, dy in [(-0.30, 0.28), (0, 0.36), (0.30, 0.28)]:
        ax.plot([cx, cx + dx * w * 0.55], [cy + h * 0.02, cy + h * 0.02 + dy * h],
                color=c, lw=1.0, zorder=6)
        ax.add_patch(Circle((cx + dx * w * 0.55, cy + h * 0.02 + dy * h), h * 0.05,
                            facecolor=c, edgecolor="none", zorder=7))

def icon_gauge(ax, cx, cy, w, h, c):
    th = np.linspace(0, np.pi, 50)
    ax.plot(cx - w * 0.30 + np.cos(th) * w * 0.30, cy - h * 0.10 + np.sin(th) * h * 0.26,
            color=c, lw=1.2, zorder=6)
    ax.plot([cx, cx + w * 0.18], [cy - h * 0.10, cy + h * 0.10], color=c, lw=1.1, zorder=7)
    ax.add_patch(Circle((cx, cy - h * 0.10), h * 0.04, facecolor=c, edgecolor="none", zorder=7))

def icon_slider(ax, cx, cy, w, h, c):
    for dx in (-0.26, 0, 0.26):
        ax.add_patch(Circle((cx + dx * w, cy), h * 0.028, facecolor=c, edgecolor="none", zorder=6))
    ax.plot([cx - w * 0.36, cx + w * 0.36], [cy, cy], color=c, lw=1.2, zorder=5)
    ax.plot([cx - w * 0.09, cx - w * 0.09], [cy - h * 0.16, cy + h * 0.16], color=c, lw=1.0, zorder=6)
    ax.add_patch(Circle((cx - w * 0.09, cy), h * 0.085, facecolor="white", edgecolor=c, lw=1.2, zorder=7))

def icon_stack(ax, cx, cy, w, h, c):
    cs = [BLUE_E, GREE_E, ORAN_E, RED_E]
    for i in range(4):
        ax.add_patch(Rectangle((cx - w * 0.30 + i * w * 0.16, cy - h * 0.30),
                               w * 0.12, h * 0.60, facecolor=cs[i], edgecolor="none", zorder=6))

def icon_vote(ax, cx, cy, w, h, c):
    for i, f in enumerate([0.38, 0.85, 0.55]):
        ax.add_patch(Rectangle((cx - w * 0.26 + i * w * 0.20, cy - h * 0.26),
                               w * 0.12, h * f * 0.70, facecolor=c, edgecolor="none",
                               alpha=0.9, zorder=6))
    ax.plot([cx - w * 0.32, cx + w * 0.32], [cy - h * 0.28, cy - h * 0.28], color=c, lw=1.0, zorder=6)

def icon_warn(ax, cx, cy, w, h, c):
    ax.add_patch(Polygon([[cx - w * 0.30, cy - h * 0.28], [cx + w * 0.30, cy - h * 0.28],
                          [cx, cy + h * 0.30]], closed=True, facecolor="none", edgecolor=c, lw=1.3, zorder=6))
    ax.plot([cx, cx], [cy - h * 0.12, cy + h * 0.06], color=c, lw=1.2, zorder=7)
    ax.add_patch(Circle((cx, cy - h * 0.20), h * 0.032, facecolor=c, edgecolor="none", zorder=7))

def icon_loop(ax, cx, cy, w, h, c):
    ax.add_patch(FancyArrowPatch((cx - w * 0.22, cy - h * 0.10), (cx + w * 0.22, cy - h * 0.10),
                                 connectionstyle="arc3,rad=0.95", arrowstyle="-|>",
                                 mutation_scale=9, color=c, lw=1.2, zorder=6))

def icon_check(ax, cx, cy, w, h, c):
    ax.plot([cx - w * 0.24, cx - w * 0.04, cx + w * 0.30],
            [cy - h * 0.04, cy - h * 0.26, cy + h * 0.26],
            color=c, lw=1.8, solid_capstyle="round", zorder=6)

def icon_bulb(ax, cx, cy, w, h, c):
    ax.add_patch(Circle((cx, cy + h * 0.07), h * 0.20, facecolor="none", edgecolor=c, lw=1.2, zorder=6))
    ax.add_patch(Rectangle((cx - w * 0.06, cy - h * 0.26), w * 0.12, h * 0.14,
                           facecolor="none", edgecolor=c, lw=1.1, zorder=6))
    for ang in (55, 90, 125):
        a = np.deg2rad(ang)
        ax.plot([cx + np.cos(a) * h * 0.27, cx + np.cos(a) * h * 0.38],
                [cy + h * 0.07 + np.sin(a) * h * 0.27, cy + h * 0.07 + np.sin(a) * h * 0.38],
                color=c, lw=1.0, zorder=6)

def icon_chart(ax, cx, cy, w, h, c):
    x = np.array([0, .25, .25, .55, .55, .8, .8, 1])
    y = np.array([.08, .08, .38, .38, .72, .72, .95, .95])
    ax.plot(cx - w * 0.30 + x * w * 0.60, cy - h * 0.28 + y * h * 0.56,
            color=c, lw=1.2, zorder=6)
    ax.plot([cx - w * 0.32, cx + w * 0.32], [cy - h * 0.28 + 0.9 * h * 0.56] * 2,
            color=c, lw=0.8, ls=(0, (3, 2)), zorder=6)

def icon_doc(ax, cx, cy, w, h, c):
    ax.add_patch(Rectangle((cx - w * 0.20, cy - h * 0.32), w * 0.40, h * 0.64,
                           facecolor="none", edgecolor=c, lw=1.2, zorder=6))
    for i in range(3):
        yy = cy + h * 0.12 - i * h * 0.15
        ax.plot([cx - w * 0.11, cx + w * 0.11], [yy, yy], color=c, lw=0.9, zorder=7)

# ---------------- 模块/分组/箭头 ----------------
def box(x, y, w, h, title, sub=None, icon=None, fill="white", edge=GRAY_E,
        lw=1.0, ls="-", tsize=8, ssize=6.8, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={min(w, h) * 0.13}",
                                facecolor=fill, edgecolor=edge, linewidth=lw,
                                linestyle=ls, zorder=3))
    if icon is not None:
        icon(ax, x + w / 2, y + h * 0.70, w * 0.62, h * 0.48, edge)
        ty = y + h * 0.32 if sub else y + h * 0.34
    else:
        ty = y + h / 2
    ax.text(x + w / 2, ty, title, ha="center", va="center", fontsize=tsize,
            fontweight="bold" if bold else "normal", color="#222222", zorder=8,
            linespacing=1.25)
    if sub:
        ax.text(x + w / 2, y + h * 0.13, sub, ha="center", va="center", fontsize=ssize,
                color="#555555", zorder=8, linespacing=1.2)

def group(x, y, w, h, label, ec="#AAAAAA"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.4",
                                facecolor="none", edgecolor=ec, linewidth=1.0,
                                linestyle=(0, (5, 3)), zorder=1))
    ax.text(x + 1.6, y + h - 1.0, label, fontsize=7.5, style="italic",
            color="#888888", zorder=2, va="top")

def arrow(x1, y1, x2, y2, dashed=False, color=INK, lw=1.1, label=None, lab_off=(0, 1.2), fs=6.8):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
                                 color=color, lw=lw,
                                 linestyle=(0, (4, 2)) if dashed else "-",
                                 shrinkA=1, shrinkB=1, zorder=5))
    if label:
        ax.text((x1 + x2) / 2 + lab_off[0], (y1 + y2) / 2 + lab_off[1], label,
                fontsize=fs, color=color, ha="center", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

# ================= Row 1:输入与特征路径 =================
box(2, 70, 18, 14, "Input", sub="19-ch EEG epochs\n(250 Hz, 2 s)", icon=icon_wave,
    fill="white", edge=INK, lw=1.2)

group(24, 66, 22, 22, "Coordination")
box(26, 79, 18, 7, "Quality gating", sub="SNR / artifact ratio", icon=icon_gauge,
    fill=GRAY_F, edge=GRAY_E, tsize=7.5, ssize=6.5)
box(26, 67.5, 18, 7, "Dynamic weights", sub="val-init, online", icon=icon_slider,
    fill=GRAY_F, edge=GRAY_E, tsize=7.5, ssize=6.5)
arrow(20, 77, 26, 82.5)
arrow(35, 79, 35, 74.5)

group(50, 66, 52, 22, "Feature agents")
box(52, 72, 11, 12, "Time", sub="228-d", icon=icon_wave, fill=BLUE_F, edge=BLUE_E, tsize=7.5)
box(65, 72, 11, 12, "Freq", sub="152-d", icon=icon_spectrum, fill=BLUE_F, edge=BLUE_E, tsize=7.5)
box(78, 72, 11, 12, "TF", sub="152-d", icon=icon_tf, fill=BLUE_F, edge=BLUE_E, tsize=7.5)
box(91, 72, 9, 12, "Event", sub="82-d", icon=icon_event, fill=BLUE_F, edge=BLUE_E, tsize=7.5)
arrow(44, 71, 52, 76, label=None)

# 特征总线 → concat
for xc in (57.5, 70.5, 83.5, 95.5):
    ax.plot([xc, xc], [72, 70], color=INK, lw=0.9, zorder=5)
ax.plot([57.5, 112], [70, 70], color=INK, lw=0.9, zorder=5)
arrow(112, 70, 112, 72, lw=0.9)

box(106, 72, 12, 12, "Concat", sub="614-d", icon=icon_stack, fill="white",
    edge=GRAY_E, tsize=7.5)
box(122, 68, 16, 18, "LightGBM", sub="mRMR-128\nfrom 614-d", icon=icon_tree,
    fill=YELL_F, edge=YELL_E, tsize=8)
arrow(118, 78, 122, 77)

# raw-epochs 旁路总线
ax.plot([11, 11], [70, 64], color=INK, lw=1.0, zorder=5)
ax.plot([11, 120], [64, 64], color=INK, lw=1.0, zorder=5)
ax.text(60, 65.4, "raw epochs", fontsize=6.8, color="#666666", ha="center", va="center",
        zorder=6, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
for xc in (72.5, 94, 120):
    arrow(xc, 64, xc, 62, lw=0.9)

# ================= Row 2:信号路径(深度模型) =================
group(60, 48, 74, 14, "Signal agents")
box(63, 51, 19, 9, "EEGNet", icon=icon_nn, fill=BLUE_F, edge=BLUE_E, tsize=7.5)
box(85, 51, 18, 9, "TCN", icon=icon_nn, fill=BLUE_F, edge=BLUE_E, tsize=7.5)
box(106, 51, 26, 9, "Transformer", icon=icon_nn, fill=BLUE_F, edge=BLUE_E, tsize=7.5)

# ================= Row 3:融合 =================
box(70, 32, 68, 10, "Weighted soft voting", sub="stacking meta-learner, weights updated online",
    icon=icon_vote, fill=GRAY_F, edge=GRAY_E, tsize=8)
arrow(72.5, 51, 72.5, 42)
arrow(94, 51, 94, 42)
arrow(119, 51, 119, 42)
arrow(136.5, 68, 136.5, 42)

# ================= Row 4:分歧检测与二次仲裁 =================
box(18, 16, 52, 12, "Disagreement detection",
    sub="prob-diff \u2265 0.30  \u00b7  majority < 0.60  \u00b7  entropy \u2265 1.099\n(calibrated trigger rate 39.7%)",
    icon=icon_warn, fill=ORAN_F, edge=ORAN_E, tsize=8, ssize=6.6)
box(84, 16, 32, 12, "Second-pass arbitration",
    sub="attention-weighted\nconsensus", icon=icon_loop, fill=RED_F, edge=RED_E,
    tsize=7.5, ls=(0, (4, 2)))
arrow(85, 32, 48, 28)
arrow(70, 22, 84, 22, dashed=True, color=RED_E, label="trigger", lab_off=(0, 1.6))
arrow(100, 28, 116, 32, dashed=True, color=RED_E, label="refine", lab_off=(3.5, 0.8))

# ================= Row 5:验证层与输出 =================
group(6, 2, 64, 12, "Validation")
box(9, 4, 26, 8, "Consistency agent", icon=icon_check, fill=GREE_F, edge=GREE_E, tsize=7.5)
box(41, 4, 26, 8, "Explainability agent", icon=icon_bulb, fill=GREE_F, edge=GREE_E, tsize=7.5)
arrow(44, 16, 38, 14)

box(76, 2, 24, 12, "Subject aggregation", sub="p90 over epochs", icon=icon_chart,
    fill="white", edge=GRAY_E, tsize=7.5)
box(106, 2, 32, 13, "Output", sub="Normal / Abnormal\n+ confidence + explanation",
    icon=icon_doc, fill=GREE_F, edge=GREE_E, tsize=8, lw=1.3)
arrow(70, 8, 76, 8)
arrow(100, 8, 106, 8)

# 图例
ax.plot([4, 8], [15.5, 15.5], color=INK, lw=1.1)
ax.text(9, 15.5, "data flow", fontsize=6.8, color="#555555", va="center")
ax.plot([4, 8], [13.2, 13.2], color=RED_E, lw=1.1, ls=(0, (4, 2)))
ax.text(9, 13.2, "arbitration feedback", fontsize=6.8, color="#555555", va="center")

fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(DELIVER_PNG, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figure saved")

# ================= Word 说明文档(同款格式,换新图) =================
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.54)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

def para(text="", size=11, bold=False, center=False, space_after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.font.size = Pt(size)
    return p

para("EEG-MAS: A Three-Layer Multi-Agent System for Pediatric EEG Screening",
     size=14, bold=True, center=True, space_after=4)
para("System Architecture", size=12, bold=True, center=True, space_after=10)

para(
    "The EEG-MAS pipeline processes 19-channel EEG epochs (250 Hz, 2-s segments) through "
    "three coordinated layers. A feature layer extracts 614 features per epoch from four "
    "complementary domains — time (228), frequency (152), time–frequency (152), and "
    "clinical event markers (82) — from which 128 features are selected by mRMR for the "
    "LightGBM agent; in parallel, EEGNet, TCN, and Transformer agents read the raw signal. "
    "Their weighted soft votes (stacking meta-learner, weights updated online) are monitored "
    "by a disagreement detector applying three calibrated rules — probability gap ≥ 0.30, "
    "majority agreement < 0.60, and entropy ≥ 1.099 — which routes 39.7% of cases to a "
    "second-pass attention-weighted arbitration. A validation layer then checks prediction "
    "consistency and generates explanations before subject-level p90 aggregation produces "
    "the final screening decision (Normal / Abnormal) with confidence and explanation.",
    size=11, space_after=12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(DELIVER_PNG, width=Cm(16.0))

cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_after = Pt(6)
r1 = cap.add_run("Figure 1. ")
r1.bold = True
r1.font.size = Pt(9)
r2 = cap.add_run("Three-layer architecture of EEG-MAS. Solid arrows indicate data flow; "
                 "dashed red arrows indicate the arbitration feedback loop; dashed grey "
                 "containers mark the coordination, feature, signal, and validation layers.")
r2.font.size = Pt(9)

doc.save(DELIVER_DOCX)
print("docx saved:", DELIVER_DOCX)
