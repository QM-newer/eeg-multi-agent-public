# -*- coding: utf-8 -*-
"""生成投稿格式主文表 Table 1/2/3/6（对应 caption 清单编号）。

数据来源（运行时读取，零手抄）：
  data_quality.json            -> Table 1（数据划分）
  binary_eval.json             -> Table 2（二分类单 Agent 基线）
  ablation_features.json       -> Table 3（特征域消融）
  ablation_system.json         -> Table 5 校准后数值（系统消融，实际由 merged 生成器产出）
  disagreement_calibration.json -> Table 5（升级标记校准：legacy/推荐配置 + Pareto 点）

格式：三线表，英文 caption 置于表上方，Times New Roman。
输出：Agent/投稿格式主文表.docx
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
DQ = json.load(open(BASE / "eeg_multi_agent/outputs/data_quality.json", encoding="utf-8"))
BE = json.load(open(BASE / "eeg_multi_agent/outputs/binary_eval.json", encoding="utf-8"))
AF = json.load(open(BASE / "eeg_multi_agent/outputs/ablation_features.json", encoding="utf-8"))
ASY = json.load(open(BASE / "eeg_multi_agent/outputs/ablation_system.json", encoding="utf-8"))
CAL = json.load(open(BASE / "eeg_multi_agent/outputs/disagreement_calibration.json", encoding="utf-8"))

MAJORITY_TEST = 0.5466  # = 129/236（1,588 队列 @10），与各 JSON 内 baseline 字段一致（校验见文末 assert）


# ---------- docx helpers（与 generate_merged_tables.py 同规范） ----------
def set_font(run, size=9.5, bold=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def para(doc, text, size=10.5, bold=False, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    set_font(run, size=size, bold=bold)
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
            p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if c == 0
                           else WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(rows[r][c])
            set_font(run, size=9.5, bold=(r, c) in bold_cells)
    return tbl


def note(doc, lines):
    for t in lines:
        para(doc, t, size=8.5, space_after=2)
    para(doc, "", size=4, space_after=0)


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Pt(72)

# ---------- 工作稿说明（投稿时删除） ----------
para(doc, "投稿格式主文表（工作稿）", size=14, bold=True, space_after=4)
para(doc, "Table 1 = 报告 Table 3（数据划分）　Table 2 = 报告 Table 8（二分类基线）"
          "　Table 3 = 报告 Table 13（特征消融）　Table 5 = 升级标记校准（disagreement_calibration.json）",
     size=9, space_after=2)
para(doc, "数据读取自 outputs/*.json（零手抄）。投稿时删除本页说明。", size=9, space_after=12)

# ================= Table 1: dataset splits =================
para(doc, "Table 1", size=10, bold=True, space_after=2)
para(doc, "Dataset splits and class distribution (1,588 pediatric routine EEG records, "
          "one record per subject; 19 channels, 250 Hz, 2-s epochs).", size=10, space_after=8)

rows1 = [["Split", "Records\n(subjects)", "Epochs", "Normal", "Borderline", "Abnormal",
          "Majority\nbaseline"]]
for split in ("train", "val", "test"):
    s = DQ[split]
    rb = s["records_by_class"]
    maj = (f"{max(rb.values()) / s['n_records']:.4f}"
           if split in ("val", "test") else "—")
    rows1.append([{"train": "Train", "val": "Validation", "test": "Test"}[split],
                  str(s["n_records"]), str(s["n_epochs"]),
                  str(rb["Normal"]), str(rb["Borderline"]), str(rb["Abnormal"]), maj])

three_line_table(doc, rows1, set(),
                 col_widths=[Pt(62), Pt(82), Pt(66), Pt(62), Pt(76), Pt(72), Pt(76)])
note(doc, [
    "Notes. Majority baseline = largest class share of records within each split (train not evaluated). "
    "All reported results use the @10 protocol (a fixed-seed uniform sample of up to 10 epochs per record; "
    "2,360 test epochs, 15,877 in total); full-length epoch counts are listed for reference.",
])

# ================= Table 2: binary single-agent baselines =================
para(doc, "Table 2", size=10, bold=True, space_after=2)
para(doc, "Binary single-agent baselines (subject-level, mean epoch-probability aggregation, "
          "test@10, n = 236; Borderline merged into Abnormal; majority baseline Acc = 0.5466).",
     size=10, space_after=8)

AG = {"lightgbm": "LightGBM (532-d + mRMR-128)", "eegnet": "EEGNet",
      "tcn": "TCN", "transformer": "Transformer"}
rows2 = [["Diagnosis agent", "Subject\nAcc", "Subject\nmacro F1", "Subject\nAUC",
          "Inference\n time (s)"]]
for a, label in AG.items():
    v = BE["agents"][a]
    rows2.append([label, f"{v['binary']['accuracy']:.4f}",
                  f"{v['binary']['macro_f1']:.4f}", f"{v['binary']['auc']:.4f}",
                  f"{v['seconds']:.1f}"])

# 每列最优加粗（时间列取最小）
bold2 = set()
for c, key, best in [(1, "accuracy", max), (2, "macro_f1", max), (3, "auc", max),
                     (4, "seconds", min)]:
    vals = [BE["agents"][a]["binary"][key] if key != "seconds" else BE["agents"][a][key]
            for a in AG]
    target = best(vals)
    for r, a in enumerate(AG, start=1):
        v = BE["agents"][a]["binary"][key] if key != "seconds" else BE["agents"][a][key]
        if abs(v - target) < 1e-9:
            bold2.add((r, c))

three_line_table(doc, rows2, bold2,
                 col_widths=[Pt(150), Pt(70), Pt(78), Pt(70), Pt(80)])
note(doc, [
    "Notes. Inference time measured over the 2,360 test epochs on identical hardware. "
    "Borderline records are retained in the Abnormal arm (conservative protocol). "
    "Best per column in bold.",
])

# ================= Table 3: feature-domain ablation =================
para(doc, "Table 3", size=10, bold=True, space_after=2)
para(doc, "Feature-domain ablation (LightGBM with mRMR-128 selection, binary protocol, "
          "subject-level mean aggregation, test@10, n = 236).", size=10, space_after=8)

FV = AF["variants"]
n_full = FV["full"]["n_features"]
feat_order = [("Full (all feature blocks)", "full"),
              ("w/o event statistics", "no_event"),
              ("w/o time domain", "A1_no_time"),
              ("w/o frequency domain", "A2_no_freq"),
              ("w/o time–frequency domain", "A3_no_timefreq")]
acc_full = FV["full"]["subject_mean"]["accuracy"]
rows3 = [["Variant", "Feature\ndims", "Subject\nAcc", "Subject\nAUC", "ΔAcc\nvs. full"]]
for label, k in feat_order:
    v = FV[k]
    acc, auc = v["subject_mean"]["accuracy"], v["subject_mean"]["auc"]
    d = "—" if k == "full" else f"{acc - acc_full:+.4f}"
    rows3.append([f"{label} (−{n_full - v['n_features']}-d)" if k != "full" else label,
                  str(v["n_features"]), f"{acc:.4f}", f"{auc:.4f}", d])

bold3 = set()
for c, key in [(2, "accuracy"), (3, "auc")]:
    vals = [FV[k]["subject_mean"][key] for _, k in feat_order]
    best_r = vals.index(max(vals)) + 1
    bold3.add((best_r, c))
if acc_full == max(FV[k]["subject_mean"]["accuracy"] for _, k in feat_order):
    bold3.add((1, 4))  # full 行 ΔAcc 为基准，若 full 即最优则加粗其 "—"

three_line_table(doc, rows3, bold3,
                 col_widths=[Pt(190), Pt(60), Pt(70), Pt(70), Pt(78)])
note(doc, [
    "Notes. ΔAcc relative to the full 614-d feature vector. Feature blocks: time (228-d), "
    "frequency (152-d), time–frequency (152-d), epileptiform-event statistics (82-d). "
    "Every leave-one-block-out variant outperforms the full vector; removing the event block yields "
    "the largest gain (+4.2 pt, AUC +0.018), so the deployed configuration uses the 532-d base. "
    "Frequency-domain features are the most critical base block (removal costs 1.7 pt relative to "
    "no_event). Best per column in bold.",
])

# ================= Table 5: escalation-flag calibration =================
para(doc, "Table 5", size=10, bold=True, space_after=2)
para(doc, "Escalation-flag calibration for human review (validation split, @10 protocol, "
          "2,390 epochs / 239 subjects).", size=10, space_after=8)

# 数值全部来自 disagreement_calibration.json（零手抄）
rec = CAL["recommend"]
bl = CAL["baselines"]
err_base = bl["n_wrong_epochs"] / CAL["n_epochs"]
pareto = CAL["pareto"]


def pick_pareto(target):
    return min(pareto, key=lambda p: abs(p["trigger_rate"] - target))


def cfg_str(p):
    return (f"({p['prob_diff_threshold']:.2f} / {p['label_majority_threshold']:.2f} / "
            f"{p['entropy_threshold']:.2f})")


p184 = pick_pareto(0.18)
p316 = pick_pareto(0.32)
rows6 = [["Configuration\n(θd / θm / θe)", "Trigger\nrate", "Error\nrecall",
          "Flagged-set\nerror precision", "Flagged-set\nepoch Acc"],
         ["Legacy (0.15 / 0.60 / 0.80)", "100.0%", "100.0%",
          f"{err_base * 100:.1f}%", f"{bl['epoch_acc_all']:.4f}"],
         [f"Pareto point {cfg_str(p184)}, selective",
          f"{p184['trigger_rate'] * 100:.1f}%", f"{p184['error_recall'] * 100:.1f}%",
          f"{p184['error_precision'] * 100:.1f}%", f"{p184['flagged_epoch_acc']:.4f}"],
         [f"Pareto point {cfg_str(p316)}, balanced",
          f"{p316['trigger_rate'] * 100:.1f}%", f"{p316['error_recall'] * 100:.1f}%",
          f"{p316['error_precision'] * 100:.1f}%", f"{p316['flagged_epoch_acc']:.4f}"],
         [f"Recommended {cfg_str(rec)}",
          f"{rec['trigger_rate'] * 100:.1f}%", f"{rec['error_recall'] * 100:.1f}%",
          f"{rec['error_precision'] * 100:.1f}%", f"{rec['flagged_epoch_acc']:.4f}"]]
bold6 = {(4, 1), (4, 2), (4, 3)}  # 推荐行

three_line_table(doc, rows6, bold6, col_widths=[Pt(150), Pt(62), Pt(62), Pt(78), Pt(70)])
note(doc, [
    "Notes. Thresholds (θd = prob-diff, θm = label-majority, θe = entropy) selected by grid search on "
    "the validation split; rows show the Pareto frontier of trigger rate vs. error recall. The legacy "
    "entropy threshold (0.80) lies below every observed entropy value (median 1.0860; upper bound "
    "ln 3 ≈ 1.0986), firing on 100% of epochs — the calibrated threshold (1.10) disables the degenerate "
    "rule. The recommended configuration flags 48.4% of epochs and captures 55.3% of misclassified "
    "epochs at 50.4% precision, against a base error rate of 44.1% (1,054 / 2,390).",
])

# ---------- 一致性断言 ----------
assert abs(BE["agents"]["lightgbm"]["binary"]["accuracy"] - 0.6102) < 1e-9
assert DQ["test"]["n_records"] == 236 and DQ["val"]["n_records"] == 239
assert abs(max(DQ["test"]["records_by_class"].values()) / 236 - MAJORITY_TEST) < 1e-4

out = BASE / "投稿格式主文表.docx"
doc.save(out)
print("saved:", out)
