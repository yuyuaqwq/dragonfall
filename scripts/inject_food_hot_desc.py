# -*- coding: utf-8 -*-
"""v101.28 食物 hot desc 第二遍：多行条目 desc 在下一行，按最近 key 归属处理"""
import re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/items.py"
lines = open(PATH, encoding="utf-8").read().split("\n")

FOODS = {"i_bread","i_oats_porridge","i_honey_pancake","i_herb_tea","i_ale","i_apple_wine",
"i_ember_pepper","i_wild_honey","i_holy_water_drink","i_eagle_egg","i_mushroom_soup",
"i_wolf_jerky","i_roast_bird","i_meat_skewer","i_honey_tea","i_silver_jelly",
"i_dragon_pepper","i_fish_soup","i_deer_cheese","i_fog_coffee","i_stone_ale",
"i_snake_soup","i_stew","it_slime_jelly","i_laurel_tea","i_blessed_pastry",
"i_tree_honey","i_frost_berry","i_dock_rum","i_dwarf_oven_bread","i_octopus_ball",
"i_ash_pancake","i_deer_burger","i_sacred_bread","i_reindeer_jerky","i_salt_baked_fish",
"i_miner_stew","i_elf_fruit","it_cook_skewer","i_moon_cake","i_lava_egg",
"i_nectar_wine","i_pirate_stew","i_seafood_chowder","i_elf_jam","i_snowwolf_steak",
"i_gold_dessert","i_royal_soup","i_royal_roast","it_gold_feast","i_dragon_egg_pancake"}

# 第一遍已插字段：从文件提取每个 key 的 hot/turns/mana 参数
def entry_block(key, lines):
    """返回 key 条目块文本（key 行到闭合 } 行）"""
    buf = []
    in_block = False
    depth = 0
    for ln in lines:
        if re.match(r'\s*"%s": \{' % re.escape(key), ln):
            in_block = True
        if in_block:
            buf.append(ln)
            depth += ln.count("{") - ln.count("}")
            if depth <= 0:
                return "\n".join(buf)
    return None

params = {}
for k in FOODS:
    blk = entry_block(k, lines)
    if not blk:
        print(f"!! {k} 块未找到"); continue
    hot = re.search(r'"hot":\s*([0-9.]+)', blk)
    turns = re.search(r'"hot_turns":\s*(\d+)', blk)
    hmana = re.search(r'"hot_mana":\s*([0-9.]+)', blk)
    params[k] = {
        "hot": float(hot.group(1)) if hot else 0.0,
        "turns": int(turns.group(1)) if turns else 3,
        "hot_mana": float(hmana.group(1)) if hmana else 0.0,
    }

changed = 0
out = []
cur_key = None
for ln in lines:
    m = re.match(r'\s*"([a-z_0-9]+)": \{', ln)
    if m:
        cur_key = m.group(1)
    if cur_key in FOODS and '"desc":' in ln:
        dm = re.search(r'"desc":\s*"([^"]*)"', ln)
        if dm:
            desc = dm.group(1)
            desc = desc.replace("非战斗回复", "回复").replace("战斗外回复", "回复")
            p = params[cur_key]
            parts = []
            if p["hot"] > 0:
                parts.append(f"战斗中每回合回复 {int(p['hot']*100)}% 生命")
            if p["hot_mana"] > 0:
                parts.append(f"战斗中每回合回复 {int(p['hot_mana']*100)}% 魔力")
            if parts and "战斗中每回合" not in desc:
                desc = desc.rstrip("。") + "；" + "、".join(parts) + f"（{p['turns']} 回合）"
                ln = ln[:dm.start(1)] + desc + ln[dm.end(1):]
                changed += 1
                print(f"desc OK {cur_key}: {desc[:60]}")
    out.append(ln)

open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print(f"\ndesc 更新 {changed} 件")
