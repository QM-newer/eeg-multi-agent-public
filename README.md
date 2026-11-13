# EEG-MAS: 儿科 EEG 多智能体筛查系统

基于质量感知多智能体协作的儿童常规脑电（EEG）自动筛查系统（代码实现）。

> 完整的安装、复现与结果说明见 [`eeg_multi_agent/README.md`](eeg_multi_agent/README.md)。

## 算法

系统为三层多智能体架构，在 2-s epoch 级别处理 19 通道 / 250 Hz 信号：

1. **特征层** — 每个 epoch 提取 532 维多域特征（时域 228 / 频域 152 / 时频 152），经 mRMR（MID 准则）为特征驱动 Agent 选出 128 维子集
2. **诊断层** — 四个异构 Agent：
   - **LightGBM**：特征驱动，mRMR-128 输入（200 树，lr 0.05，31 叶子）
   - **EEGNet**：原始 epoch，紧凑 CNN（filter bank 8/16/16，dropout 0.25）
   - **TCN**：六层膨胀因果卷积（64 通道，kernel 5，dilation base 2）
   - **Transformer**：epoch 切 50-sample patch（d_model 128，8 heads，4 层）
3. **验证层** — 跨 Agent 一致性评分 + 特征级证据链

融合与升级机制：

- **质量感知动态加权投票**：基础权重由验证集被试级准确率超出基线的部分归一化（截断 [0.05, 0.60]）；推理时按 SNR 质量三档调整（高质量档 EEGNet/Transformer ×1.10，低质量档 LightGBM ×1.15），每 50 epoch 用滞后窗口的滚动准确率在线更新
- **分歧检测与升级标记**：三条规则（最大概率差 θd / 多数一致率 θm / 香农熵 θe），校准后阈值 (0.30, 0.60, 1.10)，仅用于标记人工复核，不修改结论；系统不含仲裁（二次推理）阶段
- **subject 级聚合**：mean 为全局预指定口径（p90 仅作敏感性分析）；二分类口径为 Normal vs. (Borderline + Abnormal)

## 代码

```
eeg_multi_agent/
├── config.py                 # 全局配置
├── agents/                   # 特征 / 诊断 / 验证三层 Agent
├── orchestrator/             # 协调层：orchestrator / voting / disagreement / dynamic_weight
├── models/                   # EEGNet / TCN / Transformer 网络定义
├── features/                 # 特征提取与融合
├── data/                     # 读取、预处理、epoch 缓存
├── training/                 # train_lightgbm / train_eegnet / train_tcn / train_transformer
├── evaluation/               # 指标、消融、可视化
├── scripts/                  # 评估、消融、校准、作图制表脚本
└── outputs/                  # 结果 JSON（所有评估数字的唯一来源）
```

### 安装与运行

```bash
pip install -r requirements.txt
cd eeg_multi_agent
python scripts/run_single_diagnosis.py     # 单样本诊断
python scripts/evaluate_binary.py          # 二分类评估
python scripts/evaluate_subject_level.py   # 被试级评估
python scripts/run_ablation.py             # 特征域消融
python scripts/calibrate_disagreement.py   # 升级阈值校准
```

模型权重位于 `checkpoints/`（不随仓库分发，放入后 Orchestrator 自动加载）；`outputs/*.json` 为匿名化评估结果，脚本可直接读取复现全部表格与图。

## 数据与隐私

原始 EEG 数据与病例表含可识别健康信息，不随仓库发布。`.gitignore` 屏蔽 `*.xlsx`、`subject_master.csv`、`record_index.csv` 与 `*exclude_records*`；任何包含患者姓名、年龄或姓名-编号对照的文件都不得提交。
