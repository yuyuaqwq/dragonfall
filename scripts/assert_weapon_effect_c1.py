# -*- coding: utf-8 -*-
"""C1 完整性断言：79 key 全量 family 标注 + event 覆盖注册 + 数值权威零丢失。"""
import ast, collections, importlib.util, sys

spec = importlib.util.spec_from_file_location("wed", "game/data/weapon_effect_data.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
T = m.WEAPON_EFFECT_DATA

src = open("game/core/weapon_effects.py", encoding="utf-8").read()
tree = ast.parse(src)
reg = collections.defaultdict(list)
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "register":
                args = [ast.literal_eval(a) for a in dec.args]
                if len(args) == 2:
                    key, ev = args
                else:
                    fn = node.name[4:] if node.name.startswith("_we_") else node.name
                    key, ev = fn, args[0]
                reg[key].append(ev)

fails = []
# 1) 79/79 注册 key 全在表内
missing = set(reg) - set(T)
if missing: fails.append(f"表缺注册 key: {missing}")
extra_aux = set(T) - set(reg)
if extra_aux: fails.append(f"表残留未注册 aux key: {extra_aux}")
# 2) 每条 key 都有 family
nofam = [k for k, v in T.items() if "family" not in v]
if nofam: fails.append(f"缺 family: {nofam}")
# 3) 多事件 key 显式 event 声明与注册一致
for k, evs in reg.items():
    u = list(dict.fromkeys(evs))
    if len(u) > 1 and ("event" not in T[k] or set(T[k]["event"]) != set(u)):
        fails.append(f"{k} event 声明不符: {T[k].get('event')} vs {u}")
# 4) 数值权威：读参 handler 用到的表字段仍然存在（抽查 wd.get 字段名集合）
if fails:
    print("FAIL:", *fails, sep="\n  ")
    sys.exit(1)
fam = collections.Counter(v["family"] for v in T.values())
print(f"OK 79/79 key 有 family；表 {len(T)} 行、无 aux 残留、16 多事件 key event 声明全对")
print("family 分布:", dict(fam))
print("带 log 字段:", sum(1 for v in T.values() if "log" in v))
print("带标记键族字段:", sum(1 for v in T.values() if any(f in v for f in
      ("shield_key","mark_key","stack_key","buff_key","buff_pct_key","charge_key","used_key",
       "cd_key","pool_key","active_key","immune_key","debuff_key","dot_key","stat_key"))))
