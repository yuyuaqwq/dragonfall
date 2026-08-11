# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - pets.py

24 章《宠物与伙伴系统》：14 品种（v101.11 扩容，原 4 品种），Lv.10 解锁宠物技能，饱食度系统。
品质统一复用 equipment.QUALITY 5 档（⚪普通/🟢优秀/🔵稀有/🟣史诗/🟠传说），全项目一致。
掉落表 PET_EGG_ROLL 数据化（v101.11 从 combat.py 硬编码迁入），加新宠物 = 加一行。

宠物技能类型：
  atk_pct   每 N 回合帮主人造成 攻击力 × value 伤害
  matk_pct  每 N 回合造成 魔攻 × value 伤害
  heal_pct  每 N 回合为主人回复 max_hp × value 生命
  block     每 N 回合 value 概率替主人挡一次攻击（敌方行动时触发）
  lifesteal 每 N 回合造成 攻击 × value 伤害，并回复伤害 50% 生命（v101.11 新增）
  pierce    每 N 回合造成 攻击 × value 伤害，并破防（敌方防御 -value×100%，持续 2 回合）（v101.11 新增）
  buff_atk  每 N 回合为主人加 攻击 × value buff（持续 2 回合）（v101.11 新增）
  crit_up   每 N 回合为主人加暴击 +value（持续 2 回合）（v101.11 新增）
"""

PET_POOL = [
    # ---------- ⚪ 普通 ----------
    {"key": "pet_wolf",   "name": "森林狼崽", "icon": "🐺", "quality": "white", "focus": "攻击",
     "skill_name": "撕咬", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.40,
     "source": "野外兽类怪(狼/狗/野猪/熊)掉落狼崽蛋",
     "desc": "忠诚的森林伙伴，每 3 回合帮主人撕咬敌人造成攻击伤害",
     "lines": ["嗷呜！", "汪！主人我上啦！", "（龇牙）交给我！"]},
    {"key": "pet_turtle", "name": "铁壳龟", "icon": "🐢", "quality": "white", "focus": "防守",
     "skill_name": "铁壁缩壳", "skill_interval": 4, "skill_type": "block", "skill_value": 0.15,
     "source": "垂钓稀有产出(blue 档)/橡木镇新手任务",
     "desc": "慢吞吞但硬邦邦，每 4 回合有 15% 概率替主人挡下一次攻击",
     "lines": ["……（缩头）", "壳！", "慢慢来，比较快。"]},
    # ---------- 🟢 优秀 ----------
    {"key": "pet_cat",    "name": "黑猫", "icon": "🐈‍⬛", "quality": "green", "focus": "敏捷",
     "skill_name": "影袭", "skill_interval": 3, "skill_type": "block", "skill_value": 0.25,
     "source": "精英怪概率掉落(城市/密林精英)",
     "desc": "神秘的黑猫，每 3 回合有 25% 概率替主人挡下一次攻击",
     "lines": ["喵——！", "（无声的扑击）", "影子会保护你。"]},
    {"key": "pet_rabbit", "name": "月光兔", "icon": "🐇", "quality": "green", "focus": "恢复",
     "skill_name": "月光祝福", "skill_interval": 4, "skill_type": "heal_pct", "skill_value": 0.08,
     "source": "采集点/垂钓稀有产出(特殊蛋)",
     "desc": "月光下诞生的灵兔，每 4 回合为主人回复 8% 生命",
     "lines": ["（抖耳朵）月光在照耀！", "咕噜噜～", "别怕，我带着月亮的温柔。"]},
    {"key": "pet_dove",   "name": "圣光鸽", "icon": "🕊️", "quality": "green", "focus": "恢复",
     "skill_name": "圣光羽翼", "skill_interval": 4, "skill_type": "heal_pct", "skill_value": 0.12,
     "source": "垂钓稀有产出(blue 档)圣光鸽蛋",
     "desc": "教会的信使，每 4 回合为主人回复 12% 生命",
     "lines": ["咕咕！愿圣光护佑你！", "（羽翼洒下光尘）", "光明与你同在。"]},
    # ---------- 🔵 稀有 ----------
    {"key": "pet_fox",    "name": "冰晶狐", "icon": "🦊", "quality": "blue", "focus": "元素",
     "skill_name": "霜刃", "skill_interval": 3, "skill_type": "matk_pct", "skill_value": 0.50,
     "source": "北境野外怪(狐/貂/雪兽)掉落冰晶狐蛋",
     "desc": "北境雪原的精灵，每 3 回合以霜刃造成 50% 魔攻伤害",
     "lines": ["（尾巴凝出冰霜）", "霜雪会埋葬敌人！", "嘶——好冷！"]},
    {"key": "pet_salamander", "name": "火尾蜥", "icon": "🦎", "quality": "blue", "focus": "元素",
     "skill_name": "烈焰尾击", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.55,
     "source": "火山/沙漠野外怪(蜥/火蛇)掉落火尾蜥蛋",
     "desc": "尾尖燃着不灭的火焰，每 3 回合以烈焰尾击造成 55% 攻击伤害",
     "lines": ["嘶嘶——！", "（尾巴甩出火星）", "烧起来啦！"]},
    {"key": "pet_panther", "name": "影豹", "icon": "🐆", "quality": "blue", "focus": "敏捷",
     "skill_name": "狩猎之眼", "skill_interval": 3, "skill_type": "crit_up", "skill_value": 0.20,
     "source": "密林精英怪概率掉落影豹蛋",
     "desc": "潜伏在密林阴影中的猎手，每 3 回合为主人加持 20% 暴击(2 回合)",
     "lines": ["（瞳孔收缩）", "猎物……跑不掉的。", "狩猎开始！"]},
    # ---------- 🟣 史诗 ----------
    {"key": "pet_drake",  "name": "龙裔幼崽", "icon": "🐉", "quality": "purple", "focus": "元素",
     "skill_name": "龙息", "skill_interval": 4, "skill_type": "matk_pct", "skill_value": 0.60,
     "source": "Boss 概率掉落(龙系/精英 Boss)",
     "desc": "龙族的幼崽，每 4 回合喷吐龙息造成 60% 魔攻伤害",
     "lines": ["吼——！（喷出一小团火）", "吾之血脉，燃烧！", "（龙威初显）"]},
    {"key": "pet_bat",    "name": "血蝠", "icon": "🦇", "quality": "purple", "focus": "攻击",
     "skill_name": "吸血撕咬", "skill_interval": 4, "skill_type": "lifesteal", "skill_value": 0.30,
     "source": "洞穴/墓穴精英怪概率掉落血蝠蛋",
     "desc": "暗夜中的吸血鬼，每 4 回合撕咬造成 30% 攻击伤害，回复伤害一半的生命",
     "lines": ["叽叽叽！", "（蝠翼展开）", "献上你的血……哦不是，你的败北！"]},
    {"key": "pet_armadillo", "name": "岩甲兽", "icon": "🦔", "quality": "purple", "focus": "防守",
     "skill_name": "碎岩冲撞", "skill_interval": 4, "skill_type": "pierce", "skill_value": 0.35,
     "source": "矿洞/山丘精英怪概率掉落岩甲兽蛋",
     "desc": "披着岩石甲壳的重装兽，每 4 回合冲撞造成 35% 攻击伤害并破防(敌方防御减半 2 回合)",
     "lines": ["哼哧哼哧！", "（滚成球冲出去）", "岩石的力量！"]},
    {"key": "pet_thunderbird", "name": "雷羽鸟", "icon": "🦅", "quality": "purple", "focus": "元素",
     "skill_name": "雷鸣鼓舞", "skill_interval": 4, "skill_type": "buff_atk", "skill_value": 0.30,
     "source": "高地 Boss 概率掉落",
     "desc": "羽翼缠绕雷霆的战鸟，每 4 回合为主人加持 30% 攻击(2 回合)",
     "lines": ["嘎——！（雷光闪烁）", "雷霆之力，借给你！", "（羽毛噼啪作响）"]},
    # ---------- 🟠 传说 ----------
    {"key": "pet_griffin", "name": "幼年狮鹫", "icon": "🦁", "quality": "orange", "focus": "攻击",
     "skill_name": "狮鹫俯冲", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.70,
     "source": "传说级 Boss 极稀有掉落",
     "desc": "天空之王的后裔，每 3 回合俯冲造成 70% 攻击伤害",
     "lines": ["嗷——！（展翅）", "天空，是我的猎场！", "俯冲！"]},
    {"key": "pet_starbutterfly", "name": "星灵蝶", "icon": "🦋", "quality": "orange", "focus": "恢复",
     "skill_name": "星辉治愈", "skill_interval": 3, "skill_type": "heal_pct", "skill_value": 0.15,
     "source": "传说级垂钓稀有产出/神秘宝箱",
     "desc": "翅膀洒落星辉的传说之蝶，每 3 回合为主人回复 15% 生命",
     "lines": ["（翅膀洒下星尘）", "星光会治愈一切～", "（轻盈地绕着你飞）"]},
]

# v101.11 蛋掉落表数据化（原 combat.py 硬编码迁入）：
#   每项 {key, rate, role?, is_elite?, is_boss?, name_kw?}，命中条件全部满足才掷概率。
#   加新掉落渠道 = 加一行；条件语义：role=怪物定位 / is_elite / is_boss / name_kw=名字含任一关键词
PET_EGG_ROLL = [
    {"key": "pet_wolf",        "rate": 0.015, "role": "dps", "name_kw": ["狼", "狗", "野猪", "熊"]},
    {"key": "pet_salamander",  "rate": 0.015, "role": "dps", "name_kw": ["蜥", "火蛇", "蛇"]},
    {"key": "pet_fox",         "rate": 0.015, "role": "dps", "name_kw": ["狐", "貂", "雪兽", "鹿"]},
    {"key": "pet_cat",         "rate": 0.065, "is_elite": True},
    {"key": "pet_panther",     "rate": 0.035, "is_elite": True},
    {"key": "pet_bat",         "rate": 0.030, "is_elite": True},
    {"key": "pet_armadillo",   "rate": 0.030, "is_elite": True},
    {"key": "pet_drake",       "rate": 0.120, "is_boss": True},
    {"key": "pet_thunderbird", "rate": 0.080, "is_boss": True},
    {"key": "pet_griffin",     "rate": 0.020, "is_boss": True},
]

# 垂钓/采集特殊渠道概率定义在 core/constants.py（PET_EGG_ORANGE_CHANCE / RARE_MAT_CHANCE），单一来源。


def make_pet_egg(pet_key):
    """构造宠物蛋物品(入包用)。pet_key 不存在时兜底为狼崽蛋。"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), PET_POOL[0])
    q = p.get("quality", "white")
    qname = _quality_name(q)
    return {"name": f"{p['name']}蛋", "type": "宠物蛋", "pet_key": p["key"], "stackable": True,
            "price": 200, "quality": q,
            "desc": f"{qname}宠物蛋，使用后可孵化出『{p['name']}』"}


def _quality_name(q):
    """品质显示名：普通/优秀/稀有/史诗/传说（复用 equipment.QUALITY，无则白板）"""
    from ..data.equipment import QUALITY
    return QUALITY.get(q, {}).get("name", "普通")


def pet_quality_label(pet_key):
    """宠物品质标签：🟣史诗（面板/详情用）"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), None)
    if not p:
        return ""
    from ..data.equipment import QUALITY
    q = QUALITY.get(p.get("quality", "white"), {})
    return f"{q.get('color', '⚪')}{q.get('name', '普通')}"


# 宠物技能类型 → 描述模板（v101.3：加新技能类型 = 加一行，改文案不动逻辑）
_PET_SKILL_DESC = {
    "atk_pct":  lambda p, iv: f"每 {iv} 回合 {int(p['skill_value']*100)}% 攻击伤害",
    "matk_pct": lambda p, iv: f"每 {iv} 回合 {int(p['skill_value']*100)}% 魔攻伤害",
    "heal_pct": lambda p, iv: f"每 {iv} 回合回复 {int(p['skill_value']*100)}% 生命",
    "block":    lambda p, iv: f"每 {iv} 回合 {int(p['skill_value']*100)}% 概率挡一次攻击",
    "lifesteal": lambda p, iv: f"每 {iv} 回合 {int(p['skill_value']*100)}% 攻击伤害并吸血回复一半",
    "pierce":   lambda p, iv: f"每 {iv} 回合 {int(p['skill_value']*100)}% 攻击伤害并破防 2 回合",
    "buff_atk": lambda p, iv: f"每 {iv} 回合为 {int(p['skill_value']*100)}% 攻击加成(2 回合)",
    "crit_up":  lambda p, iv: f"每 {iv} 回合为 {int(p['skill_value']*100)}% 暴击加成(2 回合)",
}


def pet_skill_label(pet_key):
    """宠物技能一句话描述(面板用)，如「撕咬(每 3 回合 40% 攻击伤害)」"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), None)
    if not p:
        return ""
    detail = _PET_SKILL_DESC.get(p["skill_type"], lambda p, iv: "")(p, p["skill_interval"])
    return f"{p['skill_name']}({detail})"


def pet_line(pet_key):
    """宠物随机战斗台词（无则返回空串；v101.11 活人感）"""
    import random
    p = next((x for x in PET_POOL if x["key"] == pet_key), None)
    if not p:
        return ""
    lines = p.get("lines") or []
    return random.choice(lines) if lines else ""


def pet_exp_need(level):
    """升级所需经验：level * 50(1→10 累计 2250)。"""
    return level * 50
