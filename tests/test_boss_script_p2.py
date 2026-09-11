# -*- coding: utf-8 -*-
"""5c P2 验证：Boss 剧本导演——开场技 / 玩家低血追击 / 简单机制 token。

直接单测 boss_script 导演函数（手写 cfg，逻辑干净可控）：
- opening atk_up：第一帧 → Boss atk/matk ×1.30 时效（expire=now+power）+ 演出
- opening mortal_wound：玩家 effects 落 mortal_wound 条目（吸血批消费预留）
- opening once（第二帧不重复）
- player_low：玩家低血 → 演出 + 本刻 atk ×1.25（once）；满血不触发
- stacks：每 2 刻 +1 cap5，atk mult 累计
- heal：每 4 刻回 8%
- enrage 补漏（phases 无 enrage phase）：血<30% once ×1.35
- shield：开战 once 20% 盾
- 简单机制帧不拦截行动（非演出刻）

跑法：python tests/test_boss_script_p2.py
"""
import os
import sys
import tempfile
import json

os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.mkdtemp(), "game.db")
os.environ["GWEN_TEST_MODE"] = "1"
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
sys.path.insert(0, _PLUGIN_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from battle2 import config as _b2c  # noqa: E402
from game.content_rules.apply import ensure_engine_configured as _eng_cfg; _eng_cfg()  # noqa: E402
from game.store.connection import init_db  # noqa: E402
init_db()

from game import content as C  # noqa: E402
from game import db  # noqa: E402
from game.content_rules.panel import player_final_stats
from game.commands import instance_battle as IB  # noqa: E402
from game.commands import boss_script as BS  # noqa: E402
from battle2 import Battle as B2  # noqa: E402

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


GID = "g_bs2"


def mk_snap(qid, name, cls="cls_zhan_shi", level=20, hp_pct=1.0):
    db.create_player(GID, qid, name, cls, {}, 100, 100)
    db.update_player(GID, qid, level=level, cur_map="mainland", cur_subarea="",
                     learned_skills=[], stamina=999,
                     attributes=json.dumps({"str": 5, "agi": 5, "int": 5, "vit": 5}))
    pl = db.get_player(GID, qid)
    st = player_final_stats(cls, level, {}, 0, pl.get("attributes"), 0, {}, pl.get("race"))
    mh = int(st.get("max_hp", 100))
    cur = max(1, int(mh * hp_pct))
    db.update_player(GID, qid, max_hp=mh, max_mp=50, hp=cur, mp=50)
    pl = db.get_player(GID, qid)
    return {"name": name, "qq_id": qid, "class_name": cls, "level": level,
            "hp": int(pl.get("hp", 0)), "max_hp": mh, "mp": 50, "max_mp": 50,
            "equipment": {}, "skills": [], "learned_skills": [],
            "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
            "bonus": {"panel": {}, "cap": {}, "cost": {}}, "race": pl.get("race"), "uid": f"p_{qid}",
            "buffs": {}, "stacks": {}, "defending": False, "charging": None,
            "ct": 0.0, "p_shields": {}, "spd": int(st.get("spd", 0) or 0)}


def mk_env(hp_pct=1.0, boss_hp_pct=1.0):
    """真 B2 battle（玩家 + 假 boss actor）+ 手写 cfg。返回 (battle, boss, cfg, st)。"""
    boss = {"uid": "e_test", "id": "b_test_boss", "name": "测试Boss", "role": "boss",
            "is_boss": True, "hp": int(10000 * boss_hp_pct), "max_hp": 10000,
            "atk": 200, "matk": 200, "def": 100, "mdef": 100, "spd": 100,
            "lv": 20, "skills": [], "effects": {}, "shields": {},
            "auto_act": None, "ct": 0.0}
    st = {"type": "instance", "inst_id": "inst_test", "leader": "80001",
          "members": ["80001"], "alive": {"80001": True},
          "players": {"80001": mk_snap(80001, "勇者", hp_pct=hp_pct)},
          "boss": boss, "enemy": boss, "enemies": [boss], "pets": {},
          "p_buffs": {"80001": {}}, "p_hot": {"80001": {}},
          "p_food_effects": {"80001": []}, "p_defending": {"80001": False},
          "mech_stacks": {"80001": {}}, "now": 0.0, "battle": None,
          "contribution": {}, "threat": {"80001": 0}, "over": False,
          "turn_time": 0, "stage_pending": [], "inst_stages": [],
          "stage_idx": 0, "stage_cleared": False, "world_id": ""}
    b = B2("instance", sides={"player": [dict(st["players"]["80001"],
                                              uid="p_80001", effects={})],
                              "enemy": [boss]})
    return b, boss, st


def mk_cfg(mech=None, opening=None, triggers=None, phases=None):
    return {"mech": mech or [], "opening": opening,
            "triggers": triggers or {}, "phases": phases or [],
            "chains": None, "on_interrupt": None, "on_minion_died": None}


def test_1_opening_atk_up():
    print("【1. opening atk_up：第一帧演出 + Boss atk/matk ×1.30 时效】")
    b, boss, st = mk_env()
    cfg = mk_cfg(mech=["phase_open"], opening={"name": "深渊咆哮", "effect": "atk_up",
                                               "power": 2})
    bs = BS._new_script_state()
    bs["round_no"] = 1
    logs = []
    BS._check_opening(st, b, boss, cfg, bs, 10.0, logs)
    joined = "\n".join(logs)
    check("演出文案", "深渊咆哮" in joined, joined)
    ef = boss.get("effects") or {}
    check("atk ×1.30", abs(float(ef["boss_open_atk"]["mult"]) - 1.30) < 0.001,
          str(ef.get("boss_open_atk")))
    check("matk ×1.30", abs(float(ef["boss_open_matk"]["mult"]) - 1.30) < 0.001)
    check("时效 expire = now+power", abs(float(ef["boss_open_atk"]["expire"]) - 12.0) < 0.001,
          str(ef["boss_open_atk"]))
    check("once 标记", bs["flags"].get("_open_played") is True)


def test_2_opening_once():
    print("【2. opening once：第二帧不重复】")
    b, boss, st = mk_env()
    cfg = mk_cfg(mech=["phase_open"], opening={"name": "深渊咆哮", "effect": "atk_up"})
    bs = BS._new_script_state()
    bs["round_no"] = 1
    logs = []
    BS._check_opening(st, b, boss, cfg, bs, 0.0, logs)
    n_ef = len((boss.get("effects") or {}).get("boss_open_atk", {}))
    bs["round_no"] = 2
    logs2 = []
    BS._check_opening(st, b, boss, cfg, bs, 1.0, logs2)
    check("第二帧无新演出", not any("深渊咆哮" in x for x in logs2), str(logs2))


def test_3_opening_mortal_wound():
    print("【3. opening mortal_wound：玩家落重创条目】")
    b, boss, st = mk_env()
    cfg = mk_cfg(mech=["phase_open"], opening={"name": "神罚·重创", "effect": "mortal_wound",
                                               "power": 2})
    bs = BS._new_script_state()
    bs["round_no"] = 1
    logs = []
    BS._check_opening(st, b, boss, cfg, bs, 5.0, logs)
    pa = b.sides_of("player")[0]
    mw = (pa.get("effects") or {}).get("mortal_wound")
    check("玩家 mortal_wound 条目存在", mw is not None and mw.get("stacks") == 1,
          str(pa.get("effects")))
    check("expire = now+power", mw and abs(float(mw.get("expire")) - 7.0) < 0.001,
          str(mw))
    check("演出含重创", any("重创" in x for x in logs), str(logs))


def test_4_player_low():
    print("【4. player_low：玩家低血 → 演出 + 本刻 ×1.25（once）】")
    b, boss, st = mk_env(hp_pct=0.20)  # 玩家 20% 血
    cfg = mk_cfg(mech=["player_low"], triggers={"player_low": {"hp": 0.3}})
    bs = BS._new_script_state()
    logs = []
    BS._check_player_low(st, b, boss, cfg, bs, 0.0, logs)
    joined = "\n".join(logs)
    check("演出（低血追击）", "低血" in joined or "重伤" in joined or "追击" in joined,
          joined)
    ef = boss.get("effects") or {}
    check("本刻 atk ×1.25", abs(float(ef["boss_low_atk"]["mult"]) - 1.25) < 0.001,
          str(ef.get("boss_low_atk")))
    # 满血玩家不触发
    b2, boss2, st2 = mk_env(hp_pct=1.0)
    cfg2 = mk_cfg(mech=["player_low"], triggers={"player_low": {"hp": 0.3}})
    bs2 = BS._new_script_state()
    logs2 = []
    BS._check_player_low(st2, b2, boss2, cfg2, bs2, 0.0, logs2)
    check("满血不触发", not logs2 and not (boss2.get("effects") or {}).get("boss_low_atk"),
          str(logs2))
    # 无 token 无 triggers 不触发
    b3, boss3, st3 = mk_env(hp_pct=0.10)
    bs3 = BS._new_script_state()
    logs3 = []
    BS._check_player_low(st3, b3, boss3, mk_cfg(mech=["phase"]), bs3, 0.0, logs3)
    check("无配置不触发", not logs3, str(logs3))


def test_5_stacks():
    print("【5. stacks：每 2 刻 +1 cap5，atk 累计 ×(1+0.08n)】")
    b, boss, st = mk_env()
    cfg = mk_cfg(mech=["stacks"])
    bs = BS._new_script_state()
    for rn in range(1, 13):
        bs["round_no"] = rn
        logs = []
        BS._check_simple_mech(st, b, boss, cfg, bs, float(rn), logs)
    n = bs.get("stacks_n")
    check("stacks_n cap 5", n == 5, f"n={n}")
    mult = float((boss.get("effects") or {}).get("boss_mech_stacks_atk", {}).get("mult", 0))
    check("atk mult = 1+0.08×5 = 1.40", abs(mult - 1.40) < 0.001, f"mult={mult}")


def test_6_heal():
    print("【6. heal：每 4 刻回 8%】")
    b, boss, st = mk_env(boss_hp_pct=0.50)
    boss["hp"] = int(boss["max_hp"] * 0.50)
    cfg = mk_cfg(mech=["heal"])
    bs = BS._new_script_state()
    hp0 = boss["hp"]
    bs["round_no"] = 4
    logs = []
    BS._check_simple_mech(st, b, boss, cfg, bs, 4.0, logs)
    gain = boss["hp"] - hp0
    expect = int(10000 * 0.08)
    check("第 4 刻回 8%（≈800）", hp0 < boss["hp"] <= hp0 + expect + 2,
          f"hp {hp0}->{boss['hp']} gain={gain}")
    # 非 4 的倍数不回
    hp1 = boss["hp"]
    bs["round_no"] = 5
    BS._check_simple_mech(st, b, boss, cfg, bs, 5.0, [])
    check("非 4 刻不回", boss["hp"] == hp1)


def test_7_enrage_fallback():
    print("【7. enrage 补漏：phases 无 enrage → 血<30% once ×1.35】")
    b, boss, st = mk_env(boss_hp_pct=0.25)
    cfg = mk_cfg(mech=["enrage", "phase"], phases=[{"min": 60, "add_skills": []}])
    bs = BS._new_script_state()
    logs = []
    BS._check_simple_mech(st, b, boss, cfg, bs, 3.0, logs)
    joined = "\n".join(logs)
    check("演出狂暴", "狂暴" in joined, joined)
    mult = float((boss.get("effects") or {}).get("boss_enrage_atk", {}).get("mult", 0))
    check("atk ×1.35", abs(mult - 1.35) < 0.001, f"mult={mult}")
    check("once 标记", bs.get("flags", {}).get("_enraged") is True)
    # 满血不触发
    b2, boss2, st2 = mk_env()
    bs2 = BS._new_script_state()
    BS._check_simple_mech(st2, b2, boss2, mk_cfg(mech=["enrage"]), bs2, 1.0, [])
    check("满血不狂暴", not (boss2.get("effects") or {}).get("boss_enrage_atk"),
          str(boss2.get("effects")))


def test_8_enrage_phase_covers():
    print("【8. phases 含 enrage phase → enrage token 由 phases 管（不重复）】")
    b, boss, st = mk_env(boss_hp_pct=0.25)
    cfg = mk_cfg(mech=["enrage"], phases=[{"min": 60, "phase_id": "enrage"}])
    bs = BS._new_script_state()
    logs = []
    BS._check_simple_mech(st, b, boss, cfg, bs, 1.0, logs)
    check("enrage token 跳过（无 ×1.35 演出）",
          not (boss.get("effects") or {}).get("boss_enrage_atk"), str(logs))


def test_9_shield():
    print("【9. shield：开战 once 20% 护盾】")
    b, boss, st = mk_env()
    cfg = mk_cfg(mech=["shield"])
    bs = BS._new_script_state()
    logs = []
    BS._check_simple_mech(st, b, boss, cfg, bs, 1.0, logs)
    sh = boss.get("shields") or {}
    total = sum(int(s.get("value", 0) or 0) for s in sh.values())
    check("护盾 = 20% max_hp（2000）", total == 2000, f"shields={sh} total={total}")
    check("护盾 halve 标记", any(s.get("halve") for s in sh.values()), str(sh))
    check("once（二帧不再加）", bs.get("flags", {}).get("_shielded") is True)


def test_10_simple_mech_no_skip():
    print("【10. 简单机制帧不拦截行动（非演出刻）】")
    b, boss, st = mk_env()
    cfg = mk_cfg(mech=["stacks"])
    bs = BS._new_script_state()
    bs["round_no"] = 2
    # stacks 触发后 _check_phases 空 phases 返回 False → 不 skip
    skip = BS._check_phases(st, b, boss, cfg, bs, [])
    check("空 phases 不 skip", skip is False, f"skip={skip}")


def main():
    print("5c P2 Boss 剧本导演：开场技 / 低血追击 / 简单机制")
    test_1_opening_atk_up()
    test_2_opening_once()
    test_3_opening_mortal_wound()
    test_4_player_low()
    test_5_stacks()
    test_6_heal()
    test_7_enrage_fallback()
    test_8_enrage_phase_covers()
    test_9_shield()
    test_10_simple_mech_no_skip()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    if FAILURES:
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
