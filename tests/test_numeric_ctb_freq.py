# -*- coding: utf-8 -*-
"""N02 任务卡·交付 1：CTB 行动频率测试（防站桩回归）

目的：锁定 CTB 行动时间轴频率比——当前 15 倍是已知失衡基线，
      （spd 差 2.3 倍 → 频率差 15 倍）锁定现状 + 注释，CTB 修复后收紧断言。

CTB 参考公式（game/battle.py v121）：
  - 玩家 ct 初始 = -spd_p；敌方单位 ct 初始 = -spd_e（快者先手）
  - 玩家行动：p_ct += 100/有效spd_p；敌方存活单位 ct -= 100/有效spd_p
  - 敌方行动段（_enemy_phase）：while 敌方存活中最小 ct < p_ct → 该单位行动；
    行动后自身 ct += 100/有效spd_e，玩家 ct -= 100/有效spd_e（含连动，硬上限 8 次）
  - 有效 spd = min(spd, SPD_CT_CAP=80)
  ⇒ 玩家每次行动使「p_ct - 敌方ct」收窄 2×cost_p；敌方行动使差距拉大 cost_p+cost_e

⚠️ 失衡基线（spd 72 vs 31）：
  理论首次出手比 = ceil((spd_p - spd_e) / (2×cost_p)) = ceil(41 / (2×1.389)) = 15
  → 玩家先白打 15 个回合，怪全程站桩，实测 20 回合怪仅行动 3 次（6.67:1）。
  修复目标 ≤ 3:1（同卡 FRAMEWORK.md：当前基线 = 当前代码锁定，修复由主 agent 统一更新断言）。

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
            first[0] = b._next_turn
        return orig(self, player2, unit)

    BT.Battle._enemy_turn = counting
    try:
        for i in range(1, rounds + 1):
            if b.result:
                break
            b._next_turn = i
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
    # v130.10 绝对时刻 CTB 修复：频率线性（spd72 vs 31 → 理论 2.32:1），无站桩
    check("✅ 20 回合怪行动 == 8 次（线性频率实测）", ea_a == 8, f"ea={ea_a}")
    check("✅ 首次怪动在第 3 次玩家行动后（无 15 回合站桩）",
          first_a == 3, f"first={first_a}")
    check("✅ 频率比 2.50:1 ≤ 3:1 修复目标（达标）",
          ratio_a <= 3.0, f"ratio={ratio_a:.2f}")

    print("【CTB 行动频率 · 场景② 全力刺客：spd41 vs spd31】")
    pb = mk_player("cls_ci_ke", 11, {"str": 39})
    mb = mk_monster("m_ctb_s41", "dps", 22)
    st_b = E.player_final_stats("cls_ci_ke", 11, {}, 0, {"str": 39})
    check("面板前置：玩家 spd == 41（刺客11级39全力）", st_b["spd"] == SPD_B, f"spd={st_b['spd']}")
    ea_b, _ = run_freq(pb, mb)
    ratio_b = ROUNDS / ea_b
    print(f"  📊 20 回合怪行动次数 = {ea_b}，频率比 = 20/{ea_b} ≈ {ratio_b:.2f}:1")
    check("锁定现状：20 回合怪行动 == 15 次（全力刺客实测）", ea_b == 15, f"ea={ea_b}")

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