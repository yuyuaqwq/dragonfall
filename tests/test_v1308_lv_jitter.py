# -*- coding: utf-8 -*-
"""v130.8 野外普通怪等级波动 ±2 固化测试（玩家意见 #32）

覆盖：
  ① build_monster 普通怪 lv_jitter=2：N 次等级 ∈ [map_lv-2, map_lv+2]；
     mock randint 钉 ±2 → 精确 28/32（判别 ±2 而非 ±1）；下限保底 Lv.1
  ② 精英 def：lv_jitter=2 仍固定（base_lv 不变）
  ③ Boss def：固定
  ④ 探索路径（combat.py explore 普通怪分支）：金穗平原野牛 Lv.32/Lv.28、
     橡木平原绿史莱姆 Lv.1 保底（random.random 钉 0.99 跳过事件/精英/Boss）
  ⑤ 撞怪路径（world.py _travel_ambush）：野牛 Lv.32/Lv.28
  ⑥ 回归：build_monster 其他字段稳定（键集合/身份/地图字段不因 jitter 变化）

运行：python tests/test_v1308_lv_jitter.py（exit=0 全绿）
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, db, clean_db, Main, FakeEvent, run, make_player  # noqa: E402

passed = failed = 0
G = 1095961608
GP = C.MAP_BY_ID["gold_plain"]   # 金穗平原 lv30，入口子区域 gold_plain_1 野牛 lv30
OAK = C.MAP_BY_ID["oak_plain"]   # 橡木平原 lv1，入口子区域 oak_plain_1 绿史莱姆 lv1
BULL = GP["subareas"][0]["monsters"][0]      # ('m_wild_bull', '野牛', 'tank', 30, ...)
SLIME = OAK["subareas"][0]["monsters"][0]    # 绿史莱姆 lv1

NORM_DEF = ("m_norm_test", "普通测试怪", "tank", 30, [], [])
ELITE_DEF = ("m_elite_test", "精英测试怪", "elite", 30, [], [])
BOSS_DEF = ("m_boss_test", "Boss测试怪", "boss", 30, [], [])


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def with_randint(val, fn):
    """临时把 random.randint 钉死为固定返回值，执行 fn 后恢复。"""
    orig = random.randint
    try:
        random.randint = lambda a, b: val
        return fn()
    finally:
        random.randint = orig


async def explore(level, map_id, rint_val):
    """完整探索：random.random 钉 0.99（跳过事件/空探索/精英/Boss/隐藏怪 →
    必走普通怪分支），random.randint 钉 rint_val（build_monster 等级波动）。"""
    clean_db()
    make_player(G, "p1", "等级波动", "战士", level=level)
    db.update_player(G, "p1", cur_map=map_id)
    m = Main(None)
    orig_r, orig_i = random.random, random.randint
    try:
        random.random = lambda: 0.99
        random.randint = lambda a, b: rint_val
        ev = FakeEvent(G, "p1", "探索")
        out = await run(m.explore, ev)
    finally:
        random.random, random.randint = orig_r, orig_i
    return "".join(str(x) for x in out)


async def main():
    print("【① build_monster 普通怪 ±2 波动区间】")
    # 真实随机 N 次：全部落在 [28, 32]
    lvs = [C.build_monster(NORM_DEF, GP, lv_jitter=2)["lv"] for _ in range(300)]
    check("N=300 全部 ∈ [28, 32]", all(28 <= l <= 32 for l in lvs), f"min={min(lvs)} max={max(lvs)}")
    # mock 钉 ±2：精确判别（若 jitter=1 则钉 2 只会得 31、钉 -2 得 29）
    lv_up = with_randint(2, lambda: C.build_monster(NORM_DEF, GP, lv_jitter=2)["lv"])
    lv_dn = with_randint(-2, lambda: C.build_monster(NORM_DEF, GP, lv_jitter=2)["lv"])
    check("钉 randint=2 → Lv.32（±2 判别）", lv_up == 32, f"lv={lv_up}")
    check("钉 randint=-2 → Lv.28（±2 判别）", lv_dn == 28, f"lv={lv_dn}")

    print("【② 下限保底 Lv.1】")
    lvs1 = [C.build_monster(SLIME, OAK, lv_jitter=2)["lv"] for _ in range(200)]
    check("lv1 怪 N=200 全部 ≥1", all(l >= 1 for l in lvs1), f"min={min(lvs1)}")
    lv_floor = with_randint(-2, lambda: C.build_monster(SLIME, OAK, lv_jitter=2)["lv"])
    check("lv1 怪钉 -2 → 保底 Lv.1", lv_floor == 1, f"lv={lv_floor}")

    print("【③④ 精英 / Boss 固定】")
    elvs = with_randint(2, lambda: [C.build_monster(ELITE_DEF, GP, lv_jitter=2)["lv"] for _ in range(50)])
    check("精英 lv_jitter=2 固定 30", all(l == 30 for l in elvs), f"{set(elvs)}")
    blvs = with_randint(-2, lambda: [C.build_monster(BOSS_DEF, GP, lv_jitter=2)["lv"] for _ in range(50)])
    check("Boss lv_jitter=2 固定 30", all(l == 30 for l in blvs), f"{set(blvs)}")

    print("【⑤ 探索路径（combat.py explore 普通怪分支）】")
    # 与 test_v1307_zone_risk 同款打桩：野外 NPC 偶遇（日期轮换）与今日奇遇
    _orig_wild = C.roll_wild_encounter
    _orig_tde = C.today_event_effects
    C.roll_wild_encounter = lambda *a, **k: None
    C.today_event_effects = lambda map_id: {}
    try:
        out = await explore(30, "gold_plain", 2)
        check("探索金穗平原钉 2 → 【野牛】Lv.32", "【野牛】Lv.32" in out, out.splitlines()[:2])
        out = await explore(30, "gold_plain", -2)
        check("探索金穗平原钉 -2 → 【野牛】Lv.28", "【野牛】Lv.28" in out, out.splitlines()[:2])
        out = await explore(1, "oak_plain", -2)
        check("探索橡木平原钉 -2 → 【绿史莱姆】Lv.1（保底）", "【绿史莱姆】Lv.1" in out, out.splitlines()[:2])
    finally:
        C.roll_wild_encounter = _orig_wild
        C.today_event_effects = _orig_tde

    print("【⑥ 撞怪路径（world.py _travel_ambush）】")
    m = Main(None)
    orig_r = random.random
    try:
        random.random = lambda: 0.0  # diff=0 → chance=0.18 → 命中
        hit2 = with_randint(2, lambda: m._travel_ambush({"level": 30}, GP))
        hitn2 = with_randint(-2, lambda: m._travel_ambush({"level": 30}, GP))
    finally:
        random.random = orig_r
    check("撞怪钉 2 → 野牛 Lv.32", isinstance(hit2, dict) and hit2["lv"] == 32, f"{hit2}")
    check("撞怪钉 -2 → 野牛 Lv.28", isinstance(hitn2, dict) and hitn2["lv"] == 28, f"{hitn2}")

    print("【⑦ 回归：build_monster 其他字段稳定】")
    m_up = with_randint(2, lambda: C.build_monster(BULL, GP, lv_jitter=2))
    m_dn = with_randint(-2, lambda: C.build_monster(BULL, GP, lv_jitter=2))
    keys_ok = set(m_up) == set(m_dn) and "name" in m_up and "drops" in m_up
    check("键集合不随 jitter 变化", keys_ok, f"{len(m_up)} keys")
    check("身份/地图字段保持", m_up["name"] == "野牛" and m_up["role"] == "tank"
          and m_up["map"] == GP["name"] and m_up["map_area"] == GP.get("area", GP["id"]),
          f"{m_up.get('name')}/{m_up.get('role')}/{m_up.get('map')}")
    check("uid 含波动后等级（确定性）", m_up["uid"] == "e_m_wild_bull-32" and m_dn["uid"] == "e_m_wild_bull-28",
          f"{m_up['uid']}/{m_dn['uid']}")
    check("波动后战斗数值按新等级派生且为正", m_up["hp"] > 0 and m_up["atk"] > 0
          and m_up["exp"] > 0 and m_up["gold"] > 0, f"{m_up.get('hp')}/{m_up.get('exp')}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


_asy = __import__("asyncio")
_asy.run(main())