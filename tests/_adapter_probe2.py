# -*- coding: utf-8 -*-
"""适配验证 v2：旧王陵全链路（2 人队开本→逐房清怪→移动→Boss→通关），
以及各副本 Boss 血量缩放断言。"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, FakeEvent, run

def _fake_spend(self, gid, qid, cost, player, action="行动"):
    return True, self._stamina(player)
Main._spend_stamina = _fake_spend

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

def _rooms_left(st):
    return {k: [mm[1] if isinstance(mm,(list,tuple)) and len(mm)>1 else mm for mm in (v.get("monsters_left") or [])]
            for k, v in (st.get("rooms") or {}).items()}

async def enter_combat(m, gid, qid):
    for _ in range(6):
        out = await cmd(m, "explore", gid, qid, "探索")
        b = db.get_battle(gid, qid)
        if b and b["state"].get("mode") == "battle" and (b["state"].get("enemies") or []):
            return out
    return out

async def clear_current(m, gid, qid, max_rounds=10):
    """把当前战斗的敌人清掉（先压血低攻）。返回 (out, still_battle)"""
    for _ in range(max_rounds):
        b = db.get_battle(gid, qid)
        if not b:
            return "", False
        st = b["state"]
        if st.get("mode") == "map":
            # 房内还有怪物池 → 探索遇怪；无怪 → 肃清
            rstate = (st.get("rooms") or {}).get(st.get("cur_subarea") or "") or {}
            if (rstate.get("monsters_left") or []):
                out = await enter_combat(m, gid, qid)
                continue
            return "", True
        # battle：压血低攻
        for _u in st.get("enemies") or []:
            _u["hp"] = 1
            _u["atk"] = 1
            _u["matk"] = 1
        st["turn_time"] = int(time.time())
        db.save_battle(gid, qid, st)
        cur = st["members"][st["turn"]]
        out = await cmd(m, "attack", gid, cur, "攻击")
        b = db.get_battle(gid, qid)
        if not b or b["state"].get("cleared"):
            return out, False
        st = b["state"]
        if st.get("mode") == "map":
            return out, True
    return "", False

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员 男")
    for q in ("i1", "i2"):
        db.update_player("g1", q, level=40, gold=10000, cur_map="dawn_city")
        _p = db.get_player("g1", q)
        if _p:
            db.update_player("g1", q, hp=_p.get("max_hp",500), max_hp=_p.get("max_hp",500),
                             mp=_p.get("max_mp",100), max_mp=_p.get("max_mp",100))
    for _ in range(10):
        db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})

    print("【开本】")
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("开本成功", "副本开启" in out, out[:200])
    b = db.get_battle("g1", "i1")
    st = b["state"]
    check("状态存队长名下", st["type"] == "instance" and len(st["members"]) == 2)
    check("mode=map", st.get("mode") == "map")
    check("boss=None", st.get("boss") is None)
    check("rooms 3 房", len(st.get("rooms") or {}) == 3, str(list((st.get('rooms') or {}).keys())))
    check("入口房有怪池", len((st.get("rooms") or {}).get("old_king_tomb_1", {}).get("monsters_left") or []) == 2)
    p1 = db.get_player("g1", "i1")
    check("玩家落点 cur_map", p1.get("cur_map") == "old_king_tomb", f"{p1.get('cur_map')}")
    check("玩家落点 cur_subarea", p1.get("cur_subarea") == "old_king_tomb_1", f"{p1.get('cur_subarea')}")

    print("【房1 探索战斗】")
    out = await enter_combat(m, "g1", "i1")
    b = db.get_battle("g1", "i1")
    st = b["state"]
    check("探索进战斗 mode=battle", st.get("mode") == "battle", out[:200])
    check("enemies 有怪", len(st.get("enemies") or []) >= 1, str([(u.get('name')) for u in st.get('enemies', [])]))
    ename = (st.get("enemies") or [{}])[0].get("name", "")
    check("第 1 房小怪", ename in ("骷髅兵", "僵尸"), f"enemy={ename}")
    check("非首领", (st.get("enemies") or [{}])[0].get("is_boss") is not True)
    check("分层状态 stage_idx", st.get("stage_idx") == 0 and st.get("inst_stages"))

    print("【轮流回合】")
    # 压低攻击防秒杀
    for _u in st.get("enemies") or []:
        _u["atk"] = 5
        _u["matk"] = 5
    db.save_battle("g1", "i1", st)
    first_m = st["members"][0]
    second_m = st["members"][1]
    out = await cmd(m, "attack", "g1", second_m, "攻击")
    check("非当前行动者被拦", "等待" in out or "回合" in out, out[:120])
    out = await cmd(m, "attack", "g1", first_m, "攻击")
    st2 = db.get_battle("g1", "i1")["state"]
    def _next_player_key(stt):
        cts = {str(mm): float(stt["players"][str(mm)].get("ct", 0) or 0) for mm in stt["members"]
               if stt.get("alive", {}).get(str(mm), True)}
        return min(cts, key=cts.get) if cts else None
    check("轮到下一位(ct 判定)", str(st2["members"][st2["turn"]]) == _next_player_key(st2), f"turn={st2['turn']}")

    print("【超时自动防御】")
    st3 = db.get_battle("g1", "i1")["state"]
    for _u in st3.get("enemies") or []:
        _u["atk"] = 5
        _u["matk"] = 5
    st3["turn_time"] = int(time.time()) - 200
    for key in st3["players"]:
        st3["players"][key]["ct"] = -50.0 if key == st3["members"][0] else 0.0
    for _u in st3.get("enemies") or []:
        _u["ct"] = 0.0
    db.save_battle("g1", "i1", st3)
    out = await cmd(m, "attack", "g1", second_m, "攻击")
    check("超时自动防御并行动", "自动" in out, out[:200])

    print("【肃清房1 + 移动房2】")
    out, cleared = await clear_current(m, "g1", "i1")
    b = db.get_battle("g1", "i1")
    st = b["state"]
    check("房1 清空", st.get("mode") == "map" and not (st.get("rooms") or {}).get("old_king_tomb_1", {}).get("monsters_left"), str(_rooms_left(st)))
    # 移动房2（队长带队）
    out = await cmd(m, "move", "g1", "i1", "移动 殉葬坑")
    b = db.get_battle("g1", "i1")
    st = b["state"]
    p = db.get_player("g1", "i1")
    check("移动后落点", p.get("cur_subarea") == "old_king_tomb_2", f"{p.get('cur_subarea')}")
    if st.get("mode") == "map":
        # 探索遇怪（房2：幽灵 + 幽灵骑士）
        out = await enter_combat(m, "g1", "i1")
        b = db.get_battle("g1", "i1")
        st = b["state"]
    check("房2 遇怪", st.get("mode") == "battle" and len(st.get("enemies") or []) >= 1, str([(u.get('name')) for u in st.get('enemies', [])]))

    print("【清房2 → Boss 房】")
    out, cleared = await clear_current(m, "g1", "i1")
    b = db.get_battle("g1", "i1")
    st = b["state"]
    check("房2 清空", st.get("mode") == "map" and not (st.get("rooms") or {}).get("old_king_tomb_2", {}).get("monsters_left"), str(_rooms_left(st)))
    # 移动 Boss 房
    out = await cmd(m, "move", "g1", "i1", "移动 王座厅")
    b = db.get_battle("g1", "i1")
    st = b["state"]
    p = db.get_player("g1", "i1")
    check("Boss 房落点", p.get("cur_subarea") == "old_king_tomb_3", f"{p.get('cur_subarea')}")
    check("Boss 战触发", st.get("mode") == "battle", out[:250])
    check("Boss 登场", (st.get("boss") or {}).get("name") == "古王·奥德里克", f"boss={(st.get('boss') or {}).get('name')}")

    print("【Boss 血量缩放】")
    _inst = C.INSTANCES["inst_old_king_tomb"]
    base = C.build_monster(_inst["boss"], {"id": "x", "name": "x", "area": "instance"})["max_hp"]
    expect = int(base * (_inst["hp_mult"] + 0.65 * (2 - _inst.get("min_players", 1))))
    check("Boss 血量 2.5 倍", abs((st.get("boss") or {}).get("max_hp", 0) - expect) <= 1, f"{st.get('boss',{}).get('max_hp')} vs {expect}")

    print("【击杀 Boss 通关】")
    for _ in range(8):
        b = db.get_battle("g1", "i1")
        if not b:
            break
        st = b["state"]
        for _u in st.get("enemies") or []:
            _u["hp"] = 1
            _u["atk"] = 5
            _u["matk"] = 5
        st["turn_time"] = int(time.time())
        db.save_battle("g1", "i1", st)
        cur = st["members"][st["turn"]]
        out = await cmd(m, "attack", "g1", cur, "攻击")
        if "通关" in out or "击败" in out:
            break
    check("通关结算", "通关" in out or "击败" in out, out[:300])
    check("金币奖励", "+200" in out or "金币" in out, out[:300])
    check("材料奖励", "古王剑碎片" in out, out[:300])  # v173 问题B：材料改名 古王剑→古王剑碎片
    b = db.get_battle("g1", "i1")
    check("通关后停留搜刮", b is not None and b["state"].get("cleared"), str(b)[:200] if b else "")
    out = await cmd(m, "instance_leave", "g1", "i1", "离开副本")
    check("离开副本传出", "离开" in out, out[:150])
    b = db.get_battle("g1", "i1")
    check("战斗已清除", b is None, "")

    print(f"\n结果: {passed} passed, {failed} failed")
    return failed

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
