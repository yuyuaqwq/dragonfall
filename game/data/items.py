# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - items.py 材料部分(阶段一生成，2026－08－06)"""
MATERIALS = {
    # F2 P1：mesh_rooms_south.py:946 精英『百族战将·亡影』(Lv45) 掉落『亡影铠甲片』补定义
    # 原仅此一处引用 → 消费端 resolve 失败静默跳过；按同级材料惯例定义为兽材、可作锻造/炼金原料
    "mat_wang_ying_kai_jia_pian": {
        'price': 120, 'name': "亡影铠甲片", 'type': "兽材",
        'desc': "百族战将·亡影身上剥落的暗色铠甲残片，隐约残留着战魂的余温，铁匠铺与炼金坊都愿意出价收购",
    },
    # v94 图纸经济：重复图纸折算材料，出售 10 金/张（铁匠/炼金 0.9 折 → 9 金）
    "mat_tu_zhi_can_ye": {
        'price': 10,
        'name': "图纸残页",
    },
    # ================= v104 M20 P2：7 张支线奖励图纸（静态物品，s24/s25/s27/s30/s31/s33/s35）=================
    # 支线交付按名字 resolve("materials") 发放 → 必须挂在 MATERIALS；type=图纸 可被『学习』识别
    # price 与 make_blueprint 公式 int(lv×3+20) 一致（s27/s33 复用现有名册装备 lv）
    "mat_bp_lie_zong_liao_ya": {
        'price': 110, 'name': "裂鬃獠牙图纸", 'type': "图纸",
        'blueprint_for': "裂鬃獠牙", 'roster_id': "eq_lie_zong_liao_ya",
        'desc': "野猪王·裂鬃的锻造图纸，学习后可锻造【裂鬃獠牙】(Lv.30 匕首)",
    },
    "mat_bp_tie_ya_lang_pi": {
        'price': 65, 'name': "铁牙狼皮图纸", 'type': "图纸",
        'blueprint_for': "铁牙狼皮", 'roster_id': "eq_tie_ya_lang_pi_jia",
        'desc': "丘陵狼王·铁牙的锻造图纸，学习后可锻造【铁牙狼皮】(Lv.15 护甲)",
    },
    "mat_bp_lan_ge_zhi_lei": {
        'price': 224, 'name': "澜歌之泪图纸", 'type': "图纸",
        'blueprint_for': "澜歌之泪", 'roster_id': "eq_lang_ge_zhi_lei",
        'desc': "海神祭司·澜歌的锻造图纸，学习后可锻造【澜歌之泪】(Lv.68 项链)",
    },
    "mat_bp_lei_ming_long_lin": {
        'price': 194, 'name': "雷鸣龙鳞图纸", 'type': "图纸",
        'blueprint_for': "雷鸣龙鳞", 'roster_id': "eq_lei_ming_long_lin_dun",
        'desc': "风暴海龙·雷鸣的锻造图纸，学习后可锻造【雷鸣龙鳞】(Lv.58 盾牌)",
    },
    "mat_bp_jin_he_zhi_xin": {
        'price': 278, 'name': "烬核之心图纸", 'type': "图纸",
        'blueprint_for': "烬核之心", 'roster_id': "eq_jin_he_zhi_xin_zhang",
        'desc': "岩浆王·烬核的锻造图纸，学习后可锻造【烬核之心】(Lv.86 法杖)",
    },
    "mat_bp_ao_la_sheng_yin": {
        'price': 305, 'name': "奥拉圣印图纸", 'type': "图纸",
        'blueprint_for': "奥拉圣印", 'roster_id': "eq_ao_la_sheng_yin",
        'desc': "云中圣者·奥拉的锻造图纸，学习后可锻造【奥拉圣印】(Lv.95 项链)",
    },
    "mat_bp_mu_ying_long_hun": {
        'price': 284, 'name': "暮影龙魂图纸", 'type': "图纸",
        'blueprint_for': "暮影龙魂", 'roster_id': "eq_mu_ying_long_hun_jian",
        'desc': "龙陨战魂·暮影的锻造图纸，学习后可锻造【暮影龙魂】(Lv.88 大剑)",
    },
    "mat_qiu_ling_lang_pi": {
        'price': 5,
        'name': "丘陵狼皮",
    },
    "mat_wu_zei_wan_zu": {
        'price': 35,
        'name': "乌贼腕足", "food": True,
    },
    "mat_yun_nu_zhi_he": {
        'price': 200,
        'name': "云怒之核碎片",
    },
    "mat_yun_dian_kai_jia": {
        'price': 60,
        'name': "云殿铠甲",
    },
    "mat_yun_xiong_mao": {
        'price': 60,
        'name': "云熊毛",
    },
    "mat_yun_xu": {
        'price': 60,
        'name': "云絮",
    },
    "mat_wang_ying_zhan_hui": {
        'price': 15,
        'name': "亡影战徽",
    },
    "mat_guang_zhi_sheng_dian": {
        'price': 60,
        'name': "光之圣典",
    },
    "mat_ke_luo_de_luo_pan": {
        'price': 15,
        'name': "克罗的罗盘碎片",
    },
    "mat_tu_mao": {
        'price': 5,
        'name': "兔毛",
    },
    "mat_tu_pi": {
        'price': 5,
        'name': "兔皮",
    },
    "mat_shou_ren_zhan_hui": {
        'price': 15,
        'name': "兽人战徽",
    },
    "mat_shou_ren_fu_ren": {
        'price': 15,
        'name': "兽人斧刃",
    },
    "mat_bing_yuan_su_he_xin": {
        'price': 35,
        'name': "冰元素核心",
    },
    "mat_bing_xiong_pi": {
        'price': 35,
        'name': "冰熊皮",
    },
    "mat_bing_lang_ya": {
        'price': 35,
        'name': "冰狼牙",
    },
    "mat_bing_tong_zhi_zhu": {
        'price': 80,
        'name': "冰瞳之珠",
    },
    "mat_bing_she_lin": {
        'price': 35,
        'name': "冰蛇鳞",
    },
    "mat_dong_yu_lin": {
        'price': 35,
        'name': "冻鱼鳞",
    },
    "mat_jian_chi_hu_ya": {
        'price': 35,
        'name': "剑齿虎牙",
    },
    "mat_fu_guan_xun_zhang": {
        'price': 5,
        'name': "副官勋章",
    },
    "mat_jie_lve_zhe_hui_ji": {
        'price': 5,
        'name': "劫掠者徽记",
    },
    "mat_gu_dai_wen_xian": {
        'price': 15,
        'name': "古代文献",
    },
    "mat_gu_mu_zhi": {
        'price': 5,
        'name': "古木枝",
    },
    "mat_gu_shu_zhi_xin": {
        'price': 80,
        'name': "古树之心",
    },
    "mat_gu_wang_jian": {
        'price': 15,
        'name': "古王剑碎片",
    },
    "mat_gu_long_yi_jia": {
        'price': 60,
        'name': "古龙裔甲",
    },
    "mat_gu_long_lin": {
        'price': 60,
        'name': "古龙鳞",
    },
    "mat_shi_lai_mu_hui_zhang": {
        'price': 15,
        'name': "史莱姆徽章",
    },
    "mat_shi_lai_mu_nian_ye": {
        'price': 5,
        'name': "史莱姆黏液",
    },
    "mat_gu_lu_de_huang_guan": {
        'price': 80,
        'name': "咕噜皇冠",
    },
    "mat_ge_bu_lin_hui_ji": {
        'price': 5,
        'name': "哥布林徽记",
    },
    "mat_ge_bu_lin_er_zhui": {
        'price': 15,
        'name': "哥布林耳坠",
    },
    "mat_ge_bu_lin_er_duo": {
        'price': 5,
        'name': "哥布林耳朵",
        # v104 R3 M08 P3-1：手写 type/desc（规则把"哥布林"里的"布"误判为织物）
        'type': "兽材",
        'desc': "哥布林毛茸茸的尖耳朵，猎人们的战利品，据说晒干磨粉可以入药。",
    },
    "mat_ge_bu_lin_tie_pian": {
        'price': 5,
        'name': "哥布林铁片",
    },
    "mat_sheng_guang_sheng_hui": {
        'price': 15,
        'name': "圣光圣徽",
    },
    "mat_sheng_guang_jie_jing": {
        'price': 15,
        'name': "圣光结晶",
    },
    "mat_sheng_dian_tie_kuai": {
        'price': 5,
        'name': "圣殿铁块",
    },
    "mat_sheng_shui": {
        'price': 15,
        'name': "圣水",
    },
    "mat_di_di_e_mo_jiao": {
        'price': 35,
        'name': "地底恶魔角",
    },
    "mat_di_di_long_lin": {
        'price': 35,
        'name': "地底龙鳞",
    },
    "mat_di_yu_quan_ya": {
        'price': 35,
        'name': "地狱犬牙",
    },
    "mat_duo_luo_jing_ling_hu_fu": {
        'price': 15,
        'name': "堕落精灵护符",
    },
    "mat_ye_ge_zhi_yan": {
        'price': 80,
        'name': "夜歌之眼",
    },
    "mat_da_shi_lai_mu_he": {
        'price': 5,
        'name': "大史莱姆核",
    },
    "mat_tian_kong_zhan_ren": {
        'price': 60,
        'name': "天空战刃",
    },
    "mat_tian_ying_yu": {
        'price': 60,
        'name': "天鹰羽",
    },
    "mat_ao_la_sheng_yin": {
        'price': 60,
        'name': "奥拉圣印碎片",
        # v104 M20 P1：原自动 desc 承诺「别小看它」，但全配方零消费——改纯收藏语义
        # v105 M06 P3-2：材料改名「奥拉圣印碎片」——与 Lv.95 橙项链装备「奥拉圣印」区分（拾取/图鉴防混淆）
        'desc': "云中圣者·奥拉的圣印碎片，天空试炼的见证(纯收藏，无配方用途)",
    },
    "mat_nu_pu_suo_lian": {
        'price': 35,
        'name': "奴仆锁链",
    },
    "mat_bao_zi_nang": {
        'price': 35,
        'name': "孢子囊",
    },
    "mat_shou_wei_gu_mu": {
        'price': 35,
        'name': "守卫古木",
    },
    "mat_shou_wei_kai_jia_sui_pian": {
        'price': 200,
        'name': "守卫铠甲碎片",
    },
    "mat_shou_hu_zhe_sui_pian": {
        'price': 80,
        'name': "守护者碎片",
    },
    "mat_shen_pan_guan_zhi_lian": {
        'price': 15,
        'name': "审判官之链",
    },
    "mat_xiao_e_mo_jiao": {
        'price': 35,
        'name': "小恶魔角",
    },
    "mat_shan_yang_jiao": {
        'price': 5,
        'name': "山羊角",
    },
    "mat_lan_ge_zhi_yu": {
        'price': 15,
        'name': "岚歌之羽",
    },
    "mat_dao_zhu_ya": {
        'price': 15,
        'name': "岛猪牙",
    },
    "mat_yan_jiang_ru_chong_pi": {
        'price': 60,
        'name': "岩浆蠕虫皮",
    },
    "mat_yan_yang_mao": {
        'price': 5,
        'name': "岩羊毛",
    },
    "mat_yan_xi_lin": {
        'price': 5,
        'name': "岩蜥鳞",
    },
    "mat_yan_shu_ya": {
        'price': 5,
        'name': "岩鼠牙",
    },
    "mat_yan_long_lin": {
        'price': 60,
        'name': "岩龙鳞",
    },
    "mat_ju_shou_zhi_ya": {
        'price': 80,
        'name': "巨兽之牙",
    },
    "mat_ju_xing_ye_zhu_ya": {
        'price': 5,
        'name': "巨型野猪牙",
    },
    "mat_ju_mo_ya": {
        'price': 5,
        'name': "巨魔牙",
    },
    "mat_ju_mo_liao_ya": {
        'price': 5,
        'name': "巨魔獠牙",
    },
    "mat_ju_mo_xue": {
        'price': 5,
        'name': "巨魔血",
    },
    "mat_ju_lu_yu_gu": {
        'price': 15,
        'name': "巨鲈鱼骨",
    },
    "mat_ju_e_lin": {
        'price': 5,
        'name': "巨鳄鳞",
    },
    "mat_ju_ying_yu": {
        'price': 15,
        'name': "巨鹰羽",
    },
    "mat_ju_gui_jia": {
        'price': 35,
        'name': "巨龟甲",
    },
    "mat_wu_shi_fa_zhang_sui_pian": {
        'price': 80,
        'name': "巫师法杖碎片",
    },
    "mat_you_long_lin": {
        'price': 60,
        'name': "幼龙鳞",
    },
    "mat_you_ling_zhi_chen": {
        'price': 15,
        'name': "幽灵之尘",
    },
    "mat_you_ling_fan_bu": {
        'price': 35,
        'name': "幽灵帆布",
    },
    "mat_you_hun_chen": {
        'price': 15,
        'name': "幽魂尘",
    },
    "mat_wan_dao_sui_pian": {
        'price': 80,
        'name': "弯刀碎片",
    },
    "mat_qiang_hua_shi": {
        'price': 15,
        'name': "淬火石",
    },
    "mat_cai_hong_lu": {
        'price': 60,
        'name': "彩虹露",
    },
    "mat_cai_hong_lin": {
        'price': 60,
        'name': "彩虹鳞",
    },
    "mat_ying_bao_pi": {
        'price': 15,
        'name': "影豹皮",
    },
    "mat_yuan_ling_zhi_chen": {
        'price': 35,
        'name': "怨灵之尘",
    },
    "mat_guai_wu_tu_jian_sui_pian": {
        'price': 80,
        'name': "怪物图鉴碎片",
    },
    "mat_e_mo_zhan_ren": {
        'price': 60,
        'name': "恶魔战刃",
    },
    "mat_cheng_nian_long_lin": {
        'price': 60,
        'name': "成年龙鳞",
    },
    "mat_zhan_zheng_ji_qi_ling_jian": {
        'price': 15,
        'name': "战争机器零件",
    },
    "mat_zhan_hun_zhi_chen": {
        'price': 60,
        'name': "战魂之尘",
    },
    "mat_mo_luo_zhi_guan": {
        'price': 200,
        'name': "摩罗之冠碎片",
    },
    "mat_ao_lan_zhi_zhu": {
        'price': 80,
        'name': "敖澜之珠碎片",
    },
    "mat_jiao_guan_zhi_jian": {
        'price': 15,
        'name': "教官之剑",
    },
    "mat_xing_lang_pi": {
        'price': 60,
        'name': "星狼皮",
    },
    "mat_xing_hui_chen": {
        'price': 60,
        'name': "星辉尘",
    },
    "mat_chen_xi_zhi_guan": {
        'price': 80,
        'name': "晨曦之冠碎片",
    },
    "mat_an_ying_hui_ji": {
        'price': 15,
        'name': "暗影徽记",
    },
    "mat_an_ying_jing_ling_ren": {
        'price': 35,
        'name': "暗影精灵刃",
    },
    "mat_mu_ying_long_hun": {
        'price': 60,
        'name': "暮影龙魂碎片",
        # v104 M20 P1：原自动 desc 承诺「高级炼金的核心材料」，但全配方零消费——改纯收藏语义
        'desc': "龙陨战魂·暮影的龙魂余烬，龙陨谷守望的见证(纯收藏，无配方用途)",
    },
    "mat_yue_guang_jing_hua": {
        'price': 15,
        'name': "月光精华",
    },
    "mat_yue_ying_zhi_zhao": {
        'price': 15,
        'name': "月影之爪",
    },
    "mat_yue_xiong_pi": {
        'price': 15,
        'name': "月熊皮",
    },
    "mat_yue_lang_mao_pi": {
        'price': 15,
        'name': "月狼毛皮",
    },
    "mat_yue_lu_jiao": {
        'price': 15,
        'name': "月鹿角",
    },
    "mat_mu_zhuang_sui_pian": {
        'price': 80,
        'name': "木桩碎片",
    },
    "mat_shu_shi_fa_zhang": {
        'price': 60,
        'name': "术士法杖",
    },
    "mat_ji_xie_ling_jian": {
        'price': 35,
        'name': "机械零件",
    },
    "mat_jie_ke_de_jin_gou": {
        'price': 5,
        'name': "杰克的金钩碎片",
    },
    "mat_ji_guang_hu_wei": {
        'price': 35,
        'name': "极光狐尾",
    },
    "mat_lin_yu_zhi_ye": {
        'price': 15,
        'name': "林语之叶",
    },
    "mat_ran_xue_sheng_dian": {
        'price': 60,
        'name': "染血圣典",
    },
    "mat_ran_xue_ji_qi": {
        'price': 35,
        'name': "染血祭器",
    },
    "mat_ran_hei_sheng_dian": {
        'price': 15,
        'name': "染黑圣典",
    },
    "mat_ran_hei_sheng_ling": {
        'price': 15,
        'name': "染黑圣铃",
    },
    # v104 M20 P3：s7 修道院的玫瑰设计目标（06 章 S7「收集 3 朵染黑玫瑰」）补全——腐蚀修女掉落
    "mat_ran_hei_mei_gui": {
        'price': 20,
        'name': "染黑玫瑰",
        'desc': "被黑气浸染的玫瑰，花瓣边缘泛着不详的暗光。",
    },
    "mat_can_hai_he_xin": {
        'price': 60,
        'name': "残骸核心",
    },
    "mat_mu_zhu_pi": {
        'price': 5,
        'name': "母猪皮",
    },
    "mat_shui_shou_gu_pai": {
        'price': 35,
        'name': "水手骨牌",
    },
    "mat_shui_mu_ning_jiao": {
        'price': 15,
        'name': "水母凝胶",
    },
    "mat_shui_jing_ling_lei": {
        'price': 15,
        'name': "水精灵泪",
    },
    "mat_shui_jing_ling_lin": {
        'price': 15,
        'name': "水精灵鳞",
    },
    "mat_shui_zhi_wang_ya": {
        'price': 35,
        'name': "水蛭王牙",
    },
    "mat_shui_gui_zhi_lei": {
        'price': 80,
        'name': "水鬼之泪",
    },
    "mat_chen_mu": {
        'price': 15,
        'name': "沉木",
    },
    "mat_he_tun_du_su": {
        'price': 15,
        'name': "河豚毒素",
    },
    "mat_he_long_ling_zhu_lin": {
        'price': 15,
        'name': "河龙领主鳞",
    },
    "mat_he_long_lin": {
        'price': 15,
        'name': "河龙鳞",
    },
    "mat_hai_yao_zhi_yu": {
        'price': 15,
        'name': "海妖之羽",
    },
    "mat_hai_yao_lin": {
        'price': 15,
        'name': "海妖鳞",
    },
    "mat_hai_yao_lin_pian": {
        'price': 5,
        'name': "海妖鳞片",
    },
    "mat_hai_ju_ren_lin": {
        'price': 35,
        'name': "海巨人鳞",
    },
    "mat_hai_xing_pian": {
        'price': 15,
        'name': "海星片",
    },
    "mat_hai_yan_jie_jing": {
        'price': 5,
        'name': "海盐结晶",
    },
    "mat_hai_shen_ji_qi": {
        'price': 35,
        'name': "海神祭器",
    },
    "mat_hai_zao_chan_rao": {
        'price': 15,
        'name': "海藻缠绕",
    },
    "mat_hai_she_lin": {
        'price': 35,
        'name': "海蛇鳞",
    },
    "mat_hai_ou_yu_mao": {
        'price': 5,
        'name': "海鸥羽毛",
    },
    "mat_xiao_hao_pin": {
        'price': 15,
        'name': "消耗品",
    },
    "mat_tao_sheng_jing_jiao": {
        'price': 35,
        'name': "涛声鲸角",
    },
    "mat_shen_hai_qi_shi_jia": {
        'price': 35,
        'name': "深海骑士甲",
    },
    "mat_shen_yuan_shou_wei_jia": {
        'price': 60,
        'name': "深渊守卫甲",
    },
    "mat_shen_yuan_e_mo_jiao": {
        'price': 60,
        'name': "深渊恶魔角",
    },
    "mat_shen_yuan_fa_shi_zhang": {
        'price': 60,
        'name': "深渊法师杖",
    },
    "mat_shen_yuan_quan_ya": {
        'price': 60,
        'name': "深渊犬牙",
    },
    "mat_shen_yuan_qi_shi_kui_jia_sui_pian": {
        'price': 200,
        'name': "深渊骑士盔甲碎片",
    },
    "mat_yuan_ying_zhi_lin": {
        'price': 35,
        'name': "渊影之鳞",
    },
    "mat_hu_bing_he_xin": {
        'price': 35,
        'name': "湖冰核心",
    },
    "mat_hu_yao_lei": {
        'price': 15,
        'name': "湖妖泪",
    },
    "mat_hu_ling_lei": {
        'price': 35,
        'name': "湖灵泪",
    },
    "mat_hu_wang_zhu": {
        'price': 15,
        'name': "湖王珠",
    },
    "mat_xi_xi_lin": {
        'price': 5,
        'name': "溪蜥鳞",
    },
    "mat_xi_lu_pi": {
        'price': 5,
        'name': "溪鹿皮",
    },
    "mat_ni_gu_zhi_mao": {
        'price': 35,
        'name': "溺骨之锚",
    },
    "mat_xuan_wo_lei": {
        'price': 15,
        'name': "漩涡泪",
    },
    "mat_chao_xi_zhi_lei": {
        'price': 80,
        'name': "潮汐之泪",
    },
    "mat_chao_xi_sui_pian": {
        'price': 80,
        'name': "潮汐碎片",
    },
    # R3 P1-4：潮汐祭司支线素材（29 章 13.4：收集 3 片贝壳换潮汐护符）
    "mat_chao_xi_bei_ke": {
        'price': 30,
        'name': "潮汐贝壳",
    },
    "mat_chao_xi_hu_fu": {
        'price': 200,
        'name': "潮汐护符",
    },
    "mat_lan_ge_zhi_lei": {
        'price': 80,
        'name': "澜歌之泪残片",
        # v104 M20 P1：原自动 desc 承诺「炼金师视若珍宝」，但全配方零消费——改纯收藏语义
        'desc': "海神祭司·澜歌的泪滴结晶，海神试炼的见证(纯收藏，无配方用途)",
    },
    "mat_huo_xi_yi_lin": {
        'price': 35,
        'name': "火蜥蜴鳞",
    },
    "mat_huo_fu_yi": {
        'price': 60,
        'name': "火蝠翼",
    },
    "mat_hui_ying_lang_ya": {
        'price': 5,
        'name': "灰影狼牙",
    },
    "mat_hui_ai_ren_hui_ji": {
        'price': 35,
        'name': "灰矮人徽记",
    },
    "mat_jin_he": {
        'price': 60,
        'name': "烬核",
    },
    "mat_jin_he_zhi_xin": {
        'price': 200,
        'name': "烬核之心碎片",
        # v104 M20 P1：原自动 desc 承诺「魔导器运转的燃料」，但全配方零消费——改纯收藏语义
        'desc': "岩浆王·烬核的核心，地底火焰暴动的见证(纯收藏，无配方用途)",
    },
    "mat_jin_yi_long_lin": {
        'price': 60,
        'name': "烬翼龙鳞",
    },
    "mat_yan_yi_long_lin": {
        'price': 60,
        'name': "焰翼龙鳞",
    },
    "mat_rong_yan_he_xin": {
        'price': 35,
        'name': "熔岩核心",
    },
    "mat_rong_yan_jia_ke": {
        'price': 60,
        'name': "熔岩甲壳",
    },
    "mat_rong_yan_ru_chong_pi": {
        'price': 35,
        'name': "熔岩蠕虫皮",
    },
    "mat_rong_yan_ling_zhu_he": {
        'price': 35,
        'name': "熔岩领主核",
    },
    "mat_niu_jiao": {
        'price': 15,
        'name': "牛角",
    },
    "mat_kuang_zhan_shi_yao_dai": {
        'price': 5,
        'name': "狂战士腰带",
    },
    "mat_gou_ya": {
        'price': 5,
        'name': "狗牙",
    },
    "mat_lang_wang_ya": {
        'price': 5,
        'name': "狼王牙",
    },
    "mat_lang_pi": {
        'price': 5,
        'name': "狼皮",
    },
    "mat_lie_quan_xiang_quan": {
        'price': 15,
        'name': "猎犬项圈",
    },
    "mat_meng_ma_mao": {
        'price': 35,
        'name': "猛犸毛",
    },
    "mat_shan_hu_zhi": {
        'price': 35,
        'name': "珊瑚枝",
    },
    "mat_jia_ke_can_pian": {
        'price': 35,
        'name': "甲壳残片",
    },
    "mat_bai_zu_hui_zhang": {
        'price': 15,
        'name': "百族徽章",
    },
    "mat_dao_zei_mian_jin": {
        'price': 15,
        'name': "盗贼面巾",
    },
    "mat_mang_yu_lin": {
        'price': 35,
        'name': "盲鱼鳞",
    },
    "mat_zhen_jun_rou": {
        'price': 35,
        'name': "真菌肉",
    },
    "mat_shi_lu_zhi_chui": {
        'price': 35,
        'name': "石炉之锤",
    },
    "mat_shi_xi_lin": {
        'price': 5,
        'name': "石蜥鳞",
    },
    "mat_shi_long_lin": {
        'price': 60,
        'name': "石龙鳞",
    },
    "mat_kuang_shi_sui_pian": {
        'price': 80,
        'name': "矿石碎片",
    },
    "mat_kuang_mo_zhi_jiao": {
        'price': 80,
        'name': "矿魔之角",
    },
    "mat_sui_lie_feng_yin_shi": {
        'price': 60,
        'name': "碎裂封印石",
    },
    "mat_sui_gu": {
        'price': 15,
        'name': "碎骨",
    },
    "mat_tu_jiu_yu": {
        'price': 15,
        'name': "秃鹫羽",
    },
    "mat_zhang_yu_mo_nang": {
        'price': 35,
        'name': "章鱼墨囊",
    },
    "mat_fu_wen_shi": {
        'price': 15,
        'name': "符文石",
    },
    "mat_jing_ling_guo": {
        'price': 15,
        'name': "精灵果",
    },
    "mat_jing_ling_lu_jiao": {
        'price': 15,
        'name': "精灵鹿角",
    },
    "mat_jing_rui_pei_jian": {
        'price': 5,
        'name': "精锐佩剑",
    },
    "mat_hong_ji_shan_hu": {
        'price': 15,
        'name': "红棘珊瑚",
    },
    "mat_lv_lu_jiao": {
        'price': 15,
        'name': "绿鹿角",
    },
    "mat_cui_lu_jiao": {
        'price': 15,
        'name': "翠鹿角",
    },
    "mat_fei_cui_sen_lin": {
        'price': 15,
        'name': "翡翠森林",
    },
    "mat_fu_guan_jun": {
        'price': 35,
        'name': "腐冠菌",
    },
    "mat_fu_ya_shou_ya": {
        'price': 35,
        'name': "腐牙兽牙",
    },
    "mat_fu_ya_zhan_hui": {
        'price': 35,
        'name': "腐牙战徽",
    },
    "mat_fu_rou": {
        'price': 15,
        'name': "腐肉",
    },
    "mat_fu_shi_shou_zhao": {
        'price': 35,
        'name': "腐蚀兽爪",
    },
    "mat_chuan_zhang_luo_pan": {
        'price': 35,
        'name': "船长罗盘",
    },
    "mat_cao_yuan_lang_pi": {
        'price': 15,
        'name': "草原狼皮",
    },
    "mat_ying_guang_hu_wei": {
        'price': 15,
        'name': "荧光狐尾",
    },
    "mat_ying_guang_fen": {
        'price': 35,
        'name': "荧光粉",
    },
    "mat_sa_man_tu_teng": {
        'price': 5,
        'name': "萨满图腾",
    },
    "mat_lan_ge_zhi_guan": {
        'price': 80,
        'name': "蓝歌之冠残片",
    },
    "mat_xu_kong_quan_ya": {
        'price': 60,
        'name': "虚空犬牙",
    },
    "mat_she_pi": {
        'price': 5,
        'name': "蛇皮",
    },
    "mat_feng_zhen": {
        'price': 5,
        'name': "蜂针",
    },
    "mat_zhi_zhu_si": {
        'price': 35,
        'name': "蜘蛛丝",
    },
    "mat_bian_fu_yi": {
        'price': 15,
        'name': "蝙蝠翼",
    },
    "mat_fu_yi": {
        'price': 5,
        'name': "蝠翼",
    },
    "mat_xie_ke": {
        'price': 15,
        'name': "蟹壳",
    },
    "mat_lie_zong_liao_ya": {
        'price': 5,
        'name': "裂鬃獠牙碎片",
        # v104 M20 P1：原自动 desc 承诺「可打磨成武器配件」，但全配方零消费——改纯收藏语义
        'desc': "野猪王·裂鬃的獠牙，灰羽猎人的战利品纪念(纯收藏，无配方用途)",
    },
    "mat_chu_shou_pi": {
        'price': 15,
        'name': "触手皮",
    },
    "mat_gu_di_lu_shui": {
        'price': 15,
        'name': "谷地露水",
    },
    "mat_chi_yi_yu": {
        'price': 60,
        'name': "赤翼羽",
    },
    "mat_he_er_jia_de_ji_qi": {
        'price': 60,
        'name': "赫尔加的祭器碎片",
    },
    "mat_chen_guang_long_lin": {
        'price': 60,
        'name': "辰光龙鳞",
    },
    "mat_xun_meng_long_zhao": {
        'price': 35,
        'name': "迅猛龙爪",
    },
    "mat_yuan_gu_fu_wen_shi": {
        'price': 35,
        'name': "远古符文石",
    },
    "mat_ye_zhu_ya": {
        'price': 5,
        'name': "野猪牙",
    },
    "mat_jin_yan_hu_pi": {
        'price': 15,
        'name': "金焰虎皮",
    },
    "mat_tie_ya_lang_pi": {
        'price': 15,
        'name': "铁牙狼皮碎片",
        # v104 M20 P1：原自动 desc 承诺「打造武器的骨干」，但全配方零消费——改纯收藏语义
        'desc': "丘陵狼王·铁牙的皮毛，铁盾镇除害的见证(纯收藏，无配方用途)",
    },
    "mat_tie_jia_zhu_pi": {
        'price': 15,
        'name': "铁甲猪皮",
    },
    "mat_yin_hui_yue_shi": {
        'price': 35,
        'name': "银辉月石",
    },
    "mat_yin_zong_lang_pi": {
        'price': 15,
        'name': "银鬃狼皮",
    },
    "mat_xiu_jian_sui_pian": {
        'price': 200,
        'name': "锈剑碎片",
    },
    "mat_xiu_jia_sui_pian": {
        'price': 80,
        'name': "锈甲碎片",
    },
    "mat_fu_mo_fen_chen": {
        'price': 15,
        'name': "附魔粉尘",
    },
    "mat_yun_xing_he": {
        'price': 60,
        'name': "陨星核",
    },
    "mat_xue_tu_pi": {
        'price': 35,
        'name': "雪兔皮",
    },
    "mat_xue_ling_liao_ya": {
        'price': 35,
        'name': "雪岭獠牙",
    },
    "mat_xue_lang_pi": {
        'price': 35,
        'name': "雪狼皮",
    },
    "mat_lei_jing": {
        'price': 60,
        'name': "雷晶",
    },
    "mat_lei_xi_pi": {
        'price': 60,
        'name': "雷蜥皮",
    },
    "mat_lei_ting_zhi_xin": {
        'price': 200,
        'name': "雷霆之心",
    },
    "mat_lei_man_pi": {
        'price': 35,
        'name': "雷鳗皮",
    },
    "mat_lei_niao_yu": {
        'price': 60,
        'name': "雷鸟羽",
    },
    "mat_lei_ming_zhi_yi": {
        'price': 60,
        'name': "雷鸣之翼",
    },
    "mat_lei_ming_long_lin": {
        'price': 35,
        'name': "雷鸣龙鳞碎片",
        # v104 M20 P1：原自动 desc 承诺「水火不侵的天然护材」，但全配方零消费——改纯收藏语义
        'desc': "风暴海龙·雷鸣的鳞片，风暴之海异变的见证(纯收藏，无配方用途)",
    },
    "mat_wu_guan_jing": {
        'price': 60,
        'name': "雾冠晶",
    },
    "mat_shuang_ju_mo_wang_jiao": {
        'price': 35,
        'name': "霜巨魔王角",
    },
    "mat_shuang_ju_mo_xue": {
        'price': 35,
        'name': "霜巨魔血",
    },
    "mat_shuang_ya_long_lin": {
        'price': 35,
        'name': "霜牙龙鳞",
    },
    "mat_shuang_bai_liao_ya": {
        'price': 35,
        'name': "霜白獠牙",
    },
    "mat_shuang_yu_sheng_dian": {
        'price': 35,
        'name': "霜语圣典",
    },
    "mat_shuang_yu_ju_mo_xue": {
        'price': 35,
        'name': "霜语巨魔血",
    },
    "mat_xia_guang_long_lin": {
        'price': 60,
        'name': "霞光龙鳞",
    },
    "mat_ling_zhu_gu_mu_xin": {
        'price': 35,
        'name': "领主古木心",
    },
    "mat_ling_zhu_gu_jia": {
        'price': 15,
        'name': "领主骨甲",
    },
    "mat_feng_zhi_he_xin": {
        'price': 200,
        'name': "风之核心",
    },
    "mat_feng_zhi_yu": {
        'price': 60,
        'name': "风之羽",
    },
    "mat_feng_bao_zhi_ling_chen": {
        'price': 35,
        'name': "风暴之灵尘",
    },
    "mat_feng_bao_shou_pi": {
        'price': 60,
        'name': "风暴兽皮",
    },
    "mat_feng_bao_he_xin": {
        'price': 15,
        'name': "风暴核心",
    },
    "mat_feng_bao_ying_yu": {
        'price': 60,
        'name': "风暴鹰羽",
    },
    "mat_feng_yu_jie_jing": {
        'price': 15,
        'name': "风语结晶",
    },
    "mat_feng_yu_lu_jiao": {
        'price': 15,
        'name': "风语鹿角",
    },
    "mat_feng_long_yu": {
        'price': 60,
        'name': "风龙羽",
    },
    "mat_ma_er_ku_si_de_fa_guan": {
        'price': 15,
        'name': "马尔库斯的法冠残片",
    },
    "mat_qi_shi_hui_ji": {
        'price': 15,
        'name': "骑士徽记",
    },
    "mat_gu_chong_ke": {
        'price': 35,
        'name': "骨虫壳",
    },
    "mat_gu_mo_xiang_he": {
        'price': 60,
        'name': "骨魔像核",
    },
    "mat_gu_jiu_yu": {
        'price': 60,
        'name': "骨鹫羽",
    },
    "mat_gu_long_can_hai": {
        'price': 60,
        'name': "骨龙残骸",
    },
    "mat_hai_wang_long_gu": {
        'price': 60,
        'name': "骸王龙骨",
    },
    "mat_gao_ji_qiang_hua_shi": {
        'price': 80,
        'name': "高级强化石",
        'desc': "高级强化石，淬火石精炼而成的高纯度矿石，是高级锻造的基石。",
    },
    "mat_lie_xi_pi": {
        'price': 15,
        'name': "鬣蜥皮",
    },
    "mat_mo_xiang_he_xin": {
        'price': 15,
        'name': "魔像核心",
    },
    "mat_mo_xiang_can_he": {
        'price': 15,
        'name': "魔像残核",
    },
    "mat_mo_yan_zhi_he": {
        'price': 200,
        'name': "魔眼之核",
    },
    "mat_jiao_ren_lin": {
        'price': 15,
        'name': "鲛人鳞",
    },
    "mat_sha_yu_ya": {
        'price': 15,
        'name': "鲨鱼牙",
    },
    "mat_e_yu_pi": {
        'price': 5,
        'name': "鳄鱼皮",
    },
    "mat_ying_wu_yu": {
        'price': 15,
        'name': "鹦鹉羽",
    },
    "mat_mai_jiu": {
        'price': 15,
        'name': "麦酒",
        # v104 R3 M08 P3-1：手写 desc（规则按"麦"生成谷物描述，实为酒）
        'desc': "麦芽酿成的麦酒，酒香醇厚，烹饪去腥增香的绝佳调料。",
    },
    "mat_li_ming_zhi_guang": {
        'price': 80,
        'name': "黎明之光",
    },
    "mat_li_ming_zhi_guang_sui_pian": {
        'price': 200,
        'name': "黎明之光碎片",
    },
    "mat_hei_an_jing_ling_ren": {
        'price': 35,
        'name': "黑暗精灵刃",
    },
    "mat_hei_yao_sui_pian": {
        'price': 80,
        'name': "黑曜碎片",
    },
    "mat_hei_yuan_zhi_yan": {
        'price': 200,
        'name': "黑渊之眼残片",
    },
    "mat_hei_ya_pi_feng": {
        'price': 15,
        'name': "黑鸦披风",
    },
    "mat_long_zai_zhao": {
        'price': 60,
        'name': "龙崽爪",
    },
    "mat_long_xia_ke": {
        'price': 35,
        'name': "龙虾壳",
    },
    "mat_long_yi_can_hun": {
        'price': 60,
        'name': "龙裔残魂",
    },
    "mat_long_yu_chuan_cheng": {
        'price': 200,
        'name': "龙语传承",
    },
    "mat_long_hun_sui_pian": {
        'price': 200,
        'name': "龙魂碎片",
    },
    "mat_long_jing_zhi": {
        'price': 35,
        'name': "龙鲸脂",
    },
    "mat_long_lin_shou_pi": {
        'price': 60,
        'name': "龙鳞兽皮",
    },
    "mat_long_lin_shou_cang": {
        'price': 15,
        'name': "龙鳞收藏",
    },
    "mat_long_lin_sui_pian": {
        'price': 80,
        'name': "龙鳞碎片",
    },
    "mat_sheng_guang_bai_he": {
        "price": 30,
        "name": "圣光百合"
    },
    "mat_qi_shi_tuan_hui_ji": {
        "price": 35,
        "name": "骑士团徽记"
    },
    "mat_luo_lan_de_duan_jian": {
        "price": 50,
        "name": "罗兰的断剑"
    },
    # ---- 副业基础材料（2026-08-06 补齐，13 章 5.1 副业基础材料表）----
    "mat_cao_yao": {
        "price": 8,
        "name": "草药"
    },
    "mat_jiang_guo": {
        "price": 5,
        "name": "浆果", "food": True
    },
    # v124 支线配方材料（S49 金锅野猪肋排 / S51 银铃鲤饵）
    "mat_ye_mei": {
        "price": 5,
        "name": "野莓", "food": True
    },
    "mat_mian_tuan": {
        "price": 3,
        "name": "面团", "food": True
    },
    "mat_yue_guang_cao": {
        "price": 80,
        "name": "月光草"
    },
    "mat_zhao_ze_hua": {
        "price": 40,
        "name": "沼泽花"
    },
    "mat_bing_jing": {
        "price": 60,
        "name": "冰晶"
    },
    "mat_long_xue_cao": {
        "price": 400,
        "name": "龙血草"
    },
    "mat_tie_kuang_shi": {
        "price": 10,
        "name": "铁矿石"
    },
    "mat_shi_cai": {
        "price": 5,
        "name": "石材"
    },
    "mat_jing_tie": {
        "price": 30,
        "name": "精铁"
    },
    "mat_mi_yin": {
        "price": 80,
        "name": "秘银"
    },
    "mat_jing_jin": {
        "price": 200,
        "name": "精金"
    },
    "mat_yuan_zhi": {
        "price": 500,
        "name": "源质"
    },
    "mat_shou_rou": {
        "price": 12,
        "name": "兽肉", "food": True
    },
    "mat_mian_fen": {
        "price": 3,
        "name": "面粉", "food": True
    },
    "mat_kong_ping": {
        "price": 5,
        "name": "空瓶"
    },
    "mat_yu_mao": {
        "price": 8,
        "name": "羽毛"
    },
    "mat_shou_xue": {
        "price": 15,
        "name": "兽血"
    },
    "mat_shui_jing": {
        "price": 20,
        "name": "水晶"
    },
    "mat_mo_fa_fen_chen": {
        "price": 25,
        "name": "魔法粉尘"
    },
    "mat_yin_lin_yu": {
        "price": 6,
        "name": "银鳞鱼",
        "type": "鱼",
        "quality": "white"
    },
    "mat_jin_li": {
        "price": 12,
        "name": "金鲤",
        "quality": "green",
        # v104 R3 M08 P3-1：手写 type/desc（规则按"金"误判为矿石，实为鱼）
        "type": "鱼",  # v124 与 FISH_POOL 对齐（垂钓入包以 FISH_POOL type 为权威）
        "desc": "通体金红的鲤鱼，鳞片泛着贵气光泽，据说能带来好运。"
    },
    # v104 R3 M08 P2-6 回滚：帝王鲑/盲鱼是 fishing.py FISH_POOL 垂钓鱼（按名 resolve→mat_ 键），不可删
    "mat_di_wang_gui": {
        "price": 22,
        "name": "帝王鲑",
        # 垂钓材料品质以 FISH_POOL 品种档为权威（16 章 1.1），非价档——保持 green
        "type": "鱼",
        "quality": "green"
    },
    "mat_mang_yu": {
        "price": 9,
        "name": "盲鱼",
        "type": "鱼",
        "quality": "green"
    },
    "mat_ye_guang_jiao": {
        "price": 35,
        "name": "夜光鲛",
        "type": "材料"
    },
    "mat_jiao_ren_lei": {
        "price": 120,
        "name": "鲛人泪",
        "type": "材料",
        "quality": "blue"
    },
    "mat_shen_hai_shui_jing": {
        "price": 250,
        "name": "深海水晶",
        "type": "材料",
        "quality": "purple"
    },
    "mat_long_xian_xiang": {
        "price": 180,
        "name": "龙涎香",
        "type": "材料",
        "quality": "purple"
    },
    "mat_gu_dai_yu_gu": {
        "price": 200,
        "name": "古代鱼骨",
        "type": "材料",
        "quality": "orange"
    },
    # ---- 阶段四：5 个新副本 Boss 专属材料（04 章补登，13 章 5.7 登记）----
    "mat_yao_sai_can_pian": {
        "price": 60,
        "name": "要塞残片"
    },
    "mat_shi_lian_hui_ji": {
        "price": 90,
        "name": "试炼徽记"
    },
    "mat_yue_hui_sui_pian": {
        "price": 130,
        "name": "月辉碎片"
    },
    "mat_yong_dong_zhi_he": {
        "price": 180,
        "name": "永冻之核"
    },
    "mat_feng_bao_zhi_he": {
        "price": 230,
        "name": "风暴之核"
    },
    # ---- 渔获材料（16 章品质垂钓：垂钓唯一/主要来源，quality 对齐五档）----
    "mat_yue_guang_yu": {
        "price": 27,
        "name": "月光鱼",
        "type": "鱼",
        "quality": "blue"
    },
    # ---- v126.6 鱼种扩容（FISH_POOL↔MATERIALS 同步登记，价格交叉校验）----
    "mat_xi_zun": {
        "price": 7,
        "name": "溪鳟",
        "type": "鱼",
        "quality": "white"
    },
    "mat_qing_wen_lu": {
        "price": 15,
        "name": "青纹鲈",
        "type": "鱼",
        "quality": "green"
    },
    "mat_zhao_ya_shan": {
        "price": 32,
        "name": "沼牙鳝",
        "type": "鱼",
        "quality": "blue"
    },
    "mat_deng_yu_xue": {
        "price": 38,
        "name": "灯语鳕",
        "type": "鱼",
        "quality": "blue"
    },
    "mat_bing_lin_xun": {
        "price": 130,
        "name": "冰鳞鲟",
        "type": "鱼",
        "quality": "purple"
    },
    "mat_lei_wen_qing": {
        "price": 145,
        "name": "雷纹鲭",
        "type": "鱼",
        "quality": "purple"
    },
    "mat_shen_mi_lin_pian": {
        "price": 30,
        "name": "神秘鳞片",
        "type": "材料",
        "quality": "blue"
    },
    "mat_hu_zhen_zhu": {
        "price": 40,
        "name": "湖珍珠",
        "type": "材料",
        "quality": "blue"
    },
    "mat_hai_zao": {
        "price": 15,
        "name": "海藻",
        "type": "材料",
        "quality": "green"
    },
    "mat_zhen_zhu_bei": {
        "price": 35,
        "name": "珍珠贝",
        "type": "材料",
        "quality": "blue"
    },
    "mat_jing_xu_cao": {
        "price": 20,
        "name": "鲸须草",
        "type": "材料",
        "quality": "green"
    },
    "mat_lei_jing_sha": {
        "price": 80,
        "name": "雷晶砂",
        "type": "材料",
        "quality": "purple"
    },
    "mat_feng_bao_bei": {
        "price": 40,
        "name": "风暴贝",
        "type": "材料",
        "quality": "blue"
    },
    "mat_shen_yuan_zhen_zhu": {
        "price": 45,
        "name": "深渊珍珠",
        "type": "材料",
        "quality": "blue"
    },
    "mat_yun_mian": {
        "price": 22,
        "name": "云棉",
        "type": "材料",
        "quality": "green"
    },
    "mat_cai_hong_lu_zhu": {
        "price": 50,
        "name": "彩虹露珠",
        "type": "材料",
        "quality": "blue"
    },
    # v124 FISH_POOL↔MATERIALS 防漂移：垃圾/宝物/鱼王类渔获补登记（_settle_fishing 按名
    # resolve("materials") 入包，缺登记会以中文名回退成包 key；price/type 与 fishing.py 一致）
    "mat_shui_cao": {
        "price": 1,
        "name": "水草",
        "type": "垃圾",
        "quality": "white"
    },
    "mat_po_jiu_de_xue_zi": {
        "price": 1,
        "name": "破旧的靴子",
        "type": "垃圾",
        "quality": "white"
    },
    "mat_chen_jiu_de_bao_xiang": {
        "price": 0,
        "name": "陈旧的宝箱",
        "type": "宝物",
        "quality": "purple"
    },
    "mat_yu_wang_fei_cui_ju_long": {
        "price": 245,
        "name": "鱼王·翡翠巨龙",
        "type": "鱼王",
        "quality": "orange"
    },
    # ---- 烹饪材料（13 章 2.3 烹饪表）----
    # ---- v83 彩蛋收藏鱼（16 章 4.x，纯收藏：不入配方、回收 1 金币）----
    "mat_rainbow_kite": {
        "price": 1,
        "name": "虹彩龙鲤",
        "quality": "orange",
        "type": "收藏"
    },
    "mat_moon_jelly": {
        "price": 1,
        "name": "月华水母",
        "quality": "blue",
        "type": "收藏"
    },
    "mat_star_remnant": {
        "price": 1,
        "name": "星骸遗鳞",
        "quality": "purple",
        "type": "收藏"
    },
    # ---- v87 隐藏线材料（04 章十六节隐藏怪物掉落）----
    "mat_hu_po_jing_hua": {
        "price": 88,
        "name": "琥珀精华",
        "quality": "purple",
        "desc": "黄金史莱姆的精华凝结，据说能点石成金(炼金高级配方)。"
    },
    "mat_bai_lu_jiao": {
        "price": 150,
        "name": "白鹿角",
        "quality": "orange",
        "type": "传说",
        "desc": "白鹿王的角，蕴含月光的祝福(传说锻造材料)。"
    },
    "mat_ying_guang_lin": {
        "price": 66,
        "name": "荧光鳞",
        "quality": "purple",
        "desc": "荧光鱼群的鳞片，在暗处散发幽光(炼金稀有材料)。"
    },
    "mat_fu_wen_sui_pian": {
        "price": 100,
        "name": "符文碎片",
        "quality": "purple",
        "desc": "符文魔像的碎片，刻着失传的符文知识(图鉴补全/隐藏成就线索)。"
    },
    "mat_an_ying_jing_hua": {
        "price": 120,
        "name": "暗影精华",
        "quality": "purple",
        "desc": "暗影猎手留下的精华，蕴藏着夜色之力(附魔材料)。"
    },
    "mat_xing_yun_fu": {
        "price": 50,
        "name": "幸运符",
        "quality": "blue",
        "desc": "幸运灵狐赠与的护符，使用后当日运势提升(签到运势 + 1 档)。"
    },
    # ---- v87 隐藏线任务道具（06 章七.5：H3/H4，collect 目标走 resolve("materials")）----
    "mat_ember_ash": {
        "price": 100,
        "name": "烬火余烬",
        "type": "任务道具",
        "desc": "烬山深处烧红的余烬，仍散发着灼人的温度(隐藏任务 H3 收集品)"
    },
    "mat_old_page": {
        "price": 80,
        "name": "泛黄书页",
        "type": "任务道具",
        "desc": "一张泛黄的书页，边缘烧焦，字迹依稀可辨(隐藏任务 H4 收集品)"
    },
    "mat_ember_beacon": {
        "price": 500,
        "name": "烬火信标",
        "type": "任务道具",
        "desc": "老守墓人·灰须的馈赠，指引通往灰烬回廊(H7 隐藏区域准入)"
    },
    "mat_jian_sheng_can_ye": {
        "price": 120,
        "name": "咒刃残页",
        "type": "任务道具",
        "desc": "失落图书馆中散落的咒刃剑谱残页，记载着魔能剑术的奥义(魔剑士试炼收集品)"
    },
    "mat_star_hourglass": {
        "price": 800,
        "name": "星尘沙漏",
        "type": "任务道具",
        "desc": "图书管理员·贝拉托付的沙漏，沙粒泛着星辉(星尘套锻造核心)"
    },
    "mat_hui_jin_zhi_he": {
        "price": 1200,
        "name": "灰烬之核",
        "type": "任务道具",
        "desc": "烬火领主·伊格尼斯心脏中的灼热核心，灰烬守卫套锻造核心(H7 隐藏区域 Boss 掉落)"
    },
    # ---- v87.2 副本地图化 loot 材料（29 章 13.3：宝箱/补给/遗骸掉落）----
    "mat_jun_qi_sui_pian": {"price": 100, "name": "军旗碎片", "type": "材料", "desc": "鹿角要塞军旗的碎片，可作钥匙进入鹿角要塞(首通后免钥匙)"},
    "mat_gu_wang_sui_pian": {"price": 200, "name": "古王碎片", "type": "材料", "desc": "古王奥德里克陪葬品的残片，蕴含古老的力量"},
    "mat_sheng_tang_mi_juan": {"price": 180, "name": "圣堂密卷", "type": "材料", "desc": "枢机主教密室的封印密卷，记载着教会秘史"},
    "mat_da_sheng_ming_yao_shui": {"price": 150, "name": "大生命药水", "type": "材料", "desc": "浓稠的生命药水，可恢复大量生命(材料，可用于交易/任务)"},
    "mat_you_ling_chuan_piao": {"price": 120, "name": "幽灵船票", "type": "材料", "desc": "锈蚀的船票，幽灵水手用它摆渡亡魂(可作钥匙进入沉船湾)"},
    "mat_xing_hui_shi": {"price": 300, "name": "星辉石", "type": "材料", "desc": "星门开启时落下的星辉结晶，锻造极品材料"},
    "mat_yue_guang_shi": {"price": 220, "name": "月光石", "type": "材料", "desc": "月光凝成的宝石，精灵古物常用它镶嵌"},
    "mat_yue_hui_shi": {"price": 180, "name": "月辉石", "type": "材料", "desc": "月神圣殿的供品宝石，泛着清冷的月辉"},
    "mat_lang_mu_jiu": {"price": 80, "name": "朗姆酒", "food": True, "type": "材料", "desc": "沉船湾出产的烈酒，水手们的最爱"},
    "mat_hai_dao_cang_bao_tu": {"price": 60, "name": "海盗的藏宝图", "type": "材料", "desc": "从搁浅水手怀里找到的藏宝图，标着海蚀洞窟的秘密角落"},
    "mat_hai_shen_dao_wen": {"price": 260, "name": "海神祷文", "type": "材料", "desc": "海神神殿的祷文刻章(可作钥匙进入海神神殿)"},
    "mat_shen_yuan_qi_shi_hu_fu": {"price": 240, "name": "深渊骑士护符", "type": "材料", "desc": "深渊骑士残骸上的护符，抵挡过黑暗的侵蚀"},
    "mat_lei_he": {"price": 280, "name": "雷核", "type": "材料", "desc": "风暴中凝聚的雷电核心，蕴含狂暴的能量"},
    "mat_long_gong_zhu": {"price": 300, "name": "龙宫珠", "type": "材料", "desc": "龙宫的夜明珠，价值连城(可作钥匙进入深海龙宫)"},
    "mat_long_lin": {"price": 260, "name": "龙鳞", "type": "材料", "desc": "古龙的鳞片，坚硬如铁，锻造极品材料"},
    # v97.4 探索事件专属材料（蜂蜜/风干肉/霜花/夜枭羽毛/萤火虫/幽光菇）
    "mat_feng_mi": {"price": 30, "name": "蜂蜜", "food": True, "type": "材料", "desc": "野蜂巢采得的金黄蜜浆，甜得能挂住勺子"},
    "mat_feng_gan_rou": {"price": 25, "name": "风干肉", "food": True, "type": "材料", "desc": "猎户屋檐下风干的兽肉条，咸香耐存，路上最好的干粮"},
    "mat_shuang_hua": {"price": 40, "name": "霜花", "type": "材料", "desc": "寒夜里凝成的冰晶花朵，碰一下就碎，炼金师眼中的宝贝"},
    "mat_ye_xiao_yu_mao": {"price": 35, "name": "夜枭羽毛", "type": "材料", "desc": "夜枭在月下抖落的羽毛，暗纹流转，附魔师喜欢它"},
    "mat_ying_huo_chong": {"price": 15, "name": "萤火虫", "type": "材料", "desc": "装在小瓶里也会发光的萤火虫，夜晚的引路小灯"},
    "mat_you_guang_gu": {"price": 50, "name": "幽光菇", "type": "材料", "desc": "只在蘑菇圈里生长的稀有蘑菇，伞盖泛着幽幽蓝光，炼金珍品"},
    # v97.6 彩蛋事件专属材料（橡木种子/月之泪）
    "mat_xiang_mu_zhong_zi": {"price": 20, "name": "橡木种子", "type": "材料", "desc": "会说话的老橡树赠予的种子，据说种下能长出守护之树"},
    "mat_yue_zhi_lei": {"price": 120, "name": "月之泪", "type": "材料", "desc": "月光凝成的泪滴，只在月门城的月色下出现，精灵视若珍宝"},
    # v95.32 #403 炼金配方数据断裂修复：12 材料 + 2 强化石补全（原 alchemy.py/sets.py 引用但无定义无掉落源）
    "mat_yao_jing_zhi_chen": {"price": 45, "name": "妖精之尘", "desc": "妖精振翅时洒落的微光之尘，是炼金术最常用的媒介"},
    "mat_zhi_zhu_du_nang": {"price": 35, "name": "蜘蛛毒囊", "desc": "巨型蜘蛛腹部的毒囊，剧毒浓缩成一颗，炼金师小心取用"},
    "mat_rong_yan_shi": {"price": 55, "name": "熔岩石", "desc": "熔岩元素崩解后留下的滚烫石块，冷却后依然温热"},
    "mat_shen_yuan_jing_gang": {"price": 160, "name": "深渊精钢", "desc": "深渊之力淬炼的钢铁，暗沉无光却坚硬异常"},
    "mat_gui_hun_jing_hua": {"price": 85, "name": "鬼魂精华", "desc": "亡魂消散时凝成的幽蓝精华，触碰指尖发凉"},
    "mat_sheng_guang_yu_mao": {"price": 110, "name": "圣光羽毛", "desc": "圣光笼罩下飘落的羽毛，带着暖意与肃穆"},
    "mat_xue_zhi_jing_hua": {"price": 90, "name": "雪之精华", "desc": "千年雪原凝出的冰之精华，握在手里反而清凉舒服"},
    "mat_an_ying_sui_pian": {"price": 75, "name": "暗影碎片", "desc": "暗影教徒身上剥落的阴影碎片，轻若无物却沉甸甸"},
    "mat_huo_yan_he_xin": {"price": 150, "name": "火焰核心", "desc": "火蜥蜴心口跳动的火种，熔金化铁不在话下"},
    "mat_ling_hun_sui_pian": {"price": 180, "name": "灵魂碎片", "desc": "怨灵不灭的执念碎片，幽光里隐约有低语"},
    "mat_shou_ren_liao_ya": {"price": 100, "name": "兽人獠牙", "desc": "兽人劫掠者的獠牙，粗粝弯曲，带着凶性"},
    "mat_zuo_lang_quan_chi": {"price": 110, "name": "座狼犬齿", "desc": "狼王座下凶兽的犬齿，锋利得能划开铁甲"},
    "i_stone_upgrade": {"price": 400, "name": "强化石", "desc": "炼金提纯的魔力矿石，强化装备失败时自动护住不掉级（消耗品）"},
    "i_stone_refine": {"price": 1100, "name": "精炼强化石", "desc": "二次精炼的强化石，强化时消耗可提升成功率 +25%"},
    "i_stone_blessed": {"price": 1500, "name": "祝福符石",
                        "desc": "铁匠大师祝福过的符石，强化时自动消耗提升成功率 +15%（可叠加精炼强化石）"},
    # ---- v102.3 生活技能差异化：限定材料（采集时机限定 + 深矿专属） ----
    "mat_night_mushroom": {"price": 120, "name": "夜雾菇", "desc": "只在月光下撑开伞盖的菌菇，伞面凝着细碎的夜露"},
    "mat_aurora_flower": {"price": 300, "name": "极光花", "desc": "冬夜极光映照下才绽放的花，花瓣流光溢彩，转瞬即逝"},
    "mat_thunder_vine": {"price": 250, "name": "雷雨藤", "desc": "雷雨过后藤蔓上残留电弧，触碰会微微发麻"},
    "mat_moon_dew": {"price": 180, "name": "月露", "desc": "子夜草叶上凝结的露珠，盛在玉瓶里能存住月光"},
    "mat_deep_crystal": {"price": 350, "name": "深渊水晶", "desc": "矿洞最深处才有的幽蓝水晶，内里仿佛有星光流转"},
    "mat_star_iron": {"price": 600, "name": "星铁", "desc": "深隧里挖出的陨铁，锻打时溅出星星点点的火光"},
    # ---- v104 隐藏区域掉落材料补全（失落图书馆 lv55 / 灰烬回廊 lv85）----
    # 原 subareas.py 掉落引用这 8 个名字但 MATERIALS 无定义 → combat resolve 失败整场掉落被吞
    "mat_jiu_shu_can_ye": {"price": 60, "name": "旧书残页", "type": "杂物",
                           "desc": "失落图书馆里泛黄的书页残片，字迹早已模糊，学者愿意收购"},
    "mat_mo_shui_ping": {"price": 50, "name": "墨水瓶", "type": "杂物",
                         "desc": "馆中遗留的空墨水瓶，瓶底凝着一圈干涸的墨渍"},
    "mat_tui_se_mo_shui": {"price": 65, "name": "褪色墨水", "type": "精华",
                           "desc": "书页精灵身上洒落的古墨水，颜色已褪却仍带着淡淡墨香"},
    "mat_dang_an_shi_yao_shi": {"price": 80, "name": "档案室钥匙", "type": "任务道具",
                                "desc": "档案馆长随身保管的铜钥匙，或许能打开馆内某扇尘封的门"},
    "mat_yu_jin_jia_pian": {"price": 150, "name": "余烬甲片", "type": "兽材",
                            "desc": "烬火守卫身上剥落的烧灼甲片，余温未散，铁匠铺高价收购"},
    "mat_jin_lang_ya": {"price": 130, "name": "烬狼牙", "type": "兽材",
                        "desc": "烬狼口中镶着火星的獠牙，磨成粉末是炼金的好料"},
    "mat_shao_jiao_jian_ren": {"price": 160, "name": "烧焦剑刃", "type": "材料",
                               "desc": "灰烬骑士断落的残剑，刃口焦黑卷曲，回炉重锻或能再用"},
    "mat_yong_shi_yu_jin": {"price": 200, "name": "勇士余烬", "type": "精华",
                            "desc": "灰烬勇士消散后留下的余烬，灼热不灭，蕴含战意精华"},
    # ---- v104 M20 P1：支线缺失奖励实体（06 章承诺：S9 徽章 / S17 随机符文 / S20 传说锻造材料 / S22 笔记）----
    "mat_qi_shi_tuan_hui_zhang": {"price": 600, "name": "骑士团徽章", "type": "收藏",
                                  "desc": "圣光骑士团授予的银质徽章，见证你在晨曦城证明了自己的勇气(纯收藏，无配方用途)"},
    "mat_lie_yan_fu_wen": {"price": 300, "name": "烈焰符文", "type": "收藏",
                           "desc": "矮人符文大师吉姆利传授的符文之一，刻着古老的火焰铭文(随机符文奖励，纯收藏)"},
    "mat_han_shuang_fu_wen": {"price": 300, "name": "寒霜符文", "type": "收藏",
                              "desc": "矮人符文大师吉姆利传授的符文之一，刻着古老的冰霜铭文(随机符文奖励，纯收藏)"},
    "mat_lei_ji_fu_wen": {"price": 300, "name": "雷击符文", "type": "收藏",
                          "desc": "矮人符文大师吉姆利传授的符文之一，刻着古老的雷霆铭文(随机符文奖励，纯收藏)"},
    "mat_chuan_shuo_duan_zao_cai_liao": {"price": 1500, "name": "传说锻造材料", "type": "传说",
                                         "desc": "托尔丁·铁锤为传奇冒险者准备的传说级附魔胚料(纯收藏，无配方用途)"},
    "mat_li_shi_xue_jia_bi_ji": {"price": 800, "name": "历史学家笔记", "type": "收藏",
                                 "desc": "亡灵学者·骨语的亲笔笔记，记录着百族战争鲜为人知的细节(背景故事收藏)"},
    # ================= 21 份支线设计稿新增奖励物品（2026-08-16 批量登记） =================
    # 说明：任务道具/信物统一 type=任务道具（批量出售保护）；收藏/纪念品 type=收藏；
    #      图纸 type=图纸（blueprint_for 指向配方名，roster_id 空缺=烹饪/炼金配方，待对应配方表登记）
    # ---- 01 教会的阴影 ----
    "mat_sheng_nv_ting_feng_la": {"price": 50, "name": "圣女庭封蜡", "type": "任务道具",
                                  "desc": "水鬼公文箱上的蜡封，压着圣女庭蔷薇纹章——教会的印记，藏着一个不能说的名字(线索道具，s46 潮痕之下奖励)"},
    # TODO 来源待接线：教会密文 desc 声称 H2 线索收集物，hq2 未登记、全库零引用
    "mat_jiao_hui_mi_wen": {"price": 50, "name": "教会密文", "type": "任务道具",
                            "desc": "从教会耳目手中截获的密文残页，拼合起来指向一个被抹去的名字(线索收集物，H2 地精的情报网)"},
    # ---- 02 圣战真相 ----
    "mat_jun_tuan_zhang_ye": {"price": 30, "name": "军团账页", "type": "任务道具",
                              "desc": "灰斗篷买家的账页，背面拓着「晨星与锁链」旧徽——剑与锁链交叠，两个身影并肩而立(s46 交付物)"},
    # TODO 来源待接线：烧焦的剑鞘残片 desc 声称 s15 交付物，任务无发放/收集接线（零引用）
    "mat_shao_jiao_de_jian_qiao_can_pian": {"price": 30, "name": "烧焦的剑鞘残片", "type": "任务道具",
                                            "desc": "三百年前嵌进古树树身的剑鞘残片，焦痕之下依稀可辨一缕金纹(古树记忆的凭证，s15 交付物)"},
    "mat_ge_zhe_zhi_xia": {"price": 40, "name": "歌者之匣", "type": "任务道具",
                           "desc": "铁皮木匣，内装随军诗人·里昂·晨歌的遗稿与一截断琴弦(s47 交付物)"},
    # TODO 来源待接线：里昂·晨歌的手稿 desc 声称 s47 歌者之匣内，任务无发放接线（零引用）
    "mat_li_ang_chen_ge_de_shou_gao": {"price": 40, "name": "里昂·晨歌的手稿", "type": "任务道具",
                                       "desc": "羊皮手稿，写下「烬山的火里站着两个人，同握一柄剑」；可反复阅读(s47 歌者之匣内)"},
    # TODO 来源待接线：黎明之诗（残页）desc 声称 H1 三信物之一/s47 歌者之匣内，hq1 未登记、任务无发放接线（零引用）
    "mat_li_ming_zhi_shi_can_ye": {"price": 40, "name": "黎明之诗（残页）", "type": "任务道具",
                                   "desc": "残缺的歌谱残页，H1 三信物之一；交付莎拉后并入信物串(s47 歌者之匣内)"},
    # TODO 来源待接线：英雄王佩剑碎片 desc 声称 H1 三信物之一，hq1 未登记、全库零引用
    "mat_ying_xiong_wang_pei_jian_sui_pian": {"price": 40, "name": "英雄王佩剑碎片", "type": "任务道具",
                                              "desc": "旧王陵石棺夹层中取出的剑脊残片，錾着锁链纹(H1 三信物之一)"},
    # TODO 来源待接线：守夜者金羽 desc 声称 H1 三信物之一，hq1 未登记、全库零引用
    "mat_shou_ye_zhe_jin_yu": {"price": 40, "name": "守夜者金羽", "type": "任务道具",
                               "desc": "老朝圣者手杖上取下的一根金羽，烬山战场的遗物——链尾 S19 接取时的信物凭证(H1 三信物之一)"},
    # TODO 来源待接线：灰烬回响·封印残片 desc 声称 s19 链尾追加，任务无发放接线（零引用）
    "mat_hui_jin_hui_xiang_feng_yin_can_pian": {"price": 40, "name": "灰烬回响·封印残片", "type": "任务道具",
                                                "desc": "封印崩落时迸出的残片，刻着半句话；主线揭示全文后可与蚀夜对话解锁额外台词(s19 链尾追加)"},
    # ---- 03 深渊封印 ----
    # TODO 来源待接线：刻符石板碎片 desc 声称 S6 收集物，任务无接线（零引用）
    "mat_ke_fu_shi_ban_sui_pian": {"price": 20, "name": "刻符石板碎片", "type": "任务道具",
                                   "desc": "山丘矿洞中挖出的石板残片，刻着锚纹；集齐三片可拼合成完整的石板拓片(S6 收集物)"},
    "mat_shi_ban_tuo_pian": {"price": 60, "name": "石板拓片", "type": "任务道具",
                             "desc": "布鲁姆拼合还原的石板拓片——三百年前英雄王插上门闩的那把「锁」，也是开启古树地宫根门的钥匙(S6 奖励)"},
    # TODO 来源待接线：圣光蜡烛 desc 声称 S46 任务道具（quests.py 注释「已登记·剧情前置发放，未并入 reward_item」），实际无发放接线
    "mat_sheng_guang_la_zhu": {"price": 30, "name": "圣光蜡烛", "type": "任务道具",
                               "desc": "约拿所赠的圣光蜡烛，火焰朝地弯下时，便是封印异常的低语警告(S46 任务道具)"},
    "mat_bi_yan_zhi_tong_hui_ji": {"price": 30, "name": "闭眼之瞳徽记", "type": "任务道具",
                                   "desc": "黑底银纹、一只闭合的眼睛——不属于任何军队的徽记，揭示「聆潮者」教团的身份(S46 线索道具)"},
    # TODO 来源待接线：《渊语纪事》desc 声称 S47 find 物，任务无 find/reward 接线（零引用）
    "mat_yuan_yu_ji_shi": {"price": 40, "name": "《渊语纪事》", "type": "任务道具",
                           "desc": "古树地宫中以锚纹写成的古代典籍，记载着「世界的伤口」与锁的由来，末页被撕去一角(S47 find 物)"},
    # TODO 来源待接线：《渊语纪事》译文 desc 声称 S47 完成奖励，任务无发放接线（零引用）
    "mat_yuan_yu_ji_shi_yi_wen": {"price": 60, "name": "《渊语纪事》译文", "type": "任务道具",
                                  "desc": "橡心逐页翻译的译文，末页附一幅完整的图——锁、梯子与一滴泪(S47 完成奖励·线索道具)"},
    "mat_yuan_huo_jing_gang": {"price": 800, "name": "渊火精钢", "type": "传说",
                               "desc": "深渊裂隙熔火中淬出的精钢，犬牙般的暗纹在高温下浮现——传说级锻造/附魔材料"},
    # TODO 来源待接线：渊火精钢无任何消费点（s20 实际奖励「传说锻造材料」mat_chuan_shuo_duan_zao_cai_liao，未用本品；建议主 agent 决定替换或补接线）
    "mat_ling_ya_fu": {"price": 50, "name": "聆牙符", "type": "任务道具",
                       "desc": "托尔丁用熔化的深渊犬牙铸成的黑色铁牌，进入深渊祭坛时发烫——低语将至的预警(S20 完成奖励)"},
    # TODO 来源待接线：祭坛密文 desc 声称 S32 collect 目标，任务仅剧情文本提及、无 collect/reward 接线
    "mat_ji_tan_mi_wen": {"price": 50, "name": "祭坛密文", "type": "任务道具",
                          "desc": "刻于深渊祭坛骨柱上的密文，流动如潮；交予微光解读(S32 collect 目标)"},
    # TODO 来源待接线：深渊密文 desc 声称 S32 完成奖励，任务无发放接线（零引用）
    "mat_shen_yuan_mi_wen": {"price": 100, "name": "深渊密文", "type": "任务道具",
                             "desc": "微光所赠的拓本——揭露聆潮者与献祭仪式同构的关键证物，主线最终决战前可触发特殊剧情分支(S32 完成奖励)"},
    # ---- 04 北境生存 ----
    "mat_chang_ye_deng_huo": {"price": 30, "name": "长夜灯火", "type": "任务道具",
                              "desc": "永冬湖冰面下取回的灯火，点燃长夜篝火后化作一缕暖光(S46 任务道具)"},
    "mat_bai_hua_de_yu_jin": {"price": 80, "name": "白桦的余烬", "type": "传说",
                              "desc": "猎户白桦的骨灰，混着未散尽的深渊黑纹。人的灰，镇得住非人的火(S18 黑暗结局·唯一)"},
    # TODO 来源待接线：烬核之泪 desc 声称 S31 隐藏掉落/传说锻造附魔材料，无掉落与配方接线（零引用）
    "mat_jin_he_zhi_lei": {"price": 200, "name": "烬核之泪", "type": "传说",
                           "desc": "岩浆王烬核被人的骨灰镇住时，熔岩凝出的一滴泪——传说级锻造/附魔材料(S31 隐藏掉落)"},
    "mat_fu_ya_xue_nang": {"price": 60, "name": "腐牙血囊", "type": "任务道具",
                           "desc": "嚎骨体内取出的血囊，蕴含深渊气息——深渊系炼金材料，可出售(S18 掉落)"},
    # ---- 05 海洋之歌 ----
    # TODO 来源待接线：灯塔的灯芯 desc 声称 S42 奖励，任务无发放接线（零引用）
    "mat_deng_ta_de_deng_xin": {"price": 60, "name": "灯塔的灯芯", "type": "杂物",
                                "desc": "无名灯塔烧过的灯芯，光柄所赠——「海上的故事，总要有人接着讲下去。」可用于低级附魔或收藏(S42 奖励)"},
    "mat_ji_hai_deng_you": {"price": 30, "name": "祭海灯油", "type": "任务道具",
                            "desc": "海祭用灯油，渔港可购；点燃后海雾为归人让路(S46 任务道具)"},
    "mat_chao_xi_ri_zhi_can_ye": {"price": 60, "name": "潮汐日志残页", "type": "收藏",
                                  "desc": "白沫与埃德蒙合记的潮汐日志残页，标注归帆号航线；补全图鉴条目「归帆号」(S46 奖励)"},
    # TODO 来源待接线：未寄出的信 desc 声称 S43 任务道具，任务无发放接线（零引用）
    "mat_wei_ji_chu_de_xin": {"price": 40, "name": "未寄出的信", "type": "任务道具",
                              "desc": "埃德蒙的亡灵攥了十二年的信，火漆呈泪痕状；交付伊莲后保留为剧情纪念(S43 任务道具)"},
    # TODO 来源待接线：归帆金币 desc 声称 S29 奖励/可交付伊莲换取祝福，任务无发放接线（零引用）
    "mat_gui_fan_jin_bi": {"price": 60, "name": "归帆金币", "type": "杂物",
                           "desc": "净化后的金币，背面刻着遇难船员的名字；可交付伊莲换取祝福，或作锻造材料(S29 奖励)"},
    # TODO 来源待接线：名单残页 desc 声称 S29 剧情道具/图鉴，任务无发放接线（零引用）
    "mat_ming_dan_can_ye": {"price": 60, "name": "名单残页", "type": "收藏",
                            "desc": "金币箱底的遇难者名单，埃德蒙手迹；补全图鉴条目「归帆号的账」(S29 剧情道具)"},
    # TODO 来源待接线：龙鲸之角 desc 声称 S28 奖励，任务无发放接线（零引用）
    "mat_long_jing_zhi_jiao": {"price": 60, "name": "龙鲸之角", "type": "兽材",
                               "desc": "龙鲸王·涛声所赠，温润如玉——进入海神神殿的凭证，留存后亦可作稀有材料(S28 奖励)"},
    # ---- 06 龙裔传承 ----
    # TODO 来源待接线：龙语铜牌 desc 声称 S21 奖励，任务无发放接线（零引用）
    "mat_long_yu_tong_pai": {"price": 40, "name": "龙语铜牌", "type": "任务道具",
                             "desc": "奥姆之子所授的铜牌，刻有古龙语——龙脊山脉通行与拜见古尔之凭证(S21 奖励)"},
    # TODO 来源待接线：龙语挽歌·残卷 desc 声称 S45 奖励，任务无发放接线（零引用）
    "mat_long_yu_wan_ge_can_juan": {"price": 50, "name": "龙语挽歌·残卷", "type": "任务道具",
                                    "desc": "龙语者·古尔手书六十年的挽歌，唯有习得龙语者能吟唱(S45 奖励)"},
    # TODO 来源待接线：鳞歌之鳞 desc 声称 S22 奖励·链式信物，任务无发放接线（零引用）
    "mat_lin_ge_zhi_lin": {"price": 60, "name": "鳞歌之鳞", "type": "任务道具",
                           "desc": "龙裔先祖·瓦罗·鳞歌所赠的鳞片，温热不散；龙陨谷的魂火认此信物，可深入龙骸区(S22 奖励·链式信物)"},
    # TODO 来源待接线：赤鳞之印 desc 声称 S35 奖励·链式信物，任务无发放接线（零引用）
    "mat_chi_lin_zhi_yin": {"price": 60, "name": "赤鳞之印", "type": "任务道具",
                            "desc": "赤鳞龙王·暮影的魂印；云翼大长老凭此开启云中圣殿的传承之路(S35 奖励·链式信物)"},
    # ---- 07 美食与美酒 ----
    "mat_mei_shi_jie_yin_jian_xin": {"price": 30, "name": "美食节引荐信", "type": "任务道具",
                                     "desc": "洛根亲笔的引荐信，盖着金勺酒楼的徽记——美食节会场的入场凭证(S23 追加交付)"},
    "mat_shi_pu_tu_zhi_xiang_cao_kao_shou_rou": {"price": 90, "name": "食谱图纸·香草烤兽肉", "type": "图纸",
                                                 "blueprint_for": "香草烤兽肉",
                                                 "desc": "香草烤兽肉配方：兽肉×2+草药×1+浆果×1，攻+6%持续 2 场战斗(S47 奖励·图纸学习解锁)"},
    "mat_shi_pu_tu_zhi_jin_guo_ye_zhu_pai_pai": {"price": 150, "name": "食谱图纸·金锅野猪肋排", "type": "图纸",
                                                 "blueprint_for": "金锅野猪肋排",
                                                 "desc": "胖托尼获奖菜谱：野猪牙×3+野莓×2+草药×2，攻+10%持续 3 场战斗(S49 奖励·图纸学习解锁)"},
    "mat_cai_pu_tuo_ben": {"price": 30, "name": "菜谱拓本", "type": "任务道具",
                           "desc": "烹饪大赛获奖菜谱拓本——金锅决赛菜谱的誊本，交予白鹿与麦酒酒馆(S56 use 目标)"},
    # ---- 08 药园与花匠 ----
    # TODO 来源待接线：月光兰 desc 声称 S46 链内发现物·图鉴，任务无接线（零引用）
    "mat_yue_guang_lan": {"price": 60, "name": "月光兰", "type": "草药",
                          "desc": "白鹿之森月光药园园心唯一的月光兰，花心一线白——「月之誓」的见证(S46 链内发现物·图鉴)"},
    # TODO 来源待接线：月光兰花瓣 desc 声称 S47 配方材料·任务消耗，炼金配方未引用、任务无接线（零引用）
    "mat_yue_guang_lan_hua_ban": {"price": 30, "name": "月光兰花瓣", "type": "任务道具",
                                  "desc": "月光兰外层的老花瓣，小荨剪取——月光安神剂的引子(S47 配方材料·任务消耗)"},
    "mat_yue_guang_lan_mi": {"price": 120, "name": "月光兰蜜", "type": "草药",
                             "desc": "月光兰凝出的蜜露，月色流转其间——月光安神剂的主料，炼金配方独占材料(S49 奖励)"},
    "mat_yue_guang_zhu_dao_yin_zi": {"price": 30, "name": "月光祝祷·引子", "type": "任务道具",
                                     "desc": "奥德里克所赠的一瓶月露与口授祷词，S49 仪式中使用后消耗(S48 任务道具)"},
    "mat_pei_fang_yue_guang_an_shen_ji": {"price": 120, "name": "配方·月光安神剂", "type": "图纸",
                                          "blueprint_for": "月光安神剂",
                                          "desc": "月光安神剂配方：月光草×2+沼泽花×1+月光兰蜜×1，炼金 Lv.3 可制作(S49 奖励·图纸学习解锁)"},
    # TODO 来源待接线：小荨的草药包 desc 声称 S36 奖励沿用，任务无发放接线（零引用）
    "mat_xiao_xun_de_cao_yao_bao": {"price": 30, "name": "小荨的草药包", "type": "任务道具",
                                    "desc": "采药女小荨扎的草药包，内装草药×5——采集/炼金的补给(S36 奖励沿用)"},
    "mat_you_liang_cao_yao": {"price": 30, "name": "优良草药", "type": "草药",
                              "desc": "品相上乘的草药，可进高级炼金配方(S46 奖励·采集副业品质材料)"},
    # ---- 09 收藏家 ----
    # TODO 来源待接线：兽骨怀表 desc 声称 S46 任务道具，任务无发放接线（零引用）
    "mat_shou_gu_huai_biao": {"price": 40, "name": "兽骨怀表", "type": "任务道具",
                              "desc": "老栎古董店的兽骨怀表，表盖内侧刻着一行小字——收藏家的执念由此而起(S46 任务道具)"},
    "mat_li_ming_wang_guan_sui_pian": {"price": 50, "name": "黎明王冠碎片", "type": "任务道具",
                                       "desc": "黎明王冠的残片，鎏金剥落处露出旧铜——与馆藏赝品似曾相识(S48 任务道具)"},
    "mat_li_ming_wang_guan": {"price": 80, "name": "黎明王冠", "type": "任务道具",
                              "desc": "王棺室寻回的真品王冠，冠沿錾着百族战争前的古纹——博物馆的镇馆之宝(S49 任务道具·图鉴)"},
    # ---- 10 宠物情缘 ----
    "mat_yue_hui_xin_wu": {"price": 40, "name": "月辉信物", "type": "任务道具",
                           "desc": "泛月辉的银哨，长老·银歌所赠；交付后留作纪念品，可展示(L1-4 任务道具)"},
    # ---- 11 商路风云 ----
    "mat_shang_hui_huo_dan_yin_feng_xian": {"price": 30, "name": "商会货单·银风线", "type": "任务道具",
                                            "desc": "盖满沿途验货章的商路货单，记录冒险者商路的第一单(S46 交付凭证·可收藏)"},
    # TODO 来源待接线：灰旗碎片 desc 声称 S47 交付凭证（quests.py 注释「已登记·未并入 reward_item」），实际无发放接线
    "mat_hui_qi_sui_pian": {"price": 30, "name": "灰旗碎片", "type": "任务道具",
                            "desc": "从西岭盗贼身上搜出的褪色灰布旗角，灰旗会的记号(S47 交付凭证)"},
    "mat_hui_qi_hui_mi_xin": {"price": 30, "name": "灰旗会密信", "type": "任务道具",
                              "desc": "盖有金穗纹火漆印的密信，交后归档销毁(S48 交付凭证)"},
    # TODO 来源待接线：旧战场遗物·锈剑穗 desc 声称 S48 收藏品·图鉴/拍卖行挂售，任务无发放接线（零引用）
    "mat_jiu_zhan_chang_yi_wu_xiu_jian_sui": {"price": 100, "name": "旧战场遗物·锈剑穗", "type": "收藏",
                                              "desc": "百族战争时期的旧剑穗，铁锈里嵌着半枚铜星——可在铁港城拍卖行挂售(S48 收藏品·图鉴)"},
    "mat_san_ben_zhang_ce": {"price": 30, "name": "三本账册", "type": "任务道具",
                             "desc": "灰旗会走私账/雇凶账/囤货账，交后由商会归档，不再流通(S49 交付凭证)"},
    "mat_hui_qi_hui_zhang_ce": {"price": 30, "name": "灰旗会账册", "type": "任务道具",
                                "desc": "旧战场出土的账册，记录着灰旗会的秘密交易——走私/雇凶/囤货，灰旗会的三本账(S73 collect×3)"},
    # ---- 12 侦探与怪盗 ----
    "mat_mao_zhao_ka_pian": {"price": 30, "name": "猫爪卡片", "type": "任务道具",
                             "desc": "黑色硬卡，正面银线猫爪，背面「假货，差评。——影子猫」(S46 任务道具)"},
    "mat_xiang_mu_tong_lv_dian_fang_zhang": {"price": 30, "name": "橡木桶旅店房账", "type": "任务道具",
                                             "desc": "玛莎手写账页：「三份史莱姆果冻×2 晚、猫薄荷茶×1」，署名 L·K(S47 任务道具)"},
    "mat_cheng_zhu_fu_jiu_dang_kou_ya_wen_shu": {"price": 30, "name": "城主府旧档·扣押文书", "type": "任务道具",
                                                 "desc": "二十年前税关文书抄件，归还栏空白，背面有影子猫炭笔批注(S49 任务道具)"},
    "mat_ying_zi_mao_de_xin": {"price": 40, "name": "影子猫的信", "type": "任务道具",
                               "desc": "猫爪火漆，五页信纸，附文书抄件与家徽拓印——怪盗最后的心事(S50 任务道具)"},
    # ---- 13 老兵不死 ----
    "mat_jin_yu_can_pian": {"price": 30, "name": "金羽残片", "type": "任务道具",
                            "desc": "守夜者金羽的残角，微温；安抚旧壕英魂后化作光点消散(与 H1 信物「守夜者金羽」同源互文，S46 奖励)"},
    "mat_xiu_shi_de_yin_shao": {"price": 30, "name": "锈蚀的银哨", "type": "任务道具",
                                "desc": "半截断哨，哨身刻字：「吹响它的人，会替你记住回家的路。」交付后由铁面挂上吧台(S47 find 物)"},
    "mat_jin_luo_cun_jiu_dang_chao_ben": {"price": 40, "name": "烬落村旧档抄本", "type": "任务道具",
                                          "desc": "圣光大教堂圣战旧档的抄本，记录余烬元年北境烬落村遗孤安置一事(S48 奖励·可保留为收藏)"},
    "mat_luo_sha_lin_de_jiu_shou_pa": {"price": 100, "name": "罗莎琳的旧手帕", "type": "收藏",
                                       "desc": "白鹿城接生婆的旧手帕，绣着一支小小的烛火——「长夜节的烛，点了三百年。」(S49 纪念品·lore)"},
    # 守夜者徽章：真实装备已登记 equip_roster eq_shou_ye_zhe_hui_zhang（s84 eq: 奖励），原占位条目已删除
    # ---- 14 学徒之路 ----
    "mat_tie_shao_zi": {"price": 50, "name": "铁哨子", "type": "收藏",
                        "desc": "老铁赶工打的铁哨子，哨音又尖又亮——小灰说：「我认得这个声音。」(S48 收藏道具)"},
    "mat_mao_xian_zhe_shou_ce": {"price": 40, "name": "《冒险者手册》", "type": "任务道具",
                                 "desc": "牛皮封面旧书，扉页题字：「打铁先打人，人正铁才正。——老铁匠·古铁。」内夹压平的橡树叶与炭笔画(S49 find 物)"},
    "mat_xiao_hui_de_mu_diao": {"price": 50, "name": "小灰的木雕", "type": "收藏",
                                "desc": "一只刻得歪歪扭扭、却打磨得光光滑滑的橡木小鸟——「送人的东西要用心。」(S50 唯一性收藏)"},
    # ---- 17 北境东境散支线 ----
    # 松木护符：真实装备已登记 equip_roster eq_song_mu_hu_fu（s104 eq: 奖励），原占位条目已删除
    "mat_rong_huo_jing_tie": {"price": 60, "name": "熔火精铁", "type": "矿石",
                              "desc": "熔岩元素身上凝结的纯铁，出炉时仍带着熔炉谷的热气(S57 collect 目标·锻造材料)"},
    # ---- 18 隐藏支线 ----
    "mat_hui_chang_ge_de_bei_ke": {"price": 80, "name": "会唱歌的贝壳", "type": "收藏",
                                   "desc": "凑近能听见三百年前的水手歌谣——鸦羽货摊的旧物(H5 收藏道具)"},
    # TODO 来源待接线：亡者之灯 desc 声称 H5 探索道具·灯，任务/商店无接线（零引用）
    "mat_wang_zhe_zhi_deng": {"price": 200, "name": "亡者之灯", "type": "收藏",
                              "desc": "鸦羽货摊的旧提灯，装备后夜间探索事件概率+10%(H5 探索道具·灯，效果待实现)"},
    "mat_tu_zhi_ye_xing_pi_feng": {"price": 100, "name": "夜行披风图纸", "type": "图纸",
                                   "blueprint_for": "夜行披风",
                                   "desc": "Lv.30 蓝装披风锻造图纸，唯一来源为鸦羽货摊(H5 稀有锻造图纸·图纸学习解锁)"},
    # TODO 来源待接线：雨泪珍珠 desc 声称 H5 炼金材料/雨泪药剂主料，炼金配方未引用、任务无接线（零引用）
    "mat_yu_lei_zhen_zhu": {"price": 100, "name": "雨泪珍珠", "type": "宝石",
                            "desc": "雨夜垂钓才见得到的珍珠，裹着一层水汽——炼金「雨泪药剂」的主料(H5 炼金材料)"},
    # TODO 来源待接线：旧物·沉船怀表 desc 声称 H5 对话赠礼，hq5 任务无发放接线（零引用）
    "mat_jiu_wu_chen_chuan_huai_biao": {"price": 100, "name": "旧物·沉船怀表", "type": "收藏",
                                        "desc": "鸦羽的旧物，含三百年前沉船线索——后续版本的暗线信物(H5 对话赠礼)"},
    "mat_white_ash": {"price": 150, "name": "白石圣灰", "type": "精华",
                      "desc": "修道院墓园圣物匣中带出的圣灰，三百年不腐，泛着微光——隐藏配方主料/圣光系炼金材料(H6 唯一来源)"},
    "mat_pei_fang_bai_shi_sheng_hui_yao_ji": {"price": 120, "name": "隐藏配方·白石圣灰药剂", "type": "图纸",
                                              "blueprint_for": "白石圣灰药剂",
                                              "desc": "白石圣灰×2+草药×1+空瓶×1→圣灰药剂：战斗中驱散全队负面(炼金 Lv.4，H6 唯一来源·图纸学习解锁)"},
    "mat_chuan_shuo_tu_zhi_rong_lu_zhi_xin": {"price": 300, "name": "熔炉之心图纸", "type": "图纸",
                                              "blueprint_for": "熔炉之心",
                                              "desc": "Lv.85 传说武器图纸：熔岩核心×3+精金×5+源质×2+熔炉之心的祝福(H8 唯一来源·图纸学习解锁)"},
    "mat_qing_tong_yu_ling": {"price": 40, "name": "青铜雨铃", "type": "任务道具",
                              "desc": "雨夜三声铃响的青铜铃——鸦羽货摊的钥匙，任务完成后保留为收藏(H5 信物)"},
    "mat_lao_xiu_shi_shou_gao": {"price": 30, "name": "老修士手稿", "type": "任务道具",
                                 "desc": "白石墓园老修士的手稿，交灰杖可换取 lore 对话(H6 任务道具)"},
    "mat_sheng_wu_xia": {"price": 30, "name": "圣物匣", "type": "任务道具",
                         "desc": "第九块碑下的白石圣物匣，交灰杖后留在墓园(H6 任务道具)"},
    "mat_yue_guang_yin_ji": {"price": 40, "name": "月光印记", "type": "任务道具",
                             "desc": "月冠王庭信使身份的月光印记——任务后保留，声望商店折扣凭证(H7 信物)"},
    "mat_xian_zu_fu_wen_chui": {"price": 40, "name": "先祖符文锤", "type": "任务道具",
                                "desc": "铁砧要塞先祖传下的符文锤——任务后保留，要塞声望象征(H8 信物)"},
    # ---- 19 垂钓传说 ----
    "mat_yue_lin_ban_pian": {"price": 30, "name": "月鳞（半片）", "type": "任务道具",
                             "desc": "月光鱼腹中剖出的半片银鳞，切口平整如镜——归帆的引子(S48 交付物)"},
    # TODO 来源待接线：月鳞（完整）desc 声称 S51 收藏纪念（quests.py 注释「已登记·未并入 reward_item」），实际无发放接线
    "mat_yue_lin_wan_zheng": {"price": 100, "name": "月鳞（完整）", "type": "收藏",
                              "desc": "合拢如月的完整银鳞，不可交易、不可入配方——「守湖人认你。」(S51 收藏纪念·图鉴)"},
    "mat_pei_fang_yin_ling_li_er": {"price": 60, "name": "配方·银铃鲤饵", "type": "图纸",
                                    "blueprint_for": "银铃鲤饵",
                                    "desc": "银鳞鱼×1+面团×1+月光草×1→银铃鲤饵×3，烹饪 Lv.6(S51 奖励·图纸学习解锁)"},
    # ---- 20 旧友重逢 ----
    "item_late_letter": {"price": 30, "name": "迟到的信", "type": "任务道具",
                         "desc": "一封压在箱底二十年的信，桦皮纸，字迹被水渍洇开几处。火漆完好。收件人：白鹿城·茉莉(S46 奖励)"},
    "item_edmund_tag": {"price": 100, "name": "埃德蒙的佣兵铭牌", "type": "收藏",
                        "desc": "北境第三佣兵团的铜制铭牌，正面刻着名字与番号，背面刻着「白鹿城·茉莉」。他至死都带着她的名字(S48 纪念品)"},
    "item_dried_flower": {"price": 100, "name": "白鹿干花", "type": "收藏",
                          "desc": "茉莉亲手晒的白鹿干花，用蓝布条扎着——白鹿城人系剑的旧习惯。二十年前的约定开的花(S50 纪念品)"},
    "item_thank_letter": {"price": 100, "name": "信鸽的感谢信", "type": "收藏",
                          "desc": "信鸽写的感谢信，字迹工整得像刻碑：「是您替我补上了。往后路过邮局，老头子请您喝热茶。」(彩蛋奖励·可反复阅读)"},
    # ---- 21 花匠与四季 ----
    # TODO 来源待接线：花种·雏菊 desc 声称 S46 纪念品·家园系统预留，任务无发放接线（零引用）
    "mat_guang_zhong_ju_hua": {"price": 10, "name": "花种·雏菊", "type": "收藏",
                               "desc": "一小包雏菊花种，可售店或家园花圃种植(S46 纪念品·家园系统预留)"},
    # TODO 来源待接线：老花农的旧花剪 desc 声称 S47 纪念品·采集彩蛋，任务无发放接线（零引用）
    "mat_lao_hua_nong_de_jiu_hua_jian": {"price": 30, "name": "老花农的旧花剪", "type": "收藏",
                                         "desc": "苍耳用了一辈子的花剪，握柄磨得发亮——采集时低概率额外+1 草药(S47 纪念品·采集彩蛋)"},
    "mat_chun_feng_ling_zhong_zi": {"price": 40, "name": "春风铃种子", "type": "任务道具",
                                    "desc": "会随着春风轻轻摇响的铃兰种子，S48 播种后开出春风铃(S47 任务道具·S48 消耗)"},
    "mat_ying_huo_chong_fen": {"price": 30, "name": "萤火虫粪", "type": "草药",
                               "desc": "白鹿之森萤火虫的肥料粒，夜里微微发光——炼金辅材「萤光肥料」(S48 材料)"},
    "mat_chun_feng_ling_hua_ban": {"price": 60, "name": "春风铃花瓣", "type": "草药",
                                   "desc": "春风铃落下的一瓣，带着清甜的铃声余韵——炼金辅材「春风铃香露」(S49 材料)"},
    "mat_yue_guang_lu": {"price": 60, "name": "月光露", "type": "草药",
                         "desc": "白鹿之森夜晚草叶上凝出的露水，盛着月色——夜晚采集可得(白鹿之森采集池)，永恒花之名任务收集目标(S105 collect×3)"},
    # TODO 来源待接线：原 desc 称「月系炼金辅材(S50 材料)」——炼金配方无引用、S50 标记有误（实际为 S105 收集目标），已修正；炼金配方待接线
    # TODO 来源待接线：月桂叶 desc 声称 S50 材料（quests.py 注释「已登记·未并入 reward_item」），实际无接线
    "mat_yue_gui_ye": {"price": 60, "name": "月桂叶", "type": "草药",
                       "desc": "月桂树的老叶，揉碎有清苦的香气——炼金辅材/烹饪香料(S50 材料)"},
    "mat_yong_heng_hua_ban": {"price": 50, "name": "永恒花瓣（叶歌遗物）", "type": "任务道具",
                              "desc": "叶歌留下的最后一片花瓣，永不凋谢——埋入花苞根部，四季便有了归处(S50 任务道具·S51 消耗)"},
    "mat_yong_heng_hua_zhong_zi": {"price": 300, "name": "永恒花种子", "type": "传说",
                                   "desc": "叶语所赠的传说花种，全任务链唯一——可家园花圃种植，亦为炼金传说材料「永恒花露」之源(S51 纪念品/材料)"},

    # ===== v136 Phase6 合并: MATERIALS (5 条) =====
    'mat_ye_zhu_pi': {'price': 10, 'name': '野猪皮', 'type': '兽材', 'desc': '野猪岭野猪的厚皮，粗糙坚韧，鞣制后是新手护甲的内衬'},
    'mat_shan_zei_hui_zhang': {'price': 12, 'name': '山贼徽章', 'type': '兽材', 'desc': '山贼头目分发的铁皮徽章，敲碎能熔出一点铁料，铁匠铺照单全收'},
    'mat_shu_shi_he_xin': {'price': 35, 'name': '鼠狮核心', 'type': '兽材', 'desc': '鼠狮兽胸口凝聚的魔核，蕴藏着不安分的野性魔力'},
    'mat_yue_ying_zhi_pi': {'price': 65, 'name': '月影之皮', 'type': '兽材', 'desc': '月影林影豹的毛皮，月光下泛着银辉，是上等的法袍衬里'},
    'mat_long_yan_jing_hua': {'price': 80, 'name': '龙焰精华', 'type': '元素', 'desc': '龙脊山脉龙焰淬炼出的火系精华，握在掌心能感到灼热的脉动'},
    # ================= v167 锻造基础料体系（布料/皮革/金属锭/通用木料，鱼鱼拍板 2026-09-02） =================
    # 用途：白/蓝/绿常规装备用料贴合材质身份（布甲用布/皮甲用革/重甲用锭/弓杖用木）
    # 价格对齐 v165 经济价带；获取源见 shop/gather_pools/alchemy/subareas（v167 挂源）
    # ---- 布料线（布甲 int 系）----
    'mat_sen_lin_ya_ma_bu': {'price': 10, 'name': '林语麻布', 'type': '材料', 'desc': '橡木镇老织娘用山间亚麻织成的粗布，细密透气，是新手布衣的底料'},
    'mat_yue_guang_mian': {'price': 25, 'name': '月光棉', 'type': '材料', 'desc': '月光下采摘的银白棉絮纺成，触手温凉，隐约有月色流转'},
    'mat_yin_ling_si': {'price': 45, 'name': '银铃丝', 'type': '材料', 'desc': '铁港银铃坊织出的银丝，细韧光亮，贵族袍服最爱用它'},
    'mat_fu_wen_duan': {'price': 95, 'name': '符文绸', 'type': '材料', 'desc': '织入微光符文的绸缎，魔力在其间缓缓流淌'},
    'mat_sheng_hui_rong': {'price': 140, 'name': '圣辉绒', 'type': '材料', 'desc': '受过圣光祝福的绒料，泛着柔和的白芒，缝进法袍可护心神'},
    'mat_yue_hua_chou': {'price': 190, 'name': '月华绸', 'type': '材料', 'desc': '月语精灵以月华为线织出的绸缎，薄如蝉翼却坚韧异常'},
    'mat_xing_chen_jin': {'price': 280, 'name': '星辰锦', 'type': '材料', 'desc': '缀满星辉的锦缎，深夜中会泛起点点星光'},
    'mat_ling_wen_juan': {'price': 350, 'name': '灵纹绢', 'type': '材料', 'desc': '天生带着灵性纹路的绢帛，是传说法袍的至臻底材'},
    # ---- 皮革线（皮甲 agi 系，兽皮鞣制半成品）----
    'mat_cu_zhi_ge': {'price': 15, 'name': '粗制革', 'type': '材料', 'desc': '粗鞣过的兽皮，还带着些野性气味，结实耐磨'},
    'mat_ren_pi_ge': {'price': 60, 'name': '韧皮革', 'type': '材料', 'desc': '反复捶打鞣制的皮革，韧性十足，刀剑难透'},
    'mat_ying_zhi_ge': {'price': 95, 'name': '硬皮革', 'type': '材料', 'desc': '硬化的厚革，可抵挡中等程度的劈砍'},
    'mat_ying_ying_ge': {'price': 140, 'name': '影皮革', 'type': '材料', 'desc': '影豹皮鞣制的轻革，轻薄如影，适合刺客夜行'},
    'mat_jing_zhi_ge': {'price': 190, 'name': '精制革', 'type': '材料', 'desc': '精灵工艺精制的皮革，柔韧与坚固兼得'},
    'mat_shuang_han_ge': {'price': 245, 'name': '霜寒革', 'type': '材料', 'desc': '北境冰兽之皮鞣成，触手生寒，御寒绝佳'},
    'mat_mo_neng_ge': {'price': 350, 'name': '魔能革', 'type': '材料', 'desc': '龙皮与魔能淬炼的至强皮革，刀枪不入'},
    # ---- 金属锭线（重甲 str/vit 系 + 近战武器）----
    'mat_cu_tie': {'price': 5, 'name': '粗铁', 'type': '材料', 'desc': '未精炼的生铁，村中铁匠也能随手锻打'},
    'mat_qing_tong': {'price': 15, 'name': '青铜', 'type': '材料', 'desc': '铜锡合金，比粗铁坚韧，铁港工匠的入门料'},
    'mat_jing_tie_ding': {'price': 45, 'name': '精铁锭', 'type': '材料', 'desc': '反复锻打提纯的精铁锭，装备强化的优质底材'},
    'mat_gang_tie_ding': {'price': 95, 'name': '钢锭', 'type': '材料', 'desc': '精炼钢材，中域军械的主力料'},
    'mat_hei_tie_ding': {'price': 160, 'name': '黑铁锭', 'type': '材料', 'desc': '沉黑如墨的铁锭，淬火后坚硬无比'},
    'mat_mi_yin_ding': {'price': 245, 'name': '秘银锭', 'type': '材料', 'desc': '秘银炼成的银白锭块，轻盈却坚固，附魔首选'},
    'mat_jing_jin_ding': {'price': 315, 'name': '精金锭', 'type': '材料', 'desc': '精金铸锭，传说武器与重甲的脊梁'},
    'mat_xing_tie': {'price': 385, 'name': '星辰铁', 'type': '材料', 'desc': '陨落星辰中炼出的铁，泛着幽蓝星芒'},
    # ---- 通用木料线（弓/杖共用，鱼鱼拍板去部件名）----
    'mat_qing_xiang_mu': {'price': 10, 'name': '青橡木', 'type': '材料', 'desc': '青翠的老橡木，年轻而坚韧，做弓削杖皆宜'},
    'mat_lie_huo_mu': {'price': 45, 'name': '猎火木', 'type': '材料', 'desc': '猎火平原的硬木，纤维紧实，火烤也不易裂'},
    'mat_lie_feng_zhi_mu': {'price': 80, 'name': '猎风之木', 'type': '材料', 'desc': '猎风劲吹下生长的木料，轻韧如风'},
    'mat_ling_mu': {'price': 115, 'name': '灵木', 'type': '材料', 'desc': '精灵灵木，触手温润，魔力贯通无碍'},
    'mat_jing_ling_zhi_mu': {'price': 190, 'name': '精灵之木', 'type': '材料', 'desc': '月语古林深处的灵木，带着月华的气息'},
    'mat_chen_xing_zhi_mu': {'price': 215, 'name': '晨星之木', 'type': '材料', 'desc': '辉映晨星的木料，握在手中隐隐发亮'},
    'mat_yuan_su_zhi_mu': {'price': 315, 'name': '元素之木', 'type': '材料', 'desc': '受元素浸染的木料，天然亲和魔力'},
    'mat_cang_qiong_tian_mu': {'price': 315, 'name': '苍穹天木', 'type': '材料', 'desc': '苍穹之上坠落的古木，硬逾精钢却轻如云絮'},
}

# ============ 阶段四：消耗品（13 章 2.1/2.2/3/4 + 07 章 6.3，2026-08-06） ============
# 价格按 13 章货币说明：银币/金币数值直接取整为金币（1 银币 = 1 金币）
# heal/mana 为百分比（0.2 = 回复 20% HP），use 命令会转绝对值；旧固定值物品（heal>=1）兼容
CONSUMABLES = {
    # ---- 2.1 药水（回复类） ----
    "i_treat_s": {"cast": 1.0, "name": "治疗药水(小)", "price": 10, "heal": 0.2,
                  "desc": "回复 20% HP"},
    "i_treat_m": {"cast": 1.0, "name": "治疗药水(中)", "price": 30, "heal": 0.4,
                  "desc": "回复 40% HP"},
    "i_treat_l": {"cast": 1.0, "name": "治疗药水(大)", "price": 100, "heal": 0.6,
                  "desc": "回复 60% HP"},
    "i_mana_s": {"name": "魔法药水(小)", "price": 10, "mana": 0.2,
                 "desc": "回复 20% MP"},
    "i_mana_m": {"name": "魔法药水(中)", "price": 30, "mana": 0.4,
                 "desc": "回复 40% MP"},
    "i_mana_l": {"name": "魔法药水(大)", "price": 100, "mana": 0.6,
                 "desc": "回复 60% MP"},
    "i_full_potion": {"cast": 1.6, "name": "全效药水", "price": 50, "heal": 0.3, "mana": 0.3,
                      "desc": "回复 30% HP + 30% MP"},
    "i_holy_water": {"cast": 1.0, "name": "祝福圣水", "price": 80, "heal": 0.25,
                     "desc": "回复 25% HP（圣堂祝福的净水）"},
    # ---- 2.2 食物（非战斗回复 + 持续 buff） ----
    "i_bread": {"cast": 0.8, "name": "黑面包", "food": True, "price": 10, "hot": 0.03, "hot_turns": 3, "heal": 0.2, "stamina": 20,
                "desc": "回复 20% HP + 20 体力；战斗中每刻回复 3% 生命（3 刻）"},
    "i_meat_skewer": {"cast": 0.8, "name": "烤肉串", "food": True, "price": 15, "hot": 0.06, "hot_turns": 3, "heal": 0.25, "stamina": 30,
                      "desc": "回复 25% HP + 30 体力；战斗中每刻回复 6% 生命（3 刻）"},
    "i_ale": {"cast": 1.0, "name": "醇香麦酒", "food": True, "price": 10, "hot": 0.05, "hot_turns": 3, "hot_mana": 0.06, "heal": 0.15, "mana": 0.15, "stamina": 15,
              "desc": "回复 15% HP/MP + 15 体力；战斗中每刻回复 5% 生命、6% 魔力（3 刻）"},
    "i_stew": {"cast": 0.8, "name": "炖菜", "food": True, "price": 20, "hot": 0.06, "hot_turns": 3, "hot_mana": 0.08, "heal": 0.28, "mana": 0.2, "stamina": 40,
               "desc": "回复 28% HP + 20% MP + 40 体力；战斗中每刻回复 6% 生命、8% 魔力（3 刻）"},
    "i_elf_fruit": {"cast": 1.0, "name": "精灵圣果", "food": True, "price": 30, "hot": 0.08, "hot_turns": 3, "hot_mana": 0.12, "heal": 0.3, "mana": 0.3, "stamina": 30,
                    "desc": "回复 30% HP + 30% MP + 30 体力；战斗中每刻回复 8% 生命、12% 魔力（3 刻）"},
    "i_dwarf_liquor": {"cast": 1.0, "name": "矮人烈酒", "food": True, "price": 40, "effect": "buff_atk_food", "stamina": 15,
                       "desc": "回复 15 体力；战斗中攻击+10%（3 刻）"},
    # ---- 3 药剂（战斗中瞬时 buff） ----
    "i_str_potion": {"cast": 1.4, "name": "力量药剂", "price": 100, "effect": "buff_atk",
                     "desc": "3 刻攻击 + 30%"},
    "i_def_potion": {"cast": 1.4, "name": "铁壁药剂", "price": 500, "effect": "buff_def",
                     "desc": "抵挡 3 次受击防御 + 45%"},
    "i_spd_potion": {"cast": 1.4, "name": "疾风药剂", "price": 145, "effect": "buff_spd",
                     "desc": "3 刻速度 + 40%"},
    "i_fury_potion": {"cast": 2.0, "name": "狂怒药剂", "price": 240, "effect": "next_atk_up", "effect_data": {"pct": 0.5},
                      "desc": "下一次攻击 + 50%"},
    "i_holy_potion": {"cast": 1.4, "name": "圣光药剂", "price": 300, "effect": "heal_up", "effect_data": {"pct": 0.2},
                      "desc": "3 刻治疗技能效果 + 20%"},
    "i_dragon_scale_potion": {"cast": 2.0, "name": "龙鳞药剂", "price": 400, "effect": "magic_resist", "effect_data": {"pct": 0.15},
                              "desc": "3 刻受到魔法伤害－15%"},
    "i_battlecry_potion": {"cast": 2.0, "name": "战吼药剂", "price": 30, "effect": "buff_atk_big",
                           "desc": "3 刻攻击 + 40%"},
    "i_lucky_potion": {"cast": 1.0, "name": "幸运药剂", "price": 200, "effect": "buff_crit",
                       "desc": "3 刻暴击率 + 20%"},
    # ---- 4 卷轴（一次性法术） ----
    "i_scroll_heal": {"cast": 0.6, "name": "治愈卷轴", "price": 200, "heal": 0.4,
                      "desc": "战斗内回复 40% HP"},
    "i_scroll_purify": {"cast": 0.6, "name": "净化卷轴", "price": 300, "effect": "purify",
                        "desc": "战斗内驱散全队负面"},
    "i_scroll_teleport": {"name": "传送卷轴", "price": 500, "effect": "teleport_portal",
                          "desc": "传送到最近激活的方碑城镇（需先激活方碑，方碑锚定传送）"},
    # ---- 消耗珍宝（v104：原 MATERIALS 材料壳修复——双倍金币符/复活羽毛实现效果；
    #      改名卡/经验药水无对应模板支撑已删除占位） ----
    "i_shuang_bei_jin_bi_fu": {"name": "双倍金币符", "price": 300, "effect": "lucky",
                               "desc": "金色符箓，使用后 10 分钟内打怪金币＋50%、材料掉落＋1（一次消耗）"},
    "i_fu_huo_yu_mao": {"name": "复活羽毛", "price": 200, "effect": "return_vila",
                        "desc": "泛着微光的洁白羽毛，捏碎后化作光芒送你返回最近城镇（野外保命珍宝，一次消耗）"},
    # ---- 07 章 6.3 ----
    "i_holy_charm": {"name": "圣光护符", "price": 100, "effect": "purify",
                     "desc": "驱散一次负面状态"},
    "i_moon_dew": {"cast": 1.0, "name": "月之露", "price": 50, "heal": 0.5, "mana": 0.5,
                   "desc": "战斗外回复 50% HP/MP"},
    # ---- 烹饪产物（13 章 2.3 烹饪表）----
    # v94 体力：食物附带体力恢复（烹饪副业核心价值）
    "it_slime_jelly": {"cast": 1.0, "name": "史莱姆果冻", "food": True, "price": 20, "hot": 0.06, "hot_turns": 3, "heal": 0.2, "stamina": 20,
                      "desc": "回复 20% HP + 20 体力；战斗中每刻回复 6% 生命（3 刻）"},
    "it_cook_skewer": {"cast": 0.8, "name": "烤肉串(自制)", "food": True, "price": 30, "hot": 0.08, "hot_turns": 3, "heal": 0.35, "stamina": 30,
                      "desc": "回复 35% HP + 30 体力；战斗中每刻回复 8% 生命（3 刻）"},
    "it_gold_feast": {"cast": 1.2, "name": "金鲤盛宴", "food": True, "price": 60, "hot": 0.1, "hot_turns": 4, "hot_mana": 0.08, "heal": 0.5, "mana": 0.2, "stamina": 60,
                     "desc": "回复 50% HP + 20% MP + 60 体力；战斗中每刻回复 10% 生命、8% 魔力（4 刻）"},
    # ---- 垂钓产业链·炼金（16 章 2.5：鲛人泪/龙涎香独占材料） ----
    "i_mermaid_tear": {"name": "鲛人之泪", "price": 150, "effect": "buff_matk",
                      "desc": "3 刻魔攻 + 30%"},
    "i_ambergris_draught": {"cast": 1.0, "name": "龙涎药剂", "price": 250, "effect": "buff_atk_def",
                           "desc": "3 刻攻击 + 30%；抵挡 3 次受击防御 + 45%"},
    # ============ v97.7 道具模板批量生成（55→250，全部走 core/item_templates.py） ============
    # ---- A. 药水线扩展（heal/mana/复合）----
    "i_treat_micro": {"cast": 1.0, "name": "微效治疗药水", "price": 8, "heal": 0.15,
                      "desc": "回复 15% HP"},
    "i_treat_light": {"cast": 1.0, "name": "轻效治疗药水", "price": 20, "heal": 0.25,
                      "desc": "回复 25% HP"},
    "i_treat_strong": {"cast": 2.0, "name": "强效治疗药水", "price": 60, "heal": 0.5,
                       "desc": "回复 50% HP"},
    "i_treat_holy": {"cast": 2.0, "name": "圣辉治疗药水", "price": 180, "heal": 0.8,
                     "desc": "回复 80% HP"},
    "i_treat_divine": {"cast": 2.0, "name": "神愈药水", "price": 300, "heal": 1.0,
                       "desc": "完全回复 HP"},
    "i_herb_juice": {"cast": 1.0, "name": "草药汁", "price": 12, "heal": 0.2,
                     "desc": "回复 20% HP（路边野草熬成）"},
    "i_bandage": {"cast": 1.0, "name": "止血绷带", "price": 25, "heal": 0.3,
                  "desc": "回复 30% HP"},
    "i_holy_light_pot": {"cast": 1.0, "name": "圣光药水", "price": 90, "heal": 0.5,
                         "desc": "回复 50% HP（圣堂祝福）"},
    "i_dragon_blood_pot": {"cast": 2.0, "name": "龙血药水", "price": 200, "heal": 0.7,
                           "desc": "回复 70% HP（龙之血脉沸腾）"},
    "i_phoenix_tear": {"cast": 2.0, "name": "凤凰之泪", "price": 350, "heal": 0.9,
                       "desc": "回复 90% HP（浴火重生之力）"},
    "i_life_spring": {"cast": 2.0, "name": "生命之泉", "price": 500, "heal": 1.0,
                      "desc": "完全回复 HP（精灵圣地泉水）"},
    "i_mana_micro": {"name": "微效魔力药水", "price": 8, "mana": 0.15,
                     "desc": "回复 15% MP"},
    "i_mana_light": {"name": "轻效魔力药水", "price": 20, "mana": 0.25,
                     "desc": "回复 25% MP"},
    "i_mana_strong": {"name": "强效魔力药水", "price": 60, "mana": 0.5,
                      "desc": "回复 50% MP"},
    "i_mana_holy": {"name": "圣辉魔力药水", "price": 180, "mana": 0.8,
                    "desc": "回复 80% MP"},
    "i_mana_divine": {"name": "神愈魔力药水", "price": 300, "mana": 1.0,
                      "desc": "完全回复 MP"},
    "i_arcane_crystal": {"name": "秘法结晶", "price": 100, "mana": 0.6,
                         "desc": "回复 60% MP（法师塔结晶）"},
    "i_moonlight_pot": {"name": "月光药剂", "price": 50, "mana": 0.3,
                        "desc": "回复 30% MP（月门城特产）"},
    "i_starlight_pot": {"name": "星辉药剂", "price": 150, "mana": 0.5,
                        "desc": "回复 50% MP（星辰之力）"},
    "i_arcane_dew": {"name": "奥术甘露", "price": 220, "mana": 0.7,
                     "desc": "回复 70% MP"},
    "i_mana_source": {"name": "法力源泉", "price": 400, "mana": 0.9,
                      "desc": "回复 90% MP"},
    "i_lingxi_pot": {"name": "灵犀药剂", "price": 70, "mana": 0.4,
                     "desc": "回复 40% MP（心境通明）"},
    "i_full_potion_hi": {"cast": 1.6, "name": "高级全效药水", "price": 120, "heal": 0.4, "mana": 0.4,
                         "desc": "回复 40% HP + 40% MP"},
    "i_full_potion_super": {"cast": 2.0, "name": "超级全效药水", "price": 250, "heal": 0.5, "mana": 0.5,
                            "desc": "回复 50% HP + 50% MP"},
    "i_sage_pot": {"cast": 1.6, "name": "贤者药剂", "price": 180, "heal": 0.3, "mana": 0.5,
                   "desc": "回复 30% HP + 50% MP"},
    "i_battle_mix": {"cast": 1.6, "name": "战斗合剂", "price": 160, "heal": 0.4, "mana": 0.2,
                     "desc": "回复 40% HP + 20% MP"},
    "i_adventurer_mix": {"cast": 1.6, "name": "冒险者合剂", "price": 100, "heal": 0.2, "mana": 0.4,
                         "desc": "回复 20% HP + 40% MP"},
    "i_holy_sage_pot": {"cast": 1.6, "name": "圣贤药剂", "price": 420, "heal": 0.6, "mana": 0.6,
                        "desc": "回复 60% HP + 60% MP"},
    "i_expedition_mix": {"cast": 1.6, "name": "远征合剂", "price": 200, "heal": 0.5, "mana": 0.3,
                         "desc": "回复 50% HP + 30% MP"},
    "i_apprentice_mix": {"cast": 1.6, "name": "学徒合剂", "price": 30, "heal": 0.15, "mana": 0.15,
                         "desc": "回复 15% HP + 15% MP"},
    "i_life_elixir": {"cast": 1.0, "name": "生命灵液", "price": 130, "heal": 0.6,
                      "desc": "回复 60% HP（精灵泉水提炼）"},
    "i_moon_holy_water": {"name": "月光圣水", "price": 160, "mana": 0.8,
                          "desc": "回复 80% MP（月下凝结）"},
    "i_salve_s": {"cast": 1.0, "name": "治疗药膏", "price": 40, "heal": 150,
                  "desc": "回复 150 点 HP（固定值，旧式配方）"},
    "i_salve_m": {"cast": 2.0, "name": "强效药膏", "price": 120, "heal": 300,
                  "desc": "回复 300 点 HP（固定值，旧式配方）"},
    "i_salve_l": {"cast": 2.0, "name": "秘制药膏", "price": 300, "heal": 500,
                  "desc": "回复 500 点 HP（固定值，旧式配方）"},
    # ---- B. 食物线（城镇特色 12 地 × 3 + 野外野味）----
    "i_oats_porridge": {"cast": 0.8, "name": "燕麦粥", "food": True, "price": 10, "hot": 0.03, "hot_turns": 3, "heal": 0.2, "stamina": 20,
                        "desc": "回复 20% HP + 20 体力（橡木镇农家）；战斗中每刻回复 3% 生命（3 刻）"},
    "i_honey_pancake": {"cast": 0.8, "name": "蜂蜜烤饼", "food": True, "price": 12, "hot": 0.03, "hot_turns": 3, "stamina": 25,
                        "desc": "回复 25 体力（橡木镇甜点）；战斗中每刻回复 3% 生命（3 刻）"},
    "i_apple_wine": {"cast": 1.0, "name": "苹果酒", "food": True, "price": 10, "hot_turns": 3, "hot_mana": 0.04, "mana": 0.1, "stamina": 15,
                     "desc": "回复 10% MP + 15 体力（橡木镇果园）；战斗中每刻回复 4% 魔力（3 刻）"},
    "i_deer_burger": {"cast": 0.8, "name": "鹿肉汉堡", "food": True, "price": 25, "effect": "buff_def_food", "heal": 0.3, "stamina": 35,
                      "desc": "回复 30% HP + 35 体力（白鹿城名吃）；战斗中防御+15%（3 刻）"},
    "i_honey_tea": {"cast": 1.0, "name": "蜂蜜茶", "food": True, "price": 15, "hot_turns": 3, "hot_mana": 0.08, "mana": 0.2, "stamina": 20,
                    "desc": "回复 20% MP + 20 体力（白鹿城茶点）；战斗中每刻回复 8% 魔力（3 刻）"},
    "i_deer_cheese": {"cast": 1.0, "name": "鹿奶干酪", "food": True, "price": 18, "food_effect": "thorns", "stamina": 25,
                      "desc": "回复 25 体力（白鹿城牧场）；战斗中吃下获得【反伤】：受击 10% 反弹 30% 伤害"},
    "i_seafood_chowder": {"cast": 0.8, "name": "海鲜浓汤", "food": True, "price": 35, "food_effect": "precise", "heal": 0.35, "stamina": 40,
                          "desc": "回复 35% HP + 40 体力（铁港城码头）；战斗中吃下获得【精准】：本场伤害 + 10%"},
    "i_salt_baked_fish": {"cast": 0.8, "name": "盐焗烤鱼", "food": True, "price": 28, "hot": 0.08, "hot_turns": 3, "hot_mana": 0.04, "heal": 0.25, "mana": 0.1, "stamina": 30,
                          "desc": "回复 25% HP + 10% MP + 30 体力（铁港城渔获）；战斗中每刻回复 8% 生命、4% 魔力（3 刻）"},
    "i_dock_rum": {"cast": 1.0, "name": "码头朗姆", "food": True, "price": 22, "hot_turns": 3, "hot_mana": 0.08, "mana": 0.2, "stamina": 20,
                   "desc": "回复 20% MP + 20 体力（铁港城水手）；战斗中每刻回复 8% 魔力（3 刻）"},
    "i_moon_cake": {"cast": 0.8, "name": "月光饼", "food": True, "price": 30, "food_effect": "meditate", "heal": 0.25, "mana": 0.25, "stamina": 30,
                    "desc": "回复 25% HP + 25% MP + 30 体力（月门城点心）；战斗中吃下获得【冥想】：每刻回复 1% 魔力"},
    "i_laurel_tea": {"cast": 1.0, "name": "月桂茶", "food": True, "price": 20, "hot_turns": 3, "hot_mana": 0.12, "mana": 0.3, "stamina": 25,
                     "desc": "回复 30% MP + 25 体力（月门城茶会）；战斗中每刻回复 12% 魔力（3 刻）"},
    "i_silver_jelly": {"cast": 1.0, "name": "银月果冻", "food": True, "price": 16, "hot": 0.06, "hot_turns": 3, "stamina": 20,
                       "desc": "回复 20 体力（月门城甜品）；战斗中每刻回复 6% 生命（3 刻）"},
    "i_sacred_bread": {"cast": 0.8, "name": "圣餐面包", "food": True, "price": 26, "food_effect": "shield", "heal": 0.3, "stamina": 30,
                       "desc": "回复 30% HP + 30 体力（圣堂赐福）；战斗中吃下获得【护盾】：获得 10% 生命护盾（3 刻）"},
    "i_holy_water_drink": {"cast": 1.0, "name": "圣堂净水", "food": True, "price": 12, "hot_turns": 3, "hot_mana": 0.06, "mana": 0.15, "stamina": 15,
                           # v104 R3 M08 P2-3：改名消除三名"圣水"歧义（材料 mat_sheng_shui / 药水 i_holy_water / 本品）
                           "desc": "回复 15% MP + 15 体力（圣堂净水）；战斗中每刻回复 6% 魔力（3 刻）"},
    "i_blessed_pastry": {"cast": 1.0, "name": "祝福糕点", "food": True, "price": 20, "hot": 0.06, "hot_turns": 3, "heal": 0.2, "stamina": 25,
                         "desc": "回复 20% HP + 25 体力（圣堂烘焙）；战斗中每刻回复 6% 生命（3 刻）"},
    "i_pirate_stew": {"cast": 0.8, "name": "海盗炖鱼", "food": True, "price": 32, "food_effect": "execute", "heal": 0.3, "stamina": 35,
                      "desc": "回复 30% HP + 35 体力（无名港私房）；战斗中吃下获得【处决】：对生命<30%的敌人 + 30%伤害"},
    "i_octopus_ball": {"cast": 0.8, "name": "章鱼烧", "food": True, "price": 24, "hot": 0.06, "hot_turns": 3, "stamina": 30,
                       "desc": "回复 30 体力（无名港小吃）；战斗中每刻回复 6% 生命（3 刻）"},
    "i_fog_coffee": {"cast": 1.0, "name": "雾港咖啡", "food": True, "price": 18, "effect": "buff_spd_food", "mana": 0.2, "stamina": 20,
                     "desc": "回复 20% MP + 20 体力（无名港提神）；战斗中速度+12%（3 刻）"},
    "i_ash_pancake": {"cast": 0.8, "name": "灰烬烤饼", "food": True, "price": 24, "food_effect": "element_fire", "heal": 0.25, "stamina": 30,
                      "desc": "回复 25% HP + 30 体力（灰烬城炭火烤）；战斗中吃下获得【元素·火】：攻击附加 5% 火属性伤害"},
    "i_lava_egg": {"cast": 0.8, "name": "熔岩蛋", "food": True, "price": 30, "hot": 0.08, "hot_turns": 3, "hot_mana": 0.08, "heal": 0.25, "mana": 0.2, "stamina": 35,
                   "desc": "回复 25% HP + 20% MP + 35 体力（灰烬城特产）；战斗中每刻回复 8% 生命、8% 魔力（3 刻）"},
    "i_ember_pepper": {"cast": 1.0, "name": "烬火辣椒", "food": True, "price": 10, "food_effect": "bleed", "heal": 0.1, "stamina": 15,
                       "desc": "回复 10% HP + 15 体力（灰烬城辣味）；战斗中吃下获得【流血】：攻击 20% 使敌人流血（每刻 5% 生命，3 刻）"},
    "i_royal_roast": {"cast": 1.2, "name": "皇家烤肉", "food": True, "price": 55, "food_effect": "charge", "heal": 0.4, "stamina": 45,
                      "desc": "回复 40% HP + 45 体力（王都御膳）；战斗中吃下获得【蓄力】：攻击 10% 造成 150% 伤害"},
    "i_gold_dessert": {"cast": 1.0, "name": "金箔甜点", "food": True, "price": 45, "hot_turns": 4, "hot_mana": 0.12, "mana": 0.3, "stamina": 30,
                       "desc": "回复 30% MP + 30 体力（王都宫廷）；战斗中每刻回复 12% 魔力（4 刻）"},
    "i_royal_soup": {"cast": 1.2, "name": "御膳汤", "food": True, "price": 50, "food_effect": "dawn_crown", "heal": 0.3, "mana": 0.2, "stamina": 40,
                     "desc": "回复 30% HP + 20% MP + 40 体力（王都名厨）；战斗中吃下获得【晨曦祝福】：每刻回复 2% 生命"},
    "i_elf_jam": {"cast": 1.0, "name": "精灵果酱", "food": True, "price": 35, "effect": "food_spd_up_small", "heal": 0.3, "stamina": 25,
                  # v105R3 M16 P2-8：实现为 3 刻 buff（battle.py BUFF_MULT food_spd_up_small），
                  # desc 不再写「本场」（策划口径 2 场待拍板，先与实现统一）
                  "desc": "回复 30% HP + 25 体力（精灵森林）；战斗中速度+10%（3 刻）"},
    "i_nectar_wine": {"cast": 1.0, "name": "花蜜酒", "food": True, "price": 30, "effect": "buff_matk_food", "mana": 0.3, "stamina": 20,
                      "desc": "回复 30% MP + 20 体力（精灵花房）；战斗中魔攻+10%（3 刻）"},
    "i_tree_honey": {"cast": 1.0, "name": "树蜜糖", "food": True, "price": 20, "food_effect": "regen", "heal": 0.2, "stamina": 15,
                     "desc": "回复 20% HP + 15 体力（世界树蜜）；战斗中吃下获得【回春】：每刻回复 1% 生命"},
    "i_dwarf_oven_bread": {"cast": 0.8, "name": "铁炉面包", "food": True, "price": 22, "hot": 0.06, "hot_turns": 3, "heal": 0.25, "stamina": 30,
                           "desc": "回复 25% HP + 30 体力（矮人铁炉）；战斗中每刻回复 6% 生命（3 刻）"},
    "i_miner_stew": {"cast": 0.8, "name": "矿工炖肉", "food": True, "price": 28, "hot": 0.08, "hot_turns": 3, "heal": 0.3, "stamina": 35,
                     "desc": "回复 30% HP + 35 体力（矮人矿场）；战斗中每刻回复 8% 生命（3 刻）"},
    "i_stone_ale": {"cast": 1.0, "name": "石酿麦酒", "food": True, "price": 18, "hot_turns": 3, "hot_mana": 0.08, "mana": 0.2, "stamina": 20,
                    "desc": "回复 20% MP + 20 体力（矮人酒窖）；战斗中每刻回复 8% 魔力（3 刻）"},
    # v105R3 M16 P2-1：雪狼皮×1=35 成本，38 售价 ratio=0.92 超 90% 上限 → 40（0.875）
    "i_snowwolf_steak": {"cast": 0.8, "name": "雪狼肉排", "food": True, "price": 40, "food_effect": "pierce", "heal": 0.35, "stamina": 40,
                         "desc": "回复 35% HP + 40 体力（霜原猎手）；战斗中吃下获得【贯穿】：攻击 20% 无视防御"},
    "i_frost_berry": {"cast": 1.0, "name": "冰霜浆果", "food": True, "price": 20, "food_effect": "element_ice", "mana": 0.2, "stamina": 25,
                      "desc": "回复 20% MP + 25 体力（霜原冰果）；战斗中吃下获得【元素·冰】：攻击附加 5% 冰伤 + 减速"},
    "i_reindeer_jerky": {"cast": 1.0, "name": "驯鹿干", "food": True, "price": 26, "hot": 0.08, "hot_turns": 3, "heal": 0.25, "stamina": 30,
                         "desc": "回复 25% HP + 30 体力（霜原风干）；战斗中每刻回复 8% 生命（3 刻）"},
    "i_dragon_pepper": {"cast": 1.0, "name": "龙息辣椒", "food": True, "price": 16, "effect": "buff_crit_food", "heal": 0.15, "stamina": 20,
                        "desc": "回复 15% HP + 20 体力（龙脊山民）；战斗中暴击+8%（3 刻）"},
    "i_dragon_egg_pancake": {"cast": 1.2, "name": "龙蛋煎饼", "food": True, "price": 90, "food_effect": "dragon_tongue", "heal": 0.4, "mana": 0.2, "stamina": 45,
                             "desc": "回复 40% HP + 20% MP + 45 体力（龙脊盛宴）；战斗中吃下获得【龙语印记】：攻击叠印记（每层 + 2%伤害，上限 5 层）"},
    "i_wolf_jerky": {"cast": 0.8, "name": "狼肉干", "food": True, "price": 14, "food_effect": "counter", "heal": 0.2, "stamina": 30,
                     "desc": "回复 20% HP + 30 体力（野外干粮）；战斗中吃下获得【反击】：受击 20% 反击 60% 伤害"},
    "i_eagle_egg": {"cast": 0.8, "name": "鹰蛋", "food": True, "price": 12, "food_effect": "combo", "heal": 0.2, "stamina": 20,
                    "desc": "回复 20% HP + 20 体力（悬崖鹰巢）；战斗中吃下获得【连击】：攻击 15% 追加 50% 伤害"},
    "i_snake_soup": {"cast": 1.0, "name": "蛇羹", "food": True, "price": 18, "food_effect": "lifesteal", "heal": 0.2, "mana": 0.1, "stamina": 25,
                     "desc": "回复 20% HP + 10% MP + 25 体力（沼泽风味）；战斗中吃下获得【吸血】：攻击回复 8% 伤害为生命"},
    "i_mushroom_soup": {"cast": 0.8, "name": "蘑菇汤", "food": True, "price": 12, "food_effect": "armor_break", "heal": 0.15, "stamina": 20,
                        "desc": "回复 15% HP + 20 体力（森林采菇）；战斗中吃下获得【破甲】：攻击 25% 降敌防 15%（2 刻）"},
    "i_wild_honey": {"cast": 1.0, "name": "野蜂蜜", "food": True, "price": 10, "hot_turns": 3, "hot_mana": 0.06, "mana": 0.15, "stamina": 15,
                     "desc": "回复 15% MP + 15 体力（树洞蜂巢）；战斗中每刻回复 6% 魔力（3 刻）"},
    "i_roast_bird": {"cast": 0.8, "name": "烤鸟肉", "food": True, "price": 14, "hot": 0.05, "hot_turns": 3, "heal": 0.2, "stamina": 25,
                     "desc": "回复 20% HP + 25 体力（篝火烤鸟）；战斗中每刻回复 5% 生命（3 刻）"},
    "i_fish_soup": {"cast": 0.8, "name": "鱼汤", "food": True, "price": 16, "hot": 0.06, "hot_turns": 3, "heal": 0.2, "stamina": 25,
                    "desc": "回复 20% HP + 25 体力（河边鲜鱼）；战斗中每刻回复 6% 生命（3 刻）"},
    "i_herb_tea": {"cast": 1.0, "name": "草药茶", "food": True, "price": 8, "hot": 0.03, "hot_turns": 3, "hot_mana": 0.04, "heal": 0.1, "mana": 0.1, "stamina": 15,
                   "desc": "回复 10% HP + 10% MP + 15 体力（清苦回甘）；战斗中每刻回复 3% 生命、4% 魔力（3 刻）"},
    # ---- C. 战斗药水扩展（buff 模板，6 种 p_buffs key）----
    "i_war_god_pot": {"cast": 2.0, "name": "战神药剂", "price": 1635, "effect": "buff_atk",
                      "desc": "3 刻攻击 + 30%"},
    "i_brute_pot": {"cast": 2.0, "name": "蛮力药剂", "price": 140, "effect": "buff_atk_small",
                    "desc": "3 刻攻击 + 20%"},
    "i_armor_break_pot": {"cast": 1.4, "name": "破甲药剂", "price": 325, "effect": "armor_break_pot", "effect_data": {"pct": 0.15, "turns": 2},
                          "desc": "敌人防御－15%（2 刻）"},
    "i_dragon_power_pot": {"cast": 1.4, "name": "龙力药剂", "price": 1105, "effect": "buff_atk_big",
                           "desc": "3 刻攻击 + 40%"},
    "i_rock_shield_pot": {"cast": 1.8, "name": "岩盾药剂", "price": 295, "effect": "rock_shield", "effect_data": {"pct": 0.10},
                          "desc": "获得 10% 生命护盾（3 刻）"},
    "i_thorn_pot": {"cast": 1.8, "name": "荆棘药剂", "price": 265, "effect": "thorns_pot", "effect_data": {"pct": 0.30},
                    "desc": "3 刻受击反弹 30% 伤害"},
    "i_holy_shield_pot": {"cast": 1.8, "name": "圣盾药剂", "price": 180, "effect": "holy_shield", "effect_data": {"pct": 0.15},
                          "desc": "获得 15% 生命护盾（3 刻）"},
    "i_immovable_pot": {"cast": 1.8, "name": "不动药剂", "price": 115, "effect": "cc_immune", "effect_data": {"turns": 3},
                        "desc": "3 刻免疫眩晕/冻结/减速"},
    "i_swift_pot": {"cast": 1.4, "name": "迅捷药剂", "price": 800, "effect": "buff_spd",
                    "desc": "3 刻速度 + 40%"},
    "i_shadowstep_pot": {"cast": 1.8, "name": "影步药剂", "price": 235, "effect": "dodge_pot", "effect_data": {"pct": 0.15},
                         "desc": "3 刻 15% 概率闪避攻击"},
    "i_pene_pot": {"cast": 1.8, "name": "穿甲药剂", "price": 160, "effect": "pene_pot", "effect_data": {"pct": 0.15},
                   "desc": "3 刻物穿 + 15%"},
    "i_pene_magi_pot": {"cast": 1.8, "name": "破法药剂", "price": 160, "effect": "pene_magi_pot", "effect_data": {"pct": 0.15},
                        "desc": "3 刻法穿 + 15%"},
    "i_lifesteal_pot": {"cast": 1.8, "name": "嗜血药剂", "price": 170, "effect": "lifesteal_pot", "effect_data": {"pct": 0.15},
                        "desc": "3 刻吸血 + 15%"},
    "i_crit_dmg_pot": {"cast": 1.8, "name": "狂暴药剂", "price": 510, "effect": "crit_dmg_pot", "effect_data": {"pct": 0.25},
                       "desc": "3 刻暴击伤害 + 25%"},
    "i_block_pot": {"cast": 1.0, "name": "岩壁药剂", "price": 470, "effect": "block_pot", "effect_data": {"pct": 0.15},
                    "desc": "3 刻格挡 + 15%"},
    "i_windspirit_pot": {"cast": 1.4, "name": "风灵药剂", "price": 415, "effect": "buff_spd_small",
                         "desc": "3 刻速度 + 20%"},
    "i_lethal_pot": {"cast": 1.4, "name": "致命药剂", "price": 570, "effect": "buff_crit_big",
                     "desc": "3 刻暴击率 + 30%"},
    "i_sharpeye_pot": {"cast": 1.4, "name": "锐目药剂", "price": 100, "effect": "buff_crit_small",
                       "desc": "3 刻暴击率 + 15%"},
    "i_death_pot": {"cast": 2.0, "name": "死神药剂", "price": 295, "effect": "execute_pot", "effect_data": {"pct": 0.30, "hp_threshold": 0.30},
                    "desc": "3 刻对生命<30%敌人 + 30%伤害"},
    "i_arcane_pot": {"cast": 1.4, "name": "奥术药剂", "price": 120, "effect": "buff_matk",
                     "desc": "3 刻魔攻 + 30%"},
    "i_mystic_pot": {"cast": 1.4, "name": "秘法药剂", "price": 225, "effect": "buff_matk_strong",
                     "desc": "3 刻魔攻 + 80%"},
    "i_starfire_pot": {"cast": 1.4, "name": "星火药剂", "price": 265, "effect": "buff_matk_strong",
                       "desc": "3 刻魔攻 + 80%"},
    "i_void_pot": {"cast": 2.0, "name": "虚空药剂", "price": 915, "effect": "buff_matk_crit",
                   "desc": "3 刻魔攻 + 80%、暴击率 + 15%"},
    "i_berserker_pot": {"cast": 2.0, "name": "狂战士药剂", "price": 200, "effect": "buff_atk_def",
                        "desc": "3 刻攻击 + 30%；抵挡 3 次受击防御 + 45%"},
    "i_warsaint_pot": {"cast": 2.0, "name": "战圣药剂", "price": 1465, "effect": "buff_atk_big_def",
                       "desc": "3 刻攻击 + 40%；抵挡 3 次受击防御 + 45%"},
    # ---- D. 卷轴/护符/券扩展 ----
    "i_scroll_guild": {"name": "公会回城卷", "price": 300, "effect": "return_vila",
                       "desc": "立即返回最近城镇（公会刻印）"},
    "i_scroll_camp": {"name": "营地回城卷", "price": 200, "effect": "return_vila",
                      "desc": "立即返回最近城镇（营地常备）"},
    "i_scroll_noble": {"name": "贵族传送卷", "price": 800, "effect": "return_vila",
                       "desc": "立即返回最近城镇（鎏金卷轴）"},
    "i_lucky_coin": {"name": "幸运金币", "price": 300, "effect": "lucky",
                     "desc": "10 分钟内打怪金币 + 50%、材料 + 1"},
    "i_four_leaf": {"name": "四叶草", "price": 400, "effect": "lucky",
                    "desc": "10 分钟内打怪金币 + 50%、材料 + 1（精灵祝福）"},
    "i_fortune_paper": {"name": "福神签", "price": 500, "effect": "lucky",
                        "desc": "10 分钟内打怪金币 + 50%、材料 + 1（庙里求的）"},
    "i_wealth_talisman": {"name": "财神符", "price": 800, "effect": "lucky",
                          "desc": "10 分钟内打怪金币 + 50%、材料 + 1（王都财神）"},
    "i_pardon_order": {"name": "赦免令", "price": 1000, "effect": "clear_red",
                       "desc": "立即消除红名（王都签发）"},
    "i_absolution_scroll": {"name": "洗罪券", "price": 1500, "effect": "clear_red",
                            "desc": "立即消除红名（圣堂赦罪）"},
    "i_king_pardon": {"name": "国王赦书", "price": 2000, "effect": "clear_red",
                      "desc": "立即消除红名（御笔亲书）"},
    # ---- E. 宝箱扩展（open_chest 模板）----
    "i_chest_wood": {"name": "木箱", "price": 50, "effect": "open_chest",
                     "desc": "打开获得金币，概率开出图纸"},
    "i_chest_iron": {"name": "铁箱", "price": 120, "effect": "open_chest",
                     "desc": "打开获得金币，概率开出图纸"},
    "i_chest_bronze": {"name": "青铜箱", "price": 200, "effect": "open_chest",
                       "desc": "打开获得金币，概率开出图纸"},
    "i_chest_silver": {"name": "白银箱", "price": 350, "effect": "open_chest",
                       "desc": "打开获得金币，概率开出图纸"},
    "i_chest_gold": {"name": "黄金箱", "price": 600, "effect": "open_chest",
                     "desc": "打开获得金币，概率开出图纸"},
    "i_chest_mithril": {"name": "秘银箱", "price": 1000, "effect": "open_chest",
                        "desc": "打开获得金币，概率开出图纸"},
    "i_chest_dragon": {"name": "龙晶箱", "price": 2000, "effect": "open_chest",
                       "desc": "打开获得金币，概率开出图纸"},
    "i_chest_pirate": {"name": "海盗宝箱", "price": 300, "effect": "open_chest",
                       "desc": "打开获得金币，概率开出图纸（无名港战利品）"},
    "i_chest_tomb": {"name": "古墓宝箱", "price": 500, "effect": "open_chest",
                     "desc": "打开获得金币，概率开出图纸（遗迹出土）"},
    "i_chest_elf": {"name": "精灵宝箱", "price": 800, "effect": "open_chest",
                    "desc": "打开获得金币，概率开出图纸（藤蔓缠绕）"},
    "i_chest_royal": {"name": "王库宝箱", "price": 1500, "effect": "open_chest",
                      "desc": "打开获得金币，概率开出图纸（国库封存）"},
    "i_chest_abyss": {"name": "深渊宝箱", "price": 2500, "effect": "open_chest",
                      "desc": "打开获得金币，概率开出图纸（深渊气息）"},
    # ---- G. 收藏品（纪念/图鉴向，不能使用）----
    "i_badge_iron_rank": {"name": "铁牌徽章", "price": 50, "type": "收藏品",
                          "desc": "冒险者行会颁发的铁牌，冒险生涯的起点（主线 q1_2 行会入门奖励）"},
    "i_mem_emberwalker": {"name": "余烬行者徽章", "price": 300, "type": "收藏品",
                          "desc": "冒险纪念：余烬行者徽章"},
    # ---- 旧 ID 别名（兼容旧测试/旧数据引用，内容对齐新世界） ----
    "i_treatment_potion": {"cast": 1.0, "name": "治疗药水", "price": 10, "heal": 0.2,
                           "desc": "回复 20% HP"},
    "i_mana_potion": {"name": "魔法药水", "price": 10, "mana": 0.2,
                      "desc": "回复 20% MP"},
    "i_great_treatment": {"cast": 1.0, "name": "高效治疗药水", "price": 30, "heal": 0.4,
                          "desc": "回复 40% HP"},
    "i_great_mana": {"name": "强效魔法药水", "price": 200, "mana": 0.4,
                     "desc": "回复 40% MP"},
    "i_super_treatment": {"cast": 2.0, "name": "超级治疗药水", "price": 450, "heal": 0.6,
                          "desc": "回复 60% HP"},
    "i_super_mana": {"name": "超级魔法药水", "price": 450, "mana": 0.6,
                     "desc": "回复 60% MP"},
    "i_scroll_escape": {"cast": 0.6, "name": "回城卷轴", "price": 500, "effect": "return_vila",
                        "desc": "立即返回最近城镇"},
    # ---- 2.9 副本入场钥匙（29 章 11 节：高难/外域副本门槛） ----
    "i_key_old_king": {"name": "王陵钥匙", "price": 500, "key_item": True,
                       "desc": "旧王陵的入场钥匙(白鹿城铁匠铺购买)"},
    "i_key_crypt": {"name": "圣堂信物", "price": 300, "key_item": True,
                    "desc": "圣堂地窖的入场信物(晨曦城大教堂任务奖励)"},
    "i_key_elven": {"name": "精灵遗印", "price": 800, "key_item": True,
                    "desc": "精灵废墟的入场印记(翡翠森林精英掉落)"},
    "i_key_ash": {"name": "烬火令", "price": 1500, "key_item": True,
                  "desc": "烬山祭坛的入场令牌(烬山精英掉落)"},
    "i_key_abyss": {"name": "深渊钥匙", "price": 2000, "key_item": True,
                    "desc": "深渊裂隙的入场钥匙(深渊骑士掉落)"},
    "i_key_dragon_tomb": {"name": "龙牙信物", "price": 2000, "key_item": True,
                          "desc": "龙之墓的入场信物(龙脊山脉精英掉落)"},
    # F3 P1-2 修复：删除 4 把死数据钥匙（i_key_deer_fort 鹿角军旗/i_key_sunken 沉船湾船票/
    # i_key_sea_god 海神殿祷文/i_key_dragon_palace 龙宫宝珠）——v110.11 消歧改名后副本
    # key_item 回退材料名（军旗碎片/幽灵船票/海神祷文/龙宫珠），这 4 把 i_key 无发放源、
    # 无副本引用，纯死数据；钥匙体系以材料名为准（29 章 P0 闭环）
    "i_key_trial": {"name": "试炼令", "price": 400, "key_item": True,
                    "desc": "圣光试炼场的入场令牌(铁盾镇兵营任务奖励)"},
    "i_key_moon": {"name": "月辉钥匙", "price": 3000, "key_item": True,
                   "desc": "月神圣殿的入场钥匙(月冠王庭月市购买)"},
    "i_key_frost": {"name": "寒冰令", "price": 3500, "key_item": True,
                    "desc": "冰霜王座的入场令牌(永冻冰原精英掉落)"},
    "i_key_storm_throne": {"name": "雷光令", "price": 4000, "key_item": True,
                           "desc": "风暴王座的入场令牌(风暴崖精英掉落)"},
    "i_key_siren": {"name": "海妖鳞片信物", "price": 1200, "key_item": True,
                    "desc": "海妖巢穴的入场信物(海妖湾精英掉落)"},
    "i_key_gray_dwarf": {"name": "灰矮人通行令", "price": 2800, "key_item": True,
                         "desc": "灰矮人要塞的通行令(地底集市任务奖励)"},
    "i_key_under_dragon": {"name": "龙鳞钥匙", "price": 3000, "key_item": True,
                           "desc": "地底龙巢的入场钥匙(熔火深渊精英掉落)"},
    "i_key_eye_storm": {"name": "雷核钥匙", "price": 4500, "key_item": True,
                        "desc": "风暴之眼的入场钥匙(雷暴高原精英掉落)"},
    "i_key_abyss_throne": {"name": "深渊圣印", "price": 4500, "key_item": True,
                           "desc": "深渊王座的入场圣印(深渊祭坛精英掉落)"},
    "i_key_cloud": {"name": "云玺", "price": 5000, "key_item": True,
                    "desc": "云中圣殿的入场玉玺(星辉台精英掉落)"},
    # v95.32 #403 炼金配方数据断裂修复：3 个战斗药水/护符补全（alchemy.py 产出物）
    "i_atk_potion": {"cast": 1.4, "name": "攻击药水", "price": 325, "effect": "buff_atk",
                     "desc": "战斗中使用，攻击力 + 30%(3 刻)"},
    "i_crit_potion": {"cast": 1.4, "name": "暴击药水", "price": 250, "effect": "buff_crit",
                      "desc": "战斗中使用，暴击率 + 20%(3 刻)"},
    "i_lucky_charm": {"name": "幸运护符", "price": 300, "effect": "lucky",
                      "desc": "提升打怪金币与材料掉落(10 分钟)"},
    # ---- v102.3 生活技能差异化：稀有食谱产物（烹饪） ----
    "i_night_mushroom_soup": {"cast": 0.8, "name": "夜雾菇浓汤", "food": True, "price": 300, "food_effect": "regen", "heal": 0.3, "stamina": 25,
                              "desc": "回复 30% HP + 25 体力（月光珍馐）；战斗中吃下获得【回春】：每刻回复 1% 生命（本场）"},
    "i_moon_tea": {"cast": 1.0, "name": "月光草茶", "food": True, "price": 200, "food_effect": "meditate", "mana": 0.25, "stamina": 15,
                   "desc": "回复 25% MP + 15 体力（月下清茗）；战斗中喝下获得【冥想】：每刻回复 1% 魔力（本场）"},
    "i_aurora_honey": {"cast": 1.0, "name": "极光花蜜", "food": True, "price": 380, "food_effect": "aurora_guard", "heal": 0.2, "stamina": 20,
                       "desc": "回复 20% HP + 20 体力（极光珍酿）；战斗中吃下获得【极光庇护】：受击伤害－15%（本场战斗）"},
    "i_dragon_blood_hotpot": {"cast": 1.2, "name": "龙血火锅", "food": True, "price": 550, "food_effect": "charge", "heal": 0.4, "stamina": 40,
                              "desc": "回复 40% HP + 40 体力（猛火珍馐）；战斗中吃下获得【蓄力】：10% 追加 50% 伤害"},
    "i_thunder_skewer": {"cast": 1.0, "name": "雷雨藤烤串", "food": True, "price": 600, "food_effect": "static", "heal": 0.15, "stamina": 20,
                         "desc": "回复 15% HP + 20 体力（酥麻串烧）；战斗中吃下获得【静电麻痹】：攻击 20% 令敌减速"},
    # ---- v102.3 生活技能差异化：稀有药水产物（炼金） ----
    "i_moon_dew_essence": {"cast": 1.8, "name": "月露精华", "price": 450, "effect": "next_atk_up", "effect_data": {"pct": 0.5},
                           "desc": "战斗中使用，下一次攻击伤害 + 50%（月华凝露）"},
    "i_abyss_crystal_potion": {"cast": 2.0, "name": "深渊药剂", "price": 440, "effect": "magic_resist", "effect_data": {"pct": 0.15},
                               "desc": "战斗中使用，3 刻受到魔法伤害－15%（深渊幽蓝）"},
    "i_star_iron_agent": {"cast": 1.0, "name": "星铁强化剂", "price": 1200, "effect": "enhance_boost",
                          "desc": "使用后下一次强化装备必定成功（星火淬炼）"},
    # ---- v102.3 生活技能差异化：鱼饵（烹饪/炼金产出，垂钓品质加权） ----
    "it_glow_bait": {"name": "萤光鱼饵", "price": 110, "effect": "bait_glow",
                     "desc": "炼金调制的荧光饵料，幽光引鱼——下次垂钓紫/橙档概率大幅提升(仅 1 次)"},
    "it_dough_bait": {"name": "面团鱼饵", "price": 20, "effect": "bait_dough",
                      "desc": "揉得松软的麦粉饵团——下次垂钓绿/蓝档品质权重提升(仅 1 次)"},
    "it_blood_bait": {"name": "血饵", "price": 35, "effect": "bait_blood",
                      "desc": "浸透兽血的饵团，凶猛的掠食鱼最爱的味道——下次垂钓稀有鱼种概率提升(仅 1 次)"},
    # ============ v117 副本材料联动·方案D：符文匣（炼金配方原料：副本闲置材料） ============
    # 副本闲置材料（黑渊之眼/龙宫珠 等）经炼金配方合成符文匣 → 『使用』开出随机稀有/紫色符文，
    # 联动符文系统（open_rune_chest 模板，见 core/item_templates.py）。
    "i_hei_yuan_fu_wen_xiang": {"name": "黑渊符文匣", "price": 405, "type": "消耗品",
                                "effect": "open_rune_chest",
                                "rune_pool": "blue_purple",
                                "desc": "黑渊之眼封存的符文匣，匣缝溢出深渊的幽光——使用后随机获得一枚稀有/紫色符文"},
    "i_long_gong_fu_wen_xiang": {"name": "龙宫符文匣", "price": 415, "type": "消耗品",
                                 "effect": "open_rune_chest",
                                 "rune_pool": "blue_purple",
                                 "desc": "龙宫珠封存的符文匣，珠辉流转如水波——使用后随机获得一枚稀有/紫色符文"},
    # ============ v152 策略道具（鱼鱼拍板：战斗喝药有策略，使用耗时即战术） ============
    "i_emergency_salve": {"cast": 0.3, "name": "应急灵液", "price": 150, "type": "消耗品",
                          "heal": 0.15, "quality": "blue",
                          "desc": "瓶口一拧即饮的救命灵液，瞬发回复 15% 生命。几乎不耽误出手——但效果也弱，贵在安全"},
    "i_brutal_wine": {"cast": 2.5, "name": "蛮血烈酒", "price": 25, "type": "消耗品",
                      "effect": "next_atk_up", "effect_data": {"pct": 0.5},
                      "quality": "purple",
                      "desc": "饮下后血脉贲张：下次攻击 +50%。但喝药极慢（2.5 刻），期间敌方至少动 2 次——残血喝=找死，得提前规划"},
    "i_field_ration": {"cast": 1.0, "name": "行军用粮", "price": 40, "type": "消耗品",
                       "food": True, "hot": 0.06, "hot_turns": 5, "stamina": 30,
                       "quality": "green",
                       "desc": "军旅干粮，每刻回复 6% 生命持续 5 刻。持久战口粮，性价比高——但被控/被集火时喝不上"},
    "i_flash_powder": {"cast": 0.6, "name": "闪现粉", "price": 120, "type": "消耗品",
                       "effect": "buff_phys_next", "effect_data": {"pct": 0.4},
                       "quality": "purple",
                       "desc": "快动作撒粉（0.6 刻），下次物理攻击 +40%。抢出手的战术道具"},
    "i_ironwall_salve": {"cast": 1.8, "name": "铁壁药膏", "price": 160, "type": "消耗品",
                         "effect": "shield_big", "effect_data": {"pct": 0.30, "turns": 3},
                         "quality": "purple",
                         "desc": "厚涂铁壁药膏，获得最大生命 30% 护盾（3 刻）。涂抹慢（1.8 刻），Boss 大招前要算好提前量"},
    "i_antidote_pill": {"cast": 0.4, "name": "解毒丹", "price": 60, "type": "消耗品",
                        "effect": "cc_immune", "effect_data": {"turns": 3},
                        "quality": "blue",
                        "desc": "快速服下（0.4 刻），3 刻内免疫中毒/控制。解毒要快，慢悠悠吃药会多吃几跳伤害"},
}

# ================= 材料分类与品质（v101.25e 鱼鱼拍板：按类型分设施出售 + 全服通用品质） =================
# 类型关键词规则（顺序敏感：先匹配先得；越具体的词越靠前）
_MAT_TYPE_RULES = [
    ("宝石", ("宝石", "珍珠", "珠", "翡翠", "玛瑙", "水晶", "琥珀", "钻石", "玉髓")),
    ("食材", ("鱼", "肉", "虾", "蟹", "贝", "蛋", "果", "菜", "蔬", "米", "麦", "蜜", "腕足", "乳")),
    ("草药", ("草", "花", "根", "叶", "菇", "菌", "藤", "参", "芝", "芦")),
    ("木材", ("木", "枝", "树", "柴", "板")),
    ("织物", ("布", "丝", "棉", "麻", "绒", "绸", "线", "絮", "纱")),
    ("矿石", ("矿", "铁", "铜", "银", "金", "玉", "岩", "石", "砂", "锡", "铅", "钢", "锭")),
    ("兽材", ("皮", "毛", "牙", "角", "骨", "爪", "羽", "壳", "鳞", "蹄", "尾", "血", "鬃", "甲", "铠")),
    ("精华", ("核", "粉", "液", "精华", "魂", "尘", "灰", "烬", "泪", "露", "晶", "髓", "涎", "浆", "息")),
]
_MAT_TYPE_FALLBACK = "杂物"


def _mat_type(name: str) -> str:
    """材料类型（按名字关键词；无命中 → 杂物）"""
    for _t, _kws in _MAT_TYPE_RULES:
        if any(_k in name for _k in _kws):
            return _t
    return _MAT_TYPE_FALLBACK


def _mat_quality(price: int) -> str:
    """材料品质（全服通用白绿蓝紫橙，按价格分档）"""
    if price <= 12:
        return "white"
    if price <= 30:
        return "green"
    if price <= 60:
        return "blue"
    if price <= 120:
        return "purple"
    return "orange"


from .fishing import FISH_POOL as _FISH_POOL  # v124：渔获 type 权威来源（防双处定义漂移）
_FISH_TYPE_BY_NAME = {_f["name"]: _f["type"] for _f in _FISH_POOL}

for _mid, _m in MATERIALS.items():
    # v124：垂钓鱼 type 一律以 FISH_POOL 为准（_settle_fishing 入包即 fish["type"]，与
    # data/__init__.py 启动校验一致）；其余材料：已有（收藏/传说/任务道具）保留；
    # "材料"占位或无 → 按名规则重算
    _fish_t = _FISH_TYPE_BY_NAME.get(_m.get("name"))
    if _fish_t:
        _m["type"] = _fish_t
    elif not _m.get("type") or _m.get("type") == "材料":
        _m["type"] = _mat_type(_m["name"])
    # quality：已有（收藏品等）保留；无 → 按价格分档
    if not _m.get("quality"):
        _m["quality"] = _mat_quality(_m["price"])

# ===== v165 材料分阶段定价覆盖（2026-09-02 鱼鱼拍板，economy_lib 模型推导）=====
# 有怪物掉落的材料按产出等级带涨价（价格带 5~395），无怪掉落(采集/商店料)保持。
# 修复观感：高级怪不再掉 5-15 元低价料 ×几十个（星辉尘 Lv93→355 等）。
# v173 问题B 补丁：4 个副本通关 Boss 级材料价倒挂（v165 漏网——副本材料无怪物等级，
# 原 5-15 元白档 < 同副本小怪料 25-35 元；按副本产出等级带对齐：
#   海蚀洞窟 Lv22→E2 档 35；旧王陵 Lv35/圣堂地窖 Lv42→E3 档 90；沉船湾 Lv38→120（对齐幽灵船票 120））
MATERIAL_PRICE_OVERRIDE = {
    "mat_cao_yao": 10,
    "mat_ge_bu_lin_hui_ji": 10,
    "mat_feng_zhen": 10,
    "mat_xi_lu_pi": 10,
    "mat_gu_mu_zhi": 10,
    "mat_ge_bu_lin_tie_pian": 10,
    "mat_shan_yang_jiao": 10,
    "mat_sa_man_tu_teng": 15,
    "mat_xi_xi_lin": 15,
    "mat_da_shi_lai_mu_he": 15,
    "mat_e_yu_pi": 15,
    "mat_tu_pi": 15,
    "mat_kuang_zhan_shi_yao_dai": 15,
    "mat_hai_yan_jie_jing": 25,
    "mat_fu_yi": 25,
    "mat_hai_yao_lin_pian": 25,
    "mat_yan_xi_lin": 25,
    "mat_shan_zei_hui_zhang": 25,
    "mat_jing_rui_pei_jian": 35,
    "mat_shui_jing_ling_lei": 35,
    "mat_hai_ou_yu_mao": 35,
    "mat_niu_jiao": 35,
    "mat_he_long_lin": 50,
    "mat_qiu_ling_lang_pi": 50,
    "mat_sheng_guang_jie_jing": 50,
    "mat_sheng_dian_tie_kuai": 50,
    "mat_dao_zei_mian_jin": 50,
    "mat_qi_shi_hui_ji": 50,
    "mat_sui_gu": 50,
    "mat_tie_jia_zhu_pi": 50,
    "mat_an_ying_hui_ji": 65,
    "mat_ran_hei_mei_gui": 65,
    "mat_mo_xiang_he_xin": 65,
    "mat_tu_jiu_yu": 65,
    "mat_you_ling_zhi_chen": 65,
    "mat_fu_rou": 65,
    "mat_shu_shi_he_xin": 65,
    "mat_hai_xing_pian": 65,
    "mat_xie_ke": 65,
    "mat_you_hun_chen": 65,
    "mat_jiao_guan_zhi_jian": 65,
    "mat_ran_hei_sheng_ling": 65,
    "mat_cao_yuan_lang_pi": 65,
    "mat_ran_hei_sheng_dian": 80,
    "mat_he_tun_du_su": 80,
    "mat_hai_zao_chan_rao": 80,
    "mat_mo_xiang_can_he": 80,
    "mat_lie_quan_xiang_quan": 80,
    "mat_lie_xi_pi": 80,
    "mat_shou_ren_fu_ren": 100,
    "mat_dao_zhu_ya": 100,
    "mat_jing_ling_lu_jiao": 100,
    "mat_hai_yao_lin": 100,
    "mat_cui_lu_jiao": 100,
    "mat_jin_yan_hu_pi": 100,
    "mat_jiao_ren_lin": 100,
    "mat_zhan_zheng_ji_qi_ling_jian": 100,
    "mat_ying_wu_yu": 100,
    "mat_yue_lang_mao_pi": 100,
    "mat_hu_yao_lei": 100,
    "mat_gu_di_lu_shui": 100,
    "mat_feng_yu_lu_jiao": 100,
    "mat_xuan_wo_lei": 120,
    "mat_feng_bao_he_xin": 120,
    "mat_hai_yao_zhi_yu": 120,
    "mat_feng_yu_jie_jing": 120,
    "mat_lv_lu_jiao": 120,
    "mat_yue_lu_jiao": 120,
    "mat_shou_ren_zhan_hui": 120,
    "mat_gu_shu_zhi_xin": 120,
    "mat_ying_bao_pi": 120,
    "mat_shui_jing_ling_lin": 120,
    "mat_chu_shou_pi": 120,
    "mat_ju_ying_yu": 145,
    "mat_yue_ying_zhi_zhao": 145,
    "mat_yue_xiong_pi": 145,
    "mat_yue_ying_zhi_pi": 145,
    "mat_mo_shui_ping": 145,
    "mat_jiu_shu_can_ye": 145,
    "mat_duo_luo_jing_ling_hu_fu": 145,
    "mat_ju_lu_yu_gu": 145,
    "mat_sha_yu_ya": 145,
    "mat_yao_jing_zhi_chen": 145,
    "mat_tui_se_mo_shui": 145,
    "mat_shui_mu_ning_jiao": 145,
    "mat_yue_guang_jing_hua": 145,
    "mat_ying_guang_hu_wei": 145,
    "mat_hu_wang_zhu": 170,
    "mat_wu_zei_wan_zu": 170,
    "mat_zhang_yu_mo_nang": 170,
    "mat_zhi_zhu_si": 170,
    "mat_xue_lang_pi": 170,
    "mat_yue_hui_sui_pian": 170,
    "mat_zhi_zhu_du_nang": 170,
    "mat_xue_zhi_jing_hua": 170,
    "mat_long_jing_zhi": 170,
    "mat_jian_chi_hu_ya": 170,
    "mat_yuan_gu_fu_wen_shi": 170,
    "mat_an_ying_jing_ling_ren": 170,
    "mat_shui_shou_gu_pai": 170,
    "mat_hai_shen_ji_qi": 170,
    "mat_bing_yuan_su_he_xin": 170,
    "mat_you_ling_fan_bu": 170,
    "mat_hai_she_lin": 195,
    "mat_chao_xi_sui_pian": 195,
    "mat_huo_xi_yi_lin": 195,
    "mat_meng_ma_mao": 195,
    "mat_huo_yan_he_xin": 195,
    "mat_shou_wei_gu_mu": 195,
    "mat_jia_ke_can_pian": 195,
    "mat_lei_man_pi": 195,
    "mat_bing_xiong_pi": 195,
    "mat_feng_bao_zhi_ling_chen": 195,
    "mat_zhen_jun_rou": 195,
    "mat_chuan_zhang_luo_pan": 195,
    "mat_xue_tu_pi": 195,
    "mat_shuang_ju_mo_xue": 195,
    "mat_bao_zi_nang": 195,
    "mat_hu_bing_he_xin": 195,
    "mat_rong_yan_he_xin": 195,
    "mat_shan_hu_zhi": 195,
    "mat_ling_zhu_gu_mu_xin": 195,
    "mat_rong_yan_shi": 195,
    "mat_rong_huo_jing_tie": 195,
    "mat_bing_lang_ya": 225,
    "mat_bing_she_lin": 225,
    "mat_shen_hai_qi_shi_jia": 225,
    "mat_fu_ya_shou_ya": 225,
    "mat_hai_ju_ren_lin": 225,
    "mat_dong_yu_lin": 225,
    "mat_ying_guang_fen": 225,
    "mat_kuang_mo_zhi_jiao": 225,
    "mat_long_xia_ke": 225,
    "mat_ju_gui_jia": 225,
    "mat_mang_yu_lin": 225,
    "mat_shuang_yu_sheng_dian": 225,
    "mat_hei_an_jing_ling_ren": 225,
    "mat_ji_guang_hu_wei": 255,
    "mat_xiao_e_mo_jiao": 255,
    "mat_ji_xie_ling_jian": 255,
    "mat_hu_ling_lei": 255,
    "mat_hui_ai_ren_hui_ji": 255,
    "mat_yong_dong_zhi_he": 255,
    "mat_yuan_ling_zhi_chen": 255,
    "mat_fu_shi_shou_zhao": 255,
    "mat_shuang_yu_ju_mo_xue": 255,
    "mat_ling_hun_sui_pian": 255,
    "mat_di_di_e_mo_jiao": 255,
    "mat_di_yu_quan_ya": 285,
    "mat_rong_yan_ru_chong_pi": 285,
    "mat_long_lin_shou_cang": 285,
    "mat_long_lin_sui_pian": 285,
    "mat_ran_xue_ji_qi": 285,
    "mat_shuang_ya_long_lin": 285,
    "mat_gu_chong_ke": 285,
    "mat_hei_yao_sui_pian": 285,
    "mat_nu_pu_suo_lian": 285,
    "mat_long_yan_jing_hua": 285,
    "mat_e_mo_zhan_ren": 320,
    "mat_shi_long_lin": 320,
    "mat_xun_meng_long_zhao": 320,
    "mat_di_di_long_lin": 320,
    "mat_feng_long_yu": 320,
    "mat_yu_jin_jia_pian": 320,
    "mat_yan_long_lin": 320,
    "mat_zhan_hun_zhi_chen": 320,
    "mat_sui_lie_feng_yin_shi": 320,
    "mat_jin_lang_ya": 320,
    "mat_shao_jiao_jian_ren": 320,
    "mat_gu_long_yi_jia": 320,
    "mat_rong_yan_jia_ke": 320,
    "mat_xiu_jian_sui_pian": 320,
    "mat_lei_xi_pi": 320,
    "mat_feng_zhi_yu": 320,
    "mat_feng_bao_ying_yu": 320,
    "mat_yun_xu": 320,
    "mat_gu_mo_xiang_he": 320,
    "mat_yan_jiang_ru_chong_pi": 320,
    "mat_ran_xue_sheng_dian": 320,
    "mat_xu_kong_quan_ya": 320,
    "mat_long_zai_zhao": 320,
    "mat_long_yi_can_hun": 320,
    "mat_chi_yi_yu": 320,
    "mat_gu_jiu_yu": 320,
    "mat_gu_long_can_hai": 320,
    "mat_you_long_lin": 355,
    "mat_cai_hong_lu": 355,
    "mat_tian_ying_yu": 355,
    "mat_shu_shi_fa_zhang": 355,
    "mat_huo_fu_yi": 355,
    "mat_lei_jing": 355,
    "mat_feng_bao_shou_pi": 355,
    "mat_long_hun_sui_pian": 355,
    "mat_yun_xiong_mao": 355,
    "mat_feng_zhi_he_xin": 355,
    "mat_xing_hui_chen": 355,
    "mat_can_hai_he_xin": 355,
    "mat_shen_yuan_shou_wei_jia": 355,
    "mat_tian_kong_zhan_ren": 355,
    "mat_shen_pan_guan_zhi_lian": 355,
    "mat_shen_yuan_e_mo_jiao": 355,
    "mat_cai_hong_lin": 355,
    "mat_cheng_nian_long_lin": 355,
    "mat_xing_lang_pi": 355,
    "mat_long_lin_shou_pi": 355,
    "mat_shou_wei_kai_jia_sui_pian": 355,
    "mat_shen_yuan_qi_shi_kui_jia_sui_pian": 355,
    "mat_feng_bao_zhi_he": 355,
    "mat_yun_dian_kai_jia": 395,
    "mat_gu_long_lin": 395,
    "mat_shen_yuan_fa_shi_zhang": 395,
    "mat_shen_yuan_quan_ya": 395,
    "mat_lei_niao_yu": 395,
    "mat_yun_xing_he": 395,
    "mat_guang_zhi_sheng_dian": 395,
    # ---- v173 问题B 倒挂材料价对齐（Boss 级通关材料价 ≥ 同副本小怪料带，见上方注释）----
    "mat_jie_ke_de_jin_gou": 35,
    "mat_gu_wang_jian": 90,
    "mat_ma_er_ku_si_de_fa_guan": 90,
    "mat_ke_luo_de_luo_pan": 120,
}

_PRICE_SPECIAL_TYPES = {"收藏", "传说", "任务道具", "收藏品", "图纸"}
for _mid, _m in MATERIALS.items():
    if _mid in MATERIAL_PRICE_OVERRIDE:
        _m["price"] = MATERIAL_PRICE_OVERRIDE[_mid]
        if _m.get("type") not in _PRICE_SPECIAL_TYPES:
            _m["quality"] = _mat_quality(_m["price"])
# ===== /v165 材料价格覆盖 =====

# 材料按名索引（背包显示/出售设施匹配用）
# ================= 材料描述生成（v101.25g 鱼鱼：物品详情要有描述） =================
# 手写 desc 优先保留；缺省按类型/子关键词模板生成（确定性哈希选变体）
import hashlib as _hashlib

_MAT_DESC_RULES = {
    "兽材": {
        ("皮",): ["{name}，质地坚韧的兽皮，缝制护甲的上等材料。", "{name}，带着体温的皮革，铁匠铺常年收购。", "{name}，厚实耐用的皮毛，鞣制后能做护具内衬。"],
        ("毛", "鬃"): ["{name}，柔软蓬松的兽毛，填充护具能抵御寒风。", "{name}，粗硬的鬃毛，搓成绳索结实耐用。"],
        ("牙", "獠牙"): ["{name}，锋利的兽牙，可打磨成武器配件或饰品。", "{name}，泛着寒光的獠牙，是猎人的战利品。"],
        ("角",): ["{name}，坚硬有光泽的兽角，锻造与工艺的上佳材料。", "{name}，螺旋状的兽角，磨成粉末可入药。"],
        ("骨",): ["{name}，打磨光滑的兽骨，可雕刻成骨饰或工具柄。", "{name}，粗壮的兽骨，敲碎后髓质可提炼精华。"],
        ("爪",): ["{name}，弯钩般的兽爪，锋利程度不输刀刃。", "{name}，坚硬锐利的兽爪，镶嵌在武器上可增杀伤。"],
        ("羽",): ["{name}，色泽鲜亮的羽毛，箭矢尾羽的首选。", "{name}，轻盈柔韧的飞羽，风系附魔常用材料。"],
        ("壳",): ["{name}，坚硬厚实的甲壳，天然的保护材料。", "{name}，泛着光泽的甲壳，磨碎后是炼金原料。"],
        ("鳞",): ["{name}，细密交错的鳞片，防御与装饰两相宜。", "{name}，覆着微光的鳞片，水火不侵的天然护材。"],
        ("蹄",): ["{name}，厚实的兽蹄甲，耐磨程度超乎想象。", "{name}，结实的蹄甲，能加工成纽扣或小配件。"],
        ("尾",): ["{name}，柔韧的兽尾，编织后是上好的绳索。", "{name}，带着独特气息的尾毛，炼金师偶尔会用到。"],
        ("血",): ["{name}，腥气未散的兽血，炼金术的常用媒介。", "{name}，殷红的兽血，蕴含着一丝野性力量。"],
    },
    "食材": {
        ("鱼",): ["{name}，鲜活肥美的河鲜，烤一烤就香气四溢。", "{name}，鳞片银亮的鲜鱼，是酒馆菜单的常客。", "{name}，肉质细嫩的鱼，煮汤清甜可口。"],
        ("肉",): ["{name}，新鲜宰割的兽肉，篝火上一烤滋滋冒油。", "{name}，纹理分明的肉块，是冒险者的能量来源。"],
        ("蛋",): ["{name}，温润的禽蛋，煎炒蒸煮样样皆宜。", "{name}，个头饱满的蛋，敲开是金黄的蛋液。"],
        ("果",): ["{name}，饱满多汁的野果，酸甜解渴。", "{name}，挂在枝头的成熟果实，补充体力的小零嘴。"],
        ("菜", "蔬"): ["{name}，水灵灵的新鲜蔬菜，炊事兵的宝贝。", "{name}，带着泥土气息的野菜，洗净就能下锅。"],
        ("米", "麦"): ["{name}，颗粒饱满的谷物，磨成粉是主食来源。", "{name}，金黄的麦穗，烘烤后有麦芽的甜香。"],
        ("蜜",): ["{name}，金黄透亮的蜂蜜，甜到心坎里。", "{name}，野蜂巢里淌出的蜜露，滋补又美味。"],
        ("乳",): ["{name}，新鲜温热的奶，牧民家最朴实的馈赠。", "{name}，奶香浓郁的乳汁，发酵后别有风味。"],
        ("虾", "蟹", "贝", "腕足"): ["{name}，带着海水咸鲜的甲壳鲜物，清蒸最是原味。", "{name}，壳硬肉肥的海产，渔港最爱的下酒菜。"],
    },
    "草药": {
        ("草",): ["{name}，带着晨露的草药，叶片揉碎有清香。", "{name}，路旁常见的药草，晒干后能久存。"],
        ("花",): ["{name}，花瓣娇艳的花朵，入药有安神之效。", "{name}，香气袭人的花，晒干泡茶别有一番风味。"],
        ("根",): ["{name}，须根繁茂的药根，苦味入药最见效。", "{name}，粗壮有力的根茎，切片晒干是常用药材。"],
        ("叶",): ["{name}，肥厚翠绿的叶片，捣碎外敷能止血。", "{name}，脉络清晰的叶子，煮水有清热的功效。"],
        ("菇", "菌"): ["{name}，雨后冒出的菌菇，伞盖饱满肉质厚。", "{name}，躲藏在腐木下的蘑菇，小心甄别才能入菜。"],
        ("藤",): ["{name}，攀援缠绕的藤蔓，柔韧程度胜过绳索。", "{name}，表皮粗糙的老藤，蕴含丰富的汁液。"],
        ("参", "芝"): ["{name}，形如人形的珍贵药材，补气养元的佳品。", "{name}，菌盖上泛着光泽的灵芝，可遇不可求。"],
        ("芦",): ["{name}，青翠多汁的芦草，汁液清凉解毒。", "{name}，叶鞘肥厚的芦草，捣汁可外敷消肿。"],
    },
    "矿石": {
        ("矿", "岩", "石"): ["{name}，沉甸甸的矿石，敲开有闪烁的矿脉。", "{name}，边缘锋利的岩块，是锻造的原料基石。", "{name}，粗糙的矿石表面，隐约可见金属光泽。"],
        ("铁", "钢", "锭"): ["{name}，乌黑的铁锭，锻造台上叮当作响。", "{name}，淬炼过的金属块，是打造武器的骨干。"],
        ("铜", "锡", "铅"): ["{name}，泛着暗红的金属块，延展性极好。", "{name}，质地柔软的金属，新手铁匠的练习材料。"],
        ("银", "金"): ["{name}，泛着贵气光泽的金属，打磨后耀眼夺目。", "{name}，价值不菲的贵金属，珠宝匠人的心头好。"],
        ("玉", "砂"): ["{name}，温润细腻的玉料，雕刻成饰品价值倍增。", "{name}，颗粒均匀的矿砂，淘洗后可得精矿。"],
    },
    "木材": {
        ("木", "树"): ["{name}，纹理细密的木材，敲击有清脆的回响。", "{name}，年轮清晰的木料，烘干后不易变形。"],
        ("枝", "柴"): ["{name}，干爽的树枝，篝火的完美燃料。", "{name}，劈好的柴火，营地过夜全靠它。"],
        ("板",): ["{name}，刨平的好木板，木匠的必备料。", "{name}，厚薄均匀的木板，做箱做盾都合适。"],
    },
    "织物": {
        ("布",): ["{name}，织法细密的布料，缝缝补补的日常材料。", "{name}，手感柔软的棉布，裁衣做包皆可。"],
        ("丝", "绸"): ["{name}，光滑如水的丝绸，贵族才用得起的料子。", "{name}，泛着珠光的丝线织物，高级时装的灵魂。"],
        ("棉", "麻"): ["{name}，透气吸汗的麻布，远行者的首选。", "{name}，蓬松洁白的棉絮，保暖填充两相宜。"],
        ("绒", "线", "絮", "纱"): ["{name}，细软蓬松的绒料，冬天最暖和的里衬。", "{name}，捻得均匀的纱线，织布绣花都能用。"],
    },
    "宝石": {
        ("宝石", "水晶"): ["{name}，折射着光芒的晶体，镶嵌在首饰上璀璨夺目。", "{name}，晶莹剔透的水晶，蕴藏着纯粹的元素之力。"],
        ("珍珠", "珠"): ["{name}，圆润饱满的珍珠，贝母日积月累的馈赠。", "{name}，泛着柔和光泽的珠子，串成项链价值不菲。"],
        ("翡翠", "玛瑙", "琥珀", "钻石", "玉髓"): ["{name}，色泽温润的宝石，工匠手中的点睛之石。", "{name}，坚硬罕见的宝石，是身份与财富的象征。"],
    },
    "精华": {
        ("粉", "尘", "灰", "烬"): ["{name}，细腻如雪的粉末，炼金锅里咕嘟冒泡的常客。", "{name}，泛着微光的粉尘，附着着淡淡的魔力。"],
        ("液", "涎", "浆", "露", "泪"): ["{name}，装在瓶里晃荡的液体，气味奇异但很值钱。", "{name}，黏稠的浆液，炼金师视若珍宝。"],
        ("核", "晶", "髓"): ["{name}，凝聚着能量的核心，魔导器运转的燃料。", "{name}，散发着微光的晶核，蕴含着浓缩的力量。"],
        ("魂", "息", "精华"): ["{name}，带着神秘气息的精华，触碰时有微弱的共鸣。", "{name}，凝而不散的精华，是高级炼金的核心材料。"],
    },
    "杂物": [("{name}，看起来平平无奇，说不定在哪能派上用场。",), ("{name}，路边捡到的小物件，商贩们愿意收下。",), ("{name}，说不清来历的小东西，留着总没错。",), ("{name}，常见的小杂物，积少成多也是一笔收入。",)],
    "收藏": [("{name}，颇具纪念意义的藏品，收藏家愿意出高价。",)],
    "传说": [("{name}，传闻中才存在的至宝，价值无法估量。",)],
    "任务道具": [("{name}，与某个任务息息相关，最好随身携带。",)],
}
_MAT_DESC_FALLBACK = ["{name}，看似普通，却有它独到的用处。", "{name}，冒险路上常见的小材料，别小看它。"]


def _gen_mat_desc(name: str, mtype: str) -> str:
    rules = _MAT_DESC_RULES.get(mtype)
    if not rules:
        return _pick_desc(name, _MAT_DESC_FALLBACK).format(name=name)
    # 子关键词优先（取最长命中）
    best = None
    if isinstance(rules, dict):
        for kws, variants in rules.items():
            if isinstance(variants, tuple) and len(variants) == 1 and isinstance(variants[0], str):
                variants = [variants[0]]
            if any(k in name for k in kws):
                if best is None or len(kws[0]) > len(best[0]):
                    best = (kws, variants)
        if best:
            return _pick_desc(name, best[1]).format(name=name)
        # 类型级兜底
        all_v = [v for kws, v in rules.items() for v in v]
        if all_v:
            return _pick_desc(name, all_v).format(name=name)
    else:
        return _pick_desc(name, [v[0] if isinstance(v, tuple) else v for v in rules]).format(name=name)
    return _pick_desc(name, _MAT_DESC_FALLBACK).format(name=name)


def _pick_desc(name: str, variants) -> str:
    _h = int(_hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    return variants[_h % len(variants)]


# ================= v124 支线扩容：9 件缺失物品补登记（2026-08-16，S108/S111-S114/S116/S119/H7/H8） =================
# 名称与 quests.py 注释严格一致（reward_item/collect/use 按名 resolve("materials") 引用，必须挂在 MATERIALS）
# S51 长夜徽记 / S95 传说钓竿·银铃之竿：真实装备已登记 equip_roster（eq_chang_ye_hui_ji / eq_chuan_shuo_diao_gan，
# 任务经 eq: 前缀发放），原收藏占位条目已删除
MATERIALS.update({
    # ---- H7 候鸟的信：候鸟的信（hq7_1 湖心的来信·任务道具）----
    "mat_hou_niao_de_xin": {"price": 30, "name": "候鸟的信", "type": "任务道具",
        "desc": "灰羽候鸟·翎信叼来的旧信——三百年前英雄王·艾德里克写给星语湖畔恋人的诀别信(H7 任务道具)"},
    # ---- H8 熔炉之心：先祖碑石碎片（hq8_2 塌方下的锻炉·任务道具×3）----
    "mat_xian_zu_bei_shi_sui_pian": {"price": 30, "name": "先祖碑石碎片", "type": "任务道具",
        "desc": "先祖锻炉炉底散落的碑石碎片，刻满古矮人符文——「地火三锻」的记载(H8 任务道具×3)"},
    # ---- S108 一封迟了二十年的信：和解信（任务道具）----
    "mat_he_jie_xin": {"price": 30, "name": "和解信", "type": "任务道具",
        "desc": "老橡写给橡木镇镇长·霍布斯的信——二十年倔脾气，一坛酒来化(S108 任务道具)"},
    # ---- S116 等了五十七年的哨声：旧银哨（任务道具）----
    "mat_jiu_yin_shao": {"price": 30, "name": "旧银哨", "type": "任务道具",
        "desc": "湖心岛银叶树下埋了五十七年的银哨——两支哨子一起响，风会把话带给彼此(S116 任务道具)"},
    # ---- S114 河神的银铃：河神银铃（任务道具）----
    "mat_he_shen_yin_ling": {"price": 30, "name": "河神银铃", "type": "任务道具",
        "desc": "银铃河上游洞穴中寻回的河神银铃——铃一响，鱼汛就来(S114 任务道具)"},
    # ---- S112 烛影密信：王室密信（任务道具）----
    "mat_wang_shi_mi_xin": {"price": 30, "name": "王室密信", "type": "任务道具",
        "desc": "盖着王室印信的信，被灰羽鸟叼进大教堂——御前会议前必须寻回(S112 任务道具)"},
    # ---- S113 烛火不熄：蜂蜡（材料）----
    "mat_feng_la": {"price": 10, "name": "蜂蜡", "type": "材料",
        "desc": "野蜂酿的蜂蜡，白石修道院圣光节圣烛的原料(S113 材料)"},
    # ---- S111 面包贼蓬尾：被偷的面包（任务道具）----
    "mat_bei_tou_de_mian_bao": {"price": 5, "name": "被偷的面包", "type": "任务道具",
        "desc": "被松鼠「蓬尾」拖进藏粮树洞的白面包，码得整整齐齐(S111 任务道具)"},
    # ---- S119 雏龙不识归途：龙哨（任务道具）----
    "mat_long_shao": {"price": 30, "name": "龙哨", "type": "任务道具",
        "desc": "雏龙·烬鳞母亲蜕下的鳞片磨成的哨子——吹响三声，烬鳞循声而归(S119 任务道具)"},
})

# v172 装备重锻（怪猎派生树，原 v136 装备进化）：同系列旧武器 + 稀有素材 → 高阶武器。
# 重锻链源装备名（REFINE_RECIPES 的 key）→ 名册旧装备；重锻派生 / 怪异炼成消耗。
# 语义：v172 起命令/文案全部改『重锻』（evolve 词留给转职），素材 desc 同步。
MATERIALS.update({
    # ---- 血誓之源：血誓战团 Boss 怨念物（血誓战剑重锻原料）----
    "mat_xue_shi_zhi_yuan": {"price": 300, "name": "血誓之源", "type": "精华", "quality": "purple",
        "desc": "血誓战团长·血誓的心脏结晶，跳动着不灭的战誓(Boss 稀有素材，装备重锻/怪异炼成消耗)"},
    # ---- 余烬核心：灰烬军团 Boss 怨念物（血誓战剑→余烬军团战剑 重锻原料 / 怪异炼成通用消耗）----
    "mat_yu_jin_he_xin": {"price": 400, "name": "余烬核心", "type": "精华", "quality": "orange",
        "desc": "灰烬军团长的核心，灼热不灭，蕴含整支军团的战意(Boss 稀有素材，装备重锻/怪异炼成消耗)"},
    # ---- 夜祷之心：夜祷祭司 Boss 怨念物（日冕权杖→夜祷权杖 重锻原料）----
    "mat_ye_dao_zhi_xin": {"price": 350, "name": "夜祷之心", "type": "精华", "quality": "purple",
        "desc": "夜祷祭司的圣物，浸透午夜祈祷的幽蓝微光(Boss 稀有素材，装备重锻消耗)"},
})

# ================= v140 波3.5：任务专属材料 + 图纸/工具实体（2026-08-30） =================
# 3 种任务专属材料定义见 quest_add_v140.py::QUEST_MAT（q3_3 潮汐黑铁 / q7_3 月辉精魄 / q9_4 烬核火种），
# 仅任务可得、用于传说锻造；按名 resolve("materials") 发放 → 必须挂 MATERIALS，与 QUEST_MAT 字段一致。
MATERIALS.update({
    "mat_tide_blackiron": {
        "name": "潮汐黑铁", "type": "材料", "quality": "blue",
        "price": 300,
        "desc": "独眼杰克的旗舰龙骨下压着的深海黑铁，被潮汐淬炼了百年——传说锻造「海神之怒·潮汐」的基石材料（仅任务可得）",
    },
    "mat_moonlight_essence": {
        "name": "月辉精魄", "type": "材料", "quality": "purple",
        "price": 600,
        "desc": "星语湖王消散时留下的月辉结晶，倒映着湖底古老的星图——传说锻造「星辉之缚·苍穹」的基石材料（仅任务可得）",
    },
    "mat_ember_seed": {
        "name": "烬核火种", "type": "材料", "quality": "orange",
        "price": 1500,
        "desc": "赫尔加仪式炉中未燃尽的火种，仍跳动着烬山的余温——传说锻造「灰烬圣剑·初火」的基石材料（仅任务可得）",
    },
})

# ================= v140 波3.5：5 种图纸/工具实体（2026-08-30） =================
# q3_3 金钩弯刀图纸（金钩弯刀=eq_jin_gou_wan_dao 橙 Lv26 铁港系列，equip_roster 已登记）／
# q9_3 赫尔加的祭器图纸（eq_he_er_jia_de_ji_qi 橙 Lv72 霜狼系列）／q8_6 破甲符文（紫符文，同 s17 符文奖励先例）／
# q10_6 幸运宝石（对照 v136 宝石体系：装备孔位镶嵌提升暴击率）／银铃之竿（v124 垂钓线纪念，对照钓竿工具）。
MATERIALS.update({
    # ---- 金钩弯刀图纸：海盗王·独眼杰克专属武器图纸（q3_3 主线奖励）----
    "mat_bp_jin_gou_wan_dao": {
        'price': 200, 'name': "金钩弯刀图纸", 'type': "图纸",
        'blueprint_for': "金钩弯刀", 'roster_id': "eq_jin_gou_wan_dao",
        'desc': "海盗王独眼杰克的弯刀锻造图纸，学习后可锻造【金钩弯刀】(Lv.26 橙武，铁港系列)",
    },
    # ---- 赫尔加的祭器图纸：恶魔祭司·赫尔加专属祭器图纸（q9_3 主线奖励）----
    "mat_bp_he_jia_de_ji_qi": {
        'price': 300, 'name': "赫尔加的祭器图纸", 'type': "图纸",
        'blueprint_for': "赫尔加的祭器", 'roster_id': "eq_he_er_jia_de_ji_qi",
        'desc': "烬山祭坛恶魔祭司赫尔加的祭器锻造图纸，学习后可锻造【赫尔加的祭器】(Lv.72 橙项链，霜狼系列)",
    },
    # ---- 破甲符文：紫符文（q8_6 战歌·Lv.62 档主线奖励；符文掉落先例见 s17 随机符文）----
    "mat_po_jia_fu_wen": {
        "price": 400, "name": "破甲符文", "type": "符文", "quality": "purple",
        "desc": "战歌中铭刻的破甲符文，附魔后攻击可无视部分防御",
    },
    # ---- 幸运宝石：宝石（q10_6 最后的拥抱·Lv.88 档主线奖励；对照 v136 宝石体系嵌入孔位）----
    "mat_xing_yun_bao_shi": {
        "price": 500, "name": "幸运宝石", "type": "宝石", "quality": "purple",
        "desc": "蕴含好运的宝石，可嵌入装备孔位提升暴击率",
    },
    # ---- 传说钓竿·银铃之竿：工具（v124 垂钓线传说钓竿，对照钓竿工具格式；真装备 eq_chuan_shuo_diao_gan 已登记名册）----
    "mat_chuan_shuo_diao_gan_yin_ling": {
        "price": 800, "name": "传说钓竿·银铃之竿", "type": "工具", "quality": "orange",
        "desc": "垂钓传说档极稀有的银铃钓竿，愿者上钩——垂钓者的眷顾，掉落收益提升",
    },
    # ---- 灰影狼牙刃图纸：狼王·灰影专属武器图纸（q2_3 主线奖励；craft.py 无 blueprint 引用，纯任务奖励）----
    "mat_bp_hui_ying_lang_ya_ren": {
        'price': 150, 'name': "灰影狼牙刃图纸", 'type': "图纸",
        'blueprint_for': "灰影狼牙刃", 'roster_id': "eq_hui_ying_lang_ya_ren",
        'desc': "狼王·灰影的獠牙磨成的短刃锻造图纸，学习后可锻造【灰影狼牙刃】(Lv.14 紫匕首，铁牙系列)",
    },
    # ---- 古王剑图纸：古王·奥德里克陪葬王剑图纸（q6_2 主线奖励；craft.py blueprint 引用同名配方）----
    "mat_bp_gu_wang_jian": {
        'price': 260, 'name': "古王剑图纸", 'type': "图纸",
        'blueprint_for': "古王剑", 'roster_id': "eq_gu_wang_jian",
        'desc': "古王·奥德里克陪葬王剑的锻造图纸，学习后可锻造【古王剑】(Lv.42 橙剑，圣光系列)",
    },
    # ---- 蚀夜之面图纸：蚀夜（真相形态）暗影面具图纸（q12_2 主线奖励；craft.py 无引用，纯任务奖励）----
    "mat_bp_shi_ye_zhi_mian": {
        'price': 380, 'name': "蚀夜之面图纸", 'type': "图纸",
        'blueprint_for': "蚀夜之面", 'roster_id': "eq_shi_ye_zhi_mian",
        'desc': "蚀夜褪下的暗影面具锻造图纸，学习后可锻造【蚀夜之面】(Lv.98 橙头盔，影纱系列)",
    },
})

# ================= 材料 desc 注入（v101.25g，手写优先） =================
for _mid, _m in MATERIALS.items():
    if not _m.get("desc"):
        _m["desc"] = _gen_mat_desc(_m["name"], _m.get("type", "杂物"))

MATERIALS_BY_NAME = {_m["name"]: _m for _m in MATERIALS.values()}

# 其余 ITEMS（消耗品/装备材料等）后续阶段补充，当前仅材料
ITEMS = dict(MATERIALS)
ITEMS.update(CONSUMABLES)

# ================= v101.30 阶段四：高级钓点材料药水/料理（炼金/烹饪配方消费点，全部复用已有 effect 键） =================
ITEMS.update({
    "i_pearl_tonic": {"name": "珍珠明目水", "price": 100, "effect": "buff_crit_small",
                      "desc": "战斗中使用，暴击率 + 15%(3 刻)，湖珍珠磨粉调制的灵水"},
    "i_abyss_echo": {"name": "深渊回响药剂", "price": 120, "effect": "buff_matk",
                     "desc": "战斗中使用，魔攻 + 30%(3 刻)，深渊珍珠研磨的暗色药水"},
    "i_rainbow_elixir": {"name": "彩虹药剂", "price": 120, "effect": "next_atk_up", "effect_data": {"pct": 0.5},
                         "desc": "战斗中使用，下一次攻击伤害 + 50%，映着七色光的梦幻药剂"},
    "i_storm_chowder": {"name": "风暴贝汤", "price": 100, "hot": 0.08, "hot_turns": 3, "heal": 0.2,
                        "desc": "风暴贝熬的鲜汤，战斗中每刻回复 8% 生命（3 刻）"},
    # v104 R3 M15 P2-2：夜光鲛消费点（13 章 line 134 烹饪/炼金用途落地——垂钓独占材料→烹饪）
    "i_glow_shark_soup": {"name": "夜光鲛汤", "price": 100, "hot": 0.08, "hot_turns": 3, "heal": 0.2,
                          "desc": "夜光鲛熬成的鲜汤，汤面泛着幽幽荧光，战斗中每刻回复 8% 生命（3 刻）"},
    "i_thunder_elixir": {"name": "雷晶药剂", "price": 200, "effect": "buff_atk_big",
                         "desc": "战斗中使用，攻击力 + 40%(3 刻)，雷晶砂淬炼的噼啪药剂"},
    "i_dragonbone_elixir": {"name": "龙骨药剂", "price": 400, "effect": "buff_atk_big_def",
                            "desc": "战斗中使用，攻击 + 40%；抵挡 3 次受击防御 + 45%，上古鱼骨熬成的猛药"},
})

# ================= v112 隐藏技能书（P1：横向扩展，跨流派稀有技） =================
# 设计文档：design/new_world/09_职业体系.md §6
# 字段：learn_skill=学会的技能名；require_class=源流限定（隐藏线 cls_id，可空=全职业）
# 『使用 技能书』→ 校验源流与等级 → 技能进 learned_skills（复用学习管线）→ 消耗道具
# 铁律：未来新特殊技能统一走技能书，不再开新职业线
ITEMS.update({
    "i_tome_long_xi_zhi_nu": {"name": "龙息之怒技能书", "price": 5000, "type": "消耗品",
                              "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi",
                              "desc": "记载着龙息之怒的古卷——战士一脉皆可参悟，习得真伤绝技"},
    "i_tome_xu_kong_bao_po": {"name": "元素湮灭技能书", "price": 6000, "type": "消耗品",
                              "learn_skill": "元素湮灭", "require_class": "cls_fa_shi",
                              "desc": "记录着虚空回响的残卷——法师一脉皆可参悟，吸蓝爆破"},
    "i_tome_du_bao": {"name": "荆棘爆技能书", "price": 4500, "type": "消耗品",
                      "learn_skill": "荆棘爆", "require_class": "cls_you_xia",
                      "desc": "浸着草汁的旧册——游侠一脉皆可参悟，引爆毒层造成高额伤害"},
    "i_tome_an_mian_qu": {"name": "安眠曲技能书", "price": 4500, "type": "消耗品",
                          "learn_skill": "安眠曲", "require_class": "cls_shi_ren",
                          "desc": "记着古老摇篮曲的乐谱——诗人一脉皆可参悟，歌声使人安眠"},
    "i_tome_shou_ge": {"name": "收割技能书", "price": 5000, "type": "消耗品",
                       "learn_skill": "收割", "require_class": "cls_ci_ke",
                       "desc": "染着暗红墨迹的薄册——刺客一脉皆可参悟，斩杀残血"},
})

# ================= v173.3 意见#103（鱼鱼拍板自选礼包）：新手武器自选礼包 =================
# q1_6 主线『第一杯麦酒』奖励替换：不再固定发法杖，改为自选礼包（使用→弹6职业选项→发数字领取）
# pick_options 每项: name=展示名(同装备名), rid=名册ID, desc=展示行
ITEMS.update({
    "i_novice_weapon_pack": {
        "name": "新手武器自选礼包", "price": 0, "type": "消耗品", "weapon_pick": True,
        "desc": "镇长送的行礼——打开后可自选一件新手武器（战士/法师/游侠/牧师/刺客/拳师）",
        "pick_options": [
            {"name": "誓约长剑·初心", "rid": "eq_shi_yue_chang_jian_chu_xin",
             "desc": "⚔️【誓约长剑·初心】誓约铁剑——战士的剑（力量系）"},
            {"name": "誓约之杖·初芽", "rid": "eq_shi_yue_zhi_zhang_chu_ya",
             "desc": "🔮【誓约之杖·初芽】新手法杖——法师/诗人的杖（智力系）"},
            {"name": "誓约长弓·新绿", "rid": "eq_shi_yue_zhang_gong_xin_lv",
             "desc": "🏹【誓约长弓·新绿】柘木猎弓——游侠的弓（敏捷系）"},
            {"name": "誓约权杖·初沐", "rid": "eq_shi_yue_quan_zhang_chu_mu",
             "desc": "✨【誓约权杖·初沐】圣堂权杖——牧师的杖（智力系）"},
            {"name": "誓约匕首·初影", "rid": "eq_shi_yue_bi_shou_chu_ying",
             "desc": "🗡️【誓约匕首·初影】夜行短刃——刺客的匕首（敏捷系）"},
            {"name": "誓约拳套·初锋", "rid": "eq_shi_yue_quan_tao_chu_feng",
             "desc": "👊【誓约拳套·初锋】缠布拳套——拳师的拳套（力量系）"},
        ],
    },
})

# ================= 21 份支线设计稿新增奖励物品：消耗品/纪念品（2026-08-16 批量登记） =================
# 消耗品字段复用 item_templates.py 既有模板（heal/mana 百分比、effect 战斗 buff 键）；
# 纪念品/收藏品无使用逻辑，type=收藏品 仅展示（desc 注明设计效果，待对应系统落地）。
ITEMS.update({
    # ---- 03 深渊封印：圣光草（S46 约拿赠礼·回复道具）----
    # TODO 来源待接线：圣光草 desc 声称约拿赠礼（S46），任务无发放接线（零引用）
    "i_sheng_guang_cao": {"name": "圣光草", "price": 8, "heal": 0.1, "type": "消耗品",
                          "desc": "晒干的圣光草，含在嘴里有暖意——回复 10% 生命(约拿的见面礼)"},
    # ---- 04 北境生存：黑羽箭（S18 铁弓赠·一次性战斗道具）/ 长夜暖酒（S46 交付·消耗品）----
    # TODO 来源待接线：黑羽箭 desc 声称 S18 铁弓赠，任务无发放接线（零引用）
    "i_hei_yu_jian": {"name": "黑羽箭", "price": 30, "effect": "next_atk_up", "effect_data": {"pct": 0.5}, "type": "消耗品",
                      "desc": "铁弓亲手削的黑羽箭，首刻额外伤害——下一次攻击伤害+50%(一次性战斗道具)"},
    # TODO 来源待接线：长夜暖酒 desc 声称 S46 交付·消耗品，任务无发放接线（零引用）
    "i_chang_ye_nuan_jiu": {"name": "长夜暖酒", "food": True, "price": 60, "heal": 0.4, "mana": 0.4,
                            "effect": "buff_atk_food", "type": "消耗品",
                            "desc": "霜角堡长夜节的热酒——战斗外回复 40% 生命/魔力；战斗中攻击+10%(3 刻，设计稿 +5% 取最近档)"},
    # ---- 08 药园与花匠：月光安神剂（S49 炼金产物·消耗品）----
    "i_yue_guang_an_shen_ji": {"name": "月光安神剂", "price": 60, "heal": 0.4, "mana": 0.2, "type": "消耗品",
                               "desc": "月光兰蜜调成的安神药水——战斗外回复 40% HP + 20% MP(设计稿附清除 1 层负面，待驱散逻辑接入)"},
    # ---- 21 花匠与四季：春风铃花蜜（S48 奖励·消耗品）----
    # TODO 来源待接线：春风铃花蜜 desc 声称 S48 奖励，任务无发放接线（零引用）
    "i_chun_feng_ling_hua_mi": {"name": "春风铃花蜜", "food": True, "price": 25, "heal": 0.2, "mana": 0.1, "type": "消耗品",
                                "desc": "春风铃酿的花蜜，甜得带着铃声的余韵——非战斗回复 20% HP + 10% MP(可入烹饪)"},
    # ---- 09 收藏家：纪念品（老栎的鉴定放大镜/歌贝挂饰/晨曦博物馆珍藏册）----
    "i_lao_li_de_jian_ding_fang_da_jing": {"name": "老栎的鉴定放大镜", "price": 60, "type": "收藏品",
                                           "desc": "老栎古董店的黄铜放大镜，使用后鉴定背包内 1 件物品并展示一段来历 lore(一次性，鉴定功能待实现)"},
    "i_ge_bei_gua_shi": {"name": "歌贝挂饰", "price": 50, "effect": "food_spd_up_small", "type": "消耗品",
                         "desc": "会唱歌的海贝挂饰——战斗中使用，本场全队速度+10%(歌贝之声)"},
    # TODO 来源待接线：晨曦博物馆珍藏册（09 收藏家纪念品），无任何发放/使用接线（零引用）
    "i_chen_xi_bo_wu_guan_zhen_cang_ce": {"name": "晨曦博物馆珍藏册", "price": 80, "type": "收藏品",
                                          "desc": "晨曦博物馆的藏品册，使用后图鉴条目+1 并解锁 1 条藏品故事(一次性，图鉴功能待实现)"},
    # ---- 10 宠物情缘：宠物口粮 / 月尾狐食谱 / 絮毛宠物店贵宾卡 ----
    "i_chong_wu_kou_liang": {"name": "宠物口粮", "food": True, "price": 30, "type": "消耗品",
                             "desc": "絮毛宠物店配方口粮，喂养宠物饱食度+40(高于普通食材的+30，宠物系统对接待实现)"},
    "i_yue_wei_hu_shi_pu": {"name": "月尾狐食谱·月光三色餐", "price": 30, "type": "收藏品",
                            "desc": "记录月光羹配方(月光草×1+银鳞鱼×1+兽肉×1)的收集册，无数值功能(图鉴类道具)"},
    "i_xu_mao_chong_wu_dian_gui_bin_ka": {"name": "絮毛宠物店贵宾卡", "price": 100, "type": "收藏品",
                                          "desc": "絮毛宠物店贵宾卡——永久 9 折(含月尾宠物店分店)，可存背包展示(折扣功能待实现)"},
    # ---- 11 商路风云：一袋商路口粮（S46 消耗品）/ 纪念品 ----
    # TODO 来源待接线：一袋商路口粮 desc 声称 S46 消耗品，任务无发放接线（零引用）
    "i_yi_dai_shang_lu_kou_liang": {"name": "一袋商路口粮", "food": True, "price": 30, "heal": 0.4, "type": "消耗品",
                                    "desc": "商队标准口粮，干饼配咸肉——非战斗回复 40% 生命(跑商人的味道)"},
    "i_yun_wen_si_jin": {"name": "云纹丝巾", "price": 150, "type": "收藏品",
                         "desc": "赛琳夫人所赠的晨曦丝绸，云纹暗绣——佩戴后交易折扣+5%(饰品，折扣效果待装备表落地)"},
    # TODO 来源待接线：黑铁商会印 desc 声称 S49 徽记（quests.py 注释「已登记·未并入 reward_item」），实际无发放接线
    "i_hei_tie_shang_hui_yin": {"name": "黑铁商会印", "price": 100, "type": "收藏品",
                                "desc": "铁港商会黑铁印章，商会执事级信物——持有者享商会柜台 9 折补给(S49 收藏品·徽记)"},
    "i_shang_hui_gu_fen_ping_zheng": {"name": "商会股份凭证", "price": 100, "type": "任务道具",
                                      "desc": "印有玩家姓名的烫金股份凭证——每周领取商路分红 50 金币(生活线长期收益，分红功能待实现；任务道具 use 不消耗)"},
    # TODO 来源待接线：银风商铃（quests.py 注释「已登记·未并入 reward_item」），实际无发放接线（零引用）
    "i_yin_feng_shang_ling": {"name": "银风商铃", "price": 100, "type": "收藏品",
                              "desc": "银风商道的铃铛，叮当声是商路的信物——商路类委托报酬+5%(纪念品·饰品，效果待实现)"},
    # ---- 12 侦探与怪盗：嘉奖令 / 博物馆荣誉徽章（猫眼石胸针为真实装备，已登记 equip_roster eq_mao_yan_shi_xiong_zhen）----
    "i_chen_xi_cheng_wei_bing_jia_jiang_ling": {"name": "晨曦城卫兵嘉奖令", "price": 50, "type": "收藏品",
                                                "desc": "卫兵队长嘉奖文书，盖晨曦城卫兵印章(S49 正义线收藏品)"},
    # TODO 来源待接线：王都博物馆荣誉徽章 desc 声称 S50 收藏品，任务无发放接线（零引用）
    "i_wang_du_bo_wu_guan_rong_yu_hui_zhang": {"name": "王都博物馆荣誉徽章", "price": 80, "type": "收藏品",
                                               "desc": "铜质徽章，刻「王都博物馆·致谢」(S50 收藏品)"},
    # ---- 06 龙裔传承：古龙语·守望之息（收藏纪念）/ 云鳞护符（链尾纪念品）----
    # 守望之息技能未在 skills.py 注册（Lv.96 龙语系最终技），无 learn_skill/发放接线，暂作收藏品登记；技能落地后再改回技能书
    "i_gu_long_yu_shou_wang_zhi_xi": {"name": "古龙语·守望之息", "price": 80, "type": "收藏品",
                                      "desc": "以古龙语写就的传承祝词，相传吟诵者可唤风守望群山——龙裔传承的最终纪念(Lv.96 龙语系最终技·收藏)"},
    # TODO 来源待接线：云鳞护符 desc 声称链尾完成纪念品，任务无发放接线（零引用）
    "i_yun_lin_hu_fu": {"name": "云鳞护符", "price": 100, "type": "收藏品",
                        "desc": "以暮影之鳞与云海之晶打造的护符——守望者的信物(链尾完成纪念品)"},
    # ---- 14 学徒之路：小灰攒钱买的麦酒（Lv.30 彩蛋·消耗品）----
    # TODO 来源待接线：小灰攒钱买的麦酒 desc 声称 Lv.30 彩蛋，任务无发放接线（零引用）
    "i_xiao_hui_mai_jiu": {"name": "小灰攒钱买的麦酒", "food": True, "price": 20, "heal": 0.3, "mana": 0.3, "type": "消耗品",
                           "desc": "橡木镇特酿，用粗布包着——「请重要的人喝酒，要用自己挣的钱。」恢复 30% 生命/魔力"},
    # ---- 18 隐藏支线：装着一小片海的瓶子（H5 海之瓶·消耗品）/ 银铃鲤饵（S51 鱼饵·一次性）----
    # TODO 来源待接线：装着一小片海的瓶子 desc 声称 H5 海之瓶，hq5 任务无发放接线（零引用）
    "i_zhuang_zhe_yi_xiao_pian_hai_de_ping_zi": {"name": "装着一小片海的瓶子", "price": 40, "heal": 0.4, "type": "消耗品",
                                                 "desc": "玻璃瓶里装着一小片海，摇一摇能听见潮声——战斗外回复 40% 生命(收藏/应急两用)"},
    "i_yin_ling_li_er": {"name": "银铃鲤饵", "price": 110, "type": "消耗品",
                         "desc": "银铃鲤银鳞磨制的鱼饵——下一次垂钓传说档位概率×3，垂钓结算后消失(鱼饵系统接入待实现)"},
    # ---- v124 支线配方产物（S47 香草烤兽肉 / S49 金锅野猪肋排 / H6 白石圣灰药剂）----
    "i_xiang_cao_kao_shou_rou": {"name": "香草烤兽肉", "food": True, "price": 30, "heal": 0.3, "stamina": 25,
                                 "effect": "buff_atk_food", "type": "消耗品",
                                 "desc": "香草裹着兽肉烤得滋滋冒油——战斗外回复 30% 生命；战斗中攻击+10%(3 刻，设计稿 +6% 持续 2 场取最近档)"},
    "i_jin_guo_ye_zhu_pai_pai": {"name": "金锅野猪肋排", "food": True, "price": 36, "heal": 0.35, "stamina": 35,
                                 "effect": "buff_atk_food", "type": "消耗品",
                                 "desc": "胖托尼获奖的金锅肋排——战斗外回复 35% 生命；战斗中攻击+10%(3 刻，设计稿 +10% 持续 3 场取最近档)"},
    "i_bai_shi_sheng_hui_yao_ji": {"name": "白石圣灰药剂", "price": 100, "heal": 0.3, "type": "消耗品",
                                   "desc": "白石圣灰调成的圣光药剂——战斗外回复 30% 生命；战斗中驱散全队负面(驱散逻辑待接入)"},
})

# ================= v130.2 核心资源重设计：六职业线资源联动消耗品（回资源类） =================
# 设计稿：resource_redesign_v130/<线名>.md §7 物品联动提案（2026-08-19）
# 效果字段规范（v130.2 新增 effect 族，消费端实现归批次 2 引擎/消费层）：
#   - restore_resource      立即回复资源量            effect_data {key, amount}
#   - restore_resource_full 立即充满资源（带代价）      effect_data {key, penalty_pct, penalty_turns}
#   - resource_amp          指定触发下资源获取额外 +N  effect_data {key, amount, turns 或 hits, trigger}
#   - battle_start_resource 战前/战斗开始预充资源       effect_data {key, amount, buff(可选)}
#   - mana_cost_down        技能魔力消耗 -P%          effect_data {pct, turns}
#   - buff_phys_next        下一次气力/物理技能 +P%     effect_data {pct}
#   - full_tension（游侠守线专属满弦）                  effect_data {turns}
# ⚠️ v130.2 基础法师无资源（纯蓝）：元素结晶/元素亲和药剂 按设计稿 §7 落地为纯蓝补给，不做充能写入（攻线限定说明见 desc）。
# 资源 key 对齐 core_resources.py：rage / energy / faith / cp / chi / time_sand（法师基础 element 不再写入）。
# 价格口径：一般 45-200 金、传说级特殊消耗品 400+（参考现有效果类物品；设计稿银/金参考值已按经济系统校准）。
ITEMS.update({
    # ---- 战士线（怒气 rage，max 10）----
    "i_rage_draught": {"name": "怒火药剂", "price": 70, "type": "消耗品",
                       "effect": "restore_resource", "effect_data": {"key": "rage", "amount": 3},
                       "desc": "战斗中使用，立即回复 3 点怒气（占 1 刻行动）；怒火在喉，一饮而尽 (精良，炼金商人 / 军营杂货出售)"},
    "i_boiling_war_blood": {"name": "沸腾战血", "price": 110, "type": "消耗品",
                            "effect": "resource_amp", "effect_data": {"key": "rage", "amount": 2, "turns": 3, "trigger": "on_hit"},
                            "desc": "战斗中使用，3 刻内受击时 怒气获取 + 2（可与血债/浴血叠加）(精良，炼金商人 / 副本掉落)"},
    "i_molten_core": {"name": "熔核之心", "price": 450, "type": "消耗品",
                      "effect": "restore_resource_full", "effect_data": {"key": "rage", "penalty_pct": 0.2, "penalty_turns": 2},
                      "desc": "战斗中使用，立即充满怒气；代价：2 刻内 全减伤 - 20%（限定补给，拿血换怒的物资层延伸）(史诗，高级炼金 / 精英副本 / 军团军需官)"},
    "i_prebattle_feast": {"name": "战前猛火餐", "food": True, "price": 50, "type": "消耗品",
                          "effect": "battle_start_resource", "effect_data": {"key": "rage", "amount": 2},
                          "desc": "战斗开始前食用，首刻 怒气 + 2 预充（烧烤巨兽肝，食物 buff，非战斗中）(稀有，军营厨师 / 篝火烹饪)"},
    # ---- 法师线（v130.2 基础无资源 → 纯蓝补给；时之沙漏为时咒隐藏线专属）----
    "i_element_crystal": {"name": "元素结晶", "price": 90, "type": "消耗品", "mana": 0.6,
                          "desc": "使用后回复 60% 魔力——冰火雷元素凝成的纯净结晶（精良，元素地脉矿点 / 炼金师「结晶调和」）"},
    "i_affinity_draught": {"name": "元素亲和药剂", "price": 120, "type": "消耗品",
                           "effect": "mana_cost_down", "effect_data": {"pct": 0.1, "turns": 3},
                           "desc": "战斗中使用，3 刻内 技能魔力消耗 - 10%（基础法师纯蓝减耗，蓝量管理即节奏锚点；攻线转职后同时提供充能获取 + 1）(精良，附魔台 / 药剂商店)"},
    # ---- 游侠线（精力 energy，max 100，自然回 30）----
    "i_vitality_draught": {"name": "活力原浆", "price": 60, "type": "消耗品",
                           "effect": "restore_resource", "effect_data": {"key": "energy", "amount": 40},
                           "desc": "战斗中使用，立即回复 40 点精力（占 1 刻行动；精力是全资源唯一天然回，补给即输出上限）(精良，炼金商人 / 山间草药合成)"},
    "i_swiftness_core": {"name": "迅捷之核", "price": 80, "type": "消耗品",
                         "effect": "resource_amp", "effect_data": {"key": "energy", "amount": 30, "turns": 1, "trigger": "regen"},
                         "desc": "战斗中使用，本刻 精力自然回复 + 30（与自然回叠加）(精良，猎人营地铁匠 / 副本掉落)"},
    "i_fulltension_brew": {"name": "满弦烈酒", "food": True, "price": 95, "type": "消耗品",
                           "effect": "full_tension", "effect_data": {"turns": 1},
                           "desc": "战斗中使用，立即进入满弦状态 1 刻（精力阈值视为已满足；游侠守线·风行者专属补给，基础/攻线携带无效）(精良，酒馆 / 杂货出售)"},
    # ---- 牧师线（信仰 faith，max 10）----
    "i_radiance_potion": {"name": "圣辉药剂", "price": 140, "type": "消耗品",
                          "effect": "restore_resource", "effect_data": {"key": "faith", "amount": 3, "cooldown": 2},
                          "desc": "战斗中使用，立即回复 3 点信仰值（冷却 2 刻）(精良，圣教团声望商店 / 炼金配方)"},
    "i_faith_crystal": {"name": "信仰结晶", "price": 300, "type": "消耗品",
                        "effect": "restore_resource", "effect_data": {"key": "faith", "amount": 5, "next_heal_pct": 0.2},
                        "desc": "战斗中使用，立即回复 5 点信仰值，并使下一次治疗技能效果 + 20%（圣光凝聚的结晶，光芒愈盛）(史诗，圣光教徒精英掉落)"},
    "i_incense_candle": {"name": "香薰圣烛", "price": 110, "type": "消耗品",
                         "effect": "resource_amp", "effect_data": {"key": "faith", "amount": 1, "turns": 3, "trigger": "on_heal"},
                         "desc": "战斗外点燃，开场 3 刻内 治疗获得 信仰值 + 1（香薰安神，预热神恩）(精良，杂货商 / 支线奖励)"},
    # ---- 刺客线（连击点 cp，max 5）----
    "i_shadowstrike_potion": {"name": "影袭药水", "price": 80, "type": "消耗品",
                              "effect": "resource_amp", "effect_data": {"key": "cp", "amount": 1, "hits": 3, "trigger": "on_hit"},
                              "desc": "战斗中使用，接下来 3 次出手命中时 额外 + 1 连击点 (稀有，炼金商人 / 19-25 级副本)"},
    "i_blink_crystal": {"name": "瞬步结晶", "price": 280, "type": "消耗品",
                        "effect": "restore_resource", "effect_data": {"key": "cp", "amount": 2, "once_per_battle": True},
                        "desc": "战斗中使用，立即获得 2 连击点（每场战斗限用 1 次）；身影一瞬，再出现时已贴近要害 (史诗，精英怪掉落 / 影纱任务链)"},
    "i_nightowl_tea": {"name": "夜枭茶", "food": True, "price": 55, "type": "消耗品",
                       "effect": "battle_start_resource", "effect_data": {"key": "cp", "amount": 1},
                       "desc": "战斗开始前饮用（30 分钟效果），战斗开始时 + 1 连击点；夜枭静栖，敛翼待猎 (稀有，餐厅 / 营地烹饪)"},
    # ---- 拳师线（气 chi，max 10）----
    "i_chi_pellet": {"name": "斗气凝丸", "price": 60, "type": "消耗品",
                     "effect": "restore_resource", "effect_data": {"key": "chi", "amount": 2},
                     "desc": "战斗中使用，立即回复 2 点气（转职攻线/苦修后，本刻不破坏蓄势斜坡）(精良，商店 / 炼金)"},
    "i_chi_essence": {"name": "引气精华", "price": 160, "type": "消耗品",
                      "effect": "buff_phys_next", "effect_data": {"pct": 0.2},
                      "desc": "战斗中使用，下一次气力技 物理伤害 + 20%（引气入体，气力灌注拳锋）(史诗，副本掉落 / 炼金台)"},
    "i_surging_brew": {"name": "澎湃烈酒", "food": True, "price": 85, "type": "消耗品",
                       "effect": "battle_start_resource", "effect_data": {"key": "chi", "amount": 1, "buff": {"kind": "phys_up", "pct": 0.05, "turns": 3}},
                       "desc": "战斗前饮用，开战后前 3 刻 物理伤害 + 5%，且初始 + 1 点气；烈酒入喉，气机澎湃 (稀有，酒馆 / 任务奖励)"},
})


# ================= v140 资源获取渠道丰富化新增道具（39件） =================
# 来源：战斗机制道具20+功能生活道具19（方案 3.6/3.7 节）
ITEMS.update({
    'i_jin_ling_xiang_lu': {'name': '烬灵香炉', 'price': 60, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'summon', 'effect_data': {'tid': 'ember_wisp', 'turns': 3, 'limit': 1, 'atk_ratio': 0.35, 'bodyguard': 0.3}, 'desc': '青铜香炉袅袅生烟，召出「烬灵」并肩而战——自动攻击(35%攻击)并为你挡刀，持续 3 刻(每场限 1 只，战斗内使用)'},
    'i_sheng_hui_ti_shen_xiang': {'name': '圣徽替身像', 'price': 120, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'summon', 'effect_data': {'tid': 'holy_totem', 'turns': 3, 'limit': 1, 'taunt': True, 'heal_bonus': 0.15}, 'desc': '圣徽圣像嘲讽敌方 1 刻，其后 2 刻你受治疗+15%(每场限 1，战斗内使用)'},
    'i_jing_ji_kui_lei_zhong': {'name': '荆棘傀儡种', 'price': 80, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'summon', 'effect_data': {'tid': 'thorn_golem', 'turns': 3, 'limit': 1, 'thorns': 0.2}, 'desc': '撒下荆棘傀儡种，召出傀儡 3 刻，受击反弹 20% 伤害(每场限 1，战斗内使用)'},
    'i_zhan_di_yi_zhe_mo_ou': {'name': '战地医者魔偶', 'price': 150, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'summon', 'effect_data': {'tid': 'medic_golem', 'turns': 3, 'limit': 1, 'heal_pct': 0.08}, 'desc': '召出医者魔偶 3 刻，每刻末回复 8% 最大生命(每场限 1，战斗内使用)'},
    'i_shuang_han_bu_shou_jia': {'name': '霜寒捕兽夹', 'price': 70, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'trap', 'effect_data': {'ctrl': 'freeze', 'turns': 1, 'boss_downgrade': 'slow', 'shatter_bonus': 1.5}, 'desc': '冻结敌人 1 刻(Boss 降级为减速)，可接碎冰 1.5 倍增伤(战斗内使用)'},
    'i_chen_mo_feng_zhou_la': {'name': '沉默封咒蜡', 'price': 110, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'trap', 'effect_data': {'ctrl': 'silence', 'turns': 1, 'boss_rate': 0.6}, 'desc': '沉默敌人 1 刻(Boss 成功率 60%)(战斗内使用)'},
    'i_jiao_xie_sheng_wang': {'name': '缴械绳网', 'price': 60, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'trap', 'effect_data': {'ctrl': 'disarm', 'turns': 1, 'atk_reduce': 0.6}, 'desc': '敌方普攻伤害-60% 持续 1 刻(缴械)(战斗内使用)'},
    'i_mei_huo_mo_fen': {'name': '魅惑魔粉', 'price': 200, 'type': '消耗品', 'quality': 'purple', 'battle_ok': True, 'effect': 'trap', 'effect_data': {'ctrl': 'charm', 'turns': 1, 'self_damage': 0.5, 'boss_downgrade': 0.2, 'limit': 1}, 'desc': '魅惑敌人 1 刻，其攻击自身造成 50% 自伤(Boss 免疫，改降攻 20%)(每场限 1，战斗内使用)'},
    'i_sheng_quan_yuan_quan_ping': {'name': '圣泉源泉瓶', 'price': 130, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'mana_restore', 'effect_data': {'mana_pct': 0.25, 'cost_reduce': 0.25, 'turns': 2}, 'desc': '回复 25% 最大法力，且技能消耗-25% 持续 2 刻(战斗内使用)'},
    'i_chong_neng_zheng_liu_qi': {'name': '充能蒸馏器', 'price': 140, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'resource_charge', 'effect_data': {'res_gain': 2, 'cd_reduce': 1}, 'desc': '核心资源+2，且全部技能冷却-1 刻(战斗内使用)'},
    'i_ji_hun_shui_jing': {'name': '汲魂水晶', 'price': 90, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'steal_buff', 'effect_data': {'turns': 2, 'no_target_no_consume': True}, 'desc': '偷取敌方 1 个增益转给自己 2 刻(敌方无增益则不消耗)(战斗内使用)'},
    'i_shi_zhi_yan_xiang': {'name': '时之延香', 'price': 120, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'buff_extend', 'effect_data': {'extend_turns': 2}, 'desc': '自身全部增益时长+2 刻(战斗内使用)'},
    'i_bu_si_niao_zhi_yu': {'name': '不死鸟之羽', 'price': 260, 'type': '消耗品', 'quality': 'purple', 'battle_ok': True, 'effect': 'phoenix', 'effect_data': {'revive_hp': 0.3, 'dmg_reduce': 0.2, 'turns': 3, 'limit': 1}, 'desc': '濒死守护：被击倒后以 30% 生命复活 1 次，复活后 3 刻减伤 20%(每场限 1，战斗内使用)'},
    'i_sheng_guang_jing_shui': {'name': '圣光净水', 'price': 85, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'purify_immune', 'effect_data': {'purify': True, 'immune': ['silence', 'stun'], 'turns': 3}, 'desc': '净化全部负面状态，且 3 刻免疫沉默/眩晕(战斗内使用)'},
    'i_long_xue_bian_shen_yao': {'name': '龙血变身药剂', 'price': 240, 'type': '消耗品', 'quality': 'purple', 'battle_ok': True, 'effect': 'morph', 'effect_data': {'atk_up': 0.3, 'matk_up': 0.3, 'dmg_taken_up': 0.15, 'turns': 3, 'limit': 1}, 'desc': '变身 3 刻：攻/魔攻+30%，但受击伤害+15%(每场限 1，战斗内使用)'},
    'i_ci_yuan_men_fei_fu': {'name': '次元门扉符', 'price': 280, 'type': '消耗品', 'quality': 'purple', 'battle_ok': True, 'effect': 'invuln', 'effect_data': {'turns': 1, 'stun_after': 1, 'limit': 1}, 'desc': '无敌 1 刻免疫一切伤害，但下刻无法行动(僵直)(每场限 1，战斗内使用)'},
    'i_yuan_su_yin_bao_ji': {'name': '元素引爆剂', 'price': 100, 'type': '消耗品', 'quality': 'blue', 'battle_ok': True, 'effect': 'apply_mark', 'effect_data': {'mark': 'fire', 'stacks': 2, 'react_bonus': 1.3}, 'desc': '对目标施加 2 层火印，接蒸发 1.30 倍/引爆反应(战斗内使用)'},
    'i_lian_xie_zeng_fu_mo': {'name': '连携增幅墨', 'price': 75, 'type': '消耗品', 'quality': 'green', 'battle_ok': True, 'effect': 'dot_amp', 'effect_data': {'turns': 2, 'layer_per_hit': 1}, 'desc': '2 刻内每次命中使目标毒/灼烧/流血层数+1(战斗内使用)'},
    'i_yuan_su_gong_ming_shi': {'name': '元素共鸣石', 'price': 220, 'type': '消耗品', 'quality': 'purple', 'battle_ok': True, 'effect': 'reaction', 'effect_data': {'trigger_react': True, 'fallback_matk': 0.9}, 'desc': '直接引爆目标印记触发元素反应(无印记则造成 90% 魔攻伤害)(战斗内使用)'},
    'i_ruo_dian_ji_po_shi': {'name': '弱点击破石', 'price': 210, 'type': '消耗品', 'quality': 'purple', 'battle_ok': True, 'effect': 'vuln', 'effect_data': {'per_debuff': 0.12, 'max_debuff': 3, 'max_bonus': 0.36, 'turns': 3}, 'desc': '目标每有 1 种负面状态，你对其伤害+12%(上限 3 种+36%)，持续 3 刻(战斗内使用)'},
    'i_kuang_gong_ti_deng': {'name': '矿工提灯', 'price': 150, 'type': '消耗品', 'quality': 'blue', 'effect': 'lantern', 'effect_data': {'dur_min': 30, 'treasure_boost': 0.5, 'night_only': True}, 'desc': '30 分钟内探索事件出现宝藏/稀有档概率+50%(夜间限定)'},
    'i_pan_yan_gou_suo': {'name': '攀岩钩索', 'price': 90, 'type': '消耗品', 'quality': 'green', 'effect': 'grapple', 'effect_data': {'reach_unexplored': True, 'free_move': True}, 'desc': '下次探索必定抵达 1 个相邻未探索地图，并免 1 次移动消耗(仅野外)'},
    'i_xun_bao_luo_pan': {'name': '寻宝罗盘', 'price': 240, 'type': '消耗品', 'quality': 'purple', 'effect': 'compass', 'effect_data': {'dur_min': 30, 'chest_quality_up': 1, 'no_stack': True}, 'desc': '30 分钟内探索开出的宝箱品质+1 档(不叠加，与幸运符同池互斥)'},
    'i_xing_guang_wang_yuan_jing': {'name': '星光望远镜', 'price': 50, 'type': '消耗品', 'quality': 'white', 'effect': 'scout', 'effect_data': {'info': 'map_specialty'}, 'desc': '查看当前地图特产/隐藏区域线索/危险度(纯信息)'},
    'i_feng_rao_zhi_chu': {'name': '丰饶之锄', 'price': 230, 'type': '消耗品', 'quality': 'purple', 'effect': 'harvest_boost', 'effect_data': {'dur_min': 30, 'quality_up': 1, 'no_stack': True}, 'desc': '30 分钟内采集/挖掘产出品质+1 档(不叠加)'},
    'i_jiao_xiao_yu_wang': {'name': '鲛绡鱼网', 'price': 140, 'type': '消耗品', 'quality': 'blue', 'effect': 'fish_net', 'effect_data': {'catch_mult': 2, 'no_stack_with_bait': True}, 'desc': '下次垂钓渔获数量×2(不与鱼饵叠加)'},
    'i_ling_zhong_dai': {'name': '灵种袋', 'price': 80, 'type': '消耗品', 'quality': 'green', 'effect': 'seed_planter', 'effect_data': {'seed_pack': True}, 'desc': '家园花圃种子包，收获食材/草药原料(需家园系统)'},
    'i_bian_xie_zhong_zhi_xiang': {'name': '便携种植箱', 'price': 260, 'type': '消耗品', 'quality': 'blue', 'effect': 'garden_slot', 'effect_data': {'slot_add': 1, 'per_house_limit': 3}, 'desc': '家园花圃永久+1 种植位(每宅限 3 次，需房产)'},
    'i_kong_jian_bu_dai': {'name': '空间布袋', 'price': 300, 'type': '消耗品', 'quality': 'blue', 'effect': 'bag_expand', 'effect_data': {'slots': 5, 'per_char_limit': 3}, 'desc': '背包永久+5 格(每角色限 3 次)'},
    'i_xin_ya_ling': {'name': '信鸦翎', 'price': 100, 'type': '消耗品', 'quality': 'green', 'effect': 'mail', 'effect_data': {'fee_rate': 0.05, 'no_bound': True}, 'desc': '邮寄 1 件非绑定物品给指定玩家(收 5% 邮费)'},
    'i_geng_ming_qi_yue': {'name': '更名契约', 'price': 400, 'type': '消耗品', 'quality': 'purple', 'effect': 'rename', 'effect_data': {'monthly_limit': 1}, 'desc': '玩家改名 1 次(每角色月限 1)'},
    'i_gui_tu_xing_sha': {'name': '归途星砂', 'price': 180, 'type': '消耗品', 'quality': 'blue', 'effect': 'anchor', 'effect_data': {'dur_hours': 24, 'unique': True}, 'desc': '野外放置临时锚点，24 小时内可一键返回(锚点唯一)'},
    'i_duan_lu_zhong_zhu_quan': {'name': '锻炉重铸券', 'price': 350, 'type': '消耗品', 'quality': 'purple', 'effect': 'reforge', 'effect_data': {'keep_enhance': True, 'per_item_limit': 1, 'no_orange': True}, 'desc': '装备品质档随机重随 1 次，保留强化等级(每件限 1 次，橙装禁用)'},
    'i_ming_yun_zhi_mo': {'name': '命运之墨', 'price': 320, 'type': '消耗品', 'quality': 'purple', 'effect': 're_roll_affix', 'effect_data': {'same_tier': True}, 'desc': '重随装备 1 条附加词条(同档位)'},
    'i_yi_wang_zhi_quan': {'name': '遗忘之泉', 'price': 800, 'type': '消耗品', 'quality': 'purple', 'effect': 'reset_voucher', 'effect_data': {'free_reset': True}, 'desc': '免费属性+技能洗点 1 次(替代 500 金收费)'},
    'i_tui_bian_shen_yao': {'name': '蜕变神药', 'price': 500, 'type': '消耗品', 'quality': 'orange', 'effect': 'pet_rename', 'effect_data': {'per_pet_limit': 1}, 'desc': '宠物改名 1 次(每宠限 1 次)'},
    'i_huan_xing_wan_ou': {'name': '幻形玩偶', 'price': 200, 'type': '消耗品', 'quality': 'blue', 'effect': 'toy_form', 'effect_data': {'dur_min': 30, 'form': 'npc', 'no_stat': True}, 'desc': '30 分钟变身 NPC 形态，纯展示无属性(战斗无效)'},
    'i_qing_dian_yan_hua': {'name': '庆典烟花', 'price': 60, 'type': '消耗品', 'quality': 'green', 'effect': 'firework', 'effect_data': {'daily_limit': 1, 'cooldown_min': 10}, 'desc': '全群广播祝福语烟花(每日限 1，冷却 10 分钟)'},
    'i_yu_jin_ji_nian_zhang': {'name': '余烬纪念章', 'price': 1, 'type': '收藏品', 'quality': 'orange', 'effect': 'collection', 'effect_data': {'codex': True}, 'desc': '成就纪念品，图鉴点亮，纯收藏'},
})