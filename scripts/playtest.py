# -*- coding: utf-8 -*-
"""实玩体检：注册→找镇长→打怪升级→10级，逐面板检查排版。"""
import os, sys, asyncio, sqlite3

PLUGIN_DIR = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
QQBOT_DIR = r"C:\Users\yuyu\qqbot"
TEST_DB = os.path.join(PLUGIN_DIR, "test_game_data.db")
os.environ["GWEN_GAME_DB"] = TEST_DB
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import content as C, db
from data.plugins.dragonfall.main import Main


class FakeEvent:
    def __init__(self, group_id, qq_id, msg=""):
        self._g, self._q = group_id, qq_id
        self.message_str = msg

    def get_group_id(self): return self._g
    def get_sender_id(self): return self._q
    def get_message_str(self): return self.message_str
    def plain_result(self, text): return text


async def run(handler, ev):
    gen = handler(ev)
    results = []
    try:
        while True:
            results.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return results


G, Q = "g_play", "q_play"
M = Main(None)

HANDLERS = {
    "注册": "register", "找": "find_npc", "探索": "explore", "攻击": "attack",
    "角色": "profile", "属性": "attributes", "背包": "inventory", "技能": "skill",
    "地图": "map_view", "帮助": "help_cmd", "商店": "shop", "任务": "quest_view",
    "移动": "move",
}


def clean():
    db.init_db()
    conn = sqlite3.connect(db.DB_PATH)
    try:
        for t in ("players", "player_groups", "inventory", "quests", "battle_state",
                  "achievements", "stats", "feedback", "bestiary", "professions"):
            conn.execute(f"DELETE FROM {t}")
        conn.commit()
    finally:
        conn.close()


async def cmd(m, text, label=""):
    """模拟玩家输入：解析触发词 → 找 handler → 调用。"""
    ev = FakeEvent(G, Q, text)
    handler_name = None
    for kw, hn in HANDLERS.items():
        if text.startswith(kw):
            handler_name = hn
            break
    if not handler_name or not hasattr(m, handler_name):
        return f"[无匹配 handler] {text}"
    rs = await run(getattr(m, handler_name), ev)
    out = "\n".join(str(r) for r in rs if r)
    if label:
        print(f"\n{'='*66}\n▶ {label}：{text}\n{'='*66}")
    print(out)
    return out


async def main():
    clean()
    print("╔════════════════════════════════════════════╗")
    print("║  实玩体检：战士 从注册打到 10 级            ║")
    print("╚════════════════════════════════════════════╝")

    # 1. 注册
    await cmd(M, "注册 战士 阿烬 人类", "注册")

    # 2. 找镇长接任务
    await cmd(M, "找 镇长", "找镇长")

    # 2.5 移动去野外（城镇安全区探索不到敌人）
    await cmd(M, "移动 橡木林", "移动去橡木林")
    await cmd(M, "地图", "地图")

    # 3. 打怪升级循环：先橡木草地(Lv.1)练到3级 → 再橡木林(Lv.3)练到10级
    lv = 1
    guard = 0
    while lv < 10 and guard < 80:
        guard += 1
        p = db.get_player(G, Q)
        target_map = "oak_meadow" if lv < 3 else "oak_forest"
        if p["cur_map"] != target_map:
            await cmd(M, f"移动 {target_map}", "")
        # 探索遇怪（若已在战斗中则跳过）
        if not db.get_battle(G, Q):
            r = await cmd(M, "探索", "")
            if "附近没有敌人" in r:
                await cmd(M, f"移动 {target_map}", "")
                await cmd(M, "探索", "")
        # 连续攻击直到战斗结束
        round_guard = 0
        while db.get_battle(G, Q) and round_guard < 20:
            round_guard += 1
            await cmd(M, "攻击", "")
        p = db.get_player(G, Q)
        new_lv = p["level"]
        if new_lv != lv:
            lv = new_lv
            print(f"\n── 🎉 升级到 {lv} 级！──")
        if lv >= 10:
            break

    # 4. 10级后看各个面板
    await cmd(M, "角色", "10级角色面板")
    await cmd(M, "属性", "属性面板")
    await cmd(M, "背包", "背包")
    await cmd(M, "技能", "技能")
    await cmd(M, "地图", "地图")
    await cmd(M, "帮助", "帮助")


if __name__ == "__main__":
    asyncio.run(main())
