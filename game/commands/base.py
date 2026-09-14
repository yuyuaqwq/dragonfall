# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - base（base）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。

【骨架归属（2026-09-11，M2；★ B18-L7 收尾，2026-09-14）】命令层的**通用那一半**（分页 /
页码解析 / 文本剥离 / 提示抽取 / handler 查找与转发 / 守卫装饰器 / 指令正则集合）
来自框架 `saintess_engine.command`。

本文件此后**只剩框架钩子 + 一行转发** —— 游戏内容整块进包 `content/cmds_base_rules.py`：
  * 注册装饰器 / 守卫骨架：`require_player` / `require_battle`（框架再导出）、
    `_GameCmdFilter` + `_maint_gate`（停服 gate，宿主平台装配）；
  * 框架契约的「使用方钩子表」（权威出处 = 框架 `command/base.py` 模块头那张表）：
    `_uid` / `_player` / `_in_any_battle` / `_tip_pool_map` / `_record_state` /
    `_host_handler_finder` / `_build_static_handlers` / `_build_command_regex_strings`；
  * 已是一行转发的公共钩子：`_rule_fire` / `_title_bonus`；平台发送能力口 `_broadcast`；
  * **游戏内容**（设施判定 `_at_smith`/`_at_shop`/`_sa_shop_kind`/`_wild_trader_here`/`_at_healer`/
    `_facility_hint`、属性行 `_fmt_stat_src`、体力族 `_stamina*`、等待型副业守卫 `no_prof_waiting`、
    三条文案 `REGISTER_HINT`/`battle_none_hint`/`command_aliases`）
    → 实现、判定与文案全在包内，本文件同名**一行转发**。

对外名字**零变化**（`CommandBase` / `require_player` / `no_prof_waiting` /
`require_battle` / `REGISTER_HINT` 照旧从这里 import）——
其余 20 个命令模块的 import 与调用点一行都不用改。行为逐字节不变
（证据 = `overnight/W-B18-L7.md`：202 场景三分支快照，改前/改后同 sha256）。
"""
import functools
import json
import os
import re
import time

from saintess_engine.command import CommandBase as _KitCommandBase
from saintess_engine.command import HandlerHit, PatternSet
# 守卫装饰器由框架提供，这里**原样再导出**（既有 import 点不变）
from saintess_engine.command import require_battle, require_player  # noqa: F401
from saintess_engine.session import SessionAdapter

from ._platform import AstrMessageEvent, filter  # noqa: F401（filter 供 @filter.custom_filter 用；正则装饰器已全部迁声明表）
from ._platform import MessageChain
from ._platform import CustomFilter
from ._platform import RegexFilter
from ._platform import EventType, star_handlers_registry

from ._declared import declared

from .. import content as C
from .. import db
from ..content_rules.panel import STAT_NAMES
from ..log_setup import LOG

# ---------- ★ B18-L7：命令层「游戏内容」实现进包 ----------
# 真源 = `games/orlandia/content/cmds_base_rules.py`（判定 / 文案 / 格式全在那里）；
# 本文件只保留同名**一行转发**，故 20+ 处 `from .base import no_prof_waiting` 等调用点一行未改。
# 取件：宿主唯一包加载口 `game/__init__.py` 已把框架根插进 sys.path（幂等；失败大声抛）。
from .. import bootstrap as _BST  # noqa: E402
_BST.package_apply()
from content import cmds_base_rules as _RULES  # noqa: E402

#: 等待型副业守卫装饰器（★ B18-L7 起实现进包；此处**同名再导出**，签名/语义/文案不变）
no_prof_waiting = _RULES.no_prof_waiting



# ---------- v96 停服维护全局拦截 ----------
# 停服时非 GM 玩家发任何游戏指令都会被高优先级 gate 拦下（日常聊天不受影响）。
class _GameCmdFilter(CustomFilter):
    """只命中「游戏指令」（_registry.COMMAND_REGEX 任一正则），避免误拦群聊日常。

    匹配机制（懒编译 + 缓存 + 零宽跳过）在框架 `saintess_engine.command.PatternSet`。
    """

    _PATTERNS = None

    @classmethod
    def _patterns(cls):
        if cls._PATTERNS is None:
            from ._registry import COMMAND_REGEX
            cls._PATTERNS = PatternSet(lambda: list(COMMAND_REGEX.values()))
        return cls._PATTERNS

    def filter(self, event, cfg) -> bool:
        text = event.get_message_str().strip()
        return self._patterns().matches(text)


# 等待型副业守卫装饰器 `no_prof_waiting()`：★ B18-L7 起实现进包 —— 见上方 import 段的同名再导出；
# 判定（`self._prof_wait_state`）与文案（`content/catalog_life.PROF_WAIT_BASE`）全在
# `content/cmds_base_rules.py`，本文件不再留任何判定与句子。


# v95.26 统一注册引导：所有"没角色"拦截只走这一处文案，改格式只动这里
# v105 P3(M01)：与注册错误提示格式统一（『注册 <名字> <性别> [种族]』），防两处格式串不一致
# ★ B18-L7：句子唯一真源 = 包内 `content/guards.py::NO_PLAYER_HINT`（本名转引包侧；外部 import 面不变）
REGISTER_HINT = _RULES.REGISTER_HINT


def _resolve_uid(raw: str) -> str:
    """平台标识 → 玩家账号 id（延迟 import 防 `_platform` 装配期循环）。"""
    from . import _identity
    return _identity.resolve_uid(raw)


# 会话适配点（框架 `saintess_engine.session.SessionAdapter`）：
# 「群号怎么来 + 发送者标识怎么翻译」收在这一个对象里 —— 换宿主只动这一处。
_session = SessionAdapter(private_fallback="private", unknown_fallback="unknown",
                          resolve_uid=_resolve_uid)


class CommandBase(_KitCommandBase):
    """本游戏命令层基类：通用部分继承框架，这里只填「内容与宿主适配」。"""

    # ---------- 框架钩子：文案（★ B18-L7：句子取包侧，钩子名/语义不变）----------
    register_hint = REGISTER_HINT
    battle_none_hint = _RULES.BATTLE_NONE_HINT
    logger_name = "astrbot"

    # ---------- 框架钩子：剥参数时的指令别名（v83.1 精简：只保留仍在用的）----------
    command_aliases = _RULES.COMMAND_ALIASES

    # ---------- 框架钩子：内容来源 ----------
    def _tip_pool_map(self) -> dict:
        """面板底部引导提示的分类库（v127 数据驱动；★ B18-L7 取包侧同一对象）。"""
        return _RULES.TIP_POOL

    def _record_state(self, key: str, value: str) -> None:
        db.set_event_state(key, value)

    # ---------- 框架钩子：静态正则表 / 指令正则集合 ----------
    @classmethod
    def _build_static_handlers(cls) -> list:
        """静态命令正则表（Mixin 切分后各文件 @filter.regex 的汇总）。

        用于测试环境/注册表缺失时快捷指令的校验与转发；真实 AstrBot 注册表优先。
        """
        from ._registry import COMMAND_REGEX
        return [(re.compile(pat), name) for name, pat in COMMAND_REGEX.items()]

    @classmethod
    def _build_command_regex_strings(cls):
        from ._registry import COMMAND_REGEX
        return list(COMMAND_REGEX.values())

    # ---------- 框架钩子：宿主注册表探测（AstrBot 适配）----------
    def _host_handler_finder(self):
        """返回一个 `finder(text) -> HandlerHit | None`（框架 `_find_handler` 用）。

        优先查 AstrBot 全局注册表；跳过私有 handler（`_maint_gate` 等）与
        `shortcut*`，并用 `handler_module_path` 限定本模块，防跨插件误命中。
        """
        def _find(text: str):
            for md in star_handlers_registry._handlers:
                if md.event_type != EventType.AdapterMessageEvent:
                    continue
                if md.handler_module_path != self.__class__.__module__:
                    continue
                raw = md.handler
                if isinstance(raw, functools.partial):
                    # AstrBot 加载插件时 handler 被包装成 partial(raw, star_cls)（无 __name__），
                    # 直接 getattr 拿名字恒为空串 → v96.1 的私有跳过在真实进程失效
                    raw = raw.func
                name = getattr(raw, "__name__", "")
                if name.startswith("shortcut") or name.startswith("_"):
                    # v96：跳过私有 handler（_maint_gate 等），避免空正则污染快捷转发
                    continue
                for f in md.event_filters:
                    if isinstance(f, RegexFilter):
                        try:
                            if f.regex.search(text):
                                prebound = (isinstance(md.handler, functools.partial)
                                            or getattr(md.handler, "__self__", None) is not None)
                                return HandlerHit(name, md.handler, prebound, raw=md)
                        except re.error:
                            continue
            return None
        return _find

    # ---------- v96 GM 身份与停服状态 ----------
    @staticmethod
    def _gm_whitelist() -> set:
        """GM 白名单：环境变量 GWEN_GM_QQ ∪ 数据库 gm_whitelist(JSON 数组)。"""
        wl = set()
        for x in os.environ.get("GWEN_GM_QQ", "").split(","):
            x = x.strip()
            if x:
                wl.add(x)
        try:
            raw = db.get_event_state("gm_whitelist")
            if raw:
                for x in json.loads(raw):
                    wl.add(str(x))
        except Exception:
            # q11：白名单读取失败回退环境变量，留痕便于排查
            LOG.warning(
                "[dragonfall] 读取 GM 白名单失败，回退环境变量", exc_info=True
            )
        return wl

    def _is_gm(self, qq_id) -> bool:
        """GM 判定：gm_ 前缀测试身份 / 数据库+环境变量白名单。"""
        # q11 注释：gm_ 前缀的授予范围与安全边界——
        # 授予范围：凡以 "gm_" 开头的任意字符串均视为 GM（playthrough 文件回环
        # /多号联测等测试身份，是 QQ 不存在的虚拟号），仅服务于本插件内部测试链路，
        # 不下发真实玩家。
        # 安全边界：真实 QQ 号是纯数字，日常群聊不会误带 gm_ 前缀；但 gm_ 前缀属
        # 无条件放行后门，若事件来源可伪造 sender_id（外部恶意事件/代理伪装）需警惕。
        # 面向真实玩家的 GM 权限应只信任 _gm_whitelist()（db gm_whitelist ∪
        # GWEN_GM_QQ 环境变量）中的实名白名单，勿依赖 gm_ 前缀判别线上真实身份。
        qq_id = str(qq_id)
        if qq_id.startswith("gm_"):
            return True
        return qq_id in self._gm_whitelist()

    @staticmethod
    def _server_down() -> bool:
        """服务器是否处于停服维护状态。"""
        try:
            return db.get_event_state("server_maintenance") == "1"
        except Exception:
            return False

    @staticmethod
    def _server_down_msg() -> str:
        try:
            return db.get_event_state("server_maintenance_msg") or ""
        except Exception:
            return ""

    @declared("_maint_gate", priority=100)
    @filter.custom_filter(_GameCmdFilter, priority=100)
    async def _maint_gate(self, event: AstrMessageEvent):
        """v96 停服维护拦截：停服时非 GM 的游戏指令一律拦下并停止传播。
        开服或 GM 直接放行（不产出任何结果，事件继续传给真正的指令 handler）。
        v127.5：任意游戏指令入口 → 惰性刷新通用倒计时引擎（懒计时，见 timed_events）。
        """
        group_id, qq_id = self._uid(event)
        # v127.5：任意玩家游戏指令先刷一次倒计时（过期清理+on_expire，无害幂等；
        # GM 也刷（GM 无事件则空扫）；日常闲聊不进本 gate 不触发，零开销）
        try:
            from ..core import timed_events as _te
            _te.refresh_timed(group_id, qq_id)
        except Exception:
            LOG.warning(
                "[timed_events] _maint_gate 刷新失败（不影响指令主流程）", exc_info=True)
        # v140 波2：任意指令惰性刷新野王全局状态（跨时段/存活超时懒清理 + 时段首刷，
        # 与倒计时引擎同款懒计时思路；幂等，不阻塞指令主流程）
        try:
            from ..core.wild_king import wild_king_tick
            wild_king_tick()
        except Exception:
            pass
        # v141 大陆回收（P0-3，2026-08-30 审计）：任意指令惰性清理超龄大陆实例
        # （24h 无活动；内存 dict 轻扫 + DB event_state 孤儿键），幂等不阻塞主流程
        try:
            from ..core.worlds import cleanup_stale_instances as _csi
            _csi(24 * 3600)
        except Exception:
            pass
        if self._is_gm(qq_id):
            return
        if self._server_down():
            # v134.7：停服时『意见』指令放行（玩家反馈渠道不能断，维护期也要能提意见）
            _text = event.get_message_str().strip()
            if re.match(r"^(?:\[At:[^\]]+\]\s*)?意见", _text):
                return
            # v134.7：停服其他指令直接无视（不回复维护提示，静默 stop 不产出结果）
            event.stop_event()
            return
        # 开服：放行
        return

    # ---------- v87.17 设施子区域判定（★ B18-L7：判定进包，本处一行转发）----------
    def _at_smith(self, player: dict) -> bool:
        """当前是否在铁匠铺/锻造坊/工坊/军械/强化类子区域（实现 = 包内 `at_smith`）。"""
        return _RULES.at_smith(player)

    def _at_shop(self, player: dict, group_id: str = "", qq_id: str = "") -> bool:
        """当前子区域是否有商店（实现 = 包内 `at_shop`；含野外行商在场）。"""
        return _RULES.at_shop(player, group_id, qq_id)

    def _sa_shop_kind(self, player: dict) -> str | None:
        """当前子区域商店类型 smith/herb/tavern/cook/general/misc（实现 = 包内 `sa_shop_kind`）。"""
        return _RULES.sa_shop_kind(player)

    def _wild_trader_here(self, player: dict, group_id: str = "", qq_id: str = "") -> str | None:
        """当前地图可交易的野外行商 NPC id，无则 None（实现 = 包内 `wild_trader_here`）。"""
        return _RULES.wild_trader_here(player, group_id, qq_id)

    def _at_healer(self, player: dict) -> bool:
        """当前子区域是否有旅店（实现 = 包内 `at_healer`）。"""
        return _RULES.at_healer(player)

    def _facility_hint(self, player: dict, kind: str) -> str:
        """提示最近设施所在子区域（实现 = 包内 `facility_hint`）。"""
        return _RULES.facility_hint(player, kind)

    def _fmt_stat_src(self, src: dict) -> str:
        """格式化单条属性来源：『来源名: 攻击＋8 生命＋40 暴击＋5%』（实现 = 包内 `fmt_stat_src`）"""
        return _RULES.fmt_stat_src(src)

    async def _broadcast(self, text: str, exclude_group: str | None = None):
        """向所有有玩家注册过的群广播公告（不含私聊）。

        只广播到 player_groups 表记录过的群号；exclude_group 可跳过当前群（避免重复）。
        """
        groups = db.get_player_groups()
        if not groups:
            return
        chain = MessageChain().message(text)
        for gid in groups:
            if exclude_group and str(gid) == str(exclude_group):
                continue
            try:
                # ⚠️ 平台前缀必须是配置里的平台 id "onebot_v11_qq"（不是 type "aiocqhttp"）——
                # v101.28q 实测：aiocqhttp 前缀 send_message 返回 False 静默不发（广播从未生效）
                await self.context.send_message(
                    f"onebot_v11_qq:GroupMessage:{gid}", chain
                )
            except Exception as e:
                LOG.warning(f"[dragonfall] 广播到群 {gid} 失败: {e}")

    # ---------- 框架钩子：上下文 ----------
    def _uid(self, event: AstrMessageEvent) -> tuple:
        """返回 (group_id, qq_id)

        v2026-09-07 QQ官方迁移：sender 若是 openid（官方 bot 只给 openid），
        经 identity_map 映射回玩家原本的 QQ 号——DB/命令全不用改。
        适配点实现（兜底值 + 标识翻译）见模块级 `_session`（框架 SessionAdapter）。
        """
        return _session.uid(event)

    def _player(self, group_id, qq_id):
        return db.get_player(group_id, qq_id)

    def _in_any_battle(self, group_id, qq_id) -> bool:
        """v95.26 是否存在战斗（普通战斗或副本战斗）——require_battle 守卫用。
        _instance_battle_for 定义在 InstanceCmds，用 getattr 兼容 CommandBase 单独使用。"""
        if db.get_battle(group_id, qq_id):
            return True
        f = getattr(self, "_instance_battle_for", None)
        if f is not None:
            try:
                return bool(f(group_id, qq_id))
            except Exception:
                return False
        return False

    # ---------- v94 体力系统（★ B18-L7：公式/落库/格式进包，本处一行转发）----------
    def _stamina_max(self, player: dict) -> int:
        """体力上限：100 + 等级×2（实现 = 包内 `stamina_max`）"""
        return _RULES.stamina_max(player)

    def _stamina(self, player: dict) -> int:
        """（实现 = 包内 `stamina`）"""
        return _RULES.stamina(player)

    def _spend_stamina(self, group_id, qq_id, cost: int, player: dict, action: str = "行动") -> tuple:
        """扣体力；不足返回 (False, 提示)。够则落库并返回 (True, 剩余)（实现 = 包内 `spend_stamina`；
        v185 措辞同源 `content.flow.instance_gate.stamina_short_msg`）。"""
        return _RULES.spend_stamina(group_id, qq_id, cost, player, action)

    def _add_stamina(self, group_id, qq_id, amount: int, player: dict) -> int:
        """加体力（封顶上限），返回实际增加量（实现 = 包内 `add_stamina`）。"""
        return _RULES.add_stamina(group_id, qq_id, amount, player)

    def _stamina_bar(self, player: dict, sep: str = " ") -> str:
        """体力显示条：⚡ 82/102（sep 可传『：』统一标签冒号格式；实现 = 包内 `stamina_bar`）"""
        return _RULES.stamina_bar(player, sep)

    # ---------- v97.5 行为彩蛋规则 ----------
    def _rule_fire(self, trigger: str, group_id, qq_id, player: dict, cur_map: dict, evt: dict = None) -> str:
        """行为规则触发器挂点：命中返回彩蛋文本，未命中返回 ""。"""
        from ..core.rule_engine import fire as _fire
        return _fire(group_id, qq_id, player, cur_map, trigger, evt or {},
                     hooks={"title_bonus": lambda q: self._title_bonus(group_id, q)})

    def _title_bonus(self, group_id, qq_id) -> dict:
        """当前玩家外部面板增幅聚合（称号/成就/收藏；未来纯数值来源）。

        N5b4-4 泛化：实现已下沉 core/stat_bonus.py（原名 title_bonus.py，v174 并入
        收藏册后语义=外部增幅聚合器）。方法名保留（命令层 20+ 处调用 + rule_engine
        hooks 键 title_bonus 契约；旧引擎冻结区 N10 删旧时一并收敛）。
        v105 M01#11：命令层与 store 惰性升级共用同一实现。
        """
        from ..core.stat_bonus import stat_bonus
        return stat_bonus(group_id, qq_id, self._player(group_id, qq_id) or {})
