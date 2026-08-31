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
                "desc": "长剑划出利落的弧光——造成 100% 物理伤害；若你的速度高于目标，先发剑势更盛(伤害＋15%)",
                "name": "挥砍",
            },
    "sk_meng_ji": {
                "lv": 2,
                "mp": 4,
                "power": 1.2,
                "kind": "物理",
                "res_gain": 1,
                "desc": "双臂蓄满蛮力猛然砸下——造成 120% 物理伤害",
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
                "desc": "剑锋劈入甲胄缝隙，无视防御造成 130% 物理伤害；自身生命低于 40% 时绝境反扑(伤害＋20%)",
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
                "desc": "身形旋起如风暴，横扫前排造成 110% 全体物理伤害；目标生命高于 70% 时威力暴涨(伤害＋40%)",
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
                "desc": "重剑砸裂大地，无视防御造成 180% 物理伤害；怒气蓄满 8 点时怒意喷薄(伤害＋50%)",
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
                "desc": "屏息沉肩，将全身力量注入剑锋——蓄力 1 回合(受击会打断)，挥出 220% 破防一击",
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
                "desc": "胸腔炸开一声战吼，战意点燃血液——攻击＋30% 持续 3 回合；组队时战意传染全队(全队攻击＋30%)",
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
                "desc": "举盾凝立如城墙——防御＋45% 持续 3 回合",
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
                "desc": "收剑凝神，斗气在筋脉中翻涌——攻击＋30% 持续 3 回合，为终结技蓄足锋芒",
                "name": "蓄势",
            },
    "sk_dun_ji": {
                "lv": 17,
                "mp": 6,
                "power": 1.3,
                "kind": "物理",
                "cd": 3,
                "cc": "stun",
                "desc": "重盾悍然撞出——造成 130% 伤害，35% 概率震晕目标 1 回合(CD 3)",
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
                "desc": "铁靴重重踏裂地面，震波席卷前排造成 80% 全体伤害；目标被冻结或减速时冲击更烈(伤害＋40%)",
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
                "desc": "将满腔怒意化作一往无前的冲锋——消耗全部怒气，每点怒气＋12% 伤害(满怒可至 220% 威力)",
                "name": "无畏冲击",
            },
    "sk_p_zhan_yi": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "atk", "cond": "rage>=5", "mult": 0.15},
                "desc": "战意随怒气沸腾——怒气达到 5 点时攻击＋15%",
                "name": "战意高涨",
            },
    "sk_p_tie_bi_zhi_xin": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05},
                "desc": "铠甲与意志凝为一体——受到伤害时减伤 5%",
                "name": "铁壁之心",
            },
    # v112 一转觉醒被动（Lv.30）：基础职业与隐藏线线级被动对齐的仪式感节点
    "sk_p_gang_tie_bi_lei": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "def", "cond": "hp_high_70", "mult": 0.10},
                "desc": "气血充盈时防线如铁铸——生命高于 70% 时防御＋10%",
                "name": "钢铁壁垒",
            },
    "sk_p_po_jia_ben_neng": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "pierce", "mult": 1.1},
                "desc": "久经沙场的本能——破防类技能伤害＋10%",
                "name": "破甲本能",
            },
    "sk_p_zhan_zheng_pa_xiao": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "res_gain_bonus"},
                "desc": "每一声怒吼都在积累战意——攻击命中时额外获得 1 点怒气",
                "name": "战争咆哮",
            },
    "sk_p_p...tong": {
                "lv": 45,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "pene_phys", "add": 0.05},
                "desc": "熟知每一处甲胄的薄弱——物理穿透＋5%(无视物理防御，v106.2 职业特色渠道)",
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
                "desc": "将游离的火元素凝成灼热弹丸掷出，命中即焚(100% 火系伤害)；目标已带灼烧时火焰燎原(伤害＋20%)",
                "name": "火球术",
            },
    "sk_bing_jing": {
                "lv": 2,
                "mp": 8,
                "power": 1.05,
                "kind": "魔法",
                "element": "ice",
                "desc": "指尖凝出剔透冰晶掷向敌人，寒气透骨——造成 105% 冰系魔法伤害",
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
                "desc": "召唤尖锐冰锥破空直刺，造成 110% 冰系伤害并减速 1 回合；目标已被冻结时寒霜更烈(伤害＋30%)",
                "name": "冰锥",
            },
    "sk_lei_ji": {
                "lv": 14,
                "mp": 20,
                "power": 1.046,
                "kind": "魔法",
                "element": "thunder",
                "cond": {"type": "player_first", "mult": 1.15, "label": "雷系爆发"},
                "desc": "电弧在指尖跳跃，化作惊雷劈落——造成 120% 雷系伤害；先手(速度高于目标)时电弧暴涨(伤害＋15%)",
                "name": "雷击",
            },
    "sk_yuan_su_bao_fa": {
                "lv": 20,
                "mp": 30,
                "power": 1.6,
                "kind": "魔法",
                "element": "current",
                "desc": "调动周身元素之力倾泻而出——造成 160% 当前系伤害，蓝量倾泻、直伤爆发",
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
                "desc": "让元素在脉络中流转不息——魔攻＋50% 持续 3 回合；组队时元素之力流向全队（全队魔攻强化）",
                "name": "元素流转",
            },
    "sk_yuan_su_dan_mu": {
                "lv": 6,
                "mp": 12,
                "power": 0.842,
                "kind": "魔法",
                "multi": 2,
                "desc": "连珠般掷出两枚元素弹丸——造成 100%×2 当前系伤害（共 200%），低耗填充输出",
                "name": "元素弹幕",
            },
    "sk_yuan_su_hu_dun": {
                "lv": 11,
                "mp": 20,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "desc": "以元素之力在周身凝成护盾——防御＋45% 持续 3 回合（CD 3）",
                "name": "元素护盾",
            },
    "sk_ao_shu_qiang_hua": {
                "lv": 17,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "desc": "吟唱奥术咒文强化自身——魔攻＋50% 持续 3 回合，为爆发蓄势（CD 3）",
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
                "desc": "冰霜以自身为圆心炸裂扩散——造成 80% 全体冰系伤害，30% 概率冻结目标 1 回合（强控·群体，CD 3）",
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
                "desc": "唤起元素风暴席卷全场——造成 200% 当前系全体伤害；目标带有元素印记时风暴过载（伤害＋50%）；转职后可借元素架设强化(魔法技能伤害＋40%)",
                "name": "元素风暴"
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
                # v139 架设保护：架设中蓄力不会被打断（充能 -1 代替）；已转职法师打断时充能 -1 + 50% MP 返还并存
                "focus_charge_protect": True,
                "desc": "引燃天际火云召唤陨石——蓄力 2 回合（受击会打断，元素架设中不会被打断、改充能-1），陨石坠落后轰击全场，造成 300% 火系范围伤害（可及全阵后排）",
                "name": "陨石术"
            },
    "sk_fa_shu_fan_zhi": {
                "lv": 16,
                "mp": 15,
                "power": 0.3,
                "kind": "魔法",
                "element": "current",
                "cd": 3,
                "interrupt": True,
                "desc": "以法术禁制攫住敌手的吟唱——造成 30% 微量魔法伤害，命中即打断目标蓄力（可打断读条技能）",
                "name": "法术禁制",
            },
    "sk_p_lie_yan_qin_he": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "fire_bonus", "mult": 0.10},
                "desc": "与火元素心意相通，施放火系技能时伤害＋10%(被动)",
                "name": "烈焰亲和",
            },
    "sk_p_han_shuang_qin_he": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "ice_slow"},
                "desc": "寒气随施法悄然蔓延，冰系技能命中附带减速(被动)",
                "name": "寒霜亲和",
            },
    "sk_p_mo_li_peng_pai": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "matk", "cond": "hp_high_70", "mult": 0.08},
                "desc": "生命高于 70% 时魔力澎湃涌动，魔攻＋8%(被动)",
                "name": "魔力澎湃",
            },
    "sk_p_mo_li_yong_dong": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "mp", "mult": 0.15},
                "desc": "魔力源泉深不见底，最大魔力＋15%(被动)",
                "name": "魔力涌动",
            },
    "sk_p_yuan_su_gong_ming": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "reaction", "mult": 1.15},
                "desc": "元素之力彼此应和，元素系技能伤害＋15%(被动)",
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
                # v139 屏息窗口联动：屏息窗口内 2 段 → 3 段（低耗档 ≤25 判定内）
                "breathe_seg_bonus": 1,
                "desc": "弓弦颤动如风吟，两箭连珠破空而出——连续射击 2 次，每次造成 60% 物理伤害；凝神屏息窗口内段数＋1(3 段)",
                "name": "疾风连射",
            },
    "sk_miao_zhun": {
                "lv": 2,
                "mp": 0,
                "res_cost": {"energy": 10},
                "power": 1.4,
                "kind": "物理",
                "desc": "凝神屏息，将呼吸与弓弦调成同频——蓄势一箭造成 140% 物理伤害",
                "name": "瞄准射击",
            },
    "sk_zhi_ming_ju_ji": {
                "lv": 8,
                "mp": 0,
                "power": 1.357,
                "kind": "物理",
                "res_cost": {"energy": 35},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.4, "mult": 1.5, "label": "绝境之眼"},
                "desc": "鹰瞳锁定猎物最后一口气，箭矢循着死亡轨迹射出——造成 180% 物理伤害；目标生命低于 40% 时，绝境之眼睁开（伤害＋50%）",
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
                "desc": "在林间暗处布下缠着火绒的猎网，猎物踏入即燃——造成 120% 物理伤害并附加 2 层灼烧（烈火噬身，延时迸发）",
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
                # v139 屏息窗口联动：屏息窗口内标记 1 层 → 2 层
                "breathe_mark_extra": 1,
                "desc": "吟诵林间古语，箭矢裹挟自然之力烙印猎物——造成 150% 自然伤害并施加猎杀标记，命中时汲取 10 点精力（自然印记·标记核心）；凝神屏息窗口内标记叠 2 层",
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
                "desc": "瞳中映出鹰隼的金芒，猎物的一切破绽无所遁形——暴击率＋20%，持续 3 回合",
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
                # v139 机动泄压：施放当回合精力 -15（位移从成本变收益，快排语义）
                "vent_energy": 15,
                "desc": "风元素缠绕足踝，身形化作林间掠影——速度＋40%，持续 3 回合（机动）；施放当回合精力-15(机动泄压)",
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
                "desc": "箭簇浸过幽绿毒液，破空时带起一缕腥风——造成 80% 物理伤害并附加 3 层中毒（消耗 20 精力）",
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
                # v139 泄压阀载体之一：效果期间成功闪避精力 -15
                "vent_on_dodge": 15,
                "desc": "扯下林地与暮色织成的帷幕披在身上，身形与草木融为一体——闪避率＋40%，持续 3 回合（隐形求生）；效果期间成功闪避精力-15(泄压阀)",
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
                "desc": "胸腔中炸开一声猎者的咆哮，热血与战意一同沸腾——攻击＋30%，持续 3 回合（标记爆发前奏）",
                "name": "狩猎咆哮",
            },
    "sk_shou_lie_zhong_zhang": {
                "lv": 30,
                "mp": 0,
                "power": 1.78,
                "kind": "物理",
                "res_cost": {"energy": 100},
                # v130.2：100 档终极奥义「狩猎终章」纯伤害（EQ 锚定铁律 2）；去叠毒引爆条件（叠标/引爆归攻线林语者）
                # v133 峰值红线收敛：power 1.78（L30 裸装峰值 40.9% ≤42% 红线，100 精力大终结 vs 瞄准射击 10 精力 29.2%）
                # v139 校准尝试 2.20（P0 DPR 修复）→ 实测裸装暴击峰值 53.2% 超红线 → 回退 1.78（去 mark_burst 后峰值 40.9%）
                # v139 红线收敛：去掉 mark_burst（引爆标记），保持纯伤害定位（峰值 40.9%≤42% 红线；标记连招专属攻线林语者引爆技）
                "desc": "倾尽周身精力拉开满月之弓，射出终结猎物的最后一箭——造成 178% 致命一击，消耗全部精力（100 精力大终结）",
                "name": "狩猎终章"
            },
    "sk_xu_li_ju_ji": {
                "lv": 26,
                "mp": 0,
                "power": 1.4,
                "kind": "物理",
                "pierce": True,
                "res_cost": {"energy": 50},
                "cd": 4,
                # v139 电荷制蓄力（云海弓手三律翻译）：charge 0-3 电荷池——「蓄力」动作耗 10 精力、电荷+1 并立即出伤 0.7/1.3/1.9；受击电荷 -1 不清零；电荷=3 强制释放狙击
                "charge": 0,
                "charge_mode": "ranger_charge",
                "charge_cfg": {
                    "max": 3,
                    "charge_cost": 10,
                    "m_base": 0.7,
                    "m_step": 0.6,
                    "snipe_m_base": 0.7,
                    "interrupt_loss": 1,
                    "full_force": True,
                    "snipe_min": 1,
                    "snipe_reach": 3
                },
                "reach": 3,
                # v139 狙击指定层：可指定 rank=3 后排目标（无视站位射程判定）；对后排目标伤害 ×1.2
                "snipe_backrank": {"mult": 1.2},
                "desc": "电荷制蓄力狙击——「蓄力」动作(耗 10 精力)电荷+1 并立即出伤 0.7/1.3/1.9；受击电荷-1不清零；电荷=3 强制释放狙击(M 2.8、破防、reach3、可指定后排)",
                "name": "蓄力狙击"
            },
    "sk_p_lie_shou_ben_neng": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "crit_mark", "mult": 0.1},
                "desc": "猎手对猎物的直觉，让每一次出手都直指要害——对带标记目标暴击＋10%（星语者觉醒即得，被动）",
                "name": "猎手本能",
            },
    "sk_p_feng_xing_bu": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "spd", "mult": 0.08},
                "desc": "踏风而行，步履轻如鸿羽——速度＋8%（被动）",
                "name": "风行步",
            },
    "sk_p_ji_feng_zhi_yan": {
                "lv": 32,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                # v134.1 意见#45：速度→暴击（疾风之眼）——每点速度 +0.1% 暴击（10点速度+1%）
                "passive": {"stat": "spd_crit", "mult": 0.1},
                "desc": "疾风入眼，万物皆慢——每 10 点速度转化为 1% 暴击率（被动）",
                "name": "疾风之眼",
            },
    "sk_p_feng_zhi_jia_hu": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "dodge", "mult": 0.05},
                "desc": "林风环绕周身，为猎者拂开袭来的利刃——闪避率＋5%（一转觉醒·风之加护，被动）",
                "name": "风之加护",
            },
    "sk_p_ying_yan": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "mark_extra", "chance": 0.15},
                "desc": "鹰之眼俯瞰战场，猎物身上多出一道道无形准星——攻击时 15% 概率额外叠加 1 层印记（与追踪印记叠加，被动）",
                "name": "鹰眼",
            },
    "sk_p_zhui_zong_yin_ji": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "mark_extra", "chance": 0.3},
                "desc": "箭矢与猎物之间仿佛牵起无形的线，越缠越紧——攻击时 30% 概率额外叠加 1 层印记（被动）",
                "name": "追踪印记",
            },
    "sk_p_c...jian": {
                "lv": 48,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "pene_phys", "add": 0.05},
                "desc": "箭簇打磨得足以撕裂重甲与龙鳞——物理穿透＋5%，无视目标部分物理防御（被动）",
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
                "desc": "凝圣光为弹丸疾射而出——造成 100% 圣光伤害；自身生命高于 70% 时，光之祝福加持（伤害＋20%）",
                "name": "圣光弹",
            },
    "sk_sheng_guang": {
                "lv": 2,
                "mp": 8,
                "power": 1.15,
                "kind": "魔法",
                "res_gain": 1,
                "desc": "圣光凝聚成束贯穿敌人，造成 115% 圣光伤害",
                "name": "圣光术",
            },
    "sk_zhi_yu_shu": {
                "lv": 8,
                "mp": 15,
                "power": 2.0,
                "kind": "治疗",
                # v130.2 治疗系 per-skill gain 归零（攒点走全局 on_heal +2，防双计数）
                "cond": {"type": "player_hp_low", "hp_pct": 0.3, "mult": 1.5, "label": "治愈之光"},
                "desc": "引导圣光抚慰伤口——治疗 200% 生命；自身生命低于 30% 时圣光愈发炽烈（治疗量＋50%，紧急救治）",
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
        "desc": "圣光化作鞭挞落下，造成 120% 圣光伤害，命中积攒 1 点信仰",
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
                "desc": "汇聚圣光重击敌人——造成 200% 伤害并驱散敌方增益；信仰达到 8 点时神威更盛（伤害＋40%）",
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
                "desc": "以圣光凝成壁垒护住自身——防御＋45% 持续 3 回合（保命）",
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
                "desc": "圣光如甘霖洒落全队——治疗全队 150% 生命（群奶核心，团队技能）",
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
                "desc": "向神明祈祷，换取力量加身——魔攻＋50% 持续 3 回合（增幅）",
                "name": "信仰祈祷",
            },
    "sk_shen_sheng_dao_yan": {
                "lv": 17,
                "mp": 25,
                "power": 0,
                "kind": "增益",
                "effect": "matk_up",
                "cd": 3,
                "desc": "高声诵出神圣祷言，信仰与魔力一同沸腾——魔攻＋50% 持续 3 回合(爆发前奏)",
                "name": "神圣祷言",
            },
    "sk_sheng_guang_qu_san": {
                "lv": 24,
                "mp": 35,
                "power": 0,
                "kind": "增益",
                "effect": "def_up",
                "cd": 3,
                "desc": "圣光屏障护佑全队——全队防御强化（团队技能；当前实现为防御强化，驱散/净化战斗加成二期排期待定）",
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
                "desc": "神恩如瀑布倾泻，治愈全队——治疗全队 180% 生命，消耗全部信仰（每点使治疗量＋8%）；自身生命低于 30% 时圣光迸发（治疗量＋50%，低血救场）",
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
                "desc": "屏息凝聚圣光，蓄力 1 回合(受击会打断)；蓄力完成施展大治愈，为全队治疗 320% 生命",
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
                "desc": "引动神罚圣裁从天而降——造成 300% 全体圣光伤害，消耗全部信仰（基础满点神迹）",
                "name": "神罚·圣裁",
            },
    "sk_p_bi_hu_zhi_guang": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "heal_shield", "pct": 0.2},
                "desc": "治疗溢出时圣光凝为护盾，溢出量的 20% 转为护盾(被动)",
                "name": "庇护之光",
            },
    "sk_p_shen_sheng_jian_ren": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05, "res_gain": 1},
                "desc": "圣光淬炼体魄，受击减伤 5%，且受击时积攒 1 点信仰(被动)",
                "name": "神圣坚韧",
            },
    "sk_p_sheng_guang_zhu_fu": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "heal_power", "add": 0.05},
                "desc": "圣光常驻祝福，治疗强度＋5%(被动)",
                "name": "圣光祝福",
            },
    "sk_p_xin_yang_jian_ding": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "mp", "mult": 0.15},
                "desc": "信仰凝为坚实根基，最大魔力＋15%(被动)",
                "name": "信仰坚定",
            },
    "sk_p_shen_en": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "heal", "mult": 1.1},
                "desc": "神恩常伴左右，治疗技能效果＋10%(被动)",
                "name": "神恩",
            },
        },
    },
    "cls_ci_ke": {
        "name": "刺客",
        "skills": {
    # v139：段数三线投喂 + 终结阈值 DSL——多段技能每段投喂 cp/combo/poison（ASSASSIN_HIT_FEED 数据驱动）；
    # 终结技（res_cost cp 3/5 档）是刺客全职业唯一判断消耗点，战前可设终结阈值 4 档（快刀/满刃/残血/满段）
    # （阈值配置已放 battle_config.py ASSASSIN_FINISHER_THRESHOLD，不占技能表条目）
    "sk_ci_ji": {
                "lv": 1,
                "mp": 3,
                "power": 1.0,
                "kind": "物理",
                "res_gain": 1,
                "cond": {"type": "player_first", "mult": 1.2, "label": "先手偷袭"},
                "desc": "匕尖自袖中无声递出，直取要害——造成 100% 物理伤害；先手出手时，暗影加持（伤害＋20%）",
                "name": "刺击",
            },
    "sk_ge_lie": {
                "lv": 2,
                "mp": 4,
                "power": 1.15,
                "kind": "物理",
                "res_gain": 1,
                "desc": "利刃划过血肉，留下一道深可见骨的伤口——造成 115% 物理伤害",
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
                "desc": "双匕翻飞如蝶，趁目标气血充盈时连斩两记——每次造成 90% 物理伤害（共 2 次）；目标生命高于 70% 时，背刺角度刁钻（伤害＋30%）",
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
                "desc": "匕尖在幽绿毒液中浸过，再吻上猎物的咽喉——造成 100% 物理伤害并附加 2 层中毒（毒刃之道，核心起手）",
                "name": "淬毒",
            },
    "sk_an_sha": {
                "lv": 20,
                "mp": 12,
                "power": 1.147,
                "kind": "物理",
                "res_cost": {"cp": 3},
                "cond": {"type": "enemy_hp_low", "hp_pct": 0.4, "mult": 1.4, "label": "残血收割"},
                "desc": "自阴影中现身的必杀一击，直指垂死之敌——造成 240% 物理伤害；目标生命低于 40% 时，死神已在旁等待（伤害＋40%）",
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
                "desc": "身形没入暗影，气息与杀意一同敛去——暴击率＋20%，持续 3 回合，且下次攻击必定暴击（爆发核心）",
                "name": "潜行",
            },
    "sk_ji_ying": {
                "lv": 6,
                "mp": 3,
                "power": 0,
                "kind": "增益",
                "effect": "spd_up",
                "cd": 2,
                "desc": "足尖点地，身影拖出残像掠向目标——速度＋40%，持续 2 回合（机动）",
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
                "desc": "顺着影子扑向猎物，匕刃与黑暗一同落下——造成 120% 物理伤害并叠加 1 层影袭（潜行联动）",
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
                "desc": "在猎物眉心烙下死亡的印记，令其成为众矢之的——目标受击伤害＋30%（铺垫）",
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
                "desc": "掷出毒囊炸开一片幽绿雾气，腐蚀全场敌人的血肉——造成 80% 全体物理伤害并附加 2 层中毒（毒刃流铺场）",
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
                "desc": "暗影凝成刃锋，对垂死之敌执行最后的处刑——基础造成 320% 致命一击，消耗全部连击点；目标生命低于 30% 时，死亡边缘的恐惧令威力＋50%",
                "name": "暗影处刑",
            },
    "sk_p_an_ying_zhi_wu": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "stealth_crit_dmg", "mult": 0.3},
                "desc": "与暗影共舞，藏于黑暗中的刃更加致命——潜行状态下暴击伤害＋30%（暮影行者觉醒即得，被动）",
                "name": "暗影之舞",
            },
    "sk_p_ji_ying": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "spd", "mult": 0.08},
                "desc": "将疾影的残像刻入身法——速度＋8%（被动）",
                "name": "疾影术",
            },
    "sk_p_ying_ren_jing_tong": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "crit_dmg", "add": 0.10},
                "desc": "刃与影浑然一体，出刀必中要害——暴击伤害＋10%（一转觉醒·影刃精通，被动）",
                "name": "影刃精通",
            },
    "sk_p_ju_du_qin_he": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "poison", "mult": 1.2},
                "desc": "血肉与毒素渐生共鸣，毒液成了最亲密的盟友——毒层每层伤害＋20%（被动）",
                "name": "剧毒亲和",
            },
    "sk_p_zhi_ming_yu_mou": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "battle_start_cp"},
                "desc": "战斗未启，杀局已布——战斗开始时即获得 1 点连击点（被动）",
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
                "desc": "一记笔直的拳锋破空而出——造成 100% 单体伤害(连招【拳】)；先手出招时力道更沉(伤害＋15%)",
                "name": "直拳",
            },
    "sk_chong_quan": {
                "lv": 2,
                "mp": 3,
                "power": 1.1,
                "kind": "物理",
                "res_gain": 1,
                "combo": "拳",
                "desc": "沉肩发力，拳势如弩箭离弦——造成 110% 物理伤害(连招【拳】)",
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
        "desc": "拳风裹挟气力，直撼骨节——造成 150% 破防伤害(连招【拳】)，消耗 3 点气；目标生命高于 70% 时拳势更重(伤害＋20%)",
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
                "desc": "身形腾转，一记回旋腿扫过前排——造成 120% 全体伤害(连招【踢】)；目标减速或冻结时踢势更狠(伤害＋30%)",
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
                "desc": "重腿砸地，震波轰然扩散——造成 130% 全体伤害(连招【踢】)，35% 概率震晕目标",
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
                "desc": "侧身一记凌厉踢击——造成 110% 伤害(连招【踢】)；上一招为拳时衔接流畅(伤害＋10%)",
                "name": "侧踢",
            },
    "sk_tie_zhang": {
                "lv": 6,
                "mp": 5,
                "power": 1.2,
                "kind": "物理",
                "combo": "掌",
                "res_gain": 1,
                "desc": "拳掌如铁，蓄势待发——造成 120% 伤害(连招【掌】)，为三连蓄势",
                "name": "钢拳",
            },
    "sk_qi_xi_tiao_xi": {
                "lv": 11,
                "mp": 5,
                "power": 0.15,
                "kind": "治疗",
                "cd": 3,
                "res_gain": 2,
                "desc": "敛息凝神，引导气力温养周身——回复 15% 生命",
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
                "desc": "周身气劲凝为壁垒，坚不可摧——防御＋45% 持续 2 回合",
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
                # v139 三连击破改造挂点：三连击破命中追加 shaken +15（打晕）+ def_down 破防（打防御）同时生效（共用一次命中）
                "triple_break": {"shaken_gain": 15, "def_down": True},
                "desc": "拳、踢、掌三段连环如行云流水——连续攻击 3 次(每次 150% 伤害)；三连完成时气力技威力＋20%；三连击破命中追加破绽+15 并施加破防(打晕与破防共用一次命中)",
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
                "desc": "将周身气力凝于一拳，如破晓曙光——造成 63% 基础伤害，消耗全部气(每点气＋10% 威力，满 10 气约 127%)；目标处于破绽被晕当回合伤害×1.15",
                "name": "破晓之拳"
            },
    "sk_p_lian_zhao_jing_tong": {
                "lv": 12,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "combo_boost"},
                "desc": "千锤百炼的连招技艺——三连击破的追加伤害提升至 50%(v109.2 武圣连击强化)",
                "name": "连招精通",
            },
    "sk_p_pan_shi_ti": {
                "lv": 25,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "dmg_taken", "reduce": 0.05, "res_gain": 1},
                "desc": "身躯如磐石般沉稳——受到伤害时减伤 5%，并凝聚 1 点气",
                "name": "磐石体",
            },
    "sk_p_qi_shou_shi": {
                "lv": 30,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "atk", "cond": "battle_start", "mult": 0.08},
                "desc": "开战瞬间便抢占先机——战斗开始时攻击＋8%",
                "name": "起手式",
            },
    "sk_p_qi_xi_tiao_he": {
                "lv": 38,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"proc": "turn_heal", "pct": 0.02},
                "desc": "气随呼吸流转不息——每回合回复 2% 生命",
                "name": "气力调和",
            },
    "sk_p_dou_qi_ning_ju": {
                "lv": 55,
                "mp": 0,
                "power": 0,
                "kind": "被动",
                "passive": {"stat": "chi_gain", "mult": 1},
                "desc": "气劲涌动如渊，凝聚更快——气获取＋1",
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
                        # v139 狂暴态增益：狂暴形态下伤害 +20%（怒斩 = 入狂暴门槛技）
                        "cond_rage_form": {"type": "player_rage_form", "mult": 1.2, "label": "狂暴增益"},
                        "mp": 5,
                        "desc": "怒意化作劈山一剑——造成 238% 物理伤害；自身生命低于 50% 时狂血翻涌(伤害＋25%)；狂暴形态下怒意更炽(伤害＋20%)",
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
                        # v139 狂暴精通前置：狂暴中维持成本 -1 → 0（与狂暴精通叠加归零）
                        "rage_form": {"maintain_cost_reduce": 1},
                        "desc": "伤越重，战意越炽——生命低于 50% 时攻击＋10%；狂暴形态下维持成本 -1(狂暴维持归零)",
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
                        # v139 狂暴强化：狂暴形态下吸血翻倍（25% → 50%）
                        "rage_form": {"lifesteal_mult": 2},
                        "mp": 8,
                        "desc": "利刃贪婪地渴饮鲜血——造成 160% 物理伤害并吸血 25%；目标身带减益时剑势更凶(伤害＋20%)；狂暴形态下吸血翻倍(50%)",
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
                        "desc": "怒血燃尽，孤注一掷——终结技造成 240% 物理伤害；自身生命低于 30% 时背水一战(伤害＋40%)",
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
                        "desc": "挥剑如龙啸，吐出灼热吐息——造成 100% 真伤(无视全部防御)并附加 2 层灼烧",
                        "name": "龙息之怒"
                    }
,
                    # v139 新增：狂暴精通（攻线签名，云海疾剑式翻译）——被动：狂暴中维持成本 -1 → 0、受击成本 -1 → 0
                    "狂暴精通":                     {
                        "lv": 50,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "rage_form_mastery"
                        },
                        "rage_form": {"maintain_cost_reduce": 1, "hit_cost_reduce": 1},
                        "desc": "狂暴技艺炉火纯青——狂暴形态下维持成本 -1、受击成本 -1（维持/受击消耗归零）",
                        "name": "狂暴精通"
                    }
,
                    # v139 新增：破势斩（云海本命「入剑追加」翻译）——入狂暴当回合自动追加 1 次 120% 物理（不占行动）
                    "破势斩":                     {
                        "lv": 52,
                        "mp": 0,
                        "power": 1.2,
                        "kind": "物理",
                        "auto": "rage_form_enter",
                        "desc": "入狂暴当回合自动追加 1 次 120% 物理斩击（不占行动）",
                        "name": "破势斩"
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
                        # v139 姿态联动：守护姿态生效时伤害 +20%
                        "cond_stance": {"type": "player_stance", "mult": 1.2, "label": "姿态联动"},
                        "mp": 5,
                        "desc": "重盾裹挟守护之力悍然砸出——造成 238% 盾击伤害，概率震晕目标 1 回合；目标已被眩晕时追加 50% 伤害；守护姿态生效时伤害＋20%",
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
                        # v139 云海骑士反冲槽翻译：受击自动反击 40%（不耗怒、不计 CD、每受击至多 1 次）+ 回合末保底回怒 1
                        "counter_attack": {"proc": "on_hit", "power": 0.4, "per_hit": 1, "free": True},
                        "stance_floor": {"res_gain": 1, "per_turn": 1},
                        "desc": "沉稳如山的守护架势——受到伤害降低 10%，受击时凝聚怒气；受击自动反击 40% 物理(不耗怒气、不吃 CD、每受击至多 1 次)，回合末保底回怒 1",
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
                        "desc": "高举坚盾，壁垒护佑全队——组队时全队防御强化",
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
                        # v139 顿足盾击联动：嘲讽失效（目标死亡/免疫）当回合自动衔接 40% 顿足盾击（不占行动）
                        "auto_followup": {"trigger": "taunt_failed", "skill": "顿足盾击", "power": 0.4, "free": True},
                        "desc": "一声挑衅怒喝，将敌意尽数引向自身——强制怪物攻击自己 2 回合(CD 3)；嘲讽失效时当回合自动衔接 40% 顿足盾击(不占行动)",
                        "name": "嘲讽"
                    }
,
                    # v139 新增：顿足盾击（云海战士余势斩翻译）——嘲讽失效/格挡被破当回合自动 40% 低伤盾击（不占主行动、不吃 CD、不耗怒）
                    "顿足盾击":                     {
                        "lv": 50,
                        "mp": 0,
                        "power": 0.4,
                        "kind": "物理",
                        "auto": "stance_followup",
                        "auto_cond": {"taunt_failed": True, "block_break": True},
                        "desc": "守线自动衔接技——嘲讽失效或格挡被破当回合自动打出 40% 盾击(不占主行动、不吃 CD、不耗怒)",
                        "name": "顿足盾击"
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
                        "desc": "狂战士之魂永不熄灭——怒气获取＋1",
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
                        "desc": "剑光如狂风乱舞——连斩 3 次(每次 120% 物理伤害)",
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
                        "desc": "审判之剑落下，终结一切抵抗——造成 300% 斩杀伤害；目标生命低于 35% 时(伤害＋50%)",
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
                        # v139 格挡反击：守护姿态生效时格挡成功触发一次 40% 反击（复用 block_counter 挂点）
                        "block_counter": {"power": 0.4, "stance_only": True},
                        "desc": "神圣壁垒护体——格挡率＋10%；守护姿态生效时格挡成功触发一次 40% 反击",
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
                        "desc": "伤痛点燃复仇之焰——受击后下一次攻击＋30%",
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
                        "desc": "如攻城巨锤轰碎防线——造成 220% 破防伤害；目标生命高于 70% 时全力压制(伤害＋50%)",
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
                        "desc": "剑势如怒涛连绵不绝——全体连斩 3 次(每次 180% 伤害)；怒气达到 9 点时威力再涨(伤害＋30%)",
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
                        "desc": "化身战争本身，挥出毁天灭地的一剑——造成 500% 毁灭斩击，消耗全部 10 点怒气",
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
                        "desc": "展开属于战争的领域——3 回合内攻击大幅提升",
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
                        # v139 守护誓言期间姿态反击倍率 40% → 50%
                        "stance_counter_boost": {"mult": 0.1},
                        "desc": "以誓言为盾，守护全队——组队时全队防御强化；守护誓言期间姿态反击倍率提升(40%→50%)",
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
                        "desc": "筑起不破的壁垒——全队减伤 25% 持续 3 回合",
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
                        "desc": "圣光凝成守护圣域——为全队张开无敌屏障",
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
                        # v139 架设联动：架设中命中额外充能 +1（施法频率预算化）
                        "focus_gain_extra": 1,
                        "desc": "将当前系元素凝成冲击波轰出，造成 190% 伤害并烙下元素印记；目标已有印记时万象共鸣(伤害＋20%、充能＋1)；元素架设中命中额外充能＋1",
                        "name": "元素冲击"
                    }
,
                    # v139 新增：元素聚焦（攻线开启技，云海架设翻译）——开启「元素架设」专注施法态
                    "元素聚焦":                     {
                        "lv": 32,
                        "mp": 20,
                        "power": 0,
                        "kind": "增益",
                        "effect": "element_focus",
                        "cd": 3,
                        "desc": "凝神开启元素架设——本场进入专注施法态：魔法技能伤害＋40%、受击＋20%、不能普攻/换系(可防御/用道具)；主动解除无损；被打断只掉 1 层充能、不清零",
                        "name": "元素聚焦"
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
                        "desc": "与万象元素共鸣，施放元素技能时伤害＋8%(被动)",
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
                        # v139 多段适配：分段铺印（每段+1）、首段结算反应、反应触发时充能 -1
                        "reaction_first_seg": True,
                        "desc": "双系元素连珠齐射，造成当前系 130%×2 伤害并叠 2 层印记；目标印记≥3 层时连环迸发(伤害＋25%，消耗 3 充能)；多段分段铺印、反应仅首段结算",
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
                        # v139 架设联动：架设中触发蒸发/超载反应时反应倍率 ×1.2（聚焦放大反应）
                        "focus_reaction_mult": 1.2,
                        "desc": "引动元素印记连锁炸裂，造成当前系 240% 伤害；目标印记≥2 层时元素共鸣(伤害＋30%，消耗 2 充能)；架设中触发反应倍率×1.2",
                        "cd": 3,
                        "name": "元素引爆"
                    }
,
                    # v113：吸蓝机制下放——原时咒线吸蓝流派技降为基础法师攻线 Lv.55 进阶技
                    # v130.2：黑名单违名技更名「元素湮灭」——重定位为攻线 T1 满充能全耗终极（consume_all element per 0.2）
                    "元素湮灭":                     {
                        "lv": 55,
                        "mp": 40,
                        "power": 1.2,
                        "kind": "魔法",
                        "mp_steal": 0.20,
                        "consume_all": {"key": "element", "per": 0.2},
                        "cd": 4,
                        # v139 架设联动：架设中释放 power 基础 ×1.4 但受 pmult cap 封顶（峰值红线锚）
                        "focus_power_mult": 1.4,
                        "desc": "湮灭之力倾泻而出，造成 120% 魔法伤害并消耗全部充能(每点＋20%，满 5 充能威力翻倍)，同时回复 20% 伤害值的魔力；元素架设中释放威力×1.4(受乘区封顶)",
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
                                 "desc": "奥术能量如幕布倾洒，造成 110%×3 伤害并使奥术充能＋1；充能≥2 层时蓄势更猛(伤害＋15%)",
                                 "name": "奥术弹幕"},
                    "奥术直觉": {"lv": 38, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "arcane_regen", "mech": "arcane", "mult": 1},
                                 "desc": "奥术直觉如影随形，每回合开始自动获得 1 层奥术充能(被动)；深度冥想中叠加为每回合＋2",
                                 "name": "奥术直觉"},
                    # v139 新增：深度冥想（守线版架设）——开启后 arcane 每回合自动 +1（与奥术直觉叠加）+ 魔法技能 +40% + 受击 +20% + 施法受限；主动解除无损、被控解除
                    "深度冥想": {"lv": 40, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "element_focus", "focus_variant": "arcane",
                                 "arcane_auto_per_turn": 1, "cd": 3,
                                 "desc": "沉入深度冥想，开启架设驻留态——魔法技能伤害＋40%、受击＋20%、施法受限；每回合开始奥术充能＋1(与奥术直觉叠加为每回合＋2)；主动解除无损，被控强制解除",
                                 "name": "深度冥想"},
                    "奥术飞弹": {"lv": 40, "mp": 15, "power": 1.0, "kind": "魔法",
                                 "mech": "arcane", "mech_val": 1, "cd": 1,
                                 "res_gain": {"element": 1},
                                 "focus_gain_extra": 1,
                                 "desc": "奥术飞弹划出湛蓝弧光，造成 100% 魔法伤害并叠加 1 层奥术印记(充能＋1)；架设中命中额外充能＋1",
                                 "name": "奥术飞弹"},
                    "奥术爆破": {"lv": 45, "mp": 20, "power": 1.5, "kind": "魔法",
                                 "multi": 2, "mech": "arcane", "mech_val": 2,
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 4, "mult": 1.25, "label": "共鸣输出"},
                                 "cd": 2,
                                 "res_cost": {"element": 1},
                                 # v139 多段适配：多段首段结算「共鸣输出」层数判定
                                 "reaction_first_seg": True,
                                 "desc": "奥术能量蓄满爆破，造成 150%×2 伤害并使奥术充能＋2；充能≥4 层时共鸣输出(伤害＋25%，消耗 1 充能)；多段首段结算共鸣判定",
                                 "name": "奥术爆破"},
                    "奥术脉冲": {"lv": 48, "mp": 25, "power": 1.6, "kind": "魔法",
                                 "mech": "arcane_burst", "mech_val": 0, "cd": 3,
                                 # v139 架设驻留保护：架设中「燃尽」只烧一半（向下取整）——奥术驻留不清零
                                 "focus_burn_half": True,
                                 "desc": "奥术脉冲激荡而出，造成 160% 魔法伤害并燃尽全部奥术印记(每层追加伤害)；架设中燃尽只烧一半(向下取整)",
                                 "name": "奥术脉冲"},
                    "秘法护盾": {"lv": 55, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "shield_all", "cd": 4,
                                 "desc": "秘法之力织成魔力护盾，获得相当于 20% 魔攻的护盾持续 3 回合",
                                 "name": "秘法护盾"},
                    "奥术洪流": {"lv": 55, "mp": 30, "power": 1.844, "kind": "魔法",
                                 "mech": "arcane_burst",
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 5, "mult": 1.4, "label": "共鸣巅峰"},
                                 "cd": 3,
                                 "desc": "奥术洪流奔涌而出，造成 250% 伤害并消耗全部充能(每层＋15%)；充能≥5 层时共鸣巅峰(伤害＋40%)",
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
                        "desc": "元素之心与魔力同频跳动，元素系技能伤害＋10%(被动)",
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
                        "desc": "身形在元素间跃迁流转，切换当前元素系(火→冰→雷)，下次元素技能伤害＋20%(充能＋1)",
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
                        "desc": "以元素铸成壁垒护体，防御强化(消耗 2 充能)",
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
                        "desc": "雷元素骤然迸发，造成 150% 雷系超远程伤害(消耗 1 充能，CD 1)",
                        "name": "元素迸发"
                    }
,
                },
                "奥秘术士": {
                    "奥术核心": {"lv": 60, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "arcane_dmg", "mult": 0.15},
                                 "desc": "奥术核心在体内运转不息，奥术系伤害＋15%(被动)",
                                 "name": "奥术核心"},
                    "奥术之心": {"lv": 60, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "arcane_dmg", "mult": 0.1},
                                 "desc": "奥术之心凝聚如水晶，奥术技能伤害＋10%(被动)",
                                 "name": "奥术之心"},
                    "法术反制": {"lv": 62, "mp": 15, "power": 0.6, "kind": "魔法",
                                 "mech": "arcane", "mech_val": 2, "cc": "silence",
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 2, "mult": 1.2, "label": "反制强化"},
                                 "res_gain": {"element": 1},
                                 # v139 架设联动：架设中反制成功（目标沉默生效）额外充能 +1
                                 "focus_counter_extra": 1,
                                 "desc": "掐断敌方咒语节律，造成 60% 反制伤害并使敌人沉默，同时奥术充能＋2；充能≥2 层时反制更强(伤害＋20%、充能＋1)；架设中反制成功额外充能＋1",
                                 "name": "法术反制"},
                    "法力护盾": {"lv": 68, "mp": 30, "power": 0, "kind": "增益",
                                 "effect": "def_up", "cd": 3,
                                 "res_cost": {"element": 1},
                                 "desc": "法力凝成护盾环绕，防御强化(消耗 1 充能)",
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
                        # v139 多段适配同双系连珠（首段反应、分段铺印）
                        "reaction_first_seg": True,
                        "desc": "万象元素化作风暴席卷全场，造成当前系 180%×3 全体伤害；目标带有印记时万象连环(伤害＋30%、充能＋1)；多段分段铺印、反应仅首段结算",
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
                        "desc": "终极技——天雷自九霄倾落，对全体造成雷系 450% 伤害，并为全队加持魔攻强化(消耗 3 充能)",
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
                        "desc": "三转奥义——元素之力凝成裁决之光，对全体造成当前系 400% 伤害(消耗 5 充能)",
                        "name": "元素裁决"
                    }
,
                },
                "奥秘贤者": {
                    "奥术爆发": {"lv": 90, "mp": 40, "power": 2.2, "kind": "魔法",
                                 "mech": "arcane_burst", "mech_val": 0, "cd": 4,
                                 "desc": "奥术能量轰然爆发，造成 220% 魔法伤害并燃尽全部奥术印记",
                                 "name": "奥术爆发"},
                    "奥术领域": {"lv": 90, "mp": 100, "power": 4.0, "kind": "魔法",
                                "aoe": "all", "team": "shield_all", "cd": 6,
                                "res_cost": {"element": 3},
                                "desc": "三转奥义——展开奥术领域，对全体造成 400% 奥术伤害并为全队加持护盾(消耗 3 充能)",
                                "name": "奥术领域"},
                    "大奥术": {"lv": 92, "mp": 30, "power": 2.0, "kind": "魔法",
                               "multi": 2, "aoe": "all", "mech": "arcane", "mech_val": 2,
                               "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 6, "mult": 1.3, "label": "大奥术回响"},
                               "cd": 3,
                               "res_gain": {"element": 1},
                               "desc": "大奥术回响轰鸣，对全体造成奥术 200%×2 伤害并使充能＋2；充能≥6 层时回响更盛(伤害＋30%、充能＋1)",
                               "name": "大奥术"},
                    "奥术主宰": {"lv": 98, "mp": 120, "power": 4.5, "kind": "魔法",
                                 "cond": {"type": "player_mech_stacks", "mech": "arcane", "stacks": 5, "mult": 1.4, "label": "奥术主宰"},
                                 "cd": 5,
                                 "res_cost": {"element": 5},
                                 "desc": "终极技——奥术主宰万物，造成 450% 奥术伤害；充能≥5 层时主宰降临(伤害＋40%，消耗 5 充能)",
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
                        # v139 屏息窗口联动：屏息状态下命中标记目标再 +10%
                        "breathe_mark_mult": 0.1,
                        "desc": "循着猎杀标记的气味穷追不舍，箭矢咬住猎物的背影——造成 190% 物理伤害；目标被标记时，猎杀本能苏醒（伤害＋30%）；凝神屏息窗口内对标记目标再＋10%",
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
                        "desc": "目光所及，皆是猎物——对标记目标的伤害＋8%（被动，标记特攻）",
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
                        # v139 屏息窗口喂毒：屏息窗口内毒层 +1
                        "breathe_poison_extra": 1,
                        "desc": "召唤林间藤蔓破土而出，缠上猎物的足踝并注入麻痹毒汁——造成 80% 物理伤害并叠加 2 层中毒（自然毒藤）；凝神屏息窗口内毒层＋1",
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
                        "desc": "以林语唤醒沉睡的藤蔓，化为守卫并肩而战——召唤藤蔓守卫加入战斗（可叠加 2 只，自动攻击并挡刀）",
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
                        # v139 屏息窗口提前引爆：引爆时若处于屏息窗口毒层阈值 -1（≥2 层可爆）
                        "breathe_burst_threshold": -1,
                        "desc": "以自然之力引燃猎物体内的毒素，令其由内而外迸发——造成 60% 物理伤害；毒层达到 3 层时迸发，每层追加 15% 攻击的物理伤害；凝神屏息窗口内毒层≥2 层即可迸发",
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
                        # v139 屏息窗口放宽条件：屏息窗口内速度比阈值降到 1.3
                        "breathe_ratio_lower": 1.3,
                        "desc": "借风势射出疾驰一箭，箭速快过猎物反应——造成 190% 物理伤害；速度比达到 1.5 倍以上时，疾风连击呼啸（伤害＋50%）；凝神屏息窗口内速度比阈值降至 1.3",
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
                        "desc": "风在身后追赶，箭在风中先行——速度高于目标时，伤害＋8%（被动，高速压制）",
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
                        # v139 屏息窗口联动：屏息窗口内 2 段 → 3 段
                        "breathe_seg_bonus": 1,
                        "desc": "弓弦一颤两箭齐出，如双燕掠空——造成 110% 物理伤害×2；自身未受击时，身姿轻灵无瑕（伤害＋15%）；凝神屏息窗口内段数＋1(3 段)",
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
                        # v139 屏息窗口联动：屏息窗口内 3 段 → 4 段（AOE 版）
                        "breathe_seg_bonus": 1,
                        "desc": "弓弦化作风刃席卷全场，割裂一切甲胄——造成 130% 物理伤害×3 的全体攻击（无视防御），冷却 3 回合；速度比达到 2 倍以上时，极速之风加持（伤害＋25%）；凝神屏息窗口内段数＋1(4 段)",
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
                        "desc": "万物在自然之眼中皆有破绽——对标记目标的伤害＋10%（二转被动，标记强化）",
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
                        # v139 屏息循环衔接：施放后精力 +5 → 与屏息循环衔接（回精力 = 推迟节流阀）
                        "breathe_energy_sync": True,
                        "desc": "吹响猎杀盛宴的号角，全队的杀意一同高涨——全队暴击强化 3 回合，施放时回复 5 点精力（狂宴回力，攻线叠标回精引擎；回精力=推迟凝神屏息）",
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
                        "desc": "毒与自然在血脉中交融，毒液化作第二颗心脏——毒系技能伤害＋20%（被动）",
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
                        # v139 狙击后排联动：对后排目标（rank=3）伤害 ×1.2
                        "backrank_mult": 1.2,
                        "desc": "箭矢穿透层层甲胄，直指心脏——造成 280% 破防物理伤害；目标被标记时，要害暴露无遗（伤害＋30%）；对后排目标伤害×1.2",
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
                        "desc": "疾风在血脉中奔流不息——速度＋8%（二转被动，机动强化）",
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
                        # v139 屏息爆发窗口最高段载体：屏息窗口内 5 段 → 6 段
                        "breathe_seg_bonus": 1,
                        "desc": "弓弦几乎失去踪影，箭雨连绵不绝——造成 90% 物理伤害×5（高速叠印）；凝神屏息窗口内段数＋1(6 段)",
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
                        # v139 屏息视为增益：屏息窗口触发「风速」条件（player_buffed 语义扩展）
                        "breathe_as_buff": True,
                        "desc": "一箭穿云破雾，裹着风压直贯敌阵——造成 220% 破防物理伤害；自身带有增益时，风助箭势（伤害＋20%）；凝神屏息视为增益触发风速",
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
                        # v139 屏息爆发窗口主载体：屏息窗口内 4 段 → 5 段
                        "breathe_seg_bonus": 1,
                        "desc": "四箭连珠，箭箭皆奔要害而去——造成 140% 物理伤害×4（叠印爆发）；凝神屏息窗口内段数＋1(5 段)",
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
                        "desc": "唤醒沉睡千年的古树化作重装守卫，以庞大身躯为伙伴挡下刀锋——召唤古树守卫（单只重装，挡刀率高）并令攻击＋30%，持续 3 回合",
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
                        # v139 狙击后排联动（T3 形态）：对 rank=3 目标 ×1.2
                        "backrank_mult": 1.2,
                        "desc": "死神借弓弦睁开眼，一箭定生死——造成 450% 破防物理伤害；目标被标记时，死神注视之下伤害＋40%（终极技）；对后排目标伤害×1.2",
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
                        "desc": "万物寂灭，唯余猎杀——对标记目标造成 400% 破防斩杀一击（单点核爆，三转奥义）",
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
                        # v139 屏息窗口联动：屏息窗口内 4 段 → 5 段
                        "breathe_seg_bonus": 1,
                        "desc": "身随风暴起舞，箭矢如雨点般倾泻——造成 160% 物理伤害×4（终极连射）；凝神屏息窗口内段数＋1(5 段)",
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
                        # v139 屏息窗口联动：屏息窗口内 3 段 → 4 段
                        "breathe_seg_bonus": 1,
                        "desc": "疾风化作骤雨，箭矢铺天盖地落下——造成 200% 物理伤害×3，冷却联动全技能（终极技）；凝神屏息窗口内段数＋1(4 段)",
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
                        # v139 泄压阀最高档：施放当回合精力 -15（位移从成本变收益的直接兑现）
                        "vent_energy": 15,
                        "desc": "风神之息灌入四肢百骸，身形快如流光——速度大幅提升，持续 3 回合（极速爆发，三转奥义）；施放当回合精力-15(机动泄压)",
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
                                 # v139 谱曲标记：命中附加「轻旋律」（2 回合内下一次演唱共鸣 -1）
                                 "light_melody": {"res_cost_reduce": 1, "turns": 2},
                                 "desc": "指尖拨动琴弦即兴弹唱，琴音如刃造成 100% 物理伤害，并有 15% 概率使目标中毒；命中附加「轻旋律」(2 回合内下一次演唱共鸣-1)",
                                 "name": "即兴弹唱"},
                    "轻快拨弦": {"lv": 35, "mp": 3, "power": 1.1, "kind": "物理",
                                 "res_gain": {"resonance": 1, "echo": 1}, "mech": "poison", "mech_chance": 0.1,
                                 # v139 同放双涨：歌类输出 共鸣+1·回声+1（固化为分支级规则）
                                 "bard_dual_gain": True,
                                 "desc": "轻快拨动琴弦奏出刁钻音刃，造成 110% 物理伤害并有 10% 概率附加中毒(共鸣＋1·回声＋1 同放双涨)",
                                 "name": "轻快拨弦"},
                    "战歌": {"lv": 38, "mp": 10, "power": 0, "kind": "增益",
                             "res_gain": {"echo": 1},
                             "effect": "atk_up", "team": "atk_all", "cd": 2,
                             # v139 双行算式：全队增益团队 100% / 歌者自身仅享 55%（self_gain_factor）；自身减伤 -5%（战歌反面）
                             "self_gain_factor": 0.55,
                             "self_penalty": {"reduce_dmg_taken": 0.05},
                             "desc": "激昂战歌响彻战场，全队攻击＋30% 持续 3 回合(团队技能)；自身仅享 55%(攻+16.5%)，自身减伤-5%(战歌反面)",
                             "name": "战歌"},
                    "安眠曲": {"lv": 45, "mp": 10, "power": 0, "kind": "增益",
                               "res_gain": {"echo": 1},
                               "effect": "sleep", "cd": 3,
                               "desc": "悠扬曲调化作睡意笼罩，使敌人陷入沉睡 2 回合(受击解除，对首领只持续 1 回合)",
                               "name": "安眠曲"},
                    # v130.2 新增：歌者签名一（v130.2 双资源·启明全队增益，消耗 3 共鸣）
                    "启明圣咏": {"lv": 50, "mp": 20, "power": 0, "kind": "增益",
                                 "res_gain": {"echo": 1},
                                 "effect": "atk_up", "team": "atk_all", "cd": 2,
                                 "res_cost": {"resonance": 3},
                                 # v139 双行折算：团队 100% / 自身 55%
                                 "self_gain_factor": 0.55,
                                 "desc": "启明圣咏驱散阴霾，全队攻击＋10% 持续 3 回合(消耗 3 共鸣·回声＋1)；自身仅享 55%(双行折算)",
                                 "name": "启明圣咏"},
                },                "神谕者": {
                    "圣言术":                     {
                        "lv": 32,
                        "power": 2.5,
                        "kind": "治疗",
                        # v139 P0 修复：res_gain 2 → 0（治疗攒点收敛到全局 on_heal +2，防双计数）
                        "res_gain": 0,
                        "cond": {
                            "type": "player_hp_low",
                            "hp_pct": 0.3,
                            "mult": 1.5,
                            "label": "圣言回响"
                        },
                        "mp": 10,
                        "desc": "圣言落下即愈，治疗 250% 生命；自身生命低于 30% 时圣言回响(治疗量＋50%)；治疗攒点走全局 on_heal+2(无双计数)",
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
                        "desc": "虔诚圣祷引来神恩眷顾，治疗时有 20% 概率额外治疗 30%(被动)",
                        "name": "圣祷"
                    }
,
                    # v139：净化术 → 圣辉涤净（云海净涤翻译）——清除自身 1 个异常 + 全队防御强化；随附（不占主行动）
                    "圣辉涤净":                     {
                        "lv": 45,
                        "mp": 20,
                        "power": 0,
                        "kind": "增益",
                        "effect": "def_up",
                        "cleanse_self": 1,
                        "team": "def_all",
                        "cd": 2,
                        "support": True,
                        "desc": "圣辉涤荡污秽——清除自身 1 个异常并全队防御强化；随附支援(不占主行动，每回合至多 1 件)",
                        "name": "圣辉涤净"
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
                        # v139 随附支援入守线：本回合治疗后自动「圣辉祝福」（全队减伤 5%，1 回合）
                        "support_followup": {"effect": "reduce_all", "reduce_all": 0.05, "turns": 1, "team": True},
                        "desc": "圣光汇聚成治愈之潮，为全队治疗 300% 生命(团队核心)；治疗后自动随附「圣辉祝福」(全队减伤 5% 1 回合)",
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
                             "desc": "歌声激昂鼓舞人心，全队暴击率＋20% 持续 3 回合(团队技能)",
                             "name": "鼓舞"},
                    "哀歌": {"lv": 62, "mp": 15, "power": 1.7, "kind": "魔法",
                             "cc": "silence", "cd": 3,
                             "res_gain": {"resonance": 1, "echo": 1},
                             "desc": "悲怆哀歌化作音刃，造成 170% 魔法伤害并有 50% 概率沉默目标 2 回合(共鸣＋1·回声＋1)",
                             "name": "哀歌"},
                    "伴奏": {"lv": 65, "mp": 0, "power": 0, "kind": "被动",
                             "passive": {"proc": "bard_echo", "chance": 0.2},
                             "desc": "共鸣伴唱如影随形，施放歌类技能时有 20% 概率额外获得 1 层回声(被动)",
                             "name": "伴奏"},
                    "轻风咏叹": {"lv": 68, "mp": 15, "power": 0, "kind": "增益",
                                 "res_gain": {"echo": 1},
                                 "effect": "spd_up", "team": "spd_all", "cd": 2,
                                 "res_cost": {"resonance": 3},
                                 # v139 双行折算：团队 100% / 自身 55%
                                 "self_gain_factor": 0.55,
                                 "desc": "轻风咏叹拂过全场，全队速度＋40% 持续 3 回合(消耗 3 共鸣·回声＋1)；自身仅享 55%(双行折算)",
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
                        "desc": "神圣恩典常驻心间，治疗效果＋10%(被动)",
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
                        "desc": "生命之泉汩汩涌流，全队每回合回复 5% 生命(被动)",
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
                        # v139 随附支援入守线：护盾时自动「圣辉守护」（自身 1 回合减伤 10%）
                        "support_followup": {"effect": "dmg_reduce", "reduce": 0.1, "turns": 1, "self": True},
                        "desc": "神圣光辉织成庇护之壁，为全队加持护盾(CD 4，消耗 5 信仰)；护盾时自动随附「圣辉守护」(自身 1 回合减伤 10%)",
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
                                   # v139 随附化：本技能治疗「不占主行动」（1 回合只 1 次）
                                   "support_free": True,
                                   "desc": "吟唱英雄史诗，圣光随旋律抚愈全队——治疗全队 150% 生命(共鸣＋2)；治疗随附化不占主行动(1 回合 1 次)",
                                   "name": "英雄叙事诗"},
                    "奥术咏叹调": {"lv": 92, "mp": 20, "power": 0, "kind": "增益",
                                   "res_gain": {"echo": 1},
                                   "effect": "matk_up", "team": "matk_all", "cd": 2,
                                   "res_cost": {"resonance": 3},
                                   # v139 双行折算：团队 100% / 自身 55%
                                   "self_gain_factor": 0.55,
                                   "desc": "咏叹调与奥术共鸣，全队魔攻＋50% 持续 3 回合(消耗 3 共鸣·回声＋1)；自身仅享 55%(双行折算)",
                                   "name": "奥术咏叹调"},
                    "快板节奏": {"lv": 95, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"stat": "cdr", "add": 0.08},
                                 "desc": "快板节奏令人手起招落，冷却缩减＋8%(被动)",
                                 "name": "快板节奏"},
                    "终章·黎明颂歌": {"lv": 98, "mp": 35, "power": 0, "kind": "增益",
                                       "res_gain": {"echo": 2},
                                       "effect": "atk_up_strong", "team": "atk_all", "cd": 5,
                                       "res_cost": {"resonance": 5},
                                       # v139 双行折算：团队 100% / 自身 55%
                                       "self_gain_factor": 0.55,
                                       "desc": "黎明颂歌奏响终章，全队攻击＋75% 持续 3 回合(消耗 5 共鸣·回声＋2)；自身仅享 55%(双行折算)",
                                       "name": "终章·黎明颂歌"},
                    # v130.2 新增：歌者 tier3 专属攒点技（光咏晨祷，共鸣 +1）
                    "破晓圣咏": {"lv": 94, "mp": 30, "power": 1.8, "kind": "魔法",
                                 "cd": 3, "reach": 2,
                                 "res_gain": {"resonance": 1, "echo": 1},
                                 # v139 补强为歌者伤害终结门槛：共鸣 ≥5 时 +15%（EQ ≈ 2.1 中档伤害口）
                                 "cond": {"type": "player_res_stacks", "res_key": "resonance", "stacks": 5, "mult": 1.15, "label": "共鸣巅峰"},
                                 "desc": "破晓之光凝入咏唱，造成 180% 圣咏魔法伤害(共鸣＋1·回声＋1)；共鸣≥5 时伤害＋15%(EQ≈2.1)",
                                 "name": "破晓圣咏"},
                    # v139 新增：破晓长歌（云海「收束·尾声」翻译，歌者 T3 伤害终结）——320% 单体圣咏魔法，消耗 5 共鸣，命中后回声 +1；EQ = 3.2 × 1.5 ≈ 4.8
                    "破晓长歌": {"lv": 96, "mp": 40, "power": 3.2, "kind": "魔法",
                                 "cd": 5, "reach": 2,
                                 "res_cost": {"resonance": 5},
                                 "res_gain": {"echo": 1},
                                 "desc": "共鸣燃至顶点，奏响破晓长歌——造成 320% 圣咏魔法伤害，消耗 5 共鸣(清空短燃料条)，命中后回声＋1(EQ≈4.8 伤害终结)",
                                 "name": "破晓长歌"},
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
                        "desc": "圣光赞歌响彻天际，为全队治疗 250% 生命(消耗 5 信仰)",
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
                        "desc": "终极技——神迹再现，为全队恢复至满血(消耗 10 信仰，团队终极技)",
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
                        "desc": "三转奥义——展开生命圣域，为全队恢复满血并减伤(消耗 6 信仰，终极救场)",
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
                        # v139 链值驱动追加段：命中时连段 +1（现有 res_gain 链值）+ 链值 ≥5 追加段 +1（影追）
                        "combo_gain": 1,
                        "combo_chase": {"at": 5, "power": 0.5, "cap": 1},
                        "desc": "匕刃自影中探出，割向气血正盛的猎物——造成 285% 物理伤害；目标生命高于 70% 时，暗影亲和（伤害＋20%）；链值≥5 时追加 1 段影追(0.5×)",
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
                        "desc": "杀意收敛于呼吸之间，身形与暗影无异——闪避率＋30%（被动，潜行生存）",
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
                        # v139 段数三线投喂：每段命中各 +1 链值（3 段 = +3）；链值 ≥8 时第 4 段只喂链值不喂连击点（旋锋锁死）
                        "multi_feed": {"combo": 1},
                        "spin_lock": 8,
                        "desc": "身影化作三道残像，匕尖如毒蛇连番噬咬——造成 100% 物理伤害×3；自身未受击时，身轻如燕（伤害＋15%）；每段命中各+1 链值，链值≥8 追加段只喂链值(旋锋锁死)",
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
                        # v139 链点回流：终结伤害 > 敌方 max_hp×10% 时链值返还 3 层（打空/闪避/低伤害不回流）
                        "combo_reflow": {"hp_pct": 0.1, "layers": 3},
                        # v139 终结阈值 DSL 消费点：res_cost cp 档即「判断消耗点」（战前可设快刀/满刃/残血/满段档）
                        "finisher_tier": "5cp",
                        "desc": "暗影中跃出的终焉之刃，对残血之敌执行处刑——造成 400% 物理伤害；目标生命低于 40% 时，死亡之舞旋起（伤害＋40%）；终结伤害达标(>敌 max_hp 10%)链值回流 3 层",
                        "cd": 2,
                        "name": "终结·处刑"
                    }
,
                    # v139 新增：链舞（攻线本命·信物）——被动：链值每层终结技增伤 5%→8%（只放大连段终结一轴）
                    "链舞":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "combo_finisher_per_layer",
                            "mult": 0.08
                        },
                        "desc": "链舞翩跹，越连越狠——链值每层终结技增伤 8%(本命·信物，只放大连段终结一轴)",
                        "name": "链舞"
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
                        # v139 主动负向设计：守线技能明确不带 pierce（高毒腐蚀即破防）
                        "no_pierce": True,
                        "desc": "刃锋淬满剧毒，划开血肉的同时种下毒种——造成 285% 物理伤害并叠加 2 层中毒；目标已中毒时，毒素蔓延加速（伤害＋15%）（守线不带破防：毒蚀降防即破防）",
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
                        "desc": "毒师的目光扫过之处，中毒者伤口溃烂得更快——中毒目标受到的伤害＋8%（被动，毒系增伤）",
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
                        # v139 段数即毒层产出率：命中时「毒层投喂 +1」（每段+1 等效产出率翻倍）；毒层 ≥5 时不再吃追加段（守线锁死：毒层 cap5 即资源饱和）
                        "multi_feed": {"poison": 1},
                        "poison_cap_stop": 5,
                        "desc": "双刃各淬异毒，交错斩出双重毒蚀——造成 100% 物理伤害×2并叠加 3 层中毒；目标中毒达 3 层时，毒师专注（伤害＋15%）；每段毒层投喂+1，毒层≥5 停止投喂(饱和)",
                        "name": "双毒刃"
                    }
,
                    "毒爆":                     {
                        "lv": 55,
                        "power": 2.0,
                        "kind": "物理",
                        # v139 改版：吃 3 cp 引爆（mech poison_burst），引爆伤害按毒层 n×atk×0.30（现有引擎已支持），毒层 ≥3 可爆（提前引爆拿虚弱压制的价值保留）
                        "mech": "poison_burst",
                        "mech_val": 1,
                        "res_cost": {
                            "cp": 3
                        },
                        "cond": {
                            "type": "enemy_poison_stacks",
                            "stacks": 3,
                            "mult": 1.3,
                            "label": "剧毒共鸣"
                        },
                        "mp": 12,
                        "finisher_tier": "3cp",
                        "desc": "将猎物体内积攒的剧毒尽数引燃，令其由内溃烂——消耗 3 连击点引爆毒层(每层 n×atk×0.30)；目标中毒达 3 层时，剧毒共鸣迸发（伤害＋30%）",
                        "cd": 2,
                        "name": "毒爆"
                    }
,
                    # v139 新增：蚀骨（守线本命·信物）——被动：毒层引爆伤害 +20%（只放大毒层引爆一轴，不与连段/暴击轴交叉）
                    "蚀骨":                     {
                        "lv": 55,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "poison_burst_amp",
                            "mult": 0.2
                        },
                        "desc": "蚀骨蚀心，毒爆更烈——毒层引爆伤害＋20%(本命·信物，只放大毒层引爆一轴)",
                        "name": "蚀骨"
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
                        "desc": "暗影之力在心脏中搏动，影系技艺愈发锋锐——影系技能伤害＋10%（二转被动）",
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
                        # v139 命中链值 +1（位移保段）
                        "combo_gain": 1,
                        "desc": "自暗影中突进，刃光与身形同时闪现——造成 160% 物理伤害，冷却 2 回合；自身未受击时，突袭更加凌厉（伤害＋20%）；命中链值＋1(位移保段)",
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
                        "desc": "以暗影之力在目标身上烙下双重死印——标记目标，使其受击伤害提升（配合团队斩杀）",
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
                        # v139 链值消费点第二处：链值 ≥3 时伤害 +10%（攻线不加毒）
                        "combo_cond": {"type": "player_combo_stacks", "stacks": 3, "mult": 1.1, "label": "链刃"},
                        "desc": "镰刃般的匕锋划过战场，收割垂死者的生命——造成 190% 物理伤害；目标生命低于 50% 时，收割之势更盛（伤害＋30%）；链值≥3 时伤害＋10%",
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
                        "desc": "毒液在血脉中日夜淬炼，毒性愈发猛烈——毒层伤害＋10%（二转被动，毒强化）",
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
                        "desc": "掷出淬炼过的毒囊，幽绿雾气弥漫全场——造成 80% 全体物理伤害并叠加 2 层中毒，冷却 3 回合（AOE 叠毒）",
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
                        # v139 毒层投喂 +1（+5 层，触达 cap5 上限满毒）
                        "multi_feed": {"poison": 1},
                        "poison_cap_stop": 5,
                        "desc": "匕刃在毒液中淬至极致，一击种下深重毒患——造成 200% 物理伤害并叠加 4 层中毒（深度叠毒）；毒层投喂+1 触达满毒(5 层)",
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
                        # v139 段数三线投喂 T3 形态：每段 +1 链值（5 段 = +5，触发影追临界）；链值 ≥8 锁死不累积
                        "multi_feed": {"combo": 1},
                        "spin_lock": 8,
                        "desc": "身影在敌阵中翩然起舞，匕光织成夺命之网——造成 100% 物理伤害×5（终极连击）；每段命中各+1 链值，链值≥8 锁死不累积",
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
                        # v139 链点回流（同 T1 规则，返还 5 层）
                        "combo_reflow": {"hp_pct": 0.1, "layers": 5},
                        "finisher_tier": "5cp",
                        "desc": "暗影化作绞索缠上咽喉，终结一切反抗——造成 500% 物理伤害（终极爆发）；终结伤害达标链值回流 5 层",
                        "name": "终结·暗影绞杀"
                    }
,
                    "影之国度":                     {
                        "lv": 90,
                        "mp": 0,
                        "power": 0,
                        "kind": "增益",
                        "effect": "shadow_realm",
                        "cd": 6,
                        "res_cost": {
                            "cp": 4
                        },
                        # v139 链值三驱动中的「暴击」驱动：开启期间「影追追加段」概率 ×2
                        "chase_prob_mult": 2,
                        "desc": "撕裂现实踏入影之国度，万物皆在暗影掌控之中——速度＋40%、每回合暴击大幅提升，持续 3 回合（三转奥义）；期间影追追加段概率×2",
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
                        # v139 守线 AOE 每目标独立叠毒，产率 ×目标数（保留语义标注）
                        "multi_feed": {"poison": 1},
                        "desc": "掀起剧毒风暴席卷全场，腐蚀每一寸血肉——造成 150% 全体物理伤害并叠加 4 层中毒，冷却 4 回合（群体毒爆；AOE 每目标独立叠毒）",
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
                        "finisher_tier": "5cp",
                        "desc": "万种剧毒凝于匕尖，噬心蚀骨——造成 300% 物理伤害并叠加 5 层中毒（终极毒杀，满毒大终结）",
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
                        "finisher_tier": "5cp",
                        "desc": "万毒归一，全场敌人体内毒素同时崩解迸发——全体剧毒爆发，毒层越厚崩解越烈（毒爆核弹，三转奥义；满毒 AOE 引爆核弹）",
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
                        "desc": "拳速如疾风掠影——造成 285% 物理伤害；气达到 5 点时拳势叠加(伤害＋50%)",
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
                        "desc": "格斗技巧融入血脉——连招期间伤害＋5%",
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
                        # v139 破绽积蓄：命中时 shaken +5（多目标 AOE 每条注入各自独立）
                        "shaken_gain": 5,
                        "desc": "身体旋起如风暴之眼——造成 130% 物理伤害；目标减速时踢中要害(伤害＋20%)；命中推破绽积蓄+5",
                        "name": "旋风踢"
                    }
,
                    # v139 新增：碎颅势（云海「破头」独立投射，T1-50）——单体 160% 拳；若目标 shaken > 0 则伤害 ×1.25；命中 shaken +15；cd2
                    "碎颅势":                     {
                        "lv": 50,
                        "power": 1.6,
                        "kind": "物理",
                        "combo": "拳",
                        "cd": 2,
                        "mp": 10,
                        "shaken_gain": 15,
                        "cond": {"type": "enemy_shaken_gt", "stacks": 0, "mult": 1.25, "label": "破头"},
                        "desc": "重拳直取颅骨，撼动敌人心神——造成 160% 物理伤害(拳连招)；目标破绽积蓄>0 时伤害×1.25(破头)；命中推破绽积蓄+15",
                        "name": "碎颅势"
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
                        "desc": "气力轰然爆发，灌注全身——造成 280% 物理伤害；自身生命低于 40% 时残血反扑(伤害＋30%)",
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
                        # v139 守线磐核 P1 自主来源：命中磐核 +1（不依赖挨打）
                        "guard_core_gain": 1,
                        "desc": "拳出如铁壁横移——造成 285% 物理伤害并获得防御强化；自身有护盾时拳势更沉(伤害＋15%)；命中磐核+1",
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
                        "desc": "气血盈满时身如大地——生命高于 70% 时防御＋10%",
                        "name": "厚土"
                    }
,
                    # v139 新增：守御姿态（守线签名挂点，非新技能——基础「防御」指令的守线专属化）——
                    # 守线专属：防御指令下受击磐核 +1（P1 受击渠道）+ 未受击保底 +1（P2 蓄能律）；受击只增不减（P3 不清零）
                    "守御姿态":                     {
                        "lv": 40,
                        "mp": 0,
                        "power": 0,
                        "kind": "被动",
                        "passive": {
                            "proc": "guard_stance",
                            "defend_hit_core": 1,
                            "defend_idle_core": 1
                        },
                        "desc": "以拳卸力，守御如磐——防御指令下受击磐核+1、未受击保底+1(P2 蓄能律)；磐核受击不清零(只增不减)",
                        "name": "守御姿态"
                    }
,
                    # v139 新增：磐岩释能（云海守卫 C1 释能斩翻译，T1-48）——清空全部磐核，M = 1.0 + 0.7×核数（3 核 3.10 / 5 核 4.50）；cd4；吃蓄势
                    "磐岩释能":                     {
                        "lv": 48,
                        "power": 1.0,
                        "kind": "物理",
                        "combo": "拳",
                        "cd": 4,
                        "mp": 10,
                        "res_cost": {"guard_core": 1},
                        "consume_all": {"key": "guard_core"},
                        "discharge": {"base": 1.0, "per_core": 0.7},
                        "desc": "引磐核之力凝于一击——清空全部磐核释放，倍率 M = 1.0 + 0.7×核数(3 核 3.10 / 5 核 4.50，线性刻意)；吃蓄势",
                        "name": "磐岩释能"
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
                        "desc": "引气归元，温养创伤——回复 200% 生命；自身生命低于 40% 时气力回涌更盛(治疗量＋50%)",
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
                        "desc": "以彼之力还施彼身——受到伤害时 30% 概率反弹 30% 伤害",
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
                        "desc": "守势之中暗藏杀机——受击时 20% 概率立即以普攻反击",
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
                        "desc": "大地之力筑成护壁——全队减伤 15% 持续 2 回合",
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
                        "desc": "气力在心底凝成泉眼——气获取＋1",
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
                        "desc": "拳影连环不绝——连续出拳 4 次(每次 110% 伤害)，快速凝聚气力",
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
                        "desc": "一拳击出，气浪撕裂长空——造成 260% 破防物理伤害",
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
                        "desc": "心如磐石，不动如山——受到伤害再减 5%",
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
                        "desc": "以守为攻的极致——受击时 30% 概率立即以普攻反击",
                        "name": "反击之王"
                    }
,
                    # v139 新增：磐核爆发（守线中期节奏口，T2-68）——清空 3 核，M = 1.0+0.7×3 = 3.10（固定按 3 核档）；若目标正处破绽被晕，M → 3.60
                    "磐核爆发":                     {
                        "lv": 68,
                        "power": 3.1,
                        "kind": "物理",
                        "combo": "拳",
                        "cd": 4,
                        "mp": 15,
                        "res_cost": {"guard_core": 3},
                        "cond": {"type": "enemy_shaken_gt", "stacks": 0, "mult": 1.161, "label": "破绽震慑"},
                        "desc": "磐核凝为一点轰然迸发——清空 3 核造成 310% 物理伤害(固定 3 核档 M 3.10)；目标处于破绽被晕时威力升至 360%",
                        "name": "磐核爆发"
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
                        "desc": "气力化作守护之墙——为全队张开生命值 20% 的护盾",
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
                        # v139 段数即注入加速：每段命中各 shaken +3（5 段 +15）
                        "shaken_gain": 3,
                        "desc": "拳影快到无形——连续攻击 5 次(每次 130% 伤害)；气达到 8 点时气力充盈(伤害＋30%)；每段命中推破绽积蓄+3(5 段+15)",
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
                        "desc": "气力贯通天地，一拳定乾坤——造成 500% 物理伤害并为全队附加攻击强化",
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
                        "desc": "气机直冲云霄——3 回合内每次攻击大幅增伤",
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
                        "desc": "绝境之中身化磐石——生命低于 30% 时减伤 40%",
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
                        "desc": "气力流转，护佑众生——全队减伤 30% 持续 3 回合",
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
                        "desc": "大地之力加护全队——全队减伤 50% 持续 3 回合",
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
                    # v139 双形态签名：「龙焰初击」——入龙焰当回合自动追加 1 次 70% 真伤（不占行动）
                    "龙焰初击": {"lv": 40, "mp": 0, "power": 0.7, "kind": "真伤",
                                "auto": "dragon_form_enter",
                                "desc": "入龙焰当回合自动追加 1 次 70% 真伤（不占行动，龙焰初击）",
                                "name": "龙焰初击"},
                    "龙息": {"lv": 40, "mp": 20, "power": 0.9, "kind": "真伤",
                             "mech": "burn", "mech_val": 1, "cd": 2,
                             "res_gain": {"dragon_might": 1},
                             # v139 双形态联动：龙焰形态下 90%→108% 吃 +20%（龙息/龙爪/龙焰吐息 白名单）
                             "dragon_form_dmg_bonus": 0.2,
                             "desc": "喉间涌起龙血炽焰，一口龙息焚尽敌甲——造成 90% 真伤(无视全部防御)，附带灼烧 1 层，命中时龙力＋1；龙焰形态下伤害＋20%",
                             "name": "龙息"},
                    "龙鳞": {"lv": 46, "mp": 15, "power": 0, "kind": "增益",
                             "effect": "def_up", "cd": 3,
                             "res_cost": {"dragon_might": 2},
                             # v139 龙鳞 → 龙鳞壁垒：保留自身防御 +45% + 新增团队件（组队时全队防御+30% 3回合）
                             "team": "def_all",
                             "team_def_all": 0.30,
                             "desc": "龙血凝鳞覆体，坚逾玄铁——防御＋45% 持续 2 回合（消耗 2 点龙力）；组队时全队防御＋30% 持续 3 回合(龙鳞壁垒)",
                             "name": "龙鳞"},
                    "龙威": {"lv": 54, "mp": 20, "power": 0, "kind": "增益",
                             "effect": "mon_atk_down", "cd": 4,
                             "res_cost": {"dragon_might": 2},
                             # v139 灼烧联动：命中追加「敌方灼烧层 +1」（真伤+灼烧身份强化）
                             "burn_extra": 1,
                             "desc": "释放上古龙威压向敌阵——敌方攻击－30% 持续 3 回合（消耗 2 点龙力）；命中追加敌方灼烧层+1",
                             "name": "龙威"},
                    # v139 新增：龙威咆哮（补坦克定位嘲讽，T1-48）——kind=嘲讽/team=taunt：强制怪物攻击自己 2 回合；施放即龙力+2；cd3
                    "龙威咆哮": {"lv": 48, "mp": 20, "power": 0, "kind": "嘲讽",
                                "cd": 3, "team": "taunt",
                                "res_gain": {"dragon_might": 2},
                                "desc": "仰天咆哮，龙威震慑全场——强制怪物攻击自己 2 回合(单人=敌方降攻、副本=拉仇恨)，施放即龙力＋2(CD 3)",
                                "name": "龙威咆哮"},
                },
            },
            2: {
                "龙裔斗士": {
                    # v113 修复：原 T2 分支空表，60 级升档无新技能；补 1 主动 + 1 被动（龙血主题）
                    # 主动参考龙息(真伤灼烧)同型，被动参考火之亲和(burn_amp)同型
                    "龙爪": {"lv": 64, "mp": 18, "power": 1.5, "kind": "真伤",
                             "mech": "burn", "mech_val": 2, "cd": 2,
                             "res_gain": {"dragon_might": 2},
                             # v139 双形态联动：龙焰形态下可双形态追加（龙焰中 150%×2 两段，每段+1 力不计满力）
                             "dragon_form_double": {"segments": 2, "per_seg_might": 1},
                             "desc": "利爪裹着灼热龙炎撕裂血肉——造成 150% 真伤(无视防御)，附带灼烧 2 层，命中时龙力＋2；龙焰形态下可双段追加(150%×2)",
                             "name": "龙爪"},
                    "内燃": {"lv": 62, "mp": 0, "power": 0, "kind": "被动",
                             "passive": {"proc": "burn_amp", "mult": 1.15},
                             # v139 龙脉沸腾 → 内燃（火免断供修复）：对免疫灼烧目标，灼烧层以「内燃」形式生效——按真伤轴结算（绕过 immune_dots）+ 灼烧伤害+15% 保留
                             "inner_fire": {"true_dmg": True},
                             "desc": "血脉中的龙之力量翻涌不息——灼烧伤害＋15%（被动）；对免疫灼烧的目标，灼烧层以「内燃」真伤轴生效(绕过免疫)",
                             "name": "内燃"},
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
                                 # v139 双形态联动：龙焰形态下伤害 +20%（白名单）+ 消耗 -1（-5→-4，龙焰形态主导技能）
                                 "dragon_form_dmg_bonus": 0.2,
                                 "dragon_form_cost_reduce": 1,
                                 "desc": "倾尽龙魂之力喷吐熔金烈焰——260% 真伤(无视全部防御)，附带灼烧 2 层，消耗 5 点龙力、命中返还 1 点；龙力≥8 时伤害＋20%(龙威)；龙焰形态下伤害＋20%、消耗-1(-5→-4)",
                                 "name": "龙焰吐息"},
                    # v130.2 新增：满龙力大终结（v130.2f 每层 0.10 收敛：EQ ≈ 6.40 = 3.2 × 2.0）
                    "龙脉终曲": {"lv": 80, "mp": 40, "power": 3.2, "kind": "真伤",
                                 "cd": 5,
                                 "res_cost": {"dragon_might": 10},
                                 # v139 龙焰形态限定（唯一必须龙焰形态才能放的全耗大终结）；龙焰增伤白名单明确排除本技（防 EQ 超限）
                                 "dragon_form_only": True,
                                 "flame_dmg_exempt": True,
                                 "desc": "龙脉燃至顶点，以全副龙血奏响终章——造成 320% 真伤，消耗 10 点龙力（满龙力终极：施放时每点龙力使伤害＋10%）；仅龙焰形态可放(终曲只在龙焰高峰奏响)",
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
                               # v139 凝滞态增伤：凝滞态下伤害 160%→224%（吃 +40% 增伤，不作用于耗沙大爆发）
                               "stasis_dmg_bonus": 0.4,
                               "desc": "拨动时间的丝线，让敌手的动作凝滞如浆——造成 160% 魔法伤害，50% 概率使目标减速 2 回合（时之沙＋1）；时间凝滞中伤害＋40%",
                               "name": "时滞术"},
                    # v139 新增：时间凝滞（云海机械师架设态翻译，开启技）——进入凝滞态（占 1 回合 + 沙1；凝滞中每回合 +1 沙；技能伤害 +40%；受击 +20%；受击 30% 打断；维持 3 回合；cd 3）
                    "时间凝滞": {"lv": 42, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "time_stasis",
                                 "stasis": {"enter_turn": 1, "enter_gain": 1, "gain_per_turn": 1,
                                            "dmg_bonus": 0.4, "taken_bonus": 0.2, "interrupt_rate": 0.3,
                                            "max_turns": 3, "erosion_power": 0.6},
                                 "cd": 3,
                                 "desc": "凝固时间的流速，进入时间凝滞——占 1 回合进入并预装 1 沙；凝滞中每回合沙+1、技能伤害＋40%、受击＋20%；受击 30% 打断(沙保留不清零)；最多维持 3 回合",
                                 "name": "时间凝滞"},
                    "时间裂隙": {"lv": 48, "mp": 20, "power": 1.3, "kind": "魔法",
                                 "multi": 2, "mech": "spd_down", "mech_chance": 0.4, "cd": 2,
                                 "res_cost": {"time_sand": 1},
                                 # v139 凝滞态增伤：凝滞态下 130%×2×1.4=364%
                                 "stasis_dmg_bonus": 0.4,
                                 "desc": "撕裂时间之壁，放出两道错位的时光刃——造成 130%×2 魔法伤害，每段 40% 概率减速（消耗 1 点时之沙）；时间凝滞中伤害＋40%",
                                 "name": "时间裂隙"},
                    "凝时锁": {"lv": 55, "mp": 20, "power": 1.4, "kind": "魔法",
                               "mech": "stun", "mech_chance": 0.35, "cd": 3,
                               "res_cost": {"time_sand": 1},
                               # v139 凝滞态增伤：凝滞态下 196%（只加伤害不加 mech 概率）
                               "stasis_dmg_bonus": 0.4,
                               "desc": "以流逝之光凝成无形锁链，锁死敌手的瞬间——造成 140% 魔法伤害，35% 概率眩晕 1 回合（消耗 1 点时之沙）；时间凝滞中伤害＋40%",
                               "name": "凝时锁"},
                },
            },
            2: {
                "时律术士": {
                    "时间静止": {"lv": 62, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "sleep", "cd": 3,
                                 "res_gain": {"time_sand": 1},
                                 "desc": "吟唱禁忌咒文，令时间在此刻停驻——使目标陷入停滞 2 回合（时之沙＋1）",
                                 "name": "时间静止"},
                    # v139 新增：时之守护（云海稳架/铁壁工事翻译，T2 保命口）——凝滞态限定：受击 -30%、打断率 30%→15%，持续 2 回合，cd4
                    "时之守护": {"lv": 64, "mp": 15, "power": 0, "kind": "增益",
                                 "effect": "stasis_guard",
                                 "stasis_only": True,
                                 "stasis_guard": {"taken_reduce": 0.3, "interrupt_rate": 0.15, "turns": 2},
                                 "cd": 4,
                                 "desc": "以时光之力织成守护壁垒——时间凝滞中受击－30%、打断率 30%→15%，持续 2 回合(CD 4，凝滞态限定)",
                                 "name": "时之守护"},
                    # v139 新增：时间共鸣（云海快弦/绷紧翻译，T2 攒沙加速口）——90% 魔法伤害 + 沙+2，cd3（凝滞态下 126% + 沙+2）
                    "时间共鸣": {"lv": 66, "mp": 20, "power": 0.9, "kind": "魔法",
                                 "res_gain": {"time_sand": 2},
                                 "stasis_dmg_bonus": 0.4,
                                 "cd": 3,
                                 "desc": "让时光与魔力同频共振，沙漏加速流转——造成 90% 魔法伤害，时之沙＋2(CD 3)；时间凝滞中伤害＋40%(126%)",
                                 "name": "时间共鸣"},
                },
            },
            3: {
                "时间领主": {
                    # v130.2f 口径注：时停领域 EQ = 3.0 × 1.3 = 3.9（单体·满沙 5/5 口径；沙漏盈满 cond 已含在倍率内，勿再乘 1.3——T13 曾误算 5.07 = 3.9×1.3；技能无 aoe 标注，不做全体折算；眩晕控场收益另计）
                    "时停领域": {"lv": 90, "mp": 100, "power": 3.0, "kind": "魔法",
                                 "mech": "stun", "mech_chance": 1.0, "cd": 6,
                                 "res_cost": {"time_sand": 3},
                                 "cond": {"type": "player_res_stacks", "res_key": "time_sand", "stacks": 5, "mult": 1.3, "label": "沙漏盈满"},
                                 "desc": "三转奥义，将一方天地拖入静止时域——300% 魔法伤害，必定眩晕 1 回合，消耗 3 点时之沙；时之沙盈满(5)时伤害＋30%(沙漏盈满)",
                                 "name": "时停领域"},
                    # v130.2 新增：5 沙全耗终极（EQ≈4.8+控场）；命中 ≥3 目标 返还 1 沙（时间回环）
                    "时间坍缩": {"lv": 92, "mp": 100, "power": 1.5, "kind": "魔法",
                                 "aoe": "all", "mech": "stun", "mech_chance": 0.5, "reach": 3, "cd": 6,
                                 "res_cost": {"time_sand": 5},
                                 "res_gain": {"time_sand": 1},
                                 "desc": "撕开时间奇点，令战场随钟摆崩塌——150% 全场魔法伤害，全场减速、50% 概率眩晕(时停大炮)，消耗 5 点时之沙，命中 ≥3 目标返还 1 点",
                                 "name": "时间坍缩"},
                    # v130.2 新增：-2 沙保命口（解除减速/刷新技能 cd）
                    "时光回溯": {"lv": 95, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "cleanse", "cd": 4, "reach": 1,
                                 "res_cost": {"time_sand": 2},
                                 "desc": "让指针倒转，把受创的时光重新拨回——解除自身减速并刷新自身技能冷却（消耗 2 点时之沙）",
                                 "name": "时光回溯"},
                    # v139 新增：时间过载（云海过载齐射翻译）——凝滞态限定：350% 单体（无控场，纯输出峰值），-3 沙，立即结束凝滞态，cd5
                    "时间过载": {"lv": 93, "mp": 80, "power": 3.5, "kind": "魔法",
                                 "stasis_only": True,
                                 "res_cost": {"time_sand": 3},
                                 "end_stasis": True,
                                 "cd": 5,
                                 "desc": "将凝滞的时间尽数过载引爆——造成 350% 单体魔法伤害(无控场纯输出峰值)，消耗 3 点时之沙，立即结束时间凝滞(CD 5，凝滞态限定)",
                                 "name": "时间过载"},
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
                             # v139 星轨锁定联动：对锁定目标伤害 ×1.2
                             "lock_mult": 1.2,
                             "desc": "引动星辉坠击，为猎物烙上命定的印记——造成 165% 物理伤害，叠加 1 层猎杀标记（命中时猎印＋1）；对星轨锁定目标伤害×1.2",
                             "name": "星陨"},
                    "占卜": {"lv": 46, "mp": 15, "power": 0, "kind": "增益",
                             "effect": "crit_up", "cd": 3,
                             # v139 占卜期间星移步泄压量 +1（−2 印）
                             "vent_extra": 1,
                             "desc": "仰望星轨占卜吉凶，让下一次出手更加致命——暴击＋20% 持续 3 回合；占卜期间星移步泄压量+1(-2 印)",
                             "name": "占卜"},
                    # v139 新增：星移步（云海游侠「位移泄压」翻译，lv44）——闪避 +30% 持续 2 回合；效果期间成功闪避 → 猎印 −1（泄压）；cd 3
                    "星移步": {"lv": 44, "mp": 10, "power": 0, "kind": "增益",
                               "effect": "dodge_up",
                               "vent_on_dodge": 1,
                               "cd": 3,
                               "desc": "身随星轨游移，闪避命运的刀锋——闪避＋30% 持续 2 回合；成功闪避时猎印−1(泄压，占卜期间−2)；CD 3",
                               "name": "星移步"},
                    # v139 新增：星轨锁定（云海弓手「任意部位任选」翻译，lv50）——消耗 1 印；锁定指定目标（任意站位），3 回合内对锁定目标攻击无视站位直击；锁定期间首次命中额外标记 +1；对锁定目标暴击时猎印额外 +1；门槛：猎印 ≥2 才可施放；cd 4
                    "星轨锁定": {"lv": 50, "mp": 15, "power": 0, "kind": "增益",
                                 "effect": "star_lock",
                                 "res_cost": {"hunt_mark": 1},
                                 "star_lock": {"min_marks": 2, "duration": 3, "cd": 4, "mark_extra": 1, "crit_mark_extra": 1},
                                 "cd": 4,
                                 "desc": "以星光锁定命定之敌——消耗 1 印锁定指定目标(无视站位直击，3 回合)；首命中标记+1、对锁定目标暴击猎印+1；门槛猎印≥2 才可施放(CD 4)",
                                 "name": "星轨锁定"},
                    # v130.2：命运之轮 定为 T1 教学档消耗（-1 印）+ power 微调
                    "命运之轮": {"lv": 55, "mp": 30, "power": 1.6, "kind": "魔法",
                                 "multi": 3, "cd": 4,
                                 "res_cost": {"hunt_mark": 1},
                                 # v139 星轨锁定联动：对锁定目标 3 段全中时猎印 +1
                                 "lock_full_hit_mark": 1,
                                 "desc": "转动命运之轮，三连星芒接连噬咬猎物——造成 160% 魔法伤害连击 3 次（消耗 1 点猎印）；对锁定目标 3 段全中时猎印+1",
                                 "name": "命运之轮"},
                },
            },
            2: {
                "星相师": {
                    "星辰之力": {"lv": 62, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"stat": "luck", "add": 0.05},
                                 "desc": "沐浴星光而行，幸运随之眷顾——幸运＋5%（被动）",
                                 "name": "星辰之力"},
                    # v130.2 新增：T2 攒印加速口（与星陨双攒，把 5 印攒满压到 ~2 回合）
                    "星轨连射": {"lv": 64, "mp": 15, "power": 1.2, "kind": "物理",
                                 "multi": 2, "mech": "mark", "mech_val": 1, "cd": 2,
                                 "res_gain": {"hunt_mark": 1},
                                 # v139 星轨锁定联动：对锁定目标 2 段全中时猎印 +1 追加
                                 "lock_full_hit_mark": 1,
                                 "desc": "循着星轨连发两箭，星辉再度烙上印记——造成 120%×2 物理伤害，叠加 1 层猎杀标记（命中时猎印＋1）；对锁定目标 2 段全中时猎印+1 追加",
                                 "name": "星轨连射"},
                
                    # v139 新增：星光庇护（生存四缺修复主口，lv66）——获得 15% 最大生命护盾（吃 shield_power，3 回合）；持盾期间闪避 +10%；护盾被击破时猎印 +1（星光余烬·命运在受创时仍回馈一印）；cd 5
                    "星光庇护": {"lv": 66, "mp": 25, "power": 0, "kind": "增益",
                                 "effect": "shield_all",
                                 "shield_pct": 0.15,
                                 "shield_dodge": 0.1,
                                 "break_mark_back": 1,
                                 "cd": 5,
                                 "desc": "星光凝成命运之盾——获得 15% 最大生命护盾(吃盾量加成，3 回合)；持盾期间闪避＋10%；护盾被击破时猎印＋1(星光余烬)；CD 5",
                                 "name": "星光庇护"},
                    },
            },
            3: {
                "命运编织者": {
                    "星祭": {"lv": 75, "mp": 35, "power": 2.0, "kind": "物理",
                             "mech": "mark", "mech_val": 2, "cd": 4,
                             "res_cost": {"hunt_mark": 3},
                             # v139 星轨锁定联动：对锁定目标伤害 ×1.2（大终结前奏）
                             "lock_mult": 1.2,
                             "desc": "以猎印为祭、星光为刃，劈向命定之敌——造成 200% 物理伤害，叠加 2 层猎杀标记，消耗 3 点猎印；对星轨锁定目标伤害×1.2",
                             "name": "星祭"},
# v130.2 新增：大终结前奏（+2 印 + 满印暴击抬升）
                    "星辉祈愿": {"lv": 78, "mp": 25, "power": 0, "kind": "增益",
                                 "effect": "crit_up", "cd": 5,
                                 "res_gain": {"hunt_mark": 2},
                                 # v139 深排：祈愿期间流星陨落可延迟 1 回合释放（深排，伤害仍享满印 cond ×1.15）
                                 "vent_deep_delay": 1,
                                 "desc": "向星海许下祈愿，星光凝聚成新的印记——暴击率＋20% 持续 3 回合，施放后猎印＋2（大终结前奏）；祈愿期间流星陨落可延迟 1 回合释放(深排)",
                                 "name": "星辉祈愿"},
                    # v130.2 新增：5 印大终结·EQ≈4.8（满印 cond ×1.15；通用标记易伤每层＋20% 叠加）
                    "流星陨落": {"lv": 80, "mp": 40, "power": 3.2, "kind": "物理",
                                 "pierce": True, "reach": 3, "cd": 6,
                                 "res_cost": {"hunt_mark": 5},
                                 "cond": {"type": "player_res_stacks", "res_key": "hunt_mark", "stacks": 5, "mult": 1.15, "label": "流星盈满"},
                                 # v139 升级为排气核心：满 5 印 → 下回合开始自动强制释放（系统执行、托管照常）；玩家可提前手动释放（常规排气）；排气后下回合首次命中猎印额外 +1（排气余烬）；reach/pierce/易伤全保留
                                 "vent_auto": True,
                                 "vent_recovery_extra": 1,
                                 "desc": "召唤流星群终结被星光标记的猎物——320% 致命一击，消耗 5 点猎印；目标带标记受易伤(每层＋20%)，猎印满(5/5)施放伤害＋15%(流星盈满)；满 5 印下回合自动强制释放(节流阀)，排气后首命中猎印+1(排气余烬)",
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
                                 # v139 铺场即挂标记：召唤骷髅自动对当前主目标附加 1 层「灵魂标记」（诅咒，不可驱散，最多 3 层，每层全队对其伤害 +6%）
                                 "soul_mark_on_summon": 1,
                                 "desc": "吟唱悼咏，唤出墓穴中的白骨仆从——召唤骷髅兵加入战斗(上限 3，自动攻击并为你挡刀)，消耗 2 点悼咏；召唤时自动对主目标附加 1 层灵魂标记(每层全队对其伤害+6%，不可驱散)",
                                 "name": "召唤骷髅"},
                    "亡灵狂暴": {"lv": 48, "mp": 20, "power": 0, "kind": "增益",
                                 "effect": "atk_up", "cd": 3,
                                 "desc": "以悼咏催动亡者的凶性，白骨之军杀意暴涨——攻击＋30% 持续 3 回合",
                                 "name": "亡灵狂暴"},
                    # v130.2 新增：暗蚀攒点技（转职第一秒即攒悼咏）
                    "死亡汲取": {"lv": 44, "mp": 15, "power": 1.2, "kind": "魔法",
                                 "lifesteal": 0.5, "cd": 2, "reach": 2,
                                 "res_gain": {"canticle": 1},
                                 # v139 诅咒联动：对带「骨噬/灵魂标记」目标伤害 ×1.15（取云海「杖击命中标记处 +1 孢子」的自主注入精神）
                                 "curse_dmg_mult": 1.15,
                                 "desc": "以暗蚀之力啃噬生灵，将其生命据为己有——造成 120% 暗蚀伤害，吸血回复等于伤害的一半（悼咏＋1）；对带诅咒(骨噬/灵魂标记)目标伤害×1.15",
                                 "name": "死亡汲取"},
                },
            },
            2: {
                "亡魂引渡者": {
                    "死亡契约": {"lv": 62, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"proc": "death_pact"},
                                 "desc": "与亡者缔结的契约在生死之际应验——致命伤害由召唤物代受(以 20% 生命存活，每场 1 次，被动)",
                                 "name": "死亡契约"},
                    # v130.2 新增：一档神迹·铺场（T2 中消耗口）
                    "墓穴低语": {"lv": 64, "mp": 20, "power": 0.8, "kind": "魔法",
                                 "aoe": "all", "summon": "skeleton", "cd": 3, "reach": 2,
                                 "res_cost": {"canticle": 3},
                                 # v139 诅咒出口：施放后对主目标挂 1 层「骨噬」（若已存在则续期至 3 回合）
                                 "curse_apply": {"key": "curse", "turns": 3, "renew": True},
                                 "desc": "墓穴深处的低语化作蚀骨寒风，吹醒沉睡的白骨——造成 80% 全体暗蚀伤害并召唤 1 只骷髅，消耗 3 点悼咏；施放后对主目标挂 1 层骨噬(全队对其伤害+20%+命中+10%，续期 3 回合)",
                                 "name": "墓穴低语"},
                },
            },
            3: {
                "黯灵主教": {
                    "骷髅海": {"lv": 70, "mp": 30, "power": 0, "kind": "增益",
                               "summon": "skeleton", "effect": "atk_up", "cd": 5,
                               "res_cost": {"canticle": 5},
                               # v139 白骨之潮：若场上存活骷髅 <2 额外召唤 1 只；施放时每只在场骷髅对主目标附加 1 层灵魂标记（封顶 3 层）
                               "bone_tide": {"min_skeleton": 2, "extra_summon": 1},
                               "soul_mark_per_skeleton": 1,
                               "desc": "打开墓门，让白骨之潮汹涌而出——召唤骷髅兵并攻击＋30% 持续 3 回合，消耗 5 点悼咏；骷髅<2 时额外召唤 1 只(白骨之潮)，每只在场骷髅对主目标附加 1 层灵魂标记(封顶 3 层)",
                               "name": "骷髅海"},
                    # v139 新增：死歌·战死歌（云海战歌翻译，T3）——-5 悼咏：全队攻击 +25%（3 回合，team=atk_all）；自身只享受 55%；施放时场上每只骷髅向主目标追加一次 60% 物理爪击（不占行动）
                    "死歌·战死歌": {"lv": 72, "mp": 40, "power": 0, "kind": "增益",
                                    "effect": "atk_up", "team": "atk_all", "cd": 4,
                                    "res_cost": {"canticle": 5},
                                    "self_gain_factor": 0.55,
                                    "dirge": "war",
                                    "skeleton_claw": {"power": 0.6, "free": True},
                                    "desc": "奏响战争死歌，亡灵军团杀气冲天——全队攻击＋25% 持续 3 回合(自身仅享 55%)；场上每只骷髅向主目标追加一次 60% 物理爪击(不占行动)",
                                    "name": "死歌·战死歌"},
                    # v139 新增：死歌·守死歌（云海守歌翻译）——-5 悼咏：全队减伤 20% + 每回合全队回复 5% 生命（3 回合）；自身 only 55%；死亡契约若已触发过，本歌期间额外获得第 2 次免死
                    "死歌·守死歌": {"lv": 74, "mp": 40, "power": 0, "kind": "增益",
                                    "effect": "reduce_all", "reduce_all": 0.2, "team": "reduce_all", "cd": 4,
                                    "team_regen": 0.05,
                                    "res_cost": {"canticle": 5},
                                    "self_gain_factor": 0.55,
                                    "dirge": "guard",
                                    "death_pact_extra": True,
                                    "desc": "奏响守护死歌，亡者之墙庇护全军——全队减伤 20% 并每回合回复 5% 生命(3 回合，自身仅享 55%)；死亡契约触发过则本歌期间获得第 2 次免死",
                                    "name": "死歌·守死歌"},
                    # v139 新增：死歌·疾死歌（云海疾歌翻译）——-5 悼咏：全队速度 +30%（3 回合）；自身 55%；全体骷髅本回合行动 +1 次（亡灵节拍）
                    "死歌·疾死歌": {"lv": 76, "mp": 40, "power": 0, "kind": "增益",
                                    "effect": "spd_up", "team": "spd_all", "cd": 4,
                                    "res_cost": {"canticle": 5},
                                    "self_gain_factor": 0.55,
                                    "dirge": "swift",
                                    "undead_beat": {"extra_action": 1},
                                    "desc": "奏响疾速死歌，白骨之军踏碎时间——全队速度＋30% 持续 3 回合(自身仅享 55%)；全体骷髅本回合行动＋1 次(亡灵节拍)",
                                    "name": "死歌·疾死歌"},
                    # v130.2 新增：二档中消耗·吃掉亡灵换暗蚀潮
                    "献祭暗焰": {"lv": 76, "mp": 30, "power": 1.3, "kind": "魔法",
                                 "aoe": "all", "cd": 4, "reach": 2,
                                 "res_cost": {"canticle": 5},
                                 # v139 补满档 cond（P1 修复）：悼咏满 10 时伤害 ×1.3（复用现有 cond 注册表，引擎零改动）
                                 "cond": {"type": "player_res_stacks", "res_key": "canticle", "stacks": 10, "mult": 1.3, "label": "满档挽歌"},
                                 "desc": "将亡灵献入暗焰，蚀骨火海吞没战场——130% 全体魔法伤害，消耗 1 只骷髅追加 60% 全体暗蚀，消耗 5 点悼咏；悼咏满 10 时伤害×1.3(满档挽歌)",
                                 "name": "献祭暗焰"},
                    # v139 新增：骸骨洪流（云海孢爆/孢雨翻译，个人伤害出口）——-8 悼咏：消耗全部存活骷髅（每只 90% 全体暗蚀）；对带诅咒目标追加 +30% 伤害；CD 5
                    "骸骨洪流": {"lv": 78, "mp": 45, "power": 0.9, "kind": "魔法",
                                 "aoe": "all", "cd": 5, "reach": 2,
                                 "res_cost": {"canticle": 8},
                                 "consume_skeletons": True,
                                 "curse_bonus": 0.3,
                                 "desc": "将白骨之军化为蚀骨洪流吞没战场——消耗全部存活骷髅(每只 90% 全体暗蚀)，对带诅咒目标追加伤害＋30%(CD 5，无骷髅不可用)",
                                 "name": "骸骨洪流"},
                    # v130.2 新增：三档满档挽歌大终结（EQ = 3.0 全体 ×1.6 ≈ 4.8）
                    "安魂曲": {"lv": 80, "mp": 40, "power": 3.0, "kind": "魔法",
                               "aoe": "all", "cd": 6, "reach": 2,
                               "res_cost": {"canticle": 10},
                               "desc": "奏响送葬终章，以暗蚀淹没战场——300% 全体暗蚀伤害，以伤害值一半回复自身，消耗 10 点悼咏（满档挽歌）",
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
                               # v139 影舞态联动：影舞态内追加 1 段（0.5×，吃潜行乘区；追加段不计影步不计满步）
                               "dance_extra_seg": {"power": 0.5, "no_step": True},
                               "desc": "幽影自暗处扑出，匕刃吻向气血充盈的猎物——造成 130% 物理伤害，对满血目标必定暴击（暴击命中时影步＋1）；影舞态内追加 1 段(0.5×，不计影步)",
                               "name": "幽影袭"},
                    "暗影步": {"lv": 52, "mp": 20, "power": 0, "kind": "增益",
                               "effect": "stealth", "cd": 4,
                               "res_cost": {"shadow_step": 1},
                               # v139 战前可配「伏击预案：影步≥3 才入潜行」（剑客阈值 DSL）
                               "ambush_threshold": 3,
                               "desc": "一步踏碎光影，身形没入暗影之中——消耗 1 点影步进入潜行，下次攻击必定暴击（战前可配伏击预案：影步≥3 才入潜行）",
                               "name": "暗影步"},
                    # v139 新增：噬影（补 T1 技能数 + 主动保障口，lv48）——100% 物理；命中时若目标未满血，闪避下回合攻击 +20%；影步+1（非暴击也+1）
                    "噬影": {"lv": 48, "mp": 12, "power": 1.0, "kind": "物理",
                             "mech": "shadow", "mech_val": 1, "cd": 2,
                             "res_gain": {"shadow_step": 1},
                             "dodge_next_if_hurt": 0.2,
                             "desc": "噬咬猎物未愈的伤口，暗影随之侵蚀——造成 100% 物理伤害；目标未满血时闪避下回合攻击＋20%；影步+1(非暴击也+1)",
                             "name": "噬影"},
                },
            },
            2: {
                "暮刃大师": {
                    "幽影连刺": {"lv": 62, "mp": 25, "power": 1.2, "kind": "物理",
                                 "multi": 2, "mech": "shadow", "mech_val": 1, "cd": 2,
                                 "res_gain": {"shadow_step": 1},
                                 # v139 影舞态联动：影舞态内追加 1 段（不计影步不计满步）
                                 "dance_extra_seg": {"power": 0.5, "no_step": True},
                                 "desc": "幽影化作两道残像接连刺出，皆奔要害而去——造成 120% 物理伤害×2，对满血目标必定暴击（2 段全暴击时影步＋2）；影舞态内追加 1 段(不计影步)",
                                 "name": "幽影连刺"},
                    # v139 新增：暗影分身（补 T2 技能数 + 唯一资源保险，lv66）——增益：立即 +2 影步，受击不清空持续 2 回合（分身代受）；CD 6
                    "暗影分身": {"lv": 66, "mp": 25, "power": 0, "kind": "增益",
                                 "effect": "shadow_clone",
                                 "res_gain": {"shadow_step": 2},
                                 "hit_clear_protect": 2,
                                 "cd": 6,
                                 "desc": "裂出暗影分身代受刀锋——立即获得 2 点影步，受击不清空持续 2 回合(分身代受)；CD 6",
                                 "name": "暗影分身"},
                },
            },
            3: {
                "暮影收割者": {
                    "幽影刃": {"lv": 75, "mp": 35, "power": 2.0, "kind": "物理",
                               "mech": "shadow", "mech_val": 1, "cd": 4,
                               "res_cost": {"shadow_step": 3},
                               # v139 影舞态内潜行乘区 ×1.15 叠乘
                               "dance_stealth_mult": 1.15,
                               "desc": "凝聚暗影为刃，自潜行中一击破敌——造成 200% 物理伤害，对满血目标必定暴击，消耗 3 点影步（潜行出手时伤害×1.15；影舞态内乘区叠乘）",
                               "name": "幽影刃"},
                    # v130.2 新增：影步 4 步大终结（EQ = 3.2 × 1.5 = 4.8；暗影步 1 + 终结 4 = 5 = 影步上限，潜行伏击连招可达成）
                    "终结·破影一击": {"lv": 80, "mp": 45, "power": 3.2, "kind": "物理",
                                 "mech": "shadow", "mech_val": 1, "cd": 6, "reach": 1,
                                 "res_cost": {"shadow_step": 4},
                                 # v139 影舞态内潜行乘区 ×1.5 叠乘（EQ 可达 4.8×1.5≈7.2 窗口上限）
                                 "dance_stealth_mult": 1.15,
                                 "desc": "破开影幕的终焉一击，伏于暗影中的杀机倾泻而出——造成 320% 致命一击，消耗 4 点影步；潜行伏击出手时伤害×1.15（影舞态内乘区叠乘，受乘区封顶）",
                                 "name": "终结·破影一击"},
                    # v139 新增：绞杀·缚影步（主动负向设计，云海蚀牙连精神，lv85）——190% 物理 + 目标攻-20% 持续 2 回合；仅影舞态可用；不攒影步、不触发满步
                    "绞杀·缚影步": {"lv": 85, "mp": 35, "power": 1.9, "kind": "物理",
                                     "dance_only": True,
                                     "enemy_atk_down": 0.2,
                                     "no_step_gain": True,
                                     "cd": 4,
                                     "desc": "影舞中绞杀猎物，缚住其影——造成 190% 物理伤害并使目标攻击－20% 持续 2 回合；仅影舞态可用(不攒影步、不触发满步)",
                                     "name": "绞杀·缚影步"},
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
                               # v139 撼岳之势联动：命中推条 +1 层（连招命中即推条，共用一次命中判定无额外 roll）
                               "shaken_push": 1,
                               "desc": "拳势如裂岩冲锋——造成 130% 物理伤害，命中叠加 1 层气力(每层伤害＋12%)(禅意＋1)；命中推撼岳之势+1 层",
                               "name": "裂岩冲"},
                    # v130.2 更名（气力连打→蓄劲连打）+ 挂禅意攒点
                    "蓄劲连打": {"lv": 55, "mp": 20, "power": 1.4, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_gain": {"zen": 1},
                                 # v139 撼岳之势联动：命中推条 +1 层
                                 "shaken_push": 1,
                                 "desc": "蓄满劲力连环击出——造成 140% 物理伤害(拳连招，衔接拳-踢-掌三连追加)(禅意＋1)；命中推撼岳之势+1 层",
                                 "name": "蓄劲连打"},
                    # v130.2 新增：T1 主轴（-3 禅意·EQ≈4.65）
                    "裂岳连击": {"lv": 48, "mp": 10, "power": 1.9, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_cost": {"zen": 3},
                                 # v139 撼岳之势联动：命中推条 +1 层
                                 "shaken_push": 1,
                                 "desc": "拳劲足以裂开山岳——造成 190% 物理伤害，每点禅意威力＋12%，消耗 3 点禅意；命中推撼岳之势+1 层",
                                 "name": "裂岳连击"},
                    # v130.2 新增：换气攒点技（转进隐藏线第一回合即摸到 zen）
                    "苦行呼吸": {"lv": 42, "mp": 5, "power": 0, "kind": "增益",
                                 "effect": "def_up", "cd": 2,
                                 "res_gain": {"zen": 1},
                                 "desc": "以苦行磨砺身心，气机随之沉淀——获得防御强化(禅意＋1)",
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
                                 # v139 撼岳之势联动：每段命中推条 +1 层
                                 "shaken_push": 1,
                                 "desc": "蓄势待发，连击两段——造成 120%×2 物理伤害(拳连招深化)(禅意＋1)；每段命中推撼岳之势+1 层",
                                 "name": "势蓄连打"},
                    # v130.2 新增：2 禅意轻倾泻（慢热期小口释放）
                    "律动连打": {"lv": 66, "mp": 14, "power": 1.8, "kind": "物理",
                                 # v139 顺带修复：combo 拳→踢（修三连 tag 撞车——淬势者 6 个 combo 技全「拳」tag 导致三连永不触发）
                                 "combo": "踢", "cd": 2,
                                 "res_cost": {"zen": 2},
                                 # v139 撼岳之势联动：命中推条 +1 层
                                 "shaken_push": 1,
                                 "desc": "拳随呼吸律动，一击重过一击——造成 180% 物理伤害(踢连招，衔接拳-踢-掌三连)，每点禅意威力＋12%，消耗 2 点禅意；命中推撼岳之势+1 层",
                                 "name": "律动连打"},
                },
            },
            3: {
                "撼岳者": {
                    "气爆": {"lv": 75, "mp": 35, "power": 1.8, "kind": "物理",
                             # v139 mech 修复：chi_burst（引爆气力层）→ 纯禅意消耗（移除气力层依赖，每层禅意 +15% 追加直接按倾泻公式结算，EQ 3.10 不变）
                             "res_cost": {"zen": 5},
                             "cd": 4,
                             # v139 撼岳之势联动：命中推条 +2 层
                             "shaken_push": 2,
                             "desc": "将周身禅意压缩至极限后猛然迸发——造成 180% 物理伤害，每层禅意追加 15% 伤害(纯禅意倾泻公式)，消耗 5 点禅意(EQ 3.10)；命中推撼岳之势+2 层",
                             "name": "气爆"},
                    # v130.2 新增：满 10 禅意大终结（实算 EQ≈5.50 = 2.5 × 2.2，无破势 ×1.1）
                    "撼岳·终焉": {"lv": 80, "mp": 30, "power": 2.5, "kind": "物理",
                                  "combo": "拳", "cd": 6,
                                  "res_cost": {"zen": 10},
                                  # v139 撼岳之势联动：满条震慑时可释放；命中推条 +2 层
                                  "shaken_push": 2,
                                  "shaken_stun_gate": True,
                                  "desc": "撼动山岳的终焉之拳——造成 250% 致命一击，每点禅意威力＋12%，消耗 10 点禅意；满条震慑时可释放，命中推撼岳之势+2 层",
                                  "name": "撼岳·终焉"},
                    # v130.2 新增：T3 续势攒点（禅意 +2）
                    "裂岳绝式": {"lv": 82, "mp": 16, "power": 1.3, "kind": "物理",
                                 "combo": "拳", "cd": 2,
                                 "res_gain": {"zen": 2},
                                 # v139 撼岳之势联动：命中推条 +1 层
                                 "shaken_push": 1,
                                 "desc": "裂岳绝式起手，气劲暗涌——造成 130% 物理伤害(禅意＋2)；命中推撼岳之势+1 层",
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
                "desc": "龙魂寄于血脉，诸般元素难侵——元素抗性＋5%（龙裔誓约觉醒即得，被动）",
                "name": "龙魂",
            },
            "sk_huo_zhi_qin_he": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"proc": "burn_amp", "mult": 1.2},
                "desc": "血脉与火焰共鸣，灼烧愈发炽烈——灼烧伤害＋20%（龙裔誓约觉醒即得，被动）",
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
                "desc": "每一次攻击都拨动时间的节拍——攻击命中时，时间之沙＋1（时咒法师觉醒即得，被动）",
                "name": "魔力贯穿",
            },
            "sk_shi_jian_gan_zhi": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "cdr", "add": 0.05},
                "desc": "对时间流逝的敏锐感知，让咒语衔接更快——冷却缩减＋5%（时咒法师觉醒即得，被动）",
                "name": "时间感知",
            },
        },
    },
    "cls_wild_hunter": {
        "skills": {
            "sk_p_lie_shou_ben_neng": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "crit_mark", "mult": 0.1},
                "desc": "猎手对猎物的直觉，让每一次出手都直指要害——对带标记目标暴击＋10%（星语者觉醒即得，被动）",
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
                "desc": "亡者的护佑缠身，伤痛与悼咏一同沉淀——受击减伤 5%，受击时悼咏＋1（暗影神谕觉醒即得，被动）",
                "name": "墓穴护甲",
            },
        },
    },
    "cls_shadow_blade": {
        "skills": {
            # v139：暗影之舞（与基础刺客共享 ID）→ 暮刃之舞（独有被动，拆共享 ID 修复）——潜行暴伤 +30% 保留 + 追加「影舞态内 CD 全 -1」
            "«redacted:sk_…»": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"stat": "stealth_crit_dmg", "mult": 0.3},
                "dance_cd_reduce": 1,
                "desc": "与暗影共舞，藏于黑暗中的刃更加致命——潜行状态下暴击伤害＋30%；影舞态内全技能冷却-1(暮刃之舞，觉醒即得，被动)",
                "name": "暮刃之舞",
            },
        },
    },
    "cls_wu_sheng": {
        "skills": {
            # v139：气力调和（与基础拳师共享 ID）→ 禅心通明（拆独立 ID 修复，P3 零关联被动）——受击时 +1 禅意（proc dmg_taken + res_gain 1）
            "«redacted:sk_…»": {
                "lv": 40, "mp": 0, "power": 0, "kind": "被动",
                "passive": {"proc": "dmg_taken", "res_gain": 1},
                "desc": "受创愈深，禅心愈明——受击时 +1 禅意(禅心通明，淬势者觉醒即得，被动；出招/连击/受击三路积攒不变)",
                "name": "禅心通明",
            },
        },
    },
}
PLAYER_SKILLS.update(_ADD_HIDDEN_SKILLS)

# ===== v151 职业体系重构：6 基础职业新技能表（整体替换，overrides 已含旧 key 兼容映射）=====
# 来源：game/data/skills_v151_overrides.py（由 workspace/skills_v151_*.py 归一化生成）
# 策略：PLAYER_SKILLS 整体替换 6 职业段（同名技能沿用旧 key，玩家存档兼容；纯新增用新 key）
#      BRANCH_SKILLS 整体替换 6 职业段（分支 key 1/2/3 保留，技能 key 统一中文名）
try:
    from .skills_v151_overrides import _V151_PLAYER_SKILLS, _V151_BRANCH_SKILLS
    PLAYER_SKILLS.update(_V151_PLAYER_SKILLS)
    BRANCH_SKILLS.update(_V151_BRANCH_SKILLS)
except Exception as _e:  # pragma: no cover - v151 覆盖层失败时静默降级（不影响旧数据加载）
    print(f"[skills] v151 override import failed: {_e}")

# v95.23 职业导师进阶技能：各城导师专属，普通『技能学习』学不到，需找导师对话学习
# 格式与 PLAYER_SKILLS 技能一致（battle/engine 按名字查定义）
TUTOR_SKILLS = {
    "cls_zhan_shi": {
    },
    "cls_fa_shi": {
        "sk_mo_li_mai_chong": {
            "lv": 6, "mp": 10, "power": 1.7, "kind": "魔法",
            "mech": "arcane", "cd": 2,
            "desc": "凝集魔力脉冲轰向敌阵，奥术之力在命中的瞬间奔涌——造成 170% 魔法伤害（导师秘传，CD 2）",
            "name": "魔力脉冲",
        },
    },
    "cls_you_xia": {
    },
    "cls_mu_shi": {
        "sk_sheng_guang_cheng_jie": {
            "lv": 6, "mp": 10, "power": 1.4, "kind": "魔法",
            "cd": 2,
            "desc": "召来圣光凝成惩戒之剑劈落——造成 140% 魔法伤害，对黑暗生物格外克制（导师秘传，CD 2）",
            "name": "圣光惩戒",
        },
        "sk_jiu_shu_zhi_guang": {
            "lv": 10, "mp": 15, "power": 1.5, "kind": "治疗",
            "cd": 2, "team": "heal_all",
            "desc": "高举圣徽，救赎之光洒遍全队——治疗全队 150% 生命（团队技能，冒险中全队共享，CD 2）",
            "name": "救赎之光",
        },
    },
    "cls_ci_ke": {
        "sk_cui_du_zhi_ren": {
            "lv": 10, "mp": 10, "power": 1.3, "kind": "物理",
            "mech": "poison", "mech_chance": 0.5, "cd": 3,
            "desc": "导师亲授的淬毒杀法，匕刃划过时毒液渗入伤口——造成 130% 物理伤害，50% 概率使目标中毒 2 回合",
            "name": "淬毒之刃",
        },
    },
    "cls_wu_seng": {
        "sk_beng_quan_lie": {
            "lv": 6, "mp": 8, "power": 1.6, "kind": "物理",
            "mech": "stun", "mech_chance": 0.2, "cd": 2,
            "desc": "拳锋直取骨骼要害——造成 160% 物理伤害，20% 概率击晕目标",
            "name": "裂骨击",
        },
        "sk_jin_gang_ti": {
            "lv": 10, "mp": 12, "power": 0, "kind": "增益",
            "effect": "def_up", "cd": 3,
            "desc": "身如磐石，傲然挺立——防御＋45% 持续 2 回合",
            "name": "磐石之体",
        },
    },
}
