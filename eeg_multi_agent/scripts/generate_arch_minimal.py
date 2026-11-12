# -*- coding: utf-8 -*-
"""EEG-MAS 架构图——极简学术风(零图标、零彩色块、线框+浅灰泳道)。
布局坐标逐项精算,文字与图形间距充分,无重叠。
内容与论文当前版本一致:614-d、mRMR-128、三规则(39.7%)、p90。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams.update({"font.family": "Arial", "font.size": 8})

OUT_FIG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\eeg_multi_agent\outputs\figures\fig_system_architecture_minimal.png"
DELIVER_PNG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS架构图(极简学术版).png"
DELIVER_DOCX = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS系统架构图说明.docx"

INK = "#1a1a1a"
BAND = "#F5F5F5"
GREY = "#666666"
RED = "#B03A2E"

fig, ax = plt.subplots(figsize=(10, 12.8))
ax.set_xlim(0, 104)
ax.set_ylim(0, 131)
ax.axis("off")


def box(x, y, w, h, main, sub=None, edge=INK, lw=0.9, ls="-", msize=8.5, ssize=7):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=edge,
                           linewidth=lw, linestyle=ls, zorder=3))
    if sub:
        ax.text(x + w / 2, y + h * 0.62, main, ha="center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=4)
        ax.text(x + w / 2, y + h * 0.26, sub, ha="center", va="center",
                fontsize=ssize, color="#333333", zorder=4, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, main, ha="center", va="center",
                fontsize=msize, fontweight="bold", color=INK, zorder=4)


def band(x, y, w, h, label):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=BAND, edgecolor="none", zorder=1))
    ax.text(x + 1.5, y + h - 1.4, label, fontsize=7, style="italic",
            color=GREY, zorder=2, va="top")


def arrow(x1, y1, x2, y2, color=INK, dashed=False, lw=0.9):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=8, color=color, linewidth=lw,
                                 linestyle=(0, (4, 2)) if dashed else "-",
                                 shrinkA=0, shrinkB=0, zorder=5))


def seg(x1, y1, x2, y2, color=INK, lw=0.9, dashed=False):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw,
            linestyle=(0, (4, 2)) if dashed else "-", zorder=5,
            solid_capstyle="butt")


# ================= Input =================
box(30, 124, 40, 5, "Input: 19-channel EEG epochs (250 Hz, 2 s)", msize=8.5)
arrow(50, 124, 50, 118.2)

# ================= Coordination =================
band(2, 108, 94, 14, "Coordination layer")
box(7, 110, 36, 8, "Quality gating", "SNR, artifact ratio")
box(57, 110, 36, 8, "Dynamic weighting", "val-initialised, online")
arrow(43, 114, 57, 114)

# weights -> feature 分配线
arrow(75, 110, 75, 105.7)
seg(17.5, 105.5, 83, 105.5)
for xc in (17.5, 38.5, 59.5, 83):
    arrow(xc, 105.5, xc, 103.2)

# ================= Feature =================
band(2, 84, 94, 23, "Feature layer")
box(8, 93, 19, 10, "Time domain", "228 features")
box(29, 93, 19, 10, "Frequency", "152 features")
box(50, 93, 19, 10, "Time–frequency", "152 features")
box(71, 93, 24, 10, "Event", "82 features")
for xc in (17.5, 38.5, 59.5, 83):
    arrow(xc, 93, xc, 90.2)
box(16, 85.5, 68, 4.5, "Concatenation  \u2192  614-d feature vector", msize=8)

# ================= Diagnosis =================
band(2, 52, 94, 31, "Diagnosis layer")
# 特征路径
arrow(22, 85.5, 22, 76.2)
ax.text(24, 80.5, "614-d \u2192 mRMR-128", fontsize=6.5, color=GREY, va="center")
box(6, 64, 32, 12, "LightGBM", "mRMR-128 features\n(feature path)")
# 信号路径(raw 旁路)
seg(70, 126.5, 97.5, 126.5)
seg(97.5, 126.5, 97.5, 78)
ax.text(99.3, 102, "raw epochs", rotation=90, fontsize=6.5, color=GREY,
        ha="center", va="center")
seg(50.5, 78, 97.5, 78)
for xc in (50.5, 67.5, 86.5):
    arrow(xc, 78, xc, 74.2)
box(42, 66, 17, 8, "EEGNet", "signal path", msize=8)
box(61, 66, 13, 8, "TCN", "signal path", msize=8, ssize=6.5)
box(78, 66, 17, 8, "Transformer", "signal path", msize=8, ssize=6.5)
# 融合
box(14, 53, 74, 7, "Weighted soft voting", "stacking meta-learner, weights updated online", msize=8.5)
for xc in (22, 50.5, 67.5, 86.5):
    arrow(xc, 64 if xc == 22 else 66, xc, 60.2)

# ================= 分歧检测与二次仲裁(层外) =================
box(10, 38, 58, 11.5, "Disagreement detection",
    "prob-diff \u2265 0.30   \u00b7   majority < 0.60   \u00b7   entropy \u2265 1.099\n(calibrated trigger rate: 39.7%)",
    msize=8.5, ssize=7)
arrow(51, 53, 51, 49.7)

box(74, 37, 26, 13, "Second-pass arbitration",
    "attention-weighted\nconsensus", edge=RED, lw=1.0, ls=(0, (4, 2)), msize=8, ssize=7)
arrow(68, 44, 74, 44, color=RED, dashed=True)
ax.text(71, 45.8, "trigger", fontsize=6.5, color=RED, ha="center")
# refine 回路(折线,最外侧)
seg(100, 43.5, 102.5, 43.5, color=RED, dashed=True)
seg(102.5, 43.5, 102.5, 56.5, color=RED, dashed=True)
arrow(102.5, 56.5, 88.2, 56.5, color=RED, dashed=True)
ax.text(95.5, 58, "refine", fontsize=6.5, color=RED, ha="center")

# ================= Validation =================
band(2, 26, 94, 9, "Validation layer")
arrow(39, 38, 39, 36.2)
seg(25, 36, 74, 36)
arrow(25, 36, 25, 33.2)
arrow(74, 36, 74, 33.2)
box(8, 27, 34, 6, "Consistency agent", msize=8)
box(54, 27, 40, 6, "Explainability agent", msize=8)

# ================= 输出 =================
box(14, 17, 72, 6, "Subject-level aggregation (p90 over epochs)", msize=8.5)
arrow(25, 27, 25, 23.2)
arrow(74, 27, 74, 23.2)
box(22, 6, 56, 8, "Output", "Normal / Abnormal + confidence + explanation", msize=8.5)
arrow(50, 17, 50, 14.2)

# ================= 图例 =================
seg(4, 2.5, 8, 2.5)
ax.text(9.5, 2.5, "data flow", fontsize=6.5, color=GREY, va="center")
seg(24, 2.5, 28, 2.5, color=RED, dashed=True)
ax.text(29.5, 2.5, "arbitration feedback", fontsize=6.5, color=GREY, va="center")
ax.add_patch(Rectangle((50, 1.9), 4, 1.2, facecolor=BAND, edgecolor="none"))
ax.text(55.5, 2.5, "system layer", fontsize=6.5, color=GREY, va="center")

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
p.add_run().add_picture(DELIVER_PNG, width=Cm(12.5))

cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_after = Pt(6)
r1 = cap.add_run("Figure 1. ")
r1.bold = True
r1.font.size = Pt(9)
r2 = cap.add_run("Three-layer architecture of EEG-MAS. Solid arrows indicate data flow; "
                 "dashed red arrows indicate the arbitration feedback loop; grey bands "
                 "mark the coordination, feature, diagnosis, and validation layers.")
r2.font.size = Pt(9)

doc.save(DELIVER_DOCX)
print("docx saved:", DELIVER_DOCX)
