# -*- coding: utf-8 -*-
"""临时调试：复现 test_v104_quests [1] 段，打印每步输出"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests')
sys.path.insert(0, '.')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
from conftest import C, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

def qdata(qid, status, prog=None):
    return {"main_quest": qid, "main_status": status, "main_progress": prog or {},
            "side": {}, "completed_main": [], "completed_side": []}

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "p1", "注册 战士 旅人 男")
    db.update_player("g1", "p1", level=30, cur_map="dawn_city", cur_subarea="dawn_city_2")
    db.save_quests("g1", "p1", qdata("q5_5", "active"))
    print("--- 步骤1: 对话 国王（无花，active）---")
    out = await cmd(m, "talk_choice", "g1", "p1", "对话 国王")
    print(repr(out[:300]))
    print("状态:", db.get_quests("g1", "p1")["main_status"])
    db.add_item("g1", "p1", "mat_sheng_guang_bai_he", {"name": "圣光百合", "type": "材料", "stackable": True, "price": 30}, 1)
    print("--- 步骤2: 对话 国王（有花）---")
    out = await cmd(m, "talk_choice", "g1", "p1", "对话 国王")
    print(repr(out[:300]))
    print("状态:", db.get_quests("g1", "p1")["main_status"])
    print("--- 步骤3: 对话 国王（再对话）---")
    out = await cmd(m, "talk_choice", "g1", "p1", "对话 国王")
    print(repr(out[:400]))
    print("状态:", db.get_quests("g1", "p1")["main_status"])
    print("--- 步骤4: 回复 2 ---")
    out = await cmd(m, "talk_choice", "g1", "p1", "2")
    print(repr(out[:400]))
    print("--- 步骤5: 回复 1 ---")
    out = await cmd(m, "talk_choice", "g1", "p1", "1")
    print(repr(out[:400]))
    print("最终:", db.get_quests("g1", "p1"))

asyncio = __import__('asyncio')
asyncio.run(main())
