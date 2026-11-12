# -*- coding: utf-8 -*-
"""生成投稿格式合并表（Table 4 = 报告 T14+T15）。机制消融表已移入附表 S10。

数据来源（运行时读取，零手抄）：
  eeg_multi_agent/outputs/ablation_agents.json  -> Table 4
  eeg_multi_agent/outputs/ablation_system.json  -> Table 5

格式：期刊三线表（booktabs 风格：上下粗线 + 表头下细线，无竖线），
英文 caption 置于表上方（期刊惯例），Times New Roman。
输出：Agent/投稿格式合并表.docx
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BASE = Path(__file__).resolve().parents[2] if False else Path(r"c:\Users\23373\Desktop\eeg\data and code\Agent")
AA = json.load(open(BASE / "eeg_multi_agent/outputs/ablation_agents.json", encoding="utf-8"))
ASY = json.load(open(BASE / "eeg_multi_agent/outputs/ablation_system.json", encoding="utf-8"))

B1 = AA["bases"]["lightgbm"]["variants"]          # Base 1: 532-d
B2 = AA["bases"]["lightgbm_event"]["variants"]    # Base 2: 614-d with event


# ---------- docx helpers ----------
def set_font(run, size=9.5, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    r = run._element.rPr.rFonts
    r.set(qn("w:eastAsia"), "Microsoft YaHei")


def para(doc, text, size=10.5, bold=False, italic=False, align=None,
         space_after=6, color=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    set_font(run, size=size, bold=bold, italic=italic)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p


def _set_borders(el, edges):
    """edges: dict edge -> size(pt*8) or None(=no border)"""
    pr = el.find(qn("w:tblPr")) if el.tag == qn("w:tbl") else el.get_or_add_tcPr()
    if el.tag == qn("w:tbl"):
        tag = "w:tblBorders"
        borders = pr.find(qn(tag))
        if borders is None:
            borders = OxmlElement(tag)
            pr.append(borders)
    else:
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


def three_line_table(doc, rows, bold_cells, col_widths, header_rows=1):
    """rows: list[list[str]]; bold_cells: set[(r,c)]; 三线表"""
    n_r, n_c = len(rows), len(rows[0])
    tbl = doc.add_table(rows=n_r, cols=n_c)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    # 表级边框：上下粗线
    _set_borders(tbl._tbl, {"top": 12, "bottom": 12, "left": None,
                            "right": None, "insideH": None, "insideV": None})
    for r in range(n_r):
        row = tbl.rows[r]
        row.height = Pt(16)
        for c in range(n_c):
            cell = tbl.cell(r, c)
            cell.width = col_widths[c]
            # 表头行底边细线
            if r == header_rows - 1:
                _set_borders(cell._tc, {"bottom": 6})
            p = cell.paragraphs[0]
            p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if c == 0
                           else WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(rows[r][c])
            set_font(run, size=9.5, bold=(r, c) in bold_cells)
    return tbl


def note(doc, lines):
    for i, t in enumerate(lines):
        para(doc, t, size=8.5, italic=False, space_after=2)
    para(doc, "", size=4, space_after=0)


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Pt(72)

# ---------- 文档头（中文工作稿说明） ----------
para(doc, "投稿格式合并表（工作稿）", size=14, bold=True, space_after=4)
para(doc, "Table 4 = 实验报告 Table 14 + Table 15（Agent 消融 + 融合对比，部署基底）",
     size=9, space_after=2)
para(doc, "数据读取自 outputs/ablation_agents.json 与 ablation_system.json（零手抄）。"
          "投稿时删除本页说明，保留两表及其 caption 与表注。", size=9, space_after=12)

# ================= Table 4 =================
para(doc, "Table 4", size=10, bold=True, space_after=2)
para(doc, "Diagnosis-agent ablation and fusion comparison (Stacking meta-learner, binary "
          "protocol, subject-level mean aggregation, test@10, n = 236, majority baseline 0.5466).",
     size=10, space_after=8)

rows4 = [["Variant", "Acc", "macro F1", "AUC"]]
order = [
    ("Stacking (4 agents)", "stacking_full"),
    ("A4: w/o EEGNet", "A4_no_eegnet"),
    ("A5: w/o TCN", "A5_no_tcn"),
    ("A6: w/o Transformer", "A6_no_transformer"),
    ("A9: equal-weight soft voting", "A9_soft_voting_equal"),
    ("Hard voting (tie → Normal)", "hard_voting"),
    ("Single: LightGBM", "single_lightgbm"),
    ("Single: EEGNet", "single_eegnet"),
    ("Single: TCN", "single_tcn"),
    ("Single: Transformer", "single_transformer"),
]
for label, k in order:
    v = B1[k]
    rows4.append([label, f"{v['acc']:.4f}", f"{v['macro_f1']:.4f}",
                  "—" if v["auc"] is None else f"{v['auc']:.4f}"])

# 每列最优加粗（hard voting 的 AUC 为 null 不参与）
bold4 = set()
for c, key in [(1, "acc"), (2, "macro_f1"), (3, "auc")]:
    best_val, best_r = None, None
    for r, (_, k) in enumerate(order, start=1):
        v = B1[k][key]
        if v is None:
            continue
        if best_val is None or v > best_val:
            best_val, best_r = v, r
    bold4.add((best_r, c))

three_line_table(doc, rows4, bold4,
                 col_widths=[Pt(170), Pt(80), Pt(90), Pt(80)])

note(doc, [
    "Notes. Base = LightGBM on the deployed 532-d base features (mRMR-128); the Stacking meta-learner "
    "(LightGBM) is trained on validation-set agent probabilities. An event-feature (614-d) base was also "
    "evaluated but is superseded by the feature-domain ablation (main-text Table 3), which shows the "
    "event block is harmful; those results are therefore omitted here. Best per column in bold; "
    "hard-voting AUC is undefined (—). No fused configuration exceeds the best single agent (EEGNet "
    "0.6441); removing EEGNet (A4) is the most damaging ablation, falling to the majority baseline.",
])

out = BASE / "投稿格式合并表.docx"
doc.save(out)
print("saved:", out)
