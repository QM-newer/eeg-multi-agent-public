# demo/prepare_demo.py
"""
演示病例一键准备（向老师汇报现场演示用）

从 test 集自动筛选 3 个代表性病例并生成完整诊断报告：
    病例 1（正常）   系统高置信判对 —— 展示"放心通过"的常规初筛路径
    病例 2（异常）   系统高置信判对 —— 展示"抓到异常"的能力与证据链
    病例 3（可疑）   置信差最小（优先临床 Borderline）—— 展示"拿不准就建议人工复核"的安全设计

流程：
    1. 载入 test 集（@20 epochs，原始 µV，与批量评估同口径）
    2. 候选池 = Normal 8 个 + 全部 Borderline + Abnormal 12 个（按 ID 排序，确定性可复现）
    3. 逐候选跑完整 Orchestrator，聚合被试级概率 / 置信差 / 一致性
    4. 选定 3 例，调用 generate_report 为每例生成结构化报告到 demo/reports/
    5. 写 demo/cases_manifest.json（病例一览 + 汇报讲解要点）

用法：
    python demo/prepare_demo.py
输出：
    demo/reports/<SUBJ_XXXX>_report.md × 3
    demo/cases_manifest.json
"""
import json
import os
import sys
import time
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from config import CLASS_NAMES, DISAGREEMENT_CONFIG
from data.epoch_cache import EpochCache
from orchestrator.orchestrator import Orchestrator
from generate_report import main as generate_case_report

DEMO_DIR = os.path.join(_ROOT, "demo")
REPORTS_DIR = os.path.join(DEMO_DIR, "reports")
MANIFEST = os.path.join(DEMO_DIR, "cases_manifest.json")

N_NORMAL = 8            # Normal 候选数
N_ABNORMAL = 12         # Abnormal 候选数（该类召回偏低，池子放大）
MAX_EPOCHS = 20
BORDERLINE_MARGIN = 0.10   # 与 generate_report 一致：置信差 < 0.10 → "可疑/界限性倾向"
CONSISTENCY_REVIEW = 0.6   # 与 generate_report 一致：一致性 < 0.6 → 建议人工复核

TALKING_POINTS = {
    "normal": "正常病例：高置信判为正常、一致性良好，展示\"放心通过\"的常规初筛路径（秒级完成）。",
    "abnormal": "异常病例：高置信判为异常并附证据链与多 Agent 共识过程，展示\"抓到异常\"的可解释能力。",
    "suspicious": "可疑病例：置信差小、系统主动建议人工复核，展示临床安全设计——AI 只做初筛，拿不准就交还医生。",
}


def evaluate_subject(system, X):
    """对一个被试的全部 epoch 走完整诊断，返回被试级聚合指标。"""
    probs, cons = [], []
    n_dis = 0
    for x in X:
        r = system.diagnose(x)
        probs.append(r["final_prob"])
        cons.append(r["consistency"]["consistency_score"])
        n_dis += int(r["disagreement"])
    p = np.mean(probs, axis=0)
    order = np.argsort(p)[::-1]
    return {
        "probs": p,
        "top": int(order[0]),
        "margin": float(p[order[0]] - p[order[1]]),
        "consistency": float(np.mean(cons)),
        "disagreement_rate": n_dis / len(X),
    }


def conclusion_text(r):
    """与 generate_report.subject_label_name 相同的被试级结论措辞。"""
    p = r["probs"]
    order = np.argsort(p)[::-1]
    top, second = order[0], order[1]
    if p[top] - p[second] < BORDERLINE_MARGIN:
        return (f"可疑/界限性倾向（{CLASS_NAMES[top]} {p[top]:.1%} vs "
                f"{CLASS_NAMES[second]} {p[second]:.1%}）")
    return CLASS_NAMES[top]


def main():
    t0 = time.time()
    print("=" * 74)
    print("演示病例准备：正常 / 异常 / 可疑 各一例（test 集，@20 epochs）")
    print("=" * 74)

    cache = EpochCache()
    print("载入 test 集 epoch 缓存...")
    X, y, sids, _ = cache.load_split("test", max_epochs_per_record=MAX_EPOCHS,
                                     normalize=None)

    label_of = {}
    by_class = {0: [], 1: [], 2: []}
    for u in sorted(set(sids)):
        lab = int(y[sids == u][0])
        label_of[u] = lab
        by_class[lab].append(u)
    print(f"test 被试: Normal {len(by_class[0])} / Borderline {len(by_class[1])} "
          f"/ Abnormal {len(by_class[2])}")

    pool = by_class[0][:N_NORMAL] + by_class[1] + by_class[2][:N_ABNORMAL]
    print(f"候选池: {len(pool)} 个被试（Normal {min(N_NORMAL, len(by_class[0]))} + "
          f"Borderline {len(by_class[1])} + Abnormal {min(N_ABNORMAL, len(by_class[2]))}）")

    print("初始化多Agent系统...")
    system = Orchestrator(device="cpu")

    results = {}

    def evaluate_one(u):
        mask = sids == u
        results[u] = evaluate_subject(system, X[mask])

    for k, u in enumerate(pool, 1):
        evaluate_one(u)
        r = results[u]
        ok = "判对" if r["top"] == label_of[u] else "判错"
        print(f"  [{k}/{len(pool)}] {u}  临床={CLASS_NAMES[label_of[u]]:<10} "
              f"系统={CLASS_NAMES[r['top']]:<10} {ok}  "
              f"margin={r['margin']:.3f}  一致性={r['consistency']:.2f}")

    def best_correct(cls):
        cands = [(u, r) for u, r in results.items()
                 if label_of[u] == cls and r["top"] == cls]
        return max(cands, key=lambda t: t[1]["margin"]) if cands else None

    # 兜底扩展（正常情况下不会触发）：池内没找到判对样本时再补评同类候选
    for cls, first_n in ((0, N_NORMAL), (2, N_ABNORMAL)):
        if best_correct(cls) is None:
            rest = by_class[cls][first_n:]
            print(f"  池内无判对的 {CLASS_NAMES[cls]}，扩展候选评估...")
            for i in range(0, len(rest), 10):
                for u in rest[i:i + 10]:
                    evaluate_one(u)
                if best_correct(cls) is not None:
                    break
            if best_correct(cls) is None:
                raise SystemExit(f"test 集中未找到判对的 {CLASS_NAMES[cls]} 被试，演示无法准备")

    case_normal = best_correct(0)
    case_abnormal = best_correct(2)
    # 可疑病例：优先临床 Borderline 中置信差最小者；无 Borderline 则全局最小
    bl = [(u, r) for u, r in results.items() if label_of[u] == 1]
    case_suspicious = min(bl, key=lambda t: t[1]["margin"]) if bl else \
        min(results.items(), key=lambda t: t[1]["margin"])

    picks = [
        ("normal", case_normal, TALKING_POINTS["normal"]),
        ("abnormal", case_abnormal, TALKING_POINTS["abnormal"]),
        ("suspicious", case_suspicious, TALKING_POINTS["suspicious"]),
    ]

    os.makedirs(REPORTS_DIR, exist_ok=True)
    manifest_cases = []
    for role, (u, r), talking in picks:
        print(f"\n生成报告: {u}（{role}）")
        path = generate_case_report(split="test", subject=u, max_epochs=MAX_EPOCHS,
                                   out_dir=REPORTS_DIR)
        manifest_cases.append({
            "role": role,
            "subject_id": u,
            "clinical_label": CLASS_NAMES[label_of[u]],
            "system_conclusion": conclusion_text(r),
            "probs": {CLASS_NAMES[i]: round(float(r["probs"][i]), 4) for i in range(3)},
            "top1_top2_margin": round(r["margin"], 4),
            "consistency": round(r["consistency"], 3),
            "disagreement_trigger_rate": round(r["disagreement_rate"], 3),
            "review_flag": bool(r["consistency"] < CONSISTENCY_REVIEW
                                or r["margin"] < BORDERLINE_MARGIN),
            "report": os.path.relpath(path, _ROOT).replace("\\", "/"),
            "talking_point": talking,
        })

    manifest = {
        "purpose": "汇报演示病例清单（demo/prepare_demo.py 自动生成）",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "protocol": f"test 集，@{MAX_EPOCHS} epochs/记录，与批量评估同口径",
        "disagreement_thresholds": {
            "prob_diff": DISAGREEMENT_CONFIG["prob_diff_threshold"],
            "majority": DISAGREEMENT_CONFIG["label_majority_threshold"],
            "entropy": DISAGREEMENT_CONFIG["entropy_threshold"],
        },
        "cases": manifest_cases,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 74)
    print("选定病例")
    print("=" * 74)
    for c in manifest_cases:
        print(f"[{c['role']}] {c['subject_id']}  临床={c['clinical_label']}")
        print(f"    系统结论: {c['system_conclusion']}  "
              f"复核标记={'是' if c['review_flag'] else '否'}")
        print(f"    报告: {c['report']}")
    print(f"\n清单文件: {MANIFEST}")
    print(f"总耗时: {manifest['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
