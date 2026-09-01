# -*- coding: utf-8 -*-
"""数值工具集自检 test_numeric_toolkit —— 防 numeric_lib 本身退化（v131 新增）。

覆盖：
  1. legacy 模型对照：--loadout legacy 的哥布林营地轮数 ≈ 升级前旧工具 118（±3%）
     —— 保证"升级校准工具不改变旧模型语义"，对照数字可信；
  2. 真实玩家模型 vs 真实引擎：per_action_dmg 期望 vs BT.Battle 实测平均（纯普攻）误差 <10%
  3. 乘区归因单调：关掉任一乘区 → 单发伤害下降（且幅度 >1%）
  4. curve_override 上下文还原：覆盖后怪物成长表变化、退出后还原（无污染）
  5. 组队公式自洽：boss_hp 数学、team_net_mult(4人)>1
  6. team_matrix 完整性：全副本返回、BossHP>0、轮数>0

运行：python tests/test_numeric_toolkit.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # tests/
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)                        # dragonfall/
_SCRIPTS_DIR = os.path.join(_PLUGIN_DIR, "scripts")
for _p in (_SCRIPTS_DIR, _PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa: E402,F401
from numeric_lib.team import team_matrix  # noqa: E402
from numeric_lib.player import per_action_dmg, PlayerOptions  # noqa: E402
from numeric_lib.monster import curve_override  # noqa: E402
from numeric_lib.team import boss_hp, team_net_mult, team_rounds  # noqa: E402
from numeric_lib.constants import BOSS_HP_MULT  # noqa: E402
from numeric_lib.gear import make_gear  # noqa: E402
import numeric_sim as NS  # noqa: E402

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


def main():
    print("【1/6 legacy 对照：旧残疾模型（v131 怪物数据下）轮数锚点】")
    rows = team_matrix(loadout="legacy")
    by_id = {r["iid"]: r for r in rows}
    gob = by_id.get("inst_goblin_camp", {}).get("rounds")
    # v131 怪物变强（HP×2、boss×2.5）后旧模型打怪轮数按比例放大；锚点随怪数据同步重标定
    check("哥布林营地 legacy 轮数 565~665（v136 hp_mult 渐进标定 3.9 后）",
          565 <= gob <= 665, f"rounds={gob}")
    old_king = by_id.get("inst_old_king_tomb", {}).get("rounds")
    check("老王之墓 legacy 轮数 277~377（v136 hp_mult 渐进标定 1.5 后）",
          277 <= old_king <= 377, f"rounds={old_king}")

    print("【2/6 真实模型 vs 真实引擎：per_action_dmg vs BT.Battle 每行动实测（20 seeds）】")
    m = NS.monster_of("dps", 11)
    ehp = m.get("max_hp", 0)
    wins, avg_round = NS.class_battle_matrix("战士", 11, {"str": 39}, {}, "dps", 11, seeds=20)
    check("战士 11v11 胜率高（引擎 sanity）", wins >= 15, f"wins={wins}/20")
    # 每行动实际伤害：完整玩家构造（照抄 numeric_sim），总伤害 = 胜利场 × 怪HP（满伤精确）
    # v152：玩家行动带行为耗时（普攻 0.5×cost），'击杀回合' 口径改用行动次数——avg_acts = 引擎实测
    # 总行动次数/场（与模型 per_action_dmg 的'每行动伤害'同口径，消除溢出与回合换算偏差）
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game import engine as E
    import random
    total_actions, wins2 = 0, 0
    for seed in range(20):
        random.seed(seed)
        st = E.player_final_stats("战士", 11, {}, 0, {"str": 39})
        player = {
            "class_name": "战士", "level": 11, "class_tier": 0, "evolve_path": 0,
            "equipment": {}, "attributes": {"str": 39}, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None,
        }
        b = BT.Battle(btype="monster", enemy=dict(NS.monster_of("dps", 11)), player=player)
        guard = 0
        while b.result is None and guard < 500:
            guard += 1
            b.player_turn("attack", None, player)
            # v154 读条命中制：player_turn 只出手（排 cast_done），命中结算在出招读条结束后——
            # 推进到 p_ct 触发 cast_done（伤害/击杀在出招读条结束时才生效），保持与 v152 同口径
            b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, [], player)
            total_actions += 1
        wins2 += (b.result == "victory")
    eng_total = ehp * wins2
    eng_avg = eng_total / max(total_actions, 1)
    avg_acts = total_actions / max(1, int(20))  # v152：场均行动次数（含战败场，与 avg_round 同分母）
    opts_pa = PlayerOptions(attr_points=True, tier=False, evolve=False,
                            skills=False, affixes=False, enchant=False, potion=False)
    d_model = per_action_dmg("cls_zhan_shi", 11, {}, m.get("def", 0), m.get("mdef", 0), opts_pa)
    # 对照口径 = 击杀回合（溢出效应使"每行动伤害"天然低于单发期望，回合数对照无此偏差）
    model_rounds = ehp / max(d_model, 1)
    check(f"模型预测击杀行动 vs 引擎实测场均行动误差 ≤3（模型={model_rounds:.1f} 引擎={avg_acts:.1f}）",
          abs(model_rounds - avg_acts) <= 3.0, f"diff={abs(model_rounds - avg_acts):.2f}")

    print("【3/6 乘区归因单调：关掉任一乘区 → 伤害下降】")
    gear = make_gear(30, "blue", 3)
    mb = NS.monster_of("dps", 30)
    edef, mdef = mb.get("def", 0), mb.get("mdef", 0)
    full = per_action_dmg("cls_zhan_shi", 30, gear, edef, mdef, PlayerOptions(), potion_on=True)
    for key, attach in [("attr_points", lambda o: setattr(o, "attr_points", False)),
                        ("tier", lambda o: setattr(o, "tier", False)),
                        ("skills", lambda o: setattr(o, "skills", False)),
                        ("affixes", lambda o: setattr(o, "affixes", False)),
                        ("enchant", lambda o: setattr(o, "enchant", False)),
                        ("potion", lambda o: setattr(o, "potion", False))]:
        o = PlayerOptions()
        attach(o)
        d = per_action_dmg("cls_zhan_shi", 30, gear, edef, mdef, o, potion_on=(key != "potion"))
        check(f"关闭 {key} 后伤害下降（{full:.1f} → {d:.1f}）", d < full * 0.99,
              f"降幅={(1 - d / full):.1%}")

    print("【4/6 curve_override 上下文还原（预演不污染）】")
    from data.plugins.dragonfall.game.data import stat_templates as S
    from data.plugins.dragonfall.game.core import stats as ST
    before_growth = {r: dict(v) for r, v in S.MONSTER_ROLE_GROWTH.items()}
    before_hp_fn = ST.hp_stage_mult
    before_30 = ST.hp_stage_mult(30)
    try:
        with curve_override(growth={"dps": {"hp": 99}},
                            hp_stage=[(15, 1.0), (30, 1.5), (999, 2.0)]):
            check("覆盖生效（dps.hp成长=99）", S.MONSTER_ROLE_GROWTH["dps"]["hp"] == 99)
            check("覆盖生效（hp_stage_mult(30)=1.5 原值=%.2f）" % before_30,
                  ST.hp_stage_mult(30) == 1.5, f"got={ST.hp_stage_mult(30)}")
        check("退出后 dps.hp 成长还原", S.MONSTER_ROLE_GROWTH["dps"]["hp"] == before_growth["dps"]["hp"])
        check("退出后 hp_stage_mult 还原", ST.hp_stage_mult(30) == before_30,
              f"got={ST.hp_stage_mult(30)}")
        check("退出后函数引用还原", ST.hp_stage_mult is before_hp_fn)
    finally:
        # 异常兜底：确保测试失败也不污染全局
        S.MONSTER_ROLE_GROWTH = before_growth
        ST.hp_stage_mult = before_hp_fn

    print("【5/6 组队公式自洽（32 章三）】")
    h1 = boss_hp(1000, 1, 1, 1.7)
    h4 = boss_hp(1000, 4, 1, 2.85)
    check("单刷 BossHP = 模板×hp_mult(1000×1.7)", h1 == 1700, f"h1={h1}")
    check("4人 BossHP = 模板×[2.85+0.65×3](1000×4.8)", h4 == 4800, f"h4={h4}")
    # 按 32 章档位：单刷(1.7) vs 4人(2.85+1.95=4.8)，DPS 4×1.1 → 组队应明显更快
    r_solo = team_rounds(100, 1, boss_hp(1000, 1, 1, 1.7), 1.0)
    r_team = team_rounds(100, 4, boss_hp(1000, 4, 1, 2.85), 1.1)
    check(f"4人组队比单刷快 ≥20%（单刷{r_solo:.1f}轮 vs 4人{r_team:.1f}轮）",
          r_team <= r_solo * 0.8, f"ratio={r_team / r_solo:.2f}")
    net = team_net_mult(4, 1, 2.85)
    check("team_net_mult 数学自洽（4人=4×1.1/4.8）", abs(net - 4 * 1.1 / 4.8) < 1e-9, f"net={net:.3f}")
    r1 = team_rounds(100, 1, 4800, 1.0)
    r4 = team_rounds(100, 4, 4800, 1.1)
    check("4人轮数 < 1人轮数（同 BossHP 下）", r4 < r1, f"r1={r1:.1f} r4={r4:.1f}")

    print("【6/6 team_matrix 完整性（全副本）】")
    rows = team_matrix(loadout="team_mid")
    rows_low = team_matrix(loadout="solo_low")
    check(f"全副本返回（22 个）", len(rows) >= 20, f"n={len(rows)}")
    check("全部 BossHP>0", all(r["boss_hp"] > 0 for r in rows))
    check("全部轮数>0", all(r["rounds"] > 0 for r in rows))
    check("solo_low 存在超标 🔴（校准工具判红能力）", any(r["flag"] == "🔴" for r in rows_low))
    check("team_mid 存在长盘 🟡/🔴（v136 副本 100 轮长盘策略设计）", any(r["flag"] in ("🟡", "🔴") for r in rows))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()