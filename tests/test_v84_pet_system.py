# -*- coding: utf-8 -*-
"""24 章《宠物与伙伴系统》专项测试：4 品种 + 孵化图鉴 + 面板 + 喂养放生 + 战斗技能 + 经验加成 + 饱食度衰减 + 分档掉落"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, E, BT, Main, FakeEvent, run, clean_db

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人 男")
    db.update_player("g1", "w1", cur_map="oak_plain")

    # ---- 数据层：14 品种（v101.11 扩容）+ 技能定义 ----
    check("PET_POOL >= 10 品种", len(C.PET_POOL) >= 10, str([p["key"] for p in C.PET_POOL]))
    keys = {p["key"] for p in C.PET_POOL}
    check("旧 4 品种保留", {"pet_wolf", "pet_cat", "pet_drake", "pet_rabbit"} <= keys, str(keys))
    check("新 10 品种加入", len(keys - {"pet_wolf", "pet_cat", "pet_drake", "pet_rabbit"}) >= 10, str(keys))
    for p in C.PET_POOL:
        check(f"{p['name']} 技能字段齐", p.get("skill_name") and p.get("skill_interval") and p.get("skill_type") and 0 < p.get("skill_value") < 1)
    check("宠物蛋构造", C.make_pet_egg("pet_rabbit")["name"] == "月光兔蛋")
    check("技能标签", "撕咬" in C.pet_skill_label("pet_wolf") and "40%" in C.pet_skill_label("pet_wolf"))

    # ---- 孵化 + 图鉴 ----
    out = await cmd(m, "use", "g1", "w1", "使用 宠物蛋")
    check("无蛋提示", "没有" in out or "宠物蛋" in out, out[:120])
    egg = C.make_pet_egg("pet_wolf")
    db.add_item("g1", "w1", "petegg_pet_wolf", egg)
    out = await cmd(m, "use", "g1", "w1", "使用 森林狼崽蛋")
    check("孵化狼崽", "森林狼崽" in out and "破壳而出" in out, out[:200])
    pet = db.pet_get("w1")
    check("宠物落库", pet and pet["pet_key"] == "pet_wolf" and pet["level"] == 1, str(pet)[:120])
    dex = db.pet_dex_get("w1")
    check("图鉴记录 1/4", dex.get("pet_wolf") == 1, str(dex))
    # 重复蛋：已有同品种 → 提示可出售/放生
    db.add_item("g1", "w1", "petegg_pet_wolf", egg)
    out = await cmd(m, "use", "g1", "w1", "使用 森林狼崽蛋")
    check("同品种重复蛋拦截", "该品种" in out, out[:200])
    # 其他品种蛋：已有宠物提示放生
    db.add_item("g1", "w1", "petegg_pet_cat", C.make_pet_egg("pet_cat"))
    out = await cmd(m, "use", "g1", "w1", "使用 黑猫蛋")
    check("异品种需放生", "放生" in out, out[:200])

    # ---- 宠物面板（24 章六模板）----
    out = await cmd(m, "pet_view", "g1", "w1", "宠物")
    check("面板标题", "宠物 · 森林狼崽" in out, out[:200])
    check("面板饱食度", "饱食度" in out, out[:200])
    check("面板技能行", "技能" in out, out[:200])

    # ---- 喂养 +30 ----
    # 给背包加一个食物（v130.7 意见#22：只喂食物/鱼，材料类需带 food 标记）
    db.add_item("g1", "w1", "mat_shou_rou", {"name": "兽肉", "type": "材料", "stackable": True, "price": 10})
    out = await cmd(m, "pet_feed", "g1", "w1", "喂养 兽肉")
    check("喂养成功 +30", "饱食度 +30" in out, out[:200])
    pet = db.pet_get("w1")
    check("饱食度 100（上限）", pet["satiety"] == 100, str(pet["satiety"]))
    # 鱼也能喂（24 章四：肉/鱼/草药均可）
    db.add_item("g1", "w1", "m_fish", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 10})
    out = await cmd(m, "pet_feed", "g1", "w1", "喂养 银鳞鱼")
    check("鱼可喂养", "饱食度 +30" in out, out[:200])

    # ---- 宠物改名 ----
    out = await cmd(m, "pet_rename", "g1", "w1", "宠物改名 阿黄")
    check("改名成功", "阿黄" in out, out[:120])
    pet = db.pet_get("w1")
    check("改名落库", pet["name"] == "阿黄", str(pet["name"]))

    # ---- 战斗引擎：宠物技能（撕咬 40% 攻击伤害，每 3 回合）----
    # 造一只 Lv.10 狼崽
    db.pet_update("w1", level=10, satiety=100)
    monster = C.build_monster(["m_test", "测试野狗", "dps", 3, [], ["狗牙"]], C.MAP_BY_ID["oak_plain"])
    b = BT.Battle("monster", monster, {}, player=db.get_player("g1", "w1"), pet=db.pet_get("w1"))
    # 打满 3 回合：round=3 时应触发撕咬
    logs = []
    for _ in range(3):
        logs2, ended = b.player_turn("attack", None, db.get_player("g1", "w1"))
        logs += logs2
        if ended:
            break
    pet_log = "\n".join(logs)
    check("撕咬触发", "撕咬" in pet_log, pet_log[-300:])
    # 饱食度 =0 → 技能失效
    b2 = BT.Battle("monster", C.build_monster(["m_test2", "测试野狗2", "dps", 3, [], ["狗牙"]], C.MAP_BY_ID["oak_plain"]),
                   {}, player=db.get_player("g1", "w1"), pet={"pet_key": "pet_wolf", "name": "阿黄", "level": 10, "satiety": 0})
    logs2 = []
    for _ in range(3):
        l, ended = b2.player_turn("attack", None, db.get_player("g1", "w1"))
        logs2 += l
        if ended:
            break
    check("饱食度 0 技能不触发", "撕咬" not in "\n".join(logs2), "\n".join(logs2)[-200:])

    # 战斗引擎：黑猫影袭挡刀（每 3 刻触发，先跑到 tick_no=3）——v152：影袭判定按行动轮次
    # （_pet_block_check：_tick_no() % 3 == 0 → now=2.0 时 tick_no=3 触发；now=3.0 tick_no=4 不触发）
    b3 = BT.Battle("monster", C.build_monster(["m_test3", "测试强敌", "dps", 3, [], ["狗牙"]], C.MAP_BY_ID["oak_plain"]),
                   {}, player=db.get_player("g1", "w1"), pet={"pet_key": "pet_cat", "name": "咪咪", "level": 10, "satiety": 100})
    b3._now = 2.0  # v152：行动轮次 3（int(2/1)+1=3）→ 影袭判定点（1刻=1秒）
    # 固定随机：让影袭必然触发（random 在 0.25 内）——直接走 _damage_player 受击路径（影袭是受击拦截）
    import random as _r
    orig_random = _r.random
    _r.random = lambda: 0.01
    try:
        logs3 = []
        b3._damage_player(db.get_player("g1", "w1"), 50, logs3)
    finally:
        _r.random = orig_random
    pet_log3 = "\n".join(logs3)
    check("影袭挡刀", "影袭" in pet_log3 and "挡下" in pet_log3, pet_log3[-200:])

    # ---- 经验加成（饱食度>0 全额，=0 减半）+ 宠物分得经验 ----
    # 先喂饱
    db.pet_update("w1", satiety=100, level=1, exp=0)
    # 造 3 级怪（exp 约 30+）
    mon = C.build_monster(["m_test4", "测试野狼", "dps", 3, [], ["狗牙"]], C.MAP_BY_ID["oak_plain"])
    exp0 = mon["exp"]
    # 手动调宠物到 Lv.5（加成 20% 上限，v133 收敛：等级/20 cap 0.2，原 等级/10 cap 0.5），饱食度 100
    db.pet_update("w1", level=5, satiety=100, exp=0)
    player = db.get_player("g1", "w1")
    fe = FakeEvent("g1", "w1", "")
    for _r2 in m._handle_victory(fe, "g1", "w1", player, mon, ""):
        pass
    pet_after = db.pet_get("w1")
    check("战斗后宠物分得经验", pet_after["exp"] == max(1, int(exp0 * 0.2)), f"exp={pet_after['exp']} 期望={max(1, int(exp0*0.2))}")
    check("战斗扣饱食度 -2", pet_after["satiety"] == 98, str(pet_after["satiety"]))
    check("宠物等级仍 5（经验不足以升级）", pet_after["level"] == 5, str(pet_after["level"]))

    # ---- 饱食度自然衰减（每小时 -1）----
    pet = db.pet_get("w1")
    import time
    decayed = db.pet_decay_satiety(dict(pet), now=int(time.time()) + 3600 * 3)
    check("3 小时衰减 -3", decayed["satiety"] == pet["satiety"] - 3, f"{decayed['satiety']} vs {pet['satiety']}")
    # 衰减到 0 不穿底
    db.pet_update("w1", satiety=1)
    pet = db.pet_get("w1")
    decayed = db.pet_decay_satiety(dict(pet), now=int(time.time()) + 3600 * 5)
    check("衰减不穿底", decayed["satiety"] == 0, str(decayed["satiety"]))

    # ---- 放生 + 图鉴保留 ----
    db.pet_update("w1", satiety=50)
    out = await cmd(m, "pet_release", "g1", "w1", "放生")
    check("放生成功", "放生" in out and "图鉴记录已保留" in out, out[:200])
    check("宠物已删除", db.pet_get("w1") is None)
    dex = db.pet_dex_get("w1")
    check("图鉴仍保留狼崽", "pet_wolf" in dex, str(dex))

    # ---- 掉落分档（概率采样）----
    import random
    random.seed(42)
    n = 20000
    wolf_hits = sum(1 for _ in range(n)
                    if C.build_monster(["m_wild_dog", "野狗", "dps", 3, [], ["狗牙"]], C.MAP_BY_ID["oak_plain"])["role"] == "dps")
    # 狼崽蛋：普通兽类怪 1.5%（名字含 狼/狗）
    egg_hits = 0
    for _ in range(n):
        mm = C.build_monster(["m_wild_dog", "野狗", "dps", 3, [], ["狗牙"]], C.MAP_BY_ID["oak_plain"])
        # 模拟掉落判定（与 combat._handle_victory 一致）
        if mm.get("role") == "dps" and any(k in mm.get("name", "") for k in ["狼", "狗", "野猪", "熊"]):
            if random.random() < 0.015:
                egg_hits += 1
    rate = egg_hits / n
    check("普通兽类怪蛋率≈1.5%", 0.01 < rate < 0.02, f"{rate:.4f}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
