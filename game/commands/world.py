# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - world（world）—— B9 线2 **薄壳**

由 main.py 拆分而来，作为 Mixin 被 Main 继承。**B9 线2（2026-09-13）薄壳化**后本文件只剩四件事：

    命令注册（@declared 装饰器）· 取玩家（self._uid / self._player）· 调包（一行转发）· 渲染

真源（实现本体）全在内容包：`content/world_cmds.py`（103 个方法逐字搬过去，见那边的头注）。
本文件保留的方法只有两类：

  · **命令入口**（36 个）：装饰器 + 「取玩家 + `async for _r in _WC.<名>(...)`」转发；
    名字/装饰器/注册序与改造前逐行相同（`@declared` 是宿主侧的**注册**动作：正则来自
    `game/data/command_specs.json`，框架注册表 + `_registry` 都从它派生）。
  · **一行委托桩**（67 个）：非命令私有方法，`(*args, **kwargs)` 原样转发给包内同名函数。
    执行 `self._<名>(...)` 的调用方（本文件、其它 Mixin、测试）**零改动**：名字集合与改造前
    逐名相同 → Main 的 MRO 解析结果不变。

★ 两个**故意留在宿主**的实现（都是宿主源码级门禁要求，不是遗漏，详见包内头注）
  · `quest_view`：`tests/test_texts_table.py:81 WIRED` 的「声明 ↔ 调用点」AST 对账按本文件做，
    每日任务域 `daily.*` 的 `T.text/T.static` 调用点必须在本文件里；
  · `_instance_gate_block`：`tests/test_v185_instance_admission.py:1129` 要求本文件源码出现
    `instance_gate.walk_admission`。

宿主替身注入：`db` / `C`（内容聚合层）—— 包内正文里 `db.xxx(...)` / `C.xxx` **一行未改**。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import db
from .. import content as C
from ..core import texts as T
from ..commands.base import CommandBase, no_prof_waiting, require_player

# ============ v181 P4-1 试点：每日任务域规则实现已收敛至 game/services/quests.py ============
# 原 v116 每日任务常量（DAILY_LIMIT/_DAILY_REPEAT_FACTORS/_DAILY_META_KEYS）与
# 结算单点（_settle_daily_quest/_daily_need/_daily_repeat_pct）本体已下沉 services；
# world/combat 命令层一律 import services（combat 不再 from .world 引私有函数）。
# 本文件保留模块级常量兼容导出（值逐字符同源，diff 校验相等）：
from ..services.quests import (  # noqa: F401  （P4-1 兼容导出：原 world.py 顶层常量名）
    DAILY_LIMIT, DAILY_REPEAT_FACTORS as _DAILY_REPEAT_FACTORS,
    DAILY_META_KEYS as _DAILY_META_KEYS, daily_need,
)


def _settle_daily_quest(inst, group_id, qq_id, daily, dq, lines=None):
    """（P4-1 兼容壳：转调 game/services/quests.settle_daily_quest——world/combat 命令层
    调用点已全部改走 services 直调；本壳仅供外部存档/工具兜底）"""
    from ..services.quests import settle_daily_quest as _settle_impl
    _settle_impl(group_id, qq_id, daily, dq, lines)


def _bump_daily_progress(group_id, qq_id, obj_key, lines=None):
    """（P4-1 兼容壳：转调 game/services/quests.bump_daily_progress——供存档/工具兜底）"""
    from ..services.quests import bump_daily_progress as _bump_impl
    return _bump_impl(group_id, qq_id, obj_key, lines)


def _daily_pool(player, dq):
    """（P4-1 兼容壳：转调 game/services/quests.daily_pool——『每日』抽取已改 services 直调）"""
    from ..services.quests import daily_pool as _pool_impl
    return _pool_impl(player, dq)


# 任务目标类型 → 进度展示行（v101.3：加新目标类型 = 加一行，quest_view 零改动）
def _kill_prog_count(obj, prog):
    """v105 M19 P2：击杀进度聚合读——兼容旧存档老 key（v95.7 之前进度记
    monster['name'] 而非 obj['kill']，如『精英森林狼』），面板不再显示 0/N 孤儿计数。
    目标 key 有值用目标 key；为 0 时汇总其余包含目标名的历史 key。"""
    v = prog.get(obj["kill"], 0)
    if v == 0:
        v = sum(c for k, c in prog.items() if k != obj["kill"] and obj["kill"] in k)
    return v


_OBJ_PROGRESS_LINES = {
    "kill":    lambda obj, prog: f"  进度：{_kill_prog_count(obj, prog)}/{obj['count']}",
    "collect": lambda obj, prog: f"  收集：{prog.get(obj['collect'], 0)}/{obj['count']}",
    "explore": lambda obj, prog: f"  前往：{C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}",
    "talk":    lambda obj, prog: f"  交谈：与 {C.NPCS.get(obj['talk'], {}).get('name', '？')} 对话",
}

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）
from content import world_cmds as _WC                        # noqa: E402

_WC.bind_host(db=db, content=C)                              # 宿主替身注入（正文 `db.`/`C.` 不改）
# v104 M23 修复：许愿井彩蛋概率（唯一定义点已随实现搬进包内 `content/world_cmds.py`；本行兼容再导出）
WISH_WELL_EGG_CHANCE = _WC.WISH_WELL_EGG_CHANCE


class WorldCmds(CommandBase):
    """命令层（B9 线2 薄壳）：注册 + 取玩家 + 调包 + 渲染；实现全在包内 `content/world_cmds.py`。"""


    _HURRY_ALIAS = {
        "npc": "npc",
        "怪物": "monster", "怪": "monster", "monster": "monster",
        "场景": "scene", "scene": "scene", "景物": "scene",
        "设施": "facility", "facility": "facility", "商店": "facility",
    }

    def _map_facilities(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_facilities`（B9 线2 薄壳）。"""
        return _WC._map_facilities(self, *args, **kwargs)

    def _map_scene(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_scene`（B9 线2 薄壳）。"""
        return _WC._map_scene(self, *args, **kwargs)

    def _visible_sas(self, *args, **kwargs):
        """委托包内 `content/world_cmds._visible_sas`（B9 线2 薄壳）。"""
        return _WC._visible_sas(self, *args, **kwargs)

    @staticmethod
    def _conn_target(*args, **kwargs):
        """委托包内 `content/world_cmds._conn_target`（B9 线2 薄壳）。"""
        return _WC._conn_target(*args, **kwargs)

    @staticmethod
    def _conn_subarea_name(*args, **kwargs):
        """委托包内 `content/world_cmds._conn_subarea_name`（B9 线2 薄壳）。"""
        return _WC._conn_subarea_name(*args, **kwargs)

    def _home_map_id(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_map_id`（B9 线2 薄壳）。"""
        return _WC._home_map_id(self, *args, **kwargs)

    @declared("deed_view")
    @require_player()
    async def deed_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.deed_view(self, event, group_id, qq_id, player):
            yield _r

    @declared("deed_buy")
    @require_player()
    async def deed_buy(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.deed_buy(self, event, group_id, qq_id, player):
            yield _r

    @declared("deed_sell")
    @require_player()
    async def deed_sell(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.deed_sell(self, event, group_id, qq_id, player):
            yield _r

    def _deed_upgrade(self, *args, **kwargs):
        """委托包内 `content/world_cmds._deed_upgrade`（B9 线2 薄壳）。"""
        return _WC._deed_upgrade(self, *args, **kwargs)

    @declared("go_home")
    @require_player()
    @no_prof_waiting()
    async def go_home(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.go_home(self, event, group_id, qq_id, player):
            yield _r

    @declared("go_out")
    @require_player()
    @no_prof_waiting()
    async def go_out(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.go_out(self, event, group_id, qq_id, player):
            yield _r

    @declared("visit_home")
    @require_player()
    @no_prof_waiting()
    async def visit_home(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.visit_home(self, event, group_id, qq_id, player):
            yield _r

    def _home_storage_key(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_storage_key`（B9 线2 薄壳）。"""
        return _WC._home_storage_key(self, *args, **kwargs)

    def _home_storage_load(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_storage_load`（B9 线2 薄壳）。"""
        return _WC._home_storage_load(self, *args, **kwargs)

    def _home_storage_save(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_storage_save`（B9 线2 薄壳）。"""
        return _WC._home_storage_save(self, *args, **kwargs)

    @declared("home_storage")
    @require_player()
    async def home_storage(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.home_storage(self, event, group_id, qq_id, player):
            yield _r

    @declared("home_storage_take")
    @require_player()
    async def home_storage_take(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.home_storage_take(self, event, group_id, qq_id, player):
            yield _r

    @declared("map_view")
    @require_player()
    async def map_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.map_view(self, event, group_id, qq_id, player):
            yield _r

    @declared("region_view")
    @require_player()
    async def region_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.region_view(self, event, group_id, qq_id, player):
            yield _r

    def _map_blocks(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_blocks`（B9 线2 薄壳）。"""
        return _WC._map_blocks(self, *args, **kwargs)

    def _map_nav_body(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_nav_body`（B9 线2 薄壳）。"""
        return _WC._map_nav_body(self, *args, **kwargs)

    @declared("location_view")
    @require_player()
    async def location_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.location_view(self, event, group_id, qq_id, player):
            yield _r

    def _hurry_type(self, *args, **kwargs):
        """委托包内 `content/world_cmds._hurry_type`（B9 线2 薄壳）。"""
        return _WC._hurry_type(self, *args, **kwargs)

    def _hurry_section(self, *args, **kwargs):
        """委托包内 `content/world_cmds._hurry_section`（B9 线2 薄壳）。"""
        return _WC._hurry_section(self, *args, **kwargs)

    def _hurry_panel(self, *args, **kwargs):
        """委托包内 `content/world_cmds._hurry_panel`（B9 线2 薄壳）。"""
        return _WC._hurry_panel(self, *args, **kwargs)

    @declared("hurry_view")
    @require_player()
    @no_prof_waiting()
    async def hurry_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.hurry_view(self, event, group_id, qq_id, player):
            yield _r

    def _move_blocked_msg(self, *args, **kwargs):
        """委托包内 `content/world_cmds._move_blocked_msg`（B9 线2 薄壳）。"""
        return _WC._move_blocked_msg(self, *args, **kwargs)

    @declared("back_cmd")
    @require_player()
    async def back_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.back_cmd(self, event, group_id, qq_id):
            yield _r

    @declared("ask_way")
    @require_player()
    async def ask_way(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.ask_way(self, event, group_id, qq_id, player):
            yield _r

    def _instance_gate_block(self, player: dict, group_id: str, qq_id: str, target: dict) -> str:
        """q1-B 副本图门禁：徒步『前往/移动』不可直接进入副本图（type=副本）。

        否则终局副本旁路：ash_temple/abyss_gate 等副本图经 MAP_CONNECTIONS 连通可徒步
        到达，玩家走进即自动完成 explore 主线目标（q9_3/q10_3 目标 ash_temple，
        q12_3 目标 abyss_gate），绕过『副本 <名字>』开本流程的钥匙/等级/人数校验。
        准入判定有三档（任一满足即放行，返回值空串）：
          - 玩家正持有 active 且 explore 目标为本图的**主线或支线任务**（任务内进入不受影响）；
          - 背包持有该副本 key_item（如 ash_temple→烬火令，abyss_gate→深渊钥匙）；
          - 已通关该副本（inst_clear_* 首通记录，与 instance.py 免钥匙同口径）。

        v141 审计 #9：钥匙三路匹配 + 通关豁免抽到 core/instance_gate.py
        （find_instance_key_item / instance_cleared_qq），此处只做任务放行层 + 调用公共函数。
        设计语义：**徒步进图不扣钥匙**（只校验持有，钥匙由『副本 <名字>』开本时才扣），
        任务/钥匙两路放行；开本才扣（见 instance.py _instance_start 同款公共函数调用）。

        v185：三档判定收敛成 core/instance_gate.walk_admission（`mode='any'`，任一命中即
        放行；全不通过时链级 reason = 原文案），本方法只负责取数与渲染 `v.reason`。

        命中时返回拦截文案；非副本图直接放行。『副本 <名字>』开本入口不经过本方法，不受影响。
        """
        if target.get("type") != C.MAP_TYPE_INSTANCE:
            return ""
        from ..core import instance_gate
        kid = target.get("id", "")
        mid = f"inst_{kid}"
        inst = C.INSTANCES.get(mid)
        # 1) 任务内进入：active 主线或支线 explore 目标 == 本副本图 → 放行
        quests = db.get_quests(group_id, qq_id)
        quest_open = False
        if quests.get("main_status") == "active":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == quests.get("main_quest")), None)
            if mq and mq["objective"].get("explore") == kid:
                quest_open = True
        if not quest_open:
            side = quests.get("side") or {}
            quest_open = any(sq.get("status") == "active"
                             and next((q for q in C.SIDE_QUESTS if q["id"] == sid), {}).get("objective", {}).get("explore") == kid
                             for sid, sq in side.items())
        # 2) 持有钥匙（与 instance.py 开本钥匙判定同源，抽公共 core/instance_gate.py）
        # 3) 已通关副本 → 免钥匙放行（与 instance.py 同口径）
        # ★ D2（v185 本轮登记的有意差异）：这一档原先查 `inst_clear_<地图id>`（kid），
        #   而真实通关写入的是 `inst_clear_<inst键>`（instance.py 通关结算 / instance_router 读档）
        #   ⇒ 线上**不可达**（实测：写真实键仍被拦、写地图 id 形式反而放行）。
        #   现改为查 inst 键（mid），与 instance.py 免钥匙真正同口径；不保留旧键兼容（一套口径）。
        key_item = (inst or {}).get("key_item")
        ctx = {
            "inst_name": (inst or {}).get("name") or C.MAP_BY_ID.get(kid, {}).get("name", "副本"),
            "tip": self._tip("instance"),
            "quest_open": quest_open,
            "key_held": bool(key_item) and instance_gate.find_instance_key_item(
                group_id, qq_id, key_item) is not None,
            "cleared": instance_gate.instance_cleared_qq(group_id, qq_id, mid),
        }
        v = instance_gate.walk_admission(ctx).check(ctx)
        return "" if v.ok else v.reason

    @declared("move")
    @require_player()
    @no_prof_waiting()
    async def move(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.move(self, event, group_id, qq_id):
            yield _r

    def _subarea_arrive(self, *args, **kwargs):
        """委托包内 `content/world_cmds._subarea_arrive`（B9 线2 薄壳）。"""
        return _WC._subarea_arrive(self, *args, **kwargs)

    def _instance_dungeon_move(self, *args, **kwargs):
        """委托包内 `content/world_cmds._instance_dungeon_move`（B9 线2 薄壳）。"""
        return _WC._instance_dungeon_move(self, *args, **kwargs)

    def _travel_ambush(self, *args, **kwargs):
        """委托包内 `content/world_cmds._travel_ambush`（B9 线2 薄壳）。"""
        return _WC._travel_ambush(self, *args, **kwargs)

    @declared("portal_view")
    @require_player()
    async def portal_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.portal_view(self, event, group_id, qq_id, player):
            yield _r

    @declared("portal_activate")
    @require_player()
    async def portal_activate(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.portal_activate(self, event, group_id, qq_id, player):
            yield _r

    @declared("portal_travel")
    @require_player()
    @no_prof_waiting()
    async def portal_travel(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.portal_travel(self, event, group_id, qq_id):
            yield _r

    def _update_explore_quests(self, *args, **kwargs):
        """委托包内 `content/world_cmds._update_explore_quests`（B9 线2 薄壳）。"""
        return _WC._update_explore_quests(self, *args, **kwargs)

    @declared("quest_view")
    @require_player()
    async def quest_view(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if self._is_redname(qq_id):
            yield event.plain_result("☠️ 你是红名！守卫不让你靠近任务板……(等红名消退再来)")
            return
        quests = db.get_quests(group_id, qq_id)
        lines = ["📜 【冒险日志】", "━━━━━━━━━━━━"]
        # 主线
        main_id = quests.get("main_quest")
        if main_id:
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
            # v104 M19：旧存档 main_quest 指向已下线 id（如 "q1"）→ 面板主线空白。
            # 与 _take_main_quest 同样的存档容错：重置回主线起点并落库。
            if not mq:
                quests["main_quest"] = "q1_1"
                quests["main_status"] = "pending"
                quests["main_progress"] = {}
                main_id = "q1_1"
                mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
                db.save_quests(group_id, qq_id, quests)
            if mq:
                _ginfo = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
                giver = _ginfo.get("name", "？")
                giver_map = _ginfo.get("map", "")
                giver_map_name = C.MAP_BY_ID.get(giver_map, {}).get("name", "？")
                lines.append(f"【主线】『{mq['name']}』")
                lines.append(f"  {mq['desc']}")
                st = quests.get("main_status", "pending")
                if st == "pending":
                    lines.append(f"  ⏳ 未接取：去找 {giver}(在{giver_map_name})对话接取")
                elif st == "ready":
                    # v95.25 #47b：主线交付=找 NPC 自动触发（与『交付任务』指令并存），不写死交付方式
                    lines.append(f"  ✅ 目标达成！回去找 {giver} 交付")
                else:
                    prog = quests.get("main_progress", {})
                    obj = mq["objective"]
                    # v101.3：目标类型展示查表化（kill/collect/explore/talk，顺序与原 if-elif 一致）
                    # v169.9：主线 collect 面板实时查背包（对齐支线口径）——此前只读 main_progress
                    # 存档，玩家采到材料但没对话过 NPC 时面板仍显示 0/N，误以为物品对不上（#143）
                    if obj.get("collect"):
                        have = db.count_item(group_id, qq_id, obj["collect"])
                        need = obj.get("count", 1)
                        if have >= need:
                            lines.append(f"  ✅ 材料已齐：{obj['collect']} {have}/{need}（回去找 {giver} 交付）")
                        else:
                            lines.append(f"  收集：{have}/{need}")
                    else:
                        for _k, _fn in _OBJ_PROGRESS_LINES.items():
                            if obj.get(_k):
                                lines.append(_fn(obj, prog))
                                break
        else:
            lines.append("【主线】已全部完成！🎊")
        # 支线（v101.25i3：已完成任务不进面板，鱼鱼：交了还显示）
        side = quests.get("side", {})
        side_items = [(sid, sq) for sid, sq in side.items() if sq.get("status", "active") != "done"]
        if side_items:
            lines.append("")
            lines.append("【支线】")
            raw = self._strip_cmd(event, "任务")
            page = self._parse_page(raw)
            page_items, pages, page = self._page_items(side_items, page, per_page=5)
            for i, (sid, sq) in enumerate(page_items, (page - 1) * 5 + 1):
                sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
                if not sqd:
                    continue
                giver = (C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}).get("name", "？")
                st = sq.get("status", "active")
                obj = sqd["objective"]
                # v95.12：已交付支线显示已完成（不占可交付位）
                if st == "done":
                    lines.append(f"{i:>2}. 『{sqd['name']}』[✅ 已完成]")
                    continue
                # v127.7 排版：任务名单独一行（名字+状态），描述缩进下一行，目标进度行统一再缩进
                # v116 §3.4：进行中支线可放弃（主线不可弃），放弃提示统一放面板底部（v123e 去行尾冗余）
                # 收集型：实时按背包材料判断（v104 补测：复合目标同时显示击杀进度防误导）
                if obj.get("collect"):
                    have = db.count_item(group_id, qq_id, obj["collect"])
                    need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 的复合目标不再 KeyError
                    prog = sq.get("progress", {})
                    kill_txt = ""
                    if obj.get("kill"):
                        kv = _kill_prog_count(obj, prog)  # v105 M19 P2：兼容旧档老 key 聚合
                        kill_txt = f"｜击杀：{kv}/{obj.get('count', 0)}"
                    if have >= need:
                        lines.append(f"{i:>2}. 『{sqd['name']}』[✅ 可交{kill_txt}]")
                        lines.append(f"    {sqd['desc']}")
                        lines.append(f"    材料已齐！回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    else:
                        lines.append(f"{i:>2}. 『{sqd['name']}』[⏳{kill_txt}]")
                        lines.append(f"    {sqd['desc']}")
                        lines.append(f"    收集：{obj['collect']} {have}/{need}{kill_txt}")
                    # v125.1 P2：复合目标（collect+use/find/explore，如 s53/s56/s64/s105）
                    # 补显其余目标行，与 find/use 分支的 _obj_text_lines 展示口径一致
                    # （收集/击杀行已在上方展示，过滤避免重复）
                    for _t in self._obj_text_lines(obj, st):
                        if _t.startswith(("收集", "击败")):
                            continue
                        lines.append(f"    {_t}")
                    continue
                # v104 M20 P2：find 型（告示委托等）面板提示机制——在 XX 探索有概率遇到
                # （此前走通用兜底只显示 desc+[⏳]，玩家不知如何推进）
                if obj.get("find"):
                    lines.append(f"{i:>2}. 『{sqd['name']}』[{'✅ 可交' if st == 'ready' else '⏳'}]")
                    lines.append(f"    {sqd['desc']}")
                    # v124.2 复合目标逐行显示（s18 kill+find 两行都展示）
                    for _t in self._obj_text_lines(obj, st):
                        lines.append(f"    {_t}")
                    if st == "ready":
                        lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    continue
                # v124 use 型（使用指定物品达成）——同 find 处理
                if obj.get("use"):
                    lines.append(f"{i:>2}. 『{sqd['name']}』[{'✅ 可交' if st == 'ready' else '⏳'}]")
                    lines.append(f"    {sqd['desc']}")
                    for _t in self._obj_text_lines(obj, st):
                        lines.append(f"    {_t}")
                    if st == "ready":
                        lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
                    continue
                mark = "✅ 可交" if st == "ready" else "⏳"
                lines.append(f"{i:>2}. 『{sqd['name']}』[{mark}]")
                lines.append(f"    {sqd['desc']}")
                if st == "ready":
                    lines.append(f"    回去找 {giver} {self._deliver_hint(sqd['giver'])}")
            # v127.7 翻页提示补全：上一页/下一页 + 总页数（此前只有下一页）
            if pages > 1:
                _nav = []
                if page > 1:
                    _nav.append(f"『任务 {page-1}』上一页")
                if page < pages:
                    _nav.append(f"『任务 {page+1}』下一页")
                lines.append(f"💡 {' | '.join(_nav)}(共 {pages} 页)")
            self._record_list_state(qq_id, "任务", page, pages)
        else:
            lines.append("")
            lines.append("【支线】暂无——找镇上的 NPC 聊聊可能有意外收获")
        # 每日
        # v116 §3.4：daily 含 _completed/_repeat 元数据（active 任务清空后仍在）——
        # 只剩元数据 = 今日全部完成，按"已完成"分支展示；_completed 超额时给出计数。
        # v127.7：玩家从未领取（daily 为空）→ 提示『每日』领取，不再误报"已完成"。
        daily = quests.get("daily", {})
        active_keys = [k for k in daily if k not in _DAILY_META_KEYS]
        if active_keys:
            lines.append("")
            lines.append(T.static("daily.section"))
            _daily_n = 0  # v116 每日任务序号（仅计实际任务，跨元数据）
            for dkey, dq in daily.items():
                if dkey in _DAILY_META_KEYS:  # 跨天/计数元数据，跳过
                    continue
                _daily_n += 1
                # v125.1 P2：序号用 _daily_n（仅计实际任务）——原用 enumerate 的 i 会把
                # _date/_completed/_repeat 元数据占位算进去（面板显示 4./5.，『放弃』按 1..N 对不上）
                need = daily_need(dq)
                # v127.7 排版：每日任务名单独一行，描述缩进下一行
                if need is None:
                    # v125.1 P2：无达标数定义时只显示实际进度，不再兜底假 99
                    lines.append(T.text("daily.item", n=_daily_n, name=dq["name"]))
                    lines.append(T.text("daily.item_plain", desc=dq["desc"],
                                        prog=dq.get("progress", 0)))
                else:
                    lines.append(T.text("daily.item", n=_daily_n, name=dq["name"]))
                    lines.append(T.text("daily.item_progress", desc=dq["desc"],
                                        prog=dq.get("progress", 0), need=need))
        else:
            lines.append("")
            if not daily:
                # v127.7 修复：从未领取（新号/跨天清空）→ 引导领取，不显示"已完成"
                lines.append(T.static("daily.never"))
            else:
                _done = int(daily.get("_completed", 0) or 0)
                if _done >= DAILY_LIMIT:
                    lines.append(T.text("daily.done_full", done=_done, limit=DAILY_LIMIT))
                else:
                    lines.append(T.text("daily.done_part", done=_done))
        # v101.30d #O1：师门考验追踪——对话树进行中时面板显示（playtest 小红：考验无面板条目）
        _MASTER_IDS = ("npc_herb_master", "npc_mine_master", "npc_fish_master", "npc_cook_master",
                       "npc_alchemy_master", "npc_craft_master", "npc_enhance_master", "npc_rune_master")
        ts = db.get_talk_state(group_id, qq_id)
        if ts and ts.get("npc") in _MASTER_IDS:
            _tnpc = C.NPCS.get(ts["npc"]) or {}
            lines.append("")
            lines.append("【师门考验】")
            lines.append(f"  ⏳ 正在接受【{_tnpc.get('name', '导师')}】的拜师考验，回复『继续』接着进行")
        lines.append("")
        # v127.1 每面板只抽 1 条随机提示（v123e 放弃/接取引导并入随机池）
        lines.append(self._tip("quest"))
        yield event.plain_result("\n".join(lines))

    @declared("quest_accept")
    @require_player()
    async def quest_accept(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.quest_accept(self, event, group_id, qq_id):
            yield _r

    def _sq_unlocked(self, *args, **kwargs):
        """委托包内 `content/world_cmds._sq_unlocked`（B9 线2 薄壳）。"""
        return _WC._sq_unlocked(self, *args, **kwargs)

    def _sq_stats_met(self, *args, **kwargs):
        """委托包内 `content/world_cmds._sq_stats_met`（B9 线2 薄壳）。"""
        return _WC._sq_stats_met(self, *args, **kwargs)

    def _available_quest_list(self, *args, **kwargs):
        """委托包内 `content/world_cmds._available_quest_list`（B9 线2 薄壳）。"""
        return _WC._available_quest_list(self, *args, **kwargs)

    @declared("quest_abandon")
    async def quest_abandon(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.quest_abandon(self, event, group_id, qq_id):
            yield _r

    @declared("daily")
    @require_player()
    async def daily(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.daily(self, event, group_id, qq_id, player):
            yield _r

    def _daily_pool(self, *args, **kwargs):
        """委托包内 `content/world_cmds._daily_pool`（B9 线2 薄壳）。"""
        return _WC._daily_pool(self, *args, **kwargs)

    def _bump_daily_progress(self, *args, **kwargs):
        """委托包内 `content/world_cmds._bump_daily_progress`（B9 线2 薄壳）。"""
        return _WC._bump_daily_progress(self, *args, **kwargs)

    def _home_view(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_view`（B9 线2 薄壳）。"""
        return _WC._home_view(self, *args, **kwargs)

    def _current_npcs(self, *args, **kwargs):
        """委托包内 `content/world_cmds._current_npcs`（B9 线2 薄壳）。"""
        return _WC._current_npcs(self, *args, **kwargs)

    def _present_wild_hints(self, *args, **kwargs):
        """委托包内 `content/world_cmds._present_wild_hints`（B9 线2 薄壳）。"""
        return _WC._present_wild_hints(self, *args, **kwargs)

    def _start_talk_list(self, *args, **kwargs):
        """委托包内 `content/world_cmds._start_talk_list`（B9 线2 薄壳）。"""
        return _WC._start_talk_list(self, *args, **kwargs)

    def _find_npc_in_map(self, *args, **kwargs):
        """委托包内 `content/world_cmds._find_npc_in_map`（B9 线2 薄壳）。"""
        return _WC._find_npc_in_map(self, *args, **kwargs)

    def _town_npc_absent_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._town_npc_absent_hint`（B9 线2 薄壳）。"""
        return _WC._town_npc_absent_hint(self, *args, **kwargs)

    def _player_map_name(self, *args, **kwargs):
        """委托包内 `content/world_cmds._player_map_name`（B9 线2 薄壳）。"""
        return _WC._player_map_name(self, *args, **kwargs)

    def _subarea_name(self, *args, **kwargs):
        """委托包内 `content/world_cmds._subarea_name`（B9 线2 薄壳）。"""
        return _WC._subarea_name(self, *args, **kwargs)

    def _find_wild_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds._find_wild_npc`（B9 线2 薄壳）。"""
        return _WC._find_wild_npc(self, *args, **kwargs)

    def _wild_unseen_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._wild_unseen_hint`（B9 线2 薄壳）。"""
        return _WC._wild_unseen_hint(self, *args, **kwargs)

    def _npc_direction_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._npc_direction_hint`（B9 线2 薄壳）。"""
        return _WC._npc_direction_hint(self, *args, **kwargs)

    def _npc_dialogue(self, *args, **kwargs):
        """委托包内 `content/world_cmds._npc_dialogue`（B9 线2 薄壳）。"""
        return _WC._npc_dialogue(self, *args, **kwargs)

    def _take_main_quest(self, *args, **kwargs):
        """委托包内 `content/world_cmds._take_main_quest`（B9 线2 薄壳）。"""
        return _WC._take_main_quest(self, *args, **kwargs)

    def _obj_text(self, *args, **kwargs):
        """委托包内 `content/world_cmds._obj_text`（B9 线2 薄壳）。"""
        return _WC._obj_text(self, *args, **kwargs)

    def _obj_text_lines(self, *args, **kwargs):
        """委托包内 `content/world_cmds._obj_text_lines`（B9 线2 薄壳）。"""
        return _WC._obj_text_lines(self, *args, **kwargs)

    def _quest_reputation(self, *args, **kwargs):
        """委托包内 `content/world_cmds._quest_reputation`（B9 线2 薄壳）。"""
        return _WC._quest_reputation(self, *args, **kwargs)

    def _wild_cond_label(self, *args, **kwargs):
        """委托包内 `content/world_cmds._wild_cond_label`（B9 线2 薄壳）。"""
        return _WC._wild_cond_label(self, *args, **kwargs)

    @declared("time_cmd")
    @require_player()
    async def time_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.time_cmd(self, event, group_id, qq_id, player):
            yield _r

    @declared("wild_notes")
    @require_player()
    async def wild_notes(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.wild_notes(self, event, group_id, qq_id, player):
            yield _r

    @declared("npc_quick_dialog", priority=100)
    async def npc_quick_dialog(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.npc_quick_dialog(self, event, group_id, qq_id):
            yield _r

    def find_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds.find_npc`（B9 线2 薄壳）。"""
        return _WC.find_npc(self, *args, **kwargs)

    def _grant_wild_unlock_flags(self, *args, **kwargs):
        """委托包内 `content/world_cmds._grant_wild_unlock_flags`（B9 线2 薄壳）。"""
        return _WC._grant_wild_unlock_flags(self, *args, **kwargs)

    def _teach_by_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds._teach_by_npc`（B9 线2 薄壳）。"""
        return _WC._teach_by_npc(self, *args, **kwargs)

    @declared("interact_prop")
    @require_player()
    @no_prof_waiting()
    async def interact_prop(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        async for _r in _WC.interact_prop(self, event, group_id, qq_id):
            yield _r

    def _talk_active(self, *args, **kwargs):
        """委托包内 `content/world_cmds._talk_active`（B9 线2 薄壳）。"""
        return _WC._talk_active(self, *args, **kwargs)

    def _talk_ctx(self, *args, **kwargs):
        """委托包内 `content/world_cmds._talk_ctx`（B9 线2 薄壳）。"""
        return _WC._talk_ctx(self, *args, **kwargs)

    def _side_menu_expand(self, *args, **kwargs):
        """委托包内 `content/world_cmds._side_menu_expand`（B9 线2 薄壳）。"""
        return _WC._side_menu_expand(self, *args, **kwargs)

    def _render_talk_node(self, *args, **kwargs):
        """委托包内 `content/world_cmds._render_talk_node`（B9 线2 薄壳）。"""
        return _WC._render_talk_node(self, *args, **kwargs)

    def _branch_wait_sid(self, *args, **kwargs):
        """委托包内 `content/world_cmds._branch_wait_sid`（B9 线2 薄壳）。"""
        return _WC._branch_wait_sid(self, *args, **kwargs)

    def _weapon_pick_active(self, *args, **kwargs):
        """委托包内 `content/world_cmds._weapon_pick_active`（B9 线2 薄壳）。"""
        return _WC._weapon_pick_active(self, *args, **kwargs)

    def _weapon_pick_choose(self, *args, **kwargs):
        """委托包内 `content/world_cmds._weapon_pick_choose`（B9 线2 薄壳）。"""
        return _WC._weapon_pick_choose(self, *args, **kwargs)

    def _remove_one_by_name(self, *args, **kwargs):
        """委托包内 `content/world_cmds._remove_one_by_name`（B9 线2 薄壳）。"""
        return _WC._remove_one_by_name(self, *args, **kwargs)

    def _update_use_quests(self, *args, **kwargs):
        """委托包内 `content/world_cmds._update_use_quests`（B9 线2 薄壳）。"""
        return _WC._update_use_quests(self, *args, **kwargs)

    def _talk_quest_progress(self, *args, **kwargs):
        """委托包内 `content/world_cmds._talk_quest_progress`（B9 线2 薄壳）。"""
        return _WC._talk_quest_progress(self, *args, **kwargs)

    def _do_join_class(self, *args, **kwargs):
        """委托包内 `content/world_cmds._do_join_class`（B9 线2 薄壳）。"""
        return _WC._do_join_class(self, *args, **kwargs)

    def _do_evolve_via_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds._do_evolve_via_npc`（B9 线2 薄壳）。"""
        return _WC._do_evolve_via_npc(self, *args, **kwargs)

    def _apply_talk_action_async(self, *args, **kwargs):
        """委托包内 `content/world_cmds._apply_talk_action_async`（B9 线2 薄壳）。"""
        return _WC._apply_talk_action_async(self, *args, **kwargs)

    def _apply_talk_action(self, *args, **kwargs):
        """委托包内 `content/world_cmds._apply_talk_action`（B9 线2 薄壳）。"""
        return _WC._apply_talk_action(self, *args, **kwargs)

    @declared("talk_choice")
    @require_player()
    async def talk_choice(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.talk_choice(self, event, group_id, qq_id, player):
            yield _r

    def _deliver_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._deliver_hint`（B9 线2 薄壳）。"""
        return _WC._deliver_hint(self, *args, **kwargs)

    def _side_available_list(self, *args, **kwargs):
        """委托包内 `content/world_cmds._side_available_list`（B9 线2 薄壳）。"""
        return _WC._side_available_list(self, *args, **kwargs)

    def _offer_side_quest(self, *args, **kwargs):
        """委托包内 `content/world_cmds._offer_side_quest`（B9 线2 薄壳）。"""
        return _WC._offer_side_quest(self, *args, **kwargs)

    def _offer_side_quests(self, *args, **kwargs):
        """委托包内 `content/world_cmds._offer_side_quests`（B9 线2 薄壳）。"""
        return _WC._offer_side_quests(self, *args, **kwargs)

    @declared("turn_in")
    @require_player()
    async def turn_in(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.turn_in(self, event, group_id, qq_id, player):
            yield _r

    def _grant_quest_rewards(self, *args, **kwargs):
        """委托包内 `content/world_cmds._grant_quest_rewards`（B9 线2 薄壳）。"""
        return _WC._grant_quest_rewards(self, *args, **kwargs)

    def _complete_side_quest(self, *args, **kwargs):
        """委托包内 `content/world_cmds._complete_side_quest`（B9 线2 薄壳）。"""
        return _WC._complete_side_quest(self, *args, **kwargs)

    @declared("rest_camp")
    @require_player()
    async def rest_camp(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.rest_camp(self, event, group_id, qq_id, player):
            yield _r

    @declared("rest")
    @require_player()
    async def rest(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.rest(self, event, group_id, qq_id, player):
            yield _r

    @declared("reputation")
    @require_player()
    async def reputation(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.reputation(self, event, group_id, qq_id, player):
            yield _r

    @declared("rep_shop")
    @require_player()
    async def rep_shop(self, event: AstrMessageEvent):
        async for _r in _WC.rep_shop(self, event):
            yield _r

    def _camp_ctx(self, *args, **kwargs):
        """委托包内 `content/world_cmds._camp_ctx`（B9 线2 薄壳）。"""
        return _WC._camp_ctx(self, *args, **kwargs)

    def _camp_save(self, *args, **kwargs):
        """委托包内 `content/world_cmds._camp_save`（B9 线2 薄壳）。"""
        return _WC._camp_save(self, *args, **kwargs)

    @declared("camp_join")
    @require_player()
    async def camp_join(self, event: AstrMessageEvent):
        async for _r in _WC.camp_join(self, event):
            yield _r

    @declared("camp_task")
    @require_player()
    async def camp_task(self, event: AstrMessageEvent):
        async for _r in _WC.camp_task(self, event):
            yield _r

    @declared("camp_shop")
    @require_player()
    async def camp_shop(self, event: AstrMessageEvent):
        async for _r in _WC.camp_shop(self, event):
            yield _r

    @declared("camp_rank")
    @require_player()
    async def camp_rank(self, event: AstrMessageEvent):
        async for _r in _WC.camp_rank(self, event):
            yield _r

    @declared("chronicle")
    @require_player()
    async def chronicle(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        async for _r in _WC.chronicle(self, event, group_id, qq_id, player):
            yield _r
