# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑： v101.24 端到端验证：镇长对话接取支线 s2（迷路的商人）"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import C, db, clean_db, Main, FakeEvent, run  # noqa: E402

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


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人 男")
    db.update_player("g1", "w1", level=10, gold=5000, cur_map="oak_town", cur_subarea="oak_town_2")

    # 主线推到 q1_2（q1_1 完成），s2 未接
    db.save_quests("g1", "w1", {
        "main_quest": "q1_2", "main_status": "active", "main_progress": {},
        "daily": {}, "completed_main": ["q1_1"], "side": {}})

    # 找镇长 → 对话里应有『有活儿要交给我吗』
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    print(out)
    check("对话含接支线选项", "有活儿要交给我吗" in out, out[:200])

    # 选『有活儿要交给我吗』（需要知道序号——找出来）
    import re
    lines = out.split("\n")
    idx = None
    for ln in lines:
        mt = re.match(r"^(\d+)\. 📜 有活儿要交给我吗", ln)
        if mt:
            idx = int(mt.group(1))
    check("定位接支线选项序号", idx is not None, str(lines))
    if idx is None:
        print(f"\n结果: {passed} 通过, {failed} 失败")
        return 1 if failed else 0

    out2 = await cmd(m, "talk_choice", "g1", "w1", f"对话 {idx}")
    print(out2)
    check("接取提示出现", "迷路的商人" in out2, out2[:300])

    q = db.get_quests("g1", "w1")
    check("s2 已入存档", "s2" in (q.get("side") or {}), str(q.get("side")))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return 1 if failed else 0


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
