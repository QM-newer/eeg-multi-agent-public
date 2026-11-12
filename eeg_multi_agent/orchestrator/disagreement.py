# orchestrator/disagreement.py

import numpy as np
from collections import Counter


def check_disagreement(agent_results, config):
    """
    分歧检测：三条规则，任一满足即判定有分歧

    参数:
        agent_results: list[dict]，各Agent预测结果
        config: dict，分歧阈值配置
            - prob_diff_threshold: 最大概率差阈值
            - label_majority_threshold: 标签多数派比例阈值
            - entropy_threshold: 平均概率熵值阈值

    返回:
        bool: True=有分歧，False=无分歧
    """
    probs = np.array([r["prob"] for r in agent_results])
    labels = [r["label"] for r in agent_results]

    # 规则1：最大概率差超过阈值
    # 同一类别上，不同Agent预测的概率最大值与最小值之差
    max_prob_diff = np.max(probs.max(axis=0) - probs.min(axis=0))
    if max_prob_diff > config["prob_diff_threshold"]:
        return True

    # 规则2：标签不统一（多数派比例低于阈值）
    majority_count = Counter(labels).most_common(1)[0][1]
    majority_ratio = majority_count / len(labels)
    if majority_ratio < config["label_majority_threshold"]:
        return True

    # 规则3：平均概率的熵值过高（不确定性大）
    avg_prob = np.mean(probs, axis=0)
    # 三类均匀分布的熵约为 log(3) ≈ 1.0986
    entropy = -np.sum(avg_prob * np.log(avg_prob + 1e-10))
    if entropy > config["entropy_threshold"]:
        return True

    return False
