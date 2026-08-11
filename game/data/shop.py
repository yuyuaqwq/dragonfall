# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - shop.py（阶段四重写，2026-08-06）

商店体系（07 章 6.2 城镇特色 + 6.3 消耗品 + 13 章 2.1/2.2/3/4）：
- SHOP_ITEMS：key = 城镇地图 ID（24 城镇，按等级递进补货）
- SHOP_WEAPONS：key = 城镇地图 ID，值 = (名字, 武器类型英文ID, 等级, 品质ID)
  武器名来自 10 章装备名册（商店可售的基础/进阶武器）
"""
SHOP_ITEMS = {
    # ---- 南境（Lv.1-30） ----
    "oak_town": [          # 橡木镇：基础补给
        "i_treat_s", "i_mana_s", "i_bread", "i_ale", "i_scroll_escape",
    ],
    "maple_village": [     # 枫橡村
        "i_treat_s", "i_mana_s", "i_bread", "i_ale",
    ],
    "white_deer": [        # 白鹿城 南境首府
        "i_treat_s", "i_treat_m", "i_mana_s", "i_mana_m", "i_meat_skewer", "i_ale",
    ],
    "ironharbor": [        # 铁港城 冒险者圣地：全种类
        "i_treat_s", "i_treat_m", "i_mana_s", "i_mana_m", "i_meat_skewer", "i_stew", "i_scroll_teleport",
    ],
    "silver_brook": [      # 银溪镇
        "i_treat_m", "i_mana_m", "i_meat_skewer", "i_ale",
    ],
    # ---- 中域（Lv.25-55） ----
    "dawn_city": [         # 晨曦城 王都：圣光/药剂
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_holy_water", "i_str_potion",
        "i_def_potion", "i_spd_potion", "i_scroll_purify", "i_holy_charm",
    ],
    "ironshield_town": [   # 铁盾镇
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_stew", "i_str_potion",
    ],
    "jade_port": [         # 翡翠港（外域·群岛门户）
        "i_treat_m", "i_mana_m", "i_meat_skewer", "i_ale", "i_scroll_teleport",
    ],
    "shell_town": [        # 贝壳镇
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_meat_skewer",
    ],
    "moon_gate": [         # 月冠隘口
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_elf_fruit",
    ],
    "star_song": [         # 星歌镇
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_elf_fruit",
    ],
    # ---- 西境/无尽海（Lv.45-78） ----
    "moon_court": [        # 月冠王庭 精灵主城：月系
        "i_treat_l", "i_mana_l", "i_elf_fruit", "i_full_potion", "i_moon_dew",
    ],
    "nameless_harbor": [   # 无名港
        "i_treat_l", "i_mana_l", "i_meat_skewer", "i_stew", "i_scroll_teleport",
    ],
    "pearl_city": [        # 珍珠城
        "i_treat_l", "i_mana_l", "i_full_potion", "i_scroll_teleport",
    ],
    # ---- 北境（Lv.60-95） ----
    "frost_horn": [        # 霜角堡 北境主城：抗寒
        "i_treat_l", "i_mana_l", "i_full_potion", "i_dwarf_liquor",
    ],
    "anvil_fort": [        # 铁砧要塞 矮人主城：符文/烈酒
        "i_treat_l", "i_mana_l", "i_dwarf_liquor", "i_full_potion",
    ],
    "cold_ridge": [        # 寒脊营地
        "i_treat_l", "i_mana_l", "i_stew",
    ],
    "aurora_town": [       # 极光镇
        "i_treat_l", "i_mana_l", "i_ale",
    ],
    "deep_tunnel": [       # 深岩隧道（地底入口）
        "i_treat_l", "i_mana_l", "i_bread",
    ],
    "under_market": [      # 地底集市
        "i_treat_l", "i_mana_l", "i_full_potion",
    ],
    # ---- 东境/风翼群岛（Lv.80-100） ----
    "dragon_pass": [       # 龙脊山口：龙裔
        "i_treat_l", "i_mana_l", "i_full_potion", "i_battlecry_potion",
    ],
    "dragon_kin": [        # 龙裔聚落
        "i_treat_l", "i_mana_l", "i_dragon_scale_potion",
    ],
    "ember_camp": [        # 灰烬营地
        "i_treat_l", "i_mana_l", "i_battlecry_potion",
    ],
    "wind_city": [         # 风翼城
        "i_treat_l", "i_mana_l", "i_holy_charm", "i_scroll_purify",
    ],
}

# v95.4 野外行商货物（游商·老马等 trade 型野外 NPC 在场时可用）
SHOP_WILD_TRADE = [
    "i_treat_s", "i_mana_s", "i_bread", "i_ale", "i_meat_skewer", "i_scroll_escape",
]

# ================= v101.25h 子区域独立配货（鱼鱼：草药铺不该卖吃的，按子区域配置） =================
# key = 子区域 ID，value = 该店专属货物（物品 ID 列表）。
# 未在此表配置的子区域回退到 SHOP_ITEMS（城镇级）——新子区域不配置也不会空店。
# 设计分工：药剂店(herb)→药水/药剂；酒馆旅店(tavern)→食物/饮品；集市商行(general)→卷轴/杂物/护符；
# 铁匠工坊(smith)→武器+锻造材料（is_smith 分支），可追加军需补给。
SHOP_SUBAREA_ITEMS = {
    # ---------- 橡木镇（新手村） ----------
    "oak_town_5": [  # 艾琳炼药铺（炼药师·艾琳）
        "i_treat_s", "i_mana_s", "i_herb_juice", "i_bandage",
    ],
    "oak_town_4": [  # 橡木桶旅店
        "i_bread", "i_ale", "i_meat_skewer",
    ],
    "oak_town_3": [  # 老铁铁匠铺（smith 分支：武器+锻造材料）
        "i_stone_upgrade",
    ],
    # ---------- 白鹿城（南境首府） ----------
    "white_deer_6": [  # 医师馆
        "i_treat_s", "i_treat_m", "i_mana_s", "i_mana_m", "i_herb_juice", "i_bandage",
    ],
    "white_deer_5": [  # 白鹿与麦酒酒馆
        "i_ale", "i_meat_skewer", "i_stew", "i_deer_burger", "i_deer_cheese",
    ],
    "white_deer_7": [  # 烹饪坊
        "i_bread", "i_meat_skewer", "i_stew", "i_blessed_pastry",
    ],
    "white_deer_8": [  # 强化工坊（smith 分支 + 强化石）
        "i_stone_upgrade", "i_stone_refine",
    ],
    "white_deer_3": [  # 鹿角铁匠铺（smith 分支）
        "i_stone_upgrade",
    ],
    "white_deer_4": [  # 白鹿圣堂（heal + 圣物）
        "i_holy_water", "i_holy_charm", "i_scroll_purify",
    ],
    # ---------- 铁港城（冒险者圣地） ----------
    "ironharbor_5": [  # 铁锚酒馆
        "i_ale", "i_dock_rum", "i_meat_skewer", "i_stew",
    ],
    "ironharbor_6": [  # 金齿轮商行
        "i_scroll_escape", "i_scroll_teleport", "i_holy_charm", "i_stone_upgrade", "i_stone_refine",
    ],
    "ironharbor_8": [  # 渔人码头
        "i_meat_skewer", "i_stew", "i_scroll_teleport",
    ],
    "ironharbor_4": [  # 金槌拍卖行
        "i_scroll_teleport", "i_holy_charm", "i_stone_refine",
    ],
    "ironharbor_9": [  # 锻造坊（smith 分支）
        "i_stone_upgrade", "i_stone_refine",
    ],
    # ---------- 银溪镇 ----------
    "silver_brook_3": [  # 河畔旅店
        "i_bread", "i_ale", "i_meat_skewer",
    ],
    "silver_brook_4": [  # 集市
        "i_scroll_escape", "i_meat_skewer", "i_stew",
    ],
    "silver_brook_2": [  # 磨坊街
        "i_bread", "i_ale", "i_apple_wine",
    ],
    # ---------- 枫橡村 ----------
    "maple_village_4": [  # 枫叶旅店
        "i_bread", "i_ale", "i_scroll_escape",
    ],
    # ---------- 晨曦城（王都） ----------
    "dawn_city_3": [  # 圣光大教堂
        "i_bread", "i_holy_water", "i_holy_charm", "i_scroll_purify",
    ],
    "dawn_city_5": [  # 炼金工坊（herb 优先 + craft）
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_str_potion", "i_def_potion", "i_spd_potion",
    ],
    # ---------- 铁盾镇 ----------
    "ironshield_town_3": [  # 军械铺（smith + 军需补给）
        "i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_stew", "i_str_potion", "i_stone_upgrade",
    ],
    # ---------- 月冠隘口 ----------
    "moon_gate_2": [  # 银月旅店
        "i_bread", "i_ale", "i_elf_fruit",
    ],
    "moon_gate_3": [  # 哨塔集市
        "i_scroll_escape", "i_meat_skewer", "i_elf_fruit",
    ],
    # ---------- 星歌镇 ----------
    "star_song_2": [  # 星光集市
        "i_scroll_escape", "i_elf_fruit", "i_stew",
    ],
    "star_song_3": [  # 星歌旅店
        "i_bread", "i_ale", "i_elf_fruit",
    ],
    # ---------- 霜角堡 ----------
    "frost_horn_3": [  # 霜角酒馆
        "i_ale", "i_dwarf_liquor", "i_stew",
    ],
    "frost_horn_5": [  # 随军圣堂
        "i_bread", "i_holy_water",
    ],
    # ---------- 铁砧要塞 ----------
    "anvil_fort_3": [  # 符文工坊（smith + 烈酒）
        "i_dwarf_liquor", "i_stone_upgrade", "i_stone_refine",
    ],
    # ---------- 寒脊营地 ----------
    "cold_ridge_1": [  # 营地口（综合补给）
        "i_treat_l", "i_mana_l", "i_bread", "i_ale", "i_scroll_escape",
    ],
    "cold_ridge_2": [  # 主帐篷
        "i_bread", "i_stew",
    ],
    "cold_ridge_3": [  # 补给站
        "i_treat_l", "i_mana_l", "i_scroll_escape", "i_stew",
    ],
    # ---------- 极光镇 ----------
    "aurora_town_4": [  # 暖炉旅店
        "i_bread", "i_ale", "i_scroll_escape",
    ],
    # ---------- 龙裔聚落 ----------
    "dragon_kin_3": [  # 旅店
        "i_bread", "i_ale", "i_meat_skewer",
    ],
    # ---------- 翡翠港 ----------
    "jade_port_2": [  # 翡翠集市
        "i_scroll_teleport", "i_meat_skewer", "i_stew",
    ],
    "jade_port_3": [  # 船坞旅店
        "i_bread", "i_ale",
    ],
    # ---------- 贝壳镇 ----------
    "shell_town_1": [  # 贝壳集市
        "i_scroll_teleport", "i_meat_skewer", "i_stew",
    ],
    "shell_town_2": [  # 码头
        "i_meat_skewer", "i_stew", "i_scroll_teleport",
    ],
    "shell_town_3": [  # 旅店
        "i_bread", "i_ale",
    ],
    # ---------- 无名港 ----------
    "nameless_harbor_3": [  # 远洋码头
        "i_scroll_teleport", "i_meat_skewer", "i_stew", "i_dock_rum",
    ],
    # ---------- 珍珠城 ----------
    "pearl_city_3": [  # 珊瑚拍卖行
        "i_scroll_teleport", "i_holy_charm", "i_stone_refine",
    ],
    "pearl_city_4": [  # 商行
        "i_scroll_escape", "i_scroll_teleport", "i_holy_charm", "i_stone_upgrade",
    ],
    "pearl_city_5": [  # 渔港
        "i_meat_skewer", "i_stew", "i_scroll_teleport",
    ],
    # ---------- 深岩隧道 ----------
    "deep_tunnel_3": [  # 营地区
        "i_bread", "i_ale",
    ],
    # ---------- 地底集市 ----------
    "under_market_1": [  # 集市广场
        "i_scroll_escape", "i_stew", "i_meat_skewer",
    ],
    "under_market_2": [  # 拍卖区
        "i_scroll_teleport", "i_holy_charm", "i_stone_refine",
    ],
    "under_market_3": [  # 旅店
        "i_bread", "i_ale",
    ],
    # ---------- 灰烬营地 ----------
    "ember_camp_1": [  # 营地口（综合补给）
        "i_treat_l", "i_mana_l", "i_bread", "i_scroll_escape",
    ],
    "ember_camp_4": [  # 补给站
        "i_treat_l", "i_mana_l", "i_stew", "i_scroll_escape",
    ],
}

SHOP_WEAPONS = {
    # 南境·橡木系列（10 章 4.1：白装新手武器）
    "oak_town": [
        ["铁剑", "sword", 2, "white"],
        ["猎弓", "bow", 2, "white"],
        ["学徒法杖", "staff", 2, "white"],
        ["橡木短棍", "mace", 2, "white"],
        ["布拳套", "fist", 2, "white"],  # #236: 拳师武器链
    ],
    "maple_village": [
        ["铁剑", "sword", 2, "white"],
        ["猎弓", "bow", 2, "white"],
        ["学徒法杖", "staff", 2, "white"],
    ],
    # 南境·白鹿城：进阶白装 + 蓝装
    "white_deer": [
        ["铁剑", "sword", 3, "white"],
        ["猎鹿弓", "bow", 5, "blue"],
        ["学徒之杖", "staff", 5, "blue"],
        ["橡木短棍", "mace", 3, "white"],
        ["皮革拳套", "fist", 6, "green"],  # #236: 拳师武器链
    ],
    # 南境·铁港系列（10 章 4.2：海盗/水手风）
    "ironharbor": [
        ["弯刀", "sword", 14, "blue"],
        ["水手短刃", "dagger", 12, "blue"],
        ["海风长弓", "bow", 16, "blue"],
        ["铁指虎", "fist", 14, "blue"],  # #236: 拳师武器链
    ],
    "silver_brook": [
        ["弯刀", "sword", 14, "blue"],
        ["海风长弓", "bow", 14, "blue"],
    ],
    # 中域·圣光系列（10 章 4.3：王国/教会风）
    "dawn_city": [
        ["圣光长剑", "sword", 28, "blue"],
        ["晨曦法杖", "staff", 28, "blue"],
        ["王都长弓", "bow", 32, "purple"],
        ["圣殿战锤", "mace", 34, "purple"],
    ],
    "ironshield_town": [
        ["圣光长剑", "sword", 28, "blue"],
        ["晨曦法杖", "staff", 28, "blue"],
    ],
    # 群岛（翡翠海）
    "jade_port": [
        ["弯刀", "sword", 36, "blue"],
        ["海风长弓", "bow", 38, "blue"],
    ],
    "shell_town": [
        ["水手短刃", "dagger", 40, "blue"],
        ["海风长弓", "bow", 42, "blue"],
    ],
    # 西境·月语系列（10 章 4.4：精灵风）
    "moon_gate": [
        ["月语长弓", "bow", 46, "purple"],
        ["银叶法杖", "staff", 46, "purple"],
        ["月光短刃", "dagger", 48, "purple"],
    ],
    "star_song": [
        ["月语长弓", "bow", 48, "purple"],
        ["银叶法杖", "staff", 48, "purple"],
    ],
    "moon_court": [
        ["月语长弓", "bow", 55, "purple"],
        ["银叶法杖", "staff", 55, "purple"],
        ["月光短刃", "dagger", 58, "purple"],
    ],
    # 无尽海
    "nameless_harbor": [
        ["海风长弓", "bow", 56, "purple"],
        ["弯刀", "sword", 55, "purple"],
    ],
    "pearl_city": [
        ["海风长弓", "bow", 62, "purple"],
        ["银叶法杖", "staff", 62, "purple"],
    ],
    # 北境·霜狼系列（10 章 4.5：北境/矮人风）
    "frost_horn": [
        ["霜狼长剑", "sword", 62, "purple"],
        ["北风长弓", "bow", 60, "purple"],
        ["铁砧战锤", "mace", 65, "purple"],
    ],
    "anvil_fort": [
        ["铁砧战锤", "mace", 65, "purple"],
        ["霜狼长剑", "sword", 66, "purple"],
    ],
    "cold_ridge": [
        ["北风长弓", "bow", 68, "purple"],
        ["霜狼长剑", "sword", 68, "purple"],
    ],
    "aurora_town": [
        ["霜狼长剑", "sword", 70, "purple"],
        ["北风长弓", "bow", 70, "purple"],
    ],
    "deep_tunnel": [
        ["铁砧战锤", "mace", 65, "purple"],
    ],
    "under_market": [
        ["铁砧战锤", "mace", 70, "purple"],
        ["霜狼长剑", "sword", 70, "purple"],
    ],
    # 东境·龙脊系列（10 章 4.6：龙裔风）
    "dragon_pass": [
        ["龙脊大剑", "sword", 82, "purple"],
        ["龙语法杖", "staff", 82, "purple"],
    ],
    "dragon_kin": [
        ["龙脊大剑", "sword", 84, "purple"],
        ["龙语法杖", "staff", 84, "purple"],
    ],
    "ember_camp": [
        ["龙脊大剑", "sword", 86, "purple"],
        ["龙语法杖", "staff", 86, "purple"],
    ],
    "wind_city": [
        ["龙脊大剑", "sword", 86, "purple"],
        ["龙语法杖", "staff", 86, "purple"],
    ],
}

# v92 铁匠类商店材料：craft 场所（铁匠铺/锻造坊/军械/符文工坊等）只卖武器+锻造材料+全套装备，不卖消耗品
# key = 城镇地图 ID（cur or area_id 回退），值 = 材料 ID 列表（MATERIALS 表）
SHOP_SMITH_MATERIALS = {
    # 南境（Lv.1-30）：橡木镇/白鹿城/铁港
    "oak_town": [           # 老铁铁匠铺
        "mat_tie_kuang_shi",  # 铁矿石 10
        "mat_shi_cai",        # 石材 5
        "mat_jing_tie",       # 精铁 30
    ],
    "white_deer": [         # 鹿角铁匠铺
        "mat_tie_kuang_shi",  # 铁矿石 10
        "mat_jing_tie",       # 精铁 30
        "mat_mi_yin",         # 秘银 80
    ],
    "ironharbor": [         # 锻造坊
        # v101.25 #319：补铁矿石——挖掘拜师（矿工长巴尔金）要 5 铁矿石，
        # 玩家没挖掘技能挖不了矿（#318 闭环断裂），铁港城锻造坊直接卖矿解决死锁
        "mat_tie_kuang_shi",  # 铁矿石 10
        "mat_jing_tie",       # 精铁 30
        "mat_mi_yin",         # 秘银 80
    ],
    # 中域（Lv.25-55）
    "ironshield_town": [    # 军械铺
        "mat_mi_yin",         # 秘银 80
        "mat_jing_jin",       # 精金
    ],
    "dawn_city": [          # 炼金工坊（craft 但炼金除外走普通商店）
    ],
    "anvil_fort": [         # 符文工坊
        "mat_jing_jin",       # 精金
        "mat_bing_jing",      # 冰晶
    ],
}

# v93 铁匠类商店全套装备：key = 城镇地图 ID，值 = 装备名册 ID 列表（EQUIP_ROSTER）
SHOP_EQUIP = {
    "oak_town": [           # 橡木镇白装 6 件
        "eq_pi_jia",
        "eq_jiu_pi_xue",
        "eq_xiang_mu_hu_tui",
        "eq_mao_pi_mao",
        "eq_xiang_mu_jie_zhi",
        "eq_xiang_mu_xiang_lian",
    ],
    "white_deer": [         # 白鹿城绿装 6 件
        "eq_bai_lu_pi_mao",
        "eq_bai_lu_xiong_jia",
        "eq_bai_lu_hu_tui",
        "eq_bai_lu_pi_xue",
        "eq_bai_lu_zhi_jie",
        "eq_bai_lu_diao_zhu",
    ],
}
