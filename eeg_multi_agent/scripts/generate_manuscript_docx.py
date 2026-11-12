# -*- coding: utf-8 -*-
"""从 main.tex 生成论文 Word 版(论文正文Word版.docx)。
流程:复制 main.tex 到临时目录 → 预处理 pandoc 友好化
(xltabular→longtable、includegraphics 解析为 PNG、显式 Abstract/References 标题)
→ pandoc --citeproc 转 docx → python-docx 后处理
(Times New Roman、页边距、图尺寸上限、图注/表注样式)→ 校验(图数/表格数/关键数值)。
所有数值仍来自生成的 main.tex,零手抄。"""
import os
import re
import shutil
import tempfile

import fitz  # PyMuPDF:PDF 图栅格化
import pypandoc
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

SRC_DIR = r"c:\Users\23373\Desktop\eeg\data and code\Agent\论文正文LaTeX初稿"
FIG_DIR = os.path.join(SRC_DIR, "figures")
OUT_DOCX = os.path.join(SRC_DIR, "论文正文Word版.docx")

KEY_NUMBERS = ["0.6134", "39.7", "567.3", "0.7519", "614", "Lawhern"]

XLTAB_BEGIN = ("\\begin{xltabular}{\\textwidth}{@{}>{\\footnotesize\\raggedright"
               "\\arraybackslash\\hsize=.85\\hsize}X >{\\footnotesize\\raggedright"
               "\\arraybackslash\\hsize=.80\\hsize}X >{\\footnotesize\\raggedright"
               "\\arraybackslash\\hsize=1.0\\hsize}X >{\\footnotesize\\raggedright"
               "\\arraybackslash\\hsize=.65\\hsize}X >{\\footnotesize\\raggedright"
               "\\arraybackslash\\hsize=1.70\\hsize}X@{}}")


def rasterize_pdf(pdf_path, png_path, dpi=300):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(dpi=dpi)
    pix.save(png_path)
    doc.close()


def build():
    build_dir = tempfile.mkdtemp(prefix="eeg_docx_")
    img_dir = os.path.join(build_dir, "img")
    os.makedirs(img_dir)
    try:
        tex = open(os.path.join(SRC_DIR, "main.tex"), encoding="utf-8").read()

        # --- 预处理 1:去掉 graphicspath(pandoc 不解析) ---
        tex = tex.replace("\\graphicspath{{figures/}}\n", "")

        # --- 预处理 2:xltabular → longtable(简列规格),去掉续页表头/表脚 ---
        assert XLTAB_BEGIN in tex, "xltabular 列规格串未找到,main.tex 可能已变更"
        tex = tex.replace(XLTAB_BEGIN, "\\begin{longtable}{lllll}")
        tex = tex.replace("\\end{xltabular}", "\\end{longtable}")
        tex = tex.replace("\\begin{xltabular}", "\\begin{longtable}")  # 兜底
        tex = re.sub(r"\\endfirsthead.*?\\endlastfoot", "\\\\endfirsthead",
                     tex, flags=re.S)

        # --- 预处理 3:显式 Abstract / References 标题(pandoc 不自动加) ---
        tex = tex.replace("\\begin{abstract}", "\\section*{Abstract}\n")
        tex = tex.replace("\\end{abstract}", "\n")
        tex = tex.replace("\\bibliography{references}",
                          "\\section*{References}\n\\bibliography{references}")

        # --- 预处理 4:includegraphics → img/<name>.png(PDF 栅格化 300dpi) ---
        def repl(m):
            opts, name = m.group(1), m.group(2)
            stem = re.sub(r"\.(png|pdf|jpg)$", "", name)
            src_png = os.path.join(FIG_DIR, stem + ".png")
            src_pdf = os.path.join(FIG_DIR, stem + ".pdf")
            dst = os.path.join(img_dir, stem + ".png")
            if os.path.exists(src_png):
                shutil.copy(src_png, dst)
            elif os.path.exists(src_pdf):
                rasterize_pdf(src_pdf, dst)
            else:
                raise FileNotFoundError(f"figure not found: {stem}")
            return f"\\includegraphics{{{os.path.join('img', stem + '.png').replace(os.sep, '/')}}}"

        tex, n_fig = re.subn(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
                             lambda m: repl(re.match(
                                 r"(\\includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}", m.group(0))),
                             tex)

        with open(os.path.join(build_dir, "main_docx.tex"), "w",
                  encoding="utf-8") as f:
            f.write(tex)
        shutil.copy(os.path.join(SRC_DIR, "references.bib"), build_dir)

        # --- pandoc 转换 ---
        cwd = os.getcwd()
        os.chdir(build_dir)
        try:
            pypandoc.convert_file(
                "main_docx.tex", "docx", format="latex",
                outputfile=OUT_DOCX,
                extra_args=["--citeproc", "--bibliography=references.bib",
                            "--resource-path=."])
        finally:
            os.chdir(cwd)

        # --- 后处理:样式 ---
        doc = Document(OUT_DOCX)
        sec = doc.sections[0]
        sec.left_margin = sec.right_margin = Inches(1)
        sec.top_margin = sec.bottom_margin = Inches(1)

        for st in doc.styles:
            try:
                st.font.name = "Times New Roman"
                rpr = st.element.get_or_add_rPr()
                rf = rpr.get_or_add_rFonts()
                rf.set(qn("w:eastAsia"), "Times New Roman")
            except Exception:
                pass

        def style_or_none(name):
            try:
                return doc.styles[name]
            except KeyError:
                return None

        for nm in ("Normal", "Body Text", "First Paragraph"):
            s = style_or_none(nm)
            if s is not None:
                s.font.size = Pt(11)
                s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for nm in ("Image Caption", "Table Caption", "Caption"):
            s = style_or_none(nm)
            if s is not None:
                s.font.size = Pt(9)
                s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for lvl in range(1, 4):
            s = style_or_none(f"Heading {lvl}")
            if s is not None:
                s.font.size = Pt(14 if lvl == 1 else 12 if lvl == 2 else 11)

        # 图尺寸上限:宽 6.2in,高 8.3in(300dpi 原图过大)
        for shp in doc.inline_shapes:
            w, h = shp.width.inches, shp.height.inches
            scale = min(6.2 / w if w > 6.2 else 1.0,
                        8.3 / h if h > 8.3 else 1.0)
            if scale < 1.0:
                shp.width = Inches(w * scale)
                shp.height = Inches(h * scale)

        # --- 标题编号(镜像 LaTeX:section 1..5,附录 A;带星号节不编号;
        #     \paragraph(Heading 4)不编号) ---
        STARRED_H1 = {"Abstract", "References", "Declarations"}
        APPENDIX_H1 = "Supplementary figures"
        h1_no, h2_no, in_appendix = 0, 0, False
        for p in doc.paragraphs:
            name = p.style.name
            txt = p.text.strip()
            if not txt:
                continue
            if name == "Heading 1":
                if txt in STARRED_H1:
                    in_appendix = False
                    continue
                if txt == APPENDIX_H1:
                    in_appendix = True
                    p.runs[0].text = "A. " + p.runs[0].text
                    continue
                h1_no += 1
                h2_no = 0
                p.runs[0].text = f"{h1_no}. " + p.runs[0].text
            elif name == "Heading 2" and not in_appendix:
                h2_no += 1
                p.runs[0].text = f"{h1_no}.{h2_no}. " + p.runs[0].text

        # --- 图/表注加编号前缀(附录两图用 S1/S2,与正文引用一致) ---
        n_img_cap = 0
        for p in doc.paragraphs:
            if p.style.name == "Image Caption" and p.text.strip():
                n_img_cap += 1
                if n_img_cap <= 8:
                    prefix = f"Figure {n_img_cap}. "
                else:
                    prefix = f"Figure S{n_img_cap - 8}. "
                if p.runs:
                    p.runs[0].text = prefix + p.runs[0].text
        n_tab_cap = 0
        for p in doc.paragraphs:
            if p.style.name == "Table Caption" and p.text.strip():
                n_tab_cap += 1
                if p.runs:
                    p.runs[0].text = f"Table {n_tab_cap}. " + p.runs[0].text

        # --- 附录图引用修正:pandoc 把 \ref{fig:three_class/quality}
        #     解析为内部编号 9/10,改回 S1/S2(仅超链接内文本,
        #     其他编号 9/10 不存在:表≤7、节≤5,安全) ---
        fix_map = {"9": "S1", "10": "S2"}
        n_fixed = 0
        for p in doc.paragraphs:
            for t in p._p.xpath(".//w:hyperlink//w:t"):
                if t.text and t.text.strip() in fix_map:
                    t.text = fix_map[t.text.strip()]
                    n_fixed += 1
        print(f"appendix figure refs fixed (9->S1, 10->S2): {n_fixed}")

        # --- 全文文字统一黑色:所有 run 颜色强制 000000,移除下划线
        #     (pandoc 超链接为蓝色+下划线,标题样式带主题色) ---
        def force_black(element):
            n_u = 0
            for rPr in element.iter(qn('w:rPr')):
                for el in list(rPr.findall(qn('w:u'))):
                    rPr.remove(el)
                    n_u += 1
                color = rPr.find(qn('w:color'))
                if color is None:
                    try:
                        color = rPr.get_or_add_color()
                    except AttributeError:
                        color = rPr.makeelement(qn('w:color'), {})
                        rPr.append(color)
                color.set(qn('w:val'), '000000')
                for attr in (qn('w:themeColor'), qn('w:tint'), qn('w:shade')):
                    if attr in color.attrib:
                        del color.attrib[attr]
            return n_u

        n_u_doc = force_black(doc.element.body)
        n_u_sty = force_black(doc.styles.element)
        print(f"forced black: underlines removed doc/styles = "
              f"{n_u_doc}/{n_u_sty}")

        # --- 字体统一:所有 rFonts 四槽位(ascii/hAnsi/eastAsia/cs)
        #     强制 Times New Roman,清除主题字体引用(asciiTheme 等) ---
        FONT = "Times New Roman"
        THEME_ATTRS = (qn('w:asciiTheme'), qn('w:hAnsiTheme'),
                       qn('w:eastAsiaTheme'), qn('w:cstheme'))
        SLOT_ATTRS = (qn('w:ascii'), qn('w:hAnsi'),
                      qn('w:eastAsia'), qn('w:cs'))

        def force_font(element):
            n_rfonts = 0
            for rPr in element.iter(qn('w:rPr')):
                rFonts = rPr.find(qn('w:rFonts'))
                if rFonts is None:
                    try:
                        rFonts = rPr.get_or_add_rFonts()
                    except AttributeError:
                        rFonts = rPr.makeelement(qn('w:rFonts'), {})
                        rPr.insert(0, rFonts)
                for attr in THEME_ATTRS:
                    if attr in rFonts.attrib:
                        del rFonts.attrib[attr]
                for attr in SLOT_ATTRS:
                    rFonts.set(attr, FONT)
                n_rfonts += 1
            return n_rfonts

        n_f_doc = force_font(doc.element.body)
        n_f_sty = force_font(doc.styles.element)
        print(f"forced font {FONT}: rFonts set doc/styles = "
              f"{n_f_doc}/{n_f_sty}")
        doc.save(OUT_DOCX)

        # --- 校验 ---
        doc = Document(OUT_DOCX)
        full = "\n".join(p.text for p in doc.paragraphs)
        n_tables = len(doc.tables)
        n_imgs = len(doc.inline_shapes)
        missing = [k for k in KEY_NUMBERS if k not in full and
                   not any(k in c.text for t in doc.tables for r in t.rows
                           for c in r.cells)]
        print(f"figures included: {n_fig}")
        print(f"docx inline images: {n_imgs}")
        print(f"docx tables: {n_tables}")
        print(f"missing key numbers: {missing if missing else '无'}")
        assert n_imgs == n_fig, f"图数不符: tex={n_fig} docx={n_imgs}"
        assert not missing, f"关键数值缺失: {missing}"
        # 表格数对账:tex 中 table 环境数(含 xltabular)
        n_tex_tables = tex.count("\\begin{table}") + tex.count("\\begin{longtable}")
        print(f"tex table envs: {n_tex_tables}")
        assert n_tables == n_tex_tables, \
            f"表数不符: tex={n_tex_tables} docx={n_tables}"

        # 黑色统一校验:正文与样式表中不得残留非 000000 颜色或下划线
        def scan_color_underline(element):
            bad_c, n_u = [], 0
            for rPr in element.iter(qn('w:rPr')):
                if rPr.findall(qn('w:u')):
                    n_u += 1
                c = rPr.find(qn('w:color'))
                if c is not None and c.get(qn('w:val')) not in (None, '000000'):
                    bad_c.append(c.get(qn('w:val')))
            return bad_c, n_u

        bad_c1, n_u1 = scan_color_underline(doc.element.body)
        bad_c2, n_u2 = scan_color_underline(doc.styles.element)
        print(f"non-black colors remaining doc/styles: "
              f"{bad_c1 or '无'} / {bad_c2 or '无'}")
        print(f"underlined runs remaining doc/styles: {n_u1}/{n_u2}")
        assert not bad_c1 and not bad_c2, "存在非黑色文字"
        assert n_u1 == 0, "正文仍有下划线"

        # 字体统一校验:所有 rFonts 四槽位 == Times New Roman,无主题字体
        def scan_fonts(element):
            bad, total = [], 0
            for rf in element.iter(qn('w:rFonts')):
                total += 1
                for attr in SLOT_ATTRS + THEME_ATTRS:
                    v = rf.get(attr)
                    if attr in THEME_ATTRS:
                        if v is not None:
                            bad.append((attr.localname, v))
                    elif v != FONT:
                        bad.append((attr.localname, v))
            return bad, total

        bad_f1, t1 = scan_fonts(doc.element.body)
        bad_f2, t2 = scan_fonts(doc.styles.element)
        print(f"rFonts scanned doc/styles: {t1}/{t2}")
        print(f"non-TNR fonts remaining doc/styles: "
              f"{bad_f1 or '无'} / {bad_f2 or '无'}")
        assert not bad_f1 and not bad_f2, f"存在未统一字体: {bad_f1 + bad_f2}"
        print("OK ->", OUT_DOCX)
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


if __name__ == "__main__":
    build()
