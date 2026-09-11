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
"""
import datetime
import json

from ._platform import AstrMessageEvent, filter

from .. import content as C
from .. import db
from ..commands.base import CommandBase, require_player

# L3-P2a：状态函数族 + 击杀结算下沉 services/tower_progress.py（服务层订阅方消费，
# services 禁 import commands 红线）；命令层 re-export 同名单保持零改动引用。
from ..services.tower_progress import (  # noqa: F401  (re-export)
    _tower_key, _tower_state, _save_tower_state, _floor_def,
    tower_guard_on_kill,
)


def build_tower_guard(floor: int) -> dict:
    """构造第 floor 层塔卫（普通战斗敌人 dict；exp/gold = 层奖励）。"""
    fd = _floor_def(floor) or {}
    name = fd.get("guard") or f"第{floor}层守卫"
    lv = int(fd.get("lv") or min(100, 70 + floor))
    role = fd.get("role") or "dps"
    skills = list(fd.get("skills") or [])
    fake_map = {"id": "trial_tower", "name": "修炼塔", "lv": lv, "area": "tower"}
    try:
        guard = C.build_monster((f"tower_{floor}", name, role, lv, skills, []), fake_map)
    except Exception:
        # build_monster 失败兜底：手搓最小敌人（防数据漂移导致爬塔不可玩）
        guard = {
            "id": f"tower_{floor}", "uid": f"e_tower_{floor}", "name": name, "lv": lv,
            "role": role, "rank": 1, "reach": 1,
            "defending": False, "charging": None,
            "hp": 600, "max_hp": 600, "atk": 60, "def": 30, "matk": 30, "mdef": 30,
            "spd": 12, "exp": 0, "gold": 0, "skills": [], "drops": [],
            "map": "修炼塔", "map_area": "tower", "is_boss": False, "is_elite": False,
            "mech": "", "mod": "",
        }
    # 层挑战系数（hp/atk 放大；exp/gold 覆盖为层奖励）
    guard["hp"] = max(1, int(guard.get("hp", 100) * float(fd.get("hp_mult") or 1.0)))
    guard["max_hp"] = guard["hp"]
    guard["atk"] = max(1, int(guard.get("atk", 10) * float(fd.get("atk_mult") or 1.0)))
    guard["matk"] = max(1, int(guard.get("matk", 10) * float(fd.get("atk_mult") or 1.0)))
    # v93 经济：怪物 gold 字段不直接入账（折算材料），塔的金币奖励改由
    # tower_guard_on_kill 结算时显式发放 → 怪物 gold 置 0 防白嫖材料掉落
    guard["exp"] = int(fd.get("reward_exp") or 0)
    guard["gold"] = 0
    return guard


class TowerCmds(CommandBase):
    """修炼爬塔：Lv70+ 单人守关挑战"""

    @filter.regex(r"^(?:\[At:[^\]]+\]\s*)?爬塔(?:\s+(\d+))?\s*$")
    @require_player()
    async def tower_cmd(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        lv = int(player.get("level") or 1)
        min_lv = int(getattr(C, "TRIAL_MIN_LV", 70) or 70)
        max_floor = int(getattr(C, "TRIAL_MAX_FLOOR", 30) or 30)
        daily_limit = int(getattr(C, "TRIAL_DAILY_LIMIT", 3) or 3)
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
        guard = build_tower_guard(floor)
        guard_name = guard.get("name", "塔卫")
        # N5b4-6：塔开战 saintess_engine 化（四步仪式：prepare → sides → 装配 → B2；
        # 同 _open_battle 语义，tower 是普通战斗形态）
        from ..services import battle_bridge as BR
        tb = self._title_bonus(group_id, qq_id)
        BR.prepare_player_for_battle(player, tb, db)
        _sides = BR.build_sides(player=player, enemies=[guard])
        for _a in _sides.get("player", []):
            try:
                # v181.M-bonus 统一数值容器：外部面板增幅聚合塞 bonus.panel（cap/cost 由
                # apply_to_actor 装备装配覆盖写各分域）
                _a["bonus"] = {"panel": dict(tb or {}), "cap": {}, "cost": {}}
            except Exception:
                pass
            try:
                from ..services.battle_equip_proc import apply_to_actor as _EP_apply
                _EP_apply(_a)
            except Exception:
                pass
            try:
                from ..services.class_mech_proc import apply_class_mech as _CM_apply
                _CM_apply(_a)
            except Exception:
                pass  # 技能 mech 兑现装配异常不阻断开战
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
