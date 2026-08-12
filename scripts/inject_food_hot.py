# -*- coding: utf-8 -*-
"""v101.28 食物 hot 批量注入：按价格分档加 hot/hot_turns/hot_mana 字段 + desc 追加战斗说明"""
import re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/items.py"
src = open(PATH, encoding="utf-8").read()

# 食物清单: key -> (hot, hot_turns, hot_mana)  hot=None 表示按档自动
FOODS = {
    "i_bread": None, "i_oats_porridge": None, "i_honey_pancake": None,
    "i_herb_tea": None, "i_ale": None, "i_apple_wine": None,
    "i_ember_pepper": None, "i_wild_honey": None, "i_holy_water_drink": None,
    "i_eagle_egg": None, "i_mushroom_soup": None, "i_wolf_jerky": None,
    "i_roast_bird": None, "i_meat_skewer": None, "i_honey_tea": None,
    "i_silver_jelly": None, "i_dragon_pepper": None, "i_fish_soup": None,
    "i_deer_cheese": None, "i_fog_coffee": None, "i_stone_ale": None,
    "i_snake_soup": None, "i_stew": None, "it_slime_jelly": None,
    "i_laurel_tea": None, "i_blessed_pastry": None, "i_tree_honey": None,
    "i_frost_berry": None, "i_dock_rum": None, "i_dwarf_oven_bread": None,
    "i_octopus_ball": None, "i_ash_pancake": None, "i_deer_burger": None,
    "i_sacred_bread": None, "i_reindeer_jerky": None, "i_salt_baked_fish": None,
    "i_miner_stew": None, "i_elf_fruit": None, "it_cook_skewer": None,
    "i_moon_cake": None, "i_lava_egg": None, "i_nectar_wine": None,
    "i_pirate_stew": None, "i_seafood_chowder": None, "i_elf_jam": None,
    "i_snowwolf_steak": None, "i_gold_dessert": None, "i_royal_soup": None,
    "i_royal_roast": None, "it_gold_feast": None, "i_dragon_egg_pancake": None,
}

def hot_for(price, has_heal, has_mana):
    """价格分档。纯回蓝食物 hot=0（只回蓝），纯体力/回血食物给回血 hot"""
    if not has_heal and has_mana:
        return 0.0
    if price <= 8:
        return 0.03
    if price <= 14:
        return 0.05
    if price <= 24:
        return 0.06
    if price <= 34:
        return 0.08
    if price <= 49:
        return 0.08
    return 0.10

def turns_for(price):
    return 4 if price >= 35 else 3

changed = 0
lines = src.split("\n")
out = []
for ln in lines:
    m = re.match(r'\s*"([a-z_0-9]+)": \{', ln)
    replaced = False
    if m and m.group(1) in FOODS:
        key = m.group(1)
        # 提取 price/heal/mana
        price = int(re.search(r'"price":\s*(\d+)', ln).group(1))
        has_heal = bool(re.search(r'"heal":\s*([0-9.]+)', ln))
        has_mana = bool(re.search(r'"mana":\s*([0-9.]+)', ln))
        has_stam = bool(re.search(r'"stamina":', ln))
        if not (has_heal or has_mana or has_stam):
            out.append(ln); continue
        hot = hot_for(price, has_heal, has_mana)
        turns = turns_for(price)
        hot_mana = 0.0
        if has_mana:
            mm = re.search(r'"mana":\s*([0-9.]+)', ln)
            hot_mana = round(float(mm.group(1)) * 0.4, 2)
        # desc 更新
        dm = re.search(r'"desc":\s*"([^"]*)"', ln)
        if dm:
            desc = dm.group(1)
            # 非战斗/战斗外前缀去掉（战斗中也能用了）
            desc = desc.replace("非战斗回复", "回复").replace("战斗外回复", "回复")
            parts = []
            if hot > 0:
                parts.append(f"战斗中每回合回复 {int(hot*100)}% 生命")
            if hot_mana > 0:
                parts.append(f"战斗中每回合回复 {int(hot_mana*100)}% 魔力")
            if parts:
                desc = desc.rstrip("。") + "；" + "、".join(parts) + f"（{turns} 回合）"
            ln = ln[:dm.start(1)] + desc + ln[dm.end(1):]
        # 插入 hot 字段（在 "price" 之后）
        fields = []
        if hot > 0:
            fields.append(f'"hot": {hot}')
        fields.append(f'"hot_turns": {turns}')
        if hot_mana > 0:
            fields.append(f'"hot_mana": {hot_mana}')
        ins = ", ".join(fields)
        pm = re.search(r'"price":\s*\d+', ln)
        ln = ln[:pm.end()] + ", " + ins + ln[pm.end():]
        replaced = True
        changed += 1
        print(f"OK {key}: hot={hot} turns={turns} hot_mana={hot_mana} price={price}")
    out.append(ln)

open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print(f"\n共修改 {changed} 件")
