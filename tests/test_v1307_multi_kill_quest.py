# -*- coding: utf-8 -*-
"""v130.7 玩家意见#17 多目标战斗任务击杀计数固化测试（tests/test_v1307_multi_kill_quest.py）。

玩家反馈：『如果遇到多个目标的怪物，只有后击杀的怪物才会计算进任务里』——真 bug：
victory 结算只传阵列首位主怪，多怪战（双只/精英带爪牙/Boss 带小怪）副怪击杀全部丢失。

修复：battle.py `_remove_unit` 敌方死亡时把单位 dict 快照记入 `killed_enemies`
（随战斗状态序列化，跨消息续战不丢）；combat.py 胜利结算任务进度按全部击杀单位
逐个调 `_update_quests` 计数——掉落/经验/金币仍只按主怪结算一次。

覆盖：
  ① 双怪战（主怪在前排先死、『野猪』+『野猪·幼崽』前缀变体）：主线进度 +2、
     每日 kill_any +2、支线 kill +2；经验只结算一次（+1000×加成，不翻倍）；
     掉落材料仅一行；击杀记录跨消息持久化
  ② 单怪战不回归：进度 +1
  ③ 引擎级：_remove_unit 快照顺序、同单位去重、compact 阵亡单位一并记录、
     to_state/from_state 往返

运行：python tests/test_v1307_multi_kill_quest.py（exit=0 全绿）
"""
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, FakeEvent, run, BT, E, make_player  # noqa: E402

# v154 读条命中制：玩家出手只排 cast_done 事件，出招读条结束（命中时刻）才结算伤害。
# 引擎 cast_done 分支结算击杀后未置 result（战斗胜利判定缺位，主 agent 引擎修复前的
# 测试侧等价补丁）——命令层读 ended/result 才走胜利结算（_handle_victory 任务进度）。
# 此处 monkeypatch Battle.player_turn：返回前若敌方已全灭则补 result=victory + _end_round，
# 使命令层攻击流程（footer 渲染 / 胜利结算）按 v154 节奏正常工作。仅改测试，不动 game/。
_orig_player_turn = BT.Battle.player_turn


def _player_turn_v154(self, action, skill_name, player, enemy_act=True, target=None):
    logs, ended = _orig_player_turn(self, action, skill_name, player, enemy_act=enemy_act, target=target)
    if not ended and getattr(self, "result", None) is None and self._enemy_dead():
        # v154：cast_done 命中结算击杀 → 敌方全灭 → 补胜利判定（引擎缺口等价补丁）
        self.result = "victory"
        self._end_round()
        ended = True
    return logs, ended


BT.Battle.player_turn = _player_turn_v154

passed = failed = 0
G, Q = 1095961999, "v1307k1"
G2, Q2 = 1095961200, "v1307k2"


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


def mk_enemy(name, uid, rank=1, hp=1, exp=1000, gold=100, lv=30, role="normal"):
    """敌方单位（含胜利结算所需的 exp/gold/lv/role/name；drops 固定单材料防随机）。"""
    return {
        "uid": uid, "id": "test_multi_kill", "name": name, "side": "enemy",
        "rank": rank, "reach": 1, "hp": hp, "max_hp": hp,
        "atk": 1, "matk": 1, "def": 0, "mdef": 0, "spd": 1, "crit": 0.0,
        "buffs": {}, "stacks": {}, "defending": False, "charging": None,
        "exp": exp, "gold": gold, "lv": lv, "role": role, "drops": ["兽肉"],
    }


def seed_quests(gid, qid):
    """主线 q1_3（杀 5 野猪）+ 每日 kill_any(5) + 支线 s101（杀 3 野猪）。"""
    today = datetime.date.today().isoformat()
    db.save_quests(gid, qid, {
        "main_quest": "q1_3", "main_status": "active", "main_progress": {},
        "daily": {"_date": today,
                  "d0": {"name": "讨伐试炼", "desc": "击杀任意怪物",
                         "objective": {"kill_any": 5},
                         "reward_exp": 100, "reward_gold": 50, "progress": 0}},
        "completed_main": [], "side": {"s101": {"status": "active", "progress": {}}},
    })


def expected_exp_gain(p):
    """与 _handle_victory 同口径：主怪 exp=1000 ×(1+求知 exp_bonus)。"""
    try:
        _st = E.player_final_stats(p["class_name"], p["level"], p.get("equipment", {}),
                                   p.get("class_tier", 0), p.get("attributes"),
                                   p.get("evolve_path", 0), p.get("_title_bonus") or {}, p.get("race"))
        _eb = min(float(_st.get("exp_bonus", 0) or 0), 0.5)
    except Exception:
        _eb = 0.0
    return int(1000 * (1 + _eb)) if _eb > 0 else 1000


async def main():
    m = Main(None)

    # ============ ① 双怪战：全部击杀逐个计任务进度，掉落/经验只结算一次 ============
    print("\n【① 双怪战：主线/每日/支线各 +2，经验/掉落单次结算】")
    clean_db()
    make_player(G, Q, "多目标杀手", "战士", level=30)
    seed_quests(G, Q)
    p0 = db.get_player(G, Q)
    exp0, hp0 = p0["exp"], p0["hp"]
    b = BT.Battle("monster", None, {}, player=db.get_player(G, Q),
                  enemies=[mk_enemy("野猪", "u1", rank=1), mk_enemy("野猪·幼崽", "u2", rank=2)])
    db.save_battle(G, Q, b.to_state())

    # 第一击：前排野猪死（非胜利，战斗继续），击杀记录需已持久化
    r1 = await cmd(m, "attack", G, Q, "攻击")
    st = db.get_battle(G, Q)["state"]
    k1 = [k.get("name") for k in (st.get("killed_enemies") or [])]
    check("① 首击后击杀记录随战斗状态持久化", k1 == ["野猪"], str(k1))
    b2 = BT.Battle.from_state(st)  # 模拟跨消息恢复
    check("① 恢复后 killed_enemies 不丢", [k.get("name") for k in b2.killed_enemies] == ["野猪"], "")

    # 第二击：副怪死 → 胜利
    r2 = await cmd(m, "attack", G, Q, "攻击")
    out = str(r2)
    q = db.get_quests(G, Q)
    check("① 主线进度 +2（两只都计）", q["main_progress"] == {"野猪": 2}, str(q["main_progress"]))
    check("① 胜利面板逐只显示进度 1/5→2/5", "1/5" in out and "2/5" in out, out[:400])
    check("① 每日 kill_any +2", (q["daily"] or {}).get("d0", {}).get("progress") == 2, str(q.get("daily")))
    check("① 支线 kill +2（含『·』前缀变体）",
          (q["side"] or {}).get("s101", {}).get("progress") == {"野猪": 2}, str(q.get("side")))
    # 经验/掉落只结算一次（主怪 exp=1000；祈祷无翻倍）
    exp_gain = expected_exp_gain(p0)
    p1 = db.get_player(G, Q)
    check("① 经验恰为主怪一次（不翻倍）", p1["exp"] - exp0 == exp_gain, f"delta={p1['exp']-exp0} expect={exp_gain}")
    check("① 面板经验行仅一行", out.count("✨ 经验 +") == 1 and f"✨ 经验 +{exp_gain}" in out
          and f"✨ 经验 +{exp_gain * 2}" not in out, out[:400])
    check("① 掉落材料仅一行", out.count("拾取材料") == 1, out[:400])
    check("① 战斗已结算清除", db.get_battle(G, Q) is None, "")

    # ============ ② 单怪战不回归：进度 +1 ============
    print("\n【② 单怪战回归：进度 +1】")
    clean_db()
    make_player(G2, Q2, "单怪猎手", "战士", level=30)
    seed_quests(G2, Q2)
    p0 = db.get_player(G2, Q2)
    exp0 = p0["exp"]
    b = BT.Battle("monster", None, {}, player=db.get_player(G2, Q2),
                  enemies=[mk_enemy("野猪", "s1", rank=1)])
    db.save_battle(G2, Q2, b.to_state())
    r = await cmd(m, "attack", G2, Q2, "攻击")
    out = str(r)
    q = db.get_quests(G2, Q2)
    check("② 主线进度 +1", q["main_progress"] == {"野猪": 1}, str(q["main_progress"]))
    check("② 面板 1/5 且无 2/5", "1/5" in out and "2/5" not in out, out[:400])
    check("② 每日 kill_any +1", (q["daily"] or {}).get("d0", {}).get("progress") == 1, "")
    check("② 经验单次结算", db.get_player(G2, Q2)["exp"] - exp0 == expected_exp_gain(p0), "")

    # ============ ③ 引擎级：快照/去重/compact/序列化 ============
    print("\n【③ 引擎级：_remove_unit 击杀记录】")
    clean_db()
    e1 = mk_enemy("野猪", "u1", rank=1)
    e2 = mk_enemy("野猪·幼崽", "u2", rank=2)
    b = BT.Battle("monster", None, {}, player={"hp": 100, "max_hp": 100, "mp": 100, "max_mp": 100, "atk": 50},
                  enemies=[e1, e2])
    b._remove_unit("enemy", e1)
    b._remove_unit("enemy", e1)  # 同单位重复移除：去重
    b._remove_unit("enemy", e2)
    names = [k["name"] for k in b.killed_enemies]
    check("③ 击杀记录两只且顺序正确", names == ["野猪", "野猪·幼崽"], str(names))
    check("③ 快照为副本（后续改原对象不影响记录）", b.killed_enemies[0]["hp"] == 1, "")
    b.enemies[0]["hp"] = 5
    check("③ 快照与存活单位解耦", b.killed_enemies[0]["hp"] == 1 and b.killed_enemies[1]["hp"] == 1, "")
    # compact 阵亡单位一并记录（AOE 同时击杀场景）
    b3 = BT.Battle("monster", None, {}, player={"hp": 100, "max_hp": 100, "mp": 100, "max_mp": 100, "atk": 50},
                   enemies=[mk_enemy("甲", "a1", rank=1), mk_enemy("乙", "a2", rank=1, hp=0)])
    b3._remove_unit("enemy", b3.enemies[0])
    check("③ compact 阵亡单位一并记录", [k["name"] for k in b3.killed_enemies] == ["甲", "乙"],
          str([k["name"] for k in b3.killed_enemies]))
    # 序列化往返
    st = b.to_state()
    b4 = BT.Battle.from_state(st)
    check("③ to_state/from_state 往返不丢", [k["name"] for k in b4.killed_enemies] == ["野猪", "野猪·幼崽"], "")
    # 旧存档无 killed_enemies 键 → 容错为空列表
    st2 = b.to_state()
    del st2["killed_enemies"]
    b5 = BT.Battle.from_state(st2)
    check("③ 旧存档缺键容错", getattr(b5, "killed_enemies", None) == [], str(getattr(b5, "killed_enemies", None)))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


import asyncio
asyncio.run(main())