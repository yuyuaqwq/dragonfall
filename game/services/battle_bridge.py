# -*- coding: utf-8 -*-
"""v181.P4 N5b 数据桥（saintess_engine 命令层适配）——旧数据层 → saintess_engine actor 翻译。

位置：game/services/（saintess_engine 包外——鱼鱼红线：saintess_engine 引擎零改动、零旧数据知识，
本桥是"命令层侧的翻译层"，把命令层手里的旧数据形态（player dict / 怪组 / pet）
翻译成 saintess_engine 的 sides actors。

翻译规则：
- 玩家（DB player dict）→ player actor：
    make_actor(uid=f"p_{qq_id}", side="player", kind="player", human_controlled=True,
               class_name/level/equipment/skills 透传，hp/mp 当前值透传)
    class_tier/attributes/evolve_path/race 透传（stats.actor_stats 重算面板用）
- 怪物（build_monster 产物 dict）→ enemy actor：
    lv → level（引擎不认 lv）；hp/max_hp/atk/def/matk/mdef/spd/crit 直读；
    身份字段 rank/reach/role/is_boss/is_elite/exp/gold/drops 透传；
    buffs/stacks/defending/charging → saintess_engine 对应字段；
    class_name/equipment/learned_skills（怪扮职业）透传；
    auto_act（怪 AI）→ actor["auto_act"]（saintess_engine actor_auto 读它）
- 宠物 pet dict → saintess_engine pet（Battle 构造 pet 参数；战斗内宠物技能由命令层/引擎按需接入）

★ B10-L4 收口（2026-09-13）：本文件 = **委托薄壳**（构造半边 + 回写半边两向全委托）
----------------------------------------------------------------
实现真源 = 包内 `games/orlandia/content/bridge.py`（构造半边 D3 批搬入；回写半边 B9-L8 批搬入
——两条方向同处一个模块）。逐函数对拍（`overnight/_b10_l4_recon.py`）：10 个同名函数里
6 个「去 docstring 后逐行相同」，其余 4 个差异全部是**已记录的宿主耦合替身**
（见下「替身接口」）⇒ 本文件是**纯冗余副本 + 2 个宿主专属件**（`attach_tlog` / `_default_db`）。

本文件只「再导出 + 一行委托」，名字 / 签名一字不变 —— 调用点零改动：

    commands/combat.py   BR.build_sides / prepare_player_for_battle(player, tb, db) /
                         apply_battle_loadout / player_to_actor / attach_tlog
                         from ..services.battle_bridge import sync_player_from_actor
    commands/tower.py / economy.py / instance_battle.py / services/battle_tlog.py /
    tests/numeric_sim.py / test_battle_bridge.py / test_battle_cmdflow.py /
    tests/test_v182_battle_tlog.py / tools/probe_phase_skill_index.py（monster_to_actor）

替身接口（宿主 db → 包内 `event_state` dict 协议；`prepare_player_for_battle` /
`apply_player_battle_start` 的第三参）：
    宿主 `db or _default_db()`                 → `_EventStateView(db or _default_db())`
    `db.get_event_state(k)`                    → `view.get(k)`
    `db.set_event_state(k, v)`                 → `view[k] = v`
    `db.delete_event_state(k)`                 → `view.pop(k, None)`
（`_EventStateView` 是 **dict 子类但不落存储**：只为满足包内 `isinstance(event_state, dict)`
 守卫；三动词全部转发宿主 db。db=None / 空 → 与旧实现同款回落 `_default_db()`。）

宿主专属件（**不进包**，留在本文件，未改一字）：`attach_tlog`（读 `game/tlog_setup` 流水开关 +
采集 sink）、`_default_db`（宿主存储层访问器 `from .. import db`）。
模块级常量（`_PLAYER_PASSTHROUGH` / `_BACK_SYNC_SCALARS` / `_BACK_SYNC_BAGS`）走 PEP 562
惰性再导出（import 期不碰包、不改宿主 import 顺序副作用）。

等价证据：`overnight/b10_l4_snap.py`（改造前后逐字节快照：构造/回写/真战斗全链）·
          `overnight/B10-L4-cond-food-wb-bridge.md`。
"""
from __future__ import annotations

from typing import Optional


# ============================================================
# 包加载口（惰性；本文件所有实现都从这里取）
# ============================================================

_PKG_BRIDGE = None          # 包内 `content.bridge` 模块缓存（惰性加载——import 期不碰包）


def _pkg_bridge():
    """包内 `content/bridge.py`（构造半边 + 回写半边唯一实现源）：首次调用加载包，之后走缓存。

    包装载口 = `game/bootstrap.package_apply()`（本进程唯一，幂等）。失败**抛**、不静默降级：
    回写漏做会让玩家存档停在开战时的值（血/增益读不到），构造漏做会让整场战斗起不来 ——
    两者都比报错难查得多。
    """
    global _PKG_BRIDGE
    if _PKG_BRIDGE is None:
        from .. import bootstrap as _bootstrap
        _bootstrap.package_apply()
        from content import bridge as _pkg
        _PKG_BRIDGE = _pkg
    return _PKG_BRIDGE


# ============================================================
# 玩家 / 怪物 → actor，sides 组装（委托）
# ============================================================

def player_to_actor(player: dict) -> dict:
    """玩家 DB dict → saintess_engine player actor（human_controlled=True）。

    ★ B10-L4：委托薄壳，实现（逐字）在包内 `content/bridge.player_to_actor`。
    """
    return _pkg_bridge().player_to_actor(player)


def monster_to_actor(mon: dict, idx: int = 0) -> dict:
    """单只怪 dict（build_monster 产物）→ saintess_engine enemy actor。

    ★ B10-L4：委托薄壳，实现（逐字）在包内 `content/bridge.monster_to_actor`。
    """
    return _pkg_bridge().monster_to_actor(mon, idx)


def enemies_to_actors(enemies: list) -> list:
    """怪组 list → enemy actor list（★ B10-L4：委托薄壳 → 包内）。"""
    return _pkg_bridge().enemies_to_actors(enemies)


def build_sides(player: Optional[dict] = None, enemies: Optional[list] = None,
                allies: Optional[list] = None) -> dict:
    """组 sides：{player: [玩家actor, ...], enemy: [怪actor, ...]}（★ B10-L4：委托薄壳 → 包内）。"""
    return _pkg_bridge().build_sides(player, enemies, allies)


def _battle_boons_to_effects(player: dict, actor: dict) -> dict:
    """开战仪式产物（`_battle_boons`）→ actor.effects 面板快照（★ B10-L4：委托薄壳 → 包内）。"""
    return _pkg_bridge()._battle_boons_to_effects(player, actor)


# ============================================================
# 开战仪式 / 装配序列（委托；第三参 db 走 `_EventStateView` 替身）
# ============================================================

class _EventStateView(dict):
    """宿主 db → 包内 `event_state` 协议替身（只用到 get / 赋值 / pop 三动词）。

    包内 `prepare_player_for_battle(player, title_bonus, event_state)` 的第三参是**普通 dict**
    （等价宿主 event_state 存储）。本类把宿主 db 的三动词接上：

        view.get(k)                 → db.get_event_state(k)
        view[k] = v                 → db.set_event_state(k, v)
        view.pop(k, default)        → db.delete_event_state(k)（键不存在则返回 default）

    `dict` 子类**只为**满足包内 `isinstance(event_state, dict)` 守卫 —— 键值**不落本对象**
    （`__setitem__` 已改道 db），故本对象不持有第二份状态。
    ⚠️ 契约：包内对 `event_state` 只用上述三动词；若包内改用 `setdefault` / `in` / 迭代，
       会落到 dict 自己的空存储上（静默偏差）→ 改包内那侧时必须同步改这里。
    """

    __slots__ = ("_db",)

    def __init__(self, db):
        super().__init__()
        self._db = db

    def get(self, key, default=None):
        v = self._db.get_event_state(key)
        return default if v is None else v

    def __setitem__(self, key, value):
        self._db.set_event_state(key, value)

    def pop(self, key, default=None):
        v = self._db.get_event_state(key)
        if v is None:
            return default
        self._db.delete_event_state(key)
        return v


def _es_arg(db):
    """宿主第三参 `db` → 包内 `event_state` 替身（`db or _default_db()`，与旧实现一字同款）。"""
    return _EventStateView(db or _default_db())


def prepare_player_for_battle(player: dict, title_bonus: Optional[dict] = None,
                              db=None) -> dict:
    """开战仪式（player dict 侧，build_sides 前调用）—— 委托薄壳，实现见包内 `content/bridge`。

    ★ B10-L4：实现（逐字，含 4 步：字段播种 / max_hp·max_mp 实时重算 / echo_bless 消费 /
    神龛祝福消费）在包内；本函数只把第三参 `db` 适配成包内 `event_state` dict 协议
    （见 `_EventStateView`）。签名 / 语义 / 返回（原地补全后同一引用）一字不变。
    """
    return _pkg_bridge().prepare_player_for_battle(player, title_bonus, _es_arg(db))


def apply_player_battle_start(player: dict, actor: dict, db=None) -> dict:
    """把旧 Battle.__init__ 的玩家侧开战仪式结果应用到 actor（★ B10-L4：委托薄壳 → 包内）。

    保留旧签名/语义（命令层调用点可能传 actor）；返回 actor（原地补全后同一引用）。
    """
    return _pkg_bridge().apply_player_battle_start(player, actor, _es_arg(db))


def apply_battle_loadout(actor: dict, title_bonus: Optional[dict] = None) -> dict:
    """开战装配序列（每个 player actor 调一次）：外部面板增幅 + 装备词条 + 职业机制。

    ★ B10-L4：委托薄壳 —— 序列本身（① `actor["bonus"]` 播种 ② 装备装配 ③ 职业机制装配）
    与 ②③ 的**静默容错**（个别词条/技能解析失败不阻断开战）逐字在包内
    `content/bridge.apply_battle_loadout`（②③ 的实现来源 = 包内 `content/mech/{equip,class_mech}`）。
    三处生产调用点（combat `_open_battle` / `_open_pvp`、tower）零改动。
    """
    return _pkg_bridge().apply_battle_loadout(actor, title_bonus)


def _seed_battle_keys(player: dict) -> dict:
    """玩家战斗可变键播种（★ B10-L4：委托薄壳 → 包内）。"""
    return _pkg_bridge()._seed_battle_keys(player)


# ============================================================
# 流水挂载（宿主专属件 —— 不进包；读 game/tlog_setup 开关 + 采集 sink）
# ============================================================

def attach_tlog(b, *, btype: str = "monster", player=None, enemies=None, seed=None):
    """给一场战斗挂**流水采集**（可拔插：未启用流水时**零行为**，直接返回 `b`）。

    开关在 `game/tlog_setup.py`（`DRAGONFALL_TLOG=1` 或显式 `enable()`）；
    采集器与回放见 `game/services/battle_tlog.py`，设计见 `docs/REFACTOR_tlog_landing.md`。
    调用点：开战处一行（`combat._open_battle` 等）；异常一律吞掉 —— 流水不该影响开战。

    ⚠️ 本函数**不委托包内**：它读宿主流水开关与 sink（`game.tlog_setup` / `battle_tlog`），
    属宿主侧契约（包内 `content/bridge.py` 头注「未搬」清单第 1 项）。
    """
    try:
        from ..tlog_setup import tlog as _tlog
        tl = _tlog()
        if tl is None:
            return b
        from .battle_tlog import BattleTLog
        BattleTLog(tl).attach(b, btype=btype, seed=seed, player=player, enemies=enemies)
    except Exception:                                         # noqa: BLE001
        pass
    return b


# ============================================================
# 战斗回写（actor → 命令层 player dict）
# ------------------------------------------------------------
# 实现真源 = 包内 `content/bridge.py:sync_player_from_actor`（回写半边与构造半边同处一个模块；
# B9-L8 批搬入）。本文件只留一层委托 —— 调用点（`from ..services.battle_bridge import
# sync_player_from_actor` / `BR.sync_player_from_actor`）零改动：签名 / 语义 / 返回
# （原地回写后同一引用）一字不变。等价证据：`overnight/b9_l8_backsync_verify.py`（三源逐字节）
# · `overnight/b9_l8_snap.py` · 报告 `overnight/B9-L8-bridge.md`。
# ============================================================

def sync_player_from_actor(player: dict, actor: dict) -> dict:
    """saintess_engine actor 战斗后状态 → player dict 回写（命令层行动后调用）。

    旧 Battle 构造时把 player dict 直接当 _focus 引用，引擎内 hp/buffs 改动
    自动落在 player dict 上；saintess_engine 的 player actor 是 make_actor 副本，
    命令层在每次 human_act / 战斗结束结算前调用本函数，把战斗结果同步回
    player dict，后续 db.update_player / 展示面板读到的才是最新值。

    ★ B9-L8 起：本函数 = 一层委托薄壳 —— 实现（逐字）在包内 `content/bridge.py`。
    """
    return _pkg_bridge().sync_player_from_actor(player, actor)


def _default_db():
    """延迟取宿主存储层（避免顶部循环 import）。★ 宿主专属件（不进包）。"""
    from .. import db as _db
    return _db


# 模块级常量：PEP 562 惰性再导出（import 期不碰包）
_LAZY = ("_PLAYER_PASSTHROUGH", "_BACK_SYNC_SCALARS", "_BACK_SYNC_BAGS")


def __getattr__(name):
    """PEP 562：把模块级常量转发到包内那份（同一元组对象 —— 双源已收口）。"""
    if name in _LAZY:
        return getattr(_pkg_bridge(), name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
