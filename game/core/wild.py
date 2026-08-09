# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - wild.py（18 章野外 NPC 判定引擎，2026-08-06）

出现链路：
  地图匹配（含 roam 游走定位）→ unlock 解锁（flag/道具/任务）→ 基础条件（时间/季节/天气/等级/任务/道具/星期）
  → 随机性（chance 概率 + cycle 周期 + 保底）→ 偶遇（记录见闻录）

随机性（18 章 1.5b）：
  chance：每 30 分钟独立判定（简化：每次判定独立）
  roam：日期哈希定当天位置，全服一致
  cycle：date.toordinal() % N == 0
  保底：连续 7 次条件满足未遇 → 下次必出

⚠️ 不要模块级 from .. import db——data/_assembly 加载时会循环导入（connection import content）。
所有用 db 的函数内延迟导入（skill 坑：core 模块用 db 必须 from .. import db，不能 C.db）。
"""
import datetime
import json
import random

from ..data.wild_npcs import WILD_NPCS, HIDDEN_NPCS
from .time_weather import current_period, current_season, today_weather

# 全部野外/隐藏 NPC（HIDDEN 后合并，同 map 遍历顺序：普通先、隐藏后）
ALL_WILD = {**WILD_NPCS, **HIDDEN_NPCS}

WILD_META_KEY = "wildmeta_{gid}_{qid}"
MISS_GUARANTEE = 7  # 连续 7 次条件满足未遇 → 必出


def _day_hash(seed: int, salt: str = "") -> int:
    h = seed * 2654435761 + (sum(ord(c) for c in salt) if salt else 0)
    return h & 0x7FFFFFFF


def npc_map_id(npc_id: str, npc: dict, now: datetime.date | None = None) -> str | None:
    """NPC 当天所在地图：roam 用日期哈希定位，否则返回固定 map"""
    roam = npc.get("roam")
    if roam:
        now = now or datetime.date.today()
        return roam[_day_hash(now.toordinal(), npc_id) % len(roam)]
    return npc.get("map")


def _quest_known(q: dict, qid: str) -> bool:
    """任务已知(主线完成 / 支线已接或进行中)。支线完成即从 side 删除，无完成记录。"""
    return qid in q.get("completed_main", []) or qid in q.get("side", {})


def unlock_met(npc_id: str, npc: dict, group_id: str, qq_id: str) -> bool:
    """解锁条件(unlock)：flag:xxx / item:mat_xxx / quest:qid。无 unlock=天然解锁。"""
    from .. import db  # noqa: E402（延迟导入防 data/_assembly 循环）
    unlock = npc.get("unlock")
    if not unlock:
        return True
    if unlock.startswith("flag:"):
        flag = unlock[5:]
        return flag in db.get_talk_flags(group_id, qq_id, npc_id)
    if unlock.startswith("item:"):
        item = unlock[5:]
        return db.count_item(group_id, qq_id, item) > 0
    if unlock.startswith("quest:"):
        qid = unlock[6:]
        return _quest_known(db.get_quests(group_id, qq_id), qid)
    if unlock.startswith("quest_done:"):
        # v87：已完成任务解锁（如 图书管理员·贝拉 需通关圣堂地窖）
        qid = unlock[11:]
        return _quest_known(db.get_quests(group_id, qq_id), qid)
    return True


def base_conditions_met(npc_id: str, npc: dict, player: dict, group_id: str, qq_id: str) -> bool:
    """基础出现条件(AND)：time/season/weather/min_level/max_level/quest_done/quest_active/flag/item/day_of_week"""
    from .. import db  # noqa: E402（延迟导入防 data/_assembly 循环）
    cond = npc.get("condition", {})
    # 时间段
    t = cond.get("time")
    if t and current_period() not in t:
        return False
    # 季节
    s = cond.get("season")
    if s and current_season() not in s:
        return False
    # 天气
    w = cond.get("weather")
    if w:
        cur_w = today_weather(npc_map_id(npc_id, npc))
        if w == "sunny":
            if cur_w not in ("sunny", "cloudy"):
                return False
        elif cur_w != w:
            return False
    # 等级区间
    if cond.get("min_level") and player.get("level", 1) < cond["min_level"]:
        return False
    if cond.get("max_level") and player.get("level", 1) > cond["max_level"]:
        return False
    q = db.get_quests(group_id, qq_id)
    # 已完成任务
    qd = cond.get("quest_done")
    if qd and not all(_quest_known(q, x) for x in qd):
        return False
    # 任务进行中
    qa = cond.get("quest_active")
    if qa and not any(x in q.get("side", {}) for x in qa):
        return False
    # 对话 flag（任意 NPC 的 flag 都算——talkflags 按 NPC 分组，这里扫全部）
    if cond.get("flag"):
        if not any(cond["flag"] in db.get_talk_flags(group_id, qq_id, nid) for nid in ALL_WILD):
            return False
    # 持有道具
    if cond.get("item") and db.count_item(group_id, qq_id, cond["item"]) <= 0:
        return False
    # 星期（周一=0）
    dw = cond.get("day_of_week")
    if dw and datetime.date.today().weekday() not in dw:
        return False
    return True


def _get_meta(group_id: str, qq_id: str) -> dict:
    from .. import db  # noqa: E402（延迟导入防 data/_assembly 循环）
    raw = db.get_event_state(WILD_META_KEY.format(gid=group_id, qid=qq_id))
    if not raw:
        return {"met": [], "miss": {}, "last": {}}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {"met": [], "miss": {}, "last": {}}


def _save_meta(group_id: str, qq_id: str, meta: dict):
    from .. import db  # noqa: E402（延迟导入防 data/_assembly 循环）
    db.set_event_state(WILD_META_KEY.format(gid=group_id, qid=qq_id),
                       json.dumps(meta, ensure_ascii=False))


def met_wild(group_id: str, qq_id: str) -> list:
    """见闻录：已遇见的野外 NPC id 列表"""
    return _get_meta(group_id, qq_id).get("met", [])


def _roll_random(npc_id: str, npc: dict, group_id: str, qq_id: str) -> bool:
    """随机性判定：cycle 硬条件 + chance 概率(含保底)。返回是否出现。"""
    cycle = npc.get("cycle")
    if cycle and datetime.date.today().toordinal() % cycle != 0:
        return False
    chance = npc.get("chance")
    if not chance:
        return True
    meta = _get_meta(group_id, qq_id)
    miss = meta.get("miss", {}).get(npc_id, 0)
    if miss >= MISS_GUARANTEE:
        meta.setdefault("miss", {}).pop(npc_id, None)  # 保底必出 = 本次遇到，清计数
        _save_meta(group_id, qq_id, meta)
        return True  # 保底：连续 7 次未遇必出
    if random.random() < chance:
        return True
    meta.setdefault("miss", {})[npc_id] = miss + 1
    _save_meta(group_id, qq_id, meta)
    return False


def wild_npc_findable(npc_id: str, npc: dict, player: dict, group_id: str, qq_id: str) -> bool:
    """『找 <名字>』直接寻找的判定：解锁 + 基础条件 + cycle 硬条件（跳过 chance——
    主动寻找不受概率限制，条件满足就能找到；cycle 是硬规律必须满足）。"""
    if npc.get("cycle") and datetime.date.today().toordinal() % npc["cycle"] != 0:
        return False
    return unlock_met(npc_id, npc, group_id, qq_id) and base_conditions_met(npc_id, npc, player, group_id, qq_id)


def roll_wild_encounter(group_id: str, qq_id: str, player: dict, map_id: str):
    """探索/进入地图时调用：当前地图满足条件的野外 NPC → 返回 (npc_id, npc)，否则 None。

    记录见闻录 + 清保底计数 + 30 分钟冷却（同一 NPC 30 分钟内不重复偶遇，防蹲守刷屏）。
    只返回第一个命中的 NPC（偶遇一次）。
    """
    today = datetime.date.today()
    now = int(datetime.datetime.now().timestamp())
    meta = _get_meta(group_id, qq_id)
    for nid, npc in ALL_WILD.items():
        if npc_map_id(nid, npc, today) != map_id:
            continue
        if not unlock_met(nid, npc, group_id, qq_id):
            continue
        if not base_conditions_met(nid, npc, player, group_id, qq_id):
            continue
        # 30 分钟冷却（偶遇过的不立刻重复出现）
        last = meta.get("last", {}).get(nid, 0)
        if last and now - last < 1800:
            continue
        if not _roll_random(nid, npc, group_id, qq_id):
            continue
        # 偶遇！见闻录记录 + 清保底 + 冷却
        if nid not in meta["met"]:
            meta["met"].append(nid)
        meta.setdefault("miss", {}).pop(nid, None)
        meta.setdefault("last", {})[nid] = now
        _save_meta(group_id, qq_id, meta)
        return nid, npc
    return None


def nearby_hints(group_id: str, qq_id: str, player: dict, map_id: str) -> list:
    """『时间』指令：当前地图满足条件(含随机性)的野外 NPC 提示列表(供"附近可遇"显示)"""
    hints = []
    today = datetime.date.today()
    for nid, npc in ALL_WILD.items():
        if npc_map_id(nid, npc, today) != map_id:
            continue
        if not unlock_met(nid, npc, group_id, qq_id):
            continue
        if not base_conditions_met(nid, npc, player, group_id, qq_id):
            continue
        hints.append((nid, npc))
    return hints
