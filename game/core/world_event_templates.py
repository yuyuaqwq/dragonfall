# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - world_event_templates.py（v98.5：世界事件展示注册表）

消灭 commands/social.py world_event() 里的 etype if-elif 硬编码（6 分支）：
世界事件数据（data/events.py WORLD_EVENT_POOL）只声明 type，展示统一走本模块注册表。

扩展方式：
- 加事件类型：WORLD_EVENT_POOL 加一条数据 + register 一个展示函数（~5 行）
- 函数签名：fn(self, cur, lines, group_id) -> None
  self 为 social 命令类实例（_player 查名等），cur 为世界事件状态 dict，
  lines 为输出行列表（函数向其中 append 展示行），group_id 为群号

约定：
- 未知 etype 安全降级（不显示任何事件详情，与旧 elif 链兜底一致）
"""
DISPLAYS = {}


def register(etype):
    """展示注册装饰器。"""
    def deco(fn):
        DISPLAYS[etype] = fn
        return fn
    return deco


@register("auction")
def _d_auction(self, cur, lines, group_id):
    """拍卖：列出在拍物品 + 当前最高价"""
    items = cur["data"].get("items", [])
    for it in items:
        top = max(it["bids"].values()) if it["bids"] else 0
        top_name = ""
        if it["bids"]:
            top_qq = max(it["bids"], key=it["bids"].get)
            top_name = self._player(group_id, top_qq)
            top_name = top_name["name"] if top_name else top_qq
        lines.append(f"📦 {it['id']}. {it['name']} ｜ 底价 {it['base']}｜ 最高 {top_name or '无人出价'}：{top}")
        lines.append(f"   💰 一口价 {it['buyout']}｜『竞拍 {it['id']} <金币>』")


@register("boss")
def _d_boss(self, cur, lines, group_id):
    """世界 Boss：当前血量 + 讨伐入口"""
    b = cur["data"].get("boss", {})
    pct = max(0, int(b.get("hp", 0) / max(1, b.get("max_hp", 1)) * 100))
    lines.append(f"{b.get('icon', '')} {b.get('name', '')} Lv.{b.get('lv', 1)}")
    lines.append(f"❤️ 剩余血量 {max(0, b.get('hp', 0)):,} / {b.get('max_hp', 0):,}({pct}%)")
    lines.append(f"⚔️ 输入『讨伐』参与战斗！贡献越高奖励越丰厚！")


@register("merchant")
def _d_merchant(self, cur, lines, group_id):
    """行商：全商店 8 折"""
    lines.append("🎁 所有商店 8 折优惠进行中！『商店』查看，『购买 <物品>』扫货！")


@register("omen")
def _d_omen(self, cur, lines, group_id):
    """凶兆：经验金币 +50%"""
    lines.append("🌧️ 经验与金币收益＋50%！快去『探索』打怪吧！")


@register("swarm")
def _d_swarm(self, cur, lines, group_id):
    """兽潮：怪物经验 +30%，击杀声望双倍"""
    lines.append("⚔️ 怪物经验＋30%，击杀声望双倍！守护大陆！")


@register("festival")
def _d_festival(self, cur, lines, group_id):
    """庆典：签到奖励翻倍，金币掉落增加"""
    lines.append("🎉 『签到』奖励翻倍！金币掉落增加！")


# ============ 事件初始化注册表（v100.2）============
# 消灭 commands/social.py 事件触发时 data 生成的 etype if-elif（原 2 分支）。
# 与 DISPLAYS 对称：加新事件类型 = WORLD_EVENT_POOL 加数据 + register 展示 + register_init 初始化。
# 函数签名：fn(rnd) -> data dict（rnd 为 random 模块/实例，social.py 传入函数内局部 _rnd）
# 约定：未知 etype 不注册 → 返回空 data（与旧代码非 auction/boss 分支 data={} 一致）
INITIALIZERS = {}


def register_init(etype):
    """初始化注册装饰器。"""
    def deco(fn):
        INITIALIZERS[etype] = fn
        return fn
    return deco


@register_init("auction")
def _i_auction(rnd):
    """拍卖：随机抽 3 件高品质装备作拍卖品"""
    from .. import content as C  # 延迟导入防循环
    items = []
    pool = rnd.sample(C.AUCTION_POOL, min(3, len(C.AUCTION_POOL)))
    for i, ap in enumerate(pool, 1):
        equip = C.generate_equip(ap["slot"], ap["lv"], ap["quality"])
        items.append({
            "id": i, "name": equip["name"], "slot": ap["slot"],
            "stats": equip.get("stats", {}), "desc": equip.get("desc", ""),
            # v104 P1：存完整 equip，结算/一口价直接发放（修复成交发 lv30 紫装与展示不符）
            "equip": equip,
            "base": ap["base"], "buyout": ap["buyout"],
            "bids": {},  # qq -> amount
        })
    return {"items": items}


@register_init("boss")
def _i_boss(rnd):
    """世界 Boss：随机抽取一只并初始化讨伐状态"""
    from .. import content as C  # 延迟导入防循环
    b = rnd.choice(C.WORLD_BOSS_POOL)
    return {"boss": {"name": b["name"], "icon": b["icon"], "lv": b["lv"],
                     "hp": b["hp"], "max_hp": b["hp"],
                     "reward": b["reward"], "contrib": {},
                     "mech": b.get("mech", ""),
                     "map": b.get("map", ""), "map_name": b.get("map_name", "")}}

