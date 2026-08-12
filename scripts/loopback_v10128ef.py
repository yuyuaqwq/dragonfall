# -*- coding: utf-8 -*-
"""v101.28e/f loopback 实测：食物效果独立化 + 药水特殊效果（真实 AstrBot 环境）"""
import os, sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PLUGIN_DIR = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall"
sys.path.insert(0, r"C:/Users/yuyu/qqbot")
sys.path.insert(0, PLUGIN_DIR)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "game", "game_data.db"))

from data.plugins.dragonfall.main import Main
from data.plugins.dragonfall.game import content as C, db

class FakeEvent:
    def __init__(self, msg, group_id="g_loop", qq_id="loop_v10128e"):
        self.message_str = msg
        self.message = [{"type": "text", "data": {"text": msg}}]
        self.group_id = group_id
        self.qq_id = qq_id
        self.self_id = "bot"
        self.msg_type = "group"
        self.stop_event = None
        self.reply_called = []
        self._g = group_id
        self._q = qq_id
        self._stopped = False
    def get_group_id(self):
        return self._g
    def get_sender_id(self):
        return self._q
    def get_message_str(self):
        return self.message_str
    def plain_result(self, text):
        self.reply_called.append(text)
        return text

async def run_cmd(main, handler_name, cmd, gid, qid):
    ev = FakeEvent(cmd, gid, qid)
    handler = getattr(main, handler_name, None)
    if handler is None:
        return f"(无 handler: {handler_name})"
    results = []
    async for r in handler(ev):
        if r is not None:
            results.append(str(r) if not hasattr(r, "text") else r.text)
    return "\n".join(results) if results else "\n".join(ev.reply_called)

async def main_loop():
    m = Main(None)
    gid, qid = "g_loop", "loop_v10128e"
    r0 = await run_cmd(m, "register", "注册 试吃员 男 人类", gid, qid)
    print("【注册】", r0[:120], "\n---")
    # 塞蛇羹（food_effect=lifesteal）+ 狂怒药剂（next_atk_up）+ 岩盾药剂（shield_small）
    snake = C.ITEMS["i_snake_soup"]
    fury = C.ITEMS["i_fury_potion"]
    rock = C.ITEMS["i_rock_shield_pot"]
    db.add_item(gid, qid, "i_snake_soup", snake)
    db.add_item(gid, qid, "i_fury_potion", fury)
    db.add_item(gid, qid, "i_rock_shield_pot", rock)
    # 看物品详情 desc（新数值文案）
    r = await run_cmd(m, "item_detail", "物品详情 蛇羹", gid, qid)
    print("【蛇羹详情】\n", r[:300], "\n---")
    r = await run_cmd(m, "item_detail", "物品详情 狂怒药剂", gid, qid)
    print("【狂怒药剂详情】\n", r[:300], "\n---")
    # 进战斗（直接改位置到野外，循环探索直到遇怪）
    db.update_player(gid, qid, cur_map="oak_plain", cur_subarea="oak_plain_1")
    for _i in range(6):
        r = await run_cmd(m, "explore", "探索", gid, qid)
        if any(k in r for k in ("⚔️", "遭遇", "战斗开始", "野狗", "史莱姆")):
            break
    print("【探索】", r[:150], "\n---")
    r = await run_cmd(m, "attack", "攻击", gid, qid)
    print("【首回合】", r[:200], "\n---")
    # 战斗中使用蛇羹
    r = await run_cmd(m, "use", "使用 蛇羹", gid, qid)
    print("【战斗吃蛇羹】\n", r[:400], "\n---")
    # 战斗中使用狂怒药剂
    r = await run_cmd(m, "use", "使用 狂怒药剂", gid, qid)
    print("【战斗用狂怒药剂】\n", r[:400], "\n---")
    # 战斗中使用岩盾药剂
    r = await run_cmd(m, "use", "使用 岩盾药剂", gid, qid)
    print("【战斗用岩盾药剂】\n", r[:400], "\n---")
    # 状态行（看护盾/蓄力显示）——attack 回合尾会带 _battle_footer
    r = await run_cmd(m, "attack", "攻击", gid, qid)
    print("【下一回合状态】\n", r[:400])

asyncio.run(main_loop())
