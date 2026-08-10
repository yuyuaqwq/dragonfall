# -*- coding: utf-8 -*-
"""v87 隐藏线深化：隐藏怪物 / POI 探索点 / 探索彩蛋扩充 / 常规事件扩容

覆盖：
1. 数据完整性：HIDDEN_MONSTERS 6 种、POIS 7 种、SUBAREA_POIS 子区域 ID 全有效、新材料注册
2. 隐藏怪条件匹配：森林/水域/遗迹/夜间/任意
3. POI 触发：roll_poi 概率、子区域挂载
4. 探索彩蛋：新彩蛋 old_map/gold_slime 可触发
5. 常规事件扩容：12 种
"""
import sys, os, random
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
    print("【v87 隐藏线深化】")

    # ===== 1. 数据完整性 =====
    print("  · 数据完整性")
    check("HIDDEN_MONSTERS 25 种", len(C.HIDDEN_MONSTERS) == 25,
          f"实际 {len(C.HIDDEN_MONSTERS)}")
    check("POIS 10 种（含 v87.9 风景）", len(C.POIS) == 10, f"实际 {len(C.POIS)}")
    check("PROPS 55 种", len(C.PROPS) == 55, f"实际 {len(C.PROPS)}")
    check("SUBAREA_POIS 挂载数 ≥25", len(C.SUBAREA_POIS) >= 25,
          f"实际 {len(C.SUBAREA_POIS)}")
    # 子区域 ID 全有效
    bad = []
    for k in C.SUBAREA_POIS:
        mid, sid = k.split(":")
        if mid not in C.MAP_BY_ID:
            bad.append(k + " 地图不存在"); continue
        sids = [s["id"] for s in C.MAP_BY_ID[mid].get("subareas", [])]
        if sid not in sids:
            bad.append(k + " 子区域不存在")
    check("SUBAREA_POIS 子区域 ID 全有效", not bad, "；".join(bad))
    # 新材料
    for n in ["琥珀精华", "白鹿角", "荧光鳞", "符文碎片", "暗影精华", "幸运符"]:
        mid = C.resolve("materials", n)
        check(f"材料 {n} 已注册", mid in C.MATERIALS)
    # 隐藏怪技能 ID 有效
    from data.plugins.dragonfall.game.data import monsters
    sks = monsters.MONSTER_SKILLS
    bad_sk = []
    for hdef in C.HIDDEN_MONSTERS.values():
        for sk in hdef.get("skills", []):
            if sk not in sks:
                bad_sk.append(f"{hdef['name']}->{sk}")
    check("隐藏怪技能 ID 全有效", not bad_sk, "；".join(bad_sk))

    # ===== 2. 隐藏怪条件匹配 =====
    print("  · 隐藏怪条件匹配（用 Main._roll_hidden_monster 需实例，这里直接验证 cond 分类函数逻辑）")
    # 验证 build_monster 能构造隐藏怪
    import uuid
    test_def = ("e_gold_slime", "黄金史莱姆", "elite", 5, ["ms_du_ya"], ["琥珀精华"])
    m = C.build_monster(test_def, {"id": "oak_plain", "name": "橡木平原", "lv": 2})
    check("隐藏怪 build_monster 成功", m["name"] == "黄金史莱姆" and m["is_elite"])
    check("隐藏怪等级 = 地图等级+偏移", m["lv"] == 5, f"实际 {m['lv']}")

    # ===== 3. POI 触发 =====
    print("  · POI 触发")
    random.seed(1)
    hit = C.roll_poi("g", "q", "oak_town", "oak_town_1", chance=1.0)
    check("roll_poi 必中返回 POI", hit is not None and hit[0] in C.POIS)
    random.seed(2)
    miss = C.roll_poi("g", "q", "oak_town", "oak_town_1", chance=0.0)
    check("roll_poi 0% 概率返回 None", miss is None)
    nopoi = C.roll_poi("g", "q", "oak_town", "oak_town_2", chance=1.0)
    check("无 POI 子区域返回 None", nopoi is None)

    # ===== 4. 探索彩蛋扩充 =====
    print("  · 探索彩蛋扩充")
    from data.plugins.dragonfall.game.data.events import EXPLORE_EGG_EVENTS, EXPLORE_EVENTS
    egg_ids = [e["id"] for e in EXPLORE_EGG_EVENTS]
    # v97.6 扩容 5→30（区域 15 + 全局 10）
    check("彩蛋事件 30 种（含 old_map/gold_slime + v97.6 新 25）",
          len(egg_ids) == 30 and "old_map" in egg_ids and "gold_slime" in egg_ids
          and "egg_oak_whisper" in egg_ids and "egg_twin_moon" in egg_ids,
          f"实际 {len(egg_ids)}")
    ev_ids = [e["id"] for e in EXPLORE_EVENTS]
    # v97.4 扩容 12→30（新 18：firefly/old_well/windmill/hunter_hut/beehive/floating_bridge/
    # old_tree_hollow/stone_tablet/cart_wreck/night_owl/spider_web/frost_flower/old_boot/
    # mushroom_ring/echo_cave/campfire_ashes/drifting_bottle/abandoned_minecart）
    check("常规事件 30 种（含 lost_camp/meteor/animal/rain + v97.4 新 18）",
          len(ev_ids) == 30
          and all(x in ev_ids for x in ("lost_camp", "meteor", "animal", "rain"))
          and all(x in ev_ids for x in ("firefly", "old_well", "windmill", "hunter_hut", "beehive",
                                        "floating_bridge", "old_tree_hollow", "stone_tablet",
                                        "cart_wreck", "night_owl", "spider_web", "frost_flower",
                                        "old_boot", "mushroom_ring", "echo_cave",
                                        "campfire_ashes", "drifting_bottle", "abandoned_minecart")),
          f"实际 {len(ev_ids)}")

    # ===== 5. 探索点显示（_map_scene 包含 POI）=====
    print("  · 探索点显示")
    from data.plugins.dragonfall.main import Main
    inst = Main.__new__(Main)
    player = {"qq_id": "q", "cur_subarea": "oak_town_1"}
    cur_map = C.MAP_BY_ID["oak_town"]
    lines = inst._map_scene(cur_map, player)
    poi_lines = [l for l in lines if "探索" in l and "发现" in l]
    check("地图面板显示 POI（冒险者广场）", len(poi_lines) >= 1, f"实际 {poi_lines}")

    # ===== 6. 隐藏 NPC +3 =====
    print("  · 隐藏 NPC")
    check("HIDDEN_NPCS 数 ≥13（原 10 + 新 3）", len(C.HIDDEN_NPCS) >= 13,
          f"实际 {len(C.HIDDEN_NPCS)}")
    for nid in ("h_gravekeeper", "h_librarian", "h_night_trader"):
        check(f"隐藏 NPC {nid} 存在", nid in C.HIDDEN_NPCS)
    check("老守墓人 quest=s_hidden_ember",
          C.HIDDEN_NPCS.get("h_gravekeeper", {}).get("quest") == "s_hidden_ember")
    check("图书管理员 quest=s_hidden_library",
          C.HIDDEN_NPCS.get("h_librarian", {}).get("quest") == "s_hidden_library")

    # ===== 7. 隐藏任务链 =====
    print("  · 隐藏任务链")
    qids = [q["id"] for q in C.SIDE_QUESTS]
    check("s_hidden_ember 存在", "s_hidden_ember" in qids)
    check("s_hidden_library 存在", "s_hidden_library" in qids)
    qe = next((q for q in C.SIDE_QUESTS if q["id"] == "s_hidden_ember"), None)
    check("H3 reward_item=烬火信标", qe and qe.get("reward_item") == "烬火信标")
    ql = next((q for q in C.SIDE_QUESTS if q["id"] == "s_hidden_library"), None)
    check("H4 reward_item=星尘沙漏", ql and ql.get("reward_item") == "星尘沙漏")

    # ===== 8. 任务道具注册 =====
    print("  · 任务道具")
    for n in ["烬火余烬", "泛黄书页", "烬火信标", "星尘沙漏"]:
        mid = C.resolve("materials", n)
        check(f"任务道具 {n} 在 MATERIALS", mid in C.MATERIALS)

    # ===== 9. 每日运势（签到逻辑：直接验证 event_state 写入函数路径）=====
    print("  · 每日运势")
    import datetime
    db.set_event_state(f"daily_fortune_test", '{"date": "' + datetime.date.today().isoformat() + '", "fortune": "大吉"}')
    st = db.get_event_state("daily_fortune_test")
    check("运势 state 可写读", st is not None and "大吉" in st)

    # ===== 10. 隐藏装备/套装 =====
    print("  · 隐藏装备")
    check("EQUIP_ROSTER 112 件（+12 隐藏）", len(C.EQUIP_ROSTER) == 112, str(len(C.EQUIP_ROSTER)))
    for n in ["星尘法杖", "星尘长袍", "星尘之戒", "星尘坠饰", "星尘护腿",
              "灰烬长剑", "灰烬铠甲", "灰烬之盔", "灰烬之盾", "灰烬护腿", "灰烬战靴", "星陨之剑"]:
        check(f"隐藏装备 {n}", bool(C.EQUIP_ROSTER_BY_NAME.get(n)))
    eq = C.generate_roster_equip("eq_xing_chen_fa_zhang")
    check("星尘法杖生成成功", eq["name"] == "星尘法杖" and eq["quality"] == "purple")
    eq3 = C.generate_roster_equip("eq_starfall_sword")
    check("星陨之剑传奇效果", eq3.get("legendary") == "starfall")
    eq4 = C.generate_roster_equip("eq_hui_jin_kai_jia")
    check("灰烬铠甲专属效果", eq4.get("legendary") == "ember_ward")
    check("灰烬壁垒注册", "ember_ward" in C.LEGENDARY_EFFECTS)
    check("套装星尘套注册", "set_xing_chen_tao" in C.SETS)
    check("套装灰烬守卫注册", "set_hui_jin_shou_wei_tao" in C.SETS)

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
