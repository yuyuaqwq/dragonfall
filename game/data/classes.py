# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - classes.py(v48 key 转 ID)

v112 职业体系重构（主题线制）：13 隐藏 → 6 隐藏线（每基础 1 条），
每线 = 主题 + 核心资源（core_resources.py）+ 线级被动 + 2-3 流派（evolve_branches[1]）。
v112 新增数据字段（数据驱动收敛，逻辑层只读数据）：
  aliases      转职短别名 → 流派索引（『转职 龙血』→ cls_dragon_oath 流派 1）
  lore         传承文案
  hint         未解锁线索
  tier_levels  隐藏线档位门槛（缺省 40/60/90）
  attack_text  普攻动作文案（battle.py 读取）
  tutor        (导师名, 地点)（转职指引/技能学习拦截提示）

v139 职业融合（云海猎团职业卡吸收，13 份方案 design/new_world/参考_云海猎团职业融合_v139_*.md）：
  mech 描述更新为「奥兰迪亚身份 + v139 融合机制」一句话（职业指南/战斗展示用）；
  新增职业级机制字段（说明性引用，值与 core_resources.py / battle_config.py 同名字段同构，
  由 battle.py 通用引擎机消费——dual_form 双形态 / focus 架设态 / vent 排气节流阀 /
  charge 电荷蓄力 / enemy_bar 挂敌身条 / combo 链值 / support 随附支援 / dirge 死歌 等）：
  P2E（2026-09-07）：classes 内机制参数字段与 battle_config/core_resources 并存属历史双源；
  删除评估在数据批次（combo dict 已随 P2E-P2a 删），引擎读 core_resources / battle_config。
    cls_zhan_shi      dual_form（攻线狂战士狂暴）
    cls_fa_shi        focus（元素架设）
    cls_you_xia       vent + charge（凝神屏息 + 电荷蓄力）
    cls_mu_shi        support（守线圣辉支援）
    cls_ci_ke         finisher_threshold + combo（终结档位 + 链值滚雪球）
    cls_wu_seng       enemy_bar.shaken + guard_core（破绽挂敌身 + 磐核）
    cls_dragon_oath   dual_form（龙焰形态）
    cls_chronomancer  focus（时间凝滞）
    cls_wild_hunter   vent + star_lock（猎印排气 + 星轨锁定）
    cls_hymn          enemy_bar.curse/soul_mark + dirge（诅咒挂敌身 + 死歌）
    cls_shadow_blade  dual_form（影舞态）+ ambush_plan（伏击四预案）
    cls_wu_sheng      dual_form（蓄势/倾泻）+ enemy_bar.shaken（撼岳之势）
  原则：只加数据不改结构（desc/evolve 分支不动），旧字段无该键 = 默认不启用（引擎兼容旧数据）。
"""
CLASSES = {
    "cls_novice": {
        "desc": "刚踏上冒险之路的新人，还没有正式职业。去冒险者行会找接待员就职，或到各城寻找职业导师吧！",
        "icon": "🧭",
        "role": "见习",
        "attack_text": "挥剑攻击",
        "basic_skill": {"name": "挥拳", "kind": "物理", "exprs": ["atk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "挥剑攻击"},
        "base": {
            "hp": 110,
            "mp": 50,
            "atk": 11,
            "def": 9,
            "matk": 9,
            "mdef": 9,
            "spd": 10,
            "crit": 0.05,
            "dodge": 0.03
        },
        "growth": {
            "hp": 14,
            "mp": 6,
            "atk": 1.3,
            "def": 1.1,
            "matk": 1.1,
            "mdef": 1.1,
            "spd": 1.0
        },
        "weapon_type": "sword",
        "name": "见习冒险者",
        "default_rank": 1,   # v2 站位层：前排
        "reach": 1,          # v2 攻击范围
        "rank_label": "前排",
    },
    "cls_zhan_shi": {
        "desc": "身穿重甲、手持巨剑的钢铁壁垒，正面硬刚一切敌人。",
        # v139（云海猎团职业融合·狂战士样板）：攻线狂战士「血怒双形态」——满怒入狂暴、
        # 双段输出+维持消耗+<4 强制回斧（怒尽回斧无惩罚）；守线盾卫士「防御即生产」——
        # 守护姿态受击自动反击 + 保底回怒 + 坚韧抗控。转职全链覆盖（基础 1-30 → 攻/守双线）。
        "mech": "怒气三路攒满10放背水一战；攻线入狂暴双形态，守线防御即生产。",  # v130.7 意见#19 / v139 融合
        "icon": "🛡️",
        "role": "坦克",
        "cast_atk": 1.15,      # v154 基准减半（速度50→出招0.7s）：重剑普攻慢
        "cast_defend": 0.4,    # 重甲防御稍慢
        "cast_flee": 1.1,      # 重甲逃跑慢
        "evolve": ["狂战士(30)", "狂战统领(60)", "战争领主(90)"],
        "evolve_branches": {
            # v139：攻线=狂战士（血怒双形态，狂暴精通/破势斩）；守线=盾卫士（防御即生产，守护姿态反击+坚韧）
            1: ["狂战士", "盾卫士"],
            2: ["狂战统领", "坚盾卫士"],
            3: ["战争领主", "坚城统帅"],
        },
        # v139（云海狂战士双形态翻译，样板定稿）：攻线狂战士狂暴形态——字段与
        # core_resources.py cls_zhan_shi.dual_form 同构（enter_requirement 10 / maintain_cost 1 /
        # hit_cost 1 / hit_cost_cap 1 / force_return 4 / form "fury"），由 battle.py 通用形态机消费；
        # 战前可设入狂暴 4 档预设（满怒/7怒/窗口/血线），守线 side 另有 tenacity 坚韧副资源
        "dual_form": {
            "enter_requirement": 10, "maintain_cost": 1, "hit_cost": 1,
            "hit_cost_cap": 1, "force_return": 4, "return_penalty": "none", "form": "fury",
        },
        "attack_text": "挥剑斩击",
        "basic_skill": {"name": "挥剑斩击", "kind": "物理", "exprs": ["atk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "res_gain": 1, "cast_verb": "挥剑斩击"},
        "tutor": ("老兵·格里姆", "白鹿城·白鹿广场"),
        "base": {
            "hp": 150,
            "mp": 40,
            "atk": 18,
            "def": 14,
            "matk": 6,
            "mdef": 10,
            "spd": 10,
            "crit": 0.05,
            "dodge": 0.03,
            "elem_res": 0.05,
            "shield_power": 0.05,
        },
        "growth": {
            "hp": 22,
            "mp": 3,
            "atk": 3.2,
            "def": 2.6,
            "matk": 0.5,
            "mdef": 1.2,
            "spd": 0.6
        },
        "weapon_type": "sword",
        "name": "战士",
        "default_rank": 1,   # v2 站位层：前排（坦克壁垒）
        "reach": 1,          # v2 攻击范围：近战
        "rank_label": "前排",
    },
    "cls_fa_shi": {
        "desc": "掌控元素之力的施法者，输出爆炸但身板脆弱。",
        # v139（云海机械师融合）：转职后攻线·元素/守线·奥秘可开「元素架设」专注施法模式——
        # +40% 施法增伤、受击 +20%、不能普攻/换系、打断不清零（只掉 1 层）、主动解除无损。
        # 基础法师（未转职）纯蓝不经营不变（v130.2 身份铁律）。
        "mech": "纯蓝施法者；转职解锁充能条 + 元素架设(专注+40%增伤)。",  # v130.7 意见#19 / v139 融合
        "icon": "🔥",
        "role": "输出",
        "cast_atk": 1.0,       # v156 法系定位：法师普攻弱（魔杖敲击），输出靠技能，保持 v154 值
        "cast_defend": 0.45,
        "cast_flee": 1.2,
        # v130.2（鱼鱼拍板）：基础法师无核心资源 = 纯蓝施法者——技能全纯 mp，
        # 0 res_gain / 0 res_cost / 模型无 on_skill 渠道；element 充能条(0-5) 定义保留在
        # core_resources.py，随攻线·元素法师 / 守线·奥秘法师 转职首获（转职批次挂 res_gain 生效）。
        # v112.5（鱼鱼拍板）：基础法师两条初始线——元素（攻）+ 奥秘（守）；
        # 奥秘守线 = 奥术师与秘法族合并体（原隐藏奥秘线元素流降为基础守线）
        # v139：攻线=元素架设爆发（聚焦→满充能→湮灭）、守线=深度冥想驻留（低耗高频+叠层加速）
        "evolve": ["元素使(30)", "元素术士(60)", "元素贤者(90)"],
        "evolve_branches": {
            1: ["元素使", "奥术学者"],
            2: ["元素术士", "奥术大师"],
            3: ["元素贤者", "奥秘主宰"],
        },
        # v139（云海机械师架设态翻译）：元素架设 focus——字段与 core_resources.py cls_fa_shi.focus
        # 同构（enter_turn 1 / dmg_bonus 0.40 / taken_bonus 0.20 / interrupt 只掉 1 层 /
        # max_turns 3 / free_exit），由 battle.py 通用专注机消费；攻线开启技「元素聚焦」、
        # 守线开启技「深度冥想」（架设中每刻 arcane 自动 +1）
        "focus": {
            "enter_turn": 1, "dmg_bonus": 0.40, "taken_bonus": 0.20,
            "interrupt_charge_loss": 1, "max_turns": 3, "free_exit": True,
            "blocked": ["attack", "skill", "swap"],
        },
        "attack_text": "凝聚魔力轰出法球",
        "basic_skill": {"name": "法球", "kind": "魔法", "exprs": ["matk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "凝聚魔力轰出法球"},
        "tutor": ("大法师·艾德琳", "白鹿城·白鹿广场"),
        "base": {
            "hp": 90,
            "mp": 120,
            "atk": 8,
            "def": 7,
            "matk": 22,
            "mdef": 14,
            "spd": 12,
            "crit": 0.08,
            "dodge": 0.05,
            "pene_magi": 0.10,
            "abyss_res": 0.05,
        },
        "growth": {
            "hp": 10,
            "mp": 10,
            "atk": 0.8,
            "def": 1.0,
            "matk": 3.8,
            "mdef": 1.8,
            "spd": 0.9
        },
        "weapon_type": "staff",
        "name": "法师",
        "default_rank": 2,   # v2 站位层：后排（施法者）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
    },
    "cls_you_xia": {
        # v113（鱼鱼拍板）：攻线"猎魔人"主题名实不符（无猎魔内容），
        # 改为自然系"林语者"——狩猎印记保留 + 自然毒藤 + 植物召唤（机制下放自隐藏线自然/兽群流）
        # v139（云海游侠+弓手融合）：精力满 100 强制「凝神屏息」（节流阀）+ 电荷制蓄力三律
        # （边攒边打/打断-1阶不清零/满阶强制释放）+ 狙击指定后排（rank=3 瞄准权）。
        "desc": "敏捷的弓箭手，箭无虚发，暴击与闪避的艺术家。攻线觉醒自然之力，与万木为友。",
        # v130.7 意见#19 / v139 融合：精力三档预算身份保留，v139 满 100 强制屏息排气 + 电荷蓄力
        "mech": "每刻回30精力；满100凝神屏息，蓄力改电荷制(边攒边打)。",
        "icon": "🏹",
        "role": "输出",
        "cast_atk": 1.0,       # v156 普攻节奏重标定（0.4→1.0）：同级频率 1.25:1 健康（1.15 过慢怪反超 4:1）；裸装约 6 轮击杀
        "cast_defend": 0.25,
        "cast_flee": 0.8,
        "evolve": ["森语者(30)", "自然守望者(60)", "万木之灵(90)"],
        "evolve_branches": {
            # v139：攻线=林语者（标记叠层+毒 DOT+屏息爆发窗口）；守线=风行者（速度增伤+电荷蓄力狙击）
            1: ["森语者", "风行者"],
            2: ["自然守望者", "疾风射手"],
            3: ["万木之灵", "狂风之猎"],
        },
        # v139（云海游侠节流阀翻译）：精力排气——VENT_CFG（battle_config.py）触发=100 强制屏息、
        # 闪避/机动泄压 -15、排气后低耗档段数 +1；字段说明性引用（核心数据在 battle_config.py VENT_CFG）
        "vent": {
            "trigger": 100, "auto": True, "reset": 0,
            "seg_bonus": 1, "low_cost_max": 25,
            "vent_on_dodge": 15, "vent_on_mobile": 15,
        },
        # v139（云海弓手蓄力三律翻译）：电荷制蓄力——CHARGE_CFG 引擎默认值（battle_config.py；
        # max 3 / 边攒边打出伤 0.7/1.3/1.9 / 打断-1阶 / 满 3 强制释放 / 狙击 reach=3
        # ⚠️ 死字段：技能无 charge_cfg 挂载（skills.py 全表 0 处）、引擎 battle_bars charge_def
        #   只读 skill_info.charge/charge_cfg（不读本职业 dict）→ 本 dict 零消费；删除归数据批次。
        #   兜底活源 = battle_config CHARGE_CFG（battle_bars _cfg(_battle_cfg("charge"),…)）。
        "charge": {
            "max": 3, "gain_per_turn": 1, "dmg_per_stage": [0.7, 1.3, 1.9],
            "interrupt_penalty": 1, "force_release": True, "release_power": 2.8,
            "release_extra": {"pierce": True, "reach": 3},
        },
        "attack_text": "弯弓搭箭",
        "basic_skill": {"name": "疾射", "kind": "物理", "exprs": ["atk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "弯弓搭箭"},
        "tutor": ("猎手·柯恩", "铁港城·港口广场"),
        "base": {
            "hp": 110,
            "mp": 60,
            "atk": 15,
            "def": 10,
            "matk": 8,
            "mdef": 9,
            "spd": 16,
            "crit": 0.15,
            "dodge": 0.12,
        },
        "growth": {
            "hp": 14,
            "mp": 5,
            "atk": 2.6,
            "def": 1.6,
            "matk": 0.8,
            "mdef": 1.0,
            "spd": 1.4
        },
        "weapon_type": "bow",
        "name": "游侠",
        "default_rank": 2,   # v2 站位层：后排（射手）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
    },
    "cls_mu_shi": {
        "desc": "信仰圣光的神职者，能打能奶，队伍的灵魂。",
        # v139（云海吟游诗人+圣骑士融合）：攻线歌者=全队 100%/自身 55% 双行放大器
        # （共鸣短燃料+回声长驻留，谱曲节奏 mace/staff 分化）；守线神谕=治疗即支援的圣辉引擎
        # （治疗攒圣律 vow → 随附支援不占主行动，每刻至多 1 件）。
        "mech": "治疗攒信仰值满10放神迹；攻线歌者双资源，守线圣律随附支援。",  # v130.7 意见#19 / v139 融合
        "icon": "✨",
        "role": "治疗",
        "cast_atk": 0.6,       # v156 法系定位：牧师普攻弱（法杖），输出靠治疗/技能，保持 v154 值
        "cast_defend": 0.35,
        "cast_flee": 1.0,
        # v112.3（鱼鱼拍板）：攻线"圣武士/审判骑士/裁决骑士"整体换为诗人路线——
        # 吟游诗人→灵魂歌者→黎明颂者（歌声递进：鼓舞→治愈→终极颂歌），
        # 独立隐藏职业"吟游诗人"删除并回归牧师攻线（回到 6 隐藏线结构）
        # v130.2（鱼鱼拍板）：攻线歌者转职后=双核心资源「共鸣 resonance(max10) + 回声 echo(max3)」——
        # 基础牧师仍单信仰值 faith；共鸣/回声定义已注册 core_resources.py（按资源 key 作注册键），
        # 需引擎批次 2 在 evolve_branches 攻线侧提供 分支级 resource_override 使 battle.py 能识别
        # 双资源；echo 建议落 mech_stacks 驻留叠层（战斗内不清零），刻起始全队恢复+增益续时另需引擎挂点。
        # v139：攻线歌者补双行算式+破晓长歌（EQ≈4.8）；守线神谕圣辉支援（圣律 vow 0-3，随附不占行动）
        "evolve": ["神谕者(30)", "大主教(60)", "圣光先知(90)"],
        "evolve_branches": {
            1: ["神谕者", "死灵祭司"],
            2: ["大主教", "亡魂引渡者"],
            3: ["圣光先知", "黯灵君主"],
        },
        # v139（云海圣骑士随附支援翻译）：守线圣辉支援——圣律 vow 0-3（core_resources.py 注册），
        # 治疗命中/受击攒圣律（每刻至多 1），消耗 1 圣律施放 1 件支援（不占主行动、主行动后结算）；
        # 攻线歌者共鸣/回声双资源见 core_resources.py 表尾段
        "support": {
            "res_key": "vow", "max": 3, "per_turn_cap": 1,
            "type": "post_action",  # 主行动结算后触发（随附）
        },
        "attack_text": "圣光冲击",
        "basic_skill": {"name": "圣光冲击", "kind": "魔法", "exprs": ["matk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "圣光冲击"},
        "tutor": ("圣殿执事·莉亚", "白鹿城·白鹿广场"),
        "base": {
            "hp": 100,
            "mp": 110,
            "atk": 10,
            "def": 11,
            "matk": 16,
            "mdef": 16,
            "spd": 11,
            "crit": 0.06,
            "dodge": 0.06,
            "elem_res": 0.05,
            "heal_power": 0.10,
        },
        "growth": {
            "hp": 12,
            "mp": 9,
            "atk": 1.2,
            "def": 1.8,
            "matk": 2.6,
            "mdef": 2.4,
            "spd": 0.8
        },
        "weapon_type": "mace",
        "name": "牧师",
        "default_rank": 2,   # v2 站位层：后排（远程治疗+输出）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
    },
    "cls_ci_ke": {
        "desc": "暗影中的利刃，出手必见血，暴击与闪避的极致。",
        # v139（云海盗贼+剑客融合）：段数三线投喂（攻线=连击点+连段链值 / 守线=毒层+破防），
        # 攻线链值滚雪球（影追追加段/终结+40%/暴击注入）+ 旋锋锁死（爆发覆盖率 60%）；
        # 全职业唯一判断消耗点=终结技，战前可设终结阈值档位（快刀/满刃/残血/满段）。
        "mech": "命中攒连击点满5爆发；多段投喂链值/毒层，终结阈值可配。",  # v130.7 意见#19 / v139 融合
        "icon": "🗡️",
        "role": "输出",
        "cast_atk": 0.8,       # v156 普攻节奏重标定（0.35→0.8）：裸装同级 4 轮击杀（32 章五 4-6 轮目标），满装 1.9 轮；v154 0.35s 普攻 1.8 轮秒怪致技能无价值
        "cast_defend": 0.25,   # 轻甲防御快
        "cast_flee": 0.8,      # 轻甲逃跑快
        "evolve": ["影舞者(30)", "暗影之刃(60)", "无影之刃(90)"],
        "evolve_branches": {
            # v139：攻线=影舞者（链值滚雪球+段数三线投喂）；守线=毒刃者（毒层伺服/引爆，主动放弃直破防）
            1: ["影舞者", "毒刃者"],
            2: ["暗影之刃", "淬毒师"],
            3: ["无影之刃", "蚀骨者"],
        },
        # v139（云海剑客战前阈值 DSL 翻译）：终结阈值档位——player.event_state["finisher_threshold"]
        # 战斗内只读；档位A 快刀(cp≥3) / B 满刃(cp=5) / C 残血(HP<40%+cp≥3) / D 满段(攻线链值≥8)
        "finisher_threshold": {
            "data_field": "player.event_state.finisher_threshold",
            "default": "满刃", "options": ["快刀", "满刃", "残血", "满段"],
        },
        # v139（云海盗贼段数三线投喂翻译）：攻线连段链值 combo——数值权威 = battle_config
        # COMBO_CFG（P2E 后 = MECH_CFG['assassin_combo']）：cap 10 / finish_min 3 /
        # per_layer 0.05 / max_bonus 0.40 / class_id cls_ci_ke / path 1。
        # 机制 TODO（未实装设计，零读字段不保留数值 dict）：chase_at 5 / chase_power 0.5
        # （追加段触发）/ inject_at 8（暴击注入链值）/ spin_lock 8（旋锋锁死不累积）——引擎只读 COMBO_CFG。
        "attack_text": "匕首突刺",
        "basic_skill": {"name": "暗刺", "kind": "物理", "exprs": ["atk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "匕首突刺"},
        "tutor": ("暗影渡鸦", "铁港城·港口广场"),
        "base": {
            "hp": 95,
            "mp": 70,
            "atk": 17,
            "def": 9,
            "matk": 7,
            "mdef": 8,
            "spd": 19,
            "crit": 0.2,
            "dodge": 0.18,
            "pene_phys": 0.10,
            "cdr": 0.05,
        },
        "growth": {
            "hp": 12,
            "mp": 5,
            "atk": 3.0,
            "def": 1.3,
            "matk": 0.6,
            "mdef": 0.9,
            "spd": 1.6
        },
        "weapon_type": "dagger",
        "name": "刺客",
        "default_rank": 1,   # v122f 站位层：前排（匕首近战，鱼鱼拍板：刺客哪有那么长手）
        "reach": 1,          # v122f 攻击范围：近战（原 2 错误，匕首近战系）
        "rank_label": "前排",
    },
    "cls_wu_seng": {
        "desc": "以拳入道的修行者，拳拳到肉，连击与反击的行家。",
        # v139（云海斗士×守卫融合）：攻线格斗士=「破绽积蓄」挂敌身（shaken，不吃异常免疫，
        # 打晕与破防共用一次命中，免疫巨兽唯一软解）；守线磐石行者=「磐核」承伤即收益
        # （挨打攒核/未挨打保底+1，攒满放线性倍率磐岩释能）。两线共用气+三连骨架。
        "mech": "出招攒气3/10气双档；攻线推敌破绽条，守线防御攒磐核。",  # v130.7 意见#19 / v139 融合
        "icon": "🥊",
        "role": "辅助",
        "cast_atk": 1.15,      # v154 基准减半（速度50→出招0.3s）：拳师极快
        "cast_defend": 0.25,
        "cast_flee": 0.9,
        # v112 P0-3（鱼鱼拍板）：拳斗士→格斗士、武斗师→拳术师（与隐藏线"武僧"词族拉开）
        # v139：攻线=格斗士（shaken 挂敌身+三连打晕破防）；守线=磐石行者（磐核+守御姿态保底）
        "evolve": ["格斗士(30)", "拳术师(60)", "破晓者(90)"],
        "evolve_branches": {
            1: ["格斗士", "磐石行者"],
            2: ["拳术师", "铁壁行者"],
            3: ["破晓者", "不破之壁"],
        },
        # v139（云海斗士晕眩积蓄挂敌身翻译）：破绽 shaken——ENEMY_BAR_CFG（battle_config.py）
        # max 50 / 每刻衰减 4 / 阈值 50×1.35 递增封顶 / 触发=敌方跳过下刻行动；
        # 只吃自身三律（阈值递增+免疫窗口+触发不续攒），不吃异常免疫/反弹
        "enemy_bar": {
            "shaken": {
                "max": 50, "decay_per_turn": 4,
                "threshold_base": 50, "threshold_inc": 1.35, "threshold_cap": 2.5,
                "auto_trigger": True, "immune_turns": 1, "trigger_effect": "skip_turn",
            },
        },
        # v139（云海守卫充能核翻译）：守线磐核 guard_core 0-5——引擎字面实现
        # 守御姿态受击+1 / 未受击保底+1 / 技能命中+1；磐岩释能 M=1.0+0.7×核（线性刻意，早放高频 vs 攒满峰值）
        "guard_core": {
            "max": 5, "on_defend_hit": 1, "on_defend_idle": 1,
            "discharge_base": 1.0, "discharge_per_core": 0.7,
        },
        "attack_text": "挥拳轰击",
        "basic_skill": {"name": "直拳", "kind": "物理", "exprs": ["atk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "挥拳轰击"},
        "tutor": ("船帮武师·老陈", "铁港城·港口广场"),
        "base": {
            "hp": 135,
            "mp": 55,
            "atk": 15,
            "def": 12,
            "matk": 6,
            "mdef": 11,
            "spd": 14,
            "crit": 0.1,
            "dodge": 0.12,
        },
        "growth": {
            "hp": 18,
            "mp": 4,
            "atk": 2.8,
            "def": 2.0,
            "matk": 0.5,
            "mdef": 1.6,
            "spd": 1.1
        },
        "weapon_type": "fist",
        "name": "拳师",
        "default_rank": 1,   # v2 站位层：前排
        "reach": 1,          # v2 攻击范围：近战
        "rank_label": "前排",
    },
    "cls_shi_ren": {
        "desc": "怀抱诗琴的吟游诗人，旋律即力量——唱响战歌鼓舞全队，或以挽歌瓦解敌阵。",
        # v153（第七职业独立）：v151 把诗人挂在牧师攻线（歌者词族），v153 独立为基础职业。
        # 形式「驻留旋律」：同时 1 首旋律常驻（battle_aura + 强度层），起手 0.6/吟唱 1.2/终章 2.4
        # 三档节奏切换；咏叹线把旋律唱成全队变强，挽歌线把旋律唱成敌方变弱。
        "mech": "旋律驻留：唱一首歌持续光环，强度满 5 触发终章爆发；咏叹增益线/挽歌瓦解线。",  # v153 §7
        "icon": "🎵",
        "role": "支援",
        "cast_atk": 0.5,       # v154 基准减半（速度50→出招0.5s）：弹唱起手快
        "cast_defend": 0.35,
        "cast_flee": 1.0,
        "evolve": ["咏叹者(30)", "晨曦歌者(60)", "天籁颂者(90)"],
        "evolve_branches": {
            1: ["咏叹者", "挽歌者"],
            2: ["晨曦歌者", "安魂歌者"],
            3: ["天籁颂者", "镇魂挽者"],
        },
        "attack_text": "拨弦攻击",
        "basic_skill": {"name": "拨弦", "kind": "魔法", "exprs": ["matk*1.0"], "cast": 0.0, "cd": 0, "mp": 0, "basic": True, "trigger_hit": True, "cast_verb": "拨弦攻击"},
        "tutor": ("流浪乐师·阿莱克斯", "白鹿城·酒馆"),
        "base": {
            "hp": 95,
            "mp": 105,
            "atk": 9,
            "def": 10,
            "matk": 15,
            "mdef": 14,
            "spd": 13,
            "crit": 0.07,
            "dodge": 0.08,
        },
        "growth": {
            "hp": 11,
            "mp": 9,
            "atk": 1.1,
            "def": 1.5,
            "matk": 2.5,
            "mdef": 2.2,
            "spd": 0.9
        },
        "weapon_type": "staff",
        "name": "吟游诗人",
        "default_rank": 2,   # 后排（旋律支援，自身脆弱）
        "reach": 2,
        "rank_label": "后排",
    },
}
