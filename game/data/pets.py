# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - pets.py

24 章《宠物与伙伴系统》：4 品种，Lv.10 解锁宠物技能，饱食度系统。
旧版 7 品种（幼狼/黑猫/灵狐/夜枭/雏龙/火凤凰/幼年神龙）随删档废弃。
"""

# 宠物技能类型：
#   atk_pct   每 N 回合帮主人造成 攻击力 × value 伤害
#   matk_pct  每 N 回合造成 魔攻 × value 伤害
#   heal_pct  每 N 回合为主人回复 max_hp × value 生命
#   block     每 N 回合 value 概率替主人挡一次攻击（敌方行动时触发）
PET_POOL = [
    {"key": "pet_wolf",   "name": "森林狼崽", "icon": "🐺", "focus": "攻击",
     "skill_name": "撕咬", "skill_interval": 3, "skill_type": "atk_pct", "skill_value": 0.40,
     "source": "野外兽类怪（狼/野狗）掉落狼崽蛋",
     "desc": "忠诚的森林伙伴，每 3 回合帮主人撕咬敌人造成攻击伤害"},
    {"key": "pet_cat",    "name": "黑猫", "icon": "🐈⬛", "focus": "敏捷",
     "skill_name": "影袭", "skill_interval": 3, "skill_type": "block", "skill_value": 0.25,
     "source": "精英怪概率掉落（城市/密林精英）",
     "desc": "神秘的黑猫，每 3 回合有 25% 概率替主人挡下一次攻击"},
    {"key": "pet_drake",  "name": "龙裔幼崽", "icon": "🐉", "focus": "元素",
     "skill_name": "龙息", "skill_interval": 4, "skill_type": "matk_pct", "skill_value": 0.60,
     "source": "Boss 概率掉落（龙系/精英 Boss）",
     "desc": "龙族的幼崽，每 4 回合喷吐龙息造成魔攻伤害"},
    {"key": "pet_rabbit", "name": "月光兔", "icon": "🐇", "focus": "恢复",
     "skill_name": "月光祝福", "skill_interval": 4, "skill_type": "heal_pct", "skill_value": 0.08,
     "source": "采集点/垂钓稀有产出（特殊蛋）",
     "desc": "月光下诞生的灵兔，每 4 回合为主人回复生命"},
]


def make_pet_egg(pet_key):
    """构造宠物蛋物品（入包用）。pet_key 不存在时兜底为狼崽蛋。"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), PET_POOL[0])
    return {"name": f"{p['name']}蛋", "type": "宠物蛋", "pet_key": p["key"], "stackable": True,
            "price": 200, "desc": f"使用后可孵化出『{p['name']}』"}


def pet_skill_label(pet_key):
    """宠物技能一句话描述（面板用），如「撕咬（每 3 回合 40% 攻击伤害）」"""
    p = next((x for x in PET_POOL if x["key"] == pet_key), None)
    if not p:
        return ""
    interval = p["skill_interval"]
    if p["skill_type"] == "atk_pct":
        detail = f"每 {interval} 回合 {int(p['skill_value']*100)}% 攻击伤害"
    elif p["skill_type"] == "matk_pct":
        detail = f"每 {interval} 回合 {int(p['skill_value']*100)}% 魔攻伤害"
    elif p["skill_type"] == "heal_pct":
        detail = f"每 {interval} 回合回复 {int(p['skill_value']*100)}% 生命"
    elif p["skill_type"] == "block":
        detail = f"每 {interval} 回合 {int(p['skill_value']*100)}% 概率挡一次攻击"
    else:
        detail = ""
    return f"{p['skill_name']}（{detail}）"


def pet_exp_need(level):
    """升级所需经验：level * 50（1→10 累计 2250）。"""
    return level * 50
