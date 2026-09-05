# 新会话设计新 Boss 速查（v177 actor-agnostic 引擎已就绪）

> 背景：v177 完成"玩家/怪物同一套引擎"——任何玩家效果怪物都能纯配置获得。
> 本文件是新会话设计 Boss 的配置速查 + 验证方法。引擎改动已完成并全绿（40 门禁）。

## 怪物现在能配什么（全部实测通过）

### 1. 装备词条（同玩家解析，存怪自己的 equipment 字段）
```python
boss["equipment"] = {"armor": {"affixes": ["thorns"], "quality": "blue"},  # 反伤
                     "boots": {"affixes": ["dodge"], "quality": "blue"}}    # 闪避
```
词条 ID 见 `game/data/affixes.py`（stat 型 thorns/dodge/block/phys_reduce 等 41+）。

### 2. 引用玩家技能（关键——直接放玩家技能 key，走完整玩家管线）
```python
boss["skills"] = ["sk_hui_kan",       # 战士挥砍（exprs 成长 + mech 战意叠层）
                  "<牧师治愈术key>",   # 治疗（heal_formula 自疗）
                  "sk_tie_bi",        # 铁壁 buff（reduce 45% 减伤）
                  "召唤骷髅",          # 召唤援军（分支技能 key 是中文名）
                  "<AOE技能key>"]      # AOE
```
- 技能 key 全局唯一：基础职业用 sk_xxx ID；分支技能用中文名（唤火/召唤骷髅等）
- 查表 `E.skill_by_key(key)` 已覆盖基础 + 分支 + 导师 305 技能
- 施放走**完整玩家管线**：exprs 成长（skill_lv≈怪lv/2 折算）、mech 叠层、cond 条件、多段、暴击、元素、标记全语义

### 3. 资源（resource_def，内联 dict 或引用 CORE key）
```python
boss["resource_def"] = {"key": "rage", "name": "狂怒", "max": 10, "on_hit": 1}
# 或引用玩家定义: "resource_def": "rage"
boss["resources"] = {}  # 随战斗存这里
```

### 4. 防御/受击（字段即能力）
```python
boss.update({
    "dodge": 0.15, "block": 0.10, "phys_reduce": 0.10,   # 防御字段（_enemy_stats 读）
    "shields": {"boss": {"value": 2000, "halve": True}},  # 护盾 dict（halve=受伤减半）
    "on_taken": {"heal": {"pct": 0.02},                   # 受击回血
                 "atk_up": {"pct": 0.10, "turns": 2},      # 受击激怒
                 "shield": {"pct": 0.05}},                 # 受击凝甲
    "buffs": {}, "resources": {}, "stacks": {},           # actor 状态（都在自己 dict 上）
})
```

### 5. 怪物自家技能（MONSTER_SKILLS）增强字段
```python
# game/data/monsters.py 技能可加:
"res_gain": {"rage": 2},    # 命中攒资源（AI 会优先放攒资源的）
"res_cost": {"rage": 10},   # 施放门槛（资源不足回落普攻/其他技）
```

## 关键引擎 API（新会话可能用到）
- `E.skill_by_key(key)` / `E.skill_owner_cls(key)`：玩家技能全局查表
- `battle._lookup_skill_info(key)`：统一查表（先怪表后玩家表）
- `_cast_ctx` / `_target_ctx`：施法/目标 actor 上下文（玩家技能管线双向）
- `_res_gain(actor, key, amount)`：资源一套（玩家/怪同函数）
- `_deal_hit(dmg, logs)`：伤害落点双向
- `_monster_cast_playerskill(unit, skill_name, player, ev)`：怪物施放玩家技能入口

## 怎么把 Boss 装进游戏
1. **野外 Boss**：`game/data/monster_mods.py` 加条目（mech/ai/on_taken/resource_def/dodge/equipment 等扩展字段）+ 地图怪物引用
2. **副本 Boss**：`game/data/instances.py` 条目（Boss 配置覆盖）
3. **验证**：
   ```bash
   python tests/test_numeric_engine_generic.py   # 引擎通用性 10 项矩阵
   python scripts/run_numeric_tests.py            # 40 门禁全绿
   python scripts/refactor_regression.py --compare docs/refactor_baseline_v176.json  # 回归一致
   ```
   或写 playtest 模拟（参考 tests/test_numeric_actor_ontaken.py / _equip / _playerskill）

## 铁律
- 旧 205 怪物技能零改动兼容（新字段缺省不启用）
- 数值不许拍脑袋：新 Boss 数值过 numeric 门禁，战斗模拟验证（numeric_lib/battle2.py）
- 改动跑 40 门禁 + 回归 + 双仓提交（代码仓 dragonfall / 策划案仓 design/new_world）
- 设计 Boss 前先出策划案 → 同步 design/new_world/（独立 git 仓）

## 历史提交（v177 全程）
B1 怪物防御字段透传 → B2a 护盾统一 → B2b 承伤 _damage_actor → B3 资源一套化 → B4 技能资源接线 → B5 承伤回调化 → B6a 装备词条 actor → B6b/c 玩家技能引用(伤害/治疗) → B7 施法者路由+buff actor化 → B8 管线双向 → B8b 通用性门禁
