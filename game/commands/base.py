# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - base（base）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
import random
import re
import time

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.star.filter.regex import RegexFilter
from astrbot.core.star.star_handler import EventType, star_handlers_registry

from .. import content as C
from .. import db
from .. import engine as E
from .. import battle as BT


def no_prof_waiting():
    """等待型副业（v55：垂钓/采集/挖掘）进行中时拦截该命令。

    装饰 async generator 命令方法（命令类方法都是 yield event.plain_result 的 async generator）。
    用法（@filter.regex 的下方）：
        @filter.regex(r"...")
        @no_prof_waiting()
        async def move(self, event): ...
    以后任何"会换场景/进战斗"的命令（副本、探索、世界 Boss 等）要跟副业互斥，
    加这一行装饰器即可，检查逻辑只维护这一处。
    """
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(self, event: AstrMessageEvent, *args, **kwargs):
            group_id, qq_id = self._uid(event)
            st = self._prof_wait_state(group_id, qq_id)
            if st and st["finish"] > int(time.time()):
                left = st["finish"] - int(time.time())
                tname = self._PROF_WAIT_BASE.get(st["type"], (0, 0, "副业"))[2]
                yield event.plain_result(
                    f"⏳ 你还在{tname}呢，再有 {left} 秒完成，先别走开！(完成会自动入包)"
                )
                return
            async for item in fn(self, event, *args, **kwargs):
                yield item
        return wrapper
    return deco


class CommandBase:

    def _strip_cmd(self, event: AstrMessageEvent, cmd: str) -> str:
        """从消息中剥离 At 前缀和指令名，返回剩余参数"""
        msg = event.get_message_str().strip()
        msg = re.sub(r"^\[At:[^\]]*\]\s*", "", msg)
        msg = re.sub(r"^\[At:全体成员\]\s*", "", msg)
        msg = re.sub(r"^\[引用消息[^\]]*\]\s*", "", msg)
        if msg.startswith(cmd):
            msg = msg[len(cmd):].strip()
        else:
            # 尝试别名（v83.1 精简：只保留仍在用的别名）
            for alias in ("我的角色", "位置", "主线", "help"):
                if alias != cmd and msg.startswith(alias):
                    msg = msg[len(alias):].strip()
                    break
        return msg

    @staticmethod
    def _page_items(items: list, page: int, per_page: int = 5) -> tuple:
        """通用翻页：返回 (当前页条目, 总页数, 当前页码)"""
        total = len(items)
        pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        start = (page - 1) * per_page
        return items[start:start + per_page], pages, page

    def _parse_page(self, raw: str) -> int:
        """解析参数中的页码；纯数字 → 页码，否则 1"""
        raw = (raw or "").strip()
        if raw.isdigit():
            return int(raw)
        return 1

    def _at_smith(self, player: dict) -> bool:
        """当前是否在铁匠铺/锻造坊/工坊/军械/强化类子区域（锻造/代工/强化/附魔场所）。
        v87.6 子区域化：不再地图级一刀切（广场/旅店不能锻造）。"""
        cur_map = player.get("cur_map", "")
        if cur_map not in C.ENHANCE_SMITH_MAPS:
            return False
        sa_id = player.get("cur_subarea") or ""
        if not sa_id:
            return False
        cm = C.MAP_BY_ID.get(cur_map, {})
        for sa in (cm.get("subareas") or []):
            if sa["id"] == sa_id:
                name = sa.get("name", "")
                funcs = sa.get("funcs") or []
                if "craft" in funcs:
                    return True
                return any(k in name for k in ("铁匠", "锻造", "军械", "工坊", "强化"))
        return False

    def _at_shop(self, player: dict, group_id: str = "", qq_id: str = "") -> bool:
        """v87.17 当前子区域是否有商店（shop: true 或 funcs 含 shop）。
        设施子区域绑定铁律：商店命令只在有商店的子区域放行。
        v95.4：野外行商（trade funcs）在场时也可交易。"""
        cur_map = player.get("cur_map", "")
        sa_id = player.get("cur_subarea") or ""
        if sa_id:
            cm = C.MAP_BY_ID.get(cur_map, {})
            for sa in (cm.get("subareas") or []):
                if sa["id"] == sa_id:
                    if sa.get("shop") or "shop" in (sa.get("funcs") or []):
                        return True
                    break  # v95.4：当前子区域不是商店 → 继续查野外行商
        # v95.4：不在城镇设施 → 看是否有野外行商在场
        return self._wild_trader_here(player, group_id, qq_id)

    def _wild_trader_here(self, player: dict, group_id: str = "", qq_id: str = "") -> bool:
        """v95.4：当前地图是否有可交易的野外行商（funcs 含 trade 且出现条件满足）"""
        if not (group_id and qq_id):
            return False
        cur = player.get("cur_map", "")
        for nid, wnpc in C.ALL_WILD.items():
            if "trade" not in (wnpc.get("funcs") or []):
                continue
            if C.npc_map_id(nid, wnpc) != cur:
                continue
            if C.wild_npc_findable(nid, wnpc, player, group_id, qq_id):
                return True
        return False

    def _at_healer(self, player: dict) -> bool:
        """v87.17 当前子区域是否有旅店（healer: true 或 funcs 含 heal）。
        设施子区域绑定铁律：住宿只在旅店子区域放行。"""
        cur_map = player.get("cur_map", "")
        sa_id = player.get("cur_subarea") or ""
        if not sa_id:
            return False
        cm = C.MAP_BY_ID.get(cur_map, {})
        for sa in (cm.get("subareas") or []):
            if sa["id"] == sa_id:
                if sa.get("healer"):
                    return True
                return "heal" in (sa.get("funcs") or [])
        return False

    def _facility_hint(self, player: dict, kind: str) -> str:
        """v87.17 提示最近设施所在子区域（kind: shop/healer）。
        返回如『去 老铁铁匠铺 或 草药铺 看看』，无则空串。"""
        cur_map = player.get("cur_map", "")
        cm = C.MAP_BY_ID.get(cur_map, {})
        names = []
        for sa in (cm.get("subareas") or []):
            if kind == "shop":
                if sa.get("shop") or "shop" in (sa.get("funcs") or []):
                    names.append(sa.get("name", ""))
            elif kind == "healer":
                if sa.get("healer") or "heal" in (sa.get("funcs") or []):
                    names.append(sa.get("name", ""))
        if not names:
            return ""
        uniq = []
        for n in names:
            if n and n not in uniq:
                uniq.append(n)
        return "去 " + " 或 ".join(uniq[:3]) + " 看看"

    # 静态命令正则表（Mixin 切分后各文件 @filter.regex 的汇总）。
    # 用于测试环境/注册表缺失时快捷指令的校验与转发；真实 AstrBot 注册表优先。
    _STATIC_HANDLERS = None

    @classmethod
    def _static_handlers(cls):
        """收集本类(含 Mixin)上所有 @filter.regex 正则 → [(正则, 方法名)]"""
        if cls._STATIC_HANDLERS is not None:
            return cls._STATIC_HANDLERS
        from ._registry import COMMAND_REGEX
        out = [(re.compile(pat), name) for name, pat in COMMAND_REGEX.items()]
        cls._STATIC_HANDLERS = out
        return out

    def _find_handler(self, text: str):
        """按指令文本查找匹配的 handler 元数据（快捷指令转发用）。

        优先查 AstrBot 全局注册表；注册表缺失（测试/静态分析）时回退到
        本类 @filter.regex 装饰器收集的静态表。跳过快捷指令自身防递归。
        """
        text = text.strip()
        try:
            for md in star_handlers_registry._handlers:
                if md.event_type != EventType.AdapterMessageEvent:
                    continue
                if md.handler_module_path != self.__class__.__module__:
                    continue
                name = getattr(md.handler, "__name__", "")
                if name.startswith("shortcut"):
                    continue
                for f in md.event_filters:
                    if isinstance(f, RegexFilter):
                        try:
                            if f.regex.search(text):
                                return md, f
                        except re.error:
                            continue
        except Exception:
            pass
        # 回退：静态正则表
        for regex, name in self._static_handlers():
            try:
                if regex.search(text):
                    return name, regex
            except re.error:
                continue
        return None

    async def _run_shortcut(self, event: AstrMessageEvent, text: str):
        """执行快捷指令：把文本当作真实指令转发给匹配的 handler。

        临时替换 event 消息文本为绑定指令（让目标 handler 正确解析参数），
        调用完毕后恢复原消息。直接调用目标 handler 方法（绑定 self），复用其回复。
        """
        hit = self._find_handler(text)
        if not hit:
            yield event.plain_result(f"❌ 快捷指令『{text}』无法识别，请先确认指令存在～")
            return
        if isinstance(hit[0], str):
            # 静态表回退：hit = (方法名, regex)，直接 getattr 取 bound method
            handler_fn = getattr(self, hit[0], None)
            if handler_fn is None:
                yield event.plain_result(f"❌ 快捷指令『{text}』无法识别(处理器缺失)～")
                return
            is_prebound = True
        else:
            # 注册表命中：hit = (md, filter)
            md, _ = hit
            handler_fn = md.handler
            # AstrBot 运行时 handler 是 functools.partial(raw, star_cls)（handler(event)）；
            # 或 bound method（handler(event)）；测试/未绑定场景是 unbound function（handler(self, event)）
            is_prebound = isinstance(handler_fn, functools.partial) or getattr(handler_fn, "__self__", None) is not None
        orig_msg = event.message_str
        event.message_str = text
        try:
            if is_prebound:
                gen = handler_fn(event)
            else:
                gen = handler_fn(self, event)
            if inspect.isasyncgen(gen):
                async for r in gen:
                    yield r
            else:
                r = await gen
                if r:
                    yield r
        except Exception as e:
            import logging
            logging.getLogger("astrbot").warning(f"[dragonfall] 快捷转发失败 {text}: {e}")
            yield event.plain_result(f"❌ 快捷指令执行出错：{e}")
        finally:
            event.message_str = orig_msg

    def _fmt_stat_src(self, src: dict) -> str:
        """格式化单条属性来源：『来源名: 攻击＋8 生命＋40 暴击＋5%』"""
        parts = []
        for k, v in src["stats"].items():
            name = E.STAT_NAMES.get(k, k)
            if k in ("crit", "dodge"):
                sign = "+" if v >= 0 else ""
                pct = "+" if src.get("pct") and k not in ("crit", "dodge") else ""
                parts.append(f"{name}{pct}{sign}{int(v*100)}%")
            else:
                sign = "+" if v >= 0 else ""
                if src.get("pct"):
                    parts.append(f"{name}+{int(v*100)}%")
                else:
                    parts.append(f"{name}{sign}{v}")
        return f"{src['name']}: {' '.join(parts)}" if parts else ""

    def _attr_sources(self, player: dict, title_bonus: dict = None) -> list[str]:
        """玩家属性来源明细(v16 属性来源拆解)"""
        try:
            st, sources = E.player_stats_detail(
                player["class_name"], player["level"], player["equipment"],
                player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0),
                title_bonus, player.get("race"))
        except Exception:
            return []
        lines = []
        for src in sources:
            s = self._fmt_stat_src(src)
            if s:
                lines.append(s)
        return lines

    async def _reply(self, event: AstrMessageEvent, text: str):
        """统一回复"""
        yield event.plain_result(text)

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
                await self.context.send_message(
                    f"aiocqhttp:GroupMessage:{gid}", chain
                )
            except Exception as e:
                import logging
                logging.getLogger("astrbot").warning(f"[dragonfall] 广播到群 {gid} 失败: {e}")

    def _uid(self, event: AstrMessageEvent) -> tuple:
        """返回 (group_id, qq_id)"""
        group_id = event.get_group_id() or "private"
        sender_id = event.get_sender_id() or "unknown"
        return group_id, sender_id

    def _player(self, group_id, qq_id):
        return db.get_player(group_id, qq_id)

    # ---------- v94 体力系统 ----------
    def _stamina_max(self, player: dict) -> int:
        """体力上限：100 + 等级×2"""
        return 100 + (player.get("level") or 1) * 2

    def _stamina(self, player: dict) -> int:
        return int(player.get("stamina") or 0)

    def _spend_stamina(self, group_id, qq_id, cost: int, player: dict, action: str = "行动") -> tuple:
        """扣体力；不足返回 (False, 提示)。够则落库并返回 (True, 剩余)。"""
        cur = self._stamina(player)
        if cur < cost:
            return False, (
                f"😮‍💨 体力不足！{action}需要 {cost} 点体力，你只有 {cur} 点。\n"
                f"🍖 吃点食物(『烹饪』/『使用 <食物>』)或去旅店『住宿』恢复体力～"
            )
        db.update_player(group_id, qq_id, stamina=cur - cost)
        return True, cur - cost

    def _add_stamina(self, group_id, qq_id, amount: int, player: dict) -> int:
        """加体力（封顶上限），返回实际增加量。"""
        cur = self._stamina(player)
        mx = self._stamina_max(player)
        new = min(mx, cur + amount)
        if new != cur:
            db.update_player(group_id, qq_id, stamina=new, stamina_ts=int(time.time()))
            player["stamina"] = new  # v95.16 #80：同步 player dict，st_msg 显示恢复后值而非旧值
        return new - cur

    def _stamina_bar(self, player: dict) -> str:
        """体力显示条：⚡ 82/102"""
        return f"⚡ 体力 {self._stamina(player)}/{self._stamina_max(player)}"


    def _title_bonus(self, group_id, qq_id) -> dict:
        """副业大师称号的属性加成汇总(Lv.10 称号 bonus 叠加 + 阶段九成就称号 bonus)"""
        bonus = {}
        try:
            earned = self._earned_titles(group_id, qq_id, self._player(group_id, qq_id) or {})
            for i, t in enumerate(C.TITLES):
                if earned[i] and t.get("bonus"):
                    for k, v in t["bonus"].items():
                        bonus[k] = bonus.get(k, 0) + v
            # 阶段九：成就称号 bonus（14 章 3.3，达成即生效）
            try:
                unlocked_achs = {r[0] for r in db.get_achievements("", qq_id)}
            except Exception:
                unlocked_achs = set()
            for a in C.ACHIEVEMENTS:
                if a.get("bonus") and a["id"] in unlocked_achs:
                    for k, v in a["bonus"].items():
                        if k != "atk" or v != 0:  # 占位字段跳过
                            bonus[k] = bonus.get(k, 0) + v
        except Exception:
            pass
        return bonus
