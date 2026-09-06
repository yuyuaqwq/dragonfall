# v180F 战斗引擎完全 actor 化重构设计（v2.0——通用阵营架构）

> 状态：设计定稿（鱼鱼 2026-09-07 拍板：引擎要能支持任意 actor 对阵，如怪vs怪/随从vs怪，玩法入口以后再说）
> 哲学锚点：**战斗引擎必须完全 actor 化——不假设有"玩家"。**
> 任意 actor 集合按阵营排布、按 ct 行动，直到一方全灭。谁操作/谁 AI 只是行动来源。

---

## 〇、为什么不是"party actor 化"而是"通用 actor 化"

v1.0 设计的 `self.party`（玩家侧统一数组）仍隐含"战斗分玩家侧/敌方侧"。
鱼鱼追问"如果一场战斗没有 player 呢？两个怪物对打？"——暴露了更深的问题：
**引擎不该写死"玩家中心"**。

现在引擎的"玩家中心"假设（侦察确认）：
1. `self.player` 焦点玩家 + `self.allies` 队友 → "玩家侧"
2. `self.enemies` → "敌方"
3. 行动驱动：玩家 = 外部指令（player_turn 同步调用），怪物 = 内部 AI（事件驱动）
4. 胜利/失败判定：玩家全灭 = defeat，敌方全灭 = victory
5. 承伤/治疗/挡刀已 actor-agnostic 大半（v180 系列成果），但行动调度、目标选择、
   战斗结局仍绑"玩家 vs 怪"二元

**通用 actor 引擎目标**：以上全部不假设"哪方是人类"。

---

## 一、目标架构（通用阵营）

```
Battle:
  self.sides: dict[str, list[actor]]
      # 常规 = {"player": [...], "enemy": [...]}
      # 怪vs怪 = {"enemy_a": [...], "enemy_b": [...]}
      # 随从vs怪 = {"player": [随从...], "enemy": [...]}（无真人玩家）
  actor = {side, kind(player|monster|pet|summon), uid, rank, ct, hp, ...,
           control: "human"|"ai", ai: {...}}
  self.focus: actor | None   # 当前行动者（任何阵营成员）
```

**核心机制**：
1. **所有 actor 统一入 `self.sides`**（不再有 player/allies/enemies/companions 四容器）
2. **行动调度统一 CTB**：所有 actor 按 ct 选下一个行动者（无玩家中心）
3. **行动来源**：actor 声明 `control`——human 等外部指令、ai 走内部 AI（现有 `_enemy_turn` 逻辑泛化）
4. **目标选择**：阵营间敌对关系由 `side` 决定（不是写死"打玩家"）
5. **战斗结束**：某阵营全灭（可多阵营混战，全部只剩一方存活）
6. **结算通用**：承伤/治疗/挡刀/增益/DOT 已 actor-agnostic，全部以 actor dict + side 字段结算

---

## 二、与现状的差距（改造清单）

### 数据容器层（最大）
| 现状 | 目标 | 改动 |
|---|---|---|
| self.player + self.allies | sides["player"]（可空） | 98+16 处引用 → sides/焦点 |
| self.companions | sides["player"] 里 kind!=player 的 actor | 17 处 → sides |
| self.enemies | sides["enemy"] | 已近数组，改 sides |
| self.summons（property） | 删除（扫 sides） | 7 处 |
| self.pet | sides["player"] 里 kind==pet 的 actor | 13 处 |
| `_p_*` 252 处读 self.player | 读 focus（当前行动者，任意阵营） | 252 处 helper 收口 |

### 行动调度层
| 现状 | 目标 |
|---|---|
| 玩家 = player_turn 同步调用 | 统一：任意 focus 行动者，human 来源等外部指令 / ai 来源走 AI |
| 敌方 = 事件队列 enemy_act | 事件队列本来就是 actor 通用的，泛化触发条件 |
| `_after_actor_ct(side)` 写 p_ct/e_ct | 写 actor["ct"]（所有 actor 一样） |

### 战斗流程层
| 现状 | 目标 |
|---|---|
| defeat = 玩家死 / victory = 敌死 | 结束 = 某阵营全灭（记录胜方阵营） |
| `_pick_enemy_target` 从 allies 选人打 | 通用：side B 的 actor 从 side A（敌对阵营）选目标 |
| 治疗 b<N> 走 allies | 治疗目标 = 同阵营 actor（编号/uid） |
| 挡刀读 companions + self.player | 挡刀 = 受击者同阵营的 guard actor（按 owner） |
| `_damage_enemy`/`_damage_player` | `_damage_actor`（已存在！统一收口） |

### 序列化层
| 现状 | 目标 |
|---|---|
| to_state 单焦点扁平顶层键 | sides 数组按 actor 各自状态序列化（旧档兼容读） |
| _restore_pstate 单份 | 废弃（actor 状态直接携带） |
| tick_effects actor_ref="player"/"pet"/uid | actor_ref 泛化（side+uid/idx） |

---

## 三、分期实施（每步全量回归绿，最终形态无兼容残留）

鱼鱼拍板：**一次性改完不中间提交**。但改动横跨 battle.py 万行 + instance + 测试，
实施顺序按依赖（避免半成品态）：
1. **sides 数组建立**：__init__ 装配 sides，player/allies/companions/enemies 变派生视图（中间态）
2. **helper 收口**：`_p_*` → `_actor_*(actor)`；focus 语义化
3. **承伤链修复**：5 函数读 actor 自身袋（不读焦点）
4. **随从 owner**：装配落 owner，挡刀/宠物行为按 owner
5. **行动调度统一**：focus 泛化 + AI/人类行动来源
6. **序列化重写**：sides 落档 + 旧档兼容读
7. **战斗流程**：结局判定/目标选择/治疗/挡刀全走 side
8. **instance/combat 命令层适配**
9. **测试迁移 + 门禁**

---

## 四、风险与对策

| 风险 | 对策 |
|---|---|
| 改动横跨万行，中间态不可运行 | 依赖顺序推进，每步是"当前架构可运行 + 渐进替换"，非半成品 |
| 566 测试全绑 player 构造 | conftest 工厂 + 分文件迁移；构造签名最终改 sides |
| 副本重建 Battle 模式 | sides 装配替代 st.players；`_load_player_state` 语义退化 |
| 战斗结局语义变化 | 保留 result 兼容值（victory/defeat）+ 新增 winner_side |
| 怪 vs 怪 AI 互相打 | `_enemy_turn` AI 逻辑泛化（现在假设打玩家侧） |

---

## 五、验收

- 任意 actor 对阵可构造：Battle(sides={"a": [...], "b": [...]})
- 全量回归绿（含全部现有玩法：野外/副本/PVP/宠物/随从）
- 新门禁：怪vs怪能跑完（AI 互打）、随从单挑怪、无玩家战斗正常结束
- grep 断言：self.player/self.allies/self.companions/self.enemies 无新增（或仅派生视图）
