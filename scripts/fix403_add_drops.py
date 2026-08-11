# -*- coding: utf-8 -*-
"""v95.32 #403 炼金材料掉落源补全：给真实怪物掉落列表加缺失材料中文名"""
import io, sys

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\subareas.py"

# (锚点旧掉落名, 新增掉落名) —— 锚点必须唯一
ADDITIONS = [
    ("\"灰影狼牙\"", "座狼犬齿"),        # 狼王·灰影
    ("\"暗影徽记\"", "暗影碎片"),        # 暗影教徒
    ("\"幽灵之尘\"", "鬼魂精华"),        # 幽灵
    ("\"兽人斧刃\"", "兽人獠牙"),        # 兽人劫掠者
    ("\"骑士团徽记\"", "圣光羽毛"),      # 圣光骑士团追兵
    ("\"堕落精灵护符\"", "妖精之尘"),    # 堕落精灵
    ("\"蜘蛛丝\"", "蜘蛛毒囊"),          # 巨型蜘蛛
    ("\"雪狼皮\"", "雪之精华"),          # 雪狼
    ("\"火蜥蜴鳞\"", "火焰核心"),        # 火蜥蜴
    ("\"熔岩核心\"", "熔岩石"),          # 熔岩元素
    ("\"深渊犬牙\"", "深渊精钢"),        # 深渊猎犬
    ("\"怨灵之尘\"", "灵魂碎片"),        # 湖底怨灵
]

with io.open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

stats = {}
for anchor, new_name in ADDITIONS:
    hits = [i for i, ln in enumerate(lines) if anchor in ln]
    if len(hits) == 0:
        stats[anchor] = "MISS"
        continue
    # 同一怪物可能多处子区域重复（野外版+副本版），全部插入保持掉落一致
    added = 0
    for idx in reversed(hits):
        line = lines[idx]
        indent = line[:len(line) - len(line.lstrip())]
        if f"\"{new_name}\"" in line:
            continue  # 已存在（幂等）
        lines.insert(idx + 1, f"{indent}\"{new_name}\",\n")
        added += 1
    stats[anchor] = f"OK x{len(hits)}(+{added})"

with io.open(PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

for k, v in stats.items():
    print(f"{k}: {v}")
