# -*- coding: utf-8 -*-
"""T13: dump full class tree blocks for ranger / chronomancer / wild_hunter / bard."""
import io, re

SRC = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py", encoding="utf-8").read()

def dump_class(cls_key, width=6000):
    m = re.search(r'\n    "%s": \{\n' % cls_key, SRC)
    if not m:
        print(f"### {cls_key}: NOT FOUND"); return
    start = m.start()
    depth = 0
    for i in range(start, len(SRC)):
        if SRC[i] == "{": depth += 1
        elif SRC[i] == "}":
            depth -= 1
            if depth == 0:
                print(f"### {cls_key}\n{SRC[start:i+1][:width]}\n---"); return

for ck in ["cls_you_xia", "cls_chronomancer", "cls_wild_hunter", "cls_bard"]:
    dump_class(ck, 5000)

# find where bard branches live (cls_mu_shi 歌者) - dump cls_mu_shi attack branch 1
print("\n== cls_mu_shi block (branches) ==")
m = re.search(r'\n    "cls_mu_shi": \{\n', SRC)
if m:
    start = m.start()
    depth = 0
    for i in range(start, len(SRC)):
        if SRC[i] == "{": depth += 1
        elif SRC[i] == "}":
            depth -= 1
            if depth == 0:
                print(SRC[start:i+1][:6000]); break