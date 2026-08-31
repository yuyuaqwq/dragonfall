# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - monster_mods.py（v58 怪物个体特色）

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
    # v95.16 #74：主线 q2_3『狼王·灰影』难度断层（Lv.10-11 单人 4 刻死 vs 17 刻才能杀）
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
        "mech": "summon,phase_open,player_low",
        # v116.1 低血追击示范（玩家 HP<30% 时追击，cooldown=3 防刷屏）
        "triggers": {"player_low": {"hp": 0.30, "cooldown": 3}},
        # v1.3 重创开场：玩家吸血/治疗偷取减半（2 刻）——反制吸血站撸 Boss
        "opening": {"name": "龙威·重创", "effect": "mortal_wound", "power": 2},
        "desc": "古龙·奥姆之影：龙威浩荡，会召唤雏龙护卫，开场龙威重创挑战者",
    },
    "b_cardinal": {  # 旧 b_abyss_pope 大祭司·克劳斯
        "hp_mult": 1.30, "matk_mult": 1.20,
        "mech": "heal,phase_open",
        # v1.3 神罚·重创开场：玩家吸血/治疗偷取减半（2 刻）——回血 Boss 反制吸血站撸
        "opening": {"name": "神罚·重创", "effect": "mortal_wound", "power": 2},
        "desc": "枢机主教·奥古斯都：借用旧神之力回复自身，开场神罚重创挑战者",
    },
    "b_king_odric": {  # 旧 b_silent_king 白骨君王
        "hp_mult": 1.35, "atk_mult": 1.15,
        "mech": "summon",
        "desc": "古王·奥德里克：每过几刻就唤起新的骸骨卫士",
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
    # ================= v125.1 P2 补登（boss/elite 裸奔审计） =================
    # 说明：
    # 1) 副本 Boss（19 个 b_*）由 instances.py 的 mech/hp_mult/atk_mult 注入覆盖（instance.py
    #    _enter_stage_combat/_instance_act 消费），数值与机制均不裸奔，此处不补 mod：
    #    b_goblin_chief / b_jack_pirate / b_king_odric / b_marcus / b_dawn_elf / b_helga /
    #    b_eter / b_om_shadow / b_fort_ghost / b_trial_knight / b_moon_guard / b_frost_lord /
    #    b_storm_king / b_ghost_captain / b_siren_queen / b_lange / b_aolan / b_gray_lord /
    #    b_under_dragon / b_storm_master / b_ola（其中 b_goblin_chief/b_king_odric/b_eter/
    #    b_om_shadow/b_moro/b_cardinal 本表已有数值 mod，instances mech 叠加生效）。
    #    仅 b_ember_lord（烬火·野外）/ b_lost_archivist（藏书阁·野外）无副本覆盖 → 下方补数值 mod。
    # 2) 野外/隐藏精英（e_*）此前全部裸奔 → 统一补保守个体 mod（±5%~20%），
    #    只写 6 个 mult 键（hp/atk/def/spd/matk/mdef），不改变原 role 公式基调。

    # ---------- 隐藏精英（hidden_monsters.py，v125.1 P2 补登） ----------
    "e_gold_slime": {
        "hp_mult": 1.20, "spd_mult": 0.90,
        "desc": "黄金史莱姆：一身金壳又厚又沉，跑得略慢",
    },
    "e_fortune_fox": {
        "spd_mult": 1.15, "atk_mult": 1.05,
        "desc": "幸运灵狐：机敏迅捷，爪击带三分灵气",
    },
    "e_glimmer_fish": {
        "spd_mult": 1.10, "matk_mult": 1.10,
        "desc": "荧光鱼群：游弋如光，水弹更疼",
    },
    "e_iron_bull": {
        "atk_mult": 1.10, "hp_mult": 1.15,
        "desc": "铁角蛮牛：铁角冲撞势大力沉",
    },
    "e_swamp_croc": {
        "atk_mult": 1.10, "hp_mult": 1.15,
        "desc": "沼泽巨鳄：皮糙肉厚，撕咬凶狠",
    },
    "e_forest_wolf_king": {
        "atk_mult": 1.15, "spd_mult": 1.10,
        "desc": "森林狼王：狼群之首，又快又狠",
    },
    "e_moon_wolf": {
        "spd_mult": 1.15, "atk_mult": 1.10,
        "desc": "月狼：月光下快如残影",
    },
    "e_frost_bear": {
        "hp_mult": 1.20, "atk_mult": 1.05,
        "desc": "霜原巨熊：厚毛如甲，一巴掌拍碎冰面",
    },
    "e_fungus_king": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "真菌之王：菌盖坚硬，孢子携带剧毒",
    },
    "e_mine_troll": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "矿洞巨魔：常年挖矿，身板结实",
    },
    "e_abbey_guardian": {
        "def_mult": 1.15, "hp_mult": 1.10,
        "desc": "圣堂武僧：金钟罩般的横练功夫",
    },
    "e_ash_salamander": {
        "matk_mult": 1.15, "spd_mult": 1.10,
        "desc": "烬火蝾螈：吐息滚烫，身形灵活",
    },
    "e_sea_serpent": {
        "atk_mult": 1.10, "hp_mult": 1.15,
        "desc": "海蛇：鳞甲坚韧，绞杀有力",
    },
    "e_storm_eagle": {
        "spd_mult": 1.20, "atk_mult": 1.05,
        "desc": "雷暴鹰：俯冲快若闪电",
    },
    "e_cloud_serpent": {
        "matk_mult": 1.15, "spd_mult": 1.10,
        "desc": "云龙：腾云驾雾，吐息带雷光",
    },
    "e_deep_angler": {
        "matk_mult": 1.15, "hp_mult": 1.05,
        "desc": "深海鮟鱇：幽光钓饵摄人心魄",
    },
    "e_dragon_hatchling": {
        "atk_mult": 1.15, "spd_mult": 1.05,
        "desc": "幼龙：龙威初显，爪牙锋利",
    },
    "e_ghost_knight": {
        "atk_mult": 1.10, "def_mult": 1.15,
        "desc": "幽灵骑士：锈甲不腐，剑刃带寒",
    },
    "e_lava_golem": {
        "hp_mult": 1.20, "atk_mult": 1.10,
        "desc": "熔岩魔像：滚烫岩躯，重拳如锤",
    },
    "e_royal_guard": {
        "def_mult": 1.15, "atk_mult": 1.05,
        "desc": "王都禁卫：重甲在身，枪阵森严",
    },
    "e_shadow_stalker": {
        "atk_mult": 1.15, "spd_mult": 1.10,
        "desc": "暗影猎手：黑暗中出手，快而致命",
    },
    "e_siren": {
        "matk_mult": 1.15, "hp_mult": 1.05,
        "desc": "塞壬：歌声如刃，法术凌厉",
    },
    # ---------- 野外精英（subareas.py，v125.1 P2 补登） ----------
    "e_great_boar": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "巨型野猪：獠牙拱地，皮厚膘肥",
    },
    "e_gorge_troll": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "峡谷巨魔：山石般的身板",
    },
    "e_boar_king": {
        "hp_mult": 1.20, "atk_mult": 1.10,
        "desc": "野猪王·裂鬃：鬃毛如刺，冲撞开山",
    },
    "e_valley_troll": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "谷地巨魔：皮糙肉厚，蛮力惊人",
    },
    "e_swamp_king": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "沼泽巨鳄·沼王：潜伏一击，咬合如闸",
    },
    "e_plain_wolf": {
        "atk_mult": 1.10, "spd_mult": 1.10,
        "desc": "平原狼王：草原猎手，快准狠",
    },
    "e_cave_troll": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "洞穴巨魔：洞窟霸主，筋骨结实",
    },
    "e_pirate_lieutenant": {
        "atk_mult": 1.10, "hp_mult": 1.05,
        "desc": "海盗副官：弯刀淬毒，出手狠辣",
    },
    "e_river_dragon_lord": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "河龙领主：控水成术，鳞甲坚韧",
    },
    "e_inquisitor": {
        "matk_mult": 1.15, "hp_mult": 1.05,
        "desc": "审判官：圣焰法术炽烈",
    },
    "e_hill_wolf_king": {
        "atk_mult": 1.10, "hp_mult": 1.15,
        "desc": "丘陵狼王·铁牙：铁牙咬碎盾牌",
    },
    "e_knight_instructor": {
        "atk_mult": 1.10, "def_mult": 1.10,
        "desc": "骑士教官：攻守有度，招式老辣",
    },
    "e_battle_lord": {
        "atk_mult": 1.15, "hp_mult": 1.10,
        "desc": "百族战将·亡影：百战余生，凶悍绝伦",
    },
    "e_reef_king": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "珊瑚礁主·红棘：棘甲坚硬，钳击有力",
    },
    "e_island_tiger": {
        "atk_mult": 1.15, "spd_mult": 1.10,
        "desc": "落日岛虎·金焰：扑击迅猛，爪裂岩石",
    },
    "e_siren_lord": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "海妖领主·潮汐：潮汐之力加身",
    },
    "e_valley_lord": {
        "matk_mult": 1.10, "hp_mult": 1.15,
        "desc": "翠谷领主·林语：自然之力厚重",
    },
    "e_moon_wolf_alpha": {
        "atk_mult": 1.10, "spd_mult": 1.15,
        "desc": "月狼王·银鬃：月色下的闪电",
    },
    "e_storm_leviathan": {
        "hp_mult": 1.15, "matk_mult": 1.10,
        "desc": "风暴巨兽：雷雨淬炼的庞然巨物",
    },
    "e_lake_king": {
        "matk_mult": 1.10, "hp_mult": 1.15,
        "desc": "星语湖王：湖灵庇佑，水术绵长",
    },
    "e_wind_king": {
        "spd_mult": 1.15, "matk_mult": 1.10,
        "desc": "风语王·岚歌：御风而行，风刃无形",
    },
    "e_archive_warden": {
        "matk_mult": 1.15, "hp_mult": 1.05,
        "desc": "档案馆长·奥古斯特：禁书法术凌厉",
    },
    "e_moon_lord": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "月光领主·银辉：月华护体，法术皎洁",
    },
    "e_moonshadow_lord": {
        "atk_mult": 1.10, "spd_mult": 1.15,
        "desc": "月影领主·夜歌：影随心动，快如鬼魅",
    },
    "e_trench_leviathan": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "海沟巨兽·渊影：深渊巨口，吞天噬地",
    },
    "e_whale_king": {
        "hp_mult": 1.20, "atk_mult": 1.05,
        "desc": "龙鲸王·涛声：如山身躯，一撞碎舟",
    },
    "e_graveyard_lord": {
        "atk_mult": 1.15, "def_mult": 1.05,
        "desc": "沉船领主·溺骨：锈刃凶戾，怨气缠身",
    },
    "e_ice_fang_lord": {
        "atk_mult": 1.10, "hp_mult": 1.10,
        "desc": "冰牙领主·霜白：冰甲覆身，獠牙如锥",
    },
    "e_frost_troll_lord": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "霜巨魔王：霜巨人中的王，耐打且力大",
    },
    "e_storm_dragon": {
        "matk_mult": 1.15, "spd_mult": 1.05,
        "desc": "风暴海龙·雷鸣：吐息裹挟雷暴",
    },
    "e_frost_mammoth": {
        "hp_mult": 1.20, "atk_mult": 1.05,
        "desc": "冰原猛犸·雪岭：长毛如甲，踩踏如崩",
    },
    "e_lake_lord": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "永冬湖主·冰瞳：冰术深沉，冻气逼人",
    },
    "e_dark_leech": {
        "matk_mult": 1.10, "hp_mult": 1.15,
        "desc": "黑暗水蛭王：吸饱暗能，身躯坚韧",
    },
    "e_rot_chief_guard": {
        "hp_mult": 1.15, "atk_mult": 1.10,
        "desc": "腐牙亲卫：腐化之躯不知疼痛",
    },
    "e_glacier_wyrm": {
        "atk_mult": 1.10, "hp_mult": 1.15,
        "desc": "冰川龙·霜牙：寒鳞如铁，牙口锋利",
    },
    "e_demon_warrior": {
        "atk_mult": 1.15, "hp_mult": 1.10,
        "desc": "恶魔战士：地狱火淬炼的肌肉",
    },
    "e_molten_lord": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "熔火领主·烬核：岩浆在胸腔翻涌",
    },
    "e_ash_champion": {
        "atk_mult": 1.15, "spd_mult": 1.05,
        "desc": "灰烬勇士：余烬不灭，战意不熄",
    },
    "e_cloud_lord": {
        "matk_mult": 1.10, "hp_mult": 1.15,
        "desc": "云海领主·雾冠：云雾凝甲，术法悠长",
    },
    "e_red_dragon_lord": {
        "matk_mult": 1.15, "atk_mult": 1.05,
        "desc": "赤龙领主·烬翼：龙息焚天，爪裂山岩",
    },
    "e_magma_king": {
        "hp_mult": 1.15, "matk_mult": 1.10,
        "desc": "岩浆王·烬核：岩浆之躯，法术滚烫",
    },
    "e_altar_guardian": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "祭坛守卫·魔眼：邪眼凝视，术法诡异",
    },
    "e_dragon_lord_ghost": {
        "atk_mult": 1.10, "hp_mult": 1.15,
        "desc": "龙陨战魂·暮影：执念凝躯，龙威犹在",
    },
    "e_dragon_roost_king": {
        "atk_mult": 1.15, "hp_mult": 1.10,
        "desc": "龙巢王·焰翼：巢穴之主，爪牙如刃",
    },
    "e_rainbow_dragon": {
        "matk_mult": 1.10, "spd_mult": 1.10,
        "desc": "彩虹龙·霞光：七色吐息变幻莫测",
    },
    "e_storm_lord": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "雷暴领主·雷霆：雷云随身，术法轰鸣",
    },
    "e_star_dragon": {
        "matk_mult": 1.15, "atk_mult": 1.05,
        "desc": "星龙·辰光：星光凝息，爪带星辉",
    },
    # ---------- 野外 Boss（无副本 mech 覆盖，v125.1 P2 补登） ----------
    "b_ember_lord": {
        "hp_mult": 1.20, "atk_mult": 1.10, "matk_mult": 1.10,
        "desc": "烬火领主·伊格尼斯：烬山之心，烈焰不熄",
    },
    "b_lost_archivist": {
        "matk_mult": 1.15, "hp_mult": 1.10,
        "desc": "守馆者·遗忘贤者：禁书库的守门人，术法渊深",
    },
}
