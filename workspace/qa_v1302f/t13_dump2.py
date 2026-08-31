# -*- coding: utf-8 -*-
"""T13: full dict dumps for key skills + grep design/test numbers."""
import io, re, glob

SRC = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py", encoding="utf-8").read()

def dump(name, width=1700):
    idx = SRC.find('"name": "%s"' % name)
    if idx < 0:
        print(f"### {name}: NOT FOUND"); return
    lb = SRC.rfind("{", 0, idx)
    depth = 0
    for i in range(lb, len(SRC)):
        if SRC[i] == "{": depth += 1
        elif SRC[i] == "}":
            depth -= 1
            if depth == 0:
                print(f"### {name}\n{SRC[lb:i+1][:width]}\n---"); return

for nm in ["时停领域", "时间坍缩", "流星陨落", "撼岳·终焉", "终结·破影一击", "幽影刃", "龙脉终曲",
           "神罚·圣裁", "安魂曲", "致命连射", "穿云箭", "猎杀标记", "星空之印", "星辉祈愿",
           "元素湮灭", "无畏冲击", "破晓之拳", "暗影处刑", "裂岳连击", "气爆", "碎骨拳"]:
    dump(nm, 900)

# search official test doc header + design docs for key numbers
print("\n== test_v1302f_job_quality.py header ==")
t = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/tests/test_v1302f_job_quality.py", encoding="utf-8").read()
print(t[:3500])

print("\n== 5.07 / 5.12 / 5.89 / 5.52 / 6.05 in design+tests ==")
for f in glob.glob(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/design/**/*.md", recursive=True) + \
         [r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/tests/test_v1302f_job_quality.py",
          r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/tests/test_v1302f2_engine_fix.py"]:
    s = io.open(f, encoding="utf-8").read()
    for pat in ["5.07", "5.12", "5.89", "5.52", "6.05", "4.68", "6.24", "6.40", "6.4"]:
        for m in re.finditer(re.escape(pat), s):
            line = s[:m.start()].count("\n") + 1
            txt = s.splitlines()[line-1].strip()
            print(f"{f.split('dragonfall')[-1]}:{line} [{pat}] {txt[:150]}")