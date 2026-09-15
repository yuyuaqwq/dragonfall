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
少量方法（`_stall_label` / 平台例外 5 条）。
★ P5E「壳去逻辑」批（2026-09-15）：原 `_HURRY_ALIAS`（赶路别名表）与 `_instance_gate_block`
（走包内 `flow/` 准入链的取数 + ctx 组装）已搬回包内（`content/world_cmds.py`），
`gm_play` / `gm_spy` 的实现也已搬回包内（`content/cmds_gm.py`），本文件对这三项只剩
**转发 / 平台配置常量**。
其余方法都是「转引包内真源」，与旧壳逐名同义（旧壳本身就是 `_RULES.xxx` 一行转发）。
"""
from __future__ import annotations

import functools
import importlib
import json
import logging
import os
import pkgutil
import re

from saintess_engine.command import CommandBase as _EngineCommandBase
from saintess_engine.session import SessionAdapter

from . import _identity as _host_identity

LOG = logging.getLogger("astrbot")

#: 包内模块缓存（`{包根: [模块…]}`）——助手按名解析用；前缀从包清单 entry 派生，**不写包名**
_HELPER_MODULES: dict = {}


def _noop(*_a, **_k):
    return None


def _binds_shell(fn) -> bool:
    """包内函数是否以「宿主壳」为第一参数（`def fn(self, …)` / `def fn(shell, …)`）。"""
    import inspect
    try:
        params = list(inspect.signature(fn).parameters)
    except (TypeError, ValueError):
        return False
    return bool(params) and params[0] in ("self", "shell")


# ============================================================
# 平台配置常量（`gm_窥探` 投递面）—— **流程实现已在包内** `content/cmds_gm.py::gm_spy`
# ------------------------------------------------------------
# P5E「壳去逻辑」批（2026-09-15）：窥探的实录解析 / 拆角色卡 / 多卡投递流程搬回包内；
# 壳侧只留 `gm_spy` 一条转发 + 本组**平台配置常量**，经 `_spy_ops()` 交给包内
# （与 `_identity_ops()` 同款「平台能力口」口径）。
# ============================================================
#: 窥探投递目标（运营号；环境变量可覆盖，换号不改代码）
GM_OWNER_QQ = (os.environ.get("GWEN_GM_QQ") or "1454832774").split(",")[0].strip()
#: 鱼鱼所在游戏群（`--群` 变体投递目标）
OWNER_GROUP = os.environ.get("GWEN_GM_GROUP") or "1095961596"
#: AstrBot 平台 id（**不是**适配器 type；用 aiocqhttp 前缀发送会返回 False 静默不发）
PLATFORM_PREFIX = "onebot_v11_qq"
#: playtest 交互实录目录（`playtest_spy_round{N}.md`，导出脚本轮末生成）
SPY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


class _ShellEnv(object):
    """包内守卫钩子要的最小 `Env` 面（`uid` / `group_id` / `text` / `state["shell"]`）。"""

    def __init__(self, *, uid="", group_id="", text="", shell=None):
        self.uid = str(uid)
        self.group_id = str(group_id)
        self.text = str(text)
        self.player = None
        self.state = {"shell": shell}


class HostShell(_EngineCommandBase):
    """终态宿主壳：`env.state["shell"]`（引擎 `Host.build_env` 之前由装配处注入 `inject`）。"""

    logger_name = "astrbot"

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

    # ★ P5E「壳去逻辑」批（2026-09-15）：原 `_instance_gate_block`（走包内 `flow/` 准入链的
    #   取数 + ctx 组装）与只服务它的 `_facade()` 已从本文件删除 —— 实现搬回包内
    #   `content/world_cmds.py::_instance_gate_block`；包内实现在 `self.<名>` 调用点仍由本类
    #   `__getattr__` 按名解析（壳侧不再留第二份）。

    # ============================================================
    # 包内助手按名解析（终态壳的「私有方法面」）
    # ------------------------------------------------------------
    # 旧壳（`game/commands/**`）里除命令入口外还有 ~258 个**非命令助手**
    # （`_bag_view` / `_skill_panel` / `_instance_battle_for` …）：包内实现体以
    # `self.<名>(…)` 调用它们。终态壳不把这 258 个名字抄一遍（那就是第二份漂移源），
    # 改为**按名向包内解析**——模块前缀从包清单 `entry` 派生（`content/apply.py` → `content`），
    # 所以宿主里**零包名**。
    #
    # 解析顺序（与 tests/_engine_harness.py 的同名能力**同序**）：
    #   ① 包内模块级函数（`content/xxx.py::_bag_view`）
    #   ② 包内模块级类的同名方法（`content/economy_cmds.py::EconomyImpl._bag_view`）
    # 都取不到 → `AttributeError`（不静默造空实现）。
    # ============================================================
    def _package_modules(self) -> list:
        """包内模块清单（懒扫 + 缓存；扫描根 = 包清单 entry 的同级包）。"""
        pkg = self.__dict__.get("_pkg")
        if pkg is None:
            return []
        key = str(getattr(pkg, "root", "") or id(pkg))
        cached = _HELPER_MODULES.get(key)
        if cached is not None:
            return cached
        mods = []
        entry = str(getattr(pkg, "entry", "") or "")
        if entry.endswith(".py") and "/" in entry:
            prefix = entry[:-3].replace("/", ".").rsplit(".", 1)[0]
            try:
                root = importlib.import_module(prefix)
                for info in pkgutil.walk_packages(root.__path__, prefix + "."):
                    try:
                        mods.append(importlib.import_module(info.name))
                    except Exception:                            # noqa: BLE001
                        continue
            except Exception:                                    # noqa: BLE001
                LOG.warning("[dragonfall] 包内模块扫描失败（助手按名解析不可用）", exc_info=True)
        _HELPER_MODULES[key] = mods
        return mods

    def _package_helper(self, name):
        """按名找包内助手 —— **两遍解析**：先自绑壳候选，再自由函数；找不到 → None。

        ★ P5E-DELETE / D1（2026-09-15）：为什么必须两遍（P6-PREP 实测定性，反证见
        `out/probes/probe3d_bump_repro.py`）——
        包内有**两个同名** `_bump_daily_progress`：
          · `content/world_cmds.py::_bump_daily_progress(self, group_id, qq_id, obj_key, lines=None)`
            （`_binds_shell=True`，壳应以 `self` 绑定后调用 = 模块扫序 **152**）
          · `content/profession_quests.py::_bump_daily_progress(inst, group_id, qq_id, obj_key, lines=None)`
            （首参名 `inst` ⇒ `_binds_shell=False` = 模块扫序 **122**）
        旧的「第 1 遍按模块扫序取模块级函数」会取中**扫序在前**的那个 ⇒ 命中非自绑的
        `profession_quests` 版；调用方按 `(group_id, qq_id, obj_key, lines)` 传四参 ⇒
        实参整体左移一位（`inst=group_id, group_id=qq_id, …`）⇒ 包内入口查不到 daily
        ⇒ **静默 return**（`lines==[]`、`_completed` 不 +1、金币不涨、**无异常**）。
        影响面：全包 143 条同名碰撞里只有这一条实取候选与自绑候选**形参个数相同**，
        其余 142 条形参个数不同（调用即 `TypeError`，吵闹但不静默）——见
        `out/probes/probe3e_helper_collisions.json`。

        修法 = 与 `tests/_engine_harness.py::Main.__getattr__` 同序：
        **pass 1 只收 `_binds_shell(fn)` 的候选**（模块级函数在前、模块级类的同名方法在后），
        pass 2 再回退自由函数（保持原有「模块扫序先落者胜」口径不变）。
        """
        mods = self._package_modules()
        # ---- pass 1：自绑壳候选（`def fn(self, …)` / `def fn(shell, …)`）----
        for mod in mods:
            fn = getattr(mod, name, None)
            if callable(fn) and getattr(fn, "__module__", "") == mod.__name__ and _binds_shell(fn):
                return fn
        for mod in mods:
            for value in vars(mod).values():
                if not isinstance(value, type):
                    continue
                if getattr(value, "__module__", "") != mod.__name__:
                    continue
                attr = getattr(value, name, None)
                if callable(attr) and _binds_shell(attr):
                    return attr
        # ---- pass 2：自由函数（不绑壳；候选按模块扫序，取先落者）----
        for mod in mods:
            fn = getattr(mod, name, None)
            if callable(fn) and getattr(fn, "__module__", "") == mod.__name__:
                return fn
        for mod in mods:
            for value in vars(mod).values():
                if not isinstance(value, type):
                    continue
                if getattr(value, "__module__", "") != mod.__name__:
                    continue
                attr = getattr(value, name, None)
                if callable(attr):
                    return attr
        return None

    def __getattr__(self, name):
        """缺失属性 → 包内助手（非命令）。双下划线名直接拒绝，避免干扰 copy/pickle 探测。"""
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        helper = self._package_helper(name)
        if helper is None:
            raise AttributeError(
                "%s has no attribute %r（包内无同名落点）" % (type(self).__name__, name))
        return functools.partial(helper, self) if _binds_shell(helper) else helper

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

    def _identity_ops(self):
        """平台身份映射面（openid ⇄ QQ）——包内 GM 身份表的宿主能力口（`_cap(shell, …)` 探测）。"""
        return _host_identity

    def _spy_ops(self):
        """窥探投递平台面（实录目录 / 合并转发类型 / 投递目标 / 宿主日志）。

        包内 `content/cmds_gm.py::gm_spy` 经此取平台件（与 `_identity_ops()` 同款能力口）；
        壳侧不留流程实现（P5E「壳去逻辑」批）。
        """
        from . import _platform as _pf
        return {"dir": SPY_DIR, "prefix": PLATFORM_PREFIX,
                "owner_qq": GM_OWNER_QQ, "owner_group": OWNER_GROUP,
                "Node": _pf.Node, "Plain": _pf.Plain,
                "Nodes": _pf.Nodes, "MessageChain": _pf.MessageChain,
                "log": LOG}

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

    def _guard_hook(self, name, *, uid="", group_id="", text=""):
        """跑包内一条守卫钩子（判定与文案都在包）；包内没有 → None（不拦）。

        平台例外命令（`gm_play` / `gm_spy`）**不进**引擎的 `Host.invoke`，所以它们的权限判定
        由本方法显式补一次——否则这两条会绕过包内 `hook:gm`（形同后门）。
        """
        hooks = self._pkg.guard_hooks() if self._pkg is not None else {}
        fn = hooks.get(name) if isinstance(hooks, dict) else None
        if not callable(fn):
            return None
        env = _ShellEnv(uid=uid, group_id=group_id, text=text, shell=self)
        return fn(env, None) or None

    async def gm_play(self, event):
        """`gm_play <指令>`（平台例外）：转发包内实现。"""
        group_id, qq_id = self._uid(event)
        async for r in self._sub("cmds_gm").gm_play(self, event, group_id, qq_id):
            yield r

    async def gm_spy(self, event):
        """`gm_窥探`（平台例外）：转发包内实现。"""
        group_id, qq_id = self._uid(event)
        async for r in self._sub("cmds_gm").gm_spy(self, event, group_id, qq_id):
            yield r


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
