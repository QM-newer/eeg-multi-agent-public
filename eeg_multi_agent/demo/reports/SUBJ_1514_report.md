# 脑电多智能体辅助诊断报告

- 被试编号：`SUBJ_1514`
- 生成时间：2026-10-07 15:44
- 分析样本：20 个 epoch（2s / 250Hz / 19 通道，每记录最多取 20 个）
- 临床参考标签：**Borderline**（医生判读，仅供对照）

## 一、结论

**系统诊断：可疑/界限性倾向（Normal 35.3% vs Abnormal 34.5%）**

| 类别 | 平均概率 | 跨epoch波动(std) |
|---|---|---|
| Normal | 35.3% | 0.067 |
| Borderline | 30.2% | 0.022 |
| Abnormal | 34.5% | 0.065 |

## 二、信号质量

- epoch 质量等级分布：high 20 个
- 质量等级由 SNR 与伪迹比例自动评定（utils/signal_utils），并驱动各 Agent 动态权重。

## 三、多Agent意见与共识过程

| 诊断Agent | 平均动态权重 | 主要意见（epoch票数） |
|---|---|---|
| lightgbm | 0.465 | Abnormal 11、Normal 8、Borderline 1 |
| eegnet | 0.438 | Normal 10、Abnormal 10 |
| tcn | 0.048 | Normal 17、Abnormal 3 |
| transformer | 0.049 | Normal 18、Borderline 2 |

- 分歧触发率：6/20（30%，触发即进入补充特征→重推理→可信度仲裁流程）
- 仲裁执行率：6/20
- 跨Agent一致性得分：0.535（建议人工复核）

分歧仲裁示例（首个分歧 epoch）：

- 补充空间域特征 43 维（扩充后 171 维）后二次诊断；特征可信度：lightgbm=0.77、eegnet=0.76、tcn=0.83、transformer=0.78

## 四、证据链（可解释性）

各 epoch 可解释性 Agent 输出的高频 Top 特征（特征索引 @ 532 维多域特征）：

| 特征索引 | 出现次数 |
|---|---|
| 72 | 8 |
| 77 | 8 |
| 97 | 7 |
| 46 | 7 |
| 109 | 5 |
| 103 | 4 |
| 95 | 4 |
| 82 | 4 |

> 特征索引按 [时域 0-227 | 频域 228-379 | 时频 380-531] 分块，可对照 `training/common.py::_make_feature_agents` 定位特征含义。

## 五、说明与免责

- 本报告由 EEG-MAS 多智能体系统自动生成，仅供研究/辅助参考，不构成临床诊断结论。
- 单被试推理耗时 1.9s（20 epoch，CPU）。
