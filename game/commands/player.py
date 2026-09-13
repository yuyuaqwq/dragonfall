# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - player（player）—— B11 L3 **薄壳**

由 main.py 拆分而来，作为 Mixin 被 Main 继承。**B11 L3（2026-09-14）薄壳化**后本文件只剩四件事：

    命令注册（`@declared` 装饰器）· 取玩家（`self._uid` / `self._player`）· 调包（一行转发）· 渲染

真源（实现本体）全在内容包：`content/player_cmds.py`（35 个方法逐字搬过去，见那边的头注）。
本文件保留的方法只有两类：

  · **命令入口**（22 个）：装饰器 + 「取玩家 + `async for _r in _PC.<名>(...)`」转发；
    名字/装饰器/注册序与改造前逐行相同（`@declared` 是宿主侧的**注册**动作：正则来自
    `game/data/command_specs.json`，框架注册表 + `_registry` 都从它派生）。
  · **一行委托桩**（13 个）：非命令私有方法，`(*args, **kwargs)` 原样转发给包内同名函数。
    执行 `self._<名>(...)` 的调用方（本文件、其它 Mixin、测试）**零改动**：名字集合与改造前
    逐名相同 → Main 的 MRO 解析结果不变。

宿主替身注入：`db` / `C`（内容聚合层）—— 包内正文里 `db.xxx(...)` / `C.xxx` **一行未改**。

★ 一处**源码级门禁字面量**（不是遗漏）：`tests/test_v1303_feedback_fixes.py` ⑤ 直接读本文件源码，
  断言「📈」与「数值成长」两个字符串在 `game/commands/player.py` 里 —— 实现本体已随本批搬进
  包内 `content/player_cmds.py:_skill_detail_message`，下面这行按门禁原样保留（同为玩家可见文案）：
      📈 数值成长：（技能详情逐级数值区块）
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import content as C
from .. import db
from ..commands.base import CommandBase, require_player

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）
from content import player_cmds as _PC                       # noqa: E402

_PC.bind_host(db=db, content=C)                              # 宿主替身注入（正文 `db.`/`C.` 不改）


class PlayerCmds(CommandBase):
    """命令层（B11 L3 薄壳）：注册 + 取玩家 + 调包 + 渲染；实现全在包内 `content/player_cmds.py`。"""

    @declared("shortcut")
    @require_player()
    async def shortcut(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.shortcut(self, event, group_id, qq_id, player):
            yield _r

    @declared("shortcut_trigger")
    async def shortcut_trigger(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.shortcut_trigger(self, event, group_id, qq_id, player):
            yield _r

    @declared("page_flip")
    async def page_flip(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _PC.page_flip(self, event, group_id, qq_id):
            yield _r

    @declared("register")
    async def register(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _PC.register(self, event, group_id, qq_id):
            yield _r

    @declared("bind_identity")
    async def bind_identity(self, event: AstrMessageEvent):
        async for _r in _PC.bind_identity(self, event):
            yield _r

    @declared("profile")
    @require_player()
    async def profile(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.profile(self, event, group_id, qq_id, player):
            yield _r

    @declared("leaderboard")
    async def leaderboard(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _PC.leaderboard(self, event, group_id, qq_id):
            yield _r

    @declared("races")
    async def races(self, event: AstrMessageEvent):
        async for _r in _PC.races(self, event):
            yield _r

    @declared("evolve")
    @require_player()
    async def evolve(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.evolve(self, event, group_id, qq_id, player):
            yield _r

    def _branch_title(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._branch_title`（B11 L3 薄壳）。"""
        return _PC._branch_title(self, *args, **kwargs)

    def _hidden_alias_map(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._hidden_alias_map`（B11 L3 薄壳）。"""
        return _PC._hidden_alias_map(self, *args, **kwargs)

    def _hidden_class_routes(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._hidden_class_routes`（B11 L3 薄壳）。"""
        return _PC._hidden_class_routes(self, *args, **kwargs)

    def _hidden_tier_levels(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._hidden_tier_levels`（B11 L3 薄壳）。"""
        return _PC._hidden_tier_levels(self, *args, **kwargs)

    async def _evolve_hidden_status(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._evolve_hidden_status`（B11 L3 薄壳）。"""
        async for _r in _PC._evolve_hidden_status(self, *args, **kwargs):
            yield _r

    async def _evolve_hidden_generic(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._evolve_hidden_generic`（B11 L3 薄壳）。"""
        async for _r in _PC._evolve_hidden_generic(self, *args, **kwargs):
            yield _r

    def _evolve_auto_skills(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._evolve_auto_skills`（B11 L3 薄壳）。"""
        return _PC._evolve_auto_skills(self, *args, **kwargs)

    def _tier_title(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._tier_title`（B11 L3 薄壳）。"""
        return _PC._tier_title(self, *args, **kwargs)

    @declared("attributes")
    @require_player()
    async def attributes(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.attributes(self, event, group_id, qq_id, player):
            yield _r

    @declared("add_attr")
    @require_player()
    async def add_attr(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.add_attr(self, event, group_id, qq_id, player):
            yield _r

    @declared("reset_skill")
    @require_player()
    async def reset_skill(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.reset_skill(self, event, group_id, qq_id, player):
            yield _r

    @declared("evolve_reset")
    @require_player()
    async def evolve_reset(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.evolve_reset(self, event, group_id, qq_id, player):
            yield _r

    @declared("reset_attr")
    @require_player()
    async def reset_attr(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.reset_attr(self, event, group_id, qq_id, player):
            yield _r

    @declared("power")
    @require_player()
    async def power(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.power(self, event, group_id, qq_id, player):
            yield _r

    @declared("skill_detail")
    @require_player()
    async def skill_detail(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.skill_detail(self, event, group_id, qq_id, player):
            yield _r

    def _skill_detail_message(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._skill_detail_message`（B11 L3 薄壳）。"""
        return _PC._skill_detail_message(self, *args, **kwargs)

    @declared("skill_learn")
    @require_player()
    async def skill_learn(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.skill_learn(self, event, group_id, qq_id, player):
            yield _r

    def _skill_learn_msg(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._skill_learn_msg`（B11 L3 薄壳）。"""
        return _PC._skill_learn_msg(self, *args, **kwargs)

    def _skill_cast_text(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._skill_cast_text`（B11 L3 薄壳）。"""
        return _PC._skill_cast_text(self, *args, **kwargs)

    def _skill_formula_text(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._skill_formula_text`（B11 L3 薄壳）。"""
        return _PC._skill_formula_text(self, *args, **kwargs)

    def _skill_upgrade_gains(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._skill_upgrade_gains`（B11 L3 薄壳）。"""
        return _PC._skill_upgrade_gains(self, *args, **kwargs)

    @declared("skill_upgrade")
    @require_player()
    async def skill_upgrade(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.skill_upgrade(self, event, group_id, qq_id, player):
            yield _r

    @declared("skill_bar_view")
    @require_player()
    async def skill_bar_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.skill_bar_view(self, event, group_id, qq_id, player):
            yield _r

    @declared("skill_bar_set")
    @require_player()
    async def skill_bar_set(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.skill_bar_set(self, event, group_id, qq_id, player):
            yield _r

    @declared("build_view")
    @require_player()
    async def build_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.build_view(self, event, group_id, qq_id, player):
            yield _r

    @declared("delete_account")
    @require_player()
    async def delete_account(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.delete_account(self, event, group_id, qq_id, player):
            yield _r
