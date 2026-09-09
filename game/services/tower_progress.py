# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - tower_progress（修炼塔进度域，v181 L3-P2a 下沉）

commands/tower.py 的爬塔状态函数族原样下沉（L3 玩家事件总线订阅方需要纯 services 消费，
services 禁止 import commands/* 红线）。commands/tower.py 顶部 re-export 保持命令层零改动引用。

依赖红线：可 import data/core/store/db/engine/reward/sibling services；禁止 import commands/*。
"""

from __future__ import annotations

import datetime
import json

from .. import db
from .. import content as C


def _tower_key(qq_id) -> str:
    return f"tower_{qq_id}"


def _tower_state(qq_id):
    d = None
    raw = db.get_event_state(_tower_key(qq_id))
    if raw:
        try:
            d = json.loads(raw)
        except Exception:
            d = None
    st = {"cur": 0, "cleared_today": [], "count_today": 0, "date": ""}
    if isinstance(d, dict):
        st.update(d)
    today = datetime.date.today().isoformat()
    if st.get("date") != today:
        st["cleared_today"] = []
        st["count_today"] = 0
    st["date"] = today
    # 类型兜底（旧档脏数据防御）
    st["cleared_today"] = [int(x) for x in (st.get("cleared_today") or [])]
    try:
        st["count_today"] = int(st.get("count_today") or 0)
    except Exception:
        st["count_today"] = 0
    try:
        st["cur"] = int(st.get("cur") or 0)
    except Exception:
        st["cur"] = 0
    return st


def _save_tower_state(qq_id, st):
    db.set_event_state(_tower_key(qq_id), json.dumps(st, ensure_ascii=False))


def _floor_def(floor: int) -> dict:
    """TRIAL_FLOORS 表查找（1 基；找不到返回 None）。"""
    floors = list(getattr(C, "TRIAL_FLOORS", None) or [])
    for f in floors:
        if int(f.get("floor") or 0) == int(floor):
            return f
    return None


def tower_guard_on_kill(group_id, qq_id, monster) -> list:
    """塔卫被击杀 → 爬塔状态推进 + 金币结算 + 文案（L3 订阅方/combat 击杀后调用）。

    v181 L3-P2a 下沉版：原 commands/tower.py 同逻辑，签名去掉 inst（原 inst._player 读
    等价换 db.get_player——存档玩家必存在）。

    经验已由标准战斗结算按 monster.exp 发放；金币（v93 怪物 gold 不直接入账）在此
    显式 +reward_gold。返回通知行由调用方拼入结算输出。
    """
    lines = []
    try:
        mid = str(monster.get("id") or "")
        if not mid.startswith("tower_"):
            return lines
        floor = int(mid[len("tower_"):])
        fd = _floor_def(floor) or {}
        gold = int(fd.get("reward_gold") or 0)
        # 金币显式入账（v93：怪物 gold 折算材料不入账，塔的金币走这里）
        if gold > 0:
            player = db.get_player(group_id, qq_id) or {}
            db.update_player(group_id, qq_id, gold=int(player.get("gold", 0) or 0) + gold)
            lines.append(f"💰 塔层赏金：金币 +{gold}")
        st = _tower_state(qq_id)
        today_cleared = [int(x) for x in (st.get("cleared_today") or [])]
        # 幂等：同一天同层已结算过不再重复计数
        if floor in today_cleared:
            return lines
        today_cleared.append(floor)
        st["cleared_today"] = sorted(today_cleared)
        st["count_today"] = len(today_cleared)
        st["cur"] = max(int(st.get("cur") or 0), floor)
        _save_tower_state(qq_id, st)
        lines.append(f"🏯 第 {floor} 层【{fd.get('name') or ''}】突破！")
        left = max(0, int(getattr(C, "TRIAL_DAILY_LIMIT", 3) or 3) - st["count_today"])
        if floor >= int(getattr(C, "TRIAL_MAX_FLOOR", 30) or 30):
            lines.append("👑 你已登顶修炼塔之巅——奥兰迪亚的强者之名，当之无愧！")
        elif left > 0:
            nxt = floor + 1
            nfd = _floor_def(nxt)
            lines.append(f"💡 今日还可突破 {left} 层——回复『爬塔』挑战第 {nxt} 层"
                         + (f"【{nfd.get('name') or ''}】(建议 Lv.{nfd.get('lv')})" if nfd else ""))
        else:
            lines.append("🌙 今日修炼已满 3 层，好好消化感悟，明日再来！(失败/逃跑不占次数)")
    except Exception:
        pass
    return lines
