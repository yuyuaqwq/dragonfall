# -*- coding: utf-8 -*-
"""v181.P4 N5b4-5a 副本战斗控制器（**命令层薄壳 · B2-W2 机械指向**）。

包内实现（唯一真源）：`<pkg>/content/flow/instance_battle.py`

本文件只剩三类东西（B2-W2：把原来逐个手写的转发实现换成**机械指向**，不再抄一遍转发）：

| 类 | 内容 | 为什么必须留宿主 |
|---|---|---|
| 宿主耦合注入 | `_script_api()`（Boss 剧本导演 = `._boss_script_port` 适配包内端口）· `_sync_player(snap, actor)`（回写半边）· `_db_update(...)`（宿主持久化写库） | 三者的**实现体**是宿主侧端口/存储层；包内替身接口允许调用方传参（`script_api=` / `sync_player_fn=` / `db_update_fn=`） |
| 三个入口包装 | `build_battle(st)` / `act(st, gid, qid, action[, skill, target])` / `sync_views(st, gid)` | ★ 口径差：包内 `act` 返回**四位**（第 4 位 = abort 码），宿主壳按调用方契约折成**三元**（`tests/test_battle_n5b4_instance.py:131` 按三元解包）；`build_battle` 另需把宿主 `script_api` 传进去 |
| 机械指向 | `_VIEW_ST_KEYS` / `_player_actor` / `_instance_target_picker` / `_instance_team_event` / `_players_of` / `_enemies_of` / `player_actor_of` / `next_actor_key` | 逐名转发 → `__getattr__` 指向包内**同一对象**（PEP 562；`from ….instance_battle import _instance_target_picker` 等调用点零改动） |

包加载口 = `from .. import bootstrap; bootstrap.package_apply()`（唯一，幂等）。
调用方契约（改动前后一致）：`build_battle(st)` / `act(st, gid, qid, action[, skill, target])`
→ `(logs, ended, next_key)` / `sync_views(st, gid)` / `next_actor_key` / `player_actor_of`
/ `_players_of` / `_enemies_of` / `_attach_instance_hooks` / `_instance_target_picker` /
`_instance_team_event` / `_player_actor` / `_VIEW_ST_KEYS`。
"""
from __future__ import annotations

from typing import Optional

from .. import bootstrap as _BST

_BST.package_apply()                                      # 唯一包加载口（包根进 sys.path + install_engine）
from content.flow import instance_battle as _IB           # noqa: E402  包内实现（编排唯一真源）


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


# ── 薄壳入口（签名/返回与改动前逐字一致）────────────────────────────────────
def _instance_team_event(st: dict):
    """团队技能广播观察者 —— 包内 `_instance_team_event(st, team_heal_text=None)`：
    宿主壳**必须**把 `team_heal_text` 传进去（不传 = 治疗照算但**该行文案不追加**，行为会变）。"""
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


# ── 机械指向（PEP 562）：逐名转发 → 包内同一对象 ────────────────────────────
_FORWARDS = (
    "_VIEW_ST_KEYS",
    "_player_actor", "_instance_target_picker",
    "_players_of", "_enemies_of", "player_actor_of", "next_actor_key",
)


def __getattr__(name):
    """PEP 562：按名指向包内实现（同一对象；不再是宿主侧手写的一行转发）。"""
    if name in _FORWARDS:
        return getattr(_IB, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


__all__ = [
    "build_battle", "act", "sync_views", "next_actor_key", "player_actor_of",
]
