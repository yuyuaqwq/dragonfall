# -*- coding: utf-8 -*-
"""最终合并：把 merged.json 映射到 115 个真实技能 key。
策略：每个真实技能 sk_key，从 merged 里收集所有版本（sk_key 直取 + name 匹配中文名 key），
取数值保留度最高 + 字数适中的版本。
输出 final_desc_map.json: {sk_key: {"name": ..., "new_desc": ...}}
"""
import json, re, os

WS = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace"
SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
src = open(SRC, encoding="utf-8").read()

# 真实技能表
real_skills = {}
for m in re.finditer(r'"((?:sk|b_)[a-z0-9_]+)"\s*:\s*\{', src):
    sid = m.group(1)
    blk = src[m.end():m.end()+400]
    nm = re.search(r'"name"\s*:\s*"([^"]+)"', blk)
    real_skills[sid] = nm.group(1) if nm else sid

merged = json.load(open(os.path.join(WS, "desc_rewrite_merged.json"), encoding="utf-8"))

def num_score(s):
    return len(re.findall(r"\d+%|\d+ 回合|\d+层|×\d|\d+点|CD\s*\d+", s))

def pick_best(versions):
    """versions: [(new_desc, name), ...] → 最优版本"""
    if not versions:
        return None
    # 排序：数值保留度最高优先，其次字数适中（30-70），再次短
    def quality(v):
        desc = v[0]
        ns = num_score(desc)
        ln = len(desc)
        if 30 <= ln <= 70:
            ln_score = 1.0
        elif ln < 30:
            ln_score = 0.5
        else:
            ln_score = 0.3
        return (ns, ln_score, -abs(ln-50))
    versions.sort(key=quality, reverse=True)
    return versions[0]

final = {}
no_cover = []
for sk, nm in real_skills.items():
    versions = []
    # 直接 sk_ key
    if sk in merged and "new_desc" in merged[sk]:
        versions.append((merged[sk]["new_desc"], merged[sk].get("name", nm)))
    # name 匹配
    nm_low = (nm or "").strip().lower()
    for mk, mv in merged.items():
        if mk.strip().lower() == nm_low and "new_desc" in mv:
            versions.append((mv["new_desc"], mv.get("name", nm)))
        elif mv.get("name") and mv["name"].strip().lower() == nm_low:
            versions.append((mv["new_desc"], mv["name"]))
    if versions:
        best, name = pick_best(versions)
        final[sk] = {"name": nm, "new_desc": best}
    else:
        no_cover.append(sk)

print(f"覆盖: {len(final)} / {len(real_skills)}")
print(f"漏网: {len(no_cover)}")
for sk in no_cover:
    print(f"  {sk} ({real_skills[sk]})")

with open(os.path.join(WS, "final_desc_map.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print(f"\n→ final_desc_map.json ({len(final)} 技能)")
