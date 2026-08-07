# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - monster_mods.py（v58 怪物个体特色）

同一 role 同等级的怪原本数值完全相同（公式化）。这里按怪物 ID 给个体修正，
让同名怪有"性格"：皮糙肉厚 / 快而脆 / 攻高防低 等。

字段：hp_mult / atk_mult / def_mult / spd_mult / matk_mult / mdef_mult
- 值 >1 增强、<1 削弱；未配置的字段保持公式值
- 只写与模板不同的字段；desc 用于图鉴展示
"""
MONSTER_MODS = {
    # ---------- 南境·橡木镇（新手区） ----------
    "m_stray_dog": {
        "atk_mult": 1.20, "hp_mult": 0.85, "spd_mult": 1.15,
        "desc": "野狗：牙尖嘴利攻高，但瘦弱血少",
    },
    "m_giant_rat": {
        "hp_mult": 0.75, "spd_mult": 1.35,
        "desc": "巨型老鼠：快而脆，成群出没",
    },
    "e_bandit_leader": {
        "hp_mult": 1.30, "atk_mult": 0.90,
        "desc": "山贼头目：皮糙肉厚，比普通精英更能扛",
    },
    # ---------- 翡翠森林 ----------
    "m_forest_wolf": {
        "atk_mult": 1.15, "def_mult": 0.85,
        "desc": "森林狼：猎手本性，攻高防低",
    },
    "m_venom_spider": {
        "spd_mult": 1.40, "hp_mult": 0.80,
        "desc": "毒蜘蛛：动作极快，毒牙致命但身板脆",
    },
    "m_greensprite": {
        "matk_mult": 1.25, "hp_mult": 0.85,
        "desc": "绿妖精：法术暴烈，本体孱弱",
    },
    "e_forest_treant": {
        "hp_mult": 1.45, "atk_mult": 0.85, "spd_mult": 0.70,
        "desc": "远古树人：皮糙肉厚行动迟缓，别跟它耗",
    },
    "b_ancient_elk": {
        "hp_mult": 1.25, "spd_mult": 1.30,
        "mech": "heal",
        "desc": "远古圣鹿：森林之灵，矫健而坚韧，会汲取自然之力自愈",
    },
    # ---------- 矿洞 ----------
    "m_goblin_grunt": {
        "def_mult": 1.20, "atk_mult": 0.95,
        "desc": "地精步兵：破铜烂铁堆出来的硬壳",
    },
    "m_mine_bat": {
        "spd_mult": 1.50, "hp_mult": 0.70,
        "desc": "矿洞蝙蝠：速度极快，怕光",
    },
    "m_tunnel_snake": {
        "hp_mult": 1.35, "atk_mult": 0.90,
        "desc": "洞穴巨蛇：缠住就不撒口，血厚耐打",
    },
    "e_goblin_shaman": {
        "matk_mult": 1.30, "hp_mult": 0.90,
        "desc": "地精萨满：黑巫术加持，法术更凶",
    },
    "b_tunnel_king": {
        "hp_mult": 1.30, "atk_mult": 1.15,
        "mech": "enrage",
        "desc": "隧洞之王：矿洞霸主，力大无穷，重伤后陷入狂暴",
    },
    # ---------- 沼泽 ----------
    "m_swamp_zombie": {
        "hp_mult": 1.40, "atk_mult": 0.90, "spd_mult": 0.70,
        "desc": "沼泽僵尸：笨重迟缓，但很难打死",
    },
    "m_bog_ghost": {
        "matk_mult": 1.30, "hp_mult": 0.80,
        "desc": "沼泽鬼魂：怨念凝形，法术凶猛",
    },
    "e_bone_warlock": {
        "matk_mult": 1.35, "hp_mult": 0.90,
        "desc": "骸骨术士：死灵法术比同类更凶",
    },
    "b_decay_lord": {
        "hp_mult": 1.30, "atk_mult": 1.10,
        "mech": "summon",
        "desc": "腐朽领主：吞噬生机的沼泽霸主，会呼唤腐尸助战",
    },
    # ---------- 战歌营地 ----------
    "m_orc_grunt": {
        "atk_mult": 1.20, "hp_mult": 1.10,
        "desc": "兽人步兵：力气大血也厚",
    },
    "m_warg": {
        "spd_mult": 1.45, "atk_mult": 1.10,
        "desc": "座狼：兽人驯养的猎犬，快且狠",
    },
    "e_orc_berserker": {
        "atk_mult": 1.35, "hp_mult": 1.10,
        "desc": "兽人狂战士：陷入狂怒后不管不顾",
    },
    # ---------- 死城/黑石 ----------
    "m_skeleton_guard": {
        "def_mult": 1.35, "atk_mult": 0.90,
        "desc": "骷髅卫兵：白骨甲胄硬得很",
    },
    "m_ghoul": {
        "atk_mult": 1.20, "spd_mult": 1.15,
        "desc": "食尸鬼：扑咬凶狠，动作不慢",
    },
    "e_death_knight": {
        "atk_mult": 1.20, "def_mult": 1.20,
        "desc": "死亡骑士：攻守兼备的亡灵战将",
    },
    # ---------- 熔岩 ----------
    "m_fire_elemental": {
        "matk_mult": 1.30, "def_mult": 0.80,
        "desc": "火元素：纯法术输出，遇水即弱",
    },
    "e_flame_giant": {
        "hp_mult": 1.30, "atk_mult": 1.15,
        "desc": "火焰巨人：熔岩铸就的庞然巨物",
    },
    # ---------- 冰原 ----------
    "m_frost_troll": {
        "hp_mult": 1.40, "spd_mult": 0.75,
        "desc": "冰霜巨魔：冰雪冻住了它的腿脚",
    },
    "m_snow_wraith": {
        "matk_mult": 1.25, "spd_mult": 1.20,
        "desc": "雪魅：御风而行，法术寒意刺骨",
    },
    # ---------- 风暴 ----------
    "m_giant_eagle": {
        "spd_mult": 1.50, "atk_mult": 1.10,
        "desc": "巨鹰：俯冲快若闪电",
    },
    "e_sky_hunter": {
        "spd_mult": 1.35, "atk_mult": 1.15,
        "desc": "苍穹猎手：风暴之子，快攻型",
    },
    # ---------- 暗影 ----------
    "m_shadow_demon": {
        "matk_mult": 1.30, "hp_mult": 0.90,
        "desc": "暗影恶魔：阴影中的法术杀手",
    },
    "m_void_reaver": {
        "atk_mult": 1.30, "hp_mult": 0.90,
        "desc": "虚空掠夺者：牺牲体魄换来的极致攻击",
    },
    # ---------- 秘银 ----------
    "m_mithril_golem": {
        "def_mult": 1.45, "atk_mult": 0.85, "spd_mult": 0.60,
        "desc": "秘银魔像：刀枪不入的重甲傀儡",
    },
    "m_runebound_knight": {
        "atk_mult": 1.20, "def_mult": 1.15,
        "desc": "符文骑士：符文之力加持的攻守均衡",
    },
    # ---------- 远境 ----------
    "m_holy_guard": {
        "def_mult": 1.30, "hp_mult": 1.15,
        "desc": "大教堂卫士：圣盾加护的铁壁",
    },
    "m_seraph": {
        "matk_mult": 1.30, "hp_mult": 0.85,
        "desc": "白翼教众：圣光法术炽烈，肉体凡胎",
    },
    # ---------- 精灵 ----------
    "m_elf_archer": {
        "atk_mult": 1.15, "spd_mult": 1.25,
        "desc": "精灵弓手：箭术百步穿杨",
    },
    "m_moon_panther": {
        "spd_mult": 1.50, "atk_mult": 1.10,
        "desc": "月影豹：月光下快得只剩残影",
    },
    # ---------- 龙族 ----------
    "m_cliff_wyvern": {
        "spd_mult": 1.40, "atk_mult": 1.10,
        "desc": "岩脊飞龙：俯冲撕裂，快攻型",
    },
    "m_dragonkin": {
        "atk_mult": 1.20, "hp_mult": 1.10,
        "desc": "龙裔战士：血脉之力，攻高血厚",
    },
    "b_dark_lord": {
        "hp_mult": 1.25, "atk_mult": 1.10,
        "mech": "enrage",
        "desc": "魔王·阿兹莫丹：深渊之门的主宰，濒死时爆发出最后的暴怒",
    },
    "b_dragon_king": {
        "hp_mult": 1.35, "atk_mult": 1.20,
        "mech": "summon",
        "desc": "古龙·奥瑞斯：龙威浩荡，会召唤雏龙护卫",
    },
    "b_abyss_pope": {
        "hp_mult": 1.30, "matk_mult": 1.20,
        "mech": "heal",
        "desc": "大祭司·克劳斯：借用旧神之力回复自身",
    },
    "b_silent_king": {
        "hp_mult": 1.35, "atk_mult": 1.15,
        "mech": "summon",
        "desc": "白骨君王：每过几回合就唤起新的骸骨卫士",
    },
    "b_chaos_lord": {
        "hp_mult": 1.40, "atk_mult": 1.25,
        "mech": "enrage",
        "desc": "巫王·莫里斯：混沌巫术的顶点，越战越狂",
    },
    # ---------- 虚空 ----------
    "m_void_worm": {
        "spd_mult": 1.45, "hp_mult": 0.85,
        "desc": "裂隙蠕虫：扭曲空间穿行，快而脆",
    },
    "m_void_colossus": {
        "hp_mult": 1.45, "atk_mult": 1.10, "spd_mult": 0.70,
        "desc": "裂隙巨像：虚空造物，迟钝而恐怖",
    },
}
