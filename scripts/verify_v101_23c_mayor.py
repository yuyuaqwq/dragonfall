# -*- coding: utf-8 -*-
"""v101.23c 验证：q1_1 完成后镇长不再显示史莱姆话题（选项隐藏 + dogs 变体）"""
import sys, os, asyncio

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from data.plugins.dragonfall.game import content as C, db, engine as E  # noqa: E402,F401
from data.plugins.dragonfall.game.core.dialogue import get_dialogue, visible_options, node_text  # noqa: E402

async def main():
    dlg = get_dialogue("npc_mayor")
    assert dlg, "镇长对话树缺失"

    class P:
        level = 30
    p = P()

    def ctx_for(quests_dict, flags=None):
        return {
            "player": p,
            "quests": quests_dict,
            "flags": flags or {},
            "npc_id": "npc_mayor",
        }

    # ---- 场景A：q1_1 未完成（新手）→ 史莱姆话题应该还在 ----
    qa = {"main_quest": "q1_1", "main_status": "active", "completed_main": []}
    opts_a = [o["text"] for o in visible_options(dlg, dlg["nodes"]["welcome"], ctx_for(qa))]
    print("【A】q1_1 未完成: 选项 =", opts_a)
    assert any("史莱姆" in t for t in opts_a), "A: 史莱姆话题应该可见！"
    assert node_text(dlg["nodes"]["dogs"], ctx_for(qa)) == dlg["nodes"]["dogs"]["text"], "A: dogs 默认台词"
    print("A ✅ 新手阶段：史莱姆话题可见，dogs 是原台词\n")

    # ---- 场景B：q1_1 已完成（鱼鱼现状）→ 史莱姆话题应该隐藏 ----
    qb = {"main_quest": "q1_2", "main_status": "active", "completed_main": ["q1_1"]}
    ctx_b = ctx_for(qb)
    opts_b = [o["text"] for o in visible_options(dlg, dlg["nodes"]["welcome"], ctx_b)]
    print("【B】q1_1 已完成: 选项 =", opts_b)
    assert not any("史莱姆" in t for t in opts_b), f"B: 史莱姆话题仍可见！{opts_b}"
    assert "镇长，镇子最近还好吗？" in opts_b, "B: 近况话题应该在"
    print("B ✅ 史莱姆选项已隐藏，近况选项保留\n")

    # ---- 场景C：dogs 节点台词变体（兜底）----
    txt_c = node_text(dlg["nodes"]["dogs"], ctx_b)
    print("【C】q1_1 完成后 dogs 台词 =", txt_c[:40], "...")
    assert "了结" in txt_c or "清净" in txt_c, f"C: dogs 变体台词未生效！{txt_c}"
    print("C ✅ dogs 变体台词生效\n")

    # ---- 场景D：town 节点入口也隐藏 ----
    opts_d = [o["text"] for o in visible_options(dlg, dlg["nodes"]["town"], ctx_b)]
    print("【D】town 节点选项 =", opts_d)
    assert not any("史莱姆" in t for t in opts_d), f"D: town 里史莱姆话题仍可见！{opts_d}"
    print("D ✅ town 入口也已隐藏")

    print("\n🎉 全部通过！")

asyncio.run(main())
