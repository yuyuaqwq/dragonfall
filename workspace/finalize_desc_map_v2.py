# -*- coding: utf-8 -*-
"""终极合并 v2：用 ast 解析 skills.py 拿真实技能表，从 merged 按 name 匹配取新 desc。
覆盖：PLAYER_SKILLS + BRANCH_SKILLS + _ADD_HIDDEN_SKILLS + TUTOR_SKILLS 所有技能块。
输出 final_desc_map_v2.json: {真实sk_key: {"name": ..., "new_desc": ...}}
"""
import ast, json, os

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
WS = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace"
src = open(SRC, encoding="utf-8").read()
tree = ast.parse(src)

# 1. 顶层 dict 名
top = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        for t in node.targets:
            if isinstance(t, ast.Name):
                top[t.id] = node.value

# 2. 遍历所有 dict 里的技能块：key 是 sk_xxx / b_xxx（或 TUTOR 里嵌套的）
def collect_skill_dicts(d: ast.Dict, out: dict):
    """递归收集所有 {skill_key: {...dict}}，key 以 sk_/b_ 开头或块里有 name 字段"""
    for k, v in zip(d.keys, d.values):
        if not (isinstance(k, ast.Constant) and isinstance(v, ast.Dict)):
            continue
        key = str(k.value)
        # 技能块特征：key 以 sk_/b_ 开头，或 v 里有 name 字段
        has_name = any(isinstance(kk, ast.Constant) and kk.value == "name"
                       for kk in v.keys)
        if (key.startswith("sk_") or key.startswith("b_")) and has_name:
            # 提取 name + desc
            fields = {}
            for kk, vv in zip(v.keys, v.values):
                if isinstance(kk, ast.Constant) and isinstance(vv, ast.Constant):
                    fields[str(kk.value)] = vv.value
            out[key] = fields
        # 递归（技能块内部可能有嵌套，如 TUTOR 的 {职业: {技能: ...}}）
        collect_skill_dicts(v, out)

real = {}
for name, d in top.items():
    collect_skill_dicts(d, real)

print(f"ast 解析真实技能: {len(real)}")

# 3. merged
merged = json.load(open(os.path.join(WS, "desc_rewrite_merged.json"), encoding="utf-8"))

# 4. 按 name 匹配（merged 的 key 可能是 sk_/b_ 或中文名；优先 value.name 匹配）
def find_new_desc(sk_key, name):
    versions = []
    # 直接 key
    if sk_key in merged and "new_desc" in merged[sk_key]:
        versions.append(merged[sk_key]["new_desc"])
    # name 匹配
    for mk, mv in merged.items():
        if mv.get("name") and mv["name"] == name:
            versions.append(mv["new_desc"])
    if not versions:
        return None
    # 取最长（通常最完整）
    return max(versions, key=len)

final = {}
no_cover = []
for sk, fields in real.items():
    name = fields.get("name", sk)
    nd = find_new_desc(sk, name)
    if nd:
        final[sk] = {"name": name, "new_desc": nd}
    else:
        no_cover.append((sk, name))

print(f"覆盖: {len(final)} / {len(real)}")
print(f"漏网: {len(no_cover)}")
for sk, nm in no_cover:
    print(f"  {sk} ({nm})")

with open(os.path.join(WS, "final_desc_map_v2.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print(f"\n→ final_desc_map_v2.json ({len(final)} 技能)")
