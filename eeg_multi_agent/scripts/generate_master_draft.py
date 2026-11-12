# -*- coding: utf-8 -*-
"""生成《论文写作总稿》：图表总稿（主文 8 图 + 6 表、附录 2 图 + 9 表、Related Work 表）
+ 中文写作大纲与思路。

表格来源：直接从已生成的三个投稿格式 docx 提取"caption+表+表注"块合并（零重算）。
图片来源：outputs/figures/*.png。
输出：Agent/论文写作总稿.docx
"""
import copy
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

BASE = Path(r"c:\Users\23373\Desktop\eeg\data and code\Agent")
FIGD = BASE / "eeg_multi_agent/outputs/figures"


# ---------- 基础 helpers ----------
def set_font(run, size=10.5, bold=False, italic=False, color=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:eastAsia"), "Microsoft YaHei")
    if color:
        from docx.shared import RGBColor
        run.font.color.rgb = RGBColor(*color)


def para(doc, text, size=10.5, bold=False, italic=False, space_after=6,
         color=None, indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Pt(indent)
    set_font(p.add_run(text), size=size, bold=bold, italic=italic, color=color)
    return p


def h1(doc, text):
    doc.add_page_break()
    para(doc, text, size=15, bold=True, space_after=10, color=(31, 56, 100))


def h2(doc, text):
    para(doc, text, size=12.5, bold=True, space_after=6, color=(31, 56, 100))


def h3(doc, text):
    para(doc, text, size=11, bold=True, space_after=4)


def bullets(doc, items, size=10.5):
    for t in items:
        para(doc, "• " + t, size=size, space_after=3, indent=12)


def pic(doc, path, width=5.8):
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, "", size=2, space_after=0)


# ---------- 从源 docx 提取"表块" ----------
def ptext(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


CAPTION_RE = re.compile(r"^Table (?:S?\d+)[.\s]*$")


def extract_blocks(path):
    """按 caption（严格匹配 "Table N" / "Table S1." 的短段）切分为块：
    [caption 段…, 表, 表注段…]。工作稿说明页的映射行（如 "Table 1 = 报告 Table 3…"）
    不匹配该模式，自动排除。"""
    src = Document(path)
    children = [el for el in src.element.body
                if el.tag in (qn("w:p"), qn("w:tbl"))]
    blocks, cur, started = [], [], False
    for el in children:
        if el.tag == qn("w:p") and CAPTION_RE.match(ptext(el).strip()):
            if cur:
                blocks.append(cur)
            cur, started = [el], True
        elif started:
            cur.append(el)
    if cur:
        blocks.append(cur)
    return blocks


def find_block(blocks, label):
    """按 caption 文本（如 "Table 1"）定位块，找不到则报错。"""
    for b in blocks:
        if ptext(b[0]).strip().rstrip(".") == label:
            return b
    raise KeyError(f"block not found: {label}")


def append_block(doc, block):
    """把表块插入文档流末尾（body 级 sectPr 之前）。
    注意：不能用 body.append()——那会把内容排到 sectPr 之后，
    破坏节结构（表格会被挤到最后一节之外）。"""
    body = doc.element.body
    sectPr = body.find(qn("w:sectPr"))
    for el in block:
        el = copy.deepcopy(el)
        if sectPr is not None:
            sectPr.addprevious(el)
        else:
            body.append(el)


def tbl_label(doc, text):
    para(doc, text, size=11, bold=True, space_after=4, color=(192, 0, 0))


def usage(doc, text):
    para(doc, "写作要点：" + text, size=9.5, italic=True, space_after=14,
         color=(89, 89, 89))


def fig_item(doc, no, cname, fname, note, width=5.8):
    h3(doc, f"Fig. {no}　{cname}（{fname}）")
    if fname:
        pic(doc, FIGD / fname, width)
    usage(doc, note)


# ---------- Related Work 表（硬编码，来自 RelatedWork对比表.md） ----------
def _set_borders(el, edges):
    if el.tag == qn("w:tbl"):
        pr = el.find(qn("w:tblPr"))
        borders = pr.find(qn("w:tblBorders"))
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            pr.append(borders)
    else:
        pr = el.get_or_add_tcPr()
        borders = OxmlElement("w:tcBorders")
        pr.append(borders)
    for edge, sz in edges.items():
        e = borders.find(qn(f"w:{edge}"))
        if e is None:
            e = OxmlElement(f"w:{edge}")
            borders.append(e)
        if sz is None:
            e.set(qn("w:val"), "nil")
        else:
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(sz))
            e.set(qn("w:color"), "000000")


def rw_table(doc, rows, col_widths, fsize=8):
    n_r, n_c = len(rows), len(rows[0])
    tbl = doc.add_table(rows=n_r, cols=n_c)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    _set_borders(tbl._tbl, {"top": 12, "bottom": 12, "left": None,
                            "right": None, "insideH": 4, "insideV": None})
    for r in range(n_r):
        for c in range(n_c):
            cell = tbl.cell(r, c)
            cell.width = col_widths[c]
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            set_font(p.add_run(rows[r][c]), size=fsize, bold=(r == 0))
    return tbl


# ============================================================
doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Pt(72)

para(doc, "EEG-MAS 论文写作总稿", size=18, bold=True, space_after=4)
para(doc, "图表总稿 + 写作大纲与思路（中文工作稿）　编制日期：2026-10-14", size=10,
     space_after=2)
para(doc, "配套文件：论文图表caption清单.md（英文 caption 稿）／RelatedWork对比表.md／"
          "投稿格式主文表.docx／投稿格式合并表.docx／投稿格式附表S1-S9.docx",
     size=9, italic=True, space_after=10)

# ============================================================
# 第一部分 定位与总纲
# ============================================================
doc.add_page_break()
h2(doc, "第一部分　论文定位与写作总纲")

h3(doc, "1.1 一句话定位")
para(doc, "面向儿童常规脑电筛查的质量感知多智能体辅助判读系统（EEG-MAS）：以“三层协作架构"
          " + 分歧阈值校准方法论 + 严谨的机制级评估（含阴性结果）”为核心贡献的系统论文，"
          "而非以绝对精度为卖点的模型论文。")

h3(doc, "1.2 核心贡献（投稿主张，按重要性排序）")
bullets(doc, [
    "C1 架构贡献：信号级三层多智能体系统（协调层 + 特征层/诊断层/验证层），异构 agent 融合"
    "（feature-driven: mRMR+LightGBM；signal-driven: EEGNet/TCN/Transformer 原始 epoch 输入）——"
    "多智能体医疗 AI 此前集中在 LLM/文本/EHR 层面，本工作是信号级协作。",
    "C2 方法学贡献（全文最亮点）：分歧阈值校准方法论。诊断出熵规则在近均匀三分类分布下退化"
    "（中位熵 1.088 ≈ ln3=1.0986）；校准后触发率 100%→39.7%，推理时间 −39%（785→476 s），"
    "精度与仲裁贡献完全保持。",
    "C3 评估规范贡献：机制级 McNemar 精确检验 + 阴性结果如实报告（仲裁 +0.84pt 不显著、"
    "动态权重无低质优势、A9 等权不显著）——倡导临床多智能体系统的评估标准。",
    "C4 特征闭环贡献：82 维事件特征块 +2.1pt；“小样本快评不可靠”的实证教训"
    "（快评 −2.2pt vs 全量 +2.1pt 反转）。",
])

h3(doc, "1.3 叙事主线（三幕结构）")
bullets(doc, [
    "第一幕·为什么：儿童 EEG 判读负担 → 现有自动化方法单模型、成人基准（TUAB）、无分歧处理"
    " → 临床筛查需要的是“可仲裁、可解释、可升级人工”的系统而非单点模型。",
    "第二幕·是什么/怎么样：三层架构（Fig.1）→ 数据与动机（Table 1 / Fig.2 / Fig.3）→ "
    "消融链条逐层递进（基线→特征→agent→机制），每层回答一个问题。",
    "第三幕·深层贡献：校准方法论（Fig.8 / Table 6）升格为可推广的方法学；阴性结果转化为"
    "评估规范倡议；“低置信度→人工复核”收尾于临床安全设计。",
])

h3(doc, "1.4 关键数字速查（写作时随手引用）")
bullets(doc, [
    "数据：1,597 records / 159,501 epochs / train-val-test = 1,119-240-238；19 导联、250 Hz、2 s；"
    "三档标签 N/BL/A；test@20 = 4,760 epochs。",
    "基线：majority = 0.5504（131/238）。",
    "最佳：A6（去 Transformer）= 0.6134（+6.3pt），macro F1 0.6107；AUC 0.6458。",
    "单 Agent：LightGBM=EEGNet=0.6050；EEGNet 11.8 s vs LightGBM 594.6 s（约 50×）。",
    "特征消融：freq −5.5pt > TF −2.5pt > time −0.9pt；event +2.1pt。",
    "机制：仲裁 +0.84pt（McNemar p=0.50, n.s.）；触发率 100%→39.7%；推理 −39%。",
    "质量：99.2% epoch 高质量；低/中质子集 n=22/18（仅指示性）。",
])

h3(doc, "1.5 目标期刊与投稿策略")
bullets(doc, [
    "首选：Journal of Neuroscience Methods（方法学导向，重系统与评估严谨性）或 "
    "Artificial Intelligence in Medicine（临床决策支持系统完美契合 scope）。",
    "可冲：Biomedical Signal Processing and Control、Journal of Neural Engineering。",
    "保底：Frontiers in Neuroscience、Sensors、IEEE Access。",
    "差异化路线（需临床合作者）：Clinical Neurophysiology——单病例报告与“人工复核”安全设计"
    "对临床读者有吸引力。",
    "策略：实验体量（8 图 6 表 + 9 附表）适合直接投期刊全文 + 丰富 Supplementary；"
    "不建议先压成 4 页会议短文（会丢掉评估完整性这一最大卖点）。",
])

# ============================================================
# 第二部分 主文图表总稿（按论文出现顺序）
# ============================================================
h1(doc, "第二部分　主文图表总稿（按论文出现顺序排列）")
para(doc, "图片直接嵌入；表格从投稿格式 docx 提取合并（含英文 caption 与表注）。"
          "每项下方红字为中文写作要点。", size=9.5, italic=True, space_after=10)

blocks_main = extract_blocks(BASE / "投稿格式主文表.docx")   # T1, T2, T3, T6
blocks_merge = extract_blocks(BASE / "投稿格式合并表.docx")  # T4, T5
T = lambda bl, lab: find_block(bl, lab)

h2(doc, "2.1 Introduction 素材")
fig_item(doc, 1, "系统架构图（新绘）", "fig_system_architecture.png",
         "放置 Introduction 末尾或 Methods 开头。正文按 step 1–9 顺序走一遍流程；"
         "重点讲三个设计决策：双路径异构（feature-driven 走特征层、signal-driven 直连原始 epoch）、"
         "质量感知动态权重（step 1–2）、条件仲裁（红色支路，step 7）。图内已标注校准后阈值"
         "（0.30/0.60/1.099）与 39.7% 触发率，与 Fig.8 呼应。")

h2(doc, "2.2 Methods — Dataset 素材")
tbl_label(doc, "Table 1　数据划分与类分布（报告 Table 3）")
append_block(doc, T(blocks_main, "Table 1"))
usage(doc, "Methods–Dataset 小节。类不平衡直接给出 majority 基线 0.5504；"
           "epochs 口径（train 111,804 / val 23,923 / test@20 4,760）写入 caption 或正文。")
fig_item(doc, 2, "数据概览（三面板精简版）", "paper_fig2_dataset_overview.png",
         "与 Table 1 配套。三个面板各支撑一句话：(a) 类不平衡→基线；"
         "(b) 儿科 δ 占 39% 主导（人群特征，也铺垫频域特征重要性）；"
         "(c) 质量整体高（中位 keep rate 0.91）→ 呼应后面“低质场景欠表达”的局限。")
fig_item(doc, 3, "事件动机图", "fig_label_event_insight.png",
         "Methods 数据小节末（元数据洞察）或 Introduction 动机段。讲“标签–事件耦合”链条："
         "slow wave 阳性率 2.0%/72.6%/97.4%（N/BL/A）几乎完美分离 → 这就是 82 维事件特征块的"
         "来源；同时 BL 居中 → Borderline 难分的伏笔（Results 里回收）。")

h2(doc, "2.3 Results — 单 Agent 基线素材")
fig_item(doc, 4, "二分类基线（单面板重绘）", "paper_fig4_binary_baselines.png",
         "Results 开场先用附表 S3 讲三分类失败（BL F1≈0、Transformer 全预测 Normal）"
         "justify 二分类协议，再引本图。卖点句：四个 agent 全部超基线；"
         "EEGNet 以约 50× 更低的推理成本（11.8 s vs 594.6 s）匹配 LightGBM 精度——"
         "临床部署的性价比论据。")
tbl_label(doc, "Table 2　二分类单 Agent 基线（报告 Table 8）")
append_block(doc, T(blocks_main, "Table 2"))
usage(doc, "与 Fig.4 配套（图给直观对比，表给精确数值含 F1）。"
           "LightGBM 时间被特征提取主导这一点必须在正文说明，避免审稿人误判模型效率。")

h2(doc, "2.4 Results — 特征域消融素材")
fig_item(doc, 5, "特征域消融", "fig_ablation_features.png",
         "特征侧核心图。结论排序 freq > TF > time；event +2.1pt。"
         "inset 面板讲“快评 vs 全量”反转（−2.2 → +2.1pt），这是 C4 贡献的证据，"
         "写法上先给反转现象再给教训（小样本 A/B 无效力）。")
tbl_label(doc, "Table 3　特征域消融（报告 Table 13）")
append_block(doc, T(blocks_main, "Table 3"))
usage(doc, "与 Fig.5 配套；ΔAcc 列直接支撑重要性排序。注意 A1 的 AUC（0.6839）略高于 full，"
           "正文可顺带说明“删除 time 域轻微提升 AUC 但损害 Acc”，体现报告诚实性。")

h2(doc, "2.5 Results — Agent 消融与融合素材")
fig_item(doc, 6, "Agent 消融（两基底）", "fig_ablation_agents.png",
         "agent 侧核心图。三个结论：A6（去 Transformer）在事件基底下达全局最优 0.6134；"
         "去掉 TCN 伤害最大（−5.5pt）；soft voting AUC 最高但 Acc 最差 → 学习型融合"
         "（Stacking）优于规则融合。")
tbl_label(doc, "Table 4　Agent 消融两基底合并表（报告 Table 14+15）")
append_block(doc, T(blocks_merge, "Table 4"))
usage(doc, "本表是全文最重的结果表。写作时说明合并规则：单 agent 行跨基底输入相同数值一致，"
           "只列一次；LightGBM 行两基底分别重训（行名 –event 标注）。全局最优配置"
           "（LightGBM-event + EEGNet + TCN）在表注中显式声明。")

h2(doc, "2.6 Results — 机制消融与显著性素材")
fig_item(doc, 7, "机制消融 + McNemar（双面板重绘）", "paper_fig7_mechanism_ablation.png",
         "机制侧核心图。叙事节奏：先报效应（仲裁 +0.84pt），再报显著性（全部 n.s.），"
         "然后把“阴性”转写为贡献：在 238 被试下 ±2pt 属噪声范围——这正是需要机制级检验"
         "才能得出的结论（C3 贡献的证据）。")
tbl_label(doc, "Table 5　机制消融 + McNemar 合并表（报告 Table 16+17）")
append_block(doc, T(blocks_merge, "Table 5"))
usage(doc, "“点估计 + b/c + 精确 p”一体化的报告范式，本身就是论文的评估规范主张。"
           "表注已含机制统计（触发率、仲裁前后精度），epoch 级与质量分层指向 S7。")

h2(doc, "2.7 Results — 阈值校准素材")
fig_item(doc, 8, "分歧阈值校准（方法学核心图）", "fig_disagreement_calibration.png",
         "建议独立成小节 3.5。四面板“问题→根因→规则→收益”叙事：(a)(b) 旧阈值低于中位数"
         "→每 epoch 必触发；熵分布贴着 ln3 → 熵规则退化（根因）；(c) 触发率 100%→39.7%；"
         "(d) 推理 −39% 且精度不变。Discussion 中升格为可推广方法论。")
tbl_label(doc, "Table 6　校准前后对比（报告 Table 21）")
append_block(doc, T(blocks_main, "Table 6"))
usage(doc, "正文用“三不变一降”概括：精度不变、epoch 精度不变、仲裁贡献不变，触发率与时间大降。"
           "表注说明 grid search（1,116 组合、val replay）与“拒绝 never-arbitrate 以保留仲裁活动”"
           "的成本–性能权衡决策。")

h2(doc, "2.8 Results — 病例展示（可选）")
para(doc, "Fig. 9（可选）　单病例报告样例（SUBJ_0034）——无现成图，需从报告 §10 的输出截图"
          "或绘制简版示意图；投临床类期刊（Clinical Neurophysiology / AIM）强烈建议保留，"
          "投方法类期刊（JNM）可降为补充材料或 Box。", size=10.5, space_after=4)
usage(doc, "内容：Abnormal 36.7% vs Normal 34.4% 的低置信度输出、跨 agent 一致性 0.515、"
           "特征证据链、“建议人工复核”——“低置信度→升级人工”安全设计的具体化，"
           "是临床期刊审稿人的加分项。")

# ============================================================
# 第三部分 附录图表
# ============================================================
h1(doc, "第三部分　附录（Supplementary）图表总稿")
blocks_supp = extract_blocks(BASE / "投稿格式附表S1-S9.docx")

h2(doc, "3.1 附图")
fig_item(doc, "S1", "三分类单 Agent 基线", "paper_figS1_three_class_baselines.png",
         "与附表 S3 配套；正文 3.1 节开头引用以 justify 二分类协议"
         "（BL F1≈0、Transformer 塌缩）。", width=5.2)
fig_item(doc, "S2", "质量分层分析", "paper_figS2_quality_stratification.png",
         "与附表 S7 配套；Limitations 引用：99.2% 高质量 epoch 导致动态权重的目标场景"
         "（低质数据）欠表达。", width=5.2)

h2(doc, "3.2 附表 S1–S9（含英文 caption 与表注）")
SUPP_NOTES = [
    "信号质量统计（报告 T4）——Methods 或附录；支撑“数据整体高质”的声明。",
    "标签元数据分析（报告 T5）——Fig.3 的全量数值版（含 sharp wave、年龄）；"
    "837/1,830 覆盖率与三 split 覆盖率在表注。",
    "三分类基线全表（报告 T7）——justify 二分类的核心证据。",
    "标签来源分组（报告 T10）——Limitations 必引：无 agent 稳定超过组内基线，"
    "标签来源异质性是精度上限的约束。",
    "融合对比（报告 T11）——与 Table 4 互补；soft voting AUC 最高（0.6852）但 Acc 最差，"
    "支撑“以 Acc 为主指标”的决策。",
    "事件特征 A/B：快评 vs 全量（报告 T12）——C4 贡献的直接证据（−2.2→+2.1pt 反转）。",
    "质量分层合并表（报告 T18+19）——与 Fig.S2 配套；n=22/18 仅指示性。",
    "年龄残差化对比（报告 T22）——排除年龄混杂（ΔAUC −0.005）。",
    "慢波检测子任务（报告 T23）——AUC 0.7519 佐证基础特征含慢波信息，"
    "但二分类仅达多数基线（慢波阳性是必要非充分条件）。",
]
for i in range(1, 10):
    tbl_label(doc, f"附表块 {i}　Table S{i}")
    append_block(doc, T(blocks_supp, f"Table S{i}"))
    usage(doc, SUPP_NOTES[i - 1])

# ============================================================
# 第四部分 写作大纲与思路
# ============================================================
h1(doc, "第四部分　写作大纲与思路（IMRaD，段落级）")

h2(doc, "4.1 标题候选")
bullets(doc, [
    "T1（推荐，系统+方法学双关键词）：EEG-MAS: A Quality-Aware Multi-Agent System with "
    "Calibrated Disagreement Arbitration for Pediatric EEG Screening",
    "T2（方法学优先）：Calibrated Disagreement Arbitration for Multi-Agent EEG Screening: "
    "Architecture, Evaluation, and Negative Results",
    "T3（学位论文/中文备用）：面向儿童脑电辅助筛查的多智能体系统：架构、分歧校准与严谨评估",
])

h2(doc, "4.2 Abstract（约 250 词，六句骨架）")
bullets(doc, [
    "① 背景：儿童常规 EEG 判读负担重、专家稀缺。",
    "② 缺口：现有自动化方法以单模型为主、在成人主导的精选基准（TUAB）上评估、"
    "且没有处理模型内部分歧的机制。",
    "③ 方法一：提出 EEG-MAS 三层多智能体架构（协调层调度特征/诊断/验证层；四个异构 agent："
    "mRMR+LightGBM 特征路径与 EEGNet/TCN/Transformer 原始信号路径）。",
    "④ 方法二：提出分歧阈值校准方法论（诊断熵规则在近均匀三分类分布下退化；grid search 校准）。",
    "⑤ 结果：1,597 records / 238 test subjects 真实三档标签；二分类 0.6134（+6.3pt）；"
    "校准使触发率 100%→39.7%、推理 −39%、精度不变；机制消融经 McNemar 检验无显著差异，如实报告。",
    "⑥ 结论：校准方法论与评估规范可推广至投票型多智能体临床系统；低置信度升级人工复核"
    "支持人机协同筛查。",
])

h2(doc, "4.3 Introduction（五段式）")
bullets(doc, [
    "P1 临床钩子：儿童癫痫/神经发育问题的 EEG 筛查需求与判读瓶颈（引流行病学与工作量文献）。",
    "P2 自动判读现状与局限：TUAB 基准系（Schirrmeister 2017 → ChronoNet → Chen 2024）；"
    "单模型/同质集成、成人为主、二分类精选口径——与儿科真实场景（三档标签、标签噪声、"
    "常规采集）的落差。此处挂 Related Work 定位表（Table A，见第七部分）。",
    "P3 多智能体趋势与空白：MDAgents/ColaCare/MAC/DynamiCare 均在 LLM/文本/EHR 层面；"
    "信号级判读的多智能体协作缺失（Table B）。分歧与仲裁恰是信号判读最需要而现有工作没有的。",
    "P4 方案概述：EEG-MAS 一段话（三层 + 四 agent + 条件仲裁 + 人工复核出口）+ Fig.1；"
    "强调三个设计决策对应 P2/P3 的两个缺口。",
    "P5 贡献列表（C1–C4，与 1.2 节一致）+ 论文结构句。",
])

h2(doc, "4.4 Methods（六小节）")
bullets(doc, [
    "2.1 Dataset and preprocessing：数据来源与伦理 → 预处理（19ch/250Hz/2s）→ 三档标签定义 → "
    "划分（Table 1, Fig.2）→ 质量统计（S1）→ 元数据洞察与事件块动机（Fig.3, S2）。"
    "写作注意：把“标签–事件耦合”写成 feature 设计的动机链，而非孤立的描述统计。",
    "2.2 Feature layer：614 维四块构成（time 228 / freq 152 / TF 152 / event 82，正文小表或"
    "文字化）；mRMR-128 选择；事件块特征定义（本报告原 Table 6 压缩进正文）。",
    "2.3 Diagnosis agents：四个 agent 的输入/架构/训练设置；异构性设计理由——"
    "feature-driven 与 signal-driven 的互补性（对应 Fig.1 双路径）。",
    "2.4 Fusion, disagreement and arbitration：SNR 感知动态权重；Stacking meta-learner"
    "（val 概率训练，避免泄漏）；分歧三规则（prob_diff/majority/entropy）；仲裁二队（P1–P4）；"
    "校准流程（1,116 组合 grid search、val replay、成本–性能权衡）。",
    "2.5 Validation layer and explainability：跨 agent 一致性分数；特征证据链；"
    "低置信度→人工复核阈值。",
    "2.6 Evaluation protocol：二分类口径（BL→A，保守性理由）；聚合口径声明段（特征消融报 mean、"
    "agent 消融/融合报 p90，理由：p90 对 Stacking 概率排序更稳健）；test@20 vs @100 成本权衡；"
    "McNemar 精确检验；硬件与时间测量口径。此小节是“评估规范贡献”的方法学落点，务必写实。",
])

h2(doc, "4.5 Results（六小节，对应第二部分素材）")
bullets(doc, [
    "3.1 Single-agent baselines（Fig.4, Table 2, S3, S4）：先三分类失败 → 二分类协议 → "
    "四 agent 超基线 → EEGNet 时间优势。S4（标签来源）可放此或 Limitations。",
    "3.2 Feature-domain ablation（Fig.5, Table 3, S6）：freq>TF>time 排序；event +2.1pt；"
    "快评反转教训（也可移 Discussion）。",
    "3.3 Agent ablation and fusion（Fig.6, Table 4, S5）：A6 全局最优；TCN 最关键；"
    "soft voting 的 AUC/Acc 倒挂 → 主指标选择理由。",
    "3.4 Mechanism ablation with significance（Fig.7, Table 5, S7）：效应 + 显著性 + "
    "噪声范围论证；质量分层阴性结果一句话带过（细节在 S7/Fig.S2）。",
    "3.5 Threshold calibration（Fig.8, Table 6）：独立小节，四面板叙事；"
    "此节是全文方法学高光，写作篇幅应最重。",
    "3.6 Case study（Fig.9 可选）：SUBJ_0034 低置信度输出与人工复核建议。",
])

h2(doc, "4.6 Discussion（六段式）")
bullets(doc, [
    "D1 主要发现总结（一段，数字回收）。",
    "D2 与 TUAB 系工作对比：口径不可比论证（Table A 表注）；强调 1,597 被试在临床 EEG 研究"
    "中的规模位置；0.61 精度反映任务难度（三档真实标签 + 标签噪声上限）而非方法失效。",
    "D3 校准方法学的普适性：任何投票型多分类器系统都可复用该流程（分布诊断 → grid search → "
    "成本–性能权衡）；熵规则在近均匀分布退化的机理对多分类不确定度建模的启示。",
    "D4 阴性结果的价值：机制不显著、动态权重无低质优势——评估规范倡议（点估计+精确检验+"
    "效应量+置信区间一体化报告）。",
    "D5 临床视角：triage 而非诊断的定位；“低置信度→人工复核”的交互成本与安全设计；"
    "与医生工作流的衔接设想（谨慎，不过度承诺）。",
    "D6 Limitations：单中心私有数据、标签来源异质性（S4）、99.2% 高质量 epoch 使低质场景"
    "欠表达（S7）、Borderline 语义模糊、无外部验证集。逐条给出缓解方向。",
])

h2(doc, "4.7 Conclusion 与其他声明")
bullets(doc, [
    "Conclusion 四句：系统 → 校准 → 评估规范 → 临床安全设计。",
    "Ethics：儿童临床数据 IRB 审批号与知情同意口径（按实际填写，投稿硬要求）。",
    "Data & Code availability：数据去标识化后可协商共享；代码 GitHub"
    "（github.com/QM-newer/eeg-multi-agent）+ 一段复现声明（替代报告原 Table 25/26）。",
    "Cover letter 三卖点：① 校准方法论（触发 −60pt、时间 −39%、精度无损）；"
    "② 机制级显著性检验与阴性结果如实报告（契合期刊方法论导向）；"
    "③ 儿科常规 EEG 真实三档标签的稀缺评估场景。",
    "投稿路线：JNM → AIM → BSPC；每次被拒吸收审稿意见迭代后再投，不建议一稿多投。",
])

# ============================================================
# 第五部分 弃用素材与投稿前检查
# ============================================================
h1(doc, "第五部分　弃用素材与投稿前检查清单")

h2(doc, "5.1 弃用素材（防返工清单）")
for t in [
    "报告 Table 2（Key findings 速览）→ 删：内部速览。",
    "报告 Table 6（614 维特征布局）→ 压缩进 Methods 文字。",
    "报告 Table 9（早期 N-vs-A）→ 删：旧 361 维版本，口径混乱风险。",
    "报告 Table 11（融合对比）→ 降为 Table S5。",
    "报告 Table 20（校准分布表）→ 删：已被 Fig.8(a,b) 完整可视化。",
    "报告 Table 24/25/26 → 删：换成 GitHub 链接 + 复现声明。",
    "报告 Fig.4（融合对比图）→ 删：与 Table 4 / Fig.6 三重冗余。",
]:
    para(doc, "• " + t, size=10, space_after=2, indent=12)

h2(doc, "5.2 投稿前检查清单")
bullets(doc, [
    "① Methods 聚合口径声明段（mean vs p90 及理由）——必写。",
    "② test@20 vs @100 采样口径说明——必写。",
    "③ 最佳配置混淆矩阵——尚缺！临床期刊几乎必查 per-class 表现"
    "（数据已在 subject_level_eval.json 的 confusion_matrix 字段，可随时生成）。",
    "④ Related Work 定位表——已完成（本稿第七部分，含核实清单）。",
    "⑤ 伦理声明 + 数据可用性声明——投稿前补齐。",
    "⑥ 图件齐备：主文 8 图 + 附图 2 张已全部就绪（Fig.9 可选待定）。",
])

# ============================================================
# 第六部分 Related Work 对比表（横向页）
# ============================================================
h1(doc, "第六部分　Related Work 对比表（Table A / Table B，横向页）")
para(doc, "详细版（含数字核实清单与 gap 陈述英文草稿）见 RelatedWork对比表.md。"
          "标 [转引] 的数字投稿前需回原始文献核对。", size=9.5, italic=True, space_after=10)

# 切横向页
land = doc.add_section(WD_SECTION.NEW_PAGE)
land.orientation = WD_ORIENT.LANDSCAPE
w, h = land.page_width, land.page_height
land.page_width, land.page_height = h, w
land.left_margin = land.right_margin = Pt(54)

h3(doc, "Table A　自动 EEG 异常判读方法定位表")
rows_a = [
    ["Study", "Method family", "Dataset (population)", "Task / protocol",
     "Reported performance", "Key differences vs. EEG-MAS"],
    ["Schirrmeister et al. 2017", "End-to-end deep ConvNet (Deep4/Shallow)",
     "TUH Abnormal (TUAB; adult-dominant)", "Binary abnormal screening", "Acc 85.4%",
     "Single end-to-end model; curated binary labels; no uncertainty or escalation"],
    ["Roy et al. 2019", "ChronoNet (CNN + gated RNN)", "TUAB", "Binary",
     "Acc 86.6% [转引]", "Single deep model; same protocol caveats"],
    ["Amin / Albaqami / Khan 2019–2023", "Transfer learning & CNN hybrids",
     "TUAB", "Binary", "Acc 86.2–88.8% [转引]", "Architecture-centric single models"],
    ["Chen et al. 2024", "Multi-domain feature fusion + GBDT (CatBoost)",
     "TUAB v3.0.1", "Binary", "Acc ≈ 90%",
     "Closest methodologically; single feature-driven pipeline; no deep-agent collaboration or "
     "disagreement handling"],
    ["ADHD/CD-NET 2024", "Explainable deep network",
     "Private pediatric + public (n=123/121)", "ADHD/CD vs. HC", "Acc 93.7%",
     "Pediatric but disease-specific healthy-vs-patient; small n"],
    ["vEpiNetV2 2025 (BMC Medicine)", "Multimodal deep IED detection",
     "Prospective, 3 centers", "IED (event) detection",
     "AUC 0.96–0.98; FPR 0.16–0.31/min @80% sens.",
     "Event-level detection (parallels EventAgent motivation); no record-level verdict or "
     "multi-agent voting"],
    ["NeoNaid 2026", "Neonatal pipeline with QC gating", "2 centers",
     "FBA estimation / sleep staging", "FBA MAE 0.50–0.55 wk; κ 0.87–0.89",
     "Demonstrates QC value (parallels step 1); different tasks"],
    ["EEG-MAS (ours)",
     "Multi-agent: mRMR+LightGBM (614-d incl. 82-d event block) + EEGNet/TCN/Transformer + "
     "Stacking; quality-aware weighting; calibrated disagreement-triggered arbitration",
     "Private pediatric routine EEG, 1,597 records / 238 test subjects",
     "3-tier clinical labels (N/BL/A); binary protocol (BL→A)",
     "Binary Acc 0.6134 (+6.3 pt over majority); AUC 0.65; inference −39% via calibration",
     "Signal-level heterogeneous multi-agent fusion; realistic label tiers; calibrated conditional "
     "arbitration; mechanism-level significance testing; low-confidence → human review"],
]
rw_table(doc, rows_a, [80, 118, 108, 82, 105, 145])
para(doc, "表注（英文草稿见 md）：跨研究性能数字不可直接比较——TUAB 系为成人主导精选语料的"
          "二分类口径；本工作为儿科常规 EEG 真实三档标签（Borderline 保守并入 Abnormal 臂），"
          "标签来源异质性约束可达精度。", size=9, italic=True, space_after=14)

h3(doc, "Table B　多智能体医疗 AI 定位表")
rows_b = [
    ["Study", "Framework", "Domain / input", "Evaluation", "Key differences vs. EEG-MAS"],
    ["MDAgents 2024", "Adaptive LLM team; complexity-based recruitment", "Medical QA (text)",
     "Accuracy vs. single LLMs", "LLM-centric; no physiological signal; no calibrated triggering"],
    ["MAC 2025", "4 doctor agents + supervisor, MDT-style debate", "302 rare-disease cases",
     "Accuracy vs. GPT-3.5/4", "Text-only consultation; fixed agent count; no cost–performance "
     "calibration"],
    ["ColaCare 2024", "MetaAgent + DoctorAgents + RAG guidelines", "EHR tabular data",
     "3 EHR datasets", "LLM-orchestrated on structured records; not signal-level"],
    ["DynamiCare 2025", "Dynamic specialist team", "Open-ended medical dialogue",
     "Framework benchmarks", "Interaction-centric; no quantitative clinical endpoint"],
    ["EEG-MAS (ours)",
     "Orchestrator pipeline: quality assessment → dynamic weighting → parallel heterogeneous "
     "diagnosis → weighted voting → calibrated disagreement detection → conditional arbitration → "
     "consistency & explainability",
     "Raw EEG epochs (19 ch, 250 Hz) + engineered features",
     "Subject-level screening on 238 subjects; McNemar exact tests; calibration trade-off",
     "Signal-level multi-agent collaboration; heterogeneous feature/signal agents; honest "
     "negative-result reporting"],
]
rw_table(doc, rows_b, [80, 175, 110, 118, 155])

out = BASE / "论文写作总稿.docx"
doc.save(out)
print("saved:", out)

# ---------- 自检 ----------
chk = Document(out)
print("tables:", len(chk.tables), " images:", len(chk.inline_shapes))
