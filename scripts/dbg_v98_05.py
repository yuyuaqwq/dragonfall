# -*- coding: utf-8 -*-
"""调试 test_v98_05：第二次攻击后战斗为何结束"""
import sys, os, asyncio
_PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN, "tests"))
sys.path.insert(0, _PLUGIN)
from conftest import C, E, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 游侠 队长 男")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 哥布林营地")
    st = db.get_battle("g1", "i1")["state"]
    print("开本:", st["type"], "members:", st["members"])

    for _ in range(5):
        out = await cmd(m, "explore", "g1", "i1", "探索")
        if db.get_battle("g1", "i1"):
            break
    st = db.get_battle("g1", "i1")["state"]
    print("进入战斗 boss:", st["boss"]["name"], "lv", st["boss"]["lv"], "hp", st["boss"]["hp"], "round", st.get("round"))
    print("玩家hp:", st["players"]["i1"]["hp"], "/", st["players"]["i1"]["max_hp"])

    st["e_minions"] = [{"name": "测试爪牙", "hp": 500, "max_hp": 500, "atk": 100, "matk": 0}]
    st["round"] = 5
    st["boss"]["hp"] = 999999
    db.save_battle("g1", "i1", st)
    out = await cmd(m, "attack", "g1", "i1", "攻击")
    print("=== 攻击1:", out[:300].replace("\n", " | "))
    st2 = db.get_battle("g1", "i1")
    print("攻击1后战斗存在:", st2 is not None, "round:", st2["state"].get("round") if st2 else "-")

    out2 = await cmd(m, "attack", "g1", "i1", "攻击")
    print("=== 攻击2:", out2[:400].replace("\n", " | "))
    st3 = db.get_battle("g1", "i1")
    print("攻击2后战斗存在:", st3 is not None)
    if st3:
        print("round:", st3["state"].get("round"), "over:", st3["state"].get("over"),
              "alive:", st3["state"].get("alive"), "boss_hp:", st3["state"]["boss"]["hp"])
        print("players hp:", {k: v["hp"] for k, v in st3["state"]["players"].items()})

if __name__ == "__main__":
    asyncio.run(main())
