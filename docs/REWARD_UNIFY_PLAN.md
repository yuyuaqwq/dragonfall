# 奖励系统统一抽象方案（REWARD_UNIFY）

> 状态：方案设计（待鱼鱼拍板） ｜ 2026-09-04
> 触发：鱼鱼「扫码项目看还有哪些掉落类（交互等）——是不是可以抽象成奖励表，只要是发奖就走这个」

## 一、现状扫描结论（全仓 174 py 审计）

发奖/掉落点遍布 **25+ 文件、10+ 种结构**，但本质都是同一组动作：

| 动作 | 现有表达（字段名五花八门） |
|---|---|
| 加经验 | `reward_exp` / `give_exp` / `{"exp": N}` |
| 加金币 | `reward_gold` / `give_gold` / `sign_gold` / `{"gold": N}` |
| 给物品 | `reward_item`(单/列表) / `give_item:{key,count}` / `items:{key:count}` |
| 给装备 | `reward_item="eq:xxx"` 前缀 / 各掉落池 |
| 给宠物/坐骑 | `reward_pet` / `reward_mount` / petegg: 池 |
| 给称号/属性 | collection `{title, bonus}` / achievements `points` |

**发放代码也重复**：任务 `_grant_quest_rewards`、成就 `claim_achievement_rewards`、对话 `action_give_*`、
收藏 `_claim_book_reward`、签到、周常、爬塔……各写一份"加 exp+金币+升级结算+物品入包+文案"。

### 已统一（v174 完成 ✅）
- **掉落池（概率发奖）**：DROP_POOLS + drop_engine——采集/挖掘/垂钓/副本Boss/精英/战利品堆/暗格宝箱

### 待统一（本次方案）
- **确定奖励（非概率）**：任务/成就/收藏/对话/NPC/签到/周常/爬塔/宝箱内容

## 二、设计目标

### 统一奖励数据格式（REWARD dict）
所有"发确定奖励"的来源收敛成同一结构：

```python
REWARD = {
    "exp": 1000,                      # 经验（触发升级结算）
    "gold": 500,                      # 金币
    "items": [{"item": "mat_x", "n": 3}],    # 物品/材料（key 兼容中文名/ID）
    "equips": [{"rid": "eq_x"}],      # 名册装备（或 item="eq:xxx" 兼容旧）
    "pets": ["pet_x"],                # 宠物蛋
    "mounts": ["mount_x"],            # 坐骑缰绳
    "title": "称号",                  # 称号
    "stats": {"atk": 2},              # 属性/词条（收藏 bonus 类）
    "buff": {"stat": "atk", "mult": 1.1, "left": 5},   # 限时 buff
    "chest": "i_chest_wood",          # 开箱（等价于掉 DROP_POOLS 池）
}
```

### 统一发放器 `grant_reward(reward, group_id, qq_id, *, player=None) -> list[str]`
一个函数处理所有类型：加 exp（含升级结算）→ 加金币 → 物品/装备/宠物/坐骑入包 →
称号/属性/buff 应用 → 返回文案行。**消灭 8 处重复的"加经验金币+升级+入包"代码**。

### 所有来源数据统一到一张奖励配置表
```python
REWARD_TABLE = {
    "quest:q1_1":    {"exp": 100, "gold": 50, "items": [...]},
    "ach:first_kill": {...},
    "collect:fish_1": {...},
    "npc:oak_elder:thanks": {...},   # 对话节点奖励
    "sign:day1": {...},
    "weekly:w1": {...},
    ...
}
# 数据来源（quests.py/achievements.py/collection_book.py/dialogues.py/...）
# 各自的 reward 字段 → 生成器收敛进 REWARD_TABLE（保留旧字段兼容）
```

## 三、分步计划（每步跑全量回归）

1. **核心 grant_reward**：新建 `game/core/reward.py`——统一发放器 + 全类型支持 + 文案
2. **格式规约文档**：REWARD dict 字段规范（docs/REWARD_FORMAT.md）
3. **接入第一批**：成就（claim_achievement_rewards 改调 grant_reward）→ 任务（_grant_quest_rewards）
   → 对话（action_give_*）
4. **数据收敛生成器**：把 quests/achievements/collection/dialogues 的奖励字段标准化（保留旧字段，
   生成器产出统一 REWARD 视图，老测试不破坏）
5. **接入第二批**：收藏/签到/周常/爬塔/宝箱内容
6. **门禁**：`test_numeric_reward_unify.py`——每个来源的奖励能正常发放、升级结算、物品入包
7. **全量回归 + 策划案同步 + 双仓提交**

## 四、收益
- "发奖"一词一条路：数据统一格式 + 发放统一函数，新增奖励 = 加一行配置
- 消灭 8+ 份重复发放代码（升级结算漏写/物品发放失败吞错这类 bug 不再各犯一次）
- 成就/任务/对话奖励可审计、可统一调数值

## 五、边界与风险
- **触发条件不统一**（成就判定/任务提交/对话节点/集齐检查）——统一的是"发奖动作"，不是触发
- 掉落池（DROP_POOLS）已是概率系统，与确定奖励本质不同 → 不合并，但 chest 型奖励可引用池
- 存量数据多（几百条任务/成就/对话），用**兼容视图**收敛，不物理改老数据（防 245 测试大改）
- 部分来源有特有副作用（任务解锁职业/声望、对话 set_flag）——留在调用方，grant 只发奖励

## 六、需鱼鱼确认
1. 这个分层（统一 REWARD 格式 + grant_reward + 数据收敛视图）OK？
2. 范围：先做核心 grant + 第一批接入（成就/任务/对话）？还是等全量？
