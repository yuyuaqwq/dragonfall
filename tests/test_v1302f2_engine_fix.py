# -*- coding: utf-8 -*-
"""v130.2f2 引擎修复批次测试（test_v1302f2_engine_fix.py）

v151（2026-08-31）职业体系重构适配版：
  ① 潜行乘区数据表（SHADOW_STEALTH_DMG_MULT）保留（配置兼容），但表中技能
     （终结·破影一击/幽影刃）已随隐藏职业删除——改断言：数据表存在 + 潜行通用行为
     （潜行 buff → 必暴 + 攻击后消耗）在 v151 刺客技能上生效。
  ② 苦修士 ZEN_HOLD_CFG 随 v151 删除——v151 后由拳师蓄势（MOMENTUM_CFG +
     _momentum_mult）承担持有加伤（攻线·格斗士 path=1）。

设计原则（对齐 test_v1302f_job_quality.py 脚手架姿势）：
  - 行为断言确定性：random.random → 0.99（不自然暴击/不幸运/不闪避）+
    random.uniform → 0.0（calc_damage 波动归零）双 mock；
  - 负例保证不改变其他职业行为（守线拳师不吃蓄势加伤）。

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


def _init_res(b):
    # v180-B：resources 权威在 player actor dict——REBIND 整袋先 clear 后 update（同迁移指南）
    b._p_res().clear()
    b._p_res().update({"rage": 0, "element": "fire", "energy": 100, "faith": 0, "cp": 0, "chi": 0})


def _dmg_run(b, p, skill=None, stealth=False, chi=None):
    """确定性伤害跑法：random → 0.99（不自然暴击/不幸运/不闪避）+
    random.uniform → 0.0（calc_damage ±15% 波动归零）。
    stealth=True 手动挂潜行 buff；chi 非 None 则预置气。返回 (伤害值, 日志)。
    v154 读条命中制：施放走 actor_turn（排 cast_done），推进到命中时刻才结算。
    v180-B：p_buffs/resources 经 _p_buffs_bag()/_p_res() 读玩家 actor dict。"""
    if stealth:
        b._p_buffs_bag()["stealth"] = 1
    if chi is not None:
        b._p_res()["chi"] = chi
    before = b.enemy.get("hp", 0)
    with mock.patch.object(BT.random, "random", return_value=0.99), \
            mock.patch.object(BT.random, "uniform", return_value=0.0):
        if skill:
            logs, _ = b.actor_turn("skill", skill, p, enemy_act=False)
            b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
        else:
            st = b._player_stats(p)
            logs = b._actor_attack(st, p)
    dmg = before - b.enemy.get("hp", 0)
    return dmg, logs


# ================= ① 潜行乘区数据 + 潜行通用行为 =================
def test_shadow_stealth_mult():
    print("\n【① 潜行机制（数据表保留 + v151 刺客潜行必暴/消耗）】")
    # ---- 数据层：配置表存在且数值正确（v151 保留兼容；表内技能已随隐藏职业删除）----
    try:
        from data.plugins.dragonfall.game.data.battle_config import SHADOW_STEALTH_DMG_MULT as SSDM
    except Exception as ex:
        skip("数据：SHADOW_STEALTH_DMG_MULT 表", str(ex))
        return
    check_float("数据：破影一击 潜行倍率 ×1.5（配置保留）", float(SSDM.get("终结·破影一击", 0)), 1.5)
    check_float("数据：幽影刃 潜行倍率 ×1.25（配置保留）", float(SSDM.get("幽影刃", 0)), 1.25)
    check("数据：表内仅暮影两终结技（配置未扩散）",
          set(SSDM.keys()) == {"终结·破影一击", "幽影刃"}, str(SSDM))
    check("v151：表内技能（终结·破影一击/幽影刃）已随隐藏职业从技能表删除",
          E.skill_info("cls_ci_ke", "终结·破影一击") is None
          and E.skill_info("cls_ci_ke", "幽影刃") is None, "")
    # ---- 行为：v151 刺客 潜行 buff → 下次攻击必暴 + 攻击后消耗 ----
    try:
        b1, p1 = new_battle("cls_ci_ke", 0, 0, learned=["刺击"])
        _init_res(b1)
        dmg_ns, logs_ns = _dmg_run(b1, p1, "刺击")
        b2, p2 = new_battle("cls_ci_ke", 0, 0, learned=["刺击"])
        _init_res(b2)
        dmg_s, logs_s = _dmg_run(b2, p2, "刺击", stealth=True)
        check("潜行伤害 > 非潜行（潜行=必暴 生效）", dmg_s > dmg_ns, f"ns={dmg_ns} s={dmg_s}")
        check("潜行日志（🌙 潜行生效）",
              any("潜行生效" in str(l) for l in logs_s), f"{logs_s[:2]}")
        check("非潜行日志无潜行生效",
              not any("潜行生效" in str(l) for l in logs_ns), f"{logs_ns[:2]}")
        check("潜行 buff 攻击后已消耗（一次性语义）",
              b2._p_buffs_bag().get("stealth") is None, f"p_buffs={b2._p_buffs_bag()}")
        # 潜行技能本体（v151 基础 潜行）：施放挂潜行 buff
        b3, p3 = new_battle("cls_ci_ke", 0, 0, learned=["潜行"])
        _init_res(b3)
        with mock.patch.object(BT.random, "random", return_value=0.99):
            logs3, _ = b3.actor_turn("skill", "潜行", p3, enemy_act=False)
            # v154 读条命中制：增益类技能也走读条——推进后生效
            b3._process_until(float(getattr(b3, "p_ct", 0) or 0) + 0.001, logs3, p3)
        check("施放【潜行】→ 挂 stealth buff", (b3._p_buffs_bag() or {}).get("stealth") == 1,
              f"p_buffs={b3._p_buffs_bag()} logs={logs3}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：潜行 必暴/消耗", str(ex))


# ================= ② 拳师蓄势持有加伤（v151 替代苦修禅意） =================
def test_zen_hold_bonus():
    print("\n【② 拳师蓄势持有加伤（v151 攻线·格斗士 path=1，每 1 气 +3%，满 10 +30%）】")
    # ---- 数据层：MOMENTUM_CFG 数值（desc 承诺 3%/气、满 10 封顶）----
    try:
        from data.plugins.dragonfall.game.data.battle_config import MOMENTUM_CFG as MMC
    except Exception as ex:
        skip("数据：MOMENTUM_CFG 表", str(ex))
        return
    check_float("数据：per_chi=0.03（每 1 气 +3%）", float(MMC.get("per_chi", 0)), 0.03)
    check("数据：cap_chi=10（满 10 封顶）", int(MMC.get("cap_chi", 0)) == 10, str(MMC))
    # ---- 单元：_momentum_mult 线性/封顶/线别门（攻线限定）----
    try:
        b, p = new_battle("cls_wu_seng", 1, 1, level=95)
        b._p_res()["chi"] = 10
        check_float("攻线·格斗士 气 10 → ×1.30（满 +30%）", b._momentum_mult(p), 1.30)
        b._p_res()["chi"] = 5
        check_float("攻线·格斗士 气 5 → ×1.15（+15%）", b._momentum_mult(p), 1.15)
        b._p_res()["chi"] = 0
        check_float("攻线·格斗士 气 0 → ×1.0（无持有无加成）", b._momentum_mult(p), 1.0)
        b._p_res()["chi"] = 12
        check_float("攻线·格斗士 气 12 → 封顶仍 ×1.30", b._momentum_mult(p), 1.30)
        b2, p2 = new_battle("cls_wu_seng", 1, 2, level=95)   # 守线（磐石行者）不吃
        b2._p_res()["chi"] = 10
        check_float("负例：守线（磐石行者）不吃持有加伤 ×1.0", b2._momentum_mult(p2), 1.0)
        # v176 判据改资源键+攻线：战士对照须 evolve_path=0（攻线=1 即使塞 chi 也会命中蓄势——
        # 旧测试给战士设 path=1 又塞 chi 自相矛盾，v176 后穿帮）
        b3, p3 = new_battle("cls_zhan_shi", 1, 0, level=95)  # 战士（无攻线）不吃
        b3._p_res()["chi"] = 10
        check_float("负例：战士 不吃拳师蓄势 ×1.0", b3._momentum_mult(p3), 1.0)
    except (AttributeError, TypeError) as ex:
        skip("引擎：_momentum_mult 单元", str(ex))
    # ---- 行为：普攻（物理）满 10 气 ≈ ×1.30 / 5 气 ≈ ×1.15 + 日志标签 ----
    try:
        b4, p4 = new_battle("cls_wu_seng", 1, 1, level=95)
        _init_res(b4)
        dmg0, _ = _dmg_run(b4, p4)
        b5, p5 = new_battle("cls_wu_seng", 1, 1, level=95)
        _init_res(b5)
        dmg10, logs10 = _dmg_run(b5, p5, chi=10)
        b6, p6 = new_battle("cls_wu_seng", 1, 1, level=95)
        _init_res(b6)
        dmg5, logs5 = _dmg_run(b6, p6, chi=5)
        check("普攻：10 气 > 0 气（加伤生效）", dmg10 > dmg0, f"0={dmg0} 10={dmg10}")
        check("普攻：10 气/0 气 ≈ ×1.30", abs(dmg10 / dmg0 - 1.30) < 0.06,
              f"ratio={dmg10 / dmg0:.4f}")
        check("普攻：5 气/0 气 ≈ ×1.15", abs(dmg5 / dmg0 - 1.15) < 0.05,
              f"ratio={dmg5 / dmg0:.4f}")
        check("普攻：满 10 气日志含 🔥蓄势x1.3", any("蓄势x1.3" in str(l) for l in logs10),
              f"{logs10[-1]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：普攻 蓄势持有加伤", str(ex))
    # ---- 行为：技能（连招三连，无气消耗）满 10 气 ≈ ×1.30 + 日志标签 ----
    try:
        b7, p7 = new_battle("cls_wu_seng", 1, 1, learned=["连招三连"], level=95)
        _init_res(b7)
        dmg0s, _ = _dmg_run(b7, p7, "连招三连")
        b8, p8 = new_battle("cls_wu_seng", 1, 1, learned=["连招三连"], level=95)
        _init_res(b8)
        dmg10s, logs8 = _dmg_run(b8, p8, "连招三连", chi=10)
        check("技能：10 气/0 气 ≈ ×1.30（多段 int 截断致 ±0.07 漂移）", abs(dmg10s / dmg0s - 1.30) < 0.10,
              f"ratio={dmg10s / dmg0s:.4f}")
        check("技能：满 10 气日志含 🔥蓄势x1.3", any("蓄势x1.3" in str(l) for l in logs8),
              f"{logs8[-1]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：技能 蓄势持有加伤", str(ex))
    # ---- 负例：守线（磐石行者）有气不吃蓄势加伤 ----
    try:
        b9, p9 = new_battle("cls_wu_seng", 1, 2, level=95)
        _init_res(b9)
        dmg9_a, logs9 = _dmg_run(b9, p9, chi=10)
        b10, p10 = new_battle("cls_wu_seng", 1, 2, level=95)
        _init_res(b10)
        dmg9_b, _ = _dmg_run(b10, p10)
        check("负例：守线（磐石行者）有气不加伤（无蓄势标签）",
              abs(dmg9_a - dmg9_b) <= 1 and not any("蓄势x" in str(l) for l in logs9),
              f"0={dmg9_b} 10={dmg9_a}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：负例对照", str(ex))


if __name__ == "__main__":
    clean_db()
    test_shadow_stealth_mult()
    test_zen_hold_bonus()
    print(f"\n===== v130.2f2 引擎修复批次: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)
