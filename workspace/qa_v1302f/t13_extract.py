# -*- coding: utf-8 -*-
"""T13 audit: read-only extraction of finisher skills from skills.py (bypass display masking)."""
import re, io, sys

P = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py"
src = io.open(P, encoding="utf-8").read()

# 1) check 破势 occurrences anywhere in game/
import glob
hits = []
for f in glob.glob(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/**/*.py", recursive=True):
    s = io.open(f, encoding="utf-8").read()
    for m in re.finditer(r"破势", s):
        line = s[:m.start()].count("\n") + 1
        hits.append((f.split("dragonfall/")[-1], line, s.splitlines()[line-1].strip()[:120]))
print("== 破势 hits in game/ ==")
for h in hits:
    print(h)

# 2) extract skill entries by name
names = ["无畏冲击", "神罚·圣裁", "暗杀", "暗影处刑", "破晓之拳", "碎骨拳", "元素湮灭", "元素风暴",
         "龙脉终曲", "龙焰吐息", "时停领域", "流星陨落", "安魂曲", "破影一击", "幽影刃",
         "撼岳·终焉", "气爆", "裂岳连击", "裂岩冲", "蓄劲连打", "哀歌", "战歌", "处刑标记", "猎鹰突袭", "穿云箭", "满弦"]
print("\n== finisher skill blocks ==")
for nm in names:
    # find '"name": "xxx"' then walk back to enclosing key
    idx = src.find('"name": "%s"' % nm)
    if idx < 0:
        print(f"### {nm}: NOT FOUND")
        continue
    # find enclosing top-level key: walk back to '    "..."': {  at 4-space indent
    key = None
    for m in re.finditer(r'\n    "([^"]+)": \{\n', src[:idx]):
        key = m.group(1)
    # block end: find matching closing brace by brace counting from idx
    start = idx
    # find the next '\n    "' at 4-space indent after the block end
    rest = src[idx:]
    depth = 0
    end = None
    for i, ch in enumerate(rest):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = idx + i + 1
                break
    block = src[idx:end]
    # trim to the enclosing dict of this skill (walk back to '{')
    # find last '{' before idx
    lb = src.rfind("{", 0, idx)
    block = src[lb:end]
    print(f"### {nm}  (key={key})")
    print(block[:1400])
    print("---")