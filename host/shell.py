# -*- coding: utf-8 -*-
"""宿主命令壳（`HostShell`）—— **终态宿主壳**（P5C：`game/commands/**` 194 壳的收编体）。

它是什么
--------
引擎 host 契约把「一条消息 → 引擎 `Env` → 包内 handler」打通；包内 handler 的**实现体**
仍需要一个「平台能力面」对象（历史形态 = 宿主 Mixin 壳 `Main`，包内一律经
`env.state["shell"]` 取它）。本文件就是那只壳的终态落点：**引擎通用那一半 + 宿主平台那一半**，
**内容那一半全部转引包内真源**。

| 面 | 来源 | 说明 |
|---|---|---|
| 分页 / 页码 / 文本剥离 / 提示抽取 / handler 路由 / `_run_shortcut` | 引擎 `saintess_engine.command.base.CommandBase` | 一行不抄 |
| 体力族 / 设施判定 / 提示库 / 别名 | 包内 `cmds_base_rules`（经 `Package.optional_submodule`） | 内容规则只此一份 |
| 面板增幅 / 行为规则 | 包内 `stat_bonus` · `rule_engine` | 同上 |
| 认人 / 读档 / 落状态 / 战斗判定 | 引擎 `SessionAdapter` + 存档半边（`persistence`） | 平台适配在 `host/_identity.py` |
| 平台动作（广播 / 通知 / 停服 gate / 4 条平台例外） | 本文件 + `host/_platform.py` + `host/adapter_qq.py` | 真·平台面 |
| 渲染（句子） | **包内** `texts`（经 `optional_submodule("texts")`） | 宿主零句子 |

零包知识口径（本文件为何用 `optional_submodule` 而不是 `import content.x`）
------------------------------------------------------------------------
plan §6⑨ ① 要求宿主里不出现包名 / `content.*`。本文件因此**不写任何包内模块字面量**：
包对象由装配处（`main.py` / 测试驱动口）经配置给出，包内半边一律按**半边名**向
`Package.optional_submodule(name)` 取（引擎公开 API，名字是契约里的半边名，不是模块路径）。

历史来源（逐条可查，不重写语义）
--------------------------------
`game/commands/base.py`（`CommandBase` 平台钩子 / `_maint_gate` / `_GameCmdFilter`）·
`game/commands/{player,world,combat,misc,social,gm,instance,instance_router}.py` 里**平台专有**的
少量方法（`_stall_label` / `_HURRY_ALIAS` / `_instance_gate_block` / 平台例外 5 条）。
其余方法都是「转引包内真源」，与旧壳逐名同义（旧壳本身就是 `_RULES.xxx` 一行转发）。
"""
from __future__ import annotations

import functools
import json
import logging
import os
import re

from saintess_engine.command import CommandBase as _EngineCommandBase
from saintess_engine.session import SessionAdapter

from . import _identity as _host_identity

LOG = logging.getLogger("astrbot")


def _noop(*_a, **_k):
    return None


class HostShell(_EngineCommandBase):
    """终态宿主壳：`env.state["shell"]`（引擎 `Host.build_env` 之前由装配处注入 `inject`）。"""

    logger_name = "astrbot"

    #: 赶路别名表（原 `game/commands/world.py` 类属性，包内 `world_cmds.py:1103` 以 `self._HURRY_ALIAS` 取用）
    _HURRY_ALIAS = {
        "npc": "npc", "怪物": "monster", "monster": "monster",
        "场景": "scene", "scene": "scene", "景物": "scene",
        "设施": "facility", "facility": "facility", "商店": "facility",
    }

    def __init__(self, *, pkg=None, store=None, context=None, session=None,
                 events=None, finder=None):
        self._pkg = pkg
        #: 存档半边门面（`host.store_factory.HostStore` 或等价物；`_player` / `_record_state` 用）
        self._store = store or store_half(pkg)
        self.context = context                      # 平台发送面（AstrBot context / 测试记录器）
        self._events = events if events is not None else []   # 平台动作记录（广播 / 通知）
        self._finder = finder                       # 平台 handler 探测器（不给 → 引擎静态兜底）
        self._session = session or SessionAdapter(
            private_fallback="private", unknown_fallback="unknown",
            resolve_uid=lambda raw: _host_identity.resolve_uid(raw))

    # ============================================================
    # 包内半边取件（按名、懒取；不写包内模块字面量）
    # ============================================================
    def bind_package(self, pkg) -> "HostShell":
        """装配处绑定引擎 `Package`（幂等；绑定后各半边按名解析）。"""
        self._pkg = pkg
        if self._store is None:
            self._store = store_half(pkg)
        return self

    def _sub(self, name):
        """包内半边（`Package.optional_submodule`）；包未绑定 → 抛（拒绝静默空跑）。"""
        if self._pkg is None:
            raise RuntimeError("HostShell：未绑定引擎包（装配处应先 `bind_package(pkg)`）")
        mod = self._pkg.optional_submodule(name)
        if mod is None:
            raise RuntimeError("HostShell：包内半边 %r 不存在（包契约缺件）" % (name,))
        return mod

    def _rules(self):
        """内容规则半边（体力 / 设施 / 提示库 / 别名）。"""
        return self._sub("cmds_base_rules")

    # ---- 框架钩子：文案 / 别名 / 提示库（值取包内真源，本地零句子）----
    @property
    def register_hint(self):
        return self._rules().REGISTER_HINT

    @property
    def battle_none_hint(self):
        return self._rules().BATTLE_NONE_HINT

    @property
    def command_aliases(self):
        return self._rules().COMMAND_ALIASES

    def _tip_pool_map(self):
        return self._rules().TIP_POOL

    # ---- 框架钩子：认人 / 读档 / 战斗 / 状态 ----
    def _uid(self, event):
        return self._session.uid(event)

    def _player(self, group_id, qq_id):
        return self._store.get_player(group_id, qq_id)

    def _record_state(self, key, value):
        self._store.set_event_state(key, value)

    def _in_any_battle(self, group_id, qq_id):
        if self._store.get_battle(group_id, qq_id):
            return True
        fn = getattr(self, "_instance_battle_for", None)
        if fn is None:
            return False
        try:
            return bool(fn(group_id, qq_id))
        except Exception:                                        # noqa: BLE001
            return False

    # ---- 框架钩子：静态正则表 / 平台注册表探测 ----
    @classmethod
    def _build_static_handlers(cls):
        """静态兜底表 = 包内声明表（`content/data/commands.json` 的正则 → key）。"""
        mod = cls._static_source
        return mod() if mod is not None else []

    #: 装配处注入的「静态表供体」（`() -> [(compiled_re, key)]`）；不给 → 空表
    _static_source = None

    def _host_handler_finder(self):
        return self._finder

    # ---- 引擎钩子：包内游戏规则（全部转引包内真源，零重写）----
    def _at_smith(self, player):
        return self._rules().at_smith(player)

    def _at_shop(self, player, group_id="", qq_id=""):
        return self._rules().at_shop(player, group_id, qq_id)

    def _sa_shop_kind(self, player):
        return self._rules().sa_shop_kind(player)

    def _wild_trader_here(self, player, group_id="", qq_id=""):
        return self._rules().wild_trader_here(player, group_id, qq_id)

    def _at_healer(self, player):
        return self._rules().at_healer(player)

    def _facility_hint(self, player, kind):
        return self._rules().facility_hint(player, kind)

    def _stamina_max(self, player):
        return self._rules().stamina_max(player)

    def _stamina(self, player):
        return self._rules().stamina(player)

    def _spend_stamina(self, group_id, qq_id, cost, player, action="行动"):
        return self._rules().spend_stamina(group_id, qq_id, cost, player, action)

    def _add_stamina(self, group_id, qq_id, amount, player):
        return self._rules().add_stamina(group_id, qq_id, amount, player)

    def _stamina_bar(self, player, sep=" "):
        return self._rules().stamina_bar(player, sep)

    def _title_bonus(self, group_id, qq_id):
        """外部面板增益聚合（原 `game/commands/base.py::_title_bonus`；真源 = 包内 `stat_bonus`）。"""
        return self._sub("stat_bonus").stat_bonus(
            group_id, qq_id, self._player(group_id, qq_id) or {})

    def _rule_fire(self, trigger, group_id, qq_id, player, cur_map, evt=None):
        return self._sub("rule_engine").fire(
            group_id, qq_id, player, cur_map, trigger, evt or {},
            hooks={"title_bonus": lambda q: self._title_bonus(group_id, q)})

    # ---- 平台专有（原宿主各壳里的少量非转发方法）----
    @staticmethod
    def _stall_label(stall):
        """摊位标签（逐字 = 原 `game/commands/social.py::_stall_label`）。"""
        if not stall:
            return ""
        return stall.get("title") or stall.get("name") or "货摊"

    def _instance_gate_block(self, player, group_id, qq_id, target):
        """副本图门禁：徒步『前往/移动』不得直接进副本图（原 `game/commands/world.py` 同名方法）。

        判定本体在包内 `flow/instance_gate.py::walk_admission`；这里只做「取数 + 组装 ctx」，渲染走包内文案。
        """
        C = self._facade()
        if target.get("type") != C.MAP_TYPE_INSTANCE:
            return ""
        gate = self._flow("instance_gate")
        texts = self._sub("texts")
        if hasattr(gate, "set_text_table"):
            gate.set_text_table(texts.table())
        kid = target.get("id", "")
        mid = "inst_%s" % kid
        inst = (C.INSTANCES or {}).get(mid)
        quests = self._store.get_quests(group_id, qq_id)
        quest_open = False
        if quests.get("main_status") == "active":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == quests.get("main_quest")), None)
            if mq and mq["objective"].get("explore") == kid:
                quest_open = True
        if not quest_open:
            side = quests.get("side") or {}
            quest_open = any(
                sq.get("status") == "active"
                and next((q for q in C.SIDE_QUESTS if q["id"] == sid), {}).get(
                    "objective", {}).get("explore") == kid
                for sid, sq in side.items())
        key_item = (inst or {}).get("key_item")
        ctx = {
            "inst_name": (inst or {}).get("name") or (C.MAP_BY_ID.get(kid) or {}).get("name", "副本"),
            "tip": self._tip("instance"),
            "quest_open": quest_open,
            "key_held": bool(key_item) and gate.find_instance_key_item(
                self._store.get_inventory(group_id, qq_id) or [], key_item,
                items=(C.ITEMS or {})) is not None,
            "cleared": gate.instance_cleared(
                self._store.get_achievements(group_id, qq_id) or [], mid),
        }
        verdict = gate.walk_admission(ctx).check(ctx)
        return "" if verdict.ok else verdict.reason

    def _facade(self):
        """包内聚合门面（半边名 = `facade`；取 `.C`）。"""
        mod = self._sub("facade")
        return getattr(mod, "C", mod)

    def _flow(self, name):
        """包内 `flow/` 子包里的半边。"""
        return getattr(self._sub("flow"), name)

    # ============================================================
    # 平台动作（广播 / 通知）—— 有 context 才真发，否则落记录
    # ============================================================
    async def _broadcast(self, text, exclude_group=None):
        groups = self._store.get_player_groups()
        if not groups:
            return
        for gid in groups:
            if exclude_group and str(gid) == str(exclude_group):
                continue
            await self._deliver(str(gid), str(text))

    async def _notify_hermes(self, group_id, qq_id, content, msg_type):
        await self._deliver(str(group_id), str(content))

    async def _deliver(self, group_id, text):
        self._events.append({"action": "say", "group_id": group_id, "text": text})
        if self.context is None:
            return
        try:
            from ._platform import MessageChain
            await self.context.send_message(
                "onebot_v11_qq:GroupMessage:%s" % group_id, MessageChain().message(text))
        except Exception as exc:                                 # noqa: BLE001
            LOG.warning("[dragonfall] 广播到群 %s 失败: %s", group_id, exc)

    # ============================================================
    # 身份 / 停服（平台判定）
    # ============================================================
    def _gm_whitelist(self):
        wl = set()
        for x in (os.environ.get("GWEN_GM_QQ") or "").split(","):
            x = x.strip()
            if x:
                wl.add(x)
        try:
            raw = self._store.get_event_state("gm_whitelist")
            if raw:
                for x in json.loads(raw):
                    wl.add(str(x))
        except Exception:                                        # noqa: BLE001
            LOG.warning("[dragonfall] 读取 GM 白名单失败，回退环境变量", exc_info=True)
        return wl

    def _is_gm(self, qq_id):
        qq_id = str(qq_id)
        return qq_id.startswith("gm_") or qq_id in self._gm_whitelist()

    def _server_down(self):
        return self._store.get_event_state("server_maintenance") == "1"

    def _server_down_msg(self):
        return self._store.get_event_state("server_maintenance_msg") or ""

    # ============================================================
    # 平台例外 5 条（包内有声明、无处理器）
    # ============================================================
    async def _maint_gate(self, event):
        """停服 gate（逐字 = 原 `game/commands/base.py::_maint_gate`）。"""
        group_id, qq_id = self._uid(event)
        try:
            self._sub("timed_events").refresh_timed(group_id, qq_id)
        except Exception:                                        # noqa: BLE001
            LOG.warning("[timed_events] _maint_gate 刷新失败（不影响指令主流程）", exc_info=True)
        try:
            self._sub("wild_king").wild_king_tick()
        except Exception:                                        # noqa: BLE001
            pass
        try:
            self._sub("worlds").cleanup_stale_instances(24 * 3600)
        except Exception:                                        # noqa: BLE001
            pass
        if self._is_gm(qq_id):
            return None
        if self._server_down():
            text = (event.get_message_str() or "").strip()
            if re.match(r"^(?:\[At:[^\]]+\]\s*)?意见", text):
                return None
            event.stop_event()
            return None
        return None

    async def page_flip(self, event):
        """翻页快捷键（平台例外）：转发包内实现。"""
        gid, qid = self._uid(event)
        async for r in self._sub("player_cmds").page_flip(self, event, gid, qid):
            yield r

    async def shortcut_trigger(self, event):
        """裸数字快捷触发（平台例外）：转发包内实现。"""
        gid, qid = self._uid(event)
        player = self._player(gid, qid)
        async for r in self._sub("player_cmds").shortcut_trigger(self, event, gid, qid, player):
            yield r

    async def gm_play(self, event):
        """`gm_play <指令>` 转发（平台例外）：走引擎静态路由（`_run_shortcut`）。"""
        raw = self._strip_cmd(event, "gm_play").strip()
        if not raw:
            yield event.plain_result("🎮 用法：gm_play <指令>")
            return
        if raw.startswith("gm_"):
            yield event.plain_result("⛔ 不能转发 GM 指令至自身（防递归）～")
            return
        async for r in self._run_shortcut(event, raw):
            yield r

    async def gm_spy(self, event):
        """`gm_spy` 实况转发（平台例外，纯平台投递）。无投递面 → 明确抛，不静默。"""
        raise NotImplementedError(
            "gm_spy 是纯平台投递通道（私聊转发 playtest 实况），需平台 context；"
            "未接投递面时拒绝静默空跑")


# ============================================================
# 宿主侧存档半边取件（与 `host/store_factory.HostStore` 同形，但不依赖它）
# ============================================================
def store_half(pkg):
    """取包内存档半边（`persistence`），包未绑定 → None（装配处随后补）。"""
    if pkg is None:
        return None
    half = pkg.optional_submodule("persistence")
    if half is None:
        raise RuntimeError("HostShell：包内存档半边 `persistence` 取不到（包契约缺件）")
    return half
