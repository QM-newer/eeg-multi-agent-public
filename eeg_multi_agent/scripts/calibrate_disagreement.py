# scripts/calibrate_disagreement.py
"""
分歧检测阈值校准

背景：系统已移除二次仲裁，最终结论由「SNR 感知动态权重 + 一轮加权投票」给出。
因此分歧检测不再改变预测，其作用是标记"低一致性 / 高风险"的 epoch。
本脚本据此重新校准阈值：让触发集合尽可能富集错误样本，同时保持足够的选择性。

方法（在 val@20 上校准，避免动 test）：
    1. 逐 epoch 走 Orchestrator 第一轮（质量→动态权重→特征→四Agent→加权投票），
       缓存三个分歧指标：max_prob_diff / majority_ratio / entropy 与一轮投票概率
    2. 任意阈值组合零成本模拟触发率，并统计触发集合的错误召回 / 精确率
    3. 宽范围网格扫描 + 帕累托前沿（触发率 vs 错误召回）+ 推荐配置

已知分布事实（val@20, 4800 epochs）：
    entropy 中位数 1.0878（≈ln3 上限 1.0986）→ 熵规则阈值需 ≥1.09 才有选择性
    max_prob_diff 中位数 0.178 → 0.15 阈值触发 67%
    majority_ratio ∈ {0.5, 0.75, 1.0}，0.5（标签分裂）占 32.6%

输出:
    outputs/disagreement_calibration.json
    cache/features/disagreement_val.npz  逐epoch原始指标

用法:
    python scripts/calibrate_disagreement.py                 # 全量
    python scripts/calibrate_disagreement.py --from-cache    # 复用 npz 离线分析
"""
import argparse
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from sklearn.metrics import accuracy_score

from config import resolve_path
from utils.io_utils import ensure_dir, save_json

FEATURE_DIR = os.path.join("cache", "features")  # 2026-11 起存本地（E: 盘写入不稳定）
CACHE_PATH = os.path.join(FEATURE_DIR, "disagreement_val.npz")


def epoch_metrics(first_results):
    """与 orchestrator.disagreement.check_disagreement 完全一致的三个指标"""
    probs = np.array([r["prob"] for r in first_results], dtype=np.float64)
    labels = [r["label"] for r in first_results]
    max_prob_diff = float(np.max(probs.max(axis=0) - probs.min(axis=0)))
    majority_ratio = Counter(labels).most_common(1)[0][1] / len(labels)
    avg_prob = probs.mean(axis=0)
    entropy = float(-np.sum(avg_prob * np.log(avg_prob + 1e-10)))
    return max_prob_diff, majority_ratio, entropy


def collect(n_jobs_note=""):
    """跑 val@20 第一轮（动态权重 + 加权投票），缓存指标与投票概率"""
    from data.epoch_cache import EpochCache
    from orchestrator.orchestrator import Orchestrator
    from orchestrator.voting import weighted_vote

    cache = EpochCache()
    X, y, sids, _ = cache.load_split("val", max_epochs_per_record=10,
                                     normalize=None)
    n = len(X)
    uniq = sorted(set(sids))
    sid_idx = np.searchsorted(np.array(uniq), sids)
    print(f"val: {n} epochs, {len(uniq)} 被试")

    print("\n初始化 Orchestrator...")
    system = Orchestrator(device="cpu")

    print(f"逐 epoch 诊断（{n} 个）...")
    t0 = time.time()
    m_diff = np.zeros(n); m_maj = np.zeros(n); m_ent = np.zeros(n)
    p_first = np.zeros((n, 3))
    for i in range(n):
        qr = system._assess_quality(X[i])
        dyn_w = system._adjust_weights(qr)
        feats = system._extract_features(X[i])
        first = system._run_diagnosis(X[i], feats)
        m_diff[i], m_maj[i], m_ent[i] = epoch_metrics(first)
        p_first[i] = weighted_vote(first, dyn_w)["prob"]
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{n}  ({time.time()-t0:.0f}s)")
    print(f"完成，耗时 {time.time()-t0:.0f}s")

    ensure_dir(FEATURE_DIR)
    np.savez(CACHE_PATH, max_prob_diff=m_diff, majority_ratio=m_maj,
             entropy=m_ent, p_first=p_first, y=y, sid_idx=sid_idx)
    return m_diff, m_maj, m_ent, p_first, y, sid_idx


def main(from_cache=False):
    print("=" * 74)
    print("分歧检测阈值校准（val@20，Orchestrator 三分类口径，单轮投票）")
    print("=" * 74)

    if from_cache and os.path.exists(CACHE_PATH):
        print(f"复用缓存: {CACHE_PATH}")
        z = np.load(CACHE_PATH)
        m_diff, m_maj, m_ent = z["max_prob_diff"], z["majority_ratio"], z["entropy"]
        p_first = z["p_first"]
        y, sid_idx = z["y"], z["sid_idx"]
        uniq_n = int(sid_idx.max()) + 1
        y_sub = np.array([y[sid_idx == u][0] for u in range(uniq_n)])
    else:
        m_diff, m_maj, m_ent, p_first, y, sid_idx = collect()
        uniq_n = int(sid_idx.max()) + 1
        y_sub = np.array([y[sid_idx == u][0] for u in range(uniq_n)])
    n = len(y)

    # ---- 分布统计 ----
    def q(a): return {p: round(float(np.quantile(a, p)), 4)
                      for p in (0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99)}
    dist = {"max_prob_diff": q(m_diff), "majority_ratio": q(m_maj),
            "entropy": q(m_ent)}

    # ---- 当前配置的规则触发率 ----
    cur = {"prob_diff_threshold": 0.15, "label_majority_threshold": 0.6,
           "entropy_threshold": 0.8}
    r1 = m_diff > cur["prob_diff_threshold"]
    r2 = m_maj < cur["label_majority_threshold"]
    r3 = m_ent > cur["entropy_threshold"]
    current_fire = {
        "rule1_prob_diff": round(float(r1.mean()), 4),
        "rule2_majority": round(float(r2.mean()), 4),
        "rule3_entropy": round(float(r3.mean()), 4),
        "combined": round(float((r1 | r2 | r3).mean()), 4),
    }

    # ---- 一轮投票的基线表现 ----
    pred_ep = p_first.argmax(axis=1)
    ep_correct = pred_ep == y
    n_wrong = int((~ep_correct).sum())
    counts = np.bincount(sid_idx, minlength=uniq_n)
    p_sub = np.zeros((uniq_n, 3))
    for c in range(3):
        p_sub[:, c] = np.bincount(sid_idx, weights=p_first[:, c],
                                  minlength=uniq_n) / counts
    baselines = {
        "epoch_acc_all": round(float(ep_correct.mean()), 4),
        "subject_acc_all": round(float(accuracy_score(y_sub, p_sub.argmax(axis=1))), 4),
        "n_wrong_epochs": n_wrong,
    }

    # ---- 宽范围网格扫描：触发集合应富集错误样本 ----
    # t2: 0.5=规则关闭（majority≥0.5 恒成立）；0.6=标签分裂(2-2/2-1-1)时触发
    # t3: 熵上限 ln3≈1.0986，网格须覆盖到 1.098 才能关掉该规则
    t1_grid = np.round(np.arange(0.15, 1.001, 0.05), 2)
    t3_grid = np.round(np.arange(0.80, 1.101, 0.01), 3)   # 上限 1.10 > ln3≈1.0986，可完全关闭熵规则
    grid = []
    for t2 in (0.5, 0.6):
        r2b = m_maj < t2
        for t1 in t1_grid:
            r1b = m_diff > t1
            for t3 in t3_grid:
                trig = r1b | r2b | (m_ent > t3)
                rate = float(trig.mean())
                if rate > 0.50 or not trig.any():   # 触发过半无选择性，不入网格
                    continue
                n_trig = int(trig.sum())
                n_trig_wrong = int((trig & ~ep_correct).sum())
                grid.append({
                    "prob_diff_threshold": float(t1),
                    "label_majority_threshold": float(t2),
                    "entropy_threshold": float(t3),
                    "trigger_rate": round(rate, 4),
                    "n_triggered": n_trig,
                    "error_recall": round(n_trig_wrong / max(n_wrong, 1), 4),
                    "error_precision": round(n_trig_wrong / n_trig, 4),
                    "flagged_epoch_acc": round(1.0 - n_trig_wrong / n_trig, 4),
                })

    if grid:
        # 推荐配置：触发率≤0.50 内错误召回最高，并列时取触发率更低者
        best = max(g["error_recall"] for g in grid)
        tied = [g for g in grid if g["error_recall"] >= best - 0.005]
        recommend = min(tied, key=lambda g: g["trigger_rate"])
        grid.sort(key=lambda g: (-g["error_recall"], g["trigger_rate"]))
    else:
        grid = []
        recommend = None

    # ---- 帕累托前沿：触发率升序，错误召回单调不降的组合 ----
    pareto = []
    best_so_far = -1.0
    for g in sorted(grid, key=lambda g: g["trigger_rate"]):
        if g["error_recall"] > best_so_far:
            pareto.append(g)
            best_so_far = g["error_recall"]

    results = {
        "protocol": "val@20, 3-class Orchestrator, 4 diagnosis agents, single-round voting",
        "n_epochs": int(n), "n_subjects": int(uniq_n),
        "metric_distributions": dist,
        "current_config_firing": current_fire,
        "baselines": baselines,
        "grid_top10": grid[:10],
        "pareto": pareto,
        "recommend": recommend,
    }

    print("\n---- 指标分布（分位数）----")
    for k, v in dist.items():
        print(f"  {k}: {v}")
    print("\n---- 当前配置规则触发率 ----")
    for k, v in current_fire.items():
        print(f"  {k}: {v:.1%}")
    print(f"\n基线(单轮投票): epoch_acc={baselines['epoch_acc_all']:.4f} | "
          f"subject_acc={baselines['subject_acc_all']:.4f} | "
          f"错分 epoch={baselines['n_wrong_epochs']}")
    if pareto:
        print("\n---- 帕累托前沿（触发率 → 错误召回）----")
        for g in pareto:
            print(f"  触发 {g['trigger_rate']:>5.1%}  错误召回 {g['error_recall']:.4f}"
                  f"  触发集精度 {g['flagged_epoch_acc']:.4f}"
                  f"  (diff>{g['prob_diff_threshold']:.2f} "
                  f"maj<{g['label_majority_threshold']:.1f} "
                  f"ent>{g['entropy_threshold']:.3f})")
    print(f"\n推荐配置: {recommend}")

    out_path = resolve_path("outputs/disagreement_calibration.json")
    ensure_dir(os.path.dirname(out_path))
    save_json(results, out_path)
    print(f"\n结果已保存: {out_path}")
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-cache", action="store_true",
                    help="复用 disagreement_val.npz 离线分析")
    a = ap.parse_args()
    main(from_cache=a.from_cache)
