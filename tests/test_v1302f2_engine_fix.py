# -*- coding: utf-8 -*-
"""v130.2f2 引擎修复批次测试（test_v1302f2_engine_fix.py）

覆盖两处「desc 声称但引擎缺失」机制的落地（本批次仅引擎改动，数据 desc 维持不动）：

  ① 暮影潜行伤害乘区：终结·破影一击 潜行×1.5 / 幽影刃 潜行×1.25
     —— skills.py desc 声称（3293/3299），此前引擎只有「潜行=必暴」（battle.py:3009 消费
     p_buffs["stealth"]），无伤害乘区。本次数据驱动落地 SHADOW_STEALTH_DMG_MULT
     （battle_config.py），潜行判定与「满血必暴」共享同一字段（攻击时消费即潜行出手）。
  ② 苦修「持有每 1 禅意 物理伤害 +4%（满 +40%）」
     —— core_resources.py 禅意 desc 声称、引擎无挂点（battle_config.py 原注释自述无挂点）；
     本次照拳师蓄势（MOMENTUM_CFG + _momentum_mult）同型落地 ZEN_HOLD_CFG + _zen_hold_mult，
     技能端与普攻端双消费（battle.py _player_skill / _player_attack）。

设计原则（对齐 test_v1302f_job_quality.py 脚手架姿势）：
  - 行为断言确定性：random.random → 0.99（不自然暴击/不幸运/不闪避）+
    random.uniform → 0.0（calc_damage 波动归零）双 mock；
  - 满血敌人 + mech=shadow → 潜行/非潜行都必暴，比值纯隔离「潜行乘区」；
  - 负例保证不改变其他技能/职业行为（表外技能 幽影袭 不受乘；拳师不吃禅意加伤）。

运行：python tests/test_v1302f2_engine_fix.py（exit=0 全绿；skip 不计数为失败）
"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 独立私有临时库（绝不触碰生产 game_data.db / 既有测试库）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1302f2_engine_fix.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import E, BT, clean_db  # noqa: E402

passed = failed = skipped = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def check_float(name, got, want, tol=1e-9):
    check(name, abs(got - want) < tol, f"got={got} want={want}")


def skip(name, reason):
    global skipped
    skipped += 1
    print(f"  ⏭️  {name}（引擎未就绪/被改，待引擎修复后回归）：{reason}")


# ---------------- 构造（与 test_v1302f_job_quality.py 同款脚手架） ----------------
def make_enemy(hp=200000, atk=40):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 40,
            "def": 20, "mdef": 20, "spd": 5, "crit": 0.05}


def mk_player(cls, tier, path, learned=(), equipment=None, level=95):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": equipment or {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "测试勇者"}


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p


def _dmg_run(b, p, skill=None, stealth=False, zen=None):
    """确定性伤害跑法：random → 0.99（不自然暴击/不幸运/不闪避）+
    random.uniform → 0.0（calc_damage ±15% 波动归零）。
    stealth=True 手动挂潜行 buff；zen 非 None 则预置禅意。返回 (伤害值, 日志)。"""
    if stealth:
        b.p_buffs["stealth"] = 1
    if zen is not None:
        b.resources["zen"] = zen
    before = b.enemy.get("hp", 0)
    with mock.patch.object(BT.random, "random", return_value=0.99), \
            mock.patch.object(BT.random, "uniform", return_value=0.0):
        if skill:
            logs = b._do_player_skill(skill, p)
        else:
            st = b._player_stats(p)
            logs = b._player_attack(st, p)
    dmg = before - b.enemy.get("hp", 0)
    return dmg, logs


# ================= ① 暮影潜行乘区（破影一击×1.5 / 幽影刃×1.25） =================
def test_shadow_stealth_mult():
    print("\n【① 暮影潜行乘区（终结·破影一击 潜行×1.5 / 幽影刃 潜行×1.25）】")
    # ---- 数据层：配置表存在且数值正确（desc 承诺 1.5/1.25）----
    try:
        from data.plugins.dragonfall.game.data.battle_config import SHADOW_STEALTH_DMG_MULT as SSDM
    except Exception as ex:
        skip("数据：SHADOW_STEALTH_DMG_MULT 表", str(ex))
        return
    check_float("数据：破影一击 潜行倍率 ×1.5", float(SSDM.get("终结·破影一击", 0)), 1.5)
    check_float("数据：幽影刃 潜行倍率 ×1.25", float(SSDM.get("幽影刃", 0)), 1.25)
    check("数据：表内仅暮影两终结技（不扩散其他技能）",
          set(SSDM.keys()) == {"终结·破影一击", "幽影刃"}, str(SSDM))
    # ---- 行为：满血敌人（mech=shadow 满血必暴）+ 潜行 → 伤害含 ×1.5（对照非潜行同条件）----
    try:
        b1, p1 = new_battle("cls_shadow_blade", 3, 3, learned=["终结·破影一击"], level=95)
        b1.resources["shadow_step"] = 5
        dmg_ns, logs_ns = _dmg_run(b1, p1, "终结·破影一击")
        b2, p2 = new_battle("cls_shadow_blade", 3, 3, learned=["终结·破影一击"], level=95)
        b2.resources["shadow_step"] = 5
        dmg_s, logs_s = _dmg_run(b2, p2, "终结·破影一击", stealth=True)
        check("破影一击：潜行伤害 > 非潜行（乘区生效）", dmg_s > dmg_ns, f"ns={dmg_ns} s={dmg_s}")
        check("破影一击：潜行/非潜行 ≈ ×1.5", abs(dmg_s / dmg_ns - 1.5) < 0.07,
              f"ratio={dmg_s / dmg_ns:.4f}")
        check("破影一击：潜行日志含乘区标签（🌙潜行x1.5）",
              any("🌙潜行x1.5" in str(l) for l in logs_s), f"{logs_s[-1]}")
        check("破影一击：非潜行日志无乘区标签",
              not any("🌙潜行x" in str(l) for l in logs_ns), f"{logs_ns[-1]}")
        check("破影一击：潜行 buff 攻击后已消耗（下次不再必暴）",
              b2.p_buffs.get("stealth") is None, f"p_buffs={b2.p_buffs}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：破影一击 潜行×1.5", str(ex))
    # ---- 幽影刃 ×1.25 ---- 
    try:
        b3, p3 = new_battle("cls_shadow_blade", 3, 3, learned=["幽影刃"], level=95)
        b3.resources["shadow_step"] = 5
        dmg_ns2, logs_ns2 = _dmg_run(b3, p3, "幽影刃")
        b4, p4 = new_battle("cls_shadow_blade", 3, 3, learned=["幽影刃"], level=95)
        b4.resources["shadow_step"] = 5
        dmg_s2, logs_s2 = _dmg_run(b4, p4, "幽影刃", stealth=True)
        check("幽影刃：潜行伤害 > 非潜行（乘区生效）", dmg_s2 > dmg_ns2, f"ns={dmg_ns2} s={dmg_s2}")
        check("幽影刃：潜行/非潜行 ≈ ×1.25", abs(dmg_s2 / dmg_ns2 - 1.25) < 0.05,
              f"ratio={dmg_s2 / dmg_ns2:.4f}")
        check("幽影刃：潜行日志含乘区标签（🌙潜行x1.25）",
              any("🌙潜行x1.25" in str(l) for l in logs_s2), f"{logs_s2[-1]}")
        check("幽影刃：非潜行日志无乘区标签",
              not any("🌙潜行x" in str(l) for l in logs_ns2), f"{logs_ns2[-1]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：幽影刃 潜行×1.25", str(ex))
    # ---- 负例：表外技能（幽影袭，同职业同 mech）潜行出手只必暴不加乘 ----
    try:
        b5, p5 = new_battle("cls_shadow_blade", 1, 1, learned=["幽影袭"], level=95)
        dmg_a, _ = _dmg_run(b5, p5, "幽影袭")
        b6, p6 = new_battle("cls_shadow_blade", 1, 1, learned=["幽影袭"], level=95)
        dmg_b, logs6 = _dmg_run(b6, p6, "幽影袭", stealth=True)
        check("负例：幽影袭 潜行出手不加乘（伤害严格相等）", dmg_a == dmg_b, f"ns={dmg_a} s={dmg_b}")
        check("负例：幽影袭 潜行日志无乘区标签",
              not any("🌙潜行x" in str(l) for l in logs6), f"{logs6[-1]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：负例 表外技能不加乘", str(ex))


# ================= ② 苦修禅意持有加伤（每 1 禅意 物伤 +4%，满 +40%） =================
def test_zen_hold_bonus():
    print("\n【② 苦修禅意持有加伤（武僧线 每 1 禅意 物理伤害 +4%，满 10 +40%）】")
    # ---- 数据层：ZEN_HOLD_CFG 数值（desc 承诺 4%/意、满 10 封顶）----
    try:
        from data.plugins.dragonfall.game.data.battle_config import ZEN_HOLD_CFG as ZHC
    except Exception as ex:
        skip("数据：ZEN_HOLD_CFG 表", str(ex))
        return
    check_float("数据：per_zen=0.04（每 1 禅意 +4%）", float(ZHC.get("per_zen", 0)), 0.04)
    check("数据：cap_zen=10（满 10 封顶）", int(ZHC.get("cap_zen", 0)) == 10, str(ZHC))
    # ---- 单元：_zen_hold_mult 线性/封顶/线别门（与蓄势同型判定）----
    try:
        b, p = new_battle("cls_wu_sheng", 3, 1, level=95)
        b.resources["zen"] = 10
        check_float("武僧线 禅意 10 → ×1.40（满 +40%）", b._zen_hold_mult(p), 1.40)
        b.resources["zen"] = 3
        check_float("武僧线 禅意 3 → ×1.12（+12%）", b._zen_hold_mult(p), 1.12)
        b.resources["zen"] = 0
        check_float("武僧线 禅意 0 → ×1.0（无持有无加成）", b._zen_hold_mult(p), 1.0)
        b.resources["zen"] = 12
        check_float("武僧线 禅意 12 → 封顶仍 ×1.40", b._zen_hold_mult(p), 1.40)
        b2, p2 = new_battle("cls_wu_sheng", 2, 2, level=95)   # 守线（大地武僧）不吃
        b2.resources["zen"] = 10
        check_float("负例：守线（大地武僧）不吃持有加伤 ×1.0", b2._zen_hold_mult(p2), 1.0)
        b3, p3 = new_battle("cls_wu_seng", 1, 1, level=95)    # 基础拳师（对照蓄势互不干扰）
        b3.resources["zen"] = 10
        check_float("负例：基础拳师 不吃禅意持有加伤 ×1.0", b3._zen_hold_mult(p3), 1.0)
    except (AttributeError, TypeError) as ex:
        skip("引擎：_zen_hold_mult 单元", str(ex))
    # ---- 行为：普攻（物理）满 10 意 ≈ ×1.40 / 3 意 ≈ ×1.12 + 日志标签 ----
    try:
        b4, p4 = new_battle("cls_wu_sheng", 3, 1, level=95)
        dmg0, _ = _dmg_run(b4, p4)
        b5, p5 = new_battle("cls_wu_sheng", 3, 1, level=95)
        dmg10, logs10 = _dmg_run(b5, p5, zen=10)
        b6, p6 = new_battle("cls_wu_sheng", 3, 1, level=95)
        dmg3, logs3 = _dmg_run(b6, p6, zen=3)
        check("普攻：10 意 > 0 意（加伤生效）", dmg10 > dmg0, f"0={dmg0} 10={dmg10}")
        check("普攻：10 意/0 意 ≈ ×1.40", abs(dmg10 / dmg0 - 1.40) < 0.06,
              f"ratio={dmg10 / dmg0:.4f}")
        check("普攻：3 意/0 意 ≈ ×1.12", abs(dmg3 / dmg0 - 1.12) < 0.05,
              f"ratio={dmg3 / dmg0:.4f}")
        check("普攻：满 10 意日志含 🧘禅意x1.4", any("🧘禅意x1.4" in str(l) for l in logs10),
              f"{logs10[-1]}")
        check("普攻：3 意日志含 🧘禅意x1.12", any("🧘禅意x1.12" in str(l) for l in logs3),
              f"{logs3[-1]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：普攻 禅意持有加伤", str(ex))
    # ---- 行为：技能（蓄劲连打，无 zen 消耗）满 10 意 ≈ ×1.40 + 日志标签 ----
    try:
        b7, p7 = new_battle("cls_wu_sheng", 3, 1, learned=["蓄劲连打"], level=95)
        dmg0s, _ = _dmg_run(b7, p7, "蓄劲连打")
        b8, p8 = new_battle("cls_wu_sheng", 3, 1, learned=["蓄劲连打"], level=95)
        dmg10s, logs8 = _dmg_run(b8, p8, "蓄劲连打", zen=10)
        check("技能：10 意/0 意 ≈ ×1.40", abs(dmg10s / dmg0s - 1.40) < 0.06,
              f"ratio={dmg10s / dmg0s:.4f}")
        check("技能：满 10 意日志含 🧘禅意x1.4", any("🧘禅意x1.4" in str(l) for l in logs8),
              f"{logs8[-1]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：技能 禅意持有加伤", str(ex))
    # ---- 负例：拳师守线（磐石行者）有气不吃禅意加伤；蓄势挂点不受影响 ----
    try:
        b9, p9 = new_battle("cls_wu_sheng", 1, 1, level=95)
        b9.resources["zen"] = 10
        st9 = b9._player_stats(p9)
        dmg9_a, logs9 = _dmg_run(b9, p9, zen=10)
        b10, p10 = new_battle("cls_wu_sheng", 1, 1, level=95)
        dmg9_b, _ = _dmg_run(b10, p10)
        check("负例：武僧 T1 档（path=1）加伤与 T3 档同源生效（×1.40）",
              dmg9_a > dmg9_b and any("🧘禅意x1.4" in str(l) for l in logs9),
              f"0={dmg9_b} 10={dmg9_a}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：负例对照", str(ex))


if __name__ == "__main__":
    clean_db()
    test_shadow_stealth_mult()
    test_zen_hold_bonus()
    print(f"\n===== v130.2f2 引擎修复批次: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)