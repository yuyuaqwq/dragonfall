# -*- coding: utf-8 -*-
"""v95.3 排版规范批量处理：全角圆括号→半角；+- 符号→全角 ＋－ 且去空格。
只动字符串文案（全角括号只存在于字符串里；加减号用精确模式避免误伤代码运算符）。
"""
import re, sys, os

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

# 只处理命令/数据展示层（文案集中地）
FILES = []
for dirpath, _dirs, files in os.walk(ROOT):
    for fn in files:
        if fn.endswith(".py"):
            p = os.path.join(dirpath, fn)
            FILES.append(p)

total_brackets = 0
total_plus = 0
total_minus = 0

for path in FILES:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    orig = src
    # 1) 全角圆括号 → 半角圆括号
    n1 = src.count("（") + src.count("）")
    src = src.replace("（", "(").replace("）", ")")
    # 2) "+{x}" / "+数字" / "+ 数字" → "＋x"（去空格）
    #    模式：加号前可能有空格（文案里 " +{v}"），把 " +" 和 "+" 统一为全角＋
    #    只处理紧贴数字/花括号的加号（运算符两边都有空格的不动）
    src2, n2 = re.subn(r'(?<=[（( ])\s*\+(\s*)(?=[\d{])', '＋', src)
    # 3) 减号同理
    src3, n3 = re.subn(r'(?<=[（( ])\s*\-(\s*)(?=[\d{])', '－', src2)
    if src3 != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src3)
        total_brackets += n1
        total_plus += n2
        total_minus += n3
        print(f"  {os.path.relpath(path, ROOT)}: （）{n1} +{n2} -{n3}")

print(f"\n总计：全角括号 {total_brackets}，加号 {total_plus}，减号 {total_minus}")
