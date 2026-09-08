# -*- coding: utf-8 -*-
"""v181.P4 N5b4-5a 副本战斗控制器（battle2 原生重写版）。

鱼鱼 2026-09-08 拍板：副本战斗不用旧引擎、不在老 instance.py 上打洞——
本控制器以 battle2 state 为战斗权威：

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

引擎零改动依赖：battle2 + bridge + schedule；本文件不 import 旧 game.battle。
"""
from __future__ import annotations

from typing import Optional

from ..services import battle2_bridge as BR
from ..core.skill_kinds import K_HEAL, K_BUFF

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
    """玩家快照 + st per-player 键 → battle2 player actor（sides 用）。

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
    # 通用外部增幅（N5b4-4c）：快照 stat_bonus（旧档 title_bonus 键兜底）
    _sb = snap.get("stat_bonus") or snap.get("title_bonus") or {}
    actor["stat_bonus"] = dict(_sb or {})
    return actor


def build_battle(st: dict) -> "object":
    """遭遇/切怪/Boss 战：组 sides → B2 → st["battle"]=to_state。返回 B2。

    玩家 side = st["members"] 存活者 actor；敌 side = st["enemies"] 单位 actor。
    宠物：当前队长/首成员宠物照传（只存不驱动，宠物批前不参与）。
    """
    from ..battle2 import Battle as B2
    sides: dict = {"player": [], "enemy": []}
    for k in st.get("members") or []:
        kk = str(k)
        if not (st.get("alive") or {}).get(kk, True):
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
    from ..battle2 import Battle as B2
    from .. import engine as E
    st_battle = st.get("battle") or {}
    if not st_battle.get("sides"):
        return ["战斗状态异常，请重新遭遇！"], True, None
    b = B2.from_state(st_battle)
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
        return ["你已不在战斗中（状态异常）！"], True, None
    _tgt = target
    # 目标解析：battle2 引擎只吃 actor dict（字符串会崩）——名字/编号在此翻译。
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
            _info = E.skill_info(my.get("class_name") or "", skill_name) or {}
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
    """唯一视图/DB 同步点：battle2 actors → 玩法壳旧键 + 玩家 DB 血量。

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
        from ..services.battle2_bridge import sync_player_from_actor
        sync_player_from_actor(snap, _a)  # hp/mp/max/buffs/shields/defending/charging...
        for _ak, _sk in _VIEW_ST_KEYS.items():
            if _a.get(_ak) is not None:
                st.setdefault(_sk, {})[_k] = _a[_ak]
        snap["ct"] = float(_a.get("ct", 0) or 0)
        snap["stat_bonus"] = dict(_a.get("stat_bonus") or {})
        # 倒地标记（O105 语义）
        if snap.get("hp", 0) <= 0 and st.get("alive", {}).get(_k, True):
            st["alive"][_k] = False
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
