# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - skills.py（从旧 pyc 恢复，v48 转换前）"""

PLAYER_SKILLS = {
    "战士": {
        "猛击": {
            "lv": 1,
            "mp": 5,
            "power": 1.5,
            "kind": "物理",
            "mech": "rage",
            "mech_val": 1,
            "desc": "挥剑猛击敌人，造成 150% 物理伤害，叠 1 层狂暴"
        },
        "破甲斩": {
            "lv": 5,
            "mp": 12,
            "power": 2.0,
            "kind": "物理",
            "desc": "撕裂护甲的斩击，造成 200% 伤害并降低敌防（敌人血量>70%时威力×1.4）",
            "cond": {
                "type": "enemy_hp_high",
                "hp_pct": 0.7,
                "mult": 1.4,
                "label": "破甲压制"
            }
        },
        "怒吼": {
            "lv": 10,
            "mp": 15,
            "power": 0,
            "kind": "增益",
            "effect": "atk_up",
            "desc": "怒吼提升攻击力 30%，持续 3 回合"
        },
        "旋风斩": {
            "lv": 15,
            "mp": 25,
            "power": 2.6,
            "kind": "物理",
            "mech": "rage",
            "mech_val": 1,
            "desc": "旋转斩击，造成 260% 物理伤害，叠 1 层狂暴"
        },
        "铁壁": {
            "lv": 20,
            "mp": 20,
            "power": 0,
            "kind": "增益",
            "effect": "def_up",
            "desc": "凝聚钢铁意志，防御提升 40%，持续 3 回合"
        },
        "处决": {
            "lv": 25,
            "mp": 35,
            "power": 3.5,
            "kind": "物理",
            "mech": "rage",
            "mech_val": 1,
            "desc": "对残血敌人执行处决，造成 350% 伤害（敌人血量越低伤害越高），叠 1 层狂暴"
        },
        "裂空斩": {
            "lv": 30,
            "mp": 50,
            "power": 4.5,
            "kind": "物理",
            "mech": "rage",
            "mech_val": 2,
            "cond": {
                "type": "enemy_hp_low",
                "hp_pct": 0.4,
                "mult": 1.5,
                "label": "裂空斩杀"
            },
            "desc": "撕裂天空的终极斩击，造成 450% 物理伤害，叠 2 层狂暴（残血斩杀×1.5）"
        }
    },
    "法师": {
        "火球术": {
            "lv": 1,
            "mp": 8,
            "power": 1.6,
            "kind": "魔法",
            "mech": "burn",
            "mech_val": 1,
            "desc": "投掷火球，造成 160% 魔法伤害，叠 1 层灼烧"
        },
        "寒冰箭": {
            "lv": 5,
            "mp": 14,
            "power": 2.0,
            "kind": "魔法",
            "mech": "freeze",
            "mech_val": 1,
            "desc": "冰霜之箭，造成 200% 伤害并降低敌速，概率冻结"
        },
        "雷电术": {
            "lv": 10,
            "mp": 22,
            "power": 2.4,
            "kind": "魔法",
            "cond": {
                "type": "enemy_frozen",
                "mult": 1.6,
                "label": "冰雷连携"
            },
            "desc": "召唤雷电轰击，造成 240% 魔法伤害（敌人被冻结时威力×1.6）"
        },
        "魔力涌动": {
            "lv": 15,
            "mp": 18,
            "power": 0,
            "kind": "增益",
            "effect": "matk_up",
            "desc": "魔力涌动，魔法攻击提升 35%，持续 3 回合"
        },
        "陨石术": {
            "lv": 20,
            "mp": 35,
            "power": 3.2,
            "kind": "魔法",
            "mech": "burn",
            "mech_val": 2,
            "cond": {
                "type": "enemy_hp_low",
                "hp_pct": 0.4,
                "mult": 1.5,
                "label": "陨石收割"
            },
            "desc": "召唤陨石坠落，造成 320% 魔法伤害，叠 2 层灼烧（残血×1.5）"
        },
        "奥术强化": {
            "lv": 25,
            "mp": 30,
            "power": 0,
            "kind": "增益",
            "effect": "matk_up_strong",
            "desc": "奥术之力涌入，魔法攻击提升 65%，持续 3 回合"
        },
        "龙息术": {
            "lv": 30,
            "mp": 55,
            "power": 4.8,
            "kind": "魔法",
            "mech": "burn",
            "mech_val": 3,
            "desc": "古龙之息再现，造成 480% 魔法伤害，叠 3 层灼烧"
        }
    },
    "游侠": {
        "精准射击": {
            "lv": 1,
            "mp": 5,
            "power": 1.5,
            "kind": "物理",
            "mech": "mark",
            "mech_val": 1,
            "desc": "瞄准要害射击，造成 150% 物理伤害，标记目标"
        },
        "连射": {
            "lv": 5,
            "mp": 12,
            "power": 1.2,
            "kind": "物理",
            "multi": 2,
            "mech": "wind",
            "mech_val": 1,
            "desc": "快速射出两箭，每箭造成 120% 伤害，叠 1 层风印"
        },
        "毒箭": {
            "lv": 10,
            "mp": 15,
            "power": 1.8,
            "kind": "物理",
            "mech": "poison",
            "mech_val": 2,
            "desc": "淬毒之箭，造成 180% 伤害并中毒，叠 2 层毒"
        },
        "疾风步": {
            "lv": 15,
            "mp": 18,
            "power": 0,
            "kind": "增益",
            "effect": "spd_up",
            "desc": "疾风加持，速度提升 40%，持续 3 回合"
        },
        "贯穿箭": {
            "lv": 20,
            "mp": 28,
            "power": 2.8,
            "kind": "物理",
            "pierce": True,
            "cond": {
                "type": "enemy_marked",
                "mult": 1.5,
                "label": "标记贯穿"
            },
            "desc": "无视防御的贯穿箭，造成 280% 物理伤害（目标被标记时威力×1.5）"
        },
        "鹰眼": {
            "lv": 20,
            "mp": 20,
            "power": 0,
            "kind": "增益",
            "effect": "crit_up",
            "desc": "鹰眼开启，暴击率大幅提升，持续 3 回合"
        },
        "龙息箭": {
            "lv": 30,
            "mp": 50,
            "power": 4.2,
            "kind": "物理",
            "pierce": True,
            "mech": "mark",
            "mech_val": 2,
            "cond": {
                "type": "enemy_marked",
                "mult": 1.6,
                "label": "猎杀箭雨"
            },
            "desc": "灌注龙息之力的终极一箭，造成 420% 无视防御伤害，标记目标（被标记时×1.6）"
        }
    },
    "牧师": {
        "圣光弹": {
            "lv": 1,
            "mp": 8,
            "power": 1.5,
            "kind": "魔法",
            "mech": "judge",
            "mech_val": 1,
            "desc": "凝聚圣光攻击，造成 150% 魔法伤害，暴击时叠 1 层审判"
        },
        "治愈术": {
            "lv": 5,
            "mp": 15,
            "power": 3.0,
            "kind": "治疗",
            "desc": "圣光治愈，恢复 300% 魔法攻击的生命"
        },
        "圣盾": {
            "lv": 10,
            "mp": 18,
            "power": 0,
            "kind": "增益",
            "effect": "def_up",
            "desc": "圣光护盾，防御提升 45%，持续 3 回合"
        },
        "惩戒": {
            "lv": 15,
            "mp": 25,
            "power": 2.4,
            "kind": "魔法",
            "mech": "judge",
            "mech_val": 1,
            "cond": {
                "type": "enemy_hp_high",
                "hp_pct": 0.7,
                "mult": 1.4,
                "label": "惩恶扬善"
            },
            "desc": "圣光惩戒，造成 240% 魔法伤害，暴击叠审判（敌人血量>70%时×1.4）"
        },
        "群体治愈": {
            "lv": 20,
            "mp": 35,
            "power": 4.5,
            "kind": "治疗",
            "desc": "群体圣光，恢复 450% 魔法攻击的生命"
        },
        "神圣祷言": {
            "lv": 25,
            "mp": 30,
            "power": 0,
            "kind": "增益",
            "effect": "matk_up_strong",
            "desc": "祷言加身，魔法攻击提升 65%，持续 3 回合"
        },
        "圣焰": {
            "lv": 30,
            "mp": 55,
            "power": 4.6,
            "kind": "魔法",
            "mech": "judge",
            "mech_val": 2,
            "cond": {
                "type": "player_hp_high",
                "hp_pct": 0.8,
                "mult": 1.5,
                "label": "圣战之势"
            },
            "desc": "圣焰降临，造成 460% 魔法伤害，暴击叠 2 层审判（自身血量>80%时×1.5）"
        }
    },
    "刺客": {
        "背刺": {
            "lv": 1,
            "mp": 5,
            "power": 1.8,
            "kind": "物理",
            "mech": "shadow",
            "mech_val": 1,
            "cond": {
                "type": "enemy_full_hp",
                "mult": 1.6,
                "label": "先手背刺"
            },
            "desc": "绕到敌人背后捅刺，造成 180% 物理伤害，叠 1 层影袭（满血敌人×1.6）"
        },
        "双刃乱舞": {
            "lv": 5,
            "mp": 12,
            "power": 1.2,
            "kind": "物理",
            "multi": 2,
            "mech": "shadow",
            "mech_val": 1,
            "desc": "双匕首快速连击 2 次，每次 120% 伤害，叠 1 层影袭"
        },
        "淬毒": {
            "lv": 10,
            "mp": 15,
            "power": 1.8,
            "kind": "物理",
            "mech": "poison",
            "mech_val": 2,
            "desc": "淬毒一击，造成 180% 伤害并使敌中毒，叠 2 层毒"
        },
        "影袭": {
            "lv": 15,
            "mp": 18,
            "power": 2.2,
            "kind": "物理",
            "mech": "shadow",
            "mech_val": 1,
            "desc": "遁入暗影突袭，造成 220% 物理伤害，叠 1 层影袭"
        },
        "致命标记": {
            "lv": 20,
            "mp": 25,
            "power": 2.0,
            "kind": "物理",
            "mech": "mark",
            "mech_val": 2,
            "desc": "标记目标要害，造成 200% 伤害并使其受伤增加，叠 2 层标记"
        },
        "疾影": {
            "lv": 20,
            "mp": 20,
            "power": 0,
            "kind": "增益",
            "effect": "spd_up",
            "desc": "化身疾影，速度提升 50%，持续 3 回合"
        },
        "暗杀": {
            "lv": 30,
            "mp": 50,
            "power": 4.2,
            "kind": "物理",
            "mech": "shadow_burst",
            "desc": "必杀之技，造成 420% 物理伤害，影袭层数转为额外伤害"
        }
    },
    "武僧": {
        "铁拳": {
            "lv": 1,
            "mp": 5,
            "power": 1.5,
            "kind": "物理",
            "mech": "chi",
            "mech_val": 1,
            "desc": "凝聚气劲的铁拳，造成 150% 物理伤害，攒 1 点气力"
        },
        "连打": {
            "lv": 5,
            "mp": 12,
            "power": 1.2,
            "kind": "物理",
            "multi": 2,
            "mech": "chi",
            "mech_val": 1,
            "desc": "快速连打 2 拳，每拳 120% 伤害，攒 1 点气力"
        },
        "金刚腿": {
            "lv": 10,
            "mp": 15,
            "power": 2.0,
            "kind": "物理",
            "mech": "chi",
            "mech_val": 2,
            "desc": "刚猛鞭腿，造成 200% 物理伤害，攒 2 点气力"
        },
        "内息调理": {
            "lv": 15,
            "mp": 18,
            "power": 3.0,
            "kind": "治疗",
            "desc": "运转内息，恢复 300% 攻击力的生命"
        },
        "震地击": {
            "lv": 20,
            "mp": 28,
            "power": 2.8,
            "kind": "物理",
            "mech": "chi",
            "mech_val": 2,
            "cond": {
                "type": "enemy_hp_high",
                "hp_pct": 0.7,
                "mult": 1.4,
                "label": "震地破势"
            },
            "desc": "震裂大地，造成 280% 物理伤害，攒 2 点气力（敌人血量>70%时×1.4）"
        },
        "百裂拳": {
            "lv": 25,
            "mp": 32,
            "power": 1.6,
            "kind": "物理",
            "multi": 3,
            "mech": "chi",
            "mech_val": 2,
            "desc": "百裂拳影，连打 3 拳每拳 160% 伤害，攒 2 点气力"
        },
        "气功波": {
            "lv": 30,
            "mp": 50,
            "power": 4.4,
            "kind": "物理",
            "mech": "chi_burst",
            "cond": {
                "type": "player_chi_stacks",
                "stacks": 3,
                "mult": 1.5,
                "label": "一气呵成"
            },
            "desc": "凝聚全身气劲轰出，造成 440% 物理伤害，气力层数转为额外伤害（气力≥3时×1.5）"
        }
    }
}
BRANCH_SKILLS = {
    "战士": {
        "1": {
            "狂战士": {
                "连环斩": {
                    "lv": 32,
                    "mp": 45,
                    "power": 2.6,
                    "kind": "物理",
                    "desc": "狂暴连斩 2 次，每次 260%，叠加狂暴层数",
                    "multi": 2,
                    "mech": "rage",
                    "mech_val": 2
                },
                "战吼": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "攻击+75%，叠 1 层狂暴",
                    "effect": "atk_up_strong",
                    "mech": "rage",
                    "mech_val": 1
                },
                "嗜血斩": {
                    "lv": 45,
                    "mp": 40,
                    "power": 5.8,
                    "kind": "物理",
                    "desc": "580% 吸血斩击，叠 1 层狂暴（敌方血量>70%时威力×1.5）",
                    "effect": "lifesteal",
                    "mech": "rage",
                    "mech_val": 1,
                    "cond": {
                        "type": "enemy_hp_high",
                        "hp_pct": 0.7,
                        "mult": 1.5,
                        "label": "狂暴压制"
                    }
                },
                "狂战之魂": {
                    "lv": 55,
                    "mp": 45,
                    "power": 0,
                    "kind": "增益",
                    "desc": "消耗全部狂暴层，每层 +18% 攻击，持续 3 回合",
                    "effect": "rage_burst"
                }
            },
            "圣骑士": {
                "圣光斩": {
                    "lv": 32,
                    "mp": 45,
                    "power": 5.0,
                    "kind": "物理",
                    "desc": "500% 无视防御圣光斩，叠 1 层圣盾",
                    "pierce": True,
                    "mech": "shield",
                    "mech_val": 1
                },
                "圣盾术": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "防御+45%，叠 2 层圣盾",
                    "effect": "def_up",
                    "mech": "shield",
                    "mech_val": 2
                },
                "圣光祝福": {
                    "lv": 45,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "攻击+75%，叠 1 层圣盾",
                    "effect": "atk_up_strong",
                    "mech": "shield",
                    "mech_val": 1
                },
                "盾击": {
                    "lv": 55,
                    "mp": 50,
                    "power": 6.2,
                    "kind": "物理",
                    "desc": "消耗全部圣盾层，每层 +12% 伤害（自身有护盾时威力×1.5）",
                    "mech": "shield_burst",
                    "cond": {
                        "type": "player_shield",
                        "mult": 1.5,
                        "label": "坚盾反击"
                    }
                }
            }
        },
        "2": {
            "狂战统领": {
                "狂暴连斩": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "狂暴连斩 3 次每次 220%，叠 2 层狂暴",
                    "multi": 3,
                    "mech": "rage",
                    "mech_val": 2
                },
                "破防斩": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.5,
                    "kind": "物理",
                    "desc": "750% 无视防御，叠 1 层狂暴",
                    "pierce": True,
                    "mech": "rage",
                    "mech_val": 1
                }
            },
            "圣殿骑士": {
                "坚守": {
                    "lv": 62,
                    "mp": 45,
                    "power": 0,
                    "kind": "增益",
                    "desc": "防御+45%，叠 2 层圣盾",
                    "effect": "def_up",
                    "mech": "shield",
                    "mech_val": 2
                },
                "圣光冲击": {
                    "lv": 68,
                    "mp": 65,
                    "power": 2.6,
                    "kind": "物理",
                    "desc": "圣光冲击 2 次每次 260%，叠 1 层圣盾",
                    "multi": 2,
                    "mech": "shield",
                    "mech_val": 1
                }
            }
        },
        "3": {
            "战争领主": {
                "狂风连斩": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.0,
                    "kind": "物理",
                    "desc": "狂风连斩 4 次每次 200%，叠 3 层狂暴",
                    "multi": 4,
                    "mech": "rage",
                    "mech_val": 3
                },
                "致命重斩": {
                    "lv": 98,
                    "mp": 105,
                    "power": 9.5,
                    "kind": "物理",
                    "desc": "950% 无视防御，消耗狂暴层每层 +15%",
                    "pierce": True,
                    "mech": "rage_burst"
                }
            },
            "守护骑士": {
                "圣光冲锋": {
                    "lv": 92,
                    "mp": 80,
                    "power": 5.5,
                    "kind": "物理",
                    "desc": "550% 圣光冲锋，叠 2 层圣盾",
                    "mech": "shield",
                    "mech_val": 2
                },
                "圣光惩戒": {
                    "lv": 98,
                    "mp": 105,
                    "power": 9.0,
                    "kind": "物理",
                    "desc": "900% 无视防御，消耗圣盾层每层 +14%",
                    "pierce": True,
                    "mech": "shield_burst"
                }
            }
        }
    },
    "法师": {
        "1": {
            "元素大师": {
                "烈焰冲击": {
                    "lv": 32,
                    "mp": 45,
                    "power": 5.2,
                    "kind": "魔法",
                    "desc": "520% 烈焰冲击，叠 2 层灼烧",
                    "mech": "burn",
                    "mech_val": 2
                },
                "魔力激荡": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "魔攻+75%，叠 1 层灼烧",
                    "effect": "matk_up_strong",
                    "mech": "burn",
                    "mech_val": 1
                },
                "连珠火球": {
                    "lv": 45,
                    "mp": 45,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "连珠火球 2 次每次 240%，叠 2 层灼烧",
                    "multi": 2,
                    "mech": "burn",
                    "mech_val": 2
                },
                "元素狂暴": {
                    "lv": 55,
                    "mp": 50,
                    "power": 0,
                    "kind": "增益",
                    "desc": "引爆灼烧：每层灼烧立即造成 30% 魔攻伤害（敌方血量<40%时威力×1.8）",
                    "effect": "burn_burst",
                    "cond": {
                        "type": "enemy_hp_low",
                        "hp_pct": 0.4,
                        "mult": 1.8,
                        "label": "残血引爆"
                    }
                }
            },
            "冰霜贤者": {
                "冰枪术": {
                    "lv": 32,
                    "mp": 45,
                    "power": 5.2,
                    "kind": "魔法",
                    "desc": "520% 冰枪，概率冻结敌人 1 回合",
                    "mech": "freeze",
                    "mech_val": 1
                },
                "寒冰壁垒": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "防御+45%，冰系技能冻结概率+15%",
                    "effect": "def_up",
                    "mech": "freeze",
                    "mech_val": 1
                },
                "冰霜新星": {
                    "lv": 45,
                    "mp": 45,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "冰霜新星 2 次每次 240%，概率冻结",
                    "multi": 2,
                    "mech": "freeze",
                    "mech_val": 1
                },
                "冰锥术": {
                    "lv": 55,
                    "mp": 50,
                    "power": 6.5,
                    "kind": "魔法",
                    "desc": "650% 巨型冰锥，冻结概率翻倍（敌人被冻结时威力×1.7）",
                    "mech": "freeze",
                    "mech_val": 2,
                    "cond": {
                        "type": "enemy_frozen",
                        "mult": 1.7,
                        "label": "碎冰重击"
                    }
                }
            }
        },
        "2": {
            "烈焰术士": {
                "爆炎术": {
                    "lv": 62,
                    "mp": 65,
                    "power": 2.6,
                    "kind": "魔法",
                    "desc": "爆炎连爆 3 次每次 260%，叠 3 层灼烧",
                    "multi": 3,
                    "mech": "burn",
                    "mech_val": 3
                },
                "熔岩爆破": {
                    "lv": 68,
                    "mp": 80,
                    "power": 7.8,
                    "kind": "魔法",
                    "desc": "780% 无视防御，叠 2 层灼烧",
                    "pierce": True,
                    "mech": "burn",
                    "mech_val": 2
                }
            },
            "寒霜术士": {
                "寒冰风暴": {
                    "lv": 62,
                    "mp": 65,
                    "power": 2.6,
                    "kind": "魔法",
                    "desc": "寒冰风暴 3 次每次 260%，概率冻结",
                    "multi": 3,
                    "mech": "freeze",
                    "mech_val": 1
                },
                "极寒冰刺": {
                    "lv": 68,
                    "mp": 80,
                    "power": 7.8,
                    "kind": "魔法",
                    "desc": "780% 无视防御，冻结目标额外 +50%",
                    "pierce": True,
                    "mech": "freeze",
                    "mech_val": 2
                }
            }
        },
        "3": {
            "大法师": {
                "奥术风暴": {
                    "lv": 92,
                    "mp": 90,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "奥术风暴 4 次每次 240%，叠 4 层灼烧",
                    "multi": 4,
                    "mech": "burn",
                    "mech_val": 4
                },
                "烈焰新星": {
                    "lv": 98,
                    "mp": 110,
                    "power": 10.0,
                    "kind": "魔法",
                    "desc": "1000% 无视防御，引爆全部灼烧层",
                    "pierce": True,
                    "mech": "burn_burst"
                }
            },
            "奥术贤者": {
                "冰霜漩涡": {
                    "lv": 92,
                    "mp": 90,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "冰霜漩涡 4 次每次 240%，高概率冻结",
                    "multi": 4,
                    "mech": "freeze",
                    "mech_val": 2
                },
                "绝对零度": {
                    "lv": 98,
                    "mp": 110,
                    "power": 10.0,
                    "kind": "魔法",
                    "desc": "1000% 无视防御，必定冻结",
                    "pierce": True,
                    "mech": "freeze",
                    "mech_val": 5
                }
            }
        }
    },
    "游侠": {
        "1": {
            "猎魔人": {
                "追猎箭": {
                    "lv": 32,
                    "mp": 40,
                    "power": 5.0,
                    "kind": "物理",
                    "desc": "500% 追猎箭，标记目标 2 回合",
                    "mech": "mark",
                    "mech_val": 2
                },
                "猎手本能": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "暴击提升，叠 1 层猎杀印记",
                    "effect": "crit_up",
                    "mech": "mark",
                    "mech_val": 1
                },
                "双箭齐发": {
                    "lv": 45,
                    "mp": 40,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "双箭齐发 2 次每次 240%，标记目标",
                    "multi": 2,
                    "mech": "mark",
                    "mech_val": 1
                },
                "夺命射击": {
                    "lv": 55,
                    "mp": 45,
                    "power": 6.8,
                    "kind": "物理",
                    "desc": "680% 夺命一击，对标记目标每层 +20%（敌方血量<40%时威力×1.6）",
                    "mech": "mark_burst",
                    "cond": {
                        "type": "enemy_hp_low",
                        "hp_pct": 0.4,
                        "mult": 1.6,
                        "label": "处决狙击"
                    }
                }
            },
            "风行者": {
                "疾风射击": {
                    "lv": 32,
                    "mp": 40,
                    "power": 5.0,
                    "kind": "物理",
                    "desc": "500% 疾风射击，叠 1 层风印（每层连击+1）",
                    "mech": "wind",
                    "mech_val": 1
                },
                "风行步": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "速度+40%，叠 2 层风印",
                    "effect": "spd_up",
                    "mech": "wind",
                    "mech_val": 2
                },
                "双重射击": {
                    "lv": 45,
                    "mp": 40,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "双重射击 2 次每次 240%，叠 1 层风印",
                    "multi": 2,
                    "mech": "wind",
                    "mech_val": 1
                },
                "精准打击": {
                    "lv": 55,
                    "mp": 45,
                    "power": 6.2,
                    "kind": "物理",
                    "desc": "620% 精准打击，风印层数转化为连击次数（自身加速时威力×1.5）",
                    "mech": "wind_burst",
                    "cond": {
                        "type": "player_spd_up",
                        "mult": 1.5,
                        "label": "风行无影"
                    }
                }
            }
        },
        "2": {
            "暗夜猎手": {
                "三连矢": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "三连矢 3 次每次 240%，标记目标",
                    "multi": 3,
                    "mech": "mark",
                    "mech_val": 2
                },
                "暗影之箭": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.5,
                    "kind": "物理",
                    "desc": "750% 无视防御，标记目标",
                    "pierce": True,
                    "mech": "mark",
                    "mech_val": 1
                }
            },
            "疾风射手": {
                "疾风连射": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "疾风连射 3 次每次 240%，叠 2 层风印",
                    "multi": 3,
                    "mech": "wind",
                    "mech_val": 2
                },
                "穿透射击": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.5,
                    "kind": "物理",
                    "desc": "750% 无视防御，叠 1 层风印",
                    "pierce": True,
                    "mech": "wind",
                    "mech_val": 1
                }
            }
        },
        "3": {
            "猎魔大师": {
                "风暴箭雨": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "风暴箭雨 4 次每次 220%，标记目标",
                    "multi": 4,
                    "mech": "mark",
                    "mech_val": 3
                },
                "致命猎杀": {
                    "lv": 98,
                    "mp": 100,
                    "power": 9.2,
                    "kind": "物理",
                    "desc": "920% 无视防御，猎杀标记每层 +22%",
                    "pierce": True,
                    "mech": "mark_burst"
                }
            },
            "神射手": {
                "漫天箭雨": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "漫天箭雨 4 次每次 220%，叠 3 层风印",
                    "multi": 4,
                    "mech": "wind",
                    "mech_val": 3
                },
                "百发百中": {
                    "lv": 98,
                    "mp": 100,
                    "power": 9.2,
                    "kind": "物理",
                    "desc": "920% 无视防御，风印层数转化为连击",
                    "pierce": True,
                    "mech": "wind_burst"
                }
            }
        }
    },
    "牧师": {
        "1": {
            "圣武士": {
                "圣光之刃": {
                    "lv": 32,
                    "mp": 45,
                    "power": 5.0,
                    "kind": "魔法",
                    "desc": "500% 圣光之刃，暴击时叠 1 层审判",
                    "mech": "judge",
                    "mech_val": 1
                },
                "圣战之誓": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "魔攻+75%，叠 1 层审判",
                    "effect": "matk_up_strong",
                    "mech": "judge",
                    "mech_val": 1
                },
                "圣光连击": {
                    "lv": 45,
                    "mp": 45,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "圣光连击 2 次每次 240%，暴击叠审判",
                    "multi": 2,
                    "mech": "judge",
                    "mech_val": 1
                },
                "圣裁之光": {
                    "lv": 55,
                    "mp": 50,
                    "power": 6.5,
                    "kind": "魔法",
                    "desc": "650% 圣裁，消耗审判层每层 +15%（自身血量>80%时威力×1.5）",
                    "mech": "judge_burst",
                    "cond": {
                        "type": "player_hp_high",
                        "hp_pct": 0.8,
                        "mult": 1.5,
                        "label": "圣战之势"
                    }
                }
            },
            "神谕者": {
                "圣言术": {
                    "lv": 32,
                    "mp": 45,
                    "power": 4.8,
                    "kind": "魔法",
                    "desc": "480% 圣言术，过量治疗转护盾",
                    "mech": "bless",
                    "mech_val": 1
                },
                "庇护之光": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "防御+45%，神恩+1",
                    "effect": "def_up",
                    "mech": "bless",
                    "mech_val": 1
                },
                "恢复术": {
                    "lv": 45,
                    "mp": 45,
                    "power": 6.0,
                    "kind": "治疗",
                    "desc": "恢复 600% 魔攻生命，过量转护盾",
                    "mech": "bless",
                    "mech_val": 2
                },
                "大治愈术": {
                    "lv": 55,
                    "mp": 55,
                    "power": 8.0,
                    "kind": "治疗",
                    "desc": "恢复 800% 魔攻生命，神恩层数增加护盾（自身血量<50%时治疗量×1.8）",
                    "mech": "bless",
                    "mech_val": 3,
                    "cond": {
                        "type": "player_hp_low",
                        "hp_pct": 0.5,
                        "mult": 1.8,
                        "label": "濒危救治"
                    }
                }
            }
        },
        "2": {
            "审判骑士": {
                "圣光三连": {
                    "lv": 62,
                    "mp": 65,
                    "power": 2.6,
                    "kind": "魔法",
                    "desc": "圣光三连 3 次每次 260%，暴击叠审判",
                    "multi": 3,
                    "mech": "judge",
                    "mech_val": 2
                },
                "审判之剑": {
                    "lv": 68,
                    "mp": 80,
                    "power": 7.6,
                    "kind": "魔法",
                    "desc": "760% 无视防御，叠 1 层审判",
                    "pierce": True,
                    "mech": "judge",
                    "mech_val": 1
                }
            },
            "大主教": {
                "圣光震荡": {
                    "lv": 62,
                    "mp": 65,
                    "power": 2.6,
                    "kind": "魔法",
                    "desc": "圣光震荡 3 次每次 260%，神恩+2",
                    "multi": 3,
                    "mech": "bless",
                    "mech_val": 2
                },
                "神恩庇护": {
                    "lv": 68,
                    "mp": 70,
                    "power": 0,
                    "kind": "增益",
                    "desc": "消耗神恩层数转化为护盾，每层 8% 魔攻",
                    "effect": "bless_shield"
                }
            }
        },
        "3": {
            "裁决骑士": {
                "圣光风暴": {
                    "lv": 92,
                    "mp": 90,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "圣光风暴 4 次每次 240%，暴击叠审判",
                    "multi": 4,
                    "mech": "judge",
                    "mech_val": 3
                },
                "最终审判": {
                    "lv": 98,
                    "mp": 110,
                    "power": 9.8,
                    "kind": "魔法",
                    "desc": "980% 无视防御，审判层每层 +18%",
                    "pierce": True,
                    "mech": "judge_burst"
                }
            },
            "神眷者": {
                "圣光之雨": {
                    "lv": 92,
                    "mp": 90,
                    "power": 2.4,
                    "kind": "魔法",
                    "desc": "圣光之雨 4 次每次 240%，神恩+3",
                    "multi": 4,
                    "mech": "bless",
                    "mech_val": 3
                },
                "神圣之光": {
                    "lv": 98,
                    "mp": 110,
                    "power": 9.8,
                    "kind": "魔法",
                    "desc": "980% 无视防御，神恩转护盾",
                    "pierce": True,
                    "mech": "bless_shield"
                }
            }
        }
    },
    "刺客": {
        "1": {
            "影舞者": {
                "影刃": {
                    "lv": 32,
                    "mp": 40,
                    "power": 5.2,
                    "kind": "物理",
                    "desc": "520% 影刃，满血目标必暴",
                    "mech": "shadow",
                    "mech_val": 1
                },
                "暗影步伐": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "速度+50%，影袭印记+1",
                    "effect": "spd_up",
                    "mech": "shadow",
                    "mech_val": 1
                },
                "影刃连刺": {
                    "lv": 45,
                    "mp": 40,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "影刃连刺 2 次每次 240%，叠 2 层影袭",
                    "multi": 2,
                    "mech": "shadow",
                    "mech_val": 2
                },
                "致命突袭": {
                    "lv": 55,
                    "mp": 45,
                    "power": 6.8,
                    "kind": "物理",
                    "desc": "680% 致命突袭，影袭层每层 +18%（敌方满血时威力×1.6）",
                    "mech": "shadow_burst",
                    "cond": {
                        "type": "enemy_full_hp",
                        "mult": 1.6,
                        "label": "先手背刺"
                    }
                }
            },
            "毒刃者": {
                "淬毒匕首": {
                    "lv": 32,
                    "mp": 40,
                    "power": 5.0,
                    "kind": "物理",
                    "desc": "500% 淬毒匕首，叠 2 层毒",
                    "mech": "poison",
                    "mech_val": 2
                },
                "淬毒术": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "暴击提升，叠 1 层毒",
                    "effect": "crit_up",
                    "mech": "poison",
                    "mech_val": 1
                },
                "毒刃双刺": {
                    "lv": 45,
                    "mp": 40,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "毒刃双刺 2 次每次 240%，叠 2 层毒",
                    "multi": 2,
                    "mech": "poison",
                    "mech_val": 2
                },
                "毒蚀": {
                    "lv": 55,
                    "mp": 45,
                    "power": 6.2,
                    "kind": "物理",
                    "desc": "620% 毒蚀，引爆毒层每层 +15%（敌方中毒≥3层时威力×1.6）",
                    "mech": "poison_burst",
                    "cond": {
                        "type": "enemy_poison_stacks",
                        "stacks": 3,
                        "mult": 1.6,
                        "label": "剧毒侵蚀"
                    }
                }
            }
        },
        "2": {
            "幻影刺客": {
                "幻影连刺": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "幻影连刺 3 次每次 240%，叠 2 层影袭",
                    "multi": 3,
                    "mech": "shadow",
                    "mech_val": 2
                },
                "暗影割喉": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.6,
                    "kind": "物理",
                    "desc": "760% 无视防御，叠 1 层影袭",
                    "pierce": True,
                    "mech": "shadow",
                    "mech_val": 1
                }
            },
            "淬毒大师": {
                "毒刃连舞": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "毒刃连舞 3 次每次 240%，叠 3 层毒",
                    "multi": 3,
                    "mech": "poison",
                    "mech_val": 3
                },
                "淬毒刺杀": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.6,
                    "kind": "物理",
                    "desc": "760% 无视防御，叠 2 层毒",
                    "pierce": True,
                    "mech": "poison",
                    "mech_val": 2
                }
            }
        },
        "3": {
            "暗影刺客": {
                "暗影狂舞": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "暗影狂舞 4 次每次 220%，叠 3 层影袭",
                    "multi": 4,
                    "mech": "shadow",
                    "mech_val": 3
                },
                "暗影一击": {
                    "lv": 98,
                    "mp": 100,
                    "power": 9.4,
                    "kind": "物理",
                    "desc": "940% 无视防御，影袭层每层 +20%",
                    "pierce": True,
                    "mech": "shadow_burst"
                }
            },
            "剧毒大师": {
                "剧毒乱刺": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "剧毒乱刺 4 次每次 220%，叠 4 层毒",
                    "multi": 4,
                    "mech": "poison",
                    "mech_val": 4
                },
                "毒杀": {
                    "lv": 98,
                    "mp": 100,
                    "power": 9.4,
                    "kind": "物理",
                    "desc": "940% 无视防御，引爆毒层每层 +18%",
                    "pierce": True,
                    "mech": "poison_burst"
                }
            }
        }
    },
    "武僧": {
        "1": {
            "拳师": {
                "寸劲": {
                    "lv": 32,
                    "mp": 40,
                    "power": 5.0,
                    "kind": "物理",
                    "desc": "500% 寸劲，攒 2 点气力",
                    "mech": "chi",
                    "mech_val": 2
                },
                "气劲凝聚": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "攻击+75%，攒 1 点气力",
                    "effect": "atk_up_strong",
                    "mech": "chi",
                    "mech_val": 1
                },
                "连环拳": {
                    "lv": 45,
                    "mp": 40,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "连环拳 2 次每次 240%，攒 2 点气力",
                    "multi": 2,
                    "mech": "chi",
                    "mech_val": 2
                },
                "重拳": {
                    "lv": 55,
                    "mp": 45,
                    "power": 6.5,
                    "kind": "物理",
                    "desc": "650% 重拳，气力每点 +12%（气力≥3点时威力×1.6）",
                    "mech": "chi_burst",
                    "cond": {
                        "type": "player_chi_stacks",
                        "stacks": 3,
                        "mult": 1.6,
                        "label": "一气呵成"
                    }
                }
            },
            "金刚罗汉": {
                "罗汉拳": {
                    "lv": 32,
                    "mp": 40,
                    "power": 5.0,
                    "kind": "物理",
                    "desc": "500% 罗汉拳，叠 1 层金身（减伤+反伤）",
                    "mech": "iron",
                    "mech_val": 1
                },
                "金钟罩": {
                    "lv": 38,
                    "mp": 35,
                    "power": 0,
                    "kind": "增益",
                    "desc": "防御+45%，叠 2 层金身",
                    "effect": "def_up",
                    "mech": "iron",
                    "mech_val": 2
                },
                "金刚连拳": {
                    "lv": 45,
                    "mp": 40,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "金刚连拳 2 次每次 240%，叠 1 层金身",
                    "multi": 2,
                    "mech": "iron",
                    "mech_val": 1
                },
                "伏虎拳": {
                    "lv": 55,
                    "mp": 45,
                    "power": 6.2,
                    "kind": "物理",
                    "desc": "620% 伏虎拳，金身层转伤害（自身血量<30%时威力×1.8）",
                    "mech": "iron_burst",
                    "cond": {
                        "type": "player_hp_low",
                        "hp_pct": 0.3,
                        "mult": 1.8,
                        "label": "背水金身"
                    }
                }
            }
        },
        "2": {
            "武斗大师": {
                "三连拳": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "三连拳 3 次每次 240%，攒 3 点气力",
                    "multi": 3,
                    "mech": "chi",
                    "mech_val": 3
                },
                "破甲拳": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.5,
                    "kind": "物理",
                    "desc": "750% 无视防御，攒 1 点气力",
                    "pierce": True,
                    "mech": "chi",
                    "mech_val": 1
                }
            },
            "不动金刚": {
                "罗汉连拳": {
                    "lv": 62,
                    "mp": 60,
                    "power": 2.4,
                    "kind": "物理",
                    "desc": "罗汉连拳 3 次每次 240%，叠 2 层金身",
                    "multi": 3,
                    "mech": "iron",
                    "mech_val": 2
                },
                "金身冲击": {
                    "lv": 68,
                    "mp": 75,
                    "power": 7.5,
                    "kind": "物理",
                    "desc": "750% 无视防御，叠 1 层金身",
                    "pierce": True,
                    "mech": "iron",
                    "mech_val": 1
                }
            }
        },
        "3": {
            "拳法宗师": {
                "百裂连击": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "百裂连击 4 次每次 220%，攒 4 点气力",
                    "multi": 4,
                    "mech": "chi",
                    "mech_val": 4
                },
                "拳法奥义": {
                    "lv": 98,
                    "mp": 100,
                    "power": 9.4,
                    "kind": "物理",
                    "desc": "940% 无视防御，气力每点 +15%",
                    "pierce": True,
                    "mech": "chi_burst"
                }
            },
            "金刚不坏": {
                "金身连打": {
                    "lv": 92,
                    "mp": 85,
                    "power": 2.2,
                    "kind": "物理",
                    "desc": "金身连打 4 次每次 220%，叠 3 层金身",
                    "multi": 4,
                    "mech": "iron",
                    "mech_val": 3
                },
                "不坏金身": {
                    "lv": 98,
                    "mp": 100,
                    "power": 9.4,
                    "kind": "物理",
                    "desc": "940% 无视防御，金身层转伤害",
                    "pierce": True,
                    "mech": "iron_burst"
                }
            }
        }
    }
}
REMOVED_SKILLS = {
    "战意沸腾": 20,
    "狂战之怒": 35,
    "战斧投掷": 40,
    "裂地斩": 50,
    "无尽斩击": 60,
    "破城重斩": 80,
    "裁决重斩": 90,
    "破碎重击": 100,
    "寒冰护盾": 20,
    "火焰风暴": 35,
    "冰晶结界": 40,
    "雷暴术": 45,
    "时空裂隙": 50,
    "奥术洪流": 55,
    "极光轰炸": 60,
    "元素融合": 70,
    "暗影领域": 80,
    "陨星术": 90,
    "禁忌魔法": 100,
    "标记猎杀": 25,
    "穿透箭雨": 35,
    "迅捷射击": 40,
    "影袭": 45,
    "猎杀标记": 50,
    "穿风之箭": 55,
    "多重射击": 60,
    "幻影步": 70,
    "致命狙击": 80,
    "百步穿杨": 90,
    "穿云之箭": 100,
    "驱散": 20,
    "圣光审判": 35,
    "神圣庇护": 40,
    "复活术": 45,
    "圣歌": 50,
    "圣盾壁垒": 55,
    "圣恩": 60,
    "圣光领域": 70,
    "圣光裁决": 80,
    "圣眷": 90,
    "圣光之辉": 100,
    "毒刃风暴": 25,
    "绝命突刺": 35,
    "烟雾弹": 40,
    "毒刃连刺": 45,
    "影分身": 50,
    "嗜血匕首": 55,
    "死神之舞": 60,
    "暗影突袭": 70,
    "割喉": 80,
    "影遁": 90,
    "虚空刺杀": 100,
    "铁布衫": 40,
    "龙爪手": 45,
    "如来神掌": 50,
    "斗转星移": 55,
    "万佛朝宗": 60,
    "不动明王": 70,
    "天龙八部": 80,
    "金身不坏": 90,
    "破碎虚空": 100
}
