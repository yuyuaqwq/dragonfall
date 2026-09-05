# -*- coding: utf-8 -*-
"""v97.4 探索事件扩容 12→30 验证：新模板行为 + 18 个新事件数据完整性 + bless 战斗联动。

覆盖：
1. 30 个常规事件数据完整（id 唯一 / template 注册 / mats 全部可解析）
2. random_choice 概率分支（chance=1 必走 hit，chance=0 必走 miss）
3. stamina_cost 扣体力（浮桥落水）
4. echo_cave 祝福：set_state 写 bless_{gid}_{qid} → Battle 创建自动注入 echo_bless（一次性消耗）
5. Battle 内 atk +5% 生效（_player_stats × BUFF_MULT）
6. 新事件冒烟：18 个新事件固定 seed 跑两轮不崩（覆盖 hit/miss 两条路径）
7. 新材料掉落：loot_materials 给蜂蜜/泛黄书页 正常入包
"""
import sys, os, random, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player, Main, FakeEvent, run, BT

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail).encode('utf-8', 'replace').decode('utf-8', 'replace')[:300]}")

async def main():
    from data.plugins.dragonfall.game.core.event_templates import TEMPLATES, execute_event_template, EventContext
    from data.plugins.dragonfall.game.core.index import _INDEXES
    mats_idx = _INDEXES["materials"]["name_to_id"]

    print("【1. 数据完整性：30 个常规事件】")
    ids = set()
    for ev in C.EXPLORE_EVENTS:
        check(f"事件 {ev['id']} id 唯一", ev["id"] not in ids)
        ids.add(ev["id"])
        check(f"事件 {ev['id']} template 已注册", ev.get("template") in TEMPLATES)
    check("常规事件数量 = 100（v125 扩容 50→100）", len(C.EXPLORE_EVENTS) == 100, len(C.EXPLORE_EVENTS))

    # 新模板注册
    for t in ["random_choice", "stamina_cost"]:
        check(f"v97.4 新模板 {t} 已注册", t in TEMPLATES)

    # 递归检查所有 mats 可解析
    def check_mats(params, path):
        for k, v in params.items():
            if k == "mats" and isinstance(v, list):
                for m in v:
                    check(f"{path} 材料[{m}]可解析", m in mats_idx, m)
            elif k in ("hit", "miss") and isinstance(v, dict):
                check_mats(v.get("params", {}), f"{path}.{k}")
            elif k == "steps" and isinstance(v, list):
                for i, s in enumerate(v):
                    check_mats(s.get("params", {}), f"{path}.steps[{i}]")
    for ev in C.EXPLORE_EVENTS:
        check_mats(ev.get("params", {}), ev["id"])

    print("\n【2. random_choice 概率分支】")
    clean_db()
    m = Main(None)
    make_player("g1", "q1", level=5)
    cur_map = C.MAP_BY_ID["oak_plain"]

    # chance=1 必走 hit
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map, params={
        "chance": 1.0,
        "hit": {"template": "dialog", "params": {"texts": ["HIT!"]}},
        "miss": {"template": "dialog", "params": {"texts": ["MISS!"]}},
    }, name="橡木平原")
    text = execute_event_template("random_choice", ctx)
    check("chance=1 必走 hit", text == "HIT!", text)

    # chance=0 必走 miss
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map, params={
        "chance": 0.0,
        "hit": {"template": "dialog", "params": {"texts": ["HIT!"]}},
        "miss": {"template": "dialog", "params": {"texts": ["MISS!"]}},
    }, name="橡木平原")
    text = execute_event_template("random_choice", ctx)
    check("chance=0 必走 miss", text == "MISS!", text)

    # 嵌套 combo（stone_tablet 结构：hit 里 combo 两步骤）
    random.seed(42)
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map, params={
        "chance": 1.0,
        "hit": {"template": "combo", "params": {"steps": [
            {"template": "set_flag", "params": {"flag": "h_test", "key": "k1", "header": "见闻!"}},
            {"template": "loot_materials", "params": {"mats": ["泛黄书页"], "n": 1, "bp_line": "", "header": "获得 {mats}!"}},
        ]}},
        "miss": {"template": "dialog", "params": {"texts": ["MISS!"]}},
    }, name="橡木平原")
    text = execute_event_template("random_choice", ctx)
    check("嵌套 combo 输出两段", "见闻!" in text and "泛黄书页" in text, text)
    check("combo 内 set_flag 写入", "k1" in db.get_talk_flags("g1", "q1", "h_test"))
    check("combo 内 loot_materials 给泛黄书页", db.count_item("g1", "q1", "泛黄书页") == 1)

    print("\n【3. stamina_cost 扣体力】")
    db.update_player("g1", "q1", stamina=50)
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map,
                       params={"cost": 5, "header": "体力 -{cost} 剩 {stamina}/{max}"}, name="橡木平原")
    text = execute_event_template("stamina_cost", ctx)
    p = db.get_player("g1", "q1")
    check("stamina 50-5=45", p["stamina"] == 45, (p["stamina"], text))
    # 下限 0
    db.update_player("g1", "q1", stamina=2)
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map,
                       params={"cost": 5, "header": "体力 -{cost}"}, name="橡木平原")
    execute_event_template("stamina_cost", ctx)
    p = db.get_player("g1", "q1")
    check("体力下限 0（2-5→0）", p["stamina"] == 0, p["stamina"])

    print("\n【4. echo_cave 祝福 → Battle 联动】")
    clean_db()
    make_player("g1", "q1", level=5)
    # 强制 echo_cave 走 hit（bless 分支）
    ev = next(e for e in C.EXPLORE_EVENTS if e["id"] == "echo_cave")
    params = dict(ev["params"]); params["chance"] = 1.0
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map,
                       params=params, name="橡木平原")
    text = execute_event_template(ev["template"], ctx)
    check("echo_cave hit 文案含 +5%", "攻击力 +5%" in text, text)
    raw = db.get_event_state("bless_q1")
    st = json.loads(raw) if raw else {}
    check("event_state 写入 bless_q1", st.get("pct") == 5, raw)

    # 创建战斗 → 注入 echo_bless + 状态一次性消耗
    p = db.get_player("g1", "q1")
    m_def = cur_map["subareas"][0]["monsters"][0]
    monster = C.build_monster(m_def, cur_map)
    b = BT.Battle("monster", monster, None, player=p)
    check("Battle 注入 echo_bless", b._p_buffs_bag().get("echo_bless") == 1, b._p_buffs_bag())
    raw2 = db.get_event_state("bless_q1")
    check("bless 状态一次性消耗", not raw2, raw2)

    # 第二次战斗不再有 echo_bless
    b2 = BT.Battle("monster", monster, None, player=db.get_player("g1", "q1"))
    check("第二次战斗无 echo_bless", not b2._p_buffs_bag().get("echo_bless"), b2._p_buffs_bag())

    # atk +5% 生效验证
    st0 = b2._player_stats(db.get_player("g1", "q1"))
    st1 = b._player_stats(db.get_player("g1", "q1"))
    check("echo_bless 攻击 +5%", st1["atk"] == int(st0["atk"] * 1.05), (st0["atk"], st1["atk"]))

    print("\n【5. 18 个新事件冒烟（hit+miss 双路径）】")
    new_ids = ["firefly", "old_well", "windmill", "hunter_hut", "beehive", "floating_bridge",
               "old_tree_hollow", "stone_tablet", "cart_wreck", "night_owl", "spider_web",
               "frost_flower", "old_boot", "mushroom_ring", "echo_cave",
               "campfire_ashes", "drifting_bottle", "abandoned_minecart"]
    clean_db()
    make_player("g1", "q1", level=5)
    ok = True
    for eid in new_ids:
        ev = next(e for e in C.EXPLORE_EVENTS if e["id"] == eid)
        for force in [1.0, 0.0]:  # 强制 hit / 强制 miss
            random.seed(7)
            params = dict(ev["params"])
            if ev["template"] == "random_choice":
                params["chance"] = force
            ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map,
                               params=params, name="橡木平原")
            try:
                text = execute_event_template(ev["template"], ctx) or ""
                if force == 1.0 and "hit" in ev.get("params", {}):
                    check(f"{eid} hit 路径出文案", len(text) > 0, text[:80])
            except Exception as ex:
                ok = False
                check(f"{eid} 执行不崩({force})", False, repr(ex))
    check("18 新事件冒烟全部通过", ok)

    print("\n【6. 新材料掉落】")
    clean_db()
    make_player("g1", "q1", level=5)
    random.seed(3)
    ctx = EventContext("g1", "q1", db.get_player("g1", "q1"), cur_map, params={
        "mats": ["蜂蜜"], "n": 1, "bp_line": "", "header": "获得 {mats}!"}, name="橡木平原")
    execute_event_template("loot_materials", ctx)
    check("蜂蜜入包", db.count_item("g1", "q1", "蜂蜜") == 1, db.count_item("g1", "q1", "蜂蜜"))

    print(f"\n======== 结果: {passed} 通过 / {failed} 失败 ========")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
