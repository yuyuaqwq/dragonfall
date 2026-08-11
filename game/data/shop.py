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
