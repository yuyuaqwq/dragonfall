# -*- coding: utf-8 -*-
"""T7 只读审计辅助 v7：全表 element 技能扫描（PLAYER/BRANCH/TUTOR/HIDDEN）"""
import io, os, sys, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

base = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data"
with open(os.path.join(base, "skills.py"), "r", encoding="utf-8") as f:
    src = f.read()
tree = ast.parse(src)
names = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        for t in node.targets:
            if isinstance(t, ast.Name):
                names[t.id] = ast.literal_eval(node.value)

def walk(d, owner, path=""):
    out = []
    if isinstance(d, dict):
        if "element" in d and d.get("kind") != "被动" and d.get("element"):
            out.append((path, d.get("name"), d.get("element"), d.get("kind")))
        for k, v in d.items():
            out += walk(v, owner, f"{path}.{k}" if path else str(k))
    return out

for dn in ("PLAYER_SKILLS", "BRANCH_SKILLS", "TUTOR_SKILLS", "_ADD_HIDDEN_SKILLS"):
    for owner, cls_d in (names.get(dn) or {}).items():
        for p, nm, el, kd in walk(cls_d, owner):
            print(f"[{dn}] {owner} {p} → {nm} element={el} kind={kd}")