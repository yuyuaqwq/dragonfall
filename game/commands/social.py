# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - social（social）★ B18-L8 终态：**一行转发**

33 条社交命令的**守卫 / 取参 / 分支业务 / 面板行序 / 渲染全在包内**
（`content/cmds_social.py` 登记进 `content/commands.py::COMMANDS`）。本模块只剩三件事：

  ① **注册**：`@declared("<key>")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "<key>", event)` —— 桥到引擎 host 契约（造 `Env` → 守卫
     → 包内 handler → 一条成品文本）
  ③ **私有方法桩**：非命令的 `_xxx` 一行委托（其它 Mixin/测试按 MRO 直调，名字集合与改造前逐名相同）；
     外加三个既有包模块的**宿主替身注入**（`bind_host`，与 `game/commands/world.py` 同款）

宿主里**零** 文案调用点（`grep -c 'T\\.text\\|T\\.static' game/commands/social.py` = 0）。

★ **三条异步命令的例外（有先例，非遗漏）**
  · `world_event` / `auction` / `bid` 的实现体要 `await` 平台广播（`shell._broadcast` → 真挂起），
    同步桥 `_BRIDGE.run` 跑不了 → 按 B18-L3c 战斗族先例，包内用 `_declare` 登记为 `async def`，
    宿主这两行用 `_BRIDGE.run_async`（逐条 `yield`，与改造前 `for _line in await …: yield`
    的消息切分逐字相同）。其余 30 条一律一行 `_BRIDGE.run`。

改动前的实现去向（搬家不是重写；B9-L3 / B12-L1 / B12-L4 已先搬走大部分实现体）
  · `content/social_stall.py` ← 市场/摆摊族的解析与守卫（本文件只留编排）
  · `content/social_guild.py` ← 公会全族（经 `game/services/guild.py` 同名薄壳取）
  · `content/social_pet.py` ← 宠物面板/改名/喂养/放生/坐骑
  · `content/social_cmds.py` ← 世界事件惰性调度 + 事件/拍卖/竞拍面板
  · `content/party.py` ← 组队族（经 `game/services/party.py` 同名薄壳取）
  · `content/cmds_social.py` ← **本线**：上列之外的全部宿主编排（守卫/取参/分支/提示行/记账）

形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 =
`overnight/W-B18-L8-social.md`（129 项三分支快照 sha256 改前 = 改后）。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import db
from .. import content as C
from ..commands.base import CommandBase
from ..store import social as _store_social          # noqa: F401  包门面注入用（模块本体）

from . import _host_bridge as _BRIDGE

# ============================================================================
# 包加载 + 宿主替身注入（幂等；与 game/commands/world.py 同款）
#   · `social_stall` / `social_pet` / `social_cmds` 三个包内模块的 `bind_host` 注入位
#     在**宿主薄壳 import 期**调用（包内不 import 宿主，I2）；`services.guild` /
#     `services.party` 的替身由那两个同名薄壳自己的 import 期注入完成。
# ============================================================================
from .. import bootstrap as _bootstrap               # noqa: E402
from ..services import guild as _GSD                 # noqa: E402,F401  触发包内 social_guild 注入

_bootstrap.package_apply()                           # 包加载口（幂等；失败抛，不静默）
from content import social_stall as _SS               # noqa: E402
from content import social_pet as _SP                 # noqa: E402
from content import social_cmds as _SC                # noqa: E402

_SS.bind_host(db, maps=C.MAP_BY_ID, house_levels=C.HOUSE_LEVELS, quality=C.QUALITY,
              econ=C.ECON_CONFIG, store_social=_store_social)
_SP.bind_host(db, content=C, quality=C.QUALITY)
_SC.bind_host(db=db, content=C)


class SocialCmds(CommandBase):
    """命令层（★ B18-L8 终态）：注册 + 一行转发；守卫/取参/业务/渲染全在包内 `content/cmds_social.py`。"""

    # ---------------- 市场 ----------------
    @declared("market")
    async def market(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "market", event))

    @declared("market_sell")
    async def market_sell(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "market_sell", event))

    @declared("market_unsell")
    async def market_unsell(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "market_unsell", event))

    @declared("market_buy")
    async def market_buy(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "market_buy", event))

    # ---------------- v66 摆摊系统（v167 拆分为 摆卖/摆换 两指令，鱼鱼拍板） ----------------
    # 『摆卖 <物/背包序号> <单价> [数量]』= 摆摊出售（金币）
    # 『摆换 <物/背包序号> [数量]』       = 摆摊以物换物（无金币价）
    # 『收摊』『摊位』『换 <编号> <物品>』 维持不变
    # 说明：v167 起废弃老『摆摊』一词（它同时承载卖/换两种语义靠有无价格区分，
    # 与数量参数互相歧义——一介散人『咕噜的皇冠』同名事件暴露按名匹配的坑）。
    # 老『摆摊』仅作引导提示（v167.1 意见：不静默消失）；`priority=5` 让位给新指令。
    @declared("stall_deprecated", priority=5)
    async def stall_deprecated(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "stall_deprecated", event))

    @staticmethod
    def _stall_label(s):
        """摊位价格标签：price>0 → 'N 金币'；price=0 → '🔄 换'(以物换物)。

        B9-L3：实现已进包（`content/social_stall.py:stall_label`）；本方法只作薄委托 ——
        `game/commands/world.py:2418` 仍按 `self._stall_label(...)` 调用（命令层共用壳）。
        """
        return _SS.stall_label(s)

    @declared("stall_sell")
    async def stall_sell(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "stall_sell", event))

    @declared("stall_exchange_pawn")
    async def stall_exchange_pawn(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "stall_exchange_pawn", event))

    @declared("stall_close")
    async def stall_close(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "stall_close", event))

    @declared("stall_view")
    async def stall_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "stall_view", event))

    @declared("stall_exchange")
    async def stall_exchange(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "stall_exchange", event))

    # ---------------- 组队 ----------------
    @declared("party")
    async def party(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "party", event))

    @declared("party_leave")
    async def party_leave(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "party_leave", event))

    # ---------------- 公会 ----------------
    @declared("guild_create_cmd")
    async def guild_create_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_create_cmd", event))

    @declared("guild_join_cmd")
    async def guild_join_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_join_cmd", event))

    @declared("guild_leave_cmd")
    async def guild_leave_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_leave_cmd", event))

    @declared("guild_disband_cmd")
    async def guild_disband_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_disband_cmd", event))

    @declared("guild_info")
    async def guild_info(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_info", event))

    @declared("guild_sign")
    async def guild_sign(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_sign", event))

    @declared("guild_task")
    async def guild_task(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_task", event))

    @declared("guild_donate_cmd")
    async def guild_donate_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_donate_cmd", event))

    @declared("guild_rank")
    async def guild_rank(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_rank", event))

    # ---------------- v116 公会成长纵深：公会商店 / 公会技能 / 职位体系 ----------------
    @declared("guild_shop")
    async def guild_shop(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_shop", event))

    @declared("guild_skill_view")
    async def guild_skill_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_skill_view", event))

    @declared("guild_appoint")
    async def guild_appoint(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_appoint", event))

    @declared("guild_demote")
    async def guild_demote(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "guild_demote", event))

    # ---------------- 宠物 / 坐骑 ----------------
    @declared("pet_view")
    async def pet_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "pet_view", event))

    @declared("pet_rename")
    async def pet_rename(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "pet_rename", event))

    @declared("pet_feed")
    async def pet_feed(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "pet_feed", event))

    @declared("pet_release")
    async def pet_release(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "pet_release", event))

    @declared("mount_cmd")
    async def mount_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "mount_cmd", event))

    # ---------------- 世界事件 / 拍卖 / 竞拍（异步：见模块头注 ★） ----------------
    async def _maybe_roll_event(self, group_id: str) -> str:
        """（B12-L1 薄壳：转调包内 `content/social_cmds.maybe_roll_event`，实现真源已进包）"""
        return await _SC.maybe_roll_event(group_id, self._broadcast)

    @declared("world_event")
    async def world_event(self, event: AstrMessageEvent):
        async for _r in _BRIDGE.run_async(self, "world_event", event):
            yield _r

    def _settle_auction(self, cur, group_id: str) -> str:
        """（v181 P4-5 兼容壳：转调 game/services/auction.settle_auction——拍卖到期结算本体已下沉 service）"""
        from ..services.auction import settle_auction as _sa
        return _sa(cur, group_id)

    @declared("auction")
    async def auction(self, event: AstrMessageEvent):
        async for _r in _BRIDGE.run_async(self, "auction", event):
            yield _r

    @declared("bid")
    async def bid(self, event: AstrMessageEvent):
        async for _r in _BRIDGE.run_async(self, "bid", event):
            yield _r
