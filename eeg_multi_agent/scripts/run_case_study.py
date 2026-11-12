# -*- coding: utf-8 -*-
"""III-F 案例研究数据生成：指定被试在 @10 协议下的单被试诊断轨迹。

用法: python scripts/run_case_study.py [SUBJ_0034]
输出: outputs/case_study.json（真实标签、逐 epoch 诊断、一致性、解释特征）
"""
import json
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.stdout.reconfigure(encoding="utf-8")

from data.epoch_cache import EpochCache          # noqa: E402
from orchestrator.orchestrator import Orchestrator  # noqa: E402

LABELS = {0: "Normal", 1: "Borderline", 2: "Abnormal"}


def main(sid="SUBJ_0034"):
    cache = EpochCache()
    X, y, sids, _ = cache.load_split("test", max_epochs_per_record=10, normalize=None)
    idx = [i for i, s in enumerate(sids) if s == sid]
    split = "test"
    if not idx:
        X, y, sids, _ = cache.load_split("val", max_epochs_per_record=10, normalize=None)
        idx = [i for i, s in enumerate(sids) if s == sid]
        split = "val"
    if not idx:
        print(f"{sid} not found in test/val")
        return

    system = Orchestrator()
    i0 = idx[0]
    y_true = LABELS[int(y[i0])]
    print(f"{sid}: {len(idx)} epochs ({split}@10), true label = {y_true}")

    epochs = []
    prob_sum = None
    n_disagree = 0
    cons_sum = 0.0
    for i in idx:
        r = system.diagnose(X[i])
        p = np.asarray(r["final_prob"], dtype=float)
        prob_sum = p if prob_sum is None else prob_sum + p
        n_disagree += int(bool(r["disagreement"]))
        cons_sum += float(r["consistency"]["consistency_score"])
        epochs.append({
            "true_label": LABELS[int(y[i])],
            "label": r["final_label"],
            "prob": [round(float(v), 4) for v in r["final_prob"]],
            "confidence": round(float(r["confidence"]), 4),
            "quality_tier": r["quality_report"].get("quality_tier"),
            "snr_db": round(float(r["quality_report"].get("snr_db", float("nan"))), 2),
            "disagreement": bool(r["disagreement"]),
            "consistency": round(float(r["consistency"]["consistency_score"]), 4),
            "weights": {k: round(float(v), 4) for k, v in r["weights"].items()},
        })
        print(f"  epoch: pred={r['final_label']:<10} conf={r['confidence']:.3f} "
              f"disagree={r['disagreement']} cons={r['consistency']['consistency_score']:.3f}")

    subj_prob = (prob_sum / len(idx)).tolist()
    order = np.argsort(-np.asarray(subj_prob))
    out = {
        "subject": sid,
        "split": split,
        "protocol": "@10",
        "n_epochs": len(idx),
        "true_label": y_true,
        "subject_prob": [round(float(v), 4) for v in subj_prob],
        "subject_pred": LABELS[int(order[0])],
        "top2": {
            "first": {"label": LABELS[int(order[0])], "p": round(float(subj_prob[order[0]]), 4)},
            "second": {"label": LABELS[int(order[1])], "p": round(float(subj_prob[order[1]]), 4)},
        },
        "n_disagreement_epochs": n_disagree,
        "mean_consistency": round(cons_sum / len(idx), 4),
        "epochs": epochs,
    }
    out_path = BASE / "outputs" / "case_study.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nsubject-level:", out["subject_pred"],
          [round(v, 3) for v in subj_prob],
          "| top2:", out["top2"], "| mean consistency:", out["mean_consistency"])
    print("saved:", out_path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "SUBJ_0034")
