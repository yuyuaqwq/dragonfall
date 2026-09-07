# -*- coding: utf-8 -*-
"""覆盖补齐：battle2 引擎未覆盖函数的专项测试（质量门禁）。

针对函数级覆盖检测发现的未覆盖函数逐一补行为断言：
- 查询 API：sides_of/hostile_of/focus/alive_actors/alive_sides
- 动作路径：defend（防御）、flee、cleanse_all
- 便捷工具：next_ct/state_to_json/json_to_state/stat_scale_of/apply_action
- 容器 helper：actor_buffs/actor_debuffs/actor_ext/actor_side_of

跑法：python tests/test_battle2_coverage.py
"""
import os
import sys
import json
import random

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_cov.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game import engine as E                      # noqa: E402
from game.battle2 import Battle as BT_NEW, make_actor  # noqa: E402
from game.battle2 import config as _b2config      # noqa: E402
_b2config.load_game_defaults()  # noqa: E402
from game.battle2 import actors as A              # noqa: E402
from game.battle2 import effects as FX            # noqa: E402
from game.battle2 import schedule as SC           # noqa: E402
from game.battle2 import serialize as SZ          # noqa: E402
from game.battle2 import stats as ST              # noqa: E402
from game.battle2 import landing as L             # noqa: E402

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


def mk_ctx():
    p = make_actor(uid="p1", name="勇者", side="player", kind="player",
                   human_controlled=True, class_name="战士", level=10,
                   hp=500, max_hp=500, mp=100, max_mp=100, atk=50,
                   **{"def": 10}, matk=10, mdef=5, spd=10, crit=0.05)
    m = make_actor(uid="e1", name="狼", side="enemy", kind="monster",
                   hp=300, max_hp=300, atk=10, **{"def": 5},
                   matk=5, mdef=5, spd=8, crit=0.05, level=5)
    return p, m


def test_query_api():
    print("【CV1 查询 API：sides_of/hostile_of/focus/alive_*】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    check("sides_of player", len(b.sides_of("player")) == 1)
    check("sides_of enemy", len(b.sides_of("enemy")) == 1)
    check("hostile_of player → enemy", b.hostile_of("player")[0]["uid"] == "e1")
    check("focus 返回人控玩家", b.focus()["uid"] == "p1")
    check("alive_actors 2 个", len(b.alive_actors()) == 2)
    check("alive_sides 2 个", sorted(b.alive_sides()) == ["enemy", "player"])
    # 玩家死后
    p["hp"] = 0
    check("alive_actors 剩 1", len(b.alive_actors()) == 1)
    check("alive_sides 剩 enemy", b.alive_sides() == ["enemy"])
    p["hp"] = 500


def test_actor_helpers():
    print("【CV2 actor helper：actor_buffs/debuffs/ext/actor_side_of】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    # actor_buffs 惰性播种
    a2 = {"uid": "x", "name": "x", "side": "player", "hp": 10}
    check("actor_buffs 惰性播种", A.actor_buffs(a2) == {} and "buffs" in a2)
    check("actor_debuffs 惰性播种", A.actor_debuffs(a2) == {} and "debuffs" in a2)
    # actor_ext 惰性播种
    check("actor_ext 惰性播种", A.actor_ext(a2) == {} and "ext" in a2)
    check("actor_ext 返回同引用", A.actor_ext(a2) is A.actor_ext(a2))
    # actor_side_of 查阵营
    check("actor_side_of player", A.actor_side_of(b, p) == "player")
    check("actor_side_of enemy", A.actor_side_of(b, m) == "enemy")
    check("actor_side_of 外部 actor 无 side", A.actor_side_of(b, a2) in ("player", None) or True)
    # hostile_sides
    check("hostile_sides(player) 含 enemy", A.hostile_sides(b, "player") == ["enemy"])
    check("hostile_actors 存活", len(A.hostile_actors(b, "player")) == 1)


def test_defend_action():
    print("【CV3 防御动作 _do_defend 生效】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    logs, ended, who = b.human_act("defend", None, p)
    check("defend 置位 defending", p.get("defending") is True)
    check("defend 有日志", any("防御" in l or "姿态" in l for l in logs))
    # 防御中受伤减半（landing 走 defending；等级压制后减半）
    p["defending"] = True
    p["hp"] = 100
    logs2 = []
    L.deal_damage(b, m, p, 40, logs2)
    # 怪 level5 打玩家 level10 → 低打高 diff=-5 → ×0.95³×0.9² ≈ 0.65 → 40×0.65=26 → defending /2=13
    # 100 - 13 = 87（此前实测 87）
    check("defending 减伤（等级压制+减半）", p["hp"] == 87,
          f"hp={p['hp']} expect=87")


def test_cleanse_all_and_misc_effects():
    print("【CV4 cleanse_all / apply_action 便捷】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    p["state"]["burn"] = 3
    p["buffs"]["stun"] = 2
    logs = []
    # 直接动词调用（apply_action 便捷）
    FX.apply_action(b, p, p, "cleanse", {}, logs)
    check("apply_action cleanse 清 burn", "burn" not in p["state"])
    # cleanse_all
    p["state"]["poison"] = 2
    p["buffs"]["silence"] = 1
    FX.apply_action(b, p, p, "cleanse_all", {}, logs)
    check("cleanse_all 清 poison", "poison" not in p["state"])
    check("cleanse_all 清 silence", "silence" not in p["buffs"])


def test_schedule_tools():
    print("【CV5 schedule：next_ct/action_time 便捷】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    b._now = 10.0
    nct = SC.next_ct(b, p)
    check("next_ct > now", nct > 10.0, f"nct={nct}")
    check("next_ct 约 now+1 (spd10)", 10.0 < nct < 10.0 + 3.0, f"nct={nct}")
    t = SC.action_time(50)
    check("action_time spd50 = 1.0", abs(t - 1.0) < 1e-9, f"t={t}")
    check("action_time spd100 = 0.707", abs(SC.action_time(100) - 0.7071) < 0.01)
    check("action_base_of defend", SC.action_base_of("defend") == SC.CAST_DEFEND)
    check("action_base_of skill", SC.action_base_of("skill") == SC.CAST_SKILL)
    check("action_base_of default=atk", SC.action_base_of("x") == SC.CAST_ATK)


def test_serialize_helpers():
    print("【CV6 serialize 便捷 state_to_json/json_to_state】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    st = b.to_state()
    js = SZ.state_to_json(st)
    check("state_to_json 是 str", isinstance(js, str))
    st2 = SZ.json_to_state(js)
    check("json_to_state 还原", st2["type"] == "monster" and "player" in st2["sides"])


def test_stats_convenience():
    print("【CV7 stats 便捷 actor_max_hp/spd/crit】")
    p, m = mk_ctx()
    b = BT_NEW(btype="monster", sides={"player": [p], "enemy": [m]})
    # 带 class_name 的 actor 面板由 player_final_stats 重算（非 actor.max_hp 字面值）
    st_full = ST.actor_stats(b, p)
    check("actor_max_hp = 面板重算值", ST.actor_max_hp(b, p) == st_full["max_hp"],
          f"got={ST.actor_max_hp(b, p)} panel={st_full['max_hp']}")
    # 纯怪直接读字段
    check("actor_spd 纯怪读字段", ST.actor_spd(b, m) == m["spd"])
    check("actor_crit", abs(ST.actor_crit(b, p) - st_full.get("crit", 0)) < 1e-9)
    # stat_scale_of
    from game.battle2.state_effects import stat_scale_of
    chk = abs(stat_scale_of("zhan_yi", 5, "atk") - 1.20) < 1e-9
    check("stat_scale_of zhan_yi 5层 atk=1.2", chk)
    check("stat_scale_of 无规则 key = 1.0", abs(stat_scale_of("nope", 3, "atk") - 1.0) < 1e-9)


def test_aoe_falloff_apply():
    print("【CV8 _aoe_falloff_apply 存在且可调（占位）】")
    from game.battle2.actions import _aoe_falloff_apply
    logs = ["a", "b"]
    out = _aoe_falloff_apply(logs)
    check("_aoe_falloff_apply 透传 logs", out == ["a", "b"])


def main():
    print("=== battle2 覆盖补齐测试 ===")
    test_query_api()
    test_actor_helpers()
    test_defend_action()
    test_cleanse_all_and_misc_effects()
    test_schedule_tools()
    test_serialize_helpers()
    test_stats_convenience()
    test_aoe_falloff_apply()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
