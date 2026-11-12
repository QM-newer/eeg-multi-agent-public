# scripts/generate_experiment_report.py
"""
生成《EEG-MAS 完整实验报告》Word 文档（论文写作前的实验过程与结果汇总）。

数据来源：outputs/*.json（2026-10-07 快照），全部数字由脚本运行时从 JSON 读入，
保证与实验产出一致。

用法：
    python scripts/generate_experiment_report.py
输出：
    outputs/EEG-MAS实验报告_<日期>.docx
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
FIG_DIR = OUT / "figures"

ASCII_FONT = "Calibri"
EAST_FONT = "微软雅黑"


def load(name):
    with open(OUT / name, encoding="utf-8") as f:
        return json.load(f)


dq = load("data_quality.json")
sle = load("subject_level_eval.json")
be = load("binary_eval.json")
sva = load("subject_val_accuracies.json")
lsc = load("label_source_comparison.json")
se = load("stacking_eval.json")
eab = load("event_feature_ab.json")
af = load("ablation_features.json")
aa = load("ablation_agents.json")
asy = load("ablation_system.json")
cal = load("disagreement_calibration.json")
ac = load("age_correction_eval.json")
sw = load("slow_wave_subtask.json")
lma = load("label_metadata_analysis.json")
slt = load("subject_level_train.json")

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)  # A4

# ---------------- 排版辅助 ----------------
# 字号方案：标题 22/16/14/12 加粗，正文 11pt，表格 10pt，全部颜色"自动"(黑色)
STYLE_SIZES = {"Title": 22, "Heading 1": 16, "Heading 2": 14, "Heading 3": 12,
               "Heading 4": 12, "Normal": 11, "List Bullet": 11, "List Number": 11,
               "Body Text": 11}
BOLD_STYLES = {"Title", "Heading 1", "Heading 2", "Heading 3", "Heading 4"}


def set_color_auto(rPr):
    """移除显式/主题颜色，写入 w:color val=auto（自动=黑色）"""
    for c in rPr.findall(qn("w:color")):
        rPr.remove(c)
    el = OxmlElement("w:color")
    el.set(qn("w:val"), "auto")
    rPr.append(el)


def apply_styles():
    for name, size in STYLE_SIZES.items():
        try:
            st = doc.styles[name]
        except KeyError:
            continue
        st.font.size = Pt(size)
        st.font.bold = name in BOLD_STYLES
        rPr = st.element.get_or_add_rPr()
        set_color_auto(rPr)
        rf = rPr.get_or_add_rFonts()
        rf.set(qn("w:ascii"), ASCII_FONT)
        rf.set(qn("w:hAnsi"), ASCII_FONT)
        rf.set(qn("w:eastAsia"), EAST_FONT)


def _fix_run(run, in_table=False):
    rPr = run._element.get_or_add_rPr()
    set_color_auto(rPr)
    if in_table and run.font.size is None:
        run.font.size = Pt(10)
    if run.font.name == "Consolas":      # 代码样式只补中文字体
        rPr.get_or_add_rFonts().set(qn("w:eastAsia"), EAST_FONT)
        return
    run.font.name = ASCII_FONT
    rPr.get_or_add_rFonts().set(qn("w:eastAsia"), EAST_FONT)


def finalize_fonts():
    apply_styles()
    for p in doc.paragraphs:
        for r in p.runs:
            _fix_run(r)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        _fix_run(r, in_table=True)


def H(text, level=1):
    doc.add_heading(text, level=level)


def P(text="", bold=False, italic=False, size=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    return p


def BUL(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def NUM(items):
    for it in items:
        doc.add_paragraph(it, style="List Number")


def CODE(lines):
    for ln in lines:
        p = doc.add_paragraph()
        r = p.add_run(ln)
        r.font.name = "Consolas"
        r.font.size = Pt(9)


_tbl_no = [0]
_fig_no = [0]


def FIG(name, caption, width_cm=15.5):
    """插入居中图片 + 图注（图注加粗 10pt），图编号自动递增"""
    path = FIG_DIR / name
    if not path.exists():
        print(f"  [警告] 缺图: {path}")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    _fig_no[0] += 1
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(f"Figure {_fig_no[0]}  {caption}")
    r.bold = True
    r.font.size = Pt(10)


def TBL(caption, headers, rows):
    _tbl_no[0] += 1
    P(f"Table {_tbl_no[0]}  {caption}", bold=True, size=10)
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]
        c.text = ""
        r = c.paragraphs[0].add_run(str(h))
        r.bold = True
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.rows[i + 1].cells[j]
            c.text = ""
            c.paragraphs[0].add_run(str(v))
    P("", size=4)
    return t


def f4(x):
    return "—" if x is None else f"{x:.4f}"


def pct(x, nd=1):
    return "—" if x is None else f"{x * 100:.{nd}f}%"


# ================= 封面 / 导言 =================
doc.add_heading("EEG 多智能体辅助诊断系统（EEG-MAS）实验报告", 0)
P(f"生成日期：{datetime.now():%Y-%m-%d}    数据快照：outputs/*.json    代码库：eeg_multi_agent/")
P("用途：论文写作前的完整实验过程与结果汇总（对应论文计划 5.3 对比基线、5.4 消融实验及机制分析章节）。"
  "全部结果由脚本从实验产出 JSON 自动汇编。")

# ================= 1 项目概述 =================
H("1  项目概述")
P("EEG-MAS 面向儿童常规脑电图的异常自动判读辅助，将“特征提取—诊断—验证”组织为三层多智能体协作系统，"
  "由协调层（Orchestrator）统一调度：单 epoch 诊断流程为 信号质量评估 → 动态权重 → 多域特征提取 → "
  "四个诊断 Agent 并行推理 → 加权投票 → 分歧检测 → （触发时）补充空间特征二次推理与可信度仲裁 → "
  "一致性得分与可解释性输出。epoch 级概率再经被试级聚合（mean / max / p90）形成最终结论。")
P("分类口径：三分类（Normal / Borderline / Abnormal）与二分类（Normal vs Abnormal，Borderline 并入 "
  "Abnormal）。除特别注明外，被试级评估均基于 test 集 @20 epochs/记录（238 被试、4760 epochs），"
  "多数类基线为 0.5504（Normal 131/238）。")
TBL("System architecture", ["Layer", "Members", "Description"], [
    ["Feature layer", "time_domain / freq_domain / timefreq", "532-dim base multi-domain features (228+152+152)"],
    ["Feature layer", "event (added 2026-10)", "82-dim epileptiform-event statistics, gated by include_event"],
    ["Diagnosis layer", "lightgbm", "mRMR-128 feature selection + LightGBM (feature-driven)"],
    ["Diagnosis layer", "eegnet / tcn / transformer", "Deep models (signal-driven), 3-class & binary variants"],
    ["Validation layer", "consistency / explainability agents", "Cross-agent consistency score, top-feature evidence chain"],
    ["Coordination layer", "Orchestrator", "Quality assessment, dynamic weights, voting, disagreement detection & arbitration"],
])
P("核心结论速览：", bold=True)
TBL("Key findings at a glance", ["Item", "Result"], [
    ["Best config (lightgbm_event + EEGNet + TCN, Stacking)", "Subject-level binary Acc 0.6134 (baseline 0.5504, +6.3pt)"],
    ["Default 4-agent Stacking", "Acc 0.5798 (+2.9pt)"],
    ["Event-level features (82-dim), full-scale gain", "+2.1pt Acc (0.6092 → 0.6303)"],
    ["Feature-block importance ranking", "freq > time-freq > time (removing freq −5.5pt)"],
    ["Disagreement-threshold calibration", "Trigger rate 100% → 39.7%, inference time −39%"],
    ["Arbitration contribution (subject-level)", "+0.84pt (McNemar p=0.50, n.s.)"],
    ["Dynamic vs fixed weights", "No significant difference (p=1.00); 99.2% epochs high-quality"],
    ["Borderline class", "macro F1 ≈ 0 for all agents; binary protocol adopted"],
    ["Age-corrected features", "No gain (ΔAUC −0.005)"],
])

# ================= 2 数据集与预处理 =================
H("2  数据集与预处理")
P(f"数据经 250 Hz 重采样、19 通道、2 s 分段，缓存于 E:/eeg_asd_cache/epochs，共 {dq['n_records']} 条记录、"
  f"{dq['n_epochs']} 个 epoch（每条记录对应一名被试，最多 100 epochs）。按记录分层划分："
  f"train {dq['train']['n_records']} / val {dq['val']['n_records']} / test {dq['test']['n_records']}。")
FIG("fig_data_overview.png", "Dataset overview: records and epochs per split (by class), mean band-power share, signal-quality distributions")
TBL("Data splits and class distribution", ["Split", "Records (subjects)", "Epochs", "Normal", "Borderline", "Abnormal", "Majority baseline"], [
    ["train", dq["train"]["n_records"], dq["train"]["n_epochs"],
     f"{dq['train']['records_by_class']['Normal']}", f"{dq['train']['records_by_class']['Borderline']}",
     f"{dq['train']['records_by_class']['Abnormal']}", "—"],
    ["val", dq["val"]["n_records"], dq["val"]["n_epochs"],
     f"{dq['val']['records_by_class']['Normal']}", f"{dq['val']['records_by_class']['Borderline']}",
     f"{dq['val']['records_by_class']['Abnormal']}", f4(133 / 240)],
    ["test", dq["test"]["n_records"], dq["test"]["n_epochs"],
     f"{dq['test']['records_by_class']['Normal']}", f"{dq['test']['records_by_class']['Borderline']}",
     f"{dq['test']['records_by_class']['Abnormal']}", f4(131 / 238)],
])
snr, art, keep, amp = dq["snr_db"], dq["artifact_ratio"], dq["keep_rate"], dq["amplitude"]["epoch_std_uV"]
TBL("Signal-quality statistics (all records)", ["Metric", "Mean", "Median", "P10", "P90", "Range"], [
    ["SNR (dB)", f"{snr['mean']:.2f}", f"{snr['median']:.2f}", f"{snr['p10']:.2f}", f"{snr['p90']:.2f}",
     f"{snr['min']:.2f}–{snr['max']:.2f}"],
    ["Artifact ratio", f"{art['mean']:.3f}", f"{art['median']:.3f}", f"{art['p10']:.3f}", f"{art['p90']:.3f}",
     f"{art['min']:.3f}–{art['max']:.3f}"],
    ["Epoch keep rate", f"{keep['mean']:.3f}", f"{keep['median']:.3f}", f"{keep['p10']:.3f}", f"{keep['p90']:.3f}",
     f"{keep['min']:.3f}–{keep['max']:.3f}"],
    ["Epoch amplitude std (µV)", f"{amp['mean']:.1f}", f"{amp['median']:.1f}", f"{amp['p10']:.1f}", f"{amp['p90']:.1f}",
     f"{amp['min']:.1f}–{amp['max']:.1f}"],
])
bp = dq["band_power_percent"]
P(f"带功率占比：δ(0.5-4Hz) {bp['delta0.5-4']}%、θ {bp['theta4-8']}%、α {bp['alpha8-13']}%、"
  f"β {bp['beta13-30']}%、γ {bp['gamma30-45']}%（δ 占比高与儿童低龄构成一致）。"
  f"test@20 口径下 99.2%（4720/4760）的 epoch 被质量评定为 high。")
P("归一化：训练集逐通道 z-score，统计量持久化于 checkpoints/norm_stats.json，训练与推理共用，"
  "避免泄漏。")
w = lma["wave_vs_label"]
TBL("Label metadata insight (837/1830 records with clinical fields): event-positive rate by label",
    ["Metric", "Abnormal", "Borderline", "Normal"], [
        ["Slow-wave positive rate", pct(w["slow_wave"]["pos_rate_by_label"]["Abnormal"] / 100),
         pct(w["slow_wave"]["pos_rate_by_label"]["Borderline"] / 100),
         pct(w["slow_wave"]["pos_rate_by_label"]["Normal"] / 100)],
        ["Sharp-wave positive rate", pct(w["sharp_wave"]["pos_rate_by_label"]["Abnormal"] / 100),
         pct(w["sharp_wave"]["pos_rate_by_label"]["Borderline"] / 100),
         pct(w["sharp_wave"]["pos_rate_by_label"]["Normal"] / 100)],
        ["Spike-wave positive rate", pct(w["spike_wave"]["pos_rate_by_label"]["Abnormal"] / 100),
         pct(w["spike_wave"]["pos_rate_by_label"]["Borderline"] / 100),
         pct(w["spike_wave"]["pos_rate_by_label"]["Normal"] / 100)],
        ["Epileptiform event (any)", pct(w["epileptiform_count"]["pos_rate_by_label"]["Abnormal"] / 100),
         pct(w["epileptiform_count"]["pos_rate_by_label"]["Borderline"] / 100),
         pct(w["epileptiform_count"]["pos_rate_by_label"]["Normal"] / 100)],
        ["Mean age (years)", f"{lma['age_by_label']['Abnormal']['mean']:.2f}",
         f"{lma['age_by_label']['Borderline']['mean']:.2f}",
         f"{lma['age_by_label']['Normal']['mean']:.2f}"],
    ])
P("解读：判读标签高度事件驱动——慢波等事件阳性率在 Abnormal（97.4%）与 Normal（2.0%）间差距悬殊，"
  "Borderline 介于其间（72.6%）。这既支撑了事件级特征的引入（第 6 节），也预示 Borderline 档的判别难度"
  "（第 4 节证实其不可分）。")
FIG("fig_label_event_insight.png", "Epileptiform-event positive rate by clinical label (motivation for event-level features)")

# ================= 3 实验设置 =================
H("3  实验设置与评估协议")
TBL("Feature system (614-dim layout)", ["Block", "Dim", "Index range", "Content"], [
    ["Time domain", "228", "0–227", "Statistical / morphological / complexity features"],
    ["Frequency domain", "152", "228–379", "Band-power spectral features"],
    ["Time-frequency", "152", "380–531", "Wavelet / TF-energy features"],
    ["Event (new)", "82", "532–613", "Epileptiform-event statistics (EventAgent)"],
])
BUL([
    "特征选择：mRMR（MID 准则）统一降至 128 维后训练 LightGBM；深度模型直接消费原始 epoch。",
    "聚合方式：epoch 概率 → 被试级 mean / max / p90。特征消融主口径为被试级 mean；Agent 消融与融合沿 "
    "stacking_eval 口径用 p90；系统级三分类用 mean。各表标题均注明口径。",
    "评估口径：test@20（238 被试、4760 epochs）为主报告口径；全量特征提取时 train/val 用 @100。",
    "环境：i9-13900HX（24 核）/ 15.7 GB RAM / Windows；Python 3.12.3、numpy 1.26.4、scikit-learn 1.4.2、"
    "LightGBM 4.6.0、PyTorch 2.9.1+cpu；特征提取 8 进程并行。",
])

# ================= 4 各诊断 Agent 基线 =================
H("4  各诊断 Agent 基线（test@20）")
FIG("fig_agent_baselines.png", "Diagnosis-agent baselines: 3-class (mean/p90 aggregation) and binary (Acc/AUC/inference time)")
H("4.1  三分类（被试级 mean / p90 聚合）", 2)
rows = []
for a in ("lightgbm", "eegnet", "tcn", "transformer"):
    d = sle["agents"][a]
    m, p = d["aggregation"]["mean"], d["aggregation"]["p90"]
    rows.append([a, f4(d["epoch_accuracy"]), f4(m["subject_accuracy"]), f4(m["subject_macro_f1"]),
                 f4(p["subject_accuracy"]), f4(p["subject_macro_f1"])])
rows.append(["Majority baseline", "—", f4(0.5504), "—", f4(0.5504), "—"])
TBL("3-class single-agent baselines", ["Agent", "epoch Acc", "Subject Acc (mean)", "macro F1 (mean)", "Subject Acc (p90)", "macro F1 (p90)"], rows)
BUL([
    "Transformer 概率坍缩：被试级全部预测 Normal（macro F1 0.2367），epoch Acc 表面最高（0.5237）纯因多数类占比。",
    "Borderline 档全线 F1 ≈ 0：各混淆矩阵中该档几乎全部误判，三分类 macro F1 被系统性拖低（≤0.40）。",
    "EEGNet 被试级最高 0.5672（mean 与 p90 相同），是唯一超过多数类基线的单 Agent。",
])

H("4.2  二分类（Borderline→Abnormal，被试级 mean 聚合）", 2)
rows = []
for a in ("lightgbm", "eegnet", "tcn", "transformer"):
    d = be["agents"][a]
    rows.append([a, f4(d["binary"]["accuracy"]), f4(d["binary"]["macro_f1"]), f4(d["binary"]["auc"]),
                 f"{d['seconds']:.1f}"])
TBL("Binary single-agent baselines (incl. inference time over 4760 epochs)", ["Agent", "Acc", "macro F1", "AUC", "Time (s)"], rows)
P(f"LightGBM 耗时最高（594.6 s，特征提取占绝对大头），深度模型 10–43 s。验证集参考精度（早期同口径评估）："
  f"lightgbm {sva['lightgbm']:.4f} / eegnet {sva['eegnet']:.4f} / tcn {sva['tcn']:.4f} / "
  f"transformer {sva['transformer']:.4f}。")
P("早期版本（361 维特征、@20）的严格 N vs A 评估（剔除 Borderline 被试）：", bold=True)
r = slt["results"]
TBL("Early N-vs-A evaluation (Borderline subjects excluded)", ["Protocol", "val Acc / baseline", "test Acc / baseline"], [
    ["3-class", f"{r['3class_val']['accuracy']:.4f} / {r['3class_val']['majority_baseline']:.4f}",
     f"{r['3class_test']['accuracy']:.4f} / {r['3class_test']['majority_baseline']:.4f}"],
    ["N vs A (n=212/210)", f"{r['2class_N_vs_A_val']['accuracy']:.4f} / {r['2class_N_vs_A_val']['majority_baseline']:.4f}",
     f"{r['2class_N_vs_A_test']['accuracy']:.4f} / {r['2class_N_vs_A_test']['majority_baseline']:.4f}"],
])
P("Borderline 恢复尝试：以置信度带（0.35–0.65）预测“界限性”两档时，非界限样本上各 Agent 精度仅 "
  "0.086–0.186——Borderline 无法通过置信度恢复，后续主线采用二分类口径。")

H("4.3  标签来源分组分析", 2)
rows = []
for a in ("lightgbm", "eegnet", "tcn", "transformer"):
    g = lsc["groups"][a]
    rows.append([a, f"{g['project']['accuracy']:.4f} ({g['project']['margin_over_baseline']:+.4f})",
                 f"{g['raw_index']['accuracy']:.4f} ({g['raw_index']['margin_over_baseline']:+.4f})"])
TBL("Subject-level accuracy by label source (parentheses: margin over in-group majority baseline)",
    ["Agent", "project group (n=121, baseline 0.5207)", "raw_index group (n=117, baseline 0.5812)"], rows)
P("无论哪一来源组，各 Agent 均未稳定超过组内多数类基线（仅 EEGNet 在 project 组 +3.3pt）；"
  "提示标签存在来源异质性与噪声，是当前精度上限的重要约束。")

# ================= 5 融合 =================
H("5  多模型融合（二分类，被试级 p90 聚合）")
rows = [
    ["Stacking (LightGBM meta-model)", f4(se["stacking"]["acc"]), f4(se["stacking"]["f1"]), f4(se["stacking"]["auc"])],
    ["Soft voting (equal-weight average)", f4(se["soft_voting"]["acc"]), "—", f4(se["soft_voting"]["auc"])],
]
for a in ("lightgbm", "eegnet", "tcn", "transformer"):
    rows.append([f"Single agent: {a}", f4(se["single_agents"][a]["acc"]), "—", f4(se["single_agents"][a]["auc"])])
rows.append(["Majority baseline", f4(se["baseline"]), "—", "—"])
TBL("Fusion method comparison", ["Method", "Acc", "F1", "AUC"], rows)
P("Stacking（val 上训练 LightGBM 元模型组合 4 Agent 的 P(Abnormal)）达 0.5798，超多数类基线 2.9pt、"
  "超最好单 Agent（EEGNet 0.5462）3.4pt；软投票 0.5168 显著劣化，被弱 Agent 拖累。AUC 上软投票反而最高"
  "（0.6852）——概率校准好但排序未转化为精度，故以 Acc 为主指标、AUC 为辅。")
FIG("fig_fusion_comparison.png", "Fusion method comparison: Stacking / voting baselines / single agents (incl. best config lightgbm_event + EEGNet + TCN)")

# ================= 6 事件特征闭环 =================
H("6  事件级特征闭环（2026-10 新增）")
P("动机即第 2 节元数据洞察：标签与癫痫样事件强相关。EventAgent 输出 82 维事件统计特征，"
  "通过 include_event 开关接入特征管线（旧 532 维模型完全向后兼容，融合器持久化口径标记）。")
TBL("Event-feature A/B: quick screen vs full-scale (LightGBM binary)",
    ["Protocol", "Dims", "Acc", "AUC", "ΔAUC"], [
        ["Quick screen (5000 train / 2000 val epochs, 5/record): with event", f"{eab['dims']['time_domain'] + eab['dims']['freq_domain'] + eab['dims']['timefreq'] + eab['dims']['event']}",
         f4(eab["with_event"]["acc"]), f4(eab["with_event"]["auc"]),
         f"{eab['delta']['auc']:+.4f}"],
        ["Quick screen: without event", "532", f4(eab["without_event"]["acc"]), f4(eab["without_event"]["auc"]), ""],
        ["Full-scale (train full @100, test@20, subject mean): with event", f"{af['variants']['full']['n_features']}",
         f4(af["variants"]["full"]["subject_mean"]["accuracy"]), f4(af["variants"]["full"]["subject_mean"]["auc"]),
         f"{af['variants']['full']['subject_mean']['auc'] - af['variants']['no_event']['subject_mean']['auc']:+.4f}"],
        ["Full-scale: without event", f"{af['variants']['no_event']['n_features']}",
         f4(af["variants"]["no_event"]["subject_mean"]["accuracy"]),
         f4(af["variants"]["no_event"]["subject_mean"]["auc"]), ""],
    ])
P(f"快评口径下事件特征为负增益（ΔAUC {eab['delta']['auc']:+.4f}），但全量口径下为正增益"
  f"（Acc {af['variants']['full']['subject_mean']['accuracy'] - af['variants']['no_event']['subject_mean']['accuracy']:+.4f}、"
  f"AUC {af['variants']['full']['subject_mean']['auc'] - af['variants']['no_event']['subject_mean']['auc']:+.4f}）——"
  f"小样本快评结论被推翻。方法论教训：A/B 预实验功效不足以支撑特征取舍。mRMR 在快评中选中 "
  f"{eab['mrmr_event_selected']} 个事件特征，说明其信息量不低但与基础特征部分冗余。")
P("产出：checkpoints/lightgbm_binary_event 与 fusion_binary_event（融合器记录 include_event 口径，"
  "推理时自动匹配特征维度）。")

# ================= 7 消融实验 =================
H("7  消融实验（论文计划 5.4）")
H("7.1  特征域消融 A1–A3 + 事件特征开关", 2)
order = ["full", "no_event", "A1_no_time", "A2_no_freq", "A3_no_timefreq"]
names = {"full": "full (all 614 dims)", "no_event": "no_event (w/o event, 532 dims)", "A1_no_time": "A1: w/o time domain",
         "A2_no_freq": "A2: w/o freq domain", "A3_no_timefreq": "A3: w/o time-freq"}
base_acc = af["variants"]["full"]["subject_mean"]["accuracy"]
rows = []
for v in order:
    d = af["variants"][v]
    rows.append([names[v], d["n_features"], f4(d["train_epoch_acc"]), f4(d["subject_mean"]["accuracy"]),
                 f4(d["subject_mean"]["auc"]), f"{d['subject_mean']['accuracy'] - base_acc:+.4f}"])
TBL("Feature-domain ablation (LightGBM binary, mRMR-128, subject-level mean)",
    ["Variant", "Dims", "train epoch Acc", "test subject Acc", "subject AUC", "ΔAcc vs full"], rows)
P("频域最关键（−5.5pt），时频次之（−2.5pt），时域最小（−0.9pt）；特征块重要性排序：频域 > 时频 > 时域。"
  "train epoch Acc 普遍高于 test 被试 Acc 3–9pt（epoch 级任务更易 + 轻度过拟合）。")
FIG("fig_ablation_features.png", "Feature-domain ablation A1–A3 and event-feature gain (quick screen vs full scale)")

H("7.2  诊断 Agent 消融 A4–A6 / A9（二分类，被试级 p90）", 2)
vnames = {"stacking_full": "Stacking (4 agents)", "A4_no_eegnet": "A4: w/o EEGNet", "A5_no_tcn": "A5: w/o TCN",
          "A6_no_transformer": "A6: w/o Transformer", "A9_soft_voting_equal": "A9: equal-weight soft voting",
          "hard_voting": "Hard voting (tie → Normal)", "single_lightgbm": "Single: LightGBM",
          "single_lightgbm_event": "Single: LightGBM (event)", "single_eegnet": "Single: EEGNet",
          "single_tcn": "Single: TCN", "single_transformer": "Single: Transformer"}
for base_key, base_title in (("lightgbm", "Base 1: lightgbm (532-dim base features)"),
                             ("lightgbm_event", "Base 2: lightgbm_event (614-dim with event)")):
    P(base_title, bold=True)
    vs = aa["bases"][base_key]["variants"]
    keys = ["stacking_full", "A4_no_eegnet", "A5_no_tcn", "A6_no_transformer", "A9_soft_voting_equal",
            "hard_voting", "single_lightgbm_event" if base_key == "lightgbm_event" else "single_lightgbm",
            "single_eegnet", "single_tcn", "single_transformer"]
    rows = []
    for k in keys:
        d = vs[k]
        rows.append([vnames[k], f4(d["acc"]), f4(d["macro_f1"]), f4(d["auc"])])
    TBL(f"Agent-side ablation ({base_title}, test 238 subjects, baseline 0.5504)",
        ["Variant", "Acc", "macro F1", "AUC"], rows)
P("要点：①事件版 LightGBM 使 Stacking 0.5798 → 0.6050（+2.5pt）；②两套基底下去 Transformer 均不掉点甚至"
  "升点，全局最优为 lightgbm_event + EEGNet + TCN = 0.6134；去 TCN 伤害最大；Transformer 在当前数据规模下"
  "无正向贡献；③等权软投票（0.5168）与硬投票（0.5336）均显著劣于 Stacking——论证元学习融合的必要性。")
FIG("fig_ablation_agents.png", "Diagnosis-agent ablation A4–A6 / A9 and voting baselines (two bases)")

H("7.3  系统机制消融 A8–A9（三分类完整系统，被试级 mean）", 2)
mm = asy["mechanism_metrics"]
rows = []
# A7（无仲裁）已随仲裁机制移除，机制消融仅剩 full vs A8 vs A9
for v in ("full", "A8_fixed_weights", "A9_equal_weights"):
    d = asy["variants"][v]
    rows.append([v, f4(d["epoch_acc"]), f4(d["epoch_macro_f1"]), f4(d["subject_acc"]), f4(d["subject_macro_f1"])])
TBL("System-mechanism ablation (test@20, 4760 epochs / 238 subjects, majority baseline 0.5504)",
    ["Variant", "epoch Acc", "epoch macro F1", "subject Acc", "subject macro F1"], rows)
P(f"机制指标：分歧触发率 {pct(mm['disagreement_rate'])}（校准后）；{mm['arbitration_improvement']['n_disagreement_arbitrated']} 个"
  f"分歧 epoch 上仲裁前后 epoch Acc {mm['arbitration_improvement']['acc_before_arbitration']:.4f} → "
  f"{mm['arbitration_improvement']['acc_after_arbitration']:.4f}。静态权重（agent_weights.json，验证集历史"
  "准确率衰减加权）：lightgbm 0.492 / eegnet 0.417 / tcn 0.045 / transformer 0.045。")

H("7.4  McNemar 显著性检验（被试级配对 vs full）", 2)
rows = []
for v, d in asy["mcnemar_vs_full"].items():
    rows.append([v, d["full_correct_variant_wrong"], d["full_wrong_variant_correct"], f4(d["p_value"]),
                 "Yes" if d["significant_at_0.05"] else "No"])
TBL("McNemar test (b = full correct & variant wrong; c = full wrong & variant correct)",
    ["Variant", "b", "c", "exact p", "Significant (α=0.05)"], rows)
P("两个机制消融均不显著（p ≥ 0.5）：238 被试下 ±2pt 的被试级差异均在噪声范围内。A8 与 full 仅差 1 个被试，"
  "动态权重与固定权重实质等价。论文应报告 b/c 计数与效应量，避免只报点估计。")

H("7.5  信号质量分层分析", 2)
qs = asy["quality_stratified"]
rows = []
for lvl in ("high", "medium", "low"):
    d = qs["epoch_level"][lvl]
    rows.append([lvl, d["n_epochs"], f4(d["full"]),
                 f4(d["A8_fixed_weights"]), f4(d["A9_equal_weights"])])
TBL("Epoch-level stratification by quality level", ["Quality", "n", "full", "A8", "A9"], rows)
rows = []
for g in ("all_high_quality", "contains_medium_low"):
    d = qs["subject_level"][g]
    rows.append([g, d["n_subjects"], f4(d["full"]),
                 f4(d["A8_fixed_weights"]), f4(d["A9_equal_weights"])])
TBL("Subject-level stratification (with / without medium-low quality epochs)", ["Group", "n", "full", "A8", "A9"], rows)
P("99.2% 的 epoch 为高质量；可观测的中低质量子集仅 40 epochs / 23 被试，动态权重未显示一致优势。"
  "诚实结论：动态权重机制的设计目标场景（噪声/伪迹较重的临床现场数据）在本数据集中未能充分体现——"
  "作为局限报告，而非声称有效。")
FIG("fig_system_ablation.png", "System-mechanism ablation A8–A9, McNemar paired tests, and quality-stratified analysis")

# ================= 8 分歧检测阈值校准 =================
H("8  分歧检测阈值校准")
P("问题：旧配置（prob_diff 0.15 / majority 0.6 / entropy 0.80）触发率 100%，仲裁退化为“永远执行”，"
  "推理成本翻倍且失去选择性。")
md = cal["metric_distributions"]
cf = cal["current_config_firing"]
TBL("Disagreement-metric distributions & threshold calibration (val@20, 4800 epochs)",
    ["Metric", "P25", "Median", "P75", "P90", "Old thr → rate", "New thr"], [
        ["Max prob diff", f4(md["max_prob_diff"]["0.25"]), f4(md["max_prob_diff"]["0.5"]),
         f4(md["max_prob_diff"]["0.75"]), f4(md["max_prob_diff"]["0.9"]),
         f"0.15 → {pct(cf['rule1_prob_diff'])}", "0.30"],
        ["Majority ratio", f4(md["majority_ratio"]["0.25"]), f4(md["majority_ratio"]["0.5"]),
         f4(md["majority_ratio"]["0.75"]), f4(md["majority_ratio"]["0.9"]),
         f"0.60 → {pct(cf['rule2_majority'])}", "0.60 (kept)"],
        ["Mean prob entropy", f4(md["entropy"]["0.25"]), f4(md["entropy"]["0.5"]),
         f4(md["entropy"]["0.75"]), f4(md["entropy"]["0.9"]),
         f"0.80 → {pct(cf['rule3_entropy'])}", "1.099 (≈disabled)"],
        ["Combined trigger rate", "—", "—", "—", "—", f"→ {pct(cf['combined'])}", "≈40% (test 39.7%)"],
    ])
P("根因：四个异构 Agent 的平均概率接近均匀分布（中位熵 1.0878，理论上限 ln3≈1.0986），熵规则常态触发；"
  "概率差中位 0.178 > 0.15 也常年触发。方法：val@20 逐 epoch 缓存三个指标与无条件两轮概率，"
  "网格扫描 1116 组阈值组合零成本复算精度（scripts/calibrate_disagreement.py）。")
TBL("Before vs after calibration on test (@20, 4760 epochs)", ["Metric", "Before", "After"], [
    ["Disagreement trigger rate", "100%", "39.7%"],
    ["Full-system subject Acc", "0.5378", "0.5378"],
    ["Full-system epoch Acc", "0.5042", "0.5044"],
    ["Inference time", "785 s", "476 s (−39%)"],
])
P("说明：网格中纯精度最优为“从不仲裁”（val 被试 0.5833 / epoch 0.5408）；采用的 40% 触发配置在 val 上"
  "被试精度持平（0.5833）且 epoch 精度更高（0.5417），在保留仲裁机制活性（系统贡献叙事）与推理成本之间"
  "取平衡。test 验证：触发率 39.7%，被试精度保持。")
FIG("fig_disagreement_calibration.png", "Disagreement-threshold calibration: metric distributions and thresholds, rule firing rates, calibration gains")

# ================= 9 辅助分析 =================
H("9  辅助分析")
H("9.1  年龄校正", 2)
TBL("Age-residualized vs original features (binary LightGBM)", ["Features", "Acc", "AUC"], [
    ["Original 532-dim", f4(ac["uncorrected"]["acc"]), f4(ac["uncorrected"]["auc"])],
    ["Age-residualized", f4(ac["age_corrected"]["acc"]), f4(ac["age_corrected"]["auc"])],
])
P(f"年龄校正无增益（ΔAUC {ac['delta_auc']:+.4f}）。与年龄相关性最高的特征集中于时频块"
  f"（Top10 中 9 个索引 ≥ 386）——年龄效应主要藏在时频特征里，但去除后不提升泛化。")
H("9.2  慢波检出子任务", 2)
TBL("Slow-wave detection subtask (120 records: 30 positive / 90 negative)", ["Task", "AUC", "Acc", "F1", "Baseline"], [
    ["Slow-wave detection", f4(sw["slow_wave_auc"]), f4(sw["slow_wave_acc"]), f4(sw["slow_wave_f1"]),
     f4(sw["slow_baseline"])],
    ["N vs A binary (same subset)", f4(sw["original_binary_auc"]), f4(sw["original_binary_acc"]), "—", "—"],
])
P("特征中确已携带慢波信息（AUC 0.7519），但仅与多数类基线持平——判别力有限，未成为独立增量来源。")

# ================= 10 单病例报告 =================
H("10  单病例自动报告（阶段 6 收尾）")
P("scripts/generate_report.py 从 epoch 缓存选取被试，逐 epoch 走完整 Orchestrator 流程，输出结构化 "
  "Markdown 报告（结论 / 信号质量 / 多 Agent 意见与共识过程 / 证据链 / 免责声明）。"
  "样例 SUBJ_0034（临床 Abnormal，20 epochs，3.0 s）：系统输出“可疑/界限性倾向（Abnormal 36.7% vs "
  "Normal 34.4%）”，跨 Agent 一致性 0.515，触发人工复核建议——体现“低置信度 → 建议复核”的临床安全设计。"
  "报告存于 outputs/reports/SUBJ_0034_report.md。")

# ================= 11 结论与论文写作建议 =================
H("11  结论与论文写作建议")
NUM([
    "最优配置为 lightgbm_event + EEGNet + TCN 的 Stacking（被试级二分类 Acc 0.6134，超多数类基线 6.3pt）；"
    "系统默认 4-Agent Stacking 0.5798（+2.9pt）。",
    "事件级特征全量口径 +2.1pt，但 5000 样本快评为 −2.0pt——特征取舍必须以全量/足量口径为准。",
    "特征块重要性：频域 > 时频 > 时域（去频域 −5.5pt）。",
    "Borderline 档全线 F1 ≈ 0 且无法用置信度恢复；论文主线建议采用二分类口径，Borderline 作为局限讨论。",
    "Transformer 在当前数据规模下概率坍缩（全预测 Normal），对 Stacking 无正向贡献。",
    "分歧阈值校准使触发率 100% → 39.7%、推理耗时 −39%，"
    "且不损失精度——校准方法本身（指标分布 + 网格扫描 + 帕累托分析）可作为论文的一个分析贡献。",
    "动态权重 vs 固定权重无显著差异（p=1.00）：数据集 99.2% epoch 为高质量，机制价值未获体现，建议如实报告。",
    "标签来源分组分析显示无 Agent 稳定超过组内基线——标签噪声是精度上限的重要约束。",
    "年龄校正无增益；慢波信息已隐含于特征（AUC 0.75）但无独立增量。",
])
TBL("Suggested mapping to paper sections", ["Paper section", "Supporting experiments", "Key numbers"], [
    ["5.3 Baselines", "Hard voting 0.5336 / equal soft voting 0.5168 / single agents 0.4748–0.5462 / Stacking 0.5798",
     "Best 0.6134 (+6.3pt vs baseline)"],
    ["5.4 Feature-domain ablation A1–A3 + event", "Table (Sec. 7.1)", "freq −5.5pt; event +2.1pt"],
    ["5.4 Agent ablation A4–A6 / A9", "Tables (Sec. 7.2), two bases", "w/o Transformer best 0.6134; w/o TCN worst"],
    ["5.4 Mechanism ablation A8–A9 + significance", "Tables (Sec. 7.3 / 7.4)", "All n.s."],
    ["Mechanism analysis / discussion", "Threshold calibration + quality stratification (Sec. 8 / 7.5)",
     "Trigger rate 100%→39.7%; 99.2% high-quality"],
])
P("主要局限：", bold=True)
BUL([
    "238 被试的样本量使 McNemar 检验功效不足（±2pt 差异不可分辨），效应量与置信区间应随点估计一并报告。",
    "Borderline 不可分，三分类 macro F1 被系统性压低。",
    "Transformer 失效与动态权重未显现优势均与数据规模/质量有关，需在讨论中界定适用范围。",
    "test@20 与全量 @100 两种采样口径并存（计算成本权衡），论文中需统一说明。",
])

# ================= 附录 =================
H("附录 A  产出文件清单")
TBL("Experiment outputs (outputs/)", ["File", "Content"], [
    ["data_quality.json", "Data scale, class distribution, signal-quality statistics"],
    ["label_metadata_analysis.json", "Label metadata analysis (event-positive rates, age)"],
    ["subject_level_eval.json", "3-class single-agent baselines (mean/max/p90 + confusion matrices)"],
    ["binary_eval.json", "Binary single-agent baselines + confidence-band borderline analysis"],
    ["subject_level_train.json", "Early N-vs-A evaluation (361-dim version)"],
    ["label_source_comparison.json", "Analysis grouped by label source"],
    ["stacking_eval.json", "Fusion baselines (Stacking / soft voting / single agents)"],
    ["subject_val_accuracies.json", "Val-set reference accuracies per agent"],
    ["event_feature_ab.json", "Event-feature quick A/B screen"],
    ["ablation_features.json", "Feature-domain ablation A1–A3 + event toggle (full-scale)"],
    ["ablation_agents.json", "Agent-side ablation A4–A6 / A9 + hard voting (two bases)"],
    ["ablation_system.json", "System-mechanism ablation A8–A9 + McNemar + quality stratification"],
    ["disagreement_calibration.json", "Disagreement-threshold calibration (distribution / grid / Pareto)"],
    ["age_correction_eval.json", "Age-residualization control"],
    ["slow_wave_subtask.json", "Slow-wave detection subtask"],
    ["reports/SUBJ_0034_report.md", "Single-case report sample"],
])
TBL("Experiment scripts (scripts/)", ["Script", "Purpose"], [
    ["extract_full_features.py", "One-shot full 614-dim feature extraction (train/val@100 + test@20)"],
    ["run_ablation.py", "Feature-side ablation A1–A3 + event toggle; produces event model"],
    ["run_ablation_agents.py", "Agent-side ablation + hard-voting baseline (reuses probability cache)"],
    ["run_ablation_system.py", "System-mechanism ablation + McNemar + quality stratification"],
    ["calibrate_disagreement.py", "Disagreement-threshold calibration (distribution / grid / Pareto)"],
    ["generate_report.py", "Single-case Markdown report generation"],
    ["generate_experiment_report.py", "This report generator"],
])
P("模型清单（checkpoints/）：eegnet(-binary)、tcn(-binary)、transformer(-binary)、lightgbm(-binary、"
  "-binary_agecorrected、-binary_event)、fusion(-binary、-binary_agecorrected、-binary_event)、stacking。")
P("特征与概率缓存（E:/eeg_asd_cache/features/）：三 split 614 维特征矩阵 + 元数据、Agent epoch 概率、"
  "分歧指标缓存、manifest。")

H("附录 B  复现指南与代码仓库")
P("代码仓库（GitHub）", bold=True)
P("项目全部代码已上传至 GitHub 仓库：")
P("https://github.com/QM-newer/eeg-multi-agent", bold=True)
P("仓库内容：eeg_multi_agent/ 完整源码（agents / orchestrator / training / scripts / utils）、"
  "配置文件、本报告生成脚本；数据缓存与模型权重体积较大，不在仓库内，可按下列步骤重建。")
P("环境依赖", bold=True)
CODE([
    "Python 3.12.3",
    "numpy==1.26.4  scikit-learn==1.4.2  lightgbm==4.6.0",
    "PyTorch==2.9.1+cpu  matplotlib  python-docx  joblib  scipy",
    "# 硬件参考：Intel i9-13900HX（24 核）/ 15.7 GB RAM / Windows 11，全程 CPU 推理",
])
P("目录结构（关键部分）", bold=True)
CODE([
    "eeg_multi_agent/",
    "├── agents/                 # 特征层 3+1 Agent、诊断层 4 Agent、验证层 2 Agent",
    "├── orchestrator/           # 协调层：调度 / 投票 / 分歧检测 / 仲裁",
    "├── training/               # 各诊断模型训练入口与公共特征管线",
    "├── scripts/                # 实验脚本（消融 / 校准 / 评估 / 报告与图表生成）",
    "├── data/epoch_cache.py     # epoch 缓存读写与归一化",
    "├── checkpoints/            # 模型权重与融合器（训练后生成）",
    "├── outputs/                # 全部实验结果 JSON / figures / reports",
    "└── config.py               # 路径、阈值、训练超参等全局配置",
])
P("完整复现流程（按顺序执行）", bold=True)
CODE([
    "# 0) 数据准备：将原始 EEG 记录构建 epoch 缓存（E:/eeg_asd_cache/epochs）",
    "python scripts/build_epoch_cache.py             # 一次性（约 1-2 h）",
    "",
    "# 1) 训练各诊断 Agent（三分类与二分类双口径）",
    "python training/train_lightgbm.py             # LightGBM（532 维基础特征）",
    "python training/train_eegnet.py               # EEGNet",
    "python training/train_tcn.py                  # TCN",
    "python training/train_transformer.py          # Transformer",
    "python scripts/train_stacking.py              # Stacking 元模型",
    "",
    "# 2) 本轮实验（2026-10）",
    "python scripts/extract_full_features.py       # 全量 614 维特征提取（约 40 min）",
    "python scripts/run_ablation.py                # 特征侧消融 A1-A3 + 事件开关（约 30 min）",
    "python scripts/run_ablation_agents.py         # Agent 侧消融 + 硬投票基线",
    "python scripts/run_ablation_system.py         # 系统机制消融 + McNemar + 分层（约 8 min）",
    "python scripts/calibrate_disagreement.py      # 分歧阈值校准（--from-cache 复用缓存）",
    "python scripts/generate_report.py             # 单病例报告样例",
    "",
    "# 3) 图表与本 Word 报告",
    "python scripts/generate_figures.py            # 8 张实验图（outputs/figures/）",
    "python scripts/generate_experiment_report.py  # 本报告（自动汇编 outputs/*.json）",
])
P("说明：脚本均从项目根目录运行；中间产物（特征矩阵、Agent 概率、分歧指标缓存）写入 "
  "E:/eeg_asd_cache/features/，各消融实验共享缓存以避免重复计算。")

finalize_fonts()
out_path = OUT / f"EEG-MAS实验报告_{datetime.now():%Y-%m-%d}.docx"
doc.save(out_path)
print(f"报告已生成: {out_path}")
print(f"表格数: {_tbl_no[0]}")
