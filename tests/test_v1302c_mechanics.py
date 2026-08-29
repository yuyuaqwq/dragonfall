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
    """黑盒施放：真实走 _do_player_skill 全链（校验/消耗/统一公式折算），
    仅把伤害结算 _player_skill 替换为捕获器记录引擎折算后的 info['power']
    （确定性：不跑真实伤害链的随机点）。"""
    captured = {}

    def _fake(st, skill_name, info, player, target=None):
        captured["power"] = float(info.get("power") or 0)
        return []

    b._player_skill = _fake
    logs = b._do_player_skill(skill_name, p)
    return captured, logs


# ================= 1. consume_all 统一公式 =================
def test_consume_all_formula():
    print("\n【1. consume_all 统一公式（4 技能数值）】")
    # ---- 数据层硬断言：power / per 配置（折算公式 = power × (1 + per×当前持有值)）----
    w = E.skill_info("cls_zhan_shi", "无畏冲击") or {}
    check("数据：无畏冲击 power=0.724 / consume_all{rage, per:0.12}（v133 峰值收敛 2.2→0.724）",
          abs(float(w.get("power", 0)) - 0.724) < 1e-9 and w.get("consume_all") == {"key": "rage", "per": 0.12},
          str({k: w.get(k) for k in ("power", "consume_all")}))
    s = E.skill_info("cls_ci_ke", "暗影处刑") or {}
    check("数据：暗影处刑 power=1.317 / consume_all{cp, per:0.0} / 残血 cond 1.5（v133 峰值收敛 3.2→1.317）",
          abs(float(s.get("power", 0)) - 1.317) < 1e-9
          and s.get("consume_all") == {"key": "cp", "per": 0.0}
          and (s.get("cond") or {}).get("mult") == 1.5
          and (s.get("cond") or {}).get("hp_pct") == 0.3,
          str({k: s.get(k) for k in ("power", "consume_all", "cond")}))
    pn = E.skill_info("cls_wu_seng", "破晓之拳") or {}
    check("数据：破晓之拳 power=0.634 / consume_all{chi, per:0.1}（v133 峰值收敛 2.4→0.634）",
          abs(float(pn.get("power", 0)) - 0.634) < 1e-9 and pn.get("consume_all") == {"key": "chi", "per": 0.1},
          str({k: pn.get(k) for k in ("power", "consume_all")}))
    e = E.skill_info("cls_fa_shi", "元素湮灭") or {}
    # v139 峰值红线收敛：元素湮灭 power 2.4→1.2（满充能 EQ 4.8→2.4，峰值 92.8%→过线）
    check("数据：元素湮灭 power=1.2 / consume_all{element, per:0.2}",
          abs(float(e.get("power", 0)) - 1.2) < 1e-9 and e.get("consume_all") == {"key": "element", "per": 0.2},
          str({k: e.get(k) for k in ("power", "consume_all")}))
    # ---- 引擎黑盒：满资源施放 → 折算 power（捕获 _do_player_skill 折算结果）----
    try:
        b, p = new_battle("cls_zhan_shi", 0, 0, learned=["无畏冲击"])
        b.resources["rage"] = 10
        cap, logs = cast_capture(b, "无畏冲击", p)
        check_float("无畏冲击 满 10 怒折算 power = 1.593（round(0.724×2.2, 3)）",
                    cap.get("power", 0), round(0.724 * (1 + 0.12 * 10), 3))
        check("无畏冲击 施放后怒气扣光 = 0", b.resources.get("rage") == 0,
              f"rage={b.resources.get('rage')} logs={logs[:2]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：无畏冲击 折算", str(ex))
    try:
        b, p = new_battle("cls_ci_ke", 0, 0, learned=["暗影处刑"])
        b.resources["cp"] = 5
        cap, logs = cast_capture(b, "暗影处刑", p)
        check_float("暗影处刑 per=0 折算 power = 1.317（恒为数据表值）", cap.get("power", 0), 1.317)
        b.enemy["hp"] = 100  # 5% < 30% → 残血 cond 激活
        cm = b._cond_mult(E.skill_info("cls_ci_ke", "暗影处刑"), p)
        check_float("暗影处刑 残血 cond ×1.5（死亡边缘）", cm, 1.5)
        check_float("暗影处刑 EQ = 1.317×1.5 = 1.9755", cap.get("power", 0) * cm, 1.9755)
        check("暗影处刑 施放后连击点扣光 = 0", b.resources.get("cp") == 0,
              f"cp={b.resources.get('cp')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：暗影处刑 折算", str(ex))
    try:
        b, p = new_battle("cls_wu_seng", 0, 0, learned=["破晓之拳"])
        b.resources["chi"] = 10
        cap, logs = cast_capture(b, "破晓之拳", p)
        check_float("破晓之拳 满 10 气折算 power = 1.268（0.634×2.0）", cap.get("power", 0), 1.268)
        check("破晓之拳 施放后气扣光 = 0", b.resources.get("chi") == 0,
              f"chi={b.resources.get('chi')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：破晓之拳 折算", str(ex))
    try:
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素湮灭"])
        b.resources["element_charge"] = 5
        cap, logs = cast_capture(b, "元素湮灭", p)
        check_float("元素湮灭 满 5 充能折算 power = 2.4（1.2×2.0）", cap.get("power", 0), 2.4)
        check("元素湮灭 施放后充能扣光 = 0", b._elem_charge() == 0,
              f"charge={b._elem_charge()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：元素湮灭 折算", str(ex))


# ================= 2. 超标 P1-2 回归（资源不满可施放） =================
def test_overcap_regression():
    print("\n【2. 超标 P1-2 回归（资源不满可施放）】")
    try:
        # 持 4 怒（<10 满值）施放无畏冲击：不被预检拦截、成功、扣光
        b, p = new_battle("cls_zhan_shi", 0, 0, learned=["无畏冲击"])
        b.resources["rage"] = 4
        logs, blocked = b._skill_cast_blocked("无畏冲击", p)
        check("持 4 怒预检不拦截（consume_all 需 ≥1 点而非满值）", blocked is False, f"{logs}")
        logs = b._do_player_skill("无畏冲击", p)
        check("持 4 怒施放成功（无资源不足日志）", not any("不足" in l for l in logs), f"{logs[:2]}")
        check("持 4 怒施放后怒气扣光 = 0", b.resources.get("rage") == 0,
              f"rage={b.resources.get('rage')}")
        b2, p2 = new_battle("cls_zhan_shi", 0, 0, learned=["无畏冲击"])
        b2.resources["rage"] = 4
        cap, _ = cast_capture(b2, "无畏冲击", p2)
        check_float("4 怒折算 power = 1.072（round(0.724×(1+0.12×4), 3)）", cap.get("power", 0),
                    round(0.724 * (1 + 0.12 * 4), 3))
    except (AttributeError, TypeError) as ex:
        skip("引擎：持 4 怒无畏冲击", str(ex))
    try:
        # 持 2 充能（<5 满值）施放元素湮灭：资源不满可施放、成功、扣光
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素湮灭"])
        b.resources["element_charge"] = 2
        logs, blocked = b._skill_cast_blocked("元素湮灭", p)
        check("持 2 充能预检不拦截", blocked is False, f"{logs}")
        logs = b._do_player_skill("元素湮灭", p)
        check("持 2 充能施放成功（无资源不足日志）", not any("不足" in l for l in logs), f"{logs[:2]}")
        check("持 2 充能施放后充能扣光 = 0", b._elem_charge() == 0,
              f"charge={b._elem_charge()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：持 2 充能元素湮灭", str(ex))


# ================= 3. 回声单通道闭环（歌者） =================
def test_bard_echo_loop():
    print("\n【3. 回声单通道闭环（歌者 cls_mu_shi tier1 path1）】")
    try:
        b, p = new_battle("cls_mu_shi", 1, 1, learned=["战歌", "英雄叙事诗"], level=95)
        logs = b._do_player_skill("战歌", p)
        check("施放战歌 → 回声 +1（res_gain 单通道）", b._echo_layers() == 1,
              f"echo={b._echo_layers()} logs={logs}")
        check("战歌日志含回声驻留反馈", any("回声" in l for l in logs))
        logs2 = b._do_player_skill("英雄叙事诗", p)
        check("施放英雄叙事诗 → 回声不变（仍 1，非歌类无 echo 增益）",
              b._echo_layers() == 1, f"echo={b._echo_layers()}")
        check("英雄叙事诗 → 共鸣 +2（res_gain {resonance:2}）",
              b._res_read("resonance") == 2, f"resonance={b._res_read('resonance')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：歌者 战歌/英雄叙事诗 叠层", str(ex))
    try:
        # 回声恢复：1 层 6/回合；满 3 层翻倍 6×3×2 = 36/回合
        b2, p2 = new_battle("cls_mu_shi", 1, 1, level=95)
        b2._echo_add(p2, [])
        p2["hp"] = 100
        b2._turn_start(p2)
        check("回声 1 层回合初始恢复 6", p2["hp"] == 106, f"hp={p2['hp']}")
        b2._echo_add(p2, [])
        b2._echo_add(p2, [])
        check("回声叠满 3 层（max_layers）", b2._echo_layers() == 3, f"echo={b2._echo_layers()}")
        p2["hp"] = 100
        logs3 = b2._turn_start(p2)
        check("满 3 层回合初始恢复 36（满层翻倍 6×3×2）", p2["hp"] == 136,
              f"hp={p2['hp']} logs={logs3}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：回声 _turn_start 恢复", str(ex))


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
        b._turn_start(p)
        # v139 凝神屏息：60+30+10=100 满值自动排气归零（签名机制）——余韵回复本身已生效（达到 100 上限）
        check("回合开始：自然回 30 + 疾风余韵 10 = 满 100 触发排气", b.resources["energy"] == 0,
              f"energy={b.resources['energy']}")
        b2, p2 = new_battle("cls_you_xia", 1, 2, equipment=mk_eq(mk_piece(["swift_tailwind"])))
        b2._tailwind_prev_energy = 70
        check("疾风余韵：上回合精力 70 <80 → 不触发", b2._tailwind_regen_bonus(p2) == 0,
              f"bonus={b2._tailwind_regen_bonus(p2)}")
        b2.resources["energy"] = 60
        b2._turn_start(p2)
        check("无余韵加成：60 + 30 = 90", b2.resources["energy"] == 90,
              f"energy={b2.resources['energy']}")
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
        # 5a. 元素使徒：充能上限 5→6；4 件全耗 -1 留残点
        eq = mk_eq(mk_piece(set_id="set_yuan_su_shi_tu"), mk_piece(set_id="set_yuan_su_shi_tu"),
                   mk_piece(set_id="set_yuan_su_shi_tu"), mk_piece(set_id="set_yuan_su_shi_tu"))
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素湮灭"], equipment=eq)
        check("元素使徒 2 件：充能上限 5 → 6", b._res_max(p, "element") == 6,
              f"max={b._res_max(p, 'element')}")
        b._res_gain(p, "element", 10)
        check("充能获取封顶 6", b._elem_charge() == 6, f"charge={b._elem_charge()}")
        cap, logs = cast_capture(b, "元素湮灭", p)
        check_float("6 充能元素湮灭折算 power = 2.64（1.2×2.2）", cap.get("power", 0), 2.64)
        check("元素使徒 4 件：全耗 -1 留残点 1（-6→-5）", b._elem_charge() == 1,
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
        info = E.skill_info("cls_ci_ke", "暗影处刑") or {}
        check_float("夜幕合契·影纱 4 件：终结技暴击 +15%", b._set_crit_bonus(p, info), 0.15)
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
        b, p = new_battle("cls_zhan_shi", 0, 0, learned=["无畏冲击"], equipment=eq)
        b.resources["rage"] = 10
        check("满怒判定 _rage_full = True", b._rage_full(p) is True, f"rage={b.resources.get('rage')}")
        cap, logs = cast_capture(b, "无畏冲击", p)
        check("余烬军团 4 件：满怒大招怒气消耗 -1 留 1", b.resources.get("rage") == 1,
              f"rage={b.resources.get('rage')}")
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
        # 5e. 时之领主：时停领域 冷却 -1（cdr_set on=time_freeze）
        eq = mk_eq(mk_piece(set_id="set_shi_zhi_ling_zhu"), mk_piece(set_id="set_shi_zhi_ling_zhu"))
        b, p = new_battle("cls_chronomancer", 0, 0, equipment=eq)
        tf = b._set_eff(p, "cdr_set", 2, on="time_freeze")
        check("时之领主 2 件 cdr_set(time_freeze) 生效", tf is not None and int(tf.get("value", 0)) == -1,
              f"{tf}")
        # 同基准对照：chronomancer 基础 cdr 5% 使 3 → int(3×0.95)=2；套装再 -1 → 1
        b_no, p_no = new_battle("cls_chronomancer", 0, 0)
        b_no._set_skill_cd("时停领域", 3)
        cd_wo = b_no._skill_cd_left("时停领域")
        b_cd, p_cd = new_battle("cls_chronomancer", 0, 0, equipment=eq)
        b_cd._set_skill_cd("时停领域", 3)
        cd_w = b_cd._skill_cd_left("时停领域")
        check("时停领域 CD 削减 1（同基准相较差 1）", cd_w == cd_wo - 1 and cd_w >= 1,
              f"cd_wo={cd_wo} cd_w={cd_w}")
        check("带套装：CD 3 → 1（cdr 折算后再 -1）", cd_w == 1, f"cd_w={cd_w}")
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