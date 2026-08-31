# -*- coding: utf-8 -*-
"""v142 行为一致性验证：数据驱动覆盖检查（直接解析文件，避免循环导入）"""
import re, sys

BASE = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall"

# 从 sets.py + class_sets.py 提取有 params 的 effect
def extract_effects(path):
    src = open(path, encoding="utf-8").read()
    # 匹配 effect: X, ... params: {...}
    pat = re.compile(r"'?effect'?\s*:\s*['\"]([a-z_]+)['\"][^}]*?'params'\s*:\s*\{([^}]*)\}")
    out = {}
    for m in pat.finditer(src):
        eff, params_blk = m.group(1), m.group(2)
        t = re.search(r"'type'\s*:\s*['\"]([a-z_]+)['\"]", params_blk)
        if t:
            out[eff] = t.group(1)
    return out

# 从 affix_effects.py 提取 SET_PROC_TYPES 和执行器
src_ae = open(f"{BASE}/game/core/affix_effects.py", encoding="utf-8").read()
known_types = set(re.findall(r'"([a-z_]+)":\s*(_sp_[a-z_]+|_taken_[a-z_]+)', src_ae))
known_types = {t for t, _ in re.findall(r'"([a-z_]+)":\s*(_sp_[a-z_]+|_taken_[a-z_]+)', src_ae)}

# 旧 handler
legacy = set(re.findall(r'@register\(SET_PROC_EFFECTS,\s*"([a-z_]+)"\)', src_ae))

effects = {}
for p in [f"{BASE}/game/data/sets.py", f"{BASE}/game/core/class_sets.py"]:
    effects.update(extract_effects(p))

print(f"=== 有 params 的 effect: {len(effects)} 个 ===")
for eff, t in sorted(effects.items()):
    print(f"  {eff} -> {t}")

used_types = set(effects.values())
missing = used_types - known_types
print(f"\n=== type 覆盖 ===")
print(f"使用 type: {sorted(used_types)}")
print(f"已知 type: {sorted(known_types)}")
print(f"缺失执行器: {missing if missing else '无'}")

# 无 params 但仍注册的旧 handler（会走旧路径）
with_params = set(effects.keys())
still_legacy = legacy - with_params
print(f"\n=== 仍走旧 handler 的 effect（无 params，需确认是否该补）===")
print(sorted(still_legacy) if still_legacy else "无")
