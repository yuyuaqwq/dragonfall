# -*- coding: utf-8 -*-
"""v181.P4 N5b 数据桥（battle2 命令层适配）——旧数据层 → battle2 actor 翻译。

位置：game/services/（battle2 包外——鱼鱼红线：battle2 引擎零改动、零旧数据知识，
本桥是"命令层侧的翻译层"，把命令层手里的旧数据形态（player dict / 怪组 / pet）
翻译成 battle2 的 sides actors。

翻译规则：
- 玩家（DB player dict）→ player actor：
    make_actor(uid=f"p_{qq_id}", side="player", kind="player", human_controlled=True,
               class_name/level/equipment/skills 透传，hp/mp 当前值透传)
    class_tier/attributes/evolve_path/race 透传（stats.actor_stats 重算面板用）
- 怪物（build_monster 产物 dict）→ enemy actor：
    lv → level（引擎不认 lv）；hp/max_hp/atk/def/matk/mdef/spd/crit 直读；
    身份字段 rank/reach/role/is_boss/is_elite/exp/gold/drops 透传；
    buffs/stacks/defending/charging → battle2 对应字段；
    class_name/equipment/learned_skills（怪扮职业）透传；
    auto_act（怪 AI）→ actor["auto_act"]（battle2 actor_auto 读它）
- 宠物 pet dict → battle2 pet（Battle 构造 pet 参数；战斗内宠物技能由命令层/引擎按需接入）
"""
from __future__ import annotations

from typing import Optional

from ..battle2 import make_actor  # 只读 battle2 工厂，不改 battle2

# ============================================================
# 玩家 → player actor
# ============================================================

# 玩家 dict 里需要透传给 battle2 actor 的面板/配置字段
_PLAYER_PASSTHROUGH = (
    "qq_id", "group_id", "cur_map", "race", "class_tier", "attributes",
    "evolve_path", "learned_skills", "skill_levels",
    # 状态字段（战斗内玩家 buffs/叠层/资源——从旧档恢复或开战仪式已写入 player）
    "resources", "stacks", "eff", "hot", "food_effects", "poi_buff",
    "buff_hits", "last_element", "dual_form", "focus", "vent",
    "v139_modes", "v139_charge", "overflow_shield_cd", "stealth_atk",
    "reduce_all_left", "reduce_left", "combo_seq", "last_combo_tag",
    "tailwind_prev_energy", "last_skill", "last_cast_at",
)

# 玩家 dict 的 buffs 键（旧引擎把玩家 buffs 写 player["buffs"]——battle2 actor.buffs 同构）
def player_to_actor(player: dict) -> dict:
    """玩家 DB dict → battle2 player actor（human_controlled=True）。"""
    player = player or {}
    qq = str(player.get("qq_id", ""))
    # 面板当前值：hp/mp 直传（旧 DB hp/mp 是当前值）；max 由 stats 重算或 DB 值
    stats_kw = {}
    for k in ("hp", "mp", "max_hp", "max_mp", "atk", "def", "matk", "mdef", "spd",
              "crit", "crit_dmg", "dodge", "block", "pene", "luck", "tenacity",
              "race"):
        if player.get(k) is not None:
            stats_kw[k] = player[k]
    # buffs/debuffs/shields/cooldown 同构透传
    for k in ("buffs", "debuffs", "shields", "cooldown", "charging", "defending",
              "ct", "state", "poi_buff"):
        if k == "state":
            # 旧 dict 没有 state 键（旧引擎用 stacks/resources 双轨）→ 由调用方决定映射
            continue
        if player.get(k) is not None:
            stats_kw[k] = player[k]
    skills = player.get("learned_skills") or player.get("skills") or []
    actor = make_actor(
        uid=("p_%s" % qq) if qq else "p_0",
        name=player.get("name", "冒险者"),
        side="player",
        kind="player",
        human_controlled=True,
        class_name=player.get("class_name") or "战士",
        level=int(player.get("level", 1) or 1),
        equipment=player.get("equipment") or {},
        skills=list(skills) if not isinstance(skills, list) else skills,
        learned_skills=list(player.get("learned_skills") or []),
        **stats_kw,
    )
    # 透传额外字段（身份/面板/数据标签——make_actor 会把未知 key 原样带上）
    for k in _PLAYER_PASSTHROUGH:
        if k in player and k not in actor:
            actor[k] = player[k]
    # 旧 stacks/resources → battle2 state 映射（开战仪式/恢复时用；默认空）
    #   注意：只有调用方明确要迁移时才填——本函数不做隐式迁移（避免把旧职业
    #   叠层语义错误地灌进 state，那应由上层职业模块按声明表翻译）
    return actor


# ============================================================
# 怪物 → enemy actor
# ============================================================

def monster_to_actor(mon: dict, idx: int = 0) -> dict:
    """单只怪 dict（build_monster 产物）→ battle2 enemy actor。

    lv → level（引擎不认 lv）；身份/站位/掉落字段透传。
    """
    mon = mon or {}
    stats_kw = {}
    for k in ("hp", "max_hp", "mp", "max_mp", "atk", "def", "matk", "mdef", "spd",
              "crit", "crit_dmg", "dodge", "block", "pene", "luck", "tenacity"):
        if mon.get(k) is not None:
            stats_kw[k] = mon[k]
    # buffs/debuffs/shields/cooldown/hot/charging/defending/ct 同构透传
    for k in ("buffs", "debuffs", "shields", "cooldown", "hot", "charging",
              "defending", "ct", "state"):
        if mon.get(k) is not None:
            stats_kw[k] = mon[k]
    actor = make_actor(
        uid=mon.get("uid") or ("e_%d" % idx),
        name=mon.get("name", "怪物"),
        side=mon.get("side") or "enemy",
        kind=mon.get("kind") or ("monster" if not mon.get("class_name") else "player"),
        class_name=mon.get("class_name"),
        level=int(mon.get("level", mon.get("lv", 1)) or 1),  # lv → level
        equipment=mon.get("equipment") or {},
        skills=list(mon.get("skills") or []),
        learned_skills=list(mon.get("learned_skills") or []),
        auto_act=mon.get("auto_act") or ({"act": {"type": "attack"}} if not mon.get("ai") else None),
        **stats_kw,
    )
    # 怪数据标签透传（站位/身份/掉落/元素/资源定义——make_actor 会原样带未知 key）
    for k in ("rank", "reach", "role", "is_boss", "is_elite", "exp", "gold", "drops",
              "id", "map", "map_area", "mech", "mod", "ai", "resource_def",
              "element_immune", "element_weak", "dmg_taken_mult", "on_taken",
              "abyss_res", "skill_levels", "race", "side", "ext"):
        if mon.get(k) is not None and k not in actor:
            actor[k] = mon[k]
    return actor


def enemies_to_actors(enemies: list) -> list:
    """怪组 list → enemy actor list。"""
    return [monster_to_actor(m, i) for i, m in enumerate(enemies or [])]


# ============================================================
# sides 组装
# ============================================================

def build_sides(player: Optional[dict] = None, enemies: Optional[list] = None,
                allies: Optional[list] = None) -> dict:
    """组 sides：{player: [玩家actor, ...], enemy: [怪actor, ...]}。

    单人野外：player 单 actor；副本 allies 额外 actor（human_controlled 按需）。
    """
    sides: dict = {"player": [], "enemy": []}
    if player is not None:
        p_actor = player_to_actor(player)
        sides["player"].append(p_actor)
    for a in (allies or []):
        sides["player"].append(player_to_actor(a))
    sides["enemy"] = enemies_to_actors(enemies or [])
    return sides


# ============================================================
# 开战仪式（旧 Battle.__init__ 的玩家侧副作用 → actor 初始状态）
# ============================================================

def apply_player_battle_start(player: dict, actor: dict, db=None) -> dict:
    """把旧 Battle.__init__ 的玩家侧开战仪式结果应用到 battle2 actor。

    目前实现（只做数据搬运，不触发引擎逻辑）：
    - echo_bless/poi_buff 已在 player dict 的 buffs/poi_buff 键里（旧引擎构造时
      从 event_state 读取写入 player）→ actor 构造时已透传
    - 装备词条战斗开始效果（护盾/狼嚎/奥术屏障/起手资源/套装）→ 属职业/装备层，
      N5b 后续增量按效果逐项搬（不在这里一次性全做）

    返回 actor（原地补全后同一引用）。
    """
    return actor


# ============================================================
# 旧档迁移（旧 battle state → battle2 sides state）
# ============================================================

# 旧档顶层玩家状态键 → player actor 字段映射
_OLD_PSTATE_TO_ACTOR = {
    "p_buffs": "buffs",            # 玩家 buffs dict
    "p_shields": "shields",        # 玩家护盾 dict
    "p_hot": "hot",                # HOT dict
    "charging": "charging",        # 蓄力
    "p_defending": "defending",    # 防御中
    "poi_buff": "poi_buff",        # 神龛祝福
    "cooldown": "cooldown",        # 技能冷却（绝对时刻）
    "combo_seq": "combo_seq",      # 连击序列
    "last_combo_tag": "last_combo_tag",
    "last_element": "last_element",
    "tailwind_prev_energy": "tailwind_prev_energy",
    "v139_modes": "v139_modes",
    "v139_charge": "v139_charge",
    "overflow_shield_cd": "overflow_shield_cd",
    "stealth_atk": "stealth_atk",
    "buff_hits": "buff_hits",      # 增益命中计数
    "reduce_all_left": "reduce_all_left",  # 团队减伤剩余刻
    "reduce_left": "reduce_left",          # 单体减伤剩余刻
    "eff_data": "eff",             # 旧效果倍数袋（部分走 state，这里兜底 eff 键）
    "p_food_effects": "food_effects",      # 食物效果
}

# 旧档顶层玩家"叠层/资源"键 → battle2 actor.state（统一数值容器）
# 注意：旧 stacks 是 {机制key: 层数}，旧 resources 是 {资源key: 值}。
# battle2 state 容器同时承载叠层和资源——但语义声明（cap/scale）查 state_effects 表。
# 迁移时平铺进 state（不做语义判断——那是上层职业模块的活）。
_OLD_PSTATE_TO_STATE = {
    "mech_stacks": None,   # 值 dict 直接合并进 state
    "resources": None,     # 值 dict 直接合并进 state
    "eff_data": None,      # 值 dict 直接合并进 state（旧 eff 效果倍数）
}


def is_old_state(st: dict) -> bool:
    """判断 battle_state.state 是不是旧引擎格式（无 sides 键 = 旧档）。"""
    if not isinstance(st, dict):
        return False
    if st.get("sides"):
        return False
    # 旧格式特征：有 enemies/enemy 键且无 sides
    return ("enemies" in st) or ("enemy" in st)


def migrate_old_state(st: dict, player: Optional[dict] = None) -> dict:
    """旧 battle state → battle2 state（sides 结构）。

    输入：旧引擎 to_state 产物（enemies/enemy/p_buffs/mech_stacks/resources 顶层键）
    输出：battle2 serialize.to_state 兼容结构（sides + 战斗级 meta 保留）

    player：命令层手里的当前玩家 dict（恢复战斗时 db.get_player）——玩家 actor 的
      身份/面板字段从这里来；旧档顶层的玩家战斗状态（buffs/护盾/叠层/资源）灌入。

    战斗级元数据（旧 Battle 当 dict 塞的 map/name/dot_res/adapt 等）：
      保留到返回 dict 的 "meta" 键（battle2 引擎不读，命令层展示用）。
    """
    st = st or {}
    enemies_raw = st.get("enemies")
    if not enemies_raw:
        _legacy_e = st.get("enemy")
        enemies_raw = [_legacy_e] if isinstance(_legacy_e, dict) else []
    # 敌方：旧怪 dict（可能带 lv）→ battle2 enemy actor
    enemy_actors = []
    for i, m in enumerate(enemies_raw or []):
        if not isinstance(m, dict):
            continue
        enemy_actors.append(monster_to_actor(m, i))
    # 玩家 actor：player dict（命令层当前数据）→ actor，旧战斗状态灌入
    player_actors = []
    p_actor = player_to_actor(player) if player is not None else None
    if p_actor is not None:
        # 旧档玩家状态 → actor 字段
        for old_k, actor_k in _OLD_PSTATE_TO_ACTOR.items():
            if old_k in st and st[old_k] is not None:
                p_actor[actor_k] = st[old_k]
        # 旧档玩家状态 → actor.state（叠层/资源平铺）
        state = p_actor.setdefault("state", {})
        for old_k in ("mech_stacks", "resources", "eff_data"):
            if old_k in st and isinstance(st[old_k], dict):
                for k, v in st[old_k].items():
                    if k not in state:
                        state[k] = v
        player_actors.append(p_actor)
    # 战斗级元数据（旧 Battle dict 自定义键——battle2 不读，存 meta 给命令层）
    meta_keys = ("map", "name", "hp", "skills", "buffs", "debuffs", "dot_act",
                 "dot_res", "immune_dots", "adapt", "world_id", "map_name",
                 "player_hit", "first_attack_done", "death_pact_used",
                 "set_immune_used", "e_minions", "summons", "team_effects")
    meta = {}
    for k in meta_keys:
        if k in st and st[k] is not None:
            meta[k] = st[k]
    # 组 sides
    out = {
        "type": st.get("type", "monster"),
        "now": float(st.get("now", 0.0) or 0.0),
        "p_acts": int(st.get("p_acts", st.get("round", 0)) or 0),
        "result": st.get("result"),
        "winner_side": st.get("winner_side"),
        "sides": {"player": player_actors, "enemy": enemy_actors},
        "hostile_map": {},
        "title_bonus": dict(st.get("title_bonus") or {}),
        "killed": [],
        "flags": {},
        # 战斗级元数据（命令层读；battle2 引擎忽略）
        "meta": meta,
    }
    # 击杀记录（旧 killed_enemies uid 快照 → killed uid 列表；找不到实体就算了）
    _kills = []
    for _ke in (st.get("killed_enemies") or []):
        if isinstance(_ke, dict) and _ke.get("uid"):
            _kills.append(_ke["uid"])
    out["killed"] = _kills
    return out
