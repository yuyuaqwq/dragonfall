# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - skills.py(阶段六：基础技能 v2.0，12 章)"""
PLAYER_SKILLS = {
    "cls_bard": {
        "name": "吟游诗人",
        "skills": {
"sk_ji_xing_tan_chang": {
                "lv": 1, "mp": 0, "power": 1.0, "kind": "物理",
                "mech": "poison", "mech_val": 1,
                "desc": "即兴弹唱！100% 物理伤害，15% 概率使目标中毒",
                "name": "即兴弹唱",
            },
    "sk_qin_xian": {
                "lv": 2,
                "mp": 0,
                "power": 1.1,
                "kind": "物理",
                "res_gain": 1,
                "mech": "poison",
                "mech_chance": 0.1,
                "desc": "轻快拨弦，110% 物理伤害，10% 附加中毒。吟游诗人的热身曲。",
                "name": "轻快拨弦",
            },
"sk_zhan_ge": {
                "lv": 3, "mp": 10, "power": 0, "kind": "增益",
                "effect": "atk_up", "team": "atk_all", "cd": 2,
                "desc": "激昂战歌！全队攻＋25% 2 回合(副本广播，团队技能)",
                "name": "战歌",
            },
"sk_an_mian_qu": {
                "lv": 6, "mp": 10, "power": 0, "kind": "增益",
                "effect": "mon_atk_down", "cd": 3,
                "desc": "安眠曲！敌方攻击－30% 3 回合",
                "name": "安眠曲",
            },
"sk_gu_wu": {
                "lv": 9, "mp": 10, "power": 0, "kind": "增益",
                "effect": "crit_up", "team": "crit_all", "cd": 2,
                "desc": "鼓舞士气！全队暴击＋20% 2 回合(副本广播，团队技能)",
                "name": "鼓舞",
            },
"sk_ai_ge": {
                "lv": 14, "mp": 15, "power": 1.6, "kind": "魔法",
                "cc": "silence", "cd": 3,
                "desc": "哀歌！160% 魔法伤害，50% 概率沉默目标 2 回合",
                "name": "哀歌",
            },
"sk_jing_mo_zhi_ge": {
                "lv": 18, "mp": 15, "power": 0, "kind": "增益",
                "effect": "spd_up", "team": "spd_all", "cd": 2,
                "desc": "轻快旋律！全队速度＋40% 2 回合(副本广播，团队技能)",
                "name": "静默之歌",
            },
"sk_ying_xiong_xu_shi_shi": {
                "lv": 24, "mp": 20, "power": 1.5, "kind": "治疗",
                "cd": 2, "team": "heal_all",
                "desc": "英雄叙事诗！治疗全队 150% 生命(副本广播，团队技能)",
                "name": "英雄叙事诗",
            },
"sk_ao_shu_yong_tan_diao": {
                "lv": 30, "mp": 20, "power": 0, "kind": "增益",
                "effect": "matk_up", "team": "matk_all", "cd": 2,
                "desc": "奥术咏叹调！全队魔攻＋35% 2 回合(副本广播，团队技能)",
                "name": "奥术咏叹调",
            },
"sk_li_ming_song_ge": {
                "lv": 40, "mp": 35, "power": 0, "kind": "增益",
                "effect": "atk_up_strong", "team": "atk_all", "cd": 5,
                "desc": "终章·黎明颂歌！全队攻＋75% 3 回合(副本广播，团队技能)",
                "name": "终章·黎明颂歌",
            },
"sk_ban_zou": {
                "lv": 55, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "crit", "add": 0.08},
                "desc": "属性被动：伴奏之魂，暴击＋8%",
                "name": "伴奏",
            },
        }
    },
    "cls_zhan_shi": {
        "name": "战士",
        "skills": {
    "sk_hui_kan": {
                "lv": 1,
                "mp": 0,
                "power": 1.0,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"},
                "desc": "基础斩击，100% 物理伤害，怒气＋1。先手(速度高于目标)时伤害＋15%",
                "name": "挥砍",
            },
    "sk_meng_ji": {
                "lv": 2,
                "mp": 0,
                "power": 1.2,
                "kind": "物理",
                "res_gain": 1,
                "desc": "猛力一击，120% 物理伤害，怒气＋1。",
                "name": "猛击",
            },
    "sk_po_jia_zhan": {
                "lv": 8,
                "mp": 0,
                "power": 1.3,
                "kind": "物理",
                "pierce": True,
                "res_gain": 2,
                "cond": {"type": "player_hp_low", "hp_pct": 0.4, "mult": 1.2, "label": "绝地反击"},
                "desc": "破防斩击，130% 物理伤害(无视防御)，怒气＋2。自身 HP<40% 时伤害＋20%",
                "name": "破甲斩",
            },
    "sk_xuan_feng_zhan": {
                "lv": 14,
                "mp": 0,
                "power": 1.1,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "enemy_hp_high", "hp_pct": 0.7, "mult": 1.4, "label": "孤军深入"},
                "desc": "旋转斩击，110% 全体伤害(对单体等效)，怒气＋1。目标 HP>70% 时＋40%",
                "name": "旋风斩",
            },
    "sk_lie_di_zhan": {
                "lv": 20,
                "mp": 0,
                "power": 1.8,
                "kind": "物理",
                "pierce": True,
                "res_cost": {"rage": 3},
                "cond": {"type": "player_res_stacks", "res_key": "rage", "stacks": 8, "mult": 1.5, "label": "震怒"},
                "desc": "终结技，180% 破防斩击，消耗 3 怒气。怒气≥8 时伤害＋50%",
                "name": "裂地斩",
            },
    "sk_zhan_hou": {
                "lv": 3,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "atk_up",
                "cd": 3,
                "res_gain": 3,
                "team": "atk_all",
                "desc": "战吼！攻＋25% 2 回合，怒气＋3。组队时全队攻＋10%(团队技能)",
                "name": "战吼",
            },
    "sk_tie_bi": {
                "lv": 6,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "res_gain": 2,
                "desc": "铁壁！防＋40% 2 回合，怒气＋2",
                "name": "铁壁",
            },
    "sk_xu_shi": {
                "lv": 11,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "atk_up",
                "cd": 2,
                "res_gain": 4,
                "desc": "蓄势！下回合攻击＋50%，怒气＋4(终结技前奏)",
                "name": "蓄势",
            },
    "sk_dun_ji": {
                "lv": 17,
                "mp": 0,
                "power": 1.3,
                "kind": "物理",
                "cd": 3,
                "cc": "stun",
                "mech": "stun",
                "mech_val": 1,
                "desc": "盾击！130% 伤害 + 眩晕 1 回合(强控·单体，CD 3)",
                "name": "盾击",
            },
    "sk_zhan_zheng_jian_ta": {
                "lv": 24,
                "mp": 0,
                "power": 0.8,
                "kind": "物理",
                "res_gain": 2,
                "cond": {"type": "enemy_frozen", "mult": 1.4, "label": "震地压制"},
                "desc": "战争践踏！80% 全体伤害(对单体等效)，怒气＋2。目标被冻结/减速时＋40%",
                "name": "战争践踏",
            },
    "sk_wu_wei_chong_ji": {
                "lv": 30,
                "mp": 0,
                "power": 2.5,
                "kind": "物理",
                "res_cost": {"rage": 10},
                "pierce": True,
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "背水一战"},
                "desc": "无畏冲击！消耗全部怒气，每点怒气＋15% 伤害(满怒 = 250%)。自身 HP<30% 时＋50%(决死反扑)",
                "name": "无畏冲击",
            },
    "sk_p_zhan_yi": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "atk", "cond": "rage>=5", "mult": 0.15},
                "desc": "属性被动：怒气≥5时攻击＋15%",
                "name": "战意高涨",
            },
    "sk_p_tie_bi_zhi_xin": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05},
                "desc": "触发被动：受到伤害时减伤5%",
                "name": "铁壁之心",
            },
    "sk_p_po_jia_ben_neng": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "pierce", "mult": 1.1},
                "desc": "触发被动：破防类技能伤害＋10%",
                "name": "破甲本能",
            },
    "sk_p_zhan_zheng_pa_xiao": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "atk", "cond": "battle_start", "mult": 0.08},
                "desc": "属性被动：战斗开始时攻击＋8%",
                "name": "战争咆哮",
            },
        },
    },
    "cls_fa_shi": {
        "name": "法师",
        "skills": {
    "sk_huo_qiu_shu": {
                "lv": 1,
                "mp": 10,
                "power": 1.0,
                "kind": "魔法",
                "element": "fire",
                "desc": "火球术！火系 100% 伤害，挂 1 层火印。已有火印时＋20% 且层数＋1(燎原)",
                "name": "火球术",
            },
    "sk_bing_jing": {
                "lv": 2,
                "mp": 8,
                "power": 1.05,
                "kind": "魔法",
                "element": "ice",
                "desc": "凝结冰晶掷向敌人，冰系 105% 魔法伤害。元素流转的前奏。",
                "name": "冰晶术",
            },
    "sk_bing_zhui": {
                "lv": 8,
                "mp": 15,
                "power": 1.1,
                "kind": "魔法",
                "element": "ice",
                "mech": "spd_down",
                "mech_val": 1,
                "cond": {"type": "enemy_frozen", "mult": 1.3, "label": "寒霜蔓延"},
                "desc": "冰锥！冰系 110% 伤害，挂冰印 + 减速 1 回合。目标被冻结时＋30%",
                "name": "冰锥",
            },
    "sk_lei_ji": {
                "lv": 14,
                "mp": 20,
                "power": 1.2,
                "kind": "魔法",
                "element": "thunder",
                "cond": {"type": "player_first", "mult": 1.15, "label": "雷系爆发"},
                "desc": "雷击！雷系 120% 伤害，挂雷印。先手时＋15%",
                "name": "雷击",
            },
    "sk_yuan_su_bao_fa": {
                "lv": 20,
                "mp": 30,
                "power": 1.6,
                "kind": "魔法",
                "element": "thunder",
                "desc": "元素爆发！当前系 160% 伤害 + 触发一次元素反应(蒸发/超载/冻结/感电)",
                "name": "元素爆发",
            },
    "sk_yuan_su_liu_zhuan": {
                "lv": 3,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 2,
                "team": "matk_all",
                "desc": "元素流转！切换任意系，下个技能＋20%(控场核心)",
                "name": "元素流转",
            },
    "sk_ao_shu_fei_dan": {
                "lv": 6,
                "mp": 12,
                "power": 1.0,
                "kind": "魔法",
                "multi": 2,
                "desc": "奥术飞弹！100%×2，当前系增伤(低耗填充)",
                "name": "奥术飞弹",
            },
    "sk_yuan_su_hu_dun": {
                "lv": 11,
                "mp": 20,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "desc": "元素护盾！防＋40% 2 回合，按当前系减伤(CD 3)",
                "name": "元素护盾",
            },
    "sk_ao_shu_qiang_hua": {
                "lv": 17,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "desc": "奥术强化！matk＋50% 2 回合(爆发前奏)",
                "name": "奥术强化",
            },
    "sk_bing_shuang_xin_xing": {
                "lv": 24,
                "mp": 35,
                "power": 0.8,
                "kind": "魔法",
                "cd": 3,
                "element": "ice",
                "mech": "freeze",
                "mech_val": 1,
                "desc": "冰霜新星！80% 全体伤害(对单体等效)＋30% 概率冻结 1 回合(强控·群体，CD 3)",
                "name": "冰霜新星",
            },
    "sk_yuan_su_feng_bao": {
                "lv": 30,
                "mp": 60,
                "power": 2.0,
                "kind": "魔法",
                "element": "thunder",
                "cond": {"type": "player_res_stacks", "res_key": "element", "stacks": 1, "mult": 1.5, "label": "元素过载"},
                "desc": "元素风暴！当前系 200% 全体伤害(对单体等效)。目标有印记时＋50%(元素过载)",
                "name": "元素风暴",
            },
    "sk_p_lie_yan_qin_he": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "fire", "mult": 0.1},
                "desc": "属性被动：火系技能伤害＋10%",
                "name": "烈焰亲和",
            },
    "sk_p_han_shuang_qin_he": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "ice_slow"},
                "desc": "触发被动：冰系技能附带减速",
                "name": "寒霜亲和",
            },
    "sk_p_mo_li_yong_dong": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "mp", "mult": 0.15},
                "desc": "属性被动：最大魔力＋15%",
                "name": "魔力涌动",
            },
    "sk_p_yuan_su_gong_ming": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "reaction", "mult": 1.15},
                "desc": "触发被动：元素反应伤害＋15%",
                "name": "元素共鸣",
            },
        },
    },
    "cls_you_xia": {
        "name": "游侠",
        "skills": {
    "sk_ji_feng_lian_she": {
                "lv": 1,
                "mp": 0,
                "power": 0.6,
                "kind": "物理",
                "multi": 2,
                "res_cost": {"energy": 20},
                "desc": "疾风连射！连续射击 2 次，每次 60% 物理伤害，消耗 20 精力",
                "name": "疾风连射",
            },
    "sk_miao_zhun": {
                "lv": 2,
                "mp": 0,
                "energy": 10,
                "power": 1.4,
                "kind": "物理",
                "desc": "屏息瞄准，140% 物理伤害，消耗 10 精力。",
                "name": "瞄准射击",
            },
    "sk_zhi_ming_ju_ji": {
                "lv": 8,
                "mp": 0,
                "power": 1.8,
                "kind": "物理",
                "res_cost": {"energy": 35},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.4, "mult": 1.5, "label": "绝境之眼"},
                "desc": "致命狙击！180% 单体伤害，消耗 35 精力。目标 HP<40% 时＋50%(处决狙击)",
                "name": "致命狙击",
            },
    "sk_lie_wang_xian_jing": {
                "lv": 14,
                "mp": 0,
                "power": 1.2,
                "kind": "物理",
                "res_cost": {"energy": 30},
                "mech": "burn",
                "mech_val": 2,
                "desc": "猎网陷阱！120% 伤害＋2 层灼烧，消耗 30 精力(延时引爆)",
                "name": "猎网陷阱",
            },
    "sk_huan_shou_qi_yue": {
                "lv": 20,
                "mp": 0,
                "power": 1.5,
                "kind": "物理",
                "res_cost": {"energy": 40},
                "mech": "mark",
                "mech_val": 1,
                "desc": "唤兽契约！150% 暗影伤害 + 猎杀标记，消耗 40 精力(双生协战)",
                "name": "唤兽契约",
            },
    "sk_ying_yan_suo_ding": {
                "lv": 3,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "crit_up",
                "cd": 2,
                "res_cost": {"energy": 15},
                "desc": "鹰眼锁定！暴击率＋20% 2 回合，消耗 15 精力",
                "name": "鹰眼锁定",
            },
    "sk_feng_zhi_ji_zou": {
                "lv": 6,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "spd_up",
                "cd": 2,
                "res_cost": {"energy": 20},
                "desc": "风之疾走！速度＋40% 2 回合，消耗 20 精力(机动)",
                "name": "风之疾走",
            },
    "sk_cui_du_jian_shi": {
                "lv": 11,
                "mp": 0,
                "power": 0.8,
                "kind": "物理",
                "res_cost": {"energy": 25},
                "mech": "poison",
                "mech_val": 3,
                "desc": "淬毒箭矢！80% 伤害＋3 层中毒，消耗 25 精力(毒体系铺垫)",
                "name": "淬毒箭矢",
            },
    "sk_wei_zhuang_wei_mu": {
                "lv": 17,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "dodge_up",
                "cd": 3,
                "res_cost": {"energy": 30},
                "desc": "伪装帷幕！闪避率＋40% 2 回合，消耗 30 精力(隐形求生)",
                "name": "伪装帷幕",
            },
    "sk_shou_lie_pao_xiao": {
                "lv": 24,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "atk_up",
                "cd": 3,
                "res_cost": {"energy": 40},
                "team": "atk_all",
                "desc": "狩猎咆哮！攻＋25% 3 回合，消耗 40 精力(标记爆发前奏)",
                "name": "狩猎咆哮",
            },
    "sk_shou_lie_zhong_zhang": {
                "lv": 30,
                "mp": 0,
                "power": 2.0,
                "kind": "物理",
                "res_cost": {"energy": 100},
                "mech": "mark_burst",
                "cond": {"type": "enemy_poison_stacks", "stacks": 3, "mult": 1.5, "label": "狩猎盛宴"},
                "desc": "狩猎终章！200% 致命一击，消耗全部精力。目标中毒 ≥3 层时＋50%(狩猎盛宴)",
                "name": "狩猎终章",
            },
    "sk_p_lie_shou_ben_neng": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "crit_mark", "mult": 0.1},
                "desc": "属性被动：对标记目标暴击＋10%",
                "name": "猎手本能",
            },
    "sk_p_feng_xing_bu": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "spd", "mult": 0.08},
                "desc": "属性被动：速度＋8%",
                "name": "风行步",
            },
    "sk_p_ying_yan": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "crit", "mult": 0.03},
                "desc": "属性被动：暴击率＋3%",
                "name": "鹰眼",
            },
    "sk_p_zhui_zong_yin_ji": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "mark_extra", "chance": 0.3},
                "desc": "触发被动：攻击时30%概率额外叠1印记",
                "name": "追踪印记",
            },
        },
    },
    "cls_mu_shi": {
        "name": "牧师",
        "skills": {
    "sk_sheng_guang_dan": {
                "lv": 1,
                "mp": 8,
                "power": 1.0,
                "kind": "魔法",
                "res_gain": 1,
                "cond": {"type": "player_hp_high", "hp_pct": 0.7, "mult": 1.2, "label": "光之祝福"},
                "desc": "圣光弹！100% 圣光伤害，信仰＋1。自身 HP>70% 时＋20%",
                "name": "圣光弹",
            },
    "sk_sheng_guang": {
                "lv": 2,
                "mp": 8,
                "power": 1.15,
                "kind": "魔法",
                "res_gain": 1,
                "desc": "圣光凝聚成束，115% 圣光伤害，信仰＋1。",
                "name": "圣光术",
            },
    "sk_zhi_yu_shu": {
                "lv": 8,
                "mp": 15,
                "power": 2.0,
                "kind": "治疗",
                "res_gain": 2,
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "治愈之光"},
                "desc": "治愈术！治疗 200%，信仰＋2。自身 HP<30% 时治疗量＋50%(紧急救治)",
                "name": "治愈术",
            },
    "sk_cheng_jie": {
        # v95.7 #40：惩戒 14→10 级并改为耗信仰技（2 信仰），牧师 Lv.10 起信仰有消耗出口
        "lv": 10,
        "mp": 20,
        "power": 1.2,
        "kind": "魔法",
        "res_cost": {"faith": 2},
        "cond": {"type": "enemy_poison_stacks", "stacks": 1, "mult": 1.3, "label": "审判之光"},
        "desc": "惩戒！120% 圣光伤害，消耗 2 信仰。目标有减益时＋30%(审判罪者)",
        "name": "惩戒",
    },
    "sk_sheng_guang_cheng_ji": {
                "lv": 20,
                "mp": 30,
                "power": 2.0,
                "kind": "魔法",
                "res_cost": {"faith": 3},
                "mech": "cleanse",
                "mech_val": 1,
                "cond": {"type": "player_res_stacks", "res_key": "faith", "stacks": 8, "mult": 1.4, "label": "信仰坚定"},
                "desc": "圣光惩击！200% 伤害 + 驱散敌方增益，消耗 3 信仰。信仰≥8 时＋40%",
                "name": "圣光惩击",
            },
    "sk_sheng_guang_hu_dun": {
                "lv": 3,
                "mp": 12,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "res_gain": 1,
                "desc": "圣光护盾！防＋40% 2 回合，信仰＋1(保命)",
                "name": "圣光护盾",
            },
    "sk_qun_ti_zhi_yu": {
                "lv": 6,
                "mp": 20,
                "power": 1.5,
                "kind": "治疗",
                "cd": 2,
                "res_gain": 3,
                "team": "heal_all",
                "desc": "群体治愈！全队治疗 150%，信仰＋3(群奶核心，团队技能)",
                "name": "群体治愈",
            },
    "sk_xin_yang_qi_dao": {
                "lv": 11,
                "mp": 15,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "res_gain": 2,
                "desc": "信仰祈祷！matk＋30% 2 回合，信仰＋2(增幅)",
                "name": "信仰祈祷",
            },
    "sk_shen_sheng_dao_yan": {
                "lv": 17,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "desc": "神圣祷言！matk＋50% 2 回合(战斗牧师爆发前奏)",
                "name": "神圣祷言",
            },
    "sk_sheng_guang_qu_san": {
                "lv": 24,
                "mp": 35,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "desc": "圣光驱散！驱散全队全部负面状态(驱散核心，团队技能)",
                "name": "圣光驱散",
            },
    "sk_shen_en_jiang_lin": {
                "lv": 30,
                "mp": 50,
                "power": 1.8,
                "kind": "治疗",
                "res_cost": {"faith": 10},
                "team": "heal_all",
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "自我牺牲"},
                "desc": "神恩降临！全队治疗 180%，消耗全部信仰。自身 HP<30% 时治疗量＋50%(牧师殉道)",
                "name": "神恩降临",
            },
    "sk_p_bi_hu_zhi_guang": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "heal_shield", "pct": 0.2},
                "desc": "触发被动：治疗溢出20%转为护盾",
                "name": "庇护之光",
            },
    "sk_p_shen_sheng_jian_ren": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken_heal", "chance": 0.2, "pct": 0.05},
                "desc": "触发被动：受击后20%概率回复5%生命",
                "name": "神圣坚韧",
            },
    "sk_p_xin_yang_jian_ding": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "mp", "mult": 0.15},
                "desc": "属性被动：最大魔力＋15%",
                "name": "信仰坚定",
            },
    "sk_p_shen_en": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "heal", "mult": 1.1},
                "desc": "触发被动：治疗技能效果＋10%",
                "name": "神恩",
            },
        },
    },
    "cls_ci_ke": {
        "name": "刺客",
        "skills": {
    "sk_ci_ji": {
                "lv": 1,
                "mp": 0,
                "power": 1.0,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.2, "label": "先手偷袭"},
                "desc": "刺击！100% 单体伤害，连击点＋1。先手时＋20%",
                "name": "刺击",
            },
    "sk_ge_lie": {
                "lv": 2,
                "mp": 0,
                "power": 1.15,
                "kind": "物理",
                "res_gain": 1,
                "desc": "利刃撕裂，115% 物理伤害，连击点＋1。",
                "name": "割裂",
            },
    "sk_shuang_ren_luan_wu": {
                "lv": 8,
                "mp": 0,
                "power": 0.9,
                "kind": "物理",
                "multi": 2,
                "res_gain": 2,
                "cond": {"type": "enemy_hp_high", "hp_pct": 0.7, "mult": 1.3, "label": "背刺角度"},
                "desc": "双刃乱舞！90%×2，连击点＋2。目标 HP>70% 时＋30%(满血背刺)",
                "name": "双刃乱舞",
            },
    "sk_cui_du": {
                "lv": 14,
                "mp": 0,
                "power": 1.0,
                "kind": "物理",
                "mech": "poison",
                "mech_val": 2,
                "res_gain": 1,
                "desc": "淬毒！100% 伤害＋2 层中毒(毒体系核心)",
                "name": "淬毒",
            },
    "sk_an_sha": {
                "lv": 20,
                "mp": 0,
                "power": 2.4,
                "kind": "物理",
                "res_cost": {"cp": 3},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.4, "mult": 1.4, "label": "残血收割"},
                "desc": "暗杀！240% 单体伤害，消耗 3 连击点。目标 HP<40% 时＋40%(斩杀线)",
                "name": "暗杀",
            },
    "sk_qian_xing": {
                "lv": 3,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "crit_up",
                "cd": 3,
                "res_gain": 1,
                "desc": "潜行！暴击率＋30% 2 回合(下回合必暴)，连击点＋1(爆发核心)",
                "name": "潜行",
            },
    "sk_ji_ying": {
                "lv": 6,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "spd_up",
                "cd": 2,
                "desc": "疾影！速度＋40% 2 回合(机动)",
                "name": "疾影",
            },
    "sk_ying_xi": {
                "lv": 11,
                "mp": 0,
                "power": 1.2,
                "kind": "物理",
                "res_gain": 1,
                "mech": "shadow",
                "mech_val": 1,
                "desc": "影袭！120% 伤害 + 影袭层数，连击点＋1(潜行联动)",
                "name": "影袭",
            },
    "sk_si_wang_biao_ji": {
                "lv": 17,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "mark",
                "cd": 2,
                "res_gain": 1,
                "team": "crit_all",
                "desc": "死亡标记！目标易伤(受击＋30%)，连击点＋1(铺垫)",
                "name": "死亡标记",
            },
    "sk_du_wu": {
                "lv": 24,
                "mp": 0,
                "power": 0.8,
                "kind": "物理",
                "cd": 3,
                "mech": "poison",
                "mech_val": 2,
                "desc": "毒雾！80% 全体伤害(对单体等效)＋2 层中毒(毒刃流铺场)",
                "name": "毒雾",
            },
    "sk_an_ying_chu_xing": {
                "lv": 30,
                "mp": 0,
                "power": 3.0,
                "kind": "物理",
                "res_cost": {"cp": 5},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "死亡边缘"},
                "desc": "暗影处刑！300% 致命一击，消耗全部连击点。目标 HP<30% 时＋50%(一击必杀)",
                "name": "暗影处刑",
            },
    "sk_p_an_ying_zhi_wu": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "stealth_crit_dmg", "mult": 0.3},
                "desc": "属性被动：潜行状态暴击伤害＋30%",
                "name": "暗影之舞",
            },
    "sk_p_ji_ying": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "spd", "mult": 0.08},
                "desc": "属性被动：速度＋8%(疾影术)",
                "name": "疾影术",
            },
    "sk_p_ju_du_qin_he": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "poison", "mult": 1.2},
                "desc": "触发被动：毒层每层伤害＋20%",
                "name": "剧毒亲和",
            },
    "sk_p_zhi_ming_yu_mou": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "battle_start_cp"},
                "desc": "触发被动：战斗开始获得1连击点",
                "name": "致命预谋",
            },
        },
    },
    "cls_wu_seng": {
        "name": "拳师",
        "skills": {
    "sk_zhi_quan": {
                "lv": 1,
                "mp": 0,
                "power": 1.0,
                "kind": "物理",
                "combo": "拳",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.15, "label": "起手式"},
                "desc": "直拳！100% 单体伤害，气＋1，连招【拳】。先手时＋15%",
                "name": "直拳",
            },
    "sk_chong_quan": {
                "lv": 2,
                "mp": 0,
                "power": 1.1,
                "kind": "物理",
                "res_gain": 1,
                "combo": "拳",
                "desc": "沉肩冲拳，110% 物理伤害，气＋1，连招【拳】。",
                "name": "冲拳",
            },
    "sk_beng_quan": {
        # v95.7 #39：崩拳 8→4 级并改为耗气技（3 气），解决武僧 Lv.2-7 气满无出口的空转
        "lv": 4,
        "mp": 0,
        "power": 1.4,
        "kind": "物理",
        "combo": "拳",
        "pierce": True,
        "res_cost": {"chi": 3},
        "cond": {"type": "enemy_hp_high", "hp_pct": 0.7, "mult": 1.3, "label": "崩山之势"},
        "desc": "崩拳！140% 破防伤害，消耗 3 气，连招【拳】。目标 HP>70% 时＋30%",
        "name": "崩拳",
    },
    "sk_hui_xuan_ti": {
                "lv": 14,
                "mp": 0,
                "power": 1.2,
                "kind": "物理",
                "combo": "踢",
                "res_gain": 1,
                "cond": {"type": "enemy_frozen", "mult": 1.3, "label": "立足不稳"},
                "desc": "回旋踢！120% 全体伤害(对单体等效)，气＋1，连招【踢】。目标减速/冻结时＋30%",
                "name": "回旋踢",
            },
    "sk_zhen_di_ji": {
                "lv": 20,
                "mp": 0,
                "power": 1.3,
                "kind": "物理",
                "combo": "踢",
                "res_gain": 1,
                "cc": "stun",
                "mech": "stun",
                "mech_val": 1,
                "desc": "震地击！130% 全体伤害(对单体等效)＋30% 概率眩晕，气＋1，连招【踢】",
                "name": "震地击",
            },
    "sk_ce_ti": {
                "lv": 3,
                "mp": 0,
                "power": 1.1,
                "kind": "物理",
                "combo": "踢",
                "res_gain": 1,
                "desc": "侧踢！110% 伤害，气＋1，连招【踢】(连招第二段)",
                "name": "侧踢",
            },
    "sk_tie_zhang": {
                "lv": 6,
                "mp": 0,
                "power": 1.2,
                "kind": "物理",
                "combo": "掌",
                "res_gain": 1,
                "desc": "铁掌！120% 伤害，气＋1，连招【掌】(三连准备)",
                "name": "铁掌",
            },
    "sk_qi_xi_tiao_xi": {
                "lv": 11,
                "mp": 0,
                "power": 0,
                "kind": "治疗",
                "cd": 3,
                "res_gain": 2,
                "desc": "气息调息！回复 15% HP，气＋2(续航)",
                "name": "气息调息",
            },
    "sk_tie_bi": {
                "lv": 17,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "res_gain": 2,
                "team": "def_all",
                "desc": "铁壁！防＋40% 2 回合，气＋2(磐石流铺垫)",
                "name": "铁壁",
            },
    "sk_lian_zhao_san_lian": {
                "lv": 24,
                "mp": 0,
                "power": 1.5,
                "kind": "物理",
                "combo": "拳",
                "multi": 3,
                "res_gain": 3,
                "desc": "连招·三连！150%×3，气＋3(连招核心，三连完成时斗气技＋30%)",
                "name": "连招三连",
            },
    "sk_po_xiao_zhi_quan": {
                "lv": 30,
                "mp": 0,
                "power": 3.0,
                "kind": "物理",
                "res_cost": {"chi": 10},
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "磐石之心"},
                "desc": "破晓之拳！300% 致命一击，消耗全部气。自身 HP<30% 时先回复 20% 生命再发动(残血反杀)",
                "name": "破晓之拳",
            },
    "sk_p_lian_zhao_jing_tong": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "combo_boost"},
                "desc": "触发被动：连招(拳踢掌)触发率提升",
                "name": "连招精通",
            },
    "sk_p_pan_shi_ti": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05, "chi": 1},
                "desc": "触发被动：受击减伤5%，受击时气＋1",
                "name": "磐石体",
            },
    "sk_p_qi_xi_tiao_he": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "turn_heal", "pct": 0.02},
                "desc": "触发被动：每回合回复2%生命",
                "name": "气息调和",
            },
    "sk_p_dou_qi_ning_ju": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "chi_gain", "mult": 1},
                "desc": "属性被动：气获取＋1",
                "name": "斗气凝聚",
            },
        },
    },
    # ================= v87 隐藏职业：魔剑士（09 章九.2，Lv.60 解锁）=================
    "cls_spellblade": {
        "name": "魔剑士",
        "skills": {
    "sk_mo_neng_zhan": {
                "lv": 60,
                "mp": 20,
                "power": 1.3,
                "kind": "物理",
                "magic_add": 0.3,
                "mech": "spellblade",
                "mech_val": 1,
                "desc": "魔能斩！130% 物理＋30% 魔法混合伤害，命中叠 1 层魔能",
                "name": "魔能斩",
            },
    "sk_fu_wen_hu_ti": {
                "lv": 64,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "atk_up",
                "cd": 3,
                "cond": {"type": "player_mech_stacks", "mech": "spellblade", "stacks": 3, "mult": 1.0, "label": "魔能护体"},
                "desc": "符文护体！魔能≥3 时：全属性＋10% 3 回合(魔能不足则无加成)",
                "name": "符文护体",
            },
    "sk_mo_li_yong_dong": {
                "lv": 68,
                "mp": 20,
                "power": 1.0,
                "kind": "物理",
                "mech": "spellblade_surge",
                "mech_val": 0,
                "desc": "魔能涌动！消耗 2 层魔能，下次攻击额外＋80% 魔法伤害",
                "name": "魔能涌动",
            },
    "sk_jian_ren_feng_bao": {
                "lv": 72,
                "mp": 35,
                "power": 1.2,
                "kind": "物理",
                "magic_add": 0.4,
                "mech": "spellblade_storm",
                "mech_val": 0,
                "desc": "剑刃风暴！消耗 3 层魔能：全体 120% 物理＋40% 魔法",
                "name": "剑刃风暴",
            },
    "sk_mo_neng_bao_fa": {
                "lv": 76,
                "mp": 40,
                "power": 2.0,
                "kind": "物理",
                "mech": "spellblade_burst",
                "mech_val": 0,
                "desc": "魔能爆发！消耗全部魔能(≥4)：每层＋25% 伤害，最高 200%",
                "name": "魔能爆发",
            },
    "sk_fu_wen_ke_yin": {
                "lv": 80,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "spellblade_regen", "mult": 1},
                "desc": "被动：符文刻印，每回合自动获得 1 层魔能(上限 5 层)",
                "name": "符文刻印",
            },
    "sk_shuang_xiu_jing_tong": {
                "lv": 85,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "atk", "cond": "dual_stat", "mult": 0.05},
                "desc": "被动：双修精通，力量/智力同时增加时额外＋5% 攻击",
                "name": "双修精通",
            },
    "sk_xing_yun_zhan": {
                "lv": 90,
                "mp": 60,
                "power": 4.0,
                "kind": "物理",
                "magic_add": 0.4,
                "mech": "spellblade_meteor",
                "mech_val": 0,
                "desc": "奥义·星陨斩！消耗 5 层魔能：400% 混合伤害＋20% 概率眩晕",
                "name": "星陨斩",
            },
        }
    },
}

BRANCH_SKILLS = {
    "cls_zhan_shi": {
        "name": "战士",
        "branches": {
            1: {
                "狂战士": {
                    "怒斩":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.4,
                        "kind": "物理",
                        "res_gain": 2,
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.5,
                            "mult": 1.25,
                            "label": "狂战血统"
                        },
                        "desc": "140% 斩击，怒气＋2。自身 HP<50% 时伤害＋25%(残血狂战)",
                        "name": "怒斩"
                    }
,
                    "死战":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "atk",
                            "cond": "hp_low_50",
                            "mult": 0.1
                        },
                        "desc": "属性被动：生命低于 50% 时攻击＋10%",
                        "name": "死战"
                    }
,
                    "嗜血斩":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.6,
                        "kind": "物理",
                        "lifesteal": 0.25,
                        "res_gain": 2,
                        "cond": {
                            "type": "enemy_debuff",
                            "mult": 1.2,
                            "label": "猎物标记"
                        },
                        "desc": "160% 吸血斩击(吸血 25%)，怒气＋2。目标有减益时伤害＋20%",
                        "name": "嗜血斩"
                    }
,
                    "狂怒爆发":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 2.4,
                        "kind": "物理",
                        "res_cost": {
                            "rage": 5
                        },
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.3,
                            "mult": 1.4,
                            "label": "绝境狂怒"
                        },
                        "desc": "终结技，240% 斩击，消耗 5 怒气。自身 HP<30% 时伤害＋40%(背水一战)",
                        "name": "狂怒爆发"
                    }
,
                },
                "盾卫士": {
                    "盾击":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.3,
                        "kind": "物理",
                        "mech": "stun",
                        "mech_val": 1,
                        "cond": {
                            "type": "enemy_stunned",
                            "mult": 1.5,
                            "label": "盾击连打"
                        },
                        "desc": "130% 盾击，概率眩晕 1 回合。目标被眩晕时追加 50% 伤害(控制链)",
                        "name": "盾击"
                    }
,
                    "守护姿态":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "dmg_taken",
                            "reduce": 0.1,
                            "res_gain": 2
                        },
                        "desc": "触发被动：受击伤害－10%，受击怒气＋2(坦克攒怒)",
                        "name": "守护姿态"
                    }
,
                    "圣光壁垒":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "team": "def_all",
                        "res_gain": 3,
                        "desc": "全队防御强化(组队时广播)，怒气＋3。坦克核心",
                        "name": "圣光壁垒"
                    }
,
                    "嘲讽":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 0,
                        "kind": "嘲讽",
                        "cd": 3,
                        "team": "taunt",
                        "res_gain": 4,
                        "desc": "嘲讽，CD3，强制怪物攻击自己 2 回合，怒气＋4(拉怪核心)",
                        "name": "嘲讽"
                    }
,
                },
            },
            2: {
                "狂战统领": {
                    "狂战之魂":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "res_gain_bonus": 1
                        },
                        "desc": "二转被动：怒气获取＋1(攒怒更快)",
                        "name": "狂战之魂"
                    }
,
                    "乱舞":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 1.2,
                        "kind": "物理",
                        "multi": 3,
                        "res_gain": 3,
                        "desc": "120%×3 快速连斩，怒气＋3(输出循环填充)",
                        "name": "乱舞"
                    }
,
                    "处决":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 3.0,
                        "kind": "物理",
                        "res_cost": {
                            "rage": 4
                        },
                        "cond": {
                            "type": "enemy_hp_low",
                            "hp_pct": 0.35,
                            "mult": 1.5,
                            "label": "残血终结"
                        },
                        "desc": "终结技，300% 斩杀，消耗 4 怒气。目标 HP<35% 时伤害＋50%",
                        "name": "处决"
                    }
,
                },
                "圣殿骑士": {
                    "圣盾":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "block",
                            "mult": 0.1
                        },
                        "desc": "二转被动：格挡率＋10%(减伤强化)",
                        "name": "圣盾"
                    }
,
                    "复仇":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "counter",
                            "mult": 1.3
                        },
                        "desc": "触发被动：受击后下次攻击＋30%(挨打反打)",
                        "name": "复仇"
                    }
,
                    "破城锤":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.2,
                        "kind": "物理",
                        "pierce": True,
                        "res_cost": {
                            "rage": 3
                        },
                        "cond": {
                            "type": "enemy_hp_high",
                            "hp_pct": 0.7,
                            "mult": 1.5,
                            "label": "重装压制"
                        },
                        "desc": "220% 破防重锤，消耗 3 怒气。目标 HP>70% 时伤害＋50%(压制满血)",
                        "name": "破城锤"
                    }
,
                },
            },
            3: {
                "战争领主": {
                    "怒涛连斩":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.8,
                        "kind": "物理",
                        "multi": 3,
                        "res_cost": {
                            "rage": 5
                        },
                        "cond": {
                            "type": "player_res_stacks",
                            "res_key": "rage",
                            "stacks": 9,
                            "mult": 1.3,
                            "label": "战意通天"
                        },
                        "desc": "180%×3 全体连斩，消耗 5 怒气。怒气≥9 时伤害＋30%",
                        "name": "怒涛连斩"
                    }
,
                    "战争化身":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 5.0,
                        "kind": "物理",
                        "res_cost": {
                            "rage": 10
                        },
                        "cd": 5,
                        "desc": "终极技，500% 毁灭斩击，消耗全部 10 怒气(狂战巅峰)",
                        "name": "战争化身"
                    }
,
                    "战争领域":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "atk_up_strong",
                        "res_cost": {
                            "rage": 10
                        },
                        "cd": 6,
                        "desc": "三转奥义，消耗 10 怒气，3 回合内攻击大幅提升(战争领域)",
                        "name": "战争领域"
                    }
,
                },
                "圣辉骑士": {
                    "守护誓言":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_all",
                        "team": "def_all",
                        "res_cost": {
                            "rage": 4
                        },
                        "desc": "替全队承受伤害的誓言，全队防御强化，消耗 4 怒气(团队保护)",
                        "name": "守护誓言"
                    }
,
                    "不破壁垒":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "team": "reduce_all",
                        "res_cost": {
                            "rage": 5
                        },
                        "cd": 5,
                        "desc": "终极技，全队减伤 25% 3 回合，消耗 5 怒气(团队终极防御)",
                        "name": "不破壁垒"
                    }
,
                    "守护圣域":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "team": "reduce_all",
                        "res_cost": {
                            "rage": 5
                        },
                        "cd": 6,
                        "desc": "三转奥义，消耗 5 怒气，全队无敌屏障(守护圣域)",
                        "name": "守护圣域"
                    }
,
                },
            },
        },
    },
    "cls_fa_shi": {
        "name": "法师",
        "branches": {
            1: {
                "元素法师": {
                    "元素冲击":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.4,
                        "kind": "魔法",
                        "element": "current",
                        "cond": {
                            "type": "element_marks",
                            "element": "any",
                            "stacks": 1,
                            "mult": 1.2,
                            "label": "万象共鸣"
                        },
                        "desc": "当前系 140% 单体，挂元素印记。目标已有印记时伤害＋20%(反应前奏)",
                        "name": "元素冲击"
                    }
,
                    "万象亲和":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "element_dmg",
                            "mult": 0.08
                        },
                        "desc": "触发被动：施放元素技能时伤害＋8%(三系强化)",
                        "name": "万象亲和"
                    }
,
                    "双系连珠":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.3,
                        "kind": "魔法",
                        "multi": 2,
                        "element": "current",
                        "cond": {
                            "type": "element_marks",
                            "element": "any",
                            "stacks": 3,
                            "mult": 1.25,
                            "label": "连环引爆"
                        },
                        "desc": "当前系 130%×2，挂 2 层印记。目标印记≥3 层时伤害＋25%(叠印引爆)",
                        "name": "双系连珠"
                    }
,
                    "元素引爆":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 2.4,
                        "kind": "魔法",
                        "element": "current",
                        "cond": {
                            "type": "element_marks",
                            "element": "any",
                            "stacks": 2,
                            "mult": 1.3,
                            "label": "元素共鸣"
                        },
                        "desc": "当前系 240%，引爆印记。目标印记≥2 层时伤害＋30%",
                        "name": "元素引爆"
                    }
,
                },
                "奥术法师": {
                    "奥术弹幕":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.1,
                        "kind": "魔法",
                        "multi": 3,
                        "mech": "arcane",
                        "mech_val": 1,
                        "cond": {
                            "type": "player_mech_stacks",
                            "mech": "arcane",
                            "stacks": 2,
                            "mult": 1.15,
                            "label": "蓄势待发"
                        },
                        "desc": "奥术 110%×3，奥术充能＋1。充能≥2 层时伤害＋15%(蓄能强化)",
                        "name": "奥术弹幕"
                    }
,
                    "奥术直觉":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "arcane_regen",
                            "mult": 1
                        },
                        "desc": "触发被动：每回合开始奥术充能＋1(自动蓄能)",
                        "name": "奥术直觉"
                    }
,
                    "奥术爆破":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.5,
                        "kind": "魔法",
                        "multi": 2,
                        "mech": "arcane",
                        "mech_val": 2,
                        "cond": {
                            "type": "player_mech_stacks",
                            "mech": "arcane",
                            "stacks": 4,
                            "mult": 1.25,
                            "label": "共鸣输出"
                        },
                        "desc": "奥术 150%×2，奥术充能＋2。充能≥4 层时伤害＋25%(共鸣输出)",
                        "name": "奥术爆破"
                    }
,
                    "奥术洪流":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 2.5,
                        "kind": "魔法",
                        "mech": "arcane_burst",
                        "cond": {
                            "type": "player_mech_stacks",
                            "mech": "arcane",
                            "stacks": 5,
                            "mult": 1.4,
                            "label": "共鸣巅峰"
                        },
                        "desc": "奥术 250%，消耗全部充能每层＋15%。充能≥5 层时伤害＋40%(爆发窗口)",
                        "name": "奥术洪流"
                    }
,
                },
            },
            2: {
                "元素术士": {
                    "元素之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "element_dmg",
                            "mult": 0.1
                        },
                        "desc": "二转被动：元素系技能伤害＋10%(元素强化)",
                        "name": "元素之心"
                    }
,
                    "元素跃迁":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "element_shift",
                        "cd": 3,
                        "desc": "切换当前元素系(火→冰→雷)，下次元素技能伤害＋20%(切系适应)",
                        "name": "元素跃迁"
                    }
,
                    "元素壁垒":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "cd": 3,
                        "desc": "防御强化(元素法师的护盾，不脆)",
                        "name": "元素壁垒"
                    }
,
                },
                "奥术术士": {
                    "奥术之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "arcane_dmg",
                            "mult": 0.1
                        },
                        "desc": "二转被动：奥术技能伤害＋10%(奥术强化)",
                        "name": "奥术之心"
                    }
,
                    "法术反制":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0.6,
                        "kind": "魔法",
                        "mech": "arcane",
                        "mech_val": 2,
                        "cc": "silence",
                        "cond": {
                            "type": "player_mech_stacks",
                            "mech": "arcane",
                            "stacks": 2,
                            "mult": 1.2,
                            "label": "反制强化"
                        },
                        "desc": "60% 反制，沉默敌人 + 奥术充能＋2。充能≥2 层时伤害＋20%(控制向)",
                        "name": "法术反制"
                    }
,
                    "法力护盾":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "cd": 3,
                        "desc": "防御强化(法力护盾，奥术法师不脆)",
                        "name": "法力护盾"
                    }
,
                },
            },
            3: {
                "元素贤者": {
                    "万象风暴":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.8,
                        "kind": "魔法",
                        "multi": 3,
                        "element": "current",
                        "cond": {
                            "type": "element_marks",
                            "element": "any",
                            "stacks": 1,
                            "mult": 1.3,
                            "label": "万象连环"
                        },
                        "desc": "当前系 180%×3 全体。目标有印记时伤害＋30%(万象清场)",
                        "name": "万象风暴"
                    }
,
                    "万象天雷":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 4.5,
                        "kind": "魔法",
                        "element": "thunder",
                        "team": "matk_all",
                        "cd": 5,
                        "desc": "终极技，雷系 450% 全体 + 全队魔攻强化(终极元素爆发)",
                        "name": "万象天雷"
                    }
,
                    "元素裁决":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 4.0,
                        "kind": "魔法",
                        "element": "current",
                        "cd": 6,
                        "desc": "三转奥义，当前系 400% 全体核弹(清场)",
                        "name": "元素裁决"
                    }
,
                },
                "奥秘贤者": {
                    "大奥术":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 2.0,
                        "kind": "魔法",
                        "multi": 2,
                        "mech": "arcane",
                        "mech_val": 2,
                        "cond": {
                            "type": "player_mech_stacks",
                            "mech": "arcane",
                            "stacks": 6,
                            "mult": 1.3,
                            "label": "大奥术回响"
                        },
                        "desc": "奥术 200%×2 全体，奥术充能＋2。充能≥6 层时伤害＋30%(群体共鸣)",
                        "name": "大奥术"
                    }
,
                    "奥术主宰":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 4.5,
                        "kind": "魔法",
                        "cond": {
                            "type": "player_mech_stacks",
                            "mech": "arcane",
                            "stacks": 5,
                            "mult": 1.5,
                            "label": "奥术主宰"
                        },
                        "cd": 5,
                        "desc": "终极技，奥术 450% 单体。充能≥5 层时伤害＋50%(终极奥术爆发)",
                        "name": "奥术主宰"
                    }
,
                    "奥术领域":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 4.0,
                        "kind": "魔法",
                        "team": "shield_all",
                        "cd": 6,
                        "desc": "三转奥义，奥术 400% 全体 + 全队护盾(终极领域)",
                        "name": "奥术领域"
                    }
,
                },
            },
        },
    },
    "cls_you_xia": {
        "name": "游侠",
        "branches": {
            1: {
                "猎魔人": {
                    "追猎":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.2,
                        "kind": "物理",
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.3,
                            "label": "猎杀本能"
                        },
                        "desc": "120% 狙击，目标被标记时伤害＋30%(标记特攻)",
                        "name": "追猎"
                    }
,
                    "追猎者":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "mark_dmg",
                            "mult": 0.08
                        },
                        "desc": "触发被动：对标记目标伤害＋8%(标记特攻)",
                        "name": "追猎者"
                    }
,
                    "三连射":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.1,
                        "kind": "物理",
                        "multi": 3,
                        "cond": {
                            "type": "player_res_stacks",
                            "res_key": "energy",
                            "stacks": 50,
                            "mult": 1.15,
                            "label": "猎手专注"
                        },
                        "desc": "110%×3 三连射。精力>50 时伤害＋15%(满精力精准)",
                        "name": "三连射"
                    }
,
                    "夺命一击":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 3.0,
                        "kind": "物理",
                        "cond": {
                            "type": "enemy_hp_low",
                            "hp_pct": 0.3,
                            "mult": 1.5,
                            "label": "绝杀"
                        },
                        "desc": "300% 夺命一击，目标 HP<30% 时伤害＋50%(处决残血)",
                        "name": "夺命一击"
                    }
,
                },
                "风行者": {
                    "疾风射击":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.2,
                        "kind": "物理",
                        "cond": {
                            "type": "speed_ratio",
                            "ratio": 1.5,
                            "mult": 1.5,
                            "label": "疾风连击"
                        },
                        "desc": "120% 疾风射击，速度比≥1.5x 时伤害＋50%(速度压制)",
                        "name": "疾风射击"
                    }
,
                    "疾驰":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "speed_dmg",
                            "mult": 0.08
                        },
                        "desc": "触发被动：速度高于目标时伤害＋8%(高速压制)",
                        "name": "疾驰"
                    }
,
                    "双重射击":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.1,
                        "kind": "物理",
                        "multi": 2,
                        "cond": {
                            "type": "player_untouched",
                            "mult": 1.15,
                            "label": "轻灵"
                        },
                        "desc": "110%×2 双重射击。自身未受击时伤害＋15%(无伤精准)",
                        "name": "双重射击"
                    }
,
                    "风刃乱舞":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 1.3,
                        "kind": "物理",
                        "multi": 3,
                        "pierce": True,
                        "cd": 3,
                        "cond": {
                            "type": "speed_ratio",
                            "ratio": 2.0,
                            "mult": 1.25,
                            "label": "疾风领域"
                        },
                        "desc": "130%×3 风刃(无视防御)，CD3。速度比≥2x 时伤害＋25%(极速压制)",
                        "name": "风刃乱舞"
                    }
,
                },
            },
            2: {
                "暗夜猎手": {
                    "猎魔之眼":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "mark_dmg",
                            "mult": 0.1
                        },
                        "desc": "二转被动：对标记目标伤害＋10%(标记强化)",
                        "name": "猎魔之眼"
                    }
,
                    "狩猎盛宴":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "crit_all",
                        "team": "crit_all",
                        "cd": 4,
                        "desc": "全队暴击强化 3 回合(团队技能)",
                        "name": "狩猎盛宴"
                    }
,
                    "穿心箭":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.8,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.3,
                            "label": "要害瞄准"
                        },
                        "desc": "280% 破防穿心箭，目标被标记时伤害＋30%",
                        "name": "穿心箭"
                    }
,
                },
                "疾风射手": {
                    "疾风之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "spd",
                            "mult": 0.08
                        },
                        "desc": "二转被动：速度＋8%(机动强化)",
                        "name": "疾风之心"
                    }
,
                    "急速射击":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0.9,
                        "kind": "物理",
                        "multi": 5,
                        "desc": "90%×5 急速射击(高速叠印)",
                        "name": "急速射击"
                    }
,
                    "穿云箭":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.2,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "player_buffed",
                            "mult": 1.2,
                            "label": "风速"
                        },
                        "desc": "220% 破防穿云箭。自身有增益时伤害＋20%(加速增伤)",
                        "name": "穿云箭"
                    }
,
                },
            },
            3: {
                "猎魔先驱": {
                    "致命连射":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.4,
                        "kind": "物理",
                        "multi": 4,
                        "desc": "140%×4 致命连射(叠印爆发)",
                        "name": "致命连射"
                    }
,
                    "死神之箭":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 4.5,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.5,
                            "label": "死神注视"
                        },
                        "desc": "终极技，450% 死神之箭，标记目标必暴击(终极斩杀)",
                        "name": "死神之箭"
                    }
,
                    "猎杀时刻":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 4.0,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.3,
                            "label": "猎杀时刻"
                        },
                        "cd": 6,
                        "desc": "三转奥义，400% 标记斩杀(单点核爆)",
                        "name": "猎杀时刻"
                    }
,
                },
                "疾风猎手": {
                    "风暴之舞":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.6,
                        "kind": "物理",
                        "multi": 4,
                        "cd": 4,
                        "desc": "160%×4 风暴之舞(终极连射)",
                        "name": "风暴之舞"
                    }
,
                    "疾风骤雨":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 2.0,
                        "kind": "物理",
                        "multi": 3,
                        "cd": 5,
                        "desc": "终极技，200%×3 疾风骤雨(冷却联动)",
                        "name": "疾风骤雨"
                    }
,
                    "风神降临":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "spd_up",
                        "cd": 6,
                        "desc": "三转奥义，速度大幅提升 3 回合(极速爆发)",
                        "name": "风神降临"
                    }
,
                },
            },
        },
    },
    "cls_mu_shi": {
        "name": "牧师",
        "branches": {
            1: {
                "圣武士": {
                    "圣光之刃":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.4,
                        "kind": "魔法",
                        "res_gain": 1,
                        "cond": {
                            "type": "player_hp_high",
                            "hp_pct": 0.7,
                            "mult": 1.15,
                            "label": "圣战之心"
                        },
                        "desc": "140% 圣光之刃，信仰＋1。自身 HP>70% 时伤害＋15%(满血战斗)",
                        "name": "圣光之刃"
                    }
,
                    "神圣狂热":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "attack_res",
                            "res": "faith",
                            "gain": 2
                        },
                        "desc": "触发被动：攻击时信仰＋2(战斗攒信)",
                        "name": "神圣狂热"
                    }
,
                    "圣光连斩":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.2,
                        "kind": "魔法",
                        "multi": 2,
                        "res_gain": 2,
                        "cond": {
                            "type": "player_buffed",
                            "mult": 1.15,
                            "label": "神圣狂热"
                        },
                        "desc": "120%×2 圣光连斩，信仰＋2。自身有增益时伤害＋15%",
                        "name": "圣光连斩"
                    }
,
                    "圣裁":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 2.6,
                        "kind": "魔法",
                        "res_cost": {
                            "faith": 4
                        },
                        "mech": "stun",
                        "mech_val": 1,
                        "cond": {
                            "type": "enemy_hp_low",
                            "hp_pct": 0.4,
                            "mult": 1.4,
                            "label": "审判日"
                        },
                        "desc": "260% 圣裁 + 概率眩晕，消耗 4 信仰。目标 HP<40% 时伤害＋40%(斩杀)",
                        "name": "圣裁"
                    }
,
                },
                "神谕者": {
                    "圣言术":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 2.5,
                        "kind": "治疗",
                        "res_gain": 2,
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.3,
                            "mult": 1.5,
                            "label": "圣言回响"
                        },
                        "desc": "治疗 250%，信仰＋2。自身 HP<30% 时治疗量＋50%(紧急救治)",
                        "name": "圣言术"
                    }
,
                    "圣祷":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "heal_crit",
                            "mult": 0.3,
                            "chance": 0.2
                        },
                        "desc": "触发被动：治疗时 20% 概率额外治疗 30%(治疗暴击)",
                        "name": "圣祷"
                    }
,
                    "净化术":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "cd": 2,
                        "desc": "驱散全队负面状态(防御强化)，CD2(驱散核心)",
                        "name": "净化术"
                    }
,
                    "大治愈术":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 3.0,
                        "kind": "治疗",
                        "res_cost": {
                            "faith": 3
                        },
                        "team": "heal_all",
                        "desc": "全队治疗 300%，消耗 3 信仰(团队核心)",
                        "name": "大治愈术"
                    }
,
                },
            },
            2: {
                "审判骑士": {
                    "审判之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "judge",
                            "mult": 0.1
                        },
                        "desc": "二转被动：圣光技能伤害＋10%(战斗牧师强化)",
                        "name": "审判之心"
                    }
,
                    "审判之剑":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 1.8,
                        "kind": "魔法",
                        "pierce": True,
                        "res_gain": 2,
                        "desc": "180% 破防审判之剑，信仰＋2",
                        "name": "审判之剑"
                    }
,
                    "圣光风暴":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.2,
                        "kind": "魔法",
                        "res_cost": {
                            "faith": 4
                        },
                        "cond": {
                            "type": "enemy_debuff",
                            "mult": 1.4,
                            "label": "圣光扩散"
                        },
                        "desc": "220% 圣光风暴，消耗 4 信仰。目标有减益时伤害＋40%(净化增伤)",
                        "name": "圣光风暴"
                    }
,
                },
                "大主教": {
                    "神圣恩典":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "heal",
                            "mult": 0.1
                        },
                        "desc": "二转被动：治疗效果＋10%(治疗强化)",
                        "name": "神圣恩典"
                    }
,
                    "生命之泉":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "team_regen",
                            "mult": 0.05
                        },
                        "desc": "触发被动：全队每回合回血 5%(团队续航)",
                        "name": "生命之泉"
                    }
,
                    "神圣庇护":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "shield_all",
                        "team": "shield_all",
                        "cd": 4,
                        "desc": "全队护盾，CD4(持续保护)",
                        "name": "神圣庇护"
                    }
,
                },
            },
            3: {
                "裁决骑士": {
                    "天使之怒":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 3.0,
                        "kind": "魔法",
                        "res_cost": {
                            "faith": 5
                        },
                        "desc": "300% 天使之怒，消耗 5 信仰(能打能奶)",
                        "name": "天使之怒"
                    }
,
                    "圣裁之光":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 4.5,
                        "kind": "魔法",
                        "res_cost": {
                            "faith": 10
                        },
                        "team": "shield_all",
                        "cd": 5,
                        "desc": "终极技，450% 圣裁之光，消耗 10 信仰 + 全队护盾(终极神迹)",
                        "name": "圣裁之光"
                    }
,
                    "圣光化身":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "atk_up_strong",
                        "cd": 6,
                        "desc": "三转奥义，3 回合内攻击附带圣光(每次攻击大幅增伤)",
                        "name": "圣光化身"
                    }
,
                },
                "圣光先知": {
                    "圣光赞歌":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 2.5,
                        "kind": "治疗",
                        "res_cost": {
                            "faith": 5
                        },
                        "team": "heal_all",
                        "desc": "全队治疗 250%，消耗 5 信仰(终极群奶)",
                        "name": "圣光赞歌"
                    }
,
                    "神迹·重生":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 5.0,
                        "kind": "治疗",
                        "team": "heal_all",
                        "cd": 5,
                        "desc": "终极技，全队满血治疗(团队终极技)",
                        "name": "神迹·重生"
                    }
,
                    "生命圣域":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 3.0,
                        "kind": "治疗",
                        "team": "heal_all",
                        "cd": 6,
                        "desc": "三转奥义，全队满血 + 减伤(终极救场)",
                        "name": "生命圣域"
                    }
,
                },
            },
        },
    },
    "cls_ci_ke": {
        "name": "刺客",
        "branches": {
            1: {
                "影舞者": {
                    "影刃":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.3,
                        "kind": "物理",
                        "res_gain": 1,
                        "cond": {
                            "type": "enemy_hp_high",
                            "hp_pct": 0.7,
                            "mult": 1.2,
                            "label": "暗影亲和"
                        },
                        "desc": "130% 影刃，连击点＋1。目标 HP>70% 时伤害＋20%(满血刺杀)",
                        "name": "影刃"
                    }
,
                    "无声":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "dodge_up",
                            "mult": 0.3
                        },
                        "desc": "触发被动：被攻击概率降低 30%(潜行生存)",
                        "name": "无声"
                    }
,
                    "幻影连刺":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.0,
                        "kind": "物理",
                        "multi": 3,
                        "res_gain": 3,
                        "cond": {
                            "type": "player_untouched",
                            "mult": 1.15,
                            "label": "身轻如燕"
                        },
                        "desc": "100%×3 幻影连刺，连击点＋3。自身未受击时伤害＋15%(无伤精准)",
                        "name": "幻影连刺"
                    }
,
                    "终结·处刑":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 4.0,
                        "kind": "物理",
                        "res_cost": {
                            "cp": 5
                        },
                        "cond": {
                            "type": "enemy_hp_low",
                            "hp_pct": 0.4,
                            "mult": 1.4,
                            "label": "死亡之舞"
                        },
                        "desc": "终结技，400% 处刑，消耗 5 连击点。目标 HP<40% 时伤害＋40%(斩杀)",
                        "name": "终结·处刑"
                    }
,
                },
                "毒刃者": {
                    "毒刃":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.1,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 2,
                        "res_gain": 1,
                        "cond": {
                            "type": "enemy_poison_stacks",
                            "stacks": 1,
                            "mult": 1.15,
                            "label": "毒刃蔓延"
                        },
                        "desc": "110% 毒刃，叠 2 层毒，连击点＋1。目标已中毒时伤害＋15%(叠毒加速)",
                        "name": "毒刃"
                    }
,
                    "毒师":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "poison_dmg",
                            "mult": 0.08
                        },
                        "desc": "触发被动：中毒目标受到伤害＋8%(毒系增伤)",
                        "name": "毒师"
                    }
,
                    "双毒刃":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.0,
                        "kind": "物理",
                        "multi": 2,
                        "mech": "poison",
                        "mech_val": 3,
                        "cond": {
                            "type": "enemy_poison_stacks",
                            "stacks": 3,
                            "mult": 1.15,
                            "label": "毒师专注"
                        },
                        "desc": "100%×2 双毒刃，叠 3 层毒。目标毒≥3 层时伤害＋15%(深度毒伤)",
                        "name": "双毒刃"
                    }
,
                    "毒爆":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 2.0,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 2,
                        "cond": {
                            "type": "enemy_poison_stacks",
                            "stacks": 5,
                            "mult": 1.3,
                            "label": "剧毒共鸣"
                        },
                        "desc": "200% 毒爆，叠毒。目标毒≥5 层时伤害＋30%(满层毒爆)",
                        "name": "毒爆"
                    }
,
                },
            },
            2: {
                "幻影刺客": {
                    "暗影之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "shadow",
                            "mult": 0.1
                        },
                        "desc": "二转被动：潜行持续时间＋1 回合(潜行强化)",
                        "name": "暗影之心"
                    }
,
                    "暗影突袭":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 1.6,
                        "kind": "物理",
                        "cd": 2,
                        "cond": {
                            "type": "player_untouched",
                            "mult": 1.2,
                            "label": "暗影突袭"
                        },
                        "desc": "160% 暗影突袭，CD2。自身未受击时伤害＋20%",
                        "name": "暗影突袭"
                    }
,
                    "死亡标记":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "mech": "mark",
                        "mech_val": 2,
                        "desc": "标记目标，目标易伤(配合团队斩杀)",
                        "name": "死亡标记"
                    }
,
                },
                "淬毒师": {
                    "淬毒之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "poison_dmg",
                            "mult": 0.1
                        },
                        "desc": "二转被动：毒层伤害＋10%(毒强化)",
                        "name": "淬毒之心"
                    }
,
                    "毒雾":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0.8,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 2,
                        "cd": 3,
                        "desc": "80% 毒雾(全体)，叠 2 层毒，CD3(AOE 叠毒)",
                        "name": "毒雾"
                    }
,
                    "淬毒刺杀":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.0,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 4,
                        "desc": "200% 淬毒刺杀，叠 4 层毒(深度叠毒)",
                        "name": "淬毒刺杀"
                    }
,
                },
            },
            3: {
                "幽影刺客": {
                    "幻影舞":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.0,
                        "kind": "物理",
                        "multi": 5,
                        "cd": 4,
                        "desc": "100%×5 幻影舞(终极连击)",
                        "name": "幻影舞"
                    }
,
                    "终结·暗影绞杀":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 5.0,
                        "kind": "物理",
                        "res_cost": {
                            "cp": 5
                        },
                        "cd": 5,
                        "desc": "终极技，500% 暗影绞杀，消耗 5 连击点(终极爆发)",
                        "name": "终结·暗影绞杀"
                    }
,
                    "影之国度":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "spd_up",
                        "cd": 6,
                        "desc": "三转奥义，进入暗影国度 3 回合(每回合高暴击)",
                        "name": "影之国度"
                    }
,
                },
                "蚀骨者": {
                    "剧毒风暴":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.5,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 4,
                        "cd": 4,
                        "desc": "150% 剧毒风暴(全体)，叠 4 层毒，CD4(群体毒爆)",
                        "name": "剧毒风暴"
                    }
,
                    "万毒噬心":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 3.0,
                        "kind": "物理",
                        "res_cost": {
                            "cp": 5
                        },
                        "mech": "poison",
                        "mech_val": 5,
                        "cd": 5,
                        "desc": "终极技，300% 万毒噬心，消耗 5 连击点 + 叠 5 层毒(终极毒杀)",
                        "name": "万毒噬心"
                    }
,
                    "万毒归宗":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 2.5,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 5,
                        "cd": 6,
                        "desc": "三转奥义，全体剧毒爆发(毒爆核弹)",
                        "name": "万毒归宗"
                    }
,
                },
            },
        },
    },
    "cls_wu_seng": {
        "name": "拳师",
        "branches": {
            1: {
                "拳斗士": {
                    "疾风拳":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.2,
                        "kind": "物理",
                        "combo": "拳",
                        "res_gain": 2,
                        "cond": {
                            "type": "player_res_stacks",
                            "res_key": "chi",
                            "stacks": 5,
                            "mult": 1.5,
                            "label": "疾风连打"
                        },
                        "desc": "120% 疾风拳，气＋2。气≥5 时伤害＋50%(气力滚雪球)",
                        "name": "疾风拳"
                    }
,
                    "武技":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "combo_dmg",
                            "mult": 0.05
                        },
                        "desc": "触发被动：连招期间伤害＋5%(连招强化)",
                        "name": "武技"
                    }
,
                    "旋风踢":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 1.3,
                        "kind": "物理",
                        "combo": "踢",
                        "res_gain": 1,
                        "cond": {
                            "type": "enemy_slowed",
                            "mult": 1.2,
                            "label": "踢击要害"
                        },
                        "desc": "130% 旋风踢，气＋1。目标减速时伤害＋20%",
                        "name": "旋风踢"
                    }
,
                    "斗气爆发":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 2.8,
                        "kind": "物理",
                        "res_cost": {
                            "chi": 5
                        },
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.4,
                            "mult": 1.3,
                            "label": "斗气护体"
                        },
                        "desc": "280% 斗气爆发，消耗 5 气。自身 HP<40% 时伤害＋30%(残血爆发)",
                        "name": "斗气爆发"
                    }
,
                },
                "磐石行者": {
                    "铁壁拳":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.1,
                        "kind": "物理",
                        "combo": "拳",
                        "res_gain": 1,
                        "effect": "def_up",
                        "cond": {
                            "type": "player_shield",
                            "mult": 1.15,
                            "label": "铁壁连拳"
                        },
                        "desc": "110% 铁壁拳，防御强化，气＋1。自身有护盾时伤害＋15%(护盾强化)",
                        "name": "铁壁拳"
                    }
,
                    "厚土":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "def",
                            "cond": "hp_high_70",
                            "mult": 0.1
                        },
                        "desc": "属性被动：生命高于 70% 时防御＋10%(满血坦克)",
                        "name": "厚土"
                    }
,
                    "回气掌":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 2.0,
                        "kind": "治疗",
                        "combo": "掌",
                        "res_gain": 3,
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.4,
                            "mult": 1.5,
                            "label": "回气连绵"
                        },
                        "desc": "治疗 200%(自愈)，气＋3。自身 HP<40% 时治疗量＋50%(残血自愈)",
                        "name": "回气掌"
                    }
,
                    "反震":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "reflect",
                            "mult": 0.3
                        },
                        "desc": "触发被动：受击后 30% 反伤(挨打反打)",
                        "name": "反震"
                    }
,
                    "磐石护壁":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "team": "reduce_all",
                        "res_cost": {
                            "chi": 3
                        },
                        "desc": "全队减伤 15% 2 回合，消耗 3 气(坦克核心)",
                        "name": "磐石护壁"
                    }
,
                },
            },
            2: {
                "武斗师": {
                    "斗气之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "res_gain_bonus": 1
                        },
                        "desc": "二转被动：气获取＋1(连招强化)",
                        "name": "斗气之心"
                    }
,
                    "连环拳":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 1.1,
                        "kind": "物理",
                        "multi": 4,
                        "combo": "拳",
                        "res_gain": 4,
                        "desc": "110%×4 连环拳，气＋4(快速攒气)",
                        "name": "连环拳"
                    }
,
                    "斗气裂空":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.6,
                        "kind": "物理",
                        "pierce": True,
                        "res_cost": {
                            "chi": 4
                        },
                        "desc": "260% 破防斗气裂空，消耗 4 气",
                        "name": "斗气裂空"
                    }
,
                },
                "铁壁行者": {
                    "磐石之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "dmg_taken",
                            "reduce": 0.05
                        },
                        "desc": "二转被动：受击减伤＋5%(坦克强化)",
                        "name": "磐石之心"
                    }
,
                    "斗气守御":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "shield_all",
                        "team": "shield_all",
                        "res_cost": {
                            "chi": 4
                        },
                        "desc": "全队护盾 20% HP，消耗 4 气(团队盾)",
                        "name": "斗气守御"
                    }
,
                },
            },
            3: {
                "破晓者": {
                    "无影连打":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.3,
                        "kind": "物理",
                        "multi": 5,
                        "combo": "拳",
                        "cond": {
                            "type": "player_res_stacks",
                            "res_key": "chi",
                            "stacks": 8,
                            "mult": 1.3,
                            "label": "气贯长虹"
                        },
                        "desc": "130%×5 无影连打(终极连招)。气≥8 时伤害＋30%(满气终极连招)",
                        "name": "无影连打"
                    }
,
                    "斗气天地":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 5.0,
                        "kind": "物理",
                        "res_cost": {
                            "chi": 10
                        },
                        "team": "atk_all",
                        "cd": 5,
                        "desc": "终极技，500% 斗气天地，消耗 10 气 + 全队攻击强化(终极斗气)",
                        "name": "斗气天地"
                    }
,
                    "斗气通天":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "atk_up_strong",
                        "cd": 6,
                        "desc": "三转奥义，3 回合内每次攻击大幅增伤(连招极限)",
                        "name": "斗气通天"
                    }
,
                },
                "磐岩壁垒": {
                    "磐石之躯":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "dmg_taken",
                            "reduce": 0.4,
                            "cond": "hp_low_30"
                        },
                        "desc": "触发被动：HP<30% 时减伤 40%(残血坦克)",
                        "name": "磐石之躯"
                    }
,
                    "斗气万法":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "team": "reduce_all",
                        "res_cost": {
                            "chi": 10
                        },
                        "cd": 5,
                        "desc": "终极技，全队减伤 30% 3 回合，消耗 10 气(终极团队技)",
                        "name": "斗气万法"
                    }
,
                    "大地守护":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "team": "reduce_all",
                        "cd": 6,
                        "desc": "三转奥义，全队减伤 50% 3 回合(终极坦克)",
                        "name": "大地守护"
                    }
,
                },
            },
        },
    },
}

# v95.23 职业导师进阶技能：各城导师专属，普通『技能学习』学不到，需找导师对话学习
# 格式与 PLAYER_SKILLS 技能一致（battle/engine 按名字查定义）
TUTOR_SKILLS = {
    "cls_zhan_shi": {
        "sk_po_jia_zhan": {
            "lv": 6, "mp": 8, "power": 1.6, "kind": "物理",
            "mech": "spd_down", "mech_chance": 0.3, "cd": 2,
            "desc": "破甲斩！160% 物理伤害，30% 概率震慑目标(速度－20%)",
            "name": "破甲斩",
        },
        "sk_zhan_hou": {
            "lv": 10, "mp": 12, "power": 0, "kind": "增益",
            "effect": "atk_up", "cd": 3,
            "desc": "战吼！自身攻击＋30% 2 回合",
            "name": "战吼",
        },
    },
    "cls_fa_shi": {
        "sk_ao_shu_mai_chong": {
            "lv": 6, "mp": 10, "power": 1.7, "kind": "魔法",
            "mech": "arcane", "cd": 2,
            "desc": "奥术脉冲！170% 魔法伤害，奥术之力涌动",
            "name": "奥术脉冲",
        },
        "sk_bing_shuang_xin_xing": {
            "lv": 10, "mp": 14, "power": 1.3, "kind": "魔法",
            "mech": "freeze", "mech_chance": 0.25, "cd": 3,
            "desc": "冰霜新星！130% 魔法伤害，25% 概率冰冻目标",
            "name": "冰霜新星",
        },
    },
    "cls_you_xia": {
        "sk_san_lian_she": {
            "lv": 6, "mp": 8, "power": 1.55, "kind": "物理",
            "cd": 2,
            "desc": "三连射！连续射出三支箭矢，155% 物理伤害",
            "name": "三连射",
        },
        "sk_ying_yan": {
            "lv": 10, "mp": 10, "power": 0, "kind": "增益",
            "effect": "crit_up", "cd": 3,
            "desc": "鹰眼！集中精神，暴击＋25% 2 回合",
            "name": "鹰眼",
        },
    },
    "cls_mu_shi": {
        "sk_sheng_guang_cheng_jie": {
            "lv": 6, "mp": 10, "power": 1.4, "kind": "魔法",
            "cd": 2,
            "desc": "圣光惩戒！140% 魔法伤害，对黑暗生物额外威慑",
            "name": "圣光惩戒",
        },
        "sk_jiu_shu_zhi_guang": {
            "lv": 10, "mp": 15, "power": 1.5, "kind": "治疗",
            "cd": 2, "team": "heal_all",
            "desc": "救赎之光！治疗全队 150% 生命(副本广播，团队技能)",
            "name": "救赎之光",
        },
    },
    "cls_ci_ke": {
        "sk_ying_xi": {
            "lv": 6, "mp": 8, "power": 1.7, "kind": "物理",
            "mech": "shadow", "cd": 2,
            "desc": "影袭！170% 物理伤害，从阴影中出手",
            "name": "影袭",
        },
        "sk_cui_du_zhi_ren": {
            "lv": 10, "mp": 10, "power": 1.3, "kind": "物理",
            "mech": "poison", "mech_chance": 0.5, "cd": 3,
            "desc": "淬毒之刃！130% 物理伤害，50% 概率使目标中毒 2 回合",
            "name": "淬毒之刃",
        },
    },
    "cls_wu_seng": {
        "sk_beng_quan_lie": {
            "lv": 6, "mp": 8, "power": 1.6, "kind": "物理",
            "mech": "stun", "mech_chance": 0.2, "cd": 2,
            "desc": "崩拳·裂！160% 物理伤害，20% 概率击晕目标",
            "name": "崩拳·裂",
        },
        "sk_jin_gang_ti": {
            "lv": 10, "mp": 12, "power": 0, "kind": "增益",
            "effect": "def_up", "cd": 3,
            "desc": "金刚体！运气于身，防御＋40% 2 回合",
            "name": "金刚体",
        },
    },
}
