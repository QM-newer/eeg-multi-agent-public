# -*- coding: utf-8 -*-
"""EEG-MAS 架构图——参考图风格(小图标辅助理解 + 节点式布局)。
与"AI 卡片风"的区别:
1. 图标是细线条小元素,贴在模块标签旁/框内左上,不是大块装饰
2. 模块用简洁小节点框(白底细边),分散在泳道里,不是一排大卡片
3. 参考图的连线上带小图标标注(如 raw epochs),路径感强
内容与论文当前版本一致:614-d、mRMR-128、三规则(39.7%)、p90。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle, Polygon

plt.rcParams.update({"font.family": "Arial", "font.size": 8})

OUT_FIG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\eeg_multi_agent\outputs\figures\fig_system_architecture_ref.png"
DELIVER_PNG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS架构图(参考图风格版).png"
DELIVER_DOCX = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS系统架构图说明.docx"

INK = "#1a1a1a"
BAND = "#F2F2F2"
GREY = "#666666"
RED = "#B03A2E"
BLUE = "#2E5A88"

fig, ax = plt.subplots(figsize=(11, 12.5))
ax.set_xlim(0, 110)
ax.set_ylim(0, 128)
ax.axis("off")


# ---------------- 小图标(细线条, 3-4 单位大小) ----------------
def ic_wave(c, cx, cy, s=1.0):
    t = np.linspace(0, 4.2 * np.pi, 100)
    y = np.sin(t) + 0.4 * np.sin(2.6 * t + 0.7)
    ax.plot(cx - 2.0 * s + np.linspace(0, 1, 100) * 4.0 * s, cy + y * 0.7 * s,
            color=c, lw=0.9, solid_capstyle="round", zorder=7)

def ic_spectrum(c, cx, cy, s=1.0):
    for i, f in enumerate([0.9, 0.62, 0.40, 0.24, 0.12]):
        ax.add_patch(Rectangle((cx - 1.9 * s + i * 0.95 * s, cy - 0.9 * s),
                               0.6 * s, f * 1.9 * s, facecolor=c, edgecolor="none", zorder=7))

def ic_wavelet(c, cx, cy, s=1.0):
    t = np.linspace(0, 1, 80)
    y = np.exp(-3.2 * t) * np.sin(10 * np.pi * t)
    ax.plot(cx - 2.0 * s + t * 4.0 * s, cy + y * 1.2 * s, color=c, lw=0.9, zorder=7)

def ic_spike(c, cx, cy, s=1.0):
    x = np.array([0, .16, .26, .40, .52, .64, .76, .88, 1])
    y = np.array([0, .05, -.55, 1, -.05, .02, -.68, .04, 0])
    ax.plot(cx - 2.0 * s + x * 4.0 * s, cy + y * 1.1 * s, color=c, lw=0.9, zorder=7)

def ic_nn(c, cx, cy, s=1.0):
    L = [[(-1.4, -0.55), (-1.4, 0.55)], [(0, -1.0), (0, 0), (0, 1.0)], [(1.4, -0.55), (1.4, 0.55)]]
    for a in L[0]:
        for b in L[1]:
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s],
                    color=c, lw=0.45, zorder=7)
    for a in L[1]:
        for b in L[2]:
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s],
                    color=c, lw=0.45, zorder=7)
    for layer in L:
        for p in layer:
            ax.add_patch(Circle((cx + p[0] * s, cy + p[1] * s), 0.22 * s,
                                facecolor="white", edgecolor=c, lw=0.8, zorder=8))

def ic_tree(c, cx, cy, s=1.0):
    ax.plot([cx, cx], [cy - 1.0 * s, cy + 0.1 * s], color=c, lw=1.0, zorder=7)
    for dx, dy in [(-0.9, 0.9), (0, 1.1), (0.9, 0.9)]:
        ax.plot([cx, cx + dx * s], [cy + 0.1 * s, cy + dy * s], color=c, lw=0.9, zorder=7)
        ax.add_patch(Circle((cx + dx * s, cy + dy * s), 0.2 * s, facecolor=c,
                            edgecolor="none", zorder=8))

def ic_gauge(c, cx, cy, s=1.0):
    th = np.linspace(0, np.pi, 40)
    ax.plot(cx + np.cos(th) * 1.0 * s, cy - 0.4 * s + np.sin(th) * 0.9 * s,
            color=c, lw=0.9, zorder=7)
    ax.plot([cx, cx + 0.6 * s], [cy - 0.4 * s, cy + 0.45 * s], color=c, lw=0.9, zorder=8)
    ax.add_patch(Circle((cx, cy - 0.4 * s), 0.14 * s, facecolor=c, edgecolor="none", zorder=8))

def ic_weights(c, cx, cy, s=1.0):
    ax.plot([cx - 1.6 * s, cx + 1.6 * s], [cy, cy], color=c, lw=0.9, zorder=7)
    for dx, f in [(-1.0, 0.9), (0.3, 0.55), (1.3, 0.75)]:
        ax.plot([cx + dx * s, cx + dx * s], [cy - 0.9 * s, cy + 0.9 * s],
                color=c, lw=0.8, zorder=7)
        ax.add_patch(Circle((cx + dx * s, cy + (0.4 if dx == -1.0 else -0.4) * s),
                            0.24 * s, facecolor="white", edgecolor=c, lw=0.8, zorder=8))

def ic_filter(c, cx, cy, s=1.0):
    ax.add_patch(Polygon([[cx - 1.1 * s, cy + 1.0 * s], [cx + 1.1 * s, cy + 1.0 * s],
                          [cx + 0.35 * s, cy + 0.1 * s], [cx + 0.35 * s, cy - 1.0 * s],
                          [cx - 0.35 * s, cy - 1.0 * s], [cx - 0.35 * s, cy + 0.1 * s]],
                         closed=True, facecolor="none", edgecolor=c, lw=0.9, zorder=7))

def ic_merge(c, cx, cy, s=1.0):
    for dy in (-0.8, 0.8):
        ax.plot([cx - 1.7 * s, cx - 0.3 * s], [cy + dy * s, cy + dy * s],
                color=c, lw=0.9, zorder=7)
        ax.plot([cx - 0.3 * s, cx + 0.9 * s], [cy + dy * s, cy], color=c, lw=0.9, zorder=7)
    ax.add_patch(FancyArrowPatch((cx + 0.7 * s, cy), (cx + 1.8 * s, cy), arrowstyle="-|>",
                                 mutation_scale=7, color=c, lw=0.9, zorder=7))

def ic_vote(c, cx, cy, s=1.0):
    for i, f in enumerate([0.45, 0.95, 0.62]):
        ax.add_patch(Rectangle((cx - 1.4 * s + i * 1.1 * s, cy - 0.8 * s),
                               0.7 * s, f * 1.6 * s, facecolor=c, edgecolor="none",
                               alpha=0.85, zorder=7))

def ic_warn(c, cx, cy, s=1.0):
    ax.add_patch(Polygon([[cx - 1.1 * s, cy - 0.85 * s], [cx + 1.1 * s, cy - 0.85 * s],
                          [cx, cy + 0.95 * s]], closed=True, facecolor="none",
                         edgecolor=c, lw=1.0, zorder=7))
    ax.plot([cx, cx], [cy - 0.45 * s, cy + 0.15 * s], color=c, lw=0.9, zorder=8)
    ax.add_patch(Circle((cx, cy - 0.62 * s), 0.1 * s, facecolor=c, edgecolor="none", zorder=8))

def ic_loop(c, cx, cy, s=1.0):
    ax.add_patch(FancyArrowPatch((cx - 0.9 * s, cy), (cx + 0.9 * s, cy),
                                 connectionstyle="arc3,rad=1.0", arrowstyle="-|>",
                                 mutation_scale=7, color=c, lw=1.0, zorder=7))

def ic_check(c, cx, cy, s=1.0):
    ax.plot([cx - 0.9 * s, cx - 0.15 * s, cx + 1.0 * s],
            [cy - 0.1 * s, cy - 0.8 * s, cy + 0.85 * s],
            color=c, lw=1.3, solid_capstyle="round", zorder=7)

def ic_bulb(c, cx, cy, s=1.0):
    ax.add_patch(Circle((cx, cy + 0.25 * s), 0.65 * s, facecolor="none", edgecolor=c,
                        lw=0.9, zorder=7))
    ax.plot([cx - 0.28 * s, cx - 0.28 * s], [cy - 0.45 * s, cy - 0.95 * s],
            color=c, lw=0.9, zorder=7)
    ax.plot([cx + 0.28 * s, cx + 0.28 * s], [cy - 0.45 * s, cy - 0.95 * s],
            color=c, lw=0.9, zorder=7)

def ic_chart(c, cx, cy, s=1.0):
    x = np.array([0, .22, .22, .5, .5, .78, .78, 1])
    y = np.array([.05, .05, .35, .35, .68, .68, .95, .95])
    ax.plot(cx - 1.4 * s + x * 2.8 * s, cy - 0.9 * s + y * 1.8 * s, color=c, lw=1.0, zorder=7)
    ax.plot([cx - 1.5 * s, cx + 1.5 * s], [cy + 0.72 * s] * 2, color=c, lw=0.7,
            ls=(0, (3, 2)), zorder=7)

def ic_doc(c, cx, cy, s=1.0):
    ax.add_patch(Rectangle((cx - 0.7 * s, cy - 1.0 * s), 1.4 * s, 2.0 * s,
                           facecolor="none", edgecolor=c, lw=0.9, zorder=7))
    for i in range(3):
        yy = cy + 0.5 * s - i * 0.5 * s
        ax.plot([cx - 0.4 * s, cx + 0.4 * s], [yy, yy], color=c, lw=0.7, zorder=8)

def ic_db(c, cx, cy, s=1.0):
    ax.add_patch(Rectangle((cx - 0.9 * s, cy - 1.0 * s), 1.8 * s, 2.0 * s,
                           facecolor="none", edgecolor=c, lw=0.9, zorder=7))
    for i in range(2):
        yy = cy - 0.33 * s + i * 0.66 * s
        ax.plot([cx - 0.9 * s, cx + 0.9 * s], [yy, yy], color=c, lw=0.7, zorder=8)

def ic_person(c, cx, cy, s=1.0):
    ax.add_patch(Circle((cx, cy + 0.55 * s), 0.38 * s, facecolor="none", edgecolor=c,
                        lw=0.9, zorder=7))
    ax.add_patch(Polygon([[cx - 0.6 * s, cy - 0.85 * s], [cx + 0.6 * s, cy - 0.85 * s],
                          [cx + 0.4 * s, cy + 0.05 * s], [cx - 0.4 * s, cy + 0.05 * s]],
                         closed=True, facecolor="none", edgecolor=c, lw=0.9, zorder=7))


# ---------------- 基础绘制 ----------------
def box(x, y, w, h, label, icon=None, icon_pos="left", sub=None, edge=INK, lw=0.9,
        ls="-", msize=8, ssize=6.8, align="center"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=edge,
                           linewidth=lw, linestyle=ls, zorder=4))
    if icon and icon_pos == "left":
        icon(edge, x + 3.2, y + h / 2, 1.0)
        tx = x + 5.5 + w / 2 - 5.5 / 2 if False else x + w / 2 + 1.6
        tx = (x + 5.8 + x + w) / 2  # 文字在图标右侧区域居中
        ha = "center"
    elif icon and icon_pos == "top":
        icon(edge, x + w / 2, y + h * 0.72, 1.0)
        tx = x + w / 2
    else:
        tx = x + w / 2
    if sub:
        ax.text(tx, y + h * 0.62, label, ha=ha if icon else "center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=6, linespacing=1.2)
        ax.text(tx, y + h * 0.24, sub, ha=ha if icon else "center", va="center",
                fontsize=ssize, color="#333333", zorder=6, linespacing=1.2)
    else:
        ax.text(tx, y + h / 2, label, ha=ha if icon else "center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=6, linespacing=1.2)


def band(x, y, w, h, label):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=BAND, edgecolor="none", zorder=1))
    ax.text(x + 1.5, y + h - 1.3, label, fontsize=7, style="italic", color=GREY,
            zorder=2, va="top")


def arrow(x1, y1, x2, y2, color=INK, dashed=False, lw=0.9, ms=8):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=ms, color=color, linewidth=lw,
                                 linestyle=(0, (4, 2)) if dashed else "-",
                                 shrinkA=0, shrinkB=0, zorder=5))


def seg(x1, y1, x2, y2, color=INK, lw=0.9, dashed=False):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw,
            linestyle=(0, (4, 2)) if dashed else "-", zorder=5, solid_capstyle="butt")


# ================= 输入 =================
box(33, 121, 44, 6, "Input: 19-ch EEG epochs (250 Hz, 2 s)", icon=ic_wave, msize=8)
arrow(55, 121, 55, 115.5)

# ================= 协调层 =================
band(2, 101, 100, 14, "Coordination layer")
box(8, 104, 40, 7.5, "Quality gating", icon=ic_gauge, sub="SNR, artifact ratio")
box(58, 104, 40, 7.5, "Dynamic weighting", icon=ic_weights, sub="val-initialised, online")
arrow(48, 107.75, 58, 107.75)

# ================= 特征层 =================
band(2, 76, 100, 24, "Feature layer")
# weights -> 4 个特征框
arrow(78, 104, 78, 99.7)
seg(16, 99.5, 88, 99.5)
for xc in (16, 38, 60, 88):
    arrow(xc, 99.5, xc, 97.2)

box(6, 89.5, 20, 7.5, "Time domain", icon=ic_wave, sub="228 features", msize=7.5)
box(28, 89.5, 20, 7.5, "Frequency", icon=ic_spectrum, sub="152 features", msize=7.5)
box(50, 89.5, 20, 7.5, "Time–frequency", icon=ic_wavelet, sub="152 features", msize=7.5)
box(78, 89.5, 22, 7.5, "Event", icon=ic_spike, sub="82 features", msize=7.5)
for xc in (16, 38, 60, 88):
    arrow(xc, 89.5, xc, 87.2)
box(20, 80, 64, 6.5, "Concatenation → 614-d feature vector", icon=ic_merge, msize=8)

# ================= 诊断层 =================
band(2, 46, 100, 29, "Diagnosis layer")
# 特征路径
arrow(52, 80, 52, 77.2)
ax.text(54.5, 78.2, "mRMR → 128-d", fontsize=6.5, color=GREY, va="center")
box(7, 63, 34, 12.5, "LightGBM", icon=ic_tree, sub="mRMR-128 features\n(feature path)", msize=8.5)
# 信号旁路
seg(55, 121, 99, 121)
seg(99, 121, 99, 70)
ax.text(101.2, 96, "raw\nepochs", rotation=90, fontsize=6.5, color=GREY,
        ha="center", va="center")
seg(60, 70, 99, 70)
for xc in (60, 77, 93):
    arrow(xc, 70, xc, 67.2)
box(50, 59.5, 20, 7.5, "EEGNet", icon=ic_nn, sub="signal path", msize=7.5)
box(72, 59.5, 18, 7.5, "TCN", icon=ic_nn, sub="signal path", msize=7.5)
box(92, 59.5, 18, 7.5, "Transformer", icon=ic_nn, sub="signal path", msize=6.8)
# 融合
box(18, 48, 74, 8, "Weighted soft voting", icon=ic_vote, sub="stacking meta-learner, weights updated online", msize=8.5)
arrow(24, 63, 24, 56.2)
arrow(60, 59.5, 60, 56.2)
arrow(81, 59.5, 81, 56.2)
arrow(101, 59.5, 92, 52.2, lw=0.9)

# ================= 分歧检测 + 二次仲裁 =================
box(8, 33, 60, 12, "Disagreement detection", icon=ic_warn,
    sub="prob-diff ≥ 0.30 · majority < 0.60 · entropy ≥ 1.099\n(calibrated trigger rate: 39.7%)",
    msize=8.5, ssize=6.6)
arrow(55, 48, 38, 45.2)

box(76, 33, 26, 12, "Second-pass arbitration", icon=ic_loop, sub="attention-weighted\nconsensus",
    edge=RED, lw=1.0, ls=(0, (4, 2)), msize=7.2, ssize=6.6)
arrow(68, 39, 76, 39, color=RED, dashed=True)
ax.text(72, 40.8, "trigger", fontsize=6.5, color=RED, ha="center")
# refine 回路
seg(102, 39, 105, 39, color=RED, dashed=True)
seg(105, 39, 105, 52, color=RED, dashed=True)
arrow(105, 52, 92.2, 52, color=RED, dashed=True)
ax.text(98.5, 53.6, "refine", fontsize=6.5, color=RED, ha="center")

# ================= 验证层 =================
band(2, 20, 100, 11, "Validation layer")
arrow(38, 33, 38, 31.2)
seg(22, 31, 82, 31)
arrow(22, 31, 22, 28.2)
arrow(82, 31, 82, 28.2)
box(7, 21, 30, 7, "Consistency agent", icon=ic_check, msize=7.5)
box(67, 21, 33, 7, "Explainability agent", icon=ic_bulb, msize=7.5)

# ================= 输出 =================
box(20, 11, 64, 7, "Subject-level aggregation (p90 over epochs)", icon=ic_chart, msize=8)
arrow(22, 21, 22, 18.2)
arrow(82, 21, 82, 18.2)
box(30, 1, 44, 7, "Output", icon=ic_doc, sub="Normal / Abnormal + confidence + explanation",
    msize=8.5, ssize=6.5)

arrow(52, 11, 52, 8.2)

# 图例
seg(4, 24.5 - 22.5, 8, 2, lw=0.9)  # placeholder no-op (kept minimal)
seg(4, 2, 8, 2)
ax.text(9.5, 2, "data flow", fontsize=6.5, color=GREY, va="center")
seg(28, 2, 32, 2, color=RED, dashed=True)
ax.text(33.5, 2, "arbitration feedback", fontsize=6.5, color=GREY, va="center")
ax.add_patch(Rectangle((56, 1.5), 4, 1, facecolor=BAND, edgecolor="none"))
ax.text(61.5, 2, "system layer", fontsize=6.5, color=GREY, va="center")

fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(DELIVER_PNG, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figure saved")

# ================= Word 说明文档 =================
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
p.add_run().add_picture(DELIVER_PNG, width=Cm(13.5))

cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_after = Pt(6)
r1 = cap.add_run("Figure 1. ")
r1.bold = True
r1.font.size = Pt(9)
r2 = cap.add_run("Three-layer architecture of EEG-MAS. Icons mark the signal modality of "
                 "each module; solid arrows indicate data flow; dashed red arrows indicate "
                 "the arbitration feedback loop; grey bands mark the system layers.")
r2.font.size = Pt(9)

doc.save(DELIVER_DOCX)
print("docx saved:", DELIVER_DOCX)
