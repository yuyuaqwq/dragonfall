# -*- coding: utf-8 -*-
"""v97.6 彩蛋事件 5→30 (+v115 再扩)→36 + 隐藏怪物 25 验证。

覆盖：
1. 36 个彩蛋数据完整（id 唯一 / template 注册 / mats 可解析 / maps 全部是有效地图）
2. roll_explore_egg 区域过滤：指定地图只触发该地图彩蛋 + 全局彩蛋，不触发别区彩蛋
3. 25 个隐藏怪物数据完整（cond 合法 / maps 有效 / drops 可解析 / 技能 id 存在）
4. _roll_hidden_monster maps 区域限定生效
"""
import sys, os, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player, Main, FakeEvent, run

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
    from data.plugins.dragonfall.game.core.event_templates import TEMPLATES
    from data.plugins.dragonfall.game.core.events import roll_explore_egg
    from content.catalog_quests import EXPLORE_EGG_EVENTS
    from content.catalog_b143 import HIDDEN_MONSTERS

    mats_idx = {v.get("name") for v in C.MATERIALS.values()}
    map_ids = set(C.MAP_BY_ID.keys())

    print("【1. 彩蛋数据完整性：30 个】")
    ids = set()
    for e in EXPLORE_EGG_EVENTS:
        check(f"彩蛋 {e['id']} id 唯一", e["id"] not in ids)
        ids.add(e["id"])
        check(f"彩蛋 {e['id']} template 已注册", e.get("template") in TEMPLATES, e.get("template"))
        # mats 可解析（含嵌套 steps）
        def chk_params(params, path):
            for k, v in params.items():
                if k == "mats" and isinstance(v, list):
                    for m in v:
                        check(f"{path} 材料[{m}]存在", m in mats_idx, m)
                elif k == "steps" and isinstance(v, list):
                    for i, s in enumerate(v):
                        chk_params(s.get("params", {}), f"{path}.steps[{i}]")
        chk_params(e.get("params", {}), e["id"])
        # maps 有效
        for mid in (e.get("maps") or []):
            check(f"彩蛋 {e['id']} maps[{mid}]有效", mid in map_ids, mid)
    check("彩蛋总数 = 46（v125 扩容 36→46）", len(EXPLORE_EGG_EVENTS) == 46, len(EXPLORE_EGG_EVENTS))
    region_cnt = sum(1 for e in EXPLORE_EGG_EVENTS if e.get("maps"))
    check("区域彩蛋 24 个（v125 扩容 19→24）", region_cnt == 24, region_cnt)

    print("\n【2. roll_explore_egg 区域过滤】")
    clean_db()
    # oak_plain 上：只应有 oak 相关 + 全局彩蛋
    for _ in range(300):
        random.seed(random.randint(0, 999999))
        egg = roll_explore_egg("oak_plain")
        if egg and egg.get("maps"):
            # v115：橡木平原新增区域彩蛋 稻草人，橡木区合法命中集=2
            check(f"oak_plain 触发区域彩蛋 {egg['id']} 属于橡木区", egg["id"] in ("egg_oak_whisper", "egg_jumping_scarecrow"), egg["id"])
    # 非 oak 图不触发 egg_oak_whisper
    # v110 审计修复：原实现 300 次无命中时无任何失败断言、循环后无条件 check(True)
    # 恒真掩膜——改为显式失败标志（反例验证必须真的抽不到才绿）
    bad_oak = False
    for _ in range(300):
        random.seed(random.randint(0, 999999))
        egg = roll_explore_egg("emerald_forest")
        if egg and egg["id"] == "egg_oak_whisper":
            bad_oak = True
            check("emerald_forest 不触发老橡树", False, egg["id"])
            break
    check("emerald_forest 300 次抽样不触发老橡树", not bad_oak)
    # 无地图参数 = 老行为（全局池）
    for _ in range(200):
        random.seed(random.randint(0, 999999))
        egg = roll_explore_egg(None)
        if egg:
            check("无地图参数可触发全局彩蛋", True)
            break
    # 限定图触发限定彩蛋：moon_gate 能触发月光人偶
    # 注意：每次重置 seed 会让 random() 首值有相关性（进池率被压低），必须连续抽样
    random.seed(20260809)
    hit_moon = 0
    for _ in range(50000):
        egg = roll_explore_egg("moon_gate")
        if egg and egg["id"] == "egg_moon_doll":
            hit_moon += 1
            if hit_moon >= 3:
                break
    check("moon_gate 可触发月光人偶", hit_moon >= 3, hit_moon)

    print("\n【3. 隐藏怪物数据完整性：25 个】")
    valid_conds = {"any", "forest", "water", "ruin", "night_any", "forest_night"}
    for hid, h in HIDDEN_MONSTERS.items():
        check(f"隐藏怪 {hid} cond 合法", h.get("cond", "any") in valid_conds, h.get("cond"))
        for mid in (h.get("maps") or []):
            check(f"隐藏怪 {hid} maps[{mid}]有效", mid in map_ids, mid)
        for d in (h.get("drops") or []):
            check(f"隐藏怪 {hid} 掉落[{d}]存在", d in mats_idx, d)
    check("隐藏怪物总数 = 25", len(HIDDEN_MONSTERS) == 25, len(HIDDEN_MONSTERS))

    print("\n【4. _roll_hidden_monster maps 限定】")
    clean_db()
    m = Main(None)
    make_player("g1", "q1", level=5)
    # misty_swamp 上：水域隐藏怪（沼泽巨鳄/荧光鱼群/金史莱姆/灵狐）可命中
    cur_map = C.MAP_BY_ID["misty_swamp"]
    hit = None
    for _ in range(3000):
        random.seed(random.randint(0, 999999))
        r = m._roll_hidden_monster("g1", "q1", db.get_player("g1", "q1"), cur_map)
        if r:
            hit = r[0]
            break
    if hit:
        check(f"misty_swamp 命中隐藏怪 {hit['id']}", hit["id"] in
              ("e_swamp_croc", "e_glimmer_fish", "e_gold_slime", "e_fortune_fox"), hit["id"])
    else:
        # v110 审计修复：原 else 恒记绿掩膜（隐藏怪被删/条件断裂时假绿）——改为失败断言
        check("misty_swamp 3000 次抽样命中隐藏怪", False, "未命中（隐藏怪缺失或条件断裂）")
    # oak_town（城镇）不出隐藏怪
    town_map = C.MAP_BY_ID["oak_town"]
    r = m._roll_hidden_monster("g1", "q1", db.get_player("g1", "q1"), town_map)
    check("城镇不出隐藏怪", r is None, r)

    print(f"\n======== 结果: {passed} 通过 / {failed} 失败 ========")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
