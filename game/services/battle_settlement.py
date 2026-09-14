# -*- coding: utf-8 -*-
"""战斗结算服务层（`game/services/battle_settlement.py`）—— B9 线 L6 薄壳 · **B2-W2 改口**

真源正文（795 行：经验曲线 / 六类加成 / 掉落 roll / 材料折算 / 胜利·战败全同步编排）
在内容包 → `<pkg>/content/settlement.py`（唯一实现，含落库副作用）。

本文件两层东西（无一行游戏逻辑、无一句文案字面量）：

  ① **宿主服务句柄** —— B2-W2 改口：不再经由宿主壳的 `_Host` 类 / `_host()` / `_lib()` 三件套，
     而是**显式注入**包内替身口 `content/settlement.py::bind_host(**objs)`
     （键 = 符号名，见 `content/settlement.py:56-86` 的替身口说明）：

     | 注入键 | 宿主真源 | 用途 |
     |---|---|---|
     | `db` | `game.db` | 存储层（stats/图鉴/声望/背包/宠物/玩家读档落库） |
     | `content` | `game.content` 薄聚合层 | 材料/物品/符文/宠物/公会/世界事件/地图等函数读口 |
     | `player_final_stats` / `race_stats` | `game/content_rules/panel.py` | 面板 / 种族金牌加成 |
     | `resolve_drop` | `game/content_rules/gameplay.py` | 掉落名 → 材料/物品 id |
     | `rule_fire` | `game/core/rule_engine.py` | 行为彩蛋规则（battle_win） |
     | `stat_bonus` | `game/core/stat_bonus.py` | 称号/成就动态属性（rule_fire 的 title_bonus hook） |

     注入值与原 `_Host` 类**逐名同一对象**（`game.db` / `game/content_rules/*` 本来就是
     「包内同名对象的宿主再导出」）⇒ 行为逐字节不变。取不到 → 包内抛（拒绝静默空跑）。

  ② **26 个逐名包装** —— 真源名字与签名**一字不变**（`game/services/__init__.py:71-78` 与
     `game/commands/combat.py` 的 import 点、调用点零改动）。包装体 = 一行直达包内同名函数
     —— **不再传 host 首参**：包内那 26 个函数带「两种调用约定」兼容装饰器 `@_host_tolerant`
     （`content/settlement.py:199-209`），首参不是宿主面句柄时自动左对齐补上包内自解析句柄
     （= 上面注入的那批）。⇒ 宿主侧 `_Host` / `_host` / `_lib` 三个收敛掉，
     **签名/返回/异常语义一个字没动**（B2 交接 §2b③ 的硬约束）。

包加载口 = `game.bootstrap.package_apply()`（本进程唯一，幂等；失败大声抛）。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（幂等）

_bootstrap.package_apply()
from content import settlement as _pkg                       # noqa: E402 包内唯一实现

# ---- ① 宿主服务句柄：显式注入包内替身口（逐名同一对象；键 = 符号名）----
from .. import db                                            # noqa: E402
from .. import content as C                                  # noqa: E402
from ..content_rules.gameplay import resolve_drop            # noqa: E402
from ..content_rules.panel import player_final_stats, race_stats   # noqa: E402
from ..core.rule_engine import fire as rule_fire             # noqa: E402
from ..core.stat_bonus import stat_bonus                     # noqa: E402

_pkg.bind_host(db=db, content=C, player_final_stats=player_final_stats,
               race_stats=race_stats, resolve_drop=resolve_drop,
               rule_fire=rule_fire, stat_bonus=stat_bonus)


# ============ 段小函数（真源名/签名不变；实现在包内；宿主首参由包内 @_host_tolerant 补齐）====

def exp_curve(exp, monster_lv, player_level):
    return _pkg.exp_curve(exp, monster_lv, player_level)


def party_exp_bonus(group_id, qq_id, exp):
    return _pkg.party_exp_bonus(group_id, qq_id, exp)


def guild_exp_bonus(qq_id, exp):
    return _pkg.guild_exp_bonus(qq_id, exp)


def pet_exp_gain(qq_id, exp, monster):
    return _pkg.pet_exp_gain(qq_id, exp, monster)


def mount_exp_bonus(player, exp):
    return _pkg.mount_exp_bonus(player, exp)


def world_event_bonus(group_id, qq_id, exp, gold):
    return _pkg.world_event_bonus(group_id, qq_id, exp, gold)


def fortune_bonus(group_id, qq_id, exp, gold):
    return _pkg.fortune_bonus(group_id, qq_id, exp, gold)


def bump_kill_stats(group_id, qq_id, monster, evt_effects):
    return _pkg.bump_kill_stats(group_id, qq_id, monster, evt_effects)


def roll_blueprint_drop(group_id, qq_id, player, monster, gold):
    return _pkg.roll_blueprint_drop(group_id, qq_id, player, monster, gold)


def roll_equip_drop(group_id, qq_id, monster, drop_equip, drop_lines):
    return _pkg.roll_equip_drop(group_id, qq_id, monster, drop_equip, drop_lines)


def roll_pet_egg(group_id, qq_id, monster):
    return _pkg.roll_pet_egg(group_id, qq_id, monster)


def roll_mount_drop(group_id, qq_id, monster):
    return _pkg.roll_mount_drop(group_id, qq_id, monster)


def roll_rune_drop(group_id, qq_id, monster):
    return _pkg.roll_rune_drop(group_id, qq_id, monster)


def roll_gem_drop(group_id, qq_id, monster):
    return _pkg.roll_gem_drop(group_id, qq_id, monster)


def rune_income(group_id, qq_id, player, exp, gold):
    return _pkg.rune_income(group_id, qq_id, player, exp, gold)


def lucky_charm(gold, player, now):
    return _pkg.lucky_charm(gold, player, now)


def material_fold(group_id, qq_id, player, monster, gold, lucky_line):
    return _pkg.material_fold(group_id, qq_id, player, monster, gold, lucky_line)


def know_exp_bonus(group_id, qq_id, player, exp):
    return _pkg.know_exp_bonus(group_id, qq_id, player, exp)


def grant_player_exp(group_id, qq_id, player, exp):
    return _pkg.grant_player_exp(group_id, qq_id, player, exp)


# ============ 纯渲染/判定单点（真源名/签名不变） ============

def next_step_hint(group_id, qq_id, player, monster) -> str:
    return _pkg.next_step_hint(group_id, qq_id, player, monster)


def nearest_town(cur_map: str) -> str:
    return _pkg.nearest_town(cur_map)


def red_until(qq_id) -> int:
    return _pkg.red_until(qq_id)


def is_redname(qq_id) -> bool:
    return _pkg.is_redname(qq_id)


def grant_worldboss_drop(group_id, qq_id, key):
    return _pkg.grant_worldboss_drop(group_id, qq_id, key)


# ============ 大编排（命令层壳调用） ============

def victory_settle(group_id, qq_id, player, monster, result, extra_kills=None):
    return _pkg.victory_settle(group_id, qq_id, player, monster, result, extra_kills)


def defeat_settle(group_id, qq_id, player, monster, result):
    return _pkg.defeat_settle(group_id, qq_id, player, monster, result)
