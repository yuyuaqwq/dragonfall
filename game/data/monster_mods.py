# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - monster_mods.py（v58 怪物个体特色）

同一 role 同等级的怪原本数值完全相同（公式化）。这里按怪物 ID 给个体修正，
让同名怪有"性格"：皮糙肉厚 / 快而脆 / 攻高防低 等。

字段：hp_mult / atk_mult / def_mult / spd_mult / matk_mult / mdef_mult
- 值 >1 增强、<1 削弱；未配置的字段保持公式值
- 只写与模板不同的字段；desc 用于图鉴展示

v104 修复（M06 P1）：stage11 旧世界迁移后 42 条旧怪物 ID 全库零引用，
已按新世界 ID（subareas/instances/hidden_monsters）语义迁移；mech 字段随迁
（野外怪/Boss 的 mech 由 build_monster 从本表读取，副本 Boss 由 instances.py 覆盖）。
"""
MONSTER_MODS = {
    # ---------- 橡木镇·白鹿之森（新手区） ----------
    "m_wild_dog": {  # 旧 m_stray_dog 野狗
        "atk_mult": 1.20, "hp_mult": 0.85, "spd_mult": 1.15,
        "desc": "野狗：牙尖嘴利攻高，但瘦弱血少",
    },
    # m_giant_rat 保留原名：tests/test_v58_flavor.py 数值断言硬依赖（巨型老鼠 0.75x hp / 1.35x spd）
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
    # v95.16 #74：主线 q2_3『狼王·灰影』难度断层（Lv.10-11 单人 4 回合死 vs 17 回合才能杀）
    # 下调个体数值：959→498HP、98→58atk、75→45matk（相当于精英 Lv.10-11 水平，保持挑战性）
    "e_wolf_alpha": {
        "hp_mult": 0.52, "atk_mult": 0.60, "matk_mult": 0.60,
        "desc": "狼王·灰影：盘踞翡翠森林深处的狼王，凶名在外",
    },
    "m_giant_spider": {  # 旧 m_venom_spider 毒蜘蛛
        "spd_mult": 1.40, "hp_mult": 0.80,
        "desc": "巨型蜘蛛：动作极快，毒牙致命但身板脆",
    },
    "m_valley_faerie": {  # 旧 m_greensprite 绿妖精
        "matk_mult": 1.25, "hp_mult": 0.85,
        "desc": "谷地仙灵：法术暴烈，本体孱弱",
    },
    "e_tree_lord": {  # 旧 e_forest_treant 远古树人
        "hp_mult": 1.45, "atk_mult": 0.85, "spd_mult": 0.70,
        "desc": "古树领主：皮糙肉厚行动迟缓，别跟它耗",
    },
    "e_white_stag": {  # 旧 b_ancient_elk 远古圣鹿
        "hp_mult": 1.25, "spd_mult": 1.30,
        "mech": "heal",
        "desc": "白鹿王：森林之灵，矫健而坚韧，会汲取自然之力自愈",
    },
    # ---------- 矿洞/哥布林营地 ----------
    "m_goblin_warrior": {  # 旧 m_goblin_grunt 地精步兵
        "def_mult": 1.20, "atk_mult": 0.95,
        "desc": "哥布林战士：破铜烂铁堆出来的硬壳",
    },
    "m_cave_bat": {  # 旧 m_mine_bat 矿洞蝙蝠
        "spd_mult": 1.50, "hp_mult": 0.70,
        "desc": "洞穴蝙蝠：速度极快，怕光",
    },
    "m_snake": {  # 旧 m_tunnel_snake 洞穴巨蛇
        "hp_mult": 1.35, "atk_mult": 0.90,
        "desc": "毒蛇：缠住就不撒口，血厚耐打",
    },
    "m_goblin_shaman": {  # 旧 e_goblin_shaman 地精萨满
        "matk_mult": 1.30, "hp_mult": 0.90,
        "desc": "哥布林萨满：黑巫术加持，法术更凶",
    },
    "b_goblin_chief": {  # 旧 b_tunnel_king 隧洞之王
        "hp_mult": 1.30, "atk_mult": 1.15,
        "mech": "enrage",
        "desc": "哥布林酋长·咕噜：营地霸主，力大无穷，重伤后陷入狂暴",
    },
    # ---------- 沼泽/菌林 ----------
    "m_zombie": {  # 旧 m_swamp_zombie 沼泽僵尸
        "hp_mult": 1.40, "atk_mult": 0.90, "spd_mult": 0.70,
        "desc": "僵尸：笨重迟缓，但很难打死",
    },
    "m_ghost": {  # 旧 m_bog_ghost 沼泽鬼魂
        "matk_mult": 1.30, "hp_mult": 0.80,
        "desc": "幽灵：怨念凝形，法术凶猛",
    },
    "e_bone_lord": {  # 旧 e_bone_warlock 骸骨术士
        "matk_mult": 1.35, "hp_mult": 0.90,
        "desc": "骨龙领主·骸王：死灵法术比同类更凶",
    },
    "e_fungus_lord": {  # 旧 b_decay_lord 腐朽领主
        "hp_mult": 1.30, "atk_mult": 1.10,
        "mech": "summon",
        "desc": "真菌领主·腐冠：吞噬生机的沼泽霸主，会呼唤腐尸助战",
    },
    # ---------- 战歌营地/边境城堡 ----------
    "m_orc_raider": {  # 旧 m_orc_grunt 兽人步兵
        "atk_mult": 1.20, "hp_mult": 1.10,
        "desc": "兽人劫掠者：力气大血也厚",
    },
    "m_steppe_wolf": {  # 旧 m_warg 座狼
        "spd_mult": 1.45, "atk_mult": 1.10,
        "desc": "草原狼：兽人驯养的猎犬，快且狠",
    },
    "e_orc_warrior": {  # 旧 e_orc_berserker 兽人狂战士
        "atk_mult": 1.35, "hp_mult": 1.10,
        "desc": "兽人战士：陷入狂怒后不管不顾",
    },
    # ---------- 死城/王陵古道 ----------
    "m_skeleton": {  # 旧 m_skeleton_guard 骷髅卫兵
        "def_mult": 1.35, "atk_mult": 0.90,
        "desc": "骷髅兵：白骨甲胄硬得很",
    },
    "m_rot_orc": {  # 旧 m_ghoul 食尸鬼
        "atk_mult": 1.20, "spd_mult": 1.15,
        "desc": "腐牙兽人：扑咬凶狠，动作不慢",
    },
    "e_grave_lord": {  # 旧 e_death_knight 死亡骑士
        "atk_mult": 1.20, "def_mult": 1.20,
        "desc": "古墓领主：攻守兼备的亡灵战将",
    },
    # ---------- 熔岩 ----------
    "m_lava_elemental": {  # 旧 m_fire_elemental 火元素
        "matk_mult": 1.30, "def_mult": 0.80,
        "desc": "熔岩元素：纯法术输出，遇水即弱",
    },
    "e_lava_lord": {  # 旧 e_flame_giant 火焰巨人
        "hp_mult": 1.30, "atk_mult": 1.15,
        "desc": "熔岩领主：熔岩铸就的庞然巨物",
    },
    # ---------- 冰原 ----------
    "m_frost_troll": {
        "hp_mult": 1.40, "spd_mult": 0.75,
        "desc": "冰霜巨魔：冰雪冻住了它的腿脚",
    },
    "m_ice_elemental": {  # 旧 m_snow_wraith 雪魅
        "matk_mult": 1.25, "spd_mult": 1.20,
        "desc": "冰元素：御风而行，法术寒意刺骨",
    },
    # ---------- 风暴 ----------
    "m_valley_eagle": {  # 旧 m_giant_eagle 巨鹰
        "spd_mult": 1.50, "atk_mult": 1.10,
        "desc": "谷地巨鹰：俯冲快若闪电",
    },
    "e_storm_cliff_lord": {  # 旧 e_sky_hunter 苍穹猎手
        "spd_mult": 1.35, "atk_mult": 1.15,
        "desc": "风暴崖主·雷鸣：风暴之子，快攻型",
    },
    # ---------- 暗影/深渊 ----------
    "m_abyss_demon": {  # 旧 m_shadow_demon 暗影恶魔
        "matk_mult": 1.30, "hp_mult": 0.90,
        "desc": "深渊恶魔：阴影中的法术杀手",
    },
    "m_void_hound": {  # 旧 m_void_reaver 虚空掠夺者
        "atk_mult": 1.30, "hp_mult": 0.90,
        "desc": "虚空猎犬：牺牲体魄换来的极致攻击",
    },
    # ---------- 秘银/星辉 ----------
    "m_meteor_golem": {  # 旧 m_mithril_golem 秘银魔像
        "def_mult": 1.45, "atk_mult": 0.85, "spd_mult": 0.60,
        "desc": "陨星魔像：刀枪不入的重甲傀儡",
    },
    "e_rune_golem": {  # 旧 m_runebound_knight 符文骑士
        "atk_mult": 1.20, "def_mult": 1.15,
        "desc": "符文魔像：符文之力加持的攻守均衡",
    },
    # ---------- 远境/圣堂 ----------
    "m_temple_guard": {  # 旧 m_holy_guard 大教堂卫士
        "def_mult": 1.30, "hp_mult": 1.15,
        "desc": "圣殿守卫：圣盾加护的铁壁",
    },
    "m_light_priest": {  # 旧 m_seraph 白翼教众
        "matk_mult": 1.30, "hp_mult": 0.85,
        "desc": "光之祭司：圣光法术炽烈，肉体凡胎",
    },
    # ---------- 精灵 ----------
    "e_elf_sentinel": {  # 旧 m_elf_archer 精灵弓手
        "atk_mult": 1.15, "spd_mult": 1.25,
        "desc": "精灵哨兵：箭术百步穿杨",
    },
    "m_shadow_panther": {  # 旧 m_moon_panther 月影豹
        "spd_mult": 1.50, "atk_mult": 1.10,
        "desc": "影豹：月光下快得只剩残影",
    },
    # ---------- 龙族 ----------
    "m_red_wyvern": {  # 旧 m_cliff_wyvern 岩脊飞龙
        "spd_mult": 1.40, "atk_mult": 1.10,
        "desc": "赤翼飞龙：俯冲撕裂，快攻型",
    },
    "m_dragonkin": {
        "atk_mult": 1.20, "hp_mult": 1.10,
        "desc": "龙裔战士：血脉之力，攻高血厚",
    },
    "b_moro": {  # 旧 b_dark_lord 魔王·阿兹莫丹
        "hp_mult": 1.25, "atk_mult": 1.10,
        "mech": "enrage,phase_open",
        # v116.1 剧本化示范：开场咆哮 + 三阶段换招/演出/预告（数据可选字段，不配置则行为不变）
        "opening": {"name": "深渊咆哮", "effect": "atk_up", "power": 2},
        "phases": [
            {"min": 60, "add_skills": ["ms_zhao_huan_e_mo"],
             "script": {"name": "深渊之躯浮现", "icon": "🌑"}},
            {"min": 30, "add_skills": ["ms_shen_yuan_zhi_nu"],
             "script": {"name": "魔核迸裂", "icon": "💀"}},
        ],
        "desc": "深渊领主·摩罗：深渊之门的主宰，濒死时爆发出最后的暴怒",
    },
    "b_om_shadow": {  # 旧 b_dragon_king 古龙·奥瑞斯
        "hp_mult": 1.35, "atk_mult": 1.20,
        "mech": "summon,player_low",
        # v116.1 低血追击示范（玩家 HP<30% 时追击，cooldown=3 防刷屏）
        "triggers": {"player_low": {"hp": 0.30, "cooldown": 3}},
        "desc": "古龙·奥姆之影：龙威浩荡，会召唤雏龙护卫",
    },
    "b_cardinal": {  # 旧 b_abyss_pope 大祭司·克劳斯
        "hp_mult": 1.30, "matk_mult": 1.20,
        "mech": "heal",
        "desc": "枢机主教·奥古斯都：借用旧神之力回复自身",
    },
    "b_king_odric": {  # 旧 b_silent_king 白骨君王
        "hp_mult": 1.35, "atk_mult": 1.15,
        "mech": "summon",
        "desc": "古王·奥德里克：每过几回合就唤起新的骸骨卫士",
    },
    "b_eter": {  # 旧 b_chaos_lord 巫王·莫里斯
        "hp_mult": 1.40, "atk_mult": 1.25,
        "mech": "enrage",
        "desc": "蚀夜·真相形态：混沌巫术的顶点，越战越狂",
    },
    # ---------- 虚空/深渊 ----------
    "m_magma_worm": {  # 旧 m_void_worm 裂隙蠕虫
        "spd_mult": 1.45, "hp_mult": 0.85,
        "desc": "熔岩蠕虫：扭曲空间穿行，快而脆",
    },
    "m_obsidian_golem": {  # 旧 m_void_colossus 裂隙巨像
        "hp_mult": 1.45, "atk_mult": 1.10, "spd_mult": 0.70,
        "desc": "黑曜石魔像：虚空造物，迟钝而恐怖",
    },
}
