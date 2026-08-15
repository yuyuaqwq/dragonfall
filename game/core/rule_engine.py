# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - rule_engine.py（v97.5：行为彩蛋规则引擎）

规则 = 条件→反应，挂在"触发器"上（策划案 2.1/2.2）：
- 玩家每次关键动作后，引擎检查该动作的规则表，命中则触发惊喜
- 规则纯数据（data/rules.py），加规则 = 加一条 dict，零代码

规则结构：
{
    "id": "rule_xxx",
    "trigger": "explore_done",          # 触发器（见下）
    "cond": {...},                       # 条件（全部可选，组合）
    "chance": 0.5,                       # 额外概率（默认 1.0）
    "count": {"key": "xxx", "gte": 3},   # 连续命中计数：cond 连续命中 gte 次才触发，中断清零
    "action": {"template": "dialog", "params": {...}},  # 复用事件模板引擎
}

cond 支持字段：
- map / map_type      : 地图 id / 类型（str 或 list）
- time                : day(6-18) / night / deep_night(23-5)
- level_min / level_max: 玩家等级区间
- item                : 背包持有物（中文名）
- flag                : 隐藏线 talk_flag 已激活
- event               : 挂点事件特征（如 explore_done 的 empty；battle_win 的 win/lose）
- enemy_tag           : 敌人特征（boss/elite/名称关键词，str 或 list）
- hp_pct_max          : 残血（玩家 hp/max_hp <= 值）
- random_chance       : 条件级概率（与规则级 chance 二选一即可）

触发器（v97.5 已挂）：explore_done / battle_win / gather_done / move_enter / craft_done / quest_deliver
"""
import random

# 延迟导入 data.rules（避免 data 层循环）
RULES = None


def _rules():
    global RULES
    if RULES is None:
        from ..data.rules import RULES as _R
        RULES = _R
    return RULES


def _db():
    from .. import db
    return db


def _counter_key(group_id, qq_id, key):
    return f"rule_cnt_{key}_{group_id}_{qq_id}"


def _get_counter(group_id, qq_id, key) -> int:
    db = _db()
    try:
        return int(db.get_event_state(_counter_key(group_id, qq_id, key)) or 0)
    except Exception:
        return 0


def _set_counter(group_id, qq_id, key, val):
    _db().set_event_state(_counter_key(group_id, qq_id, key), str(val))


def _is_time(span: str) -> bool:
    import datetime
    h = datetime.datetime.now().hour
    if span == "day":
        # v105 M23 P2-6：与 time_weather.py 口径对齐（白天 08-18 + 清晨 05-08 + 黄昏 18-20，
        # 即非夜晚时段；night = 20:00-5:00）。原 day 6-18 与 night 18-6 与『时间』面板观感冲突
        return 5 <= h < 20
    if span == "night":
        return h >= 20 or h < 5
    if span == "deep_night":
        return h >= 23 or h < 5
    return True


def _match_cond(cond: dict, group_id, qq_id, player: dict, cur_map: dict, evt: dict) -> bool:
    """条件判定；cond 为 None/{} 恒真。"""
    if not cond:
        return True
    # 地图
    if "map" in cond:
        cur = (cur_map or {}).get("id")
        want = cond["map"]
        if isinstance(want, list):
            if cur not in want:
                return False
        elif cur != want:
            return False
    # 地图类型
    if "map_type" in cond:
        cur = (cur_map or {}).get("type")
        want = cond["map_type"]
        if isinstance(want, list):
            if cur not in want:
                return False
        elif cur != want:
            return False
    # 时段
    if "time" in cond and not _is_time(cond["time"]):
        return False
    # 等级
    if "level_min" in cond and int(player.get("level", 1)) < int(cond["level_min"]):
        return False
    if "level_max" in cond and int(player.get("level", 1)) > int(cond["level_max"]):
        return False
    # 持有物
    if "item" in cond:
        db = _db()
        want = cond["item"]
        if isinstance(want, list):
            if not any(db.count_item(group_id, qq_id, i) > 0 for i in want):
                return False
        elif db.count_item(group_id, qq_id, want) <= 0:
            return False
    # 隐藏线 flag
    if "flag" in cond:
        db = _db()
        if not db.get_talk_flags(group_id, qq_id, cond["flag"]):
            return False
    # 事件特征
    if "event" in cond:
        want = cond["event"]
        got = evt.get("event")
        if isinstance(want, list):
            if got not in want:
                return False
        elif got != want:
            return False
    # 敌人特征
    if "enemy_tag" in cond:
        enemy = evt.get("enemy") or {}
        tags = []
        if enemy.get("is_boss"):
            tags.append("boss")
        if enemy.get("is_elite"):
            tags.append("elite")
        tags.append(enemy.get("name", ""))
        tags.append(enemy.get("id", ""))
        tags += [t for t in (enemy.get("tags") or [])]
        want = cond["enemy_tag"]
        if isinstance(want, list):
            if not any(w in tags or any(w in t for t in tags if t) for w in want):
                return False
        elif want not in tags and not any(want in t for t in tags if t):
            return False
    # 残血
    if "hp_pct_max" in cond:
        pct = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        if pct > float(cond["hp_pct_max"]):
            return False
    # 条件级概率
    if "random_chance" in cond and random.random() >= float(cond["random_chance"]):
        return False
    return True


def fire(group_id, qq_id, player, cur_map, trigger, evt=None, hooks=None) -> str:
    """触发器入口：检查该 trigger 下所有规则，命中执行 action（复用事件模板）。

    返回触发文本（同一 trigger 最多触发 1 条，按规则表顺序命中即止）；
    无命中返回 ""。
    """
    evt = evt or {}
    for rule in _rules():
        if rule.get("trigger") != trigger or rule.get("enabled") is False:
            continue
        cond = rule.get("cond") or {}
        matched = _match_cond(cond, group_id, qq_id, player, cur_map, evt)
        count_cfg = rule.get("count")
        if count_cfg:
            # 连续命中计数：cond 命中累计，>=gte 触发并清零；未命中清零（连续中断）
            key = count_cfg["key"]
            cur = _get_counter(group_id, qq_id, key)
            cur = cur + 1 if matched else 0
            _set_counter(group_id, qq_id, key, cur)
            if not (matched and cur >= int(count_cfg.get("gte", 3))):
                continue
            _set_counter(group_id, qq_id, key, 0)  # 触发后清零
        else:
            if not matched:
                continue
            if random.random() >= float(rule.get("chance", 1.0)):
                continue
        # 执行 action（复用事件模板引擎）
        action = rule.get("action") or {}
        tpl = action.get("template")
        if not tpl:
            continue
        from ..core.event_templates import EventContext, execute_event_template
        ctx = EventContext(group_id, qq_id, player, cur_map,
                           params=action.get("params") or {},
                           name=(cur_map or {}).get("name", "此地"),
                           hooks=hooks or {})
        text = execute_event_template(tpl, ctx)
        if text:
            return text
    return ""
