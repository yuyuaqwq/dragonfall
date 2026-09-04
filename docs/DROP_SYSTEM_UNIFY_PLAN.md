# 掉落系统统一抽象重构方案 v2（DROP_SYSTEM_UNIFY · 分层策略）

> 状态：鱼鱼授权格温全权决定 ｜ 2026-09-04
> 目标：所有掉落收敛到统一 `DROP_POOLS` 数据表 + `drop_engine` 引擎 + 统一审计/门禁。
> 选型：**分层抽象**（统一入口 + Weighted/Fish/BossTable/Fixed 四种子策略）。

## 一、统一数据格式 DROP_POOLS

```python
DROP_POOLS = {
    # ============ Weighted 带权池（采集/挖掘/探索/通用材料） ============
    "gather:oak_plain": {
        "type": "weighted",
        "entries": [{"item": "mat_cao_yao", "w": 30}, ...],   # item=物品ID或 equip:/bp: 前缀
        "fallback": {"mode": "price_band"},                     # 可选兜底
    },
    "mine:rockfall_gorge": {"type": "weighted", "entries": [...]},

    # ============ Fish 垂钓池（质量档 → 品种） ============
    "fish:oak_plain": {
        "type": "fish",
        "spot_cfg": {"min_lv": 1, "ban_quality": ["purple", "orange"], "subarea": "oak_plain_3"},
        "quality_weights": {"1": [55,30,10,4,1], "2": [...], ...},  # 垂钓等级→五档权重（原FISH_QUALITY_WEIGHTS）
        # 品种直接来自 entries（带 quality/season/spots/weight/size_range 等元数据）
        "entries": [{"item": "mat_yin_lin_yu", "quality": "white", "w": 55, "spots": null, ...}],
    },

    # ============ BossTable 多层概率表（副本Boss/野王宝箱/垂钓惊喜） ============
    "boss:inst_goblin_camp": {
        "type": "table",
        "rolls": [
            {"pool": "fixed:咕噜皇冠", "chance": 0.05},          # 专属稀有
            {"pool": "weighted:goblin主题池", "chance": 0.35, "pity": 20},
            {"pool": "blueprint", "chance": 0.10},               # 图纸独立
            {"pool": "gem:boss", "chance": 0.20},
        ],
    },
    "chest:wild_low": {"type": "table", "rolls": [
        {"pool": "gold", "range": [300, 600]},                   # 必出
        {"pool": "blueprint", "chance": 0.5},
        {"pool": "equip:boss", "chance": 0.1},
        {"pool": "gem", "chance": 0.2},
        {"pool": "rune", "chance": 0.15},
        {"pool": "item:mat_gao_ji_qiang_hua_shi", "n": [2, 4]},
        {"pool": "weighted:mats_high", "chance": 1.0},
    ]},

    # ============ Fixed 固定掉落（精英专属/Boss材料/必掉清单） ============
    "elite:狼王·灰影": {"type": "fixed", "entries": [{"item": "eq_hui_ying_lang_ya_ren"}]},
    "mon:狼王·灰影":   {"type": "weighted", "entries": [{"item": "mat_zuo_lang_quan_chi", "w": 1}]},
}
```

### 条目 item 引用统一
- `mat_xxx` / 任意物品 ID → 物品
- `eq_xxx` 名册 ID → 名册装备
- `bp` 特殊池 → 图纸（等级就近，走 roll_blueprint）
- `gem` / `rune` / `gold` 特殊池 → 各自引擎

## 二、统一引擎 `game/core/drop_engine.py`

```python
class DropContext:  # 抽取上下文
    map_id, subarea_id, monster_name, monster_lv, role,
    inst_id, player_level, prof_lv, luck, season, night, bait, is_loot ...

def roll(pool_key: str, ctx: DropContext, *, qty=1) -> list[dict]:
    """任何池子唯一入口。返回 [{"type": "item"/"equip"/"bp"/"gem"/"gold"...,
        "item_id":..., "count":..., "data":{...}}]"""
    pool = resolve(pool_key)          # 支持 "weighted:xxx" / "fixed:xxx" 内联引用
    return POOL_STRATEGIES[pool["type"]](pool, ctx, qty)

def audit_all() -> AuditReport:
    """全量审计：断链/空池/权重和/等级匹配/重复。把今天的 audit_*.py 固化。"""
```

## 三、消费端收敛（消灭硬编码）

| 消费点 | 旧调用 | 新调用 |
|---|---|---|
| 采集 | economy.py _gather_roll 手写 | `roll(f"gather:{map}", ctx)` |
| 挖掘 | economy.py _settle_mining 手写 | `roll(f"mine:{map}", ctx)` |
| 垂钓 | core/fishing.py 手写 | `roll(f"fish:{spot}", ctx)` |
| 探索 | core/events.py | `roll(f"explore:{id}", ctx)` |
| 精英 | economy.py ELITE 分支 | `roll(f"elite:{怪名}", ctx)` |
| 副本Boss | instance.py 手写 | `roll(f"boss:{inst_id}", ctx)` |
| 野王宝箱 | wild_king.py 手写 | `roll(f"chest:{tier}", ctx)` |
| 小怪/Boss材料 | battle 胜利解析 | `roll(f"mon:{怪名}", ctx)` |
| 垂钓惊喜 | economy.py _fishing_surprise | `roll(f"fish_surprise:{品质}", ctx)` |

## 四、迁移步骤（每步验证）

1. **写 drop_engine.py**（四策略 + roll + audit）——引擎主 agent 亲写
2. **写迁移脚本**：从老数据生成 DROP_POOLS.py（自动，不丢条目）
3. **接采集/挖掘/垂钓** → 跑数值门禁
4. **接探索/精英/副本/野王/小怪** → 跑测试
5. **删老常量 + 修测试引用**（老常量删除，测试改）
6. **test_numeric_drop_unify.py 门禁**（0 断链/空池/权重/等级全绿）
7. **全量回归 244 + 策划案同步 + 双仓提交**

## 五、风险与对策
- 数据量大 → 自动迁移脚本保真 + 迁移后 audit 全绿
- 消费端 48 处引用 → 分批切，每批跑测试
- 垂钓复杂语义 → Fish 策略专门承载，不硬塞通用格式
- 244 测试引用老常量 → 老常量删除后统一改，用 grep 全清
