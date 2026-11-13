# Reconstruct the SANITIZED exclusion list (SUBJ ids only, NO names/ages)
# by diffing the E: manifest against the authoritative local feature splits.
# Privacy: never prints record_id / folder columns (they embed name fragments).
import csv, json, os
import numpy as np

MANIFEST = r"E:/eeg_asd_cache/epochs/manifest.csv"
FEAT = r"cache/features"

def sids_from_meta(path):
    z = np.load(path, allow_pickle=True)
    key = next((k for k in z.files if "sid" in k.lower() or "subj" in k.lower()), None)
    if key is None:
        raise KeyError(f"no sid-like key in {path}: {z.files}")
    arr = z[key]
    return set(str(s) for s in np.unique(arr)), key

meta = {}
for split in ("train", "val", "test"):
    p = os.path.join(FEAT, f"{split}_meta.npz")
    s, key = sids_from_meta(p)
    meta[split] = s
    print(f"{split}: features unique sid count = {len(s)} (key={key})")
    sample = sorted(s)[:2]
    print("   sample:", [x[:14] + "..." if len(x) > 14 else x for x in sample])

man = {}
with open(MANIFEST, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r.get("status") in ("ok", "skipped_exists") and int(r.get("n_epochs") or 0) > 0:
            man.setdefault(r["split"], set()).add(r["subject_id"])
for split in ("train", "val", "test"):
    print(f"{split}: manifest subject count = {len(man.get(split, set()))}")

excluded = {}
for split in ("train", "val", "test"):
    d = man.get(split, set()) - meta[split]
    if d:
        excluded[split] = sorted(d)
all_sub = sorted(set().union(*excluded.values())) if excluded else []
print("\nExcluded subjects per split (SUBJ codes only):")
for k, v in excluded.items():
    print(f"  {k}: {len(v)} -> {v}")
print("TOTAL excluded subjects:", len(all_sub))

# sanity: features side must never contain an excluded subject
for split in ("train", "val", "test"):
    leak = meta[split] & set(all_sub)
    assert not leak, f"LEAK in {split}: {leak}"
print("no-leak check OK")

spec = {
    "note": "SANITIZED exclusion list (C6 age>=18): subject codes only. "
            "Reconstructed 2026-11-13 from split diff; contains NO names, ages, or name-derived ids.",
    "subject_ids": all_sub,
    "record_ids": [],
}
out = os.path.join("..", "data", "exclude_records.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)
print("written:", os.path.abspath(out))
