# -*- coding: utf-8 -*-
"""B2 前置验证：扫描 store 动态 SQL 函数的调用点字段名，对照白名单防误杀"""
import ast, os, sys

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
GAME = os.path.join(ROOT, "game")

WHITELISTS = {
    "update_player": {  # players 表实际列（PRAGMA 2026-08-10 验证，qq_id 排除——WHERE 专用）
        "name","class_name","level","exp","gold","hp","mp","max_hp","max_mp",
        "cur_map","equipment","skills","class_tier","attr_pts","attributes",
        "skill_points","learned_skills","shortcuts","evolve_path","skill_levels",
        "created_at","last_active","portals","skill_bar","skill_spent","mounts",
        "learned_blueprints","lucky_until","deed","apprentices","race",
        "equipped_title","hidden_class_unlock","deed_lv","cur_subarea",
        "stamina","stamina_ts","explore_wandering","gender",
    },
    "bump_stats": {
        "kills","elite_kills","boss_kills","deaths","day_kills","visited_areas",
        "inst_clears","party_count","fish_count","gather_count","mine_count",
        "cook_count","alchemy_count","craft_count","enhance_count",
        "enchant_count","world_events","catch_collect",
    },
    "pet_update": {"pet_key","name","level","exp","satiety","bond","last_sat_time"},
    "add_prof_exp": set(),  # key 是位置参数，单独扫
    "forget_prof": set(),
}

PROF_KEYS = ("gather","mining","fishing","alchemy","craft","cooking","enhance","enchant")

# 位置参数扫描：add_prof_exp(gid, qid, key, exp) / forget_prof(gid, qid, key)
POS_PROF_KEYS = {"add_prof_exp", "forget_prof"}

problems = []
for d, _, files in os.walk(GAME):
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(d, f)
        src = open(path, encoding="utf-8").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else None)
            if name not in WHITELISTS and name not in POS_PROF_KEYS:
                continue
            loc = f"{os.path.relpath(path, ROOT)}:{node.lineno}"
            if name in POS_PROF_KEYS:
                # 第 3 个位置参数是 key（跳过 self/gid/qid 前的关键字）
                pos = [a for a in node.args if isinstance(a, ast.Constant)]
                # 简化：只报字符串字面量参数
                for a in node.args[2:]:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        if a.value not in PROF_KEYS:
                            problems.append(f"{loc} {name} 位置参数 {a.value!r}")
                continue
            for kw in node.keywords:
                if kw.arg and kw.arg not in WHITELISTS[name]:
                    problems.append(f"{loc} {name}({kw.arg}=...) 不在白名单")

if problems:
    print("❌ 发现白名单外调用:")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("✅ 所有调用点字段名均在白名单内，可安全加校验")
