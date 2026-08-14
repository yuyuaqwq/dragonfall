# -*- coding: utf-8 -*-
"""v113 龙裔线（原 v87 魔剑士/spellblade，v113 只留龙血流派）+ H6/H7 隐藏区域：
全链路验证

v113 收敛：魔剑士（魔能物魔混合）/圣殿骑士（护盾格挡）流派已删，cls_dragon_oath
只留「龙血」流派（真伤+灼烧）。魔剑士相关技能（魔能斩/星陨斩等）已删，但
battle_mech 里的 spellblade 机制注册仍保留（无技能引用，退化防御性代码）。

覆盖：
1. 职业数据：cls_dragon_oath 注册、hidden、evolve 三档；单流派=龙血战士
2. 龙血流派技能表：龙息/龙鳞/龙威/龙焰吐息 全注册、真伤/灼烧 mech
3. H6 失落图书馆 / H7 灰烬回廊：地图数据、Boss、NPC 挂载
4. 准入条件：HIDDEN_MAP_UNLOCK 物品型准入（泛黄书页×3 / 烬火信标）
5. 地图连接：crypt↔lost_library、cinder↔ember_corridor 双向
6. 隐藏 NPC：残魂（lore 保留，试炼并入龙裔线）
7. 任务道具：咒刃残页/泛黄书页/烬火信标/星尘沙漏/灰烬之核 材料注册
8. 转职链路：统一 _evolve_hidden_generic 路由（龙血战士 → 龙裔线 T1 龙血流）
9. 成就 ach_dragon_unlock
10. 对话：残魂对话树存在
11. spellblade 机制注册仍保留（无技能引用，退化为防御性机制；仅验证不报错）
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
    print("【v113 龙裔线·龙血流 + H6/H7 隐藏区域】")

    # ===== 1. 职业数据 =====
    print("  · 职业数据")
    check("cls_dragon_oath 已注册", "cls_dragon_oath" in C.CLASSES)
    cls = C.CLASSES.get("cls_dragon_oath", {})
    check("龙裔誓约 hidden 标记", cls.get("hidden") is True)
    check("龙裔誓约 evolve 三档", len(cls.get("evolve", [])) == 3,
          f"实际 {cls.get('evolve')}")
    check("龙裔誓约单流派（龙血战士）", cls.get("evolve_branches", {}).get(1) == ["龙血战士"]
          and cls.get("evolve_branches", {}).get(2) == ["龙裔斗士"]
          and cls.get("evolve_branches", {}).get(3) == ["龙魂战将"],
          f"实际 {cls.get('evolve_branches')}")
    check("职业描述含誓约", "誓约" in cls.get("desc", "") or "龙" in cls.get("desc", ""))

    # ===== 2. 技能表（龙血流派） =====
    print("  · 技能表（龙血流派）")
    br = C.BRANCH_SKILLS.get("cls_dragon_oath", {}).get("branches", {})
    sk = {}
    for _t, _bn in ((1, "龙血战士"), (2, "龙裔斗士"), (3, "龙魂战将")):
        sk.update(br.get(_t, {}).get(_bn, {}))
    check("龙血流技能注册", "龙息" in sk and "龙鳞" in sk and "龙威" in sk and "龙焰吐息" in sk,
          f"实际 {list(sk)}")
    # 真伤 / 灼烧机制
    found_burn = [s.get("mech") for s in sk.values() if s.get("mech") == "burn"]
    check("龙息/龙焰吐息挂 burn 灼烧", len(found_burn) >= 2, f"实际 {found_burn}")
    check("技能纯真伤（龙息/龙焰吐息）", any(s.get("kind") == "真伤" for s in sk.values()),
          str([(n, s.get("kind")) for n, s in sk.items()]))
    # 已删流派技能不再存在于技能表（魔能斩/星陨斩/圣御之盾等）
    gone = [n for n in ("魔能斩", "符文护体", "魔能涌动", "剑刃风暴", "魔能爆发",
                        "符文刻印", "双修精通", "星陨斩", "圣御之盾", "圣光审判")
            if n in sk]
    check("魔剑士/圣殿流派技能已删", not gone, str(gone))

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

    # ===== 6. NPC + 试炼任务（v113：试炼并入龙裔线，残魂保留 lore） =====
    print("  · NPC 与试炼任务")
    check("npc_spellblade_ghost 存在", "npc_spellblade_ghost" in C.HIDDEN_NPCS
          or "npc_spellblade_ghost" in C.NPCS, "NPC 缺失")
    nid = "npc_spellblade_ghost"
    npc = C.HIDDEN_NPCS.get(nid, C.NPCS.get(nid, {}))
    check("残魂无死 quest 引用（v113 并入龙裔线）", npc.get("quest") is None,
          f"实际 {npc.get('quest')}")
    check("残魂保留 lore", "lore" in (npc.get("funcs") or []), f"实际 {npc.get('funcs')}")
    qids = [q["id"] for q in C.SIDE_QUESTS]
    check("旧 s_spellblade_trial 已删除", "s_spellblade_trial" not in qids, "应删除")
    qt = next((q for q in C.SIDE_QUESTS if q["id"] == "s_dragon_warrior_trial"), None)
    check("龙裔线试炼 unlock_class=cls_dragon_oath", qt and qt.get("unlock_class") == "cls_dragon_oath",
          f"实际 {qt.get('unlock_class') if qt else None}")

    # ===== 7. 任务道具 =====
    print("  · 任务道具")
    for n in ["咒刃残页", "泛黄书页", "烬火信标", "星尘沙漏", "灰烬之核"]:
        mid = C.resolve("materials", n)
        check(f"材料 {n} 已注册", mid in C.MATERIALS, f"resolve={mid}")

    # ===== 8. 转职链路（v113：龙血战士 = 龙裔线 T1 龙血流） =====
    print("  · 转职链路")
    from data.plugins.dragonfall.main import Main
    inst = Main.__new__(Main)
    check("_evolve_hidden_generic 方法存在", hasattr(inst, "_evolve_hidden_generic"))
    check("_hidden_class_routes 方法存在", hasattr(inst, "_hidden_class_routes"))
    routes = inst._hidden_class_routes()
    check("路由表含 龙血战士/龙裔斗士/龙魂战将",
          "龙血战士" in routes and "龙裔斗士" in routes and "龙魂战将" in routes,
          f"缺: {[n for n in ['龙血战士', '龙裔斗士', '龙魂战将'] if n not in routes]}")
    check("龙血战士档位路由正确(龙裔线·龙血流)", routes.get("龙血战士") == ("cls_dragon_oath", 1, 1)
          and routes.get("龙裔斗士") == ("cls_dragon_oath", 2, 1)
          and routes.get("龙魂战将") == ("cls_dragon_oath", 3, 1), str(routes.get("龙血战士")))
    # 已删流派（魔剑士/符文剑士/咒刃君王/圣殿骑士等）不路由
    gone_route = [n for n in ("魔剑士", "符文剑士", "咒刃君王", "圣殿骑士", "圣光堡垒")
                  if n in routes]
    check("已删流派不路由", not gone_route, str(gone_route))
    # v113 统一档位门槛 40/60/90
    tlv = inst._hidden_tier_levels("cls_dragon_oath")
    check("龙裔线档位门槛 40/60/90", tlv == {1: 40, 2: 60, 3: 90}, str(tlv))
    # v113 种族限制：龙裔誓约 src_race=dragonborn
    check("龙裔线 src_race=dragonborn", C.CLASSES.get("cls_dragon_oath", {}).get("src_race") == "dragonborn",
          str(C.CLASSES.get("cls_dragon_oath", {}).get("src_race")))
    import inspect
    try:
        src = inspect.getsource(type(inst).evolve) if hasattr(inst, "evolve") else ""
        routed = "_hidden_class_routes" in src and "_evolve_hidden_generic" in src
        check("evolve 路由含统一路由", routed)
    except Exception:
        check("evolve 路由含统一路由", False, "无法检查源码")

    # ===== 9. 成就 =====
    print("  · 成就")
    aid = [a["id"] for a in C.ACHIEVEMENTS]
    check("ach_dragon_unlock 存在", "ach_dragon_unlock" in aid)
    check("旧 ach_spellblade_unlock 已删", "ach_spellblade_unlock" not in aid)

    # ===== 10. 对话树 =====
    print("  · 对话树")
    from data.plugins.dragonfall.game.data.dialogues import DIALOGUES
    check("残魂对话存在", "npc_spellblade_ghost" in DIALOGUES,
          f"实际 key 数 {len(DIALOGUES)}")

    # ===== 11. spellblade 机制注册仍保留（v113 无技能引用，退化防御性——仅验证不报错） =====
    print("  · spellblade 机制注册（防御性保留）")
    try:
        from data.plugins.dragonfall.game.core import battle_mech as BM
        has_spell = all(k in BM.MECH_EFFECTS for k in
                        ("spellblade", "spellblade_surge", "spellblade_storm",
                         "spellblade_burst", "spellblade_meteor"))
        check("spellblade 机制仍注册", has_spell)
        if has_spell:
            # 直接用机制函数验证消耗逻辑不报错（无技能名引用）
            from data.plugins.dragonfall.game import battle as BT
            b = BT.Battle("怪物", {"name": "T", "hp": 1000, "max_hp": 1000,
                                  "atk": 5, "def": 5, "spd": 3}, {},
                          {"class_name": "cls_dragon_oath"})
            p_mech = {"spellblade": 5}
            logs = []
            b._apply_mech_effect("spellblade_meteor", 0, p_mech, 100, logs, "spellblade_meteor")
            check("spellblade_meteor 满 5 层消耗不报错", p_mech["spellblade"] == 0, str(p_mech))
            b2 = BT.Battle("怪物", {"name": "T", "hp": 1000, "max_hp": 1000,
                                   "atk": 5, "def": 5, "spd": 3}, {},
                           {"class_name": "cls_dragon_oath"})
            pm2 = {}
            b2._apply_mech_effect("spellblade", 2, pm2, 100, [], "spellblade")
            check("spellblade 叠层不报错", pm2.get("spellblade", 0) == 2, str(pm2))
    except Exception as e:
        check("spellblade 机制注册", False, str(e))

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
