# -*- coding: utf-8 -*-
"""阶段八.1：怪物技能补元素字段（element）+ 冰系减速（mech slow）
- 玩家元素抗性（elem_resist 火冰雷 -8% / abyss_resist 暗影 -10%）才有作用对象
- 冰系减速给霜狼套 5 件『抗寒：免疫减速』提供触发场景
只处理 kind=魔法 且无 effect 的攻击性技能；已有 mech（stun/silence/freeze）不覆盖。
"""
import re, io, sys

path = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\monsters.py"
with io.open(path, "r", encoding="utf-8") as f:
    src = f.read()

# 扩展关键词分类（只对攻击性魔法技能）
FIRE_KW = ["火", "焰", "炎", "燃", "爆", "灼", "熔岩", "陨石", "龙息"]
ICE_KW = ["冰", "霜", "寒", "水弹", "水息", "海潮", "巨浪", "漩涡"]
THUNDER_KW = ["雷", "电"]
DARK_KW = ["暗", "影", "渊", "骨息", "腐化", "腐蚀"]

def classify(name):
    if any(k in name for k in FIRE_KW):
        return "fire"
    if any(k in name for k in ICE_KW):
        return "ice"
    if any(k in name for k in THUNDER_KW):
        return "thunder"
    if any(k in name for k in DARK_KW):
        return "dark"
    return None

# 定位技能块：{"ms_xxx": { ... },  以 "name": "中文名", 作锚点
pat = re.compile(r'("ms_[a-z_]+": \{\s*"kind": "魔法",\s*"power": [0-9.]+,\s*"desc": "[^"]*",\s*"name": "([^"]+)",)')

changed = []
count_by_elem = {}
def repl(m):
    key, name = m.group(1), m.group(2)
    elem = classify(name)
    if elem is None:
        return m.group(0)
    # 已有 mech 不覆盖（跳过冻结类技能）
    seg_end = src.find("},", m.end())
    seg = src[m.start():seg_end + 2]
    if '"mech"' in seg:
        return m.group(0)
    add = f'"element": "{elem}",'
    if elem == "ice":
        add += '\n        "mech": "slow",'
    new = m.group(0) + "\n        " + add
    changed.append((key, name, elem))
    count_by_elem[elem] = count_by_elem.get(elem, 0) + 1
    return new

new_src, n = pat.subn(repl, src)
print(f"替换 {n} 处")
for e, c in count_by_elem.items():
    print(f"  {e}: {c}")
for key, name, elem in changed:
    print(f"  {key} {name} -> {elem}")

if n > 0:
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(new_src)
    print("已写回", path)
else:
    print("无改动")
