# -*- coding: utf-8 -*-

from .stats import equip_stats, monster_exp, monster_gold, monster_stats
from .affix import (fixed_affixes, random_req, roll_affixes, stat_affix_stats)
import random

from .. import content as C
from ..data import (AFFIXES, AFFIX_POOL_BY_QUALITY, CLASS_SET_STAGES, CLASS_SET_THEMES,
                    EQUIP_NAME_PREFIX, EQUIP_NAME_SUFFIX,
                    EQUIP_PREFIX_FLAVOR, LEGENDARY_EFFECTS, QUALITY, SET_CHANCE, SET_THEMES,
                    SERIES_SETS, WEAPON_FLAVOR,
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
    """精英/Boss 掉图纸（阶段八：名册图纸化）。

    按怪物等级就近匹配 10 章名册中需要图纸的装备（source = 图纸/boss），
    返回图纸物品 data（type=图纸，blueprint_for=装备名，roster_id=名册 ID），
    学习后解锁对应名册配方（craft.py『学习』）。
    """
    cands = []
    for rid, r in C.EQUIP_ROSTER.items():
        if r["source"] in ("图纸", "boss"):
            cands.append((rid, r))
    if not cands:
        return None
    # 等级就近：优先 |lv - monster_lv| <= 15，再放宽
    near = [c for c in cands if abs(c[1]["lv"] - monster_lv) <= 15]
    pool = near or cands
    rid, r = random.choice(pool)
    q = QUALITY[r["quality"]]
    return {
        "name": f"{r['name']}图纸", "type": "图纸", "stackable": True,
        "price": int(r["lv"] * 3 + 20), "blueprint_for": r["name"], "roster_id": rid,
        "quality": r["quality"],
        # v56.4：玩家语言描述——不含内部 ID
        "desc": f"{q['name']}级图纸：{r['name']}（{C.EQUIP_SLOTS[r['slot']]}）",
    }

def roll_drop(monster_lv: int, role: str):
    """怪物死亡掉落（阶段八，20 章 4.1）：返回 (装备 or None, 图纸 or None, 金币, 经验)

    - 普通怪：12% 掉绿/蓝随机装备（固定词条 + 随机）
    - 精英：紫/蓝随机装备 + 名册图纸
    - Boss：橙/紫随机装备 + 名册图纸
    图纸与装备同时掉，消费端分别入包。
    """
    slots = ["weapon", "helm", "armor", "legs", "boots", "ring", "necklace"]
    if role == "elite":
        bp = roll_blueprint(monster_lv)
        eq = generate_equip(random.choice(slots), monster_lv,
                            random.choices(["purple", "blue"], [0.65, 0.35])[0])
        return eq, bp, 0, 0
    if role == "boss":
        bp = roll_blueprint(monster_lv)
        eq = generate_equip(random.choice(slots), monster_lv,
                            random.choices(["orange", "purple"], [0.35, 0.65])[0])
        return eq, bp, 0, 0
    # 普通怪 12% 掉绿/蓝
    if random.random() < 0.12:
        eq = generate_equip(random.choice(slots), monster_lv,
                            random.choices(["green", "blue"], [0.7, 0.3])[0])
        return eq, None, 0, 0
    return None, None, 0, 0

def generate_equip(slot: str, lv: int, quality: str, weapon_type: str | None = None):
    """生成一件随机装备（名称 + 属性 + 词条 v2 + 属性需求）。

    阶段八（2026-08-06）：词条从旧属性词条 [{'stat','value'}] 改为 20 章特效词条 ID 列表；
    常驻属性词条（暴击强化/闪避/生命强化/迅捷）折算进 stats；橙装随机挂 1 个传说专属；
    全部装备带属性需求（力量/智力/敏捷/耐力，不锁职业）。
    """
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
    # 阶段八：特效词条 v2（随机池 + 常驻属性折算）
    affix_ids = roll_affixes(slot, lv, quality)
    for k, v in stat_affix_stats(affix_ids, slot, lv).items():
        if k in ("crit", "dodge"):
            stats[k] = round(stats.get(k, 0) + v, 4)
        else:
            stats[k] = stats.get(k, 0) + int(v)
    equip = {
        "name": name,
        "slot": slot,
        "quality": quality,
        "lv": lv,
        "weapon_type": weapon_type if slot == "weapon" else None,
        "stats": stats,
        "price": int(sum(stats.values()) * (3 + lv * 0.5) * QUALITY[quality]["mult"]),
        # 阶段八：属性需求（不锁职业，只锁力量/智力/敏捷/耐力）
        "req": random_req(slot, lv, weapon_type),
    }
    if flavor_stats:
        equip["flavor"] = flavor_stats
    if affix_ids:
        equip["affixes"] = affix_ids
    # 阶段八：随机橙装挂 1 个传说专属
    if quality == "orange":
        equip["legendary"] = random.choice(list(LEGENDARY_EFFECTS.keys()))
    if set_name:
        equip["set"] = set_name
    return equip


def generate_roster_equip(rid: str, affinity: str | None = None) -> dict:
    """按 10 章名册精确生成一件装备（锻造/图纸/Boss 掉落/商店主推）。

    装备名 = 名册名（确定性）；词条 = 系列固定词条（20 章 3.x）+ 按品质随机补足；
    橙装挂名册专属；需求用名册 req；套装归属 = 系列套装名（10 章五节）。
    品质词条数：白 0 / 蓝 2（固定+随机补足）/ 紫 3 / 橙 3 + 专属。
    affinity（20 章 4.3 锻造词条倾向）：攻击/防御/元素/机动——随机补足从倾向池抽。
    """
    r = C.EQUIP_ROSTER[rid]
    slot, lv, quality = r["slot"], r["lv"], r["quality"]
    weapon_type = r.get("weapon_type")
    stats = equip_stats(slot, lv, quality)
    # v29 武器类型特色（名册武器同样吃类型风味）
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
    # 词条：系列固定 + 随机补足到品质标准数（蓝 2 / 紫 3 / 橙 3）
    fixed = fixed_affixes(r["name"])
    target_n = {"blue": 2, "purple": 3, "orange": 3}.get(quality, 0)
    random_n = max(0, target_n - len(fixed))
    pool = [a for a in AFFIX_POOL_BY_QUALITY.get(quality, AFFIX_POOL_BY_QUALITY["orange"])
            if a not in fixed]
    want_kind = "attack" if slot == "weapon" else "defense"
    pool = [a for a in pool if AFFIXES[a]["kind"] == want_kind]
    # 20 章 4.3：词条倾向 → 倾向池直接作为候选（过滤部位类型 + 固定词条）
    # 比品质随机池宽（如蓝装也能出元素词条），玩家主动指定合理
    if affinity:
        aff_pool = C.AFFIX_AFFINITY_POOLS.get(affinity, [])
        aff_pool = [a for a in aff_pool
                    if AFFIXES[a]["kind"] == want_kind and a not in fixed]
        if aff_pool:
            pool = aff_pool
    rnd = random.sample(pool, min(random_n, len(pool))) if pool and random_n else []
    affix_ids = fixed + rnd
    for k, v in stat_affix_stats(affix_ids, slot, lv).items():
        if k in ("crit", "dodge"):
            stats[k] = round(stats.get(k, 0) + v, 4)
        else:
            stats[k] = stats.get(k, 0) + int(v)
    equip = {
        "name": r["name"],
        "slot": slot,
        "quality": quality,
        "lv": lv,
        "weapon_type": weapon_type if slot == "weapon" else None,
        "stats": stats,
        "price": int(sum(stats.values()) * (3 + lv * 0.5) * QUALITY[quality]["mult"]),
        "req": dict(r["req"]),
        "series": r["series"],
    }
    if flavor_stats:
        equip["flavor"] = flavor_stats
    if affix_ids:
        equip["affixes"] = affix_ids
    if r.get("legendary"):
        equip["legendary"] = r["legendary"]
    # 阶段八：蓝以上名册装备挂系列套装（白装新手过渡，不触发套装）
    if r["series"] in SERIES_SETS and quality != "white":
        equip["set"] = SERIES_SETS[r["series"]]
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

