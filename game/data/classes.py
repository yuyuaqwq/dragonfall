# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - classes.py(v48 key 转 ID)"""
CLASSES = {
    "cls_novice": {
        "desc": "刚踏上冒险之路的新人，还没有正式职业。去冒险者行会找接待员就职，或到各城寻找职业导师吧！",
        "icon": "🧭",
        "role": "见习",
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
    },
    "cls_bard": {
        "desc": "流浪于各地的吟游诗人，歌声能鼓舞士气、也能迷惑敌人。隐藏职业，需特殊传承解锁(22 章)。",
        "icon": "🎻",
        "role": "辅助",
        "evolve": ["吟游诗人(30)", "灵魂歌者(60)", "黎明颂者(90)"],
        "evolve_branches": {
            1: ["吟游诗人"],
            2: ["灵魂歌者"],
            3: ["黎明颂者"],
        },
        "base": {
            "hp": 100,
            "mp": 100,
            "atk": 12,
            "def": 9,
            "matk": 14,
            "mdef": 12,
            "spd": 12,
            "crit": 0.06,
            "dodge": 0.05,
            "cdr": 0.10,
            "heal_power": 0.05,
        },
        "growth": {
            "hp": 9,
            "mp": 8,
            "atk": 1.2,
            "def": 1.2,
            "matk": 1.8,
            "mdef": 1.4,
            "spd": 0.9
        },
        "weapon_type": "sword",
        "name": "吟游诗人",
        "hidden": True,
        "src_base": "cls_mu_shi",  # v108 职业树：渊源根基（牧师·神谕者线，圣歌=世俗治愈变奏）
    },
    "cls_zhan_shi": {
        "desc": "身穿重甲、手持巨剑的钢铁壁垒，正面硬刚一切敌人。",
        "icon": "🛡️",
        "role": "坦克",
        "evolve": ["狂战士(30)", "狂战统领(60)", "战争领主(90)"],
                "evolve_branches": {
                    1: ["狂战士", "盾卫士"],
                    2: ["狂战统领", "坚盾卫士"],
                    3: ["战争领主", "坚城统帅"],
                },
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
        "name": "战士"
    },
    "cls_fa_shi": {
        "desc": "掌控元素之力的施法者，输出爆炸但身板脆弱。",
        "icon": "🔥",
        "role": "输出",
        "evolve": ["元素法师(30)", "元素术士(60)", "元素贤者(90)"],
                "evolve_branches": {
            1: ["元素法师", "秘法法师"],
            2: ["元素术士", "秘法术士"],
            3: ["元素贤者", "秘法贤者"],
        },
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
            "spd": 0.8
        },
        "weapon_type": "staff",
        "name": "法师"
    },
    "cls_you_xia": {
        "desc": "敏捷的弓箭手，箭无虚发，暴击与闪避的艺术家。",
        "icon": "🏹",
        "role": "输出",
        "evolve": ["猎魔人(30)", "暗夜猎手(60)", "猎魔先驱(90)"],
                "evolve_branches": {
            1: ["猎魔人", "风行者"],
            2: ["暗夜猎手", "疾风射手"],
            3: ["猎魔先驱", "疾风猎手"],
        },
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
            "spd": 1.8
        },
        "weapon_type": "bow",
        "name": "游侠"
    },
    "cls_mu_shi": {
        "desc": "信仰圣光的神职者，能打能奶，队伍的灵魂。",
        "icon": "✨",
        "role": "治疗",
        "evolve": ["圣武士(30)", "审判骑士(60)", "裁决骑士(90)"],
                "evolve_branches": {
            1: ["圣武士", "神谕者"],
            2: ["审判骑士", "大主教"],
            3: ["裁决骑士", "圣光先知"],
        },
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
            "spd": 0.7
        },
        "weapon_type": "mace",
        "name": "牧师"
    },
    "cls_ci_ke": {
        "desc": "暗影中的利刃，出手必见血，暴击与闪避的极致。",
        "icon": "🗡️",
        "role": "输出",
        "evolve": ["影舞者(30)", "幻影刺客(60)", "幽影刺客(90)"],
                "evolve_branches": {
            1: ["影舞者", "毒刃者"],
            2: ["幻影刺客", "淬毒师"],
            3: ["幽影刺客", "蚀骨者"],
        },
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
            "spd": 2.2
        },
        "weapon_type": "dagger",
        "name": "刺客"
    },
    "cls_wu_seng": {
        "desc": "以拳入道的修行者，拳拳到肉，连击与反击的行家。",
        "icon": "🥊",
        "role": "辅助",
        "evolve": ["拳斗士(30)", "武斗师(60)", "破晓者(90)"],
                "evolve_branches": {
            1: ["拳斗士", "磐石行者"],
            2: ["武斗师", "铁壁行者"],
            3: ["破晓者", "磐岩壁垒"],
        },
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
            "spd": 1.4
        },
        "weapon_type": "fist",
        "name": "拳师"
    },
    "cls_spellblade": {
        "desc": "力量×智力的双修战士——近战普攻+法术附魔，中距离爆发。隐藏职业，需完成失落图书馆试炼解锁(09 章九)。",
        "icon": "⚔️",
        "role": "输出",
        "evolve": ["魔剑士(60)", "符文骑士(75)", "咒刃领主(90)"],
        "evolve_branches": {
            1: ["魔剑士"],
            2: ["符文骑士"],
            3: ["咒刃领主"],
        },
        "base": {
            "hp": 130,
            "mp": 90,
            "atk": 16,
            "def": 11,
            "matk": 14,
            "mdef": 10,
            "spd": 12,
            "crit": 0.08,
            "dodge": 0.04,
            
            "cdr": 0.05,
        },
        "growth": {
            "hp": 19,
            "mp": 6,
            "atk": 2.6,
            "def": 1.8,
            "matk": 2.2,
            "mdef": 1.4,
            "spd": 1.0
        },
        "weapon_type": "sword",
        "name": "魔剑士",
        "hidden": True,
        "src_base": "cls_zhan_shi",  # v108 职业树：渊源根基（战士·狂战士线，力智双修）
    },
    # ================= v107 隐藏职业扩展（11 个，2026-08-13 鱼鱼拍板设计） =================
    # 设计文档：docs/HIDDEN_CLASSES_V107_DESIGN.md / 策划案 09 章五
    # 解锁统一：Lv.40+ 专属任务链（阶段⑥实现；v108 职业树起统一走 _evolve_hidden_generic 修为继承转职）
    "cls_arcanist": {
        "desc": "奥术之巅的法师——法穿 15% + 奥术印记叠层爆发。隐藏职业，需完成奥术回响任务链解锁(40 级)。",
        "icon": "🔮",
        "role": "输出",
        "evolve": ["奥术师(40)", "奥法大师(60)", "大魔导师(90)"],
        "evolve_branches": {
            1: ["奥术师"],
            2: ["奥法大师"],
            3: ["大魔导师"],
        },
        "base": {
            "hp": 95, "mp": 130, "atk": 8, "def": 7, "matk": 24, "mdef": 15,
            "spd": 12, "crit": 0.08, "dodge": 0.05,
            "pene_magi": 0.15,
        },
        "growth": {
            "hp": 10, "mp": 11, "atk": 0.8, "def": 1.0, "matk": 4.2,
            "mdef": 1.8, "spd": 0.8
        },
        "weapon_type": "staff",
        "name": "奥术师",
        "hidden": True,
        "src_base": "cls_fa_shi",  # v108 职业树：渊源根基
    },
    "cls_shadow_blade": {
        "desc": "暗影中的收割者——物穿 15% + 暴伤 20%，对残血目标斩杀。隐藏职业，需完成暗影试炼任务链解锁(40 级)。",
        "icon": "🗡️",
        "role": "输出",
        "evolve": ["影武者(40)", "影刃大师(60)", "无影之刃(90)"],
        "evolve_branches": {
            1: ["影武者"],
            2: ["影刃大师"],
            3: ["无影之刃"],
        },
        "base": {
            "hp": 100, "mp": 75, "atk": 19, "def": 9, "matk": 7, "mdef": 8,
            "spd": 20, "crit": 0.22, "dodge": 0.18,
            "pene_phys": 0.15, "crit_dmg": 0.20,
        },
        "growth": {
            "hp": 13, "mp": 5, "atk": 3.4, "def": 1.3, "matk": 0.6,
            "mdef": 0.9, "spd": 2.4
        },
        "weapon_type": "dagger",
        "name": "影武者",
        "hidden": True,
        "src_base": "cls_ci_ke",  # v108 职业树：渊源根基
    },
    "cls_dragon_warrior": {
        "desc": "龙血淬体的战士——元素抗 15% + 龙息真伤(绕过全减伤)。隐藏职业，需完成龙骨之血任务链解锁(40 级)。",
        "icon": "🐉",
        "role": "坦克",
        "evolve": ["龙血战士(40)", "龙裔斗士(60)", "龙魂战将(90)"],
        "evolve_branches": {
            1: ["龙血战士"],
            2: ["龙裔斗士"],
            3: ["龙魂战将"],
        },
        "base": {
            "hp": 160, "mp": 45, "atk": 19, "def": 15, "matk": 6, "mdef": 11,
            "spd": 10, "crit": 0.05, "dodge": 0.03,
            "elem_res": 0.15,
        },
        "growth": {
            "hp": 24, "mp": 3, "atk": 3.5, "def": 2.8, "matk": 0.5,
            "mdef": 1.3, "spd": 0.6
        },
        "weapon_type": "sword",
        "name": "龙血战士",
        "hidden": True,
        "src_base": "cls_zhan_shi",  # v108 职业树：渊源根基
    },
    "cls_void_walker": {
        "desc": "行走于深渊的暗影法师——深渊抗 15% + 吸MP(伤害回蓝)。隐藏职业，需完成深渊之门任务链解锁(40 级)。",
        "icon": "🌑",
        "role": "输出",
        "evolve": ["虚空行者(40)", "虚空先知(60)", "虚空领主(90)"],
        "evolve_branches": {
            1: ["虚空行者"],
            2: ["虚空先知"],
            3: ["虚空领主"],
        },
        "base": {
            "hp": 110, "mp": 110, "atk": 12, "def": 9, "matk": 18, "mdef": 13,
            "spd": 13, "crit": 0.08, "dodge": 0.06,
            "abyss_res": 0.15,
        },
        "growth": {
            "hp": 14, "mp": 8, "atk": 1.6, "def": 1.3, "matk": 3.0,
            "mdef": 1.8, "spd": 1.0
        },
        "weapon_type": "staff",
        "name": "虚空行者",
        "hidden": True,
        "src_base": "cls_fa_shi",  # v108 职业树：渊源根基
    },
    "cls_astrologer": {
        "desc": "仰望星空的射手——幸运 15%，运势联动暴击追加。隐藏职业，需完成占星试炼任务链解锁(40 级)。",
        "icon": "⭐",
        "role": "输出",
        "evolve": ["占星者(40)", "星相猎手(60)", "命运编织者(90)"],
        "evolve_branches": {
            1: ["占星者"],
            2: ["星相猎手"],
            3: ["命运编织者"],
        },
        "base": {
            "hp": 115, "mp": 65, "atk": 16, "def": 10, "matk": 8, "mdef": 9,
            "spd": 16, "crit": 0.16, "dodge": 0.12,
            "luck": 0.15,
        },
        "growth": {
            "hp": 15, "mp": 5, "atk": 2.8, "def": 1.6, "matk": 0.8,
            "mdef": 1.0, "spd": 1.8
        },
        "weapon_type": "bow",
        "name": "占星者",
        "hidden": True,
        "src_base": "cls_you_xia",  # v108 职业树：渊源根基
    },
    "cls_jungle_hunter": {
        "desc": "生于丛林的猎手——毒系强化，毒层引爆(毒爆)。隐藏职业，需完成丛林试炼任务链解锁(40 级)。",
        "icon": "🌿",
        "role": "输出",
        "evolve": ["丛林猎手(40)", "荒野猎人(60)", "苍林之王(90)"],
        "evolve_branches": {
            1: ["丛林猎手"],
            2: ["荒野猎人"],
            3: ["苍林之王"],
        },
        "base": {
            "hp": 115, "mp": 70, "atk": 15, "def": 10, "matk": 9, "mdef": 10,
            "spd": 17, "crit": 0.14, "dodge": 0.13,
        },
        "growth": {
            "hp": 15, "mp": 6, "atk": 2.7, "def": 1.6, "matk": 1.0,
            "mdef": 1.1, "spd": 1.9
        },
        "weapon_type": "bow",
        "name": "丛林猎手",
        "hidden": True,
        "src_base": "cls_you_xia",  # v108 职业树：渊源根基
    },
    "cls_templar": {
        "desc": "圣光的铁壁——护盾强度 15% + 格挡 10%，格挡后反击。隐藏职业，需完成圣光誓约任务链解锁(40 级)。",
        "icon": "🛡️",
        "role": "坦克",
        "evolve": ["圣殿骑士(40)", "圣辉守卫(60)", "圣光堡垒(90)"],
        "evolve_branches": {
            1: ["圣殿骑士"],
            2: ["圣辉守卫"],
            3: ["圣光堡垒"],
        },
        "base": {
            "hp": 130, "mp": 100, "atk": 12, "def": 15, "matk": 14, "mdef": 16,
            "spd": 10, "crit": 0.05, "dodge": 0.05,
            "shield_power": 0.15, "block": 0.10,
        },
        "growth": {
            "hp": 20, "mp": 7, "atk": 1.6, "def": 2.4, "matk": 2.5,
            "mdef": 2.4, "spd": 0.6
        },
        "weapon_type": "mace",
        "name": "圣殿骑士",
        "hidden": True,
        "src_base": "cls_zhan_shi",  # v108 职业树：渊源根基
    },
    "cls_wu_sheng": {
        "desc": "以武证道的拳师——连击强化(三连 0.50)，受击反击。隐藏职业，需完成苦修士试炼任务链解锁(40 级)。",
        "icon": "🥊",
        "role": "输出",
        "evolve": ["苦修士(40)", "圣痕武僧(60)", "撼岳者(90)"],
        "evolve_branches": {
            1: ["苦修士"],
            2: ["圣痕武僧"],
            3: ["撼岳者"],
        },
        "base": {
            "hp": 140, "mp": 60, "atk": 16, "def": 12, "matk": 6, "mdef": 11,
            "spd": 14, "crit": 0.10, "dodge": 0.12,
        },
        "growth": {
            "hp": 19, "mp": 4, "atk": 3.0, "def": 2.1, "matk": 0.5,
            "mdef": 1.6, "spd": 1.5
        },
        "weapon_type": "fist",
        "name": "苦修士",
        "hidden": True,
        "src_base": "cls_wu_seng",  # v108 职业树：渊源根基
    },
    "cls_blood_mage": {
        "desc": "以血换伤的法师——法吸 15% + 血魔法(消耗HP换高伤)。隐藏职业，需完成血之契约任务链解锁(40 级)。",
        "icon": "🧛",
        "role": "输出",
        "evolve": ["猩红学者(40)", "猩红术士(60)", "血之君主(90)"],
        "evolve_branches": {
            1: ["猩红学者"],
            2: ["猩红术士"],
            3: ["血之君主"],
        },
        "base": {
            "hp": 100, "mp": 120, "atk": 8, "def": 7, "matk": 23, "mdef": 14,
            "spd": 12, "crit": 0.08, "dodge": 0.05,
            "lifesteal_magi": 0.15,
        },
        "growth": {
            "hp": 12, "mp": 10, "atk": 0.8, "def": 1.0, "matk": 4.0,
            "mdef": 1.8, "spd": 0.8
        },
        "weapon_type": "staff",
        "name": "猩红学者",
        "hidden": True,
        "src_base": "cls_fa_shi",  # v108 职业树：渊源根基
    },
    "cls_necromancer": {
        "desc": "执掌亡灵的术士——召唤强化 20%，骷髅海(数量流) + 死亡契约。隐藏职业，需完成亡者低语任务链解锁(40 级)。",
        "icon": "💀",
        "role": "输出",
        "evolve": ["暗影祭司(40)", "亡魂引渡者(60)", "黯灵主教(90)"],
        "evolve_branches": {
            1: ["暗影祭司"],
            2: ["亡魂引渡者"],
            3: ["黯灵主教"],
        },
        "base": {
            "hp": 115, "mp": 115, "atk": 10, "def": 12, "matk": 17, "mdef": 15,
            "spd": 10, "crit": 0.05, "dodge": 0.05,
            "summon_power": 0.20,
        },
        "growth": {
            "hp": 15, "mp": 8, "atk": 1.2, "def": 1.9, "matk": 2.8,
            "mdef": 2.2, "spd": 0.7
        },
        "weapon_type": "mace",
        "name": "暗影祭司",
        "hidden": True,
        "src_base": "cls_mu_shi",  # v108 职业树：渊源根基
    },
    "cls_beast_king": {
        "desc": "与兽同行的驭兽师——召唤强化 30%，单宠进化(质量流)，宠强人弱。隐藏职业，需完成万兽之约任务链解锁(40 级)。",
        "icon": "🐺",
        "role": "输出",
        "evolve": ["兽王(40)", "兽灵之主(60)", "荒原领主(90)"],
        "evolve_branches": {
            1: ["兽王"],
            2: ["兽灵之主"],
            3: ["荒原领主"],
        },
        "base": {
            "hp": 120, "mp": 65, "atk": 15, "def": 11, "matk": 7, "mdef": 9,
            "spd": 17, "crit": 0.13, "dodge": 0.12,
            "summon_power": 0.30,
        },
        "growth": {
            "hp": 16, "mp": 5, "atk": 2.6, "def": 1.7, "matk": 0.6,
            "mdef": 1.0, "spd": 2.0
        },
        "weapon_type": "bow",
        "name": "兽王",
        "hidden": True,
        "src_base": "cls_you_xia",  # v108 职业树：渊源根基
    }
}
