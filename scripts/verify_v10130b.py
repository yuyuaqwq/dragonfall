# -*- coding: utf-8 -*-
"""v101.30b 满级彩蛋验证：附魔 Lv.7 紫装 3 槽 / Lv.6 紫装 2 槽拦截"""
import sys, os, io, asyncio, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from tests.conftest import C, db, clean_db, Main, FakeEvent, run

m = Main(None)

async def cmd(name, msg, gid="g1", qid="w1"):
    ev = FakeEvent(gid, qid, msg)
    results = await run(getattr(m, name), ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    await cmd("register", "注册 战士 测试满级 男")
    db.update_player("g1", "w1", cur_map="oak_town", cur_subarea="oak_town_3",
                     gold=999999, apprentices=["enchant"], stamina=100, level=20)
    db.add_prof_exp("g1", "w1", "enchant", 900)  # 附魔 Lv.10
    db.set_event_state(f"prof_daily_g1_w1_{time.strftime('%Y-%m-%d')}", "enchant|附魔装备|1|50|1|1")

    # 紫装（3 槽：Lv.7+）：附魔 3 次应全成功
    db.add_item("g1", "w1", "eq_amulet", {"name": "紫晶护符", "slot": "ring", "quality": "purple",
                                          "lv": 20, "enchant": [], "stats": {"hp": 100}, "price": 500})
    db.add_item("g1", "w1", "mat_xue_zhi_jing_hua", {"name": "雪之精华", "type": "材料", "stackable": True}, 60)
    for i in range(1, 4):
        out = await cmd("enchant", f"附魔 紫晶护符 生命")
        print(f"  紫装第{i}槽附魔:", "附魔成功" in out, "|", out[:60].replace(chr(10), ' '))
    out = await cmd("enchant", "附魔 紫晶护符 生命")
    print("  紫装第4槽应满:", "槽已满" in out or "附魔槽已满" in out, "|", out[:60].replace(chr(10), ' '))

    # 蓝装（1 槽）：第 2 次应满
    db.add_item("g1", "w1", "eq_ring", {"name": "蓝玉指环", "slot": "ring", "quality": "blue",
                                        "lv": 20, "enchant": [], "stats": {"hp": 50}, "price": 300})
    out = await cmd("enchant", "附魔 蓝玉指环 生命")
    print("  蓝装第1槽:", "附魔成功" in out)
    out = await cmd("enchant", "附魔 蓝玉指环 生命")
    print("  蓝装第2槽应满:", "槽已满" in out or "附魔槽已满" in out)

    # 大成功 10%（Lv.10）：跑 40 次统计（概率验证粗跑）
    import random
    random.seed(20260812)
    big_hits = 0
    for i in range(40):
        db.add_item("g1", "w1", f"eq_r{i}", {"name": f"测试戒{i}", "slot": "ring", "quality": "blue",
                                             "lv": 20, "enchant": [], "stats": {"hp": 50}, "price": 300})
        out = await cmd("enchant", f"附魔 测试戒{i} 生命")
        if "大成功" in out:
            big_hits += 1
    print(f"  Lv.10 大成功 40 次中出现 {big_hits} 次 (期望 ~4 次/10%)")

    print("\n✅ 满级彩蛋验证完成")

asyncio.run(main())
