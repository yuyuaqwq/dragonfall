# -*- coding: utf-8 -*-
"""v87 隐藏职业魔剑士 + H6/H7 隐藏区域：全链路验证

覆盖：
1. 职业数据：cls_spellblade 注册、hidden、evolve 三档
2. 技能表：8 技能全注册（60-90 级）、魔能机制 mech 字段
3. H6 失落图书馆 / H7 灰烬回廊：地图数据、Boss、NPC 挂载
4. 准入条件：HIDDEN_MAP_UNLOCK 物品型准入（泛黄书页×3 / 烬火信标）
5. 地图连接：crypt↔lost_library、cinder↔ember_corridor 双向
6. 隐藏 NPC：魔剑士残魂 + 试炼任务 s_spellblade_trial（unlock_class）
7. 任务道具：剑圣残页/泛黄书页/烬火信标/星尘沙漏/灰烬之核 材料注册
8. 转职链路：_evolve_spellblade 方法存在 + evolve 路由
9. 成就 ach_spellblade_unlock
10. 对话：残魂对话树存在
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))

def main():
    print("【v87 魔剑士 + H6/H7 隐藏区域】")

    # ===== 1. 职业数据 =====
    print("  · 职业数据")
    check("cls_spellblade 已注册", "cls_spellblade" in C.CLASSES)
    cls = C.CLASSES.get("cls_spellblade", {})
    check("魔剑士 hidden 标记", cls.get("hidden") is True)
    check("魔剑士 evolve 三档", len(cls.get("evolve", [])) == 3,
          f"实际 {cls.get('evolve')}")
    check("魔剑士描述含双修", "双修" in cls.get("desc", "") or "混合" in cls.get("desc", ""))

    # ===== 2. 技能表 =====
    print("  · 技能表（8 技能 60-90 级）")
    sk_table = C.PLAYER_SKILLS.get("cls_spellblade", {}).get("skills", {})
    check("PLAYER_SKILLS 魔剑士技能表 9 个", len(sk_table) == 9, f"实际 {len(sk_table)}")  # v106.2 +魔力贯穿
    want_names = ["魔能斩", "符文护体", "魔能涌动", "剑刃风暴",
                  "魔能爆发", "符文刻印", "双修精通", "星陨斩"]
    have_names = [s.get("name") for s in sk_table.values()]
    for n in want_names:
        check(f"技能 {n} 存在", n in have_names, f"实际 {have_names}")
    # 等级序列
    lvs = sorted(s["lv"] for s in sk_table.values())
    check("技能等级序列 60-90", lvs == [60, 64, 68, 72, 76, 80, 85, 88, 90], f"实际 {lvs}")  # v106.2 +魔力贯穿88
    # 魔能机制
    mechs = [s.get("mech") for s in sk_table.values() if s.get("mech")]
    for m in ["spellblade", "spellblade_surge", "spellblade_storm",
              "spellblade_burst", "spellblade_meteor"]:
        check(f"机制 {m} 挂载", m in mechs, f"实际 {mechs}")
    # 被动
    passives = [s.get("passive", {}).get("stat") for s in sk_table.values() if s.get("passive")]
    check("被动 符文刻印/双修精通", "spellblade_regen" in passives and "atk" in passives,
          f"实际 {passives}")
    # 混合伤害
    magic_add = [s.get("magic_add") for s in sk_table.values() if s.get("magic_add")]
    check("混合伤害 magic_add 至少 2 个", len(magic_add) >= 2, f"实际 {magic_add}")

    # ===== 3. H6/H7 地图 =====
    print("  · H6 失落图书馆 / H7 灰烬回廊")
    h6 = C.MAP_BY_ID.get("lost_library", {})
    check("H6 lost_library 存在", bool(h6), "地图缺失")
    check("H6 hidden=True", h6.get("hidden") is True)
    check("H6 等级 55", h6.get("lv") == 55, f"实际 {h6.get('lv')}")
    h6_sa = C.SUBAREAS.get("lost_library", [{}])[0]
    check("H6 Boss 守馆者", (h6_sa.get("boss") or [None])[0] == "b_lost_archivist",
          f"实际 {h6_sa.get('boss')}")
    check("H6 挂载魔剑士残魂 NPC", "npc_spellblade_ghost" in (h6_sa.get("npcs") or []),
          f"实际 {h6_sa.get('npcs')}")
    check("H6 怪物含图书馆守卫", any(m[1] == "图书馆守卫" for m in (h6_sa.get("monsters") or [])),
          f"实际 {[m[1] for m in h6_sa.get('monsters', [])]}")
    h7 = C.MAP_BY_ID.get("ember_corridor", {})
    check("H7 ember_corridor 存在", bool(h7), "地图缺失")
    check("H7 hidden=True", h7.get("hidden") is True)
    check("H7 等级 85", h7.get("lv") == 85, f"实际 {h7.get('lv')}")
    h7_sa = C.SUBAREAS.get("ember_corridor", [{}])[0]
    check("H7 Boss 烬火领主", (h7_sa.get("boss") or [None])[0] == "b_ember_lord",
          f"实际 {h7_sa.get('boss')}")

    # ===== 4. 准入条件（物品型） =====
    print("  · 准入条件")
    u6 = C.HIDDEN_MAP_UNLOCK.get("lost_library", {})
    check("H6 准入=泛黄书页×3", u6.get("item", {}).get("泛黄书页") == 3,
          f"实际 {u6}")
    u7 = C.HIDDEN_MAP_UNLOCK.get("ember_corridor", {})
    check("H7 准入=烬火信标×1", u7.get("item", {}).get("烬火信标") == 1,
          f"实际 {u7}")

    # ===== 5. 地图连接（双向） =====
    print("  · 地图连接")
    conn = C.MAP_CONNECTIONS
    check("secret_crypt → lost_library", "lost_library" in conn.get("secret_crypt", []),
          f"实际 {conn.get('secret_crypt')}")
    check("lost_library → secret_crypt", "secret_crypt" in conn.get("lost_library", []),
          f"实际 {conn.get('lost_library')}")
    check("cinder_mountain → ember_corridor", "ember_corridor" in conn.get("cinder_mountain", []),
          f"实际 {conn.get('cinder_mountain')}")
    check("ember_corridor → cinder_mountain", "cinder_mountain" in conn.get("ember_corridor", []),
          f"实际 {conn.get('ember_corridor')}")

    # ===== 6. NPC + 试炼任务 =====
    print("  · NPC 与试炼任务")
    check("npc_spellblade_ghost 存在", "npc_spellblade_ghost" in C.HIDDEN_NPCS
          or "npc_spellblade_ghost" in C.NPCS, "NPC 缺失")
    nid = "npc_spellblade_ghost"
    npc = C.HIDDEN_NPCS.get(nid, C.NPCS.get(nid, {}))
    check("残魂 quest=s_spellblade_trial", npc.get("quest") == "s_spellblade_trial",
          f"实际 {npc.get('quest')}")
    qids = [q["id"] for q in C.SIDE_QUESTS]
    check("s_spellblade_trial 存在", "s_spellblade_trial" in qids)
    qt = next((q for q in C.SIDE_QUESTS if q["id"] == "s_spellblade_trial"), None)
    check("试炼 unlock_class=cls_spellblade", qt and qt.get("unlock_class") == "cls_spellblade",
          f"实际 {qt.get('unlock_class') if qt else None}")
    check("试炼目标 图书馆守卫×3", qt and qt.get("objective", {}).get("kill") == "图书馆守卫"
          and qt.get("objective", {}).get("count") == 3, f"实际 {qt.get('objective') if qt else None}")
    check("试炼收集 剑圣残页×2", qt and qt.get("objective", {}).get("collect") == "剑圣残页"
          and qt.get("objective", {}).get("collect_count") == 2,
          f"实际 {qt.get('objective') if qt else None}")

    # ===== 7. 任务道具 =====
    print("  · 任务道具")
    for n in ["剑圣残页", "泛黄书页", "烬火信标", "星尘沙漏", "灰烬之核"]:
        mid = C.resolve("materials", n)
        check(f"材料 {n} 已注册", mid in C.MATERIALS, f"resolve={mid}")

    # ===== 8. 转职链路（v108 职业树：统一 _evolve_hidden_generic 路由） =====
    print("  · 转职链路")
    from data.plugins.dragonfall.main import Main
    inst = Main.__new__(Main)
    check("_evolve_hidden_generic 方法存在", hasattr(inst, "_evolve_hidden_generic"))
    check("_hidden_class_routes 方法存在", hasattr(inst, "_hidden_class_routes"))
    # 魔剑士档位全名（60/75/90）入路由表
    routes = inst._hidden_class_routes()
    check("路由表含 魔剑士/魔剑宗师/剑圣",
          "魔剑士" in routes and "魔剑宗师" in routes and "剑圣" in routes,
          f"缺: {[n for n in ['魔剑士', '魔剑宗师', '剑圣'] if n not in routes]}")
    check("魔剑士档位路由正确", routes.get("魔剑士") == ("cls_spellblade", 1)
          and routes.get("魔剑宗师") == ("cls_spellblade", 2)
          and routes.get("剑圣") == ("cls_spellblade", 3), str(routes.get("魔剑士")))
    # 特色档位门槛 60/75/90
    tlv = inst._hidden_tier_levels("cls_spellblade")
    check("魔剑士档位门槛 60/75/90", tlv == {1: 60, 2: 75, 3: 90}, str(tlv))
    # evolve 路由：检查 player.py 源码里 转职 分发含 _hidden_class_routes
    import inspect
    try:
        src = inspect.getsource(type(inst).evolve) if hasattr(inst, "evolve") else ""
        routed = "_hidden_class_routes" in src and "_evolve_hidden_generic" in src
        check("evolve 路由含魔剑士(统一路由)", routed)
    except Exception:
        check("evolve 路由含魔剑士(统一路由)", False, "无法检查源码")

    # ===== 9. 成就 =====
    print("  · 成就")
    aid = [a["id"] for a in C.ACHIEVEMENTS]
    check("ach_spellblade_unlock 存在", "ach_spellblade_unlock" in aid)

    # ===== 10. 对话树 =====
    print("  · 对话树")
    from data.plugins.dragonfall.game.data.dialogues import DIALOGUES
    check("残魂对话存在", "npc_spellblade_ghost" in DIALOGUES,
          f"实际 key 数 {len(DIALOGUES)}")

    # ===== 11. 魔能战斗支持 =====
    print("  · 魔能战斗支持")
    try:
        from data.plugins.dragonfall.game import battle
        src_txt = inspect.getsource(battle)
        has_impl = "spellblade" in src_txt
        check("battle.py 含 spellblade 处理", has_impl)
    except Exception as e:
        check("battle.py 含 spellblade 处理", False, str(e))

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
