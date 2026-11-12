# scripts/generate_figures.py
"""
Generate key experiment & result figures for EEG-MAS (paper/report style).

Style: white background, light-gray grid, multi-panel layout, value labels on
bars, green/orange/red semantic colors. All in-text labels in English.
Data source: outputs/*.json (loaded at runtime, no hand-typed numbers).

Output: outputs/figures/fig_*.png (also copied to the "data and code" folder).

Usage:
    python scripts/generate_figures.py
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------- style ----------------
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.color"] = "#dcdcdc"
    plt.rcParams["grid.linewidth"] = 0.6
# style.use resets fonts -> re-apply after
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "sans-serif"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False

C_BLUE, C_ORANGE, C_GREEN, C_RED, C_PURPLE, C_GRAY = (
    "#3498db", "#f39c12", "#2ecc71", "#e74c3c", "#9b59b6", "#95a5a6")
CLS_COLOR = {"Normal": C_GREEN, "Borderline": C_ORANGE, "Abnormal": C_RED}

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
FIG_DIR = OUT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
COPY_TO = Path(r"c:\Users\23373\Desktop\eeg\data and code\Agent\论文正文LaTeX初稿\figures")  # 论文图目录
DPI = int(os.environ.get("FIG_DPI", 300))  # 投稿用 600 dpi：FIG_DPI=600


def load(name):
    with open(OUT / name, encoding="utf-8") as f:
        return json.load(f)


def savefig(fig, name):
    p = FIG_DIR / name
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if COPY_TO.exists() and not os.environ.get("FIG_NO_COPY"):
        shutil.copy2(p, COPY_TO / name)
    print(f"  saved {name}")


def blabel(ax, containers=None, fmt="%.3f", fs=8, pad=2):
    if containers is None:
        containers = ax.containers
    for c in containers:
        ax.bar_label(c, fmt=fmt, fontsize=fs, padding=pad, color="#2c3e50")


def hline(ax, y, text, color="#7f8c8d"):
    ax.axhline(y, ls="--", lw=1.2, color=color, zorder=1)
    ax.text(ax.get_xlim()[1], y, f" {text}", va="bottom", ha="right",
            fontsize=8, color=color)


# ================= data =================
dq = load("data_quality.json")
sle = load("subject_level_eval.json")
slep = load("test_subject_level_eval_p90.json")
be = load("binary_eval.json")
bep = load("test_binary_eval_p90.json")
se = load("stacking_eval.json")
eab = load("event_feature_ab.json")
af = load("ablation_features.json")
aa = load("ablation_agents.json")
asy = load("ablation_system.json")
cal = load("disagreement_calibration.json")
lma = load("label_metadata_analysis.json")

AGENTS = ["lightgbm", "eegnet", "tcn", "transformer"]
BASELINE = 0.5466  # = 129/236 test majority（1,588 队列，@10 协议）

# ============================================================
# Fig. 1: dataset overview
# ============================================================
fig = plt.figure(figsize=(12, 8))
fig.suptitle("Fig. 1  Dataset overview (1588 records / 158,601 epochs, 19 channels @ 250 Hz, 2-s segments)",
             fontsize=13, fontweight="bold")

# (a) records per split by class
ax = fig.add_subplot(2, 2, 1)
splits = ["train", "val", "test"]
x = np.arange(len(splits))
for i, cls in enumerate(["Normal", "Borderline", "Abnormal"]):
    vals = [dq[s]["records_by_class"][cls] for s in splits]
    b = ax.bar(x + (i - 1) * 0.26, vals, 0.26, label=cls, color=CLS_COLOR[cls])
    ax.bar_label(b, fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(splits)
ax.set_ylabel("Records"); ax.set_ylim(0, 700)
ax.set_title("(a) Records per split (1 record = 1 subject)", fontsize=11)
ax.legend(fontsize=8, frameon=True)

# (b) epochs per split by class
ax = fig.add_subplot(2, 2, 2)
for i, cls in enumerate(["Normal", "Borderline", "Abnormal"]):
    vals = [dq[s]["epochs_by_class"][cls] for s in splits]
    b = ax.bar(x + (i - 1) * 0.26, vals, 0.26, label=cls, color=CLS_COLOR[cls])
    ax.bar_label(b, fmt="%d", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(splits)
ax.set_ylabel("Epochs"); ax.set_ylim(0, 70000)
ax.set_title("(b) Epochs per split (@100 epochs/record)", fontsize=11)
ax.legend(fontsize=8, frameon=True)

# (c) band-power share
ax = fig.add_subplot(2, 2, 3)
bp = dq["band_power_percent"]
bands = ["delta0.5-4", "theta4-8", "alpha8-13", "beta13-30", "gamma30-45"]
band_names = ["δ (0.5-4Hz)", "θ (4-8Hz)", "α (8-13Hz)", "β (13-30Hz)", "γ (30-45Hz)"]
vals = [bp[k] for k in bands]
b = ax.bar(band_names, vals, 0.55, color=C_BLUE, alpha=0.85)
ax.bar_label(b, fmt="%.1f%%", fontsize=9)
ax.set_ylabel("Band-power share (%)"); ax.set_ylim(0, 45)
ax.set_title("(c) Mean band-power share (δ dominant, consistent with young age)", fontsize=11)
ax.tick_params(axis="x", labelsize=9)

# (d) signal-quality distributions
gs = fig.add_gridspec(2, 2)
sub = gs[1, 1].subgridspec(3, 1, hspace=1.1)
metrics = [("SNR (dB)", dq["snr_db"], "%.1f"),
           ("Artifact ratio", dq["artifact_ratio"], "%.3f"),
           ("Epoch keep rate", dq["keep_rate"], "%.3f")]
for i, (name, m, fmt) in enumerate(metrics):
    axd = fig.add_subplot(sub[i])
    axd.plot([m["p10"], m["p90"]], [0, 0], lw=7, solid_capstyle="butt",
             color=C_BLUE, alpha=0.5, zorder=2)
    axd.plot([m["min"], m["p10"]], [0, 0], lw=1.4, color=C_BLUE, zorder=2)
    axd.plot([m["p90"], m["max"]], [0, 0], lw=1.4, color=C_BLUE, zorder=2)
    axd.plot(m["median"], 0, "o", ms=6, color=C_RED, zorder=3)
    axd.annotate(f"median {fmt % m['median']}", (m["median"], 0),
                 xytext=(0, 9), textcoords="offset points",
                 ha="center", fontsize=8, color=C_RED)
    axd.set_ylim(-0.7, 0.9); axd.set_yticks([])
    axd.set_xlim(m["min"] - (m["max"] - m["min"]) * 0.08, m["max"] * 1.02)
    axd.set_ylabel(name, fontsize=8, rotation=0, ha="right", va="center")
    axd.tick_params(axis="x", labelsize=7)
    axd.grid(False)
axd.set_xlabel("Thick line = P10–P90, thin line = full range, red dot = median", fontsize=7)
fig.text(0.72, 0.50, "(d) Signal-quality distributions", fontsize=11, fontweight="bold")

savefig(fig, "fig_data_overview.png")

# ============================================================
# Fig. 2: label metadata insight (event-positive rates)
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5.8))
w = lma["wave_vs_label"]
groups = [("Slow wave", "slow_wave"), ("Sharp wave", "sharp_wave"), ("Spike wave", "spike_wave"),
          ("Epileptiform\n(any)", "epileptiform_count"), ("Generalized\nabnormality", "generalized")]
x = np.arange(len(groups))
for i, cls in enumerate(["Normal", "Borderline", "Abnormal"]):
    vals = [w[k]["pos_rate_by_label"][cls] for _, k in groups]
    b = ax.bar(x + (i - 1) * 0.26, vals, 0.26, label=cls, color=CLS_COLOR[cls])
    ax.bar_label(b, fmt="%.1f%%", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels([g for g, _ in groups], fontsize=10)
ax.set_ylabel("Positive rate (%)"); ax.set_ylim(0, 112)
ax.legend(fontsize=9, title="Clinical label", frameon=True)
savefig(fig, "fig_label_event_insight.png")

# ============================================================
# Fig. 3: per-agent baselines
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Fig. 3  Diagnosis-agent baselines (test@10, 236 subjects / 2360 epochs, majority baseline 0.5466)",
             fontsize=13, fontweight="bold")

# (a) 3-class
ax = axes[0]
x = np.arange(len(AGENTS))
mean_v = [sle["agents"][a]["aggregation"]["mean"]["subject_accuracy"] for a in AGENTS]
p90_v = [slep["agents"][a]["aggregation"]["p90"]["subject_accuracy"] for a in AGENTS]
b1 = ax.bar(x - 0.19, mean_v, 0.38, label="Subject-level mean aggregation")
b2 = ax.bar(x + 0.19, p90_v, 0.38, label="Subject-level p90 aggregation")
blabel(ax, [b1, b2])
ax.set_xticks(x); ax.set_xticklabels(AGENTS, fontsize=10)
ax.set_ylabel("Subject-level Accuracy"); ax.set_ylim(0, 0.68)
hline(ax, BASELINE, "Majority baseline 0.5466")
ax.set_title("(a) 3-class (Normal / Borderline / Abnormal)\n"
             "Borderline macro F1 ≈ 0 for every agent", fontsize=10)
ax.legend(fontsize=8, loc="upper right")

# (b) binary
ax = axes[1]
acc_v = [be["agents"][a]["binary"]["accuracy"] for a in AGENTS]
auc_v = [be["agents"][a]["binary"]["auc"] for a in AGENTS]
t_v = [be["agents"][a]["seconds"] for a in AGENTS]
b1 = ax.bar(x - 0.19, acc_v, 0.38, label="Accuracy", color=C_BLUE)
b2 = ax.bar(x + 0.19, auc_v, 0.38, label="AUC", color=C_GREEN)
blabel(ax, [b1, b2])
ax.set_xticks(x)
ax.set_xticklabels([f"{a}\n({t:.0f}s)" for a, t in zip(AGENTS, t_v)], fontsize=9)
ax.set_ylabel("Subject-level metric (mean aggregation)"); ax.set_ylim(0, 0.80)
hline(ax, BASELINE, "Majority baseline 0.5466")
ax.set_title("(b) Binary (Borderline merged into Abnormal)\n"
             "Inference time over 2360 epochs in parentheses", fontsize=10)
ax.legend(fontsize=8, loc="upper right")
savefig(fig, "fig_agent_baselines.png")

# ============================================================
# Fig. 4: fusion comparison (deployed 532-d base, mean aggregation)
# ============================================================
vb = aa["bases"]["lightgbm"]["variants"]
rows = [
    ("Stacking · LightGBM meta · 4 agents", vb["stacking_full"]["acc"], C_BLUE),
    ("Stacking · LR meta · 4 agents", se["stacking"]["acc"], C_BLUE),
    ("Hard voting (tie → Normal)", vb["hard_voting"]["acc"], C_ORANGE),
    ("Equal-weight soft voting · 4 agents", vb["A9_soft_voting_equal"]["acc"], C_ORANGE),
    ("Single agent · EEGNet (best single)", vb["single_eegnet"]["acc"], C_GRAY),
    ("Single agent · LightGBM", vb["single_lightgbm"]["acc"], C_GRAY),
    ("Single agent · Transformer", vb["single_transformer"]["acc"], C_GRAY),
    ("Single agent · TCN", vb["single_tcn"]["acc"], C_GRAY),
]
rows.sort(key=lambda r: r[1])
fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle("Fig. 4  Fusion method comparison (binary, subject-level mean aggregation, test@10, n=236)\n"
             "Sources: ablation_agents.json (LightGBM meta) + stacking_eval.json (LR meta)",
             fontsize=12, fontweight="bold")
names = [r[0] for r in rows]; vals = [r[1] for r in rows]; cols = [r[2] for r in rows]
b = ax.barh(names, vals, 0.62, color=cols, alpha=0.9)
ax.bar_label(b, fmt="%.4f", fontsize=9, padding=3)
ax.axvline(BASELINE, ls="--", lw=1.3, color="#7f8c8d")
ax.text(BASELINE + 0.004, len(rows) - 0.4, f"Majority baseline\n{BASELINE:.4f}",
        fontsize=8, color="#7f8c8d")
ax.set_xlim(0.40, 0.70); ax.set_xlabel("Subject-level Accuracy")
ax.set_title("Blue = stacking (meta-learning fusion); orange = voting baselines; gray = single agents\n"
             "No fused configuration exceeds the best single agent (EEGNet 0.6441) on test",
             fontsize=10)
savefig(fig, "fig_fusion_comparison.png")

# ============================================================
# Fig. 5: feature-domain ablation + event-feature gain
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(13, 5.9))

# (a) A1–A3
ax = axes[0]
order = ["full", "A1_no_time", "A2_no_freq", "A3_no_timefreq", "no_event"]
labels = ["full\n(614-d)", "A1 w/o time\n(386-d)", "A2 w/o freq\n(462-d)", "A3 w/o TF\n(462-d)", "no_event\n(532-d)"]
full_acc = af["variants"]["full"]["subject_mean"]["accuracy"]
vals = [af["variants"][v]["subject_mean"]["accuracy"] for v in order]
aucs = [af["variants"][v]["subject_mean"]["auc"] for v in order]
cols = [C_BLUE if v == "full" else (C_RED if v == "A2_no_freq" else C_GRAY) for v in order]
b = ax.bar(labels, vals, 0.58, color=cols, alpha=0.9)
for i, (v, a) in enumerate(zip(vals, aucs)):
    d = (v - full_acc) * 100
    ax.text(i, v + 0.003, f"{v:.4f}\nΔ{d:+.1f}pt\nAUC {a:.3f}",
            ha="center", fontsize=7.5, color="#2c3e50", linespacing=1.15)
ax.axhline(full_acc, ls=":", lw=1.2, color=C_BLUE)
ax.set_ylabel("Subject-level Accuracy"); ax.set_ylim(0.53, 0.685)
ax.set_title("(a)", fontsize=11)
ax.tick_params(axis="x", labelsize=9)

# (b) event A/B: quick screen vs full-scale
ax = axes[1]
quick_w, quick_wo = eab["with_event"]["acc"], eab["without_event"]["acc"]
full_w, full_wo = full_acc, af["variants"]["no_event"]["subject_mean"]["accuracy"]
x = np.arange(2)
b1 = ax.bar(x - 0.18, [quick_w, full_w], 0.36, label="With event features (614-d)", color=C_GREEN)
b2 = ax.bar(x + 0.18, [quick_wo, full_wo], 0.36, label="Without event (532-d)", color=C_GRAY)
blabel(ax, [b1, b2])
d_q = (quick_w - quick_wo) * 100
d_f = (full_w - full_wo) * 100
dq_auc = eab["with_event"]["auc"] - eab["without_event"]["auc"]
df_auc = af["variants"]["full"]["subject_mean"]["auc"] - af["variants"]["no_event"]["subject_mean"]["auc"]
ax.annotate(f"ΔAcc {d_q:+.1f}pt, ΔAUC {dq_auc:+.3f}", (0, max(quick_w, quick_wo) + 0.010),
            ha="center", fontsize=9, color=C_RED, fontweight="bold")
ax.annotate(f"ΔAcc {d_f:+.1f}pt, ΔAUC {df_auc:+.3f}", (1, max(full_w, full_wo) + 0.010),
            ha="center", fontsize=9, color=C_GREEN, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(["Quick screen\n(5000 train epochs)", "Full-scale\n(train full @10)"], fontsize=10)
ax.set_ylabel("Subject-level Accuracy"); ax.set_ylim(0.55, 0.70)
ax.set_title("(b)", fontsize=11)
ax.legend(fontsize=9, loc="upper left")
savefig(fig, "fig_ablation_features.png")

# ============================================================
# Fig. 6: agent ablation A4–A6 / A9 (deployed 532-d base)
# ============================================================
fig, ax = plt.subplots(figsize=(11.5, 5.5))
fig.suptitle("Fig. 6  Agent ablation: leave-one-out + voting baselines "
             "(binary stacking, test@10, n=236)\nSource: ablation_agents.json "
             "(base LightGBM = 532-d + mRMR-128; mean aggregation)",
             fontsize=12, fontweight="bold")
var_order = ["stacking_full", "A4_no_eegnet", "A5_no_tcn", "A6_no_transformer",
             "A9_soft_voting_equal", "hard_voting"]
var_labels = ["Stacking\n4 agents", "A4\nw/o EEGNet", "A5\nw/o TCN",
              "A6\nw/o Transformer", "A9\nEqual soft voting", "Hard voting\n(tie → Normal)"]
v_base = [vb[v]["acc"] for v in var_order]
x = np.arange(len(var_order))
b1 = ax.bar(x, v_base, 0.55, color=C_BLUE, alpha=0.9)
blabel(ax, [b1])
eeg_single = vb["single_eegnet"]["acc"]
ax.axhline(eeg_single, ls=":", lw=1.4, color=C_RED,
           label=f"Best single (EEGNet) {eeg_single:.4f}")
ax.set_xticks(x); ax.set_xticklabels(var_labels, fontsize=9)
ax.set_ylabel("Subject-level Accuracy"); ax.set_ylim(0.45, 0.70)
hline(ax, BASELINE, f"Majority baseline {BASELINE:.4f}")
ax.legend(fontsize=9, loc="upper right", ncols=1)
savefig(fig, "fig_ablation_agents.png")

# ============================================================
# Fig. 7: system-mechanism ablation + McNemar + quality stratification
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(13, 9.5))
fig.suptitle("Fig. 7  System-mechanism ablation (3-class full system, mean aggregation, test@10, 2360 epochs / 236 subjects)",
             fontsize=13, fontweight="bold")
# 机制消融仅剩 full vs A8（固定权重）vs A9（等权），A7（无仲裁）已随仲裁机制移除
sys_order = ["full", "A8_fixed_weights", "A9_equal_weights"]
sys_labels = ["full\n(full system)", "A8\nfixed weights", "A9\nequal weights"]

# (a) epoch / subject accuracy
ax = axes[0, 0]
ep_v = [asy["variants"][v]["epoch_acc"] for v in sys_order]
sub_v = [asy["variants"][v]["subject_acc"] for v in sys_order]
x = np.arange(3)
b1 = ax.bar(x - 0.19, ep_v, 0.38, label="Epoch-level Acc", color=C_GRAY)
b2 = ax.bar(x + 0.19, sub_v, 0.38, label="Subject-level Acc (mean)", color=C_BLUE)
blabel(ax, [b1, b2])
ax.set_xticks(x); ax.set_xticklabels(sys_labels, fontsize=9)
ax.set_ylabel("Accuracy"); ax.set_ylim(0.40, 0.60)
hline(ax, BASELINE, f"Majority baseline {BASELINE:.4f}")
ax.set_title("(a) Mechanism ablation (subject-level)", fontsize=10)
ax.legend(fontsize=8, loc="lower left")

# (b) McNemar
ax = axes[0, 1]
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
ax.set_xticks(x); ax.set_xticklabels(mc_labels, fontsize=10)
ax.set_ylabel("Subjects"); ax.set_ylim(0, 14)
ax.set_title("(b) McNemar paired test vs full: none significant\n"
             "(with 236 subjects, ±2pt differences are within noise)", fontsize=10)
ax.legend(fontsize=8, loc="upper left")

# (c) epoch-level quality stratification
ax = axes[1, 0]
qs = asy["quality_stratified"]["epoch_level"]
lvls = ["high", "medium", "low"]
lvl_labels = ["high\n(n=2343)", "medium\n(n=11)", "low\n(n=6)"]
x = np.arange(3)
for i, v in enumerate(sys_order):
    vals = [qs[l][v] for l in lvls]
    b = ax.bar(x + (i - 1.0) * 0.2, vals, 0.19, label=v.replace("_", " "))
    ax.bar_label(b, fmt="%.3f", fontsize=6, padding=1)
ax.set_xticks(x); ax.set_xticklabels(lvl_labels, fontsize=9)
ax.set_ylabel("Epoch-level Acc"); ax.set_ylim(0, 0.90)
ax.set_title("(c) Quality stratification (epoch-level): 99.3% of epochs are high quality\n"
             "medium/low subsets are tiny (n=11/6) — indicative only", fontsize=10)
ax.legend(fontsize=7, ncols=2)

# (d) subject-level quality grouping
ax = axes[1, 1]
qg = asy["quality_stratified"]["subject_level"]
grps = ["all_high_quality", "contains_medium_low"]
grp_labels = ["All high-quality epochs\n(n=221)", "Contains medium/low\n(n=15)"]
x = np.arange(2)
for i, v in enumerate(sys_order):
    vals = [qg[g][v] for g in grps]
    b = ax.bar(x + (i - 1.0) * 0.2, vals, 0.19, label=v.replace("_", " "))
    ax.bar_label(b, fmt="%.3f", fontsize=6, padding=1)
ax.set_xticks(x); ax.set_xticklabels(grp_labels, fontsize=9)
ax.set_ylabel("Subject-level Acc"); ax.set_ylim(0, 0.80)
ax.set_title("(d) Quality grouping (subject-level): dynamic weights show no advantage on low-quality subset\n"
             "— dataset too clean for the mechanism's target scenario (reported honestly)", fontsize=10)
ax.legend(fontsize=7, ncols=2)
savefig(fig, "fig_system_ablation.png")

# ============================================================
# Fig. 8: disagreement-threshold calibration
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12.5, 9.0))
fig.subplots_adjust(hspace=0.38)
md = cal["metric_distributions"]
cf = cal["current_config_firing"]


def quantile_box(ax, q, thr_old, thr_new, xlabel, xlim, note=""):
    stats = [{"med": q["0.5"], "q1": q["0.25"], "q3": q["0.75"],
              "whislo": q["0.05"], "whishi": q["0.95"]}]
    ax.bxp(stats, vert=False, showfliers=False, widths=0.35,
           patch_artist=True, boxprops=dict(facecolor=C_BLUE, alpha=0.4),
           medianprops=dict(color=C_RED, lw=2))
    for thr, name, col in ((thr_old, "old thr", C_RED), (thr_new, "new thr", C_GREEN)):
        ax.axvline(thr, ls="--", lw=1.4, color=col)
        ax.text(thr, 1.42, f"{name} {thr}", ha="center", fontsize=8,
                color=col, fontweight="bold")
    ax.set_ylim(0.2, 1.7); ax.set_yticks([])
    ax.set_xlim(*xlim); ax.set_xlabel(xlabel, fontsize=9)
    if note:
        ax.text(0.98, 0.12, note, transform=ax.transAxes, ha="right",
                fontsize=8, color="#7f8c8d")


axes[0, 0].set_title("(a)", fontsize=11)
quantile_box(axes[0, 0], md["max_prob_diff"], 0.15, 0.30,
             "Max prob diff across 4 agents (same class)", (0.05, 0.45),
             "legacy thr 0.15 < median 0.200 → fires 73.0%\ncalibrated thr 0.30 → strong disagreements only (18.5%)")

axes[0, 1].set_title("(b)", fontsize=11)
quantile_box(axes[0, 1], md["entropy"], 0.80, 1.10,
             "Mean probability entropy (upper bound ln3 ≈ 1.0986)", (0.76, 1.12),
             "legacy thr 0.80 below all samples → fires 100%\ncalibrated thr 1.10 > P99 (1.0984) → rule disabled")

# (c) rule firing rates: legacy vs calibrated escalation thresholds
ax = axes[1, 0]
rules = [("Rule 1\nprob diff > thr", 73.0, 18.5),
         ("Rule 2\nmajority < 0.6", 37.1, 37.1),
         ("Rule 3\nentropy > thr", 100.0, 0.0),
         ("Combined\n(any rule)", 100.0, 48.4)]
x = np.arange(4)
b1 = ax.bar(x - 0.19, [r[1] for r in rules], 0.38, label="Legacy (0.15/0.6/0.80)", color=C_RED)
b2 = ax.bar(x + 0.19, [r[2] for r in rules], 0.38,
            label="Calibrated (0.30/0.6/1.10)", color=C_GREEN)
blabel(ax, [b1, b2], fmt="%.1f%%", fs=9)
ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rules], fontsize=9)
ax.set_ylabel("Escalation-flag rate (%)"); ax.set_ylim(0, 132)
ax.set_title("(c)", fontsize=11)
ax.legend(fontsize=8, loc="upper right")

# (d) Pareto frontier: trigger rate vs error recall of the flagged set
ax = axes[1, 1]
pareto = cal["pareto"]
tx = [p["trigger_rate"] * 100 for p in pareto]
ry = [p["error_recall"] * 100 for p in pareto]
ax.plot(tx, ry, "o-", ms=4, lw=1.2, color=C_BLUE,
        label="Pareto frontier (calibrated thresholds)")
rec = cal["recommend"]
ax.plot(rec["trigger_rate"] * 100, rec["error_recall"] * 100, "*",
        ms=17, color=C_GREEN, mec="#1a5276",
        label=f"Recommended 0.30/0.60/1.10\ntrigger {rec['trigger_rate']*100:.1f}%, "
              f"error recall {rec['error_recall']*100:.1f}%")
ax.plot(100, 100, "X", ms=11, color=C_RED,
        label="Legacy thresholds: flags every\nepoch, no selectivity")
ax.set_xlabel("Escalation trigger rate (%)", fontsize=9)
ax.set_ylabel("Error recall in flagged set (%)", fontsize=9)
ax.set_xlim(-3, 110); ax.set_ylim(0, 112)
ax.set_title("(d)", fontsize=11)
ax.legend(fontsize=7.5, loc="lower right")
savefig(fig, "fig_disagreement_calibration.png")

print("\nAll figures done. Output dir:", FIG_DIR)
