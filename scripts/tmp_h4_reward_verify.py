# -*- coding: utf-8 -*-
"""H4 隐藏链 P1(quests 侧) + P2 图纸奖励 reward_item 落地验证（只读，不写库）"""
import os, sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import content as C

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  [PASS] %s" % name)
    else:
        failed += 1
        print("  [FAIL] %s %s" % (name, detail))

SIDE = {q["id"]: q for q in C.SIDE_QUESTS}

print("== P2: 7 项图纸类 reward_item 落地验证 ==")
expect = {
    "s24": "裂鬃獠牙", "s25": "铁牙狼皮", "s27": "澜歌之泪",
    "s30": "雷鸣龙鳞", "s31": "烬核之心", "s33": "奥拉圣印", "s35": "暮影龙魂",
}
for qid, item in expect.items():
    q = SIDE.get(qid)
    check(f"{qid} 存在", q is not None)
    if not q:
        continue
    ri = q.get("reward_item")
    check(f"{qid} 已补 reward_item={item}", ri == item, f"实际 {ri!r}")
    if ri:
        mid = C.resolve("materials", ri)
        check(f"{qid} reward_item[{ri}] 在 MATERIALS 可解析", mid in C.MATERIALS, f"resolve={mid!r}")

# 全部 reward_item 一致性（含既有 2 项）
print("== 全量 SIDE_QUESTS reward_item 可解析 ==")
bad_ri = []
for q in C.SIDE_QUESTS:
    ri = q.get("reward_item")
    if ri:
        mid = C.resolve("materials", ri)
        if mid not in C.MATERIALS:
            bad_ri.append(f"{q['id']}->{ri}")
check("所有 reward_item 均在 MATERIALS", not bad_ri, ";".join(bad_ri))

print("== P1: s_hidden_library 任务数据完整性（quests 侧）==")
sl = SIDE.get("s_hidden_library")
check("s_hidden_library 存在", sl is not None)
if sl:
    check("giver=h_librarian", sl.get("giver") == "h_librarian", str(sl.get("giver")))
    check("map=dawn_cathedral 有效", sl.get("map") in C.MAP_BY_ID, sl.get("map"))
    check("objective.collect=泛黄书页 可解析", C.resolve("materials", sl["objective"]["collect"]) in C.MATERIALS)
    check("reward_item=星尘沙漏 可解析", C.resolve("materials", sl.get("reward_item")) in C.MATERIALS)
    check("有 exp/gold", sl.get("reward_exp") and sl.get("reward_gold"))
check("h_librarian 在 HIDDEN_NPCS", "h_librarian" in C.HIDDEN_NPCS)
if "h_librarian" in C.HIDDEN_NPCS:
    hb = C.HIDDEN_NPCS["h_librarian"]
    check("h_librarian.quest=s_hidden_library", hb.get("quest") == "s_hidden_library", str(hb.get("quest")))
    un = hb.get("unlock") or ""
    check("h_librarian.unlock 指向主线任务 q11_3（兄弟 agent 修复，本 agent 只读确认）",
          un.startswith("quest_done:q11_3"), un)
check("q11_3 在 MAIN_QUESTS", any(m["id"] == "q11_3" for m in C.MAIN_QUESTS))

print("== 数据完整性回归 ==")
ids = [q["id"] for q in C.SIDE_QUESTS]
check("SIDE_QUESTS id 无重复", len(ids) == len(set(ids)))
# 剔除项记录（设计奖励目标物品不存在 → 未补 reward_item）
print("-- 剔除并记录（设计奖励物品不存在于 MATERIALS，未补）--")
for qid, design in [("s3", "汉斯手工武器"), ("s9", "骑士团徽章"), ("s17", "随机符文"),
                    ("s20", "传说锻造材料"), ("s22", "历史学家笔记")]:
    q = SIDE.get(qid)
    has = q is not None and q.get("reward_item") is not None
    print(f"    {qid} 设计奖励「{design}」: reward_item={'已补(' + q['reward_item'] + ')' if has else '未补(目标物品不存在)'}")

print(f"\n结果: PASS {passed} / FAIL {failed}")
sys.exit(1 if failed else 0)
