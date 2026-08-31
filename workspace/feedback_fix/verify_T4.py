# -*- coding: utf-8 -*-
"""T4 背包页数位置验证脚本（改前/改后通用，证据输出）。

需求（玩家意见 #5 zerc）：『背包』的页数/翻页提示放到底部。

输出各视图完整文本 + 首行/末行页数提示归属，便于前后对比：
  - 背包          （第 1 页）
  - 背包 2        （翻页指令仍可用）
  - 背包 3        （越界 clamp）
  - 背包筛选 材料 2 （筛选视图翻页）
  - 上一页        （相对翻页）

运行：python.exe workspace/feedback_fix/verify_T4.py
"""
import asyncio
import os
import sys

os.environ["GWEN_GAME_DB"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_T4_verify.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "tests"))
from conftest import db, FakeEvent, run, clean_db, make_player  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402

GID, QID = "g1", "q1"


def seed_bag(n=17):
    """17 件材料 → 背包 2 页（每页 10 件，v127.2）。"""
    for i in range(1, n + 1):
        db.add_item(GID, QID, f"mat_t{i}",
                    {"name": f"测试材料{i}", "type": "材料", "stackable": False})


def has_page_info(line):
    return ("第 " in line and " 页" in line) or ("页数" in line)


async def show(m, label, msg, handler):
    replies = [r for r in await run(handler, FakeEvent(GID, QID, msg)) if r is not None]
    out = "\n".join(replies)
    lines = out.splitlines()
    print(f"===== {label} 指令=『{msg}』 =====")
    print(out)
    print(f"--- 首行含页数提示: {has_page_info(lines[0]) if lines else '-'}")
    print(f"--- 末行含页数提示: {has_page_info(lines[-1]) if lines else '-'}")
    print()


async def main():
    m = Main(None)
    clean_db()
    make_player(GID, QID)
    seed_bag(17)
    await show(m, "背包(第1页)", "背包", m.inventory)
    await show(m, "翻页-背包 2", "背包 2", m.inventory)
    await show(m, "越界-背包 3", "背包 3", m.inventory)
    await show(m, "筛选翻页-背包筛选 材料 2", "背包筛选 材料 2", m.bag_filter)
    await show(m, "相对翻页-上一页", "上一页", m.inventory)


if __name__ == "__main__":
    asyncio.run(main())
    print("DONE")