# -*- coding: utf-8 -*-
"""临时探针2：哥布林营地全通（清怪 → 移动 → Boss 通关），打印每步状态"""
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

def _left(m, gid, sa):
    st = (db.get_battle(gid, "i1") or {}).get("state") or {}
    return len((st.get("rooms") or {}).get(sa, {}).get("monsters_left") or [])

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

    # 阶段A：清 _1（2只）
    for i in range(2):
        # 探索遇怪
        for _ in range(8):
            out = await cmd(m, "explore", gid, A, "探索")
            s = (db.get_battle(gid, A) or {}).get("state") or {}
            if s.get("mode") == "battle": break
        # 击杀
        for _ in range(10):
            s = (db.get_battle(gid, A) or {}).get("state") or {}
            if s.get("mode") != "battle": break
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
        print(f"A{i}: _1_left={_left(m,gid,'goblin_camp_1')}")

    # 阶段B：移 _2（连通表序号 1）→ 清 2 只
    await cmd(m, "move", gid, A, "移动 1")
    print("B: 到 _2", "sa:", db.get_player(gid,A).get("cur_subarea"), "_2_left:", _left(m,gid,"goblin_camp_2"))
    for i in range(2):
        for _ in range(8):
            out = await cmd(m, "explore", gid, A, "探索")
            s = (db.get_battle(gid, A) or {}).get("state") or {}
            if s.get("mode") == "battle": break
        for _ in range(10):
            s = (db.get_battle(gid, A) or {}).get("state") or {}
            if s.get("mode") != "battle": break
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
        print(f"B{i}: _2_left={_left(m,gid,'goblin_camp_2')}")

    # 阶段C：移 _3（连通表序号 2）→ Boss
    out = await cmd(m, "move", gid, A, "移动 2")
    s = (db.get_battle(gid, A) or {}).get("state") or {}
    print("C: 到 _3", "sa:", db.get_player(gid,A).get("cur_subarea"), "mode:", s.get("mode"), "boss_alive:", (s.get("rooms") or {}).get("goblin_camp_3",{}).get("boss_alive"))
    print("C out:", (out or "")[:100].replace("\n"," "))
    # Boss 战
    if s.get("mode") == "map":
        for _ in range(6):
            out = await cmd(m, "explore", gid, A, "探索")
            s = (db.get_battle(gid, A) or {}).get("state") or {}
            if s.get("mode") == "battle": break
    s = (db.get_battle(gid, A) or {}).get("state") or {}
    print("C Boss战: mode:", s.get("mode"), "boss:", (s.get("boss") or {}).get("name"))
    for _ in range(10):
        s = (db.get_battle(gid, A) or {}).get("state") or {}
        if s.get("mode") != "battle": break
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
            print("通关!", out[:60].replace("\n"," "))
            break
    s = (db.get_battle(gid, A) or {}).get("state") or {}
    print("最终:", {k: s.get(k) for k in ("cleared","over","mode")})

asyncio.run(main())
