# -*- coding: utf-8 -*-
"""临时验证脚本：B（机制与数据层）重构后 enemy["debuffs"] 毒层叠层/免疫/毒爆。

契约 §3.1 实现验证：
1. _apply_mech_effect("poison", 2, ...) 叠毒 → battle.enemy["debuffs"]["poison"]["n"]==2
2. 免疫：enemy 带 immune_dots=["poison"] 时叠毒失败（不叠层、日志提示免疫）
3. 毒爆：n>=3 引爆后 debuffs 无 poison 且造成魔法伤害
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import battle as BT
from game.core import battle_mech as BM

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def mk_player():
    return {
        "class_name": "cls_ci_ke", "level": 30, "hp": 1000, "max_hp": 1000,
        "mp": 100, "max_mp": 200, "equipment": {}, "attributes": {"str": 10, "int": 10},
        "learned_skills": [], "race": "human",
    }


def mk_enemy(immune=None, hp=100000):
    e = {"name": "测试毒怪", "hp": hp, "max_hp": hp, "atk": 50, "def": 10,
         "mdef": 10, "spd": 10, "role": "normal"}
    if immune:
        e["immune_dots"] = list(immune)
    return e


def main():
    # ---- 1. 叠毒 ----
    print("===== 1. 叠毒写 enemy debuffs =====")
    p = mk_player()
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    b._last_player = p
    _ = b._apply_mech_effect("poison", 2, b.mech_stacks, 100, [], "淬毒", False,
                             {"name": "淬毒", "mech": "poison", "mech_chance": 1.0,
                              "mech_val": 2, "kind": "辅助"})
    deb = (b.enemy.get("debuffs") or {}).get("poison") or {}
    check("毒层 n==2", deb.get("n") == 2, f"n={deb.get('n')} debuffs={b.enemy.get('debuffs')}")
    check("mult==1.0（无被动）", deb.get("mult") == 1.0, f"mult={deb.get('mult')}")
    # 再叠 4 → min(5, 2+4)=5 封顶
    _ = b._apply_mech_effect("poison", 4, b.mech_stacks, 100, [], "淬毒", False,
                             {"name": "淬毒", "mech": "poison", "mech_chance": 1.0,
                              "mech_val": 4, "kind": "辅助"})
    deb2 = (b.enemy.get("debuffs") or {}).get("poison") or {}
    check("叠层封顶 cap 5", deb2.get("n") == 5, f"n={deb2.get('n')}")

    # ---- 2. 免疫 ----
    print("===== 2. immune_dots=['poison'] 免疫叠毒 =====")
    p2 = mk_player()
    b2 = BT.Battle("怪物", mk_enemy(immune=["poison"]), {}, p2)
    b2._last_player = p2
    logs2 = []
    _ = b2._apply_mech_effect("poison", 2, b2.mech_stacks, 100, logs2, "淬毒", False,
                              {"name": "淬毒", "mech": "poison", "mech_chance": 1.0,
                               "mech_val": 2, "kind": "辅助"})
    deb3 = (b2.enemy.get("debuffs") or {}).get("poison")
    check("免疫时未叠层", deb3 is None, f"debuffs={b2.enemy.get('debuffs')}")
    check("免疫提示日志", any("免疫中毒" in l for l in logs2), str(logs2))

    # ---- 3. 毒爆 n=3 ----
    print("===== 3. 毒爆 n=3 引爆清层+魔法伤害 =====")
    p3 = mk_player()
    b3 = BT.Battle("怪物", mk_enemy(hp=50000), {}, p3)
    b3._last_player = p3
    b3.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    hp_before = b3.enemy["hp"]
    logs3 = []
    _ = BM.MECH_EFFECTS["poison_burst"](b3, 1, b3.mech_stacks, 100, logs3, "毒爆", False)
    deb4 = (b3.enemy.get("debuffs") or {}).get("poison")
    check("引爆造成伤害", b3.enemy["hp"] < hp_before, f"{hp_before}->{b3.enemy['hp']}")
    check("引爆后清层（debuffs 无 poison）", deb4 is None, f"debuffs={b3.enemy.get('debuffs')}")
    # v1.1：毒爆改为物理段（atk×0.15×n 吃 def，dmg_type="phys"），日志标注物理伤害
    check("毒爆物理段日志", any("物理伤害" in l for l in logs3), str(logs3))

    # ---- 4. 毒爆 n=2 不引爆（阈值） ----
    print("===== 4. 毒爆 n=2 不引爆 =====")
    p4 = mk_player()
    b4 = BT.Battle("怪物", mk_enemy(hp=50000), {}, p4)
    b4._last_player = p4
    b4.enemy.setdefault("debuffs", {})["poison"] = {"n": 2, "mult": 1.0}
    hp_before4 = b4.enemy["hp"]
    logs4 = []
    _ = BM.MECH_EFFECTS["poison_burst"](b4, 1, b4.mech_stacks, 100, logs4, "毒爆", False)
    deb5 = (b4.enemy.get("debuffs") or {}).get("poison")
    check("n=2 不引爆（无伤害）", b4.enemy["hp"] == hp_before4, f"{hp_before4}->{b4.enemy['hp']}")
    check("n=2 保留层", deb5 is not None and deb5.get("n") == 2, str(b4.enemy.get('debuffs')))
    check("n=2 提示 ≥3", any("≥3" in l for l in logs4), str(logs4))

    # ---- 5. v1.1 叠毒日志含毒蚀提示 ----
    print("===== 5. v1.1 叠毒日志含毒蚀提示 =====")
    p5 = mk_player()
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    b5._last_player = p5
    logs5 = []
    _ = b5._apply_mech_effect("poison", 2, b5.mech_stacks, 100, logs5, "淬毒", False,
                              {"name": "淬毒", "mech": "poison", "mech_chance": 1.0,
                               "mech_val": 2, "kind": "辅助"})
    check("叠毒日志含毒蚀提示(-8%)", any("毒蚀" in l and "-8%" in l for l in logs5), str(logs5))
    check("叠毒日志毒蚀上限标注", any("上限20%" in l for l in logs5), str(logs5))

    # ---- 6. v1.1 叠灼烧 n≥3 易燃预备 + 灼爆易燃乘区 ----
    print("===== 6. v1.1 易燃预备 + 灼爆易燃乘区 =====")
    p6 = mk_player()
    b6 = BT.Battle("怪物", mk_enemy(hp=50000), {}, p6)
    b6._last_player = p6
    b6.enemy.setdefault("debuffs", {})["burn"] = {"n": 3, "mult": 1.0}
    logs6 = []
    _ = BM.MECH_EFFECTS["burn_burst"](b6, 1, b6.mech_stacks, 100, logs6, "灼爆", False)
    check("灼爆易燃日志[易燃]", any("易燃" in l for l in logs6), str(logs6))
    check("灼爆造成伤害", b6.enemy["hp"] < 50000, f"{50000}->{b6.enemy['hp']}")

    # ---- 7. v1.1 叠灼烧 n≥3 易燃预备日志 ----
    print("===== 7. v1.1 叠灼烧 n≥3 易燃预备 =====")
    p7 = mk_player()
    b7 = BT.Battle("怪物", mk_enemy(), {}, p7)
    b7._last_player = p7
    logs7 = []
    _ = b7._apply_mech_effect("burn", 3, b7.mech_stacks, 100, logs7, "火球术", False)
    check("叠灼烧 n≥3 日志含易燃预备(+10%)", any("易燃预备" in l and "+10%" in l for l in logs7), str(logs7))
    # n=2 应无易燃预备
    p7b = mk_player()
    b7b = BT.Battle("怪物", mk_enemy(), {}, p7b)
    b7b._last_player = p7b
    logs7b = []
    _ = b7b._apply_mech_effect("burn", 2, b7b.mech_stacks, 100, logs7b, "火球术", False)
    check("叠灼烧 n=2 无易燃预备", not any("易燃预备" in l for l in logs7b), str(logs7b))

    # ---- 8. v1.2 减益适应：连续叠毒 3 次 adapt==0.12，再叠至 cap 0.20 ----
    print("===== 8. v1.2 减益适应 poison =====")
    p8 = mk_player()
    b8 = BT.Battle("怪物", mk_enemy(), {}, p8)
    b8._last_player = p8
    b8.round = 1
    def _apply_poison(b_, mval=2):
        logs = []
        _ = b_._apply_mech_effect("poison", mval, b_.mech_stacks, 100, logs, "淬毒", False,
                                  {"name": "淬毒", "mech": "poison", "mech_chance": 1.0,
                                   "mech_val": mval, "kind": "辅助"})
        b_.round += 1
        return logs
    _apply_poison(b8)  # +4%
    _apply_poison(b8)  # +8%
    logs8_3 = _apply_poison(b8)  # +12%
    adapt8 = (b8.enemy.get("adapt") or {}).get("poison")
    check("连续叠毒 3 次 adapt==0.12", abs((adapt8 or 0.0) - 0.12) < 1e-6, f"adapt={adapt8}")
    check("叠毒日志含适应提示当前+12%", any("适应" in l and "+12%" in l for l in logs8_3), str(logs8_3))
    check("debuffs.poison.last_round 已写且==round",
          (b8.enemy.get("debuffs") or {}).get("poison", {}).get("last_round") == 3,
          str((b8.enemy.get("debuffs") or {}).get("poison", {})))
    # 继续叠到超过 0.20 → cap
    for _ in range(5):
        _apply_poison(b8)
    adapt8b = (b8.enemy.get("adapt") or {}).get("poison")
    check("适应 cap 0.20", abs((adapt8b or 0.0) - 0.20) < 1e-6, f"adapt={adapt8b}")

    # ---- 9. v1.2 灼烧适应同步（burn）+ 防刷：同型日志 ----
    print("===== 9. v1.2 减益适应 burn =====")
    p9 = mk_player()
    b9 = BT.Battle("怪物", mk_enemy(), {}, p9)
    b9._last_player = p9
    logs9 = []
    _ = b9._apply_mech_effect("burn", 1, b9.mech_stacks, 100, logs9, "火球术", False)
    adapt9 = (b9.enemy.get("adapt") or {}).get("burn")
    check("叠灼烧 1 次 adapt==0.04", abs((adapt9 or 0.0) - 0.04) < 1e-6, f"adapt={adapt9}")
    check("灼烧叠层日志含适应提示", any("适应" in l for l in logs9), str(logs9))

    # ---- 10. v1.2 _b_phase 阶段转换清 debuffs/adapt ----
    print("===== 10. v1.2 _b_phase 阶段转换清层 =====")
    p10 = mk_player()
    e10 = mk_enemy(hp=4000)
    e10["phase_count"] = 0
    e10["hp"] = 1500  # 15% 血 → 越过 50% 阈值触发阶段 1
    b10 = BT.Battle("怪物", e10, {}, p10)
    b10.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0, "last_round": 1}
    b10.enemy["adapt"] = {"poison": 0.12, "burn": 0.08}
    b10.round = 2
    logs10 = []
    _ = BM.BOSS_MECHS["phase"](b10, logs10, b10.enemy, b10.round)
    check("阶段转换后 debuffs 清空", not (b10.enemy.get("debuffs") or {}), str(b10.enemy.get("debuffs")))
    check("阶段转换后 adapt 清空", not (b10.enemy.get("adapt") or {}), str(b10.enemy.get("adapt")))
    check("阶段转换净化日志", any("净化了身上的异常状态" in l for l in logs10), str(logs10))
    check("阶段转换 phase_count 递增", b10.enemy.get("phase_count") == 1, str(b10.enemy.get("phase_count")))

    print()
    print(f"===== 临时脚本结果: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
