# -*- coding: utf-8 -*-
"""A2 真引擎多技能循环模拟器 battle2 —— v175 平衡矩阵门禁：职业×流派×副本 Boss

背景：tests/numeric_sim.py 只能单技能/纯普攻模拟（class_battle_matrix），本模块扩展为
“多技能循环”真实引擎模拟器：按流派 rotation 顺序逐技能尝试施放（被 CD/蓝/资源拦截
→ 试下一个；全部拦截 → 普攻），跑真实 BT.Battle 直到分出胜负。

用法（见 battle_rotation docstring）：
    from numeric_lib import battle2
    boss = C.INSTANCES['inst_goblin_camp']['boss']   # 或取 C.INSTANCES[iid]['boss']
    battle2.battle_rotation('cls_zhan_shi', 20, 'solo_low', {'str': 66},
                            ['挥砍', '猛击', '破甲斩'], boss, seeds=8)

口径（与 numeric_sim.class_battle_matrix 对齐）：
  - 直接构造 BT.Battle(btype="monster", enemy=怪, player=玩家)，循环 player_turn
  - 固定种子序列 seed 0..N-1：每场先 random.seed(seed) 再建人开打（可复现）
  - 玩家 dict 完全对齐 numeric_sim：class_name/level/class_tier/evolve_path/
    equipment/attributes/learned_skills/hp/mp/max_hp/max_mp/race/title_bonus
  - class_tier/evolve_path 按 lv 算：lv>=90→tier3, >=60→tier2, >=30→tier1, else 0；
    evolve_path=1（攻线）
  - 技能拦截判定：player_turn 返回后 b._p_acts 不变 且 b.result is None
    （O118 前置校验拦截：技能不存在/未学习/冷却中/蓝不足/核心资源不足 →
    玩家刻不开始、敌方不行动；numeric_sim 121-124 行同款逻辑）
  - 击杀轮口径：b._tick_no()（numeric_sim 129 行同款）
  - 护栏 max_turns=500（numeric_sim._MAX_TURNS 同款）
"""
import os
import random
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # scripts/numeric_lib/
_SCRIPTS_DIR = os.path.dirname(_SCRIPT_DIR)                       # scripts/
_PLUGIN_DIR = os.path.dirname(_SCRIPTS_DIR)                       # dragonfall/
_TESTS_DIR = os.path.join(_PLUGIN_DIR, "tests")
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))  # qqbot/
for _p in (_QQBOT_DIR, _PLUGIN_DIR, _TESTS_DIR, _SCRIPTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS_DIR, "test_game_data.db"))

from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
try:  # noqa: E402
    from .gear import gear_loadout  # noqa: E402
except ImportError:  # 直接 python 跑本文件（无父包）→ scripts/ 已在 sys.path，按包名导入
    from numeric_lib.gear import gear_loadout  # noqa: E402

_MAX_TURNS = 500  # 单场回合护栏（numeric_sim._MAX_TURNS 同款；正常对局远低于此）


def tier_path_of(lv: int) -> tuple[int, int]:
    """玩家转职档位（照任务卡）：lv>=90→tier3, >=60→tier2, >=30→tier1, else 0；evolve_path=1（攻线）。"""
    return (3 if lv >= 90 else 2 if lv >= 60 else 1 if lv >= 30 else 0), 1


def attr_pts_total(lv: int) -> int:
    """自由属性点总量 = DEFAULT_ATTR_PTS(9) + (lv-1)×3（numeric_sim ATTR_PTS_TOTAL 同口径）。"""
    return C.DEFAULT_ATTR_PTS + (lv - 1) * 3


def boss_of(boss_def: tuple, warn: bool = True) -> dict:
    """boss 6 元组 (id, 名, role, lv, [技能ID], [掉落]) → C.build_monster 展开成怪 dict。

    地图 obj 带 area='instance'（副本口径：instance Boss atk 段乘区生效）。
    展开失败（个别 Boss 需特殊 map 对象）→ fallback numeric_sim.monster_of('boss', lv)。
    """
    try:
        bd = tuple(boss_def)
        if len(bd) < 6:
            raise ValueError("boss_def 需要 6 元组 (id, 名, role, lv, [技能], [掉落])，实际长度 %d" % len(bd))
        return C.build_monster(bd, {"id": bd[0], "name": bd[1], "area": "instance", "lv": bd[3]})
    except Exception as exc:  # noqa: BLE001 —— 展开失败 fallback，保持与 numeric_sim 同源可跑
        if warn:
            print("[battle2][警告] boss_def 展开失败(%s)，fallback numeric_sim.monster_of('boss', lv=%s)"
                  % (exc, boss_def[3] if len(boss_def) > 3 else "?"))
        from data.plugins.dragonfall.tests import numeric_sim as NS  # noqa: PLC0415
        return NS.monster_of("boss", boss_def[3] if len(boss_def) > 3 else 1)


def battle_rotation(cls_id: str, lv: int, loadout: str, attr: dict,
                    rotation: list[str], boss_def: tuple, boss_lv: int | None = None,
                    seeds: int = 8, max_turns: int = 500) -> dict:
    """真实引擎多技能循环 vs Boss：返回 {wins, avg_rounds, avg_survive}

    - cls_id: 'cls_zhan_shi' 等；loadout: 'solo_mid'/'team_purple9' 等（gear_loadout）；
    - attr: 加点 dict {'str': 全部分配...}（数值=该等级自由点，见下）；
    - rotation: 技能名列表（按施放优先级排序，玩家按此顺序尝试，都不可用→普攻）；
    - boss_def: instances.py boss 6 元组 (id, 名, role, lv, [技能], [掉落]) 或 C.INSTANCES[iid]['boss']；
    - 玩家 class_tier/evolve_path 按 lv 算：lv>=90→tier3, >=60→tier2, >=30→tier1, else 0；
      evolve_path=1（攻线）
    - wins: seeds 场中胜利场数；avg_rounds: 胜利场平均击杀轮；avg_survive: 失败场平均存活轮
    """
    seeds = max(1, int(seeds or 8))
    max_turns = int(max_turns or _MAX_TURNS)
    tier, path = tier_path_of(int(lv))
    equip = gear_loadout(int(lv), loadout)
    st = E.player_final_stats(cls_id, int(lv), equip, tier, dict(attr or {}), evolve_path=path)

    # 玩家 dict 完全对齐 numeric_sim.class_battle_matrix 模板
    player = {
        "class_name": cls_id, "level": int(lv), "class_tier": tier, "evolve_path": path,
        "equipment": equip, "attributes": dict(attr or {}), "learned_skills": list(rotation),
        "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
        "race": "human", "title_bonus": None,
    }
    boss = boss_of(boss_def)

    wins = 0
    rounds_sum = 0.0
    survive_sum = 0.0
    loses = 0
    for seed in range(seeds):
        random.seed(seed)  # 固定种子序列 seed 0..N-1，可复现（与 numeric_sim 同款）
        # 每场重建敌方与玩家副本（战斗内 hp/mp 会被改；模板保持一致）
        b = BT.Battle(btype="monster", enemy=dict(boss), player=dict(player))
        turns = 0
        while b.result is None and turns < max_turns:
            acted = False
            # 按 rotation 顺序逐个试技能：被拦截（_p_acts 不变 & result 空）→ 试下一个
            for skill_name in rotation:
                prev_acts = b._p_acts
                b.player_turn("skill", skill_name, player)
                if b._p_acts != prev_acts:
                    acted = True     # 施放成功 → 本回合结束
                    break
                if b.result is not None:
                    break            # 技能路径中分出胜负（如处决类特技/反击）
            else:
                # 全部技能被拦截 → 普攻（numeric_sim 121-124 行同款转普攻逻辑）
                b.player_turn("attack", None, player)
                acted = True
            if b.result is not None:
                break
            turns += 1
        _ = acted
        if b.result == "victory":
            wins += 1
            rounds_sum += b._tick_no()
        else:
            # defeat / 超时护栏兜底都算未胜（存活轮口径 = _tick_no）
            loses += 1
            survive_sum += b._tick_no()
    return {
        "wins": wins,
        "avg_rounds": round(rounds_sum / max(wins, 1), 2),
        "avg_survive": round(survive_sum / max(loses, 1), 2),
        "seeds": seeds,
    }


def expect_vs_actual(cls_id: str, lv: int, loadout: str, attr: dict,
                     rotation: list[str], boss_def: tuple, seeds: int = 8) -> dict:
    """占位：主 agent 的期望模型跑完后填对比；先返回 battle_rotation 结果 + expect_kill=None。"""
    res = battle_rotation(cls_id, lv, loadout, attr, rotation, boss_def, seeds=seeds)
    res["expect_kill"] = None
    return res


if __name__ == "__main__":
    # 自检示例：战士 cls_zhan_shi vs 哥布林营地 boss（rotation 挥砍/猛击/破甲斩）
    from data.plugins.dragonfall.game.data import instances as _INST
    _boss = _INST.INSTANCES["inst_goblin_camp"]["boss"]
    _lv, _pts = 20, attr_pts_total(20)
    print("战士 lv%s loadout=solo_low 自由点=%s rotation=挥砍/猛击/破甲斩 vs 哥布林酋长·咕噜(lv%s)"
          % (_lv, _pts, _boss[3]))
    _r = battle_rotation("cls_zhan_shi", _lv, "solo_low", {"str": _pts},
                         ["挥砍", "猛击", "破甲斩"], _boss, seeds=8)
    print("结果:", _r)
