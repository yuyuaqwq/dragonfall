# -*- coding: utf-8 -*-
"""把 final_desc_map_v3.json 写回 skills.py（v3）：按技能 name 匹配替换 desc。
策略：按行扫描，对每个含 name 字段的技能块（name 在 desc 前或后），替换 desc。
更稳：按 name 找到块位置，块内找 desc 行替换。
"""
import json, re, os, sys

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
MAP = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace\final_desc_map_v3.json"

fin = json.load(open(MAP, encoding="utf-8"))
src = open(SRC, encoding="utf-8").read()

# 备份
bak = SRC + ".bak_desc_rewrite_v3"
open(bak, "w", encoding="utf-8").write(src)

lines = src.splitlines(keepends=True)

# 找所有 "name": "xxx" 行，往前找同块/附近块的 desc
# 方案：对每个技能 name，找 "name": "中文名" 行号，然后从该行往上找最近的 "desc": 行（在同一个 {} 块内）
# 简化：name 行向上 60 行内找 desc，且 desc 行与 name 行之间没有块结束 "}," 或同级缩进变化

name_lines = []  # (line_idx, name)
for i, ln in enumerate(lines):
    m = re.match(r'^\s*"name"\s*:\s*"([^"]+)"', ln)
    if m:
        name_lines.append((i, m.group(1)))

replaced = set()
not_found = []
for i, nm in name_lines:
    if nm not in fin:
        continue
    nd = fin[nm]["new_desc"]
    # 从 name 行向上找最近的 desc 行（在 40 行内）
    found = False
    # 块起始缩进 = name 行缩进
    nm_indent = len(lines[i]) - len(lines[i].lstrip())
    for k in range(i - 1, max(i - 40, -1), -1):
        ln = lines[k]
        # 遇到缩进更小的行（块外）就停
        stripped = ln.lstrip()
        if not stripped:
            continue
        cur_indent = len(ln) - len(stripped)
        if cur_indent < nm_indent and stripped.startswith("}"):
            break
        dm = re.match(r'^(\s*)"desc"\s*:\s*"(.*)",?\s*$', ln)
        if dm and cur_indent <= nm_indent + 4:
            esc = nd.replace("\\", "\\\\").replace('"', '\\"')
            lines[k] = f'{dm.group(1)}"desc": "{esc}",\n'
            replaced.add(nm)
            found = True
            break
    if not found:
        # 可能 desc 在 name 之后（如林语印记：desc 在前 name 在后）→ 向下找
        for k in range(i + 1, min(i + 40, len(lines))):
            ln = lines[k]
            stripped = ln.lstrip()
            if not stripped:
                continue
            cur_indent = len(ln) - len(stripped)
            if cur_indent < nm_indent and stripped.startswith("}"):
                break
            dm = re.match(r'^(\s*)"desc"\s*:\s*"(.*)",?\s*$', ln)
            if dm and cur_indent <= nm_indent + 4:
                esc = nd.replace("\\", "\\\\").replace('"', '\\"')
                lines[k] = f'{dm.group(1)}"desc": "{esc}",\n'
                replaced.add(nm)
                found = True
                break
    if not found:
        not_found.append(nm)

new_src = "".join(lines)
print(f"替换: {len(replaced)} / {len(fin)}")
print(f"未找到: {len(not_found)}")
for s in not_found[:15]:
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
