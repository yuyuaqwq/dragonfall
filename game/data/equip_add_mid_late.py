# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - equip_add_mid_late.py（v140 波1：中期+后期段补档 64 件）

来源：资源获取渠道丰富化方案 4.7 节（阶段品质梯度补档）。
- 中期 Lv.31-55 补档 44 件：白6 / 绿10 / 蓝25 / 橙3
- 后期 Lv.56-80 补档 20 件：绿3 / 蓝11 / 橙6

字段格式与 equip_roster.py EQUIP_ROSTER 一致：
name / slot / weapon_type / quality / lv / series / req / legendary / source。
补充字段（供后续波次接线消费）：
- affixes：固定词条 ID 列表（绿 1 词条 / 蓝 2 词条，ID 见 affixes.py AFFIXES）
- desc：机制特效 / 传说特效的玩家可见描述（注明触发时机与数值）
品质词条规则：白无词条；绿 1 词条；蓝「2 词条」或「机制特效(desc)」二选一；
橙 legendary（desc 注明触发+数值）。
渠道分布：商店（白绿直售，不卡属性需求）/ 锻造（圣光·铁壁蓝）/ 图纸（月语·霜狼·海神·星辉蓝）/
boss·legend（橙）。
"""

EQUIP_ADD = {
    # ================= 中期 Lv.31-55 补档（44 件） =================
    # ---------- 白装 6（无词条，商店直售） ----------
    "eq_sheng_guang_zhi_shi_chang_jian": {"name": "圣光制式长剑", "slot": "weapon", "weapon_type": "sword", "quality": "white", "lv": 32, "series": "圣光", "source": "商店"},
    "eq_sheng_guang_zhi_shi_tou_kui":    {"name": "圣光制式头盔", "slot": "helm", "quality": "white", "lv": 32, "series": "圣光", "source": "商店"},
    "eq_sheng_guang_zhi_shi_xiong_jia":  {"name": "圣光制式胸甲", "slot": "armor", "quality": "white", "lv": 34, "series": "圣光", "source": "商店"},
    "eq_sheng_guang_zhi_shi_hu_tui":     {"name": "圣光制式护腿", "slot": "legs", "quality": "white", "lv": 34, "series": "圣光", "source": "商店"},
    "eq_sheng_guang_zhi_shi_zhan_xue":   {"name": "圣光制式战靴", "slot": "boots", "quality": "white", "lv": 32, "series": "圣光", "source": "商店"},
    "eq_yue_yu_shao_bing_pi_jia":        {"name": "月语哨兵皮甲", "slot": "armor", "quality": "white", "lv": 46, "series": "月语", "source": "商店"},
    # ---------- 绿装 10（1 词条，商店直售） ----------
    "eq_sheng_guang_li_zan_hui_zhang":   {"name": "圣光礼赞徽章", "slot": "necklace", "quality": "green", "lv": 36, "series": "圣光", "affixes": ["purify"], "source": "商店"},
    "eq_sheng_guang_zhi_shi_zhan_chui":  {"name": "圣光制式战锤", "slot": "weapon", "weapon_type": "mace", "quality": "green", "lv": 34, "series": "圣光", "affixes": ["charge"], "source": "商店"},
    "eq_sheng_guang_zhi_shi_chang_gong": {"name": "圣光制式长弓", "slot": "weapon", "weapon_type": "bow", "quality": "green", "lv": 36, "series": "圣光", "affixes": ["precise"], "source": "商店"},
    "eq_sheng_guang_zhi_shi_fa_zhang":   {"name": "圣光制式法杖", "slot": "weapon", "weapon_type": "staff", "quality": "green", "lv": 36, "series": "圣光", "affixes": ["meditate"], "source": "商店"},
    "eq_sheng_guang_qi_dao_zhe_zhi_xue": {"name": "圣光祈祷者之靴", "slot": "boots", "quality": "green", "lv": 38, "series": "圣光", "affixes": ["tenacity"], "source": "商店"},
    "eq_yue_yu_ye_ge_bi_shou":           {"name": "月语夜歌匕首", "slot": "weapon", "weapon_type": "dagger", "quality": "green", "lv": 48, "series": "月语", "affixes": ["combo"], "source": "商店"},
    "eq_yue_yu_xun_lin_duan_gong":       {"name": "月语巡林短弓", "slot": "weapon", "weapon_type": "bow", "quality": "green", "lv": 46, "series": "月语", "affixes": ["precise"], "source": "商店"},
    "eq_yue_yu_shao_bing_zhi_jie":       {"name": "月语哨兵之戒", "slot": "ring", "quality": "green", "lv": 46, "series": "月语", "affixes": ["crit_up"], "source": "商店"},
    "eq_yue_yu_ye_feng_hu_tui":          {"name": "月语夜风护腿", "slot": "legs", "quality": "green", "lv": 48, "series": "月语", "affixes": ["swift"], "source": "商店"},
    "eq_yue_yu_shao_bing_xiang_lian":    {"name": "月语哨兵项链", "slot": "necklace", "quality": "green", "lv": 50, "series": "月语", "affixes": ["meditate"], "source": "商店"},
    # ---------- 蓝装 25（2 词条 或 机制特效 desc） ----------
    # 圣光（10）
    "eq_sheng_guang_zhi_wo":             {"name": "圣光之握", "slot": "armor", "quality": "blue", "lv": 44, "series": "圣光", "req": {"str": 38}, "desc": "释放治疗技能时，治疗量提升10%（触发：技能释放）", "source": "锻造"},
    "eq_sheng_guang_shen_pan_zhi_ren":   {"name": "圣光审判之刃", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 46, "series": "圣光", "req": {"str": 42}, "affixes": ["armor_break", "purify"], "source": "锻造"},
    "eq_sheng_guang_bi_hu_zhi_dun":      {"name": "圣光庇护之盾", "slot": "weapon", "weapon_type": "shield", "quality": "blue", "lv": 42, "series": "圣光", "req": {"str": 36}, "desc": "格挡成功时，受到的伤害额外降低15%（触发：格挡）", "source": "锻造"},
    "eq_sheng_guang_zhu_fu_zhi_huan":    {"name": "圣光祝福指环", "slot": "ring", "quality": "blue", "lv": 40, "series": "圣光", "req": {"int": 34}, "affixes": ["purify", "crit_up"], "source": "锻造"},
    "eq_sheng_guang_qi_dao_fa_zhang":    {"name": "圣光祈祷法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 48, "series": "圣光", "req": {"int": 44}, "affixes": ["meditate", "purify"], "source": "锻造"},
    "eq_sheng_guang_zhui_lie_chang_gong": {"name": "圣光追猎长弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 46, "series": "圣光", "req": {"agi": 42}, "affixes": ["precise", "hunt"], "source": "锻造"},
    "eq_sheng_guang_xun_dao_zhe_xiong_jia": {"name": "圣光殉道者胸甲", "slot": "armor", "quality": "blue", "lv": 50, "series": "圣光", "req": {"str": 45}, "affixes": ["dmg_reduce", "shield"], "source": "锻造"},
    "eq_sheng_guang_shao_bing_tou_kui":  {"name": "圣光哨兵头盔", "slot": "helm", "quality": "blue", "lv": 44, "series": "圣光", "req": {"str": 38}, "affixes": ["dmg_reduce", "tenacity"], "source": "锻造"},
    "eq_sheng_guang_yuan_zheng_hu_tui":  {"name": "圣光远征护腿", "slot": "legs", "quality": "blue", "lv": 46, "series": "圣光", "req": {"str": 40}, "affixes": ["dmg_reduce", "tenacity"], "source": "锻造"},
    "eq_sheng_guang_xun_li_zhan_xue":    {"name": "圣光巡礼战靴", "slot": "boots", "quality": "blue", "lv": 42, "series": "圣光", "req": {"str": 36}, "affixes": ["tenacity", "swift"], "source": "锻造"},
    # 月语（9）
    "eq_yue_yu_ci_ke_bi_shou":           {"name": "月语刺客匕首", "slot": "weapon", "weapon_type": "dagger", "quality": "blue", "lv": 52, "series": "月语", "req": {"agi": 50}, "affixes": ["crit_up", "combo"], "source": "图纸"},
    "eq_yue_yu_yin_yue_chang_gong":      {"name": "月语银月长弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 54, "series": "月语", "req": {"agi": 52}, "affixes": ["precise", "hunt"], "source": "图纸"},
    "eq_yue_yu_mi_yi_fa_zhang":          {"name": "月语秘仪法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 54, "series": "月语", "req": {"int": 52}, "affixes": ["element_ice", "meditate"], "source": "图纸"},
    "eq_yue_yu_ying_xi_xiong_jia":       {"name": "月语影袭胸甲", "slot": "armor", "quality": "blue", "lv": 50, "series": "月语", "req": {"agi": 48}, "affixes": ["dodge", "swift"], "source": "图纸"},
    "eq_yue_yu_ye_xiao_tou_kui":         {"name": "月语夜枭头盔", "slot": "helm", "quality": "blue", "lv": 52, "series": "月语", "req": {"agi": 50}, "affixes": ["swift", "dodge"], "source": "图纸"},
    "eq_yue_yu_feng_xing_zhe_zhi_xue":   {"name": "月语风行者之靴", "slot": "boots", "quality": "blue", "lv": 48, "series": "月语", "req": {"agi": 46}, "affixes": ["swift", "dodge"], "source": "图纸"},
    "eq_yue_yu_yue_ying_hu_tui":         {"name": "月语月影护腿", "slot": "legs", "quality": "blue", "lv": 52, "series": "月语", "req": {"agi": 50}, "affixes": ["swift", "dodge"], "source": "图纸"},
    "eq_yue_yu_hui_yue_xiang_lian":      {"name": "月语辉月项链", "slot": "necklace", "quality": "blue", "lv": 54, "series": "月语", "req": {"int": 50}, "affixes": ["element_ice", "meditate"], "source": "图纸"},
    "eq_yue_yu_yue_hua_zhi_jie":         {"name": "月语月华之戒", "slot": "ring", "quality": "blue", "lv": 52, "series": "月语", "req": {"agi": 48}, "affixes": ["crit_up", "element_ice"], "source": "图纸"},
    # 铁壁（6）
    "eq_tie_bi_zhan_jia":                {"name": "铁壁战甲", "slot": "armor", "quality": "blue", "lv": 52, "series": "铁壁", "req": {"str": 48}, "desc": "受击时获得护盾，吸收5%最大生命的伤害（触发：受击，每场战斗限1次）", "source": "锻造"},
    "eq_tie_bi_jun_tuan_jian":           {"name": "铁壁军团剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 54, "series": "铁壁", "req": {"str": 52}, "affixes": ["armor_break", "charge"], "source": "锻造"},
    "eq_tie_bi_bi_lei_zhi_dun":          {"name": "铁壁壁垒之盾", "slot": "weapon", "weapon_type": "shield", "quality": "blue", "lv": 53, "series": "铁壁", "req": {"str": 50}, "desc": "受击时20%概率获得护盾，吸收8%最大生命的伤害（触发：受击，数值：20%/8%）", "source": "锻造"},
    "eq_tie_bi_wei_shu_tou_kui":         {"name": "铁壁卫戍头盔", "slot": "helm", "quality": "blue", "lv": 52, "series": "铁壁", "req": {"str": 48}, "affixes": ["dmg_reduce", "tenacity"], "source": "锻造"},
    "eq_tie_bi_zhong_zhuang_zhan_xue":   {"name": "铁壁重装战靴", "slot": "boots", "quality": "blue", "lv": 50, "series": "铁壁", "req": {"str": 46}, "affixes": ["tenacity", "block"], "source": "锻造"},
    "eq_tie_bi_jun_tuan_tui_jia":        {"name": "铁壁军团腿甲", "slot": "legs", "quality": "blue", "lv": 53, "series": "铁壁", "req": {"str": 50}, "affixes": ["dmg_reduce", "block"], "source": "锻造"},
    # ---------- 橙装 3（legendary 特效，desc 注明触发+数值） ----------
    "eq_chen_xi_sheng_jian":             {"name": "晨曦圣剑", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 50, "series": "圣光", "req": {"str": 50}, "legendary": "chen_xi_sheng_jian", "desc": "暴击命中后，下一次攻击伤害+25%（触发：暴击命中，数值：+25%）", "source": "boss"},
    "eq_yue_shen_zhi_jie":               {"name": "月神之戒", "slot": "ring", "quality": "orange", "lv": 52, "series": "月语", "req": {"agi": 50}, "legendary": "yue_shen_zhi_jie", "desc": "每刻开始回复2%最大生命（触发：刻开始，数值：2%）", "source": "legend"},
    "eq_shu_guang_bi_lei":               {"name": "曙光壁垒", "slot": "weapon", "weapon_type": "shield", "quality": "orange", "lv": 55, "series": "圣光", "req": {"str": 52}, "legendary": "shu_guang_bi_lei", "desc": "受击时20%概率获得护盾，吸收10%最大生命的伤害（触发：受击，数值：20%/10%）", "source": "boss"},

    # ================= 后期 Lv.56-80 补档（20 件） =================
    # ---------- 绿装 3（1 词条，商店直售） ----------
    "eq_shuang_lang_pi_xue":             {"name": "霜狼皮靴", "slot": "boots", "quality": "green", "lv": 56, "series": "霜狼", "affixes": ["tenacity"], "source": "商店"},
    "eq_hai_shen_bei_ke_lian":           {"name": "海神贝壳链", "slot": "necklace", "quality": "green", "lv": 58, "series": "海神", "affixes": ["swift"], "source": "商店"},
    "eq_hai_shen_shan_hu_jie":           {"name": "海神珊瑚戒", "slot": "ring", "quality": "green", "lv": 60, "series": "海神", "affixes": ["element_ice"], "source": "商店"},
    # ---------- 蓝装 11（2 词条 或 机制特效 desc） ----------
    "eq_shuang_lang_zhan_ren":           {"name": "霜狼战刃", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 58, "series": "霜狼", "req": {"str": 55}, "desc": "攻击附加冰属性伤害，相当于攻击力的10%（触发：攻击命中，数值：10%）", "source": "图纸"},
    "eq_shuang_lang_lie_gong":           {"name": "霜狼猎弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 62, "series": "霜狼", "req": {"agi": 60}, "affixes": ["pierce", "precise"], "source": "图纸"},
    "eq_shuang_lang_bing_jia":           {"name": "霜狼冰甲", "slot": "armor", "quality": "blue", "lv": 64, "series": "霜狼", "req": {"str": 62}, "affixes": ["dmg_reduce", "block"], "source": "图纸"},
    "eq_shuang_lang_xue_xue":            {"name": "霜狼雪靴", "slot": "boots", "quality": "blue", "lv": 56, "series": "霜狼", "req": {"str": 52}, "affixes": ["tenacity", "swift"], "source": "图纸"},
    "eq_shuang_lang_tui_jia":            {"name": "霜狼腿甲", "slot": "legs", "quality": "blue", "lv": 60, "series": "霜狼", "req": {"str": 58}, "affixes": ["tenacity", "dmg_reduce"], "source": "图纸"},
    "eq_hai_shen_zhi_dun":               {"name": "海神之盾", "slot": "weapon", "weapon_type": "shield", "quality": "blue", "lv": 60, "series": "海神", "req": {"str": 56}, "desc": "受击时10%概率完全格挡本次伤害（触发：受击，数值：10%）", "source": "图纸"},
    "eq_hai_shen_bo_wen_jia":            {"name": "海神波纹甲", "slot": "armor", "quality": "blue", "lv": 58, "series": "海神", "req": {"agi": 55}, "affixes": ["dodge", "swift"], "source": "图纸"},
    "eq_hai_shen_zhen_zhu_lian":         {"name": "海神珍珠链", "slot": "necklace", "quality": "blue", "lv": 60, "series": "海神", "req": {"int": 56}, "affixes": ["element_ice", "meditate"], "source": "图纸"},
    "eq_xing_hui_fa_zhang":              {"name": "星辉法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 60, "series": "星辉", "req": {"int": 58}, "desc": "释放技能后叠加1层星辉，每层暴击率+2%（上限5层）（触发：技能释放后，数值：2%/层）", "source": "图纸"},
    "eq_xing_hui_chang_pao":             {"name": "星辉长袍", "slot": "armor", "quality": "blue", "lv": 68, "series": "星辉", "req": {"int": 64}, "affixes": ["meditate", "dodge"], "source": "图纸"},
    "eq_xing_hui_fa_guan":               {"name": "星辉法冠", "slot": "helm", "quality": "blue", "lv": 64, "series": "星辉", "req": {"int": 60}, "affixes": ["meditate", "swift"], "source": "图纸"},
    # ---------- 橙装 6（legendary 特效，desc 注明触发+数值） ----------
    "eq_nu_tao_san_cha_ji":              {"name": "怒涛三叉戟", "slot": "weapon", "weapon_type": "mace", "quality": "orange", "lv": 64, "series": "海神", "req": {"str": 62, "agi": 62}, "legendary": "nu_tao_san_cha_ji", "desc": "攻击20%概率溅射：对除目标外所有敌人造成60%伤害（触发：攻击命中，数值：20%/60%）", "source": "boss"},
    "eq_zhen_hai_zhi_dun":               {"name": "镇海之盾", "slot": "weapon", "weapon_type": "shield", "quality": "orange", "lv": 68, "series": "海神", "req": {"str": 65}, "legendary": "zhen_hai_zhi_dun", "desc": "受击伤害-15%；受击20%概率反弹30%伤害（触发：受击，数值：-15%/20%/30%）", "source": "boss"},
    "eq_shuang_lang_zhi_wang_ya":        {"name": "霜狼之王牙", "slot": "weapon", "weapon_type": "dagger", "quality": "orange", "lv": 76, "series": "霜狼", "req": {"agi": 72}, "legendary": "shuang_lang_zhi_wang_ya", "desc": "攻击30%概率追加冰锥，造成40%额外冰属性伤害（触发：攻击命中，数值：30%/40%）", "source": "boss"},
    "eq_bing_hao_zhan_ren":              {"name": "冰嚎战刃", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 80, "series": "霜狼", "req": {"str": 78}, "legendary": "bing_hao_zhan_ren", "desc": "攻击命中25%概率冰冻目标1 刻（冰冻：无法行动）（触发：攻击命中，数值：25%/1 刻）", "source": "legend"},
    "eq_xing_hui_zhi_guan":              {"name": "星辉之冠", "slot": "helm", "quality": "orange", "lv": 70, "series": "星辉", "req": {"int": 68}, "legendary": "xing_hui_zhi_guan", "desc": "每刻开始回复3%最大法力；施法暴击时叠加星辉，每层伤害+2%（上限5层）（触发：刻开始/施法暴击，数值：3%/2%×5）", "source": "boss"},
    "eq_xing_he_fa_zhang":               {"name": "星河法杖", "slot": "weapon", "weapon_type": "staff", "quality": "orange", "lv": 72, "series": "星辉", "req": {"int": 70}, "legendary": "xing_he_fa_zhang", "desc": "释放技能后20%概率追加一次50%伤害的星辉冲击（触发：技能释放后，数值：20%/50%）", "source": "legend"},
}
