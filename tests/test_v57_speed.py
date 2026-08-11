# -*- coding: utf-8 -*-
"""v57 速度机制专项测试：先手/多动/副本排序/Boss 多动"""
import sys, os, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, db, clean_db, Main, FakeEvent, run

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def make_player(name="战士", lv=10, spd=None):
    p = {
        "qq_id": "t", "class_name": "cls_zhan_shi", "level": lv,
        "equipment": {}, "attributes": {"str": 0, "agi": 0, "int": 0, "vit": 0},
        "learned_skills": [], "skill_levels": {}, "class_tier": 0, "evolve_path": 0,
        "hp": 9999, "mp": 9999,
    }
    return p

def make_monster(spd=5, hp=100000, defense=50, atk=10):
    return {
        "id": "t", "name": "测试怪", "lv": 5, "role": "normal",
        "hp": hp, "max_hp": hp, "atk": atk, "def": defense,
        "matk": 5, "mdef": 5, "spd": spd, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": [], "drops": [],
    }

async def main():
    clean_db()
    print("【速度机制：_speed_plan 纯逻辑】")
    p = make_player()
    m = make_monster(spd=15)  # 10级战士基础 spd=15，同速
    b = BT.Battle("monster", m)
    pe, ee, ef = b._speed_plan(p)
    check("同速玩家先手", ef is False, f"{pe},{ee},{ef}")
    check("同速无多动", pe == 0 and ee == 0, f"{pe},{ee}")

    p2 = make_player()
    p2["attributes"] = {"agi": 100}  # agi→spd 0.8/点
    m2 = make_monster(spd=10)
    b2 = BT.Battle("monster", m2)
    pe2, ee2, ef2 = b2._speed_plan(p2)
    check("速度 1.5x 以上玩家多动", pe2 >= 1, f"{pe2},{ee2},{ef2}")

    m3 = make_monster(spd=100)
    b3 = BT.Battle("monster", m3)
    pe3, ee3, ef3 = b3._speed_plan(make_player())
    check("怪快则敌方先手", ef3 is True, f"{pe3},{ee3},{ef3}")
    check("怪快则敌方多动", ee3 >= 1, f"{pe3},{ee3},{ef3}")

    print("【速度机制：实战自由出手（v61）】")
    random.seed(5)
    # 玩家速度碾压（agi 100 → spd 80 vs 怪 5）→ 获得额外行动，可自由出手
    p4 = make_player()
    p4["attributes"] = {"agi": 100}
    m4 = make_monster(spd=5, hp=100000, defense=0)
    b4 = BT.Battle("monster", m4)
    logs, done = b4.player_turn("attack", None, p4)
    check("速度优势战斗未结束（等自由出手）", done is False, f"done={done} logs={'|'.join(logs)[:150]}")
    check("提示速度优势", any("速度优势" in x for x in logs), "|".join(logs)[:150])
    check("玩家有额外行动", b4.p_extra_left > 0, f"p_extra_left={b4.p_extra_left}")
    # 额外行动自由选择：再攻击一次（消耗 1 次额外行动）
    logs2, done2 = b4.player_turn("attack", None, p4)
    check("自由出手攻击生效", m4["hp"] < 100000, f"hp={m4['hp']} logs={'|'.join(logs2)[:150]}")
    # 防御结束本回合（不打怪）
    while b4.p_extra_left > 0:
        logs3, done3 = b4.player_turn("defend", None, p4)

    print("【速度机制：敌方先手实战】")
    random.seed(7)
    p5 = make_player(lv=1)  # spd 10
    m5 = make_monster(spd=10, hp=100000, defense=50, atk=5)
    # 手动给怪更高速度
    m5["spd"] = 30
    b5 = BT.Battle("monster", m5)
    logs5, done5 = b5.player_turn("attack", None, p5)
    dmg_taken = 9999 - p5["hp"]
    check("敌方先手打玩家", dmg_taken > 0, f"dmg={dmg_taken} logs={'|'.join(logs5)[:200]}")

    print("【速度机制：增益不追击】")
    random.seed(9)
    p6 = make_player(lv=20)
    p6["attributes"] = {"agi": 100}
    p6["learned_skills"] = ["怒吼"]
    p6["skill_levels"] = {"怒吼": 1}
    p6["mp"] = 999
    m6 = make_monster(spd=5, hp=100000, defense=50)
    b6 = BT.Battle("monster", m6)
    logs6, done6 = b6.player_turn("skill", "怒吼", p6)
    check("增益后不追击（怪无伤）", m6["hp"] == 100000, f"hp={m6['hp']} logs={'|'.join(logs6)[:200]}")

    print("【副本：行动序排序（v57）】")
    m = Main(None)
    async def cmd(m, handler_name, gid, qid, msg):
        ev = FakeEvent(gid, qid, msg)
        handler = getattr(m, handler_name)
        results = await run(handler, ev)
        return results[-1] if results else ""
    await cmd(m, "register", "g1", "i1", "注册 战士 慢速 男")
    await cmd(m, "register", "g1", "i2", "注册 游侠 高速 男")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i2", level=40, gold=10000, cur_map="dawn_city")
    await cmd(m, "party", "g1", "i1", "组队 高速")
    # v86.3 入场钥匙：旧王陵需要王陵钥匙
    db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    st = db.get_battle("g1", "i1")["state"]
    spds = {k: st["players"][k].get("spd", 0) for k in st["members"]}
    check("成员按速度降序", spds[st["members"][0]] >= spds[st["members"][1]], str(spds))
    check("开本地图模式", "副本开启" in out, out[:200])
    # v87.2 副本地图化：探索触发第 1 层战斗
    await cmd(m, "explore", "g1", "i1", "探索")
    st = db.get_battle("g1", "i1")["state"]
    # Boss 多动：把 Boss 速度拉满，验证 Boss 回合行动多次
    st["boss"]["spd"] = 999
    st["boss"]["atk"] = 5
    st["boss"]["matk"] = 5
    st["boss"]["hp"] = 99999
    st["boss"]["max_hp"] = 99999
    for k in st["players"]:
        st["players"][k]["hp"] = 99999
        st["players"][k]["max_hp"] = 99999
        st["players"][k]["spd"] = 1
    st["turn"] = 0
    st["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", st)
    out1 = await cmd(m, "attack", "g1", st["members"][0], "攻击")
    out2 = await cmd(m, "attack", "g1", st["members"][1], "攻击")
    check("Boss 多动提示", "再次出手" in (out1 + out2), (out1 + out2)[:300])
    for q in ("i1", "i2"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print(f"\n结果: {passed} passed, {failed} failed")
    return failed

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
