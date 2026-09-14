# -*- coding: utf-8 -*-
"""v181.P4 N5b4-5a 副本战斗控制器（**命令层薄壳**）。

★ B8.2 线4（2026-09-13）：开战/结算编排已归内容包
------------------------------------------------
包内实现（唯一真源）：`<pkg>/content/flow/instance_battle.py`
（真源逐字搬入 + 宿主耦合替身接口；对照表见该文件头 ①②）

本文件只留「**取玩家 → 构造 → 调包 → 拼文案**」四件事 + 宿主耦合注入：

| 事 | 在本文件的位置 |
|---|---|
| 取玩家/构造/调包 | 全部委托包内 `build_battle` / `act` / `sync_views` / 目标选择闭包 |
| 拼文案 | ★ B18 L3c：3 条 key（`instance.日志_团队治疗` / `instance.结算_战斗异常` / `instance.面板_战斗_不在`）的 **文案调用点已迁进包内** `content/flow/instance_battle.py`（`team_heal_text` / `abort_text`）→ 本文件调用点计数 0 |
| 宿主耦合注入 | `sync_player_from_actor`（回写半边**未进包** = 缺口，见包内文件头 ②）/ `db.update_player` / Boss 剧本导演（★ B8.2 线5：宿主副本 `game/commands/boss_script.py` 已移出仓，`_script_api()` 改由 `._boss_script_port` 适配包内端口 `content.flow.boss_script`） |

包加载口 = `from .. import bootstrap; bootstrap.package_apply()`（唯一，幂等）。
包内实现在 `sys.modules` 里只加载一次；本文件**零实现**（无控制流、无数值、无文案字面量）。

调用方契约（改动前后一致）：`build_battle(st)` / `act(st, gid, qid, action[, skill, target])`
→ `(logs, ended, next_key)` / `sync_views(st, gid)` / `next_actor_key` / `player_actor_of`
/ `_players_of` / `_enemies_of` / `_attach_instance_hooks` / `_instance_target_picker` /
`_instance_team_event` / `_player_actor` / `_VIEW_ST_KEYS`（供玩法壳与测试同口径引用）。
"""
from __future__ import annotations

from typing import Optional

from .. import bootstrap as _BST

_BST.package_apply()                                      # 唯一包加载口（包根进 sys.path + install_engine）
from content.flow import instance_battle as _IB           # noqa: E402  包内实现（编排唯一真源）

# ── 文案（★ B18 L3c 起在包内：`content/flow/instance_battle.py::team_heal_text` /
#    `abort_text`。本文件的文案调用点计数归 0 —— 宿主零游戏文案；
#    key/槽位/整句逐字不变，表仍是宿主 `game/data/text_specs.json`）──────────────
_VIEW_ST_KEYS = _IB._VIEW_ST_KEYS


# ── 宿主耦合（包内替身接口的宿主实现）──────────────────────────────────────
def _script_api():
    """Boss 剧本导演（注入包内编排）：实现 = 包内端口 `content.flow.boss_script`
    （★ B8.2 线5：宿主副本 `boss_script.py` 已移出仓；适配器 `._boss_script_port` 把
    宿主聚合层 / 包内 boss_phases 域 / `build_monster` 三样绑进去，行为与改动前逐字一致）。"""
    from ._boss_script_port import script_api
    return script_api()


def _sync_player(snap, actor) -> None:
    """player actor → 玩家快照回写（回写半边未进包 = 缺口，见包内文件头 ②）。"""
    from ..services.battle_bridge import sync_player_from_actor
    sync_player_from_actor(snap, actor)


def _db_update(group_id, key, hp, mp, max_hp, max_mp) -> None:
    """玩家 DB 血量同步（宿主持久化层）。"""
    from .. import db as _db
    _db.update_player(group_id, key, hp=hp, mp=mp, max_hp=max_hp, max_mp=max_mp)


# ── 薄壳（签名/返回与改动前逐字一致）────────────────────────────────────────
def _player_actor(snap: dict, st: dict, key: str) -> dict:
    return _IB._player_actor(snap, st, key)


def _instance_target_picker(st: dict):
    return _IB._instance_target_picker(st)


def _instance_team_event(st: dict):
    return _IB._instance_team_event(st, _IB.team_heal_text)


def _attach_instance_hooks(b, st: dict) -> None:
    """battle 恢复/重建后重挂命令层注入钩子（编排在包，宿主耦合在注入）。"""
    return _IB._attach_instance_hooks(b, st, script_api=_script_api(),
                                      team_heal_text=_IB.team_heal_text)


def build_battle(st: dict) -> "object":
    """遭遇/切怪/Boss 战：开战编排（组 sides → 构造 → 落 st["battle"]）在包内。"""
    return _IB.build_battle(st, script_api=_script_api(), team_heal_text=_IB.team_heal_text)


def act(st: dict, group_id, qq_id, action: str, skill_name=None,
        target=None) -> tuple:
    """真人行动：from_state → human_act → to_state 落回（包内编排）。

    返回 (logs, ended, next_key)；两条守卫（战斗状态异常 / 行动者不在战斗中）
    由包回 abort 码，文案也由包渲染（`_IB.abort_text`，★ B18 L3c 起调用点在包内）。
    """
    logs, ended, nxt, abort = _IB.act(st, group_id, qq_id, action, skill_name, target,
                                      script_api=_script_api(),
                                      team_heal_text=_IB.team_heal_text)
    if abort:
        return [_IB.abort_text(abort)], True, None
    return logs, ended, nxt


def sync_views(st: dict, group_id) -> None:
    """唯一视图/DB 同步点（编排在包；快照回写与 DB 写在注入的宿主回调里）。"""
    return _IB.sync_views(st, group_id, sync_player_fn=_sync_player,
                          db_update_fn=_db_update)


_players_of = _IB._players_of
_enemies_of = _IB._enemies_of
player_actor_of = _IB.player_actor_of
next_actor_key = _IB.next_actor_key

__all__ = [
    "build_battle", "act", "sync_views", "next_actor_key", "player_actor_of",
]
