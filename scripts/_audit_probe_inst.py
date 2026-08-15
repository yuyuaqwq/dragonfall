# -*- coding: utf-8 -*-
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import C, E, db, clean_db, Main, FakeEvent, run
from data.plugins.dragonfall.game.battle import Battle

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
    await cmd(m, "register", "g1", "i1", "注册 游侠 队长 男")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    await cmd(m, "instance_cmd", "g1", "i1", "副本 哥布林营地")
    await enter_combat(m, "g1", "i1")
    st = db.get_battle("g1", "i1")["state"]
    print("enemies:", [(u.get('uid'), u.get('name'), 'rank=%s'%u.get('rank'), 'reach=%s'%u.get('reach'), 'hp=%s'%u.get('hp')) for u in (st.get('enemies') or st.get('pet') and [])])
    e_boss = st.get('enemies') or []
    print("boss:", st.get('boss', {}).get('name'), "rank", None)
    # append minion
    st["enemies"].append({"uid": "e_test_minion", "name": "测试爪牙", "hp": 500, "max_hp": 500, "atk":100,"matk":0,"def":0,"mdef":0,"spd":10,"crit":0,"dodge":0,"rank":1,"reach":1,"buffs":{},"stacks":{},"defending":False,"charging":None})
    db.save_battle("g1","i1",st)
    out = await cmd(m, "attack", "g1", "i1", "攻击")
    st2 = db.get_battle("g1","i1")["state"]
    print("after attack enemies:", [(u.get('uid'), u.get('hp')) for u in st2.get('enemies') or []])
    print("attack log:", out[:120])

asyncio.run(main())
