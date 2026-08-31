# -*- coding: utf-8 -*-
"""Probe 6: v104 flow in v137 — open_instance enter combat; boss attack skip leaver."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_game_data_v104_probe.db")
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

def heal(gid, qid):
    p = db.get_player(gid, qid)
    if p:
        db.update_player(gid, qid, hp=p.get("max_hp", 9999), mp=p.get("max_mp", 999))

async def main():
    clean_db()
    m = Main(None)
    for q in ("i1","i2","i3"):
        await cmd(m, "register", "g1", q, "注册 战士 队长 男" if q=="i1" else ("注册 法师 队员 男" if q=="i2" else "注册 游侠 甲 男"))
        db.update_player("g1", q, level=40, gold=10000, cur_map="dawn_city")
        heal("g1", q)
    for _ in range(10):
        db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("== 开本 ==", out[:200].replace("\n", " | "))
    out, st = await enter_combat(m, "g1", "i1")
    print("== 探索 ==", out[:200].replace("\n", " | "))
    if not st:
        print("NO BATTLE"); return
    print("mode:", st.get("mode"), "boss:", (st.get("boss") or {}).get("name"))
    print("rooms:", json.dumps({k: {"ml": len(v.get("monsters_left") or []), "pl": len(v.get("pois_left") or [])} for k, v in st.get("rooms", {}).items()}, ensure_ascii=False))
    # leaver test: i2 leaves, then boss high atk targets i2 (leaver) — but boss may be dead.
    # First weaken enemy and attack until boss hp low, then set threat.
    await cmd(m, "party_leave", "g1", "i2", "退队")
    print("leaver left. party:", db.party_members("g1", "i1"))
    battle = db.get_battle("g1", "i1")
    print("battle after leave:", battle is not None)
    if battle:
        stt = battle["state"]
        print("mode:", stt.get("mode"), "boss:", (stt.get("boss") or {}).get("name"))
    # ensure boss alive: heal up and fight
    for i in range(10):
        battle = db.get_battle("g1", "i1")
        if not battle:
            print("no battle at", i); break
        stt = battle["state"]
        if stt.get("mode") == "map":
            # explore again for next monster
            out = await cmd(m, "explore", "g1", "i1", "探索")
            continue
        if stt.get("boss") is None:
            print("boss None at iter", i, "mode", stt.get("mode")); break
        stt["boss"]["hp"] = 50000
        stt["boss"]["atk"] = 500
        stt["boss"]["matk"] = 500
        stt["boss"]["spd"] = 1
        stt["threat"] = {"i1": 1, "i2": 999999}
        stt["turn"] = stt["members"].index("i1")
        stt["acted"] = [True] * len(stt["members"])
        stt["turn_time"] = int(time.time())
        stt["alive"] = {str(mm): True for mm in stt["members"]}
        # 敌方 ct 拉到很负 → 必然先行动；玩家 ct 拉高 → 行动完敌方段可能连动。
        # 但这是 v104 原逻辑：attack 后敌人反击一次。敌人 atk 500 会秒人——把敌人 atk 调低
        stt["boss"]["atk"] = 5
        stt["boss"]["matk"] = 5
        stt["enemies"] = [dict(u) for u in stt.get("enemies") or []]
        for _eu in stt["enemies"]:
            _eu["hp"] = stt["boss"]["hp"]
            _eu["atk"] = 5
            _eu["matk"] = 5
        db.save_battle("g1", "i1", stt)
        out = await cmd(m, "attack", "g1", "i1", "攻击")
        print("out iter", i, ":", out[-120:].replace("\n", " | "))
        battle = db.get_battle("g1", "i1")
        if not battle:
            print("battle gone at iter", i); break
        stt = battle["state"]
        print("iter", i, "boss hp:", (stt.get("boss") or {}).get("hp"), "mode:", stt.get("mode"), "i2 hp:", stt["players"].get("i2", {}).get("hp"))
        if stt.get("mode") == "map" or stt.get("over"):
            break

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
