# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - titles.py"""
TITLES = [
    {"id": "novice",      "name": "初出茅庐",   "desc": "注册角色，踏上冒险之路"},
    {"id": "lv10",        "name": "崭露头角",   "desc": "达到 10 级"},
    {"id": "lv20",        "name": "名声鹊起",   "desc": "达到 20 级"},
    {"id": "lv30",        "name": "大陆传奇",   "desc": "达到 30 级"},
    {"id": "kill10",      "name": "新手猎人",   "desc": "累计击杀 10 只怪物"},
    {"id": "kill100",     "name": "百人斩",     "desc": "累计击杀 100 只怪物"},
    {"id": "kill500",     "name": "狩猎大师",   "desc": "累计击杀 500 只怪物"},
    {"id": "elite5",      "name": "精英猎手",   "desc": "击杀 5 只精英怪物"},
    {"id": "boss1",       "name": "屠龙者",     "desc": "击杀 1 个区域 Boss"},
    {"id": "boss3",       "name": "Boss猎手",   "desc": "击杀 3 个区域 Boss"},
    {"id": "rep_honor",   "name": "一方霸主",   "desc": "任一势力声望达到崇敬"},
    {"id": "rep_legend",  "name": "万民敬仰",   "desc": "任一势力声望达到崇拜"},
    {"id": "quest10",     "name": "任务达人",   "desc": "完成 10 个主线任务"},
    {"id": "wealthy",     "name": "腰缠万贯",   "desc": "拥有 5000 金币"},
    {"id": "explorer",    "name": "大陆探险家", "desc": "到访 10 个不同子区域"},
    # 垂钓大师 展示用：条件与奖励以成就侧为准 —— 与成就 ach_fish100『垂钓100次』同名不同条件，展示/加成统一归成就侧
    {"id": "fish10",      "name": "垂钓大师",   "desc": "垂钓 10 次"},
    {"id": "enhance5",    "name": "锻造新星",   "desc": "成功强化装备至＋5"},
    {"id": "enhance9",    "name": "神匠之手",   "desc": "成功强化装备至＋9"},
    {"id": "hidden",      "name": "秘银追寻者", "desc": "进入隐藏区域（如失落图书馆、灰烬回廊）"},
    {"id": "final",       "name": "传说终结者", "desc": "完成全部主线任务"},
    # ---- 副业称号（Lv.3/6/10 三档，大师称号带属性加成）----
    {"id": "pro_gather3", "name": "采药人",     "desc": "采集达到 Lv.3"},
    {"id": "pro_gather6", "name": "草药专家",   "desc": "采集达到 Lv.6"},
    {"id": "pro_gather10", "name": "万物采集大师", "desc": "采集达到 Lv.10(生命＋30)", "bonus": {"hp": 30}},
    {"id": "pro_mining3", "name": "挖矿工",     "desc": "挖掘达到 Lv.3"},
    {"id": "pro_mining6", "name": "矿脉猎手",   "desc": "挖掘达到 Lv.6"},
    {"id": "pro_mining10", "name": "群山之王",   "desc": "挖掘达到 Lv.10(攻击＋8)", "bonus": {"atk": 8}},
    # 垂钓新手 展示用：条件与奖励以成就侧为准 —— 副业 Lv.3 同名（ach_pro_fishing3 Lv.3 / ach_fish10 垂钓10次），展示统一
    {"id": "pro_fishing3", "name": "垂钓新手",   "desc": "垂钓达到 Lv.3"},
    {"id": "pro_fishing6", "name": "捕鱼能手",   "desc": "垂钓达到 Lv.6"},
    {"id": "pro_fishing10", "name": "深海渔神",   "desc": "垂钓达到 Lv.10(暴击＋2%)", "bonus": {"crit": 0.02}},
    {"id": "pro_alchemy3", "name": "炼金学徒",   "desc": "炼金达到 Lv.3"},
    {"id": "pro_alchemy6", "name": "药剂师",     "desc": "炼金达到 Lv.6"},
    {"id": "pro_alchemy10", "name": "贤者之石",   "desc": "炼金达到 Lv.10(魔力＋30)", "bonus": {"mp": 30}},
    {"id": "pro_craft3", "name": "铁匠学徒",   "desc": "锻造达到 Lv.3"},
    {"id": "pro_craft6", "name": "锻造师",     "desc": "锻造达到 Lv.6"},
    # 神锻名家 展示用：条件与奖励以成就侧为准 —— 副业大师同名（ach_pro_craft10 Lv.10 def:8 / ach_craft100 锻造100件），
    # 独立 bonus 注释掉（原 def:8），由成就侧 ach_pro_craft10 发属性，避免同名双端重复定义
    {"id": "pro_craft10", "name": "神锻名家",   "desc": "锻造达到 Lv.10(防御＋8)"},
    {"id": "pro_cooking3", "name": "厨房新手",   "desc": "烹饪达到 Lv.3"},
    {"id": "pro_cooking6", "name": "料理人",     "desc": "烹饪达到 Lv.6"},
    {"id": "pro_cooking10", "name": "食神",       "desc": "烹饪达到 Lv.10(速度＋3)", "bonus": {"spd": 3}},
    {"id": "fish_king",   "name": "鱼王猎手",   "desc": "钓上传说中的鱼王"},
    # ---- 荣誉商店称号（26 章 3.3）----
    {"id": "pvp_hero",    "name": "荣誉勋章",   "desc": "PVP 强者，攻击＋10(荣誉商店兑换)", "bonus": {"atk": 10}},
    # ---- 20 份支线设计稿新增称号（2026-08-16 批量登记，任务链专属/隐藏线解锁）----
    # 纯收藏型不带 bonus；带数值的走 bonus（spd 等）。
    # v124.2 修复：副业经验/折扣/声望类 desc 原承诺效果（采集+10%/商店折扣等）无消费挂点
    # （结算点在 economy.py/combat.py/store，title_bonus 只供面板属性消费）→ desc 去掉承诺，纯收藏。
    {"id": "north_benefactor", "name": "北境的恩人", "desc": "完成 S18 善结局，北境诸部的恩人(纯收藏)"},
    {"id": "nightwalker",      "name": "长夜行者",   "desc": "完成 S18 暗结局，北境风雪记住的名字(纯收藏)"},
    {"id": "guifan_seal",      "name": "归帆之印",   "desc": "完成海洋之歌线 S27，海神祝福的印记(纯收藏)"},
    {"id": "dragon_warden",    "name": "守龙者",     "desc": "完成龙裔传承线——龙骨山脉记得你的名字(纯收藏)"},
    {"id": "gourmet",          "name": "美食鉴赏家", "desc": "赢得 S49 美食节大赛(纯收藏)"},
    {"id": "herb_friend",      "name": "草木知己",   "desc": "完成 S49 月光药园线(纯收藏)"},
    {"id": "treasure_hunter",  "name": "寻宝猎人",   "desc": "完成 S49 收藏家线(纯收藏)"},
    {"id": "furry_friend",     "name": "毛茸茸之友", "desc": "完成 L1-5 宠物情缘线(纯收藏)"},
    {"id": "merchant_friend",  "name": "商会之友",   "desc": "完成 S50 商路风云线(纯收藏)"},
    {"id": "just_enforcer",    "name": "公正执法者", "desc": "侦探与怪盗线 S49 正义线(收藏)"},
    {"id": "shadow_friend",    "name": "影子之友",   "desc": "侦探与怪盗线 S49 义气线(收藏)"},
    {"id": "dusk_detective",   "name": "晨昏侦探",   "desc": "完成 S50 侦探与怪盗线(速度+3)", "bonus": {"spd": 3}},
    {"id": "peacemaker",       "name": "和解者",     "desc": "完成隐藏线·老兵不死(纯收藏)"},
    {"id": "guide",            "name": "引路人",     "desc": "完成 S50 学徒之路线，带出一个人来的冒险者不多(纯收藏)"},
    {"id": "night_rain",       "name": "夜雨常客",   "desc": "完成隐藏线 H5，雨夜的常客(速度+3)", "bonus": {"spd": 3}},
    {"id": "goose_messenger",  "name": "鸿雁传书",   "desc": "完成隐藏线 H7，翎信千里(速度+5)", "bonus": {"spd": 5}},
    {"id": "forge_son",        "name": "熔炉之子",   "desc": "完成隐藏线 H8，铁砧要塞的传人(纯收藏)"},
    {"id": "graveyard_warden", "name": "墓园守望者", "desc": "完成隐藏线 H6，白石墓园的守望者(纯展示)"},
    {"id": "fishing_legend",   "name": "垂钓传说",   "desc": "完成 S51 垂钓传说线(纯收藏)"},
    {"id": "late_messenger",   "name": "迟到的信使", "desc": "完成 S50 旧友重逢线——把一封迟了二十年的信送到终点的人(纯收藏)"},
    {"id": "season_gardener",  "name": "四季花匠",   "desc": "完成 S51 花匠与四季线——花比人长情(纯收藏)"},
]

