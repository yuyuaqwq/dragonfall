# -*- coding: utf-8 -*-
"""适配验证：直接调 handler 模拟 v137 副本全链路（开本→探索→战斗→肃清→移动→Boss→通关）。"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run

def _fake_spend(self, gid, qid, cost, player, action="行动"):
    return True, self._stamina(player)
Main._spend_stamina = _fake_spend

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def enter_combat(m, gid, qid, retries=5):
    for _ in range(retries):
        out = await cmd(m, "explore", gid, qid, "探索")
        if db.get_battle(gid, qid):
            st = db.get_battle(gid, qid)["state"]
            if st.get("mode") == "battle" and (st.get("enemies") or []):
                return out
    return out

def dump_st(m):
    b = db.get_battle("g1", "i1")
    if not b:
        return "(no battle)"
    st = b["state"]
    return {
        "mode": st.get("mode"), "boss": (st.get("boss") or {}).get("name"),
        "enemies": [(u.get("name"), u.get("hp"), u.get("rank")) for u in st.get("enemies", [])],
        "cur_subarea": m._player("g1", "i1").get("cur_subarea") if False else (db.get_player("g1","i1") or {}).get("cur_subarea"),
        "rooms_left": {k: [mm[1] if isinstance(mm,(list,tuple)) and len(mm)>1 else mm for mm in (v.get("monsters_left") or [])] for k,v in (st.get("rooms") or {}).items()},
        "stage_pending": [x[1] if isinstance(x,(list,tuple)) else x for x in (st.get("stage_pending") or [])],
    }

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员 男")
    for q in ("i1", "i2"):
        db.update_player("g1", q, level=40, gold=10000, cur_map="dawn_city")
        _p = db.get_player("g1", q)
        db.update_player("g1", q, hp=_p["max_hp"], max_hp=_p["max_hp"], mp=_p["max_mp"], max_mp=_p["max_mp"])
    for _ in range(10):
        db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})

    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("=== 开本 ===")
    print(out[:600])
    print(dump_st(m))
    p1 = db.get_player("g1", "i1")
    print("player1 cur:", p1.get("cur_map"), p1.get("cur_subarea"))
    p2 = db.get_player("g1", "i2")
    print("player2 cur:", p2.get("cur_map"), p2.get("cur_subarea"))

    out = await cmd(m, "explore", "g1", "i1", "探索")
    print("=== 探索1 ===")
    print(out[:500])
    print(dump_st(m))

    b = db.get_battle("g1", "i1")
    st = b["state"]
    if st.get("mode") == "battle":
        # 低攻+低血快速清
        for _u in st.get("enemies") or []:
            _u["hp"] = 1
            _u["atk"] = 1
            _u["matk"] = 1
        st["turn_time"] = int(time.time())
        db.save_battle("g1", "i1", st)
        cur = st["members"][st["turn"]]
        out = await cmd(m, "attack", "g1", cur, "攻击")
        print("=== 攻击1 ===")
        print(out[:600])
        print(dump_st(m))
    else:
        print("探索未遇怪：", out[:200])

    # 再探索/攻击直到肃清
    for i in range(8):
        b = db.get_battle("g1", "i1")
        if not b:
            print("no battle at", i)
            break
        st = b["state"]
        if st.get("mode") == "map":
            if st.get("cleared"):
                print("cleared!")
                break
            out = await cmd(m, "explore", "g1", "i1", "探索")
            print(f"=== 探索{i} ===", out[:300])
            b = db.get_battle("g1", "i1")
            if not b:
                break
            st = b["state"]
        if st.get("mode") == "battle":
            for _u in st.get("enemies") or []:
                _u["hp"] = 1
                _u["atk"] = 1
                _u["matk"] = 1
            st["turn_time"] = int(time.time())
            db.save_battle("g1", "i1", st)
            cur = st["members"][st["turn"]]
            out = await cmd(m, "attack", "g1", cur, "攻击")
            print(f"=== 攻击{i} ===", out[:400])
            print(dump_st(m))

    # 移动（队长带队）
    out = await cmd(m, "move", "g1", "i1", "移动 殉葬坑")
    print("=== 移动2 ===")
    print(out[:500])
    print(dump_st(m))

    print("DONE")

import asyncio
asyncio.run(main())
