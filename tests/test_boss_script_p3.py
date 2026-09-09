# -*- coding: utf-8 -*-
"""5c P3 验证：Boss 剧本导演——召唤援军（mech summon / v163 口径）。

- CD 5 刻（round_no 6 首召；距上次 <5 不召）
- 模板：INSTANCES[inst_id].minions[0].monster（v163 同图小怪模板）；
  无 inst/无 minions → 回落 Boss×0.2
- 上限 3（含开怪自带爪牙存活 is_minion；满员不召）
- 召唤物字段：uid 唯一 / is_minion / rank1 / mech="" / ct=now+2
- M-W2s：召唤物插 enemy side 队首（前排挡刀——存活序列第一名即新援军，
  玩家默认目标/a1 编号先打它；旧 append 尾部 = 后排不挡刀）
- Boss 攻击联动 atk×1.30（旧 mon_atk_up 线上行为）

跑法：python tests/test_boss_script_p3.py
"""
import os
import sys
import tempfile
import json

os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.mkdtemp(), "game.db")
os.environ["GWEN_TEST_MODE"] = "1"
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PLUGIN_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.battle2 import config as _b2c  # noqa: E402
_b2c.load_game_defaults()  # noqa: E402
from game.store.connection import init_db  # noqa: E402
init_db()

from game import content as C  # noqa: E402
from game import db  # noqa: E402
from game import engine as E  # noqa: E402
from game.commands import boss_script as BS  # noqa: E402
from game.battle2 import Battle as B2  # noqa: E402

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


GID = "g_bs3"


def mk_snap(qid, name, cls="cls_zhan_shi", level=20):
    db.create_player(GID, qid, name, cls, {}, 100, 100)
    db.update_player(GID, qid, level=level, cur_map="mainland", cur_subarea="",
                     learned_skills=[], stamina=999,
                     attributes=json.dumps({"str": 5, "agi": 5, "int": 5, "vit": 5}))
    pl = db.get_player(GID, qid)
    st = E.player_final_stats(cls, level, {}, 0, pl.get("attributes"), 0, {}, pl.get("race"))
    mh = int(st.get("max_hp", 100))
    db.update_player(GID, qid, max_hp=mh, max_mp=50, hp=mh, mp=50)
    pl = db.get_player(GID, qid)
    return {"name": name, "qq_id": qid, "class_name": cls, "level": level,
            "hp": int(pl.get("hp", 0)), "max_hp": mh, "mp": 50, "max_mp": 50,
            "equipment": {}, "skills": [], "learned_skills": [],
            "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
            "stat_bonus": {}, "race": pl.get("race"), "uid": f"p_{qid}",
            "buffs": {}, "stacks": {}, "defending": False, "charging": None,
            "ct": 0.0, "p_shields": {}, "spd": int(st.get("spd", 0) or 0)}


def mk_env(inst_id="inst_goblin_camp", extra_minions=0):
    """真 B2 battle（玩家 + Boss actor + 可选预置爪牙）。st.inst_id 决定召唤模板。"""
    boss = {"uid": "e_test_boss", "id": "b_goblin_chief", "name": "哥布林酋长·咕噜",
            "role": "boss", "is_boss": True, "hp": 50000, "max_hp": 50000,
            "atk": 300, "matk": 200, "def": 100, "mdef": 100, "spd": 100,
            "lv": 20, "skills": [], "effects": {}, "shields": {},
            "auto_act": None, "ct": 0.0, "map": inst_id}
    enemies = [boss]
    for i in range(extra_minions):
        enemies.append({"uid": f"e_open_min_{i}", "name": "哥布林打手", "role": "tank",
                        "hp": 1000, "max_hp": 1000, "atk": 50, "matk": 10,
                        "def": 50, "mdef": 50, "spd": 60, "lv": 15,
                        "is_minion": True, "is_boss": False, "is_elite": False,
                        "rank": 1, "reach": 1, "mech": "", "effects": {},
                        "shields": {}, "ct": 1.0, "side": "enemy"})
    st = {"type": "instance", "inst_id": inst_id, "leader": "80001",
          "members": ["80001"], "alive": {"80001": True},
          "players": {"80001": mk_snap(80001, "勇者")},
          "boss": boss, "enemy": boss, "enemies": enemies, "pets": {},
          "p_buffs": {"80001": {}}, "p_hot": {"80001": {}},
          "p_food_effects": {"80001": []}, "p_defending": {"80001": False},
          "mech_stacks": {"80001": {}}, "now": 0.0, "battle": None,
          "contribution": {}, "threat": {"80001": 0}, "over": False,
          "turn_time": 0, "stage_pending": [], "inst_stages": [],
          "stage_idx": 0, "stage_cleared": False, "world_id": ""}
    b = B2("instance", sides={"player": [dict(st["players"]["80001"],
                                              uid="p_80001", effects={})],
                              "enemy": enemies})
    b._now = 0.0
    return b, boss, st


def mk_cfg():
    return {"mech": ["summon", "phase"], "opening": None, "triggers": {},
            "phases": [], "chains": None, "on_interrupt": None,
            "on_minion_died": None}


def test_1_summon_cd():
    print("【1. 召唤 CD：round_no 6 首召；中间帧不召】")
    b, boss, st = mk_env()
    cfg = mk_cfg()
    bs = BS._new_script_state()
    summoned_at = []
    for rn in range(1, 12):
        bs["round_no"] = rn
        logs = []
        BS._check_summon(st, b, boss, cfg, bs, float(rn), logs)
        if any("召唤了" in x for x in logs):
            summoned_at.append(rn)
    check("首召在 round_no=5（CD 5，对齐旧 r%5==0）", summoned_at == [5, 10],
          f"summoned_at={summoned_at}")
    mins = [u for u in b.sides_of("enemy") if u.get("is_minion")]
    check("召唤物入 enemy side（2 只）", len(mins) == 2, f"n={len(mins)}")


def test_2_summon_template():
    print("【2. 召唤物 = inst.minions 模板（v163：哥布林营地 → 哥布林守卫）】")
    b, boss, st = mk_env(inst_id="inst_goblin_camp")
    cfg = mk_cfg()
    bs = BS._new_script_state()
    bs["round_no"] = 6
    logs = []
    BS._check_summon(st, b, boss, cfg, bs, 6.0, logs)
    mins = [u for u in b.sides_of("enemy") if u.get("is_minion")]
    check("召唤 1 只", len(mins) == 1, f"n={len(mins)}")
    m = mins[0]
    check("名字 = Boss的{模板名}", "咕噜的" in (m.get("name") or ""), m.get("name"))
    check("is_minion True / is_boss False",
          m.get("is_minion") is True and m.get("is_boss") is False, str(m))
    check("rank/reach = 1", m.get("rank") == 1 and m.get("reach") == 1)
    check("mech 清空（防递归剧本）", not (m.get("mech") or ""), m.get("mech"))
    check("uid 唯一", m.get("uid", "").startswith("e_min_"), m.get("uid"))
    check("ct = now+2（不插队）", abs(float(m.get("ct", 0)) - 8.0) < 0.01,
          f"ct={m.get('ct')}")
    check("Boss 攻击联动 atk×1.30",
          abs(float((boss.get("effects") or {}).get("boss_summon_atk", {}).get("mult", 0)) - 1.30) < 0.001,
          str((boss.get("effects") or {}).get("boss_summon_atk")))


def test_3_summon_fallback():
    print("【3. 无 inst minions 模板 → 回落 Boss×0.2】")
    b, boss, st = mk_env(inst_id="inst_test")
    cfg = mk_cfg()
    bs = BS._new_script_state()
    bs["round_no"] = 6
    logs = []
    BS._check_summon(st, b, boss, cfg, bs, 6.0, logs)
    mins = [u for u in b.sides_of("enemy") if u.get("is_minion")]
    check("回落路径召唤成功", len(mins) == 1, f"n={len(mins)}")
    if mins:
        m = mins[0]
        check("血量 = Boss×0.2（10000）", int(m.get("max_hp", 0)) == 10000,
              f"mh={m.get('max_hp')}")


def test_4_summon_cap():
    print("【4. 上限 3（含开怪自带爪牙）：满员不召】")
    b, boss, st = mk_env(extra_minions=2)
    cfg = mk_cfg()
    bs = BS._new_script_state()
    # 2 预置爪牙 → rn6 召 1 = 3
    bs["round_no"] = 6
    logs = []
    BS._check_summon(st, b, boss, cfg, bs, 6.0, logs)
    mins = [u for u in b.sides_of("enemy") if u.get("is_minion")]
    check("预置 2 + 召 1 = 3", len(mins) == 3, f"n={len(mins)}")
    # rn11 CD 到但满员 → 不召
    n_before = len(b.sides_of("enemy"))
    bs["round_no"] = 11
    logs2 = []
    BS._check_summon(st, b, boss, cfg, bs, 11.0, logs2)
    check("满员不召（enemy side 不增）", len(b.sides_of("enemy")) == n_before,
          f"{n_before}->{len(b.sides_of('enemy'))}")
    check("无召唤日志", not any("召唤了" in x for x in logs2), str(logs2))


def test_5_summon_dead_minion_recycle():
    print("【5. 死亡爪牙不占上限（计数存活 is_minion）】")
    b, boss, st = mk_env(extra_minions=3)
    cfg = mk_cfg()
    bs = BS._new_script_state()
    # 3 预置爪牙但 1 只死亡 → 场上存活 2 → rn6 可召 1
    dead = [u for u in b.sides_of("enemy") if u.get("is_minion")][0]
    dead["hp"] = 0
    bs["round_no"] = 6
    logs = []
    BS._check_summon(st, b, boss, cfg, bs, 6.0, logs)
    mins_alive = [u for u in b.sides_of("enemy")
                  if u.get("is_minion") and int(u.get("hp", 0) or 0) > 0]
    check("死亡爪牙不占位（存活 3）", len(mins_alive) == 3,
          f"alive_min={len(mins_alive)}")
    check("召唤成功（有日志）", any("召唤了" in x for x in logs), str(logs))


def test_6_summon_no_token():
    print("【6. 无 summon token 不召唤】")
    b, boss, st = mk_env()
    cfg = mk_cfg()
    cfg["mech"] = ["phase"]
    bs = BS._new_script_state()
    bs["round_no"] = 6
    logs = []
    BS._check_summon(st, b, boss, cfg, bs, 6.0, logs)
    mins = [u for u in b.sides_of("enemy") if u.get("is_minion")]
    check("无 token 不召", not mins and not logs, str(logs))


def test_7_summon_front_row():
    print("【7. 召唤物插队首前排挡刀（M-W2s：append 尾部=后排 bug 修复）】")
    # 无预置爪牙：召唤后召唤物 = enemy side 第 0 位（Boss 身前）
    b, boss, st = mk_env(inst_id="inst_goblin_camp")
    cfg = mk_cfg()
    bs = BS._new_script_state()
    bs["round_no"] = 6
    logs = []
    BS._check_summon(st, b, boss, cfg, bs, 6.0, logs)
    es = b.sides_of("enemy")
    check("召唤物在 enemy side 队首（index 0）",
          es and es[0].get("is_minion") and str(es[0].get("uid", "")).startswith("e_min_"),
          f"side 顺序={[u.get('name') for u in es]}")
    check("Boss 被挤到召唤物身后（index 1）",
          len(es) >= 2 and es[1] is boss, f"index1={es[1].get('name') if len(es) > 1 else None}")
    alive = [u for u in es if int(u.get("hp", 0) or 0) > 0]
    check("存活序列第一名 = 召唤物（a1 挡刀）", alive and alive[0] is es[0],
          f"alive 顺序={[u.get('name') for u in alive]}")
    # 玩家无指定目标的普攻先打召唤物（默认目标 = 敌对存活第一人 = 队首）
    from game.battle2.actors import ActCtx as _B2Ctx
    pa = b.sides["player"][0]
    pa["side"] = "player"  # mk_env 快照 actor 无 side——补阵营才能正确解析敌对目标
    pa["atk"] = 150  # 快照无 atk——补面板让普攻能造成伤害
    hp_boss0 = boss["hp"]
    hp_sum0 = es[0]["hp"]
    b.act(_B2Ctx(caster=pa, action="attack"))
    check("默认目标先打召唤物（挡刀）：Boss 不掉血", boss["hp"] == hp_boss0,
          f"boss hp={boss['hp']} expect {hp_boss0}")
    check("召唤物承伤", es[0]["hp"] < hp_sum0, f"summon hp={es[0]['hp']} <- {hp_sum0}")
    # 队首有死亡单位残留时：新召唤仍站存活序列最前（先于 Boss）
    b2, boss2, st2 = mk_env(inst_id="inst_goblin_camp", extra_minions=1)
    bs2 = BS._new_script_state()
    bs2["round_no"] = 6
    dead = [u for u in b2.sides_of("enemy") if u.get("is_minion")][0]
    dead["hp"] = 0
    BS._check_summon(st2, b2, boss2, cfg, bs2, 6.0, [])
    es2 = b2.sides_of("enemy")
    alive2 = [u for u in es2 if int(u.get("hp", 0) or 0) > 0]
    check("队首死亡残留不影响挡刀（存活第一名仍是新召唤物）",
          alive2 and alive2[0].get("is_minion") and str(alive2[0].get("uid", "")).startswith("e_min_"),
          f"alive 顺序={[u.get('name') for u in alive2]}")
    check("Boss 仍在召唤物身后存活（第二存活）",
          len(alive2) >= 2 and alive2[1] is boss2, f"alive2={[u.get('name') for u in alive2]}")


def main():
    print("5c P3 Boss 剧本导演：召唤援军")
    test_1_summon_cd()
    test_2_summon_template()
    test_3_summon_fallback()
    test_4_summon_cap()
    test_5_summon_dead_minion_recycle()
    test_6_summon_no_token()
    test_7_summon_front_row()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    if FAILURES:
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
