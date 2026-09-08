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
    # 同构状态键透传（V 系列：effects 由 make_actor 播种，调用方按需填；
    # buffs/debuffs/hot/state 旧四键已废弃——透传只会造成脏残留，剔除）
    for k in ("shields", "cooldown", "charging", "defending",
              "ct", "poi_buff"):
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
    # 同构状态键透传（V 系列：effects/shields/cooldown；旧 buffs/debuffs/hot/state 废弃剔除）
    for k in ("shields", "cooldown", "charging",
              "defending", "ct"):
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
# 开战仪式（旧 Battle.__init__ 的玩家侧副作用 → 命令层开战前对 player dict 处理）
# ============================================================

def apply_player_battle_start(player: dict, actor: dict, db=None) -> dict:
    """把旧 Battle.__init__ 的玩家侧开战仪式结果应用到 battle2 actor。

    ⚠️ 本函数保持旧签名/语义的薄壳（命令层调用点可能传 actor）——推荐新调用方
    直接调 prepare_player_for_battle(player, title_bonus, db)（build_sides 前
    对 player dict 做仪式，build_sides 透传即得仪式后 actor）。

    目前实现（只做数据搬运，不触发引擎逻辑）：
    - echo_bless/poi_buff 从 event_state 消费写入 player dict（旧引擎构造时做）→
      actor 构造时已透传
    - 装备词条战斗开始效果（护盾/狼嚎/奥术屏障/起手资源/套装/weapon_effects）→
      属职业/装备层（上层模块），N5b 不复制旧 Battle 效果逻辑进桥——留 TODO 增量。

    返回 actor（原地补全后同一引用）。
    """
    prepare_player_for_battle(player, None, db)
    return actor


def prepare_player_for_battle(player: dict, title_bonus: Optional[dict] = None,
                              db=None) -> dict:
    """开战仪式（player dict 侧，build_sides 前调用）——纯数据搬运/事件消费。

    对齐旧 Battle.__init__ 的玩家侧副作用（只做不依赖 Battle 实例的部分；
    效果执行类属上层职业/装备模块，N5b 增量）：

    1. 战斗字段键播种（buffs/shields/state/cooldown/... 与旧引擎同构）
    2. max_hp/max_mp 实时重算（v95.19：DB max 是注册/升级快照，换装备后过时——
       战斗内面板/护盾 pct/heal clamp 以实时聚合值为准）
    3. echo_bless 消费（event_state bless_{qq_id} → player.buffs.echo_bless，一次性）
    4. 神龛祝福消费（event_state poi_buff_{qq_id} → player.poi_buff，left-1；用完删）
    5. v139 core_resource 配置注入（dual_form/focus/vent 挂 player，供上层读）

    ⚠️ 依赖红线：只 import game.engine / game.db（纯函数/存储层），
    绝不 import game.battle（旧引擎）——N6 删旧引擎后本桥必须能独立存活。

    返回 player（原地补全后同一引用）。
    """
    player = player if isinstance(player, dict) else {}
    if not player:
        return player
    # 1. 战斗字段播种（与旧 Battle.__init__ _seed 同款；actor 由 build_sides 透传）
    _seed_battle_keys(player)
    # 2. 面板实时化（不传 learned_skills——战斗侧被动由上层动态处理，防双算）
    try:
        from .. import engine as _E
        _cn = player.get("class_name") or "战士"
        _st = _E.player_final_stats(
            _cn, int(player.get("level", 1) or 1),
            player.get("equipment") or {},
            int(player.get("class_tier", 0) or 0),
            player.get("attributes"),
            int(player.get("evolve_path", 0) or 0),
            title_bonus or {},
            player.get("race"),
        )
        if _st.get("max_hp"):
            player["max_hp"] = int(_st["max_hp"])
        if _st.get("max_mp") is not None:
            player["max_mp"] = int(_st["max_mp"])
    except Exception:
        pass  # 面板重算失败不阻断开战（沿用 DB 值）
    # 3. echo_bless 消费（v97.4：探索事件写 event_state bless_{qid}，本场攻击 +5%，一次性）
    try:
        _qq = player.get("qq_id")
        if _qq and not (player.get("buffs") or {}).get("echo_bless"):
            _raw = (db or _default_db()).get_event_state(f"bless_{_qq}")
            if _raw:
                player.setdefault("buffs", {})["echo_bless"] = 1
                (db or _default_db()).set_event_state(f"bless_{_qq}", "")
    except Exception:
        pass
    # 4. 神龛祝福消费（v104 M23：poi_buff_{qid}，left-1；用完删 key，flee 也算消耗）
    try:
        _qq = player.get("qq_id")
        if _qq and not player.get("poi_buff"):
            _raw = (db or _default_db()).get_event_state(f"poi_buff_{_qq}")
            if _raw:
                import json as _json
                _pb = _json.loads(_raw)
                if isinstance(_pb, dict) and _pb.get("stat") in ("atk", "def", "spd") \
                        and int(_pb.get("left", 0) or 0) > 0:
                    player["poi_buff"] = {"stat": _pb["stat"],
                                          "mult": float(_pb.get("mult", 1.10)),
                                          "name": _pb.get("name", _pb["stat"])}
                    _pb["left"] = int(_pb["left"]) - 1
                    if _pb["left"] <= 0:
                        (db or _default_db()).delete_event_state(f"poi_buff_{_qq}")
                    else:
                        (db or _default_db()).set_event_state(
                            f"poi_buff_{_qq}", _json.dumps(_pb, ensure_ascii=False))
    except Exception:
        pass
    # 5. v139 配置注入（dual_form/focus/vent 定义挂 player；缺失 = 默认不启用）
    try:
        from .. import engine as _E139
        _crd = _E139.core_resource_def(player.get("class_name", "")) or {}
        for _mk in ("dual_form", "focus", "vent"):
            if _crd.get(_mk) and not player.get(_mk):
                player[_mk] = _crd[_mk]
    except Exception:
        pass
    return player


def _seed_battle_keys(player: dict) -> dict:
    """玩家战斗可变键播种（旧 Battle.__init__ 玩家侧 setdefault 全量）。"""
    _seeds = {
        "resources": dict, "stacks": dict, "eff": dict, "shields": dict,
        "cooldown": dict, "hot": dict, "food_effects": list,
        "buff_hits": dict, "combo_seq": list,
        "last_combo_tag": None, "last_element": None,
        "tailwind_prev_energy": None, "v139_modes": dict, "v139_charge": dict,
        "overflow_shield_cd": False, "stealth_atk": False,
        "reduce_all_left": 0, "reduce_left": 0,
        "buffs": dict, "poi_buff": None, "charging": None, "defending": False,
    }
    for _k, _ctor in _seeds.items():
        if _k not in player or player[_k] is None:
            player[_k] = _ctor() if callable(_ctor) else _ctor
    return player


def _default_db():
    """延迟取存储层（避免顶部循环 import）。"""
    from .. import db as _db
    return _db


# ============================================================
# 战斗回写（battle2 actor → 命令层 player dict）
# ============================================================

# 战斗后需要同步回 player dict 的面板当前值（hp/mp 战斗中被引擎改动，
# 命令层 db.update_player / 展示页读的是 player dict——旧引擎引用传递
# 自动同步；battle2 actor 是副本，命令层行动后必须显式回写）。
_BACK_SYNC_SCALARS = (
    "hp", "mp", "max_hp", "max_mp",
)

# 战斗可变状态键（actor → player dict 同构回写；V 系列：效果状态在 effects，
# shields/cooldown 独立容器，defending/charging/ct 行动状态——战斗内由引擎维护
# 在 actor 上，战斗结束/展示前回写 player 保证命令层读得到）。
_BACK_SYNC_BAGS = (
    "effects", "shields", "cooldown", "charging", "defending",
    "ct", "poi_buff",
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

