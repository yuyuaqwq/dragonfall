# -*- coding: utf-8 -*-
"""v151 职业重构 · 战士（战意叠层）技能表 → 引擎字段格式（独立文件，主 agent 收尾合并）

来源：workspace/v151_skill_tables/zhan_shi.md + workspace/v151_field_mapping.md
两线共用基础技能（Lv.1-26，9 个）+ A线血怒 / B线铁誓（分支技能）。
引擎字段按 game/data/skills.py 现有格式；v151 机制字段引擎不支持的部分
以注释标注（引擎不支持清单见文件尾），主 agent 收尾统一接线。

注意：战意（zhan_yi）为自身叠层 mech_stacks 键，engine.py MECH_STACK_MAX 已注册
上限 10，battle_config MECH_STACK_WHITELIST 已含 zhan_yi（增益类技能 mech+mech_val
可叠层）。攻击技能命中+1战意的「命中即叠」在现有引擎需 MECH_EFFECTS handler
（battle_mech.py 无 zhan_yi handler）——已用 mech: "zhan_yi" 字段标注，主 agent 接线。
"""

PLAYER_SKILLS_zhan_shi = {
    # ============ 基础技能（Lv.1-26，两线共用 · 9 个） ============
    "sk_zhan_shi_hui_kan": {
        "lv": 1, "mp": 3, "power": 1.0, "kind": "物理",
        # 命中+1战意：引擎需 MECH_EFFECTS["zhan_yi"] handler（未注册，见文件尾）
        "mech": "zhan_yi", "mech_val": 1,
        "cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"},
        "desc": "长剑划出利落的弧光——造成 100% 物理伤害，命中积攒 1 点战意；若你的速度高于目标，先发剑势更盛(伤害＋15%)",
        "name": "挥砍",
    },
    "sk_zhan_shi_meng_ji": {
        "lv": 2, "mp": 4, "power": 1.2, "kind": "物理",
        "mech": "zhan_yi", "mech_val": 1,
        "desc": "双臂蓄满蛮力猛然砸下——造成 120% 物理伤害，命中积攒 1 点战意",
        "name": "猛击",
    },
    "sk_zhan_shi_zhan_hou": {
        "lv": 3, "mp": 5, "power": 0, "kind": "增益",
        "effect": "atk_up",
        "cd": 3,
        # 自身+2战意：增益类技能走 _apply_mech_gain（MECH_STACK_WHITELIST 已含 zhan_yi）
        "mech": "zhan_yi", "mech_val": 2,
        "team": "atk_all",
        "desc": "胸腔炸开一声战吼，战意点燃血液——攻击＋30% 持续 3 回合；组队时战意传染全队(全队攻击＋30%)，自身积攒 2 点战意",
        "name": "战吼",
    },
    "sk_zhan_shi_tie_bi": {
        "lv": 6, "mp": 5, "power": 0, "kind": "增益",
        "effect": "def_up",
        "cd": 3,
        "desc": "举盾凝立如城墙——防御＋45% 持续 3 回合",
        "name": "铁壁",
    },
    "sk_zhan_shi_po_jia_zhan": {
        "lv": 8, "mp": 6, "power": 0.875, "kind": "物理",
        "pierce": True,
        "mech": "zhan_yi", "mech_val": 1,
        "desc": "剑锋劈入甲胄缝隙，无视防御造成 130% 物理伤害，命中积攒 1 点战意",
        "name": "破甲斩",
    },
    "sk_zhan_shi_xuan_feng_zhan": {
        "lv": 14, "mp": 10, "power": 0.946, "kind": "物理",
        "aoe": "front",
        "mech": "zhan_yi", "mech_val": 1,
        "desc": "身形旋起如风暴，横扫前排造成 110% 全体物理伤害，命中积攒 1 点战意",
        "name": "旋风斩",
    },
    "sk_zhan_shi_dun_ji": {
        "lv": 18, "mp": 6, "power": 1.3, "kind": "物理",
        "cd": 3,
        "mech": "stun", "mech_chance": 0.35,
        "desc": "重盾悍然撞出——造成 130% 物理伤害，35% 概率震晕目标 1 回合(CD 3)",
        "name": "盾击",
    },
    "sk_zhan_shi_xu_li_zhan": {
        "lv": 22, "mp": 16, "power": 2.2, "kind": "物理",
        "pierce": True,
        "cd": 4,
        "charge": 1,
        "desc": "屏息沉肩，将全身力量注入剑锋——蓄力 1 回合(受击会打断)，挥出 220% 破防一击",
        "name": "蓄力斩",
    },
    "sk_zhan_shi_chong_feng": {
        "lv": 26, "mp": 8, "power": 1.1, "kind": "物理",
        "cd": 2,
        # 位移至前排+先手压制：位移无引擎字段（引擎无站位位移机制），先手压制用 player_first 条件
        "cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"},
        "desc": "身先士卒悍然冲锋，直取敌阵前排——造成 110% 物理伤害；先手(速度高于目标)时冲锋更烈(伤害＋15%)",
        "name": "冲锋",
    },
}

# ============ 分支技能：A线 血怒（战意往"更痛"长）/ B线 铁誓（战意往"更硬"长） ============
BRANCH_SKILLS_zhan_shi = {
    "name": "战士",
    "branches": {
        # ==================== A线 · 血怒 ====================
        1: {
            "血怒": {
                # ---------- T1（Lv.30-58） ----------
                "怒斩": {
                    "lv": 32, "mp": 5, "power": 1.166, "kind": "物理",
                    # 每层战意+5%伤害：引擎需战意持有增伤挂点（主 agent 接线）；此处保留 mech 标注
                    "mech": "zhan_yi", "mech_val": 1,
                    "cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": 3, "mult": 1.15, "label": "战意盈沸"},
                    "desc": "怒意化作劈山一剑——造成 116.6% 物理伤害，命中积攒 1 点战意；战意≥3 层时怒意盈沸(伤害＋15%)",
                    "name": "怒斩",
                },
                "嗜血斩": {
                    "lv": 38, "mp": 8, "power": 1.6, "kind": "物理",
                    "lifesteal": 0.25,
                    # 狂暴中吸血翻倍：引擎支持 rage_form.lifesteal_mult（v139 既有字段）
                    "rage_form": {"lifesteal_mult": 2},
                    "desc": "利刃贪婪地渴饮鲜血——造成 160% 物理伤害并吸血 25%；狂暴形态下吸血翻倍(50%)",
                    "name": "嗜血斩",
                },
                "裂地斩": {
                    "lv": 45, "mp": 10, "power": 1.4, "kind": "物理",
                    # 战意≥6 附加流血：bleed 无 MECH_EFFECTS handler（引擎不支持流血叠层，见文件尾）
                    "cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": 6, "mult": 1.2, "label": "战意裂地"},
                    "desc": "重剑砸裂大地——造成 140% 物理伤害；战意≥6 层时威势更盛(伤害＋20%)并附加流血(引擎待接线)",
                    "name": "裂地斩",
                },
                "淬血": {
                    "lv": 48, "mp": 0, "power": 0, "kind": "被动",
                    # 每层战意额外+1%吸血：引擎无「战意×吸血」按层被动挂点（不支持，见文件尾）
                    "passive": {"proc": "zhan_yi_lifesteal", "per_stack": 0.01},
                    "desc": "战意淬炼血脉——每层战意额外提供 1% 吸血(引擎待接线)",
                    "name": "淬血",
                },
                "破势斩": {
                    "lv": 52, "mp": 0, "power": 1.2, "kind": "物理",
                    # 入狂暴当回合自动追加（不占行动）：引擎 auto="rage_form_enter" 仅触发入狂暴，无伤害追加（v139 既有字段，见文件尾）
                    "auto": "rage_form_enter",
                    "desc": "入狂暴当回合自动追加 1 次 120% 物理斩击（不占行动）",
                    "name": "破势斩",
                },
                "狂战怒吼": {
                    "lv": 55, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "atk_up",
                    "cd": 3,
                    "mech": "zhan_yi", "mech_val": 3,
                    "team": "atk_all",
                    "desc": "胸腔炸开一声战吼，战意点燃血液——攻击＋30% 持续 3 回合；组队时战意传染全队(全队攻击＋30%)，自身积攒 3 点战意",
                    "name": "狂战怒吼",
                },
                # ---------- T2（Lv.58-88） ----------
                "龙息之怒": {
                    "lv": 58, "mp": 30, "power": 1.0, "kind": "真伤",
                    "mech": "burn", "mech_val": 2,
                    "cd": 4,
                    "desc": "挥剑如龙啸，吐出灼热吐息——造成 100% 真伤(无视全部防御)并附加 2 层灼烧",
                    "name": "龙息之怒",
                },
                "内燃": {
                    "lv": 62, "mp": 0, "power": 0, "kind": "被动",
                    # 灼烧+15%；免疫灼烧目标转真伤轴：引擎有 burn_amp + inner_fire 字段（v139 龙裔同款，见文件尾）
                    "passive": {"proc": "burn_amp", "mult": 1.15},
                    "inner_fire": {"true_dmg": True},
                    "desc": "血脉中的火焰翻涌不息——灼烧伤害＋15%（被动）；对免疫灼烧的目标，灼烧层以「内燃」真伤轴生效(绕过免疫)",
                    "name": "内燃",
                },
                "怒涛连斩": {
                    "lv": 66, "mp": 20, "power": 0.8, "kind": "物理",
                    "multi": 3,
                    "cd": 3,
                    # 每段命中+1战意：引擎多段仅结算一次 mech（无逐段挂点，见文件尾）
                    "mech": "zhan_yi", "mech_val": 1,
                    "desc": "剑光如怒涛连绵不绝——连斩 3 次(每次 80% 物理伤害)，命中积攒 1 点战意(每段待引擎接线)",
                    "name": "怒涛连斩",
                },
                "焚天斩": {
                    "lv": 72, "mp": 25, "power": 1.0, "kind": "物理",
                    "aoe": "front",
                    "cd": 3,
                    # 战意≥8 范围扩为全体：引擎无「条件扩大 AOE 范围」字段（见文件尾）
                    "cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": 8, "mult": 1.2, "label": "焚天战意"},
                    "desc": "烈焰焚空——对前排造成 100% 物理伤害；战意≥8 层时焚天之势席卷全场(伤害＋20%，AOE 扩为全体待引擎接线)",
                    "name": "焚天斩",
                },
                "断筋": {
                    "lv": 78, "mp": 12, "power": 1.2, "kind": "物理",
                    "cd": 3,
                    # 流血+减速：bleed 无 handler；减速用 spd_down（引擎支持）
                    "mech": "spd_down", "mech_val": 2,
                    "desc": "剑刃精准斩断目标筋腱——造成 120% 物理伤害并减速目标 2 回合；附加流血(引擎待接线)",
                    "name": "断筋",
                },
                "狂热": {
                    "lv": 84, "mp": 0, "power": 0, "kind": "被动",
                    # 战意≥8 时暴击+15%：引擎无「条件暴击」被动字段（见文件尾）
                    "passive": {"proc": "zhan_yi_crit", "cond_stacks": 8, "crit_add": 0.15},
                    "desc": "战意如烈焰焚身——战意≥8 层时暴击＋15%(引擎待接线)",
                    "name": "狂热",
                },
                # ---------- T3（Lv.90-98） ----------
                "战争化身": {
                    "lv": 92, "mp": 40, "power": 2.6, "kind": "真伤",
                    "mech": "burn", "mech_val": 3,
                    "cd": 5,
                    # 狂暴限定：引擎有 rage_form 系字段但无「狂暴形态限定施放」字段（见文件尾）
                    "cond_rage_form": {"type": "player_rage_form", "mult": 1.2, "label": "狂暴增益"},
                    "desc": "化身战争本身，挥出毁天灭地的一剑——造成 260% 真伤(无视全部防御)并附加 3 层灼烧；狂暴形态下威势更炽(伤害＋20%)",
                    "name": "战争化身",
                },
                "燎原之怒": {
                    "lv": 95, "mp": 35, "power": 1.3, "kind": "物理",
                    "aoe": "all",
                    "cd": 5,
                    # AOE+灼烧清算：灼烧层引爆需 burn_burst handler（引擎已有）；此处按 AOE+灼烧叠层落地
                    "mech": "burn", "mech_val": 2,
                    "desc": "怒火燎原席卷全场——对全体造成 130% 物理伤害并附加 2 层灼烧(灼烧清算待引擎接线)",
                    "name": "燎原之怒",
                },
                "怒涛·终焉": {
                    "lv": 98, "mp": 45, "power": 0.9, "kind": "物理",
                    "multi": 5,
                    "cd": 5,
                    "mech": "zhan_yi", "mech_val": 1,
                    "desc": "五段怒涛斩出终焉——连斩 5 次(每次 90% 物理伤害)，命中积攒 1 点战意(每段待引擎接线)",
                    "name": "怒涛·终焉",
                },
            },
        },
        # ==================== B线 · 铁誓 ====================
        2: {
            "铁誓": {
                # ---------- T1（Lv.30-58） ----------
                "盾击·卫": {
                    "lv": 32, "mp": 5, "power": 1.3, "kind": "物理",
                    "cd": 3,
                    "mech": "stun", "mech_chance": 0.35,
                    # 姿态联动+20%：引擎支持 cond_stance（v139 既有字段）
                    "cond_stance": {"type": "player_stance", "mult": 1.2, "label": "姿态联动"},
                    "desc": "重盾裹挟守护之力悍然砸出——造成 130% 盾击伤害，35% 概率震晕目标 1 回合；守护姿态生效时伤害＋20%",
                    "name": "盾击·卫",
                },
                "守护姿态": {
                    "lv": 38, "mp": 0, "power": 0, "kind": "被动",
                    # 受击反击40%+回战意，回合末保底+1：引擎支持 counter_attack + stance_floor（v139 既有字段，res_gain 指向 rage 旧资源）
                    "passive": {"proc": "dmg_taken", "reduce": 0.1, "res_gain": 2},
                    "counter_attack": {"proc": "on_hit", "power": 0.4, "per_hit": 1, "free": True},
                    "stance_floor": {"res_gain": 1, "per_turn": 1},
                    "desc": "沉稳如山的守护架势——受到伤害降低 10%；受击自动反击 40% 物理(不耗怒气、不吃 CD、每受击至多 1 次)，回合末保底回怒 1(战意版待引擎接线)",
                    "name": "守护姿态",
                },
                "坚盾壁垒": {
                    "lv": 45, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "shield_all",
                    # 花5层战意→全队护盾：战意为叠层非消耗型资源，引擎无「消耗战意」语义（见文件尾）；护盾用 shield_all effect
                    "desc": "高举坚盾，壁垒护佑全队——花 5 层战意为全队张开护盾(战意消耗待引擎接线)",
                    "name": "坚盾壁垒",
                },
                "顿足盾击": {
                    "lv": 50, "mp": 0, "power": 0.4, "kind": "物理",
                    # 嘲讽失效自动衔接（不占行动）：引擎支持 auto_followup（v139 既有字段）
                    "auto": "stance_followup",
                    "auto_cond": {"taunt_failed": True, "block_break": True},
                    "desc": "守线自动衔接技——嘲讽失效或格挡被破当回合自动打出 40% 盾击(不占主行动、不吃 CD、不耗怒)",
                    "name": "顿足盾击",
                },
                "铁壁·卫": {
                    "lv": 52, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "shield_all",
                    "cd": 3,
                    "desc": "举盾凝立如铁壁——自身获得护盾并进入格挡架势(CD 3)",
                    "name": "铁壁·卫",
                },
                "嘲讽": {
                    "lv": 55, "mp": 0, "power": 0, "kind": "嘲讽",
                    "cd": 3,
                    "team": "taunt",
                    # 强制攻击2回合：引擎 kind=嘲讽 已支持（e_buffs mon_atk_down + 团队 taunt）
                    "desc": "一声挑衅怒喝，将敌意尽数引向自身——强制怪物攻击自己 2 回合(CD 3)",
                    "name": "嘲讽",
                },
                # ---------- T2（Lv.58-88） ----------
                "圣盾": {
                    "lv": 60, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "reduce_all",
                    "reduce_all": 0.25,
                    "team": "reduce_all",
                    "cd": 4,
                    # 花3层战意：战意消耗语义引擎不支持（见文件尾）
                    "desc": "圣光凝成守护之盾——全队减伤 25% 持续 3 回合，花 3 层战意(战意消耗待引擎接线)",
                    "name": "圣盾",
                },
                "坚韧": {
                    "lv": 64, "mp": 0, "power": 0, "kind": "被动",
                    # 被控时耗2层战意跳过（每场3次）：引擎无「耗战意免疫控制」机制（见文件尾）
                    "passive": {"proc": "tenacity_cc_skip", "per_battle": 3},
                    "desc": "铁一般的意志——被控时消耗 2 层战意跳过控制(每场至多 3 次，引擎待接线)",
                    "name": "坚韧",
                },
                "复仇": {
                    "lv": 66, "mp": 10, "power": 1.8, "kind": "物理",
                    "cd": 3,
                    # 承伤越高越痛：引擎无「承伤转增伤」技能字段（见文件尾）
                    "cond": {"type": "player_hp_low", "hp_pct": 0.5, "mult": 1.2, "label": "复仇意志"},
                    "desc": "伤痛点燃复仇之焰——造成 180% 物理伤害；自身生命低于 50% 时复仇更烈(伤害＋20%)",
                    "name": "复仇",
                },
                "破城锤": {
                    "lv": 70, "mp": 15, "power": 1.4, "kind": "物理",
                    "pierce": True,
                    "cd": 4,
                    "mech": "stun", "mech_chance": 0.35,
                    "desc": "如攻城巨锤轰碎防线——造成 140% 破防伤害，35% 概率震晕目标 1 回合(CD 4)",
                    "name": "破城锤",
                },
                "誓约之盾": {
                    "lv": 76, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "shield_all",
                    "cd": 5,
                    # 挡刀+反伤30%：引擎无「挡刀」字段；反伤可用 thorns 被动（v106.4 支持）
                    "passive": {"proc": "thorns", "mult": 0.3},
                    "desc": "以誓约为盾——为全队张开护盾并附带 30% 反伤(挡刀待引擎接线，CD 5)",
                    "name": "誓约之盾",
                },
                "战吼·守": {
                    "lv": 82, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "reduce_all",
                    "reduce_all": 0.20,
                    "team": "reduce_all",
                    "cd": 4,
                    "mech": "zhan_yi", "mech_val": 2,
                    "desc": "胸腔炸开一声守护战吼——全队减伤 20% 持续 3 回合，自身积攒 2 点战意(CD 4)",
                    "name": "战吼·守",
                },
                # ---------- T3（Lv.90-98） ----------
                "守护誓言": {
                    "lv": 92, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "shield_all",
                    "cd": 5,
                    # 挡刀+反伤50%
                    "passive": {"proc": "thorns", "mult": 0.5},
                    "desc": "以誓言为盾，守护全队——为全队张开护盾并附带 50% 反伤(挡刀待引擎接线，CD 5)",
                    "name": "守护誓言",
                },
                "不破壁垒": {
                    "lv": 95, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "reduce_all",
                    "reduce_all": 0.50,
                    "team": "reduce_all",
                    "cd": 6,
                    # 花5层战意：战意消耗语义引擎不支持（见文件尾）
                    "desc": "筑起不破的壁垒——花 5 层战意为全队张开减伤 50% 屏障(战意消耗待引擎接线，CD 6)",
                    "name": "不破壁垒",
                },
                "坚城之姿": {
                    "lv": 96, "mp": 0, "power": 0, "kind": "被动",
                    # 战意满10时减伤+10%、免疫眩晕：引擎无「满战意减伤/免控」被动（见文件尾）
                    "passive": {"proc": "zhan_yi_max_guard", "cond_stacks": 10, "reduce": 0.10},
                    "desc": "战意满 10 层时坚城之姿显现——减伤＋10% 并免疫眩晕(引擎待接线)",
                    "name": "坚城之姿",
                },
                "守护圣域": {
                    "lv": 98, "mp": 0, "power": 0, "kind": "增益",
                    "effect": "reduce_all",
                    "reduce_all": 0.50,
                    "team": "reduce_all",
                    "cd": 6,
                    # 花满10层战意→全队护盾+减伤：战意消耗语义引擎不支持（见文件尾）
                    "desc": "圣光凝成守护圣域——花满 10 层战意为全队张开护盾与 50% 减伤(战意消耗待引擎接线，CD 6)",
                    "name": "守护圣域",
                },
            },
        },
    },
}

# ============================================================
# v151 机制字段 · 引擎支持情况（主 agent 收尾接线清单）
# ============================================================
# 引擎已支持（本文件已按现成字段落地）：
#   - mech: "zhan_yi" + mech_val（增益类技能经 MECH_STACK_WHITELIST 叠层，engine.py MECH_STACK_MAX 上限 10 已注册）
#   - cond: player_mech_stacks（battle_conds.py 已支持，key 用 "mech" 字段而非 "key"）
#   - pierce / aoe front|all / reach / lifesteal / mech stun+burn+poison+spd_down / cc
#   - shield_all effect / reduce_all + team / taunt / passive stat/proc（burn_amp/inner_fire/thorns/dmg_taken/counter_attack/stance_floor/auto_followup/rage_form.lifesteal_mult）
#
# 引擎不支持（需主 agent 在引擎层接线，本文件以注释/字段占位标注）：
#   1. 攻击技能「命中+1战意」：MECH_EFFECTS 无 zhan_yi handler（攻击路径 mech 只走 handler；
#      目前只有增益类可经 _apply_mech_gain 叠层）→ 需 battle_mech.py 注册 zhan_yi
#   2. 战意持有收益（每层攻击+4%/受伤+2%；血怒线 +6%/+3%）：_mech_stack_bonus 查 MECH_STACK_BONUS，
#      需加 zhan_yi 表项 + 受击方每层承伤 +2% 挂点；血怒/铁誓线被动需分支级数值
#   3. 战意「消耗」语义（坚盾壁垒 5层/圣盾 3层/不破壁垒 5层/守护圣域 满10层）：战意设计为叠层非货币，
#      引擎 mech_stacks 无扣层 API → 需 battle.py 消费点（或改为条件+免费，主 agent 定夺）
#   4. 流血 bleed：MECH_EFFECTS/DOT 结算已支持 DOT_DEFS.bleed，但无叠层 handler（技能施加不了）→ 需注册 bleed
#   5. 多段「每段命中+1战意」：multi 技能 mech 仅结算一次 → 需逐段挂点
#   6. 狂暴限定施放（战争化身）：现有 rage_form 系字段只做增益不做限定 → 需 gate 字段
#   7. 条件扩 AOE（焚天斩 战意≥8 → all）：无「条件换范围」字段 → 需引擎支持或降级为固定 front
#   8. 战意按层吸血被动（淬血）、条件暴击被动（狂热）、满战意减伤/免控（坚城之姿）、
#      被控耗战意跳过（坚韧）、承伤转增伤（复仇）：均需新被动 proc 挂点
#   9. 位移/冲锋站位：引擎无站位位移机制（冲锋以先手压制 cond 落地）
#   10. 挡刀（誓约之盾/守护誓言）：无「替队友承伤」字段（以护盾+反伤 thorns 落地）
# ============================================================
