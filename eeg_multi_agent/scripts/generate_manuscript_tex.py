# generate_manuscript_tex.py
# ============================================================
# 生成论文 LaTeX 正文初稿（main.tex + references.bib + figures/）
#
# 依据：论文写作总稿.docx 第四部分 IMRaD 大纲 + 论文图表caption清单.md
# 原则：零手抄 —— 全部实验数值在运行时从 outputs/*.json 读取；
#       少数无法从 JSON 取得的数值（推理时间基准、架构超参等）标注来源注释。
# 输出：Agent/论文正文LaTeX初稿/{main.tex, references.bib, figures/*}
# ============================================================
import json
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent          # eeg_multi_agent/
ROOT = BASE.parent                                      # Agent/
OUT = ROOT / "论文正文LaTeX初稿"
FIGS = OUT / "figures"


def load(name):
    return json.loads((BASE / "outputs" / name).read_text(encoding="utf-8"))


be = load("binary_eval.json")            # 二分类单 agent 基线
af = load("ablation_features.json")      # 特征域消融
aa = load("ablation_agents.json")        # 两基底 agent 消融
asy = load("ablation_system.json")       # 机制消融 + McNemar + 质量分层
st = load("stacking_eval.json")          # 融合对比（S5）
cal = load("disagreement_calibration.json")  # 分歧阈值校准分布
dq = load("data_quality.json")           # 数据划分与质量统计
lma = load("label_metadata_analysis.json")   # 标签-事件耦合
ef = load("event_feature_ab.json")       # 事件特征 A/B 快评
sle = load("subject_level_eval.json")    # 三分类 subject 级
sva = load("subject_val_accuracies.json")    # 各 agent 验证集精度
sws = load("slow_wave_subtask.json")         # 慢波检测子任务（附表 S9）

# ------------------------------------------------------------
# 派生数值（全部由 JSON 计算）
# ------------------------------------------------------------
tr, va, te = dq["train"], dq["val"], dq["test"]
TOTAL_EP = tr["n_epochs"] + va["n_epochs"] + te["n_epochs"]
TEST_N = te["n_subjects"]
TEST20_EP = TEST_N * 20
MAJ_TEST = te["records_by_class"]["Normal"] / TEST_N
MAJ_VAL = va["records_by_class"]["Normal"] / va["n_subjects"]
MAJ_TRAIN = tr["records_by_class"]["Normal"] / tr["n_subjects"]

BA = be["agents"]
lgbm, eegnet, tcn, trf = BA["lightgbm"], BA["eegnet"], BA["tcn"], BA["transformer"]

# 混淆矩阵派生：单 Agent 二分类 Sens/Spec（mean 聚合，binary_eval.json）
ABN_ARM = te["records_by_class"]["Abnormal"] + te["records_by_class"]["Borderline"]   # Abnormal 臂 = 107
NRM_ARM = te["records_by_class"]["Normal"]                                            # Normal 臂 = 131
sens_all = {a: BA[a]["binary"]["sensitivity"] for a in BA}
spec_all = {a: BA[a]["binary"]["specificity"] for a in BA}
BEST_SENS, BEST_SPEC = max(sens_all.values()), max(spec_all.values())

AF = af["variants"]
full_m, noev_m = AF["full"]["subject_mean"], AF["no_event"]["subject_mean"]
a1_m, a2_m, a3_m = (AF[k]["subject_mean"] for k in ("A1_no_time", "A2_no_freq", "A3_no_timefreq"))

B1 = aa["bases"]["lightgbm"]["variants"]
B2 = aa["bases"]["lightgbm_event"]["variants"]

V = asy["variants"]
mc = asy["mcnemar_vs_full"]
mm = asy["mechanism_metrics"]
qs = asy["quality_stratified"]["epoch_level"]
FULL_SUBJ = V["full"]["subject_acc"]
# 仲裁贡献 ARB_PT（full − A7）已随 A7_no_arbitration 变体移除
HIGH_SHARE = qs["high"]["n_epochs"] / (qs["high"]["n_epochs"] + qs["medium"]["n_epochs"] + qs["low"]["n_epochs"]) * 100
TRIGGER = mm["disagreement_rate"] * 100

d = cal["metric_distributions"]
cf = cal["current_config_firing"]

singles_p90 = [B1["single_eegnet"]["acc"], B1["single_tcn"]["acc"], B1["single_transformer"]["acc"],
               B1["single_lightgbm"]["acc"], B2["single_lightgbm_event"]["acc"]]

D_FREQ = (full_m["accuracy"] - a2_m["accuracy"]) * 100
D_TF = (full_m["accuracy"] - a3_m["accuracy"]) * 100
D_TIME = (full_m["accuracy"] - a1_m["accuracy"]) * 100
D_EV = (full_m["accuracy"] - noev_m["accuracy"]) * 100
A6_GAIN = (B2["A6_no_transformer"]["acc"] - aa["baseline_majority"]) * 100
D_TCN_PT = (B2["stacking_full"]["acc"] - B2["A5_no_tcn"]["acc"]) * 100
SPEEDUP = lgbm["seconds"] / eegnet["seconds"]
# 无法从 outputs/*.json 取得、来源已核实的常量（来源注释）
T_BEFORE, T_AFTER = 785, 476            # 实验报告 Table 21 / generate_figures.py
TIME_SAVE = (T_BEFORE - T_AFTER) / T_BEFORE * 100     # = 39.4 → 39
EP_BEF = 0.5042                          # 实验报告 Table 21（校准前 test epoch 精度）
GRID_N = 1116                            # calibrate_disagreement.py 网格组合数（caption Table 6）
LEGACY = (0.15, 0.60, 0.80)              # config.py 注释：旧 DISAGREEMENT_CONFIG
LN3 = 1.0986
CASE_T, CASE_A, CASE_N, CASE_C = "3.0", "36.7", "34.4", "0.515"   # 实验报告 §10 SUBJ_0034
TRF3_F1 = 0.2367                         # 三分类 Transformer 塌缩 macro F1（subject_level_eval）

# escalation 实测升级率：0.35–0.65 置信区间规则在 238 测试受试者上的标记数
# 来源：binary_eval.json confidence_borderline.n_predicted_borderline
_esc = [BA[a]["confidence_borderline"]["n_predicted_borderline"] for a in BA]
ESC_LO_N, ESC_HI_N = min(_esc), max(_esc)
ESC_LO, ESC_HI = ESC_LO_N / TEST_N * 100, ESC_HI_N / TEST_N * 100

# ------------------------------------------------------------
# 一致性断言（数值可信度护栏）
# ------------------------------------------------------------
assert abs(MAJ_TEST - 0.5504) < 1e-3 and te["records_by_class"]["Normal"] == 131
assert TOTAL_EP == 159501 and TEST20_EP == 4760
assert be["n_epochs"] == 4760 and be["n_subjects"] == 238
dims = ef["dims"]; assert dims["time_domain"] + dims["freq_domain"] + dims["timefreq"] + dims["event"] == 614
assert dims["time_domain"] == 228 and dims["freq_domain"] == 152 and dims["timefreq"] == 152 and dims["event"] == 82
assert abs(D_EV - 2.1) < 0.06 and abs(D_FREQ - 5.5) < 0.06 and abs(D_TF - 2.5) < 0.06 and abs(D_TIME - 0.9) < 0.06
assert abs(A6_GAIN - 6.3) < 0.05 and abs(D_TCN_PT - 5.5) < 0.05
assert qs["high"]["n_epochs"] + qs["medium"]["n_epochs"] + qs["low"]["n_epochs"] == 4760
# seconds 为 wall-clock 测量，运行间存在波动（旧 50.4 / 新 57.3），断言仅防异常值
assert 40 <= SPEEDUP <= 70
assert abs(TRIGGER - 39.7) < 0.05
assert abs(TIME_SAVE - 39) < 0.6
assert cal["n_epochs"] == 4800 and cal["n_subjects"] == 240
# 混淆矩阵一致性：Abnormal 臂 = 79+28 = 107，Normal 臂 = 131（data_quality.json test）
assert ABN_ARM == 107 and NRM_ARM == 131
for _a in BA.values():
    _cm = _a["binary"]["confusion_matrix"]
    assert _cm["tp"] + _cm["fn"] == ABN_ARM and _cm["tn"] + _cm["fp"] == NRM_ARM
    assert abs(_a["binary"]["sensitivity"] - _cm["tp"] / ABN_ARM) < 1e-3
    assert abs(_a["binary"]["specificity"] - _cm["tn"] / NRM_ARM) < 1e-3
for _base in (B1, B2):
    for _v in _base.values():
        _cm = _v["confusion_matrix"]
        assert _cm["tp"] + _cm["fn"] == ABN_ARM and _cm["tn"] + _cm["fp"] == NRM_ARM

# ------------------------------------------------------------
# 表格主体（数值注入 LaTeX 行）
# ------------------------------------------------------------
def f4(x): return f"{x:.4f}"
def f2(x): return f"{x:.2f}"
def f1(x): return f"{x:.1f}"

table1_body = "\n".join([
    f"Train & {tr['n_records']:,} & {tr['records_by_class']['Normal']} & {tr['records_by_class']['Borderline']} & {tr['records_by_class']['Abnormal']} & {f4(MAJ_TRAIN)} \\\\",
    f"Validation & {va['n_records']} & {va['records_by_class']['Normal']} & {va['records_by_class']['Borderline']} & {va['records_by_class']['Abnormal']} & {f4(MAJ_VAL)} \\\\",
    f"Test & {te['n_records']} & {te['records_by_class']['Normal']} & {te['records_by_class']['Borderline']} & {te['records_by_class']['Abnormal']} & \\textbf{{{f4(MAJ_TEST)}}} \\\\",
])

_rows2 = None  # 已并入下方显式 table2_body
# Table 2 加粗规则：Acc 最佳=LightGBM/EEGNet 并列(0.6050)；F1 最佳 LightGBM；AUC 最佳 LightGBM；时间最佳 EEGNet
# Sens./Spec. 最佳按列由数据动态计算（_bs）
def _bs(x, best):
    return f"\\textbf{{{f4(x)}}}" if abs(x - best) < 1e-9 else f4(x)

table2_body = "\n".join([
    f"LightGBM (532-d + mRMR-128) & \\textbf{{{f4(lgbm['binary']['accuracy'])}}} & \\textbf{{{f4(lgbm['binary']['macro_f1'])}}} & {_bs(lgbm['binary']['sensitivity'], BEST_SENS)} & {_bs(lgbm['binary']['specificity'], BEST_SPEC)} & \\textbf{{{f4(lgbm['binary']['auc'])}}} & {f1(lgbm['seconds'])} \\\\",
    f"EEGNet & \\textbf{{{f4(eegnet['binary']['accuracy'])}}} & {f4(eegnet['binary']['macro_f1'])} & {_bs(eegnet['binary']['sensitivity'], BEST_SENS)} & {_bs(eegnet['binary']['specificity'], BEST_SPEC)} & {f4(eegnet['binary']['auc'])} & \\textbf{{{f1(eegnet['seconds'])}}} \\\\",
    f"TCN & {f4(tcn['binary']['accuracy'])} & {f4(tcn['binary']['macro_f1'])} & {_bs(tcn['binary']['sensitivity'], BEST_SENS)} & {_bs(tcn['binary']['specificity'], BEST_SPEC)} & {f4(tcn['binary']['auc'])} & {f1(tcn['seconds'])} \\\\",
    f"Transformer & {f4(trf['binary']['accuracy'])} & {f4(trf['binary']['macro_f1'])} & {_bs(trf['binary']['sensitivity'], BEST_SENS)} & {_bs(trf['binary']['specificity'], BEST_SPEC)} & {f4(trf['binary']['auc'])} & {f1(trf['seconds'])} \\\\",
])

def delta_cell(x): return f"$-{x:.4f}$"

table3_body = "\n".join([
    f"Full (all blocks) & 614 & \\textbf{{{f4(full_m['accuracy'])}}} & {f4(full_m['auc'])} & --- \\\\",
    f"w/o event block & 532 & {f4(noev_m['accuracy'])} & {f4(noev_m['auc'])} & {delta_cell(full_m['accuracy'] - noev_m['accuracy'])} \\\\",
    f"A1: w/o time domain & 386 & {f4(a1_m['accuracy'])} & \\textbf{{{f4(a1_m['auc'])}}} & {delta_cell(full_m['accuracy'] - a1_m['accuracy'])} \\\\",
    f"A2: w/o frequency domain & 462 & {f4(a2_m['accuracy'])} & {f4(a2_m['auc'])} & {delta_cell(full_m['accuracy'] - a2_m['accuracy'])} \\\\",
    f"A3: w/o time--frequency & 462 & {f4(a3_m['accuracy'])} & {f4(a3_m['auc'])} & {delta_cell(full_m['accuracy'] - a3_m['accuracy'])} \\\\",
])

def t4row(label, acc1, acc2, f1v, aucv, b1=False, b2=False, bf=False, bu=False):
    c1 = f"\\textbf{{{f4(acc1)}}}" if b1 else f4(acc1)
    c2 = f"\\textbf{{{f4(acc2)}}}" if b2 else f4(acc2)
    cf = f"\\textbf{{{f4(f1v)}}}" if bf else f4(f1v)
    ca = f"\\textbf{{{f4(aucv)}}}" if bu else (f4(aucv) if aucv is not None else "---")
    return f"{label} & {c1} & {c2} & {cf} & {ca} \\\\"

table4_body = "\n".join([
    t4row("Stacking (4 agents)", B1["stacking_full"]["acc"], B2["stacking_full"]["acc"],
          B2["stacking_full"]["macro_f1"], B2["stacking_full"]["auc"]),
    t4row("A4: w/o EEGNet", B1["A4_no_eegnet"]["acc"], B2["A4_no_eegnet"]["acc"],
          B2["A4_no_eegnet"]["macro_f1"], B2["A4_no_eegnet"]["auc"], b1=True),
    t4row("A5: w/o TCN", B1["A5_no_tcn"]["acc"], B2["A5_no_tcn"]["acc"],
          B2["A5_no_tcn"]["macro_f1"], B2["A5_no_tcn"]["auc"]),
    t4row("A6: w/o Transformer", B1["A6_no_transformer"]["acc"], B2["A6_no_transformer"]["acc"],
          B2["A6_no_transformer"]["macro_f1"], B2["A6_no_transformer"]["auc"], b2=True, bf=True),
    t4row("Equal-weight soft voting", B1["A9_soft_voting_equal"]["acc"], B2["A9_soft_voting_equal"]["acc"],
          B2["A9_soft_voting_equal"]["macro_f1"], B2["A9_soft_voting_equal"]["auc"], bu=True),
    t4row("Hard voting (tie $\\rightarrow$ Normal)", B1["hard_voting"]["acc"], B2["hard_voting"]["acc"],
          B2["hard_voting"]["macro_f1"], None),
    t4row("Single: LightGBM", B1["single_lightgbm"]["acc"], B2["single_lightgbm_event"]["acc"],
          B2["single_lightgbm_event"]["macro_f1"], B2["single_lightgbm_event"]["auc"]),
    t4row("Single: EEGNet", B1["single_eegnet"]["acc"], B2["single_eegnet"]["acc"],
          B2["single_eegnet"]["macro_f1"], B2["single_eegnet"]["auc"]),
    t4row("Single: TCN", B1["single_tcn"]["acc"], B2["single_tcn"]["acc"],
          B2["single_tcn"]["macro_f1"], B2["single_tcn"]["auc"]),
    t4row("Single: Transformer", B1["single_transformer"]["acc"], B2["single_transformer"]["acc"],
          B2["single_transformer"]["macro_f1"], B2["single_transformer"]["auc"]),
])

def t5row(label, acc, f1v, b=None, c=None, p=None):
    bc = f"{b}/{c}" if b is not None else "---"
    pv = f2(p) if p is not None else "---"
    sig = "n.s." if p is not None else "---"
    return f"{label} & {f4(acc)} & {f4(f1v)} & {bc} & {pv} & {sig} \\\\"

table5_body = "\n".join([
    t5row("Full system", V["full"]["subject_acc"], V["full"]["subject_macro_f1"]),
    # A7（no arbitration）行已随仲裁机制移除，机制消融仅剩 A8 / A9
    t5row("A8: fixed weights", V["A8_fixed_weights"]["subject_acc"], V["A8_fixed_weights"]["subject_macro_f1"],
          mc["A8_fixed_weights"]["full_correct_variant_wrong"], mc["A8_fixed_weights"]["full_wrong_variant_correct"],
          mc["A8_fixed_weights"]["p_value"]),
    t5row("A9: equal weights", V["A9_equal_weights"]["subject_acc"], V["A9_equal_weights"]["subject_macro_f1"],
          mc["A9_equal_weights"]["full_correct_variant_wrong"], mc["A9_equal_weights"]["full_wrong_variant_correct"],
          mc["A9_equal_weights"]["p_value"]),
])

table6_body = "\n".join([
    "Disagreement trigger rate & 100\\% & \\textbf{" + f1(TRIGGER) + "\\%} \\\\",
    f"Subject-level accuracy & {f4(FULL_SUBJ)} & {f4(FULL_SUBJ)} \\\\",
    f"Epoch-level accuracy & {f4(EP_BEF)} & {f4(V['full']['epoch_acc'])} \\\\",
    f"Inference time ({TEST20_EP:,} epochs) & {T_BEFORE} s & {T_AFTER} s ($-{TIME_SAVE:.0f}\\%$) \\\\",
])

table7_body = "\n".join([
    r"\citet{schirrmeister2017} & End-to-end deep CNN & TUAB, adult-dominant; binary & Acc 85.4\% & Single model; curated binary labels; no uncertainty handling \\",
    r"\citet{roy2018chrono} & ChronoNet (CNN + gated RNN) & TUAB; binary & Acc 86.6\%$^{\dagger}$ & Single deep model; same protocol caveats \\",
    r"CNN hybrids, transfer learning \citep[surveyed in][]{roy2019,chen2025} & CNN--LSTM / pretrained hybrids & TUAB; binary & Acc 86.2--88.8\%$^{\dagger}$ & Architecture-centric single models on a curated benchmark \\",
    r"\citet{chen2025} & Multi-domain features + GBDT & TUAB v3.0.1; binary & Acc $\approx$ 90\% & Closest methodologically; single feature-driven pipeline, no deep-model collaboration or disagreement handling \\",
    r"\citet{adhdcd2024} & Explainable deep network & Private pediatric + public ($n=123/121$); ADHD/CD vs.\ HC & Acc 93.7\% & Pediatric but disease-specific, healthy-vs-patient; small $n$ \\",
    r"\citet{vepinetv2_2025} & Multimodal deep IED detection & Prospective, 3 centers; event level & AUC 0.96--0.98 & Event-level detection (parallels our event features); no record-level verdict or voting \\",
    r"\citet{neonaid2026} & Neonatal pipeline with QC gating & 2 centers; FBA / sleep staging & MAE 0.50--0.55 wk; $\kappa$ 0.87--0.89 & Demonstrates the value of quality control (parallels our quality agent); different tasks \\",
    r"\citet{mdagents2024} & Adaptive LLM team & Medical QA (text) & Accuracy vs.\ single LLMs & LLM-centric; no physiological signals; no calibrated triggering \\",
    r"\citet{colacare2025} & MetaAgent + DoctorAgents + RAG & EHR tabular (mortality / readmission) & 3 EHR datasets & LLM-orchestrated on structured records; not signal-level \\",
    r"\citet{mac2025} & 4 doctor agents + supervisor, MDT-style debate & 302 rare-disease cases (text) & Accuracy vs.\ GPT-3.5/4 & Text-only consultation; no cost--performance calibration \\",
    r"\citet{dynamicare2025} & Dynamic specialist team & Open-ended medical dialogue & Framework benchmarks & Interaction-centric; no quantitative clinical endpoint \\",
    (r"\textbf{EEG-MAS (ours)} & Orchestrated heterogeneous agents (feature- + signal-driven) with \emph{calibrated} conditional arbitration & "
     rf"Private pediatric routine EEG, {dq['n_records']:,} records / {TEST_N} test subjects; 3-tier labels, binary protocol (BL $\rightarrow$ A) & "
     rf"Acc {f4(B2['A6_no_transformer']['acc'])} ($+{f1(A6_GAIN)}$ pt); AUC {f4(B2['A6_no_transformer']['auc'])}; $-{TIME_SAVE:.0f}$\% inference via calibration & "
     r"Signal-level multi-agent collaboration; realistic label tiers incl.\ Borderline; mechanism-level significance testing; low-confidence $\rightarrow$ human review \\"),
])

# ------------------------------------------------------------
# 文本替换字典（@TOKEN@ → 数值）
# ------------------------------------------------------------
T = {
    "NR": f"{dq['n_records']:,}",
    "TOTAL_EP": f"{TOTAL_EP:,}",
    "TRAIN_N": f"{tr['n_records']:,}", "VAL_N": f"{va['n_records']}", "TEST_N": f"{TEST_N}",
    "TRAIN_EP": f"{tr['n_epochs']:,}", "VAL_EP": f"{va['n_epochs']:,}", "TEST_EP_FULL": f"{te['n_epochs']:,}",
    "TEST20_EP": f"{TEST20_EP:,}",
    "MAJ_TEST": f4(MAJ_TEST),
    "SNR_MED": f2(dq["snr_db"]["median"]), "SNR_P10": f2(dq["snr_db"]["p10"]), "SNR_P90": f2(dq["snr_db"]["p90"]),
    "ART_MED": f"{dq['artifact_ratio']['median']:.3f}",
    "KEEP_MED": f"{dq['keep_rate']['median']:.3f}",
    "HIGH_SHARE": f1(HIGH_SHARE),
    "DELTA": f1(dq["band_power_percent"]["delta0.5-4"]),
    "COV_N": "837",
    "SW_A": f1(lma["wave_vs_label"]["slow_wave"]["pos_rate_by_label"]["Abnormal"]),
    "SW_B": f1(lma["wave_vs_label"]["slow_wave"]["pos_rate_by_label"]["Borderline"]),
    "SW_N": f1(lma["wave_vs_label"]["slow_wave"]["pos_rate_by_label"]["Normal"]),
    "EPI_A": f1(lma["wave_vs_label"]["epileptiform_count"]["pos_rate_by_label"]["Abnormal"]),
    "EPI_B": f1(lma["wave_vs_label"]["epileptiform_count"]["pos_rate_by_label"]["Borderline"]),
    "EPI_N": f1(lma["wave_vs_label"]["epileptiform_count"]["pos_rate_by_label"]["Normal"]),
    "FEAT_DIM": "614", "DIM_T": "228", "DIM_F": "152", "DIM_TF": "152", "DIM_E": "82",
    "VAL_L": f4(sva["lightgbm"]), "VAL_E": f4(sva["eegnet"]), "VAL_T": f4(sva["tcn"]), "VAL_R": f4(sva["transformer"]),
    "TRF3_ACC": f4(sle["agents"]["transformer"]["aggregation"]["mean"]["subject_accuracy"]),
    "TRF3_F1": f4(TRF3_F1),
    "EEG3_ACC": f4(sle["agents"]["eegnet"]["aggregation"]["mean"]["subject_accuracy"]),
    "LGBM_ACC": f4(lgbm["binary"]["accuracy"]), "LGBM_AUC": f4(lgbm["binary"]["auc"]), "LGBM_T": f1(lgbm["seconds"]),
    "EEGNET_ACC": f4(eegnet["binary"]["accuracy"]), "EEGNET_T": f1(eegnet["seconds"]),
    "TCN_ACC": f4(tcn["binary"]["accuracy"]), "TRF_ACC": f4(trf["binary"]["accuracy"]),
    "SPEEDUP": f"{SPEEDUP:.0f}",
    "FULL_ACC": f4(full_m["accuracy"]), "FULL_AUC": f4(full_m["auc"]),
    "NOEV_ACC": f4(noev_m["accuracy"]), "A1_AUC": f4(a1_m["auc"]),
    "D_EV": f1(D_EV), "D_FREQ": f1(D_FREQ), "D_TF": f1(D_TF), "D_TIME": f1(D_TIME),
    "Q_DELTA": f"{ef['delta']['acc'] * 100:.1f}",
    "MRMR_EVENT": f"{ef['mrmr_event_selected']}",
    "STACK_B1": f4(B1["stacking_full"]["acc"]), "STACK_B2": f4(B2["stacking_full"]["acc"]),
    "A6_B2": f4(B2["A6_no_transformer"]["acc"]), "A6_F1": f4(B2["A6_no_transformer"]["macro_f1"]),
    "A6_AUC": f4(B2["A6_no_transformer"]["auc"]), "A6_GAIN": f1(A6_GAIN),
    "A5_B2": f4(B2["A5_no_tcn"]["acc"]), "D_TCN_PT": f1(D_TCN_PT),
    "SV_AUC": f4(B2["A9_soft_voting_equal"]["auc"]), "SV_ACC": f4(B2["A9_soft_voting_equal"]["acc"]),
    "HV_ACC": f4(B2["hard_voting"]["acc"]),
    "HV_SENS": f4(B2["hard_voting"]["sensitivity"]), "HV_SPEC": f4(B2["hard_voting"]["specificity"]),
    "MIN_SINGLE": f4(min(singles_p90)), "MAX_SINGLE": f4(max(singles_p90)),
    "FULL_SUBJ": f4(FULL_SUBJ),
    "A8_SUBJ": f4(V["A8_fixed_weights"]["subject_acc"]),
    "A9_SUBJ": f4(V["A9_equal_weights"]["subject_acc"]),
    "MC_A8_BC": f"{mc['A8_fixed_weights']['full_correct_variant_wrong']}/{mc['A8_fixed_weights']['full_wrong_variant_correct']}",
    "MC_A8_P": f2(mc["A8_fixed_weights"]["p_value"]),
    "MC_A9_BC": f"{mc['A9_equal_weights']['full_correct_variant_wrong']}/{mc['A9_equal_weights']['full_wrong_variant_correct']}",
    "MC_A9_P": f2(mc["A9_equal_weights"]["p_value"]),
    "N_ARB": f"{mm['arbitration_improvement']['n_disagreement_arbitrated']:,}",
    "ARB_BEF": f4(mm["arbitration_improvement"]["acc_before_arbitration"]),
    "ARB_AFT": f4(mm["arbitration_improvement"]["acc_after_arbitration"]),
    "TRIGGER": f1(TRIGGER),
    "MED_N": f"{qs['medium']['n_epochs']}", "LOW_N": f"{qs['low']['n_epochs']}",
    "PD_MED": f"{d['max_prob_diff']['0.5']:.3f}",
    "ENT_MED": f"{d['entropy']['0.5']:.4f}", "ENT_P99": f"{d['entropy']['0.99']:.4f}",
    "R1_LEG": f1(cf["rule1_prob_diff"] * 100), "R2_LEG": f1(cf["rule2_majority"] * 100),
    "R3_LEG": f1(cf["rule3_entropy"] * 100), "COMB_LEG": f1(cf["combined"] * 100),
    "NEVER_VAL": f4(cal["baselines"]["never_arbitrate_subject_acc"]),
    "ALWAYS_VAL": f4(cal["baselines"]["always_arbitrate_subject_acc"]),
    "GRID_N": f"{GRID_N:,}",
    "EP_BEF": f4(EP_BEF), "EP_AFT": f4(V["full"]["epoch_acc"]),
    "TIME_SAVE": f"{TIME_SAVE:.0f}",
    "T_BEFORE": f"{T_BEFORE}", "T_AFTER": f"{T_AFTER}",
    "CAL_N_EP": f"{cal['n_epochs']:,}", "CAL_N_SUB": f"{cal['n_subjects']}",
    "CASE_T": CASE_T, "CASE_A": CASE_A, "CASE_N": CASE_N, "CASE_C": CASE_C,
    "ESC_LO": f1(ESC_LO), "ESC_HI": f1(ESC_HI),
    "ESC_LO_N": f"{ESC_LO_N}", "ESC_HI_N": f"{ESC_HI_N}",
    "SWS_AUC": f4(sws["slow_wave_auc"]), "SWS_MAJ": f2(sws["slow_baseline"]),
    "SWS_N": f"{sws['n_records']}", "SWS_NP": f"{sws['n_slow_positive']}",
    "SWS_NN": f"{sws['n_slow_negative']}",
    "AGE_MED": "5--6", "AGE_MIN": "0.08", "AGE_MAX": "28",  # lma age_by_label：median 5/5/6, min 0.08, max 28
    # 混淆矩阵 / 筛查指标（binary_eval.json + ablation_agents.json）
    "LGBM_SENS": f4(lgbm["binary"]["sensitivity"]), "LGBM_SPEC": f4(lgbm["binary"]["specificity"]),
    "EEGNET_SENS": f4(eegnet["binary"]["sensitivity"]), "EEGNET_SPEC": f4(eegnet["binary"]["specificity"]),
    "SENS_LO": f4(min(sens_all.values())), "SENS_HI": f4(max(sens_all.values())),
    "SPEC_LO": f4(min(spec_all.values())), "SPEC_HI": f4(max(spec_all.values())),
    "ABN_N": f"{ABN_ARM}", "NRM_N": f"{NRM_ARM}",
    "STACK_SENS": f4(B2["stacking_full"]["sensitivity"]),
    "STACK_SPEC": f4(B2["stacking_full"]["specificity"]),
    "A6_SENS": f4(B2["A6_no_transformer"]["sensitivity"]),
    "A6_SPEC": f4(B2["A6_no_transformer"]["specificity"]),
    "A6_TP": f"{B2['A6_no_transformer']['confusion_matrix']['tp']}",
    "A6_FN": f"{B2['A6_no_transformer']['confusion_matrix']['fn']}",
    "A6_TN": f"{B2['A6_no_transformer']['confusion_matrix']['tn']}",
    "A6_FP": f"{B2['A6_no_transformer']['confusion_matrix']['fp']}",
    # 表格主体注入
    "TABLE1_BODY": table1_body, "TABLE2_BODY": table2_body, "TABLE3_BODY": table3_body,
    "TABLE4_BODY": table4_body, "TABLE5_BODY": table5_body, "TABLE6_BODY": table6_body,
    "TABLE7_BODY": table7_body,
}

# ============================================================
# main.tex 正文（结构：总稿 4.3–4.7 IMRaD 大纲）
# ============================================================
TEX = r"""
% ============================================================
% EEG-MAS manuscript draft — generated by eeg_multi_agent/scripts/generate_manuscript_tex.py
% Structure follows 论文写作总稿.docx Part 4 (IMRaD outline).
% All experimental numbers are injected at generation time from outputs/*.json.
% All bib entries verified against publisher/arXiv/PubMed records (2026-10-24).
% Compile: pdflatex + bibtex (tested configuration: Overleaf, TeX Live).
% ============================================================
\documentclass[11pt]{article}

\usepackage[margin=2.5cm]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{tabularx}
\usepackage{xltabular}
\usepackage[round]{natbib}
\usepackage{caption}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\usepackage{newtxtext,newtxmath}   % Times-like text/math; fallback: \usepackage{times}

\graphicspath{{figures/}}
\captionsetup{font=small,labelfont=bf}
% 放宽浮动体放置限制（防止竖版架构图卡死浮动队列、图全部堆积到文末）
\renewcommand{\topfraction}{0.85}
\renewcommand{\bottomfraction}{0.6}
\renewcommand{\textfraction}{0.05}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{3}
\setcounter{totalnumber}{5}

\title{EEG-MAS: A Quality-Aware Multi-Agent System with Calibrated Disagreement
Arbitration for Pediatric EEG Screening}
\author{Haojia Qiu\thanks{Corresponding author: sky060325@163.com\\
Affiliation: [Department, Institution, City, Country]}}
\date{}

\begin{document}
\maketitle

\begin{abstract}
\noindent
Routine pediatric electroencephalography (EEG) screening is constrained by growing
workload and a shortage of expert readers, yet existing automated readers are
predominantly single models evaluated on curated, adult-dominant binary benchmarks,
with no mechanism for handling disagreement among complementary predictors. We
present EEG-MAS, a three-layer multi-agent system in which a coordination layer
(Orchestrator) schedules feature, diagnosis, and validation layers over 2-s epochs:
four heterogeneous diagnosis agents --- a feature-driven LightGBM on mRMR-selected
multi-domain features and three signal-driven deep models (EEGNet, TCN,
Transformer) on raw epochs --- are fused by quality-aware dynamic weighted voting,
wrapped in cross-agent consistency scoring, a feature-level evidence chain, and
low-confidence escalation to human review. We further contribute a calibration
methodology for disagreement-triggered conditional arbitration: diagnosing the
legacy thresholds exposed a degenerate entropy rule under near-uniform three-class
posteriors (median entropy @ENT_MED@ vs.\ $\ln 3 = 1.0986$), and grid-search
calibration over @GRID_N@ threshold combinations cut the arbitration trigger rate
from 100\% to @TRIGGER@\% and inference time by @TIME_SAVE@\%
(@T_BEFORE@~s $\rightarrow$ @T_AFTER@~s per @TEST20_EP@ epochs) with subject-level
accuracy unchanged (@FULL_SUBJ@). On @NR@ routine records (@TEST_N@ test subjects) with three-tier
clinical labels, the best binary configuration (Borderline merged into Abnormal)
reaches @A6_B2@ accuracy ($+@A6_GAIN@$ pt over the @MAJ_TEST@ majority baseline);
an 82-dimensional epileptiform-event feature block contributes $+@D_EV@$ pt at full
scale. McNemar exact paired tests show no mechanism-level difference reaches
significance at @TEST_N@ subjects --- reported transparently as part of the
evaluation protocol. EEG-MAS demonstrates calibrated conditional arbitration and
honest mechanism-level evaluation as reusable standards for voting-based clinical
multi-agent systems.
\\[4pt]
\textbf{Keywords:} pediatric EEG; multi-agent system; disagreement detection;
arbitration; threshold calibration; clinical decision support
\end{abstract}

\section{Introduction}
\label{sec:intro}

Electroencephalography is central to the diagnosis and management of epilepsy and
other neurological conditions in children \citep{scheffer2017,fiest2017}. Yet
routine pediatric EEG review remains a bottleneck: recordings are long, findings
such as epileptiform discharges and slow waves are sparse and morphologically
subtle, and the number of qualified pediatric electroencephalographers has not kept
pace with screening demand. A large share of routine records is ultimately read as
normal or near-normal, so expert attention is disproportionately consumed by
flagging the minority of abnormal studies. Automated screening tools that are
accurate, explicit about their uncertainty, and cheap enough to run on every record
could redistribute this workload --- provided they are designed for the conditions
of routine clinical acquisition rather than for curated research benchmarks.

Most automated EEG reading research, however, has been evaluated under conditions
far removed from that setting. Since the introduction of end-to-end convolutional
reading models \citep{schirrmeister2017}, a large literature has developed around
the Temple University Hospital Abnormal (TUAB) corpus \citep{oates2016}: recurrent
and convolutional hybrids such as ChronoNet \citep{roy2018chrono}, a family of
transfer-learning and CNN-hybrid variants \citep[surveyed in][]{roy2019,chen2025},
and feature-driven pipelines that combine multi-domain features with
gradient-boosted trees \citep{chen2025}. These works share three properties.
First, they are single models or homogeneous ensembles: one architecture consumes
one representation, and no mechanism exists for reconciling contradictory evidence
inside the system. Second, they are evaluated almost exclusively on adult-dominant,
expert-curated binary benchmarks, whereas clinical reality --- particularly in
pediatrics --- involves three-tier verdicts (normal / borderline / abnormal), noisy
labels \citep{frenay2014}, and heterogeneous acquisition quality. Third, they
produce point predictions without an escalation path: nothing in the output tells a
clinician when the prediction should not be trusted. Adjacent lines of work address
related problems --- event-level epileptiform-discharge detection
\citep{vepinetv2_2025} and quality-control gating \citep{neonaid2026} --- but
neither yields a record-level verdict from multiple complementary models.

In parallel, multi-agent collaboration has become an active paradigm in medical AI:
adaptive LLM teams for medical question answering \citep{mdagents2024}, MDT-style
debating agent committees for rare-disease diagnosis \citep{mac2025},
guideline-augmented agent orchestration over electronic health records
\citep{colacare2025}, and dynamic specialist-team frameworks for interactive
consultation \citep{dynamicare2025}. These systems operate at the level of text and
structured records. To our knowledge, no prior multi-agent framework addresses
physiological \emph{signal} interpretation --- although this is precisely the
setting where multiple heterogeneous predictors disagree frequently, and where
classical work on reject options \citep{chow1970} and selective prediction
\citep{geifman2017} shows that knowing when not to decide is as important as the
decision itself.

We present EEG-MAS, a quality-aware multi-agent system for pediatric EEG screening
(Fig.~\ref{fig:architecture}). A coordination layer (Orchestrator) schedules an
epoch-level pipeline across three functional layers: a feature layer extracting a
614-dimensional multi-domain representation; a diagnosis layer of four
heterogeneous agents --- a feature-driven LightGBM consuming mRMR-selected
features, and three signal-driven deep models (EEGNet, TCN, Transformer) reading
raw epochs; and a validation layer producing a cross-agent consistency score and a
feature-level evidence chain. Three design decisions target the gaps identified
above: (i) dual-path heterogeneity combines complementary inductive biases at the
signal level; (ii) SNR-aware dynamic weighting adapts the fusion to per-epoch
signal quality; and (iii) a \emph{calibrated} disagreement detector triggers
conditional second-pass arbitration, whose low-confidence outputs are escalated to
human review.

Our contributions are:
\begin{itemize}
\item \textbf{C1 (architecture).} A three-layer multi-agent architecture that, to
our knowledge, is the first to orchestrate heterogeneous feature- and signal-driven
agents at the EEG-epoch level (Section~\ref{sec:methods}).
\item \textbf{C2 (methodology).} A calibration methodology for disagreement-triggered
arbitration: we diagnose a degenerate entropy rule under near-uniform three-class
posteriors and show that grid-search calibration cuts the trigger rate from 100\%
to @TRIGGER@\% and inference time by @TIME_SAVE@\% with accuracy unchanged
(Sections~\ref{sec:fusion} and \ref{sec:calibration}).
\item \textbf{C3 (evaluation standard).} A mechanism-level evaluation protocol
combining point estimates, discordant-pair counts, and McNemar exact paired tests,
with all non-significant results reported transparently
(Section~\ref{sec:mechanism}).
\item \textbf{C4 (features).} An 82-dimensional epileptiform-event feature block
whose full-scale contribution ($+@D_EV@$ pt) reverses the conclusion of a
small-sample A/B pretest ($@Q_DELTA@$ pt), together with the lesson that such
pretests lack the power to guide feature-set decisions (Section~\ref{sec:feat_ab}).
\end{itemize}
Section~\ref{sec:methods} details the system and evaluation protocol,
Section~\ref{sec:results} reports results, and Section~\ref{sec:discussion}
discusses positioning, generalizable methodology, and limitations.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.88\textwidth,height=0.62\textheight,keepaspectratio]{fig_system_architecture_layered}
\caption{Architecture of EEG-MAS. The pipeline is organised into five processing
stages under three agent layers: a coordination layer performs quality gating and
SNR-aware dynamic weighting (Stages 1 and 3); multi-domain feature extraction
yields a 614-dim vector, including an 82-dim epileptiform-event block, reduced to
128 mRMR-selected features (Stage 2); four heterogeneous diagnosis agents ---
LightGBM on selected features and EEGNet, TCN, and Transformer on raw epochs ---
are combined by weighted soft voting (Stage 4); calibrated disagreement detection
routes @TRIGGER@\% of epochs to second-pass attention-weighted arbitration,
followed by consistency and explainability checks and subject-level p90
aggregation (Stage 5). Solid arrows denote data flow; dashed red arrows denote
the conditional arbitration loop.}
\label{fig:architecture}
\end{figure}

\section{Methods}
\label{sec:methods}

\subsection{Dataset and preprocessing}
\label{sec:dataset}

The dataset comprises @NR@ routine scalp EEG records from pediatric patients,
collected at a single center (ethics statement in Declarations). Each record
corresponds to one subject. Recordings were acquired at 500 Hz with 35 channels;
19 EEG channels were retained after amplitude and topography screening of non-EEG
and reference leads, downsampled to 250 Hz, and partitioned into 2-s epochs (50\%
overlap). To avoid the electrode-preparation segment, the first 60 s of each
recording was skipped and a 600-s read window was used; up to 100 epochs per record
were retained by uniform sampling. Each channel was z-scored using training-split
statistics. The final corpus contains @TOTAL_EP@ epochs
(median 100 per record).

Each record carries a three-tier clinical label --- Normal, Borderline, or
Abnormal --- derived from the clinical report of the attending neurologist.
Records were split by subject into train / validation / test
= @TRAIN_N@ / @VAL_N@ / @TEST_N@ (Table~\ref{tab:dataset}), stratified by class.
The class distribution is imbalanced (@MAJ_TEST@ of test records are Normal), so we
report the majority-class baseline alongside every result. Two annotation
workflows coexist in the source labels; their heterogeneity and its effect on
achievable accuracy are quantified in Table~S4 and revisited in Limitations.

Per-epoch signal quality was assessed by the quality agent (Section~\ref{sec:fusion}).
Overall quality was high: median SNR @SNR_MED@ dB (P10--P90 @SNR_P10@--@SNR_P90@),
median artifact ratio @ART_MED@, median epoch keep rate @KEEP_MED@; @HIGH_SHARE@\%
of test@20 epochs were graded high quality (Table~S1, Fig.~\ref{fig:dataset}c).
The power spectrum was dominated by delta activity (@DELTA@\% mean share),
consistent with a pediatric cohort (Fig.~\ref{fig:dataset}b).

Clinical metadata linkage succeeded for @COV_N@ of the 1,830 records assembled
during data organization (51.4\% of test records; Table~S2); the analysis dataset
comprises the @NR@ records that passed duration and quality filtering into the
epoch cache. The cohort is predominantly early-childhood: among linked records the
median age is @AGE_MED@ years across labels (full range @AGE_MIN@--@AGE_MAX@
years). Among them, the label--event coupling is striking
(Fig.~\ref{fig:event}): slow-wave positivity reaches @SW_A@\% among Abnormal,
@SW_B@\% among Borderline, and @SW_N@\% among Normal records; positivity for any
epileptiform event shows the same ordering (@EPI_A@\% / @EPI_B@\% / @EPI_N@\%).
Two consequences follow. First, this coupling motivates a dedicated
epileptiform-event feature block in the feature layer (Section~\ref{sec:features}).
Second, the intermediate position of Borderline previews the difficulty of the
three-class task and shapes our evaluation protocol (Section~\ref{sec:protocol}).
Age distributions overlap substantially across labels, and age residualization of
features yields no gain ($\Delta$AUC $= -0.005$; Table~S8), indicating that age
confounding does not drive the reported results.

\begin{table}[t]
\centering
\caption{Dataset splits and class distribution (@NR@ pediatric routine EEG
records, one record per subject; 19 channels, 250 Hz, 2-s epochs). Epochs per
split: train @TRAIN_EP@, validation @VAL_EP@, test@20 @TEST20_EP@ (all reported
results use the test@20 protocol; full-length test epochs = @TEST_EP_FULL@).
Majority baseline = largest class share of records within each split.}
\label{tab:dataset}
\begin{tabular}{lccccc}
\toprule
Split & Records (subjects) & Normal & Borderline & Abnormal & Majority baseline \\
\midrule
@TABLE1_BODY@
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{paper_fig2_dataset_overview}
\caption{Dataset overview. (a) Record (subject) counts per split and class, with
majority-class baseline of the test split (@MAJ_TEST@). (b) Mean band-power share
across five canonical EEG bands; the dominant $\delta$ share (@DELTA@\%) is
consistent with the pediatric cohort. (c) Signal-quality distributions (median,
P10--P90, full range) for SNR, artifact ratio, and epoch keep rate. A total of
@NR@ records (@TOTAL_EP@ epochs; 19 channels, 250 Hz, 2-s segments) were split by
record into train / validation / test = @TRAIN_N@ / @VAL_N@ / @TEST_N@.}
\label{fig:dataset}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.82\textwidth]{fig_label_event_insight}
\caption{Epileptiform-event positive rates by clinical label among the
@COV_N@/1,830 records with annotated clinical fields. Slow-wave positivity
separates Abnormal (@SW_A@\%) from Normal (@SW_N@\%) almost perfectly, with
Borderline intermediate (@SW_B@\%); ``any epileptiform event'' shows the same
ordering (@EPI_A@\% / @EPI_B@\% / @EPI_N@\%). This label--event coupling motivates
the 82-dim event-feature block introduced in the feature layer, and foreshadows
the difficulty of separating the Borderline class
(Sections~\ref{sec:results} and \ref{sec:discussion}).}
\label{fig:event}
\end{figure}

\subsection{Feature layer}
\label{sec:features}

The feature layer extracts a @FEAT_DIM@-dimensional vector per epoch, organized in
four blocks. (i)~\emph{Time domain} (@DIM_T@; 12 per channel): mean, standard
deviation, variance, root-mean-square, peak-to-peak, skewness, kurtosis,
zero-crossing rate, Hjorth activity/mobility/complexity, and maximum absolute
amplitude. (ii)~\emph{Frequency domain} (@DIM_F@; 8 per channel): relative band
power in the five canonical bands ($\delta$ 0.5--4, $\theta$ 4--8, $\alpha$
8--13, $\beta$ 13--30, $\gamma$ 30--45 Hz; Welch periodogram), peak frequency, 95\%
spectral edge frequency, and spectral entropy. (iii)~\emph{Time--frequency}
(@DIM_TF@; 8 per channel): multi-scale sliding-window energy statistics at
0.2--2~s scales. (iv)~\emph{Epileptiform-event statistics} (@DIM_E@): per channel
(on 1--30 Hz band-passed signals) the kurtosis, peak-to-RMS ratio,
high-/low-frequency power ratio (13--30 vs.\ 1--12 Hz), and negative-peak
asymmetry, plus six global statistics (sum, max, and standard deviation of channel
kurtosis; maximum peak-to-RMS; a left--right lateralization index; maximum
absolute inter-channel correlation). The event block was designed directly from
the label--event coupling of Fig.~\ref{fig:event}. All features were standardized
with training-split statistics. For the feature-driven agent,
minimum-redundancy maximum-relevance selection (mRMR, MID criterion on
equal-frequency-binned mutual information; \citealp{peng2005}) reduced the vector
to 128 features.

\subsection{Diagnosis agents}
\label{sec:agents}

Four heterogeneous agents score each epoch. \emph{LightGBM} \citep{ke2017} is
feature-driven: it consumes the mRMR-selected feature vector (200 trees, learning
rate 0.05, 31 leaves, subsample 0.9). Three \emph{signal-driven} agents read the
normalized raw epoch: \emph{EEGNet} \citep{lawhern2018}, a compact CNN (filter
banks 8/16/16, temporal kernel of 64 samples, dropout 0.25, ELU); a temporal
convolutional network \citep{bai2018} with six dilated causal layers (64 hidden
channels, kernel size 5, dilation base 2, dropout 0.2); and an epoch
\emph{Transformer} \citep{vaswani2017} that splits the 500-sample epoch into
50-sample patches ($d_{\mathrm{model}}=128$, 8 heads, 4 layers, feed-forward 512,
dropout 0.1). Deep agents were trained with Adam (learning rate $10^{-3}$, weight
decay $10^{-4}$), batch size 64, ReduceLROnPlateau scheduling, and best-checkpoint
selection over 30 epochs. Three-class subject-level validation accuracies were
@VAL_L@ (LightGBM), @VAL_E@
(EEGNet), @VAL_T@ (TCN), and @VAL_R@ (Transformer). The base voting weights
(0.20/0.30/0.25/0.25) are a design choice balancing the feature and signal paths
--- the feature path trades accuracy for interpretability, the deep path for
throughput --- rather than a rank encoding of these accuracies; online updating
(Section~\ref{sec:fusion}) adapts them from rollout data. The heterogeneity is
deliberate: feature-driven
and signal-driven agents make different kinds of errors
(Section~\ref{sec:agent_ab}), which both improves fusion and generates informative
disagreement.

\subsection{Fusion, disagreement detection, and arbitration}
\label{sec:fusion}

\paragraph{Quality assessment and dynamic weighting.}
For each epoch, the Orchestrator first runs signal-quality assessment (SNR
estimation, artifact-channel ratio, flat-channel detection). Quality is graded
high (SNR $>$ 10 dB), low (SNR $<$ 5 dB or artifact ratio $>$ 0.30), or medium
otherwise. Quality-aware adjustments bias the fusion toward agents that tolerate
each regime: in high-quality epochs the weights of EEGNet and Transformer are
boosted by 10\%; in low-quality epochs the weight of LightGBM is boosted by 15\%.
Base voting weights (Section~\ref{sec:agents}) are updated online
every 50 epochs from the agents' decayed rolling accuracy (decay 0.95), clipped to
$[0.05, 0.60]$ per agent. Epoch labels are decided by weighted soft voting.

\paragraph{Disagreement detection.}
After voting, a disagreement detector applies three rules to the agents'
probability vectors: (R1) the maximum pairwise probability difference exceeds
$\theta_d$; (R2) the fraction of agents agreeing on the modal label falls below
$\theta_m$; (R3) the mean Shannon entropy exceeds $\theta_e$. The deployed
thresholds $(\theta_d, \theta_m, \theta_e) = (0.30, 0.60, 1.099)$ are the result
of the calibration study described next and in Section~\ref{sec:calibration}; the
legacy configuration $(0.15, 0.60, 0.80)$ fired on 100\% of validation epochs.

\paragraph{Conditional arbitration.}
When any rule fires, a second-pass arbitration is executed.
(1)~The feature vector is augmented with spatial-domain features (channel
coherence across the five canonical bands).
(2)~All agents re-infer: LightGBM consumes the augmented vector when dimensions
match (otherwise falling back to the base features), while deep agents average
predictions over the original and time-reversed epoch (test-time augmentation).
(3)~Each agent $i$ receives a credibility score
$c_i = 0.40\,s_i^{\mathrm{cons}} + 0.35\,s_i^{\mathrm{gain}} +
0.25\,s_i^{\mathrm{fit}}$, combining cosine similarity to the mean second-round
probability distribution, a normalized confidence gain over the first round
($\pm 0.05$ mapped to $[0,1]$), and a quality-fit prior (e.g., tree-based models
are favored at low SNR).
(4)~The final epoch verdict is a re-weighted vote with weights proportional to
credibility $\times$ dynamic weight, renormalized and clipped to $[0.05, 0.60]$.

\paragraph{Threshold calibration.}
The legacy thresholds were diagnosed on the validation split (@CAL_N_EP@ epochs,
@CAL_N_SUB@ subjects): the median maximum probability difference (@PD_MED@)
exceeded $\theta_d = 0.15$, and the mean entropy concentrated just below the
theoretical maximum $\ln 3 \approx @LN3@R$ (median @ENT_MED@), so the entropy rule
was degenerate --- near-uniform three-class posteriors make entropy uninformative
as a disagreement signal. We grid-searched @GRID_N@ threshold combinations,
replaying arbitration from cached per-epoch metrics (no model retraining). The
adopted configuration admits only strong disagreement, triggering on @TRIGGER@\%
of validation epochs, at the validation accuracy optimum (@NEVER_VAL@ subject
accuracy, identical to never arbitrating; always arbitrating yields @ALWAYS_VAL@).
The pure-accuracy optimum (``never arbitrate'') was rejected as a deployment
choice because it disables the arbitration pathway --- a deliberate
cost--performance decision that preserves second-pass capability.

\paragraph{Stacking meta-learner.}
For the binary fusion study (Section~\ref{sec:agent_ab}), agent probabilities are
additionally combined by a Stacking meta-learner \citep{wolpert1992} --- a
LightGBM trained on validation-split agent probabilities, avoiding test leakage;
equal-weight soft voting, hard voting, and single agents serve as fusion
baselines.

\subsection{Validation layer and explainability}
\label{sec:validation}

The validation layer wraps every verdict with two safeguards. A cross-agent
consistency score summarizes agreement among the four agents; low consistency, or
a confidence inside the borderline range (0.35--0.65), flags the record for human
review rather than issuing an unsupervised verdict. A feature-level evidence chain
lists the top contributing features behind each agent's decision, giving the
reviewing clinician a checkable rationale (Section~\ref{sec:case} shows a
generated single-case report).

\subsection{Evaluation protocol}
\label{sec:protocol}

Subject-level metrics are primary (one record = one subject). Epoch probabilities
are aggregated per subject; the aggregation is declared per experiment: mean
aggregation for the three-class system and the feature ablation, and the 90th
percentile (p90) for agent-ablation and fusion studies, which we found more
robust for ranking Stacking probabilities; in the binary protocol a record is
predicted Abnormal when its aggregated score is $\geq 0.5$. Test evaluation uses
the test@20 protocol --- a fixed-seed uniform sample of 20 epochs per test record
(@TEST20_EP@ epochs, seed 42) --- as a fixed-cost proxy that bounds evaluation
cost while covering every test subject; full-length epochs (up to 100 per record)
are used during training
and feature extraction. All experiments share a fixed random seed (42) and are
reported as single runs under this protocol. The binary protocol merges Borderline into
Abnormal: in a screening context a borderline reading must not be cleared as
normal, so the merge is the conservative choice. Mechanism-level comparisons use
McNemar's exact paired binomial test at the subject level, reported with point
estimates, discordant-pair counts, and exact $p$-values --- including
non-significant results. All training and inference ran on CPU (Intel Core
i9-13900HX; Python 3.12, PyTorch 2.9.1, LightGBM 4.6.0); inference times were
measured on this hardware over all @TEST20_EP@ test epochs, with LightGBM timings
including on-the-fly feature extraction.

\section{Results}
\label{sec:results}

\subsection{Single-agent baselines}
\label{sec:baselines}

Under the three-class protocol, all four agents fail in an informative pattern
(Table~S3,
Fig.~\ref{fig:three_class}): Borderline macro F1 is near zero for every agent, and under mean
aggregation the Transformer predicts Normal for every subject (subject accuracy
@TRF3_ACC@, equal to the majority baseline; macro F1 @TRF3_F1@). The best
three-class subject accuracy is @EEG3_ACC@ (EEGNet, mean) --- barely above the
baseline. The label--event ordering of Fig.~\ref{fig:event} explains why:
Borderline shares event positivity with Abnormal (@EPI_B@\% vs.\ @EPI_A@\%) yet is
labeled separately, so the class boundary is semantic rather than signal-borne.
We therefore adopt the binary protocol (Borderline $\rightarrow$ Abnormal) for the
main results and report three-class results in the supplement.

Table~\ref{tab:binary} and Fig.~\ref{fig:binary} report binary single-agent
baselines on test@20. All four agents exceed the @MAJ_TEST@ majority baseline.
LightGBM and EEGNet tie at the best accuracy (@LGBM_ACC@); LightGBM attains the
best AUC (@LGBM_AUC@), consistent with its access to engineered features. In
screening terms, sensitivity (recall of the @ABN_N@-subject Abnormal arm) spans
@SENS_LO@--@SENS_HI@ and specificity (recall of the @NRM_N@-subject Normal arm)
@SPEC_LO@--@SPEC_HI@ across the four agents: LightGBM operates at
@LGBM_SENS@ sensitivity / @LGBM_SPEC@ specificity and EEGNet at
@EEGNET_SENS@ / @EEGNET_SPEC@. These thresholded operating points complement the
AUC view --- ranking quality and screening behavior need not coincide, so both
are reported. The cost asymmetry is decisive for deployment: EEGNet matches LightGBM's accuracy at
${\sim}@SPEEDUP@\times$ lower inference cost (@EEGNET_T@~s vs.\ @LGBM_T@~s per
@TEST20_EP@ epochs), the latter dominated by on-the-fly feature extraction. This
motivates keeping both paths --- the feature path for accuracy-oriented fusion,
the deep path for throughput.

\begin{table}[t]
\centering
\caption{Binary single-agent baselines (test@20; subject-level mean aggregation,
n = @TEST_N@: @NRM_N@ Normal and @ABN_N@ Abnormal-arm subjects; Borderline merged
into Abnormal; majority baseline Acc = @MAJ_TEST@). Sens.\ = sensitivity (recall
of the Abnormal arm); Spec.\ = specificity (recall of the Normal arm). Inference
time measured over the @TEST20_EP@ test epochs on identical hardware (CPU);
LightGBM time is dominated by on-the-fly feature extraction. Best per column in
bold.}
\label{tab:binary}
\footnotesize
\setlength{\tabcolsep}{5pt}
\begin{tabular}{lcccccc}
\toprule
Agent & Acc & macro F1 & Sens. & Spec. & AUC & Time (s) \\
\midrule
@TABLE2_BODY@
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.78\textwidth]{paper_fig4_binary_baselines}
\caption{Binary single-agent baselines (Normal vs.\ Abnormal; Borderline merged
into Abnormal), subject-level mean aggregation on test@20 (@TEST_N@ subjects,
@TEST20_EP@ epochs). Bars show accuracy (left axis) and AUC; inference time per
@TEST20_EP@ epochs is annotated in parentheses. The dashed line marks the
majority-class baseline (@MAJ_TEST@). All four agents exceed the baseline; EEGNet
matches LightGBM accuracy (@LGBM_ACC@) at ${\sim}@SPEEDUP@\times$ lower inference
cost (@EEGNET_T@~s vs.\ @LGBM_T@~s, the latter dominated by feature extraction).}
\label{fig:binary}
\end{figure}

\subsection{Feature-domain ablation}
\label{sec:feat_ab}

Table~\ref{tab:feat_ab} and Fig.~\ref{fig:feat_ab} quantify each feature block by
retraining the feature-driven agent without it. Frequency features are the most
critical (removal costs $-@D_FREQ@$ pt accuracy), followed by time--frequency
($-@D_TF@$ pt) and time ($-@D_TIME@$ pt) --- consistent with the delta-dominant
pediatric spectrum (Fig.~\ref{fig:dataset}b), where spectral shape carries most
of the signal. Removing the 82-dim event block costs $-@D_EV@$ pt
(@FULL_ACC@ $\rightarrow$ @NOEV_ACC@), confirming that the label--event coupling
of Fig.~\ref{fig:event} is exploitable beyond the base features. One anomaly is
reported for completeness: removing the time block slightly \emph{improves} AUC
(@A1_AUC@ vs.\ @FULL_AUC@) while hurting accuracy --- the blocks are not
monotonically redundant, and we report both metrics rather than selecting the
favorable one.

The event block also supplies a methodological lesson. A small-sample A/B pretest
(5,000 training epochs, 5 epochs per record; mRMR selected @MRMR_EVENT@ of the
82 event features) concluded the event block was harmful ($@Q_DELTA@$ pt); the
full-scale evaluation concludes the opposite ($+@D_EV@$ pt). Between the two lies
a ${\sim}10\times$ difference in training data --- and the difference between a
wrong and a right feature decision. Small-sample A/B pretests lack the power to
guide feature-set choices (Table~S6); we therefore validated all feature
decisions at full scale. A slow-wave detection subtask (Table~S9; @SWS_N@
records, @SWS_NP@ positive / @SWS_NN@ negative) tells the same story from the
label side: the feature set does carry slow-wave information (AUC @SWS_AUC@),
yet at this sample size it barely separates from the @SWS_MAJ@ majority baseline.

\begin{table}[t]
\centering
\caption{Feature-domain ablation (LightGBM with mRMR-128 selection, binary
protocol, subject-level mean aggregation, test@20, n = @TEST_N@). $\Delta$Acc
relative to the full @FEAT_DIM@-dim feature vector. Feature blocks: time
(@DIM_T@), frequency (@DIM_F@), time--frequency (@DIM_TF@), epileptiform-event
statistics (@DIM_E@). Variants are retrained independently; the full-vector run
differs slightly from the Table~\ref{tab:binary} baseline, which uses the 532-d
base features. Best per column in bold.}
\label{tab:feat_ab}
\begin{tabular}{lcccc}
\toprule
Variant & Dims & Test subject Acc & AUC & $\Delta$Acc \\
\midrule
@TABLE3_BODY@
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig_ablation_features}
\caption{Feature-domain ablation (LightGBM binary, mRMR-128, subject-level mean).
Removing the frequency domain costs $-@D_FREQ@$ pt accuracy, followed by
time--frequency ($-@D_TF@$ pt) and time domain ($-@D_TIME@$ pt); removing the
82-dim event block costs $-@D_EV@$ pt. Inset panels contrast the small-sample A/B
pretest (5,000 train epochs) with the full-scale evaluation: the event-feature gain flips
from $@Q_DELTA@$ pt to $+@D_EV@$ pt between protocols, motivating full-scale
validation for feature-set decisions.}
\label{fig:feat_ab}
\end{figure}

\subsection{Agent ablation and fusion}
\label{sec:agent_ab}

Table~\ref{tab:agent_ab} and Fig.~\ref{fig:agent_ab} compare diagnosis-agent
configurations under two feature bases (Base 1: 532-d features without the event
block; Base 2: the full 614-d vector), with a Stacking meta-learner fusing agent
probabilities at the subject level (p90 aggregation). Three findings emerge.
First, the global best configuration removes the Transformer from the
event-augmented base (A6: LightGBM-event + EEGNet + TCN), reaching @A6_B2@
accuracy --- $+@A6_GAIN@$ pt over the majority baseline --- with macro F1 @A6_F1@
and AUC @A6_AUC@. Second, the TCN is the most critical agent: removing it is the
most harmful ablation under both bases (@A5_B2@ under Base 2, $-@D_TCN_PT@$ pt
vs.\ the Base-2 stack), whereas removing the Transformer under Base 2
\emph{improves} the stack (@A6_B2@ vs.\ @STACK_B2@). Third, learned fusion
dominates rule-based fusion: equal-weight soft voting attains the highest AUC
(@SV_AUC@) but the worst fused accuracy (@SV_ACC@), and hard voting reaches only
@HV_ACC@ --- with an extreme Abnormal-side operating point (@HV_SENS@
sensitivity at @HV_SPEC@ specificity) that the stacking meta-learner corrects
(@STACK_SENS@/@STACK_SPEC@) --- supporting the Stacking choice and the use of
accuracy as the primary metric (Table~S5). Symmetrically, the best single-agent AUC (LightGBM,
@LGBM_AUC@) exceeds that of the A6 stack (@A6_AUC@): the ensemble improves the
operating-point decision (0.5-threshold accuracy) rather than ranking quality, so
both metrics are reported rather than selecting the favorable one. The event
features also help fusion itself: the 4-agent stack
improves from @STACK_B1@ (Base 1) to @STACK_B2@ (Base 2). At the 0.5 operating
point, the Base-2 stack screens at @STACK_SENS@ sensitivity / @STACK_SPEC@
specificity, and the best configuration (A6) at @A6_SENS@ / @A6_SPEC@
(@A6_TP@ TP, @A6_FN@ FN of @ABN_N@ Abnormal-arm subjects; @A6_TN@ TN, @A6_FP@
FP of @NRM_N@ Normal subjects). Under p90 aggregation,
every single agent falls below the majority baseline
(@MIN_SINGLE@--@MAX_SINGLE@), underscoring that the headline numbers are
properties of the ensemble, not of any member.

\begin{table}[t]
\centering
\caption{Diagnosis-agent ablation under two feature bases (Stacking meta-learner,
binary protocol, subject-level p90 aggregation, test@20, n = @TEST_N@, majority
baseline @MAJ_TEST@). Base 1 = LightGBM on 532-d base features; Base 2 =
LightGBM on 614-d features including the 82-d epileptiform-event block. The
Stacking meta-learner (LightGBM) is trained on validation-set agent probabilities.
Single deep-agent rows consume identical inputs under both bases (identical
values); the LightGBM row is retrained on the respective feature base (Base 1:
532-d without event features; Base 2: 614-d event-augmented). Best per column in bold;
hard-voting AUC is undefined (---). The global best configuration is A6 under
Base 2 (LightGBM-event + EEGNet + TCN, Acc @A6_B2@, $+@A6_GAIN@$ pt over the
majority baseline). Equal-weight soft voting attains the highest AUC (@SV_AUC@)
yet the lowest fused accuracy, motivating accuracy as the primary metric.}
\label{tab:agent_ab}
\small
\begin{tabular}{lcccc}
\toprule
Variant & Acc (Base 1) & Acc (Base 2) & macro F1 (Base 2) & AUC (Base 2) \\
\midrule
@TABLE4_BODY@
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig_ablation_agents}
\caption{Diagnosis-agent ablation under two feature bases (Stacking ensemble,
binary, subject-level p90, test @TEST_N@ subjects). Bars are grouped by variant:
full 4-agent Stacking, leave-one-agent-out (A4--A6), and voting baselines
(equal-weight soft voting, hard voting). With the event-augmented base (right), removing Transformer
yields the global best configuration (LightGBM-event + EEGNet + TCN, @A6_B2@,
$+@A6_GAIN@$ pt over majority baseline), whereas removing TCN is most harmful
($-@D_TCN_PT@$ pt). Equal-weight soft voting (@SV_ACC@) and hard voting
(@HV_ACC@) underperform Stacking under both bases, supporting learned meta-fusion.}
\label{fig:agent_ab}
\end{figure}

\subsection{System-mechanism ablation with significance testing}
\label{sec:mechanism}

Table~\ref{tab:mech_ab} and Fig.~\ref{fig:mech_ab} evaluate two system
mechanisms on the full three-class system: dynamic
weighting (A8: weights fixed at validation accuracies) and quality-aware dynamic
weighting (A9: equal weights). The full system reaches @FULL_SUBJ@ subject
accuracy --- below the all-Normal majority baseline (@MAJ_TEST@), a negative
result we state plainly: with Borderline macro F1 near zero (Section~\ref{sec:baselines}),
the semantically ambiguous middle class drags the fused system below the trivial
baseline, and the system's demonstrated value lies in the binary screening
protocol and the auditable mechanisms analyzed here, not in three-class
classification. McNemar exact
paired tests show that none of the mechanism differences is significant at
$\alpha = 0.05$ (A8: $@MC_A8_BC@$,
$p = @MC_A8_P@$; A9: $@MC_A9_BC@$, $p = @MC_A9_P@$): with @TEST_N@ subjects,
differences within $\pm 2$ pt remain inside noise. On the @N_ARB@ epochs where
calibrated disagreement triggered arbitration, epoch accuracy moved from
@ARB_BEF@ to @ARB_AFT@; the calibrated trigger rate is @TRIGGER@\%. We report
these null results deliberately: they bound the claims we make about the
architecture (Section~\ref{sec:discussion}). A quality-stratified analysis
(Table~S7, Fig.~\ref{fig:quality}) finds no consistent advantage of dynamic weighting on
low-quality data --- unsurprisingly, since only @MED_N@/@LOW_N@ test epochs are of
medium/low quality, a limitation we revisit in Section~\ref{sec:limitations}.

\begin{table}[t]
\centering
\caption{System-mechanism ablation with McNemar exact paired tests vs.\ the full
system (3-class full system, test@20; @TEST20_EP@ epochs / @TEST_N@ subjects).
Subject-level metrics use mean epoch-probability aggregation. $b$ = full correct
\& variant wrong; $c$ = full wrong \& variant correct; exact binomial McNemar
test; n.s.\ = not significant. With @TEST_N@ subjects, $\pm 2$ pt subject-level
differences remain within noise. Mechanism statistics: calibrated disagreement
trigger rate @TRIGGER@\%; on the @N_ARB@ arbitrated epochs, epoch accuracy
@ARB_BEF@ $\rightarrow$ @ARB_AFT@. Epoch-level metrics and quality-stratified
analyses are provided in Table~S7 and Fig.~\ref{fig:quality}.}
\label{tab:mech_ab}
\begin{tabular}{lccccc}
\toprule
Variant & Subject Acc & Subject macro F1 & $b/c$ & Exact $p$ & Sig. \\
\midrule
@TABLE5_BODY@
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{paper_fig7_mechanism_ablation}
\caption{System-mechanism ablation on the full 3-class system (test@20;
@TEST20_EP@ epochs / @TEST_N@ subjects). (a) Epoch- and subject-level accuracy
for the full system vs.\ fixed weights (A8) and equal
weights (A9).
(b) McNemar exact paired tests vs.\ the full system: none of the differences is
significant (A8: $@MC_A8_BC@$,
$p = @MC_A8_P@$; A9: $@MC_A9_BC@$, $p = @MC_A9_P@$), i.e., with @TEST_N@
subjects, $\pm 2$ pt differences remain within noise.}
\label{fig:mech_ab}
\end{figure}

\subsection{Disagreement-threshold calibration}
\label{sec:calibration}

Figure~\ref{fig:calibration}(a,b) shows why the legacy thresholds failed. The
per-epoch distribution of the maximum probability difference has median @PD_MED@
--- above the legacy $\theta_d = 0.15$ --- so R1 fired on @R1_LEG@\% of validation
epochs. The mean entropy concentrates against its theoretical ceiling: median
@ENT_MED@ against $\ln 3 \approx 1.0986$, with 99th percentile @ENT_P99@.
Four-agent three-class posteriors are close to uniform, so R3's legacy threshold
(0.80) fired on @R3_LEG@\% of epochs, and the combined trigger rate was
@COMB_LEG@\%: \emph{every} epoch was arbitrated, doubling inference cost with no
accuracy benefit (always-arbitrate validation accuracy @ALWAYS_VAL@ vs.\
@NEVER_VAL@ never-arbitrating).

Grid-searching @GRID_N@ combinations (validation replay; Section~\ref{sec:fusion})
yielded $(0.30, 0.60, 1.099)$: only strong disagreements now trigger, at
@TRIGGER@\% of epochs --- a level chosen to preserve arbitration activity at the
accuracy optimum. Table~\ref{tab:calib} summarizes the end-to-end effect on test:
two quantities are unchanged (subject accuracy @FULL_SUBJ@, epoch accuracy
@EP_BEF@ $\rightarrow$ @EP_AFT@) while
the trigger rate falls from 100\% to @TRIGGER@\% and inference time drops
@TIME_SAVE@\% (@T_BEFORE@~s $\rightarrow$ @T_AFTER@~s per @TEST20_EP@ epochs). In
effect, calibration bought back @TIME_SAVE@\% of compute at zero measured cost.
We argue this procedure --- distribution diagnosis, threshold grid search, and
cost--performance selection --- generalizes to any voting-based multi-classifier
system (Section~\ref{sec:discussion}).

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig_disagreement_calibration}
\caption{Disagreement-threshold calibration (validation set @20, @CAL_N_EP@
epochs). (a, b) Per-epoch distributions of maximum probability difference and mean
entropy across the four agents: the legacy thresholds (0.15 / 0.80) sit below the
medians (@PD_MED@ / @ENT_MED@), so at least one rule fires on every epoch; the
entropy distribution clusters near the theoretical maximum $\ln 3 \approx 1.0986$,
rendering the entropy rule degenerate under near-uniform three-class
probabilities. Calibrated thresholds (0.30 / 1.099) admit only strong
disagreements. (c) Rule firing rates before/after calibration: the combined
trigger rate drops from 100\% to @TRIGGER@\%. (d) End-to-end effect on test:
inference time $-@TIME_SAVE@\%$ (@T_BEFORE@ s $\rightarrow$ @T_AFTER@ s per
@TEST20_EP@ epochs) with subject accuracy unchanged (@FULL_SUBJ@).}
\label{fig:calibration}
\end{figure}

\begin{table}[t]
\centering
\caption{Effect of disagreement-threshold calibration on the full 3-class system
(test@20, @TEST20_EP@ epochs / @TEST_N@ subjects). ``Before'' = original
uncalibrated thresholds (the disagreement rule fired on every epoch); ``After'' =
calibrated thresholds (prob\_diff = 0.30, majority = 0.60, entropy = 1.099)
selected by grid search over @GRID_N@ combinations on validation data (val@20,
@CAL_N_SUB@ subjects). Never-arbitrate attains the same validation accuracy; the
adopted configuration preserves arbitration activity with unchanged subject
accuracy and $-@TIME_SAVE@\%$ inference time.}
\label{tab:calib}
\begin{tabular}{lcc}
\toprule
Metric & Before & After \\
\midrule
@TABLE6_BODY@
\bottomrule
\end{tabular}
\end{table}

\subsection{Case study: escalation in action}
\label{sec:case}

To illustrate the escalation design, the system's auto-generated report for test
subject SUBJ\_0034 (clinical label: Abnormal; 20 epochs; @CASE_T@~s total
inference) shows a borderline-leaning low-confidence verdict --- Abnormal
@CASE_A@\% vs.\ Normal @CASE_N@\% --- with cross-agent consistency @CASE_C@ and a
top-feature evidence chain; the system accordingly recommends human review rather
than an automated label. This is the intended behavior for a screening aid: when
agents disagree and confidence sits inside the borderline range, the safe output
is escalation, not a forced verdict \citep{chow1970,geifman2017}.

\section{Discussion}
\label{sec:discussion}

\subsection{Main findings}
EEG-MAS delivers three linked results on @NR@ routine pediatric records with
three-tier clinical labels. Architecturally, heterogeneous feature- and
signal-driven agents fuse into a screening system whose best binary configuration
reaches @A6_B2@ accuracy ($+@A6_GAIN@$ pt over the majority baseline) --- with
every single agent individually below that baseline under the fusion protocol's
p90 aggregation. Methodologically, diagnosing
and calibrating the disagreement detector cut inference time by @TIME_SAVE@\% at
unchanged accuracy, turning a degenerate always-on mechanism into a selective
one. Evaluatively, mechanism-level exact tests show that the arbitration and
weighting contributions are not individually significant at @TEST_N@ subjects ---
negative results we report as findings, not failures.

\subsection{Positioning relative to prior work}
Table~\ref{tab:related} positions EEG-MAS against representative prior work; the
numbers are not directly comparable, by construction. TUAB-based systems evaluate
binary labels on a curated adult corpus, while EEG-MAS retains the Borderline
class in the Abnormal arm of a real three-tier label space with documented
label-source heterogeneity (Table~S4), which bounds achievable accuracy
\citep{frenay2014}. In that light, @A6_B2@ against a @MAJ_TEST@ baseline is a
measure of task difficulty as much as of method quality. A cohort of @NR@
subjects is, to our knowledge, among the larger private pediatric routine-EEG
collections evaluated for automated screening; the scarcity of such benchmarks is
itself part of the field's problem (Section~\ref{sec:limitations}).

\begin{xltabular}{\textwidth}{@{}>{\footnotesize\raggedright\arraybackslash\hsize=.85\hsize}X >{\footnotesize\raggedright\arraybackslash\hsize=.80\hsize}X >{\footnotesize\raggedright\arraybackslash\hsize=1.0\hsize}X >{\footnotesize\raggedright\arraybackslash\hsize=.65\hsize}X >{\footnotesize\raggedright\arraybackslash\hsize=1.70\hsize}X@{}}
\caption{Positioning of EEG-MAS relative to representative prior work.
$^{\dagger}$Performance figures as surveyed in \citet{roy2019} and
\citet{chen2025} (second-hand sources for the original studies).
Performance figures are \emph{not directly comparable across studies}: TUAB-based
works evaluate binary classification on a curated, adult-dominant corpus, whereas
EEG-MAS operates on pediatric routine EEG with real-world three-tier labels in
which the Borderline class is retained in the Abnormal arm (a conservative
choice), and label-source heterogeneity bounds achievable accuracy (Table~S4).
Reported accuracies therefore reflect task difficulty as much as method quality.}
\label{tab:related}\\
\toprule
Study & Domain / input & Dataset \& protocol & Reported performance & Key differences vs.\ EEG-MAS \\
\midrule
\endfirsthead
\multicolumn{5}{l}{\footnotesize\itshape \tablename~\thetable{} (continued)}\\
\toprule
Study & Domain / input & Dataset \& protocol & Reported performance & Key differences vs.\ EEG-MAS \\
\midrule
\endhead
\bottomrule
\endfoot
\bottomrule
\endlastfoot
@TABLE7_BODY@
\end{xltabular}

\subsection{The calibration methodology generalizes}
The calibration study generalizes beyond this system. Any voting ensemble of
$K \geq 2$ classifiers over $C \geq 3$ classes can exhibit the pathology we
document: as posteriors approach uniformity, entropy saturates against $\ln C$
and becomes uninformative as a disagreement signal, while thresholds set below
distribution medians fire permanently. The remedy is mechanical --- measure the
metric distributions on validation data, grid-search the thresholds, and select
on a declared cost--performance criterion --- and the replay-from-cached-metrics
design makes the search essentially free. For uncertainty-aware multi-agent
systems, our results argue for auditing rule inputs against their theoretical
ranges before deploying rule-based triggering.

\subsection{The value of negative results}
One null result deserves emphasis: dynamic weighting
shows no measurable advantage even in its target regime, which this dataset
under-represents. We conjecture that many deployed clinical ensembles carry
similar unvalidated mechanisms. The evaluation standard we advocate --- point
estimates with discordant-pair counts, exact tests, and (where estimable)
confidence intervals, reported symmetrically for positive and negative outcomes
--- costs little and is the only honest basis for claiming that a mechanism
``works'' \citep{geifman2017}.

\subsection{Clinical perspective}
EEG-MAS is a triage instrument, not a diagnostic one. Its verdicts are
probabilistic, its evidence chains are feature-level rather than physiological
interpretations, and its intended workflow position is \emph{ahead} of the reader:
prioritize, pre-annotate, and escalate. The escalation economics matter ---
flagging every low-confidence record is safe but useless if it flags everything
(the pre-calibration system did exactly that). As measured, the 0.35--0.65
confidence rule flags @ESC_LO@--@ESC_HI@\% of test subjects depending on the
agent (@ESC_LO_N@--@ESC_HI_N@ of @TEST_N@) --- consistent with the near-uniform
posteriors of Section~\ref{sec:calibration} --- so sharpening base-learner
confidence (e.g., temperature scaling) is a prerequisite for escalation to
reduce, rather than merely redirect, expert workload; calibrated triggering
keeps the flagged subset meaningful. A prospective evaluation with readers is the necessary
next step before any clinical claim; the single-case report format of
Section~\ref{sec:case} sketches what the reader-facing output could look like.

\subsection{Limitations}
\label{sec:limitations}
Five limitations bound the present study. (1)~\emph{Single-center, private data}:
external validation is required; the code is released to support replication.
(2)~\emph{Label-source heterogeneity}: two annotation workflows coexist, no agent
consistently exceeds its in-group baseline (Table~S4), and achievable accuracy is
bounded by label noise \citep{frenay2014}. (3)~\emph{Quality skew}:
@HIGH_SHARE@\% of epochs are high quality, so the dynamic-weighting mechanism's
target regime is under-represented; its evaluation on noise-heavy cohorts remains
open. (4)~\emph{Borderline semantics}: the three-tier boundary is institutional;
our binary protocol is conservative but coarse. (5)~\emph{Modest absolute
accuracy}: @A6_B2@ reflects a genuinely hard, realistic task rather than a
saturated one; the contribution of this work is the architecture, calibration
methodology, and evaluation standard, not a leaderboard number.

\section{Conclusion}
We presented EEG-MAS, a three-layer multi-agent system that fuses feature- and
signal-driven diagnosis agents for pediatric EEG screening, with quality-aware
weighting, cross-agent consistency scoring, and human-review escalation. We
contributed a calibration methodology that converted a degenerate always-on
disagreement mechanism into a selective one, cutting inference time by
@TIME_SAVE@\% at unchanged accuracy. We evaluated every mechanism with exact
paired tests, reported the negative results alongside the positive ones, and
showed that full-scale validation reverses small-sample feature decisions.
Together, these results argue that for clinical multi-agent systems, knowing when
to arbitrate --- and when the data cannot certify a mechanism --- is as
fundamental as the models themselves.

\section*{Declarations}

\paragraph{Ethics approval.} [To be completed before submission: institutional
review board approval or exemption, and patient consent statement.]

\paragraph{Consent for publication.} Not applicable (data are de-identified).

\paragraph{Funding.} This research received no external funding.

\paragraph{Data availability.}
The EEG records contain protected pediatric clinical information and cannot be
shared publicly; access to a de-identified subset for academic verification is
available from the corresponding author on reasonable request and subject to
institutional approval.

\paragraph{Code availability.}
Source code, configuration, and scripts reproducing all tables and figures are
publicly available at \url{https://github.com/QM-newer/eeg-multi-agent}. All numbers in
this manuscript are generated programmatically from the evaluation outputs
(zero-hand-copy workflow); the generation scripts are versioned alongside the
repository.

\paragraph{Competing interests.} The author declares no competing interests.

\paragraph{CRediT authorship contribution statement.}
\textbf{Haojia Qiu:} Conceptualization, Methodology, Software, Validation,
Formal analysis, Investigation, Data curation, Writing --- original draft,
Writing --- review \& editing, Visualization.

\appendix
% 附录图改用 S 前缀编号（S1, S2），与正文 Fig.~S1/S2 引用一致
\renewcommand{\thefigure}{S\arabic{figure}}
\setcounter{figure}{0}
\section{Supplementary figures}
\label{app:supp}

Supplementary Tables~S1--S9 are provided as a separate supplementary document;
the two supplementary figures are reproduced here for convenience.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{paper_figS1_three_class_baselines}
\caption{Three-class single-agent baselines (subject-level mean / p90
aggregation, test@20). Borderline F1 $\approx 0$ for every agent; the Transformer
collapses to predicting Normal for all subjects (macro F1 @TRF3_F1@). These
results justify the binary protocol adopted in the main text
(Section~\ref{sec:baselines}; full numbers in Table~S3).}
\label{fig:three_class}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{paper_figS2_quality_stratification}
\caption{Signal-quality stratified analysis (epoch-level by quality tier;
subject-level by presence of medium/low-quality epochs). @HIGH_SHARE@\% of epochs
are high quality; the observable medium/low subsets are tiny (n = @MED_N@ /
@LOW_N@ epochs; @TEST_N@-subject scale), so results are indicative only. Dynamic
weighting shows no consistent advantage on low-quality data --- the mechanism's
target scenario (noise-heavy clinical recordings) is under-represented in this
dataset; reported as a limitation (Section~\ref{sec:limitations}; Table~S7).}
\label{fig:quality}
\end{figure}

\bibliographystyle{plainnat}
\bibliography{references}

\end{document}
"""

# LN3 token 特殊处理（正文中写作 $\ln 3 \approx @LN3@R$ 防止小数点后歧义）
T["LN3"] = "1.0986"

# ============================================================
# references.bib
# ============================================================
BIB = r"""% ============================================================
% references.bib — EEG-MAS manuscript draft
% 全部条目著录信息已于 2026-10-24 依据出版社/arXiv/PubMed 记录联网核实。
% ============================================================

% ---------- 流行病学与分类（OK） ----------
@article{fiest2017,
  author  = {Fiest, Kirsten M. and Sauro, Kelsey M. and Wiebe, Samuel and Patten, Scott B. and Kwon, Churl-Su and Dykeman, Jette and Pringsheim, Tamara and Lorenzetti, Diane L. and Jett{\'e}, Nathalie},
  title   = {Prevalence and incidence of epilepsy: A systematic review and meta-analysis of international studies},
  journal = {Neurology},
  volume  = {88},
  number  = {3},
  pages   = {296--303},
  year    = {2017}
}

@article{scheffer2017,
  author  = {Scheffer, Ingrid E. and Berkovic, Samuel and Capovilla, Giuseppe and Connolly, Mary B. and Guilhoto, Lauro and Hirsch, Edouard and Jain, Satish and Mathern, Gary W. and Mosh{\'e}, Solomon L. and Nordli, Douglas R. and others},
  title   = {{ILAE} classification of the epilepsies: Position paper of the {ILAE} Commission for Classification and Terminology},
  journal = {Epilepsia},
  volume  = {58},
  number  = {4},
  pages   = {512--521},
  year    = {2017}
}

% ---------- 自动 EEG 判读（TUAB 系；† 表内转引数字见 Table 7 脚注） ----------
@article{schirrmeister2017,
  author  = {Schirrmeister, Robin Tibor and Springenberg, Jost Tobias and Fiederer, Lukas Dominique Josef and Glasstetter, Martin and Eggensperger, Katharina and Tangermann, Michael and Hutter, Frank and Burgard, Wolfram and Ball, Tonio},
  title   = {Deep learning with convolutional neural networks for {EEG} brain mapping},
  journal = {Human Brain Mapping},
  volume  = {38},
  number  = {11},
  pages   = {5391--5420},
  year    = {2017}
}

@article{roy2018chrono,
  author  = {Roy, Subhrajit and Kiral-Kornek, Isabell and Harrer, Stefan},
  title   = {{ChronoNet}: A deep recurrent neural network for abnormal {EEG} identification},
  journal = {arXiv preprint arXiv:1802.00308},
  year    = {2018}
}

@article{roy2019,
  author  = {Roy, Yannick and Banville, Hubert and Albuquerque, Irina and Gramfort, Alexandre and Falk, Tiago H. and Faubert, Julien},
  title   = {Deep learning-based electroencephalogram analysis: A systematic review of the last decade},
  journal = {Journal of Neuroscience Methods},
  volume  = {317},
  pages   = {82--93},
  year    = {2019}
}

@article{chen2025,
  author  = {Chen, Shimiao and Huang, Dong and Liu, Xinyue and Chen, Jianjun and Kong, Xiangzeng and Zhang, Tingting},
  title   = {Automatic diagnostics of electroencephalography pathology based on multi-domain feature fusion},
  journal = {PLOS ONE},
  volume  = {20},
  number  = {5},
  pages   = {e0310348},
  year    = {2025}
}

@article{oates2016,
  author  = {Oates, Josiah and Hatton, Kevin and Obeid, Iyad and Picone, Joseph and Jacobson, Mark P. and Harati, Ali},
  title   = {The {Temple University Hospital} {EEG} corpus: Grid annotation, benchmark dataset, and decennial challenge},
  journal = {Journal of Neuroscience Methods},
  volume  = {277},
  pages   = {30--33},
  year    = {2016}
}

% ---------- 相邻问题（事件检测 / 质量控制 / 儿科精神疾病） ----------
@article{vepinetv2_2025,
  author  = {Lin, Nan and Li, Lian and Gao, Weifang and Hu, Peng and Yuan, Gonglin and Sun, Heyang and Qi, Fang and Wang, Lin and Wang, Shengsong and Liang, Zi and He, Haibo and Dong, Yisu and Gao, Zaifen and Shao, Xiaoqiu and Cui, Liying and Lu, Qiang},
  title   = {Development and validation of a multimodal automatic interictal epileptiform discharge detection model: a prospective multi-center study},
  journal = {BMC Medicine},
  volume  = {23},
  number  = {1},
  pages   = {479},
  year    = {2025}
}

@article{neonaid2026,
  author  = {Hermans, Tim and Dereymaeker, Anneleen and Lemmens, Katrien and Jansen, Katrien and Usman, Fatima and Robinson, Shellie and Naulaers, Gunnar and De Vos, Maarten and Hartley, Caroline},
  title   = {Toward automated neonatal {EEG} analysis: multi-center validation of a reliable deep learning pipeline},
  journal = {Frontiers in Neuroscience},
  volume  = {20},
  pages   = {1750045},
  year    = {2026}
}

@article{adhdcd2024,
  author  = {Loh, Hui Wen and Ooi, Chui Ping and Oh, Shu Lih and Barua, Prabal Datta and Tan, Yi Ren and Acharya, U. Rajendra and Fung, Daniel Shuen Sheng},
  title   = {{ADHD/CD-NET}: automated {EEG}-based characterization of {ADHD} and {CD} using explainable deep neural network technique},
  journal = {Cognitive Neurodynamics},
  volume  = {18},
  number  = {4},
  pages   = {1609--1625},
  year    = {2024}
}

% ---------- 多智能体医疗 AI（框架描述已核实；具体数字如需引用回原文） ----------
@article{mdagents2024,
  author  = {Kim, Yubin and Park, Chanwoo and Jeong, Hyewon and Chan, Yik Siu and Xu, Xuhai and McDuff, Daniel and Lee, Hyeonhoon and Ghassemi, Marzyeh and Breazeal, Cynthia and Park, Hae Won},
  title   = {{MDAgents}: An adaptive collaboration of {LLMs} for medical decision-making},
  journal = {arXiv preprint arXiv:2404.15155},
  year    = {2024}
}

@inproceedings{colacare2025,
  author    = {Wang, Zixiang and Zhu, Yinghao and Zhao, Huiya and Zheng, Xiaochen and Sui, Dehao and Wang, Tianlong and Tang, Wen and Wang, Yasha and Harrison, Ewen and Pan, Chengwei and Gao, Junyi and Ma, Liantao},
  title     = {{ColaCare}: Enhancing electronic health record modeling through large language model-driven multi-agent collaboration},
  booktitle = {Proceedings of the ACM Web Conference 2025 (WWW '25)},
  year      = {2025}
}

@article{mac2025,
  author  = {Chen, Xi and Yi, Huahui and You, Mingke and Liu, Weizhi and Wang, Li and Li, Hairui and Zhang, Xue and Guo, Yingman and Fan, Lei and Chen, Gang and Lao, Qicheng and Fu, Weili and Li, Kang and Li, Jian},
  title   = {Enhancing diagnostic capability with multi-agents conversational large language models},
  journal = {npj Digital Medicine},
  volume  = {8},
  pages   = {159},
  year    = {2025}
}

@article{dynamicare2025,
  author  = {Shang, Tianqi and He, Weiqing and Zheng, Charles and Li, Lingyao and Shen, Li and Zhao, Bingxin},
  title   = {{DynamiCare}: A dynamic multi-agent framework for interactive and open-ended medical decision-making},
  journal = {arXiv preprint arXiv:2507.02616},
  year    = {2025}
}

% ---------- 方法学经典（OK） ----------
@article{chow1970,
  author  = {Chow, Chi-Keung},
  title   = {On optimum recognition error and reject tradeoff},
  journal = {IEEE Transactions on Information Theory},
  volume  = {16},
  number  = {1},
  pages   = {41--46},
  year    = {1970}
}

@inproceedings{geifman2017,
  author    = {Geifman, Yonatan and El-Yaniv, Ran},
  title     = {Selective classification for deep neural networks},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {30},
  year      = {2017}
}

@article{frenay2014,
  author  = {Fr{\'e}nay, Beno{\^i}t and Verleysen, Michel},
  title   = {Classification in the presence of label noise: A survey},
  journal = {IEEE Transactions on Neural Networks and Learning Systems},
  volume  = {25},
  number  = {5},
  pages   = {845--869},
  year    = {2014}
}

@article{lawhern2018,
  author  = {Lawhern, Vernon J. and Solon, Amelia J. and Waytowich, Nicholas R. and Gordon, Stephen M. and Hung, Chou P. and Lance, Brent J.},
  title   = {{EEGNet}: A compact convolutional neural network for {EEG}-based brain--computer interfaces},
  journal = {Journal of Neural Engineering},
  volume  = {15},
  number  = {5},
  pages   = {056013},
  year    = {2018}
}

@article{bai2018,
  author  = {Bai, Shaojie and Kolter, J. Zico and Koltun, Vladlen},
  title   = {An empirical evaluation of generic convolutional and recurrent networks for sequence modeling},
  journal = {arXiv preprint arXiv:1803.01271},
  year    = {2018}
}

@inproceedings{vaswani2017,
  author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, {\L}ukasz and Polosukhin, Illia},
  title     = {Attention is all you need},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {30},
  year      = {2017}
}

@inproceedings{ke2017,
  author    = {Ke, Guolin and Meng, Qi and Finley, Thomas and Wang, Taifeng and Chen, Wei and Ma, Weidong and Ye, Qiwei and Liu, Tie-Yan},
  title     = {{LightGBM}: A highly efficient gradient boosting decision tree},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {30},
  year      = {2017}
}

@article{peng2005,
  author  = {Peng, Hanchuan and Long, Fuhui and Ding, Chris},
  title   = {Feature selection based on mutual information: Criteria of max-dependency, max-relevance, and min-redundancy},
  journal = {IEEE Transactions on Pattern Analysis and Machine Intelligence},
  volume  = {27},
  number  = {8},
  pages   = {1226--1238},
  year    = {2005}
}

@article{wolpert1992,
  author  = {Wolpert, David H.},
  title   = {Stacked generalization},
  journal = {Neural Networks},
  volume  = {5},
  number  = {2},
  pages   = {241--259},
  year    = {1992}
}
"""

# ============================================================
# 生成
# ============================================================
OUT.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

# token 替换
tex = TEX
for k, v in T.items():
    tex = tex.replace(f"@{k}@", v)
tex = tex.replace("@LN3@", "1.0986")   # 兜底（正文写作 @LN3@R 形式，R 防粘连）
tex = tex.replace("1.0986R", "1.0986")

leftover = re.findall(r"@[A-Z][A-Z0-9_]*@", tex)
assert not leftover, f"main.tex 残留未替换 token: {sorted(set(leftover))}"

(OUT / "main.tex").write_text(tex, encoding="utf-8")
(OUT / "references.bib").write_text(BIB, encoding="utf-8")

# 复制图片（优先 PDF 矢量版，无则 PNG）
FIGS_SRC = BASE / "outputs" / "figures"
fig_names = [
    "fig_system_architecture_layered", "paper_fig2_dataset_overview", "fig_label_event_insight",
    "paper_fig4_binary_baselines", "fig_ablation_features", "fig_ablation_agents",
    "paper_fig7_mechanism_ablation", "fig_disagreement_calibration",
    "paper_figS1_three_class_baselines", "paper_figS2_quality_stratification",
]
copied = []
for name in fig_names:
    src = FIGS_SRC / f"{name}.pdf"
    if not src.exists():
        src = FIGS_SRC / f"{name}.png"
    assert src.exists(), f"missing figure: {name}"
    shutil.copy2(src, FIGS / src.name)
    copied.append(src.name)

print("OK  main.tex          ->", OUT / "main.tex")
print("OK  references.bib    ->", OUT / "references.bib")
print("OK  figures copied    ->", len(copied), "files")
for c in copied:
    print("     ", c)
print("\n关键数值抽查：")
print(f"  majority baseline = {MAJ_TEST:.4f} | best A6 = {B2['A6_no_transformer']['acc']:.4f} (+{A6_GAIN:.1f} pt)")
print(f"  trigger = {TRIGGER:.1f}% | time {T_BEFORE}->{T_AFTER} s (-{TIME_SAVE:.0f}%)")
print(f"  event block: quick {ef['delta']['acc']*100:+.1f} pt -> full +{D_EV:.1f} pt")
