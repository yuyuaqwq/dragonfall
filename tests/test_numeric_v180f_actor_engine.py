#!/usr/bin/env python3
"""v180F B5/B7 门禁：通用 actor 引擎——任意阵营对阵（怪vs怪/无玩家战斗）整场可跑完。

v180F 目标（鱼鱼拍板）：战斗引擎要能支持任意 actor 对阵，不假设有玩家。
本测试验证：
1. sides 入口构造无玩家战斗（两个怪敌对阵营）
2. AI 行动目标选择 = 敌对阵营（怪打怪，不是打空 player）
3. 战斗能整场跑完直到一方全灭
4. 伤害文案正确（攻击目标名，非"攻击你"）
5. 结局：某 side 全灭（record result 或 winner 判定）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_mon(name, hp, atk, df, spd, lv=30, side="side_a", matk=0, mdef=0, basic=None):
    return {"name": name, "hp": hp, "max_hp": hp, "atk": atk, "matk": matk,
            "def": df, "mdef": mdef, "spd": spd, "lv": lv, "role": "normal",
            "side": side, "buffs": {}, "debuffs": {},
            **({"basic_skill": basic} if basic else {})}


def run_battle(sides, max_turns=200, seed=42):
    """驱动 AI 战斗直到一方全灭或超时。返回 (battle, turn, 存活阵营统计)。"""
    from data.plugins.dragonfall.game import battle as BT
    random.seed(seed)
    b = BT.Battle("monster", sides=sides)
    turn = 0
    logs_all = []
    while turn < max_turns and b._events:
        side_names = {str(e.get("side")): [x for x in b.enemies if x.get("side") == e.get("side") and x.get("hp", 0) > 0]
                      for e in b.enemies}
        alive_sides = {s: v for s, v in side_names.items() if v}
        if len(alive_sides) <= 1:
            break
        turn += 1
        logs = []
        b._process_until(b._events[0][0] + 0.2, logs, b.player or {})
        logs_all += logs
        # 敌阵死亡清理（_remove_unit 在 _damage_actor 内做，但保险再压缩）
        b.enemies[:] = [e for e in b.enemies if e.get("hp", 0) > 0 or e.get("_dead") == "keep"]
    side_alive = {}
    for e in b.enemies:
        if e.get("hp", 0) > 0:
            side_alive.setdefault(str(e.get("side")), []).append(e)
    return b, turn, side_alive, logs_all


async def main():
    clean_db()
    print("===== v180F B5 通用 actor 引擎（怪vs怪）=====\n")

    # 1. sides 入口构造无玩家战斗
    mon_a = mk_mon("骷髅兵A", 800, 90, 25, 15, side="side_a")
    mon_b = mk_mon("史莱姆B", 600, 70, 15, 12, side="side_b")
    from data.plugins.dragonfall.game import battle as BT
    b = BT.Battle("monster", sides={"side_a": [dict(mon_a)], "side_b": [dict(mon_b)]})
    check("sides 构造：无玩家", not b.player or not b.player.get("class_name"), str(b.player))
    check("sides 保留双阵营", set(b.sides.keys()) == {"side_a", "side_b"}, str(list(b.sides.keys())))
    ea = [e for e in b.enemies if e.get("side") == "side_a"][0]
    eb = [e for e in b.enemies if e.get("side") == "side_b"][0]
    check("敌对判定", b.hostile_sides("side_a") == ["side_b"], str(b.hostile_sides("side_a")))

    # 2. AI 行动选敌对目标 + 整场跑完
    b2, turn, alive, logs2 = run_battle(
        {"side_a": [dict(mon_a)], "side_b": [dict(mon_b)]})
    alive_sides = set(alive.keys())
    check("战斗能跑完（≤200 回合）", turn > 0 and turn < 200, f"turn={turn}")
    check("一方全灭（剩 1 阵营）", len(alive_sides) == 1, f"alive={alive_sides}")
    check("伤害文案用目标名（无'攻击你'误显）",
          not any("攻击你" in l for l in logs2), str(logs2[-3:]))
    check("战斗有伤害产生", any("造成" in l and "点伤害" in l for l in logs2), str(logs2[:2]))

    # 3. 带魔法普攻的怪 vs 怪（basic_skill 走技能管线）
    mon_c = mk_mon("骷髅法师C", 800, 60, 20, 15, side="side_c", matk=120,
                   basic={"exprs": ["matk*1.2"], "kind": "magi"})
    mon_d = mk_mon("石像鬼D", 900, 80, 40, 10, side="side_d", mdef=30)
    b3, turn3, alive3, logs3 = run_battle(
        {"side_c": [dict(mon_c)], "side_d": [dict(mon_d)]}, seed=7)
    alive3_sides = set(alive3.keys())
    check("魔法怪 vs 怪能跑完", len(alive3_sides) == 1, f"alive={alive3_sides} turn={turn3}")

    # 3b. 结局判定（B7）：怪vs怪跑完 result 记胜利阵营
    check("怪vs怪 result = 胜利阵营", b3.result in ("side_c", "side_d"),
          f"result={b3.result} winner_side={getattr(b3, 'winner_side', None)}")
    check("winner_side 与存活阵营一致", getattr(b3, "winner_side", None) in alive3_sides,
          f"winner={getattr(b3, 'winner_side', None)} alive={alive3_sides}")

    # 4. 常规玩家战斗不受影响（回归：野外 player vs enemy 仍正常）
    from data.plugins.dragonfall.game import battle as _BT
    p = {"class_name": "战士", "level": 50, "hp": 8000, "max_hp": 8000, "mp": 200, "max_mp": 200,
         "atk": 500, "matk": 300, "def": 100, "mdef": 60, "spd": 20,
         "equipment": {}, "buffs": {}, "stacks": {}, "eff": {}, "resources": {},
         "attributes": {"str": 50}, "learned_skills": [], "race": "human",
         "qq_id": "t1", "name": "测试玩家"}
    mon_e = mk_mon("野狼", 500, 80, 15, 14, side="enemy")
    b4 = _BT.Battle("monster", dict(mon_e), player=p)
    logs4, ended = b4.player_turn("attack", None, p)
    check("常规玩家战斗仍正常", logs4 is not None, str(logs4[:1] if logs4 else "no logs"))

    # 5. 序列化往返（B6）：怪vs怪中途存档 → 恢复 → 继续打完
    import json
    mon_e1 = mk_mon("骷髅A", 800, 90, 25, 15, side="s_a")
    mon_e2 = mk_mon("史莱姆B", 600, 70, 15, 12, side="s_b")
    b5 = _BT.Battle("monster", sides={"s_a": [dict(mon_e1)], "s_b": [dict(mon_e2)]})
    b5._process_until(2.0, [], b5.player or {})  # 打 2 秒（中途）
    _hp1 = [e for e in b5.enemies if e.get("side") == "s_a"][0].get("hp", 0)
    try:
        js5 = json.dumps(b5.to_state(), ensure_ascii=False, default=str)
        b6 = _BT.Battle.from_state(json.loads(js5))
        _hp1r = [e for e in b6.enemies if e.get("side") == "s_a"][0].get("hp", 0)
        check("序列化往返：无循环引用 + hp 恢复", len(js5) > 0 and _hp1r == _hp1,
              f"len={len(js5)} hp={_hp1}→{_hp1r}")
        check("序列化往返：sides 阵营重建", set(b6.sides.keys()) == {"s_a", "s_b"},
              str(list(b6.sides.keys())))
    except Exception as _ex5:
        check("序列化往返：无循环引用 + hp 恢复", False, f"异常 {_ex5}")

    # 6. 命令层兼容（B8）：旧入口 Battle(player=, enemy=) 构造 → sides 派生正确 + 同引用
    b7 = _BT.Battle("monster", dict(mon_e), player=dict(p))
    check("命令层旧入口 → sides 双阵营", set(b7.sides.keys()) == {"player", "enemy"},
          str(list(b7.sides.keys())))
    _sp = (b7.sides.get("player") or [{}])[0]
    b7.player["hp"] = 4321
    check("命令层读写同步到 sides（同引用）", _sp.get("hp") == 4321,
          f"sides player hp={_sp.get('hp')}")

    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
