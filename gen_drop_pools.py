# -*- coding: utf-8 -*-
"""掉落池迁移生成器：从老数据全量生成 game/data/drop_pools.py（DROP_POOLS 统一表）

老数据 → 新池 key 映射：
  GATHER_MAP_POOLS      gather:{map}
  MINING_DEEP_POOLS     mine:{map}
  GATHER_COND_POOLS     gather_cond:{map}   （条件采集，Weighted，带 cond 标签）
  FISH_POOL + FISHING_SPOTS  fish:{spot}
  FISH_COLLECT          fish_collect        （彩蛋收藏鱼，Weighted 独立）
  EXPLORE_EVENTS        explore:{id}        （事件模板，保留原 template+params）
  ELITE_EQUIP_DROP      elite:{怪名}        （Fixed）
  INSTANCE_BOSS_EQUIP_DROP boss:{inst}      （Table：主题档+专属档）
  WILD_KING_CHEST_TIERS chest:{tier}        （Table：全套宝箱奖励）
  怪物 drops（subareas 收集） mon:{怪名}     （Weighted 全掉=各 w 1）
  WORLD_BOSS_POOL       worldboss:{name}    （预留，掉落走外部引擎）

迁移保真原则：只转格式不动语义；条目 item 统一物品ID（中文名→ID 映射处保留原名供审计）。
"""
import io, sys, os, json, re
from collections import defaultdict, Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.getcwd())
import game.data as D

ITEM_CN2ID = {v.get('name'): k for k, v in D.ITEMS.items()}

def to_id(name_or_id):
    """中文名或 ID → ID"""
    if name_or_id in D.ITEMS:
        return name_or_id
    return ITEM_CN2ID.get(name_or_id, name_or_id)

DROP = {}

def add_weighted(key, entries):
    """entries: [(item, w)] 或 [(item, w, extra_dict)]"""
    norm = []
    for t in entries:
        item, w = t[0], t[1]
        e = {"item": to_id(item), "w": int(w)}
        if len(t) > 2 and isinstance(t[2], dict):
            e.update(t[2])
        norm.append(e)
    DROP[key] = {"type": "weighted", "entries": norm}

# ============ 1. 采集池 ============
for mapid, pool in D.GATHER_MAP_POOLS.items():
    add_weighted(f"gather:{mapid}", pool)

# ============ 2. 挖掘深池 ============
for mapid, pool in D.MINING_DEEP_POOLS.items():
    add_weighted(f"mine:{mapid}", pool)

# ============ 3. 条件采集池 ============
# GATHER_COND_POOLS: map -> {cond: [(mat, w)]}
for mapid, conds in D.GATHER_COND_POOLS.items():
    if not isinstance(conds, dict):
        continue
    for cond, pool in conds.items():
        if isinstance(pool, (list, tuple)):
            add_weighted(f"gather_cond:{mapid}:{cond}", pool)

# ============ 4. 垂钓池 ============
# FISH_POOL 条目带 name/quality/type/price/spots/weight/size_range/weight_range/season/season_boost
fish_entries_by_spot = defaultdict(list)  # spot_id -> list
# FISH_POOL 30 条全部进池；品种的 spots 字段限定钓点（无 spots=全水域）
for f in D.FISH_POOL:
    entry = {
        "item": to_id(f.get("mat_id") or f.get("name")),
        "name": f.get("name"),
        "quality": f.get("quality"),
        "w": int(f.get("weight", 1)),
    }
    # 保留全部元数据字段（desc/价格/尺寸/季节/水域——展示与过滤都需要）
    for k in ("spots", "season", "season_boost", "size_range", "weight_range",
              "price", "type", "desc", "weight", "id", "mat_id"):
        if f.get(k) is not None:
            entry[k] = f[k]
    spots = f.get("spots") or list(D.FISHING_SPOTS.keys())
    for sp in spots:
        fish_entries_by_spot[sp].append(entry)

for spot_id, spot_cfg in D.FISHING_SPOTS.items():
    entries = fish_entries_by_spot.get(spot_id, [])
    DROP[f"fish:{spot_id}"] = {
        "type": "fish",
        "spot_cfg": {k: spot_cfg[k] for k in ("min_lv", "ban_quality", "subarea", "desc", "name") if k in spot_cfg},
        "entries": entries,
    }

# ============ 5. 彩蛋收藏鱼 ============
if getattr(D, "FISH_COLLECT", None):
    DROP["fish_collect"] = {
        "type": "weighted",
        "entries": [{"item": to_id(cf.get("id") or cf.get("name") or cf.get("mat_id")),
                     "name": cf.get("name"), "desc": cf.get("desc"),
                     "chance": cf.get("chance"), "spots": cf.get("spots"), "time": cf.get("time"),
                     "w": 1}
                    for cf in D.FISH_COLLECT],
    }

# ============ 6. 精英专属 ============
for mname, rid in D.ELITE_EQUIP_DROP.items():
    DROP[f"elite:{mname}"] = {"type": "fixed", "entries": [{"item": f"equip:{rid}"}]}

# ============ 7. 副本 Boss ============
for inst_id, cfg in D.INSTANCE_BOSS_EQUIP_DROP.items():
    rolls = []
    # ① 主题装档（pool 随机 1 件）
    pool = cfg.get("pool") or []
    if pool:
        # 主题池 = weighted 子池（等权），引用内联
        sub_key = f"inst_pool:{inst_id}"
        DROP[sub_key] = {"type": "weighted", "entries": [{"item": f"equip:{r}", "w": 1} for r in pool]}
        rolls.append({"pool": sub_key, "chance": float(cfg.get("pool_rate", 0))})
    # ② 专属档
    be = cfg.get("boss_equip")
    if be:
        rolls.append({"pool": f"equip:{be}", "chance": float(cfg.get("boss_rate", 0))})
    # ③ 副本专属材料（inst.materials）
    inst = D.INSTANCES.get(inst_id, {})
    mats = inst.get("materials") or []
    if mats:
        sub_key = f"inst_mats:{inst_id}"
        DROP[sub_key] = {"type": "weighted", "entries": [{"item": to_id(m), "w": 1} for m in mats]}
        rolls.append({"pool": sub_key, "chance": 1.0, "n": inst.get("mat_count", 1)})
    DROP[f"boss:{inst_id}"] = {"type": "table", "rolls": rolls}

    # ============ 副本搜刮：战利品堆 + 暗格宝箱 ============
    # v174：instance.py 通关后搜刮掉落数据化（原 _instance_loot_pile / _instance_secret_chest 手写）
    # 战利品堆（必出）：金币=副本gold×30% + 专属材料×1
    mats = inst.get("materials") or []
    loot_pile_rolls = [{"pool": "gold_pct:30", "chance": 1.0}]
    if mats:
        sub_key = f"inst_mats:{inst_id}"
        if sub_key not in DROP:
            DROP[sub_key] = {"type": "weighted", "entries": [{"item": to_id(m), "w": 1} for m in mats]}
        loot_pile_rolls.append({"pool": sub_key, "chance": 1.0, "n": 1})
    DROP[f"loot_pile:{inst_id}"] = {"type": "table", "rolls": loot_pile_rolls}
    # 暗格宝箱（5 档互斥）：图纸残页25% / 装备40%(boss60-elite40混合) / 蓝符20% / 材料10% / 星灵蝶蛋5%
    # 装备档特殊：boss 池优先 60%、失败切 elite，再失败兜底材料——用 equip_drop_mix 特殊引用
    DROP[f"secret_chest:{inst_id}"] = {
        "type": "table_choice",
        "rolls": [
            {"pool": "item:mat_tu_zhi_can_ye", "cutoff": 0.25, "n": [2, 4]},
            {"pool": "equip_drop_mix", "cutoff": 0.40,
             "fallback": f"inst_mats:{inst_id}" if mats else "item:mat_shou_rou", "fallback_n": 2},
            {"pool": "rune:blue", "cutoff": 0.20},
            {"pool": f"inst_mats:{inst_id}" if mats else "item:mat_shou_rou",
             "cutoff": 0.10, "n": 2},
            {"pool": "petegg:pet_starbutterfly", "cutoff": 0.05},
        ],
    }

# ============ 8. 野王宝箱 ============
# WILD_KING_CHEST_TIERS: tier -> {gold_range, bp_chance, gem_chance, equip_chance, rune_chance,
#                                 stone_range, pages_range, mats[], collect[]}
for tier, cfg in D.WILD_KING_CHEST_TIERS.items():
    rolls = [{"pool": f"gold:{cfg['gold_range'][0]}:{cfg['gold_range'][1]}", "chance": 1.0}]
    rolls.append({"pool": "bp", "chance": float(cfg.get("bp_chance", 0.5))})
    rolls.append({"pool": "gem", "chance": float(cfg.get("gem_chance", 0.2))})
    rolls.append({"pool": "equip_drop:boss", "chance": float(cfg.get("equip_chance", 0.1))})
    rolls.append({"pool": "rune", "chance": float(cfg.get("rune_chance", 0.15))})
    # 强化石区间
    sr = cfg.get("stone_range") or [1, 2]
    rolls.append({"pool": f"item:mat_gao_ji_qiang_hua_shi", "chance": 1.0, "n": list(sr)})
    # mats 保底材料
    mats = cfg.get("mats") or []
    if mats:
        sub_key = f"chest_mats:{tier}"
        DROP[sub_key] = {"type": "weighted", "entries": [{"item": to_id(m), "w": 1} for m in mats]}
        rolls.append({"pool": sub_key, "chance": 1.0})
    # collect 收藏品
    coll = cfg.get("collect") or []
    if coll:
        sub_key = f"chest_collect:{tier}"
        DROP[sub_key] = {"type": "weighted", "entries": [{"item": to_id(c), "w": 1} for c in coll]}
        rolls.append({"pool": sub_key, "chance": 1.0})
    DROP[f"chest:{tier}"] = {"type": "table", "rolls": rolls}

# ============ 9. 子区域怪物 drops ============
# 收集所有 monsters/elite/boss 槽位的材料掉落：mon:{怪名} 权重全 1
mon_drops = defaultdict(list)
for mapid, sas in D.SUBAREAS.items():
    for sa in sas:
        for slot in ('monsters', 'elite', 'boss'):
            ent = sa.get(slot)
            if not ent:
                continue
            lst = ent if (isinstance(ent, list) and ent and isinstance(ent[0], (list, tuple))) else ([ent] if ent else [])
            for t in lst:
                if not isinstance(t, (list, tuple)) or len(t) < 6:
                    continue
                mname = t[1]
                # 避免与精英专属 fixed 撞 key——材料池用 mon: 前缀
                seen = set()
                for dr in t[5]:
                    if dr in seen:
                        continue
                    seen.add(dr)
                    mon_drops[mname].append({"item": to_id(dr), "w": 1})
for mname, entries in mon_drops.items():
    DROP[f"mon:{mname}"] = {"type": "weighted", "entries": entries}

# ============ 10. 副本关卡小怪掉落（stages monsters） ============
# 补充 instances stages 里 monsters/elite/boss 的 drops（与 subareas 同构）
inst_mon_drops = defaultdict(list)
for iid, inst in D.INSTANCES.items():
    for st in (inst.get('stages') or []):
        if not isinstance(st, dict):
            continue
        for slot in ('monsters', 'elite', 'boss'):
            ent = st.get(slot)
            if not ent:
                continue
            lst = ent if (isinstance(ent, list) and ent and isinstance(ent[0], (list, tuple))) else ([ent] if ent else [])
            for t in lst:
                if not isinstance(t, (list, tuple)) or len(t) < 6:
                    continue
                mname = t[1]
                seen = set()
                for dr in t[5]:
                    if dr in seen:
                        continue
                    seen.add(dr)
                    inst_mon_drops[mname].append({"item": to_id(dr), "w": 1})
for mname, entries in inst_mon_drops.items():
    # 已由 subareas 登记的同名怪 → 合并（不丢条目）
    key = f"mon:{mname}"
    if key in DROP:
        existing = {e['item'] for e in DROP[key]['entries']}
        for e in entries:
            if e['item'] not in existing:
                DROP[key]['entries'].append(e)
    else:
        DROP[key] = {"type": "weighted", "entries": entries}

# ============ 输出 ============
out_path = 'game/data/drop_pools.py'
header = '''# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - drop_pools.py（掉落系统统一表 v174）

由 scripts/（迁移生成器）从老常量全量生成，勿手改。
结构：DROP_POOLS = {池key: {type, entries/rolls/spot_cfg...}}
四类 type：
  weighted  带权条目抽取（采集/挖掘/条件采集/怪物材料/彩蛋）
  fish      垂钓（spot_cfg + 质量档 + 品种 entries）
  table     多层概率表（副本Boss/野王宝箱——rolls 独立判定）
  fixed     固定掉落（精英专属）
条目 item 引用前缀：equip:rid=名册装备 / bp=图纸 / gem=宝石 / gold:a:b=金币 / item:id=物品。
消费端统一入口 game/core/drop_engine.py roll()。
"""

DROP_POOLS = {
'''
lines = [header]
for key in sorted(DROP.keys()):
    lines.append(f"    {key!r}: {DROP[key]!r},")
lines.append("}\n")
open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
print(f"生成完成: {out_path} 池数 {len(DROP)}")

# 快速统计
types = Counter(v['type'] for v in DROP.values())
print("类型分布:", dict(types))
total_entries = sum(len(v.get('entries') or []) for v in DROP.values())
print("总条目:", total_entries)
