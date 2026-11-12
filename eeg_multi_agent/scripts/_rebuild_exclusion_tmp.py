# -*- coding: utf-8 -*-
"""重建 exclude_records.json（修正版）

背景：
    旧名单按 C6 批注的 folder 旧名（后改名）做 record linkage，得到 9 条 record_id，
    并映射出一组错误的 subject_id（SUBJ_0286 等，实际为 2-7 岁儿童）。
    folder 在 E: 盘脱敏改名后，旧 record_id 全部失配 → record_id 过滤无效；
    错误 subject_id 过滤误删了 8 名儿童受试者。

修正口径（与 age_correction_experiment.load_age_map 同源）：
    subject_master.csv 的 ANON_XXXX 与 epoch manifest 的 SUBJ_XXXX 序号一致，
    取 age >= 18 的受试者，排除其名下全部记录。
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd

MANIFEST = "E:/eeg_asd_cache/epochs/manifest.csv"
SM = "data/subject_master.csv"
OUT = "data/exclude_records.json"

sm = pd.read_csv(SM)
adult = sm[sm["age"] >= 18][["anonymous_id", "name_raw", "age", "label_name"]]
adult_sids = ["SUBJ_" + a.split("_")[-1] for a in adult["anonymous_id"]]

man = pd.read_csv(MANIFEST)
hits = man[man["subject_id"].isin(adult_sids)][
    ["record_id", "subject_id", "split", "label_name"]]

# 构建 record_id -> age 映射
sid2age = {"SUBJ_" + r["anonymous_id"].split("_")[-1]: float(r["age"])
           for _, r in adult.iterrows()}
ages = {rid: sid2age[sid] for rid, sid in zip(hits["record_id"], hits["subject_id"])}

payload = {
    "reason": "age>=18 per subject_master.csv (ANON<->SUBJ serial-consistent mapping); "
              "rebuilt 2026-11-12 after folder-rename invalidated the old record-linkage IDs",
    "ages": ages,
    "record_ids": hits["record_id"].tolist(),
    "subject_ids": sorted(set(hits["subject_id"].tolist())),
    "subject_details": {
        sid: {"name": str(adult[adult["anonymous_id"] == "ANON_" + sid.split("_")[-1]].iloc[0]["name_raw"]),
              "age": sid2age[sid]}
        for sid in sorted(set(hits["subject_id"].tolist()))
    },
    "split_counts": hits["split"].value_counts().to_dict(),
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)

print("排除受试者 %d 人，记录 %d 条" % (len(payload["subject_ids"]), len(payload["record_ids"])))
print("分集:", payload["split_counts"])
for sid, d in payload["subject_details"].items():
    n = (hits["subject_id"] == sid).sum()
    print("  %s  %s  age=%s  记录数=%d" % (sid, d["name"], d["age"], n))

# 验证 EpochCache 口径
from data.epoch_cache import EpochCache
cache = EpochCache()
rows = cache.rows
print("\nEpochCache 排除后: 总记录 %d" % len(rows))
for sp in ["train", "val", "test"]:
    n = sum(1 for r in rows if r["split"] == sp)
    print("  %s: %d 条记录" % (sp, n))
# 被误排除的 8 人是否恢复
restored = [s for s in ["SUBJ_0286", "SUBJ_0293", "SUBJ_0459", "SUBJ_0530",
                        "SUBJ_0549", "SUBJ_0742", "SUBJ_0799", "SUBJ_1735"]
            if any(r["subject_id"] == s for r in rows)]
print("\n原误排除者已恢复: %s" % restored)
# 确认成人已全部移除
still = [r["record_id"] for r in rows if r["subject_id"] in
         ["SUBJ_0146", "SUBJ_0157", "SUBJ_0244", "SUBJ_0290", "SUBJ_0298",
          "SUBJ_0400", "SUBJ_0426", "SUBJ_0683", "SUBJ_0886"]]
print("成人残留: %s" % (still if still else "无 ✓"))
