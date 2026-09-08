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
# 战斗回写（battle2 actor → 命令层 player dict）
# ============================================================

# 战斗后需要同步回 player dict 的面板当前值（hp/mp 战斗中被引擎改动，
# 命令层 db.update_player / 展示页读的是 player dict——旧引擎引用传递
# 自动同步；battle2 actor 是副本，命令层行动后必须显式回写）。
_BACK_SYNC_SCALARS = (
    "hp", "mp", "max_hp", "max_mp",
)

# 战斗可变状态键（actor → player dict 同构回写；玩家 buffs/shields/state 等
# 战斗内由引擎维护在 actor 上，战斗结束/展示前回写 player 保证命令层读得到）。
_BACK_SYNC_BAGS = (
    "buffs", "debuffs", "shields", "cooldown", "hot", "charging", "defending",
    "ct", "poi_buff", "state",
    # 旧玩家 dict 兼容键（职业层可能在 player 上读，见 _PLAYER_PASSTHROUGH）
    "resources", "stacks", "eff", "food_effects", "buff_hits",
    "last_element", "v139_modes", "v139_charge", "overflow_shield_cd",
    "stealth_atk", "reduce_all_left", "reduce_left",
    "combo_seq", "last_combo_tag", "tailwind_prev_energy",
)


def sync_player_from_actor(player: dict, actor: dict) -> dict:
    """battle2 actor 战斗后状态 → player dict 回写（命令层行动后调用）。

    旧 Battle 构造时把 player dict 直接当 _focus 引用，引擎内 hp/buffs 改动
    自动落在 player dict 上；battle2 的 player actor 是 make_actor 副本，
    命令层在每次 human_act / 战斗结束结算前调用本函数，把战斗结果同步回
    player dict，后续 db.update_player / 展示面板读到的才是最新值。

    返回 player（原地回写后同一引用；player 为空 dict 时也安全）。
    """
    player = player if isinstance(player, dict) else {}
    actor = actor if isinstance(actor, dict) else {}
    if not actor:
        return player
    for k in _BACK_SYNC_SCALARS:
        if actor.get(k) is not None:
            player[k] = actor[k]
    for k in _BACK_SYNC_BAGS:
        if k in actor and actor[k] is not None:
            player[k] = actor[k]
    return player

