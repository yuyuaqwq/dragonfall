# -*- coding: utf-8 -*-
"""体验驱动：以玩家身份完整走一遍新手流程（只打印输出，不断言）。
用法：python playthrough.py <起始步骤>
"""
import sys, os, asyncio
sys.path.insert(0, r'C:\Users\yuyu\qqbot')
sys.path.insert(0, r'C:\Users\yuyu\qqbot\data\plugins\dragonfall')
os.environ['GWEN_GAME_DB'] = r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\test_game_data.db'
from data.plugins.dragonfall.game import db
from data.plugins.dragonfall.main import Main

G, Q = 'g100', 'q100'  # 玩家身份：新手冒险者

class FE:
    def __init__(s, msg=''): s._g, s._q, s.message_str = G, Q, msg
    def get_group_id(s): return s._g
    def get_sender_id(s): return s._q
    def get_message_str(s): return s.message_str
    def plain_result(s, t): return t

async def run(h, ev):
    rs = []
    try:
        while True: rs.append(await h(ev).__anext__())
    except StopAsyncIteration: pass
    return rs

async def main():
    db.init_db()
    m = Main(None)
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    async def go(step, handler, msg, label):
        if step < start: return
        print(f"\n{'='*58}\n▶ [{label}] 『{msg}』\n{'='*58}")
        try:
            out = ''.join(str(x) for x in await run(getattr(m, handler), FE(msg)))
            print(out)
        except Exception as e:
            print(f"❌ 异常: {type(e).__name__}: {e}")

    # ---- 新玩家流程 ----
    await go(1, 'register', '注册 战士 格温', '注册')
    await go(2, 'profile', '角色', '角色面板')
    await go(3, 'map_view', '地图', '地图（广场）')
    await go(4, 'find_npc', '找 镇长', '找镇长')
    await go(5, 'talk_choice', '对话 1', '镇长对话1')
    await go(6, 'quest_view', '任务', '任务面板')
    await go(7, 'shop', '商店', '商店（广场？）')

asyncio.run(main())
