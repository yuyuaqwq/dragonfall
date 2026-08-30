# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - equip_add_fist_archer.py（v140 后期段职业武器补位）

后期段（Lv.56-80）拳师拳套 + 游侠蓝弓断档补位，共 5 件蓝装：
- 拳师三档全覆盖（Lv.56 破竹紫 → Lv.82 龙爪紫 之间的蓝装过渡）
- 游侠蓝弓衔接 Lv.56 紫 → Lv.70 橙
设计依据：workspace/资源获取渠道丰富化_分析结论与方案.md 4.7 节「后期段职业武器补位（第六批）」

字段格式与 game/data/equip_roster.py EQUIP_ROSTER 一致：
- name/slot/weapon_type/quality/lv/series/req/source（属性面板由 equipment.py WEAPON_FLAVOR 结算）
- special：武器特效标注（数据说明，机制由战斗层注册；蓝装档位刻意低于紫装同款防毕业替代）
- desc：手写描述（equip_roster.py 注入逻辑对已有 desc 手写优先保留）

本文件只含数据，不含逻辑；由主 agent 合并进名册后统一挂载特效机制。
"""

EQUIP_ADD = {
    # ================= 后期段·拳师拳套补位（Lv.60/65/70 蓝） =================
    # 岩拳·裂脊：海神神殿图纸（特效参考紫装 蓄力/连击 机制，30% 低于紫装 50% 档）
    "eq_yan_quan_lie_ji": {
        "name": "岩拳·裂脊",
        "slot": "weapon",
        "weapon_type": "fist",
        "quality": "blue",
        "lv": 60,
        "series": "岩拳",
        "req": {"str": 58},
        "source": "图纸",
        "special": "岩拳之怒：每 3 次攻击后，下一次攻击伤害 +30%",
        "desc": "海神神殿出土的岩铸拳套，拳面刻满裂脊般的岩纹。岩拳之怒：每 3 次攻击后，下一次攻击伤害 +30%。",
    },
    # 铁脊拳套：永冻冰原精英掉落（特效参考 反击 词条，15%/50% 低于紫装 20%/60%）
    "eq_tie_ji_quan_tao": {
        "name": "铁脊拳套",
        "slot": "weapon",
        "weapon_type": "fist",
        "quality": "blue",
        "lv": 65,
        "series": "铁脊",
        "req": {"str": 62},
        "source": "精英",
        "special": "铁脊反击：受击时 15% 概率反击，造成 50% 伤害",
        "desc": "以永冻冰原寒铁锻成的拳套，指脊如铁骨般坚硬。铁脊反击：受击时 15% 概率反击，造成 50% 伤害。",
    },
    # 碎岳拳：冰霜王座 Boss 图纸（特效参考 破甲 词条，25%/15%/2 回合）
    "eq_sui_yue_quan": {
        "name": "碎岳拳",
        "slot": "weapon",
        "weapon_type": "fist",
        "quality": "blue",
        "lv": 70,
        "series": "碎岳",
        "req": {"str": 68},
        "source": "图纸",
        "special": "碎岳之势：攻击时 25% 概率破甲，降低目标防御 15%（2 回合）",
        "desc": "传说能一拳碎开山岳的拳套，冰霜王座之下仍有地脉余温。碎岳之势：攻击时 25% 概率破甲，降低目标防御 15%（2 回合）。",
    },
    # ================= 后期段·游侠蓝弓补位（Lv.60/70 蓝） =================
    # 霜羽长弓：海神神殿图纸（特效参考 元素·冰 词条：5% 冰伤 + 减速）
    "eq_shuang_yu_chang_gong": {
        "name": "霜羽长弓",
        "slot": "weapon",
        "weapon_type": "bow",
        "quality": "blue",
        "lv": 60,
        "series": "霜羽",
        "req": {"agi": 58},
        "source": "图纸",
        "special": "霜羽之矢：攻击附加 5% 冰属性伤害 + 减速（敌速 -10%，持续 2 回合）",
        "desc": "弓臂缀满霜羽的长弓，弦声响起时飘落细雪。霜羽之矢：攻击附加 5% 冰属性伤害 + 减速（敌速 -10%，持续 2 回合）。",
    },
    # 疾风猎弓：风暴群岛精英掉落（特效：命中叠自身速度，2 层）
    "eq_ji_feng_lie_gong": {
        "name": "疾风猎弓",
        "slot": "weapon",
        "weapon_type": "bow",
        "quality": "blue",
        "lv": 70,
        "series": "疾风",
        "req": {"agi": 68},
        "source": "精英",
        "special": "疾风追猎：攻击命中时 20% 概率自身速度 +5%，可叠加 2 层",
        "desc": "风暴群岛狂风淬炼的猎弓，箭矢离弦时快过海风。疾风追猎：攻击命中时 20% 概率自身速度 +5%，可叠加 2 层。",
    },
}
