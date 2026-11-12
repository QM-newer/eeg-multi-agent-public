# EEG-MAS: 儿科 EEG 多智能体筛查系统

基于质量感知多智能体协作的儿童脑电（EEG）自动筛查系统，配套 IEEE JBHI 投稿稿件。

> 完整的方法说明、复现步骤、结果表与数据来源映射见 [`eeg_multi_agent/README.md`](eeg_multi_agent/README.md)。

## 核心结果（test 集，@10 协议）

| 项目 | 数值 |
|---|---|
| 队列 | 1,588 条记录（train 1,113 / val 239 / test 236），0–17 岁 |
| 多数类基线 | 0.5466 |
| 最佳单模型（EEGNet） | **0.6441**（95% CI 0.581–0.702；vs 基线 McNemar p = 0.028） |
| 融合系统（质量感知加权投票） | 0.6144（95% CI 0.551–0.674；vs EEGNet p = 0.23，未显著超过） |
| 事件特征消融 | 614-d → 532-d，0.5720 → 0.6144（−4.2 pt） |
| 升级校准（validation） | 48.4% 触发率，55.3% 错误召回 |

二分类口径为 **Normal vs. (Borderline + Abnormal)**；聚合采用全局预指定的 mean，p90 仅作敏感性分析。

系统已**移除仲裁（二次推理）阶段**：最终结论由 SNR 感知的动态权重加权投票给出，分歧检测只用于标记人工复核升级，不再触发第二轮诊断。

## 数据与隐私

原始 EEG 数据含可识别健康信息，不随仓库发布。仓库仅含代码、匿名化结果 JSON 与图件。任何包含患者姓名、年龄或姓名-编号对照的文件都不得提交，`.gitignore` 已屏蔽 `*exclude_records*`。若需保留 ≥18 岁剔除的可追溯性，只使用匿名 `subject_id`，对照表仅留本地。

## 论文

*EEG-MAS: A Quality-Aware Multi-Agent System for Pediatric EEG Screening*，投稿 IEEE Journal of Biomedical and Health Informatics。稿件与补充材料位于 `essay/`。

## 权威结果文件 → 论文表/图

| JSON（`eeg_multi_agent/outputs/`） | 对应表/图 |
|---|---|
| `binary_eval.json` | Table II、Fig. 4（单模型基线） |
| `subject_val_accuracies.json` | Table V（投票权重） |
| `ablation_features.json` | Table III、Fig. 5（特征消融） |
| `ablation_agents.json` | Table IV、Fig. 6（Agent 消融） |
| `fusion_variants.json` | Table S5（融合变体） |
| `disagreement_calibration.json` | Table VI、Fig. 7（升级校准） |
| `val_binary_eval_mean.json`、`test_binary_eval_p90.json` | Table S3、Fig. S3（聚合敏感性） |
| `data_quality.json`、`label_metadata_analysis.json` | Fig. 2、Fig. 3 |

> 所有评估统一为 @10。早期 @20 产物（如 `*_test_mean.json`）已从仓库移除，不应再作为引用来源。

## 目录

- `eeg_multi_agent/` — 系统实现、训练脚本、结果 JSON、图表生成脚本
- `essay/` — 投稿稿件、补充材料、图件（TIFF/PNG）与构建脚本
