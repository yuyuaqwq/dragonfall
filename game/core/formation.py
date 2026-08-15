# -*- coding: utf-8 -*-
"""v2 多对多站位战斗引擎 —— 阵型纯函数工具（game/core/formation.py）

§3.1：不依赖 Battle 实例的纯函数，便于单测。单位用 dict 表示，站位字段：
  - rank : 当前站位层（1 前 → 3 后），压缩后可能变化
  - reach: 攻击范围（1=近战只打第 1 层 / 2=远程第 1-2 层 / 3=全域）

MAX_RANKS：层数上限（§2.1）。
"""
import random

MAX_RANKS = 3


def alive_units(units: list) -> list:
    """存活单位（hp>0）。返回新列表，不改输入。"""
    return [u for u in (units or []) if u.get("hp", 0) > 0]


def front_rank(units) -> int:
    """存活单位最小 rank；无存活返回 MAX_RANKS+1。"""
    alive = [u.get("rank", 1) for u in alive_units(units)]
    if not alive:
        return MAX_RANKS + 1
    return min(alive)


def reachable_units(attacker, units) -> list:
    """射程内存活单位（u.rank <= attacker.reach）。返回新列表。"""
    reach = int(attacker.get("reach", 1) or 1)
    return [u for u in units if u.get("hp", 0) > 0 and int(u.get("rank", 1) or 1) <= reach]


def select_target(attacker, units, threat=None, exclude_uid=None):
    """选择攻击目标。

    规则（§4.1）：射程内 → 最前排(最小 rank) → 同层随机（有 threat 表时同层按
    threat 最高，平局随机）。射程内无目标 → 兜底取最前排存活单位。exclude_uid
    排除指定单位（如已死的源单位）。

    返回 Unit|None。threat: {uid: 仇恨值}。
    """
    reach = int(attacker.get("reach", 1) or 1)
    alive = alive_units(units)
    if not alive:
        return None
    if exclude_uid:
        alive = [u for u in alive if u.get("uid") != exclude_uid]
    if not alive:
        return None
    # 射程内目标
    in_range = [u for u in alive if int(u.get("rank", 1) or 1) <= reach]
    pool = in_range if in_range else alive  # 兜底：最前排
    if not pool:
        return None
    # 最前排（最小 rank）
    min_rank = min(int(u.get("rank", 1) or 1) for u in pool)
    front = [u for u in pool if int(u.get("rank", 1) or 1) == min_rank]
    if not threat:
        if len(front) == 1:
            return front[0]
        return random.choice(front)
    # 同层按仇恨最高，平局随机
    max_th = max(float(threat.get(u.get("uid"), 0) or 0) for u in front)
    contenders = [u for u in front if float(threat.get(u.get("uid"), 0) or 0) >= max_th]
    if len(contenders) == 1:
        return contenders[0]
    return random.choice(contenders)


def select_aoe_targets(attacker, units, scope) -> list:
    """AOE 目标选择。

    scope ∈ "front"（当前最前排全部）/ "all"（全部存活）/ "rankN"（第 N 层全部，
    N 越界取最前排）。AOE 同样先按射程过滤（技能自带 reach 覆盖职业 reach 时按
    技能——attacker 的 reach 已被调用方设置为覆盖后的值）。

    返回目标列表（存活）。
    """
    reach = int(attacker.get("reach", 1) or 1)
    alive = alive_units(units)
    if not alive:
        return []
    in_range = [u for u in alive if int(u.get("rank", 1) or 1) <= reach]
    if not in_range:
        # 射程内无目标（兜底：最前排）
        mr = min(int(u.get("rank", 1) or 1) for u in alive)
        in_range = [u for u in alive if int(u.get("rank", 1) or 1) == mr]
    if scope in ("front", "rank"):
        mr = min(int(u.get("rank", 1) or 1) for u in in_range)
        return [u for u in in_range if int(u.get("rank", 1) or 1) == mr]
    if scope == "all":
        return list(in_range)
    if scope.startswith("rank"):
        try:
            n = int(scope[4:])
        except (ValueError, TypeError):
            n = 1
        layer = [u for u in in_range if int(u.get("rank", 1) or 1) == n]
        if layer:
            return layer
        # N 越界 → 取最前排
        mr = min(int(u.get("rank", 1) or 1) for u in in_range)
        return [u for u in in_range if int(u.get("rank", 1) or 1) == mr]
    # 未知 scope：默认最前排
    mr = min(int(u.get("rank", 1) or 1) for u in in_range)
    return [u for u in in_range if int(u.get("rank", 1) or 1) == mr]


def compact(units) -> list:
    """原地阵型压缩（§2.1）：存活单位按当前 rank 升序重排、rank 重编号为 1..K
    （同层内保持原有顺序）；死亡单位移除。

    返回被移除（死亡）的单位列表，供结算层发"倒下"文案。直接修改传入列表。
    """
    removed = []
    kept = []
    for u in (units or []):
        if u.get("hp", 0) > 0:
            kept.append(u)
        else:
            removed.append(u)
    # 原 rank 升序稳定排序（同层保持原顺序）
    kept.sort(key=lambda u: int(u.get("rank", 1) or 1))
    ranks = {}
    for u in kept:
        r = int(u.get("rank", 1) or 1)
        ranks.setdefault(r, []).append(u)
    new_rank = 1
    ordered = []
    for r in sorted(ranks):
        for u in ranks[r]:
            u["rank"] = new_rank
            ordered.append(u)
        new_rank += 1
    units[:] = ordered
    return removed


def formation_view(units) -> list:
    """生成站位图文案行（每层一行）。仅含存活单位；蓄力单位带"⏳蓄力中(剩N)"。

    示例：`1层: 🛡️ 战士 ❤️150 | 🔥 法师 ❤️90`
    """
    rows = []
    alive = alive_units(units)
    rows_map = {}
    for u in alive:
        r = int(u.get("rank", 1) or 1)
        rows_map.setdefault(r, []).append(u)
    for r in sorted(rows_map):
        parts = []
        for u in rows_map[r]:
            icon = u.get("icon", "") or ""
            nm = u.get("name", "单位")
            hp = u.get("hp", 0)
            seg = f"{icon} {nm} ❤️{hp}".strip()
            ch = u.get("charging")
            if ch:
                left = ch.get("left", 1)
                seg += f" ⏳蓄力中(剩{left})"
            parts.append(seg)
        rows.append(f"{r}层: " + " | ".join(parts))
    return rows
