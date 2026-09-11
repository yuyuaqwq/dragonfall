# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - weekly_progress（周常悬赏进度域，v181 L3-P2a 下沉）

commands/weekly.py 的周状态函数族 + 击杀推进原样下沉（L3 玩家事件总线订阅方需要纯
services 消费，services 禁止 import commands/* 红线）。commands/weekly.py re-export。

weekly_bump_kill 纯化：签名去掉 inst（原 inst 仅 _grant_rewards 内 inst._player 读刷新，
返回值未被使用 → 直接删读）。发奖主体 game.reward.grant_reward 本就是 services 纯函数。
"""

from __future__ import annotations

import datetime
import json

from .. import db


def _week_key(qq_id) -> str:
    """周状态 event_state key：weekly_{qq_id}_{ISO年}-W{周}（跨年自动换 key）。"""
    y, w, _wd = datetime.date.today().isocalendar()
    return f"weekly_{qq_id}_{y}-W{w:02d}"


def _week_state(qq_id):
    """读取本周状态（无记录返回 None）。"""
    raw = db.get_event_state(_week_key(qq_id))
    if not raw:
        return None
    try:
        st = json.loads(raw)
        if not isinstance(st, dict):
            return None
        st.setdefault("tasks", {})
        st.setdefault("done_n", 0)
        return st
    except Exception:
        return None


def _save_week_state(qq_id, st):
    db.set_event_state(_week_key(qq_id), json.dumps(st, ensure_ascii=False))


def _grant_rewards(group_id, qq_id, exp, gold):
    """周常达标发奖单点（与 world._settle_daily_quest 同款结算：exp/gold + 升级）。

    v174 统一抽象：走 game.reward.grant_reward（含升级结算，返回更新后 player）。
    L3-P2a：原 inst._player 刷新读无消费方，去掉 inst 参数。
    """
    from ..reward import grant_reward
    grant_reward({"exp": int(exp), "gold": int(gold)}, group_id, qq_id)


def weekly_bump_kill(group_id, qq_id, monster) -> list:
    """击杀推进周常（L3 订阅方/击杀结算处调用；v169.2 起命令层 combat 接线已切订阅）。

    周常无『接取/交付』环节：本周已发布的任务按击杀自动 +1，达标即自动结算发奖。
    与每日任务击杀分支同构——kill_any 任意击杀 / kill_elite 精英 /
    kill_boss 区域 Boss。返回通知行列表（调用方拼入战斗结算输出）。
    """
    out = []
    try:
        st = _week_state(qq_id)
        if not st or not st.get("tasks"):
            return out
        is_elite = bool(monster.get("is_elite"))
        is_boss = bool(monster.get("is_boss"))
        changed = False
        for tname, task in list(st["tasks"].items()):
            if task.get("done"):
                continue
            need = int(task.get("need") or 0)
            obj = task.get("objective") or {}
            hit = bool(obj.get("kill_any")) or (bool(obj.get("kill_elite")) and is_elite) \
                or (bool(obj.get("kill_boss")) and is_boss)
            if not hit:
                continue
            task["prog"] = int(task.get("prog", 0) or 0) + 1
            changed = True
            if task["prog"] >= need:
                task["done"] = True
                st["done_n"] = int(st.get("done_n", 0) or 0) + 1
                _grant_rewards(group_id, qq_id, task["reward_exp"], task["reward_gold"])
                out.append(f"📜 周常『{tname}』完成！奖励：经验 +{task['reward_exp']} 金币 +{task['reward_gold']}")
                if st["done_n"] >= len(st["tasks"]):
                    out.append("🏆 本周悬赏全部完成！下周刷新后再来领新赏金～")
        if changed:
            _save_week_state(qq_id, st)
    except Exception:
        # 周常推进失败不影响战斗主流程（与成就/野王 hook 同款宽容）
        pass
    return out
