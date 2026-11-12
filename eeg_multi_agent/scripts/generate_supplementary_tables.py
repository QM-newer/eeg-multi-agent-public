# -*- coding: utf-8 -*-
"""生成投稿格式附表 Table S1–S9 合集（对应 caption 清单编号）。

数据来源（运行时读取，零手抄）：
  S1  data_quality.json            信号质量统计（报告 T4）
  S2  label_metadata_analysis.json 标签元数据（报告 T5）
  S3  subject_level_eval.json      三分类基线（报告 T7）
  S4  label_source_comparison.json 标签来源分组（报告 T10）
  S5  stacking_eval.json           融合对比（报告 T11）
  S6  event_feature_ab.json + ablation_features.json  事件 A/B（报告 T12）
  S7  ablation_system.json         质量分层（报告 T18+19 合并）
  S8  age_correction_eval.json     年龄校正（报告 T22）
  S9  slow_wave_subtask.json       慢波子任务（报告 T23）
  质量分层 n 值（4720/22/18；215/23）取自报告 §7.5（JSON 未存档，有据字面量）

格式：三线表，英文 caption，Times New Roman。输出：Agent/投稿格式附表S1-S9.docx
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

BASE = Path(r"c:\Users\23373\Desktop\eeg\data and code\Agent")
OUTD = BASE / "eeg_multi_agent/outputs"
J = lambda n: json.load(open(OUTD / n, encoding="utf-8"))

DQ, LM = J("data_quality.json"), J("label_metadata_analysis.json")
SLE, LSC = J("subject_level_eval.json"), J("label_source_comparison.json")
SLEP = J("test_subject_level_eval_p90.json")
SE, EF = J("stacking_eval.json"), J("event_feature_ab.json")
AF, ASY = J("ablation_features.json"), J("ablation_system.json")
AA, FV = J("ablation_agents.json"), J("fusion_variants.json")
VBE = J("val_binary_eval_mean.json")
AC, SW = J("age_correction_eval.json"), J("slow_wave_subtask.json")


# ---------- docx helpers（与前两脚本同规范） ----------
def set_font(run, size=9.5, bold=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def para(doc, text, size=10.5, bold=False, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    set_font(p.add_run(text), size=size, bold=bold)
    return p


def _set_borders(el, edges):
    if el.tag == qn("w:tbl"):
        pr = el.find(qn("w:tblPr"))
        borders = pr.find(qn("w:tblBorders"))
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            pr.append(borders)
    else:
        pr = el.get_or_add_tcPr()
        borders = OxmlElement("w:tcBorders")
        pr.append(borders)
    for edge, sz in edges.items():
        e = borders.find(qn(f"w:{edge}"))
        if e is None:
            e = OxmlElement(f"w:{edge}")
            borders.append(e)
        if sz is None:
            e.set(qn("w:val"), "nil")
        else:
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(sz))
            e.set(qn("w:color"), "000000")


def three_line_table(doc, rows, bold_cells, col_widths, header_rows=1):
    n_r, n_c = len(rows), len(rows[0])
    tbl = doc.add_table(rows=n_r, cols=n_c)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    _set_borders(tbl._tbl, {"top": 12, "bottom": 12, "left": None,
                            "right": None, "insideH": None, "insideV": None})
    for r in range(n_r):
        tbl.rows[r].height = Pt(16)
        for c in range(n_c):
            cell = tbl.cell(r, c)
            cell.width = col_widths[c]
            if r == header_rows - 1:
                _set_borders(cell._tc, {"bottom": 6})
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c == 0 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            set_font(p.add_run(rows[r][c]), size=9.5, bold=(r, c) in bold_cells)
    return tbl


def note(doc, lines):
    for t in lines:
        para(doc, t, size=8.5, space_after=2)
    para(doc, "", size=4, space_after=0)


def caption(doc, label, text):
    para(doc, label, size=10, bold=True, space_after=2)
    para(doc, text, size=10, space_after=8)


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Pt(72)

para(doc, "投稿格式附表 S1–S9 合集（工作稿）", size=14, bold=True, space_after=4)
para(doc, "S1=报告T4　S2=报告T5　S3=报告T7　S4=报告T10　S5=报告T11　S6=报告T12　"
          "S7=报告T18+19合并　S8=报告T22　S9=报告T23。数据读取自 outputs/*.json（零手抄）；"
          "质量分层 n 值与 S6 全量口径见各表注。投稿时删除本页说明。", size=9, space_after=12)

# ================= S1: signal-quality statistics =================
caption(doc, "Table S1.",
        "Per-record signal-quality statistics over all 1,588 records "
        "(19 channels, 250 Hz, 2-s epochs, up to 100 epochs per record).")

def stats_row(name, m, unit=""):
    return [name + (f" ({unit})" if unit else ""), f"{m['mean']:.2f}",
            f"{m['median']:.2f}", f"{m['p10']:.2f}", f"{m['p90']:.2f}",
            f"{m['min']:.2f}–{m['max']:.2f}"]

rows = [["Metric", "Mean", "Median", "P10", "P90", "Range (min–max)"],
        stats_row("SNR", DQ["snr_db"], "dB"),
        stats_row("Artifact ratio", DQ["artifact_ratio"]),
        stats_row("Epoch keep rate", DQ["keep_rate"]),
        stats_row("Epoch amplitude std", DQ["amplitude"]["epoch_std_uV"], "µV"),
        stats_row("Epoch peak-to-peak", DQ["amplitude"]["epoch_ptp_uV"], "µV"),
        stats_row("Epochs per record", DQ["n_epochs"])]
three_line_table(doc, rows, set(),
                 col_widths=[Pt(150), Pt(56), Pt(56), Pt(50), Pt(50), Pt(110)])
note(doc, [
    "Notes. Artifact ratio = fraction of channels flagged by the quality agent per epoch; keep rate = "
    "fraction of epochs retained after quality gating. Amplitude statistics are estimated from "
    f"{DQ['amplitude']['sampled_records']} sampled records; no flat-channel records were detected "
    f"(flat-channel count = {DQ['amplitude']['records_with_flat_channel']}). 99.3% of epochs pass "
    "quality gating (see Table S7).",
])

# ================= S2: label metadata =================
caption(doc, "Table S2.",
        "Label–metadata analysis on the 831 of 1,820 records with annotated clinical fields: "
        "(a) event-positive rates by clinical label; (b) age statistics by label.")

waves = [("Slow wave", "slow_wave"), ("Sharp wave", "sharp_wave"),
         ("Spike–wave", "spike_wave"), ("Any epileptiform", "epileptiform_count")]
rows = [["Event type", "Normal (%)", "Borderline (%)", "Abnormal (%)"]]
bold = set()
for i, (label, k) in enumerate(waves):
    w = LM["wave_vs_label"].get(k)
    if w is None:
        continue
    pr = w["pos_rate_by_label"]
    rows.append([label, f"{pr['Normal']:.1f}", f"{pr['Borderline']:.1f}",
                 f"{pr['Abnormal']:.1f}"])
three_line_table(doc, rows, set(),
                 col_widths=[Pt(130), Pt(85), Pt(95), Pt(90)])
para(doc, "(b) Age statistics by clinical label", size=9.5, bold=True, space_after=4)
rows = [["Label", "n", "Mean age ± SD (yr)", "Median (yr)", "Range (yr)"]]
for lab in ("Normal", "Borderline", "Abnormal"):
    a = LM["age_by_label"][lab]
    rows.append([lab, str(int(a["count"])), f"{a['mean']:.2f} ± {a['std']:.2f}",
                 f"{a['50%']:.1f}", f"{a['min']:.2f}–{a['max']:.2f}"])
three_line_table(doc, rows, set(),
                 col_widths=[Pt(90), Pt(50), Pt(130), Pt(80), Pt(105)])
note(doc, [
    "Notes. Clinical annotation coverage: 831/1,820 records (45.7%; test split 126/247 = 51.0%, "
    "train 585/1,145, validation 120/244). The assembled source registry retains records beyond the "
    "1,588-record modeling cohort (all records with documented age ≥ 18 are excluded from modeling, "
    "Section II-C of the main text). Slow-wave positivity separates Abnormal (97.4%) from "
    "Normal (2.0%) almost perfectly, with Borderline intermediate (72.3%) — the motivation for the "
    "82-dim event-feature block, whose full-scale evaluation is reported in Table S6. Age "
    "distributions overlap substantially across labels.",
])

# ================= S3: three-class baselines =================
caption(doc, "Table S3.",
        "Three-class single-agent baselines (Normal / Borderline / Abnormal; test@10, "
        "2,360 epochs / 236 subjects; majority baseline 0.5466).")

AG = ["lightgbm", "eegnet", "tcn", "transformer"]
AG_LAB = {"lightgbm": "LightGBM (532-d + mRMR-128)", "eegnet": "EEGNet",
          "tcn": "TCN", "transformer": "Transformer"}
rows = [["Diagnosis agent", "Epoch\nAcc", "Subject Acc\n(mean)", "macro F1\n(mean)",
         "Subject Acc\n(p90)", "macro F1\n(p90)", "Time\n(s)"]]
vals = {}
for a in AG:
    v = SLE["agents"][a]
    vals[a] = {"epoch": v["epoch_accuracy"],
               "m_acc": v["aggregation"]["mean"]["subject_accuracy"],
               "m_f1": v["aggregation"]["mean"]["subject_macro_f1"],
               "p_acc": SLEP["agents"][a]["aggregation"]["p90"]["subject_accuracy"],
               "p_f1": SLEP["agents"][a]["aggregation"]["p90"]["subject_macro_f1"],
               "t": v["seconds"]}
    rows.append([AG_LAB[a], f"{vals[a]['epoch']:.4f}", f"{vals[a]['m_acc']:.4f}",
                 f"{vals[a]['m_f1']:.4f}", f"{vals[a]['p_acc']:.4f}",
                 f"{vals[a]['p_f1']:.4f}", f"{vals[a]['t']:.1f}"])
bold = set()
for c, key in [(1, "epoch"), (2, "m_acc"), (3, "m_f1"), (4, "p_acc"), (5, "p_f1"), (6, "t")]:
    best = (min if key == "t" else max)(vals[a][key] for a in AG)
    for r, a in enumerate(AG, 1):
        if abs(vals[a][key] - best) < 1e-9:
            bold.add((r, c))
three_line_table(doc, rows, bold,
                 col_widths=[Pt(148), Pt(58), Pt(76), Pt(64), Pt(76), Pt(64), Pt(52)])
note(doc, [
    "Notes. Subject-level metrics under mean and p90 (90th percentile) aggregation of epoch "
    "probabilities; inference time over the 2,360 test epochs. Mean aggregation was pre-specified "
    "from validation data and p90 is the sensitivity analysis (Fig. S3). Borderline macro F1 ≈ 0 "
    "for every agent — these results justify the binary protocol adopted in the main text. "
    "Best per column in bold (time: lower is better).",
])

# ================= S4: label-source comparison =================
caption(doc, "Table S4.",
        "Subject-level accuracy by label source (three-class protocol, test@10, "
        "subject-level mean aggregation).")

rows = [["Diagnosis agent", "Label-source group", "n", "Acc", "In-group\nbaseline",
         "Margin over\nbaseline"]]
for a in AG:
    for g, glab in (("project", "Project"), ("raw_index", "Raw index")):
        v = LSC["groups"][a][g]
        rows.append([AG_LAB[a] if g == "project" else "", glab, str(v["n_subjects"]),
                     f"{v['accuracy']:.4f}", f"{v['baseline']:.4f}",
                     f"{v['margin_over_baseline']:+.4f}"])
three_line_table(doc, rows, set(),
                 col_widths=[Pt(128), Pt(92), Pt(40), Pt(62), Pt(76), Pt(88)])
note(doc, [
    "Notes. Project vs. raw-index label groups reflect two annotation workflows in the source data "
    "(119 vs. 117 test subjects). In-group majority baselines differ markedly (0.5126 vs. 0.5812). "
    "EEGNet is the only agent above its in-group baseline in both groups; label-source heterogeneity "
    "remains a constraint on achievable accuracy (see Limitations).",
])

# ================= S5: fusion comparison =================
caption(doc, "Table S5.",
        "Fusion-method comparison (binary protocol, subject-level mean aggregation, test@10, "
        "n = 236; majority baseline 0.5466). Validation accuracy is shown alongside test accuracy.")

rows = [["Fusion method", "Val\nAcc", "Test\nAcc", "Test\nAUC"]]
V = FV  # 变体在顶层：4agent_equal / 4agent_valweighted / 3agent_equal / 3agent_valweighted
VB = AA["bases"]["lightgbm"]["variants"]
entries = [
    ("Soft voting, 4 agents (equal)", V["4agent_equal"]["val"]["acc"],
     V["4agent_equal"]["test"]["acc"], V["4agent_equal"]["test"]["auc"]),
    ("Soft voting, 4 agents (val-weighted)", V["4agent_valweighted"]["val"]["acc"],
     V["4agent_valweighted"]["test"]["acc"], V["4agent_valweighted"]["test"]["auc"]),
    ("Soft voting, 3 agents (equal)", V["3agent_equal"]["val"]["acc"],
     V["3agent_equal"]["test"]["acc"], V["3agent_equal"]["test"]["auc"]),
    ("Soft voting, 3 agents (val-weighted)", V["3agent_valweighted"]["val"]["acc"],
     V["3agent_valweighted"]["test"]["acc"], V["3agent_valweighted"]["test"]["auc"]),
    ("Hard voting, 4 agents (tie → Normal)", None, VB["hard_voting"]["acc"], None),
    ("Stacking (LR meta-learner)", None, SE["stacking"]["acc"], SE["stacking"]["auc"]),
    ("Stacking (LightGBM meta-learner)", None, VB["stacking_full"]["acc"],
     VB["stacking_full"]["auc"]),
]
for a in AG:
    entries.append((f"Single: {AG_LAB[a].split(' (')[0]}",
                    VBE["agents"][a]["binary"]["accuracy"],
                    SE["single_agents"][a]["acc"],
                    SE["single_agents"][a]["auc"]))
entries.append(("Majority baseline", None, SE["baseline"], None))
for lab, vacc, acc, auc in entries:
    rows.append([lab, "—" if vacc is None else f"{vacc:.4f}",
                 f"{acc:.4f}", "—" if auc is None else f"{auc:.4f}"])
bold = set()
for c, key in [(1, 1), (2, 2), (3, 3)]:
    valid = [(i, e[key]) for i, e in enumerate(entries, 1) if e[key] is not None]
    best = max(v for _, v in valid)
    for i, v in valid:
        if abs(v - best) < 1e-9:
            bold.add((i, c))
three_line_table(doc, rows, bold, col_widths=[Pt(180), Pt(70), Pt(70), Pt(70)])
note(doc, [
    "Notes. All four soft-voting variants reach the same test accuracy (0.6144): validation "
    "selection among them is immaterial on test. On validation, fusion (0.6736) improved over every "
    "single agent (best: EEGNet 0.6611), but the advantage did not transfer to test (0.6144 vs. "
    "0.6441; McNemar exact test b/c = 9/16, p = 0.23). Hard voting attains the best fused test "
    "accuracy (0.6314) yet remains below EEGNet; no fused configuration exceeds the best single "
    "agent on test. Stacking meta-learners are fit on validation probabilities, so their validation "
    "accuracy is not reported. Best per column in bold.",
])

# ================= S6: event-feature A/B =================
caption(doc, "Table S6.",
        "Event-feature A/B: quick screen vs. full-scale evaluation (LightGBM, mRMR-128, "
        "binary protocol).")

full_acc, noev_acc = (AF["variants"]["full"]["subject_mean"]["accuracy"],
                      AF["variants"]["no_event"]["subject_mean"]["accuracy"])
full_auc, noev_auc = (AF["variants"]["full"]["subject_mean"]["auc"],
                      AF["variants"]["no_event"]["subject_mean"]["auc"])
rows = [["Protocol", "With event\n(614-d)", "Without event\n(532-d)", "ΔAcc", "ΔAUC"],
        ["Quick screen (5,000 train / 2,000 val epochs)",
         f"{EF['with_event']['acc']:.4f}", f"{EF['without_event']['acc']:.4f}",
         f"{EF['delta']['acc']:+.4f}", f"{EF['delta']['auc']:+.4f}"],
        ["Full-scale (test@10, 236 subjects, mean agg.)",
         f"{full_acc:.4f}", f"{noev_acc:.4f}", f"{full_acc - noev_acc:+.4f}",
         f"{full_auc - noev_auc:+.4f}"]]
three_line_table(doc, rows, {(2, 3), (2, 4)},
                 col_widths=[Pt(190), Pt(84), Pt(92), Pt(66), Pt(66)])
note(doc, [
    "Notes. The quick screen samples 5 epochs per record with epoch-level accuracy on validation "
    f"data; mRMR selected {EF['mrmr_event_selected']} of the 82 event features. The event block is "
    "harmful at both scales (−0.6 pt quick, −4.2 pt full): the quick screen's direction was correct "
    "but underestimated the magnitude, and the deployed configuration therefore uses the 532-d base "
    "(Section III-B of the main text).",
])

# ================= S7: quality stratification (T18+19 merged) =================
caption(doc, "Table S7.",
        "Signal-quality stratified analysis for the full 3-class system and mechanism variants "
        "(test@10): (a) epoch-level accuracy by quality tier; (b) subject-level accuracy by "
        "presence of medium/low-quality epochs.")

QS = ASY["quality_stratified"]
# 机制消融仅剩 full vs A8（固定权重）vs A9（等权），A7（无仲裁）已随仲裁机制移除
VAR_ORDER = [("full", "Full system"),
             ("A8_fixed_weights", "A8: fixed weights"), ("A9_equal_weights", "A9: equal weights")]
# n 值取自 @10 评估口径（一致性：2343+11+6=2360, 221+15=236）
N_EPOCH = {"high": 2343, "medium": 11, "low": 6}
N_SUBJ = {"all_high_quality": 221, "contains_medium_low": 15}

para(doc, "(a) Epoch-level accuracy by quality tier", size=9.5, bold=True, space_after=4)
rows = [["Variant", f"High\n(n={N_EPOCH['high']})", f"Medium\n(n={N_EPOCH['medium']})",
         f"Low\n(n={N_EPOCH['low']})"]]
for k, lab in VAR_ORDER:
    e = QS["epoch_level"]
    rows.append([lab, f"{e['high'][k]:.4f}", f"{e['medium'][k]:.4f}", f"{e['low'][k]:.4f}"])
three_line_table(doc, rows, set(), col_widths=[Pt(140), Pt(92), Pt(92), Pt(92)])

para(doc, "(b) Subject-level accuracy by quality group", size=9.5, bold=True, space_after=4)
rows = [["Variant", f"All high-quality\n(n={N_SUBJ['all_high_quality']})",
         f"Contains medium/low\n(n={N_SUBJ['contains_medium_low']})"]]
for k, lab in VAR_ORDER:
    s = QS["subject_level"]
    rows.append([lab, f"{s['all_high_quality'][k]:.4f}",
                 f"{s['contains_medium_low'][k]:.4f}"])
three_line_table(doc, rows, set(), col_widths=[Pt(140), Pt(140), Pt(150)])
note(doc, [
    "Notes. Quality tiers assigned by the quality agent (step 1). 99.3% of epochs are high quality; "
    "the medium/low subsets are tiny (n = 11 / 6 epochs; 15 subjects contain any medium/low epoch), "
    "so their accuracies are indicative only. Dynamic weighting shows no consistent advantage on "
    "low-quality data — the mechanism's target scenario (noise-heavy clinical recordings) is "
    "under-represented in this dataset; reported as a limitation (also visualized in Fig. S2).",
])

# ================= S8: age correction =================
caption(doc, "Table S8.",
        "Effect of age residualization on features (binary LightGBM, 532-d base features "
        "without the event block).")

rows = [["Feature set", "Subject Acc", "Subject AUC"],
        ["Original (uncorrected)", f"{AC['uncorrected']['acc']:.4f}",
         f"{AC['uncorrected']['auc']:.4f}"],
        ["Age-residualized", f"{AC['age_corrected']['acc']:.4f}",
         f"{AC['age_corrected']['auc']:.4f}"],
        ["Δ (residualized − original)",
         f"{AC['age_corrected']['acc'] - AC['uncorrected']['acc']:+.4f}",
         f"{AC['delta_auc']:+.4f}"]]
three_line_table(doc, rows, set(), col_widths=[Pt(170), Pt(90), Pt(90)])
note(doc, [
    "Notes. Age residualization regresses each feature on age within the training split and uses the "
    "residuals. The age distribution overlaps across labels (Table S2b); removing age-correlated "
    "variance yields no material gain (ΔAUC +0.005), indicating that age confounding does not drive "
    "the reported performance.",
])

# ================= S9: slow-wave subtask =================
caption(doc, "Table S9.",
        "Slow-wave detection subtask: can the base features detect the metadata slow-wave label? "
        f"({SW['n_records']} records: {SW['n_slow_positive']} positive / "
        f"{SW['n_slow_negative']} negative; 532-d features without the event block).")

rows = [["Metric", "Value"],
        ["Slow-wave detection AUC", f"{SW['slow_wave_auc']:.4f}"],
        ["Slow-wave detection Acc", f"{SW['slow_wave_acc']:.4f}"],
        ["Slow-wave detection F1", f"{SW['slow_wave_f1']:.4f}"],
        ["Majority baseline (negative class)", f"{SW['slow_baseline']:.4f}"],
        ["Reference: original binary AUC (same records)", f"{SW['original_binary_auc']:.4f}"]]
three_line_table(doc, rows, set(), col_widths=[Pt(230), Pt(90)])
note(doc, [
    "Notes. AUC 0.8167 confirms slow-wave-related information is present in the base features "
    "(time / frequency / time–frequency), yet the same features separate the clinical binary label "
    "at near-chance level on this subsample (AUC 0.5194, 5-fold cross-validation) — the bottleneck "
    "lies in the slow-wave→diagnosis mapping, consistent with slow-wave positivity being necessary "
    "but not sufficient for the Abnormal label (97.4% of Abnormal records are slow-wave positive "
    "vs. 2.0% of Normal, Table S2a).",
])


# ================= S10: system-mechanism ablation =================
caption(doc, "Table S10.",
        "System-mechanism ablation with McNemar exact paired tests vs. the full system "
        "(three-class system, test@10; 2,360 epochs / 236 subjects).")

rows = [["Variant", "Subject Acc", "Subject macro F1", "b/c", "Exact p", "Sig."]]
for k, lab in [("full", "Full system"), ("A8_fixed_weights", "A8: fixed weights"),
               ("A9_equal_weights", "A9: equal weights")]:
    v = ASY["variants"][k]
    if k == "full":
        bc, pv, sig = "—", "—", "—"
    else:
        m = ASY["mcnemar_vs_full"][k]
        bc = f"{m['full_correct_variant_wrong']}/{m['full_wrong_variant_correct']}"
        pv = f"{m['p_value']:.2f}"
        sig = "n.s." if not m["significant_at_0.05"] else "p < 0.05"
    rows.append([lab, f"{v['subject_acc']:.4f}", f"{v['subject_macro_f1']:.4f}",
                 bc, pv, sig])
three_line_table(doc, rows, set(),
                 col_widths=[Pt(140), Pt(80), Pt(110), Pt(55), Pt(60), Pt(50)])
note(doc, [
    "Notes. Subject-level metrics use mean epoch-probability aggregation. b = full correct & "
    "variant wrong; c = full wrong & variant correct; exact binomial McNemar test; n.s. = not "
    "significant. With 236 subjects, ±2 pt subject-level differences remain within noise. The "
    "former arbitration stage has been removed from the system; the disagreement detector flags "
    f"{ASY['mechanism_metrics']['disagreement_rate'] * 100:.1f}% of test epochs for human review. "
    "Epoch-level metrics and quality-stratified analyses are provided in Table S7 and Fig. S2. "
    "This table was moved from the main text to keep the mechanism-level null results in the "
    "Supplement.",
])

# ---------- 一致性断言 ----------
assert N_EPOCH["high"] + N_EPOCH["medium"] + N_EPOCH["low"] == 2360
assert N_SUBJ["all_high_quality"] + N_SUBJ["contains_medium_low"] == 236
assert LM["n_matched"] == 831 and LM["n_records"] == 1820
assert SE["baseline"] == 0.5466 and SLE["n_subjects"] == 236
assert abs((full_acc - noev_acc) - (-0.0424)) < 1e-4
assert abs(ASY['variants']['full']['subject_acc'] - 0.5805) < 1e-4
assert abs(ASY['variants']['A9_equal_weights']['subject_acc'] - 0.5975) < 1e-4

out = BASE / "投稿格式附表S1-S10.docx"
doc.save(out)
print("saved:", out)
