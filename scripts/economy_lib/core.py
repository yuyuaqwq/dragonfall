# -*- coding: utf-8 -*-
"""economy_lib.core —— 经济模型核心计算（分阶段 × 多维度）

维度（每阶段一行 economy_row）：
  产出侧：怪金曲线 → 掉落价值 → 卖店回收 → 任务金币
  装备成本侧：蓝装推导价 / 强化期望 / 升级成本 / 锻造成本
  生活成本：住宿
  材料供需：掉落单种数量（供给）vs 配方需求（消耗）
  比率：蓝装≈几只怪 / 锻造成本占产物比 / 掉落数量

数据源全部实读 game/data + game/core，禁止硬编码魔法数（与 numeric_lib 同原则）。
"""
import statistics
import random
from .env import setup_env  # noqa
from .constants import (
    ECON_STAGES, DROP_VALUE_MULT, MATERIAL_SELL_RATE, MAIN_QUEST_GOLD_MULT,
    CRAFT_COST_RATIO_MIN, CRAFT_COST_RATIO_MAX,
)
# 只走插件根路径（import game.data as D 风格），避免 data.plugins 全包双路径循环
import game.data as D  # noqa: E402  触发 _assembly（先加载 data 包）
from game.core import stats as S  # noqa: E402
from game.core.drops import generate_roster_equip  # noqa: E402

random.seed(20260902)


# ---------------- 产出侧 ----------------
def per_kill_gold(lv: int, role: str = "dps") -> int:
    """单只普通怪金币（dps 口径，role 合法取 role）。"""
    if role not in S.MONSTER_GOLD_BASE:
        role = "dps"
    return S.monster_gold(lv, role)


def drop_value(lv: int) -> int:
    """掉落价值 = 怪金 × 1.5（v93 折算成材料）。"""
    return int(per_kill_gold(lv) * DROP_VALUE_MULT)


def income_per_10_kills(lv: int) -> int:
    """打 10 只普通怪 → 材料卖店回收（材料回收 0.9）。"""
    return int(drop_value(lv) * MATERIAL_SELL_RATE * 10)


# ---------------- 装备成本侧 ----------------
def _roster_prices(quality: str, lv: int, tolerance: int = 2) -> list:
    """名册中该品质 & 等级接近装备的推导价列表（确定性生成）。"""
    out = []
    for rid, r in D.EQUIP_ROSTER.items():
        if r.get("quality") == quality and abs(r.get("lv", 0) - lv) <= tolerance:
            try:
                out.append(generate_roster_equip(rid)["price"])
            except Exception:
                continue
    return out


def equip_price(lv: int, quality: str = "blue") -> int | None:
    """该等级蓝装（或指定品质）推导价中位。"""
    ps = _roster_prices(quality, lv)
    if not ps:
        # 放宽容差
        ps = _roster_prices(quality, lv, tolerance=5)
    return int(statistics.median(ps)) if ps else None


def enhance_expected_cost(target: int = 9) -> int:
    """强化到 target 的期望金币成本（成功率的倒数×cost 累加）。"""
    # 实读 ENHANCE_TABLE
    table = dict(D.ENHANCE_TABLE)
    total = 0
    for lv in range(1, target + 1):
        entry = table.get(lv, {})
        cost = entry.get("cost", 0)
        rate = entry.get("rate", 1.0)
        total += int(cost / max(rate, 0.01))
    return total


def upgrade_full_cost() -> int:
    """升级 0→10 总金币成本（UPGRADE_TABLE）。"""
    try:
        table = D.UPGRADE_TABLE
        return sum(int(r.get("cost", 0)) for r in table) if isinstance(table, list) else 0
    except Exception:
        return 0


def craft_cost(lv: int, quality: str = "blue") -> int | None:
    """本阶段一件蓝装锻造的材料+金币成本中位。"""
    costs = []
    for rid, rec in D.CRAFT_RECIPES.items():
        if rec.get("quality") != quality:
            continue
        if abs(rec.get("lv", 0) - lv) > 3:
            continue
        mats = rec.get("mats", {})
        if not mats:
            continue
        mc = sum(D.MATERIALS.get(m, {}).get("price", 0) * q for m, q in mats.items())
        costs.append(mc + rec.get("gold", 0))
    return int(statistics.median(costs)) if costs else None


def craft_cost_ratio(lv: int, quality: str = "blue") -> float | None:
    """锻造材料+金币成本 / 产物价 中位比率。"""
    prod = equip_price(lv, quality)
    cc = craft_cost(lv, quality)
    if not prod or not cc:
        return None
    return cc / prod


# ---------------- 生活成本 ----------------
def inn_cost(lv: int) -> int:
    """住宿费（econ_config 公式）。"""
    cfg = D.ECON_CONFIG
    if lv <= cfg.get("inn_cost_lv_cap", 15):
        return max(cfg.get("inn_cost_min_low", 30), lv * cfg.get("inn_cost_per_lv", 5))
    # Lv16+：向下取整到百
    raw = max(cfg.get("inn_cost_min_high", 100), lv * cfg.get("inn_cost_per_lv", 5) * cfg.get("inn_cost_high_mult", 2.0))
    return int(raw // 100 * 100)


# ---------------- 材料供需 ----------------
def _mat_sources() -> dict:
    """材料名 → 产出它的怪等级列表（从 MAPS 掉落池）。"""
    mat_src = {}
    mat_names = {v.get("name", k): k for k, v in D.MATERIALS.items()}
    for m in D.MAPS:
        for sub in m.get("subareas", []):
            for mon in sub.get("monsters", []):
                if len(mon) < 6:
                    continue
                for d in mon[5]:
                    if isinstance(d, str) and d in mat_names:
                        mat_src.setdefault(d, []).append(mon[3])
    return mat_src


def drop_count_sim(lv: int, role: str = "dps") -> dict:
    """单只怪材料掉落数量仿真（按 combat._handle_victory 同公式）。

    返回 {avg_count, max_count, per_mat: {材料名: 数量}}（取该等级附近怪配置均值）
    """
    mat_src = _mat_sources()
    mat_price = {v.get("name", k): v.get("price", 0) for k, v in D.MATERIALS.items()}
    rows = []
    for m in D.MAPS:
        for sub in m.get("subareas", []):
            for mon in sub.get("monsters", []):
                if len(mon) < 6:
                    continue
                if mon[2] != role or abs(mon[3] - lv) > 3:
                    continue
                drops = [d for d in mon[5] if isinstance(d, str) and d in mat_price]
                if not drops:
                    continue
                g = S.monster_gold(mon[3], role if role in S.MONSTER_GOLD_BASE else "dps")
                mv = int(g * 1.5)
                picks_n = 2 if role in ("elite", "boss") else 1
                per = mv / min(picks_n, len(drops))
                for d in drops:
                    p = mat_price[d]
                    if p <= 0:
                        continue
                    n = max(1, min(99, int(per / len(drops) / p)))
                    rows.append((n, d, p, mon[3], mon[1]))
    if not rows:
        return {"avg_count": None, "max_count": None, "samples": [], "role": role, "lv": lv}
    counts = [r[0] for r in rows]
    return {
        "avg_count": round(statistics.mean(counts), 1),
        "max_count": max(counts),
        "over_cap": sum(1 for c in counts if c > 4),
        "samples": sorted(rows, key=lambda x: -x[0])[:5],
        "role": role, "lv": lv,
    }


# ---------------- 主行 ----------------
def economy_row(stage_id: str, sample_lv: int) -> dict:
    """单阶段经济账本行。"""
    g = per_kill_gold(sample_lv)
    dv = drop_value(sample_lv)
    inc10 = income_per_10_kills(sample_lv)
    blue_p = equip_price(sample_lv, "blue")
    enh9 = enhance_expected_cost(9)
    upg = upgrade_full_cost()
    craft_c = craft_cost(sample_lv, "blue")
    craft_r = craft_cost_ratio(sample_lv, "blue")
    inn = inn_cost(sample_lv)
    dc = drop_count_sim(sample_lv, "dps")
    return {
        "stage": stage_id, "lv": sample_lv,
        "per_kill_gold": g, "drop_value": dv, "income_10_kills": inc10,
        "blue_price": blue_p,
        "blue_kills": round(blue_p / max(inc10 / 10, 1), 1) if blue_p else None,
        "enhance9_cost": enh9,
        "enhance9_blue_ratio": round(enh9 / blue_p, 2) if blue_p else None,
        "upgrade_full_cost": upg,
        "craft_cost": craft_c,
        "craft_cost_ratio": round(craft_r, 2) if craft_r else None,
        "inn_cost": inn,
        "drop_avg_count": dc["avg_count"],
        "drop_max_count": dc["max_count"],
        "drop_over_cap": dc.get("over_cap", 0),
        "drop_samples": dc.get("samples", []),
    }


def economy_scan() -> dict:
    """全阶段经济扫描。"""
    rows = [economy_row(sid, sample_lv) for sid, _, _, sample_lv, _ in ECON_STAGES]
    return {"stages": rows}


def check_health(row: dict) -> list:
    """对单行输出健康带违规清单。"""
    issues = []
    if row["blue_price"]:
        bk = row["blue_kills"]
        if bk is not None:
            if bk < 8:
                issues.append(f"蓝装≈{bk}只怪 < 8（太便宜）")
            elif bk > 20:
                issues.append(f"蓝装≈{bk}只怪 > 20（太贵）")
        er = row["enhance9_blue_ratio"]
        if er is not None and er > 3.0:
            issues.append(f"强化+9={er:.1f}×蓝装 > 3×")
    cr = row["craft_cost_ratio"]
    if cr is not None:
        if cr < CRAFT_COST_RATIO_MIN:
            issues.append(f"锻造成本占产物 {cr*100:.0f}% < 40%（材料无成本）")
        elif cr > CRAFT_COST_RATIO_MAX:
            issues.append(f"锻造成本占产物 {cr*100:.0f}% > 70%（亏本）")
    if row["drop_avg_count"] is not None and row["drop_avg_count"] > 4:
        issues.append(f"平均掉 {row['drop_avg_count']} 个/材料 > 4（数量膨胀）")
    if row["drop_max_count"] is not None and row["drop_max_count"] > 6:
        issues.append(f"最大掉 {row['drop_max_count']} 个（爆量）")
    return issues


# ---------------- 副业维度（炼金/烹饪 成本-价值检查） ----------------
def _key_price(k):
    """材料/物品 key → 现价"""
    if k in D.MATERIALS:
        return D.MATERIALS[k].get("price", 0)
    if k in D.ITEMS:
        return D.ITEMS[k].get("price", 0)
    return 0


def profession_scan() -> dict:
    """炼金/烹饪全配方成本 vs 产品价 扫描。

    返回 {alchemy: {total, broken:[...], overpriced:[...]},
          cooking: {...}}
    broken     = 材料成本 > 产品价×0.9（亏本做）
    overpriced = 成本 < 产品价×0.2（暴利，价虚高）
    """
    out = {}
    for sect, recipes in (("alchemy", D.ALCHEMY_RECIPES), ("cooking", D.COOKING_RECIPES)):
        total = 0
        broken, overpriced = [], []
        for k, rec in recipes.items():
            total += 1
            cost = sum(_key_price(m) * q for m, q in rec.get("cost", {}).items())
            prod_key = next(iter(rec.get("product", {})), None)
            prod_price = _key_price(prod_key) if prod_key else 0
            if prod_price <= 0:
                continue
            ratio = cost / prod_price
            if ratio > 0.9:
                broken.append({"name": rec.get("name", k), "min_lv": rec.get("min_lv"),
                               "cost": cost, "prod": prod_price, "ratio": round(ratio, 2)})
            elif ratio < 0.2:
                overpriced.append({"name": rec.get("name", k), "min_lv": rec.get("min_lv"),
                                   "cost": cost, "prod": prod_price, "ratio": round(ratio, 2)})
        out[sect] = {"total": total, "broken": broken, "overpriced": overpriced}
    return out
