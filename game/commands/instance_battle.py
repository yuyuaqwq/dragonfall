# -*- coding: utf-8 -*-
"""v181.P4 N5b4-5a 副本战斗控制器（saintess_engine 原生重写版）。

鱼鱼 2026-09-08 拍板：副本战斗不用旧引擎、不在老 instance.py 上打洞——
本控制器以 saintess_engine state 为战斗权威：

- `st["battle"]` = B2(...).to_state()（sides 全员 actors + now + killed；无镜像）
- `build_battle(st)`：遭遇/切怪/Boss 战组 sides → 构造 → 落 st["battle"]
- `act(...)`：from_state → human_act（副本轮流由玩法壳驱动，此处对指定 actor 出手）
  → to_state 落回；heal/buff 技能 target=None 防奶敌（同 PVP 语义）
- `sync_views(st, group_id)`：唯一视图/DB 同步点——actors → st["players"]/
  st["boss"]/st["enemies"] 玩法壳旧键 + 玩家 DB 血量（战斗内 DB 保持开本值、
  每刻同步，保留现行为）
- 轮转/超时/通关/肃清账务 = 玩法壳（instance.py）薄壳调用本控制器读 actors 结果

5a 边界（随批次补）：target_picker/on_event 预留 None（5b 仇恨/团队广播）；
宠物 Battle pet 只存不驱动（宠物批）；玩家词条种子护盾由玩法壳保留调用
（装配启用待鱼鱼拍板）；副本旧毒（debuffs.poison δ层）未迁 state dot（内容批）。

引擎零改动依赖：saintess_engine + bridge + schedule；本文件不 import 旧 game.battle。
"""
from __future__ import annotations

from typing import Optional

from ..core import instance_run as IR
from ..core import texts as T  # v185：文案表（唯一真源 game/data/text_specs.json）   # v185：名单视图（成员/存活）
from ..services import battle_bridge as BR
from saintess_engine.kinds import K_HEAL, K_BUFF

# 玩家快照/玩法壳视图需要同步回的每玩家键（actor → snap 或 st per-player 键）
# V 系列：战斗状态权威 = effects（snap 由 sync_player_from_actor 回写），
# p_buffs/p_hot 等玩法壳视图键的折算由显示层按需读 effects（N5b4-1 双引擎通用）
_VIEW_SNAP_KEYS = (
    "hp", "mp", "max_hp", "max_mp", "effects", "shields", "defending", "charging",
    "ct", "cooldown", "food_effects",
)
_VIEW_ST_KEYS = {
    "effects": "p_effects", "shields": "p_shields", "food_effects": "p_food_effects",
    "defending": "p_defending", "charging": "charging", "cooldown": "cooldown",
}


def _player_actor(snap: dict, st: dict, key: str) -> dict:
    """玩家快照 + st per-player 键 → saintess_engine player actor（sides 用）。

    快照字段全透传（身份/面板/站位）；V 系列：状态在 snap.effects（由
    sync_player_from_actor 每帧回写），p_effects 顶层键为老档兜底。
    """
    actor = BR.player_to_actor(snap)
    # 状态键合并：快照内键优先，st 顶层键兜底（老存档恢复兼容）
    _snap_src = {}
    for _k in ("effects", "shields", "defending", "charging", "ct",
               "cooldown", "food_effects"):
        if snap.get(_k) is not None:
            _snap_src[_k] = snap[_k]
    for _snap_k, _st_k in _VIEW_ST_KEYS.items():
        if _snap_k not in _snap_src and (st.get(_st_k) or {}).get(str(key)) is not None:
            _snap_src[_snap_k] = (st.get(_st_k) or {}).get(str(key))
    if _snap_src.get("effects") is not None:
        actor["effects"] = dict(_snap_src["effects"])
    if _snap_src.get("shields") is not None:
        actor["shields"] = dict(_snap_src["shields"])
    if _snap_src.get("defending") is not None:
        actor["defending"] = bool(_snap_src["defending"])
    if _snap_src.get("charging") is not None:
        actor["charging"] = _snap_src["charging"]
    if _snap_src.get("cooldown") is not None:
        actor["cooldown"] = dict(_snap_src["cooldown"])
    if _snap_src.get("food_effects") is not None:
        actor["food_effects"] = list(_snap_src["food_effects"])
    actor["ct"] = float(_snap_src.get("ct", 0) or 0)
    # 统一数值容器（v181.M-bonus）：快照 bonus 全容器恢复（panel/cap/cost 随 actor
    # 落盘/恢复）；旧档快照（无 bonus 键，stat_bonus/cap_bonus 旧键）一次性转换——
    # 仅存档数据迁移，非引擎读源回落（引擎读源一律 bonus 分域 get 兜底）
    _bns = snap.get("bonus")
    if isinstance(_bns, dict):
        actor["bonus"] = {
            "panel": dict(_bns.get("panel") or {}),
            "cap": dict(_bns.get("cap") or {}),
            "cost": dict(_bns.get("cost") or {}),
        }
    else:
        actor["bonus"] = {
            "panel": dict(snap.get("stat_bonus") or snap.get("title_bonus") or {}),
            "cap": dict(snap.get("cap_bonus") or {}),
            "cost": {},
        }
    actor.pop("stat_bonus", None)
    actor.pop("cap_bonus", None)
    return actor


def _instance_target_picker(st: dict):
    """副本自动怪目标选择闭包（5b G1：仇恨/嘲讽/target_policy）。

    返回 callable(battle, actor) -> Optional[actor]（None=引擎回落默认敌对）。
    语义对齐旧 _pick_instance_target（battle.py 1440-1479）：
    ① 嘲讽强制：st.taunt_target 存活 → 打嘲讽者
    ② 按怪 target_policy（MONSTER_MODS target_policy；Boss 缺省 hate_top，
       其他缺省 front）+ st.threat 表 → FM.pick_by_policy
    引擎零游戏知识（target_picker 只是决策注入点）。
    """
    def pick(battle, actor):
        try:
            from saintess_engine import formation as FM
            from .. import content as C
            alive_p = [a for a in battle.sides_of("player")
                       if int(a.get("hp", 0) or 0) > 0]
            if not alive_p:
                return None
            # N5B target_hint：AI 战术目标提示（v1：lowest_hp 残血收割）——
            # hint 与仇恨不冲突时优先（一次性，消费即弃；未知 hint 回落仇恨）
            _hint = actor.pop("_target_hint", None)
            if _hint == "lowest_hp":
                return min(alive_p, key=lambda a: (
                    int(a.get("hp", 0) or 0) /
                    max(1, int(a.get("max_hp", 1) or 1))))
            # ① 嘲讽强制
            tk = str(st.get("taunt_target") or "")
            if tk:
                for a in alive_p:
                    if str(a.get("qq_id") or "") == tk:
                        return a
            # ② target_policy + threat（threat 表 key=qq_id → pick 用 uid 映射）
            _threat = {}
            for a in alive_p:
                _q = str(a.get("qq_id") or "")
                _threat[str(a.get("uid") or ("p_%s" % _q))] = float(
                    (st.get("threat") or {}).get(_q, 0) or 0)
            _tpol = ""
            try:
                _mid = actor.get("id") or ""
                _tpol = str((C.MONSTER_MODS.get(_mid, {}) or {}).get("target_policy", "") or "")
            except Exception:
                _tpol = ""
            if not _tpol:
                _tpol = "hate_top" if str(actor.get("role", "")) == "boss" else "front"
            picked = FM.pick_by_policy(_tpol, alive_p, threat=_threat)
            return picked
        except Exception:
            return None
    return pick


def _instance_team_event(st: dict):
    """副本团队技能广播观察者（5b G2：act_cast + info.team → 全队效果）。

    旧引擎由 battle.py 生成 team_effects（6176/6256/7204）→ instance 层 _apply_team_effect
    消费；saintess_engine 引擎零游戏知识——本观察者经 on_event（事件总线尾部通知）监听：
      act_cast + info.team == "heal_all" → 除施放者外全队治疗（施放者已由 _do_heal 治疗）
    数据现状：skills.py team 值仅 heal_all（牧师救赎之光）——按数据声明做，无 if-elif 扩散。
    """
    def on_event(battle, evt_name, ctx, logs):
        try:
            if evt_name != "act_cast":
                return
            info = (ctx or {}).get("info") or {}
            team = info.get("team")
            if not team or team != "heal_all":
                return
            caster = (ctx or {}).get("actor")
            if not caster or int(caster.get("hp", 0) or 0) <= 0:
                return
            # 治疗量 = 施法者面板公式（对齐 _do_heal/_heal_amount，独立算全队口径）
            from saintess_engine.battle.actions import heal_amount as _hcalc
            from saintess_engine import stats as _S
            from saintess_engine.battle.landing import heal_actor as _heal
            from ..content_rules.skills import skill_level_of
            _stp = _S.actor_stats(battle, caster)
            _lv = skill_level_of(caster, info.get("name", "")) if caster.get("class_name") else 0
            try:
                _heal_v = _hcalc(_stp, caster, info, _lv)
            except Exception:
                _heal_v = 0
            if _heal_v <= 0:
                return
            for _a in battle.sides_of("player"):
                if _a is caster or int(_a.get("hp", 0) or 0) <= 0:
                    continue
                _real = _heal(battle, _a, _heal_v, logs)
                if _real > 0:
                    logs.append(T.text("instance.日志_团队治疗", name=_a.get('name', '队友'), amount=_real))
        except Exception:
            pass  # 观察者异常不阻断战斗结算
    return on_event


def _attach_instance_hooks(b, st: dict) -> None:
    """battle 恢复/重建后重挂命令层注入钩子（5b：target_picker + 5a：action_override）。

    saintess_engine 的 Battle 构造参数（target_picker/on_event/action_override）都是运行回调，
    不随 to_state/from_state 序列化——每次 from_state 后必须重挂，否则副本自动怪
    不按仇恨选目标、道具行动回调丢失。
    """
    try:
        b.target_picker = _instance_target_picker(st)
    except Exception:
        b.target_picker = None
    try:
        from .battle_item_use import make_override
        b.action_override = make_override()
    except Exception:
        b.action_override = None
    try:
        from .boss_script import make_script_event
        _se = make_script_event(st)
        _te = _instance_team_event(st)

        def _combined_event(battle, evt_name, ctx, logs):
            _te(battle, evt_name, ctx, logs)
            _se(battle, evt_name, ctx, logs)
        b.on_event = _combined_event
    except Exception:
        b.on_event = None
    try:
        # 5c P1：Boss 剧本导演钩子（敌方阵容有剧本 Boss 才挂；无 → None 回落）
        from .boss_script import boss_script_cfg, make_script_hook
        _has_script = any(
            boss_script_cfg(st, a) is not None
            for a in b.sides_of("enemy")
            if int(a.get("hp", 0) or 0) > 0
        )
        b.script_hook = make_script_hook(st) if _has_script else None
    except Exception:
        b.script_hook = None


def build_battle(st: dict) -> "object":
    """遭遇/切怪/Boss 战：组 sides → B2 → st["battle"]=to_state。返回 B2。

    玩家 side = st["members"] 存活者 actor；敌 side = st["enemies"] 单位 actor。
    宠物：当前队长/首成员宠物照传（只存不驱动，宠物批前不参与）。
    """
    from saintess_engine import Battle as B2
    sides: dict = {"player": [], "enemy": []}
    _roster = IR.roster_of(st)   # v185：名单视图（保序；缺 alive 键 = 存活）
    for kk in _roster.members:
        if not _roster.alive(kk):
            continue
        snap = (st.get("players") or {}).get(kk)
        if not snap or int(snap.get("hp", 0) or 0) <= 0:
            continue
        sides["player"].append(_player_actor(snap, st, kk))
    for u in st.get("enemies") or []:
        if not isinstance(u, dict):
            continue
        try:
            sides["enemy"].append(BR.monster_to_actor(u))
        except Exception:
            continue  # 个别单位翻译失败不阻断整场（数据异常容错）
    _pet = {}
    try:
        _first_alive = next((a for a in sides["player"]), None)
        if _first_alive:
            _k0 = str(_first_alive.get("qq_id") or "")
            _pet = (st.get("pets") or {}).get(_k0) or {}
    except Exception:
        pass
    b = B2("instance", sides=sides, title_bonus={}, pet=_pet or {})
    # 5b：构造时注入副本命令层钩子（target_picker 仇恨选目标等）
    _attach_instance_hooks(b, st)
    st["battle"] = b.to_state()
    return b


def _players_of(st: dict) -> list:
    """st["battle"] sides player actors（存活+死亡全量，按序）。"""
    _b = (st.get("battle") or {}).get("sides") or {}
    return list(_b.get("player") or [])


def _enemies_of(st: dict) -> list:
    _b = (st.get("battle") or {}).get("sides") or {}
    return list(_b.get("enemy") or [])


def player_actor_of(st: dict, qq_id) -> Optional[dict]:
    """按 qq_id 找玩家 actor（存活优先，死亡兜底——展示要显示倒地者）。"""
    _q = str(qq_id)
    acts = [a for a in _players_of(st) if str(a.get("qq_id") or "") == _q]
    if not acts:
        return None
    alive = [a for a in acts if (a.get("hp") or 0) > 0]
    return (alive or acts)[0]


def next_actor_key(st: dict) -> Optional[str]:
    """下一个该行动玩家 = sides player 存活 actor 中 ct 最小者。"""
    best, best_t = None, None
    for a in _players_of(st):
        if (a.get("hp") or 0) <= 0:
            continue
        t = float(a.get("ct", 0) or 0)
        if best_t is None or t < best_t:
            best_t, best = t, a
    return str(best.get("qq_id") or "") if best else None


def act(st: dict, group_id, qq_id, action: str, skill_name=None,
        target=None) -> tuple:
    """真人行动：from_state → human_act → to_state 落回。

    返回 (logs, ended, next_key)。副本轮流由玩法壳驱动：调用前已确认轮到 qq_id。
    target：外部解析好的目标 actor（None=自动）；heal/buff 强制 None 防奶敌。
    """
    from saintess_engine import Battle as B2
    from ..content_rules.skills import skill_info
    st_battle = st.get("battle") or {}
    if not st_battle.get("sides"):
        return [T.static("instance.结算_战斗异常")], True, None
    b = B2.from_state(st_battle)
    # I3：from_state 后注入道具行动回调 + 5b target_picker（action_override/
    # target_picker 不可序列化，恢复必重挂——副本自动怪选目标、道具行动都靠它们）
    _attach_instance_hooks(b, st)
    # 从重建后的 b.sides 定位行动者（不能从 st 旧 dict 找——from_state 是反序列化
    # 副本，引擎修改落在 b 内 actor，若用 st 旧 actor 则 to_state 落回时修改丢失：
    # hp/ct/defending 全部不写回，副本战斗永远无进展）。PVP act 同口径。
    my = None
    try:
        for _a in b.sides_of("player"):
            if str(_a.get("qq_id") or "") == str(qq_id):
                my = _a
                break
    except Exception:
        my = None
    if my is None:
        my = player_actor_of(st, qq_id)
    if my is None:
        return [T.static("instance.面板_战斗_不在")], True, None
    _tgt = target
    # 目标解析：saintess_engine 引擎只吃 actor dict（字符串会崩）——名字/编号在此翻译。
    # 支持：None=自动 / actor dict 直传 / 字符串=敌名（前缀匹配，v2 多怪指定）
    #       / aN 编号（A 层第 N 个存活敌，formation 站位编号语义，v127.3）
    if isinstance(_tgt, str):
        _s = _tgt.strip().lower()
        _alive_e = [u for u in b.sides_of("enemy") if (u.get("hp") or 0) > 0]
        _picked = None
        if _s.startswith("a") and _s[1:].isdigit():
            _idx = int(_s[1:]) - 1
            if 0 <= _idx < len(_alive_e):
                _picked = _alive_e[_idx]
        elif _s.isdigit():
            _idx = int(_s) - 1
            if 0 <= _idx < len(_alive_e):
                _picked = _alive_e[_idx]
        else:
            _nm = _tgt.strip()
            for u in _alive_e:
                if (u.get("name") or "") == _nm or (u.get("name") or "").startswith(_nm):
                    _picked = u
                    break
        _tgt = _picked  # 解析失败 → None 自动选目标（引擎 _default_target）
    _action, _skill = action, skill_name
    if action == "skill" and skill_name:
        try:
            _info = skill_info(my.get("class_name") or "", skill_name) or {}
            if _info.get("kind") in (K_HEAL, K_BUFF):
                _tgt = None  # 治疗/增益作用自己（防奶敌）
        except Exception:
            pass
    logs, ended, who = b.human_act(_action, _skill, actor=my, target=_tgt)
    st["battle"] = b.to_state()
    nxt = None
    if not ended:
        try:
            nxt = next_actor_key(st)
        except Exception:
            nxt = None
    return logs, ended, nxt


def sync_views(st: dict, group_id) -> None:
    """唯一视图/DB 同步点：saintess_engine actors → 玩法壳旧键 + 玩家 DB 血量。

    - st["players"][k] 快照：hp/mp/max/buffs/shields/defending/charging/ct/...
    - st per-player 键（p_buffs/p_hot/p_defending/...）同帧更新（老玩法壳读）
    - st["boss"]/st["enemy"]/st["enemies"]：存活敌视图（死亡由玩法壳 compact）
    - st["now"]
    - DB：存活玩家 hp/mp 写回（战斗内 DB 保持开本值每刻同步，保留现行为）
    """
    players = st.setdefault("players", {})
    for _a in _players_of(st):
        _k = str(_a.get("qq_id") or "")
        snap = players.get(_k)
        if snap is None:
            continue
        from ..services.battle_bridge import sync_player_from_actor
        sync_player_from_actor(snap, _a)  # hp/mp/max/buffs/shields/defending/charging...
        for _ak, _sk in _VIEW_ST_KEYS.items():
            if _a.get(_ak) is not None:
                st.setdefault(_sk, {})[_k] = _a[_ak]
        snap["ct"] = float(_a.get("ct", 0) or 0)
        # v181.M-bonus：统一数值容器全量回写快照（panel/cap/cost；下轮 _player_actor 恢复）
        _bn = _a.get("bonus")
        snap["bonus"] = {
            "panel": dict((_bn or {}).get("panel") or {}),
            "cap": dict((_bn or {}).get("cap") or {}),
            "cost": dict((_bn or {}).get("cost") or {}),
        }
        snap.pop("stat_bonus", None)
        snap.pop("cap_bonus", None)
        # 倒地标记（O105 语义）——v185：存活表收口 instance_run（缺 alive 键 = 存活）
        if snap.get("hp", 0) <= 0 and IR.alive_of(st, _k):
            IR.set_alive(st, _k, False)
        # DB 血量同步（快照权威 → db，保留现行为）
        try:
            from .. import db as _db
            _db.update_player(group_id, _k,
                              hp=int(snap.get("hp", 0) or 0),
                              mp=int(snap.get("mp", 0) or 0),
                              max_hp=int(snap.get("max_hp", 0) or 0),
                              max_mp=int(snap.get("max_mp", 0) or 0))
        except Exception:
            pass
    # 敌视图（存活单位；死亡单位由玩法壳 compact 移除并记账）
    _alive_e = [a for a in _enemies_of(st) if (a.get("hp") or 0) > 0]
    st["enemies"] = _alive_e
    if _alive_e:
        st.setdefault("boss", _alive_e[0])
        st["enemy"] = _alive_e[0]
    elif st.get("boss") is not None:
        # 全灭：boss 键保留原引用（玩法壳按存活/uid 判定）
        pass
    try:
        st["now"] = float((st.get("battle") or {}).get("now", 0.0) or 0.0)
    except Exception:
        pass
