# -*- coding: utf-8 -*-
"""分阶段数值扫描（v156 v2.1/v2.2，鱼鱼点名"每个阶段"）：
玩家 5 阶段（P1-P5）DPS/HP/承伤 + 阶段增幅 + 怪物相对强度（击杀轮/Boss 单发占 HP）。

口径（计划 §一.5.2 / §一.6.3）：
  STAGES 5 阶段典型等级 + 档位装备；对同级 dps 怪（普通怪难度口径）。
  - player_row: 每职业 DPS/HP/承伤%（对同级 dps 怪单发占 HP）
  - growth_row: 每职业 DPS/HP 阶段增幅（相对上一阶段）
  - monster_row: 怪物面板（dps/elite/boss）+ 玩家 vs 怪物相对强度
      kills    = 玩家（当前档）对 dps 怪击杀轮（目标 4~6）
      kills_naked = 裸装对 dps 怪击杀轮（32 章三档难度锚点）
      boss_pct = Boss 单发占玩家 HP%（目标 8~12%；后期不得低于 5%）
      elite_pct = 精英单发占玩家 HP%（目标 5~8%）

验证：workspace/_verify_stages.py / _verify_monsters.py / _verify_monster_decision.py 原型。
"""
from .env import setup_env  # noqa: F401
from .constants import (
    STAGES, cls_id, cls_name, CLASSES,
    BOSS_HIT_PCT_MIN, BOSS_HIT_PCT_MAX,
)
from .player import PlayerOptions, build_player, per_action_dmg, sustained_dps
from .gear import gear_loadout
from .monster import build as build_monster, panel as monster_panel
from battle2.formulas import calc_damage

# 诗人 DPS 口径：终章爆发折算（纯辅助职业，无常规攻击技能；计划 §一.5.2 注 2）
POET_FINALE_MULT = 2.4   # 终章 2.4× 魔攻（v153 §7 文档口径）
POET_ACTIONS_PER_FINALE = 5.0   # 吟唱 5 层 ≈ 5 行动一轮爆发

# 怪物单发口径（与 team.py _boss_hit 对齐）：Boss 攻强乘区 enraged ×1.35 保守上限
BOSS_ATK_MULT = 1.35
ELITE_ATK_MULT = 1.20   # 精英攻强乘区保守（无狂暴，取较低档）


def _poet_dps(st: dict, mdef: int) -> float:
    """诗人 DPS 估算：终章爆发当量 / 5 行动（计划 §一.5.2 注 2，纯辅助职业）。"""
    d = calc_damage(int(st.get("matk", 0) * POET_FINALE_MULT), int(mdef),
                      variance=0.0, dmg_type="magi")
    return d / POET_ACTIONS_PER_FINALE


def _is_poet(cid: str) -> bool:
    return cid == "cls_shi_ren"


def _monster_hit(role: str, lv: int, pdef: int, pmdef: int,
                 atk_mult: float) -> float:
    """怪物单发期望伤害（物理/魔法取高者，攻强乘区保守）。"""
    m = build_monster(role, lv)
    d_phys = calc_damage(int(m.get("atk", 0) * atk_mult), int(pdef),
                           variance=0.0, dmg_type="phys")
    d_magi = calc_damage(int(m.get("matk", 0) * atk_mult), int(pmdef),
                           variance=0.0, dmg_type="magi")
    return max(d_phys, d_magi)


def player_dps(cls: str, lv: int, gear: dict, edef: int, mdef: int,
               opts: PlayerOptions | None = None,
               target_max_hp: float = 0.0, target_role: str = "dps") -> float:
    """单职业可持续 DPS（v161 口径：出手频率 × 单发 × 资源折算 × 机制期望 + DOT）。

    v174：诗人取消纯辅特判（_poet_dps 终章折算拍脑袋）——v174 块 C/D 给诗人补了
    真实输出轴（锁音/破音/共振/音刃 + 咏叹/挽歌分支拉高），诗人走正常 sustained_dps
    读 ROTATIONS，让 DPS 门禁反映真实战斗力。
    """
    opts = opts or PlayerOptions()
    return sustained_dps(cls_id(cls), lv, gear, edef, mdef, opts, potion_on=True,
                         target_max_hp=target_max_hp, target_role=target_role)


def stage_row(cls: str, stage: tuple, opts: PlayerOptions | None = None) -> dict:
    """单阶段单职业玩家行：{stage, lv, loadout, dps, hp, boss_pct, elite_pct}。

    boss_pct/elite_pct = Boss/精英单发占该职业 HP%（承伤压力；对同级怪）。
    """
    name, lv, loadout, *_ = stage
    cid = cls_id(cls)
    gear = gear_loadout(lv, loadout)
    m = build_monster("dps", lv)
    edef, mdef = m.get("def", 0), m.get("mdef", 0)
    dmg = player_dps(cid, lv, gear, edef, mdef, opts,
                     target_max_hp=m.get("max_hp", 0) or m.get("hp", 0))
    st = build_player(cid, lv, gear, opts, potion=0.0)
    hp = st.get("max_hp", 0)
    boss_hit = _monster_hit("boss", lv, st.get("def", 0), st.get("mdef", 0),
                            BOSS_ATK_MULT)
    elite_hit = _monster_hit("elite", lv, st.get("def", 0), st.get("mdef", 0),
                             ELITE_ATK_MULT)
    return {
        "stage": name, "lv": lv, "loadout": loadout,
        "dps": round(dmg, 1), "hp": hp,
        "boss_pct": round(boss_hit / max(hp, 1) * 100, 2),
        "elite_pct": round(elite_hit / max(hp, 1) * 100, 2),
    }


def stage_scan(cls: str, opts: PlayerOptions | None = None) -> dict:
    """5 阶段玩家扫描：{stages: [player_row...], growth: [growth_row...]}。

    growth = 每阶段 DPS/HP 增幅（相对上一阶段；P1 无增幅）。
    """
    rows = [stage_row(cls, s, opts) for s in STAGES]
    growth = []
    for i in range(1, len(rows)):
        prev, cur = rows[i - 1], rows[i]
        growth.append({
            "from": f"{prev['stage']} Lv{prev['lv']}",
            "to": f"{cur['stage']} Lv{cur['lv']}",
            "dps_x": round(cur["dps"] / max(prev["dps"], 1), 2),
            "hp_x": round(cur["hp"] / max(prev["hp"], 1), 2),
        })
    return {"stages": rows, "growth": growth}


def monster_scan(cls: str = "cls_zhan_shi",
                 opts: PlayerOptions | None = None) -> dict:
    """怪物相对强度扫描：5 阶段玩家（战士蓝装基准）vs 同级怪物。

    返回 {stages: [{stage, lv, loadout, dps, hp, kills, kills_naked,
                    boss_pct, elite_pct, boss_atk, boss_hp, norm_hp, elite_hp}]}
    kills       = 当前档位对 dps 怪击杀轮（满装/阶段档，快刷视角）
    kills_naked = 裸装对 dps 怪击杀轮（32 章三档难度锚点：4~6 轮）
    boss_pct    = Boss 单发占 HP%（8~12%）
    elite_pct   = 精英单发占 HP%（5~8%）
    """
    cid = cls_id(cls)
    out = []
    for name, lv, loadout, *_ in STAGES:
        gear = gear_loadout(lv, loadout)
        m = build_monster("dps", lv)
        edef, mdef = m.get("def", 0), m.get("mdef", 0)
        dmg = player_dps(cid, lv, gear, edef, mdef, opts,
                         target_max_hp=m.get("max_hp", 0) or m.get("hp", 0))
        st = build_player(cid, lv, gear, opts, potion=0.0)
        hp = st.get("max_hp", 0)
        # 裸装战士（关乘区，纯裸）对 dps 怪
        opts_naked = PlayerOptions(attr_points=True, tier=False, evolve=False,
                                   skills=False, affixes=False, enchant=False,
                                   potion=False)
        st_naked = build_player(cid, lv, {}, opts_naked, potion=0.0)
        dmg_naked = per_action_dmg(cid, lv, {}, edef, mdef, opts_naked,
                                   potion_on=False)
        boss_hit = _monster_hit("boss", lv, st.get("def", 0), st.get("mdef", 0),
                                BOSS_ATK_MULT)
        elite_hit = _monster_hit("elite", lv, st.get("def", 0), st.get("mdef", 0),
                                 ELITE_ATK_MULT)
        mb = monster_panel("boss", lv)
        mn = monster_panel("dps", lv)
        me = monster_panel("elite", lv)
        out.append({
            "stage": name, "lv": lv, "loadout": loadout,
            "dps": round(dmg, 1), "hp": hp,
            "kills": round(mn["max_hp"] / max(dmg, 1), 2),
            "kills_naked": round(mn["max_hp"] / max(dmg_naked, 1), 2),
            "boss_pct": round(boss_hit / max(hp, 1) * 100, 2),
            "elite_pct": round(elite_hit / max(hp, 1) * 100, 2),
            "boss_atk": mb.get("atk", 0), "boss_hp": mb.get("max_hp", 0),
            "norm_hp": mn.get("max_hp", 0), "elite_hp": me.get("max_hp", 0),
        })
    return {"stages": out}
