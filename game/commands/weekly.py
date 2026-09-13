# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - weekly（v169.2 周常悬赏 Lv50+）

周常悬赏：每周刷新的击杀型悬赏板（Lv50+ 解锁，Lv70+ 进终局池），自动结算。
与每日任务（world.py daily）互补：周窗口、单笔经验 150-700k（新成长曲线），
作为 S4(51-70)/S5(71-100) 高频经验主轴。无接取/交付，击杀自动推进，达标即发奖。

命令：
  『周常』        查看本周悬赏（本周首查自动发布 3 条）+ 完成✅/进度⏳
  『周常列表 [页]』 全部悬赏池总览（分页 4 条/页）

状态：event_state key = weekly_{qq_id}_{ISO年}-W{周序号}（周序号 = date.isocalendar()[1]），
存 JSON {"tasks": {任务名: {need/prog/done/objective/reward_*}}, "done_n": N}。
跨周自动换 key → 旧状态自然作废（本周从未查过 = 无记录）。

推进钩子（击杀时调用，参照 world._bump_daily_progress 接线思路）：
  weekly_bump_kill(group_id, qq_id, monster) -> list[str]
    —— L3-P2a 起下沉 services/weekly_progress.py；**B8.2 线1 起实现已进内容包**
       （`content/flow/weekly_progress.py`），本模块 re-export 同名保持引用兼容；
       combat 击杀结算已切 L3 玩家事件订阅方调用。

★ B8.2 线1（2026-09-13）命令层薄壳化：本模块只留「注册 + 解析参数 + 取玩家 + 调包 + 拼文案」。
  · 状态/发奖/发布构造/悬赏池全在内容包：
      `content/flow/weekly_progress.py`（真源 = 原 `game/services/weekly_progress.py` 全文件
      + 原本文件 `_assign_week`，逐字端口；周状态族名 re-export 回来保持正文调用点不变）
      悬赏池数据 = 包内 `weekly_quests` 域（真源 `game/data/weekly_quests.py:22`，
      导出器 `scripts/export_domains/weekly_tower.py`）。
  · 渲染文案**一字未改**：`weekly.*` 的 `T.text/T.static` 调用点全部留在本文件
    （文案表门禁 `tests/test_texts_table.py` 的「声明 ↔ 调用点对账」按本文件 AST 扫）。
  · 宿主只被用来「注入替身」：`db`（event_state 四动词）+ `reward.grant_reward`。
"""
from ._platform import AstrMessageEvent

# 指令声明装配：正则来自 `data/command_specs.json`（声明是唯一真源）
from ._declared import declared

from .. import db
from .. import reward as _reward
from ..core import texts as T
from ..commands.base import CommandBase, require_player

# ★ B8.2 线1：读包（宿主 `game/data/weekly_quests.py` 与 `game/services/weekly_progress.py` 的
# 实现不再被本命令直接 import）。`package_apply()` = 本进程唯一的包加载口（`saintess_engine.package.load`：
# 包根进 sys.path → `content` 成命名空间包），幂等；失败**大声抛**（读不到包 = 悬赏板空转，比报错难查）。
from .. import bootstrap as _bootstrap          # noqa: E402

_bootstrap.package_apply()
from content.flow import weekly_progress as _WP  # noqa: E402

# 宿主替身注入：存储层（get/set_event_state）+ 发奖函数（真源 `from ..reward import grant_reward`）
_WP.bind_host(db, _reward.grant_reward)

# L3-P2a：周状态族 + 击杀推进 + 发布构造 —— 包内实现**按原名** re-export（名字不变 → 下面正文逐字保留）
from content.flow.weekly_progress import (  # noqa: E402,F401  (re-export)
    _week_key, _week_state, _save_week_state, _grant_rewards,
    weekly_bump_kill, _assign_week,
)

# 周常抽取条数 / 解锁等级（= 包内常量；真源 `game/data/weekly_quests.py:152/155`）
_WEEKLY_PICK = _WP.WEEKLY_PICK
_WEEKLY_MIN_LV = _WP.WEEKLY_MIN_LV


def _obj_label(obj: dict) -> str:
    """objective → 中文目标短标（面板行用）。"""
    if obj.get("kill_any"):
        return T.text("weekly.obj_kill_any", n=obj["kill_any"])
    if obj.get("kill_elite"):
        return T.text("weekly.obj_kill_elite", n=obj["kill_elite"])
    if obj.get("kill_boss"):
        return T.text("weekly.obj_kill_boss", n=obj["kill_boss"])
    return T.static("weekly.obj_other")


class WeeklyCmds(CommandBase):
    """周常悬赏：本周悬赏板查看/自动发布 + 悬赏池列表分页"""

    @declared("weekly_cmd")
    @require_player()
    async def weekly_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        lv = int(player.get("level") or 1)
        if lv < _WEEKLY_MIN_LV:
            yield event.plain_result(T.text("weekly.locked", min_lv=_WEEKLY_MIN_LV))
            return
        st = _week_state(qq_id)
        if not st or not st.get("tasks"):
            # 本周首查 → 自动发布
            st = {"tasks": _assign_week(player), "done_n": 0}
            _save_week_state(qq_id, st)
            lines = [T.static("weekly.title_new"), "━━━━━━━━━━━━"]
            for i, (tname, task) in enumerate(st["tasks"].items(), 1):
                lines.append(T.text("weekly.item_new", i=i, tname=tname,
                                     desc=task["desc"]))
                lines.append(T.text("weekly.item_line", obj=_obj_label(task["objective"]),
                                     exp=task["reward_exp"], gold=task["reward_gold"]))
            lines.append("")
            lines.append(T.static("weekly.tip_new"))
            yield event.plain_result("\n".join(lines))
            return
        # 查看进度
        tasks = st["tasks"]
        done_n = int(st.get("done_n", 0) or 0)
        lines = [T.text("weekly.title_progress", done_n=done_n, total=len(tasks)),
                 "━━━━━━━━━━━━"]
        for i, (tname, task) in enumerate(tasks.items(), 1):
            prog = int(task.get("prog", 0) or 0)
            need = int(task.get("need") or 1)
            if task.get("done"):
                lines.append(T.text("weekly.item_done", i=i, tname=tname))
            else:
                lines.append(T.text("weekly.item_todo", i=i, tname=tname,
                                     prog=prog, need=need))
                lines.append(T.text("weekly.item_line", obj=_obj_label(task["objective"]),
                                     exp=task["reward_exp"], gold=task["reward_gold"]))
        if done_n < len(tasks):
            lines.append("")
            lines.append(T.static("weekly.tip_progress"))
        yield event.plain_result("\n".join(lines))

    @declared("weekly_list")
    @require_player()
    async def weekly_list(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "周常列表").strip()
        page = self._parse_page(raw)
        lv = int(player.get("level") or 1)
        all_pool = _WP.weekly_pool()          # ★ B8.2 线1：悬赏池改读包内 weekly_quests 域（源列表序）
        page_items, pages, page = self._page_items(all_pool, page, per_page=4)
        lines = [T.text("weekly.pool_title", page=page, pages=pages, pick=_WEEKLY_PICK),
                 "━━━━━━━━━━━━"]
        for q in page_items:
            lv_req = int(q.get("min_lv") or 0)
            lock = " 🔒" if lv < lv_req else ""
            lines.append(T.text("weekly.pool_item", name=q["name"], lv_req=lv_req,
                                 lock=lock, desc=q["desc"]))
            lines.append(T.text("weekly.pool_reward", exp=q["reward_exp"],
                                 gold=q["reward_gold"]))
        lines.append("")
        lines.append(T.static("weekly.pool_tip"))
        if pages > 1:
            lines.append(T.text("weekly.pool_more",
                                 next_page=(page + 1 if page < pages else 1)))
        yield event.plain_result("\n".join(lines))
