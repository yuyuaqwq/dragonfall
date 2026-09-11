# -*- coding: utf-8 -*-
"""5c P4 验证：Boss 剧本导演——连招链 chains / 爪牙死亡联动 on_minion_died。

- chains：seq 顺序轮换（auto_act 指向）→ 到头回绕；cd 整链冷却；charging 不出链
- on_minion_died（观察者）：heal_pct 回血 / stacks_clear 清叠层 / atk_up 提升

跑法：python tests/test_boss_script_p4.py
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


GID = "g_bs4"


def mk_snap(qid, name, cls="cls_zhan_shi", level=20):
    db.create_player(GID, qid, name, cls, {}, 100, 100)
    db.update_player(GID, qid, level=level, cur_map="mainland", cur_subarea="",
                     learned_skills=[], stamina=999,
                     attributes=json.dumps({"str": 5, "agi": 5, "int": 5, "vit": 5}))
    pl = db.get_player(GID, qid)
    st = player_final_stats(cls, level, {}, 0, pl.get("attributes"), 0, {}, pl.get("race"))
    mh = int(st.get("max_hp", 100))
    db.update_player(GID, qid, max_hp=mh, max_mp=50, hp=mh, mp=50)
    pl = db.get_player(GID, qid)
    return {"name": name, "qq_id": qid, "class_name": cls, "level": level,
            "hp": int(pl.get("hp", 0)), "max_hp": mh, "mp": 50, "max_mp": 50,
            "equipment": {}, "skills": [], "learned_skills": [],
            "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
            "bonus": {"panel": {}, "cap": {}, "cost": {}}, "race": pl.get("race"), "uid": f"p_{qid}",
            "buffs": {}, "stacks": {}, "defending": False, "charging": None,
            "ct": 0.0, "p_shields": {}, "spd": int(st.get("spd", 0) or 0)}


def mk_env():
    boss = {"uid": "e_boss", "id": "b_moro", "name": "深渊领主·摩罗",
            "role": "boss", "is_boss": True, "hp": 50000, "max_hp": 50000,
            "atk": 300, "matk": 200, "def": 100, "mdef": 100, "spd": 100,
            "lv": 95, "skills": [], "effects": {}, "shields": {},
            "auto_act": None, "ct": 0.0}
    st = {"type": "instance", "inst_id": "inst_test", "leader": "80001",
          "members": ["80001"], "alive": {"80001": True},
          "players": {"80001": mk_snap(80001, "勇者")},
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


def mk_cfg(chains=None, on_minion_died=None):
    return {"mech": ["phase"], "opening": None, "triggers": {}, "phases": [],
            "chains": chains, "on_interrupt": None, "on_minion_died": on_minion_died}


def test_1_chains_rotate():
    print("【1. chains：seq 顺序轮换 + 到头回绕】")
    b, boss, st = mk_env()
    seq4 = ["ms_a1", "ms_a2", "ms_a3", "ms_a4"]
    cfg = mk_cfg(chains=[{"seq": seq4, "cd": 0, "break": 0.0}])
    bs = BS._new_script_state()
    picked = []
    for rn in range(1, 9):
        bs["round_no"] = rn
        logs = []
        BS._check_chains(st, b, boss, cfg, bs, float(rn), logs)
        aa = (boss.get("auto_act") or {}).get("act", {})
        picked.append(aa.get("skill"))
    check("前 4 帧依次 1-4 招", picked[:4] == seq4, f"picked={picked}")
    check("第 5 帧回绕到第 1 招（cd=0 无缝）", picked[4] == "ms_a1", f"picked={picked}")
    check("chain_pos 停在链尾 4（下帧重置回绕）", (bs.get("chain_pos") or 0) == 4,
          f"pos={bs.get('chain_pos')}")


def test_2_chains_cd():
    print("【2. chains cd=1：链尾后隔 1 帧冷却再起】")
    b, boss, st = mk_env()
    cfg = mk_cfg(chains=[{"seq": ["ms_x1", "ms_x2"], "cd": 1, "break": 0.0}])
    bs = BS._new_script_state()
    picked = []
    for rn in range(1, 9):
        bs["round_no"] = rn
        BS._check_chains(st, b, boss, cfg, bs, float(rn), [])
        picked.append((boss.get("auto_act") or {}).get("act", {}).get("skill"))
    # rn1 x1, rn2 x2（链尾 until=3）→ rn3 冷却 → rn4 x1 起新轮
    check("rn1=x1 rn2=x2", picked[0] == "ms_x1" and picked[1] == "ms_x2", f"{picked}")
    check("rn3 冷却（沿用上一招 auto_act）", picked[2] == "ms_x2", f"{picked}")
    check("rn4 新轮 x1", picked[3] == "ms_x1", f"{picked}")


def test_3_chains_charging():
    print("【3. chains：charging 读条中不出链】")
    b, boss, st = mk_env()
    cfg = mk_cfg(chains=[{"seq": ["ms_a1"], "cd": 0, "break": 0.0}])
    boss["charging"] = {"skill": "ms_ju_qi", "until": 99}
    bs = BS._new_script_state()
    bs["round_no"] = 1
    BS._check_chains(st, b, boss, cfg, bs, 1.0, [])
    check("charging 中 auto_act 未改", not (boss.get("auto_act") or {}).get("act", {}).get("skill"),
          str(boss.get("auto_act")))


def test_4_minion_died_heal():
    print("【4. on_minion_died heal_pct：爪牙死 → Boss 回 3%】")
    b, boss, st = mk_env()
    boss["hp"] = int(boss["max_hp"] * 0.50)
    cfg = mk_cfg(on_minion_died={"effect": "heal_pct", "value": 0.03})
    dead = {"uid": "e_min_1", "name": "咕噜的打手", "is_minion": True, "hp": 0}
    obs = BS.make_script_event(st)
    hp0 = boss["hp"]
    logs = []
    obs(b, "on_death", {"actor": dead}, logs)
    gain = boss["hp"] - hp0
    check("Boss 回 3%（1500）", 0 < gain <= int(50000 * 0.03) + 2,
          f"hp {hp0}->{boss['hp']} gain={gain}")
    check("日志含联动", any("恢复" in x for x in logs), str(logs))


def test_5_minion_died_stacks_clear():
    print("【5. on_minion_died stacks_clear：清叠层强化（直调分支）】")
    b, boss, st = mk_env()
    bs = st["boss_script"] = BS._new_script_state()
    bs["stacks_n"] = 3
    boss["effects"]["boss_mech_stacks_atk"] = {"stat": "atk", "op": "mul",
                                               "mult": 1.24, "stacks": 1}
    logs = []
    BS._minion_death_link(st, b, boss, {"effect": "stacks_clear", "value": 1}, logs)
    check("stacks_n 清零", bs.get("stacks_n") == 0, str(bs.get("stacks_n")))
    check("effects 移除", not (boss.get("effects") or {}).get("boss_mech_stacks_atk"),
          str(boss.get("effects")))


def test_6_minion_died_atk_up():
    print("【6. on_minion_died atk_up：Boss 攻击提升 ×1.30 时效（直调分支）】")
    b, boss, st = mk_env()
    b._now = 10.0
    logs = []
    BS._minion_death_link(st, b, boss, {"effect": "atk_up", "value": 2}, logs)
    ef = (boss.get("effects") or {}).get("boss_minion_atk")
    check("atk ×1.30", ef and abs(float(ef.get("mult")) - 1.30) < 0.001, str(ef))
    check("expire = now+2", ef and abs(float(ef.get("expire")) - 12.0) < 0.001, str(ef))


def test_7_minion_died_non_minion():
    print("【7. 非爪牙死亡不触发联动】")
    b, boss, st = mk_env()
    cfg = mk_cfg(on_minion_died={"effect": "heal_pct", "value": 0.03})
    boss["hp"] = int(boss["max_hp"] * 0.50)
    dead_elite = {"uid": "e_elite", "name": "精英", "is_minion": False, "hp": 0}
    obs = BS.make_script_event(st)
    hp0 = boss["hp"]
    obs(b, "on_death", {"actor": dead_elite}, [])
    check("精英死不回血", boss["hp"] == hp0, f"{hp0}->{boss['hp']}")


def main():
    print("5c P4 Boss 剧本导演：连招链 / 爪牙死亡联动")
    test_1_chains_rotate()
    test_2_chains_cd()
    test_3_chains_charging()
    test_4_minion_died_heal()
    test_5_minion_died_stacks_clear()
    test_6_minion_died_atk_up()
    test_7_minion_died_non_minion()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    if FAILURES:
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
