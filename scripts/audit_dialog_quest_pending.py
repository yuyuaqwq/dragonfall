# -*- coding: utf-8 -*-
"""审计：有主线任务的 NPC 对话树是否都有 quest_pending 接取入口"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r"C:\Users\yuyu\qqbot")
from data.plugins.dragonfall.game import content as C

DIALOGUES = C.DIALOGUES
MAIN_QUESTS = C.MAIN_QUESTS

# 主线 giver → 任务列表
givers = {}
for mq in MAIN_QUESTS:
    givers.setdefault(mq["giver"], []).append(mq["id"])

# 每个对话树是否有 quest_pending 接取选项（任一节点）
missing = []
for giver, qids in givers.items():
    dlg = DIALOGUES.get(giver)
    if not dlg:
        missing.append((giver, qids, "无对话树"))
        continue
    has_pending = False
    for node in dlg.get("nodes", {}).values():
        for opt in node.get("options", []):
            need = opt.get("need") or {}
            if "quest_pending" in need:
                has_pending = True
                break
        if has_pending:
            break
    if not has_pending:
        missing.append((giver, qids, "对话树无 quest_pending 接取选项"))

print(f"主线 giver 数: {len(givers)}")
if missing:
    print("❌ 缺接取入口:")
    for g, qs, reason in missing:
        print(f"  {g} {qs} → {reason}")
else:
    print("✅ 全部主线 giver 都有 quest_pending 接取入口")
