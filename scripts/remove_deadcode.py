# -*- coding: utf-8 -*-
"""v101.1 死代码批量删除：AST 定位函数行范围，删除后逐文件 py_compile 验证。
用法：python scripts/remove_deadcode.py
"""
import ast
import subprocess
import sys

TARGETS = [
    # (文件, [要删的函数名])
    ("game/core/affix_effects.py", ["_sp_frost", "_sp_burn", "_sp_thunder", "_sp_pierce",
                                    "_sp_lifesteal_set", "_sp_execute"]),  # 只删无装饰的副本（同名的第一个有 @register）
    ("game/commands/player.py", ["_do_evolve"]),
    ("game/commands/base.py", ["_attr_sources", "_reply"]),
    ("game/commands/combat.py", ["_is_grey"]),
    ("game/commands/world.py", ["_npc_func_label"]),
    ("game/core/drops.py", ["_stage_for_lv"]),
    ("game/core/craft.py", ["craft_recipes_for_level"]),
    ("game/core/affix.py", ["equip_affix_lines"]),
    ("game/core/monsters.py", ["monster_skills_pool"]),
    ("game/store/social.py", ["guild_get", "guild_kick", "guild_count"]),
    ("game/store/feedback.py", ["mark_feedback_done", "ensure_feedback_reply_col",
                                "get_feedback_with_reply", "mark_feedback_broadcast"]),
    ("game/core/time_weather.py", ["today_weather_for_test"]),
]

# 同名多定义时：只删无装饰器的副本（affix_effects 的 _sp_*）
KEEP_DECORATED = {"_sp_frost", "_sp_burn", "_sp_thunder", "_sp_pierce", "_sp_lifesteal_set", "_sp_execute"}


def remove_funcs(path, names):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    lines = src.split("\n")
    targets = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            has_dec = bool(node.decorator_list)
            if node.name in KEEP_DECORATED and has_dec:
                continue  # 保留注册版
            # 删除范围：函数体（含装饰器）；向前吞掉紧邻的空行（最多2个）
            start = node.lineno - 1
            if has_dec:
                start = node.decorator_list[0].lineno - 1
            end = node.end_lineno  # 含结束行
            targets.append((start, end, node.name))
    if not targets:
        print(f"  ⚠️ {path}: 未找到目标函数 {names}")
        return False
    # 从后往前删，行号不漂移
    for start, end, name in sorted(targets, reverse=True):
        # 吞前导空行（最多2个）
        lead = start
        while lead > 0 and lines[lead - 1].strip() == "" and start - lead < 2:
            lead -= 1
        del lines[lead:end]
        print(f"  🗑️ {path}: L{start + 1}-{end} {name} ({end - start} 行)")
    new_src = "\n".join(lines)
    open(path, "w", encoding="utf-8").write(new_src)
    return True


def main():
    for path, names in TARGETS:
        print(f"--- {path} ---")
        try:
            remove_funcs(path, names)
        except SyntaxError as e:
            print(f"  ❌ {path} 语法错误: {e}")
            sys.exit(1)
    # 验证：所有改动文件 py_compile
    print("\n=== py_compile 验证 ===")
    for path, _ in TARGETS:
        r = subprocess.run([sys.executable, "-m", "py_compile", path])
        print(f"  {'✅' if r.returncode == 0 else '❌'} {path}")


if __name__ == "__main__":
    main()
