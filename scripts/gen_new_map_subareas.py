# -*- coding: utf-8 -*-
"""生成 10 张新图子区域，替换 subareas.py 尾部路图段（2026-08-08）

用法：python scripts/gen_new_map_subareas.py
读取 game/data/maps.py 的新图定义 + 本文件内置怪物库，生成子区域 dict，
替换 subareas.py 中 road_* 路段（尾部）。
"""
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

# 怪物库（从现有 SUBAREAS 提取，36 只）
MONSTERS = {
    '野狗': ['m_wild_dog', '野狗', 'dps', 3, ['ms_si_yao'], ['狗牙']],
    '森林狼': ['m_forest_wolf', '森林狼', 'dps', 8, ['ms_si_yao', 'ms_hao_jiao'], ['狼皮']],
    '石蜥蜴': ['m_cave_lizard', '石蜥蜴', 'tank', 6, ['ms_yao_sui', 'ms_ying_hua'], ['石蜥鳞']],
    '野牛': ['m_wild_bull', '野牛', 'tank', 30, ['ms_chong_zhuang'], ['牛角']],
    '盗贼': ['m_bandit', '盗贼', 'speedster', 32, ['ms_duan_jian', 'ms_tou_qie'], ['盗贼面巾']],
    '审判猎犬': ['m_inquisitor_hound', '审判猎犬', 'speedster', 45, ['ms_si_yao'], ['猎犬项圈']],
    '骑士教官': ['e_knight_instructor', '骑士教官', 'elite', 34, ['ms_jian_ji', 'ms_zhan_hou'], ['教官之剑']],
    '古道骷髅': ['m_road_skeleton', '古道骷髅', 'dps', 33, ['ms_jian_ji'], ['碎骨']],
    '古墓幽灵': ['m_grave_ghost', '古墓幽灵', 'speedster', 36, ['ms_chuan_shen', 'ms_ai_hao'], ['幽灵之尘']],
    '丘陵狼': ['m_hill_wolf', '丘陵狼', 'dps', 28, ['ms_si_yao', 'ms_hao_jiao'], ['丘陵狼皮']],
    '战场幽魂': ['m_field_ghost', '战场幽魂', 'speedster', 34, ['ms_chuan_shen', 'ms_ai_hao'], ['幽魂尘']],
    '战争魔像（残）': ['m_war_golem', '战争魔像（残）', 'tank', 37, ['ms_zhong_ji', 'ms_tie_bi'], ['魔像残核']],
    '星语湖王': ['e_lake_king', '星语湖王', 'elite', 58, ['ms_shui_dan', 'ms_xuan_wo', 'ms_zhao_huan_shui_jing_ling'], ['湖王珠']],
    '堕落精灵': ['m_corrupted_elf', '堕落精灵', 'dps', 58, ['ms_jing_ling_jian_shu', 'ms_an_ying_zhan'], ['堕落精灵护符']],
    '远古魔像': ['m_ancient_golem', '远古魔像', 'tank', 62, ['ms_zhong_ji', 'ms_fu_wen_chong_ji'], ['远古符文石']],
    '暗影精灵': ['m_shadow_elf', '暗影精灵', 'dps', 64, ['ms_an_ying_jian', 'ms_qian_xing'], ['暗影精灵刃']],
    '古树守卫': ['m_old_tree_guardian', '古树守卫', 'tank', 68, ['ms_teng_bian', 'ms_ying_hua'], ['守卫古木']],
    '古树领主': ['e_tree_lord', '古树领主', 'elite', 70, ['ms_teng_bian', 'ms_gen_xu_chan_rao', 'ms_zhao_huan_shu_ren'], ['领主古木心']],
    '月光精灵': ['m_moon_spirit', '月光精灵', 'healer', 58, ['ms_yue_guang_zhan', 'ms_zhi_yu'], ['月光精华']],
    '翠鹿': ['m_emerald_deer', '翠鹿', 'speedster', 47, ['ms_ji_chi', 'ms_ding_zhuang'], ['翠鹿角']],
    '冰元素': ['m_ice_elemental', '冰元素', 'tank', 65, ['ms_bing_dan', 'ms_dong_jie'], ['冰元素核心']],
    '霜巨魔': ['m_frost_troll', '霜巨魔', 'dps', 68, ['ms_zhong_ji', 'ms_zai_sheng', 'ms_bing_ji'], ['霜巨魔血']],
    '熔岩元素': ['m_lava_elemental', '熔岩元素', 'tank', 70, ['ms_rong_yan_dan', 'ms_zhuo_shao'], ['熔岩核心']],
    '深渊奴仆': ['m_demon_servant', '深渊奴仆', 'tank', 82, ['ms_zhong_ji', 'ms_an_ying_dan'], ['奴仆锁链']],
    '恶魔战士': ['e_demon_warrior', '恶魔战士', 'elite', 86, ['ms_zhang_jian', 'ms_di_yu_huo'], ['恶魔战刃']],
    '恶魔祭司': ['m_demon_priest', '恶魔祭司', 'healer', 82, ['ms_an_ying_dan', 'ms_hei_an_zhi_liao'], ['染血祭器']],
    '雪原猛犸': ['m_snow_mammoth', '雪原猛犸', 'tank', 66, ['ms_chong_zhuang', 'ms_jian_ta'], ['猛犸毛']],
    '冰原巨熊': ['m_frost_bear', '冰原巨熊', 'tank', 68, ['ms_xiong_zhang', 'ms_bing_hou'], ['冰熊皮']],
    '冰川龙·霜牙': ['e_glacier_wyrm', '冰川龙·霜牙', 'elite', 82, ['ms_bing_xi', 'ms_long_zhao', 'ms_dong_jie'], ['霜牙龙鳞']],
    '龙裔战士': ['m_dragonkin', '龙裔战士', 'dps', 82, ['ms_long_jian_shu'], ['龙鳞碎片']],
    '石龙': ['m_stone_dragon', '石龙', 'tank', 85, ['ms_shi_xi', 'ms_zhong_ji'], ['石龙鳞']],
    '骨虫': ['m_bone_wyrm', '骨虫', 'speedster', 84, ['ms_gu_xi', 'ms_chuan_shen'], ['骨虫壳']],
    '落日岛虎·金焰': ['e_island_tiger', '落日岛虎·金焰', 'elite', 48, ['ms_si_yao', 'ms_pu_ji', 'ms_lie_yan_zhao'], ['金焰虎皮']],
    '海妖斥候': ['m_siren_scout', '海妖斥候', 'speedster', 45, ['ms_mei_huo_zhi_ge'], ['海妖鳞']],
    '迷雾章鱼': ['m_mist_octopus', '迷雾章鱼', 'tank', 60, ['ms_chan_rao', 'ms_mo_zhi'], ['章鱼墨囊']],
    '黑曜石魔像': ['m_obsidian_golem', '黑曜石魔像', 'tank', 82, ['ms_zhong_ji', 'ms_ying_hua'], ['黑曜碎片']],
}

# 新图子区域配置：mid -> [(子区域名, lv, [普通怪名], 精英怪名或None), ...]
NEW_SUBAREAS = {
    "silver_wind_road": [
        ("银风道口", 6, ["野狗", "石蜥蜴"], None),
        ("银风驿站", 8, ["森林狼"], None),
    ],
    "west_ridge_wilds": [
        ("西岭口", 28, ["丘陵狼"], None),
        ("荒原腹地", 31, ["野牛", "盗贼"], None),
        ("落霞坡", 34, ["古道骷髅"], None),
    ],
    "dusk_ridge_road": [
        ("岭脚石阶", 36, ["战场幽魂"], None),
        ("半山烽台", 39, ["古墓幽灵"], None),
        ("月冠垭口", 42, ["战争魔像（残）"], "骑士教官"),
    ],
    "mist_tide_passage": [
        ("港外锚地", 45, ["海妖斥候"], None),
        ("雾潮中段", 47, ["审判猎犬"], None),
        ("无名灯塔", 50, ["翠鹿"], "落日岛虎·金焰"),
    ],
    "black_tide_strait": [
        ("无名礁口", 58, ["堕落精灵"], None),
        ("黑潮中流", 60, ["月光精灵"], None),
        ("珍珠湾", 63, ["迷雾章鱼"], "星语湖王"),
    ],
    "dwarf_long_gallery": [
        ("要塞铁门", 62, ["远古魔像"], None),
        ("长廊中段", 65, ["冰元素"], None),
        ("深岩闸门", 68, ["霜巨魔"], None),
    ],
    "cold_spine_snow_trail": [
        ("铁砧北门", 66, ["雪原猛犸"], None),
        ("雪道中段", 68, ["古树守卫"], None),
        ("寒脊风口", 71, ["冰原巨熊"], None),
    ],
    "dragon_ridge_old_road": [
        ("王庭东门", 64, ["暗影精灵"], None),
        ("古道龙纹", 67, ["远古魔像"], None),
        ("龙脊崖脚", 70, ["熔岩元素"], "古树领主"),
    ],
    "dragonborn_valley_trail": [
        ("聚落石阶", 81, ["深渊奴仆"], None),
        ("谷道中段", 83, ["龙裔战士"], None),
        ("山口龙喉", 86, ["骨虫"], "冰川龙·霜牙"),
    ],
    "sky_ladder_path": [
        ("云梯起步", 82, ["黑曜石魔像"], None),
        ("云径中段", 85, ["恶魔祭司"], None),
        ("风翼台", 88, ["石龙"], "恶魔战士"),
    ],
}

MAP_NAMES = {
    "silver_wind_road": "银风商道",
    "west_ridge_wilds": "西岭荒原",
    "dusk_ridge_road": "暮岭古道",
    "mist_tide_passage": "雾潮航道",
    "black_tide_strait": "黑潮海峡",
    "dwarf_long_gallery": "矮人长廊",
    "cold_spine_snow_trail": "寒脊雪道",
    "dragon_ridge_old_road": "龙脊古道",
    "dragonborn_valley_trail": "龙裔谷道",
    "sky_ladder_path": "天梯云径",
}


def build():
    result = {}
    for mid, rows in NEW_SUBAREAS.items():
        mname = MAP_NAMES[mid]
        items = []
        for idx, (nm, lv, normal_names, elite_name) in enumerate(rows, 1):
            monsters = [MONSTERS[n] for n in normal_names]
            elite = MONSTERS[elite_name] if elite_name else None
            if elite:
                monsters.append(elite)
            items.append({
                "id": f"{mid}_{idx}",
                "name": nm,
                "icon": "🌲",
                "desc": f"{mname}·{nm}",
                "type": "野外",
                "lv": lv,
                "npcs": [],
                "monsters": monsters,
                "elite": elite,
                "boss": None,
                "funcs": ["explore"],
                "shop": False,
                "healer": False,
            })
        result[mid] = items
    return result


def fmt(items):
    import json
    return (json.dumps(items, ensure_ascii=False, indent=2)
            .replace(": false", ": False").replace(": true", ": True")
            .replace(": null", ": None"))


if __name__ == "__main__":
    subareas_path = os.path.join(PLUGIN_DIR, "game", "data", "subareas.py")
    with open(subareas_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 定位路图段：从第一个 "road_" key 到文件尾部 '}' 前
    idx = content.find('    "road_anvil_fort_cold_ridge": [')
    if idx == -1:
        print("❌ 未找到路图段起始")
        sys.exit(1)
    # 生成新段
    data = build()
    parts = []
    for mid in ["silver_wind_road", "west_ridge_wilds", "dusk_ridge_road",
                "mist_tide_passage", "black_tide_strait", "dwarf_long_gallery",
                "cold_spine_snow_trail", "dragon_ridge_old_road",
                "dragonborn_valley_trail", "sky_ladder_path"]:
        parts.append(f'    "{mid}": ' + fmt(data[mid]).replace("\n", "\n    ") )
    new_block = ",\n".join(parts)
    new_content = content[:idx] + new_block + "\n}"
    with open(subareas_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ 已写入 {len(data)} 张新图子区域")
    for mid, items in data.items():
        print(f"  {mid}: {len(items)} 子区域")
