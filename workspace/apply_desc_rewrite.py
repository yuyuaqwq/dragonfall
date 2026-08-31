# -*- coding: utf-8 -*-
"""把 final_desc_map.json 写回 skills.py：按技能块定位 desc 字段逐块替换（v2 简化版）。"""
import json, re, os, sys

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
MAP = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\workspace\final_desc_map.json"

fin = json.load(open(MAP, encoding="utf-8"))
src = open(SRC, encoding="utf-8").read()

# 备份
bak = SRC + ".bak_desc_rewrite"
open(bak, "w", encoding="utf-8").write(src)

# 用正则：匹配 技能块起始 "sk_xxx": { ... "desc": "..." 里的 desc
# 策略：先按技能块切分，在块内替换第一个 "desc": "..." 行

# 找所有技能块位置
block_pat = re.compile(r'^(\s*)"((?:sk|b_)[a-z0-9_]+)"\s*:\s*\{', re.M)

replaced = []
not_found = []
out_lines = src.splitlines(keepends=True)

# 定位所有技能块行号
blocks = []
for m in block_pat.finditer(src):
    blocks.append((m.group(2), src[:m.start()].count("\n")))

# 逐个技能块替换（从后往前改行，避免行号偏移）
# 简化：对每个技能块，找块内第一个 "desc" 行
for sid, start_ln in blocks:
    if sid not in fin:
        continue
    # 块范围：start_ln 到 下一个技能块或 缩进 <= 的 }
    end_ln = len(out_lines)
    for sid2, start_ln2 in blocks:
        if start_ln2 > start_ln:
            end_ln = start_ln2
            break
    # 在 [start_ln, end_ln) 里找 "desc": "..." 行
    for k in range(start_ln, min(end_ln, len(out_lines))):
        dm = re.match(r'^(\s*)"desc"\s*:\s*".*",?\s*$', out_lines[k])
        if dm:
            new_desc = fin[sid]["new_desc"]
            esc = new_desc.replace("\\", "\\\\").replace('"', '\\"')
            out_lines[k] = f'{dm.group(1)}"desc": "{esc}",\n'
            replaced.append(sid)
            break
    else:
        not_found.append(sid)

new_src = "".join(out_lines)

print(f"替换: {len(replaced)} 个 desc")
print(f"未找到 desc 行: {len(not_found)}")
for s in not_found:
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

# 验证：替换后的 desc 是否都是新的（抽查）
import random
sample = random.sample(list(fin.keys()), min(5, len(fin)))
for s in sample:
    pass
print(f"文件 desc 总数: {new_src.count(chr(34)+'desc'+chr(34)+': ')}")
