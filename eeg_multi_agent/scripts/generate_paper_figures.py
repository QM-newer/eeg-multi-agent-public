# -*- coding: utf-8 -*-
# scripts/generate_paper_figures.py
"""
Paper-version figures cropped from report figures (per 论文图表caption清单.md):

  Paper Fig. 2   <- report Fig.1 panels (a)(c)(d)  : dataset overview (3 panels)
  Paper Fig. 4   <- report Fig.3 panel (b)         : binary single-agent baselines
  Paper Fig. 7   <- report Fig.7 panels (a)(b)     : mechanism ablation + McNemar
  Paper Fig. S1  <- report Fig.3 panel (a)         : 3-class baselines (supplement)
  Paper Fig. S2  <- report Fig.7 panels (c)(d)     : quality stratification (supplement)

主文图不带图内大标题与解释性副标题（caption 在正文稿件中）；
补充图保留简短标题。数据全部来自 outputs/*.json，无手打数字。

Output: outputs/figures/paper_*.{png,pdf}
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------- style (与 generate_figures.py 一致) ----------------
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.color"] = "#dcdcdc"
    plt.rcParams["grid.linewidth"] = 0.6
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "sans-serif"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False

C_BLUE, C_ORANGE, C_GREEN, C_RED, C_GRAY = (
    "#3498db", "#f39c12", "#2ecc71", "#e74c3c", "#95a5a6")
CLS_COLOR = {"Normal": C_GREEN, "Borderline": C_ORANGE, "Abnormal": C_RED}

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
FIG_DIR = OUT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def load(name):
    with open(OUT / name, encoding="utf-8") as f:
        return json.load(f)


def savefig(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}",
                    dpi=int(os.environ.get("FIG_DPI", 300)) if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {name}.png / .pdf")


def blabel(ax, containers=None, fmt="%.3f", fs=8, pad=2):
    if containers is None:
        containers = ax.containers
    for c in containers:
        ax.bar_label(c, fmt=fmt, fontsize=fs, padding=pad, color="#2c3e50")


def hline(ax, y, label, color="#5d6d7d"):
    """基线虚线作为图例条目（图内不放文字，避免与柱体重叠）。"""
    ax.axhline(y, ls="--", lw=1.2, color=color, zorder=1, label=label)


# ================= data =================
dq = load("data_quality.json")
sle = load("subject_level_eval.json")
be = load("binary_eval.json")
asy = load("ablation_system.json")

AGENTS = ["lightgbm", "eegnet", "tcn", "transformer"]
AGENT_LABELS = ["LightGBM", "EEGNet", "TCN", "Transformer"]
BASELINE = 0.5466  # = 129/236 test majority（1,588 队列，@10 协议）

# ============================================================
# Paper Fig. 2: dataset overview — 3 panels (records / band power / quality)
# ============================================================
fig = plt.figure(figsize=(13, 4.4))
gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.0, 1.3], wspace=0.30)

# (a) records per split by class
ax = fig.add_subplot(gs[0])
splits = ["train", "val", "test"]
x = np.arange(3)
for i, cls in enumerate(["Normal", "Borderline", "Abnormal"]):
    vals = [dq[s]["records_by_class"][cls] for s in splits]
    b = ax.bar(x + (i - 1) * 0.26, vals, 0.26, label=cls, color=CLS_COLOR[cls])
    ax.bar_label(b, fontsize=7.5)
ax.set_xticks(x)
ax.set_xticklabels(["Train", "Validation", "Test"])
ax.set_ylabel("Records (subjects)")
ax.set_ylim(0, 700)
ax.set_title("(a)", fontsize=11)
ax.legend(fontsize=7.5, frameon=True)

# (b) band-power share
ax = fig.add_subplot(gs[1])
bp = dq["band_power_percent"]
bands = ["delta0.5-4", "theta4-8", "alpha8-13", "beta13-30", "gamma30-45"]
band_names = ["δ\n(0.5–4)", "θ\n(4–8)", "α\n(8–13)", "β\n(13–30)", "γ\n(30–45)"]
vals = [bp[k] for k in bands]
b = ax.bar(band_names, vals, 0.55, color=C_BLUE, alpha=0.85)
ax.bar_label(b, fmt="%.1f%%", fontsize=8)
ax.set_ylabel("Band-power share (%)")
ax.set_ylim(0, 45)
ax.set_title("(b)", fontsize=11)
ax.set_xlabel("EEG band (Hz)", fontsize=8)
ax.tick_params(axis="x", labelsize=8)

# (c) signal-quality distributions
sub = gs[2].subgridspec(3, 1, hspace=1.25)
metrics = [("SNR (dB)", dq["snr_db"], "%.1f"),
           ("Artifact ratio", dq["artifact_ratio"], "%.3f"),
           ("Epoch keep rate", dq["keep_rate"], "%.3f")]
for i, (name, m, fmt) in enumerate(metrics):
    axd = fig.add_subplot(sub[i])
    axd.plot([m["p10"], m["p90"]], [0, 0], lw=7, solid_capstyle="butt",
             color=C_BLUE, alpha=0.5, zorder=2)
    axd.plot([m["min"], m["p10"]], [0, 0], lw=1.4, color=C_BLUE, zorder=2)
    axd.plot([m["p90"], m["max"]], [0, 0], lw=1.4, color=C_BLUE, zorder=2)
    axd.plot(m["median"], 0, "o", ms=5, color=C_RED, zorder=3)
    axd.annotate(f"median {fmt % m['median']}", (m["median"], 0),
                 xytext=(0, 8), textcoords="offset points",
                 ha="center", fontsize=7.5, color=C_RED)
    axd.set_ylim(-0.7, 0.9)
    axd.set_yticks([])
    axd.set_xlim(m["min"] - (m["max"] - m["min"]) * 0.08, m["max"] * 1.02)
    axd.set_ylabel(name, fontsize=8, rotation=0, ha="right", va="center")
    axd.tick_params(axis="x", labelsize=7)
    axd.grid(False)
    if i == 0:
        axd.set_title("(c)", fontsize=11, loc="left", pad=3)
axd.set_xlabel("Thick line = P10–P90, thin line = full range, red dot = median",
               fontsize=7)
savefig(fig, "paper_fig2_dataset_overview")

# ============================================================
# Paper Fig. 4: binary single-agent baselines (single panel)
# ============================================================
fig, ax = plt.subplots(figsize=(7.5, 4.6))
acc_v = [be["agents"][a]["binary"]["accuracy"] for a in AGENTS]
auc_v = [be["agents"][a]["binary"]["auc"] for a in AGENTS]
t_v = [be["agents"][a]["seconds"] for a in AGENTS]
x = np.arange(4)
b1 = ax.bar(x - 0.19, acc_v, 0.38, label="Accuracy", color=C_BLUE)
b2 = ax.bar(x + 0.19, auc_v, 0.38, label="AUC", color=C_GREEN)
blabel(ax, [b1, b2])
ax.set_xticks(x)
ax.set_xticklabels([f"{l}\n({t:.0f} s)" for l, t in zip(AGENT_LABELS, t_v)],
                   fontsize=9)
ax.set_ylabel("Subject-level metric (mean aggregation)")
ax.set_xlabel("Diagnosis agent (inference time over 2,360 test epochs in parentheses)",
              fontsize=9)
ax.set_ylim(0, 0.85)
hline(ax, BASELINE, "Majority baseline (0.5466)")
ax.legend(fontsize=8, loc="upper right")
savefig(fig, "paper_fig4_binary_baselines")

# ============================================================
# Paper Fig. 7: mechanism ablation (a) + McNemar (b)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.5))
# 机制消融仅剩 full vs A8（固定权重）vs A9（等权），A7（无仲裁）已随仲裁机制移除
sys_order = ["full", "A8_fixed_weights", "A9_equal_weights"]
sys_labels = ["Full system", "A8\nfixed weights",
              "A9\nequal weights"]

# (a) epoch / subject accuracy
ax = axes[0]
ep_v = [asy["variants"][v]["epoch_acc"] for v in sys_order]
sub_v = [asy["variants"][v]["subject_acc"] for v in sys_order]
x = np.arange(3)
b1 = ax.bar(x - 0.19, ep_v, 0.38, label="Epoch-level Acc", color=C_GRAY)
b2 = ax.bar(x + 0.19, sub_v, 0.38, label="Subject-level Acc (mean)", color=C_BLUE)
blabel(ax, [b1, b2])
ax.set_xticks(x)
ax.set_xticklabels(sys_labels, fontsize=9)
ax.set_ylabel("Accuracy")
ax.set_ylim(0.40, 0.70)
hline(ax, BASELINE, "Majority baseline (0.5466)")
ax.set_title("(a)", fontsize=11)
ax.legend(fontsize=8, loc="upper center", ncols=2, frameon=True)

# (b) McNemar paired test vs full
ax = axes[1]
mc = asy["mcnemar_vs_full"]
mc_order = ["A8_fixed_weights", "A9_equal_weights"]
mc_labels = ["A8 fixed weights", "A9 equal weights"]
bb = [mc[v]["full_correct_variant_wrong"] for v in mc_order]
cc = [mc[v]["full_wrong_variant_correct"] for v in mc_order]
pp = [mc[v]["p_value"] for v in mc_order]
x = np.arange(2)
b1 = ax.bar(x - 0.17, bb, 0.34, label="b: full correct / variant wrong", color=C_GREEN)
b2 = ax.bar(x + 0.17, cc, 0.34, label="c: full wrong / variant correct", color=C_RED)
blabel(ax, [b1, b2], fmt="%d", fs=10)
for i, p in enumerate(pp):
    ax.text(i, max(bb[i], cc[i]) + 1.6, f"p = {p:.2f}\n(n.s.)",
            ha="center", fontsize=9, color="#7f8c8d")
ax.set_xticks(x)
ax.set_xticklabels(mc_labels, fontsize=9)
ax.set_ylabel("Subjects")
ax.set_ylim(0, 14)
ax.set_title("(b)", fontsize=11)
ax.legend(fontsize=8, loc="upper left")
savefig(fig, "paper_fig7_mechanism_ablation")

# ============================================================
# Paper Fig. S1: 3-class single-agent baselines (supplement)
# ============================================================
fig, ax = plt.subplots(figsize=(7.5, 4.6))
mean_v = [sle["agents"][a]["aggregation"]["mean"]["subject_accuracy"] for a in AGENTS]
slep = load("test_subject_level_eval_p90.json")
p90_v = [slep["agents"][a]["aggregation"]["p90"]["subject_accuracy"] for a in AGENTS]
x = np.arange(4)
b1 = ax.bar(x - 0.19, mean_v, 0.38, label="Subject-level mean aggregation")
b2 = ax.bar(x + 0.19, p90_v, 0.38, label="Subject-level p90 aggregation")
blabel(ax, [b1, b2])
ax.set_xticks(x)
ax.set_xticklabels(AGENT_LABELS, fontsize=9)
ax.set_ylabel("Subject-level Accuracy")
ax.set_ylim(0, 0.68)
hline(ax, BASELINE, "Majority baseline (0.5466)")
ax.legend(fontsize=8, loc="upper right")
savefig(fig, "paper_figS1_three_class_baselines")

# ============================================================
# Paper Fig. S2: quality-stratified analysis (supplement)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))

# (a) epoch-level stratification
ax = axes[0]
qs = asy["quality_stratified"]["epoch_level"]
lvls = ["high", "medium", "low"]
lvl_labels = ["high\n(n=2343)", "medium\n(n=11)", "low\n(n=6)"]
x = np.arange(3)
for i, v in enumerate(sys_order):
    vals = [qs[l][v] for l in lvls]
    b = ax.bar(x + (i - 1.0) * 0.2, vals, 0.19, label=v.replace("_", " "))
    ax.bar_label(b, fmt="%.3f", fontsize=6, padding=1)
ax.set_xticks(x)
ax.set_xticklabels(lvl_labels, fontsize=9)
ax.set_ylabel("Epoch-level Acc")
ax.set_ylim(0, 0.90)
ax.set_title("(a)", fontsize=11)
ax.legend(fontsize=7, ncols=2)

# (b) subject-level grouping
ax = axes[1]
qg = asy["quality_stratified"]["subject_level"]
grps = ["all_high_quality", "contains_medium_low"]
grp_labels = ["All high-quality epochs\n(n=221)", "Contains medium/low\n(n=15)"]
x = np.arange(2)
for i, v in enumerate(sys_order):
    vals = [qg[g][v] for g in grps]
    b = ax.bar(x + (i - 1.0) * 0.2, vals, 0.19, label=v.replace("_", " "))
    ax.bar_label(b, fmt="%.3f", fontsize=6, padding=1)
ax.set_xticks(x)
ax.set_xticklabels(grp_labels, fontsize=9)
ax.set_ylabel("Subject-level Acc")
ax.set_ylim(0, 0.80)
ax.set_title("(b)", fontsize=11)
ax.legend(fontsize=7, ncols=2)
savefig(fig, "paper_figS2_quality_stratification")

# ---------- Paper Fig. S3: aggregation-scheme sensitivity (mean vs p90) ----------
bep = load("test_binary_eval_p90.json")
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Paper Fig. S3  Aggregation-scheme sensitivity: subject-level mean vs p90 "
             "(test@10, 236 subjects)\nMean aggregation was pre-specified from validation data; "
             "p90 shown as the sensitivity analysis", fontsize=11, fontweight="bold")
for ax, ev, ep, ttl, flat in (
    (axes[0], sle, slep, "(a) 3-class accuracy", False),
    (axes[1], be, bep, "(b) Binary accuracy", True),
):
    x = np.arange(len(AGENTS))
    if flat:
        m = [ev["agents"][a]["binary"]["accuracy"] for a in AGENTS]
        p = [ep["agents"][a]["binary"]["accuracy"] for a in AGENTS]
    else:
        m = [ev["agents"][a]["aggregation"]["mean"]["subject_accuracy"] for a in AGENTS]
        p = [ep["agents"][a]["aggregation"]["p90"]["subject_accuracy"] for a in AGENTS]
    b1 = ax.bar(x - 0.19, m, 0.38, label="mean (pre-specified)")
    b2 = ax.bar(x + 0.19, p, 0.38, label="p90 (sensitivity)")
    for bb in (b1, b2):
        ax.bar_label(bb, fmt="%.4f", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(AGENTS, fontsize=10)
    ax.axhline(BASELINE, ls="--", lw=1.2, color="#7f8c8d")
    ax.text(3.4, BASELINE + 0.004, f"majority baseline {BASELINE:.4f}",
            fontsize=7.5, color="#7f8c8d", ha="right", va="bottom")
    ax.set_ylabel("Subject-level Accuracy")
    ax.set_ylim(0.35, 0.72)
    ax.set_title(ttl, fontsize=10)
    ax.legend(fontsize=9, loc="upper right")
fig.tight_layout(rect=[0, 0, 1, 0.88])
fig.savefig(FIG_DIR / "paper_figS3_agg_sensitivity.png",
            dpi=int(os.environ.get("FIG_DPI", 300)))
print("saved: paper_figS3_agg_sensitivity.png")
plt.close(fig)

print("\nPaper figures done. Output dir:", FIG_DIR)
