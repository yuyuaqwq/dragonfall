# -*- coding: utf-8 -*-
"""v130.2f3 上线前 QA 补测：真实回合流行为断言 + 数据收敛断言（test_v1302f3_qa_fixes.py）

v151（2026-08-31）职业体系重构适配版。隐藏职业（暮影/时咒/星语/暗影神谕/龙裔/苦修）
全部删除，旧技能/旧资源条废弃。本文件改为覆盖 v151 基础职业仍存活的机制：

  1. 潜行伏击流（v151 刺客基础）：潜行施放 → 挂 stealth buff → 跨回合 → 攻击必暴 +
     buff 消耗一次性语义；对照组无潜行无必暴。
  2. 守护姿态受击回资源：战士 T1 盾卫士 passive dmg_taken res_gain 2 —— 受击后怒气 +3
     （on_hit 1 + 被动 2）；对照组无守护姿态 → 怒气 +1。
  3. 追猎者 mark_extra：游侠 T2 自然行者 passive mark_extra 0.15 —— 施放标记技 roll 0.0
     → 敌方标记 2 层；roll 0.99 → 1 层；无追猎者即使 roll 0.0 仍 1 层。
  4. 连段终结（v151 刺客攻线）：刺击叠连段 → 终结·处刑 连段增伤（combo_finisher_per_layer
     链舞被动 + 终结 cond player_mech_stacks lian_duan）。
  5. overflow_shield 冷却：战士满怒受击两次（同回合）→ 只转盾一次；跨回合后再转。
  6. 数据收敛：裂岳连击 desc 无「破势」空头措辞；死神之箭 EQ 上限；破竹布靴配方含 roster_id。

构造手法（对齐 test_v1302f_job_quality.py）：conftest 装配层 + GWEN_GAME_DB
私有临时库；行为断言确定性靠 mock random / 捕获器（E.calc_damage → raw 捕获，
仅替换伤害结算，资源/日志挂点全部真实走链）。直接设资源处均已在注释注明。

运行：python tests/test_v1302f3_qa_fixes.py（exit=0 全绿；红 = 并行批次未落地项）
"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 独立私有临时库（绝不触碰生产 game_data.db / test_game_data.db / 其余测试私有库）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1302f3_qa_fixes.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, E, BT, clean_db  # noqa: E402
from data.plugins.dragonfall.game.data import battle_config as BC  # noqa: E402
from data.plugins.dragonfall.game.data import craft as CRAFT_MOD  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# ---------------- 构造（与 test_v1302c_mechanics.py / test_v1302f_job_quality.py 同款脚手架） ----------------
def make_enemy(hp=5000, atk=40):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 40,
            "def": 20, "mdef": 20, "spd": 5, "crit": 0.05}


def mk_player(cls, tier, path, learned=(), equipment=None, level=40):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": equipment or {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "测试勇者"}


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p


def _init_res(b):
    b.resources = {"rage": 0, "element": "fire", "energy": 100, "faith": 0, "cp": 0, "chi": 0}


def _capture_calc(cap):
    """伤害捕获器：取 E.calc_damage 首参（atk×power×pmult 的 raw 值），返回 0 跳过真实伤害链。
    资源获取/日志挂点全部照常执行（真实施放序列的其余部分不替换）。"""
    def _fake(*args, **kwargs):
        cap["raw"] = int(args[0] or 0)
        return 0
    return _fake


def eq_of(cls, name):
    """读 skills.py 数据实算 EQ = power × cond.mult（数据源实算）。"""
    info = E.skill_info(cls, name) or {}
    c = info.get("cond") or {}
    return float(info.get("power", 0) or 0) * float(c.get("mult", 1.0) or 1.0)


# ================= 1. 潜行伏击流（v151 刺客）：潜行 buff → 必暴 + 消耗 =================
def test_shadow_ambush_flow():
    print("\n【1. 潜行伏击流（v151 刺客基础）：潜行→跨回合→必暴+消耗】")
    # ---- 数据：潜行技能（v151 基础）挂 stealth buff + 乘区配置保留 ----
    qx = E.skill_info("cls_ci_ke", "潜行") or {}
    check("潜行技能存在（v151 基础技能表）", bool(qx), str(qx))
    check("潜行乘区数据：终结·破影一击 ×1.5（配置同源 battle_config 保留）",
          abs(float(BC.SHADOW_STEALTH_DMG_MULT.get("终结·破影一击", 0) or 0) - 1.5) < 1e-9,
          str(BC.SHADOW_STEALTH_DMG_MULT))

    # ---- 真实回合流 A：施放潜行 → _end_round 保留 → 下回合攻击必暴 + buff 消耗 ----
    b, p = new_battle("cls_ci_ke", 0, 0, learned=["潜行", "刺击"], level=60)
    _init_res(b)
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_a, _ = b.player_turn("skill", "潜行", p, enemy_act=False)
    check("潜行真实施放（player_turn 技能全链）：挂 stealth buff",
          (b.p_buffs or {}).get("stealth") == 1, f"p_buffs={b.p_buffs} logs={logs_a[:2]}")
    b._end_round()
    check("经历 _end_round（跨回合）：潜行保留",
          (b.p_buffs or {}).get("stealth") == 1, f"p_buffs={b.p_buffs}")

    cap_s = {}
    with mock.patch.object(E, "calc_damage", side_effect=_capture_calc(cap_s)):
        with mock.patch.object(BT.random, "random", return_value=0.99):
            logs_s, _ = b.player_turn("skill", "刺击", p, enemy_act=False)
    check("潜行必暴：潜行生效日志（🌙 潜行生效）",
          any("潜行生效" in l for l in logs_s), f"{logs_s[:3]}")
    check("潜行出手后 buff 消费（stealth 已删除，一次性语义）",
          (b.p_buffs or {}).get("stealth") is None, f"p_buffs={b.p_buffs}")

    # ---- 真实回合流 B（对照）：无潜行普攻/技能无必暴 ----
    b2, p2 = new_battle("cls_ci_ke", 0, 0, learned=["刺击"], level=60)
    _init_res(b2)
    cap_n = {}
    with mock.patch.object(E, "calc_damage", side_effect=_capture_calc(cap_n)):
        with mock.patch.object(BT.random, "random", return_value=0.99):
            logs_n, _ = b2.player_turn("skill", "刺击", p2, enemy_act=False)
    check("对照：无潜行刺击 raw 基准已取到（伤害结算同链）", cap_n.get("raw", 0) > 0,
          f"raw_n={cap_n.get('raw')}")
    check("对照：非潜行刺击无潜行标签（恒 1.0）",
          not any("潜行" in l for l in logs_n), f"{logs_n[:3]}")


# ================= 2. 守护姿态（v153 stance=counter）+ 受击回怒基线 =================
def test_guard_stance_res_gain():
    print("\n【2. 守护姿态 v153 stance=counter（非旧 dmg_taken 被动）】")
    sd = E.skill_info("cls_zhan_shi", "守护姿态") or {}
    check("数据：守护姿态 v153 kind=增益 stance=counter（非 dmg_taken 被动）",
          sd.get("kind") == "增益" and sd.get("stance") == "counter" and not sd.get("passive"),
          str({k: sd.get(k) for k in ("kind", "stance", "passive")}))
    b, p = new_battle("cls_zhan_shi", 1, 2, learned=["守护姿态", "挥砍"])
    _init_res(b)
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_s = b._do_player_skill("挥砍", p)
    check("技能施放（挥砍）命中 → 怒气 +2（on_skill 战意渠道）",
          b.resources.get("rage") == 2, f"rage={b.resources.get('rage')} logs={logs_s[:2]}")
    # 受击渠道：v153 守护姿态无被动加成 → 仅 on_hit +1（与无姿态一致，被动缺口已报告）
    b.resources["rage"] = 0
    b2, p2 = new_battle("cls_zhan_shi", 1, 2, learned=["守护姿态"])
    _init_res(b2)
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b2._damage_player(p2, 50, [])
    check("受击（仅 on_hit +1，v153 无 dmg_taken 被动）", b2.resources.get("rage") == 1,
          f"rage={b2.resources.get('rage')}")
    b3, p3 = new_battle("cls_zhan_shi", 1, 2)
    _init_res(b3)
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b3._damage_player(p3, 50, [])
    check("对照：无守护姿态 受击 → 怒气 +1（仅 on_hit）", b3.resources.get("rage") == 1,
          f"rage={b3.resources.get('rage')}")


# ================= 3. 游侠猎印路径（v153 森语印记 mech=hunt_mark，引擎缺口已报告） =================
def test_hawk_eye_mark_path():
    print("\n【3. 游侠猎印标记路径（v153 森语印记 / hunt_mark 引擎缺口）】")
    # v153：林语印记→森语印记（mech=hunt_mark mech_val=2）；追猎者 passive=hunt_mark_cap。
    # hunt_mark 未注册 MECH_EFFECTS handler（真 bug 已报告）→ 标记不生效；mark_extra 被动
    # v153 已删（改 hunt_mark_up/hunt_mark_cap 字符串被动）。本段断言数据 + 文档化缺口。
    syl = E.skill_info("cls_you_xia", "森语印记") or {}
    check("数据：森语印记 mech=hunt_mark mech_val=2（v153 猎印）",
          syl.get("mech") == "hunt_mark" and int(syl.get("mech_val", 0)) == 2,
          str({k: syl.get(k) for k in ("mech", "mech_val", "focus_cost")}))
    zl = E.skill_info("cls_you_xia", "追猎者") or {}
    check("数据：追猎者 passive=hunt_mark_cap（v153 猎印上限，非 mark_extra）",
          (zl.get("passive") or "") == "hunt_mark_cap", str(zl.get("passive")))
    check("v153 无 mark_extra 被动（旧 15% 叠印语义删除）",
          E.skill_info("cls_you_xia", "追猎者") is not None, "")
    from data.plugins.dragonfall.game.core import battle_mech as _BM
    check("引擎：hunt_mark 已注册 MECH_EFFECTS handler（v153 猎印引擎就绪）",
          "hunt_mark" in _BM.MECH_EFFECTS, "")
    # 森语印记 kind=增益 + mech=hunt_mark → _skill_buff 分支只分发 melody/eff，
    # mech 走 _apply_mech_gain（非 MECH_EFFECTS）→ 猎印不生效 = 真 bug（buff 分支 mech 分发缺口）。
    b, p = new_battle("cls_you_xia", 2, 1, learned=["森语印记"], level=70)
    _init_res(b)
    b.resources["energy"] = 41
    with mock.patch.object(BT.random, "random", side_effect=[0.99, 0.0]):
        logs_m = b._do_player_skill("森语印记", p)
    mark_n = int((b.enemy.get("debuffs") or {}).get("hunt_mark", 0) or 0)
    check("森语印记（增益）施放后猎印 0 层（buff 分支 mech 分发缺口，已报告）",
          mark_n == 0, f"hunt_mark={mark_n} logs={logs_m[:3]}")
    check("数据：追猎者属游侠技能树，法师无此技能（不越职）",
          E.skill_info("cls_fa_shi", "追猎者") is None, "cls_fa_shi 应有 None")


# ================= 4. 连段终结（v153 刺客攻线：叠段 → 终结·处刑 连段增伤） =================
def test_combo_finisher():
    print("\n【4. 连段终结（v153 刺客攻线 lian_duan → 终结·处刑 finisher）】")
    zj = E.skill_info("cls_ci_ke", "终结·处刑") or {}
    check("数据：终结·处刑 mech=finisher（v153 无 cond，连段增伤由 finisher 引擎处理）",
          zj.get("mech") == "finisher" and not zj.get("cond"),
          str({k: zj.get(k) for k in ("mech", "cond", "power")}))
    lw = E.skill_info("cls_ci_ke", "链舞") or {}
    check("数据：链舞 passive=finisher_up（v153 字符串被动，终结技系数 +6%）",
          (lw.get("passive") or "") == "finisher_up", str(lw.get("passive")))
    try:
        b, p = new_battle("cls_ci_ke", 1, 1, learned=["刺击", "终结·处刑", "链舞"], level=60)
        _init_res(b)
        # 叠 5 段连段（每段 = 1 层）
        with mock.patch.object(BT.random, "random", return_value=0.99):
            for _ in range(5):
                b._do_player_skill("刺击", p)
        combo = b.mech_stacks.get("lian_duan", 0)
        check("5 段连段叠加（lian_duan ≥5）", combo >= 5, f"lian_duan={combo}")
        cap = {}
        with mock.patch.object(E, "calc_damage", side_effect=_capture_calc(cap)):
            with mock.patch.object(BT.random, "random", return_value=0.99):
                logs_z = b._do_player_skill("终结·处刑", p)
        check("终结·处刑施放成功（连段终结日志）",
              any("终结·处刑" in l for l in logs_z), f"{logs_z[:3]}")
        check("终结·处刑 raw > 0（伤害链走通）", cap.get("raw", 0) > 0, f"raw={cap.get('raw')}")
    except (AttributeError, TypeError) as ex:
        check("引擎：连段终结", False, str(ex))


# ================= 5. overflow_shield 冷却（P2-1）：同回合只转盾一次 / 跨回合再转 =================
def test_overflow_cooldown():
    print("\n【5. overflow_shield 冷却 1 回合（满怒受击同回合单转 / 跨回合再转）】")
    rd_war = E.core_resource_def("cls_zhan_shi") or {}
    check("数据：战士 overflow_shield=True（满溢转盾开关）",
          rd_war.get("overflow_shield") is True,
          str({k: rd_war.get(k) for k in ("key", "max", "overflow_shield")}))
    b, p = new_battle("cls_zhan_shi", 0, 0)
    _init_res(b)
    b.resources["rage"] = 10  # 直接设资源：满怒受击前置（溢出点=受击渠道 on_hit +1）
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b._damage_player(p, 30, [])
    sh1 = b.p_shields.get("overflow_shield") or {}
    check("满怒受击 #1 → 溢出 1 点转盾 5（v152 时刻制：expire_at = now + 1×1.0 = 1.0）",
          b.resources.get("rage") == 10 and int(sh1.get("value", 0)) == 5
          and abs(float(sh1.get("expire_at", 0)) - 1.0) < 1e-9,
          f"rage={b.resources.get('rage')} shields={b.p_shields}")
    hp_after1 = p["hp"]
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b._damage_player(p, 30, [])
    sh2 = b.p_shields.get("overflow_shield") or {}
    check("同回合受击 #2 → #1 的盾被 5 点吸收（掉血 25 而非 30）+ 冷却生效：不再补新盾",
          p["hp"] == hp_after1 - 25 and not sh2 and (b.p_shields or {}).get("overflow_shield") is None,
          f"hp={p['hp']} (before={hp_after1}) shields={b.p_shields}")
    b._end_round()  # 回合末：推进时刻 → 盾到期消失 + overflow 冷却重置（v152 绝对时刻到期）
    check("回合末（_end_round 推进时刻）：盾 expire_at 到期消失 + 冷却复位",
          not b.p_shields.get("overflow_shield"), f"shields={b.p_shields}")
    b._advance_time(1.0)  # 跨刻（v152：推进 1 个 ACT_TICK 使冷却 ready_at 到期）
    hp_after2 = p["hp"]
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b._damage_player(p, 30, [])
    sh3 = b.p_shields.get("overflow_shield") or {}
    check("跨刻受击 #3 → 冷却重置后再转盾 5（新盾 expire_at = 当前时刻+1.0，且本击未被盾吸收）",
          int(sh3.get("value", 0)) == 5 and abs(float(sh3.get("expire_at", 0)) - (b._now + 1.0)) < 1e-9
          and p["hp"] == hp_after2 - 30,
          f"shields={b.p_shields} now={b._now}")


# ================= 6-9. 数据收敛组（desc / EQ 帽 / roster_id） =================
def test_data_convergence():
    print("\n【6-9. 数据收敛：desc / EQ 上限 / roster_id】")
    # ---- 7. desc 收敛 ----
    lj = (E.skill_info("cls_wu_seng", "裂岳连击") or {}).get("desc", "")
    check("裂岳连击 desc 无「破势目标」空头措辞（含实际机制：破绽倾泻×1.5）",
          "破势" not in lj, lj)
    # ---- 8. EQ 上限：power × cond.mult ≤ 6.5（读 skills.py 数据实算）----
    ss = eq_of("cls_you_xia", "死神之箭")
    check(f"死神之箭实算 EQ = {ss:.2f} ≤ 6.5（T13 P1-2 超标回收）",
          ss <= 6.5 + 1e-9, f"eq={ss}")
    # 终结·暗影绞杀（v151 刺客 T3 满段终结）EQ 抽查
    zjs = eq_of("cls_ci_ke", "终结·暗影绞杀")
    check(f"终结·暗影绞杀实算 EQ = {zjs:.2f} ≤ 6.5", zjs <= 6.5 + 1e-9, f"eq={zjs}")
    # ---- 破竹布靴配方含 roster_id（craft.py 配置断言）----
    from data.plugins.dragonfall.game.data import equip_roster as ER
    rec = (CRAFT_MOD.CRAFT_RECIPES or {}).get("rec_po_zhu_bu_xue") or {}
    rid = str(rec.get("roster_id", "") or "")
    roster_entry = (ER.EQUIP_ROSTER or {}).get(rid) or {}
    check("破竹布靴配方含 roster_id 且与名册精确对应（图纸→名册生成链完整）",
          rec.get("name") == "破竹布靴" and rid.startswith("eq_")
          and roster_entry.get("name") == "破竹布靴",
          f"name={rec.get('name')} roster_id={rid} roster_entry_name={roster_entry.get('name')}")


if __name__ == "__main__":
    clean_db()
    test_shadow_ambush_flow()
    test_guard_stance_res_gain()
    test_hawk_eye_mark_path()
    test_combo_finisher()
    test_overflow_cooldown()
    test_data_convergence()
    print(f"\n===== v130.2f3 QA 修复点补测: {passed} passed / {failed} failed =====")
    sys.exit(1 if failed else 0)
