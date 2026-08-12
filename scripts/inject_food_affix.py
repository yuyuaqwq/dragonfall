# -*- coding: utf-8 -*-
"""v101.28c 词条料理批量注入：17 件食物 hot → affix 字段 + desc 更新"""
import re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PATH = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/items.py"
src = open(PATH, encoding="utf-8").read()

# key -> (affix_id, 词条中文名)
AFFIXES = {
    "i_snake_soup": ("lifesteal", "吸血"),
    "i_ember_pepper": ("bleed", "流血"),
    "i_mushroom_soup": ("armor_break", "破甲"),
    "i_eagle_egg": ("combo", "连击"),
    "i_tree_honey": ("regen", "回春"),
    "i_deer_cheese": ("thorns", "反伤"),
    "i_pirate_stew": ("execute", "处决"),
    "i_sacred_bread": ("shield", "护盾"),
    "i_wolf_jerky": ("counter", "反击"),
    "i_dragon_egg_pancake": ("dragon_tongue", "龙语印记"),
    "i_frost_berry": ("element_ice", "元素·冰"),
    "i_moon_cake": ("meditate", "冥想"),
    "i_seafood_chowder": ("precise", "精准"),
    "i_snowwolf_steak": ("pierce", "贯穿"),
    "i_ash_pancake": ("element_fire", "元素·火"),
    "i_royal_roast": ("charge", "蓄力"),
    "i_royal_soup": ("dawn_crown", "晨曦祝福"),
}

lines = src.split("\n")
changed = 0
for i, ln in enumerate(lines):
    m = re.match(r'\s*"([a-z_0-9]+)": \{', ln)
    if not m or m.group(1) not in AFFIXES:
        continue
    key = m.group(1)
    aid, cn = AFFIXES[key]
    # 1) 移除 hot/hot_turns/hot_mana 字段
    ln = re.sub(r',?\s*"hot":\s*[0-9.]+', "", ln)
    ln = re.sub(r',?\s*"hot_turns":\s*\d+', "", ln)
    ln = re.sub(r',?\s*"hot_mana":\s*[0-9.]+', "", ln)
    # 2) 插入 affix 字段（price 后）
    pm = re.search(r'"price":\s*\d+', ln)
    if pm:
        ln = ln[:pm.end()] + f', "affix": "{aid}"' + ln[pm.end():]
    lines[i] = ln
    changed += 1
    print(f"字段 OK {key} → {aid}")

src = "\n".join(lines)

# 3) desc 更新：去掉"战斗中每回合回复 X%…（N 回合）"尾巴，追加"战斗中吃下获得【X】效果"
for key, (aid, cn) in AFFIXES.items():
    # 找该条目的 desc 行（key 行后第一个含 "desc": 的行）
    m = re.search(r'"%s": \{[^}]*?"desc": "([^"]*)"' % key, src)
    if not m:
        print(f"!! {key} desc 未找到"); continue
    desc = m.group(1)
    # 去掉战斗 hot 尾巴："；战斗中每回合回复 …（N 回合）"
    desc = re.sub(r"；战斗中每回合回复 [^（]*（\d 回合）", "", desc)
    # 去掉可能残留的"非战斗/战斗外"前缀
    desc = desc.replace("非战斗回复", "回复").replace("战斗外回复", "回复")
    if "战斗中吃下" not in desc:
        desc = desc.rstrip("。") + f"；战斗中吃下获得【{cn}】效果"
    src = src[:m.start(1)] + desc + src[m.end(1):]
    print(f"desc OK {key}: {desc[:60]}")

open(PATH, "w", encoding="utf-8", newline="\n").write(src)
print(f"\n完成 {changed} 件")
