# -*- coding: utf-8 -*-
"""终极合并 v3：ast 解析，收集所有含 name+desc 的技能块（不限 key 前缀，覆盖分支/导师/隐藏）。
输出 final_desc_map_v3.json
"""
import ast, json, os

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
WS = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace"
src = open(SRC, encoding="utf-8").read()
tree = ast.parse(src)

# 顶层 dict
top = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        for t in node.targets:
            if isinstance(t, ast.Name):
                top[t.id] = node.value

def has_field(d: ast.Dict, name: str) -> bool:
    return any(isinstance(k, ast.Constant) and k.value == name for k in d.keys)

def get_field(d: ast.Dict, name: str):
    for k, v in zip(d.keys, d.values):
        if isinstance(k, ast.Constant) and k.value == name and isinstance(v, ast.Constant):
            return v.value
    return None

def collect(d: ast.Dict, out: dict, path=""):
    """递归：任何含 name+desc 的 dict 视为技能块；记录其 key（可能是中文名）"""
    for k, v in zip(d.keys, d.values):
        if not (isinstance(k, ast.Constant) and isinstance(v, ast.Dict)):
            continue
        key = str(k.value)
        # 技能块：有 name 字段 + desc 字段
        if has_field(v, "name") and has_field(v, "desc"):
            nm = get_field(v, "name")
            dsc = get_field(v, "desc")
            if nm and dsc:
                out.setdefault(nm, {"key": key, "name": nm, "desc": dsc})
        # 递归
        collect(v, out, path + "/" + key)

real = {}
for name, d in top.items():
    collect(d, real)

print(f"ast 解析真实技能（按 name）: {len(real)}")

# merged
merged = json.load(open(os.path.join(WS, "desc_rewrite_merged.json"), encoding="utf-8"))

def find_new_desc(name):
    versions = []
    for mk, mv in merged.items():
        if mv.get("name") and mv["name"] == name:
            versions.append(mv["new_desc"])
        elif mk.strip() == name:
            versions.append(mv["new_desc"])
    if not versions:
        return None
    return max(versions, key=len)

final = {}
no_cover = []
for nm, info in real.items():
    nd = find_new_desc(nm)
    if nd:
        final[nm] = {"key": info["key"], "name": nm, "new_desc": nd}
    else:
        no_cover.append(nm)

print(f"覆盖: {len(final)} / {len(real)}")
print(f"漏网: {len(no_cover)}")
for nm in no_cover:
    print(f"  {nm}")

with open(os.path.join(WS, "final_desc_map_v3.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print(f"\n→ final_desc_map_v3.json ({len(final)} 技能)")
