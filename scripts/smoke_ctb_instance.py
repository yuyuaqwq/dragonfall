# -*- coding: utf-8 -*-
"""CTB 副本改造第二阶段冒烟测试（独立脚本，不依赖 astrbot 实例化）。
用 astrbot uv python 运行：
  "C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" scripts/smoke_ctb_instance.py
覆盖：
  1. Battle.from_state 不再引用已删 v61 字段，且读 p_ct / 敌方 ct。
  2. 玩家快照含 ct、敌方单位含 ct（构建兜底）。
  3. _instance_next_actor / _instance_min_player_ct / _instance_min_enemy_ct 判定。
  4. _instance_enemy_ct_acts 敌方连动循环（含玩家 ct 时间流逝、死亡移出候选）。
  5. _instance_ct_queue 队列预览。
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from game import battle as BT  # noqa: E402
from game.commands.instance import InstanceCmds  # noqa: E402

FAIL = []


def check(title, cond):
    print(("  OK  " if cond else "  FAIL") + " " + title)
    if not cond:
        FAIL.append(title)


def make_single_st(players=(("p1", 20.0), ("p2", 10.0)),
                   enemies=(("e_boss", 15.0, 100), ("e_minion", 30.0, 60))):
    """p1 快，spd20→ct-20；p2 中；e_boss spd15→ct-15；e_minion spd30→ct-30（最慢怪反而 ct 最负？——负分）"""
    members = [k for k, _ in players]
    st = {
        "type": "instance",
        "leader": str(members[0]),
        "members": members,
        "alive": {k: True for k, _ in players},
        "players": {k: {"name": k, "qq_id": k, "rank": 2, "reach": 2,
                        "spd": s, "ct": -s, "hp": 500, "max_hp": 500,
                        "buffs": {}, "stacks": {}, "defending": False, "charging": None}
                    for k, s in players},
        "enemies": [],
        "boss": None,
        "p_buffs": {k: {} for k, _ in players},
        "p_hot": {k: {} for k, _ in players},
        "p_food_effects": {k: [] for k, _ in players},
        "e_buffs": {},
        "p_defending": {k: False for k, _ in players},
        "mech_stacks": {k: {} for k, _ in players},
        "resources": {k: {} for k, _ in players},
        "cooldown": {k: {} for k, _ in players},
        "combo_seq": {k: [] for k, _ in players},
        "round": 1,
        "threat": {k: 0 for k, _ in players},
        "over": False,
        "turn": 0,
    }
    for (uid, spd, hp) in enemies:
        st["enemies"].append({"uid": uid, "name": uid, "spd": spd, "ct": -spd,
                              "hp": hp, "max_hp": hp, "rank": 1, "reach": 1,
                              "buffs": {}, "stacks": {}, "defending": False,
                              "charging": None})
    if enemies:
        st["boss"] = st["enemies"][0]
    return st


def main():
    print("== 1. Battle.from_state 无 v61 字段残留，读 p_ct / 敌方 ct ==")
    # 删除字段后构造应不报 AttributeError/KeyError
    b = BT.Battle.from_state({
        "type": "instance",
        "enemy": {"uid": "e_boss", "name": "BOSS", "spd": 15},
        "enemies": [{"uid": "e_boss", "name": "BOSS", "spd": 15}],
        "p_ct": -40.0,
        "p_buffs": {}, "e_buffs": {}, "round": 1,
        "resources": {}, "cooldown": {}, "combo_seq": [],
        "player_hit": False,
    })
    check("from_state 存活（不再读已删 v61 字段）", b is not None)
    check("p_ct 透传 = -40", abs(b.p_ct - (-40.0)) < 1e-9)
    check("敌方单位 ct 兜底 -spd", abs(b.enemies[0]["ct"] - (-15.0)) < 1e-9)
    check("_ct_cost 反比 spd", BT.Battle()._ct_cost(20.0) < BT.Battle()._ct_cost(10.0))

    print("== 2. 玩家/敌方 ct 字段 ==")
    st = make_single_st()
    check("玩家快照含 ct", "ct" in st["players"]["p1"])
    check("敌方单位含 ct", "ct" in st["enemies"][0])
    c = InstanceCmds()
    # 测试桩：视所有 st["members"] 为在场成员（脱机无真实组队库）
    orig_current = InstanceCmds._instance_current_members
    InstanceCmds._instance_current_members = lambda s_self, g, st: [str(m) for m in st["members"]]
    try:
        next_actor = c._instance_next_actor(st, 1)
        # ct: p1 -20, p2 -10, boss -15, minion -30 → 最小是 minion(敌 -30) → 敌方先
        check("next_actor 敌方先（minion ct 最小）", next_actor == ("e", None))
        check("min_enemy_ct = -30", abs(c._instance_min_enemy_ct(st) - (-30.0)) < 1e-9)
        check("min_player_ct = -20", abs(c._instance_min_player_ct(st, 1) - (-20.0)) < 1e-9)
        q = c._instance_ct_queue(st, 1)
        check("队列预览含敌我标记与行动顺序字样", q.startswith("⚡ 行动顺序：") and "(敌)" in q and "(我)" in q)

        print("== 3. _instance_apply_enemy_act_ct 时间流逝语义 ==")
        unit = st["enemies"][0]  # e_boss spd15 cost=100/15
        cost = BT.Battle()._ct_cost(unit["spd"])
        before_p1 = st["players"]["p1"]["ct"]
        before_unit = unit["ct"]
        c._instance_apply_enemy_act_ct(st, 1, unit)
        check("行动者 ct += cost", abs(unit["ct"] - (before_unit + cost)) < 1e-9)
        check("玩家 ct -= cost", abs(st["players"]["p1"]["ct"] - (before_p1 - cost)) < 1e-9)
    finally:
        InstanceCmds._instance_current_members = orig_current

    print("== 4. _instance_enemy_ct_acts 连动循环 ==")
    # 用 0 伤害 stub 隔离循环逻辑，验证 ct 驱动与上限
    def stub_one_act(s_self, st, group_id, unit):
        # 模拟敌人行动：不造成死亡/不掉血，仅返回文案（ct 结算走 _instance_apply_enemy_act_ct）
        tname = [p for p in st["players"].values() if st["alive"].get(str(p.get("qq_id")), True)][0]
        return [f"⚔ {unit['name']} 攻击 {tname['name']}"]
    orig_one_act = InstanceCmds._instance_enemy_one_act
    orig_current = InstanceCmds._instance_current_members
    InstanceCmds._instance_enemy_one_act = stub_one_act
    InstanceCmds._instance_current_members = lambda s_self, g, st: [str(m) for m in st["members"]]

    st2 = make_single_st(players=(("p1", 5.0),), enemies=(("e_fast", 50.0, 100), ("e_slow", 5.0, 100)))
    # p1 spd5 ct-5；e_fast spd50 ct-50（先）；e_slow spd5 ct-5（同 p1）
    logs, ok = c._instance_enemy_ct_acts(st2, 1)
    # e_fast ct-50 < p1 ct-5 → e_fast 动；e_fast cost=100/50=2 → e_fast ct=-48, 其余 -cost
    # 之后 me=e_slow(约-7) vs mp=p1(约-7)；若仍敌领先继续，直到上限或玩家更先
    check("敌方段返回 logs", isinstance(logs, list) and len(logs) >= 1)
    check("敌方段 ok 为 bool", isinstance(ok, bool))
    # 玩家 ct 被敌方时间流逝推进（打了 ≥1 敌方动作后玩家 ct 应变小）
    check("玩家 ct 受敌方时间流逝影响", st2["players"]["p1"]["ct"] < -5.0)

    # 上限：构造永不停歇（玩家 spd 极慢，敌方多个超快）→ 应被 8 上限截断
    st3 = make_single_st(players=(("p1", 1.0),),
                         enemies=tuple(("e%d" % i, 100.0, 100) for i in range(8)))
    logs3, ok3 = c._instance_enemy_ct_acts(st3, 1)
    check("敌方段上限截断（≤8 动）", len(logs3) <= 8)
    check("敌方段上限返回 ok=False", ok3 is False)

    # 死亡单位即时移出：玩家全灭 → 敌方段提前终止
    st4 = make_single_st(players=(("p1", 5.0),), enemies=(("e_fast", 50.0, 100),))
    def stub_one_act_kill(s_self, st, group_id, unit):
        for k, snap in st["players"].items():
            st["alive"][k] = False
        return ["💀 全灭"]
    InstanceCmds._instance_enemy_one_act = stub_one_act_kill
    logs4, ok4 = c._instance_enemy_ct_acts(st4, 1)
    check("玩家全灭 → 敌方段提前终止", len(logs4) == 1)

    InstanceCmds._instance_enemy_one_act = orig_one_act
    InstanceCmds._instance_current_members = orig_current

    print("== 5. 全模块 python 编译校验 ==")
    import py_compile
    py_compile.compile(os.path.join(_ROOT, "game", "commands", "instance.py"), doraise=True)
    py_compile.compile(os.path.join(_ROOT, "game", "battle.py"), doraise=True)
    check("py_compile instance.py / battle.py", True)

    print("\n==== smoke result ====")
    if FAIL:
        print("FAILED:", FAIL)
        sys.exit(1)
    print("ALL SMOKE OK")


if __name__ == "__main__":
    main()
