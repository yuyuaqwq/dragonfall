# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - skills.py(阶段六：基础技能 v2.0，12 章)"""
PLAYER_SKILLS = {
    "cls_zhan_shi": {
        "name": "战士",
        "skills": {
    "sk_hui_kan": {
                "lv": 1,
                "mp": 3,
                "power": 1.0,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"},
                "desc": "基础斩击，100% 物理伤害。先手(速度高于目标)时伤害＋15%",
                "name": "挥砍",
            },
    "sk_meng_ji": {
                "lv": 2,
                "mp": 4,
                "power": 1.2,
                "kind": "物理",
                "res_gain": 1,
                "desc": "猛力一击，120% 物理伤害。",
                "name": "猛击",
            },
    "sk_po_jia_zhan": {
                "lv": 8,
                "mp": 6,
                "power": 0.875,
                "kind": "物理",
                "pierce": True,
                "res_gain": 2,
                "cond": {"type": "player_hp_low", "hp_pct": 0.4, "mult": 1.2, "label": "绝地反击"},
                "desc": "破防斩击，130% 物理伤害(无视防御)。自身 HP<40% 时伤害＋20%",
                "name": "破甲斩",
            },
    "sk_xuan_feng_zhan": {
                "lv": 14,
                "mp": 10,
                "power": 0.946,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "enemy_hp_high", "hp_pct": 0.7, "mult": 1.4, "label": "孤军深入"},
                "aoe": "front",
                "desc": "旋转斩击，110% 全体伤害(打前排)。目标 HP>70% 时＋40%",
                "name": "旋风斩",
            },
    "sk_lie_di_zhan": {
                "lv": 20,
                "mp": 8,
                "power": 0.816,
                "kind": "物理",
                "pierce": True,
                "res_cost": {"rage": 3},
                "cond": {"type": "player_res_stacks", "res_key": "rage", "stacks": 8, "mult": 1.5, "label": "震怒"},
                "desc": "终结技，180% 破防斩击。怒气≥8 时伤害＋50%",
                "name": "裂地斩",
            },
    "sk_xu_li_zhan": {
                "lv": 22,
                "mp": 16,
                "power": 2.2,
                "kind": "物理",
                "pierce": True,
                "res_gain": 2,
                "cd": 4,
                "charge": 1,
                "desc": "蓄力斩！蓄力 1 回合，期间受击会被打断；蓄力完成挥出 220% 破防一击。",
                "name": "蓄力斩",
            },
    "sk_zhan_hou": {
                "lv": 3,
                "mp": 5,
                "power": 0,
                "kind": "增益",
                "effect": "atk_up",
                "cd": 3,
                "res_gain": 3,
                "team": "atk_all",
                "desc": "战吼！攻＋30% 3 回合。组队时全队攻＋30%(团队技能)",
                "name": "战吼",
            },
    "sk_tie_bi": {
                "lv": 6,
                "mp": 5,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "res_gain": 2,
                "desc": "铁壁！防＋45% 3 回合",
                "name": "铁壁",
            },
    "sk_xu_shi": {
                "lv": 11,
                "mp": 3,
                "power": 0,
                "kind": "增益",
                "effect": "atk_up",
                "cd": 2,
                "res_gain": 4,
                "desc": "蓄势！攻击＋30% 3 回合(终结技前奏)",
                "name": "蓄势",
            },
    "sk_dun_ji": {
                "lv": 17,
                "mp": 6,
                "power": 1.3,
                "kind": "物理",
                "cd": 3,
                "cc": "stun",
                "desc": "盾击！130% 伤害 + 35% 概率眩晕 1 回合(强控·单体，CD 3)",
                "name": "盾击",
            },
    "sk_zhan_zheng_jian_ta": {
                "lv": 24,
                "mp": 12,
                "power": 0.8,
                "kind": "物理",
                "res_gain": 2,
                "cond": {"type": "enemy_frozen", "mult": 1.4, "label": "震地压制"},
                "aoe": "front",
                "desc": "战争践踏！80% 全体伤害(打前排)。目标被冻结/减速时＋40%",
                "name": "战争践踏",
            },
    "sk_wu_wei_chong_ji": {
                "lv": 30,
                "mp": 15,
                "power": 0.724,
                "kind": "物理",
                "res_cost": {"rage": 10},
                "consume_all": {"key": "rage", "per": 0.12},
                "pierce": True,
                # v130.2 基础瘦身：去 HP<30% 血线乘区条件，做成无条件朴素满怒大招（EQ = 2.2×2.2 ≈ 4.84）
                "desc": "无畏冲击！消耗全部怒气，每点怒气＋12% 伤害(满怒 220% 威力)。基础满怒档大招。",
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
    # v112 一转觉醒被动（Lv.30）：基础职业与隐藏线线级被动对齐的仪式感节点
    "sk_p_gang_tie_bi_lei": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "def", "cond": "hp_high_70", "mult": 0.10},
                "desc": "属性被动：生命高于70%时防御＋10%(一转觉醒·钢铁壁垒)",
                "name": "钢铁壁垒",
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
                "passive": {"proc": "res_gain_bonus"},
                "desc": "触发被动：攻击命中时怒气额外+1",
                "name": "战争咆哮",
            },
    "sk_p_p...tong": {
                "lv": 45,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "pene_phys", "add": 0.05},
                "desc": "属性被动：物穿＋5%（无视物理防御，v106.2 职业特色渠道）",
                "name": "破甲精通",
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
                "power": 0.964,
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
                "power": 1.046,
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
                "element": "current",
                "desc": "元素爆发！当前系 160% 伤害 + 触发一次元素反应(蒸发/超载/冻结/感电)",
                "name": "元素爆发",
            },
    "sk_yuan_su_liu_zhuan": {
                "lv": 3,
                "mp": 5,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 2,
                "team": "matk_all",
                "desc": "元素流转！魔攻＋50% 3 回合，组队时全队魔攻强化(爆发前奏)",
                "name": "元素流转",
            },
    "sk_yuan_su_dan_mu": {
                "lv": 6,
                "mp": 12,
                "power": 0.842,
                "kind": "魔法",
                "multi": 2,
                "desc": "元素弹幕！100%×2，当前系增伤(低耗填充)",
                "name": "元素弹幕",
            },
    "sk_yuan_su_hu_dun": {
                "lv": 11,
                "mp": 20,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "desc": "元素护盾！防＋45% 3 回合(CD 3)",
                "name": "元素护盾",
            },
    "sk_ao_shu_qiang_hua": {
                "lv": 17,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "desc": "奥术强化！matk＋50% 3 回合(爆发前奏)",
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
                "aoe": "all",
                "desc": "冰霜新星！80% 全体伤害＋30% 概率冻结 1 回合(强控·群体，CD 3)",
                "name": "冰霜新星",
            },
    "sk_yuan_su_feng_bao": {
                "lv": 30,
                "mp": 60,
                "power": 2.0,
                "kind": "魔法",
                "element": "current",
                "cond": {"type": "element_marks", "element": "any", "stacks": 1, "mult": 1.5, "label": "元素过载"},
                "aoe": "all",
                "desc": "元素风暴！当前系 200% 全体伤害。目标有元素印记时＋50%(元素过载)",
                "name": "元素风暴",
            },
    "sk_yun_shi_shu": {
                "lv": 28,
                "mp": 75,
                "power": 3.0,
                "kind": "魔法",
                "element": "fire",
                "cd": 4,
                "charge": 2,
                "aoe": "all",
                "reach": 3,
                "desc": "陨石术！蓄力 2 回合，期间受击会被打断；蓄力完成召唤陨石轰击全场，火系 300% 范围伤害(可及全阵后排)。",
                "name": "陨石术",
            },
    "sk_fa_shu_fan_zhi": {
                "lv": 16,
                "mp": 15,
                "power": 0.3,
                "kind": "魔法",
                "element": "current",
                "cd": 3,
                "interrupt": True,
                "desc": "法术禁制！30% 微量魔法伤害，命中打断目标蓄力(可打断读条技能)。",
                "name": "法术禁制",
            },
    "sk_p_lie_yan_qin_he": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "fire_bonus", "mult": 0.10},
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
    "sk_p_mo_li_peng_pai": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "matk", "cond": "hp_high_70", "mult": 0.08},
                "desc": "属性被动：生命高于70%时魔攻＋8%(一转觉醒·魔力澎湃)",
                "name": "魔力澎湃",
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
                "desc": "疾风连射！连续射击 2 次，每次 60% 物理伤害",
                "name": "疾风连射",
            },
    "sk_miao_zhun": {
                "lv": 2,
                "mp": 0,
                "res_cost": {"energy": 10},
                "power": 1.4,
                "kind": "物理",
                "desc": "屏息瞄准，140% 物理伤害。",
                "name": "瞄准射击",
            },
    "sk_zhi_ming_ju_ji": {
                "lv": 8,
                "mp": 0,
                "power": 1.357,
                "kind": "物理",
                "res_cost": {"energy": 35},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.4, "mult": 1.5, "label": "绝境之眼"},
                "desc": "致命狙击！180% 单体伤害。目标 HP<40% 时＋50%(处决狙击)",
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
                "desc": "猎网陷阱！120% 伤害＋2 层灼烧(延时引爆)",
                "name": "猎网陷阱",
            },
    "sk_huan_shou_qi_yue": {
                "lv": 20,
                "mp": 0,
                "power": 1.5,
                "kind": "物理",
                "res_cost": {"energy": 40},
                # v113.1 数值：林语印记带消耗也带命中回能（res_gain 指向本职业 energy）
                "res_gain": {"energy": 10},
                "mech": "mark",
                "mech_val": 1,
                "desc": "林语印记！150% 自然伤害 + 猎杀标记，命中回复 10 点精力(自然印记·标记核心)",
                "name": "林语印记",
            },
    "sk_ying_yan_suo_ding": {
                "lv": 3,
                "mp": 0,
                "power": 0,
                "kind": "增益",
                "effect": "crit_up",
                "cd": 2,
                "res_cost": {"energy": 15},
                "desc": "鹰眼锁定！暴击率＋20% 3 回合",
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
                "desc": "风之疾走！速度＋40% 3 回合(机动)",
                "name": "风之疾走",
            },
    "sk_cui_du_jian_shi": {
                "lv": 11,
                "mp": 0,
                "power": 0.8,
                "kind": "物理",
                "res_cost": {"energy": 20},
                "mech": "poison",
                "mech_val": 3,
                "desc": "淬毒箭矢！80% 伤害＋3 层中毒(毒体系铺垫，消耗 20 精力)",
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
                "desc": "伪装帷幕！闪避率＋40% 3 回合(隐形求生)",
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
                "desc": "狩猎咆哮！攻＋30% 3 回合(标记爆发前奏)",
                "name": "狩猎咆哮",
            },
    "sk_shou_lie_zhong_zhang": {
                "lv": 30,
                "mp": 0,
                "power": 1.202,
                "kind": "物理",
                "res_cost": {"energy": 100},
                "mech": "mark_burst",
                # v130.2：100 档终极奥义「狩猎终章」纯伤害 4.8（EQ 锚定铁律 2）；去叠毒引爆条件（叠标/引爆归攻线林语者）
                "desc": "狩猎终章！480% 致命一击，消耗全部精力(100 精力大终结)。",
                "name": "狩猎终章",
            },
    "sk_xu_li_ju_ji": {
                "lv": 26,
                "mp": 0,
                "power": 2.0,
                "kind": "物理",
                "pierce": True,
                "res_cost": {"energy": 50},
                "cd": 4,
                "charge": 1,
                "reach": 3,
                "desc": "蓄力狙击！蓄力 1 回合，期间受击会被打断；狙击后排，蓄力完成射出 200% 破防一箭(可及全阵)。",
                "name": "蓄力狙击",
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
    "sk_p_feng_zhi_jia_hu": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "dodge", "mult": 0.05},
                "desc": "属性被动：闪避率＋5%(一转觉醒·风之加护)",
                "name": "风之加护",
            },
    "sk_p_ying_yan": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "mark_extra", "chance": 0.15},
                "desc": "触发被动：攻击时15%概率额外叠1印记(与追踪印记叠加)",
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
    "sk_p_c...jian": {
                "lv": 48,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "pene_phys", "add": 0.05},
                "desc": "属性被动：物穿＋5%（无视物理防御，v106.2 职业特色渠道）",
                "name": "穿甲箭",
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
                "desc": "圣光弹！100% 圣光伤害。自身 HP>70% 时＋20%",
                "name": "圣光弹",
            },
    "sk_sheng_guang": {
                "lv": 2,
                "mp": 8,
                "power": 1.15,
                "kind": "魔法",
                "res_gain": 1,
                "desc": "圣光凝聚成束，115% 圣光伤害。",
                "name": "圣光术",
            },
    "sk_zhi_yu_shu": {
                "lv": 8,
                "mp": 15,
                "power": 2.0,
                "kind": "治疗",
                # v130.2 治疗系 per-skill gain 归零（攒点走全局 on_heal +2，防双计数）
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "治愈之光"},
                "desc": "治愈术！治疗 200%。自身 HP<30% 时治疗量＋50%(紧急救治)",
                "name": "治愈术",
            },
    "sk_cheng_jie": {
        # v130.2 基础瘦身：惩戒 由「耗 2 信仰」改为「攒点 +1 信仰」——基础只留满点神迹一个消耗档
        # 原「审判之光·对中毒目标 ×1.3」多技能联动下放攻线（见 priest.md §4.1）
        "lv": 10,
        "mp": 20,
        "power": 1.2,
        "kind": "魔法",
        "res_gain": 1,
        "desc": "惩戒！120% 圣光伤害(基础圣光攒点技，命中 +1 信仰)",
        "name": "惩戒",
    },
    "sk_sheng_guang_cheng_ji": {
                "lv": 20,
                "mp": 30,
                "power": 0.905,
                "kind": "魔法",
                "res_cost": {"faith": 3},
                "mech": "cleanse",
                "mech_val": 1,
                "cond": {"type": "player_res_stacks", "res_key": "faith", "stacks": 8, "mult": 1.4, "label": "信仰坚定"},
                "desc": "圣光惩击！200% 伤害 + 驱散敌方增益。信仰≥8 时＋40%",
                "name": "圣光惩击",
            },
    "sk_sheng_guang_hu_dun": {
                "lv": 3,
                "mp": 12,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                # v130.2 增益技不攒点（gain 归零）
                "desc": "圣光护盾！防＋45% 3 回合(保命)",
                "name": "圣光护盾",
            },
    "sk_qun_ti_zhi_yu": {
                "lv": 6,
                "mp": 20,
                "power": 1.5,
                "kind": "治疗",
                "cd": 2,
                # v130.2 治疗系 per-skill gain 归零（攒点走全局 on_heal +2，防双计数）
                "team": "heal_all",
                "desc": "群体治愈！全队治疗 150%(群奶核心，团队技能)",
                "name": "群体治愈",
            },
    "sk_xin_yang_qi_dao": {
                "lv": 11,
                "mp": 15,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                # v130.2 增益技不攒点（gain 归零）
                "desc": "信仰祈祷！matk＋50% 3 回合(增幅)",
                "name": "信仰祈祷",
            },
    "sk_shen_sheng_dao_yan": {
                "lv": 17,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "desc": "神圣祷言！matk＋50% 3 回合(战斗牧师爆发前奏)",
                "name": "神圣祷言",
            },
    "sk_sheng_guang_qu_san": {
                "lv": 24,
                "mp": 35,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "desc": "圣光驱散！全队防御强化(团队技能)。注：当前实现为防御强化（effect=def_up），驱散/净化战斗加成二期排期待定",
                "name": "圣光驱散",
            },
    "sk_shen_en_jiang_lin": {
                "lv": 30,
                "mp": 50,
                "power": 1.8,
                "kind": "治疗",
                "res_cost": {"faith": 10},
                "consume_all": {"key": "faith", "per": 0.08},
                "team": "heal_all",
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "自我牺牲"},
                "desc": "神恩降临！全队治疗 180%，消耗全部信仰(每点＋8%)。自身 HP<30% 时治疗量＋50%(低血救场)",
                "name": "神恩降临",
            },
    "sk_da_zhi_liao_shu": {
                "lv": 26,
                "mp": 45,
                "power": 3.2,
                "kind": "治疗",
                "team": "heal_all",
                # v130.2 治疗系 per-skill gain 归零（攒点走全局 on_heal +2，防双计数）
                "cd": 3,
                "charge": 1,
                "desc": "大治疗术！蓄力 1 回合，期间受击会被打断；蓄力完成施展圣光治愈，全队治疗 320%。",
                "name": "大治疗术",
            },
    "sk_shen_fa_sheng_cai": {
                # v130.2 新增：基础满点神迹·神威爆发（EQ = 3.0 全体 ×1.6 折算 ≈ 4.8，铁律 2 锚定）
                "lv": 30,
                "mp": 40,
                "power": 1.663,
                "kind": "魔法",
                "aoe": "all",
                "res_cost": {"faith": 10},
                "cd": 6,
                "desc": "神罚·圣裁！300% 全体圣光惩罚，消耗全部信仰(基础满点神迹)",
                "name": "神罚·圣裁",
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
                "passive": {"proc": "dmg_taken", "reduce": 0.05, "res_gain": 1},
                "desc": "触发被动：受击减伤5%，受击时信仰+1",
                "name": "神圣坚韧",
            },
    "sk_p_sheng_guang_zhu_fu": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "heal_power", "add": 0.05},
                "desc": "属性被动：治疗强度＋5%(一转觉醒·圣光祝福)",
                "name": "圣光祝福",
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
                "mp": 3,
                "power": 1.0,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.2, "label": "先手偷袭"},
                "desc": "刺击！100% 单体伤害。先手时＋20%",
                "name": "刺击",
            },
    "sk_ge_lie": {
                "lv": 2,
                "mp": 4,
                "power": 1.15,
                "kind": "物理",
                "res_gain": 1,
                "desc": "利刃撕裂，115% 物理伤害。",
                "name": "割裂",
            },
    "sk_shuang_ren_luan_wu": {
                "lv": 8,
                "mp": 8,
                "power": 0.651,
                "kind": "物理",
                "multi": 2,
                # v130.2 基础瘦身：多段不再每段回点，统一朴素「命中 +1」（高频多段下放攻线影舞者）
                "res_gain": 1,
                "cond": {"type": "enemy_hp_high", "hp_pct": 0.7, "mult": 1.3, "label": "背刺角度"},
                "desc": "双刃乱舞！90%×2。目标 HP>70% 时＋30%(满血背刺)",
                "name": "双刃乱舞",
            },
    "sk_cui_du": {
                "lv": 14,
                "mp": 6,
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
                "mp": 12,
                "power": 1.147,
                "kind": "物理",
                "res_cost": {"cp": 3},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.4, "mult": 1.4, "label": "残血收割"},
                "desc": "暗杀！240% 单体伤害。目标 HP<40% 时＋40%(斩杀线)",
                "name": "暗杀",
            },
    "sk_qian_xing": {
                "lv": 3,
                "mp": 5,
                "power": 0,
                "kind": "增益",
                "effect": "stealth",
                "cd": 3,
                "res_gain": 1,
                "desc": "潜行！暴击率＋20% 3 回合，下次攻击必暴(爆发核心)",
                "name": "潜行",
            },
    "sk_ji_ying": {
                "lv": 6,
                "mp": 3,
                "power": 0,
                "kind": "增益",
                "effect": "spd_up",
                "cd": 2,
                "desc": "疾影！速度＋40% 2 回合(机动)",
                "name": "疾影",
            },
    "sk_ying_xi": {
                "lv": 11,
                "mp": 6,
                "power": 1.2,
                "kind": "物理",
                "res_gain": 1,
                "mech": "shadow",
                "mech_val": 1,
                "desc": "影袭！120% 伤害 + 影袭层数(潜行联动)",
                "name": "影袭",
            },
    "sk_si_wang_biao_ji": {
                "lv": 17,
                "mp": 6,
                "power": 0,
                "kind": "增益",
                "effect": "mark",
                "cd": 2,
                "res_gain": 1,
                "team": "crit_all",
                "desc": "死亡标记！目标易伤(受击＋30%)(铺垫)",
                "name": "死亡标记",
            },
    "sk_du_wu": {
                "lv": 24,
                "mp": 10,
                "power": 0.8,
                "kind": "物理",
                "cd": 3,
                "mech": "poison",
                "mech_val": 2,
                "aoe": "all",
                "desc": "毒雾！80% 全体伤害＋2 层中毒(毒刃流铺场)",
                "name": "毒雾",
            },
    "sk_an_ying_chu_xing": {
                "lv": 30,
                "mp": 18,
                "power": 1.317,
                "kind": "物理",
                # v130.2 统一公式：per=0 威力恒为数据表 3.2（满 5 点 3.2×1.5=EQ4.8，策划 12 章 §6.1 奥义基准；
                # 「每点＋40%」为 v104 旧式 1+per×cur 残留——暗影处刑定位=固定 5 点高档终结，非逐点强化）
                "consume_all": {"key": "cp", "per": 0.0},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "死亡边缘"},
                "desc": "暗影处刑！基础 320% 致命一击，消耗全部连击点。目标 HP<30% 时威力＋50%",
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
    "sk_p_ying_ren_jing_tong": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "crit_dmg", "add": 0.10},
                "desc": "属性被动：暴击伤害＋10%(一转觉醒·影刃精通)",
                "name": "影刃精通",
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
                "mp": 3,
                "power": 1.0,
                "kind": "物理",
                "combo": "拳",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.15, "label": "起手式"},
                "desc": "直拳！100% 单体伤害，连招【拳】。先手时＋15%",
                "name": "直拳",
            },
    "sk_chong_quan": {
                "lv": 2,
                "mp": 3,
                "power": 1.1,
                "kind": "物理",
                "res_gain": 1,
                "combo": "拳",
                "desc": "沉肩冲拳，110% 物理伤害，连招【拳】。",
                "name": "冲拳",
            },
    "sk_beng_quan": {
        # v95.7 #39：碎骨拳 8→4 级并改为耗气技（3 气），解决武僧 Lv.2-7 气满无出口的空转
        # v130.2：基础 3 气档轻倾泻——power 1.5，敌血高 +20%
        "lv": 4,
        "mp": 6,
        "power": 0.96,
        "kind": "物理",
        "combo": "拳",
        "pierce": True,
        "res_cost": {"chi": 3},
        "cond": {"type": "enemy_hp_high", "hp_pct": 0.7, "mult": 1.2, "label": "崩山之势"},
        "desc": "碎骨拳！150% 破防伤害，连招【拳】，消耗 3 气(基础 3 气档)。目标 HP>70% 时＋20%",
        "name": "碎骨拳",
    },
    "sk_hui_xuan_ti": {
                "lv": 14,
                "mp": 6,
                "power": 1.2,
                "kind": "物理",
                "combo": "踢",
                "res_gain": 1,
                "cond": {"type": "enemy_frozen", "mult": 1.3, "label": "立足不稳"},
                "aoe": "front",
                "desc": "回旋踢！120% 全体伤害(打前排)，连招【踢】。目标减速/冻结时＋30%",
                "name": "回旋踢",
            },
    "sk_zhen_di_ji": {
                "lv": 20,
                "mp": 8,
                "power": 1.3,
                "kind": "物理",
                "combo": "踢",
                "res_gain": 1,
                "cc": "stun",
                "aoe": "front",
                "desc": "震地击！130% 全体伤害(打前排)＋35% 概率眩晕，连招【踢】",
                "name": "震地击",
            },
    "sk_ce_ti": {
                "lv": 3,
                "mp": 4,
                "power": 1.1,
                "kind": "物理",
                "combo": "踢",
                "res_gain": 1,
                # v130.6 变招（player_combo）：上一招是【拳】→ 伤害 +10%（连击惯性，
                # 策划案 7.3「若上一招是拳（直拳），气额外+1」的伤害化表达，鼓励按序连招）
                "cond": {"type": "player_combo", "last": "拳", "mult": 1.10, "label": "连击惯性"},
                "desc": "侧踢！110% 伤害，连招【踢】(连招第二段)。上一招是拳时＋10%",
                "name": "侧踢",
            },
    "sk_tie_zhang": {
                "lv": 6,
                "mp": 5,
                "power": 1.2,
                "kind": "物理",
                "combo": "掌",
                "res_gain": 1,
                "desc": "钢拳！120% 伤害，连招【掌】(三连准备)",
                "name": "钢拳",
            },
    "sk_qi_xi_tiao_xi": {
                "lv": 11,
                "mp": 5,
                "power": 0.15,
                "kind": "治疗",
                "cd": 3,
                "res_gain": 2,
                "desc": "冥想！回复 15% HP(续航)",
                "name": "冥想",
            },
    "sk_tong_qiang": {
                "lv": 17,
                "mp": 5,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "res_gain": 2,
                "team": "def_all",
                "desc": "铜墙！防＋45% 2 回合(磐石流铺垫)",
                "name": "铜墙",
            },
    "sk_lian_zhao_san_lian": {
                "lv": 24,
                "mp": 10,
                "power": 0.896,
                "kind": "物理",
                "combo": "拳",
                "multi": 3,
                "res_gain": 3,
                "desc": "连招·三连！150%×3(连招核心，三连完成时气力技＋20%)",
                "name": "连招三连",
            },
    "sk_po_xiao_zhi_quan": {
                "lv": 30,
                "mp": 15,
                "power": 0.634,
                "kind": "物理",
                "consume_all": {"key": "chi", "per": 0.1},
                # v130.2 基础瘦身：破晓之拳重定为无条件满势终结——每 1 气物理威力 +10%（2.4×(1+0.1×10)=4.8），
                # 满 10 气 EQ≈4.8（去残血条件；res_cost 与 consume_all 冲突字段已去，改按持有气动态结算）
                "desc": "破晓之拳！240% 致命一击，消耗全部气(每点＋10%，满 10 气威力翻倍)",
                "name": "破晓之拳",
            },
    "sk_p_lian_zhao_jing_tong": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "combo_boost"},
                "desc": "触发被动：三连击破追加伤害提升至 50%（v109.2 武圣连击强化）",
                "name": "连招精通",
            },
    "sk_p_pan_shi_ti": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05, "res_gain": 1},
                "desc": "触发被动：受击减伤5%，受击时气+1",
                "name": "磐石体",
            },
    "sk_p_qi_shou_shi": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "atk", "cond": "battle_start", "mult": 0.08},
                "desc": "属性被动：战斗开始时攻击＋8%(一转觉醒·起手式)",
                "name": "起手式",
            },
    "sk_p_qi_xi_tiao_he": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "turn_heal", "pct": 0.02},
                "desc": "触发被动：每回合回复2%生命",
                "name": "气力调和",
            },
    "sk_p_dou_qi_ning_ju": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "chi_gain", "mult": 1},
                "desc": "属性被动：气获取＋1",
                "name": "气力凝聚",
            },
        },
    },
    # ================= v87 隐藏职业：魔剑士（09 章九.2，Lv.60 解锁）=================
}

BRANCH_SKILLS = {
    "cls_zhan_shi": {
        "name": "战士",
        "branches": {
            1: {
                "狂战士": {
                    "怒斩":                     {
                        "lv": 32,
                        "power": 1.166,
                        "kind": "物理",
                        "res_gain": 2,
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.5,
                            "mult": 1.25,
                            "label": "狂战血统"
                        },
                        "mp": 5,
                        "desc": "238% 斩击。自身 HP<50% 时伤害＋25%(残血狂战)",
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
                        "power": 1.6,
                        "kind": "物理",
                        "lifesteal": 0.25,
                        "res_gain": 2,
                        "cond": {
                            "type": "enemy_debuff",
                            "mult": 1.2,
                            "label": "猎物标记"
                        },
                        "mp": 8,
                        "desc": "160% 吸血斩击(吸血 25%)。目标有减益时伤害＋20%",
                        "name": "嗜血斩"
                    }
,
                    "狂怒爆发":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 1.307,
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
                        "desc": "终结技，240% 斩击。自身 HP<30% 时伤害＋40%(背水一战)",
                        "name": "狂怒爆发"
                    }
,
                    # v113：真伤机制下放——龙息之怒(原龙裔线 T3)降为战士攻线 Lv.55 进阶技
                    "龙息之怒":                     {
                        "lv": 55,
                        "mp": 30,
                        "power": 1.0,
                        "kind": "真伤",
                        "mech": "burn",
                        "mech_val": 2,
                        "cd": 4,
                        "res_gain": 2,
                        "desc": "龙息之怒！100% 真伤(无视全部防御)＋2 层灼烧(屠龙之技·下放自龙裔线)",
                        "name": "龙息之怒"
                    }
,
                },
                "盾卫士": {
                    "盾击·卫":                     {
                        "lv": 32,
                        "power": 1.634,
                        "kind": "物理",
                        "mech": "stun",
                        "mech_val": 1,
                        "cond": {
                            "type": "enemy_stunned",
                            "mult": 1.5,
                            "label": "盾击连打"
                        },
                        "mp": 5,
                        "desc": "238% 盾击，概率眩晕 1 回合。目标被眩晕时追加 50% 伤害(控制链)",
                        "cd": 3,
                        "name": "盾击·卫"
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
                        "desc": "触发被动：受击伤害－10%，受击(坦克攒怒)",
                        "name": "守护姿态"
                    }
,
                    "坚盾壁垒":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "team": "def_all",
                        "res_cost": {"rage": 3},
                        "desc": "全队防御强化(组队时广播)。坦克核心",
                        "name": "坚盾壁垒"
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
                        "res_cost": {
                            "rage": 3
                        },
                        "desc": "嘲讽，CD 3，强制怪物攻击自己 2 回合(拉怪核心)",
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
                        "power": 1.2,
                        "kind": "物理",
                        "multi": 3,
                        "res_gain": 3,
                        "mp": 10,
                        "desc": "120%×3 快速连斩(输出循环填充)",
                        "cd": 2,
                        "name": "乱舞"
                    }
,
                    "处决":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 2.647,
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
                        "desc": "终结技，300% 斩杀。目标 HP<35% 时伤害＋50%",
                        "cd": 2,
                        "name": "处决"
                    }
,
                },
                "坚盾卫士": {
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
                        "power": 1.097,
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
                        "desc": "220% 破防重锤。目标 HP>70% 时伤害＋50%(压制满血)",
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
                        "power": 1.202,
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
                        "aoe": "all",
                        "desc": "180%×3 全体连斩。怒气≥9 时伤害＋30%",
                        "cd": 3,
                        "name": "怒涛连斩"
                    }
,
                    "战争化身":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 2.396,
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
                        "desc": "三转奥义，3 回合内攻击大幅提升(战争领域)",
                        "name": "战争领域"
                    }
,
                },
                "坚城统帅": {
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
                        "desc": "替全队承受伤害的誓言，全队防御强化(团队保护)",
                        "name": "守护誓言"
                    }
,
                    "不破壁垒":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "reduce_all": 0.25,   # v1.x 数值下沉：全队减伤 25%（原 battle.py REDUCE_ALL_PCT 中文名硬编码）
                        "team": "reduce_all",
                        "res_cost": {
                            "rage": 5
                        },
                        "cd": 5,
                        "desc": "终极技，全队减伤 25% 3 回合(团队终极防御)",
                        "name": "不破壁垒"
                    }
,
                    "守护圣域":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "reduce_all": 0.50,   # v1.x 数值下沉：全队减伤 50%（守护圣域）
                        "team": "reduce_all",
                        "res_cost": {
                            "rage": 5
                        },
                        "cd": 6,
                        "desc": "三转奥义，全队无敌屏障(守护圣域)",
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
                        "power": 1.371,
                        "kind": "魔法",
                        "element": "current",
                        "cond": {
                            "type": "element_marks",
                            "element": "any",
                            "stacks": 1,
                            "mult": 1.2,
                            "label": "万象共鸣"
                        },
                        "mp": 15,
                        "res_gain": {"element": 1},
                        "desc": "当前系 190% 单体，挂元素印记。目标已有印记时伤害＋20%(反应前奏，充能 +1)",
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
                        "mp": 20,
                        "res_cost": {"element": 3},
                        "desc": "当前系 130%×2，挂 2 层印记。目标印记≥3 层时伤害＋25%（消耗 3 充能）",
                        "cd": 2,
                        "name": "双系连珠"
                    }
,
                    "元素引爆":                     {
                        "lv": 55,
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
                        "mp": 25,
                        "res_cost": {"element": 2},
                        "desc": "当前系 240%，引爆印记。目标印记≥2 层时伤害＋30%（消耗 2 充能）",
                        "cd": 3,
                        "name": "元素引爆"
                    }
,
                    # v113：吸蓝机制下放——原时咒线吸蓝流派技降为基础法师攻线 Lv.55 进阶技
                    # v130.2：黑名单违名技更名「元素湮灭」——重定位为攻线 T1 满充能全耗终极（consume_all element per 0.2）
                    "元素湮灭":                     {
                        "lv": 55,
                        "mp": 40,
                        "power": 2.4,
                        "kind": "魔法",
                        "mp_steal": 0.20,
                        "consume_all": {"key": "element", "per": 0.2},
                        "cd": 4,
                        "desc": "元素湮灭！240% 魔法伤害，消耗全部充能(每点＋20%，满 5 充能威力翻倍)，回复 20% 伤害值的魔力",
                        "name": "元素湮灭"
                    }
,
                },
                # v112.5：奥秘守线 = 奥术师（印记系）+ 秘法族（充能系）合并体，自原隐藏奥秘线降级
                "奥秘法师": {
                    "奥术弹幕": {"lv": 32, "mp": 15, "power": 0.676, "kind": "魔法",
                                 "multi": 3, "mech": "arcane", "mech_val": 1,
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 2, "mult": 1.15, "label": "蓄势待发"},
                                 "cd": 2,
                                 "desc": "奥术 110%×3，奥术充能＋1。充能≥2 层时伤害＋15%(蓄能强化)",
                                 "name": "奥术弹幕"},
                    "奥术直觉": {"lv": 38, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "arcane_regen", "mech": "arcane", "mult": 1},
                                 "desc": "触发被动：每回合开始奥术充能＋1(自动蓄能)",
                                 "name": "奥术直觉"},
                    "奥术飞弹": {"lv": 40, "mp": 15, "power": 1.0, "kind": "魔法",
                                 "mech": "arcane", "mech_val": 1, "cd": 1,
                                 "res_gain": {"element": 1},
                                 "desc": "奥术飞弹！100% 魔法伤害，命中叠 1 层奥术印记(充能 +1)",
                                 "name": "奥术飞弹"},
                    "奥术爆破": {"lv": 45, "mp": 20, "power": 1.5, "kind": "魔法",
                                 "multi": 2, "mech": "arcane", "mech_val": 2,
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 4, "mult": 1.25, "label": "共鸣输出"},
                                 "cd": 2,
                                 "res_cost": {"element": 1},
                                 "desc": "奥术 150%×2，奥术充能＋2。充能≥4 层时伤害＋25%（消耗 1 充能）",
                                 "name": "奥术爆破"},
                    "奥术脉冲": {"lv": 48, "mp": 25, "power": 1.6, "kind": "魔法",
                                 "mech": "arcane_burst", "mech_val": 0, "cd": 3,
                                 "desc": "奥术脉冲！160% 魔法伤害，引爆全部奥术印记(每层追加伤害)",
                                 "name": "奥术脉冲"},
                    "秘法护盾": {"lv": 55, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "shield_all", "cd": 4,
                                 "desc": "秘法护盾！获得 20% 魔攻护盾 3 回合(护盾强度联动)",
                                 "name": "秘法护盾"},
                    "奥术洪流": {"lv": 55, "mp": 30, "power": 1.844, "kind": "魔法",
                                 "mech": "arcane_burst",
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 5, "mult": 1.4, "label": "共鸣巅峰"},
                                 "cd": 3,
                                 "desc": "奥术 250%，消耗全部充能每层＋15%。充能≥5 层时伤害＋40%(爆发窗口)",
                                 "name": "奥术洪流"},
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
                        "mp": 25,
                        "power": 0,
                        "kind": "增益",
                        "effect": "element_shift",
                        "cd": 3,
                        "res_gain": {"element": 1},
                        "desc": "切换当前元素系(火→冰→雷)，下次元素技能伤害＋20%（充能 +1）",
                        "name": "元素跃迁"
                    }
,
                    "元素壁垒":                     {
                        "lv": 68,
                        "mp": 30,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "cd": 3,
                        "res_cost": {"element": 2},
                        "desc": "防御强化(元素法师的护盾，消耗 2 充能)",
                        "name": "元素壁垒"
                    }
,
                    # v130.2 新增：元素术士 T2 -1 高频消耗口（攻线消费阶梯 -1/-2/-3/-5 齐备）+ 补本档伤害技缺口
                    "元素迸发":                     {
                        "lv": 68,
                        "mp": 12,
                        "power": 1.5,
                        "kind": "魔法",
                        "element": "thunder",
                        "reach": 3,
                        "res_cost": {"element": 1},
                        "cd": 1,
                        "desc": "元素迸发！150% 雷系超远程小爆，消耗 1 点充能(-1 高频消耗口)",
                        "name": "元素迸发"
                    }
,
                },
                "奥秘术士": {
                    "奥术核心": {"lv": 60, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "arcane_dmg", "mult": 0.15},
                                 "desc": "被动：奥术核心，奥术系伤害＋15%",
                                 "name": "奥术核心"},
                    "奥术之心": {"lv": 60, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "arcane_dmg", "mult": 0.1},
                                 "desc": "二转被动：奥术技能伤害＋10%(奥术强化，承自秘法守线)",
                                 "name": "奥术之心"},
                    "法术反制": {"lv": 62, "mp": 15, "power": 0.6, "kind": "魔法",
                                 "mech": "arcane", "mech_val": 2, "cc": "silence",
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 2, "mult": 1.2, "label": "反制强化"},
                                 "res_gain": {"element": 1},
                                 "desc": "60% 反制，沉默敌人 + 奥术充能＋2。充能≥2 层时伤害＋20%（充能 +1）",
                                 "name": "法术反制"},
                    "法力护盾": {"lv": 68, "mp": 30, "power": 0, "kind": "增益",
                                 "effect": "def_up", "cd": 3,
                                 "res_cost": {"element": 1},
                                 "desc": "防御强化(法力护盾，消耗 1 充能)",
                                 "name": "法力护盾"},
                },
            },
            3: {
                "元素贤者": {
                    "万象风暴":                     {
                        "lv": 92,
                        "power": 1.479,
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
                        "mp": 30,
                        "aoe": "all",
                        "res_gain": {"element": 1},
                        "desc": "当前系 180%×3 全体。目标有印记时伤害＋30%（充能 +1）",
                        "cd": 3,
                        "name": "万象风暴"
                    }
,
                    "万象天雷":                     {
                        "lv": 98,
                        "mp": 120,
                        "power": 4.5,
                        "kind": "魔法",
                        "element": "thunder",
                        "team": "matk_all",
                        "cd": 5,
                        "aoe": "all",
                        "res_cost": {"element": 3},
                        "desc": "终极技，雷系 450% 全体 + 全队魔攻强化（消耗 3 充能）",
                        "name": "万象天雷"
                    }
,
                    "元素裁决":                     {
                        "lv": 90,
                        "mp": 100,
                        "power": 4.0,
                        "kind": "魔法",
                        "element": "current",
                        "cd": 6,
                        "aoe": "all",
                        "res_cost": {"element": 5},
                        "desc": "三转奥义，当前系 400% 全体核弹（消耗 5 充能）",
                        "name": "元素裁决"
                    }
,
                },
                "奥秘贤者": {
                    "奥术爆发": {"lv": 90, "mp": 40, "power": 2.2, "kind": "魔法",
                                 "mech": "arcane_burst", "mech_val": 0, "cd": 4,
                                 "desc": "奥术爆发！220% 魔法伤害，引爆全部奥术印记",
                                 "name": "奥术爆发"},
                    "奥术领域": {"lv": 90, "mp": 100, "power": 4.0, "kind": "魔法",
                                "aoe": "all", "team": "shield_all", "cd": 6,
                                "res_cost": {"element": 3},
                                "desc": "三转奥义，奥术 400% 全体 + 全队护盾（消耗 3 充能）",
                                "name": "奥术领域"},
                    "大奥术": {"lv": 92, "mp": 30, "power": 2.0, "kind": "魔法",
                               "multi": 2, "aoe": "all", "mech": "arcane", "mech_val": 2,
                               "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 6, "mult": 1.3, "label": "大奥术回响"},
                               "cd": 3,
                               "res_gain": {"element": 1},
                               "desc": "奥术 200%×2 全体，奥术充能＋2。充能≥6 层时伤害＋30%（充能 +1）",
                               "name": "大奥术"},
                    "奥术主宰": {"lv": 98, "mp": 120, "power": 4.5, "kind": "魔法",
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 5, "mult": 1.4, "label": "奥术主宰"},
                                 "cd": 5,
                                 "res_cost": {"element": 5},
                                 "desc": "终极技，奥术 450% 单体。充能≥5 层时伤害＋40%（消耗 5 充能）",
                                 "name": "奥术主宰"},
                },
            },
        },
    },
    "cls_you_xia": {
        "name": "游侠",
        "branches": {
            1: {
                # v113（鱼鱼拍板）：攻线改"林语者"自然系——狩猎印记保留 + 自然毒藤（下放）+ 植物召唤（下放）
                "林语者": {
                    "追猎":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 1.9,
                        "kind": "物理",
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.3,
                            "label": "猎杀本能"
                        },
                        "res_cost": {"energy": 20},
                        "desc": "190% 狙击，目标被标记时伤害＋30%(标记特攻)",
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
                    "藤蔓缠绕":                     {
                        "lv": 45,
                        "mp": 18,
                        "power": 0.8,
                        # v113 修复：原 kind=魔法以游侠极低 matk 结算（伤害 2-3 点近废技），
                        # 改物理以 atk 结算（battle_mech 仍叠 poison/poison_burst，机制不受影响）
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 2,
                        "cd": 2,
                        "res_cost": {"energy": 25},
                        "desc": "藤蔓缠绕！自然之力缠绕，80% 物理伤害，叠 2 层毒(自然毒藤·下放自隐藏线自然流)",
                        "name": "藤蔓缠绕"
                    }
,
                    "召唤藤蔓守卫":                     {
                        "lv": 48,
                        "mp": 20,
                        "power": 0,
                        "kind": "增益",
                        "summon": "vine_guard",
                        "cd": 3,
                        "res_cost": {"energy": 30},
                        "desc": "召唤藤蔓守卫！召唤植物伙伴加入战斗(数量流·可叠 2，自动攻击＋挡刀)",
                        "name": "召唤藤蔓守卫"
                    }
,
                    "毒爆术":                     {
                        "lv": 55,
                        "mp": 25,
                        "power": 0.6,
                        # v113 修复：原 kind=魔法以游侠极低 matk 结算近废技，改物理以 atk 结算。
                        # 毒爆引爆段(poison_burst)伤害由 battle_mech 按 matk 魔法段结算，
                        # 已由战斗层修复为按 atk，无需在本文件改动。
                        "kind": "物理",
                        "mech": "poison_burst",
                        "mech_val": 1,
                        "cd": 3,
                        "res_cost": {"energy": 35},
                        "desc": "毒爆术！自然之力引爆，60% 物理伤害，毒层≥3 引爆(每层 15% 攻击物理伤害·下放自隐藏线自然流)",
                        "name": "毒爆术"
                    }
,
                },
                "风行者": {
                    "疾风射击":                     {
                        "lv": 32,
                        "mp": 0,
                        "power": 0.951,
                        "kind": "物理",
                        "cond": {
                            "type": "speed_ratio",
                            "ratio": 1.5,
                            "mult": 1.5,
                            "label": "疾风连击"
                        },
                        "res_cost": {"energy": 20},
                        "desc": "190% 疾风射击，速度比≥1.5x 时伤害＋50%(速度压制)",
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
                        "res_cost": {"energy": 25},
                        "desc": "110%×2 双重射击。自身未受击时伤害＋15%(无伤精准)",
                        "name": "双重射击"
                    }
,
                    "风刃乱舞":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 0.629,
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
                        "res_cost": {"energy": 30},
                        "aoe": "all",
                        "desc": "130%×3 全体风刃(无视防御)，CD3。速度比≥2x 时伤害＋25%(极速压制)",
                        "name": "风刃乱舞"
                    }
,
                },
            },
            2: {
                "自然行者": {
                    "自然之眼":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "mark_dmg",
                            "mult": 0.1
                        },
                        "desc": "二转被动：对标记目标伤害＋10%(标记强化)",
                        "name": "自然之眼"
                    }
,
                    # v130.2：与基础 100 档"狩猎终章"语义区分，重命名「猎杀狂宴」+ 升格攒点/维持双用（gain 精力 +5）
                    "猎杀狂宴":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "crit_all",
                        "team": "crit_all",
                        "cd": 4,
                        "res_cost": {"energy": 30},
                        "res_gain": {"energy": 5},
                        "desc": "猎杀狂宴！全队暴击强化 3 回合 + 施放回复 5 点精力(狂宴回力，攻线叠标回精引擎)",
                        "name": "猎杀狂宴"
                    }
,
                    "剧毒之心":                     {
                        "lv": 64,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "poison_dmg",
                            "mult": 0.20
                        },
                        "desc": "被动：剧毒之心，毒系技能伤害＋20%(下放自隐藏线自然流)",
                        "name": "剧毒之心"
                    }
,
                    "穿心箭":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 1.884,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.3,
                            "label": "要害瞄准"
                        },
                        "res_cost": {"energy": 35},
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
                        "res_cost": {"energy": 30},
                        "desc": "90%×5 急速射击(高速叠印)",
                        "cd": 2,
                        "name": "急速射击"
                    }
,
                    "穿云箭":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 1.857,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "player_buffed",
                            "mult": 1.2,
                            "label": "风速"
                        },
                        "res_cost": {"energy": 30},
                        "desc": "220% 破防穿云箭。自身有增益时伤害＋20%(加速增伤)",
                        "name": "穿云箭"
                    }
,
                },
            },
            3: {
                "万木之灵": {
                    "致命连射":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.4,
                        "kind": "物理",
                        "multi": 4,
                        "res_cost": {"energy": 35},
                        "desc": "140%×4 致命连射(叠印爆发)",
                        "name": "致命连射"
                    }
,
                    "召唤古树守卫":                     {
                        "lv": 94,
                        "mp": 30,
                        "power": 0,
                        "kind": "增益",
                        "summon": "treant",
                        "effect": "atk_up",
                        "cd": 5,
                        "res_cost": {"energy": 40},
                        "desc": "召唤古树守卫！召唤古树伙伴(单只重装·挡刀率高)并攻击＋30% 3 回合",
                        "name": "召唤古树守卫"
                    }
,
                    "死神之箭":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 2.693,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.4,
                            "label": "死神注视"
                        },
                        "res_cost": {"energy": 40},
                        "desc": "终极技，450% 死神之箭，对标记目标伤害＋40%(死神注视)",
                        "cd": 3,
                        "name": "死神之箭"
                    }
,
                    "猎杀时刻":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 2.121,
                        "kind": "物理",
                        "pierce": True,
                        "cond": {
                            "type": "enemy_marked",
                            "mult": 1.3,
                            "label": "猎杀时刻"
                        },
                        "cd": 6,
                        "res_cost": {"energy": 40},
                        "desc": "三转奥义，400% 标记斩杀(单点核爆)",
                        "name": "猎杀时刻"
                    }
,
                },
                "疾风猎手": {
                    "风暴之舞":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.405,
                        "kind": "物理",
                        "multi": 4,
                        "cd": 4,
                        "res_cost": {"energy": 40},
                        "desc": "160%×4 风暴之舞(终极连射)",
                        "name": "风暴之舞"
                    }
,
                    "疾风骤雨":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 1.684,
                        "kind": "物理",
                        "multi": 3,
                        "cd": 5,
                        "res_cost": {"energy": 40},
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
                        "res_cost": {"energy": 40},
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
                "吟游诗人": {
                    "即兴弹唱": {"lv": 32, "mp": 3, "power": 1.0, "kind": "物理",
                                 "res_gain": {"echo": 1},
                                 "mech": "poison", "mech_val": 1,
                                 "desc": "即兴弹唱！100% 物理伤害，15% 概率使目标中毒(琴弦如刃)",
                                 "name": "即兴弹唱"},
                    "轻快拨弦": {"lv": 35, "mp": 3, "power": 1.1, "kind": "物理",
                                 "res_gain": {"resonance": 1, "echo": 1}, "mech": "poison", "mech_chance": 0.1,
                                 "desc": "轻快拨弦，110% 物理伤害，10% 附加中毒（共鸣 +1·回声 +1）",
                                 "name": "轻快拨弦"},
                    "战歌": {"lv": 38, "mp": 10, "power": 0, "kind": "增益",
                             "res_gain": {"echo": 1},
                             "effect": "atk_up", "team": "atk_all", "cd": 2,
                             "desc": "激昂战歌！全队攻＋30% 3 回合(副本广播，团队技能)",
                             "name": "战歌"},
                    "安眠曲": {"lv": 45, "mp": 10, "power": 0, "kind": "增益",
                               "res_gain": {"echo": 1},
                               "effect": "sleep", "cd": 3,
                               "desc": "安眠曲！使敌人陷入沉睡 2 回合（受击解除，对首领只持续 1 回合）",
                               "name": "安眠曲"},
                    # v130.2 新增：歌者签名一（v130.2 双资源·启明全队增益，消耗 3 共鸣）
                    "启明圣咏": {"lv": 50, "mp": 20, "power": 0, "kind": "增益",
                                 "res_gain": {"echo": 1},
                                 "effect": "atk_up", "team": "atk_all", "cd": 2,
                                 "res_cost": {"resonance": 3},
                                 "desc": "启明圣咏！全队攻击＋10% 3 回合（消耗 3 共鸣·回声 +1）",
                                 "name": "启明圣咏"},
                },                "神谕者": {
                    "圣言术":                     {
                        "lv": 32,
                        "power": 2.5,
                        "kind": "治疗",
                        "res_gain": 2,
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.3,
                            "mult": 1.5,
                            "label": "圣言回响"
                        },
                        "mp": 10,
                        "desc": "治疗 250%。自身 HP<30% 时治疗量＋50%(紧急救治)",
                        "cd": 2,
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
                        "mp": 20,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "cd": 2,
                        "desc": "净化术！全队防御强化，CD2(团队技能)。注：当前实现为防御强化（effect=def_up），驱散/净化战斗加成二期排期待定",
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
                        "desc": "全队治疗 300%(团队核心)",
                        "name": "大治愈术"
                    }
,
                },
            },
            2: {
                "灵魂歌者": {
                    "鼓舞": {"lv": 60, "mp": 10, "power": 0, "kind": "增益",
                             "res_gain": {"echo": 1},
                             "effect": "crit_up", "team": "crit_all", "cd": 2,
                             "desc": "鼓舞士气！全队暴击＋20% 3 回合(副本广播，团队技能)",
                             "name": "鼓舞"},
                    "哀歌": {"lv": 62, "mp": 15, "power": 1.7, "kind": "魔法",
                             "cc": "silence", "cd": 3,
                             "res_gain": {"resonance": 1, "echo": 1},
                             "desc": "哀歌！170% 魔法伤害，50% 概率沉默目标 2 回合（共鸣 +1·回声 +1）",
                             "name": "哀歌"},
                    "伴奏": {"lv": 65, "mp": 0, "power": 0, "kind": "被动",
                             "passive": {"proc": "bard_echo", "chance": 0.2},
                             "desc": "共鸣伴唱：施放歌类技能 20% 概率获得 1 层回声",
                             "name": "伴奏"},
                    "轻风咏叹": {"lv": 68, "mp": 15, "power": 0, "kind": "增益",
                                 "res_gain": {"echo": 1},
                                 "effect": "spd_up", "team": "spd_all", "cd": 2,
                                 "res_cost": {"resonance": 3},
                                 "desc": "轻风咏叹！全队速度＋40% 3 回合（消耗 3 共鸣·回声 +1）",
                                 "name": "轻风咏叹"},
                },                "大主教": {
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
                        "res_cost": {
                            "faith": 5
                        },
                        "desc": "全队护盾，CD4(持续保护)",
                        "name": "神圣庇护"
                    }
,
                },
            },
            3: {
                "黎明颂者": {
                    "英雄叙事诗": {"lv": 90, "mp": 20, "power": 1.5, "kind": "治疗",
                                   "cd": 2, "team": "heal_all",
                                   "res_gain": {"resonance": 2},
                                   "desc": "英雄叙事诗！治疗全队 150% 生命（共鸣 +2）",
                                   "name": "英雄叙事诗"},
                    "奥术咏叹调": {"lv": 92, "mp": 20, "power": 0, "kind": "增益",
                                   "res_gain": {"echo": 1},
                                   "effect": "matk_up", "team": "matk_all", "cd": 2,
                                   "res_cost": {"resonance": 3},
                                   "desc": "奥术咏叹调！魔攻＋50% 3 回合（消耗 3 共鸣·回声 +1）",
                                   "name": "奥术咏叹调"},
                    "快板节奏": {"lv": 95, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"stat": "cdr", "add": 0.08},
                                 "desc": "属性被动：快板节奏，冷却缩减＋8%",
                                 "name": "快板节奏"},
                    "终章·黎明颂歌": {"lv": 98, "mp": 35, "power": 0, "kind": "增益",
                                       "res_gain": {"echo": 2},
                                       "effect": "atk_up_strong", "team": "atk_all", "cd": 5,
                                       "res_cost": {"resonance": 5},
                                       "desc": "终章·黎明颂歌！全队攻＋75% 3 回合（消耗 5 共鸣·回声 +2）",
                                       "name": "终章·黎明颂歌"},
                    # v130.2 新增：歌者 tier3 专属攒点技（光咏晨祷，共鸣 +1）
                    "破晓圣咏": {"lv": 94, "mp": 30, "power": 1.7, "kind": "魔法",
                                 "cd": 3, "reach": 2,
                                 "res_gain": {"resonance": 1, "echo": 1},
                                 "desc": "破晓圣咏！170% 光咏魔法伤害（共鸣 +1·回声 +1）",
                                 "name": "破晓圣咏"},
                },                "圣光先知": {
                    "圣光赞歌":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 2.5,
                        "kind": "治疗",
                        "res_cost": {
                            "faith": 5
                        },
                        "team": "heal_all",
                        "desc": "全队治疗 250%(终极群奶)",
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
                        "res_cost": {
                            "faith": 10
                        },
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
                        "res_cost": {
                            "faith": 6
                        },
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
                        "power": 1.151,
                        "kind": "物理",
                        "res_gain": 1,
                        "cond": {
                            "type": "enemy_hp_high",
                            "hp_pct": 0.7,
                            "mult": 1.2,
                            "label": "暗影亲和"
                        },
                        "mp": 6,
                        "desc": "285% 影刃。目标 HP>70% 时伤害＋20%(满血刺杀)",
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
                        "power": 0.82,
                        "kind": "物理",
                        "multi": 3,
                        "res_gain": 3,
                        "cond": {
                            "type": "player_untouched",
                            "mult": 1.15,
                            "label": "身轻如燕"
                        },
                        "mp": 10,
                        "desc": "100%×3 幻影连刺。自身未受击时伤害＋15%(无伤精准)",
                        "cd": 2,
                        "name": "幻影连刺"
                    }
,
                    "终结·处刑":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 1.598,
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
                        "desc": "终结技，400% 处刑。目标 HP<40% 时伤害＋40%(斩杀)",
                        "cd": 2,
                        "name": "终结·处刑"
                    }
,
                },
                "毒刃者": {
                    "毒刃":                     {
                        "lv": 32,
                        "power": 1.387,
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
                        "mp": 6,
                        "desc": "285% 毒刃，叠 2 层毒。目标已中毒时伤害＋15%(叠毒加速)",
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
                        "mp": 10,
                        "desc": "100%×2 双毒刃，叠 3 层毒。目标毒≥3 层时伤害＋15%(深度毒伤)",
                        "name": "双毒刃"
                    }
,
                    "毒爆":                     {
                        "lv": 55,
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
                        "mp": 12,
                        "desc": "200% 毒爆，叠毒。目标毒≥5 层时伤害＋30%(满层毒爆)",
                        "cd": 2,
                        "name": "毒爆"
                    }
,
                },
            },
            2: {
                "暗影之刃": {
                    "暗影之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "stat": "shadow",
                            "mult": 0.1
                        },
                        "desc": "二转被动：影系技能伤害＋10%(影袭强化)",
                        "name": "暗影之心"
                    }
,
                    "暗影突袭":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 1.6,
                        "kind": "物理",
                        "cd": 2,
                        "res_cost": {
                            "cp": 3
                        },
                        "cond": {
                            "type": "player_untouched",
                            "mult": 1.2,
                            "label": "暗影突袭"
                        },
                        "desc": "160% 暗影突袭，CD2。自身未受击时伤害＋20%",
                        "name": "暗影突袭"
                    }
,
                    "死亡标记·影":                     {
                        "lv": 68,
                        "power": 0,
                        "kind": "增益",
                        "mech": "mark",
                        "mech_val": 2,
                        "mp": 6,
                        "desc": "标记目标，目标易伤(配合团队斩杀)",
                        "name": "死亡标记·影"
                    }
,
                    # v113：斩杀机制下放——收割(原暮影线收割流)降为基础刺客攻线 T2 进阶技
                    "收割":                     {
                        "lv": 62,
                        "mp": 25,
                        "power": 1.9,
                        "kind": "物理",
                        "cond": {
                            "type": "enemy_hp_low",
                            "hp_pct": 0.5,
                            "mult": 1.3,
                            "label": "收割"
                        },
                        "cd": 3,
                        "desc": "收割！190% 物理伤害，目标生命低于 50% 时伤害＋30%(斩杀·下放自暮影线)",
                        "name": "收割"
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
                    "毒雾·淬":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0.8,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 2,
                        "cd": 3,
                        "res_cost": {
                            "cp": 3
                        },
                        "aoe": "all",
                        "desc": "80% 毒雾(全体)，叠 2 层毒，CD3(AOE 叠毒)",
                        "name": "毒雾·淬"
                    }
,
                    "淬毒刺杀":                     {
                        "lv": 68,
                        "power": 2.0,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 4,
                        "mp": 15,
                        "desc": "200% 淬毒刺杀，叠 4 层毒(深度叠毒)",
                        "cd": 2,
                        "name": "淬毒刺杀"
                    }
,
                },
            },
            3: {
                "无影之刃": {
                    "幻影舞":                     {
                        "lv": 92,
                        "mp": 0,
                        "power": 1.0,
                        "kind": "物理",
                        "multi": 5,
                        "cd": 4,
                        "res_cost": {
                            "cp": 4
                        },
                        "desc": "100%×5 幻影舞(终极连击)",
                        "name": "幻影舞"
                    }
,
                    "终结·暗影绞杀":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 2.347,
                        "kind": "物理",
                        "res_cost": {
                            "cp": 5
                        },
                        "cd": 5,
                        "desc": "终极技，500% 暗影绞杀(终极爆发)",
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
                        "res_cost": {
                            "cp": 4
                        },
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
                        "res_cost": {
                            "cp": 4
                        },
                        "aoe": "all",
                        "desc": "150% 剧毒风暴(全体)，叠 4 层毒，CD4(群体毒爆)",
                        "name": "剧毒风暴"
                    }
,
                    "万毒噬心":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 2.604,
                        "kind": "物理",
                        "res_cost": {
                            "cp": 5
                        },
                        "mech": "poison",
                        "mech_val": 5,
                        "cd": 5,
                        "desc": "终极技，300% 万毒噬心 + 叠 5 层毒(终极毒杀)",
                        "name": "万毒噬心"
                    }
,
                    "万毒归宗":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 1.937,
                        "kind": "物理",
                        "mech": "poison",
                        "mech_val": 5,
                        "cd": 6,
                        "res_cost": {
                            "cp": 5
                        },
                        "aoe": "all",
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
                "格斗士": {
                    "疾风拳":                     {
                        "lv": 32,
                        "power": 1.728,
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
                        "mp": 6,
                        "desc": "285% 疾风拳。气≥5 时伤害＋50%(气力滚雪球)",
                        "name": "疾风拳"
                    }
,
                    "格斗术":                     {
                        "lv": 38,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "combo_dmg",
                            "mult": 0.05
                        },
                        "desc": "触发被动：连招期间伤害＋5%(连招强化)",
                        "name": "格斗术"
                    }
,
                    "旋风踢":                     {
                        "lv": 45,
                        "power": 1.3,
                        "kind": "物理",
                        "combo": "踢",
                        "res_gain": 1,
                        "cond": {
                            "type": "enemy_slowed",
                            "mult": 1.2,
                            "label": "踢击要害"
                        },
                        "mp": 8,
                        "desc": "130% 旋风踢。目标减速时伤害＋20%",
                        "name": "旋风踢"
                    }
,
                    "气力爆发":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 1.496,
                        "kind": "物理",
                        "res_cost": {
                            "chi": 5
                        },
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.4,
                            "mult": 1.3,
                            "label": "气力护体"
                        },
                        "desc": "280% 气力爆发。自身 HP<40% 时伤害＋30%(残血爆发)",
                        "name": "气力爆发"
                    }
,
                },
                "磐石行者": {
                    "铁壁拳":                     {
                        "lv": 32,
                        "power": 1.705,
                        "kind": "物理",
                        "combo": "拳",
                        "res_gain": 1,
                        "effect": "def_up",
                        "cond": {
                            "type": "player_shield",
                            "mult": 1.15,
                            "label": "铁壁连拳"
                        },
                        "mp": 6,
                        "desc": "285% 铁壁拳，防御强化。自身有护盾时伤害＋15%(护盾强化)",
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
                    "气力回涌":                     {
                        "lv": 45,
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
                        "mp": 8,
                        "desc": "治疗 200%(自愈)。自身 HP<40% 时治疗量＋50%(残血自愈)",
                        "cd": 2,
                        "name": "气力回涌"
                    }
,
                    "反震":                     {
                        "lv": 45,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "reflect",
                            "mult": 0.3,
                            "chance": 0.30
                        },
                        "desc": "触发被动：受击时 30% 概率反弹 30% 伤害(挨打反打)",
                        "name": "反震"
                    }
,
                    # v113：反击机制下放——以守为攻(原苦修线大地流)入基础拳师守线
                    "以守为攻":                     {
                        "lv": 48,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "counter_attack",
                            "chance": 0.20
                        },
                        "desc": "被动：以守为攻，受击 20% 概率立即普攻反击(下放自苦修线)",
                        "name": "以守为攻"
                    }
,
                    "磐石护壁":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "reduce_all": 0.15,   # v1.x 数值下沉：全队减伤 15%（磐石护壁）
                        "team": "reduce_all",
                        "res_cost": {
                            "chi": 3
                        },
                        "desc": "全队减伤 15% 2 回合(坦克核心)",
                        "name": "磐石护壁"
                    }
,
                },
            },
            2: {
                "拳术师": {
                    "气力之心":                     {
                        "lv": 60,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "res_gain_bonus": 1
                        },
                        "desc": "二转被动：气获取＋1(连招强化)",
                        "name": "气力之心"
                    }
,
                    "连环拳":                     {
                        "lv": 62,
                        "power": 1.1,
                        "kind": "物理",
                        "multi": 4,
                        "combo": "拳",
                        "res_gain": 4,
                        "mp": 12,
                        "desc": "110%×4 连环拳(快速攒气)",
                        "cd": 2,
                        "name": "连环拳"
                    }
,
                    "气力裂空":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 1.746,
                        "kind": "物理",
                        "pierce": True,
                        "res_cost": {
                            "chi": 4
                        },
                        "desc": "260% 破防气力裂空",
                        "name": "气力裂空"
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
                    # v113：反击机制下放——反击之王(原苦修线大地流)入基础拳师守线
                    "反击之王":                     {
                        "lv": 62,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "counter_attack",
                            "chance": 0.30
                        },
                        "desc": "被动：反击之王，受击 30% 概率立即普攻反击(下放自苦修线)",
                        "name": "反击之王"
                    }
,
                    "气力守御":                     {
                        "lv": 68,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "shield_all",
                        "team": "shield_all",
                        "res_cost": {
                            "chi": 4
                        },
                        "desc": "全队护盾 20% HP(团队盾)",
                        "name": "气力守御"
                    }
,
                },
            },
            3: {
                "破晓者": {
                    "无影连打":                     {
                        "lv": 92,
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
                        "mp": 15,
                        "desc": "130%×5 无影连打(终极连招)。气≥8 时伤害＋30%(满气终极连招)",
                        "cd": 3,
                        "name": "无影连打"
                    }
,
                    "气力天地":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 3.465,
                        "kind": "物理",
                        "res_cost": {
                            "chi": 10
                        },
                        "team": "atk_all",
                        "cd": 5,
                        "desc": "终极技，500% 气力天地 + 全队攻击强化(终极气力)",
                        "name": "气力天地"
                    }
,
                    "气力通天":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "atk_up_strong",
                        "cd": 6,
                        "res_cost": {
                            "chi": 8
                        },
                        "desc": "三转奥义，3 回合内每次攻击大幅增伤(连招极限)",
                        "name": "气力通天"
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
                    "气力万法":                     {
                        "lv": 98,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "reduce_all": 0.30,   # v1.x 数值下沉：全队减伤 30%（气力万法）
                        "team": "reduce_all",
                        "res_cost": {
                            "chi": 10
                        },
                        "cd": 5,
                        "desc": "终极技，全队减伤 30% 3 回合(终极团队技)",
                        "name": "气力万法"
                    }
,
                    "大地守护":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "reduce_all",
                        "reduce_all": 0.50,   # v1.x 数值下沉：全队减伤 50%（大地守护）
                        "team": "reduce_all",
                        "cd": 6,
                        "res_cost": {
                            "chi": 8
                        },
                        "desc": "三转奥义，全队减伤 50% 3 回合(终极坦克)",
                        "name": "大地守护"
                    }
,
                },
            },
        },
    },
    # ================= v112 隐藏线流派技能（主题线制，6 线，机制零删除） =================
    # 设计文档：design/new_world/09_职业体系.md §3/§4
    # 结构：branches[1] = 流派技能（觉醒选流派后按 skill_up 学习，传承按 lv<=level 授予），
    #       branches[2]/[3] = 各流派 T2/T3 深化技能；分支 key 用中文名（与基础职业一致）
    # 旧 13 隐藏职业技能全部保留，只改归属；秘法守线（P0-2a）并入奥秘线元素流
    "cls_dragon_oath": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「龙血」流派（真伤+灼烧），
        # 魔剑士（魔能物魔混合）与圣殿骑士（护盾格挡）流派舍弃
        "name": "龙裔誓约",
        "branches": {
            1: {
                "龙血战士": {
                    "龙息": {"lv": 40, "mp": 20, "power": 0.9, "kind": "真伤",
                             "mech": "burn", "mech_val": 1, "cd": 2,
                             "res_gain": {"dragon_might": 1},
                             "desc": "龙息！90% 真伤(无视全部防御)，附带灼烧 1 层（命中返还 龙力+1）",
                             "name": "龙息"},
                    "龙鳞": {"lv": 46, "mp": 15, "power": 0, "kind": "增益",
                             "effect": "def_up", "cd": 3,
                             "res_cost": {"dragon_might": 2},
                             "desc": "龙鳞！防御＋45% 2 回合（消耗 2 龙力）",
                             "name": "龙鳞"},
                    "龙威": {"lv": 54, "mp": 20, "power": 0, "kind": "增益",
                             "effect": "mon_atk_down", "cd": 4,
                             "res_cost": {"dragon_might": 2},
                             "desc": "龙威！敌方攻击－30% 3 回合（消耗 2 龙力）",
                             "name": "龙威"},
                },
            },
            2: {
                "龙裔斗士": {
                    # v113 修复：原 T2 分支空表，60 级升档无新技能；补 1 主动 + 1 被动（龙血主题）
                    # 主动参考龙息(真伤灼烧)同型，被动参考火之亲和(burn_amp)同型
                    "龙爪": {"lv": 64, "mp": 18, "power": 1.6, "kind": "物理",
                             "mech": "burn", "mech_val": 1, "cd": 2,
                             "res_gain": {"dragon_might": 2},
                             "desc": "龙爪！160% 物理伤害，附带灼烧 1 层（命中返还 龙力+2）",
                             "name": "龙爪"},
                    "龙脉沸腾": {"lv": 62, "mp": 0, "power": 0, "kind": "被动",
                                  "passive": {"proc": "burn_amp", "mult": 1.15},
                                  "desc": "被动：龙脉沸腾，灼烧伤害＋15%",
                                  "name": "龙脉沸腾"},
                },
            },
            3: {
                "龙魂战将": {
                    # v113：龙息之怒(真伤)下放基础战士攻线（技能书改挂 cls_zhan_shi），本线补同名机制新技
                    # v130.2：龙焰吐息 power 0.8→2.6（EQ 4.94 ✓），命中燃烧目标返还 龙力 +1
                    "龙焰吐息": {"lv": 75, "mp": 35, "power": 2.6, "kind": "真伤",
                                 "mech": "burn", "mech_val": 2, "cd": 4,
                                 "res_cost": {"dragon_might": 5},
                                 "res_gain": {"dragon_might": 1},
                                 "cond": {"type": "player_res_stacks", "res_key": "dragon_might", "stacks": 8, "mult": 1.2, "label": "龙威"},
                                 "desc": "龙焰吐息！260% 真伤(无视全部防御)，附带灼烧 2 层，消耗 5 点龙力，命中返还 1 龙力；龙力≥8 时伤害＋20%(龙威)",
                                 "name": "龙焰吐息"},
                    # v130.2 新增：满龙力大终结（v130.2f 每层 0.10 收敛：EQ ≈ 6.40 = 3.2 × 2.0）
                    "龙脉终曲": {"lv": 80, "mp": 40, "power": 3.2, "kind": "真伤",
                                 "cd": 5,
                                 "res_cost": {"dragon_might": 10},
                                 "desc": "龙脉终曲！320% 真伤，消耗 10 点龙力(满龙力终极，施放时每点龙力+10%伤害)",
                                 "name": "龙脉终曲"},
                },
            },
        },
    },
    "cls_chronomancer": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「时停」流派（时间控制），
        # 时咒线吸蓝流（原历史名含禁用字）下放基础法师攻线，血咒流（血魔法）舍弃
        "name": "时咒法师",
        "branches": {
            1: {
                "时停": {
                    "时滞术": {"lv": 40, "mp": 15, "power": 1.6, "kind": "魔法",
                               "mech": "spd_down", "mech_chance": 0.5, "cd": 1,
                               "res_gain": {"time_sand": 1},
                               "desc": "时滞术！160% 魔法伤害，50% 概率减速目标 2 回合（积沙 +1）",
                               "name": "时滞术"},
                    "时间裂隙": {"lv": 48, "mp": 20, "power": 1.3, "kind": "魔法",
                                 "multi": 2, "mech": "spd_down", "mech_chance": 0.4, "cd": 2,
                                 "res_cost": {"time_sand": 1},
                                 "desc": "时间裂隙！130%×2 魔法伤害，40% 概率减速（消耗 1 沙）",
                                 "name": "时间裂隙"},
                    "凝时锁": {"lv": 55, "mp": 20, "power": 1.4, "kind": "魔法",
                               "mech": "stun", "mech_chance": 0.35, "cd": 3,
                               "res_cost": {"time_sand": 1},
                               "desc": "凝时锁！140% 魔法伤害，35% 概率眩晕 1 回合（消耗 1 沙）",
                               "name": "凝时锁"},
                },
            },
            2: {
                "时律术士": {
                    "时间静止": {"lv": 62, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "sleep", "cd": 3,
                                 "res_gain": {"time_sand": 1},
                                 "desc": "时间静止！使目标陷入停滞 2 回合（积沙 +1）",
                                 "name": "时间静止"},
                },
            },
            3: {
                "时间领主": {
                    # v130.2f 口径注：时停领域 EQ = 3.0 × 1.3 = 3.9（单体·满沙 5/5 口径；沙漏盈满 cond 已含在倍率内，勿再乘 1.3——T13 曾误算 5.07 = 3.9×1.3；技能无 aoe 标注，不做全体折算；眩晕控场收益另计）
                    "时停领域": {"lv": 90, "mp": 100, "power": 3.0, "kind": "魔法",
                                 "mech": "stun", "mech_chance": 1.0, "cd": 6,
                                 "res_cost": {"time_sand": 3},
                                 "cond": {"type": "player_res_stacks", "res_key": "time_sand", "stacks": 5, "mult": 1.3, "label": "沙漏盈满"},
                                 "desc": "三转奥义，时停领域！300% 魔法伤害，必定眩晕 1 回合(时间停滞)，消耗 3 点时之沙；时之沙满(5)时伤害＋30%(沙漏盈满)",
                                 "name": "时停领域"},
                    # v130.2 新增：5 沙全耗终极（EQ≈4.8+控场）；命中 ≥3 目标 返还 1 沙（时间回环）
                    "时间坍缩": {"lv": 92, "mp": 100, "power": 1.5, "kind": "魔法",
                                 "aoe": "all", "mech": "stun", "mech_chance": 0.5, "reach": 3, "cd": 6,
                                 "res_cost": {"time_sand": 5},
                                 "res_gain": {"time_sand": 1},
                                 "desc": "时间坍缩！150% 全场魔法伤害，全场减速+50% 概率冻结(时停大炮)，消耗 5 沙，命中 ≥3 目标返还 1 沙",
                                 "name": "时间坍缩"},
                    # v130.2 新增：-2 沙保命口（解除减速/刷新技能 cd）
                    "时光回溯": {"lv": 95, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "cleanse", "cd": 4, "reach": 1,
                                 "res_cost": {"time_sand": 2},
                                 "desc": "时光回溯！解除自身减速并刷新自身技能冷却（消耗 2 沙）",
                                 "name": "时光回溯"},
                },
            },
        },
    },
    "cls_wild_hunter": {
        # v113（鱼鱼拍板）：隐藏线更名"星语者"——只留星运流（占星/命运），
        # 自然流（毒藤/毒爆）与兽群流（召唤进化）机制下放基础游侠攻线（林语者）
        "name": "星语者",
        "branches": {
            1: {
                "星语者": {
                    "星陨": {"lv": 40, "mp": 15, "power": 1.65, "kind": "物理",
                             "mech": "mark", "mech_val": 1, "cd": 2,
                             "res_gain": {"hunt_mark": 1},
                             "desc": "星陨！165% 物理伤害，叠 1 层猎杀标记（命中攒印 +1）",
                             "name": "星陨"},
                    "占卜": {"lv": 46, "mp": 15, "power": 0, "kind": "增益",
                             "effect": "crit_up", "cd": 3,
                             "desc": "占卜！暴击＋20% 3 回合",
                             "name": "占卜"},
                    # v130.2：命运之轮 定为 T1 教学档消耗（-1 印）+ power 微调
                    "命运之轮": {"lv": 55, "mp": 30, "power": 1.6, "kind": "魔法",
                                 "multi": 3, "cd": 4,
                                 "res_cost": {"hunt_mark": 1},
                                 "desc": "命运之轮！160% 魔法伤害连击 3 次（消耗 1 印）",
                                 "name": "命运之轮"},
                },
            },
            2: {
                "星相师": {
                    "星辰之力": {"lv": 62, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"stat": "luck", "add": 0.05},
                                 "desc": "被动：星辰之力，幸运＋5%",
                                 "name": "星辰之力"},
                    # v130.2 新增：T2 攒印加速口（与星陨双攒，把 5 印攒满压到 ~2 回合）
                    "星轨连射": {"lv": 64, "mp": 15, "power": 1.2, "kind": "物理",
                                 "multi": 2, "mech": "mark", "mech_val": 1, "cd": 2,
                                 "res_gain": {"hunt_mark": 1},
                                 "desc": "星轨连射！120%×2 物理伤害，叠 1 层猎杀标记（命中攒印 +1）",
                                 "name": "星轨连射"},
                },
            },
            3: {
                "命运编织者": {
                    "星祭": {"lv": 75, "mp": 35, "power": 2.0, "kind": "物理",
                             "mech": "mark", "mech_val": 2, "cd": 4,
                             "res_cost": {"hunt_mark": 3},
                             "desc": "星祭！200% 物理伤害，叠 2 层猎杀标记，消耗 3 点猎印",
                             "name": "星祭"},
                    # v130.2 新增：大终结前奏（+2 印 + 满印暴击抬升）
                    "星辉祈愿": {"lv": 78, "mp": 25, "power": 0, "kind": "增益",
                                 "effect": "crit_up", "cd": 5,
                                 "res_gain": {"hunt_mark": 2},
                                 "desc": "星辉祈愿！暴击率＋20% 3 回合，施放 猎印 +2（大终结前奏）",
                                 "name": "星辉祈愿"},
                    # v130.2 新增：5 印大终结·EQ≈4.8（满印 cond ×1.15；通用标记易伤每层＋20% 叠加）
                    "流星陨落": {"lv": 80, "mp": 40, "power": 3.2, "kind": "物理",
                                 "pierce": True, "reach": 3, "cd": 6,
                                 "res_cost": {"hunt_mark": 5},
                                 "cond": {"type": "player_res_stacks", "res_key": "hunt_mark", "stacks": 5, "mult": 1.15, "label": "流星盈满"},
                                 "desc": "流星陨落！320% 致命一击，消耗 5 点猎印；目标带标记时受标记易伤(每层＋20%)，满印(5/5)施放时伤害＋15%(流星盈满)",
                                 "name": "流星陨落"},
                },
            },
        },
    },
    "cls_hymn": {
        # v112.1：圣歌流派拆出为独立中立线（cls_bard 吟游诗人），本线改名暗影神谕（单流派）
        "name": "暗影神谕",
        "branches": {
            1: {
                "暗影祭司": {
                    "召唤骷髅": {"lv": 40, "mp": 20, "power": 0, "kind": "增益",
                                 "summon": "skeleton", "cd": 3,
                                 "res_cost": {"canticle": 2},
                                 "desc": "召唤骷髅！召唤骷髅兵加入战斗(上限 3，自动攻击＋挡刀)，消耗 2 点悼咏",
                                 "name": "召唤骷髅"},
                    "亡灵狂暴": {"lv": 48, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "atk_up", "cd": 3,
                                 "desc": "亡灵狂暴！攻击＋30% 3 回合",
                                 "name": "亡灵狂暴"},
                    # v130.2 新增：暗蚀攒点技（转职第一秒即攒悼咏）
                    "死亡汲取": {"lv": 44, "mp": 15, "power": 1.2, "kind": "魔法",
                                 "lifesteal": 0.5, "cd": 2, "reach": 2,
                                 "res_gain": {"canticle": 1},
                                 "desc": "死亡汲取！120% 暗蚀伤害，吸血回复等于伤害一半（攒悼咏 +1）",
                                 "name": "死亡汲取"},
                },
            },
            2: {
                "亡魂引渡者": {
                    "死亡契约": {"lv": 62, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "death_pact"},
                                 "desc": "被动：死亡契约，致命伤害由召唤物代受(以 20% 生命存活，每场 1 次)",
                                 "name": "死亡契约"},
                    # v130.2 新增：一档神迹·铺场（T2 中消耗口）
                    "墓穴低语": {"lv": 64, "mp": 20, "power": 0.8, "kind": "魔法",
                                 "aoe": "all", "summon": "skeleton", "cd": 3, "reach": 2,
                                 "res_cost": {"canticle": 3},
                                 "desc": "墓穴低语！80% 全体暗蚀 + 召唤 1 只骷髅，消耗 3 点悼咏",
                                 "name": "墓穴低语"},
                },
            },
            3: {
                "黯灵主教": {
                    "骷髅海": {"lv": 70, "mp": 30, "power": 0, "kind": "增益",
                               "summon": "skeleton", "effect": "atk_up", "cd": 5,
                               "res_cost": {"canticle": 5},
                               "desc": "骷髅海！召唤骷髅兵并攻击＋30% 3 回合，消耗 5 点悼咏",
                               "name": "骷髅海"},
                    # v130.2 新增：二档中消耗·吃掉亡灵换暗蚀潮
                    "献祭暗焰": {"lv": 76, "mp": 30, "power": 1.3, "kind": "魔法",
                                 "aoe": "all", "cd": 4, "reach": 2,
                                 "res_cost": {"canticle": 5},
                                 "desc": "献祭暗焰！130% 全体魔法伤害，消耗场上 1 只骷髅追加一次 60% 全体暗蚀，消耗 5 点悼咏",
                                 "name": "献祭暗焰"},
                    # v130.2 新增：三档满档挽歌大终结（EQ = 3.0 全体 ×1.6 ≈ 4.8）
                    "安魂曲": {"lv": 80, "mp": 40, "power": 3.0, "kind": "魔法",
                               "aoe": "all", "cd": 6, "reach": 2,
                               "res_cost": {"canticle": 10},
                               "desc": "安魂曲！300% 全体暗蚀，结算以伤害值一半回复自身，消耗 10 点悼咏（满档挽歌）",
                               "name": "安魂曲"},
                },
            },
        },
    },
    "cls_shadow_blade": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「暗杀」流派（影步+潜行爆发），
        # 收割流派（残血追猎/收割）机制下放基础刺客攻线
        "name": "暮影行者",
        "branches": {
            1: {
                "暗杀": {
                    "幽影袭": {"lv": 40, "mp": 15, "power": 1.3, "kind": "物理",
                               "mech": "shadow", "mech_val": 1, "cd": 2,
                               "res_gain": {"shadow_step": 1},
                               "desc": "幽影袭！130% 物理伤害，满血目标必暴击（暴击命中 +1 影步）",
                               "name": "幽影袭"},
                    "暗影步": {"lv": 52, "mp": 20, "power": 0, "kind": "增益",
                               "effect": "stealth", "cd": 4,
                               "res_cost": {"shadow_step": 1},
                               "desc": "暗影步！花 1 步潜入暗影(潜行)，下次攻击必定暴击",
                               "name": "暗影步"},
                },
            },
            2: {
                "暮刃大师": {
                    "幽影连刺": {"lv": 62, "mp": 25, "power": 1.2, "kind": "物理",
                                 "multi": 2, "mech": "shadow", "mech_val": 1, "cd": 2,
                                 "res_gain": {"shadow_step": 1},
                                 "desc": "幽影连刺！120%×2 物理伤害，满血目标必暴击（2 段全暴击积步 +2）",
                                 "name": "幽影连刺"},
                },
            },
            3: {
                "暮影收割者": {
                    "幽影刃": {"lv": 75, "mp": 35, "power": 2.0, "kind": "物理",
                               "mech": "shadow", "mech_val": 1, "cd": 4,
                               "res_cost": {"shadow_step": 3},
                               "desc": "幽影刃！200% 物理伤害，满血目标必暴击，消耗 3 点影步(潜行下 ×1.25)",
                               "name": "幽影刃"},
                    # v130.2 新增：影步 4 步大终结（EQ = 3.2 × 1.5 = 4.8；暗影步 1 + 终结 4 = 5 = 影步上限，潜行伏击连招可达成）
                    "终结·破影一击": {"lv": 80, "mp": 45, "power": 3.2, "kind": "物理",
                                 "mech": "shadow", "mech_val": 1, "cd": 6, "reach": 1,
                                 "res_cost": {"shadow_step": 4},
                                 "desc": "终结·破影一击！320% 致命一击，潜行伏击：潜行出招伤害×1.5，消耗 4 点影步",
                                 "name": "终结·破影一击"},
                },
            },
        },
    },
    "cls_wu_sheng": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「武僧」流派（禅意+连击），
        # 大地流派（以守为攻/反击之王）机制下放基础拳师守线
        # v130.2（拍板）：档位展示名 苦修士→淬势者；下方 branches 分支 key（武僧/大地武僧/撼岳者）
        #   与 classes.py evolve_branches 强耦合（技能授予/路由按 key 匹配），为技能键绝不动
        "name": "淬势者",
        "branches": {
            1: {
                "武僧": {
                    "裂岩冲": {"lv": 40, "mp": 12, "power": 1.3, "kind": "物理",
                               "mech": "chi", "mech_val": 1, "cd": 1,
                               "res_gain": {"zen": 1},
                               "desc": "裂岩冲！130% 物理伤害，命中叠加 1 层气力(每层伤害＋12%)（命中 +1 禅意）",
                               "name": "裂岩冲"},
                    # v130.2 更名（气力连打→蓄劲连打）+ 挂禅意攒点
                    "蓄劲连打": {"lv": 55, "mp": 20, "power": 1.4, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_gain": {"zen": 1},
                                 "desc": "蓄劲连打！140% 物理伤害，拳连招(拳-踢-掌三连追加)（禅意 +1）",
                                 "name": "蓄劲连打"},
                    # v130.2 新增：T1 主轴（-3 禅意·EQ≈4.65）
                    "裂岳连击": {"lv": 48, "mp": 10, "power": 1.9, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_cost": {"zen": 3},
                                 "desc": "裂岳连击！190% 物理伤害，每 zen 物理威力 +12%，消耗 3 点禅意",
                                 "name": "裂岳连击"},
                    # v130.2 新增：换气攒点技（转进隐藏线第一回合即摸到 zen）
                    "苦行呼吸": {"lv": 42, "mp": 5, "power": 0, "kind": "增益",
                                 "effect": "def_up", "cd": 2,
                                 "res_gain": {"zen": 1},
                                 "desc": "苦行呼吸！防御强化（蓄势换气，禅意 +1）",
                                 "name": "苦行呼吸"},
                },
            },
            2: {
                "大地武僧": {
                    # v113：反击机制下放基础拳师守线后，本档补连击深化技
                    # v130.2 更名（禅意连打→势蓄连打）+ 挂禅意攒点
                    "势蓄连打": {"lv": 62, "mp": 18, "power": 1.2, "kind": "物理",
                                 "combo": "拳", "multi": 2, "cd": 2,
                                 "res_gain": {"zen": 1},
                                 "desc": "势蓄连打！120%×2 物理伤害，拳连招(连击深化)（禅意 +1）",
                                 "name": "势蓄连打"},
                    # v130.2 新增：2 禅意轻倾泻（慢热期小口释放）
                    "律动连打": {"lv": 66, "mp": 14, "power": 1.8, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_cost": {"zen": 2},
                                 "desc": "律动连打！180% 物理伤害（每 zen 物理威力 +12%，消耗 2 点禅意）",
                                 "name": "律动连打"},
                },
            },
            3: {
                "撼岳者": {
                    "气爆": {"lv": 75, "mp": 35, "power": 1.8, "kind": "物理",
                             "mech": "chi_burst", "mech_val": 0, "cd": 4,
                             "res_cost": {"zen": 5},
                             "desc": "气爆！180% 物理伤害，引爆全部气力(每层追加＋15%伤害)，消耗 5 点禅意",
                             "name": "气爆"},
                    # v130.2 新增：满 10 禅意大终结（实算 EQ≈5.50 = 2.5 × 2.2，无破势 ×1.1）
                    "撼岳·终焉": {"lv": 80, "mp": 30, "power": 2.5, "kind": "物理",
                                  "combo": "拳", "cd": 6,
                                  "res_cost": {"zen": 10},
                                  "desc": "撼岳·终焉！250% 致命一击，每 zen 物理威力 +12%，消耗 10 点禅意",
                                  "name": "撼岳·终焉"},
                    # v130.2 新增：T3 续势攒点（禅意 +2）
                    "裂岳绝式": {"lv": 82, "mp": 16, "power": 1.3, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_gain": {"zen": 2},
                                 "desc": "裂岳绝式！130% 物理伤害（禅意 +2）",
                                 "name": "裂岳绝式"},
                },
            },
        },
    },
}

# ================= v112 隐藏线基础技能（线级被动，觉醒即得） =================
# 设计文档：design/new_world/09_职业体系.md §3 —— 每条线 1 主题 1 核心资源 1 线级被动
# 传承/升档按 lv<=level 授予（见 commands/player.py _evolve_hidden_generic）
# 注：猎手本能/暗影之舞/气力调和复用基础职业同名被动（同 ID 共享，技能名唯一铁律不破）
_ADD_HIDDEN_SKILLS = {
    "cls_dragon_oath": {
        "skills": {
            "sk_long_hun": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "elem_res", "add": 0.05},
                "desc": "被动：龙魂，元素抗性＋5%（龙裔线觉醒即得）",
                "name": "龙魂",
            },
            "sk_huo_zhi_qin_he": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"proc": "burn_amp", "mult": 1.2},
                "desc": "被动：火之亲和，灼烧伤害＋20%（龙裔线觉醒即得）",
                "name": "火之亲和",
            },
        },
    },
    "cls_chronomancer": {
        "skills": {
            # v112.5：时咒线级基础——魔力贯穿（承自原奥秘线）+ 时间感知（新）
            "sk_mo_li_guan_chuan": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"proc": "attack_res", "res": "time_sand", "gain": 1},
                "desc": "触发被动：攻击命中时时间之沙+1（时咒线觉醒即得，时间节拍加速）",
                "name": "魔力贯穿",
            },
            "sk_shi_jian_gan_zhi": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "cdr", "add": 0.05},
                "desc": "属性被动：时间感知，冷却缩减＋5%（时咒线觉醒即得）",
                "name": "时间感知",
            },
        },
    },
    "cls_wild_hunter": {
        "skills": {
            "sk_p_lie_shou_ben_neng": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "crit_mark", "mult": 0.1},
                "desc": "属性被动：对标记目标暴击＋10%（星语线觉醒即得）",
                "name": "猎手本能",
            },
        },
    },
    "cls_hymn": {
        "skills": {
            # v112.1：诗人拆为独立中立线后，暗影神谕线级基础 = 墓穴护甲（觉醒即得）
            "sk_mu_xue_hu_jia": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05, "res_gain": 1},
                "desc": "被动：墓穴护甲，受击减伤5%，受击时悼咏+1（暗影神谕线觉醒即得）",
                "name": "墓穴护甲",
            },
        },
    },
    "cls_shadow_blade": {
        "skills": {
            "sk_p_an_ying_zhi_wu": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "stealth_crit_dmg", "mult": 0.3},
                "desc": "属性被动：潜行状态暴击伤害＋30%（暮影线觉醒即得）",
                "name": "暗影之舞",
            },
        },
    },
    "cls_wu_sheng": {
        "skills": {
            "sk_p_qi_xi_tiao_he": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"proc": "turn_heal", "pct": 0.02},
                "desc": "触发被动：每回合回复2%生命（苦修线觉醒即得）",
                "name": "气力调和",
            },
        },
    },
}
PLAYER_SKILLS.update(_ADD_HIDDEN_SKILLS)

# v95.23 职业导师进阶技能：各城导师专属，普通『技能学习』学不到，需找导师对话学习
# 格式与 PLAYER_SKILLS 技能一致（battle/engine 按名字查定义）
TUTOR_SKILLS = {
    "cls_zhan_shi": {
    },
    "cls_fa_shi": {
        "sk_mo_li_mai_chong": {
            "lv": 6, "mp": 10, "power": 1.7, "kind": "魔法",
            "mech": "arcane", "cd": 2,
            "desc": "魔力脉冲！170% 魔法伤害，奥术之力涌动",
            "name": "魔力脉冲",
        },
    },
    "cls_you_xia": {
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
            "desc": "裂骨击！160% 物理伤害，20% 概率击晕目标",
            "name": "裂骨击",
        },
        "sk_jin_gang_ti": {
            "lv": 10, "mp": 12, "power": 0, "kind": "增益",
            "effect": "def_up", "cd": 3,
            "desc": "磐石之体！如磐石般挺立，防御＋45% 2 回合",
            "name": "磐石之体",
        },
    },
}
