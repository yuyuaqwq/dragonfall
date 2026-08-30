# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - equip_add_novice.py（v140 新手段 Lv.1-15 补档 24 件）

阶段品质梯度补档第五批·新手段（策划案 4.7）：Lv.1-15 补 24 件
- 白装 6：Lv.5-15 断档补位（粗制/粗布/见习/旧 前缀，纯基础无词条，无属性需求）
- 绿装 10：Lv.3-15（WOW 动物材料风『XX之爪/之牙/皮靴』，1 条固定词条，复用 affixes.py 既有词条 ID）
- 紫装 8：Lv.10-15（LOL 多兰系新手紫装，1 个机制特效 special，desc 注明触发时机+数值）

字段格式与 equip_roster.py EQUIP_ROSTER 完全一致（name/slot/weapon_type/quality/lv/series/req/source），
扩展字段：
- affix：绿装 1 条固定词条 ID（affixes.py AFFIXES 既有 key，仅作数据标注；正式生效走
  SERIES_FIXED_AFFIX 挂名册名，主 agent 收尾接线）
- special：紫装机制特效 {id/trigger/value}，desc 注明触发+数值（引擎接线由主 agent 统一做）
- desc：手写描述（紫装必含特效触发与数值说明）

渠道（source）：白/绿=商店直售；紫图纸 5 件=图纸（进图纸池），新手任务 3 件=支线（任务奖励发放）。
普通怪不掉装备（v93 铁律）——本表不触碰任何掉落池逻辑。
"""

EQUIP_ADD = {
    # ================= 白装 +6（Lv.5-15，朴实命名，纯基础无词条，无 req） =================
    "eq_cu_zhi_bi_shou": {
        "name": "粗制匕首", "slot": "weapon", "weapon_type": "dagger", "quality": "white", "lv": 5,
        "series": "粗制", "source": "商店",
        "desc": "粗制风格的短刃，刃口磨得尚可，新手刺客的第一把家伙。",
    },
    "eq_cu_zhi_tie_jian": {
        "name": "粗制铁剑", "slot": "weapon", "weapon_type": "sword", "quality": "white", "lv": 8,
        "series": "粗制", "source": "商店",
        "desc": "粗制风格的铁剑，剑脊笔直、护手朴素，比木棍结实得多。",
    },
    "eq_cu_bu_tou_jin": {
        "name": "粗布头巾", "slot": "helm", "quality": "white", "lv": 8,
        "series": "粗布", "source": "商店",
        "desc": "粗布风格的头巾，缠得紧实，挡风又吸汗。",
    },
    "eq_jian_xi_mu_zhang": {
        "name": "见习木杖", "slot": "weapon", "weapon_type": "staff", "quality": "white", "lv": 10,
        "series": "见习", "source": "商店",
        "desc": "见习风格的法杖，杖身刻着浅显的魔纹，元素之力初显。",
    },
    "eq_jiu_pi_jia_ke": {
        "name": "旧皮夹克", "slot": "armor", "quality": "white", "lv": 12,
        "series": "旧皮", "source": "商店",
        "desc": "旧皮风格的夹克，皮料揉得软熟，护得住胸背也挡得住风寒。",
    },
    "eq_cu_zhi_chang_gong": {
        "name": "粗制长弓", "slot": "weapon", "weapon_type": "bow", "quality": "white", "lv": 15,
        "series": "粗制", "source": "商店",
        "desc": "粗制风格的长弓，弓臂弧度优美，弦声清越，新手游侠的起步之选。",
    },

    # ================= 绿装 +10（Lv.3-15，WOW 动物材料风，1 条固定词条） =================
    "eq_ye_mao_zhi_zhua": {
        "name": "野猫之爪", "slot": "weapon", "weapon_type": "fist", "quality": "green", "lv": 3,
        "series": "野猫", "affix": "crit_up", "source": "商店",
        "desc": "野猫风格的拳套，爪刃薄而利，暴击率＋5%。",
    },
    "eq_lv_zhe_pi_xue": {
        "name": "旅者皮靴", "slot": "boots", "quality": "green", "lv": 3,
        "series": "旅者", "affix": "swift", "source": "商店",
        "desc": "旅者风格的皮靴，鞋底防滑走山路也稳当，速度＋5%。",
    },
    "eq_lie_quan_zhi_ya": {
        "name": "猎犬之牙", "slot": "weapon", "weapon_type": "dagger", "quality": "green", "lv": 5,
        "series": "猎犬", "affix": "combo", "source": "商店",
        "desc": "猎犬风格的短刃，獠牙般锋利，攻击 15% 追加一次 50% 伤害。",
    },
    "eq_lin_ying_zhi_gong": {
        "name": "林莺之弓", "slot": "weapon", "weapon_type": "bow", "quality": "green", "lv": 6,
        "series": "林莺", "affix": "precise", "source": "商店",
        "desc": "林莺风格的长弓，弦声轻快，命中＋10%（无视闪避），伤害＋10%。",
    },
    "eq_tie_lang_zhi_zhua": {
        "name": "铁狼之爪", "slot": "weapon", "weapon_type": "sword", "quality": "green", "lv": 8,
        "series": "铁狼", "affix": "armor_break", "source": "商店",
        "desc": "铁狼风格的利剑，刃口淬得发青，攻击 25% 降低目标防御 15%（2 回合）。",
    },
    "eq_ying_huo_fa_zhang": {
        "name": "萤火法杖", "slot": "weapon", "weapon_type": "staff", "quality": "green", "lv": 10,
        "series": "萤火", "affix": "meditate", "source": "商店",
        "desc": "萤火风格的法杖，杖顶凝着一点微光，每回合回复 1% 魔力。",
    },
    "eq_yan_yang_zhi_jiao": {
        "name": "岩羊之角", "slot": "weapon", "weapon_type": "mace", "quality": "green", "lv": 12,
        "series": "岩羊", "affix": "charge", "source": "商店",
        "desc": "岩羊风格的战锤，锤头沉重，攻击 10% 造成 150% 伤害。",
    },
    "eq_ye_lu_pi_mao": {
        "name": "野鹿皮帽", "slot": "helm", "quality": "green", "lv": 12,
        "series": "野鹿", "affix": "dodge", "source": "商店",
        "desc": "野鹿风格的皮帽，鹿皮鞣得轻软，闪避率＋5%。",
    },
    "eq_shui_ta_pi_jia": {
        "name": "水獭皮甲", "slot": "armor", "quality": "green", "lv": 14,
        "series": "水獭", "affix": "regen", "source": "商店",
        "desc": "水獭风格的皮甲，油亮的皮毛防水保暖，每回合回复 1% 生命。",
    },
    "eq_du_ya_gu_lian": {
        "name": "渡鸦骨链", "slot": "necklace", "quality": "green", "lv": 15,
        "series": "渡鸦", "affix": "crit_up", "source": "商店",
        "desc": "渡鸦风格的骨链，坠着渡鸦的喙骨，暴击率＋5%。",
    },

    # ================= 紫装 +8（Lv.10-15，LOL 多兰系新手紫装，1 个机制特效） =================
    "eq_xue_tu_zhi_xue_ren": {
        "name": "学徒之血刃", "slot": "weapon", "weapon_type": "sword", "quality": "purple", "lv": 10,
        "series": "血刃", "req": {"str": 12}, "weapon_effect": "novice_lifesteal",
        "source": "图纸",
        "desc": "血刃风格的长剑，剑身隐隐泛红——吸血特效：伤害的 5% 转化为生命回复（常驻）。",
    },
    "eq_lv_ren_zhi_dun": {
        "name": "旅人之盾", "slot": "weapon", "weapon_type": "shield", "quality": "purple", "lv": 10,
        "series": "旅人", "req": {"str": 12}, "weapon_effect": "novice_first_turn_guard",
        "source": "图纸",
        "desc": "旅人风格的盾牌，盾面厚实——守御特效：每场战斗首回合受击伤害－10%。",
    },
    "eq_xing_huo_fa_zhang": {
        "name": "星火法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 10,
        "series": "星火", "req": {"int": 12}, "weapon_effect": "novice_spark_followup",
        "source": "图纸",
        "desc": "星火风格的法杖，杖头星火明灭——星火特效：释放技能后，下次普攻伤害＋10%。",
    },
    "eq_lie_ying_zhi_ya": {
        "name": "猎影之牙", "slot": "weapon", "weapon_type": "dagger", "quality": "purple", "lv": 12,
        "series": "猎影", "req": {"agi": 14}, "weapon_effect": "novice_hunt_combo",
        "source": "图纸",
        "desc": "猎影风格的短刃，牙刃淬毒泛青——猎影特效：暴击后，本场战斗连击率＋8%。",
    },
    "eq_lv_ren_pi_jia": {
        "name": "旅人皮甲", "slot": "armor", "quality": "purple", "lv": 12,
        "series": "旅人", "req": {"vit": 10}, "weapon_effect": "novice_regen_heal",
        "source": "支线",
        "desc": "旅人风格的皮甲，缝着许多口袋——庇护特效：受到的治疗效果＋10%（常驻）。",
    },
    "eq_cui_feng_zhi_gong": {
        "name": "翠风之弓", "slot": "weapon", "weapon_type": "bow", "quality": "purple", "lv": 13,
        "series": "翠风", "req": {"agi": 15}, "weapon_effect": "novice_wind_spd",
        "source": "图纸",
        "desc": "翠风风格的长弓，弓臂缠着嫩绿藤蔓——翠风特效：攻击命中后，自身速度＋5%（持续 2 回合）。",
    },
    "eq_yuan_xing_dou_mao": {
        "name": "远行兜帽", "slot": "helm", "quality": "purple", "lv": 14,
        "series": "远行", "req": {"agi": 12}, "weapon_effect": "novice_first_turn_dodge",
        "source": "支线",
        "desc": "远行风格的兜帽，帽檐压得很低——远行特效：每场战斗首回合闪避率＋5%。",
    },
    "eq_chen_xing_diao_zhui": {
        "name": "晨星吊坠", "slot": "necklace", "quality": "purple", "lv": 15,
        "series": "晨星", "req": {"int": 14}, "weapon_effect": "novice_dawn_mana",
        "source": "支线",
        "desc": "晨星风格的吊坠，坠着一粒晨星般的宝石——晨星特效：每场战斗首次释放技能时回复 10 点魔力。",
    },
}
