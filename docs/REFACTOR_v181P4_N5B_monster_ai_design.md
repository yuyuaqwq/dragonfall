# REFACTOR_v181P4_N5B_monster_ai_design：通用怪 AI 决策器设计（条件优先级表）

> 状态：待鱼鱼审查（2026-09-09）
> 背景：battle2 怪行动 = actor_auto 读 actor.auto_act（单招固定或普攻），无决策；
> 旧引擎 ai 字段（MONSTER_MODS 21 boss 带 skill_chance/weights）battle2 无人消费。
> 本文把"每刻出什么招"做成**纯数据通用决策器**（引擎零游戏知识），
> 与 5c 导演（boss_script.py，战斗级编排）分层收敛。
> 形态：条件优先级表（rule-based / 极简 utility），不用 FSM/行为树——理由见 §0。

## 0. 为什么不用 FSM / 行为树

| 形态 | 结构 | 这套怪 AI 的问题 |
|---|---|---|
| FSM 状态机 | 状态+事件+转移表 | 怪决策是"瞬时的条件判断"不是持续状态；Boss 阶段已由 phases 血量阈值天然表达，再建模状态=双份维护；转移逻辑会代码化，违反数据驱动 |
| 行为树 BT | 选择/序列/条件节点树 | 没有子行为可复用组合（不是地图级行为编排）；等效条件树多一层结构无新能力；节点实现成本高 |
| **条件优先级表** | 有序 moves：{when 守卫 → then 动作} | 阈值/节奏/条件触发正是战斗决策的天然形状；纯数据、可读、可演进 utility 打分 |

→ 战斗内招式选择用条件表；地图级行为（巡逻/警戒/仇恨切换）若将来要做另立 BT/FSM（不同层，不冲突）。

## 1. 目标 / 非目标

**目标**：任何 actor（小怪/精英/Boss/召唤物/宠物）都能用同一套数据驱动决策器决定每刻动作。
**非目标**（标注依赖）：
- 地图级行为（巡逻/索敌/逃跑路径）→ 地图 AI 层（未来）
- Boss 战斗级编排（转阶段演出/召唤节奏/连招链）→ 已由 5c 导演完成，本批只做对接不重写
- 多目标战术权重（utility 打分完全体）→ 本批 weighted 已铺路，将来换选择器即可

## 2. 现状盘点

| 项 | 现状 | 出处 |
|---|---|---|
| 怪行动 | actor_auto 读 actor.auto_act（act.type/skill），缺省普攻 | battle2/battle.py:222 |
| 导演挂钩 | script_hook 行动帧前置（演出刻 skip/换招），on_event 观察者 | 5c boss_script.py |
| 旧 ai 数据 | MONSTER_MODS ai: {skill_chance: 0.6, weights: {技能: 权重}}，21 boss 带 | game/data/monster_mods.py |
| 行动计数 | 导演 bs.round_no（Boss 行动帧）——个体决策不应依赖 st | 本批引入 actor.act_count |
| 技能冷却 | actor.cooldown 容器（V 系列持久化） | battle2 actors.py |

## 3. 数据模型（actor.ai，纯数据，引擎零名词）

```python
actor["ai"] = {
  "select": "priority",          # priority=条件表 | weighted=权重随机
  "fallback": {"type": "attack"},# 无命中回落
  "moves": [
    {
      "when": {"self_hp_lt": 0.30},           # 守卫（多个=AND，缺省=恒真）
      "then": {"type": "skill", "skill": "ms_xxx"},
      "weight": 4,                            # select=weighted 时用
    },
    {"when": {"round_mod": [5, 0]}, "then": {"type": "skill", "skill": "ms_yyy"}},
    {"when": {"hostile_lowest_hp_lt": 0.30}, "then": {"type": "skill", "skill": "ms_zzz"}},
  ],
}
```

### 3.1 守卫谓词集（引擎通用词汇 v1，全部数值比较）

| 谓词 | 语义 | 例子 |
|---|---|---|
| `self_hp_lt` / `self_hp_gt` | 自身血量比例 < / > | {"self_hp_lt": 0.30} |
| `hostile_lowest_hp_lt` | 敌对侧存活最低血量比例 <（残血追击） | {"hostile_lowest_hp_lt": 0.30} |
| `round_mod` | actor.act_count % N == R（行动节奏） | {"round_mod": [5, 0]} |
| `cd_ok` | 技能不在冷却（actor.cooldown 表） | {"cd_ok": "ms_xxx"} |
| 缺省 | 恒真（优先无条件招） | {"when": {}} |

> 引擎不认识技能名词：谓词只做数字比较 + cooldown 查表；"打谁"仍走 target_picker（5b 仇恨已有）。

### 3.2 选择器

- **priority**：moves 从上到下第一个 when 全满足 → then。确定性战术（可读招）。
- **weighted**：命中的 moves 按 weight 随机一个；skill_chance 语义 = 命中概率用技能、否则 fallback（旧 ai.skill_chance 翻译）。
- 未来 utility：weighted 升级"算分取最高"（表结构不变）。

## 4. 引擎改动（battle2/battle.py actor_auto，≈60-100 行，纯数据）

决策顺序（优先级从高到低，互不打架）：

```
1. script_hook 演出刻（导演）→ skip 本帧          [已有]
2. actor.auto_act 显式指定 → 用之（导演换招/连招链/装配指定） [已有]
3. actor.ai 决策器 → 从 moves 选                  [本批新增]
4. 普攻兜底                                        [已有]
```

- actor_auto 内：无 auto_act 且 actor.ai 存在 → `resolve_ai_move(battle, actor)` 选动作 → ActCtx
- 每次 actor_auto 行动后 `actor["act_count"] += 1`（序列化落盘，个体行动计数；导演 bs.round_no 保持 Boss 帧语义不动）
- `resolve_ai_move`：谓词评估（纯函数，无副作用）→ 选择器 → 返回 then 动作 dict
- 冷却记录：then 的 skill 行动后照常写 actor.cooldown（引擎已有动作后冷却逻辑？若无 → 装配层记录，P2 盘点）

## 5. 迁移翻译器（MONSTER_MODS ai → actor.ai）

- 位置：game/services/battle2_bridge.py monster_to_actor 尾部（桥已有透传段）
- 翻译规则：
  - ai.weights（技能→权重 map）→ weighted moves：when={}，then=skill，weight=原值
  - ai.skill_chance（0-1）→ weighted 模式命中概率：chance 高 → 用技能概率；低 → fallback
  - 无 weights 只有 skill_chance → 简单二选（技能/普攻）
- 结果：21 boss + 普通怪 weights 全活，战斗不再只会普攻

## 6. 导演收敛路径（本批只对接，不重写）

- 导演写 actor.auto_act（转阶段换招/连招链）= 决策顺序第 2 层 → 天然压过个体 ai
  （Boss 进阶段必须用新招时不会被 weights 盖掉）✓ 无冲突
- Boss 想保留招式多样性（无导演显式招时按 weights 轮换）→ 导演不写 auto_act 时
  actor.ai 生效 → 两者自由组合
- 连招链 chains 已按 seq 写 auto_act（确定性剧本），与 AI 正交

## 7. 批切方案（每批独立验证 + commit）

| 批 | 内容 | 引擎改动 | 验证 |
|---|---|---|---|
| P1 决策器 | actor.ai 数据 + priority/weighted + 谓词集 + act_count 计数 + resolve_ai_move | 是（battle2 actor_auto） | 单测：priority 命中顺序/谓词组合/weighted 分布/cd_ok/回落链 |
| P2 翻译器 | bridge ai 翻译 + 真实怪抽查（带 weights 的怪战斗输出多样性） | 否 | battle2 全套 + 真实战斗多样断言 |
| P3 对接 | 导演 + AI 共存验证（Boss auto_act 压 AI / 无 auto_act 走 AI） | 否 | 5c e2e 回归 + 新增共存用例 |

## 8. 验证策略

1. 单测（test_monster_ai_p1.py 起）：构造手写 actor.ai 断言选择结果；weighted 采样分布
   （容差断言，防随机脆弱）；cd_ok 冷却内不选；hostile_lowest 追击。
2. 全量回归 341 = 316/25 基线逐条对照零新增。
3. 数值门禁 scripts/run_numeric_tests.py 全绿（伤害/节奏涉及）。
4. 5c e2e 不回归（导演优先级不变）。

## 9. 风险与边界

- **谓词集别膨胀**：v1 五条覆盖现状；新游戏语义先问"能不能组合现有谓词"，别为单只怪加谓词
  （引擎通用词汇纪律——加一个谓词 = 所有怪都多一个能力维度，要全局评估）。
- **随机确定性**：weighted 用 random 会打乱全量回归随机序列（测试确定性铁律 v103）——
  单测里 seed 固定/直测分布；战斗随机性已有先例容差处理。
- **冷却记录**：battle2 技能冷却消费点若不存在 → P1 盘点后决定放引擎动作后（引擎已有
  cooldown 容器）还是装配层（倾向引擎动作后统一记录，与 effects 同构）。
- **旧引擎 ai 语义核对**：skill_chance/weights 旧消费在 battle.py 敌方行动段（N10 删除
  对象）——翻译前逐条核对旧行为（chance 是"用技能概率"还是"每刻重掷"）。
- 与 N10 关系：battle_mech/battle.py 的怪 AI 消费段删旧前必须先落本批翻译器，
  否则 21 boss ai 字段随删旧变死数据（同 weapon/affix 前置纪律）。

---

## 附：已核实事实

- MONSTER_MODS 21 boss 带 ai 字段（skill_chance + weights 形态），battle2 无人消费。
- actor_auto 现决策 = auto_act 单招 / 普攻；导演 script_hook 在其前置（演出刻 skip）。
- actor.cooldown 容器随 V 系列持久化存在；技能冷却写入点在装配/翻译层（P1 盘点）。
- 5c 导演换招写 actor.auto_act（Boss 用）；AI 决策器第 3 层 → 天然不冲突。
- battle2 EVENTS 已有 on_taken/on_death 等事件可做"反应型 AI"扩展（观察者），
  本批不做（P1 先做主动决策，反应型 AI = 未来 triggers[event] 装配扩展）。
