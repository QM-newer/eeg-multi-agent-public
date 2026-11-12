# -*- coding: utf-8 -*-
"""生成论文用系统架构图（EEG-MAS 三层多智能体架构）。

依据 orchestrator/orchestrator.py 的 diagnose() 九步流程绘制：
  1 信号质量评估 → 2 SNR 感知动态权重 → 3 多域特征提取（4 个特征 Agent，614 维）
  → 4 四个诊断 Agent 并行推理 → 5 加权投票 → 6 分歧检测
  → 7（触发时）空间特征增强 + 可信度仲裁 → 8/9 一致性 + 可解释性
  → 被试级聚合（mean / max / p90）→ 最终报告。

输出：outputs/figures/fig_system_architecture.{png,pdf,svg}
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# ---------- 全局样式 ----------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Microsoft YaHei"],
    "axes.unicode_minus": False,
})

# 图层配色（与既有实验图一致的马卡龙色系）
C_COORD_FACE, C_COORD_EDGE = "#EAEFF4", "#5D6D7E"   # 协调层（Orchestrator）
C_FEAT_FACE,  C_FEAT_EDGE  = "#D6EAF8", "#2E86C1"   # 特征层
C_DIAG_FACE,  C_DIAG_EDGE  = "#FDEBD0", "#E67E22"   # 诊断层
C_SIG_FACE,   C_SIG_EDGE   = "#FEF9E7", "#B7950B"   # 信号驱动子组
C_VAL_FACE,   C_VAL_EDGE   = "#D5F5E3", "#27AE60"   # 验证层
C_ARB_FACE,   C_ARB_EDGE   = "#FADBD8", "#C0392B"   # 条件仲裁
C_IO_FACE,    C_IO_EDGE    = "#FFFFFF", "#34495E"   # 输入 / 输出
C_ARROW = "#5D6D7E"
C_TEXT  = "#1B2631"
C_MUTED = "#7F8C8D"

fig, ax = plt.subplots(figsize=(10.0, 13.0))
ax.set_xlim(0, 100)
ax.set_ylim(-5, 130)
ax.axis("off")


# ---------- 绘图原语 ----------
def box(x1, x2, y1, y2, title, subtitle=None, fc=C_IO_FACE, ec=C_IO_EDGE,
        tfs=10.5, sfs=7.8, lw=1.4):
    """圆角框：标题（上）+ 可选多行副标题（下）"""
    ax.add_patch(FancyBboxPatch(
        (x1, y1), x2 - x1, y2 - y1,
        boxstyle="round,pad=0,rounding_size=1.1",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3))
    cx = (x1 + x2) / 2
    if subtitle:
        ax.text(cx, y2 - (y2 - y1) * 0.28, title, ha="center", va="center",
                fontsize=tfs, fontweight="bold", color=C_TEXT, zorder=4)
        ax.text(cx, y1 + (y2 - y1) * 0.27, subtitle, ha="center", va="center",
                fontsize=sfs, color="#424949", zorder=4, linespacing=1.4)
    else:
        ax.text(cx, (y1 + y2) / 2, title, ha="center", va="center",
                fontsize=tfs, fontweight="bold", color=C_TEXT, zorder=4)


def container(x1, x2, y1, y2, label, ec, fs=11):
    """虚线层容器 + 左上角层名"""
    ax.add_patch(FancyBboxPatch(
        (x1, y1), x2 - x1, y2 - y1,
        boxstyle="round,pad=0,rounding_size=1.6",
        facecolor="none", edgecolor=ec, linewidth=1.3,
        linestyle=(0, (5, 3)), zorder=1))
    ax.text(x1 + 2.2, y2 - 2.6, label, ha="left", va="center",
            fontsize=fs, fontweight="bold", color=ec, zorder=2)


def arrow(p_from, p_to, color=C_ARROW, dashed=False, lw=1.5):
    ax.add_patch(FancyArrowPatch(
        p_from, p_to, arrowstyle="-|>", mutation_scale=15, color=color,
        linewidth=lw, linestyle=(0, (4, 3)) if dashed else "solid",
        zorder=2, shrinkA=0, shrinkB=0))


def polyline(points, color=C_ARROW, dashed=False, lw=1.4):
    """折线：前段普通线，末段带箭头"""
    for i in range(len(points) - 2):
        ax.add_line(Line2D([points[i][0], points[i + 1][0]],
                           [points[i][1], points[i + 1][1]],
                           color=color, linewidth=lw,
                           linestyle=(0, (4, 3)) if dashed else "solid",
                           zorder=2))
    arrow(points[-2], points[-1], color=color, dashed=dashed, lw=lw)


def step_tag(x, y, text):
    ax.text(x, y, text, ha="right", va="center", fontsize=7,
            style="italic", color=C_MUTED)


# ---------- 标题 ----------
ax.text(50, 128.6, "EEG-MAS: Three-Layer Multi-Agent System Architecture",
        ha="center", va="center", fontsize=14, fontweight="bold", color=C_TEXT)

# ---------- 输入 ----------
box(33, 67, 121, 126.5, "Input EEG Epoch",
    "19 channels · 250 Hz · 2 s (500 samples)", fc=C_IO_FACE, ec=C_IO_EDGE, lw=1.8)
arrow((50, 121), (50, 118.5))

# ---------- 协调层：质量评估 / 动态权重 ----------
box(33, 67, 112.5, 118.5, "Signal Quality Assessment",
    "SNR · artifact ratio · keep rate\n→ quality level (high / medium / low)",
    fc=C_COORD_FACE, ec=C_COORD_EDGE, sfs=7.2)
step_tag(32, 115.5, "step 1")
arrow((50, 112.5), (50, 111))

box(33, 67, 105, 111, "Dynamic Agent Weighting",
    "static base weights (val accuracy)\n+ SNR-conditioned adjustment",
    fc=C_COORD_FACE, ec=C_COORD_EDGE, sfs=7.2)
step_tag(32, 108, "step 2")
arrow((50, 105), (50, 103))

# ---------- 特征层 ----------
container(8, 92, 88, 103, "Feature Layer — parallel feature agents", C_FEAT_EDGE)
step_tag(7, 95.5, "step 3")
feat_boxes = [
    (10, 28, "Time-Domain", "228-d"),
    (30, 48, "Frequency", "152-d"),
    (50, 68, "Time-Frequency", "152-d"),
    (70, 88, "Event", "82-d · epileptiform"),
]
for x1, x2, t, s in feat_boxes:
    box(x1, x2, 94, 99, t, s, fc=C_FEAT_FACE, ec=C_FEAT_EDGE, tfs=9.5, sfs=7.2)
    arrow(((x1 + x2) / 2, 94), ((x1 + x2) / 2, 92.5), lw=1.2)

box(10, 90, 89, 92.5, "concatenate → 614-d multi-domain feature vector",
    fc="#EBF5FB", ec=C_FEAT_EDGE, tfs=9, lw=1.1)

# 614 维特征 → LightGBM（特征驱动路径）
arrow((80, 89), (80, 76))

# ---------- 诊断层 ----------
container(8, 92, 61, 84, "Diagnosis Layer — parallel diagnosis agents", C_DIAG_EDGE)
step_tag(7, 72.5, "step 4")

# 信号驱动子组（原始 epoch 输入）
container(11, 65, 63, 78.5, "signal-driven — raw epochs", C_SIG_EDGE, fs=8.5)
for x1, x2, name in [(13, 28, "EEGNet"), (30, 45, "TCN"), (47, 63, "Transformer")]:
    box(x1, x2, 64.5, 72.5, name, fc=C_SIG_FACE, ec=C_SIG_EDGE, tfs=9.5, lw=1.2)

# 特征驱动：LightGBM
box(71, 89, 66, 76, "LightGBM", "mRMR-128 features\n(feature-driven)",
    fc=C_DIAG_FACE, ec=C_DIAG_EDGE, tfs=9.5, sfs=7.2)

ax.text(50, 62.2, "each agent outputs P(Normal / Borderline / Abnormal)",
        ha="center", va="center", fontsize=7, style="italic", color=C_MUTED)

arrow((50, 61), (50, 57.5))

# ---------- 协调层：投票 / 分歧检测 ----------
box(33, 67, 52, 57.5, "Weighted Voting",
    "weighted fusion of agent probabilities",
    fc=C_COORD_FACE, ec=C_COORD_EDGE, sfs=7.2)
step_tag(32, 54.75, "step 5")
arrow((50, 52), (50, 49.5))

box(22, 60, 40.5, 49.5, "Disagreement Detection",
    "max prob-diff > 0.30\nmajority ratio < 0.60\nmean entropy > 1.099 (calibrated)",
    fc=C_COORD_FACE, ec=C_COORD_EDGE, sfs=7.4)
step_tag(21, 45, "step 6")

# 未触发直通路径
arrow((40, 40.5), (40, 34))
ax.text(41.5, 37, "not triggered (60.3%)", ha="left", va="center",
        fontsize=7, color=C_MUTED)

# 触发分支 → 仲裁
arrow((60, 45), (67, 45), color=C_ARB_EDGE, dashed=True)
box(67, 99, 36.5, 52, "Second-Pass Arbitration",
    "triggered on 39.7% of epochs\n1) spatial-feature augmentation\n"
    "2) re-inference on augmented features\n3) credibility re-weighting → re-vote",
    fc=C_ARB_FACE, ec=C_ARB_EDGE, sfs=7.4)
ax.text(82, 53.2, "step 7 (conditional)", ha="center", va="center",
        fontsize=7, style="italic", color=C_ARB_EDGE)
# 仲裁回流 → 验证层
arrow((82, 36.5), (82, 34), color=C_ARB_EDGE)

# ---------- 验证层 ----------
container(22, 90, 23, 34, "Validation Layer", C_VAL_EDGE)
step_tag(21, 28.5, "steps 8–9")
box(25, 55, 24, 30.8, "Consistency Agent", "cross-agent agreement score",
    fc=C_VAL_FACE, ec=C_VAL_EDGE, tfs=9.5, sfs=7.2)
box(58, 88, 24, 30.8, "Explainability Agent", "top-feature evidence chain",
    fc=C_VAL_FACE, ec=C_VAL_EDGE, tfs=9.5, sfs=7.2)

# ---------- epoch 级 / 被试级分界 ----------
ax.add_line(Line2D([2, 98], [19, 19], color=C_MUTED, linewidth=0.9,
                   linestyle=(0, (5, 4)), zorder=1))
ax.text(3, 20.7, "epoch level", ha="left", va="center",
        fontsize=7.5, style="italic", color=C_MUTED)
ax.text(3, 17.3, "subject level", ha="left", va="center",
        fontsize=7.5, style="italic", color=C_MUTED)

arrow((56, 23), (56, 17))

# ---------- 被试级聚合与输出 ----------
box(30, 70, 10.5, 17, "Subject-Level Aggregation",
    "epoch probabilities → mean / max / p90", fc=C_IO_FACE, ec=C_IO_EDGE)
arrow((50, 10.5), (50, 8.5))

box(22, 90, 1, 8.5, "Final Output & Report",
    "diagnosis · confidence · consistency score · evidence chain\n"
    "low confidence → recommend human review",
    fc=C_IO_FACE, ec=C_IO_EDGE, lw=1.8)

# ---------- 原始 epoch 旁路（信号驱动路径） ----------
polyline([(33, 123.75), (3.5, 123.75), (3.5, 70.5), (10.9, 70.5)])
ax.text(2.1, 97, "raw epoch (signal-driven path)", rotation=90,
        ha="center", va="center", fontsize=7.5, style="italic", color=C_MUTED)

# ---------- 图例 ----------
legend_items = [
    (C_COORD_FACE, C_COORD_EDGE, "Coordination (Orchestrator)"),
    (C_FEAT_FACE, C_FEAT_EDGE, "Feature layer"),
    (C_DIAG_FACE, C_DIAG_EDGE, "Diagnosis layer"),
    (C_VAL_FACE, C_VAL_EDGE, "Validation layer"),
    (C_ARB_FACE, C_ARB_EDGE, "Conditional arbitration"),
    (C_IO_FACE, C_IO_EDGE, "Input / output"),
]
ax.text(69, 126.2, "System layers", ha="left", va="center",
        fontsize=9, fontweight="bold", color=C_TEXT)
for i, (fc, ec, label) in enumerate(legend_items):
    y = 122.8 - i * 3.5
    ax.add_patch(FancyBboxPatch((69, y - 1.1), 4, 2.2,
                 boxstyle="round,pad=0,rounding_size=0.5",
                 facecolor=fc, edgecolor=ec, linewidth=1.1, zorder=3))
    ax.text(74.2, y, label, ha="left", va="center", fontsize=8, color=C_TEXT)
# 箭头样式说明（底部横排：实线 = 数据流，红色虚线 = 条件分支）
arrow((24, -2), (28, -2), lw=1.5)
ax.text(29, -2, "data flow", ha="left", va="center", fontsize=8, color=C_TEXT)
arrow((52, -2), (56, -2), color=C_ARB_EDGE, dashed=True, lw=1.5)
ax.text(57, -2, "conditional branch", ha="left", va="center",
        fontsize=8, color=C_TEXT)

# ---------- 保存 ----------
out_dir = Path(__file__).resolve().parents[1] / "outputs" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf", "svg"):
    fig.savefig(out_dir / f"fig_system_architecture.{ext}",
                dpi=300, bbox_inches="tight", facecolor="white")
print(f"saved: {out_dir / 'fig_system_architecture.png'}")
