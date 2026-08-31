# -*- coding: utf-8 -*-
"""v3.5 终极替换：ast 精确定位每个技能块的 desc 行号，逐行替换。最稳。"""
import ast, json, os, sys

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
MAP = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace\final_desc_map_v3.json"

fin = json.load(open(MAP, encoding="utf-8"))
src = open(SRC, encoding="utf-8").read()
lines = src.splitlines(keepends=True)

# 备份
bak = SRC + ".bak_desc_rewrite_v3"
open(bak, "w", encoding="utf-8").write(src)

tree = ast.parse(src)

# 递归找所有技能块（含 name+desc 的 dict），记录 desc 的 (lineno-1)
desc_lines = {}  # name -> [line_idx...]（同名可能多个，如共享被动）

def walk(d: ast.Dict):
    for k, v in zip(d.keys, d.values):
        if not (isinstance(k, ast.Constant) and isinstance(v, ast.Dict)):
            continue
        fields = {}
        for kk, vv in zip(v.keys, v.values):
            if isinstance(kk, ast.Constant):
                fields[str(kk.value)] = vv
        nm = fields.get("name")
        desc_node = None
        for kk, vv in zip(v.keys, v.values):
            if isinstance(kk, ast.Constant) and kk.value == "desc" and isinstance(vv, ast.Constant):
                desc_node = vv
        if nm and desc_node:
            # lineno 是 1-based
            desc_lines.setdefault(nm.value, []).append(desc_node.lineno - 1)
        walk(v)

for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        walk(node.value)

print(f"ast 定位到 desc 行: {sum(len(v) for v in desc_lines.values())} 处（{len(desc_lines)} 技能名）")

# 替换
replaced = []
missing = []
for nm, ndata in fin.items():
    if nm not in desc_lines:
        missing.append(nm)
        continue
    for ln in desc_lines[nm]:
        old = lines[ln]
        # 校验是 desc 行
        if '"desc"' not in old:
            print(f"⚠️ 行 {ln+1} 不是 desc 行（{nm}）: {old[:60]}")
            continue
        # 保留原缩进
        indent = old[:len(old) - len(old.lstrip())]
        esc = ndata["new_desc"].replace("\\", "\\\\").replace('"', '\\"')
        lines[ln] = f'{indent}"desc": "{esc}",\n'
        replaced.append(nm)

new_src = "".join(lines)
print(f"替换: {len(replaced)} 处（去重 {len(set(replaced))} 技能名）")
print(f"缺失: {len(missing)}")
for s in missing[:10]:
    print(f"  {s}")

try:
    compile(new_src, SRC, "exec")
    open(SRC, "w", encoding="utf-8").write(new_src)
    print("✅ 语法 OK，已写入")
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    open(SRC, "w", encoding="utf-8").write(src)
    print("已回滚")
    sys.exit(1)
