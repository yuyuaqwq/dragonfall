# -*- coding: utf-8 -*-
"""v101.28 loopback 实测：食物 hot 战斗内全链路（真实 AstrBot 环境）"""
import os, sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PLUGIN_DIR = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall"
sys.path.insert(0, r"C:/Users/yuyu/qqbot")
sys.path.insert(0, PLUGIN_DIR)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "game", "game_data.db"))

from data.plugins.dragonfall.main import Main
from data.plugins.dragonfall.game import content as C, db

class FakeEvent:
    def __init__(self, msg, group_id="g_loop", qq_id="loop_hot_t1"):
        self.message_str = msg
        self.message = [{"type": "text", "data": {"text": msg}}]
        self.group_id = group_id
        self.qq_id = qq_id
        self.self_id = "bot"
        self.msg_type = "group"
        self.stop_event = None
        self.reply_called = []
    def plain_result(self, text):
        self.reply_called.append(text)
        return text

async def run_cmd(main, cmd, gid, qid, name, gender="男", race="人类"):
    ev = FakeEvent(cmd, gid, qid)
    async for _ in main.handle(ev):
        pass
    return "\n".join(ev.reply_called)

async def main_loop():
    m = Main(None)
    gid, qid = "g_hot", "loop_hot_1"
    # 注册角色
    await run_cmd(m, "注册 测试阿汤 男 人类", gid, qid, "注册")
    # 塞麦酒 + 治疗药水(小)
    inv = db.get_inventory(gid, qid)
    db.add_item(gid, qid, "i_ale", {"name": "麦酒", "price": 10, "hot": 0.05, "hot_turns": 3,
                                    "hot_mana": 0.06, "heal": 0.15, "mana": 0.15, "stamina": 15,
                                    "desc": "回复 15% HP/MP＋15 体力；战斗中每回合回复 5% 生命、6% 魔力（3 回合）"})
    # 战斗外使用 → 即时回复
    r1 = await run_cmd(m, "使用 麦酒", gid, qid, "使用")
    print("【战斗外使用麦酒】")
    print(r1[:200])
    print("---")
    # 战斗内：走到野外打怪 → 使用麦酒 → 攻击看 hot 结算
    r2 = await run_cmd(m, "前往 橡木平原", gid, qid, "移动")
    print("【前往野外】", r2[:80])
    r3 = await run_cmd(m, "攻击", gid, qid, "攻击")
    print("【首回合攻击】", r3[:150])
    r4 = await run_cmd(m, "使用 麦酒", gid, qid, "战斗内使用")
    print("【战斗内使用麦酒】")
    print(r4[:300])
    print("---")
    r5 = await run_cmd(m, "攻击", gid, qid, "下一回合")
    print("【下一回合攻击(hot结算)】")
    print(r5[:400])
    print("===")
    # 清理测试角色（不污染生产库）
    db.delete_player(gid, qid)
    print("测试角色已清理")

asyncio.run(main_loop())
print("DONE")
