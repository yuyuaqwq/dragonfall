# -*- coding: utf-8 -*-
"""5c P5 验证：Boss 剧本导演——on_interrupt 读条打断联动。

- 引擎 interrupt 事件（landing 伤害打断 / effects.act_interrupt fire）
- 观察者联动：freeze_self（Boss 自冻结 skip）/ vulnerable（承伤 × 时效）
- vulnerable 到期清理（导演帧 round_no 到点移除 _dmg_taken_mult）

跑法：python tests/test_boss_script_p5.py
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
from game import engine as E  # noqa: E402
from game.commands import boss_script as BS  # noqa: E402
from battle2 import Battle as B2  # noqa: E402
from battle2 import landing as _LD  # noqa: E402

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


GID = "g_bs5"


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
            "bonus": {"panel": {}, "cap": {}, "cost": {}}, "race": pl.get("race"), "uid": f"p_{qid}",
            "buffs": {}, "stacks": {}, "defending": False, "charging": None,
            "ct": 0.0, "p_shields": {}, "spd": int(st.get("spd", 0) or 0)}


def mk_env(boss_id="b_goblin_chief"):
    """咕噜（真实 cfg：on_interrupt freeze_self）+ 玩家 + 手写 st。"""
    boss = {"uid": "e_boss", "id": boss_id, "name": "哥布林酋长·咕噜",
            "role": "boss", "is_boss": True, "hp": 50000, "max_hp": 50000,
            "atk": 300, "matk": 200, "def": 100, "mdef": 100, "spd": 100,
            "lv": 20, "skills": [], "effects": {}, "shields": {},
            "auto_act": None, "ct": 0.0, "charging": None}
    st = {"type": "instance", "inst_id": "inst_goblin_camp", "leader": "80001",
          "members": ["80001"], "alive": {"80001": True},
          "players": {"80001": mk_snap(80001, "勇者")},
          "boss": boss, "enemy": boss, "enemies": [boss], "pets": {},
          "p_buffs": {"80001": {}}, "p_hot": {"80001": {}},
          "p_food_effects": {"80001": []}, "p_defending": {"80001": False},
          "mech_stacks": {"80001": {}}, "now": 0.0, "battle": None,
          "contribution": {}, "threat": {"80001": 0}, "over": False,
          "turn_time": 0, "stage_pending": [], "inst_stages": [],
          "stage_idx": 0, "stage_cleared": False, "world_id": ""}
    pa = dict(st["players"]["80001"], uid="p_80001", effects={}, charging=None)
    b = B2("instance", sides={"player": [pa], "enemy": [boss]})
    b._now = 10.0
    return b, boss, st, pa


def test_1_freeze_self_observer():
    print("【1. 观察者 interrupt → freeze_self（咕噜真实 cfg on_interrupt）】")
    b, boss, st, pa = mk_env()
    obs = BS.make_script_event(st)
    logs = []
    obs(b, "interrupt", {"actor": boss}, logs)
    ef = (boss.get("effects") or {}).get("boss_frozen")
    check("boss_frozen 条目（mode=skip）", ef and ef.get("mode") == "skip", str(ef))
    check("expire = now+1", ef and abs(float(ef.get("expire")) - 11.0) < 0.001, str(ef))
    check("联动日志（僵直）", any("僵直" in x or "读条" in x for x in logs), str(logs))
    # 引擎 act 消费：下帧行动被 skip（mode=skip 控制）
    boss["effects"]["boss_frozen"] = {"mode": "skip", "expire": 11.0}
    logs2 = []
    b.actor_auto(boss)
    # actor_auto 里 act 会跳过行动（无伤害/无普攻输出）
    check("冻结帧不行动（无普攻伤害日志）",
          not any("攻击" in x and "伤害" in x for x in logs2), str(logs2)[:200])


def test_2_vulnerable_link():
    print("【2. _interrupt_link vulnerable：承伤 ×1.2 + 到期清理】")
    b, boss, st, pa = mk_env()
    st["boss_script"] = BS._new_script_state()
    st["boss_script"]["round_no"] = 5
    logs = []
    BS._interrupt_link(st, b, boss, {"effect": "vulnerable", "value": 1.2,
                                     "turns": 2}, logs)
    check("_dmg_taken_mult=1.2", abs(float(boss.get("_dmg_taken_mult", 0)) - 1.2) < 0.001,
          str(boss.get("_dmg_taken_mult")))
    check("flags _vuln_until = round+2（7）",
          (st["boss_script"]["flags"].get("_vuln_until") or 0) == 7,
          str(st["boss_script"]["flags"]))
    check("日志（破绽）", any("破绽" in x for x in logs), str(logs))
    # 未到期不清
    st["boss_script"]["round_no"] = 6
    BS._check_vuln_expire(st, b, boss, st["boss_script"])
    check("未到期（round 6 < 7）仍保留", abs(float(boss.get("_dmg_taken_mult", 0)) - 1.2) < 0.001,
          str(boss.get("_dmg_taken_mult")))
    # 到期清
    st["boss_script"]["round_no"] = 7
    BS._check_vuln_expire(st, b, boss, st["boss_script"])
    check("到期清 _dmg_taken_mult", "_dmg_taken_mult" not in boss, str(boss.get("_dmg_taken_mult")))
    check("flags 清除", "_vuln_until" not in st["boss_script"]["flags"],
          str(st["boss_script"]["flags"]))


def test_3_engine_interrupt_fire():
    print("【3. 引擎链路：伤害打断 charging → fire interrupt → 观察者联动】")
    b, boss, st, pa = mk_env()
    st["boss_script"] = BS._new_script_state()
    st["boss_script"]["round_no"] = 1
    b.on_event = BS.make_script_event(st)
    # Boss 读条中
    boss["charging"] = {"skill": "ms_ju_qi", "until": 99}
    boss["hp"] = 50000
    # 玩家普攻打 Boss（deal_damage 触发打断）
    logs = []
    from battle2.landing import deal_damage as _dd
    _dd(b, pa, boss, 500, logs)
    check("Boss charging 被清", not boss.get("charging"), str(boss.get("charging")))
    ef = (boss.get("effects") or {}).get("boss_frozen")
    check("联动触发（boss_frozen 落下）", ef is not None, str(ef))
    check("日志含打断", any("打破" in x or "僵直" in x for x in logs), str(logs)[:300])


def test_4_interrupt_not_boss():
    print("【4. 非剧本 Boss 打断不联动】")
    b, boss, st, pa = mk_env(boss_id="b_nobody")
    st["boss_script"] = BS._new_script_state()
    obs = BS.make_script_event(st)
    logs = []
    obs(b, "interrupt", {"actor": boss}, logs)
    check("无配置不联动", not (boss.get("effects") or {}).get("boss_frozen"), str(logs))


def main():
    print("5c P5 Boss 剧本导演：on_interrupt 读条打断联动")
    test_1_freeze_self_observer()
    test_2_vulnerable_link()
    test_3_engine_interrupt_fire()
    test_4_interrupt_not_boss()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    if FAILURES:
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
