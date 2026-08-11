# -*- coding: utf-8 -*-
"""对话树审计：扫描所有 NPC 的『陈旧台词』风险（v101.23c 镇长问题的同类检查）

对每个节点：
1. 台词是否提到具体任务剧情关键词（史莱姆/野猪/哥布林/麦田等）
2. 若有 → 检查：入口选项有没有 need 条件保护？节点有没有 texts 变体？
   两个都没有 = 陈旧台词风险（主线推进后 NPC 还在念旧任务）
"""
import sys, os
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from data.plugins.dragonfall.game import content as C  # noqa: E402

# 任务剧情关键词（台词里出现 = 绑定具体任务剧情）
KEYWORDS = [
    "史莱姆", "麦田", "野猪", "哥布林", "伤兵", "隧洞", "狼", "狼皮",
    "矿洞", "矿石", "草药", "毒蘑菇", "蜂蜜", "螃蟹", "鱼", "海",
    "酒杯", "喝酒", "陪老头子", "白鹿城", "铁匠铺", "行会",
]

def has_kw(text):
    return [k for k in KEYWORDS if k in (text or "")]

print("=" * 70)
print("一、所有『welcome/quest_talk/quest_done_talk』节点的台词绑定情况")
print("=" * 70)
for npc_id, dlg in C.DIALOGUES.items():
    nodes = dlg.get("nodes", {})
    start = dlg.get("start")
    for nid, node in nodes.items():
        # 只看通用型节点
        if nid not in ("welcome", "quest_talk", "quest_done_talk", "quest_status"):
            continue
        texts = node.get("texts") or []
        default = node.get("text", "")
        kws = has_kw(default)
        variants = []
        for tv in texts:
            variants.append((tv.get("need"), has_kw(tv.get("text", ""))))
        flag = "⚠️" if (kws and not texts) else ("✓" if texts else "·")
        print(f"{flag} {npc_id}.{nid} 默认台词关键词={kws} 变体数={len(texts)}")
        for need, vkws in variants:
            print(f"     变体 need={need} 关键词={vkws}")

print()
print("=" * 70)
print("二、全部节点：台词绑定任务剧情但『无变体 + 入口无 need』= 陈旧风险")
print("=" * 70)

risks = []
for npc_id, dlg in C.DIALOGUES.items():
    nodes = dlg.get("nodes", {})
    # 收集所有指向每个节点的入口（谁链接进来 + 有没有 need）
    entries = {}
    for nid, node in nodes.items():
        for opt in node.get("options", []):
            nxt = opt.get("next")
            if nxt and nxt != "__end__":
                entries.setdefault(nxt, []).append((nid, opt.get("need")))
    # start 节点本身是入口
    entries.setdefault(dlg.get("start"), []).append(("<start>", None))

    for nid, node in nodes.items():
        default = node.get("text", "")
        kws = has_kw(default)
        if not kws:
            continue
        has_variants = bool(node.get("texts"))
        entry_needs = entries.get(nid, [])
        # 入口全部无 need 且节点无变体 → 台词永远按默认念
        all_unprotected = all(need is None for _, need in entry_needs)
        if has_variants:
            continue  # 有变体 = 已处理
        risks.append({
            "npc": npc_id, "node": nid, "kws": kws,
            "entries": entry_needs, "unprotected": all_unprotected,
        })

for r in risks:
    ent = ", ".join(f"{e[0]}(need={e[1]})" for e in r["entries"])
    level = "🔴 高危" if r["unprotected"] else "🟡 低危(入口有条件,但台词本身不随主线变)"
    print(f"{level} {r['npc']}.{r['node']} 关键词={r['kws']}")
    print(f"        入口: {ent}")

print()
print(f"风险节点总数: {len(risks)}")
print("=" * 70)
print("三、选项文本绑定任务剧情但没有条件保护的（选项文字陈旧）")
print("=" * 70)
for npc_id, dlg in C.DIALOGUES.items():
    nodes = dlg.get("nodes", {})
    for nid, node in nodes.items():
        for opt in node.get("options", []):
            kws = has_kw(opt.get("text", ""))
            if kws and not opt.get("need"):
                print(f"⚠️ {npc_id}.{nid} 选项『{opt['text']}』→ {opt.get('next')} 无 need")
