# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - auction（拍卖域，v181 P4-5）

拍卖状态机服务层收敛点（v104R3 规则原样随迁，行为零变化）：
由 social（『拍卖』/『竞拍』命令与世界事件惰性调度）消费——把 social.py
auction/bid 区（开拍判定/出价冻结/被超退还/一口价/到期结算/过期清理）的
纯逻辑与 world_event 槽读写收进本模块。

- v104R3 P1-1：过期拍卖必须先走 settle_auction 结算——否则出价金币随 bids
  记录一起销毁，永久丢失（Boss 事件由各自指令处理）
- v104R3 P2：新出价必须严格超过当前最高价（同价出价无意义且锁金币到结算）
- v104 P1：结算/一口价直接发放初始化时存好的完整 equip（展示什么发什么），
  不再以 lv30/purple 重新生成；旧数据(无 equip)按存字段兜底

命令层能力（读玩家名/发装备/广播）经 db/content 或参数注入，本模块纯同步；
广播/yield 流留命令层（_maybe_roll_event 的"过期任何事件都清槽"控制流亦留命令层）。

依赖红线：可 import data/core/store/db/engine/reward/battle；禁止 import commands/*。
db 等依赖一律函数体内惰性 import（防 data/_assembly 加载期循环，core 样板同款铁律）。
"""
import time
import uuid as _uuid


# ============================================================
# 拍卖到期结算（原 social._settle_auction，逐行等价搬移）
# ============================================================

def settle_auction(cur, group_id: str) -> str:
    """拍卖到期结算：最高价者得物品，其余退还。返回结算文本"""
    from .. import db
    from .. import content as C
    if not cur or cur["etype"] != "auction":
        return "拍卖行已关闭。"
    items = cur["data"].get("items", [])
    lines = []
    for it in items:
        if it["bids"]:
            top_qq = max(it["bids"], key=it["bids"].get)
            amount = it["bids"][top_qq]
            # 发放装备（v48：品质档英文 ID；key 用唯一 id 而非装备名）
            # v104 P1：直接发放初始化时存好的完整 equip（展示什么发什么），
            # 不再以 lv30/purple 重新生成；旧数据(无 equip)按存字段兜底
            equip = it.get("equip") or C.generate_equip(it["slot"], it.get("lv", 30), it.get("quality", "purple"))
            db.add_item(group_id, top_qq, f"eq_{_uuid.uuid4().hex[:8]}", equip, count=1)
            p = db.get_player(group_id, top_qq)
            name = p["name"] if p else top_qq
            lines.append(f"🎉 {name} 以 {amount} 金币拍得【{it['name']}】！")
            # 退还其他出价者
            for qq2, amt2 in it["bids"].items():
                if qq2 != top_qq:
                    p2 = db.get_player(group_id, qq2)
                    if p2:
                        db.update_player(group_id, qq2, gold=p2["gold"] + amt2)
                        lines.append(f"↩️ 退还 {p2['name']} {amt2} 金币")
        else:
            lines.append(f"💤 【{it['name']}】无人出价，流拍。")
    # v104R3 P2：落槌价去向说明（复验点12：赢家金币为系统回收，无文案说明）
    if any(it.get("bids") for it in items):
        lines.append("💰 落槌价已由拍卖行收讫(系统回收)，未成交者的出价已全额退还。")
    return "\n".join(lines)


def _settle_auction(cur, group_id: str) -> str:
    """（P4-5 兼容别名，见模块 docstring；social 旧引用已改调 settle_auction）"""
    return settle_auction(cur, group_id)


# ============================================================
# 过期拍卖结算 + 事件槽清理（原 social auction/bid 命令的双份重复检查收敛）
# ============================================================

def settle_expired_auction(group_id: str) -> str:
    """当前事件槽为过期拍卖 → 结算 + 清事件槽。返回结算文本(无则空串)。

    收敛 social._settle_auction 调用前的"读 include_expired + etype 判定 + 清槽"
    重复块（auction/bid 双命令同款）。过期拍卖必须先走结算（v104R3 P1-1），
    否则出价金币随 bids 一起销毁。非 auction 过期事件不清槽——Boss 事件由
    hunt_boss 指令处理，_maybe_roll_event 的"任意过期事件清槽"控制流留在命令层。
    """
    from .. import db
    cur = db.get_world_event(include_expired=True)
    now = int(time.time())
    if not cur or cur["etype"] != "auction" or now < cur["ends_at"]:
        return ""
    lines = settle_auction(cur, group_id)
    db.clear_world_event()
    return lines


# ============================================================
# 拍卖进度持久化（原 social.bid 内 db.save_world_event 直调 ×2 收进 service）
# ============================================================

def save_auction_state(cur) -> None:
    """把拍卖进度(出价/一口价成交后物品移除)持久化回 world_event 槽。

    原命令层直调 db.save_world_event(cur["etype"], cur["ends_at"], cur["data"])——
    etype/ends_at/data 三者原样回写（store.save_world_event 先 DELETE 再 INSERT），
    槽读写语义收进 service 后由命令层在每次变更 bids 后调用。
    """
    from .. import db
    db.save_world_event(cur["etype"], cur["ends_at"], cur["data"])
