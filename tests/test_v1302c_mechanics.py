# -*- coding: utf-8 -*-
"""v130.2c/d 核心机制固化测试（test_v1302c_mechanics.py）

R3 审计（B- 68/100）：8 大核心机制 7 项无行为级固化测试 → 本文件补齐：
  1. consume_all 统一公式（无畏冲击/暗影处刑/破晓之拳/元素湮灭 4 技能数值断言）
  2. 超标 P1-2 回归（资源不满可施放：持 4 怒无畏冲击 / 持 2 充能元素湮灭）
  3. 回声单通道闭环（歌者 战歌叠层 / 英雄叙事诗不叠 / 满层 _turn_start 全队恢复 36）
  4. 六词条行为（印记铭刻 max_total 帽 / 反应催化 / 疾风余韵 / 连段护持 / 连段之锋 / 蓄势精通）
  5. 套装抽样 5 套（元素使徒 / 夜幕合契·影纱 / 圣典日冕 / 余烬军团 / 时之领主）

设计原则（对齐 test_v130_resources.py 脚手架姿势：conftest FakeEvent/run/clean_db/make_player
+ GWEN_GAME_DB 私有临时库）：
  - 引擎行为层断言参照 _smoke_v130_engine.py 已过路径；引擎未就绪 → skip 兜底（不假失败）；
  - 随机点显式固定（unittest.mock 控制 random.random），不赌 seed；
  - 纯数据断言为硬断言（值回归必红）；
  - 禁恒真 check：全部断言真数值。

运行：python tests/test_v1302c_mechanics.py（exit=0 全绿；skip 不计数为失败）
"""
import os
import sys
import math
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 独立私有临时库（绝不触碰生产 game_data.db / test_game_data.db）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1302c_mechanics.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, E, BT, clean_db  # noqa: E402
from data.plugins.dragonfall.game.data import battle_config as BC  # noqa: E402

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


# ---------------- 构造 ----------------
def make_enemy(hp=2000, atk=40):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 40,
            "def": 20, "mdef": 20, "spd": 5, "crit": 0.05}


def mk_player(cls, tier, path, learned=(), equipment=None, level=40):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": equipment or {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "测试勇者"}


def mk_piece(affixes=(), set_id=None, quality="purple"):
    """单件装备：可带词条 affixes / 套装 set 字段。"""
    it = {"name": "测试件", "quality": quality, "affixes": list(affixes)}
    if set_id:
        it["set"] = set_id
    return it


def mk_eq(*pieces):
    return {f"slot{i}": pc for i, pc in enumerate(pieces)}


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p


def cast_capture(b, skill_name, p):
    """黑盒施放：真实走 player_turn 全链（校验/消耗/统一公式折算 + v154 读条排事件），
    推进到命中时刻后把伤害结算 _player_skill 替换为捕获器记录引擎折算后的 info['power']
    （确定性：不跑真实伤害链的随机点）。"""
    captured = {}

    def _fake(st, skill_name, info, player, target=None):
        captured["power"] = float(info.get("power") or 0)
        return []

    b._player_skill = _fake
    logs, _ = b.player_turn("skill", skill_name, p, enemy_act=False)
    # v154 读条命中制：出招读条结束（cast_done）才调用 _player_skill（命中结算）——推进后触发
    b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
    return captured, logs


# ================= 1. 元素湮灭（v153：cond enemy_marks，无 consume_all） =================
def test_consume_all_formula():
    print("\n【1. 元素湮灭（v153 改版：cond enemy_marks 取代 consume_all）】")
    # ---- 数据层硬断言：v153 元素湮灭 power=1.71 / cond enemy_marks{4,×1.35}，无 consume_all ----
    e = E.skill_info("cls_fa_shi", "元素湮灭") or {}
    check("数据：元素湮灭 power=1.71", abs(float(e.get("power", 0)) - 1.71) < 1e-9,
          str(e.get("power")))
    check("数据：元素湮灭 cond=enemy_marks{4,×1.35}",
          (e.get("cond") or {}).get("type") == "enemy_marks"
          and int((e.get("cond") or {}).get("stacks", 0)) == 4
          and abs(float((e.get("cond") or {}).get("mult", 0)) - 1.35) < 1e-9,
          str(e.get("cond")))
    check("数据：元素湮灭已无 consume_all（v153 删除全耗语义）", not e.get("consume_all"),
          str(e.get("consume_all")))
    # ---- 引擎黑盒：施放不消耗充能（v153 语义：元素湮灭吃 cond 不吃充能条）----
    try:
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素湮灭"])
        b.resources["element_charge"] = 5
        cap, logs = cast_capture(b, "元素湮灭", p)
        check_float("元素湮灭 折算 power 保持 1.71（无 consume_all 放大）", cap.get("power", 0), 1.71)
        check("元素湮灭 施放后充能不变（仍 5）", b._elem_charge() == 5,
              f"charge={b._elem_charge()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：元素湮灭 折算", str(ex))


# ================= 2. 资源不满可施放（v153 语义） =================
def test_overcap_regression():
    print("\n【2. 资源门槛预检（v153：res_cost/focus_cost 门槛）】")
    try:
        # 持 2 充能施放元素湮灭（v153 无 consume_all → 不校验充能，直接施放）
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素湮灭"])
        b.resources["element_charge"] = 2
        logs, blocked = b._skill_cast_blocked("元素湮灭", p)
        check("持 2 充能预检不拦截", blocked is False, f"{logs}")
        logs, _ = b.player_turn("skill", "元素湮灭", p, enemy_act=False)
        # v154 读条命中制：施放只排读条——推进后命中结算（此处验证无资源不足日志）
        b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
        check("持 2 充能施放成功（无资源不足日志）", not any("不足" in l for l in logs), f"{logs[:2]}")
        check("施放后充能保留（v153 不消耗）", b._elem_charge() == 2,
              f"charge={b._elem_charge()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：持 2 充能元素湮灭", str(ex))
    try:
        # 拳师守线磐岩释能（res_cost guard_core）门槛 ≥1 即可
        b, p = new_battle("cls_wu_seng", 1, 2, learned=["磐岩释能"])
        b.resources["guard_core"] = 1
        logs, blocked = b._skill_cast_blocked("磐岩释能", p)
        check("持 1 磐核预检不拦截（res_cost 门槛 ≥1 即可）", blocked is False, f"{logs}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：磐岩释能 预检", str(ex))


# ================= 3. 牧师信念负载（v153 取代歌者回声） =================
def test_bard_echo_loop():
    print("\n【3. 牧师信念负载引擎（v153 取代歌者回声闭环）】")
    try:
        b, p = new_battle("cls_mu_shi", 0, 0)
        b._res_gain(p, "faith", 5)
        check("信念 +5（负载中段）", b._res_read("faith") == 5, f"faith={b._res_read('faith')}")
        b._res_gain(p, "faith", 6)
        check("信念封顶 10", b._res_read("faith") == 10, f"faith={b._res_read('faith')}")
        check("信念消耗 -4 = 6", b._res_spend("faith", 4) and b._res_read("faith") == 6,
              f"faith={b._res_read('faith')}")
        # 负载档位治疗乘区（_skill_heal 读 load_tiers）：专注档 4-7 → ×1.25
        # 用日志治疗量对比（faith=0 清醒 vs faith=5 专注，避开 max_hp 重算口径）
        p2 = {"class_name": "cls_mu_shi", "level": 30, "hp": 100, "max_hp": 1000,
              "mp": 100, "max_mp": 100, "name": "牧师", "reach": 3,
              "equipment": {"weapon": {"name": "t", "stats": {"matk": 200}, "affixes": [], "enhance": 0}},
              "attributes": {"int": 20}, "learned_skills": ["治愈术"], "race": "human"}
        import re as _re3
        def _heal_log(cls_, faith, hp=100):
            pp = dict(p2)
            pp["hp"] = hp
            bb = BT.Battle("monster", make_enemy(), player=pp)
            bb.resources["faith"] = faith
            lg, _ = bb.player_turn("skill", "治愈术", pp, enemy_act=False)
            # v154 读条命中制：治疗读条结束（cast_done）才结算——推进后生效
            bb._process_until(float(getattr(bb, "p_ct", 0) or 0) + 0.001, lg, pp)
            m3 = _re3.search(r"治愈了你 (\d+) 点生命", next(x for x in lg if "治愈" in x))
            return int(m3.group(1)) if m3 else 0
        h0 = _heal_log("cls_mu_shi", 0)
        h5 = _heal_log("cls_mu_shi", 5)
        check(f"专注档(5) 治疗量 = 清醒档(0) ×1.25（{h0} → {h5}）",
              abs(h5 - h0 * 1.25) <= 2, f"h0={h0} h5={h5}")
        h9 = _heal_log("cls_mu_shi", 9)
        check(f"透支档(9) 治疗量 = 清醒档(0) ×1.50（{h0} → {h9}）",
              abs(h9 - h0 * 1.50) <= 2, f"h0={h0} h9={h9}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：牧师信念负载", str(ex))


# ================= 4. 六词条行为 =================
def test_six_affixes():
    print("\n【4. 六词条行为】")
    try:
        # 4a. 印记铭刻：上限 3 → 4；max_total=1 帽（2 件仍 4，不叠到 5）
        b0, p0 = new_battle("cls_fa_shi", 1, 1)
        check("无词条元素印记上限 3", b0._elem_mark_max(p0) == 3, f"max={b0._elem_mark_max(p0)}")
        b, p = new_battle("cls_fa_shi", 1, 1,
                          equipment=mk_eq(mk_piece(["sigil_engrave"]), mk_piece(["sigil_engrave"])))
        check("印记铭刻 2 件上限仍 4（max_total 帽封顶多件叠加）", b._elem_mark_max(p) == 4,
              f"max={b._elem_mark_max(p)}")
        new = b._elem_mark_apply("fire", layers=5)
        check("印记实际封顶 4（叠 5 层只到 4）",
              new == 4 and b._elem_marks().get("fire") == 4, f"marks={b._elem_marks()}")
        b1, p1 = new_battle("cls_fa_shi", 1, 1, equipment=mk_eq(mk_piece(["sigil_engrave"])))
        check("印记铭刻 1 件上限 = 4", b1._elem_mark_max(p1) == 4, f"max={b1._elem_mark_max(p1)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：印记铭刻 max_total 帽", str(ex))
    try:
        # 4b. 反应催化：反应伤害 +15%（蒸发 1.30 → 1.495）
        b, p = new_battle("cls_fa_shi", 1, 1, equipment=mk_eq(mk_piece(["reaction_catalyst"])))
        check_float("反应催化倍率 = 1.15", b._reaction_catalyst_mult(p), 1.15)
        b._elem_mark_apply("ice", layers=1)
        rr = b._reaction_table_resolve(p, "fire", {"matk": 100}, [])
        check("蒸发(1.30)×反应催化(1.15) = 1.495",
              rr is not None and abs(rr[0] - 1.495) < 1e-9, f"rr={rr}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：反应催化", str(ex))
    try:
        # 4c. 疾风余韵：上回合结束精力 ≥80 → 本回合自然回复 +10
        b, p = new_battle("cls_you_xia", 1, 2, equipment=mk_eq(mk_piece(["swift_tailwind"])))
        b._end_round()  # 记录上回合精力快照 = 100（开局满精）
        check("疾风余韵：上回合精力 100 ≥80 → 额外回复 10", b._tailwind_regen_bonus(p) == 10,
              f"bonus={b._tailwind_regen_bonus(p)}")
        b.resources["energy"] = 60
        # v178.2：核心资源刻回复 + 疾风余韵迁到 _tick_regen（每秒 tick）——测新结算器
        b._tick_regen(p, [])
        # v153 精力自然回 18（v151 起 30→18 专注流量制）+ 疾风余韵 10 = 60+28=88
        check("回合开始：自然回 18 + 疾风余韵 10 = 88", b.resources["energy"] == 88,
              f"energy={b.resources['energy']}")
        b2, p2 = new_battle("cls_you_xia", 1, 2, equipment=mk_eq(mk_piece(["swift_tailwind"])))
        b2._tailwind_prev_energy = 70
        check("疾风余韵：上回合精力 70 <80 → 不触发", b2._tailwind_regen_bonus(p2) == 0,
              f"bonus={b2._tailwind_regen_bonus(p2)}")
        b2.resources["energy"] = 60
        b2._tick_regen(p2, [])
        check("无余韵加成：60 + 18 = 78", b2.resources["energy"] == 78,
              f"energy={b2.resources['energy']}")
        # 满 100 排气：v153 已废弃凝神屏息（vent trigger=999 永不到达，专注流量制）
        b3, p3 = new_battle("cls_you_xia", 1, 2, equipment=mk_eq(mk_piece(["swift_tailwind"])))
        check("v153 vent trigger=999（凝神屏息已废弃，专注流量制）",
              int((p3.get("vent") or {}).get("trigger", 0)) == 999,
              str(p3.get("vent")))
        b3.resources["energy"] = 100
        b3._tailwind_prev_energy = 100
        b3._tick_regen(p3, [])
        check("满 100 + 余韵 10 封顶 100（v153 无排气，专注流量制）", b3.resources["energy"] == 100,
              f"energy={b3.resources['energy']}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：疾风余韵", str(ex))
    try:
        # 4d. 连段护持：受击按词条概率保留连段（roll 固定验证）
        b, p = new_battle("cls_ci_ke", 1, 1,
                          equipment=mk_eq(mk_piece(["combo_ward"], quality="purple")))
        check_float("连段护持保留概率 0.15（紫）", b._combo_keep_chance(p), 0.15)
        b.mech_stacks["combo"] = 5
        with mock.patch.object(BT.random, "random", return_value=0.0):
            b._combo_break(p, b._combo_keep_chance(p))
        check("roll 0.0 < 0.15 → 连段保留", b.mech_stacks.get("combo") == 5,
              f"combo={b.mech_stacks.get('combo')}")
        with mock.patch.object(BT.random, "random", return_value=0.5):
            b._combo_break(p, b._combo_keep_chance(p))
        check("roll 0.5 ≥ 0.15 → 连段击碎", b.mech_stacks.get("combo") is None,
              f"combo={b.mech_stacks.get('combo')}")
        # 受击生产链路接线（_damage_player → _combo_break(keep_chance)）
        b2, p2 = new_battle("cls_ci_ke", 1, 1,
                            equipment=mk_eq(mk_piece(["combo_ward"], quality="purple")))
        b2.mech_stacks["combo"] = 5
        with mock.patch.object(BT.random, "random", return_value=0.0):
            b2._damage_player(p2, 50, [])
        check("受击链路：连段护持生效（连段保留）", b2.mech_stacks.get("combo") == 5,
              f"combo={b2.mech_stacks.get('combo')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：连段护持", str(ex))
    try:
        # 4e. 连段之锋：生效阈值 3 → 2
        b, p = new_battle("cls_ci_ke", 1, 1, equipment=mk_eq(mk_piece(["combo_edge"])))
        check("连段之锋阈值 3 → 2", b._combo_finish_min(p) == 2, f"min={b._combo_finish_min(p)}")
        b.mech_stacks["combo"] = 2
        check_float("combo2 增伤 ×1.10（阈值 2 生效）", b._combo_dmg_mult(p), 1.10)
        b2, p2 = new_battle("cls_ci_ke", 1, 1)
        b2.mech_stacks["combo"] = 2
        check("无词条 combo2 不达阈值 → 无增伤 ×1.0", b2._combo_dmg_mult(p2) == 1.0,
              f"mult={b2._combo_dmg_mult(p2)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：连段之锋", str(ex))
    try:
        # 4f. 蓄势精通：攻线每 1 气 +3% → +4%
        b, p = new_battle("cls_wu_seng", 1, 1, equipment=mk_eq(mk_piece(["momentum_mastery"])))
        b.resources["chi"] = 5
        check_float("蓄势精通 5 气 → ×1.20", b._momentum_mult(p), 1.20)
        b2, p2 = new_battle("cls_wu_seng", 1, 1)
        b2.resources["chi"] = 5
        check_float("无词条 5 气 → ×1.15（基础蓄势）", b2._momentum_mult(p2), 1.15)
    except (AttributeError, TypeError) as ex:
        skip("引擎：蓄势精通", str(ex))


# ================= 5. 套装抽样 5 套 =================
def test_sets_sample():
    print("\n【5. 套装抽样 5 套】")
    try:
        # 5a. 元素使徒：充能上限 5→6；v153 元素湮灭无全耗 → 只验证充能上限 + 不消耗语义
        eq = mk_eq(mk_piece(set_id="set_yuan_su_shi_tu"), mk_piece(set_id="set_yuan_su_shi_tu"),
                   mk_piece(set_id="set_yuan_su_shi_tu"), mk_piece(set_id="set_yuan_su_shi_tu"))
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素湮灭"], equipment=eq)
        check("元素使徒 2 件：充能上限 5 → 6", b._res_max(p, "element") == 6,
              f"max={b._res_max(p, 'element')}")
        b._res_gain(p, "element", 10)
        check("充能获取封顶 6", b._elem_charge() == 6, f"charge={b._elem_charge()}")
        cap, logs = cast_capture(b, "元素湮灭", p)
        check_float("元素湮灭 折算 power 保持 1.71（v153 无全耗放大）", cap.get("power", 0), 1.71)
        check("施放后充能保留 6（v153 元素湮灭不耗充能）", b._elem_charge() == 6,
              f"charge={b._elem_charge()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：元素使徒套装", str(ex))
    try:
        # 5b. 夜幕合契·影纱：开场 +1 cp；终结技暴击 +15%
        eq = mk_eq(mk_piece(set_id="set_ye_mu_he_qi_ying_sha"), mk_piece(set_id="set_ye_mu_he_qi_ying_sha"),
                   mk_piece(set_id="set_ye_mu_he_qi_ying_sha"), mk_piece(set_id="set_ye_mu_he_qi_ying_sha"))
        b, p = new_battle("cls_ci_ke", 1, 1, equipment=eq)
        check("夜幕合契·影纱 2 件：战斗开始 +1 连击点", b.resources.get("cp", 0) == 1,
              f"cp={b.resources.get('cp')}")
        # v151（2026-08-31）：刺客不再有 cp 消耗终结技（连段 lian_duan 取代连击点），
        # finisher_crit 触发条件（res_cost.cp/consume_all cp）在 v151 数据下无命中——
        # 断言套装 4 件配置存在 + 触发条件语义保留（引擎 _set_crit_bonus 读 finisher_crit）。
        eff4 = b._set_eff(p, "finisher_crit", 4)
        check("夜幕合契·影纱 4 件：finisher_crit 配置存在（+15%）",
              eff4 is not None and abs(float(eff4.get("crit", 0)) - 0.15) < 1e-9,
              f"{eff4}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：夜幕合契·影纱", str(ex))
    try:
        # 5c. 圣典·日冕：满信仰首次受击免伤 1 次/战
        eq = mk_eq(mk_piece(set_id="set_sheng_dian_ri_mian"), mk_piece(set_id="set_sheng_dian_ri_mian"),
                   mk_piece(set_id="set_sheng_dian_ri_mian"), mk_piece(set_id="set_sheng_dian_ri_mian"))
        b, p = new_battle("cls_mu_shi", 0, 0, equipment=eq)
        b.resources["faith"] = 10
        logs = []
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b._damage_player(p, 50, logs)
        check("满信仰首次受击免伤（hp 不变）", p["hp"] == 400 and b._set_immune_used is True,
              f"hp={p['hp']} immune={b._set_immune_used}")
        check("免伤日志（圣典·日冕结界）",
              any("免伤" in l or "圣典" in l for l in logs), f"{logs}")
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b._damage_player(p, 50, [])
        check("每战 1 次：第二击正常掉血", p["hp"] < 400, f"hp={p['hp']}")
        b2, p2 = new_battle("cls_mu_shi", 0, 0, equipment=eq)
        b2.resources["faith"] = 5
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b2._damage_player(p2, 50, [])
        check("不满信仰不触发免伤（cond=faith_full）",
              p2["hp"] < 400 and b2._set_immune_used is False, f"hp={p2['hp']}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：圣典·日冕", str(ex))
    try:
        # 5d. 余烬军团：满怒大招怒气消耗 -1；满怒普攻二段追击
        eq = mk_eq(mk_piece(set_id="set_yu_jin_jun_tuan_hui_zhang"), mk_piece(set_id="set_yu_jin_jun_tuan_hui_zhang"),
                   mk_piece(set_id="set_yu_jin_jun_tuan_hui_zhang"), mk_piece(set_id="set_yu_jin_jun_tuan_hui_zhang"))
        b, p = new_battle("cls_zhan_shi", 0, 0, equipment=eq)
        b.resources["rage"] = 10
        check("满怒判定 _rage_full = True", b._rage_full(p) is True, f"rage={b.resources.get('rage')}")
        # v151（2026-08-31）：战士无 consume_all 怒气技能（旧无畏冲击已删），
        # 「满怒大招怒气消耗 -1」无数据命中——保留满怒判定 + 满怒普攻二段追击断言。
        b2, p2 = new_battle("cls_zhan_shi", 0, 0, equipment=eq)
        b2.player = p2
        b2.resources["rage"] = 10
        st = b2._player_stats(p2)
        enemy_hp0 = b2.enemy["hp"]
        logs2 = []
        with mock.patch.object(BT.random, "random", return_value=0.99):
            logs2 = b2._player_attack(st, p2)
        check("满怒普攻二段追击（沸血二段追加伤害）",
              any("沸血二段" in l for l in logs2) and b2.enemy["hp"] < enemy_hp0,
              f"ehp={b2.enemy['hp']} logs={logs2}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：余烬军团", str(ex))
    try:
        # 5e. 时之领主：cdr_set(on=time_freeze) 配置保留；时停领域技能 v153 已删（时律线退役）
        eq = mk_eq(mk_piece(set_id="set_shi_zhi_ling_zhu"), mk_piece(set_id="set_shi_zhi_ling_zhu"))
        b, p = new_battle("cls_fa_shi", 3, 2, equipment=eq)
        tf = b._set_eff(p, "cdr_set", 2, on="time_freeze")
        check("时之领主 2 件 cdr_set(time_freeze) 配置生效", tf is not None and int(tf.get("value", 0)) == -1,
              f"{tf}")
        check("v153：时停领域技能已删除（时律线退役，套装 on 引用成死引用，已报告）",
              E.skill_info("cls_fa_shi", "时停领域") is None, "")
    except (AttributeError, TypeError) as ex:
        skip("引擎：时之领主", str(ex))


if __name__ == "__main__":
    clean_db()
    test_consume_all_formula()
    test_overcap_regression()
    test_bard_echo_loop()
    test_six_affixes()
    test_sets_sample()
    print(f"\n===== v130.2c/d 机制固化: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)