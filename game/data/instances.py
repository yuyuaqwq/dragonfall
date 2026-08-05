# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - instances.py（组队副本）

副本 = 组队轮流回合 Boss 战（v53 起支持配置人数）：
- 单人副本（min_players=1）：无需组队，直接『副本 <名字>』开本
- 多人副本：队长『副本 <名字>』开本（需已组队），队员自动参战
- 轮流出手：队员A行动 → 队员B行动 → Boss行动 → 下一轮
- Boss 血量 = 单人 boss 模板 × hp_mult；攻击 × atk_mult
- 血量随人数缩放：hp_mult + 0.65 × (实际人数 - min_players)
- 通关：每人金币/经验 + 专属材料；贡献最高额外图纸
"""
INSTANCES = {
    # 2-3 人副本（v49 首发）
    "inst_crypt": {
        "name": "幽暗墓穴",
        "icon": "🦴",
        "lv": 15,
        "min_players": 2,
        "max_players": 3,
        "desc": "西境古战场下的王室墓穴，亡灵的低语在石壁间回荡。据说墓穴之主——骷髅王，仍在等待生者的血肉。",
        # boss: (id, 名字, role, lv, 技能ID, 掉落) —— 与地图怪物格式一致
        "boss": ["m_crypt_king", "骷髅王", "boss", 18,
                 ["ms_zhong_ji", "ms_an_ying_jian", "ms_zhao_hun"],
                 ["mat_mu_xue_fen"]],
        "mech": "enrage",  # v58 Boss 专属：骷髅王低血量狂暴
        "hp_mult": 2.5,
        "atk_mult": 1.2,
        "gold": 200,
        "exp": 300,
        "materials": ["mat_mu_xue_fen"],
        "mat_count": 2,
        "blueprint": True,
    },
    # 单人副本（v53 新增：新手单人挑战）
    "inst_goblin_nest": {
        "name": "哥布林巢穴",
        "icon": "👺",
        "lv": 8,
        "min_players": 1,
        "max_players": 1,
        "desc": "商路旁的废弃矿洞，如今成了哥布林的地盘。哥布林王挥舞着抢来的钉头锤，正盘算着下一票买卖。",
        "boss": ["m_goblin_king", "哥布林王", "boss", 10,
                 ["ms_zhao_ji", "ms_chong_zhuang", "ms_hao_jiao"],
                 ["mat_di_jing_er_duo"]],
        "mech": "summon",  # v58 Boss 专属：哥布林王定期召唤援军
        "hp_mult": 1.6,
        "atk_mult": 1.0,
        "gold": 60,
        "exp": 100,
        "materials": ["mat_di_jing_er_duo"],
        "mat_count": 1,
        "blueprint": False,
    },
    # 4 人副本（v53 新增：月影神庙，v49 待做清单补上）
    "inst_moon_temple": {
        "name": "月影神庙",
        "icon": "🌙",
        "lv": 20,
        "min_players": 4,
        "max_players": 4,
        "desc": "月神信徒的古老神庙，月光从穹顶倾泻而下。大祭司早已堕落，将圣所献给了虚空中的暗影。",
        "boss": ["m_moon_priest", "月影祭司", "boss", 24,
                 ["ms_an_ying_jian", "ms_lei_ji", "ms_zhao_huan"],
                 ["mat_an_ying_sui_pian"]],
        "mech": "heal",  # v58 Boss 专属：月影祭司定期汲取月光自愈
        "hp_mult": 2.5,
        "atk_mult": 1.3,
        "gold": 350,
        "exp": 480,
        "materials": ["mat_an_ying_sui_pian"],
        "mat_count": 3,
        "blueprint": True,
    },
}
