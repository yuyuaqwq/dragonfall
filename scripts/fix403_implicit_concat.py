# -*- coding: utf-8 -*-
"""v95.32 #403：全文件扫描隐式字符串拼接（掉落名行无尾逗号紧跟下一引号行）
修复：给前一行补逗号（保持缩进）"""
import io, re

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\subareas.py"

with io.open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 单字符串行模式（无尾逗号）："xxx"
ONE_STR = re.compile(r'^"([^"]+)"$')
# 单字符串行模式（带尾逗号）："xxx",
ONE_STR_COMMA = re.compile(r'^"([^"]+)",$')

fixes = 0
for i in range(len(lines) - 1):
    cur = lines[i].rstrip("\r\n")
    nxt = lines[i + 1].rstrip("\r\n")
    cur_stripped = cur.strip()
    nxt_stripped = nxt.strip()
    # 当前行是无逗号的纯字符串行，下一行也是字符串元素行（有逗号）→ 隐式拼接
    if ONE_STR.match(cur_stripped) and ONE_STR_COMMA.match(nxt_stripped):
        indent = cur[:len(cur) - len(cur.lstrip())]
        lines[i] = f"{indent}\"{ONE_STR.match(cur_stripped).group(1)}\",\n"
        fixes += 1
        print(f"fix@{i+1}: {cur_stripped} + {nxt_stripped}")

with io.open(PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)
print(f"total fixes: {fixes}")
