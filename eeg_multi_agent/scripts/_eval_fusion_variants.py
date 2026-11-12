# _eval_fusion_variants.py
# 离线比较二分类融合变体（基于 run_ablation_agents 缓存的 epoch 级概率）
# 协议：在 val 上选择变体，在 test 上报告（与全文"val 择优、全局统一"一致）
import numpy as np
import json
import sys
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score

sys.stdout.reconfigure(encoding="utf-8")

AG4 = ["lightgbm", "eegnet", "tcn", "transformer"]
AG3 = ["lightgbm", "eegnet", "tcn"]


def load(split):
    """epoch 级概率 → 被试级 mean 聚合"""
    d = np.load(f"cache/features/agent_probs_{split}.npz", allow_pickle=True)
    sids = np.asarray(d["_sids"]).astype(str)
    y3 = np.asarray(d["_y3"]).astype(int)
    ybin = (y3 > 0).astype(int)
    uniq = sorted(set(sids.tolist()))
    idx = {u: np.where(sids == u)[0] for u in uniq}
    P = {a: np.array([np.asarray(d[a])[idx[u]].mean() for u in uniq])
         for a in d.files if not a.startswith("_")}
    yb = np.array([ybin[idx[u]][0] for u in uniq])
    return P, yb


def metrics(p, y):
    pred = (p >= 0.5).astype(int)
    return {
        "acc": round(float(accuracy_score(y, pred)), 4),
        "auc": round(float(roc_auc_score(y, p)), 4),
        "f1": round(float(f1_score(y, pred)), 4),
    }


def wnorm(accs):
    s = sum(accs.values())
    return {a: v / s for a, v in accs.items()}


Pv, yv = load("val")
Pt, yt = load("test")

# 各 agent 在 val 上的被试级二分类准确率（作为加权依据）
val_acc = {a: float(((Pv[a] >= 0.5).astype(int) == yv).mean()) for a in AG4}
print("val 单 Agent 被试级 acc:", {a: round(v, 4) for a, v in val_acc.items()})

variants = {
    "4agent_equal":        (AG4, {a: 1 / 4 for a in AG4}),
    "4agent_valweighted":  (AG4, wnorm(val_acc)),
    "3agent_equal":        (AG3, {a: 1 / 3 for a in AG3}),
    "3agent_valweighted":  (AG3, wnorm({a: val_acc[a] for a in AG3})),
}

res = {}
for name, (ags, w) in variants.items():
    pv = sum(w[a] * Pv[a] for a in ags)
    pt = sum(w[a] * Pt[a] for a in ags)
    res[name] = {"val": metrics(pv, yv), "test": metrics(pt, yt),
                 "weights": {a: round(w[a], 4) for a in ags}}
    r = res[name]
    print(f"{name:22s} val acc={r['val']['acc']} auc={r['val']['auc']}  |  "
          f"test acc={r['test']['acc']} auc={r['test']['auc']} f1={r['test']['f1']}")

best = max(variants, key=lambda n: (res[n]["val"]["acc"], res[n]["val"]["auc"]))
print(f"\nval 择优胜出: {best}  → test: {res[best]['test']}")
res["selected"] = best
json.dump(res, open("outputs/fusion_variants.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("已保存: outputs/fusion_variants.json")
