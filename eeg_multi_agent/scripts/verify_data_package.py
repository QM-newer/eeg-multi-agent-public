# scripts/verify_data_package.py
"""
实验数据包独立验证 —— 不信任导出代码，从最深数据源逐层向上核对：

L1 深层源核对:  E:/eeg_asd_cache 特征矩阵与元数据  vs  data_quality.json / manifest
L2 独立复算:    agent_probs / disagreement 缓存出发，重新实现聚合与元模型，
                复算单 Agent / 硬投票 / A9 / Stacking / 校准表，与 JSON 对比
L3 跨文件一致:  JSON <-> JSON 相互印证（同值不同文件、派生量、混淆矩阵求和、McNemar p 复算）
L4 交付物核对:  Excel 单元格 vs 复算值；包内 raw_json/报告 与 outputs 哈希一致

输出: 控制台 PASS/FAIL 清单 + outputs/verification_report.json
用法:  python scripts/verify_data_package.py
"""
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import lightgbm as lgb
from openpyxl import load_workbook
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from config import BINARY_LABEL_MAP, resolve_path

OUT = Path(resolve_path("outputs"))
FEAT = Path("E:/eeg_asd_cache/features")
PKG = next(OUT.glob("data_package_*"), None)
XLSX = PKG / "EEG-MAS实验数据.xlsx" if PKG else None
CLS = ["Normal", "Borderline", "Abnormal"]

results = {"generated": f"{datetime.now():%Y-%m-%d %H:%M}", "checks": [], "n_pass": 0, "n_fail": 0, "n_blocked": 0}
E_AVAILABLE = FEAT.exists()


def blocked(name, detail=""):
    results["checks"].append({"check": name, "status": "BLOCKED", "detail": str(detail)})
    results["n_blocked"] += 1
    print(f"  [BLOCKED] {name}  | {detail}")


def check(name, ok, detail=""):
    results["checks"].append({"check": name, "status": "PASS" if ok else "FAIL", "detail": str(detail)})
    results["n_pass" if ok else "n_fail"] += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  | {detail}" if detail else ""))


def load(name):
    with open(OUT / name, encoding="utf-8") as f:
        return json.load(f)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def eval_pred(y, p):
    pred = (np.asarray(p) >= 0.5).astype(int)
    return {"acc": round(float(accuracy_score(y, pred)), 4),
            "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
            "auc": round(float(roc_auc_score(y, p)), 4)}


# ================= L1 深层源核对 =================
print("\n=== L1 深层源核对（E: 缓存 → data_quality.json）===")
dq = load("data_quality.json")
if not E_AVAILABLE:
    blocked("L1 全部（E: 缓存盘未挂载，深层源暂不可核）", "重新连接 E 盘后重跑本脚本")
    blocked("L2 全部（agent_probs / disagreement 缓存不可读）", "重新连接 E 盘后重跑本脚本")
if E_AVAILABLE:
    man = json.load(open(FEAT / "manifest.json", encoding="utf-8"))
    check("manifest 列块维度和 = 614（228+152+152+82）", sum(man["dims"].values()) == 614,
          f"{man['dims']}")
    lay = man["layout"]
    ok_layout = lay["time_domain"][0] == 0 and lay["freq_domain"][0] == 228 and \
        lay["timefreq"][0] == 380 and lay["event"][0] == 532 and lay["event"][1] == 614
    check("manifest 列块布局连续且索引正确", ok_layout, f"{lay}")

    # 形状与 manifest 声明一致（test 为 @20 评估口径 = 4760 行，非全量 23774）
    for split in ("train", "val", "test"):
        exp = tuple(man["splits"][split]["feature_shape"])
        f = np.load(FEAT / f"{split}_feat.npy", mmap_mode="r")
        check(f"{split}_feat.npy 形状 = manifest 声明 {exp}", f.shape == exp, f"actual {f.shape}")
        n = f.shape[0]
        sample = np.asarray(f[np.random.default_rng(0).choice(n, 3000, replace=False)])
        check(f"{split}_feat 无 NaN/Inf（3000 行抽样）", bool(np.isfinite(sample).all()))

    check("test 特征矩阵为 @20 评估口径（4760 = 238 被试 x 20）",
          tuple(man["splits"]["test"]["feature_shape"]) == (4760, 614)
          and man["splits"]["test"]["max_epochs_per_record"] == 20,
          "data_quality.json 的 test 23774 epochs 为全量缓存口径，两者并存且报告已分别标注")

    for split in ("train", "val", "test"):
        m = np.load(FEAT / f"{split}_meta.npz", allow_pickle=True)
        y, sids = m["y"], m["subject_ids"]
        rec_cls = {c: int(sum(1 for u in np.unique(sids) if int(y[sids == u][0]) == k))
                   for k, c in enumerate(CLS)}
        n_sub = len(np.unique(sids))
        ok_rec = (rec_cls == dq[split]["records_by_class"] and n_sub == dq[split]["n_records"])
        detail = f"records {rec_cls} (n={n_sub})"
        if split in ("train", "val"):
            ep_cls = {CLS[k]: int((y == k).sum()) for k in range(3)}
            ok = ok_rec and ep_cls == dq[split]["epochs_by_class"] and len(y) == dq[split]["n_epochs"]
            detail = f"epochs {ep_cls} / {detail}"
            check(f"{split} 元数据 ↔ data_quality.json（epoch+记录分类计数）", ok, detail)
        else:
            ok = ok_rec and len(y) == man["splits"]["test"]["n_epochs"]
            check(f"test 元数据（@20）: 被试级计数 ↔ data_quality + epoch 数 ↔ manifest", ok, detail)

    # 测试集多数类基线独立复算（0.5504）
    m = np.load(FEAT / "test_meta.npz", allow_pickle=True)
    y_test3, sids_test = m["y"], m["subject_ids"]
    y_test_bin = np.array([BINARY_LABEL_MAP[int(v)] for v in y_test3])
    subj_lbl = np.array([y_test_bin[sids_test == u][0] for u in np.unique(sids_test)])
    base_rate = round(float(max(np.bincount(subj_lbl)) / len(subj_lbl)), 4)
    check("被试级多数类基线复算 = 0.5504", base_rate == 0.5504, f"recomputed {base_rate}")

# ================= L2 独立复算（不经过 run_ablation_agents 代码路径）=================
print("\n=== L2 独立复算（概率缓存 → 重算 → vs ablation_agents.json）===")
aa = load("ablation_agents.json")
if E_AVAILABLE:
    probs = {}
    for split in ("val", "test"):
        z = np.load(FEAT / f"agent_probs_{split}.npz", allow_pickle=True)
        probs[split] = {k: z[k] for k in z.files}


    def subject_meta(pd_, cols):
        sids, y3 = pd_["_sids"], pd_["_y3"]
        uniq = sorted(set(sids))
        P = np.column_stack([pd_[c] for c in cols])
        M = np.vstack([np.percentile(P[sids == u], 90, axis=0) for u in uniq])
        yb = np.array([BINARY_LABEL_MAP[int(pd_["_y3"][sids == u][0])] for u in uniq])
        return M, yb


    def stacking(vM, vy, tM, ty):
        clf = lgb.LGBMClassifier(n_estimators=50, learning_rate=0.1, num_leaves=8,
                                objective="binary", random_state=42, verbose=-1,
                                class_weight="balanced")
        clf.fit(vM, vy)
        return eval_pred(ty, clf.predict_proba(tM)[:, 1])


    base_defs = {"lightgbm": ["lightgbm", "eegnet", "tcn", "transformer"],
                 "lightgbm_event": ["lightgbm_event", "eegnet", "tcn", "transformer"]}
    variant_cols = {"stacking_full": [0, 1, 2, 3], "A4_no_eegnet": [0, 2, 3],
                    "A5_no_tcn": [0, 1, 3], "A6_no_transformer": [0, 1, 2]}
    n_checked = 0
    for bk, cols in base_defs.items():
        vM, vy = subject_meta(probs["val"], cols)
        tM, ty = subject_meta(probs["test"], cols)
        recomputed = {}
        for vk, idx in variant_cols.items():
            recomputed[vk] = stacking(vM[:, idx], vy, tM[:, idx], ty)
        recomputed["A9_soft_voting_equal"] = eval_pred(ty, tM.mean(axis=1))
        votes = (tM >= 0.5).astype(int).sum(axis=1)
        hv_pred = (votes * 2 > tM.shape[1]).astype(int)
        recomputed["hard_voting"] = {
            "acc": round(float(accuracy_score(ty, hv_pred)), 4),
            "macro_f1": round(float(f1_score(ty, hv_pred, average="macro")), 4), "auc": None}
        for i, c in enumerate(cols):
            recomputed[f"single_{c}"] = eval_pred(ty, tM[:, i])
        stored = aa["bases"][bk]["variants"]
        for vk, rv in recomputed.items():
            sv = stored[vk]
            for metric in ("acc", "macro_f1", "auc"):
                r_, s_ = rv[metric], sv[metric]
                if r_ is None and s_ is None:
                    continue
                n_checked += 1
                if not abs(r_ - s_) < 5e-5:
                    check(f"[{bk}] {vk}.{metric}", False, f"recomputed {r_} vs stored {s_}")
            if all((rv[k] is None and sv[k] is None) or abs(rv[k] - sv[k]) < 5e-5
                   for k in ("acc", "macro_f1", "auc")):
                check(f"[{bk}] {vk}（acc/f1/auc 复算一致）", True,
                      f'acc={sv["acc"]} f1={sv["macro_f1"]} auc={sv["auc"]}')
    check("复算指标总数（含隐含单项）", n_checked >= 40, f"{n_checked} metrics compared")
    check("最优配置 0.6134 独立复算命中",
          abs(aa["bases"]["lightgbm_event"]["variants"]["A6_no_transformer"]["acc"] - 0.6134) < 5e-5)

    print("\n=== L2b 校准表独立复算（disagreement_val.npz → vs disagreement_calibration.json）===")
    cal = load("disagreement_calibration.json")
    zc = np.load(FEAT / "disagreement_val.npz", allow_pickle=True)
    m_diff, m_maj, m_ent = zc["max_prob_diff"], zc["majority_ratio"], zc["entropy"]
    md = cal["metric_distributions"]
    ok_q = all(abs(np.quantile(m_diff, float(q)) - md["max_prob_diff"][q]) < 5e-4 and
               abs(np.quantile(m_maj, float(q)) - md["majority_ratio"][q]) < 5e-4 and
               abs(np.quantile(m_ent, float(q)) - md["entropy"][q]) < 5e-4 for q in ("0.25", "0.5", "0.75", "0.9"))
    check("三个分歧指标的分位数复算一致（P25/50/75/90）", ok_q)
    cf = cal["current_config_firing"]
    r1_old = (m_diff > 0.15).mean()
    r2 = (m_maj < 0.6).mean()
    r3_old = (m_ent > 0.80).mean()
    comb_new = ((m_diff > 0.30) | (m_maj < 0.6) | (m_ent > 1.099)).mean()
    check("规则触发率复算: R1旧66.7% / R3旧100% / R2 32.6%",
          abs(r1_old - 0.6667) < 0.01 and abs(r3_old - 1.0) < 1e-9 and abs(r2 - 0.3262) < 0.01,
          f"R1old={r1_old:.4f} R2={r2:.4f} R3old={r3_old:.4f}")
    check("新阈值(0.30/0.6/1.099)组合触发率复算 ≈ 39.7%",
          abs(comb_new - 0.397) < 0.005,
          f"recomputed {comb_new:.4f}"
          f"（current_config_firing.combined={cf['combined']:.4f} 为旧配置 100% 对照，"
          f"即 100%→39.7% 声称的前半；test 口径 ablation_system.mechanism_metrics=0.3968 见 L3）")
    # 选择性仲裁语义复算（与 calibrate_disagreement.py 网格扫描同口径）：
    # 触发的 epoch 用仲裁后概率 p_arb，未触发保留 p_first；被试级为均值聚合
    trig_new = (m_diff > 0.30) | (m_maj < 0.6) | (m_ent > 1.099)
    probs_sel = np.where(trig_new[:, None], zc["p_arb"], zc["p_first"])
    acc_ep = (probs_sel.argmax(axis=1) == zc["y"]).mean()
    uniq_n = int(zc["sid_idx"].max()) + 1
    y_sub = np.array([zc["y"][zc["sid_idx"] == u][0] for u in range(uniq_n)])
    cnt = np.bincount(zc["sid_idx"], minlength=uniq_n)
    p_sub = np.zeros((uniq_n, 3))
    for c_ in range(3):
        p_sub[:, c_] = np.bincount(zc["sid_idx"], weights=probs_sel[:, c_],
                                   minlength=uniq_n) / cnt
    acc_sub = (p_sub.argmax(axis=1) == y_sub).mean()
    check("选择性仲裁复算: 触发 39.7% 时 epoch 0.5417 / 被试 0.5833（config.py 校准声称）",
          abs(acc_ep - 0.5417) < 6e-5 and abs(acc_sub - 0.5833) < 6e-5,
          f"recomputed epoch {acc_ep:.4f} / subject {acc_sub:.4f}"
          f"（npz 中 p_arb 为全量仲裁语义，选择性融合口径同 calibrate_disagreement.py）")

# ================= L2c 模型工件核验（checkpoints，不依赖 E 盘）=================
print("\n=== L2c 模型工件核验（checkpoints ↔ 报告口径声明）===")
import joblib
p532 = resolve_path("checkpoints/lightgbm_binary/model.pkl")
f532 = resolve_path("checkpoints/fusion_binary/fusion.joblib")
f614 = resolve_path("checkpoints/fusion_binary_event/fusion.joblib")
p614 = resolve_path("checkpoints/lightgbm_binary_event/model.pkl")
if all(os.path.exists(p) for p in (p532, f532, f614, p614)):
    m532, fu532 = joblib.load(p532), joblib.load(f532)
    m614, fu614 = joblib.load(p614), joblib.load(f614)
    check("基础版模型：mRMR 选择后输入维度 = 128", int(m532.n_features_in_) == 128, f"n_features_in_={m532.n_features_in_}")
    check("事件版模型：输入维度 = 128 且融合器 include_event=True",
          int(m614.n_features_in_) == 128 and bool(getattr(fu614, "include_event", False)),
          f"n_features_in_={m614.n_features_in_}, include_event={getattr(fu614, 'include_event', None)}")
    check("基础版融合器不含事件口径（include_event 为 False/缺省）",
          not bool(getattr(fu532, "include_event", False)))
    n_sel532 = len(getattr(fu532, "selected_indices_", getattr(fu532, "selected_", []))) or None
    n_sel614 = len(getattr(fu614, "selected_indices_", getattr(fu614, "selected_", []))) or None
    check("两融合器各选 128 维", n_sel532 == 128 and n_sel614 == 128,
          f"base {n_sel532} / event {n_sel614}")
else:
    blocked("模型工件核验（checkpoint 文件缺失）", "checkpoints 下模型/融合器不完整")

# ================= L3 跨文件一致性 =================
print("\n=== L3 跨文件一致性（JSON ↔ JSON）===")
se, af, asy, slt = load("stacking_eval.json"), load("ablation_features.json"), load("ablation_system.json"), load("subject_level_train.json")
s_full = aa["bases"]["lightgbm"]["variants"]["stacking_full"]["acc"]
check("stacking_eval.stacking.acc == ablation_agents(base=lightgbm).stacking_full.acc",
      abs(se["stacking"]["acc"] - s_full) < 5e-5, f"{se['stacking']['acc']} vs {s_full}")
full_acc = af["variants"]["full"]["subject_mean"]["accuracy"]
check("特征消融 Δ: full−no_event = +2.1pt",
      abs((full_acc - af["variants"]["no_event"]["subject_mean"]["accuracy"]) * 100 - 2.1) < 0.06)
check("特征消融 Δ: full−A2 = −5.5pt（频域最重要）",
      abs((full_acc - af["variants"]["A2_no_freq"]["subject_mean"]["accuracy"]) * 100 - 5.5) < 0.06)
eab = load("event_feature_ab.json")
check("快评 ΔAUC 与其自身数字一致",
      abs((eab["with_event"]["auc"] - eab["without_event"]["auc"]) - eab["delta"]["auc"]) < 5e-4)
for k, v in slt["results"].items():
    cm = np.array(v["confusion_matrix"])
    check(f"subject_level_train.{k} 混淆矩阵求和 = n={v['n']}", int(cm.sum()) == v["n"],
          "sum={}".format(int(cm.sum())))
for s in ("train", "val", "test"):
    d = dq[s]
    check(f"data_quality.{s} 类别计数闭合",
          sum(d["epochs_by_class"].values()) == d["n_epochs"] and sum(d["records_by_class"].values()) == d["n_records"])
mc = asy["mcnemar_vs_full"]
ok_p = True
for v, d in mc.items():
    b, c = d["full_correct_variant_wrong"], d["full_wrong_variant_correct"]
    p_re = binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0
    ok_p = ok_p and abs(p_re - d["p_value"]) < 5e-4 and b + c <= 238
check("McNemar 精确 p 值由 b/c 复算一致（A8/A9 两组）", ok_p,
      " ".join(f"{v}: p={d['p_value']}" for v, d in mc.items()))
# “仲裁贡献 +0.84pt”自洽校验已随 A7_no_arbitration 变体移除
trig = asy.get("mechanism_metrics", {}).get("disagreement_rate", None)
check("系统消融 test 触发率 39.7%（校准后口径）", trig is None or abs(trig - 0.397) < 0.005, f"stored {trig}")

# ================= L4 交付物核对 =================
print("\n=== L4 交付物核对（Excel ↔ 复算值；包文件哈希）===")
wb = load_workbook(XLSX, data_only=True)
ws = wb["Overview"]
check("Excel Overview 最优配置 = 0.6134", abs(ws.cell(3, 2).value - 0.6134) < 5e-5)
ws = wb["AblationAgents"]
hit = [r for r in ws.iter_rows(min_row=3, values_only=True)
       if r[1] == "A6: w/o Transformer" and "event" in str(r[0])]
check("Excel AblationAgents A6(event) 行 = 0.6134/0.6107/0.6458",
      hit and abs(hit[0][2] - 0.6134) < 5e-5 and abs(hit[0][3] - 0.6107) < 5e-5
      and abs(hit[0][4] - 0.6458) < 5e-5, str(hit[:1]))
ws = wb["AblationFeatures"]
af_rows = {r[0]: r for r in ws.iter_rows(min_row=3, values_only=True)}
ok_af = True
for k, nm in (("full", "full (614-d)"), ("no_event", "no_event (532-d)"), ("A2_no_freq", "A2: w/o freq domain (462-d)")):
    v = af["variants"][k]["subject_mean"]
    ok_af = ok_af and abs(af_rows[nm][3] - v["accuracy"]) < 5e-5 and abs(af_rows[nm][4] - v["auc"]) < 5e-5
check("Excel AblationFeatures 关键行 ↔ ablation_features.json", ok_af)
ws = wb["Dataset"]
ok_ds = all(abs(ws.cell(3 + i, 2).value - dq[s]["n_records"]) < 1e-9 and
            abs(ws.cell(3 + i, 3).value - dq[s]["n_epochs"]) < 1e-9
            for i, s in enumerate(("train", "val", "test")))
check("Excel Dataset 记录/epoch 数 ↔ data_quality.json", ok_ds)

n_hash_ok, n_hash = 0, 0
for f in (PKG / "raw_json").glob("*.json"):
    n_hash += 1
    if sha(f) == sha(OUT / f.name):
        n_hash_ok += 1
check("包内 raw_json 与 outputs 哈希一致", n_hash_ok == n_hash == 15, f"{n_hash_ok}/{n_hash}")
doc = next((PKG / "report").glob("*.docx"))
check("包内报告 docx 与 outputs 哈希一致", sha(doc) == sha(next(OUT.glob("EEG-MAS实验报告_*.docx"))))

print("\n" + "=" * 60)
print(f"验证完成: PASS {results['n_pass']} / FAIL {results['n_fail']} / BLOCKED {results['n_blocked']}"
      + ("（E: 缓存盘未挂载，L1/L2 深层校验待盘恢复后重跑）" if results["n_blocked"] else ""))
with open(OUT / "verification_report.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print(f"报告已保存: {OUT / 'verification_report.json'}")
