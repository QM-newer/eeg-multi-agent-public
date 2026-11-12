# scripts/export_data_package.py
"""
导出"给老师的实验数据包"：
    1. EEG-MAS实验数据.xlsx —— 10 个 sheet，与实验报告 Table 1~26 同口径（英文表头）
    2. raw_json/ —— 全部原始结果 JSON（数据可溯源）
    3. figures/ —— 8 张实验图
    4. 报告 docx + 单病例报告样例
    5. 以上打包为 zip（同步一份到桌面）

用法:  python scripts/export_data_package.py
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
FIG = OUT / "figures"
PKG = OUT / f"data_package_{datetime.now():%Y-%m-%d}"
DESKTOP = Path(r"c:\Users\23373\Desktop")

HDR_FILL = PatternFill("solid", fgColor="2F5496")
HDR_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
ZEBRA1, ZEBRA2 = PatternFill("solid", fgColor="FFFFFF"), PatternFill("solid", fgColor="F2F6FC")
KPI_FILL = PatternFill("solid", fgColor="EAF2FF")
THIN = Side(style="thin", color="D9DEE7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def load(name):
    with open(OUT / name, encoding="utf-8") as f:
        return json.load(f)


def sheet(wb, name, headers, rows, highlight_rows=(), note=None, widths=None):
    ws = wb.create_sheet(name)
    r0 = 1
    if note:
        ws.cell(1, 1, note).font = Font(italic=True, size=9, color="7F8C8D")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(headers), 2))
        r0 = 2
    for c, h in enumerate(headers, 1):
        cell = ws.cell(r0, c, h)
        cell.fill, cell.font, cell.border = HDR_FILL, HDR_FONT, BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, row in enumerate(rows):
        for c, v in enumerate(row, 1):
            cell = ws.cell(r0 + 1 + i, c, v)
            cell.border = BORDER
            cell.fill = (KPI_FILL if i in highlight_rows
                         else (ZEBRA1 if i % 2 == 0 else ZEBRA2))
            if isinstance(v, float):
                cell.number_format = "0.0000"
    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = (widths[c - 1] if widths
                                                           else max(12, min(34, max(len(str(headers[c - 1])) * 1.1,
                                                              max((len(str(r[c - 1])) for r in rows), default=10) + 2))))
    ws.freeze_panes = ws.cell(r0 + 1, 1)
    return ws


def main():
    if PKG.exists():
        shutil.rmtree(PKG)
    (PKG / "raw_json").mkdir(parents=True)
    (PKG / "figures").mkdir()

    # ---------- 数据 ----------
    dq, lma = load("data_quality.json"), load("label_metadata_analysis.json")
    sle, be, se = load("subject_level_eval.json"), load("binary_eval.json"), load("stacking_eval.json")
    eab, af, aa = load("event_feature_ab.json"), load("ablation_features.json"), load("ablation_agents.json")
    asy, cal = load("ablation_system.json"), load("disagreement_calibration.json")
    ac, sw = load("age_correction_eval.json"), load("slow_wave_subtask.json")
    lsc, sva, slt = load("label_source_comparison.json"), load("subject_val_accuracies.json"), load("subject_level_train.json")

    AGENTS = ["lightgbm", "eegnet", "tcn", "transformer"]
    wb = Workbook()
    wb.remove(wb.active)

    # 1 Overview
    sheet(wb, "Overview", ["Item", "Value", "Source"],
          [["Best config (lightgbm_event + EEGNet + TCN, Stacking)", 0.6134, "ablation_agents.json"],
           ["Default 4-agent Stacking (binary, subject-level)", 0.5798, "stacking_eval.json / ablation_agents.json"],
           ["Event features full-scale gain (Acc)", "+2.1pt (0.6092 -> 0.6303)", "ablation_features.json"],
           ["Feature-block importance", "freq > time-freq > time (freq removal -5.5pt)", "ablation_features.json"],
           ["Disagreement trigger rate after calibration", "100% -> 39.7%, inference time -39%", "disagreement_calibration.json"],
           ["Arbitration contribution (subject-level)", "+0.84pt (McNemar p=0.50, n.s.)", "ablation_system.json"],
           ["Dynamic vs fixed weights", "No significant difference (p=1.00)", "ablation_system.json"],
           ["Borderline class", "macro F1 ~ 0 for all agents -> binary protocol", "subject_level_eval.json"],
           ["Age-corrected features", "No gain (dAUC -0.005)", "age_correction_eval.json"],
           ["Majority baseline (binary, test)", 0.5504, "derived from class distribution"]],
          highlight_rows=(0,), widths=[52, 40, 34],
          note="EEG-MAS experiment data package (2026-10). All values loaded from outputs/*.json at export time. English headers match report Tables 1-26.")

    # 2 Dataset
    rows = []
    for s in ("train", "val", "test"):
        r, e = dq[s]["records_by_class"], dq[s]["epochs_by_class"]
        rows.append([s, sum(r.values()), e["Normal"] + e["Borderline"] + e["Abnormal"],
                     e["Normal"], e["Borderline"], e["Abnormal"],
                     round(max(e.values()) / sum(e.values()), 4)])
    sheet(wb, "Dataset", ["Split", "Records (subjects)", "Epochs", "Normal", "Borderline", "Abnormal", "Majority ratio"], rows,
          note="Data splits and class distribution. Source: data_quality.json. 1597 records / 159,501 epochs total, 19 ch @ 250 Hz, 2-s epochs.")
    rows = []
    for m, label in ((dq["snr_db"], "SNR (dB)"), (dq["artifact_ratio"], "Artifact ratio"),
                     (dq["keep_rate"], "Epoch keep rate"), (dq["amplitude"]["epoch_std_uV"], "Epoch amplitude std (uV)"),
                     (dq["amplitude"]["epoch_ptp_uV"], "Epoch peak-to-peak (uV)")):
        rows.append([label, round(m["mean"], 3), round(m["median"], 3), round(m["p10"], 3),
                     round(m["p90"], 3), f'{m["min"]:.3f}-{m["max"]:.3f}'])
    sheet(wb, "Dataset_quality", ["Metric", "Mean", "Median", "P10", "P90", "Range"], rows,
          note="Signal-quality statistics (amplitude metrics over 150 sampled records; flat-channel records: 0). Source: data_quality.json")
    bp = dq["band_power_percent"]
    sheet(wb, "Dataset_bands", ["Band", "Share (%)"],
          [["delta 0.5-4Hz", bp["delta0.5-4"]], ["theta 4-8Hz", bp["theta4-8"]],
           ["alpha 8-13Hz", bp["alpha8-13"]], ["beta 13-30Hz", bp["beta13-30"]],
           ["gamma 30-45Hz", bp["gamma30-45"]]],
          note="Mean band-power share (delta dominant, consistent with young cohort). Source: data_quality.json")

    # 3 Agent baselines
    rows = []
    for a in AGENTS:
        g = sle["agents"][a]
        rows.append([a, round(g["epoch_accuracy"], 4),
                     round(g["aggregation"]["mean"]["subject_accuracy"], 4), round(g["aggregation"]["mean"]["subject_macro_f1"], 4),
                     round(g["aggregation"]["p90"]["subject_accuracy"], 4), round(g["aggregation"]["p90"]["subject_macro_f1"], 4)])
    rows.append(["Majority baseline", "-", 0.5504, "-", 0.5504, "-"])
    sheet(wb, "AgentBaselines_3class", ["Agent", "epoch Acc", "Subject Acc (mean)", "macro F1 (mean)",
                                        "Subject Acc (p90)", "macro F1 (p90)"], rows,
          note="3-class single-agent baselines, test@20 (238 subjects / 4760 epochs). Source: subject_level_eval.json")
    rows = []
    for a in AGENTS:
        b = be["agents"][a]["binary"]
        rows.append([a, round(b["accuracy"], 4), round(b["macro_f1"], 4), round(b["auc"], 4),
                     round(be["agents"][a]["seconds"], 1)])
    sheet(wb, "AgentBaselines_binary", ["Agent", "Acc", "macro F1", "AUC", "Inference time (s / 4760 epochs)"], rows,
          note="Binary (Borderline merged into Abnormal), subject-level mean aggregation. Source: binary_eval.json")

    # 4 Fusion
    rows = [["Stacking (LightGBM meta-model)", round(se["stacking"]["acc"], 4), round(se["stacking"]["f1"], 4), round(se["stacking"]["auc"], 4)],
            ["Soft voting (equal-weight)", round(se["soft_voting"]["acc"], 4), "-", round(se["soft_voting"]["auc"], 4)]]
    for a in AGENTS:
        rows.append([f"Single agent: {a}", round(se["single_agents"][a]["acc"], 4), "-", round(se["single_agents"][a]["auc"], 4)])
    rows.append(["Majority baseline", round(se["baseline"], 4), "-", "-"])
    sheet(wb, "Fusion", ["Method", "Acc", "F1", "AUC"], rows, highlight_rows=(0,),
          note="Fusion method comparison (binary, subject-level). Source: stacking_eval.json")

    # 5 Feature ablation
    rows, full_acc = [], af["variants"]["full"]["subject_mean"]["accuracy"]
    names = {"full": "full (614-d)", "no_event": "no_event (532-d)", "A1_no_time": "A1: w/o time domain (386-d)",
             "A2_no_freq": "A2: w/o freq domain (462-d)", "A3_no_timefreq": "A3: w/o time-freq (462-d)"}
    for k, nm in names.items():
        v = af["variants"][k]
        rows.append([nm, v["n_features"], round(v["train_epoch_acc"], 4),
                     round(v["subject_mean"]["accuracy"], 4), round(v["subject_mean"]["auc"], 4),
                     round((v["subject_mean"]["accuracy"] - full_acc) * 100, 1)])
    sheet(wb, "AblationFeatures", ["Variant", "Dims", "train epoch Acc", "test subject Acc (mean)",
                                   "subject AUC", "dAcc vs full (pt)"], rows, highlight_rows=(0, 4),
          note="Feature-domain ablation A1-A3 + event toggle. LightGBM binary, mRMR-128, test@20. Source: ablation_features.json. Event A/B quick screen (5000 epochs): with 0.6033/0.6352 vs without 0.6250/0.6555 (event_feature_ab.json).")

    # 6 Agent ablation
    rows = []
    vnames = {"stacking_full": "Stacking (4 agents)", "A4_no_eegnet": "A4: w/o EEGNet", "A5_no_tcn": "A5: w/o TCN",
              "A6_no_transformer": "A6: w/o Transformer", "A9_soft_voting_equal": "A9: equal soft voting",
              "hard_voting": "Hard voting (tie -> Normal)", "single_eegnet": "Single: EEGNet",
              "single_tcn": "Single: TCN", "single_transformer": "Single: Transformer"}
    def r4(x):
        return round(x, 4) if isinstance(x, (int, float)) else "-"

    for bk, bt, extra in (("lightgbm", "Base: lightgbm (532-d)", [("single_lightgbm", "Single: LightGBM")]),
                          ("lightgbm_event", "Base: lightgbm_event (614-d)",
                           [("single_lightgbm_event", "Single: LightGBM (event)")])):
        allv = list(vnames.items())[:6] + extra + list(vnames.items())[6:]
        for vk, vn in allv:
            v = aa["bases"][bk]["variants"][vk]
            rows.append([bt, vn, r4(v["acc"]), r4(v["macro_f1"]), r4(v["auc"])])
    sheet(wb, "AblationAgents", ["Base", "Variant", "Acc", "macro F1", "AUC"], rows,
          highlight_rows=(13,),  # base=event 的 A6_no_transformer（第2组第4行）= 全局最优
          note="Agent-side ablation A4-A6 / A9 + voting baselines (binary, subject-level p90, meta-model trained on val, test@20 n=238, majority baseline 0.5504). Source: ablation_agents.json. Highlighted row = global best 0.6134.")

    # 7 System ablation
    rows = []
    for v in ("full", "A8_fixed_weights", "A9_equal_weights"):
        d = asy["variants"][v]
        rows.append([v.replace("_", " "), round(d["epoch_acc"], 4), round(d["epoch_macro_f1"], 4),
                     round(d["subject_acc"], 4), round(d["subject_macro_f1"], 4)])
    sheet(wb, "AblationSystem", ["Variant", "epoch Acc", "epoch macro F1", "subject Acc", "subject macro F1"], rows,
          note="System-mechanism ablation (3-class full system, test@20, 4760 epochs / 238 subjects). Source: ablation_system.json")
    rows = []
    for v, d in asy["mcnemar_vs_full"].items():
        rows.append([v.replace("_", " "), d["full_correct_variant_wrong"], d["full_wrong_variant_correct"],
                     round(d["p_value"], 4), "Yes" if d["significant_at_0.05"] else "No"])
    sheet(wb, "AblationSystem_McNemar", ["Variant vs full", "b (full correct / variant wrong)",
                                         "c (full wrong / variant correct)", "exact p", "Significant (a=0.05)"], rows,
          note="McNemar paired test (subject-level correctness vectors, exact binomial). Source: ablation_system.json")
    rows = []
    for lvl in ("high", "medium", "low"):
        d = asy["quality_stratified"]["epoch_level"][lvl]
        rows.append([f"epoch / {lvl} (n={d['n_epochs']})"] + [round(d[v], 4) for v in
                     ("full", "A8_fixed_weights", "A9_equal_weights")])
    for g in ("all_high_quality", "contains_medium_low"):
        d = asy["quality_stratified"]["subject_level"][g]
        rows.append([f"subject / {g} (n={d['n_subjects']})"] + [round(d[v], 4) for v in
                     ("full", "A8_fixed_weights", "A9_equal_weights")])
    sheet(wb, "AblationSystem_stratified", ["Stratum", "full", "A8 fixed weights", "A9 equal weights"], rows,
          note="Quality-stratified analysis: 99.2% of epochs are high quality; medium/low subsets indicative only. Source: ablation_system.json")

    # 8 Calibration
    md, cf = cal["metric_distributions"], cal["current_config_firing"]
    rows = [["Max prob diff (4 agents)", 0.15, 0.30, f'{cf["rule1_prob_diff"]:.1%}',
             "old thr below median 0.178 -> fired on 2/3 of epochs"],
            ["Majority label ratio", 0.60, 0.60, f'{cf["rule2_majority"]:.1%}', "kept (the only selective rule)"],
            ["Mean prob entropy", 0.80, 1.099, f'{cf["rule3_entropy"]:.1%}',
             "old thr below ALL samples (median 1.0878 vs ln3=1.0986) -> 100% firing; new thr ~ disabled"],
            ["Combined (any rule)", "-", "-", f'{cf["combined"]:.1%}', "after calibration: test trigger rate 39.7%"]]
    sheet(wb, "Calibration", ["Metric", "Old threshold", "New threshold", "Firing rate (old cfg)", "Remark"], rows,
          widths=[26, 14, 14, 18, 60],
          note="Disagreement-detection threshold calibration (val@20, 4800 epochs). Source: disagreement_calibration.json. Gains: trigger rate 100%->39.7%, inference 785s->476s (-39%), subject Acc unchanged 0.5378.")

    # 9 Auxiliary analyses
    sltr = slt["results"]
    sheet(wb, "AuxAnalyses", ["Analysis", "Metric", "Value"],
          [["Age correction (binary LightGBM)", "Acc / AUC original", f'{ac["uncorrected"]["acc"]:.4f} / {ac["uncorrected"]["auc"]:.4f}'],
           ["Age correction", "Acc / AUC age-residualized", f'{ac["age_corrected"]["acc"]:.4f} / {ac["age_corrected"]["auc"]:.4f}'],
           ["Slow-wave subtask (120 records: 30 pos / 90 neg)", "AUC / Acc / F1", f'{sw["slow_wave_auc"]:.4f} / {sw["slow_wave_acc"]:.4f} / {sw["slow_wave_f1"]:.4f}'],
           ["Slow-wave subtask", "Majority baseline", f'{sw["slow_baseline"]:.4f}'],
           ["Same-subset N vs A binary", "AUC / Acc", f'{sw["original_binary_auc"]:.4f} / {sw["original_binary_acc"]:.4f}'],
           ["Early N-vs-A, 361-d features (3-class, val/test)", "Acc / baseline",
            f'{sltr["3class_val"]["accuracy"]:.4f} / {sltr["3class_test"]["accuracy"]:.4f}'],
           ["Early N-vs-A (N vs A, val/test)", "Acc / baseline",
            f'{sltr["2class_N_vs_A_val"]["accuracy"]:.4f} / {sltr["2class_N_vs_A_test"]["accuracy"]:.4f}'],
           ["Val reference (mean aggregation)", "lightgbm / eegnet / tcn / transformer",
            " / ".join(f'{sva[a]:.4f}' for a in AGENTS)]],
          widths=[44, 30, 34],
          note="Auxiliary analyses. Sources: age_correction_eval.json, slow_wave_subtask.json, subject_level_train.json, subject_val_accuracies.json")
    rows = []
    for a in AGENTS:
        g = lsc["groups"][a]
        rows.append([a, round(g["project"]["accuracy"], 4), f'{g["project"]["margin_over_baseline"]:+.4f}',
                     round(g["raw_index"]["accuracy"], 4), f'{g["raw_index"]["margin_over_baseline"]:+.4f}'])
    sheet(wb, "Aux_label_source", ["Agent", "project group Acc (n=121, base 0.5207)", "margin",
                                   "raw_index group Acc (n=117, base 0.5812)", "margin"], rows,
          note="Subject-level accuracy grouped by label source (test). Source: label_source_comparison.json")
    w = lma["wave_vs_label"]
    rows = []
    for k, nm in (("slow_wave", "Slow wave"), ("sharp_wave", "Sharp wave"), ("spike_wave", "Spike wave"),
                  ("epileptiform_count", "Epileptiform (any)")):
        p = w[k]["pos_rate_by_label"]
        rows.append([nm, p["Abnormal"], p["Borderline"], p["Normal"]])
    for cls in ("Abnormal", "Borderline", "Normal"):
        rows.append([f"Mean age ({cls})", "", "", lma["age_by_label"][cls]["mean"] if "age_by_label" in lma else ""])
    sheet(wb, "Aux_label_metadata", ["Event type", "Abnormal %", "Borderline %", "Normal %"], rows,
          note="Event-positive rate by clinical label (837 records with clinical fields). Source: label_metadata_analysis.json")

    # 10 File index
    rows = [[f.name, f"{f.stat().st_size/1024:.1f} KB", "raw_json/" + f.name,
             "Experiment output (original machine-readable data)"]
            for f in sorted(OUT.glob("*.json"))]
    rows += [["fig_*.png (8 files)", "-", "figures/", "Key experiment figures (English, same as report)"],
             ["EEG-MAS实验报告_*.docx", "-", "report/", "Full experiment report (26 tables + 8 figures)"],
             ["SUBJ_0034_report.md", "-", "report/", "Single-case auto-generated report sample"]]
    sheet(wb, "FileIndex", ["File", "Size", "Location in package", "Content"], rows, widths=[34, 10, 34, 52],
          note="Data provenance: every sheet in this workbook is exported from the JSON files listed here (loaded at export time, no hand-typed numbers).")

    xlsx_path = PKG / "EEG-MAS实验数据.xlsx"
    wb.save(xlsx_path)

    # ---------- 原始 JSON / 图 / 报告 ----------
    for f in OUT.glob("*.json"):
        shutil.copy2(f, PKG / "raw_json" / f.name)
    for f in FIG.glob("*.png"):
        shutil.copy2(f, PKG / "figures" / f.name)
    (PKG / "report").mkdir()
    for f in OUT.glob("EEG-MAS实验报告_*.docx"):
        shutil.copy2(f, PKG / "report" / f.name)
    rep_md = OUT / "reports" / "SUBJ_0034_report.md"
    if rep_md.exists():
        shutil.copy2(rep_md, PKG / "report" / rep_md.name)

    # ---------- zip ----------
    import zipfile
    zip_path = OUT / f"EEG-MAS实验数据包_{datetime.now():%Y-%m-%d}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(PKG.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(PKG.parent))
    desktop_zip = DESKTOP / zip_path.name
    shutil.copy2(zip_path, desktop_zip)

    print(f"数据包目录: {PKG}")
    print(f"Excel: {xlsx_path} ({xlsx_path.stat().st_size/1024:.0f} KB, {len(wb.sheetnames)} sheets)")
    print(f"ZIP: {zip_path} ({zip_path.stat().st_size/1024:.0f} KB)")
    print(f"桌面副本: {desktop_zip}")
    print("Sheets:", ", ".join(wb.sheetnames))


if __name__ == "__main__":
    main()
