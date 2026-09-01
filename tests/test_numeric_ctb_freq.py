# -*- coding: utf-8 -*-
"""N02 任务卡·交付 1：CTB 行动频率测试（防站桩回归）

目的：锁定 CTB 行动时间轴频率比——当前 15 倍是已知失衡基线，
      （spd 差 2.3 倍 → 频率差 15 倍）锁定现状 + 注释，CTB 修复后收紧断言。

CTB 参考公式（game/battle.py v154 读条命中制）：
  - 玩家行动：出招（cast_done 命中结算）→ 收招；p_ct = 出手时刻 + 出招 + 收招
  - 敌方行动：_enemy_turn 排 cast_done（出招读条结束才命中结算），ct 同理
  - 速度折算：出招/收招各 × (SPD_REF / 实际速度)，SPD_REF=50；速度 50 = 基准耗时
  - v154 语义：无恢复间隔——速度只影响出招/收招快慢，频率比 = 双方出招耗时比
  - 职业普攻 cast_atk（v154 减半）：刺客 0.35s / 游侠 0.4s / 拳师 0.3s / 战士 0.7s / 牧师 0.6s / 法师 1.0s
  - 敌方普攻 cast 缺省 = CAST_ATK = 1.0（@spd50）

⚠️ v154 失衡基线（spd 72 vs 31，刺客 0.35s 快匕）：
  玩家出招 = 0.35×(50/72) = 0.243s；怪出招 = 1.0×(50/31) = 1.613s
  → 出手比 = 1.613/0.243 = 6.64:1（怪永远在读条，玩家每 6~7 动怪才命中 1 次）
  理论 20 回合怪动 = 20×0.243/1.613 = 3.01 ≈ 实测 3 次。修复目标 ≤ 3:1（同卡 FRAMEWORK.md）。

场景：
  ① 玩家 spd 72（刺客 11 级 39 全敏）vs 怪 spd 31（22 级 dps）→ 锁定失衡实测
  ② 玩家 spd 41（刺客 11 级 39 全力）vs 怪 spd 31 → 锁定实测（近同级）
  ③ 同级对抗：游侠 11 级 spd 34 vs 26 级 dps 怪 spd 35（spd 差 1）→ 频率比 ≤ 3 正常区

运行：python tests/test_numeric_ctb_freq.py（exit=0 全绿）
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, E, BT  # noqa: E402

passed = failed = 0
ROUNDS = 20          # 模拟回合数（玩家行动次数）
SPD_A = 72           # 刺客 11 级 39 全敏（实测面板）
SPD_B = 41           # 刺客 11 级 39 全力
SPD_E = 31           # 22 级 dps 怪


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls, lv, attr):
    """FRAMEWORK.md 玩家 dict 构造（真实 E.player_final_stats 派生属性）。"""
    st = E.player_final_stats(cls, lv, {}, 0, attr)
    return {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": {}, "attributes": attr, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None}


def mk_monster(mid, role, lv):
    """FRAMEWORK.md 怪构造（真实 C.build_monster，lv_jitter=0 确定性）。"""
    return C.build_monster((mid, "数值测试怪", role, lv, [], []),
                           {"id": mid, "name": "数值测试图", "area": "field"})


def run_freq(player, enemy, rounds=ROUNDS, seed=0):
    """模拟 rounds 次玩家行动，返回 (怪行动次数, 首次怪动所需玩家行动次数)。

    计数只做观测包装（不改任何公式/数值）：包一层 _enemy_turn 计数后仍调原实现。
    每回合回满双方 hp——本测试只测行动频率，不测胜负（失衡测试里怪会打死/被玩家打死）。
    固定种子序列保证可复现。
    """
    random.seed(seed)
    b = BT.Battle(btype="monster", enemy=enemy, player=player)
    orig = BT.Battle._enemy_turn
    cnt, first = [0], [None]

    def counting(self, player2, unit):
        cnt[0] += 1
        if first[0] is None:
            first[0] = b._p_acts
        return orig(self, player2, unit)

    BT.Battle._enemy_turn = counting
    try:
        for i in range(1, rounds + 1):
            if b.result:
                break
            player["hp"] = player["max_hp"]
            enemy["hp"] = enemy["max_hp"]
            b.player_turn("attack", None, player)
    finally:
        BT.Battle._enemy_turn = orig
    return cnt[0], (first[0] or rounds + 1)


def main():
    print("【CTB 行动频率 · 场景① 失衡基线：刺客 spd72 vs 22级dps怪 spd31】")
    pa = mk_player("cls_ci_ke", 11, {"agi": 39})
    ma = mk_monster("m_ctb_s72", "dps", 22)
    st_a = E.player_final_stats("cls_ci_ke", 11, {}, 0, {"agi": 39})
    check("面板前置：玩家 spd == 72（刺客11级39全敏）", st_a["spd"] == SPD_A, f"spd={st_a['spd']}")
    check("面板前置：怪 spd == 31（22级dps）", ma["spd"] == SPD_E, f"spd={ma['spd']}")
    ea_a, first_a = run_freq(pa, ma)
    ratio_a = ROUNDS / ea_a
    print(f"  📊 20 回合怪行动次数 = {ea_a}，首次怪动在第 {first_a} 次玩家行动后，频率比 = 20/{ea_a} ≈ {ratio_a:.2f}:1")
    # v130.10 绝对时刻 CTB 修复：频率线性（spd72 vs 31 → 理论 1.67:1），无站桩
    # v152 行动耗时制实测：20 回合玩家行动 → 怪 11 动（理论 = (40/31+1.0)/(40/72+1.0) ≈ 1.63:1 → 12.3 动）
    # v154 读条命中制重标定：速度=出招+收招（无恢复间隔）。刺客 cast_atk=0.35（spd72→×0.694=0.243s），
    #   怪普攻 cast=CAST_ATK=1.0（spd31→×1.613=1.613s）。理论出手比 = 1.613/0.243 = 6.64:1
    #   → 20 回合怪动理论 = 20×0.243/1.613 = 3.01 ≈ 实测 3 次（怪永远在读条，玩家每 6~7 动怪才命中 1 次）
    check("20 回合怪行动 == 3 次（v154 读条命中制实测）", ea_a == 3, f"ea={ea_a}")
    check("首次怪动在第 7 次玩家行动后（v154 实测：玩家出招 0.24s vs 怪出招 1.61s）",
          first_a == 7, f"first={first_a}")
    check("频率比 6.67:1（v154 实测，线性于出招耗时比，非旧 15 倍失衡）",
          ratio_a <= 8.0, f"ratio={ratio_a:.2f}")

    print("【CTB 行动频率 · 场景② 全力刺客：spd41 vs spd31】")
    pb = mk_player("cls_ci_ke", 11, {"str": 39})
    mb = mk_monster("m_ctb_s41", "dps", 22)
    st_b = E.player_final_stats("cls_ci_ke", 11, {}, 0, {"str": 39})
    check("面板前置：玩家 spd == 41（刺客11级39全力）", st_b["spd"] == SPD_B, f"spd={st_b['spd']}")
    ea_b, _ = run_freq(pb, mb)
    ratio_b = ROUNDS / ea_b
    print(f"  📊 20 回合怪行动次数 = {ea_b}，频率比 = 20/{ea_b} ≈ {ratio_b:.2f}:1")
    # v154 重标定：全力刺客 spd41 → 出招 0.35×(50/41)=0.427s；怪 spd31 出招 1.613s
    # 理论出手比 = 1.613/0.427 = 3.78:1 → 20 回合怪动理论 = 20×0.427/1.613 = 5.29 ≈ 实测 5 次
    check("锁定现状：20 回合怪行动 == 5 次（v154 读条命中制实测）", ea_b == 5, f"ea={ea_b}")

    print("【CTB 行动频率 · 场景③ 同级对抗：游侠 spd34 vs 26级dps怪 spd35（正常区）】")
    pc = mk_player("cls_you_xia", 11, None)
    mc = mk_monster("m_ctb_equal", "dps", 26)
    st_c = E.player_final_stats("cls_you_xia", 11, {}, 0, None)
    check("面板前置：玩家 spd == 34 / 怪 spd == 35（spd 差 1）",
          st_c["spd"] == 34 and mc["spd"] == 35, f"p={st_c['spd']} e={mc['spd']}")
    ea_c, _ = run_freq(pc, mc)
    ratio_c = ROUNDS / ea_c
    print(f"  📊 20 回合怪行动次数 = {ea_c}，频率比 = 20/{ea_c} ≈ {ratio_c:.2f}:1")
    check("同级对抗频率比 ≤ 3（正常区）", ratio_c <= 3.0, f"ratio={ratio_c:.2f}")
    check("同级对抗怪行动次数 ≥ 玩家 1/3（20 回合 ≥ 7 次）", ea_c >= 7, f"ea={ea_c}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()