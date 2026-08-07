# -*- coding: utf-8 -*-
"""生成 game/data/subareas.py —— 子区域拆分数据（02 章 13 节）。

输入：maps.py 现有 MAPS（怪物/精英/Boss/NPC）+ 下方拆分表（策划案 13.2/13.3）。
输出：SUBAREAS = { map_id: [subarea_dict, ...] }，并注入 MAPS。
用法：python scripts/gen_subareas.py   （生成后由 _assembly.py 装配）
"""
import os, sys, json, copy

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
sys.path.insert(0, PLUGIN_DIR)

# ---------- 拆分表（策划案 13.2/13.3，硬编码权威数据） ----------
# 城镇：map_id -> [子区域名, ...]（顺序即默认落点顺序，第一个为广场/入口）
# v2 差异化命名：具体建筑名+方位词，禁止模板化（中心广场/中央大街/旅店街会审美疲劳）
TOWN_SPLIT = {
    "oak_town": ["冒险者广场", "老铁铁匠铺", "橡木桶旅店", "草药铺", "东街", "西巷", "镇口"],
    "white_deer": ["白鹿广场", "银盾大街", "金鹿旅馆", "铁匠街", "南市", "医师巷", "北门"],
    "ironharbor": ["港口广场", "冒险者公会", "铁锚旅店", "拍卖行", "东码头", "船坞", "货仓街", "贫民窟"],
    "silver_brook": ["银溪广场", "磨坊街", "河畔旅店", "集市", "民居巷"],
    "maple_village": ["村口", "枫叶小街", "枫叶旅店", "农田边"],
    "dawn_city": ["王都广场", "圣光大教堂", "皇家大街", "白鸽旅店", "拍卖行", "东市", "西市", "王宫前", "南门"],
    "ironshield_town": ["铁盾广场", "军械街", "老兵旅店", "集市", "兵营巷"],
    "moon_gate": ["月门广场", "银月旅店", "哨塔集市", "瞭望台"],
    "moon_court": ["王庭广场", "月辉大街", "月神圣殿", "林语旅店", "月市", "花园"],
    "star_song": ["星歌广场", "旅店街", "星光集市", "林间"],
    "frost_horn": ["堡垒广场", "寒铁大街", "霜角旅店", "集市", "兵营", "北门"],
    "anvil_fort": ["熔炉广场", "锻造街", "矮人旅店", "集市", "矿道口"],
    "cold_ridge": ["营地口", "主帐篷", "篝火旅店", "哨站"],
    "aurora_town": ["极光广场", "旅店街", "集市", "观星台"],
    "dragon_pass": ["山口广场", "龙脊旅店", "集市", "瞭望台"],
    "dragon_kin": ["聚落入口", "龙裔广场", "祭坛区", "旅店"],
    "jade_port": ["港口广场", "翡翠大街", "集市", "东码头", "船坞", "珍珠旅店"],
    "shell_town": ["镇口", "贝壳集市", "码头", "旅店"],
    "nameless_harbor": ["港口广场", "集市", "码头区", "旅店街", "灯塔下"],
    "pearl_city": ["珍珠广场", "中央大街", "集市", "拍卖行", "码头区", "旅店街"],
    "deep_tunnel": ["隧道口", "中央大厅", "集市", "营地区"],
    "under_market": ["集市广场", "拍卖区", "旅店", "矿工区", "暗巷"],
    "ember_camp": ["营地口", "中央区", "旅店", "熔炉边"],
    "wind_city": ["浮空广场", "中央大街", "旅店街", "集市", "观景台"],
}

# 野外：map_id -> [(子区域名, 等级), ...]（顺序即由浅入深）
WILD_SPLIT = {
    "oak_meadow": [("草地边缘", 1), ("草地深处", 2), ("溪边草地", 3)],
    "oak_forest": [("林间入口", 3), ("橡木林深处", 5), ("溪谷", 6)],
    "emerald_forest": [("林间小径", 8), ("森林深处", 11), ("古树空地", 14)],
    "misty_swamp": [("沼泽边缘", 12), ("芦苇荡", 15), ("沼泽深处", 18)],
    "hill_mine": [("矿洞入口", 18), ("矿道", 21), ("矿洞深处", 24)],
    "harbor_docks": [("码头栈桥", 20), ("货仓区", 23), ("海堤", 26)],
    "silver_valley": [("谷地入口", 10), ("溪谷", 13), ("谷地深处", 16)],
    "windmill_plain": [("原野边缘", 14), ("风车田", 17), ("原野深处", 20)],
    "rockfall_gorge": [("峡谷口", 4), ("峡谷栈道", 6), ("峡谷深处", 8)],
    "boar_ridge": [("山脚", 6), ("山腰", 8), ("野猪王巢", 10)],
    "dawn_cathedral": [("圣堂前庭", 28), ("回廊", 31), ("圣堂地窟", 35)],
    "gold_plain": [("平原边缘", 30), ("麦田区", 35), ("平原深处", 40)],
    "white_abbey": [("修道院门口", 32), ("庭院", 35), ("地窖", 38)],
    "border_castle": [("堡外荒野", 40), ("城墙下", 45), ("堡内广场", 50)],
    "silver_river": [("河岸", 38), ("渡口", 43), ("河心洲", 48)],
    "knight_yard": [("训练场入口", 26), ("靶场", 30), ("魔像试炼区", 34)],
    "king_road": [("古道口", 33), ("古道中段", 37), ("王陵前", 42)],
    "ironshield_hills": [("丘陵脚", 28), ("丘陵中", 32), ("丘陵顶", 36)],
    "old_battlefield": [("遗址边缘", 32), ("战壕区", 36), ("遗址核心", 40)],
    "silverwood": [("林海边缘", 46), ("林海深处", 51), ("月辉空地", 56)],
    "starlake": [("湖畔", 50), ("湖岸小径", 55), ("湖心岛", 60)],
    "elven_ruins": [("废墟入口", 58), ("残垣区", 62), ("遗迹核心", 66)],
    "ancient_tree": [("隘口下", 62), ("树道", 66), ("古树之巅", 70)],
    "moon_glade": [("林缘", 52), ("月光空地", 57), ("林深处", 62)],
    "emerald_valley": [("谷口", 47), ("谷中", 51), ("翠谷深处", 55)],
    "windvale": [("谷口", 50), ("风语草原", 54), ("谷底", 58)],
    "moonshadow_wood": [("林缘", 54), ("影径", 58), ("月影深处", 62)],
    "frost_field": [("霜原边缘", 62), ("雪地", 67), ("霜原深处", 72)],
    "forge_valley": [("谷口", 66), ("熔岩河畔", 71), ("熔炉心", 76)],
    "black_forest": [("林缘", 72), ("腐林", 77), ("森林深处", 82)],
    "cinder_mountain": [("山脚", 78), ("山腰", 83), ("火山口", 88)],
    "frost_fang": [("谷口", 63), ("冰径", 67), ("冰牙深处", 71)],
    "winter_lake": [("湖畔", 70), ("冰面", 75), ("湖心", 80)],
    "permafrost_field": [("冰原边缘", 68), ("冰原中", 73), ("冰原深处", 78)],
    "frostwhisper_canyon": [("峡谷口", 72), ("峡谷道", 77), ("霜语尽头", 82)],
    "dragon_ridge": [("山脚", 82), ("山道", 86), ("龙脊之巅", 90)],
    "dragon_roost": [("巢外峭壁", 88), ("龙巢口", 92), ("巢穴深处", 96)],
    "ancient_battlefield": [("战场边缘", 85), ("战场中", 90), ("战场核心", 95)],
    "bone_wild": [("荒野边缘", 84), ("骨堆区", 88), ("荒野深处", 92)],
    "storm_cliff": [("崖脚", 86), ("崖道", 90), ("风暴崖顶", 94)],
    "redridge_plateau": [("高原边缘", 84), ("赤脊中", 88), ("高原深处", 92)],
    "dragonsfall_valley": [("谷口", 88), ("龙骸区", 92), ("谷底", 96)],
    "coral_reef": [("礁滩", 36), ("珊瑚丛", 40), ("礁群深处", 44)],
    "sunset_isle": [("岛滩", 42), ("岛林", 47), ("岛心", 52)],
    "storm_strait": [("海峡口", 48), ("急流区", 53), ("海峡深处", 58)],
    "mermaid_bay": [("湾口", 45), ("珊瑚湾", 50), ("海妖巢", 55)],
    "mist_trench": [("海沟口", 56), ("迷雾区", 60), ("海沟深处", 64)],
    "whale_domain": [("海域边缘", 60), ("龙鲸路", 64), ("海域深处", 68)],
    "shipwreck_graveyard": [("墓地边缘", 63), ("沉船区", 67), ("墓地核心", 71)],
    "storm_sea": [("海缘", 66), ("风暴区", 70), ("海眼", 74)],
    "fungus_forest": [("菌林边缘", 66), ("孢子区", 71), ("菌林深处", 76)],
    "deep_lake": [("湖岸", 72), ("湖桥", 77), ("湖底", 82)],
    "molten_abyss": [("深渊口", 78), ("熔岩道", 83), ("深渊深处", 88)],
    "lava_bed": [("河床口", 86), ("熔岩滩", 90), ("河床深处", 94)],
    "abyss_altar": [("祭坛外围", 88), ("祭坛廊道", 92), ("祭坛核心", 96)],
    "cloud_sea": [("云海边", 86), ("云岛", 90), ("云海深处", 94)],
    "storm_plateau": [("高原边缘", 90), ("雷区", 94), ("高原核心", 98)],
    "rainbow_cloud": [("云谷口", 90), ("彩虹桥", 93), ("云谷深处", 96)],
    "starlight_terrace": [("台缘", 92), ("星辉路", 95), ("星辉之巅", 98)],
}

# 城镇子区域 -> 功能关键词（按子区域名分配 funcs/shop/healer）
# v2：优先精确建筑名，再方位词兜底
TOWN_FUNC_RULES = [
    ("铁匠铺", ["shop", "craft"], True, False),   # 具体铁匠铺
    ("锻造街", ["shop", "craft"], True, False),   # 矮人锻造街
    ("军械街", ["shop", "craft"], True, False),
    ("铁匠街", ["shop", "craft"], True, False),
    ("磨坊街", ["shop"], True, False),
    ("拍卖行", ["auction"], True, False),
    ("大教堂", ["heal"], False, True),
    ("圣殿", ["heal"], False, True),
    ("旅店", ["heal"], False, True),
    ("旅馆", ["heal"], False, True),
    ("公会", ["quest"], False, False),
    ("集市", ["shop", "stall"], True, False),
    ("南市", ["shop", "stall"], True, False),
    ("东市", ["shop", "stall"], True, False),
    ("西市", ["shop", "stall"], True, False),
    ("月市", ["shop", "stall"], True, False),
    ("星光集市", ["shop", "stall"], True, False),
    ("贝壳集市", ["shop", "stall"], True, False),
    ("哨塔集市", ["shop", "stall"], True, False),
    ("集市广场", ["shop", "stall"], True, False),
    ("码头", ["shop"], True, False),
    ("船坞", [], True, False),
    ("广场", ["quest"], False, False),            # 广场：行会/任务（无商店）
    ("大街", ["shop"], True, False),
    ("街", ["shop"], True, False),
    ("巷", [], False, False),
    ("营", [], False, False),
    ("口", [], False, False),
    ("门", [], False, False),
    ("下", [], False, False),
    ("台", [], False, False),
]

# NPC 分配规则：按 funcs/name/title 关键词 → 子区域关键词（城镇）
NPC_ROUTING = [
    (["quest"], "广场"),        # 行会/任务 → 广场类
    (["shop", "craft"], "中央大街"),  # 铁匠 → 大街
    (["shop", "stall"], "集市"),
    (["heal"], "旅店"),
    (["lore"], "旅店"),
    (["apprentice"], "集市"),  # 草药师/生活副业 → 集市（卖药/材料）
    (["enhance"], "中央大街"),
    (["cook"], "集市"),
    (["fish"], "码头"),
    (["ship"], "码头"),
]


def _sub_id(mid, idx, name):
    """子区域 id：地图id_序号（如 oak_town_1）。"""
    return f"{mid}_{idx}"


def _pick_npc_subarea(npc, subarea_names):
    """按 NPC funcs/名字选城镇子区域关键词，默认第一个广场。v2：优先建筑名精确匹配。"""
    funcs = npc.get("funcs", [])
    title = npc.get("title", "")
    name = npc.get("name", "")
    # 铁匠 → 含"铁匠"的子区域
    if "铁匠" in title or "铁匠" in name:
        for nm in subarea_names:
            if "铁匠" in nm:
                return nm
    # 旅店/老板娘/酒馆 → 含"旅店/旅馆"的子区域
    if "旅店" in title or "旅馆" in title or "老板娘" in title or "酒馆" in title:
        for nm in subarea_names:
            if "旅店" in nm or "旅馆" in nm:
                return nm
    # 草药/炼金 → 含"草药/炼金"或集市类
    if "草药" in title or "炼金" in title:
        for nm in subarea_names:
            if "草药" in nm:
                return nm
        for nm in subarea_names:
            if "市" in nm:
                return nm
    # 牧师/神父/院长 → 含"教堂/圣殿"子区域
    if any(k in title for k in ("神父", "牧师", "主教", "院长", "修女")):
        for nm in subarea_names:
            if "教堂" in nm or "圣殿" in nm:
                return nm
    # 医师/医生 → 含"医师/医馆"或民居类
    if any(k in title for k in ("医师", "医生", "药师")):
        for nm in subarea_names:
            if "医师" in nm or "医" in nm:
                return nm
        for nm in subarea_names:
            if "巷" in nm:
                return nm
    # 强化/附魔 → 大街/街
    if any(k in title for k in ("强化", "附魔")):
        for nm in subarea_names:
            if "大街" in nm or "街" in nm:
                return nm
    # 厨师/摊主 → 集市类
    if any(k in title for k in ("厨师", "摊主", "小贩", "大厨")):
        for nm in subarea_names:
            if "市" in nm or "集市" in nm:
                return nm
    # 行会/公会 → 广场或公会
    if "行会" in title or "公会" in title:
        for nm in subarea_names:
            if "公会" in nm:
                return nm
        return subarea_names[0]
    # 拍卖 → 拍卖行
    if "拍卖" in title or "拍卖" in name:
        for nm in subarea_names:
            if "拍卖" in nm:
                return nm
    # 码头/船坞
    if "码头" in title or "船长" in title or "船" in title:
        for nm in subarea_names:
            if "码头" in nm or "船坞" in nm:
                return nm
    # 城主/镇长/首领 → 广场
    if any(k in title for k in ("城主", "镇长", "首领", "村长", "领袖")):
        return subarea_names[0]
    # funcs 兜底
    if "shop" in funcs:
        for nm in subarea_names:
            if "街" in nm or "市" in nm:
                return nm
    if "quest" in funcs:
        return subarea_names[0]
    if "heal" in funcs:
        for nm in subarea_names:
            if "旅店" in nm or "旅馆" in nm:
                return nm
    return subarea_names[0]


def _pick_wild_npc_subarea(npc, subarea_names):
    """野外图 NPC：找名称/称号匹配的子区域，否则挂入口（第一个）。"""
    title = npc.get("title", "")
    name = npc.get("name", "")
    for nm in subarea_names:
        if any(k in title or k in name for k in (nm[:2],)):
            return nm
    return subarea_names[0]


def build_subareas():
    """基于 maps.py 现有数据 + 拆分表构建 SUBAREAS。"""
    sys.path.insert(0, os.path.join(PLUGIN_DIR, "game"))
    from game.data.maps import MAPS
    from game.data.npcs import NPCS

    subareas = {}
    for m in MAPS:
        mid = m["id"]
        mtype = m.get("type", "野外")
        if mtype == "副本":
            # 副本不拆子区域：单入口子区域（挂 NPC/Boss）
            items = [{
                "id": f"{mid}_1",
                "name": "入口",
                "icon": "🚪",
                "desc": f"{m['name']}入口",
                "type": "副本",
                "lv": m.get("lv", 1),
                "npcs": list(m.get("npcs", [])),
                "monsters": m.get("monsters", []),
                "elite": m.get("elite"),
                "boss": m.get("boss"),
                "funcs": ["instance"],
                "shop": False,
                "healer": False,
            }]
            subareas[mid] = items
            continue
        if mtype == "城镇区域":
            names = TOWN_SPLIT.get(mid)
            if not names:
                continue
            items = []
            for idx, nm in enumerate(names, 1):
                sa = {
                    "id": _sub_id(mid, idx, nm),
                    "name": nm,
                    "icon": "🏘️",
                    "desc": f"{m['name']}·{nm}",
                    "type": "城镇",
                    "lv": m.get("lv", 1),
                    "npcs": [],
                    "monsters": [],
                    "elite": None,
                    "boss": None,
                    "funcs": [],
                    "shop": False,
                    "healer": False,
                }
                # 功能规则
                for kw, funcs, shop, healer in TOWN_FUNC_RULES:
                    if kw in nm:
                        sa["funcs"] = list(funcs)
                        sa["shop"] = shop
                        sa["healer"] = healer
                        break
                items.append(sa)
            # NPC 分配（v2：按建筑名精确匹配子区域）
            for nid in m.get("npcs", []):
                npc = NPCS.get(nid)
                if not npc:
                    continue
                sub_name = _pick_npc_subarea(npc, [i["name"] for i in items])
                target = next((sa for sa in items if sa["name"] == sub_name), items[0])
                target["npcs"].append(nid)
            # 方碑（如果有）挂中心广场（首个子区域）
            subareas[mid] = items
        else:
            rows = WILD_SPLIT.get(mid)
            if not rows:
                continue
            monsters = m.get("monsters", []) or []
            # 按等级排序怪物（低→高）
            ms = sorted(monsters, key=lambda x: x[3])
            items = []
            # 分桶：每个子区域按等级区间收怪
            bucket_size = max(1, len(ms) // len(rows))
            for idx, (nm, lv) in enumerate(rows, 1):
                sa = {
                    "id": _sub_id(mid, idx, nm),
                    "name": nm,
                    "icon": "🌲",
                    "desc": f"{m['name']}·{nm}",
                    "type": "野外",
                    "lv": lv,
                    "npcs": [],
                    "monsters": [],
                    "elite": None,
                    "boss": None,
                    "funcs": ["explore"],
                    "shop": False,
                    "healer": False,
                }
                # 普通怪：按区间分配（入口低→深处高）
                start = (idx - 1) * bucket_size
                end = idx * bucket_size if idx < len(rows) else len(ms)
                sa["monsters"] = ms[start:end]
                items.append(sa)
            # 野外图 NPC：挂入口（或匹配名称的子区域）
            for nid in m.get("npcs", []):
                npc = NPCS.get(nid)
                if not npc:
                    continue
                sub_nm = _pick_wild_npc_subarea(npc, [i["name"] for i in items])
                target = next((sa for sa in items if sa["name"] == sub_nm), items[0])
                target["npcs"].append(nid)
            # 精英 → 最后一个子区域（最深处）
            if m.get("elite"):
                items[-1]["elite"] = m["elite"]
            # Boss → 最后一个子区域
            if m.get("boss"):
                items[-1]["boss"] = m["boss"]
            subareas[mid] = items
    return subareas


def _py_repr(obj):
    """Python 字面量序列化（None→None，中文保留，缩进美化）。"""
    if obj is None:
        return "None"
    if isinstance(obj, bool):
        return "True" if obj else "False"
    if isinstance(obj, dict):
        inner = ",\n".join(f"{json.dumps(k, ensure_ascii=False)}: {_py_repr(v)}" for k, v in obj.items())
        return "{\n" + _indent(inner) + "\n}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        inner = ",\n".join(_py_repr(v) for v in obj)
        return "[\n" + _indent(inner) + "\n]"
    if isinstance(obj, tuple):
        inner = ",\n".join(_py_repr(v) for v in obj)
        return "(\n" + _indent(inner) + "\n)"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    return repr(obj)


def _indent(s, n=4):
    return "\n".join(" " * n + line for line in s.split("\n"))


def main():
    subareas = build_subareas()
    # 生成 subareas.py
    out = []
    out.append("# -*- coding: utf-8 -*-")
    out.append('"""奥兰迪亚·余烬纪年 数据层 - subareas.py（自动生成，2026-08-07）"""')
    out.append("# 子区域拆分：02 章 13 节。key=地图id，value=子区域列表（顺序即默认落点）")
    out.append("SUBAREAS = " + _py_repr(subareas))
    out.append("")
    path = os.path.join(PLUGIN_DIR, "game", "data", "subareas.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    total = sum(len(v) for v in subareas.values())
    print(f"生成完成：{len(subareas)} 张地图，{total} 个子区域 → {path}")
    for mid, items in list(subareas.items())[:5]:
        print(f"  {mid}: {[i['name'] for i in items]}")


if __name__ == "__main__":
    main()
