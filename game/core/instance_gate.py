# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - instance_gate.py —— **B11-L2 薄壳**（副本准入域）

真源（唯一实现）已进包：`framework/games/orlandia/content/flow/instance_gate.py`
（v185 端口；规则顺序 + 全部措辞只此一处）。本文件只剩三件事：

| 本文件 | 归属 | 说明 |
|---|---|---|
| `find_instance_key_item(group_id, qq_id, key_item)` | **宿主独有**（DB 取数） | 背包 = `db.get_inventory`、ITEMS = 宿主聚合层 `C.ITEMS`；判定本体在包内 |
| `instance_cleared_qq(group_id, qq_id, inst_key)` | **宿主独有**（DB 取数） | 成就记录 = `db.get_achievements`；判定本体在包内 |
| 链与文案口的名字再导出 | 包内 | `resolve_open_members` / `member_rule` / `resume_admission` / `key_free_note` / `key_rule` / `open_admission` / `walk_admission` / `join_admission` + 14 个 `text_*` / `stamina_short_msg` + `Rule` / `Admission` |

文案：`_G.set_text_table(T.table())` —— 包内渲染挂**宿主**文案表（`game/data/text_specs.json`
仍是唯一真源，缺 key 仍走宿主 `on_miss` 的 ERROR 日志）。

调用点零改动：`commands/instance.py`（4 处）· `commands/world.py`（3 处）· `commands/base.py`（1 处，
只用 `stamina_short_msg`）· 测试 import 点。名字/签名/返回与改造前逐字一致。

★ 三条门禁面为什么长这样（照现有门禁写，不是随手）：
1. `tests/test_texts_table.py:81 WIRED["副本准入"]` 对本文件做 **AST 扫描**（声明 ↔ 调用点）：
   域名 26 条 key 必须在**本文件**里出现 ⇒ 文末 `_DOMAIN_KEYS` 登记，并在 import 期核对宿主表已声明。
2. `tests/test_v185_gate_teeth.py` 猴补**本模块属性**（`text_leader_only` / `stamina_short_msg` /
   `open_admission` / `join_admission`）来证明门禁有牙 ⇒ 链入口 `_bind_text_funcs()` 在每次调用前
   把本模块的同名文案函数接回包内全局（猴补因此仍对包内链生效）。
3. `tests/test_v185_instance_admission.py`：805 格逐格比对走本模块属性（再导出即可）；
   其 `t7_wiring` 扫的是 `instance.py`/`world.py`/`base.py` 源码，与本文件无关。
"""
from __future__ import annotations

import sys
from typing import Optional

from saintess_engine.run import Admission, Rule

from .. import bootstrap as _BST

_BST.package_apply()                                      # 本进程唯一包加载口（幂等；失败抛）
from content.flow import instance_gate as _G              # noqa: E402  包内实现（唯一真源）
from . import texts as T                                  # noqa: E402  宿主文案表（唯一真源）

_G.set_text_table(T.table())                              # 包内文案口挂宿主表（on_miss 同源）


# ======================================================================
# 一、宿主独有：DB 取数入口（判定本体在包内；`db`/`C` 延迟导入保持装配期零耦合）
# ======================================================================


def find_instance_key_item(group_id: str, qq_id: str, key_item: str) -> Optional[dict]:
    """三路匹配背包钥匙条目（宿主侧取数：`db.get_inventory` + `C.ITEMS`；匹配在包内）。"""
    from .. import db
    try:
        from .. import content as C  # 内容层（聚合 data.ITEMS）
        _items = getattr(C, "ITEMS", {}) or {}
    except Exception:
        _items = {}
    return _G.find_instance_key_item(db.get_inventory(group_id, qq_id) or [], key_item,
                                     items=_items)


def instance_cleared_qq(group_id: str, qq_id: str, inst_key: str) -> bool:
    """玩家是否已通关某副本（宿主侧取数：`db.get_achievements`；判定在包内）。"""
    from .. import db
    return _G.instance_cleared(db.get_achievements(group_id, qq_id) or [], inst_key)


# ======================================================================
# 二、包内链入口（唯一实现；调用前把宿主文案函数接回包内全局 → 猴补面活着）
# ======================================================================


def _bind_text_funcs() -> None:
    """把本模块的 12 个文案函数接进包内全局（`tests/test_v185_gate_teeth.py` 猴补面）。

    包内链按模块全局名调用文案函数；本函数在每次链入口调用前重挂一次（幂等、零副作用），
    于是「猴补 `instance_gate.text_leader_only`」对包内链同样生效。
    """
    _self = sys.modules[__name__]
    for _n in _TEXT_FUNCS:
        setattr(_G, _n, getattr(_self, _n))


def resolve_open_members(inst: dict, my_key: str, party) -> tuple:
    _bind_text_funcs()
    return _G.resolve_open_members(inst, my_key, party)


def member_rule(member, ctx, *, with_prof_wait: bool = True):
    _bind_text_funcs()
    return _G.member_rule(member, ctx, with_prof_wait=with_prof_wait)


def resume_admission(ctx: dict):
    _bind_text_funcs()
    return _G.resume_admission(ctx)


def key_free_note(ctx: dict) -> str:
    _bind_text_funcs()
    return _G.key_free_note(ctx)


def key_rule(ctx):
    _bind_text_funcs()
    return _G.key_rule(ctx)


def open_admission(ctx: dict):
    _bind_text_funcs()
    return _G.open_admission(ctx)


def walk_admission(ctx: dict):
    _bind_text_funcs()
    return _G.walk_admission(ctx)


def join_admission(ctx: dict):
    return _G.join_admission(ctx)


# 文案函数：再导出自包内（实现 = 包内；`_bind_text_funcs` 会按本模块当前属性回挂）
stamina_short_msg = _G.stamina_short_msg
text_party_need = _G.text_party_need
text_leader_only = _G.text_leader_only
text_too_few = _G.text_too_few
text_too_many = _G.text_too_many
text_member_no_char = _G.text_member_no_char
text_member_level = _G.text_member_level
text_member_dead = _G.text_member_dead
text_member_in_battle = _G.text_member_in_battle
text_member_prof_wait = _G.text_member_prof_wait
text_key_seal = _G.text_key_seal
text_entry_hint = _G.text_entry_hint
text_walk_deny = _G.text_walk_deny
text_bad_profile = _G.text_bad_profile

# 会被包内链内部调用的文案函数（`_bind_text_funcs` 的挂载名单）
_TEXT_FUNCS = ("stamina_short_msg", "text_party_need", "text_leader_only", "text_too_few",
               "text_too_many", "text_member_no_char", "text_member_level", "text_member_dead",
               "text_member_in_battle", "text_member_prof_wait", "text_key_seal",
               "text_walk_deny")
_bind_text_funcs()


# ======================================================================
# 三、域名「副本准入」26 条 key 的宿主声明面（tests/test_texts_table.py WIRED 对账面）
# ======================================================================
# 调用点已随实现进包；此处登记 key 面 + import 期核对宿主文案表确实声明了它们
# （防「声明 ↔ 调用点」AST 对账把域名判成死文案，也防宿主表漏 key）。
_DOMAIN_KEYS = (
    "instance.already_in", "instance.bad_profile", "instance.battle_full",
    "instance.battle_not_instance", "instance.battle_over", "instance.battle_retreated",
    "instance.entry_hint", "instance.i_am_leader", "instance.join_closed", "instance.join_dead",
    "instance.key_free_note", "instance.key_seal", "instance.leader_only",
    "instance.member_dead", "instance.member_in_battle", "instance.member_level",
    "instance.member_no_char", "instance.member_prof_wait", "instance.no_enemy_left",
    "instance.no_joinable", "instance.no_party", "instance.party_need", "instance.stamina_short",
    "instance.too_few", "instance.too_many", "instance.walk_deny",
)
_missing_keys = [k for k in _DOMAIN_KEYS if T.table().spec(k) is None]
if _missing_keys:                                        # pragma: no cover - 配置错误即抛
    raise RuntimeError("副本准入域名下 key 未在文案表声明：%s" % (_missing_keys,))
