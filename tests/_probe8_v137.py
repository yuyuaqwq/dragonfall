# -*- coding: utf-8 -*-
"""Probe 8: elven_ruins mech open_secret + secret chest in v137 (mech on room 2)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_game_data_v137e.db")
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
    return await cmd(m, "explore", gid, qid, "探索")

def weaken(st):
    for _eu in (st.get("enemies") or []):
        _eu["hp"] = 1
        _eu["atk"] = 5
        _eu["matk"] = 5
    st["turn_time"] = int(time.time())

def cur_sa(m, gid, qid):
    return (db.get_player(gid, qid) or {}).get("cur_subarea")

async def room_clear(m, gid, qid, max_iter=12):
    for _ in range(max_iter):
        battle = db.get_battle(gid, qid)
        if not battle:
            return "no battle"
        stt = battle["state"]
        if stt.get("mode") == "map":
            sa = cur_sa(m, gid, qid)
            ml = (stt.get("rooms", {}).get(sa, {}) or {}).get("monsters_left") or []
            if not ml:
                return f"cleared sa={sa}"
            out = await cmd(m, "explore", gid, qid, "探索")
        else:
            weaken(stt)
            db.save_battle(gid, qid, stt)
            out = await cmd(m, "attack", gid, stt["members"][stt["turn"]], "攻击")
    return "loop-end"

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    db.update_player("g1", "i1", level=70, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    # elven_ruins: 2-3 players? check min
    ins = C.INSTANCES["inst_elven_ruins"]
    print("min_players:", ins.get("min_players"), "max:", ins.get("max_players"), "lv:", ins.get("lv"), "key:", ins.get("key_item"))
    if ins.get("key_item"):
        for _ in range(5):
            db.add_item("g1", "i1", "i_key_elven_ruins", {"name": ins["key_item"], "type": "钥匙", "stackable": True, "price": 500})
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 精灵废墟")
    print("== 开本 ==", out[:200].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("rooms:", {k: {"ml": len(v.get("monsters_left") or []), "pl": v.get("pois_left")} for k, v in st.get("rooms", {}).items()})
    # room1: fire, no monsters? move to room2
    print("room1 clear:", await room_clear(m, "g1", "i1"))
    out = await cmd(m, "move", "g1", "i1", "移动 2")
    print("== move2 ==", out[:300].replace("\n", " | "))
    # investigate mech 精灵石像
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 精灵石像")
    print("== 石像 ==", out[:250].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("stage_secret_found:", st.get("stage_secret_found"))
    print("poi_unlocks:", json.dumps(st.get("poi_unlocks"), ensure_ascii=False)[:200])
    # map view shows hidden?
    out = await cmd(m, "instance_map_view_cmd", "g1", "i1", "副本地图")
    print("== 副本地图 ==", out[:600].replace("\n", " | "))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
