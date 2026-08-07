# -*- coding: utf-8 -*-
"""给 instances.py 副本加 key_item/key_source 字段（29 章 11 节）。"""
import os, re

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(PLUGIN_DIR, "game", "data", "instances.py")

# 副本key → (道具id, 道具名, 来源提示)
KEYS = {
    "inst_old_king_tomb": ("i_key_old_king", "王陵钥匙", "白鹿城铁匠铺购买（500 金）"),
    "inst_secret_crypt": ("i_key_crypt", "圣堂信物", "晨曦城大教堂任务奖励"),
    "inst_elven_ruins": ("i_key_elven", "精灵遗印", "翡翠森林精英·森林长老掉落"),
    "inst_ash_temple": ("i_key_ash", "烬火令", "烬山精英·炎魔掉落"),
    "inst_abyss_gate": ("i_key_abyss", "深渊钥匙", "深渊骑士掉落"),
    "inst_dragon_tomb": ("i_key_dragon_tomb", "龙牙信物", "龙脊山脉精英·石龙掉落"),
    "inst_deer_fort": ("i_key_deer_fort", "军旗碎片", "鹿角要塞地图探索掉落"),
    "inst_holy_trial": ("i_key_trial", "试炼令", "铁盾镇兵营任务奖励"),
    "inst_moon_temple": ("i_key_moon", "月辉钥匙", "月冠王庭月市购买（3000 金）"),
    "inst_frost_throne": ("i_key_frost", "寒冰令", "永冻冰原精英·冰原巨兽掉落"),
    "inst_storm_throne": ("i_key_storm_throne", "雷光令", "风暴崖精英·雷鸟掉落"),
    "inst_sunken_ship": ("i_key_sunken", "幽灵船票", "铁港码头精英·海盗精锐掉落"),
    "inst_siren_nest": ("i_key_siren", "海妖鳞片信物", "海妖湾精英·海妖守卫掉落"),
    "inst_sea_god_temple": ("i_key_sea_god", "海神祷文", "无名港灯塔任务奖励"),
    "inst_deep_dragon_palace": ("i_key_dragon_palace", "龙宫珠", "龙鲸海域精英·龙鲸掉落"),
    "inst_gray_dwarf": ("i_key_gray_dwarf", "灰矮人通行令", "地底集市矿工区任务奖励"),
    "inst_under_dragon": ("i_key_under_dragon", "龙鳞钥匙", "熔火深渊精英·地底恶魔掉落"),
    "inst_eye_of_storm": ("i_key_eye_storm", "雷核钥匙", "雷暴高原精英·雷元素掉落"),
    "inst_abyss_throne": ("i_key_abyss_throne", "深渊圣印", "深渊祭坛精英·深渊魔像掉落"),
    "inst_cloud_sanctum": ("i_key_cloud", "云玺", "星辉台精英·星龙掉落"),
}

with open(path, "r", encoding="utf-8") as f:
    src = f.read()

inserted = 0
for kid, (item_id, item_name, source) in KEYS.items():
    # 找到副本块
    idx = src.find(f'"{kid}": {{')
    if idx < 0:
        print(f"⚠️ 找不到副本 {kid}")
        continue
    # 检查是否已有 key_item
    block_end = src.find("\n    \"", idx + 10)
    if block_end < 0:
        block_end = len(src)
    sub = src[idx:block_end]
    if "key_item" in sub:
        print(f"⏭️ {kid} 已有 key_item")
        continue
    # 在 "mech" 行前插入（若没有 mech 则在 "lv" 行后）
    insert_block = (f'        "key_item": "{item_name}",\n'
                    f'        "key_source": "{source}",\n')
    mech_idx = sub.find('"mech"')
    if mech_idx >= 0:
        insert_pos = idx + mech_idx
    else:
        lv_idx = sub.find('"lv"')
        insert_pos = idx + lv_idx
    src = src[:insert_pos] + insert_block + src[insert_pos:]
    inserted += 1

with open(path, "w", encoding="utf-8") as f:
    f.write(src)
print(f"已为 {inserted} 个副本注入 key_item/key_source")
