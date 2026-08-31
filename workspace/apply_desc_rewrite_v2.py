# -*- coding: utf-8 -*-
"""把 final_desc_map_v2.json 写回 skills.py（v2）：按技能块替换 desc。"""
import json, re, os, sys

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
MAP = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace\final_desc_map_v2.json"

fin = json.load(open(MAP, encoding="utf-8"))
src = open(SRC, encoding="utf-8").read()

# 备份
bak = SRC + ".bak_desc_rewrite_v2"
open(bak, "w", encoding="utf-8").write(src)

# 按技能块定位 desc 行（用行号法，块起始到下一块起始）
lines = src.splitlines(keepends=True)
block_pat = re.compile(r'^(\s*)"((?:sk|b_)[a-z0-9_]+)"\s*:\s*\{', re.M)

blocks = []
for m in block_pat.finditer(src):
    blocks.append((m.group(2), src[:m.start()].count("\n")))

replaced = []
not_found = []
for sid, start_ln in blocks:
    if sid not in fin:
        continue
    # 块范围结束：下一个块或文件尾
    end_ln = len(lines)
    for sid2, start_ln2 in blocks:
        if start_ln2 > start_ln:
            end_ln = start_ln2
            break
    # 在块内找 "desc": "..." 行
    for k in range(start_ln, min(end_ln, len(lines))):
        dm = re.match(r'^(\s*)"desc"\s*:\s*"(.*)",?\s*$', lines[k])
        if dm:
            new_desc = fin[sid]["new_desc"]
            esc = new_desc.replace("\\", "\\\\").replace('"', '\\"')
            lines[k] = f'{dm.group(1)}"desc": "{esc}",\n'
            replaced.append(sid)
            break
    else:
        not_found.append(sid)

new_src = "".join(lines)
print(f"替换: {len(replaced)} / {len(fin)}")
print(f"未找到 desc 行: {len(not_found)}")
for s in not_found[:10]:
    print(f"  {s}")

# 语法检查
try:
    compile(new_src, SRC, "exec")
    open(SRC, "w", encoding="utf-8").write(new_src)
    print("✅ 语法 OK，已写入")
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    open(SRC, "w", encoding="utf-8").write(src)
    print("已回滚")
    sys.exit(1)
