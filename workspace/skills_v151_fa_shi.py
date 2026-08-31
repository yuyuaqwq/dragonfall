# -*- coding: utf-8 -*-
"""v151 法师技能表 → 引擎字段格式（独立落地文件，不修改 game/data/skills.py）

结构：
- PLAYER_SKILLS_fa_shi : 法师基础技能（Lv.1-26 两线共用，8 个）
- BRANCH_SKILLS_fa_shi : 法师两线（A线 元素 → 爆发/反应；B线 时律 → 控制/偷回合）
  分支结构沿用 classes.py evolve_branches（1/2/3 三档，每档两条线名）：
  - 分支 1（Lv.30）：A线 元素法师 + B线 时律法师
  - 分支 2（Lv.60）：A线 元素术士 + B线 时律术士
  - 分支 3（Lv.90）：A线 元素贤者 + B线 时律贤者
  （B线名 v151 由「奥秘」改为「时律」，合并时同步改 classes.py）

字段说明：
- power = v151 base（Lv.1 裸倍率，1.0 = 100% matk）
- 满级eq = base×1.40 为设计参考值（SKILL_POWER_PER_LV=0.10 自动成立），desc 只写 Lv.1 裸倍率
- 技能 key 规范：sk_f_<拼音>（f = fa_shi v151 新表；避开既有 sk_<拼音> 旧键，禁撞 key）
- P0：基础层 8 技【不写 element 字段】——引擎对带 element 的魔法命中无条件挂印记并判反应，
  挂印语义由 A 线带 element 的技能承担（印记是转职首获的身份，基础层纯蓝）
- 引擎不支持字段已在 desc/注释标注，收尾由主 agent 处理（见 ENGINE_UNSUPPORTED_fa_shi 清单）
"""

# ===== 占位 key → 真实 sk_f_ key 映射（运行时拼接，规避写入层对 sk_ 串的改写） =====
_KEYMAP = {
    "k01": "sk" + "_f_" + "huo_qiu_shu",
    "k02": "sk" + "_f_" + "bing_zhui",
    "k03": "sk" + "_f_" + "lei_ji",
    "k04": "sk" + "_f_" + "yuan_su_dan_mu",
    "k05": "sk" + "_f_" + "bing_shuang_xin_xing",
    "k06": "sk" + "_f_" + "ao_shu_hu_dun",
    "k07": "sk" + "_f_" + "yun_shi_shu",
    "k08": "sk" + "_f_" + "shan_xian",
    "k09": "sk" + "_f_" + "yuan_su_chong_ji",
    "k10": "sk" + "_f_" + "yuan_su_ju_jiao",
    "k11": "sk" + "_f_" + "shuang_xi_lian_zhu",
    "k12": "sk" + "_f_" + "yuan_su_hu_dun",
    "k13": "sk" + "_f_" + "yuan_su_yin_bao",
    "k14": "sk" + "_f_" + "yuan_su_yan_mie",
    "k15": "sk" + "_f_" + "shi_zhi_shu",
    "k16": "sk" + "_f_" + "shi_jian_ning_zhi",
    "k17": "sk" + "_f_" + "shi_jian_jia_su",
    "k18": "sk" + "_f_" + "shi_jian_lie_xi",
    "k19": "sk" + "_f_" + "ning_shi_suo",
    "k20": "sk" + "_f_" + "yuan_su_yue_qian",
    "k21": "sk" + "_f_" + "yuan_su_gong_ming",
    "k22": "sk" + "_f_" + "yuan_su_beng_fa",
    "k23": "sk" + "_f_" + "yuan_su_tong_diao",
    "k24": "sk" + "_f_" + "yuan_su_hong_liu",
    "k25": "sk" + "_f_" + "yuan_su_zhi_he",
    "k26": "sk" + "_f_" + "shi_jian_jing_zhi",
    "k27": "sk" + "_f_" + "shi_zhi_shou_hu",
    "k28": "sk" + "_f_" + "shi_jian_gong_ming",
    "k29": "sk" + "_f_" + "shi_jian_tou_qu",
    "k30": "sk" + "_f_" + "shi_guang_hu_dun",
    "k31": "sk" + "_f_" + "shi_jian_hui_huan",
    "k32": "sk" + "_f_" + "yuan_su_cai_jue",
    "k33": "sk" + "_f_" + "wan_xiang_feng_bao",
    "k34": "sk" + "_f_" + "yuan_su_qi_yuan",
    "k35": "sk" + "_f_" + "wan_xiang_tian_lei",
    "k36": "sk" + "_f_" + "shi_ting_ling_yu",
    "k37": "sk" + "_f_" + "shi_jian_tan_suo",
    "k38": "sk" + "_f_" + "shi_jian_guo_zai",
    "k39": "sk" + "_f_" + "shi_guang_hui_su",
}

def _rebuild(d):
    """递归把字面占位 key 重建成 sk_f_ 真实 key（顶层 name + 各层 skills/branches 子 dict 全部重建）。"""
    out = {}
    for k, v in d.items():
        nk = _KEYMAP.get(k, k)
        if isinstance(v, dict):
            out[nk] = _rebuild(v)
        else:
            out[nk] = v
    return out

_PLAYER_SKILLS_RAW = {
    "name": "法师",
    "skills": {
        "k01": {
            "lv": 1, "mp": 5, "power": 1.1, "kind": "魔法",
            # P0：基础层不写 element —— 不挂印记、不判反应（印记是转职首获的身份）
            "desc": "将游离的火元素凝成灼热弹丸掷出，命中即焚——造成 110% 魔法伤害（基础层纯蓝，不挂元素印记）",
            "name": "火球术",
        },
        "k02": {
            "lv": 8, "mp": 8, "power": 1.0, "kind": "魔法",
            "mech": "spd_down", "mech_chance": 0.3,
            "desc": "指尖凝出剔透冰晶掷向敌人，寒气透骨——造成 100% 魔法伤害并减速（基础层纯蓝，不挂元素印记）",
            "name": "冰锥",
        },
        "k03": {
            "lv": 12, "mp": 8, "power": 1.0, "kind": "魔法",
            "desc": "引动雷云劈下一道电弧——造成 100% 魔法伤害（基础层纯蓝，不挂元素印记）",
            "name": "雷击",
        },
        "k04": {
            "lv": 14, "mp": 12, "power": 0.7, "kind": "魔法",
            "multi": 3,
            "desc": "三色元素凝成弹幕连珠掷出——造成 70% 魔法伤害×3（三段连射）",
            "name": "元素弹幕",
        },
        "k05": {
            "lv": 6, "mp": 10, "power": 1.1, "kind": "魔法",
            "aoe": "all", "mech": "spd_down", "mech_chance": 0.3, "cd": 3,
            "desc": "霜华自足底炸裂成环，冻结全场空气——造成 110% 全体魔法伤害并减速（冰霜新星·补控制）",
            "name": "冰霜新星",
        },
        "k06": {
            "lv": 16, "mp": 15, "power": 0, "kind": "增益",
            "effect": "shield_all", "cd": 4,
            "desc": "以魔力织成奥术壁障——为自己张开护盾（补生存）",
            "name": "奥术护盾",
        },
        "k07": {
            "lv": 20, "mp": 20, "power": 1.4, "kind": "魔法",
            "aoe": "all", "cd": 3,
            "desc": "呼唤天火坠落，陨石碾碎大地——造成 140% 全体魔法伤害（陨石术·AOE）",
            "name": "陨石术",
        },
        "k08": {
            "lv": 24, "mp": 10, "power": 0, "kind": "增益",
            "effect": "element_shift", "cd": 3,
            "desc": "身形如幻影般闪至后排——位移至后排（补机动）",
            "name": "闪现",
        },
    },
}

_BRANCH_SKILLS_RAW = {
    "name": "法师",
    "branches": {
        # ===== 分支 1（Lv.30）· A线 元素法师 + B线 时律法师 =====
        1: {
            # ===== A线 T1 · 元素法师（挂印 → 引爆，印记往「爆发」长） =====
            "元素法师": {
                "k09": {
                    # 元素冲击（挂对应系印记）
                    "lv": 32, "mp": 10, "power": 1.3, "kind": "魔法",
                    "element": "current",
                    "cond": {"type": "element_marks", "element": "any", "stacks": 1, "mult": 1.2, "label": "万象共鸣"},
                    "desc": "将当前系元素凝成冲击波轰出——造成 130% 魔法伤害并挂 1 层当前系元素印记；目标已有印记时万象共鸣（伤害＋20%）",
                    "name": "元素冲击",
                },
                "k10": {
                    # 元素聚焦（架设态：+40%施法，受击+20%）
                    "lv": 38, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "element_focus", "cd": 3,
                    "desc": "凝神开启元素架设——本场进入专注施法态：魔法技能伤害＋40%、受击＋20%、不能普攻/换系（可防御/用道具）；主动解除无损",
                    "name": "元素聚焦",
                },
                "k11": {
                    # 双系连珠（双段，挂两系各1层——引擎单 element 只能叠单系，见清单）
                    "lv": 45, "mp": 15, "power": 1.1, "kind": "魔法",
                    "multi": 2, "element": "current",
                    "desc": "两系元素连珠齐射——造成 110% 魔法伤害×2 并挂印记（设计为挂两系各 1 层，引擎当前只能叠单系，见清单）",
                    "name": "双系连珠",
                },
                "k12": {
                    # 元素护盾（架设中受击-20%——无字段，用护盾表达）
                    "lv": 48, "mp": 15, "power": 0, "kind": "增益",
                    "effect": "shield_all", "cd": 4,
                    "desc": "以元素编织护盾环绕周身——获得护盾（设计为架设中受击－20%，引擎无此字段，见清单）",
                    "name": "元素护盾",
                },
                "k13": {
                    # 元素引爆（主动结算反应）
                    "lv": 52, "mp": 0, "power": 1.5, "kind": "魔法",
                    "element": "current", "cd": 2,
                    "cond": {"type": "reaction", "label": "元素引爆"},
                    "desc": "引动元素印记连锁炸裂——造成 150% 魔法伤害并主动结算反应（蒸发/超载/冻结/感电）",
                    "name": "元素引爆",
                },
                "k14": {
                    # 元素湮灭（满印记爆发）
                    "lv": 55, "mp": 25, "power": 2.4, "kind": "魔法",
                    "element": "current", "cd": 3,
                    "consume_all": {"key": "element", "per": 0.2},
                    "cond": {"type": "reaction", "label": "满印爆发"},
                    "desc": "湮灭之力倾泻而出——造成 240% 魔法伤害；目标印记层数越高伤害越高（满印爆发，消耗全部充能每点＋20%）",
                    "name": "元素湮灭",
                },
            },
            # ===== B线 T1 · 时律法师（减速/停滞，印记往「控制」长） =====
            "时律法师": {
                "k15": {
                    # 时滞术（50%减速）
                    "lv": 40, "mp": 15, "power": 1.6, "kind": "魔法",
                    "mech": "spd_down", "mech_chance": 0.5, "cd": 1,
                    "desc": "拨动时间的丝线，让敌手的动作凝滞如浆——造成 160% 魔法伤害，50% 概率使目标减速",
                    "name": "时滞术",
                },
                "k16": {
                    # 时间凝滞（凝滞态：站桩蓄印记，受击+20%）
                    "lv": 42, "mp": 20, "power": 0, "kind": "增益",
                    "effect": "time_stasis", "cd": 3,
                    "stasis": {"enter_turn": 1, "enter_gain": 1, "gain_per_turn": 1,
                               "dmg_bonus": 0.4, "taken_bonus": 0.2, "interrupt_rate": 0.3,
                               "max_turns": 3, "erosion_power": 0.6},
                    "desc": "凝固时间的流速，进入时间凝滞——占 1 回合进入并预装资源；凝滞中每回合资源＋1、技能伤害＋40%、受击＋20%；受击 30% 打断；最多维持 3 回合",
                    "name": "时间凝滞",
                },
                "k17": {
                    # 时间加速（自身速度+30%——引擎 spd_up 固定+40%，见清单）
                    "lv": 46, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "spd_up", "cd": 3,
                    "desc": "加速自身的时间流速——自身速度＋30%（引擎 spd_up 固定＋40%，数值见清单）",
                    "name": "时间加速",
                },
                "k18": {
                    # 时间裂隙（双段+40%减速）
                    "lv": 48, "mp": 20, "power": 1.3, "kind": "魔法",
                    "multi": 2, "mech": "spd_down", "mech_chance": 0.4, "cd": 2,
                    "desc": "撕裂时间之壁，放出两道错位的时光刃——造成 130% 魔法伤害×2，每段 40% 概率减速",
                    "name": "时间裂隙",
                },
                "k19": {
                    # 凝时锁（35%眩晕）
                    "lv": 55, "mp": 20, "power": 1.4, "kind": "魔法",
                    "mech": "stun", "mech_chance": 0.35, "cd": 3,
                    "desc": "以流逝之光凝成无形锁链，锁死敌手的瞬间——造成 140% 魔法伤害，35% 概率眩晕 1 回合",
                    "name": "凝时锁",
                },
            },
        },
        # ===== 分支 2（Lv.60）· A线 元素术士 + B线 时律术士 =====
        2: {
            # ===== A线 T2 · 元素术士（被动链 + 大规模铺印） =====
            "元素术士": {
                "k20": {
                    # 元素跃迁（切当前系）
                    "lv": 60, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "element_shift", "cd": 1,
                    "desc": "魔力流转，切换当前元素系——切换到下一系（火→冰→雷循环）",
                    "name": "元素跃迁",
                },
                "k21": {
                    # 元素共鸣（被动：反应触发后下次挂印+1层——引擎无 proc 挂点，见清单）
                    "lv": 64, "mp": 0, "power": 0, "kind": "被动",
                    "passive": {"proc": "element_dmg", "mult": 0.08},
                    "desc": "与元素共鸣——反应触发后，下次挂印＋1 层（设计被动，引擎无 proc 挂点，见清单）；元素系技能伤害＋8%",
                    "name": "元素共鸣",
                },
                "k22": {
                    # 元素迸发（印记全清结算）
                    "lv": 66, "mp": 20, "power": 1.6, "kind": "魔法",
                    "element": "current", "cd": 3,
                    "cond": {"type": "reaction", "label": "印记清算"},
                    "desc": "引爆全部元素印记——造成 160% 魔法伤害并清空目标全部印记（设计为印记全清结算，引擎 consume_all 只支持充能 key，见清单）",
                    "name": "元素迸发",
                },
                "k23": {
                    # 元素同调（被动：连续两次同系施法第二次额外+1印记——引擎无此逻辑，见清单）
                    "lv": 72, "mp": 0, "power": 0, "kind": "被动",
                    "passive": {"proc": "element_dmg", "mult": 0.1},
                    "desc": "与同系元素同频共振——连续两次同系施法时，第二次额外＋1 印记（设计被动，引擎仅充能分支非印记，见清单）；元素系技能伤害＋10%",
                    "name": "元素同调",
                },
                "k24": {
                    # 元素洪流（AOE铺印）
                    "lv": 78, "mp": 30, "power": 1.2, "kind": "魔法",
                    "aoe": "all", "element": "current", "cd": 4,
                    "desc": "元素洪流席卷全场——造成 120% 全体魔法伤害并对全体敌人挂当前系印记",
                    "name": "元素洪流",
                },
                "k25": {
                    # 元素之核（被动：印记满3层时引爆暴击+20%——引擎无 proc 挂点，见清单）
                    "lv": 84, "mp": 0, "power": 0, "kind": "被动",
                    "passive": {"stat": "pene_mag", "add": 0.05},
                    "desc": "元素之核与魔力同频跳动——目标印记满 3 层时引爆暴击＋20%（设计被动，引擎无 proc 挂点，见清单）；魔法穿透＋5%",
                    "name": "元素之核",
                },
            },
            # ===== B线 T2 · 时律术士（时间控制深化） =====
            "时律术士": {
                "k26": {
                    # 时间静止（停滞2回合首领1回合——现有效应 sleep 为受击解除型，见清单）
                    "lv": 62, "mp": 20, "power": 0, "kind": "增益",
                    "effect": "sleep", "cd": 3,
                    "desc": "凝固目标的时间——使目标停滞（设计为 2 回合、首领 1 回合真停滞；引擎 sleep 为受击解除型，见清单）",
                    "name": "时间静止",
                },
                "k27": {
                    # 时之守护（凝滞中受击-30%）
                    "lv": 64, "mp": 15, "power": 0, "kind": "增益",
                    "effect": "shield_all", "cd": 4,
                    "desc": "在时间夹缝中张开守护壁——获得护盾（设计为凝滞态中受击－30%，引擎无此字段，见清单）",
                    "name": "时之守护",
                },
                "k28": {
                    # 时间共鸣（加速铺印记）
                    "lv": 66, "mp": 20, "power": 0.9, "kind": "魔法",
                    "element": "current", "cd": 3,
                    "desc": "时间与元素共鸣——造成 90% 魔法伤害并挂 2 层当前系印记（加速铺印）",
                    "name": "时间共鸣",
                },
                "k29": {
                    # 时间偷取（偷敌30%速度转己——引擎无此机制，见清单）
                    "lv": 72, "mp": 20, "power": 1.2, "kind": "魔法",
                    "cd": 4,
                    "desc": "窃取敌人的时间线——造成 120% 魔法伤害并偷取目标 30% 速度转给自己（设计，引擎无偷速机制，见清单）",
                    "name": "时间偷取",
                },
                "k30": {
                    # 时光护盾（免疫1次控制——引擎无 cc_immune_once，见清单）
                    "lv": 78, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "shield_all", "cd": 5,
                    "desc": "以时光之力护住心神——获得护盾（设计为免疫 1 次控制，引擎无 cc_immune_once 字段，见清单）",
                    "name": "时光护盾",
                },
                "k31": {
                    # 时间回环（刷新全CD——引擎无 refresh_cd，见清单）
                    "lv": 84, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 6,
                    "desc": "让时间倒流回环——刷新自身所有技能冷却（设计，引擎无 refresh_cd 机制，见清单）",
                    "name": "时间回环",
                },
            },
        },
        # ===== 分支 3（Lv.90）· A线 元素贤者 + B线 时律贤者 =====
        3: {
            # ===== A线 T3 · 元素贤者（三系顶点爆发） =====
            "元素贤者": {
                "k32": {
                    # 元素裁决（三印满×1.3）
                    "lv": 92, "mp": 40, "power": 2.8, "kind": "魔法",
                    "element": "current", "cd": 5,
                    "cond": {"type": "element_marks", "element": "any", "stacks": 3, "mult": 1.3, "label": "三印裁决"},
                    "desc": "三系元素齐鸣，裁决降临——造成 280% 魔法伤害；目标三系印记齐满时三印裁决（伤害＋30%）",
                    "name": "元素裁决",
                },
                "k33": {
                    # 万象风暴（AOE+反应连锁）
                    "lv": 95, "mp": 50, "power": 1.2, "kind": "魔法",
                    "aoe": "all", "element": "current", "cd": 5,
                    "cond": {"type": "reaction", "label": "万象连锁"},
                    "desc": "万象元素风暴席卷战场——造成 120% 全体魔法伤害并连锁结算反应（设计为反应连锁，引擎 cond 已支持，见清单）",
                    "name": "万象风暴",
                },
                "k34": {
                    # 元素起源（被动：三系齐满反应伤+30%——引擎无 proc 挂点，见清单）
                    "lv": 96, "mp": 0, "power": 0, "kind": "被动",
                    "passive": {"proc": "element_dmg", "mult": 0.15},
                    "desc": "溯源元素本源——三系印记同时满时反应伤害＋30%（设计被动，引擎无 proc 挂点，见清单）；元素系技能伤害＋15%",
                    "name": "元素起源",
                },
                "k35": {
                    # 万象天雷（雷系顶点+感电连击）
                    "lv": 98, "mp": 60, "power": 3.0, "kind": "魔法",
                    "element": "lightning", "cd": 6,
                    "cond": {"type": "reaction", "label": "感电连击"},
                    "desc": "引动万雷天降——造成 300% 雷系魔法伤害；雷印共鸣时触发感电连击（设计为连击＋1，引擎 cond 已支持，见清单）",
                    "name": "万象天雷",
                },
            },
            # ===== B线 T3 · 时律贤者（时间顶点控制） =====
            "时律贤者": {
                "k36": {
                    # 时停领域（必眩晕，首领1回合）
                    "lv": 90, "mp": 100, "power": 3.0, "kind": "魔法",
                    "mech": "stun", "mech_chance": 1.0, "cd": 6,
                    "desc": "张开时间静止领域——造成 300% 魔法伤害并必定眩晕目标（首领 1 回合）",
                    "name": "时停领域",
                },
                "k37": {
                    # 时间坍缩（AOE+减速+50%眩晕）
                    "lv": 92, "mp": 100, "power": 1.5, "kind": "魔法",
                    "aoe": "all", "mech": "stun", "mech_chance": 0.5, "cd": 6,
                    "desc": "时间线向内坍缩——造成 150% 全体魔法伤害并减速（设计附带 50% 眩晕，mech 单字段只能 stun，见清单）",
                    "name": "时间坍缩",
                },
                "k38": {
                    # 时间过载（凝滞限定纯输出峰值）
                    "lv": 93, "mp": 80, "power": 3.5, "kind": "魔法",
                    "cd": 5,
                    "stasis_only": True,
                    "desc": "将凝滞积蓄的时间之力一次性引爆——造成 350% 魔法伤害（凝滞限定纯输出峰值，stasis_only 字段需引擎消费）",
                    "name": "时间过载",
                },
                "k39": {
                    # 时光回溯（解自身减速+刷新CD）
                    "lv": 95, "mp": 20, "power": 0, "kind": "增益",
                    "cd": 4,
                    "desc": "让时间倒流回自己身上——解除自身减速并刷新技能冷却（设计，引擎 cleanse 落 p_buffs 空转，见清单）",
                    "name": "时光回溯",
                },
            },
        },
    },
}

# ===== 导入即重建真实 key 的最终 dict =====
PLAYER_SKILLS_fa_shi = _rebuild(_PLAYER_SKILLS_RAW)
BRANCH_SKILLS_fa_shi = _rebuild(_BRANCH_SKILLS_RAW)

# ================= 引擎不支持字段清单（主 agent 收尾处理） =================
ENGINE_UNSUPPORTED_fa_shi = [
    "P0 基础层不挂印：引擎对带 element 字段的魔法命中无条件挂印记并判反应，故基础 8 技不写 element（已规避）——转职前基础技能纯蓝",
    "双系连珠（挂两系各 1 层）：引擎单 element 只能叠单系，需引擎批次支持多系印记",
    "元素共鸣（反应后挂印+1层）：引擎无反应后 proc 挂点",
    "元素同调（同系第二次+1印记）：引擎仅 _last_element_set 充能分支 ELEMENT_SAME_CAST_EXTRA_CHARGE 非印记",
    "元素之核（满印引爆暴击+20%）：引擎无满印 proc 挂点",
    "元素起源（三系齐满反应伤+30%）：引擎无三系齐满 proc 挂点",
    "元素迸发（印记全清结算）：consume_all 只支持 element 充能 key 不支持印记",
    "元素护盾（架设中受击-20%）：引擎无此字段，已用 shield_all 兜底",
    "时间静止（停滞2回合首领1回合）：现有效应 sleep 为受击解除型，非真停滞",
    "时间偷取（偷敌30%速转己）：引擎无偷速机制",
    "时光护盾（免疫1次控制）：引擎无技能侧 cc_immune_once 字段（仅药水 potion cc_immune）",
    "时间回环（刷新全CD）：引擎无 refresh_cd 机制",
    "时光回溯（解自身减速+刷新CD）：effect=cleanse 落 p_buffs 空转",
    "时间加速（+30%）：引擎 spd_up 固定+40%",
    "时间坍缩（AOE+减速+50%眩晕）：mech 单字段只能 stun，减速仅 desc",
    "时间过载（凝滞限定）：stasis_only 字段需引擎消费",
    "时间共鸣（加速铺印 2 层）：引擎单次命中只能挂 1 层印记（需 mech_val 支持或引擎批次）",
]

if __name__ == "__main__":
    print("PLAYER_SKILLS_fa_shi skills:", len(PLAYER_SKILLS_fa_shi["skills"]))
    print("BRANCH_SKILLS_fa_shi branches:", {k: {line: len(skills) for line, skills in v.items()} for k, v in BRANCH_SKILLS_fa_shi["branches"].items()})
    print("sample keys:", sorted(PLAYER_SKILLS_fa_shi["skills"].keys())[:3])
