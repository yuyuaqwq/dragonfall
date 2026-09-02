# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - smith_stock.py（v135 铁匠铺全服共享货架，2026-08-29）

全服共享限量货架（NPC 作品）：每城镇铁匠铺 4 件 = 2 武器 + 1 防具 + 1 饰品。
- 全服共享：event_state 用全局 key（不带 qq_id 后缀），所有玩家同一货架，先到先得
- 每日 0 点换货：读时惰性判定日期 ordinal 变化 → 全量重 roll
- 每 6 小时补货：restock_at 过期 → 保留未售罄件 + 补新品填满 4 件
- 品质权重：白 20 / 绿 25 / 蓝 35 / 紫 15 / 橙 5（紫橙可刷）
- 库存限购：每件 1~3 份（紫/橙 1 份，蓝绿 2-3 份），售罄即下架等补货
- 价格浮动：名册推导价 × 0.8~1.2 随机；保留 equip_resale_rate=0.5 防倒卖
- 命名：NPC 作品带『XX 的作品』后缀（SMITH_NPC_NAMES 按城镇映射）
- 随机池：EQUIP_ROSTER 按城镇等级 ±5 窗口 + 品质权重 sample，exclude 静态
  SHOP_EQUIP / SHOP_WEAPONS 已上架名册（避免与保底商店重复）
"""
import json
import random
import time
from datetime import date

from ..data import (EQUIP_ROSTER, EQUIP_ROSTER_BY_NAME, SHOP_EQUIP, SHOP_WEAPONS,
                   QUALITY, ECON_CONFIG, WEAPON_FLAVOR)  # noqa: F401
from ..core.stats import equip_stats, equip_value  # noqa: F401
# MAP_BY_ID/SUBAREAS 也延迟从 data 导入（防循环）
_MAP_BY_ID = {}
_SUBAREAS = {}


def _ensure_maps():
    global _MAP_BY_ID, _SUBAREAS
    if not _MAP_BY_ID:
        from ..data import MAP_BY_ID, SUBAREAS
        _MAP_BY_ID = MAP_BY_ID
        _SUBAREAS = SUBAREAS


# db 延迟导入：core 层在 data/_assembly 构建期被 import（content 尚未初始化完成），
# db 依赖 content.C_MAP_IDS → 循环导入。函数内惰性 from .. import db。
# v135：仅 get_smith_stock/buy_stock_item 用到 db，全部放函数体内导入。

# ================= 数值常量（并入既有数据体系，不单开 vXX_config） =================
# v135 铁匠铺货架品质权重（白/绿/蓝/紫/橙，鱼鱼拍板：紫橙可刷）
QUALITY_WEIGHTS = {"white": 20, "green": 25, "blue": 35, "purple": 15, "orange": 5}

STOCK_COUNT = 4      # 每城镇铁匠铺货架件数 = 2 武器 + 1 防具 + 1 饰品
STOCK_WINDOW = 5     # 城镇等级 ±5 窗口
RESTOCK_HOURS = 6    # 售罄后补货周期（小时）

# 库存限购：紫/橙 1 份，蓝/绿 2-3 份（白 2-3 份同蓝绿）
_QTY_BY_QUALITY = {"purple": 1, "orange": 1}

# 城镇铁匠 NPC 名字映射（v135 装备特色：NPC 作品命名）
SMITH_NPC_NAMES = {
    "oak_town": "老铁",
    "white_deer": "汉斯",
    "ironharbor": "奥格",
    "dawn_city": "宫廷铁匠",
    "jade_port": "翡翠匠师",
    "moon_gate": "精灵铁匠",
    "frost_horn": "托尔丁",
    "dragon_pass": "熔火",
    "wind_city": "风翼匠师",
}

# 城镇推荐等级（v135 方案文档权威等级窗口的中心值，±5 = 文档窗口：
# 橡木1-7/白鹿3-13/铁港13-23/晨曦25-35/翡翠30-40/月语47-57/霜角60-70/龙脊80-90/风翼85-95）
# v168 补两城：铁盾镇/铁砧要塞有 craft 铁匠铺但此前不在表 → 锻造分阶段漏网（F 报告），
# 按地图推荐等级 30/65 补入（铁盾≈晨曦段、铁砧≈霜角段）。
_SMITH_TOWN_LEVELS = {
    "oak_town": 4,
    "white_deer": 8,
    "ironharbor": 18,
    "ironshield_town": 30,
    "dawn_city": 30,
    "jade_port": 35,
    "moon_gate": 52,
    "frost_horn": 65,
    "anvil_fort": 65,
    "dragon_pass": 85,
    "wind_city": 90,
}

# 静态商店名册（SHOP_EQUIP + SHOP_WEAPONS 已上架名册 → 货架排除，避免重复上架）
_STATIC_SHOP_RIDS = None


def _static_shop_rids() -> set:
    """懒构建：静态 SHOP_EQUIP（含 dict 覆盖价条目）+ SHOP_WEAPONS 武器名册名。"""
    global _STATIC_SHOP_RIDS
    if _STATIC_SHOP_RIDS is None:
        s = set()
        for _lst in SHOP_EQUIP.values():
            for _e in _lst:
                s.add(_e["rid"] if isinstance(_e, dict) else _e)
        for _lst in SHOP_WEAPONS.values():
            for _wname, *_rest in _lst:
                for _rid in EQUIP_ROSTER_BY_NAME.get(_wname, []):
                    s.add(_rid)
        _STATIC_SHOP_RIDS = s
    return _STATIC_SHOP_RIDS


def town_level(map_id: str) -> int:
    """城镇推荐等级：优先 SMITH_TOWN_LEVELS 表（方案文档权威窗口中心值，
    文档窗口：橡木1-7/白鹿3-13/铁港13-23/晨曦25-35/翡翠30-40/月语47-57/霜角60-70/
    龙脊80-90/风翼85-95），兜底取 MAP_BY_ID[map_id].lv（无 lv 时按子区域怪物等级估算）。"""
    if map_id in _SMITH_TOWN_LEVELS:
        return _SMITH_TOWN_LEVELS[map_id]
    _ensure_maps()
    m = _MAP_BY_ID.get(map_id, {})
    lv = m.get("lv")
    if lv:
        return int(lv)
    # 子区域怪物等级估算兜底
    lvs = []
    for _sa in m.get("subareas") or []:
        _sad = _SUBAREAS.get(_sa) or {}
        _m = _sad.get("monsters") or []
        for _mi in _m:
            if isinstance(_mi, dict) and _mi.get("lv"):
                lvs.append(int(_mi["lv"]))
    return int(sum(lvs) / len(lvs)) if lvs else 1


def _pick_weighted_quality() -> str:
    """按品质权重随机一个品质（白20/绿25/蓝35/紫15/橙5）。"""
    total = sum(QUALITY_WEIGHTS.values())
    r = random.randint(1, total)
    acc = 0
    for q, w in QUALITY_WEIGHTS.items():
        acc += w
        if r <= acc:
            return q
    return "blue"


def roll_stock(map_id: str, town_lv: int) -> list:
    """roll 4 件货架：2 武器 + 1 防具 + 1 饰品（等级窗口 ±5 + 品质权重）。

    每件 {"rid", "qty", "price_mult"}：
    - qty：紫/橙 1 份，蓝绿 2-3 份（random 2~3）
    - price_mult：0.8~1.2 随机（保留 1 位小数）
    """
    lo, hi = town_lv - STOCK_WINDOW, town_lv + STOCK_WINDOW
    exclude = _static_shop_rids()
    pools = {"weapon": [], "armor": [], "trinket": []}
    for rid, r in EQUIP_ROSTER.items():
        if rid in exclude:
            continue
        if not (lo <= r["lv"] <= hi):
            continue
        if r["slot"] == "weapon":
            pools["weapon"].append(rid)
        elif r["slot"] in ("armor", "helm", "boots", "legs"):
            pools["armor"].append(rid)
        elif r["slot"] in ("ring", "necklace"):
            pools["trinket"].append(rid)
    # 保证 4 件：等级窗口候选不足时逐级放宽（窗口±6→全档低段→全局低段），
    # 品质权重只做倾向（未命中权重品质的槽位直接取候选池首位），不缩水货架数量
    for _ in range(6):
        if all(len(p) >= n for p, n in ((pools["weapon"], 2), (pools["armor"], 1), (pools["trinket"], 1))):
            break
        extra = [rid for rid, r in EQUIP_ROSTER.items()
                 if rid not in exclude and rid not in pools["weapon"] + pools["armor"] + pools["trinket"]
                 and (lo - 6 <= r["lv"] <= hi + 6)]
        if not extra:
            break
        rid = random.choice(extra)
        r = EQUIP_ROSTER[rid]
        if r["slot"] == "weapon":
            pools["weapon"].append(rid)
        elif r["slot"] in ("armor", "helm", "boots", "legs"):
            pools["armor"].append(rid)
        elif r["slot"] in ("ring", "necklace"):
            pools["trinket"].append(rid)
    # 等级窗口候选不足时，最后兜底从全局低等级名册补足（优先低级，防新手镇出高等级装）
    if not all(len(p) >= n for p, n in ((pools["weapon"], 2), (pools["armor"], 1), (pools["trinket"], 1))):
        missing_kinds = []
        if len(pools["weapon"]) < 2:
            missing_kinds.append("weapon")
        if len(pools["armor"]) < 1:
            missing_kinds.append("armor")
        if len(pools["trinket"]) < 1:
            missing_kinds.append("trinket")
        # 兜底池：窗口内 > 邻近 ±3 > 全局低段（lv ≤ town_lv+10，越近越好）
        def _near(rid):
            return abs(EQUIP_ROSTER[rid]["lv"] - town_lv)
        glob_cands = sorted(
            (rid for rid, r in EQUIP_ROSTER.items()
             if rid not in exclude and rid not in pools["weapon"] + pools["armor"] + pools["trinket"]
             and (lo <= r["lv"] <= hi or (lo - 3 <= r["lv"] <= hi + 3) or r["lv"] <= town_lv + 10)),
            key=lambda rid: (0 if lo <= EQUIP_ROSTER[rid]["lv"] <= hi
                             else (1 if lo - 3 <= EQUIP_ROSTER[rid]["lv"] <= hi + 3 else 2), _near(rid)))
        for mk in missing_kinds:
            for rid in glob_cands:
                r = EQUIP_ROSTER[rid]
                if mk == "weapon" and r["slot"] == "weapon":
                    pools["weapon"].append(rid)
                    break
                elif mk == "armor" and r["slot"] in ("armor", "helm", "boots", "legs"):
                    pools["armor"].append(rid)
                    break
                elif mk == "trinket" and r["slot"] in ("ring", "necklace"):
                    pools["trinket"].append(rid)
                    break
        # 若仍缺（如 Lv.1-9 无任何饰品名册），放宽 lv 上限到 town_lv + 20（新手镇也能挂上低档饰品）
        if not all(len(p) >= n for p, n in ((pools["weapon"], 2), (pools["armor"], 1), (pools["trinket"], 1))):
            glob_cands = sorted(
                (rid for rid, r in EQUIP_ROSTER.items()
                 if rid not in exclude and rid not in pools["weapon"] + pools["armor"] + pools["trinket"]),
                key=lambda rid: (abs(EQUIP_ROSTER[rid]["lv"] - town_lv)))
            for mk in missing_kinds:
                for rid in glob_cands:
                    r = EQUIP_ROSTER[rid]
                    if mk == "weapon" and r["slot"] == "weapon":
                        pools["weapon"].append(rid)
                        break
                    elif mk == "armor" and r["slot"] in ("armor", "helm", "boots", "legs"):
                        pools["armor"].append(rid)
                        break
                    elif mk == "trinket" and r["slot"] in ("ring", "necklace"):
                        pools["trinket"].append(rid)
                        break
    items = []
    for kind, need in (("weapon", 2), ("armor", 1), ("trinket", 1)):
        cands = list(pools[kind])
        for _ in range(need):
            if not cands:
                break
            # 品质权重分层 → 每层再按权重抽 1 件（保持品质分布，防同品质挤占）
            picked = None
            for _try in range(40):
                q = _pick_weighted_quality()
                layer = [rid for rid in cands if EQUIP_ROSTER[rid]["quality"] == q]
                if not layer:
                    continue
                picked = random.choice(layer)
                break
            if picked is None:
                picked = random.choice(cands)
            cands.remove(picked)
            q = EQUIP_ROSTER[picked]["quality"]
            qty = _QTY_BY_QUALITY.get(q, random.randint(2, 3))
            items.append({
                "rid": picked,
                "qty": qty,
                "price_mult": round(random.uniform(0.8, 1.2), 1),
            })
    random.shuffle(items)
    return items


def _now_ts() -> int:
    return int(time.time())


def get_smith_stock(map_id: str, town_lv: int | None = None) -> list:
    from .. import db  # 惰性导入（防 core 层循环导入）
    """读时惰性刷新全服共享货架（event_state key f"smith_stock_{map_id}"，全局共享）。

    - 无存储 → 初始化 roll 并落库
    - day 与今日 ordinal 不同 → 每日 0 点换货（全量重 roll）
    - restock_at 过期 → 补货：保留未售罄件 + 补新品填满 STOCK_COUNT
    """
    key = f"smith_stock_{map_id}"
    town_lv = town_level(map_id) if town_lv is None else town_lv
    today = date.today().toordinal()
    now = _now_ts()
    raw = db.get_event_state(key)
    st = None
    if raw:
        try:
            st = json.loads(raw)
        except (ValueError, TypeError):
            st = None
    if not st or not isinstance(st, dict):
        st = {"items": roll_stock(map_id, town_lv), "day": today,
              "restock_at": now + RESTOCK_HOURS * 3600}
        db.set_event_state(key, json.dumps(st, ensure_ascii=False))
        return list(st["items"])
    items = st.get("items") or []
    if st.get("day") != today:
        # 每日 0 点换货：全量重 roll
        st = {"items": roll_stock(map_id, town_lv), "day": today,
              "restock_at": now + RESTOCK_HOURS * 3600}
        db.set_event_state(key, json.dumps(st, ensure_ascii=False))
        return list(st["items"])
    if now >= st.get("restock_at", 0):
        # 6h 补货：保留未售罄件（qty>0），补新品填满 STOCK_COUNT
        kept = [it for it in items if it.get("qty", 0) > 0]
        missing = STOCK_COUNT - len(kept)
        if missing > 0:
            have = {it["rid"] for it in kept}
            # 复用 roll 但排除已在架名册 → 用临时逻辑补抽（roll 已 exclude 静态店名册）
            lo, hi = town_lv - STOCK_WINDOW, town_lv + STOCK_WINDOW
            cands = [rid for rid, r in EQUIP_ROSTER.items()
                     if rid not in _static_shop_rids() and rid not in have
                     and lo <= r["lv"] <= hi]
            for _ in range(missing):
                if not cands:
                    break
                rid = random.choice(cands)
                cands.remove(rid)
                r = EQUIP_ROSTER[rid]
                q = r["quality"]
                kept.append({
                    "rid": rid,
                    "qty": _QTY_BY_QUALITY.get(q, random.randint(2, 3)),
                    "price_mult": round(random.uniform(0.8, 1.2), 1),
                })
        st["items"] = kept
        st["restock_at"] = now + RESTOCK_HOURS * 3600
        db.set_event_state(key, json.dumps(st, ensure_ascii=False))
    return list(st["items"])


def _smith_equip_price(rid: str) -> int:
    """名册推导价（economy._shop_equip_price 同公式：确定性基础推导价 × 品质系数）。"""
    r = EQUIP_ROSTER[rid]
    stats = equip_stats(r["slot"], r["lv"], r["quality"])
    flavor = WEAPON_FLAVOR.get(r.get("weapon_type"), {}) if r["slot"] == "weapon" else {}
    for fk, fv in flavor.items():
        if fk == "desc" or not isinstance(fv, (int, float)):
            continue
        if fk == "crit":
            stats["crit"] = round(stats.get("crit", 0) + fv, 3)
        elif fk == "spd_fix":
            stats["spd"] = stats.get("spd", 0) + int(fv)
        elif fk == "hp_fix":
            stats["hp"] = stats.get("hp", 0) + int(fv)
        else:
            stats[fk] = stats.get(fk, 0) + int(stats.get(fk, 0) * fv)
    base = int(equip_value(stats)
               * (ECON_CONFIG["shop_equip_price_base"] + r["lv"] * ECON_CONFIG["shop_equip_price_lv"])
               * QUALITY[r["quality"]]["mult"])
    # 品质价格系数与 economy.py SHOP_EQUIP_PRICE_MULT 同源（白2.0/绿2.4/蓝3.0/紫4.0/橙5.5）
    _pm = {"white": 2.0, "green": 2.4, "blue": 3.0, "purple": 4.0, "orange": 5.5}
    return int(base * _pm.get(r["quality"], 1.5))


def smith_stock_price(rid: str, price_mult: float) -> int:
    """货架售价：名册推导价 × 浮动系数（economy 面板显示与购买同源）。"""
    return int(_smith_equip_price(rid) * price_mult)


def buy_stock_item(map_id: str, town_lv: int | None, rid: str):
    from .. import db  # 惰性导入（防 core 层循环导入）
    """原子扣减全服共享货架一件。

    返回 (ok, item_data, price)：
    - ok=True：qty-1 写回，item_data = C.generate_roster_equip(rid)（名字带『XX 的作品』后缀），
      price = 名册推导价 × price_mult（含浮动，rounded）
    - ok=False：未找到 / 售罄（rid 不在货架或 qty<=0）
    """
    key = f"smith_stock_{map_id}"
    town_lv = town_level(map_id) if town_lv is None else town_lv
    today = date.today().toordinal()
    now = _now_ts()
    # 惰性刷新（换货/补货）后做原子读-判-写
    raw = db.get_event_state(key)
    st = None
    if raw:
        try:
            st = json.loads(raw)
        except (ValueError, TypeError):
            st = None
    if not st or not isinstance(st, dict):
        st = {"items": roll_stock(map_id, town_lv), "day": today,
              "restock_at": now + RESTOCK_HOURS * 3600}
    items = st.get("items") or []
    if st.get("day") != today:
        st = {"items": roll_stock(map_id, town_lv), "day": today,
              "restock_at": now + RESTOCK_HOURS * 3600}
        items = st["items"]
    elif now >= st.get("restock_at", 0):
        kept = [it for it in items if it.get("qty", 0) > 0]
        missing = STOCK_COUNT - len(kept)
        if missing > 0:
            have = {it["rid"] for it in kept}
            lo, hi = town_lv - STOCK_WINDOW, town_lv + STOCK_WINDOW
            cands = [rid_ for rid_, r in EQUIP_ROSTER.items()
                     if rid_ not in _static_shop_rids() and rid_ not in have
                     and lo <= r["lv"] <= hi]
            for _ in range(missing):
                if not cands:
                    break
                rid_ = random.choice(cands)
                cands.remove(rid_)
                r = EQUIP_ROSTER[rid_]
                q = r["quality"]
                kept.append({
                    "rid": rid_,
                    "qty": _QTY_BY_QUALITY.get(q, random.randint(2, 3)),
                    "price_mult": round(random.uniform(0.8, 1.2), 1),
                })
        st["items"] = kept
        st["restock_at"] = now + RESTOCK_HOURS * 3600
    # 原子扣减
    for it in st.get("items") or []:
        if it.get("rid") == rid and it.get("qty", 0) > 0:
            it["qty"] -= 1
            db.set_event_state(key, json.dumps(st, ensure_ascii=False))
            from ..core.drops import generate_roster_equip
            item = generate_roster_equip(rid)
            npc = SMITH_NPC_NAMES.get(map_id, "铁匠")
            item["name"] = f"{item['name']}（{npc}的作品）"
            price = int(_smith_equip_price(rid) * it["price_mult"])
            return True, item, price
    # 未找到或售罄：仍把当前状态落库（防陈旧）
    db.set_event_state(key, json.dumps(st, ensure_ascii=False))
    return False, None, 0
