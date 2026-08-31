# -*- coding: utf-8 -*-
"""Probe 5: v95_76 flow in v137 — enter combat properly via explore, check defend sync."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_game_data_v95_76_probe.db")
from conftest import C, db, clean_db, Main, FakeEvent, run

def _fake_spend(self, gid, qid, cost, player, action="行动"):
    return True, self._stamina(player)
Main._spend_stamina = _fake_spend

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def enter_combat(m, gid, qid):
    for _ in range(8):
        out = await cmd(m, "explore", gid, qid, "探索")
        battle = db.get_battle(gid, qid)
        if battle and battle["state"].get("boss") is not None:
            return out, battle["state"]
    return out, (db.get_battle(gid, qid) or {}).get("state")

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员 男")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i2", level=40, gold=10000, cur_map="dawn_city")
    for _ in range(5):
        db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("== 开本 ==", out[:200].replace("\n", " | "))
    out, st = await enter_combat(m, "g1", "i1")
    print("== 探索输出 ==", out[:300].replace("\n", " | "))
    if not st:
        print("NO BATTLE STATE"); return
    print("mode:", st.get("mode"), "boss:", (st.get("boss") or {}).get("name"))
    leader = st["members"][0]
    snap = st["players"][leader]
    full_hp = snap["max_hp"]
    print("leader:", leader, "full_hp:", full_hp, "snap hp:", snap["hp"])
    st["players"][leader]["hp"] = int(full_hp * 0.3)
    st["turn"] = 0
    st["acted"] = [False] * len(st["members"])
    db.save_battle("g1", st["leader"], st)
    db.update_player("g1", leader, hp=full_hp)
    out = await cmd(m, "defend", "g1", leader, "防御")
    print("== 防御输出 ==", out[:300].replace("\n", " | "))
    p = db.get_player("g1", leader)
    battle = db.get_battle("g1", st["leader"])
    snap2 = battle["state"]["players"][leader] if battle else {}
    print("DB hp:", p["hp"], "snap2 hp:", snap2.get("hp"), "full:", full_hp)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
