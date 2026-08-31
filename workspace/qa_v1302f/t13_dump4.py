# -*- coding: utf-8 -*-
"""T13: dump assassin advanced finisher + bard (歌者) full tree + fa_shi line finishers."""
import io, re

SRC = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py", encoding="utf-8").read()

def block_after(marker, width=4500):
    idx = SRC.find(marker)
    if idx < 0:
        print(f"  >>> {marker}: NOT FOUND"); return
    start = idx
    depth = 0
    for i in range(idx, len(SRC)):
        if SRC[i] == "{": depth += 1
        elif SRC[i] == "}":
            depth -= 1
            if depth == 0:
                print(SRC[idx:i+1][:width]); return

# 1) 终结·处刑 + 幻影连刺 (刺客攻线)
print("=== 终结·处刑 ===")
block_after('"终结·处刑"', 1200)
print("\n=== 幻影连刺 ===")
block_after('"幻影连刺"', 700)

# 2) 歌者树: cls_mu_shi branches 1 (吟游诗人->灵魂歌者->黎明颂者)
m = re.search(r'\n    "cls_mu_shi": \{\n', SRC)
start = m.start()
depth = 0
for i in range(start, len(SRC)):
    if SRC[i] == "{": depth += 1
    elif SRC[i] == "}":
        depth -= 1
        if depth == 0:
            full = SRC[start:i+1]; break
# find branch 1 (歌者)
b1 = full.find('"吟游诗人"')
print("\n=== cls_mu_shi branches 1..3 (歌者线) ===")
print(full[b1:b1+6500] if b1 >= 0 else "branch1 NOT FOUND")