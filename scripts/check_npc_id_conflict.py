# -*- coding: utf-8 -*-
"""检查新 NPC id 是否与 HEAD 已有定义冲突"""
import sys, io, subprocess, re, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def extract_new_npcs(path):
    """从脚本文件提取 NEW_NPCS dict（用 AST 避免执行副作用）"""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "NEW_NPCS" and isinstance(node.value, ast.Dict):
                    return {k.value: v for k, v in zip(node.value.keys, node.value.values)}
    return {}

m1 = extract_new_npcs(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\scripts\add_flavor_npcs.py")
m2 = extract_new_npcs(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\scripts\add_flavor_npcs2.py")
new_ids = set(m1) | set(m2)
print(f"新 NPC 总数: {len(new_ids)}")

r = subprocess.run(["git", "show", "HEAD:game/data/npcs.py"], capture_output=True, text=True,
                   cwd=r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
head_txt = r.stdout
head_ids = set(re.findall(r'^\s{4}"([a-z0-9_]+)":\s*\{', head_txt, re.M))
print(f"HEAD 已有 NPC: {len(head_ids)}")

conflict = sorted(new_ids & head_ids)
print(f"\n=== 撞 ID 冲突 ({len(conflict)}) ===")
for c in conflict:
    head_def = re.search(rf'"{c}": \{{(.*?)\n    \}}', head_txt, re.S)
    head_name = re.search(r"'name':\s*[\"']([^\"']+)[\"']", head_def.group(1) if head_def else "")
    new_def = m1.get(c) or m2.get(c)
    # 新定义名字（AST 取 name 键）
    new_name = ""
    if new_def:
        for k, v in zip(new_def.keys, new_def.values):
            if getattr(k, "value", "") == "name":
                new_name = v.value
                break
    print(f"  {c}: HEAD='{head_name.group(1) if head_name else '?'}' | 新='{new_name}'")
