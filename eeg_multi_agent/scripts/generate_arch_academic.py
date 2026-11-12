# -*- coding: utf-8 -*-
"""学术黑白线框版系统架构图(教科书/TikZ 风格)。
内容与论文当前版本一致:614-d 特征、mRMR-128、校准后分歧三规则(39.7% 触发率)、p90 聚合。
同时生成承载该图的 Word 说明文档(给老师交付用)。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 8.5,
})

OUT_FIG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\eeg_multi_agent\outputs\figures\fig_system_architecture_academic.png"
DELIVER_PNG = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS架构图(学术黑白版).png"
DELIVER_DOCX = r"c:\Users\23373\Desktop\eeg\data and code\Agent\EEG-MAS系统架构图说明.docx"

fig, ax = plt.subplots(figsize=(7.2, 8.0))
ax.set_xlim(0, 100)
ax.set_ylim(13, 110)
ax.axis("off")

GREY_BG = "#F2F2F2"
INK = "black"


def box(x, y, w, h, text, fs=8.5, bold=False, fill="white", lw=0.9, ls="-"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=INK,
                           linewidth=lw, linestyle=ls, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", linespacing=1.3, zorder=4)


def band(x, y, w, h, label):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=GREY_BG, edgecolor="none", zorder=1))
    ax.text(x + 1.2, y + h - 1.6, label, ha="left", va="top", fontsize=7.5,
            style="italic", color="#555555", zorder=2)


def arrow(x1, y1, x2, y2, dashed=False, lw=0.9):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=9, color=INK, linewidth=lw,
                                 linestyle=(0, (4, 2)) if dashed else "-",
                                 shrinkA=0, shrinkB=0, zorder=5))


def line(x1, y1, x2, y2, lw=0.9):
    ax.plot([x1, x2], [y1, y2], color=INK, linewidth=lw, zorder=5)

# ---------- 层背景 ----------
band(6, 93, 88, 10, "Coordination layer")
band(4, 76, 92, 14, "Feature layer")
band(4, 55, 92, 19, "Diagnosis layer")
band(6, 34, 88, 8, "Validation layer")

# ---------- 输入 ----------
box(22, 105.5, 56, 3.5, "Input: 19-channel EEG epochs (250 Hz, 2-s)", fs=8.5)

# ---------- 协调层 ----------
box(8, 94.5, 38, 7, "Signal quality gating\n(SNR, artifact ratio)")
box(54, 94.5, 38, 7, "Dynamic agent weighting\n(val-initialized, updated online)")
arrow(50, 105.5, 50, 103)          # input -> coordination band
arrow(46, 98, 54, 98)              # gating -> weighting

# 特征层分流母线
line(73, 94.5, 73, 92)
line(16.25, 92, 82.25, 92)
for xc in (16.25, 38.25, 60.25, 82.25):
    arrow(xc, 92, xc, 89)

# ---------- 特征层 ----------
box(6, 82.5, 20.5, 6.5, "Time domain\n(228-d)")
box(28, 82.5, 20.5, 6.5, "Frequency\n(152-d)")
box(50, 82.5, 20.5, 6.5, "Time–frequency\n(152-d)")
box(72, 82.5, 20.5, 6.5, "Event\n(82-d)")
box(14, 76.5, 72, 4.5, "Concatenate → 614-d feature vector")
for xc in (16.25, 38.25, 60.25, 82.25):
    arrow(xc, 82.5, xc, 81)

# ---------- 信号旁路(原始 epochs 直达深度模型) ----------
line(78, 107.25, 97, 107.25)
line(97, 107.25, 97, 67.5)
arrow(97, 67.5, 95, 67.5)
ax.text(95.2, 86, "raw epochs", rotation=90, ha="center", va="center",
        fontsize=7.5, color="#555555")

# ---------- 诊断层 ----------
box(6, 64, 34, 6.5, "LightGBM\nmRMR-128 features from 614-d", fs=8)
box(52, 64, 12.5, 6.5, "EEGNet", fs=8)
box(66.5, 64, 11, 6.5, "TCN", fs=8)
box(79.5, 64, 15.5, 6.5, "Transformer", fs=8)
box(12, 56, 80, 5.5, "Weighted soft voting (stacking meta-learner, weights updated online)", fs=8.5)

arrow(50, 76.5, 23, 70.5)          # 614-d -> LightGBM
arrow(58.25, 64, 58.25, 61.5)
arrow(72, 64, 72, 61.5)
arrow(87.25, 64, 87.25, 61.5)
arrow(23, 64, 23, 61.5)

# ---------- 分歧检测 ----------
box(6, 45, 64, 8, "Disagreement detection\nprob-diff ≥ 0.30, majority < 0.60, entropy ≥ 1.099\n(calibrated trigger rate: 39.7%)", fs=8.5)
arrow(52, 56, 52, 53)

# ---------- 二次仲裁(虚线) ----------
box(74, 44.5, 23, 9, "Second-pass\narbitration\n(attention-weighted\nconsensus)", fs=8, ls=(0, (4, 2)))
arrow(70, 49, 74, 49, dashed=True)
arrow(85.5, 53.5, 92, 56, dashed=True)   # 仲裁 -> 融合 右端

# ---------- 验证层 ----------
box(10, 35, 32, 6, "Consistency agent")
box(58, 35, 32, 6, "Explainability agent")
arrow(25, 45, 26, 41)
arrow(65, 45, 74, 41)

# ---------- 聚合与输出 ----------
box(24, 26, 52, 5, "Subject-level aggregation (p90 over epochs)")
arrow(26, 35, 42, 31)
arrow(74, 35, 58, 31)
box(16, 17, 68, 5.5, "Output: Normal / Abnormal\n+ confidence + explanation", bold=True, lw=1.3)
arrow(50, 26, 50, 22.5)

# ---------- 图例 ----------
ax.text(6, 14.5, "Solid arrows: data flow    Dashed arrows: arbitration feedback    Grey bands: system layers",
        ha="left", va="center", fontsize=7.5, color="#444444")

fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(DELIVER_PNG, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figure saved")

# ============================================================
# Word 文档
# ============================================================
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
p.add_run().add_picture(DELIVER_PNG, width=Cm(15.0))

cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_after = Pt(6)
r1 = cap.add_run("Figure 1. ")
r1.bold = True
r1.font.size = Pt(9)
r2 = cap.add_run("Three-layer architecture of EEG-MAS. Solid arrows indicate data flow; "
                 "dashed arrows indicate the arbitration feedback loop; grey bands mark the "
                 "coordination, feature, diagnosis, and validation layers.")
r2.font.size = Pt(9)

doc.save(DELIVER_DOCX)
print("docx saved:", DELIVER_DOCX)
