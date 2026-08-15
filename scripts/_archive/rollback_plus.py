# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑：全库无差别全角↔半角替换会破坏合法文案。
先回滚：把误伤的全角 ＋－ 还原为半角 +-（保留括号替换的成果）。
然后 AST 精确处理字符串内的加减号。"""
import os, re, sys

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

print("🗑 本脚本已归档（scripts/_archive/）：全库无差别全角↔半角替换会破坏合法文案，禁止重跑。", file=sys.stderr)
sys.exit(1)

# 第一步：全局把全角 ＋ → +、－ → -（误伤还原）
# 注意：要跳过 docstring 注释里的合法全角？为简单起见全部还原，让 AST 版重新处理字符串
total = 0
for dirpath, _d, files in os.walk(ROOT):
    for fn in sorted(files):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            src = f.read()
        n = src.count("＋") + src.count("－")
        if n:
            src = src.replace("＋", "+").replace("－", "-")
            with open(p, "w", encoding="utf-8") as f:
                f.write(src)
            total += n
print(f"回滚全角加减号 {total} 个")
