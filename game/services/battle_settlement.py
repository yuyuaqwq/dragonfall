# -*- coding: utf-8 -*-
"""战斗结算服务层（`game/services/battle_settlement.py`）—— B9 线 L6 **薄壳**

真源正文（795 行：经验曲线 / 六类加成 / 掉落 roll / 材料折算 / 胜利·战败全同步编排）
已 **逐字搬入内容包** → `<pkg>/content/settlement.py`（唯一实现，含落库副作用）。

本文件只剩两层东西（无一行游戏逻辑、无一句文案字面量）：

  ① `_host()` —— 宿主服务句柄：把「包内实现唯一需要的宿主面」显式递给包（见下表）
  ② 25 个**逐名委托**函数 —— 真源名字与签名**一字不变**，`game/services/__init__.py`
     与 `game/commands/combat.py` / `commands/{instance,world}.py` 的 import 点、调用点
     零改动。

宿主服务句柄（真源里那些 `from .. import db` / `from .. import content as C` /
函数体内 import 的替身；**均按调用现取**，与真源函数体内惰性 import 的「活读」语义一致）：

| 句柄 | 宿主真源 | 用途 |
|---|---|---|
| `host.db` | `game.db` | 存储层（stats/图鉴/声望/背包/宠物/玩家读档落库） |
| `host.C` | `game.content` 薄聚合层 | 材料/物品/符文/宠物/公会/世界事件/地图等**未进包**的内容表 |
| `host.player_final_stats` | `game/content_rules/panel.py` | 面板（luck/gold_bonus/exp_bonus/HP-MP 重算） |
| `host.race_stats` | `game/content_rules/panel.py` | 种族金牌加成（半身人金币 +15%） |
| `host.resolve_drop` | `game/content_rules/gameplay.py` | 掉落名 → 材料/物品 id |
| `host.rule_fire` | `game/core/rule_engine.py` | 行为彩蛋规则（battle_win） |
| `host.stat_bonus` | `game/core/stat_bonus.py` | 称号/成就动态属性（rule_fire 的 title_bonus hook） |

包加载口 = `game.bootstrap.package_apply()`（本进程唯一，幂等；失败大声抛，不静默降级）。
惰性 import 包内模块：`package_apply()` 之前 `content` 还不是可用的命名空间包。
"""
from __future__ import annotations

from .. import db
from .. import content as C
from ..content_rules.gameplay import resolve_drop
from ..content_rules.panel import player_final_stats, race_stats
from ..core.rule_engine import fire as rule_fire
from ..core.stat_bonus import stat_bonus

_LIB = None


def _lib():
    """包内 `content.settlement`（唯一实现）。"""
    global _LIB
    if _LIB is None:
        import importlib

        from .. import bootstrap
        bootstrap.package_apply()          # 幂等；失败抛（不静默留空实现）
        _LIB = importlib.import_module("content.settlement")
    return _LIB


class _Host:
    """宿主服务句柄（每次调用现取——与真源函数体内惰性 import 的活读语义一致）。"""

    db = db
    C = C
    resolve_drop = staticmethod(resolve_drop)
    player_final_stats = staticmethod(player_final_stats)
    race_stats = staticmethod(race_stats)
    rule_fire = staticmethod(rule_fire)
    stat_bonus = staticmethod(stat_bonus)


def _host():
    return _Host()


# ============ 段小函数（真源名/签名不变；实现在包内） ============

def exp_curve(exp, monster_lv, player_level):
    return _lib().exp_curve(exp, monster_lv, player_level)


def party_exp_bonus(group_id, qq_id, exp):
    return _lib().party_exp_bonus(_host(), group_id, qq_id, exp)


def guild_exp_bonus(qq_id, exp):
    return _lib().guild_exp_bonus(_host(), qq_id, exp)


def pet_exp_gain(qq_id, exp, monster):
    return _lib().pet_exp_gain(_host(), qq_id, exp, monster)


def mount_exp_bonus(player, exp):
    return _lib().mount_exp_bonus(_host(), player, exp)


def world_event_bonus(group_id, qq_id, exp, gold):
    return _lib().world_event_bonus(_host(), group_id, qq_id, exp, gold)


def fortune_bonus(group_id, qq_id, exp, gold):
    return _lib().fortune_bonus(_host(), group_id, qq_id, exp, gold)


def bump_kill_stats(group_id, qq_id, monster, evt_effects):
    return _lib().bump_kill_stats(_host(), group_id, qq_id, monster, evt_effects)


def roll_blueprint_drop(group_id, qq_id, player, monster, gold):
    return _lib().roll_blueprint_drop(_host(), group_id, qq_id, player, monster, gold)


def roll_equip_drop(group_id, qq_id, monster, drop_equip, drop_lines):
    return _lib().roll_equip_drop(_host(), group_id, qq_id, monster, drop_equip, drop_lines)


def roll_pet_egg(group_id, qq_id, monster):
    return _lib().roll_pet_egg(_host(), group_id, qq_id, monster)


def roll_mount_drop(group_id, qq_id, monster):
    return _lib().roll_mount_drop(_host(), group_id, qq_id, monster)


def roll_rune_drop(group_id, qq_id, monster):
    return _lib().roll_rune_drop(_host(), group_id, qq_id, monster)


def roll_gem_drop(group_id, qq_id, monster):
    return _lib().roll_gem_drop(_host(), group_id, qq_id, monster)


def rune_income(group_id, qq_id, player, exp, gold):
    return _lib().rune_income(_host(), group_id, qq_id, player, exp, gold)


def lucky_charm(gold, player, now):
    return _lib().lucky_charm(gold, player, now)


def material_fold(group_id, qq_id, player, monster, gold, lucky_line):
    return _lib().material_fold(_host(), group_id, qq_id, player, monster, gold, lucky_line)


def know_exp_bonus(group_id, qq_id, player, exp):
    return _lib().know_exp_bonus(_host(), group_id, qq_id, player, exp)


def grant_player_exp(group_id, qq_id, player, exp):
    return _lib().grant_player_exp(_host(), group_id, qq_id, player, exp)


# ============ 纯渲染/判定单点（真源名/签名不变） ============

def next_step_hint(group_id, qq_id, player, monster) -> str:
    return _lib().next_step_hint(_host(), group_id, qq_id, player, monster)


def nearest_town(cur_map: str) -> str:
    return _lib().nearest_town(_host(), cur_map)


def red_until(qq_id) -> int:
    return _lib().red_until(_host(), qq_id)


def is_redname(qq_id) -> bool:
    return _lib().is_redname(_host(), qq_id)


def grant_worldboss_drop(group_id, qq_id, key):
    return _lib().grant_worldboss_drop(_host(), group_id, qq_id, key)


# ============ 大编排（命令层壳调用） ============

def victory_settle(group_id, qq_id, player, monster, result, extra_kills=None):
    return _lib().victory_settle(_host(), group_id, qq_id, player, monster, result, extra_kills)


def defeat_settle(group_id, qq_id, player, monster, result):
    return _lib().defeat_settle(_host(), group_id, qq_id, player, monster, result)
