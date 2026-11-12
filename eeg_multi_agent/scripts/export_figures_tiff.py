# -*- coding: utf-8 -*-
"""论文图 TIFF 导出:10 张论文图 → Agent\\论文图片TIFF\\(每图一个独立 TIFF,
300 dpi,LZW 无损压缩,RGB)。源为 outputs/figures 下 300dpi PNG。
注:本机 PIL/libtiff 压缩编码器损坏(exit 0xC0000409),故用 tifffile 写 LZW。"""
import os
from pathlib import Path

import numpy as np
from PIL import Image
import tifffile

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "outputs" / "figures"
DST = Path(r"c:\Users\23373\Desktop\eeg\data and code\Agent\论文图片TIFF")
DST.mkdir(exist_ok=True)

# (TIFF 文件名, 源 PNG)
MAPPING = [
    ("Fig1_system_architecture", "fig_system_architecture_layered.png"),
    ("Fig2_dataset_overview", "paper_fig2_dataset_overview.png"),
    ("Fig3_event_positive_rates", "fig_label_event_insight.png"),
    ("Fig4_binary_baselines", "paper_fig4_binary_baselines.png"),
    ("Fig5_feature_ablation", "fig_ablation_features.png"),
    ("Fig6_agent_ablation", "fig_ablation_agents.png"),
    ("Fig7_mechanism_ablation", "paper_fig7_mechanism_ablation.png"),
    ("Fig8_threshold_calibration", "fig_disagreement_calibration.png"),
    ("FigS1_three_class_baselines", "paper_figS1_three_class_baselines.png"),
    ("FigS2_quality_stratification", "paper_figS2_quality_stratification.png"),
]


def main():
    n = 0
    for tif_name, src_name in MAPPING:
        src = SRC / src_name
        assert src.exists(), f"missing source: {src}"
        img = Image.open(src)
        if img.mode != "RGB":
            img = img.convert("RGB")
        out = DST / f"{tif_name}.tif"
        arr = np.asarray(img)
        # resolution=(300,300) + INCH:整数有理数,精确 300 dpi
        tifffile.imwrite(out, arr, compression="lzw",
                         resolution=(300, 300),
                         resolutionunit="INCH", photometric="rgb")
        n += 1
    # 校验:重新打开检查格式/压缩/尺寸/dpi
    print(f"exported {n} tiff files -> {DST}")
    for tif_name, _ in MAPPING:
        p = DST / f"{tif_name}.tif"
        with tifffile.TiffFile(p) as tf:
            page = tf.pages[0]
            w, h = page.shape[1], page.shape[0]
            comp = "lzw" if page.compression.name == "LZW" else page.compression.name
            num, den = page.tags["XResolution"].value
            dpi = num / den
            kb = os.path.getsize(p) / 1024
        assert comp == "lzw" and abs(dpi - 300) < 1, f"{tif_name}: dpi={dpi}"
        print(f"  {tif_name}.tif  {w}x{h}px  {dpi:.0f}dpi  {comp}  {kb:.0f}KB")
    print("OK all tiff verified")


if __name__ == "__main__":
    main()
