# -*- coding: utf-8 -*-
"""Probe 7: retreat + re-enter + member leave + recovery checks (v104 §4) in v137."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_game_data_v104b_probe.db")
from conftest import C, db, clean_db, Main, FakeEvent, run

def _fake_spend(self, gid, qid, cost, player, action="行动"):
    return True, self._stamina(player)
Main._spend_stamina = _fake_spend

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    for q in ("i1","i2"):
        await cmd(m, "register", "g1", q, "注册 战士 队长 男" if q=="i1" else "注册 法师 队员 男")
        db.update_player("g1", q, level=40, gold=10000, cur_map="dawn_city")
    for _ in range(10):
        db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("== 开本 ==", "副本开启" in out)
    out = await cmd(m, "instance_retreat", "g1", "i1", "撤退")
    print("== 撤退 ==", out[:200].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("retreated:", st.get("retreated"), "mode:", st.get("mode"))
    print("player cur_subarea:", (db.get_player("g1","i1") or {}).get("cur_subarea"), (db.get_player("g1","i2") or {}).get("cur_subarea"))
    # re-enter with full party
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("== 恢复 ==", out[:250].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("retreated after:", st.get("retreated"), "mode:", st.get("mode"))
    # retreat again + member leave
    out = await cmd(m, "instance_retreat", "g1", "i1", "撤退")
    print("== 再撤退 ==", out[:200].replace("\n", " | "))
    out = await cmd(m, "party_leave", "g1", "i2", "退队")
    print("== 退队 ==", out[:150].replace("\n", " | "), "party:", db.party_members("g1","i1"))
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("== 恢复被拒? ==", out[:250].replace("\n", " | "))
    st = db.get_battle("g1", "i1")
    print("battle retained:", st is not None, (st or {}).get("state", {}).get("retreated"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
