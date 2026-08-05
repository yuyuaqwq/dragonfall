# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - monsters.py（v48 key 转 ID）"""
MONSTER_SKILLS = {
    "ms_si_yao": {
        "kind": "物理",
        "power": 1.2,
        "desc": "用尖牙撕咬敌人",
        "name": "撕咬"
    },
    "ms_zhao_ji": {
        "kind": "物理",
        "power": 1.3,
        "desc": "用利爪攻击敌人",
        "name": "爪击"
    },
    "ms_chong_zhuang": {
        "kind": "物理",
        "power": 1.5,
        "desc": "猛力冲撞敌人",
        "name": "冲撞"
    },
    "ms_pi_kan": {
        "kind": "物理",
        "power": 1.4,
        "desc": "挥砍武器攻击",
        "name": "劈砍"
    },
    "ms_zhong_ji": {
        "kind": "物理",
        "power": 1.8,
        "desc": "蓄力重击敌人",
        "name": "重击"
    },
    "ms_dun_ji": {
        "kind": "物理",
        "power": 1.5,
        "desc": "用盾牌猛击，降低敌防",
        "name": "盾击"
    },
    "ms_du_yao": {
        "kind": "物理",
        "power": 1.3,
        "desc": "带毒的撕咬，造成中毒",
        "name": "毒咬"
    },
    "ms_bing_yao": {
        "kind": "物理",
        "power": 1.4,
        "desc": "寒冰之咬，降低敌速",
        "name": "冰咬"
    },
    "ms_hao_jiao": {
        "kind": "增益",
        "effect": "atk_up",
        "desc": "嚎叫提升自身攻击",
        "name": "嚎叫"
    },
    "ms_nu_hou": {
        "kind": "增益",
        "effect": "atk_up",
        "desc": "怒吼提升自身攻击",
        "name": "怒吼"
    },
    "ms_zhan_hou": {
        "kind": "增益",
        "effect": "atk_up",
        "desc": "战吼大幅提升自身攻击",
        "name": "战吼"
    },
    "ms_kuang_bao": {
        "kind": "增益",
        "effect": "atk_up_strong",
        "desc": "进入狂暴状态，攻击大幅提升",
        "name": "狂暴"
    },
    "ms_zi_ran_zhu_fu": {
        "kind": "增益",
        "effect": "heal_self",
        "desc": "自然之力治愈自身",
        "name": "自然祝福"
    },
    "ms_zai_sheng": {
        "kind": "增益",
        "effect": "heal_self",
        "desc": "巨魔再生，恢复生命",
        "name": "再生"
    },
    "ms_mo_fa_fei_dan": {
        "kind": "魔法",
        "power": 1.4,
        "desc": "射出魔法飞弹",
        "name": "魔法飞弹"
    },
    "ms_huo_qiu": {
        "kind": "魔法",
        "power": 1.7,
        "desc": "投掷火球",
        "name": "火球"
    },
    "ms_shan_dian_jian": {
        "kind": "魔法",
        "power": 1.7,
        "desc": "射出闪电",
        "name": "闪电箭"
    },
    "ms_an_ying_jian": {
        "kind": "魔法",
        "power": 1.8,
        "desc": "射出暗影能量",
        "name": "暗影箭"
    },
    "ms_ji_qu": {
        "kind": "魔法",
        "power": 1.5,
        "desc": "吸取敌人生命",
        "name": "汲取"
    },
    "ms_ai_hao": {
        "kind": "魔法",
        "power": 1.2,
        "desc": "刺耳哀嚎",
        "name": "哀嚎"
    },
    "ms_jian_xiao": {
        "kind": "魔法",
        "power": 1.3,
        "desc": "刺耳尖啸",
        "name": "尖啸"
    },
    "ms_zhuo_shao": {
        "kind": "魔法",
        "power": 1.5,
        "desc": "灼烧敌人",
        "name": "灼烧"
    },
    "ms_lei_ji": {
        "kind": "魔法",
        "power": 1.9,
        "desc": "召唤雷电",
        "name": "雷击"
    },
    "ms_feng_ren": {
        "kind": "物理",
        "power": 1.6,
        "desc": "风之利刃",
        "name": "风刃"
    },
    "ms_shuang_xi": {
        "kind": "魔法",
        "power": 2.0,
        "desc": "吐出寒霜吐息",
        "name": "霜息"
    },
    "ms_bao_feng_xue": {
        "kind": "魔法",
        "power": 1.8,
        "desc": "召唤暴风雪",
        "name": "暴风雪"
    },
    "ms_sheng_guang_chong_feng": {
        "kind": "物理",
        "power": 2.0,
        "desc": "裹挟圣光冲锋",
        "name": "圣光冲锋"
    },
    "ms_jian_ta": {
        "kind": "物理",
        "power": 1.6,
        "desc": "猛踏地面",
        "name": "践踏"
    },
    "ms_chan_rao": {
        "kind": "物理",
        "power": 1.4,
        "desc": "缠绕敌人，降低其速",
        "name": "缠绕"
    },
    "ms_fu_chong": {
        "kind": "物理",
        "power": 1.5,
        "desc": "从天俯冲攻击",
        "name": "俯冲"
    },
    "ms_zhao_huan": {
        "kind": "增益",
        "effect": "summon",
        "desc": "召唤援军",
        "name": "召唤"
    },
    "ms_zhao_hun": {
        "kind": "增益",
        "effect": "summon",
        "desc": "招魂骷髅",
        "name": "招魂"
    },
    "ms_di_dong": {
        "kind": "物理",
        "power": 1.8,
        "desc": "引发地震",
        "name": "地动"
    },
    "ms_lie_yan_zhen_ji": {
        "kind": "魔法",
        "power": 2.0,
        "desc": "烈焰震击大地",
        "name": "烈焰震击"
    },
    "ms_yan_jiang_pen_fa": {
        "kind": "魔法",
        "power": 2.4,
        "desc": "岩浆喷发",
        "name": "岩浆喷发"
    },
    "ms_fu_xi": {
        "kind": "魔法",
        "power": 1.8,
        "desc": "腐败吐息",
        "name": "腐息"
    },
    "ms_si_wang_zhi_wo": {
        "kind": "魔法",
        "power": 1.7,
        "desc": "死亡之力扼住敌人",
        "name": "死亡之握"
    },
    "ms_wu_yao_qi_she": {
        "kind": "魔法",
        "power": 2.2,
        "desc": "齐射暗影能量",
        "name": "巫妖齐射"
    },
    "ms_xu_kong_zhan": {
        "kind": "物理",
        "power": 2.0,
        "desc": "虚空之力斩击",
        "name": "虚空斩"
    },
    "ms_di_yu_huo": {
        "kind": "魔法",
        "power": 2.4,
        "desc": "召唤地狱火",
        "name": "地狱火"
    },
    "ms_an_ying_feng_bao": {
        "kind": "魔法",
        "power": 2.6,
        "desc": "暗影风暴席卷",
        "name": "暗影风暴"
    },
    "ms_hui_mie_zhi_ji": {
        "kind": "魔法",
        "power": 3.0,
        "desc": "毁灭之力",
        "name": "毁灭之击"
    },
    "ms_fu_wen_bao_fa": {
        "kind": "魔法",
        "power": 2.2,
        "desc": "符文之力爆发",
        "name": "符文爆发"
    },
    "ms_xian_zu_zhi_nu": {
        "kind": "物理",
        "power": 2.4,
        "desc": "先祖之怒",
        "name": "先祖之怒"
    },
    "ms_mi_yin_zhen_ji": {
        "kind": "物理",
        "power": 2.6,
        "desc": "秘银之力震击",
        "name": "秘银震击"
    },
    "ms_long_zhi_nu": {
        "kind": "物理",
        "power": 2.2,
        "desc": "亚龙之怒",
        "name": "龙之怒"
    },
    "ms_feng_bao_zhao_huan": {
        "kind": "增益",
        "effect": "atk_up_strong",
        "desc": "召唤风暴强化自身",
        "name": "风暴召唤"
    },
    "ms_bing_qiang": {
        "kind": "增益",
        "effect": "def_up",
        "desc": "冰墙守护",
        "name": "冰墙"
    },
    "ms_tun_shi": {
        "kind": "物理",
        "power": 1.6,
        "desc": "吞噬敌人回复生命",
        "name": "吞噬"
    },
    "ms_fu_shen": {
        "kind": "魔法",
        "power": 1.4,
        "desc": "怨灵附身",
        "name": "附身"
    },
    "ms_bao_feng_zhi_nu": {
        "kind": "魔法",
        "power": 2.2,
        "desc": "风暴之怒席卷",
        "name": "暴风之怒"
    },
    "ms_sheng_guang_zhan": {
        "kind": "物理",
        "power": 2.0,
        "desc": "圣光之力斩击",
        "name": "圣光斩"
    },
    "ms_tian_fa": {
        "kind": "魔法",
        "power": 2.5,
        "desc": "神圣天罚降临",
        "name": "天罚"
    },
    "ms_shen_wei": {
        "kind": "增益",
        "effect": "atk_up_strong",
        "desc": "神威加身，攻击大幅提升",
        "name": "神威"
    },
    "ms_an_ying_qin_shi": {
        "kind": "魔法",
        "power": 2.2,
        "desc": "暗影之力侵蚀敌人",
        "name": "暗影侵蚀"
    },
    "ms_xu_kong_beng_ta": {
        "kind": "魔法",
        "power": 2.4,
        "desc": "虚空崩塌，撕裂空间",
        "name": "虚空崩塌"
    },
    "ms_an_ying_she_xian": {
        "kind": "魔法",
        "power": 2.6,
        "desc": "暗影射线贯穿一切",
        "name": "暗影射线"
    },
    "ms_an_ying_ling_yu": {
        "kind": "魔法",
        "power": 2.8,
        "desc": "混沌领域笼罩战场",
        "name": "暗影领域"
    },
    "ms_wang_quan_zhi_li": {
        "kind": "魔法",
        "power": 3.2,
        "desc": "王权之力，毁灭与新生",
        "name": "王权之力"
    },
    "ms_tun_shi_xu_kong": {
        "kind": "物理",
        "power": 2.4,
        "desc": "吞噬虚空，回复自身",
        "name": "吞噬虚空"
    },
    "ms_xuan_yun_zhong_ji": {
        "kind": "物理",
        "power": 1.2,
        "mech": "stun",
        "mech_val": 1,
        "desc": "沉重的一击，可能将你打晕（v63 控制）",
        "name": "眩晕重击"
    },
    "ms_chen_mo_jian_xiao": {
        "kind": "魔法",
        "power": 1.1,
        "mech": "silence",
        "mech_val": 1,
        "desc": "刺耳尖啸，沉默敌人 2 回合（v63 控制）",
        "name": "沉默尖啸"
    },
    "ms_han_bing_tu_xi": {
        "kind": "魔法",
        "power": 1.4,
        "mech": "freeze",
        "mech_val": 1,
        "desc": "极寒吐息，概率冻结敌人（v63 控制）",
        "name": "寒冰吐息"
    }
}
