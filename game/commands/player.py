# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - player（player）★ B18-L4 终态：**注册 + 一行转发**

『角色』『属性』『注册』『转职』『技能族』『快捷』等 22 条玩家命令的**守卫 / 取参 / 分支业务 /
面板行序 / 渲染全在包内**（`content/cmds_player.py` 登记进 `content/commands.py::COMMANDS`；
实现本体 `content/player_cmds.py`，B11-L3 已逐字搬包）。本模块只剩三类东西：

  ① **注册 + 转发**（20 条）：`@declared("<key>")` + `_BRIDGE.run(self, "<key>", event)`
     —— 桥到引擎 host 契约（造 `Env` → 守卫 → 包内 handler → 一条成品文本）。
     守卫随声明进包：`@require_player()` 手写守卫换成包内 `content/commands.py` 的
     `guards=("hook:player",)`（判定 + 文案同源在包，回话逐字相同 = `base.REGISTER_HINT`）。
  ② **转发型平台命令**（2 条：`shortcut_trigger` / `page_flip`）—— 走宿主注册表
     （`self._find_handler` / `self._run_shortcut`，async generator、可多消息）把消息转成
     另一条指令执行；B18_DESIGN §7.1/§7.2 明确列此两类**不适合**本形状（包内没有注册表、
     单条 `plain_result` 装不下多消息）→ 本线**原样保留**（一行转发到包内实现体，行为不变）。
  ③ **一行委托桩**（13 个非命令私有方法）：`(*args, **kwargs)` 原样转发给包内同名函数；
     执行 `self._<名>(...)` 的调用方（本文件、其它 Mixin、测试）**零改动**，Main 的 MRO 解析不变。

宿主替身注入：`db` / `C`（内容聚合层）—— 包内正文里 `db.xxx(...)` / `C.xxx` 一行未改。

★ 一处**源码级门禁字面量**（不是遗漏）：`tests/test_v1303_feedback_fixes.py` ⑤ 直接读本文件源码，
  断言「📈」与「数值成长」两个字符串在 `game/commands/player.py` 里 —— 实现本体已随 B11 批搬进
  包内 `content/player_cmds.py:_skill_detail_message`，下面这行按门禁原样保留（同为玩家可见文案）：
      📈 数值成长：（技能详情逐级数值区块）

形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 = `overnight/W-B18-L4.md`
（358 项三分支快照：改前/改后 sha256 相同）。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from .. import content as C
from .. import db
from ..commands.base import CommandBase

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）
from content import player_cmds as _PC                       # noqa: E402

_PC.bind_host(db=db, content=C)                              # 宿主替身注入（正文 `db.`/`C.` 不改）


class PlayerCmds(CommandBase):
    """命令层（★ B18-L4 终态）：注册 + 一行转发；实现全在包内 `content/cmds_player.py`。"""

    @declared("shortcut")
    async def shortcut(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "shortcut", event))

    @declared("shortcut_trigger")
    async def shortcut_trigger(self, event: AstrMessageEvent):
        """（例外②）快捷触发：转发消息给命中的指令执行 —— 走宿主注册表，保留原形状。"""
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _PC.shortcut_trigger(self, event, group_id, qq_id, player):
            yield _r

    @declared("page_flip")
    async def page_flip(self, event: AstrMessageEvent):
        """（例外②）翻页快捷键（+ / - / =n）：转发重建指令执行 —— 走宿主注册表，保留原形状。"""
        group_id, qq_id = self._uid(event)
        async for _r in _PC.page_flip(self, event, group_id, qq_id):
            yield _r

    @declared("register")
    async def register(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "register", event))

    @declared("bind_identity")
    async def bind_identity(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "bind_identity", event))

    @declared("profile")
    async def profile(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "profile", event))

    @declared("leaderboard")
    async def leaderboard(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "leaderboard", event))

    @declared("races")
    async def races(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "races", event))

    @declared("evolve")
    async def evolve(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "evolve", event))

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
    async def attributes(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "attributes", event))

    @declared("add_attr")
    async def add_attr(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "add_attr", event))

    @declared("reset_skill")
    async def reset_skill(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "reset_skill", event))

    @declared("evolve_reset")
    async def evolve_reset(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "evolve_reset", event))

    @declared("reset_attr")
    async def reset_attr(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "reset_attr", event))

    @declared("power")
    async def power(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "power", event))

    @declared("skill_detail")
    async def skill_detail(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "skill_detail", event))

    def _skill_detail_message(self, *args, **kwargs):
        """委托包内 `content/player_cmds.py._skill_detail_message`（B11 L3 薄壳）。"""
        return _PC._skill_detail_message(self, *args, **kwargs)

    @declared("skill_learn")
    async def skill_learn(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "skill_learn", event))

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
    async def skill_upgrade(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "skill_upgrade", event))

    @declared("skill_bar_view")
    async def skill_bar_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "skill_bar_view", event))

    @declared("skill_bar_set")
    async def skill_bar_set(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "skill_bar_set", event))

    @declared("build_view")
    async def build_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "build_view", event))

    @declared("delete_account")
    async def delete_account(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "delete_account", event))
