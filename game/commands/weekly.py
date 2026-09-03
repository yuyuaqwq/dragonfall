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
  weekly_bump_kill(inst, group_id, qq_id, monster) -> list[str]
    —— combat.py _update_quests 击杀结算处每只怪调一次，达标即自动发奖，
       返回通知行列表由调用方拼入战斗结算（与每日任务击杀分支同构）。
"""
import datetime
import json

from ._platform import AstrMessageEvent, filter

from .. import content as C
from .. import db
from .. import engine as E
from ..commands.base import CommandBase, require_player

# 周常抽取条数 / 解锁等级（与数据层 WEEKLY_PICK/WEEKLY_MIN_LV 对齐）
_WEEKLY_PICK = 3
_WEEKLY_MIN_LV = 50


def _week_key(qq_id) -> str:
    """周状态 event_state key：weekly_{qq_id}_{ISO年}-W{周}（跨年自动换 key）。"""
    y, w, _wd = datetime.date.today().isocalendar()
    return f"weekly_{qq_id}_{y}-W{w:02d}"


def _week_state(qq_id):
    """读取本周状态（无记录返回 None）。"""
    raw = db.get_event_state(_week_key(qq_id))
    if not raw:
        return None
    try:
        st = json.loads(raw)
        if not isinstance(st, dict):
            return None
        st.setdefault("tasks", {})
        st.setdefault("done_n", 0)
        return st
    except Exception:
        return None


def _save_week_state(qq_id, st):
    db.set_event_state(_week_key(qq_id), json.dumps(st, ensure_ascii=False))


def _grant_rewards(inst, group_id, qq_id, exp, gold):
    """周常达标发奖单点（与 world._settle_daily_quest 同款结算：exp/gold + 升级）。"""
    player = inst._player(group_id, qq_id)
    player["exp"] = int(player.get("exp", 0) or 0) + int(exp)
    player["gold"] = int(player.get("gold", 0) or 0) + int(gold)
    player["_title_bonus"] = inst._title_bonus(group_id, qq_id)
    lv_logs, player = E.check_player_level_up(group_id, qq_id, player)
    db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"],
                     level=player["level"], hp=player["hp"], mp=player["mp"],
                     max_hp=player["max_hp"], max_mp=player["max_mp"],
                     skills=player["skills"], attr_pts=player.get("attr_pts", 0),
                     skill_points=player.get("skill_points", 0),
                     learned_skills=player.get("learned_skills", []))
    return player


def weekly_bump_kill(inst, group_id, qq_id, monster) -> list:
    """击杀推进周常（combat._update_quests 击杀结算处调用）。

    周常无『接取/交付』环节：本周已发布的任务按击杀自动 +1，达标即自动结算发奖。
    与每日任务击杀分支（_update_quests）同构——kill_any 任意击杀 / kill_elite 精英 /
    kill_boss 区域 Boss。返回通知行列表（调用方拼入战斗结算输出）。
    """
    out = []
    try:
        st = _week_state(qq_id)
        if not st or not st.get("tasks"):
            return out
        is_elite = bool(monster.get("is_elite"))
        is_boss = bool(monster.get("is_boss"))
        changed = False
        for tname, task in list(st["tasks"].items()):
            if task.get("done"):
                continue
            need = int(task.get("need") or 0)
            obj = task.get("objective") or {}
            hit = bool(obj.get("kill_any")) or (bool(obj.get("kill_elite")) and is_elite) \
                or (bool(obj.get("kill_boss")) and is_boss)
            if not hit:
                continue
            task["prog"] = int(task.get("prog", 0) or 0) + 1
            changed = True
            if task["prog"] >= need:
                task["done"] = True
                st["done_n"] = int(st.get("done_n", 0) or 0) + 1
                _grant_rewards(inst, group_id, qq_id, task["reward_exp"], task["reward_gold"])
                out.append(f"📜 周常『{tname}』完成！奖励：经验 +{task['reward_exp']} 金币 +{task['reward_gold']}")
                if st["done_n"] >= len(st["tasks"]):
                    out.append("🏆 本周悬赏全部完成！下周刷新后再来领新赏金～")
        if changed:
            _save_week_state(qq_id, st)
    except Exception:
        # 周常推进失败不影响战斗主流程（与成就/野王 hook 同款宽容）
        pass
    return out


def _assign_week(player) -> dict:
    """按玩家等级发布本周 3 条悬赏（Lv50-69 中坚池 / Lv70+ 终局池），返回任务 dict。

    池内顺序取前 3（同周全员一致更公平——避免『同一周不同人任务不同』的攀比，
    也比每日 random.sample 少一个随机调用点，不扰动战斗回归随机序列）。
    """
    lv = int(player.get("level") or 1)
    pool = [q for q in C.WEEKLY_QUESTS if lv >= int(q.get("min_lv") or 0)]
    if len(pool) > _WEEKLY_PICK:
        pool = pool[: _WEEKLY_PICK]
    tasks = {}
    for q in pool:
        obj = dict(q.get("objective") or {})
        need = next((v for v in obj.values() if isinstance(v, int) and v > 0), 1)
        tasks[q["name"]] = {
            "need": need,
            "prog": 0,
            "done": False,
            "objective": obj,
            "reward_exp": int(q.get("reward_exp") or 0),
            "reward_gold": int(q.get("reward_gold") or 0),
            "desc": q.get("desc", ""),
        }
    return tasks


def _obj_label(obj: dict) -> str:
    """objective → 中文目标短标（面板行用）。"""
    if obj.get("kill_any"):
        return f"讨伐任意怪物 {obj['kill_any']} 只"
    if obj.get("kill_elite"):
        return f"讨伐精英怪物 {obj['kill_elite']} 只"
    if obj.get("kill_boss"):
        return f"讨伐区域 Boss {obj['kill_boss']} 只"
    return "讨伐指定目标"


class WeeklyCmds(CommandBase):
    """周常悬赏：本周悬赏板查看/自动发布 + 悬赏池列表分页"""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?周常(?!列表)(?:\s*|$)")
    @require_player()
    async def weekly_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        lv = int(player.get("level") or 1)
        if lv < _WEEKLY_MIN_LV:
            yield event.plain_result(
                f"🏮 悬赏板还蒙着布——上面的委托要 Lv.{_WEEKLY_MIN_LV} 的冒险者才接得动。\n"
                f"💡 先完成『每日』任务和主线提升等级，到了 Lv.{_WEEKLY_MIN_LV} 再来看看～"
            )
            return
        st = _week_state(qq_id)
        if not st or not st.get("tasks"):
            # 本周首查 → 自动发布
            st = {"tasks": _assign_week(player), "done_n": 0}
            _save_week_state(qq_id, st)
            lines = ["🏮 【本周悬赏】已发布！", "━━━━━━━━━━━━"]
            for i, (tname, task) in enumerate(st["tasks"].items(), 1):
                lines.append(f"{i}. 『{tname}』{task['desc']}")
                lines.append(f"    目标：{_obj_label(task['objective'])}｜赏金：经验 +{task['reward_exp']} 金币 +{task['reward_gold']}")
            lines.append("")
            lines.append("💡 击杀自动计数，达标立即发奖！『周常』随时查进度，『周常列表』看全池悬赏")
            yield event.plain_result("\n".join(lines))
            return
        # 查看进度
        tasks = st["tasks"]
        done_n = int(st.get("done_n", 0) or 0)
        lines = [f"🏮 【本周悬赏】{done_n}/{len(tasks)} 已完成", "━━━━━━━━━━━━"]
        for i, (tname, task) in enumerate(tasks.items(), 1):
            prog = int(task.get("prog", 0) or 0)
            need = int(task.get("need") or 1)
            if task.get("done"):
                lines.append(f"{i}. 『{tname}』 ✅ 已完成")
            else:
                lines.append(f"{i}. 『{tname}』 ⏳ {prog}/{need}")
                lines.append(f"    目标：{_obj_label(task['objective'])}｜赏金：经验 +{task['reward_exp']} 金币 +{task['reward_gold']}")
        if done_n < len(tasks):
            lines.append("")
            lines.append("💡 击杀自动计数，达标立即发奖——悬赏每周一刷新")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?周常列表(?:\s+(\d+))?\s*$")
    @require_player()
    async def weekly_list(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "周常列表").strip()
        page = self._parse_page(raw)
        lv = int(player.get("level") or 1)
        all_pool = list(C.WEEKLY_QUESTS)
        page_items, pages, page = self._page_items(all_pool, page, per_page=4)
        lines = [f"🏮 【周常悬赏池】第 {page}/{pages} 页（每周自动发布 {_WEEKLY_PICK} 条）", "━━━━━━━━━━━━"]
        for q in page_items:
            lv_req = int(q.get("min_lv") or 0)
            lock = " 🔒" if lv < lv_req else ""
            lines.append(f"· 『{q['name']}』(Lv.{lv_req}+{lock}) {q['desc']}")
            lines.append(f"    经验 +{q['reward_exp']} 金币 +{q['reward_gold']}")
        lines.append("")
        lines.append("💡 每周一刷新自动抽取适合你等级的悬赏；『周常』查看本周任务")
        if pages > 1:
            lines.append(f"📄 『周常列表 {page + 1 if page < pages else 1}』翻页")
        yield event.plain_result("\n".join(lines))
