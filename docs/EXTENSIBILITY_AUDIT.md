# 《剑与魔法》可扩展性审计报告（2026-08-10）

> 目的：全面体检各模块"加内容是否要改代码"，为千元素工程（v2.0）提供改造路线图。
> 方法：逐模块检查分发逻辑（if-elif 硬编码 vs 数据驱动 vs 声明式）。

---

## 一、总体评价

**架构骨架是健康的**：data（纯数据）/ core（纯逻辑）/ store（纯 IO）/ commands（薄层）四层单向依赖，
数据层 95% 是纯 dict，无 IO 无逻辑——这是千元素工程能成立的前提。

**核心矛盾**：**"加内容"容易（数据层加 dict），"加行为"难（效果/事件类型要改代码）**。
全项目 ~250 处 if-elif 硬编码分发，其中大部分是"内容行为"入口——加一种新玩法就要动命令层。

---

## 二、模块扩展性评分表

### ✅ A 级：数据驱动（加内容 = 加 dict，零代码）

| 模块 | 现状 | 证据 |
|---|---|---|
| 地图/子区域 | 116 图 / 347 子区域纯数据 + build_index 自动索引 | maps.py / subareas.py |
| 怪物 | 299 种 6 元组纯数据 | monsters.py |
| 装备 | 112 件 + 词缀池 + 品质表，generate_equip 通用生成 | equip_roster.py / core/drops.py |
| 材料/物品 | 459 材料 / 522 道具纯数据 | items.py |
| 采集池 | 68 野外图专属池（v97.2） | economy.py _GATHER_MAP_POOLS |
| 钓鱼 | 11 钓点 / 23 鱼纯数据 | fishing.py |
| 配方 | 锻造 87 / 炼金 16 / 附魔 7 纯数据 | craft.py / alchemy.py / enchant.py |
| NPC 对话 | 对话树 + **声明式 action**（apply_talk_action 统一落地） | dialogues.py / core/dialogue.py |
| 隐藏怪物 | cond/chance/drops 纯数据（v87 设计标杆） | hidden_monsters.py |
| 套装 | bonus_2/4/5 声明式属性加成 | sets.py |
| 世界 Boss | 纯数据 + mech 字段 | world.py |
| 方碑 | 纯数据 | portals.py |
| props | 纯数据 texts/effect | props.py |

### ⚠️ B 级：半数据（数据表 + 少量固定类型分发，可接受但有限制）

| 模块 | 现状 | 限制 |
|---|---|---|
| 技能 | 数据表 + `kind`（治疗/增益/嘲讽/物理/魔法）+ `mech` 机制字段 | 加**新种类**技能要改 battle.py；加同 kind 技能是纯数据 |
| 任务 objective | 5 种固定类型：kill/collect/explore/find/talk | 加**新目标类型**要改 world.py 进度检查 + 文案 |
| 成就 | 数据表 + cond_met 35+ 类型 if-elif | 加**新条件类型**要改 core/achievements.py |
| 世界事件 | WORLD_EVENT_POOL 数据表 + `type` 分发（auction/boss 有执行，其余仅广播） | 加**新事件类型**要改 social.py |

### ❌ C 级：硬编码（加内容必须改代码——千元素工程的死敌）

| 模块 | 现状 | 严重度 |
|---|---|---|
| **探索事件/彩蛋** | combat.py **85 处 if-elif**，12+5 事件 id 全硬编码 | 🔴 最严重 |
| **道具使用效果** | economy.py `effect == return_vila/lucky/clear_red/open_chest...` 硬编码 | 🟠 严重 |
| **怪物 cond 条件** | combat.py cond == forest/water/ruin/night_any/forest_night 硬编码 | 🟡 中 |

---

## 三、五大病灶详解

### 病灶 1：探索事件/彩蛋 if-elif（🔴 最优先）

```python
# combat.py _handle_explore_event：400-640 行
if eid == "treasure": ...
if eid == "merchant": ...
if eid == "spring": ...
if eid == "trap": ...
# ... 12 个常规事件 + 5 个彩蛋，全是 if-elif
```
**后果**：加 1 个事件 = 改代码 + 加测试 + 回归。千元素 = 千个分支 = 灾难。
**方案**：v2.0 事件模板引擎（12 种模板注册表 + 数据驱动事件 dict）——**v97.3 已排期**。

### 病灶 2：道具使用效果 if-elif（🟠 高优先）

```python
# economy.py use_item：~2500-2585
if d.get("heal"): ...
elif d.get("mana"): ...
elif d.get("stamina") is not None: ...
elif d.get("effect") == "return_vila": ...
elif d.get("effect") == "lucky": ...
elif d.get("effect") == "clear_red": ...
elif d.get("effect") == "open_chest": ...
```
**后果**：策划案阶段六的 30 件彩蛋物品（月光酿/虎斑铃铛/星尘角笛……）每个都要新 effect = 每个都要改代码。
**方案**：道具效果模板化——`effect: {"type": "heal", "pct": 0.5}` / `{"type": "buff", "key": "lucky", "dur": 600}` /
`{"type": "loot_table", ...}` 声明式，统一 use_effect 解释器（与事件模板同构）。

### 病灶 3：怪物 cond 条件硬编码（🟡 中优先）

```python
# combat.py 275-287
if cond == "forest_night": ...
elif cond == "forest": ...
elif cond == "water": ...
elif cond == "ruin": ...
elif cond == "night_any": ...
```
**后果**：策划案想加 `weather: rain` / `weekday` / `world_event` 条件 = 要改代码。
**方案**：cond 改为声明式 dict：`{"map_type": "forest", "time": "night", "weather": "rain"}`，
统一条件解释器（core/cond.py），与规则系统共用。

### 病灶 4：成就条件 cond_met if-elif（🟡 中优先）

35+ 类型虽然多，但成就系统相对稳定（加成就=加数据，加类型很少发生）。改造成注册表（dict type→函数）
成本低收益稳，建议顺手做。

### 病灶 5：世界事件 type 分发（🟡 低优先）

当前仅 auction/boss 有执行逻辑，merchant/omen/swarm/festival 只有广播 desc。等 v2.0 事件模板化后
世界事件也走模板（T9/T10 模板天然支持），无需单独改造。

---

## 四、统一改造原则（与 v2.0 策划案对齐）

1. **行为声明式化**：一切"效果"写成数据（`{"type": ..., "params": ...}`），解释器只有一个
2. **注册表模式**：`TYPE_REGISTRY = {"heal": fn, "buff": fn, ...}`，新类型 = 注册一个函数（~20 行）
3. **条件 DSL 统一**：core/cond.py 一个解释器服务所有系统（事件/规则/隐藏怪/道具）
4. **先搬家后扩容**：改造期行为 100% 不变（老数据搬进新格式），全量回归兜底
5. **校验自动化**：启动时检查模板 id/材料/地图/权重/文案，幽灵引用直接报错

## 五、改造路线图（并入 v2.0 版本规划）

| 版本 | 内容 | 消灭的病灶 |
|---|---|---|
| v97.3 | 事件模板引擎（12 模板注册表 + 老事件搬家） | 病灶 1（探索/彩蛋） |
| v97.5 | 行为规则引擎（cond.py 条件解释器落地） | 病灶 3 + 规则系统 |
| v98.x | 道具效果模板化（use_effect 解释器） | 病灶 2 |
| v98.x | 成就条件注册表化 | 病灶 4 |
| 随行 | 世界事件走模板 | 病灶 5 |

**改造完成后**：千元素工程的 824 元素 100% 纯数据落地，未来任何新玩法 = 注册模板函数 + 填数据。
