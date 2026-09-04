# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - pets.py

24 章《宠物与伙伴系统》：16 品种（v101.11 扩容至 14，原 4 品种；v124 新增月尾狐/星羽候鸟），Lv.10 解锁宠物技能，饱食度系统。
品质统一复用 equipment.QUALITY 5 档（⚪普通/🟢优秀/🔵稀有/🟣史诗/🟠传说），全项目一致。
掉落表 PET_EGG_ROLL 数据化（v101.11 从 combat.py 硬编码迁入），加新宠物 = 加一行。

宠物技能类型：
  atk_pct   每 N 刻帮主人造成 攻击力 × value 伤害
  matk_pct  每 N 刻造成 魔攻 × value 伤害
  heal_pct  每 N 刻为主人回复 max_hp × value 生命
  block     每 N 刻 value 概率替主人挡一次攻击（敌方行动时触发）
  lifesteal 每 N 刻造成 攻击 × value 伤害，并回复伤害 50% 生命（v101.11 新增）
  pierce    每 N 刻造成 攻击 × value 伤害，并破防（敌方防御减半，持续 2 刻）（v101.11 新增）
  buff_atk  每 N 刻为主人加 攻击 ×(1+value) 攻击 buff（持续 2 刻）（v101.11 新增）
  crit_up   每 N 刻为主人加暴击 +value（持续 2 刻）（v101.11 新增）
"""

PET_POOL = [
    # ---------- ⚪ 普通 ----------
    {"key": "pet_wolf",   "name": "森林狼崽", "icon": "🐺", "quality": "white", "focus": "攻击",
     "skill_name": "撕咬", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.40, "spd": 50,
     "source": "野外兽类怪(狼/狗/野猪/熊)掉落狼崽蛋",
     "desc": "忠诚的森林伙伴，每 3 刻帮主人撕咬敌人造成攻击伤害",
     "lines": ["嗷呜！", "汪！主人我上啦！", "（龇牙）交给我！"]},
    {"key": "pet_turtle", "name": "铁壳龟", "icon": "🐢", "quality": "white", "focus": "防守",
     "skill_name": "铁壁缩壳", "skill_interval": 4, "skill_type": "block", "skill_value": 0.15, "spd": 30,
     "source": "新手任务(主线 reward_pet) + 蓝档垂钓稀有产出",  # v105 M17 P2-3：橡木镇新手任务渠道已实装（reward_pet 接 world.py、quests.py，垂钓 blue 档接 economy.py），文案与实现对齐
     "desc": "慢吞吞但硬邦邦，每 4 刻有 15% 概率替主人挡下一次攻击",
     "lines": ["……（缩头）", "壳！", "慢慢来，比较快。"]},
    # ---------- 🟢 优秀 ----------
    {"key": "pet_cat",    "name": "黑猫", "icon": "🐈‍⬛", "quality": "green", "focus": "敏捷",
     "skill_name": "影袭", "skill_interval": 3, "skill_type": "block", "skill_value": 0.25, "spd": 65,
     "source": "精英怪概率掉落(城市/密林精英)",
     "desc": "神秘的黑猫，每 3 刻有 25% 概率替主人挡下一次攻击",
     "lines": ["喵——！", "（无声的扑击）", "影子会保护你。"]},
    {"key": "pet_rabbit", "name": "月光兔", "icon": "🐇", "quality": "green", "focus": "恢复",
     "skill_name": "月光祝福", "skill_interval": 4, "skill_type": "heal_pct", "skill_value": 0.08, "spd": 40,
     "source": "采集点/垂钓稀有产出(特殊蛋)",
     "desc": "月光下诞生的灵兔，每 4 刻为主人回复 8% 生命",
     "lines": ["（抖耳朵）月光在照耀！", "咕噜噜～", "别怕，我带着月亮的温柔。"]},
    {"key": "pet_dove",   "name": "圣光鸽", "icon": "🕊️", "quality": "green", "focus": "恢复",
     "skill_name": "圣光羽翼", "skill_interval": 4, "skill_type": "heal_pct", "skill_value": 0.12, "spd": 45,
     "source": "垂钓稀有产出(blue 档)圣光鸽蛋",
     "desc": "教会的信使，每 4 刻为主人回复 12% 生命",
     "lines": ["咕咕！愿圣光护佑你！", "（羽翼洒下光尘）", "光明与你同在。"]},
    # ---------- 🔵 稀有 ----------
    {"key": "pet_fox",    "name": "冰晶狐", "icon": "🦊", "quality": "blue", "focus": "元素",
     "skill_name": "霜刃", "skill_interval": 3, "skill_type": "matk_pct", "skill_value": 0.50, "spd": 45,
     "source": "北境野外怪(狐/貂/雪兽)掉落冰晶狐蛋",
     "desc": "北境雪原的精灵，每 3 刻以霜刃造成 50% 魔攻伤害",
     "lines": ["（尾巴凝出冰霜）", "霜雪会埋葬敌人！", "嘶——好冷！"]},
    {"key": "pet_salamander", "name": "火尾蜥", "icon": "🦎", "quality": "blue", "focus": "元素",
     "skill_name": "烈焰尾击", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.55, "spd": 48,
     "source": "火山/沙漠野外怪(蜥/火蛇)掉落火尾蜥蛋",
     "desc": "尾尖燃着不灭的火焰，每 3 刻以烈焰尾击造成 55% 攻击伤害",
     "lines": ["嘶嘶——！", "（尾巴甩出火星）", "烧起来啦！"]},
    {"key": "pet_panther", "name": "影豹", "icon": "🐆", "quality": "blue", "focus": "敏捷",
     "skill_name": "狩猎之眼", "skill_interval": 3, "skill_type": "crit_up", "skill_value": 0.20, "spd": 70,
     "source": "密林精英怪概率掉落影豹蛋",
     "desc": "潜伏在密林阴影中的猎手，每 3 刻为主人加持 20% 暴击(2 刻)",
     "lines": ["（瞳孔收缩）", "猎物……跑不掉的。", "狩猎开始！"]},
    # ---------- 🟣 史诗 ----------
    # v124 隐藏线·候鸟的信：星羽候鸟蛋（hq7_3 奖励，可孵化星羽候鸟）
    {"key": "pet_starswift", "name": "星羽候鸟", "icon": "🐦", "quality": "purple", "focus": "敏捷",
     "skill_name": "星羽疾风", "skill_interval": 3, "skill_type": "crit_up", "skill_value": 0.25, "spd": 75,
     "source": "v124 隐藏线·候鸟的信(hq7_3)奖励星羽候鸟蛋",
     "desc": "翅羽缀满星光的候鸟，每 3 刻以星羽疾风为主人加持 25% 暴击(2 刻)",
     "lines": ["啾——！（星羽闪烁）", "风会带我到任何地方！", "（盘旋一圈，洒下星尘）"]},
    {"key": "pet_drake",  "name": "龙裔幼崽", "icon": "🐉", "quality": "purple", "focus": "元素",
     "skill_name": "龙息", "skill_interval": 4, "skill_type": "matk_pct", "skill_value": 0.60, "spd": 40,
     "source": "Boss 概率掉落(龙系/精英 Boss)",
     "desc": "龙族的幼崽，每 4 刻喷吐龙息造成 60% 魔攻伤害",
     "lines": ["吼——！（喷出一小团火）", "吾之血脉，燃烧！", "（龙威初显）"]},
    {"key": "pet_bat",    "name": "血蝠", "icon": "🦇", "quality": "purple", "focus": "攻击",
     "skill_name": "吸血撕咬", "skill_interval": 4, "skill_type": "lifesteal", "skill_value": 0.30, "spd": 55,
     "source": "洞穴/墓穴精英怪概率掉落血蝠蛋",
     "desc": "暗夜中的吸血鬼，每 4 刻撕咬造成 30% 攻击伤害，回复伤害一半的生命",
     "lines": ["叽叽叽！", "（蝠翼展开）", "献上你的血……哦不是，你的败北！"]},
    {"key": "pet_armadillo", "name": "岩甲兽", "icon": "🦔", "quality": "purple", "focus": "防守",
     "skill_name": "碎岩冲撞", "skill_interval": 4, "skill_type": "pierce", "skill_value": 0.35, "spd": 32,
     "source": "矿洞/山丘精英怪概率掉落岩甲兽蛋",
     "desc": "披着岩石甲壳的重装兽，每 4 刻冲撞造成 35% 攻击伤害并破防(敌方防御减半 2 刻)",
     "lines": ["哼哧哼哧！", "（滚成球冲出去）", "岩石的力量！"]},
    {"key": "pet_thunderbird", "name": "雷羽鸟", "icon": "🦅", "quality": "purple", "focus": "元素",
     "skill_name": "雷鸣鼓舞", "skill_interval": 4, "skill_type": "buff_atk", "skill_value": 0.30, "spd": 42,
     "source": "高地 Boss 概率掉落",
     "desc": "羽翼缠绕雷霆的战鸟，每 4 刻为主人加持 30% 攻击(2 刻)",
     "lines": ["嘎——！（雷光闪烁）", "雷霆之力，借给你！", "（羽毛噼啪作响）"]},
    # ---------- 🟠 传说 ----------
    {"key": "pet_griffin", "name": "幼年狮鹫", "icon": "🦁", "quality": "orange", "focus": "攻击",
     "skill_name": "狮鹫俯冲", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.70, "spd": 60,
     "source": "传说级 Boss 极稀有掉落",
     "desc": "天空之王的后裔，每 3 刻俯冲造成 70% 攻击伤害",
     "lines": ["嗷——！（展翅）", "天空，是我的猎场！", "俯冲！"]},
    {"key": "pet_starbutterfly", "name": "星灵蝶", "icon": "🦋", "quality": "orange", "focus": "恢复",
     "skill_name": "星辉治愈", "skill_interval": 3, "skill_type": "heal_pct", "skill_value": 0.15, "spd": 38,
     "source": "传说级垂钓稀有产出/神秘宝箱",
     "desc": "翅膀洒落星辉的传说之蝶，每 3 刻为主人回复 15% 生命",
     "lines": ["（翅膀洒下星尘）", "星光会治愈一切～", "（轻盈地绕着你飞）"]},
    # v124 宠物情缘线终奖：第 15 品种（设计稿标注『需新增第 15 品种』，西境精灵伴生兽）
    {"key": "pet_moonfox", "name": "月尾狐", "icon": "🦊", "quality": "orange", "focus": "恢复",
     "skill_name": "月华低语", "skill_interval": 3, "skill_type": "heal_pct", "skill_value": 0.15, "spd": 42,
     "source": "v124 宠物情缘支线(s69 终奖)奖励月尾狐蛋",
     "desc": "西境精灵的伴生兽，尾尖泛着月光，每 3 刻以月华低语为主人回复 15% 生命",
     "lines": ["嘤～（蹭蹭手心）", "月华所至，皆可安眠。", "（尾尖泛起温柔的月光）"]},
]

# v101.11 蛋掉落表数据化（原 combat.py 硬编码迁入）：
#   每项 {key, rate, role?, is_elite?, is_boss?, name_kw?}，命中条件全部满足才掷概率。
#   加新掉落渠道 = 加一行；条件语义：role=怪物定位 / is_elite / is_boss / name_kw=名字含任一关键词
PET_EGG_ROLL = [
    {"key": "pet_wolf",        "rate": 0.015, "role": "dps", "name_kw": ["狼", "狗", "野猪", "熊"]},
    {"key": "pet_salamander",  "rate": 0.015, "name_kw": ["蜥", "火蛇", "蛇"]},
    # v104 M17 P1-1/P2-2 修复：冰晶狐/火尾蜥蛋掉落去掉 role=dps 限制——
    #   全库无 dps 且名字含 狐/貂/雪兽 的怪物（荧光狐/极光狐为 healer/speedster），
    #   导致冰晶狐蛋永不掉落（图鉴 13/14 绝版）；火尾蜥同理仅雷蜥命中。
    #   现放宽为任意角色、名字含关键词即按 rate 掷蛋（source 文案与实现一致）。
    {"key": "pet_fox",         "rate": 0.015, "name_kw": ["狐", "貂", "雪兽", "鹿"]},
    {"key": "pet_cat",         "rate": 0.065, "is_elite": True},
    {"key": "pet_panther",     "rate": 0.035, "is_elite": True},
    {"key": "pet_bat",         "rate": 0.030, "is_elite": True},
    {"key": "pet_armadillo",   "rate": 0.030, "is_elite": True},
    {"key": "pet_drake",       "rate": 0.120, "is_boss": True},
    {"key": "pet_thunderbird", "rate": 0.080, "is_boss": True},
    {"key": "pet_griffin",     "rate": 0.020, "is_boss": True},
]

# 垂钓/采集特殊渠道概率定义在 core/constants.py（PET_EGG_ORANGE_CHANCE / RARE_MAT_CHANCE），单一来源。


# 宠物蛋按品质定价（v104 M17 P3：传说蛋与白蛋同价 200 → 参照 13 章物品价值分档）
_PET_EGG_PRICE = {"white": 100, "green": 150, "blue": 200, "purple": 300, "orange": 500}


def make_pet_egg(pet_key):
    """构造宠物蛋物品(入包用)。pet_key 不存在时兜底为狼崽蛋。"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), PET_POOL[0])
    q = p.get("quality", "white")
    qname = _quality_name(q)
    return {"name": f"{p['name']}蛋", "type": "宠物蛋", "pet_key": p["key"], "stackable": True,
            "price": _PET_EGG_PRICE.get(q, 100), "quality": q,
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
    "atk_pct":  lambda p, iv: f"每 {iv} 刻 {int(p['skill_value']*100)}% 攻击伤害",
    "matk_pct": lambda p, iv: f"每 {iv} 刻 {int(p['skill_value']*100)}% 魔攻伤害",
    "heal_pct": lambda p, iv: f"每 {iv} 刻回复 {int(p['skill_value']*100)}% 生命",
    "block":    lambda p, iv: f"每 {iv} 刻 {int(p['skill_value']*100)}% 概率挡一次攻击",
    "lifesteal": lambda p, iv: f"每 {iv} 刻 {int(p['skill_value']*100)}% 攻击伤害并吸血回复一半",
    "pierce":   lambda p, iv: f"每 {iv} 刻 {int(p['skill_value']*100)}% 攻击伤害并破防 2 刻",
    "buff_atk": lambda p, iv: f"每 {iv} 刻为 {int(p['skill_value']*100)}% 攻击加成(2 刻)",
    "crit_up":  lambda p, iv: f"每 {iv} 刻为 {int(p['skill_value']*100)}% 暴击加成(2 刻)",
}


def pet_skill_label(pet_key):
    """宠物技能一句话描述(面板用)，如「撕咬(每 3 刻 40% 攻击伤害)」"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), None)
    if not p:
        return ""
    detail = _PET_SKILL_DESC.get(p["skill_type"], lambda p, iv: "")(p, p["skill_interval"])
    return f"{p['skill_name']}({detail})"


# v133.2 宠物经验加成品质分级（鱼鱼拍板 2026-08-28）：
#   加成 = min(等级 × 每级加成, 上限)，10 级满档；饱食度=0 减半逻辑在战斗结算/面板处。
#   品质越高每级越多（等差），上限越高——高品质宠物值得养，白宠保底成长线。
# v173.2 鱼鱼拍板（2026-09-04）：宠物封顶 Lv.30（先做 30，以后需要再扩展）——
#   per_lv 按 30 级满 cap 配；配合 pet_exp_need 非线性拉长升级节奏。
#   Lv.10 解锁宠物技能（保留）。
PET_MAX_LEVEL = 30

PET_EXP_GRADE = {
    "white":  {"per_lv": 0.05 / 30, "cap": 0.05},   # ⚪ 白：30级满 5%
    "green":  {"per_lv": 0.10 / 30, "cap": 0.10},   # 🟢 绿：30级满 10%
    "blue":   {"per_lv": 0.15 / 30, "cap": 0.15},   # 🔵 蓝：30级满 15%
    "purple": {"per_lv": 0.20 / 30, "cap": 0.20},   # 🟣 紫：30级满 20%
    "orange": {"per_lv": 0.30 / 30, "cap": 0.30},   # 🟠 橙：30级满 30%
}


def pet_exp_bonus(pet) -> float:
    """宠物等级经验加成系数（0~0.3）；按品质查表，未知品质按白。
    v133.2：per_lv 品质分级（每级加成 × 等级，cap 封顶）。
    v173.2 fix：去掉 int() 截断——per_lv 是小数系数(0.001~0.01)，
    int(level×per_lv) 恒为 0（v133.2 起宠物经验加成实际从未生效的 bug）；
    改 float 精确累加，30 级满品质 cap。"""
    p = next((x for x in PET_POOL if x["key"] == (pet or {}).get("pet_key")), None)
    g = PET_EXP_GRADE.get((p or {}).get("quality", "white"), PET_EXP_GRADE["white"])
    return min(max(float((pet or {}).get("level", 0) or 0) * g["per_lv"], 0.0), g["cap"])


def pct_str(x: float) -> str:
    """百分比显示：0.5 → '0.5'，5.0 → '5'（去尾零，宠物品质分级小数值用）。"""
    s = f"{x * 100:.1f}"
    return s[:-2] if s.endswith(".0") else s


def pet_line(pet_key):
    """宠物随机战斗台词（无则返回空串；v101.11 活人感）"""
    import random
    p = next((x for x in PET_POOL if x["key"] == pet_key), None)
    if not p:
        return ""
    lines = p.get("lines") or []
    return random.choice(lines) if lines else ""


def pet_exp_need(level):
    """升级所需经验（v173.2 非线性拉长，封顶 Lv.30 配套）：
    lv × 35 × (1 + lv/30)——1→10 累计约 1900（略慢于旧的 2750 的直觉，但 10 级前逐级 35-45
    很轻松），30 级满累计约 2.7 万 ≈ 主人打 250~460 只 30+ 级怪（约主人 45-50 级自然满）。
    旧（v118）：level×50 线性，40-80 只怪就 10 级满，宠物节奏远快于主人。"""
    return int(level * 35 * (1 + level / 30))


def pet_exp_mult(pet_lv: int, monster_lv: int) -> float:
    """宠物获得经验的等级差乘区（v173.2 鱼鱼拍板：复用玩家同款非线性曲线）。
    宠物等级 vs 怪等级差 diff = 怪lv - 宠lv：
      diff > 0（宠越级打高级怪）→ 奖励 1 + 0.015×diff²，封顶 ×2.0
      diff ∈ [-3, 0]（同级±3）→ 无惩罚 ×1.0
      diff < -3（宠碾压低级怪）→ 衰减 0.85^(-diff-3)，最低 15%
    与 combat.py 玩家经验曲线同一公式（v173.2a 压制同步 0.02→0.015/2.5→2.0），防两套口径。"""
    diff = monster_lv - pet_lv
    if diff > 0:
        mult = 1.0 + 0.015 * diff * diff
        return mult if mult < 2.0 else 2.0
    if diff < -3:
        mult = 0.85 ** (-diff - 3)
        return mult if mult > 0.15 else 0.15
    return 1.0
