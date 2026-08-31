# -*- coding: utf-8 -*-
"""临时探针：哥布林营地全通（清怪 → 移动 → Boss 通关）"""
import sys, os, time, asyncio
sys.path.insert(0, os.path.abspath('tests'))
os.environ.setdefault('GWEN_GAME_DB', os.path.join(os.path.abspath('tests'), 'test_game_data.db'))
import conftest
from conftest import C, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    gid = "g1"; A = "i1"; B = "i2"
    from conftest import make_player
    for q, nm in ((A,"队长A"),(B,"队员B")):
        make_player(gid, q, name=nm, cls="战士", level=30)
        p = db.get_player(gid, q)
        db.update_player(gid, q, hp=p["max_hp"], mp=p["max_mp"], level=30, gold=99999, cur_map="oak_town", cur_subarea="oak_town_1", stamina=999999)
    await cmd(m, "party", gid, A, "组队 队员B")
    await cmd(m, "instance_cmd", gid, A, "副本 哥布林营地")
    for step in range(30):
        s = (db.get_battle(gid, A) or {}).get("state") or {}
        if s.get("cleared") or s.get("over"):
            break
        sa = db.get_player(gid, A).get("cur_subarea")
        rstate = (s.get("rooms") or {}).get(sa) or {}
        rml = rstate.get("monsters_left") or []
        if s.get("mode") == "battle":
            stt = s
            stt["boss"] = stt.get("boss") or {}
            stt["boss"]["hp"] = 1; stt["boss"]["atk"] = 1; stt["boss"]["matk"] = 1
            stt["boss"]["max_hp"] = stt["boss"].get("max_hp") or 1
            for _eu in (stt.get("enemies") or []):
                _eu["hp"] = 1; _eu["atk"] = 1; _eu["matk"] = 1
            stt["turn_time"] = int(time.time())
            db.save_battle(gid, A, stt)
            cur = stt["members"][stt["turn"] % len(stt["members"])]
            out = await cmd(m, "attack", gid, cur, "攻击")
            if "通关" in out:
                print(f"step{step} 通关!", out[:60].replace("\n"," "))
                break
            continue
        # map 模式
        if not rml:
            # 当前房间怪清空 → 移动下一房
            out = await cmd(m, "move", gid, A, "移动 1")
            print(f"step{step} sa={sa} 移动: {(out or '')[:40].replace(chr(10),' ')}")
        else:
            out = await cmd(m, "explore", gid, A, "探索")
            print(f"step{step} sa={sa} 探索: {(out or '')[:50].replace(chr(10),' ')}")
    s = (db.get_battle(gid, A) or {}).get("state") or {}
    print("最终:", {k: s.get(k) for k in ("cleared","over","mode")}, "sa:", db.get_player(gid,A).get("cur_subarea"))
    if not s.get("cleared"):
        print("_3 boss_alive:", (s.get("rooms") or {}).get("goblin_camp_3",{}).get("boss_alive"), "_3 monsters:", len((s.get("rooms") or {}).get("goblin_camp_3",{}).get("monsters_left") or []))
        print("_2 monsters:", len((s.get("rooms") or {}).get("goblin_camp_2",{}).get("monsters_left") or []))
        print("_1 monsters:", len((s.get("rooms") or {}).get("goblin_camp_1",{}).get("monsters_left") or []))

asyncio.run(main())
