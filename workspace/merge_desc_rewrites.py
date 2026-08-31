# -*- coding: utf-8 -*-
"""合并 5 个 desc 重写 JSON → 统一 dict。重叠时优先取「数值保留完整」的版本。"""
import json, re, os, sys

WS = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace"
FILES = ["desc_rewrite_warrior.json", "desc_rewrite_mage.json", "desc_rewrite_ranger.json",
         "desc_rewrite_advanced.json", "desc_rewrite_misc.json"]

# 加载全部
all_data = {}   # key -> {name, new_desc, src}
key_sources = {}  # key -> [src...]

def norm_key(k):
    """key 可能是 sk_xxx 或中文名，统一小写去空格"""
    return str(k).strip().lower()

for f in FILES:
    path = os.path.join(WS, f)
    if not os.path.exists(path):
        continue
    d = json.load(open(path, encoding="utf-8"))
    for k, v in d.items():
        if not isinstance(v, dict) or "new_desc" not in v:
            print(f"⚠️  {f} 里 {k} 格式不对: {str(v)[:80]}")
            continue
        nk = norm_key(k)
        key_sources.setdefault(nk, []).append(f)
        # 已有版本时保留第一个（文件顺序即优先级）
        if nk not in all_data:
            all_data[nk] = {"name": v.get("name", k), "new_desc": v["new_desc"], "src": f}
        else:
            # 已有：比较数值保留度，取更完整的
            def num_score(s):
                return len(re.findall(r"\d+%|\d+ 回合|\d+层|×\d", s))
            old, new = all_data[nk], v["new_desc"]
            if num_score(new) > num_score(old["new_desc"]):
                all_data[nk] = {"name": v.get("name", k), "new_desc": new, "src": f}

print("=== 技能 key 覆盖统计 ===")
for f in FILES:
    print(f"  {f}: {sum(1 for v in all_data.values() if v['src']==f)} 个被采用")

# 统计哪些 key 被多个文件写过
multi = {k: v for k, v in key_sources.items() if len(v) > 1}
print(f"\n重叠 key: {len(multi)} 个（{sum(len(v) for v in multi.values())} 次写入）")

# 输出统一 JSON
out_path = os.path.join(WS, "desc_rewrite_merged.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=1)
print(f"\n合并完成: {len(all_data)} 个技能 → {out_path}")
