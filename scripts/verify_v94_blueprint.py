# -*- coding: utf-8 -*-
"""v94 图纸经济验证：铁匠铺买图纸 + Boss 5% + 重复图纸折算残页 + 出售残页"""
import sys, os, re, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player, new_main

async def cmd(m, name, gid, qid, text):
    ev = FakeEvent(gid, qid, text)
    handler = getattr(m, name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    m = new_main()
    make_player("g1", "q1", level=10)
    db.update_player("g1", "q1", cur_map="oak_town", cur_subarea="oak_town_3", gold=50000)
    # 1) 铁匠铺商店面板显示图纸
    out = await cmd(m, "shop", "g1", "q1", "商店")
    bp_line = [l for l in out.split("\n") if "图纸" in l]
    print("== 商店面板图纸行 ==")
    for l in bp_line:
        print(" ", l.strip())
    # 2) 按序号买图纸（材料之后第一项 = 图纸，序号 = len(材料)+1）
    mat_count = len([l for l in out.split("\n") if "锻造材料" in l])
    idx = mat_count + 1
    out = await cmd(m, "buy", "g1", "q1", f"购买 {idx}")
    print(f"== 购买 {idx}（材料后第一项）==")
    print(out[:200])
    bp_name = None
    mm = re.search(r"【(.+?图纸)】", out)
    if mm:
        bp_name = mm.group(1)
    if not bp_name:
        print("❌ 没买到图纸！")
        return
    # 3) 学习图纸
    out = await cmd(m, "learn", "g1", "q1", f"学习 {bp_name}")
    print(f"== 学习 {bp_name} ==")
    print(out[:150])
    # 4) 模拟 Boss 掉已学图纸 → 折算残页（monkeypatch roll_drop 强制掉已学图纸）
    p = db.get_player("g1", "q1")
    learned = p.get("learned_blueprints") or []
    bp = C.roll_blueprint(10)
    if bp["blueprint_for"] not in learned:
        db.update_player("g1", "q1", learned_blueprints=learned + [bp["blueprint_for"]])
    import data.plugins.dragonfall.game.content as C_mod
    _orig_roll_drop = C_mod.roll_drop
    C_mod.roll_drop = lambda lv, role: (None, bp, 0, 0)  # 必掉 bp（已学）
    try:
        mon = {"lv": 10, "role": "boss", "drops": [], "exp": 50, "gold": 0, "name": "测试Boss", "is_boss": True}
        ev = FakeEvent("g1", "q1", "")
        lines = []
        for r in m._handle_victory(ev, "g1", "q1", db.get_player("g1", "q1"), mon, "test"):
            lines.append(str(r))
    finally:
        C_mod.roll_drop = _orig_roll_drop
    out = "\n".join(lines)
    print("== Boss 掉已学图纸 ==")
    for line in out.split("\n"):
        if "残页" in line or "图纸" in line:
            print(" ", line)
    inv = db.get_inventory("g1", "q1")
    pages = sum(it["count"] for it in inv if it["key"] == "mat_tu_zhi_can_ye")
    print(f"== 背包图纸残页数量: {pages} ==")
    # 5) 出售残页
    out = await cmd(m, "sell", "g1", "q1", "出售 图纸残页")
    print("== 出售 图纸残页 ==")
    print(out[:150])
    # 6) Boss 5% 掉落率统计
    hits = 0
    N = 2000
    for _ in range(N):
        random.seed()
        d = C.roll_drop(40, "boss")
        if d[1] is not None:
            hits += 1
    print(f"== Boss 图纸掉率统计: {hits}/{N} = {hits/N:.1%}（期望 5%）==")

import random
asyncio.run(main())
