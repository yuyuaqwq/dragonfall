# -*- coding: utf-8 -*-
"""对照 merged.json 与 skills.py 真实技能表，找出：漏网技能 / 多余key / 中文名key"""
import json, re, os

WS = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace"
SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
src = open(SRC, encoding="utf-8").read()

# 1. 真实技能表：所有 "sk_xxx": { 出现位置 + 其 name
real_skills = {}  # sk_key -> name
for m in re.finditer(r'"((?:sk|b_)[a-z0-9_]+)"\s*:\s*\{', src):
    sid = m.group(1)
    # 找块内 name 字段（前 200 字符内）
    blk = src[m.end():m.end()+400]
    nm = re.search(r'"name"\s*:\s*"([^"]+)"', blk)
    real_skills[sid] = nm.group(1) if nm else None

# 2. merged
merged = json.load(open(os.path.join(WS, "desc_rewrite_merged.json"), encoding="utf-8"))

# 3. 对比
merged_keys = set(merged.keys())
real_keys = set(real_skills.keys())

# 合并里的 key 是否命中真实技能（sk_ 或 b_ 直接命中，中文名需按 name 匹配）
missing = {}  # 真实技能没被 merged 覆盖
covered_by_sk = set()
covered_by_name = set()
name_to_sk = {}
for sk, nm in real_skills.items():
    if nm:
        name_to_sk.setdefault(nm.strip().lower(), sk)

for mk in merged_keys:
    mkl = mk.strip().lower()
    if mk in real_skills:
        covered_by_sk.add(mk)
    elif mkl in name_to_sk:
        covered_by_name.add(name_to_sk[mkl])
    # 否则多余 key

for sk in real_keys:
    if sk not in covered_by_sk and sk not in covered_by_name:
        missing[sk] = real_skills[sk]

# 多余的 merged key（既不是 sk_ 也不是有效中文名）
extra = [mk for mk in merged_keys
         if mk not in real_skills and mk.strip().lower() not in name_to_sk]

print(f"真实技能: {len(real_skills)}")
print(f"merged 覆盖（直接 sk_ key）: {len(covered_by_sk)}")
print(f"merged 覆盖（中文名映射）: {len(covered_by_name)}")
print(f"总覆盖: {len(covered_by_sk | covered_by_name)}")
print(f"\n=== 漏网技能（真实但没被覆盖）: {len(missing)} ===")
for sk, nm in sorted(missing.items()):
    print(f"  {sk} ({nm})")
print(f"\n=== 多余 key（merged 有但真实技能表没有）: {len(extra)} ===")
for mk in extra[:40]:
    print(f"  {mk}")
