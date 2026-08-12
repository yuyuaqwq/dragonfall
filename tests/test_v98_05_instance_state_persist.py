# -*- coding: utf-8 -*-
"""v101.28m #438 复测回归：副本战斗状态持久化（e_minions / round / resources）

根因：_instance_act / _instance_boss_one_turn 重建 Battle 时未传/未写回
e_minions / round / resources / cooldown / combo_seq →
  - Boss 召唤的援军回合结束蒸发（不挡刀不出手）
  - 副本内耗资源技能（如游侠致命狙击 35 精力）永远不可用
  - round 恒 0 → 按回合 Boss 机制（召唤/回血）失序

验证方式：真实走 handler（开本→探索→战斗），战斗中手动向 st 注入
援军/精力状态，验证跨回合传递与写回。
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run

passed = failed = 0
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

async def enter_combat(m, gid, qid):
    for _ in range(5):
        out = await cmd(m, "explore", gid, qid, "探索")
        if db.get_battle(gid, qid):
            return out
    return out

async def main():
    clean_db()
    m = Main(None)
    # 单人副本（哥布林营地 1-2 人可单开），少一层组队复杂度
    await cmd(m, "register", "g1", "i1", "注册 游侠 队长 男")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    await cmd(m, "instance_cmd", "g1", "i1", "副本 哥布林营地")
    st = db.get_battle("g1", "i1")["state"]
    check("单人开本成功", st["type"] == "instance" and len(st["members"]) == 1, str(st.get("type")))

    out = await enter_combat(m, "g1", "i1")
    st = db.get_battle("g1", "i1")["state"]
    check("进入战斗", st.get("boss") is not None, out[:120])

    # ---------- e_minions 持久化：注入援军 → 玩家攻击应挡刀 ----------
    st["e_minions"] = [{"name": "测试爪牙", "hp": 500, "max_hp": 500, "atk": 100, "matk": 0}]
    st["round"] = 5
    st["boss"]["hp"] = 999999  # 防测试期 Boss 被秒杀导致战斗结束
    db.save_battle("g1", "i1", st)
    out = await cmd(m, "attack", "g1", "i1", "攻击")
    check("援军挡刀日志", "挡下" in out, out[:200])
    st2 = db.get_battle("g1", "i1")["state"]
    check("援军状态写回 st", st2.get("e_minions"), str(st2.get("e_minions"))[:120])
    m_hp = st2["e_minions"][0]["hp"]
    check("援军扣血", m_hp < 500, f"hp={m_hp}")
    check("round 递增写回", st2.get("round", 0) == 6, f"round={st2.get('round')}")

    # ---------- 援军出手：Boss 行动回合援军攻击玩家 ----------
    out2 = await cmd(m, "attack", "g1", "i1", "攻击")  # 触发 Boss 反击（_instance_boss_one_turn）
    check("援军出手日志", "扑向" in out2, out2[:200])
    st3 = db.get_battle("g1", "i1")["state"]
    check("Boss 行动后援军仍写回", st3.get("e_minions"), str(st3.get("e_minions"))[:120])

    # ---------- resources 持久化：注入精力 50 → 攻击后应保留且回复 ----------
    st3["resources"] = {"i1": {"energy": 50}}
    st3["e_minions"] = []  # 清援军避免干扰
    db.save_battle("g1", "i1", st3)
    out3 = await cmd(m, "attack", "g1", "i1", "攻击")
    st4 = db.get_battle("g1", "i1")["state"]
    en = st4.get("resources", {}).get("i1", {}).get("energy")
    check("精力跨回合累积", en is not None and en >= 75, f"energy={en}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
