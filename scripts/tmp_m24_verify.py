# -*- coding: utf-8 -*-
"""M24 修复验证：实例怪 resolve 全通 + 无回归（临时脚本，用完即删）"""
import sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
import game.data as C
from game.data._assembly import _collect_monster_entries

n2i = C._INDEXES["monsters"]["name_to_id"]
i2n = C._INDEXES["monsters"]["id_to_name"]

# ---- 修正版解析 ----
def collect_entries(src, slots):
    for slot in slots:
        ent = src.get(slot)
        if not ent:
            continue
        if isinstance(ent, (tuple, list)) and ent and isinstance(ent[0], (tuple, list)):
            lst = ent
        else:
            lst = [ent]
        for t in lst:
            if isinstance(t, (tuple, list)) and len(t) >= 2 and isinstance(t[1], str):
                yield t[0], t[1]

inst_entries, inst_names_ids, inst_ids = [], defaultdict(set), set()
for iid, ins in C.INSTANCES.items():
    for si, stage in enumerate(ins.get("stages") or []):
        if not isinstance(stage, dict):
            continue
        for slot in ("monsters", "elite", "boss"):
            for mid, mname in collect_entries(stage, (slot,)):
                inst_entries.append((iid, si, stage.get("name"), slot, mid, mname))
                inst_names_ids[mname].add(mid)
                inst_ids.add(mid)

sub_entries = []
for _sas in C.SUBAREAS.values():
    for _sa in _sas:
        for mid, mname in collect_entries(_sa, ("monsters", "elite", "boss")):
            sub_entries.append((mid, mname))
map_entries = []
for _m in C.MAPS:
    for mid, mname in collect_entries(_m, ("monsters", "elite", "boss")):
        map_entries.append((mid, mname))

fail = 0
def check(cond, msg):
    global fail
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        fail += 1

print("【1】实例 stage 全部名字 resolve 到实例内 id（27+ 副本怪全通）")
for name in sorted(inst_names_ids):
    rid = n2i.get(name)
    ok = rid in inst_names_ids[name] and i2n.get(rid) == name
    check(ok, f"{name:12s} resolve→{rid}  实例ids={sorted(inst_names_ids[name])}")

print("【2】实例全部 id 可 display（图鉴反查不露 id）")
for mid in sorted(inst_ids):
    check(i2n.get(mid) is not None, f"{mid:24s} display→{i2n.get(mid)}")

print("【3】串号修正：9 个同名怪不再指向子区域 id")
for name in sorted(inst_names_ids):
    if name in {e[1] for e in sub_entries}:
        sub_id = next(e[0] for e in sub_entries if e[1] == name)
        if sub_id not in inst_names_ids[name]:
            check(n2i.get(name) in inst_names_ids[name] and n2i.get(name) != sub_id,
                  f"{name:12s} 子区域={sub_id} 实例ids={sorted(inst_names_ids[name])} resolve→{n2i.get(name)}")

print("【4】无回归：子区域/地图怪（名字不与实例冲突的）resolve 不变")
shared = set(inst_names_ids)
seen = set()
for mid, mname in sub_entries:
    if mname in shared or mname in seen:
        continue  # 同名冲突交给实例优先；子区域内部同名取首个胜出 id 比对
    seen.add(mname)
    check(n2i.get(mname) == mid, f"{mname:12s} {mid} (当前→{n2i.get(mname)})")
seen = set()
for mid, mname in map_entries:
    if mname in shared or mname in seen:
        continue
    seen.add(mname)
    check(n2i.get(mname) == mid, f"{mname:12s} {mid} (当前→{n2i.get(mname)})")

print("【5】垃圾键清零 + 关键锚点")
garbage = [k for k in n2i if k.startswith("ms_")]
check(len(garbage) == 0, f"ms_* 垃圾键: {len(garbage)}")
check(n2i.get("巨型野猪") == "e_great_boar", f"巨型野猪→{n2i.get('巨型野猪')} (期望 e_great_boar)")
check(n2i.get("野狗") == "m_wild_dog", f"野狗→{n2i.get('野狗')} (期望 m_wild_dog)")
check(n2i.get("野猪") == "m_boar", f"野猪→{n2i.get('野猪')} (期望 m_boar 不变)")
for old_id, old_name in [("m_under_drake", "地底幼龙"), ("m_goblin_berserker", "哥布林狂战士")]:
    check(i2n.get(old_id) == old_name, f"旧 bestiary id {old_id} 仍可 display→{i2n.get(old_id)}")

print("【6】统计")
print(f"  实例 stage 条目 {len(inst_entries)}，唯一名 {len(inst_names_ids)}，唯一 id {len(inst_ids)}")
print(f"  name_to_id 总键数 {len(n2i)}，id_to_name 总键数 {len(i2n)}")
print(f"  实例怪 resolve 全通: {'✅' if fail == 0 else f'❌ {fail} 项失败'}")
sys.exit(1 if fail else 0)
