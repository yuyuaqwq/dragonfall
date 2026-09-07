# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - shop.py（P4-3 ShopService + TradeService 交易域）

v181.P4-3：economy.py shop/buy/sell 交易区纯逻辑服务化（逐行 copy 零变化）——
命令层只留解析 + 守卫 + async yield 壳，业务走本模块（services 禁 import commands/*）。

搬入内容（按域分块，函数名去 `_` 前缀，签名去 self，body 逐行等价）：
  - 常量：SHOP_EQUIP_PRICE_MULT / _SHOP_EQUIP_PRICE_OVERRIDE / _MAT_FACILITY / _MAT_FACILITY_HINT
  - 定价 & 货架：equip_price（= economy._shop_equip_price，v101.25e 确定性推导价 × 品质系数，
    显示价与购买价同源；v130.2d R2 rid 覆盖价）／equip_roster（静态配置 ∪ 动态补档 lv±2 ≤3 件）／
    req_label（v101.28l #443 货架属性需求标注）／req_check（阶段八属性需求检查，equip 命令仍自用 →
    保留 economy 一份，见下）
  - buy_weapon（阶段八商店武器生成：名册精确 / 随机兜底重写 desc）
  - 出售回收：pawn_rate（v101.21 出售地点限制 + 类型分店回收率 + F1 P1-5 消耗品 0.85 档）／
    is_quest_item（v104 M08 P0-1 任务道具双判据）／fish_weight_max（v126.1 鱼种重量上限）／
    sell_one（v101.13 坐骑 sell_bonus + 品质折价/锻造 craft_cost 封顶/收藏鱼 1.0 + v126.2 大鱼加权 +
    F1 P0-2 原子出售 sell_item_atomic）／apprentice_protect_mats（v101.25 #305 拜师考验材料保护）
  - 商店限购（v166）：limit_buy_guard / limit_label —— 薄转发 core.shop_stock（core 样板不搬）
  - 子区域判定：cur_subarea / is_smith_shop（v92/v104 M09 P1 同源）——sell/面板/购买守卫共用
    （is_smith_shop 内部不调 self，纯读 player/C → 可下沉；base._at_shop/_sa_shop_kind 属命令层
    位置守卫留在 base，本 service 需要时以注入参数传入）

db 一律函数体内惰性 import（防 data/_assembly 加载期循环，core 样板同款铁律）。

⚠️ 边界（本批不碰）：
  - _req_check 供 equip 命令（换装流程）使用，非交易区 → 留在 economy.py 不搬（调用点不变）。
  - _item_fits_shop 交易区无调用点（dead helper）→ 不搬不删（本批零行为变化）。
  - sell/buy/shop 命令壳 + 面板渲染行留 economy.py；buy 的成交原子动作（扣金币/发物品）留壳。
"""
from .. import content as C

# ============ 模块常量（economy.py 原样随迁） ============

# v101.25e 商店装备价格系数（鱼鱼拍板数值方案：商店价 = 确定性推导价 × 品质系数）
# v101.25h3 鱼鱼：品质价格差距调大——原白2.0/绿1.7/蓝1.5/紫1.3/橙1.2 递减系数把品质属性倍率抵消，
# 最终橙/白价格只差 1.2 倍（橙装属性 2 倍但价格几乎没差）。改为递增系数：
# 最终价格比（属性倍率×价格系数）：白2.0 / 绿3.12 / 蓝4.80 / 紫7.20 / 橙11.0（橙≈白 5.5 倍）
SHOP_EQUIP_PRICE_MULT = {"white": 2.0, "green": 2.4, "blue": 3.0, "purple": 4.0, "orange": 5.5}

# v130.2d R2：SHOP_EQUIP 条目可选 dict 覆盖价 {"rid": ..., "price": ...}
# （圣徽·誓约新手保底：推导价公式对低等级蓝装过贵；显示与购买同源取本表，事件折扣仍生效）
_SHOP_EQUIP_PRICE_OVERRIDE = {}
for _shop_list in C.SHOP_EQUIP.values():
    for _entry in _shop_list:
        if isinstance(_entry, dict) and _entry.get("rid") and _entry.get("price") is not None:
            _SHOP_EQUIP_PRICE_OVERRIDE[_entry["rid"]] = int(_entry["price"])

# v101.25e 材料类型 → 回收设施（鱼鱼拍板：不同设施收不同材料）
_MAT_FACILITY = {
    "矿石": "smith", "木材": "smith", "兽材": "smith", "宝石": "smith",
    "草药": "alchemy", "精华": "alchemy",
    "食材": "shop", "织物": "shop", "杂物": "shop",
    "收藏": "shop", "传说": "shop", "任务道具": "shop",
}

# q7-8：材料回收品类提示（新手按类型去对应柜台，防跑错店）——集中一处维护，出售提示复用
_MAT_FACILITY_HINT = ("材料按类型分店回收：矿石/木材/兽材/宝石→铁匠铺、"
                      "草药/精华→草药铺/炼金工坊、食材/织物/杂物→商店")


# ============ 装备属性需求（交易区共享：面板标注 + 武器推导） ============

def req_label(r: dict) -> str:
    """v101.28l #443：货架标注属性需求（防买了穿不上，船长帽事件）"""
    req = r.get("req") or {}
    if not req:
        return ""
    names = {"str": "力量", "agi": "敏捷", "int": "智力", "vit": "耐力"}
    return "需" + "、".join(f"{names.get(k, k)}{v}" for k, v in req.items())


# ============ 商店装备定价 / 货架 / 生成（economy._shop_equip_* 原样随迁） ============

def equip_price(slot: str, lv: int, quality: str, weapon_type: str | None = None,
                rid: str | None = None) -> int:
    """v101.25e 商店装备价：确定性基础推导价（含武器类型风味，不含随机词条）× 品质系数。
    显示价与购买价同源，避免词条随机导致价格漂移。
    v130.2d R2：rid 命中 SHOP_EQUIP 覆盖价（{"rid":..,"price":..}）时直接返回覆盖价。"""
    if rid and rid in _SHOP_EQUIP_PRICE_OVERRIDE:
        return _SHOP_EQUIP_PRICE_OVERRIDE[rid]
    stats = C.equip_stats(slot, lv, quality)
    flavor = C.WEAPON_FLAVOR.get(weapon_type, {}) if slot == "weapon" else {}
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
    base = int(C.equip_value(stats) * (C.ECON_CONFIG["shop_equip_price_base"] + lv * C.ECON_CONFIG["shop_equip_price_lv"]) * C.QUALITY[quality]["mult"])
    return int(base * SHOP_EQUIP_PRICE_MULT.get(quality, 1.5))


def equip_roster(player: dict, equip_items: list) -> list:
    """v101.25e 商店装备列表 = 静态配置 ∪ 动态补档（玩家 lv±2 内 商店/锻造 源名册装备，最多 3 件）。
    修 #298 商店装备等级断层：每个等级都有装备可买（Lv.30+ 防具走锻造/图纸/副本经济，不破坏专属掉落）。
    v130.2d R2：静态条目支持 {"rid":..,"price":..} 覆盖价 dict——此处统一归一为 rid 字符串，
    覆盖价由 _SHOP_EQUIP_PRICE_OVERRIDE（模块级）读取，列表/购买逻辑无感。"""
    base = [e["rid"] if isinstance(e, dict) else e for e in equip_items]
    exist = set(base)
    # v101.28m #440：排除 SHOP_WEAPONS 已上架的武器名册（圣光长剑重复上架事件——
    # 静态武器表与动态补档各加一次，同价 7998G 出现两行）
    cur = player.get("cur_map", "")
    _area_id = C.MAP_BY_ID.get(cur, {}).get("area", cur)
    for wname, *_rest in (C.SHOP_WEAPONS.get(cur) or C.SHOP_WEAPONS.get(_area_id, [])):
        for _rid in C.EQUIP_ROSTER_BY_NAME.get(wname, []):
            exist.add(_rid)
    plv = player["level"]
    cands = sorted(
        (rid for rid, r in C.EQUIP_ROSTER.items()
         if r.get("source") in ("商店", "锻造") and abs(r["lv"] - plv) <= 2 and rid not in exist),
        key=lambda rid: abs(C.EQUIP_ROSTER[rid]["lv"] - plv),
    )
    return base + cands[:3]


def buy_weapon(wname: str, wtype: str, wlv: int, wq: str) -> dict:
    """阶段八：商店武器生成。名册名走名册精确生成（正确 req + 固定词条），
    非名册武器名（兜底）走随机生成再覆盖名。"""
    from ..core.drops import _eq_random_desc  # 原 economy.py:22 模块级 import（函数内等位）
    ids = C.EQUIP_ROSTER_BY_NAME.get(wname, [])
    if ids:
        return C.generate_roster_equip(ids[0])
    eq = C.generate_equip("weapon", wlv, wq, wtype)
    eq["name"] = wname
    # v103.0 修复（round103 小蓝抓包）：generate_equip 的 desc 用随机 roll 出的名字生成
    # （如"烈焰长弓"），覆盖固定名后必须同步重写 desc，否则物品名与描述不符
    # （硬木战弓 desc 曾写"烈焰长弓——冒险途中得来"）
    eq["desc"] = _eq_random_desc(wname, "weapon", wtype)
    return eq


# ============ 出售域（sell） ============

def cur_subarea(player: dict) -> dict:
    """当前所在子区域 dict（无则 {}）。"""
    cur_map = player.get("cur_map", "")
    sa_id = player.get("cur_subarea") or ""
    cm = C.MAP_BY_ID.get(cur_map, {})
    for sa in (cm.get("subareas") or []):
        if sa["id"] == sa_id:
            return sa
    return {}


def is_smith_shop(player: dict) -> bool:
    """v92 铁匠类商店：craft 场所只卖武器+锻造材料。
    炼金/草药类除外——funcs 含 alchemy 或名字含『草药/炼金』（如晨曦药剂坊 dawn_city_5）
    均不算 smith（炼金卖药剂合理，v104 M09 P1 修复）。"""
    sa = cur_subarea(player)
    if not sa:
        return False
    # v104 M09 P1 修复：herb 判定与 _sa_shop_kind 同源（alchemy funcs / 草药·炼金名），
    #   否则晨曦药剂坊(dawn_city_5, shop+craft+alchemy)被误判 smith → 卖武器/图纸（策划案 07 章 6.2 草药铺不卖武器）
    if "alchemy" in (sa.get("funcs") or []) or any(k in sa.get("name", "") for k in ("草药", "炼金")):
        return False
    funcs = sa.get("funcs") or []
    if "craft" in funcs:
        return True
    return any(k in sa.get("name", "") for k in ("铁匠", "锻造", "军械", "工坊", "强化"))


def pawn_rate(player: dict, d: dict, *, is_smith_shop_=None, at_shop=None):
    """v101.21 出售地点限制：装备→铁匠/工坊（原价）；材料→按类型分设施（v101.25e 鱼鱼拍板）：
    矿石/木材/兽材/宝石→铁匠铺(0.9)；草药/精华→炼金铺(0.9)；食材/织物/杂物→商店(0.8)；其他→1.0。
    F1 P1-5：无 slot 消耗品（药水/食物/卷轴/炼金/烹饪产物）回收由 1.0 全价下调到 0.85——
    原回落 1.0 与材料 0.8~0.9 明显倒挂，白送金币（与造物成本封顶互补，_sell_one 还有 craft_cost 封顶兜底）。
    v125：回收率数据下沉 prof_config.PAWN_RATES。
    is_smith_shop_/at_shop：命令层位置守卫注入（base._is_smith_shop/_at_shop 语义），缺省回退本模块纯 C 判定。"""
    if is_smith_shop_ is None:
        is_smith_shop_ = is_smith_shop
    if d.get("slot"):  # 装备必须去铁匠铺卖（回收装备是铁匠的活）
        if is_smith_shop_(player):
            return C.PAWN_RATES["equip"]
        return None
    # v105 M17 P3-3：宠物蛋/坐骑缰绳回收折价 0.5（此前无 slot 且非材料 → 1.0 全价，
    # 掉落蛋/缰绳=白送金币；与装备回收同档，防刷钱。宠物蛋按品质已分档定价 100~500）
    if d.get("type") in (C.ITEM_TYPE_PET_EGG, C.ITEM_TYPE_MOUNT):
        return C.PAWN_RATES["pet_mount"]
    # v95.32 #397b：材料判定按名查表（data.type 可能是分类名如"精华/草药"，非"材料"）
    mm = C.MATERIALS_BY_NAME.get(d.get("name", "")) or {}
    if not mm:
        # F1 P1-5：非材料、非装备（药水/食物/卷轴/炼金/烹饪产物等消耗品）回收 0.85，
        # 与材料档对齐，避免白送金币（收藏鱼等特殊物在 _sell_one 单独置回 1.0）
        return C.PAWN_RATES["consumable"]
    mtype = mm.get("type", "杂物")
    need = _MAT_FACILITY.get(mtype, "shop")
    sa = cur_subarea(player)
    if not sa:
        return None
    name = sa.get("name", "")
    funcs = sa.get("funcs") or []
    if need == "alchemy" and ("炼金" in name or "alchemy" in funcs):
        return C.PAWN_RATES["mat_alchemy"]
    if need == "smith" and is_smith_shop_(player):
        return C.PAWN_RATES["mat_smith"]
    if need == "shop" and at_shop(player):
        return C.PAWN_RATES["mat_shop"]
    return None


def is_quest_item(d: dict) -> bool:
    """v104 M08 P0-1：任务道具判定（批量/单件出售保护共用）。

    双判据：背包 data.type 直接标注 或 按名查 MATERIALS_BY_NAME 定义兜底。
    （发放路径入包只拷 name/price 时 type 被写死为"材料"——world.py 支线奖励/
    采集/挖掘/副本拾取等均如此，仅靠 data.type 会漏判，烬火信标即可被『出售 全部』误卖。）
    """
    if d.get("type", "") == "任务道具":
        return True
    mm = C.MATERIALS_BY_NAME.get(d.get("name", ""))
    return bool(mm and mm.get("type") == "任务道具")


def fish_weight_max(d: dict):
    """v126.1 大鱼卖更贵：鱼种 weight_range 上限（kg）——FISH_POOL 按名反查；
    非鱼种/未配区间返回 None（按原价 1.0 系数）。"""
    for f in C.FISH_POOL:
        if f.get("name") == d.get("name"):
            wr = f.get("weight_range")
            return wr[1] if wr and len(wr) > 1 else None
    return None


def sell_one(group_id, qq_id, player, it, rate, *, is_smith_shop_=None, at_shop=None):
    """出售单件物品（按回收价），返回 (名称, 数量, 金币) 或 None。
    v101.13 坐骑 sell_bonus：骑乘驮兽类坐骑出售价格加成。"""
    from .. import db  # 惰性导入
    d = it["data"]
    meff = C.mount_effects(player)
    sell_mult = 1.0 + float(meff.get("sell_bonus", 0) or 0)
    # v101.25e 装备回收价：掉落装备卖商店 = 推导价 × 0.5（装备掉落是锦上添花，不能成主要收入）
    # v101.27 鱼鱼拍板上调：0.3 → 0.5（playtest 观察"回收≈买入价15%"，旧库存只回 3 金，
    # 装备误购回收惨淡；0.5 仍低于买入价，不构成刷钱渠道）
    # v95.32 #397b：判据用 slot 而非 quality——v101.25e 起材料也注入全服品质字段，材料被打 0.3 折是 bug
    if d.get("slot"):
        rate = min(rate, C.ECON_CONFIG["equip_resale_rate"])
    # M10 P1-2 锻造→卖店印钞修复：锻造产物（craft_cost=材料价+锻造费）卖店最多回本，
    # 杜绝 材料→锻造→卖店 金币永动机（104/114 配方净赚，最高 +1234%）。
    # F1 P1-5：原仅覆盖装备分支持有 craft_cost 的造物，现扩展到炼金/烹饪等带 craft_cost 的
    # 消耗品造物——与 _pawn_rate 0.85 档互补，杜绝「低材→高值消耗品→卖店」利润通道。
    cc = d.get("craft_cost")
    if cc and d.get("price"):
        rate = min(rate, cc / d["price"])
    # v104 M15 修复：彩蛋收藏鱼（type=收藏）跳过 0.8 折扣按 1 金币原价回收
    # （原 int(1×0.8)=0 返回 None，收藏鱼永久占包无法回收）
    # v104 R3 M15 P1-1：双判据按名兜底——v98.1 采集池可采出星骸遗鳞时期入包的
    # 历史堆 data.type 被写死为"材料"，仅判 data.type 仍卖不掉（0.8 折 int(0.8)=0）
    if d.get("type") == "收藏" or (C.MATERIALS_BY_NAME.get(d.get("name", "")) or {}).get("type") == "收藏":
        rate = 1.0
    price = int(d.get("price", 0) * rate * sell_mult)
    if price <= 0:
        return None
    # v126.2 大鱼卖更贵：鱼获个体属性在 item_data.tags（FIFO），单条实收 = int(base × (0.5 + w/wmax))，
    # 无 tag 的鱼（老数据/非鱼材料）按原价（1.0 系数）；remove_item 扣包时自动同步截断 tags
    _tags = (it["data"].get("tags") or [])[:it["count"]]
    gold = price * it["count"]
    if _tags and isinstance(_tags, list):
        _wmax = fish_weight_max(d)
        # v126.4 拍板项 1：只对 type=鱼 加权（渔获材料回归原价——同材料垂钓所得
        # vs 采集所得售价一致，避免"材料按类型折价"与"个体波动"语义混叠）
        if _wmax and d.get("type") == "鱼":
            # v126.4 审计 P2：t.get("weight", 0) 防损坏 tag 缺键直接 KeyError 崩出售
            gold = sum(int(price * (0.5 + (t.get("weight") or 0) / _wmax)) for t in _tags if isinstance(t, dict))
            gold += (it["count"] - len(_tags)) * price
    # F1 P0-2：原子出售（单事务：校验货存→加金币→扣包），替代原两步独立 commit
    ok = db.sell_item_atomic(group_id, qq_id, it["key"], it["count"], gold)
    return (d["name"], it["count"], gold)


def apprentice_protect_mats(group_id, qq_id) -> dict:
    """v101.25 #305：当前对话树节点（拜师考验）需要的材料名 → 数量。

    玩家正在导师考验节点（apprentice_check 选项）时，批量出售不能误卖这些
    材料——round68 小红实锤：『出售 材料』把铁矿石×7 混卖，挖掘拜师直接卡死。
    返回 {材料名: 需要数量}，无考验返回 {}。
    """
    from .. import db  # 惰性导入
    st = db.get_talk_state(group_id, qq_id)
    if not st:
        return {}
    npc_id = st.get("npc", "")
    node_id = st.get("node", "")
    dlg = C.get_dialogue(npc_id)
    if not dlg:
        return {}
    node = C.dialogue_node(dlg, node_id)
    if not isinstance(node, dict):
        return {}
    mats = {}
    for o in (node.get("options") or []):
        ac = (o.get("action") or {}).get("apprentice_check")
        if ac:
            mats[ac.get("item", "")] = int(ac.get("count", 1))
    return mats


# ============ v166 商店限购（店内共享库存 + 每日个人限购） ============

def limit_buy_guard(group_id: str, qq_id: str, sa_id: str, key: str, qty: int):
    """商店限购统一拦截（在购买成交前调用，扣库存+记日限）。

    返回 (ok, msg)：
      ok=True  已通过限购检查并完成扣减（可继续扣金币发物品）
      ok=False 被限购拦截，msg 为提示文案（yield 后 return）
    注意：调用方必须保证本次真的成交（后续金币不足时已先于本函数校验，
    或本函数之后仍可能因金币失败——由调用方保证扣款顺序）。
    """
    from ..core import shop_stock as _sshop  # v166 商店限购（店内共享库存+每日个人限购）
    ok, reason, can = _sshop.check_and_consume(group_id, qq_id, sa_id, key, qty)
    if not ok:
        return False, reason
    return True, ""


def limit_label(sa_id: str, key: str) -> str:
    """商品面板限购标注（未配置返回 ''）。"""
    from ..core import shop_stock as _sshop
    return _sshop.limit_label(sa_id, key)
