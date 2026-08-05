# -*- coding: utf-8 -*-

from .stats import equip_stats, monster_exp, monster_gold, monster_stats
from .affix import roll_affixes
import random

from .. import content as C
from ..data import (CLASS_SET_STAGES, CLASS_SET_THEMES, EQUIP_NAME_PREFIX, EQUIP_NAME_SUFFIX,
                    EQUIP_PREFIX_FLAVOR, QUALITY, SET_CHANCE, SET_THEMES, WEAPON_FLAVOR,
                    WEAPON_NAME_SUFFIX, WEAPON_TYPES)


"""《剑与魔法》数据层 - drops.py"""
def _stage_for_lv(monster_lv: int) -> dict:
    """怪物等级 → 毕业套阶段（就近取阶段等级）"""
    best = CLASS_SET_STAGES[0]
    for st in CLASS_SET_STAGES:
        if monster_lv >= st["lv"] - 5:
            best = st
    return best

def roll_blueprint(monster_lv: int):
    """精英/Boss 掉图纸：按怪物等级匹配阶段，随机掉一张该阶段职业图纸
    返回图纸物品 data（type=图纸），用于打造毕业套（必需材料）。
    """
    st = _stage_for_lv(monster_lv)
    label = st["label"]
    idx = CLASS_SET_STAGES.index(st)
    # 随机一个职业（同阶段 6 职业图纸等概率）
    cls = random.choice(list(CLASS_SET_THEMES.keys()))
    prefix = CLASS_SET_THEMES[cls]["stages"][idx]
    return {
        "name": f"{prefix}图纸", "type": "图纸", "stackable": True,
        "price": st["gold"] // 5, "blueprint_for": prefix,
        "stage": label, "class": cls,
        # v56.4：玩家语言描述——不含内部 ID、不含"毕业套"开发者术语
        "desc": f"{C.display('classes', cls)}·{prefix}套装打造图纸（{label}阶）",
    }

def roll_drop(monster_lv: int, role: str):
    """怪物死亡掉落：返回 (装备/图纸 or None, 材料名 or None, 金币, 经验)
    v41 装备 2.0：普通怪不再掉装备（0%）；精英/Boss 掉「图纸」而非成品装备，
    装备统一走打造（图纸是打造毕业套的必需材料）。
    """
    if role == "elite":
        bp = roll_blueprint(monster_lv)
        return bp, None, 0, 0
    if role == "boss":
        bp = roll_blueprint(monster_lv)
        return bp, None, 0, 0
    return None, None, 0, 0

def generate_equip(slot: str, lv: int, quality: str, weapon_type: str | None = None):
    """生成一件装备（名称 + 属性 + v10 词条/套装归属；v29 武器名与类型绑定+类型特色）
    v58：前缀风格 → 属性倾向（EQUIP_PREFIX_FLAVOR），名字真实影响手感"""
    set_name = None
    flavor_prefix = ""
    if slot == "weapon":
        if not weapon_type:
            weapon_type = random.choice(list(WEAPON_TYPES.keys()))
        base_name = EQUIP_NAME_PREFIX[quality][random.randrange(len(EQUIP_NAME_PREFIX[quality]))]
        flavor_prefix = base_name
        # v29：后缀从该武器类型的专属命名池取（杜绝"之弓"配剑）
        suffix = random.choice(WEAPON_NAME_SUFFIX[weapon_type])
        name = f"{base_name}{suffix}"
        if quality == "orange":
            name = f"传说·{base_name}{suffix}"
    else:
        prefix = EQUIP_NAME_PREFIX[quality][random.randrange(len(EQUIP_NAME_PREFIX[quality]))]
        flavor_prefix = prefix
        suffix = random.choice(EQUIP_NAME_SUFFIX[slot])
        name = f"{prefix}{suffix}"
    # v10：套装归属（蓝以上按品质概率，主题前缀即套装名）
    if quality in SET_THEMES and random.random() < SET_CHANCE.get(quality, 0):
        set_name = random.choice(SET_THEMES[quality])
        flavor_prefix = set_name  # v58：套装属性倾向跟随套装主题名
        if slot == "weapon":
            # v29：套装武器也用类型专属后缀
            suffix = random.choice(WEAPON_NAME_SUFFIX[weapon_type])
            name = f"{set_name}{suffix}"
        else:
            suffix = random.choice(EQUIP_NAME_SUFFIX[slot])
            name = f"{set_name}{suffix}"
    stats = equip_stats(slot, lv, quality)
    # v58：前缀属性倾向（名字风格真实影响手感）
    prefix_flavor = EQUIP_PREFIX_FLAVOR.get(flavor_prefix, {})
    if prefix_flavor:
        for fk, fv in prefix_flavor.items():
            if fk in ("crit", "dodge"):
                stats[fk] = round(stats.get(fk, 0) + fv, 3)
            else:
                stats[fk] = max(0, stats.get(fk, 0) + int(fv))
    # v29：武器类型特色加成（剑微暴击/法杖魔攻/弓速度暴击/匕首暴击/拳套攻击等）
    flavor = WEAPON_FLAVOR.get(weapon_type, {}) if slot == "weapon" else {}
    flavor_stats = {}
    if flavor:
        for fk, fv in flavor.items():
            if fk == "desc" or not isinstance(fv, (int, float)):
                continue
            if fk == "crit":
                stats["crit"] = round(stats.get("crit", 0) + fv, 3)
                flavor_stats["crit"] = fv
            elif fk == "spd_fix":
                stats["spd"] = stats.get("spd", 0) + int(fv)
                flavor_stats["spd"] = int(fv)
            elif fk == "hp_fix":
                stats["hp"] = stats.get("hp", 0) + int(fv)
                flavor_stats["hp"] = int(fv)
            else:
                add = int(stats.get(fk, 0) * fv)
                stats[fk] = stats.get(fk, 0) + add
                flavor_stats[fk] = add
    equip = {
        "name": name,
        "slot": slot,
        "quality": quality,
        "lv": lv,
        "weapon_type": weapon_type if slot == "weapon" else None,
        "stats": stats,
        "price": int(sum(stats.values()) * (3 + lv * 0.5) * QUALITY[quality]["mult"]),
    }
    if flavor_stats:
        equip["flavor"] = flavor_stats
    # v10：词条（独立于强化）
    affixes = roll_affixes(slot, lv, quality)
    if affixes:
        equip["affixes"] = affixes
    if set_name:
        equip["set"] = set_name
    return equip

def build_monster(monster_def: tuple, map_obj: dict):
    """将地图怪物配置展开为完整怪物字典
    v58：应用 MONSTER_MODS 个体修正（同 role 同等级不同怪数值错开）"""
    mid, name, role, lv, skills, drops = monster_def
    stats = monster_stats(lv, role)
    mod = C.MONSTER_MODS.get(mid, {})
    if mod:
        for k, mult in (("hp", "hp_mult"), ("atk", "atk_mult"), ("def", "def_mult"),
                        ("matk", "matk_mult"), ("mdef", "mdef_mult"), ("spd", "spd_mult")):
            if mult in mod:
                stats[k] = max(1, int(stats[k] * mod[mult]))
    is_boss = role == "boss"
    is_elite = role == "elite"
    return {
        "id": mid,
        "name": name,
        "lv": lv,
        "role": role,
        "hp": stats["hp"],
        "max_hp": stats["hp"],
        "atk": stats["atk"],
        "def": stats["def"],
        "matk": stats["matk"],
        "mdef": stats["mdef"],
        "spd": stats["spd"],
        "exp": monster_exp(lv, role),
        "gold": monster_gold(lv, role),
        "skills": skills,
        "drops": drops,
        "map": map_obj["name"],
        "map_area": map_obj.get("area", map_obj["id"]),
        "is_boss": is_boss,
        "is_elite": is_elite,
        "mech": mod.get("mech", ""),
        "mod": mod.get("desc", ""),
    }

