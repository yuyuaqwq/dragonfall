# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - mounts.py

坐骑 11 种（v101.11 扩容至 10，原 3 种；v124 新增雾羽候鸟）。品质统一复用 equipment.QUALITY 5 档。
效果字段（全部可叠加，骑乘中生效）：
  discount       传送费折扣（已有）
  elite_bonus    探索精英率加成（已有）
  stamina_reduce 探索/移动有概率不消耗体力（v101.11 新增，值=概率）
  sell_bonus     出售物品价格加成（v101.11 新增，值=百分比）
  collect_bonus  采集产出加成（v101.11 新增，值=概率额外一份）
  fish_bonus     钓鱼产出加成（v101.11 新增，值=概率额外一条）
  exp_mult       战斗经验加成（v101.11 新增，值=百分比）
"""
MOUNT_POOL = [
    # ---------- ⚪ 普通（商店直购） ----------
    {"key": "mount_horse", "name": "老马", "icon": "🐴", "quality": "white", "lv": 1, "price": 500,
     "discount": 0.10, "elite_bonus": 0.0, "stamina_reduce": 0.0, "sell_bonus": 0.0,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "温顺可靠的老马，腿脚虽慢但从不尥蹶子。传送费－10%"},
    {"key": "mount_donkey", "name": "小毛驴", "icon": "🫏", "quality": "white", "lv": 5, "price": 300,
     "discount": 0.05, "elite_bonus": 0.0, "stamina_reduce": 0.0, "sell_bonus": 0.05,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "倔脾气但很能驮，货郎的最爱。传送费－5%，出售价格＋5%(商店直购)"},
    # ---------- 🟢 优秀 ----------
    {"key": "mount_steed", "name": "骏马", "icon": "🐎", "quality": "green", "lv": 15, "price": 0,
     "discount": 0.20, "elite_bonus": 0.0, "stamina_reduce": 0.0, "sell_bonus": 0.0,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "脚程极快的良种骏马，跑商赶路两不误。传送费－20%(精英掉落『骏马缰绳』)"},
    {"key": "mount_camel", "name": "铁港驼马", "icon": "🐫", "quality": "green", "lv": 20, "price": 0,
     "discount": 0.15, "elite_bonus": 0.0, "stamina_reduce": 0.0, "sell_bonus": 0.10,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "铁港商队驯养的驮兽。传送费－15%，出售价格＋10%(稀有级垂钓产出『驼马缰绳』)"},
    # ---------- 🔵 稀有 ----------
    {"key": "mount_wolf", "name": "雪狼", "icon": "🐺", "quality": "blue", "lv": 30, "price": 0,
     "discount": 0.30, "elite_bonus": 0.05, "stamina_reduce": 0.0, "sell_bonus": 0.0,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "北境驯化的雪狼，嗅觉灵敏专挑厉害的打。传送费－30%，探索精英率＋5%(Boss 掉落『雪狼缰绳』)"},
    {"key": "mount_reindeer", "name": "北境驯鹿", "icon": "🦌", "quality": "blue", "lv": 35, "price": 0,
     "discount": 0.25, "elite_bonus": 0.0, "stamina_reduce": 0.15, "sell_bonus": 0.0,
     "collect_bonus": 0.05, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "踏雪无痕的北境驯鹿。传送费－25%，探索/移动 15% 概率不耗体力，采集产出＋5%(北境采集稀有产出『驯鹿缰绳』)"},
    # ---------- 🟣 史诗 ----------
    {"key": "mount_ghost", "name": "幽灵马", "icon": "👻", "quality": "purple", "lv": 45, "price": 0,
     "discount": 0.40, "elite_bonus": 0.0, "stamina_reduce": 0.0, "sell_bonus": 0.0,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.05,
     "desc": "午夜马厩里走出的幻影。传送费－40%，战斗经验＋5%(Boss 稀有掉落『幽灵缰绳』)"},
    {"key": "mount_unicorn", "name": "森林独角兽", "icon": "🦄", "quality": "purple", "lv": 45, "price": 0,
     "discount": 0.30, "elite_bonus": 0.05, "stamina_reduce": 0.10, "sell_bonus": 0.0,
     "collect_bonus": 0.10, "fish_bonus": 0.0, "exp_mult": 0.0,
     "desc": "银月林海的圣兽。传送费－30%，精英率＋5%，探索/移动 10% 概率不耗体力，采集产出＋10%(传说级垂钓稀有产出『独角兽缰绳』)"},
    # v124 隐藏线·候鸟的信：速度类坐骑（传送折扣+体力节省双速度向效果）
    {"key": "mount_fogbird", "name": "雾羽候鸟", "icon": "🕊️", "quality": "purple", "lv": 50, "price": 0,
     "discount": 0.30, "elite_bonus": 0.05, "stamina_reduce": 0.20, "sell_bonus": 0.0,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.05,
     "desc": "翅羽如雾的候鸟之王，日行千里。传送费－30%，探索/移动 20% 概率不耗体力，精英率＋5%，经验＋5%(v124 隐藏线·候鸟的信 hq7_3 奖励『雾羽候鸟缰绳』)"},
    # ---------- 🟠 传说 ----------
    {"key": "mount_griffin", "name": "狮鹫", "icon": "🦅", "quality": "orange", "lv": 60, "price": 0,
     "discount": 0.40, "elite_bonus": 0.10, "stamina_reduce": 0.20, "sell_bonus": 0.10,
     "collect_bonus": 0.0, "fish_bonus": 0.0, "exp_mult": 0.10,
     "desc": "翱翔天际的传说坐骑。传送费－40%，精英率＋10%，探索/移动 20% 概率不耗体力，出售＋10%，经验＋10%(Boss 极稀有掉落『狮鹫缰绳』)"},
    {"key": "mount_warhorse", "name": "炎蹄战马", "icon": "🔥", "quality": "orange", "lv": 55, "price": 0,
     "discount": 0.35, "elite_bonus": 0.05, "stamina_reduce": 0.10, "sell_bonus": 0.0,
     "collect_bonus": 0.0, "fish_bonus": 0.10, "exp_mult": 0.05,
     "desc": "蹄下燃着烈焰的战争坐骑。传送费－35%，精英率＋5%，探索/移动 10% 概率不耗体力，钓鱼产出＋10%，经验＋5%(Boss 极稀有掉落『炎蹄缰绳』)"},
]

MOUNT_BY_KEY = {m["key"]: m for m in MOUNT_POOL}

# v39 缰绳掉落表（精英/Boss 独立表，可继续加）
MOUNT_DROP_ELITE = {"mount_steed": 0.06}
MOUNT_DROP_BOSS = {"mount_wolf": 0.10, "mount_ghost": 0.04, "mount_warhorse": 0.02, "mount_griffin": 0.01}
