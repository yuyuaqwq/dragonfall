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
from .. import battle as BT
from ..commands.base import CommandBase, require_player


def _tower_key(qq_id) -> str:
    return f"tower_{qq_id}"


def _tower_state(qq_id):
    d = None
    raw = db.get_event_state(_tower_key(qq_id))
    if raw:
        try:
            d = json.loads(raw)
        except Exception:
            d = None
    st = {"cur": 0, "cleared_today": [], "count_today": 0, "date": ""}
    if isinstance(d, dict):
        st.update(d)
    today = datetime.date.today().isoformat()
    if st.get("date") != today:
        st["cleared_today"] = []
        st["count_today"] = 0
    st["date"] = today
    # 类型兜底（旧档脏数据防御）
    st["cleared_today"] = [int(x) for x in (st.get("cleared_today") or [])]
    try:
        st["count_today"] = int(st.get("count_today") or 0)
    except Exception:
        st["count_today"] = 0
    try:
        st["cur"] = int(st.get("cur") or 0)
    except Exception:
        st["cur"] = 0
    return st


def _save_tower_state(qq_id, st):
    db.set_event_state(_tower_key(qq_id), json.dumps(st, ensure_ascii=False))


def _floor_def(floor: int) -> dict:
    """TRIAL_FLOORS 表查找（1 基；找不到返回 None）。"""
    floors = list(getattr(C, "TRIAL_FLOORS", None) or [])
    for f in floors:
        if int(f.get("floor") or 0) == int(floor):
            return f
    return None


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
            "role": role, "rank": 1, "reach": 1, "buffs": {}, "stacks": {},
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


def tower_guard_on_kill(inst, group_id, qq_id, monster) -> list:
    """塔卫被击杀 → 爬塔状态推进 + 金币结算 + 文案（combat._handle_victory 击杀后调用）。

    经验已由标准战斗结算按 monster.exp 发放；金币（v93 怪物 gold 不直接入账）在此
    显式 +reward_gold。返回通知行由调用方拼入结算输出。
    """
    lines = []
    try:
        mid = str(monster.get("id") or "")
        if not mid.startswith("tower_"):
            return lines
        floor = int(mid[len("tower_"):])
        fd = _floor_def(floor) or {}
        gold = int(fd.get("reward_gold") or 0)
        # 金币显式入账（v93：怪物 gold 折算材料不入账，塔的金币走这里）
        if gold > 0:
            player = inst._player(group_id, qq_id)
            db.update_player(group_id, qq_id, gold=int(player.get("gold", 0) or 0) + gold)
            lines.append(f"💰 塔层赏金：金币 +{gold}")
        st = _tower_state(qq_id)
        today_cleared = [int(x) for x in (st.get("cleared_today") or [])]
        # 幂等：同一天同层已结算过不再重复计数
        if floor in today_cleared:
            return lines
        today_cleared.append(floor)
        st["cleared_today"] = sorted(today_cleared)
        st["count_today"] = len(today_cleared)
        st["cur"] = max(int(st.get("cur") or 0), floor)
        _save_tower_state(qq_id, st)
        lines.append(f"🏯 第 {floor} 层【{fd.get('name') or ''}】突破！")
        left = max(0, int(getattr(C, "TRIAL_DAILY_LIMIT", 3) or 3) - st["count_today"])
        if floor >= int(getattr(C, "TRIAL_MAX_FLOOR", 30) or 30):
            lines.append("👑 你已登顶修炼塔之巅——奥兰迪亚的强者之名，当之无愧！")
        elif left > 0:
            nxt = floor + 1
            nfd = _floor_def(nxt)
            lines.append(f"💡 今日还可突破 {left} 层——回复『爬塔』挑战第 {nxt} 层"
                         + (f"【{nfd.get('name') or ''}】(建议 Lv.{nfd.get('lv')})" if nfd else ""))
        else:
            lines.append("🌙 今日修炼已满 3 层，好好消化感悟，明日再来！(失败/逃跑不占次数)")
    except Exception:
        pass
    return lines


class TowerCmds(CommandBase):
    """修炼爬塔：Lv70+ 单人守关挑战"""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?爬塔(?:\s+(\d+))?\s*$")
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
        b = BT.Battle("monster", None, self._title_bonus(group_id, qq_id),
                      player=player, pet=db.pet_get(qq_id), enemies=[guard])
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
