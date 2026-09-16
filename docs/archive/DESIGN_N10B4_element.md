# N10-B4：element 元素伤害 + 免疫/弱点消费（G1）——设计文档

> 状态：待鱼鱼审查（2026-09-09）
> 依据：docs/archive/REFACTOR_v181P4_N10B_gap_fill.md §1 G1 行 + 主 agent 侦察
> 铁律：引擎零游戏知识（元素名 = 技能数据字段/kind 前缀推导，引擎只做查表）；
> 行为对齐旧引擎 _hostile_mitigate 元素段；范围聚焦 Boss 机制（蚀夜/冰霜领主等）。

---

## 1. 问题（侦察实锤）

| 项 | 现状 |
|---|---|
| 玩家元素技能 | 7 个 kind=魔法·火/冰/雷（火球术/陨石术等，cls_fa_shi）——battle2 能打（kind≠物理/真伤 → magi 段）但 **element 标签不携带** |
| 怪技能元素 | monsters.py ms_* 大量带 element 字段（fire/ice/thunder/dark/holy/abyss）——bridge 透传 actor 但 battle2 无人读 |
| 敌方免疫/弱点 | 数据已配：b_eter（蚀夜真相形态）element_weak holy×1.15、b_frost_lord（冰霜领主）element_weak fire×1.5；蚀夜 phases 描述"用火系输出/护体期"；**battle2 landing/actions 零消费** |
| battle2 引擎 | actions/landing/state_effects element=0、immune=0（grep 实锤） |
| bridge | monster_to_actor 已透传 element_immune/element_weak/dmg_taken_mult（无人读） |

**玩家可见影响**：元素法师火球打冰霜领主不触发 ×1.5 弱点；蚀夜真相形态 holy 弱点/火免疫不生效；"读形态换克制"核心玩法在 battle2 断裂。

## 2. 旧引擎语义（语义参考，N10 删 battle.py）

### 2.1 元素来源
- 技能数据 `info.element`（怪技能 ms_* 已带；玩家技能走 kind=魔法·火/冰/雷）
- 旧引擎 kind=魔法·火 技能的 element 推导：`kind` 含"火"→fire / "冰"→ice / "雷"→thunder
  （旧 _skill_seg_damage/_hostile_mitigate element 参数链）

### 2.2 免疫/弱点消费（battle.py:8421-8470 _hostile_mitigate 元素段）

```
dark 元素（∉ ELEMENT_MARKS）：target.element_immune 含 dark → 伤害归 0
ELEMENT_MARKS 系（fire/ice/thunder）：
  - target.element_immune 含 element → 免疫：伤害归 0（文案 💠 免疫）
  - elem_res 元素抗性（≤50%）→ 魔法段减免
  - target.element_weak[element] = 倍率（>1）→ 额外增伤
弱/免疫表在怪 dict（element_immune/element_weak）——bridge 已透传 actor
```

### 2.3 ELEMENT_MARKS / 印记系统（不迁，见 §6 边界）

engine.ELEMENT_MARKS = {fire: fire_mark, ice: ice_mark, thunder: thunder_mark} ——
元素法师职业资源（同系连发叠印记/反应），属职业机制 → 上层职业批，B4 不碰。

## 3. battle2 落点设计（最小通用）

### 3.1 element 解析 helper（命令层 bridge 或 actions 内，数据驱动）

```python
# actions.py 新增（对齐旧 kind 前缀推导；引擎零名词——只做"kind 字符串前缀"判断？
# 不——引擎不该知道"火=fire"。更干净：数据层补 element 键，kind 前缀推导放翻译层）
```

**决策点（需鱼鱼拍板）**：
- 方案 A（数据补键）：给 7 个玩家元素技能数据加 `element` 字段（fire/ice/thunder），
  引擎/actions 只读 info.element（零名词）。怪技能已有 element ✓。改动 = 7 行数据。
- 方案 B（kind 前缀推导）：actions 内"魔法·火→fire"硬映射。引擎开始认元素中文 → 违背北极星。

→ 推荐 **方案 A**（数据补键，引擎零知识；kind=魔法·火 只是展示 kind，element 是机制键）

### 3.2 承伤侧消费（landing.deal_damage 或 actions 伤害管线）

```
_single_target_pipeline（actions）计算单段伤害时：
  1. element = info.element（缺省 "" = 无元素/物理）
  2. 落地前查 target（承伤方 actor）：
     - element_immune 含 element → 伤害归 0（免疫文案）
     - element_weak[element] > 1 → dmg ×= 倍率（弱点文案）
  3. 落点在 _skill_seg_damage 后 total 汇总处（同 B2 defend_reduce 模式）
```

位置选 actions._single_target_pipeline（AOE 逐目标也走这 → 天然覆盖）：
- 免疫 = 整段归 0 前 return（不落地）
- 弱点 = total × weak_mult

### 3.3 引擎改动清单（全部 actions.py，landing 零改动）

| 文件 | 改动 | 行量 |
|---|---|---|
| game/battle2/actions.py | _single_target_pipeline total 汇总后查 target element_immune/weak → 归零/乘区 | ~25 行 |
| game/data/skills.py | 7 个元素技能补 element 键（火球术/陨石术=fire 等） | 7 行 |
| game/battle2/__init__ 或 config | 无需（字段已在 actor/bridge 透传） | 0 |

## 4. 测试计划（tests/test_battle_n10_b4_element.py 新建）

| # | 场景 | 断言 |
|---|---|---|
| 1 | 火球术（element=fire）打冰霜领主（weak fire×1.5） | 伤害 ≈ 1.5×（对照无 weak 怪） |
| 2 | 火技能打 element_immune=[fire] 怪 | 0 伤害 + 免疫文案 |
| 3 | 无元素普攻打 weak/immune 怪 | 无影响（零行为） |
| 4 | AOE 逐目标各判免疫/弱点 | 每目标独立 |
| 5 | dot/环境伤无 element → 不触发 | 零行为 |
| 6 | dark/holy 非 ELEMENT_MARKS 系同样消费（蚀夜 holy weak） | ×1.15 |
| 7 | battle2 全套回归基线零新增 | 对照 |

## 5. B5 形态轮换（随 B4 验收）

烛影/蚀夜 phases 切换时更新 actor element_immune/weak——**数据已配在 phases 吗？查证后落**：
若 phases 内联 element_weak/immune → 导演 _check_phases 转阶段时同步改写 actor 字段；
若未配 → 登记文案缺口，B5 只做数据补配。依赖 B4 落地（element 有消费才谈形态差异）。

## 6. 边界（不做）

- **ELEMENT_MARKS 印记/元素反应/元素法师连发**：职业机制 → 上层职业批（battle_rules 无声明）
- **玩家侧元素抗性词条（elem_res/abyss_res）**：属词条战斗系统批，B4 只消费"敌方" immune/weak
- **battle2 其他战斗属性消费缺失**（侦察发现 phys_reduce/magic_reduce/block/dodge/tenacity
  在 stats.py 定义但引擎无消费点）——比 B4 更大的独立缺口，单列问题给鱼鱼（见 §7）
- 不动 landing 事件总线（dmg_calc/taken_calc 已有钩子，B4 用直读字段最简单）

## 7. 附带发现（侦察新缺口，待鱼鱼裁决）

battle2 stats.py 定义了 phys_reduce/magic_reduce/elem_res/block/dodge/tenacity 聚合字段，
但 **battle2 引擎伤害管线零消费**（只有定义无读点）——旧引擎这些是玩家/怪的减伤/格挡/闪避
乘区。若属实 = 玩家被打不吃物免/魔免/格挡/闪避、怪同理。**本批不顺手修**（范围大），
单列缺口：N10 后"战斗属性消费缺失批"（或确认装配层已通过 taken_calc 事件翻译覆盖——
需进一步核查，勿想当然）。
