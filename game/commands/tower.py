# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - tower（v169.2 修炼爬塔 Lv70+）

修炼爬塔：30 层单人守关试炼，Lv70+ 解锁，每日限通过 3 层（失败/逃跑不占次数）。
每层一个塔卫（普通战斗形态），胜利按层发 exp+gold（经标准战斗结算 _handle_victory，
等级差惩罚等全套机制照常），可继续挑战下一层。

命令：
  『爬塔』           查看进度并开始下一层挑战（战斗中回复战斗状态）
  『爬塔 <层数>』     挑战指定层（1-30，只能挑战已解锁层或它的下一层）

状态：event_state key = tower_{qq_id}，存 JSON：
    {"date": 今日, "cur": 已解锁最高层, "cleared_today": [今日已通层], "count_today": 今日已通数}
规则：
  - Lv70+ 解锁；每日 count_today >= 3 且目标层已通 → 拦截（失败/逃跑不占次数）
  - 同一天同一层不重复计数（cleared_today 幂等）
  - 胜利 = 塔卫被击杀：combat._handle_victory 击杀结算后调 tower_guard_on_kill
    （与 wild_king_on_kill 同款接线：import + try/except 调用，本模块导出该函数）

★ B8.2 线1（2026-09-13）命令层薄壳化：本模块只留「注册 + 解析参数 + 取玩家 + 调包 + 拼文案」。
  · 状态族/塔表查询/塔卫构造/击杀结算全在内容包 `content/flow/tower_progress.py`
    （真源 = 原 `game/services/tower_progress.py` 全文件 + 原本文件 `build_tower_guard`，逐字端口）；
    塔表 `TRIAL_FLOORS`/`TRIAL_MIN_LV`/`TRIAL_MAX_FLOOR`/`TRIAL_DAILY_LIMIT` = 包内
    `content/flow/tower_data.py`（真源 `game/data/trial_tower.py` **整文件逐字搬入**）。
  · 渲染文案一字未改（本命令是全 f-string 文案，不涉文案表）。
  · 留在宿主的部分（**与本线正交、本线不动**）：开战装配 `services/battle_bridge`（构造 actor →
    sides → 装配序列）+ `saintess_engine.Battle` + `db.save_battle` + `_battle_formation_panel`
    —— 包内对应物是 `content/bridge.py`（D3 批已搬的「构造半边」，替身接口按 `event_state` dict
    而非宿主 db 模块），本线不切（避免跨线重叠，见 overnight/b82_L1_weekly_tower.md §遗留）。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import db
from ..core.drops import build_monster          # 未进包真源（`game/core/drops.py:389`）→ 传给包内构造
from ..commands.base import CommandBase, require_player

# ★ B8.2 线1：读包。`package_apply()` = 本进程唯一的包加载口，幂等；失败大声抛。
from .. import bootstrap as _bootstrap          # noqa: E402

_bootstrap.package_apply()
from content.flow import tower_progress as _TP   # noqa: E402

# 宿主替身注入：存储层（get/set_event_state / get_player / update_player）
_TP.bind_host(db)

# L3-P2a：状态函数族 + 击杀结算 —— 包内实现**按原名** re-export（名字不变 → 下面正文逐字保留）
from content.flow.tower_progress import (  # noqa: E402,F401  (re-export)
    _tower_key, _tower_state, _save_tower_state, _floor_def,
    tower_guard_on_kill,
)


class TowerCmds(CommandBase):
    """修炼爬塔：Lv70+ 单人守关挑战"""

    @declared("tower_cmd")
    @require_player()
    async def tower_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        lv = int(player.get("level") or 1)
        min_lv = int(getattr(_TP, "TRIAL_MIN_LV", 70) or 70)
        max_floor = int(getattr(_TP, "TRIAL_MAX_FLOOR", 30) or 30)
        daily_limit = int(getattr(_TP, "TRIAL_DAILY_LIMIT", 3) or 3)
        if lv < min_lv:
            yield event.plain_result(
                f"🏯 修炼塔的门扉紧闭——塔灵的低语传来：『未至 {min_lv} 级者，不可窥见登天之路。』\n"
                f"💡 先完成『周常』悬赏和主线提升，到了 Lv.{min_lv} 再来挑战吧～"
            )
            return
        if self._in_any_battle(group_id, qq_id):
            yield event.plain_result("⚔️ 你正在战斗中！先解决眼前的敌人再说～(『攻击』『技能 <名称>』『防御』)")
            return
        st = _tower_state(qq_id)
        today_cleared = [int(x) for x in (st.get("cleared_today") or [])]
        cur = int(st.get("cur") or 0)
        raw = self._strip_cmd(event, "爬塔").strip()
        max_reached = cur
        # 『爬塔』默认目标：已突破最高层的下一层（线性推进；每日最多 3 个新层）
        if raw.isdigit():
            floor = int(raw)
            if floor < 1 or floor > max_floor:
                yield event.plain_result(
                    f"🏯 修炼塔共 {max_floor} 层，没有第 {floor} 层哦～(『爬塔 层数』1-{max_floor})"
                )
                return
            if floor != max_reached + 1:
                yield event.plain_result(
                    f"🏯 你还没解锁第 {floor} 层——塔灵只放行已突破层数的下一层。\n"
                    f"💡 回复『爬塔』挑战第 {max_reached + 1} 层～"
                )
                return
        else:
            if max_reached >= max_floor:
                yield event.plain_result(
                    "👑 你已登顶修炼塔之巅！这座塔已没有能拦住你的楼层了——"
                    "强者无需重复登顶，把传说留给后来者吧。"
                )
                return
            floor = max_reached + 1
        # 每日上限：今日已通 >=3 → 拦截新层（已通层同层不可重刷：进度线性、防刷经验）
        if len(today_cleared) >= daily_limit:
            yield event.plain_result(
                f"🌙 今日修炼已通过 {len(today_cleared)}/{daily_limit} 层，塔灵说该歇息了——明日再来！\n"
                f"🏯 当前进度：已突破至第 {cur} 层（明日『爬塔』挑战第 {cur + 1} 层）"
            )
            return
        if floor in today_cleared:
            yield event.plain_result(
                f"🏯 第 {floor} 层今日已突破过——塔灵只认新的挑战。\n"
                f"💡 回复『爬塔』挑战第 {max_reached + 1} 层，或明日再来～"
            )
            return
        fd = _floor_def(floor)
        if not fd:
            yield event.plain_result("🏯 塔灵正在重构试炼……稍后再来挑战吧～")
            return
        guard = _TP.build_tower_guard(floor, build_monster)   # ★ 塔卫构造在包内（宿主只传 build_monster）
        guard_name = guard.get("name", "塔卫")
        # N5b4-6：塔开战 saintess_engine 化（四步仪式：prepare → sides → 装配 → B2；
        # 同 _open_battle 语义，tower 是普通战斗形态）
        from ..services import battle_bridge as BR
        tb = self._title_bonus(group_id, qq_id)
        BR.prepare_player_for_battle(player, tb, db)
        _sides = BR.build_sides(player=player, enemies=[guard])
        for _a in _sides.get("player", []):
            # 装备词条 + 职业机制 + 外部增幅容器（序列收敛于 BR.apply_battle_loadout）
            BR.apply_battle_loadout(_a, tb)
        from saintess_engine import Battle as B2
        b = B2("monster", sides=_sides, title_bonus=tb, pet=db.pet_get(qq_id))
        db.save_battle(group_id, qq_id, b.to_state())
        _lock = getattr(self, "_lock_battle", None)
        if _lock:
            try:
                _lock(group_id, qq_id)
            except Exception:
                pass
        fl_name = fd.get("name") or f"第{floor}层"
        reward_exp = int(fd.get("reward_exp") or 0)
        reward_gold = int(fd.get("reward_gold") or 0)
        lines = [
            f"🏯 【修炼塔·{fl_name}】",
            f"你踏入第 {floor} 层，一个身影从阴影中浮现——",
            f"👤 【{guard_name}】Lv.{guard.get('lv')}（建议 Lv.{fd.get('lv')}）",
            f"📜 {fd.get('desc') or ''}",
            f"━━━━━━━━━━━━",
            f"奖励：经验 +{reward_exp} 金币 +{reward_gold}（击败后自动入账）",
            f"你的行动：『攻击』『技能 <名称>』『防御』『逃跑』",
        ]
        try:
            _fp = getattr(self, "_battle_formation_panel", None)
            if _fp:
                panel = _fp(player, b)
                lines.insert(4, panel + "\n")
        except Exception:
            pass
        yield event.plain_result("\n".join(lines))
