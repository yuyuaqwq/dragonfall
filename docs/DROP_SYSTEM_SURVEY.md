# -*- coding: utf-8 -*-
"""掉落池结构差异侦察：为统一抽象设计提供依据"""
import io, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import game.data as D

print("========== 各池结构形态 ==========")
# 1. GATHER_MAP_POOLS: map -> [(mat_id, weight)]
print("1. GATHER_MAP_POOLS[oak_plain]:", D.GATHER_MAP_POOLS['oak_plain'][:3], "...")
print("   形态: dict[map_id] = list[(item_id, weight)]")

# 2. MINING_DEEP_POOLS
print("\n2. MINING_DEEP_POOLS[rockfall_gorge]:", D.MINING_DEEP_POOLS['rockfall_gorge'])
print("   形态: dict[map_id] = list[(item_id, weight)] (与采集同构)")

# 3. FISH_POOL
print("\n3. FISH_POOL[0]:", str(D.FISH_POOL[0])[:400])
print("   形态: list[dict{name, quality, weight, spots,...}]")

# 4. EXPLORE_EVENTS
print("\n4. EXPLORE_EVENTS[0]:", str(D.EXPLORE_EVENTS[0])[:400])
print("   形态: list[dict{id, weight, template, params}]")

# 5. ELITE_EQUIP_DROP
print("\n5. ELITE_EQUIP_DROP:", list(D.ELITE_EQUIP_DROP.items())[:2])
print("   形态: dict[monster_name] = roster_rid")

# 6. INSTANCE_BOSS_EQUIP_DROP
print("\n6. INSTANCE_BOSS_EQUIP_DROP[inst_goblin_camp]:", D.INSTANCE_BOSS_EQUIP_DROP['inst_goblin_camp'])
print("   形态: dict[inst_id] = {boss_equip, boss_rate, pool[], pool_rate, pity}")

# 7. WILD_KING_CHEST_TIERS
print("\n7. WILD_KING_CHEST_TIERS[low]:", D.WILD_KING_CHEST_TIERS['low'])
print("   形态: dict[tier] = {gold_range, bp_chance, equip_chance, mats[], ...}")

# 8. 小怪/精英/Boss 的 drops 字段
print("\n8. 怪物 drops 字段（6元组内嵌）: 小怪 ['巨型野猪牙'] 精英 ['灰影狼牙'] Boss ['咕噜皇冠']")
print("   形态: 怪物定义内嵌 list[str]（中文名）")

# 9. 探索事件里的材料池引用（mats 字段中文名）
print("\n9. 探索事件 params.mats 示例:", [e.get('params', {}).get('mats') for e in D.EXPLORE_EVENTS if isinstance(e, dict) and e.get('params', {}).get('mats')][:5])

# 10. roll_drop_equip 逻辑（装备池：白名单+等级就近）
print("\n10. roll_drop_equip: role->{rate, quality_ratio}, source 白名单(boss,legend), |lv差|≤15/30")

# ========== 汇总：可以统一的抽象 ==========
print("\n\n========== 统一抽象分析 ==========")
print("共同点: 几乎都是 '从带权条目集合中按权重抽一个'")
print("差异点:")
print("  A. 条目粒度: (item_id, weight) / list[dict] / monster_name->rid / 内嵌 drops")
print("  B. 引用方式: item_id / 中文名 / roster_rid / 模板+params")
print("  C. 附加维度: 等级门槛/禁档/稀有度/概率/次数/冷却")
print("  D. 消费上下文: 地图/子区域/怪物/副本/玩家等级")
