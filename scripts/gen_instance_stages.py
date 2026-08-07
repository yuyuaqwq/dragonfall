# -*- coding: utf-8 -*-
"""为全部副本生成 stages 层结构（02 章 13.8）。

逻辑：
- 层1「入口」：2 只最低级小怪
- 层2「深处」：1-2 只中级小怪 + 精英（如有）
- 层3「Boss房」：现有 boss
每层的小怪取自已有关联地图的 monsters（按等级从低到高选）。
"""
import os, sys, re, io

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

# 副本 → 关联地图（用于找小怪池）
INST_MAP = {
    "inst_goblin_camp": "goblin_camp",
    "inst_sea_cave": "sea_cave",
    "inst_old_king_tomb": "old_king_tomb",
    "inst_secret_crypt": "secret_crypt",
    "inst_elven_ruins": "elven_ruins",
    "inst_ash_temple": "ash_temple",
    "inst_abyss_gate": "abyss_gate",
    "inst_dragon_tomb": "dragon_tomb",
    "inst_deer_fort": "deer_fort",
    "inst_holy_trial": "holy_trial",
    "inst_moon_temple": "moon_temple",
    "inst_frost_throne": "frost_throne",
    "inst_storm_throne": "storm_throne",
    "inst_sunken_ship": "sunken_ship",
    "inst_siren_nest": "siren_nest",
    "inst_sea_god_temple": "sea_god_temple",
    "inst_deep_dragon_palace": "deep_dragon_palace",
    "inst_gray_dwarf": "gray_dwarf",
    "inst_under_dragon": "under_dragon",
    "inst_eye_of_storm": "eye_of_storm",
    "inst_abyss_throne": "abyss_throne",
    "inst_cloud_sanctum": "cloud_sanctum",
}

# 层2 精英：部分副本给专属精英（用地图 elite 或造一个）
ELITE_NAMES = {
    "inst_goblin_camp": ("e_goblin_berserker", "哥布林狂战士", "elite", 18, ["ms_kuang_bao", "ms_lian_zhan"], ["狂战士徽记"]),
    "inst_sea_cave": ("e_pirate_elite", "海盗精锐", "elite", 26, ["ms_wan_dao", "ms_huo_qiang"], ["海盗徽记"]),
    "inst_old_king_tomb": ("e_ghost_king", "幽灵骑士", "elite", 40, ["ms_you_ling", "ms_zhao_huan"], ["亡者碎片"]),
    "inst_secret_crypt": ("e_judge_hound", "审判猎犬", "elite", 45, ["ms_kuang_bao", "ms_si_yao"], ["审判印记"]),
    "inst_elven_ruins": ("e_ancient_golem", "远古魔像", "elite", 62, ["ms_ying_hua", "ms_zhen_ji"], ["魔像核心"]),
    "inst_ash_temple": ("e_seal_guard", "封印守卫（腐蚀）", "elite", 86, ["ms_an_ying", "ms_xu_kong"], ["腐蚀印记"]),
    "inst_abyss_gate": ("e_abyss_knight", "深渊骑士", "elite", 92, ["ms_an_ying", "ms_xu_kong"], ["深渊印记"]),
    "inst_dragon_tomb": ("e_dragon_soul", "龙魂", "elite", 95, ["ms_long_xi", "ms_zhao_huan"], ["龙魂碎片"]),
    "inst_deer_fort": ("e_fort_ghost", "要塞幽灵", "elite", 20, ["ms_you_ling", "ms_kuang_bao"], ["要塞遗物"]),
    "inst_holy_trial": ("e_trial_knight", "试炼骑士", "elite", 34, ["ms_sheng_guang", "ms_dun_ji"], ["试炼徽章"]),
    "inst_moon_temple": ("e_moon_guard", "月神守卫", "elite", 62, ["ms_yue_guang", "ms_sheng_guang"], ["月光碎片"]),
    "inst_frost_throne": ("e_frost_lord", "冰霜领主护卫", "elite", 78, ["ms_bing_shuang", "ms_han_qi"], ["寒冰碎片"]),
    "inst_storm_throne": ("e_storm_guard", "风暴守卫", "elite", 94, ["ms_feng_bao", "ms_lei_ji"], ["风暴核心"]),
    "inst_sunken_ship": ("e_ghost_captain", "幽灵大副", "elite", 42, ["ms_you_ling", "ms_wan_dao"], ["幽灵船票"]),
    "inst_siren_nest": ("e_siren_guard", "海妖守卫", "elite", 55, ["ms_hai_yao", "ms_du_ya"], ["海妖鳞片"]),
    "inst_sea_god_temple": ("e_sea_priest", "海神护卫", "elite", 68, ["ms_hai_yao", "ms_sheng_guang"], ["海神印记"]),
    "inst_deep_dragon_palace": ("e_dragon_guard", "龙宫守卫", "elite", 74, ["ms_long_xi", "ms_du_ya"], ["龙宫鳞片"]),
    "inst_gray_dwarf": ("e_dwarf_guard", "灰矮人守卫", "elite", 78, ["ms_dun_ji", "ms_kuang_bao"], ["灰矮人徽记"]),
    "inst_under_dragon": ("e_deep_dragon", "地底幼龙", "elite", 88, ["ms_long_xi", "ms_an_ying"], ["地底龙鳞"]),
    "inst_eye_of_storm": ("e_storm_elite", "风暴元素", "elite", 96, ["ms_feng_bao", "ms_lei_ji"], ["风暴之核"]),
    "inst_abyss_throne": ("e_abyss_elite", "深渊魔像", "elite", 94, ["ms_an_ying", "ms_xu_kong"], ["深渊核心"]),
    "inst_cloud_sanctum": ("e_cloud_guard", "云中守卫", "elite", 96, ["ms_sheng_guang", "ms_feng_bao"], ["云中印记"]),
}

# 每层名字（按副本主题微调）
STAGE_NAMES = {
    "inst_goblin_camp": ["营地前哨", "酋长帐篷", "酋长宝座"],
    "inst_sea_cave": ["洞口滩涂", "洞窟深处", "藏宝密室"],
    "inst_old_king_tomb": ["墓道", "主墓室", "王座厅"],
    "inst_secret_crypt": ["地窖回廊", "审判庭", "枢机密室"],
    "inst_elven_ruins": ["残垣入口", "神殿走廊", "精灵王座"],
    "inst_ash_temple": ["祭坛外围", "火焰回廊", "封印之殿"],
    "inst_abyss_gate": ["裂隙入口", "深渊长廊", "蚀夜之巢"],
    "inst_dragon_tomb": ["龙墓入口", "骨堆甬道", "龙眠大殿"],
    "inst_deer_fort": ["要塞门口", "破败庭院", "要塞主厅"],
    "inst_holy_trial": ["试炼之门", "骑士回廊", "圣光试炼场"],
    "inst_moon_temple": ["月门", "月光回廊", "月神圣殿"],
    "inst_frost_throne": ["冰封入口", "寒冰回廊", "冰霜王座"],
    "inst_storm_throne": ["风暴之门", "雷霆回廊", "风暴王座"],
    "inst_sunken_ship": ["甲板", "船舱", "船长室"],
    "inst_siren_nest": ["海藻洞", "珊瑚回廊", "海妖巢穴"],
    "inst_sea_god_temple": ["神殿入口", "潮汐回廊", "海神祭坛"],
    "inst_deep_dragon_palace": ["宫门", "珊瑚长廊", "龙王大殿"],
    "inst_gray_dwarf": ["要塞入口", "兵工厂", "领主大厅"],
    "inst_under_dragon": ["巢穴入口", "龙骸甬道", "地底龙巢"],
    "inst_eye_of_storm": ["云巅之门", "风暴回廊", "风暴之眼"],
    "inst_abyss_throne": ["深渊入口", "魔像走廊", "深渊王座"],
    "inst_cloud_sanctum": ["云门", "圣殿回廊", "云中圣殿"],
}


def build_stages(inst_key, inst, map_monsters):
    """为副本构建 stages 列表。"""
    boss = inst.get("boss")
    if not boss:
        return None
    # 关联地图的小怪（不含 boss/elite）
    mons = [m for m in map_monsters if m[3] < boss[3]]
    if not mons:
        return None
    # 按等级排序
    mons = sorted(mons, key=lambda x: x[3])
    names = STAGE_NAMES.get(inst_key, ["入口", "深处", "深处"])
    elite = ELITE_NAMES.get(inst_key)
    stages = []
    # 层1：1-2 只最低级怪
    s1 = mons[:2]
    stages.append({"name": names[0], "monsters": list(s1)})
    # 层2：剩余中级怪 + 精英
    s2 = mons[2:4]
    stage2 = {"name": names[1], "monsters": list(s2)}
    if elite:
        stage2["elite"] = list(elite)
    stages.append(stage2)
    # 层3：Boss
    stages.append({"name": names[2], "boss": list(boss)})
    return stages


def main():
    from game.data.maps import MAPS
    map_monsters = {m["id"]: (m.get("monsters") or []) for m in MAPS}
    # 读取 instances.py 原文
    path = os.path.join(PLUGIN_DIR, "game", "data", "instances.py")
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    # 用 AST 解析现有 INSTANCES
    import ast
    tree = ast.parse(src)
    inst_dict = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "INSTANCES":
                    inst_dict = ast.literal_eval(node.value)
    if not inst_dict:
        print("未找到 INSTANCES")
        return
    # 生成 stages 插入文本
    inserted = 0
    for k, inst in inst_dict.items():
        if "stages" in inst:
            continue
        stages = build_stages(k, inst, map_monsters.get(INST_MAP.get(k, ""), []))
        if not stages:
            continue
        # 在 "boss" 行后插入 stages
        stages_repr = repr(stages).replace("'", "\"").replace("True", "True").replace("False", "False")
        # 用 Python 安全 repr（保持中文）
        import json as _json
        stages_str = _json.dumps(stages, ensure_ascii=False, indent=4)
        # 缩进
        lines = stages_str.split("\n")
        indented = "\n".join("        " + l if l else l for l in lines)
        # 找到该副本 boss 行结束位置
        marker = f"\"boss\": ["
        idx = src.find(f"\"{k}\"")
        if idx < 0:
            continue
        # 在该副本块内找 "mech" 行（boss 之后）插入
        block_end = src.find("\n    \"", idx + 10)
        if block_end < 0:
            block_end = len(src)
        sub = src[idx:block_end]
        mech_idx = sub.find("\"mech\"")
        if mech_idx < 0:
            continue
        insert_pos = idx + mech_idx
        stages_block = "        \"stages\": " + indented + ",\n"
        src = src[:insert_pos] + stages_block + src[insert_pos:]
        inserted += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"已为 {inserted} 个副本插入 stages")


if __name__ == "__main__":
    main()
