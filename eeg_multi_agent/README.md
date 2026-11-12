# EEG Multi-Agent (EEG-MAS)

面向常规儿科脑电（EEG）三分类筛查的多智能体系统。四个异构诊断 Agent 通过**质量感知动态加权投票**融合，并配合跨 Agent 一致性评分、特征级证据链与**校准后的人工复核升级标记**。系统不再包含仲裁（二次推理）阶段。

## 核心结果（test，@10 协议）

| 配置 | 准确率 (95% CI) | 备注 |
|---|---|---|
| 多数类基线 | 0.5466 | 全判 Normal |
| EEGNet（最佳单模型） | **0.6441** (0.581–0.702) | 唯一显著优于基线，McNemar p = 0.028 |
| 融合系统（部署配置） | 0.6144 (0.551–0.674) | 未超最佳单模型（p = 0.23） |
| 融合系统（含事件特征） | 0.5720 | 事件特征块有害，−4.2 pt |

- 队列：**1,588** 条常规儿科记录（0–17 岁；9 条 ≥18 岁已剔除），train 1,113 / val 239 / test 236
- 协议：每条记录均匀抽样至多 10 个 2-s epoch（@10），test 共 2,360 epochs
- 标签：三分类 Normal / Borderline / Abnormal；二分类为 **Normal vs. (Borderline + Abnormal)**
- 部署特征维数：532-d（614-d 去掉 82-d 事件特征块，再经 mRMR 选 128）
- 聚合：mean 为全局预指定口径，p90 仅作敏感性分析
- 升级标记校准：48.4% 触发率、55.3% 错误召回（val 选择，test 报告）

## 项目结构

```
eeg_multi_agent/
├── config.py                 # 全局配置
├── agents/                   # Agent 层
│   ├── feature_agents/       # 特征工程组（时域/频域/时频）
│   ├── diagnosis_agents/     # 诊断推理组（LightGBM/EEGNet/TCN/Transformer）
│   └── validation_agents/    # 解释验证组（可解释性/一致性）
├── orchestrator/
│   ├── orchestrator.py       # 协调层主类
│   ├── voting.py             # 加权投票
│   ├── disagreement.py       # 分歧检测（仅用作升级标记）
│   └── dynamic_weight.py     # SNR 感知的动态权重（三档）
├── models/                   # EEGNet / TCN / Transformer
├── data/                     # 读取、预处理、epoch 缓存
├── training/                 # 训练脚本
├── evaluation/               # 指标
├── scripts/                  # 评估、消融、作图、制表脚本
├── outputs/                  # 结果 JSON（论文所有数字的来源）
└── checkpoints/              # 模型权重（不纳入版本控制）
```

## 安装与使用

```bash
pip install -r requirements.txt
cd eeg_multi_agent
python scripts/run_single_diagnosis.py     # 单样本诊断
python scripts/evaluate_binary.py          # 二分类评估
python scripts/evaluate_subject_level.py   # 被试级评估
```

模型权重位于 `checkpoints/`（未上传）。将权重放入后，`Orchestrator` 会自动加载；缺失时退回随机初始化占位模式。

## 数据

原始信号与病例表涉及患者隐私，**不随仓库分发**。`data/subject_master.csv`、`data/record_index.csv` 与所有 `.xlsx` 均被 `.gitignore` 排除。

- 采样率 500 Hz → 0.5–45 Hz 带通 → 50 Hz 陷波 → 降采样 250 Hz → 平均参考
- 2 s epoch、50% 重叠，按记录自身峰峰值中位数的 3 倍做自适应伪迹剔除（保留率中位 0.91）
- 通道：Ch1–Ch19

## 复现说明

`outputs/*.json` 是论文各表各图的唯一数据来源，仓库中的脚本直接读取这些文件生成表格与图。训练权重与逐样本结果因体积与隐私原因不公开，可向通讯作者索取。

## 引用

待论文正式接收后补充。
