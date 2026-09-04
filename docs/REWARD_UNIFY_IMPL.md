# 奖励系统统一抽象 v174 实施记录

> 状态：✅ 核心完成 ｜ 2026-09-04
> 方案：docs/REWARD_UNIFY_PLAN.md
> 触发：鱼鱼「扫码看掉落类——抽象成奖励表，发奖就走这个」

## 一、交付清单

### 1. 统一发放器 `game/reward.py`（game/ 顶层防循环 import）
- `grant_reward(reward, group, qq, *, player=None)`：统一发放入口
- 支持类型：exp(自动升级结算) / gold / items(物品材料,兼容dict和eq:前缀) / equips / pets / mounts / title / bonus
- `grant_items_batch(group, qq, {key:count})`：批量物品发放辅助（成就合并用）
- 🔴 关键 bug 修复：多动作连发（对话一次带 give_gold+give_exp+give_item）时传入旧 player 引用
  整段 update 会用旧 gold 覆盖前一动作已写库新值 → grant 内部每次读 DB 最新 player

### 2. 已接入来源（发奖走统一入口）
| 来源 | 接入 | 保留在调用方 |
|---|---|---|
| 成就 claim_achievement_rewards | 物品发放走 grant_items_batch（合并同key） | exp/gold 汇总+成就标记 |
| 任务 _grant_quest_rewards | reward_item/pet/mount/title 段走 grant_reward | exp/gold+升级+unlock_class |
| 对话 action_give_gold/exp/item | 全走 grant_reward | unlock_prof 拦截 |
| 周常 _grant_rewards | exp/gold 走 grant_reward | 达标判定 |

### 3. 门禁 tests/test_numeric_reward_unify.py（11 断言，入 run_numeric_tests）
全类型发放 / 多动作不覆盖 / 缺失不阻塞 / 空安全

**全量回归 246/246 + 数值门禁 23/23 全绿**

## 二、边界记录（诚实）

### 未接入（原因）
1. **收藏册 _claim_book_reward**：只发 chest 一个物品，改造收益小；title/bonus 是"实装新功能"
   （title_bonus() 动态计算需加"收藏册已集齐"源）——非纯重构，属后续功能开发
2. **签到(公会) 加金币**：单行 update_player，接入收益≈0（不消灭重复代码）
3. **野王宝箱 / 副本击杀 / 探索事件掉落**：概率掉落已走 DROP_POOLS，非确定奖励不并入 reward

### 设计结论（重要）
- **title_bonus 不落 players 表**：永久属性走 title_bonus() 动态计算（读 TITLES/ACHIEVEMENTS 已解锁），
  grant_reward 的 bonus 只播报不存储。收藏册 bonus 实装 = 让 title_bonus() 认识"收藏册集齐"
- **奖励 vs 掉落分离**：DROP_POOLS（概率发奖）与 REWARD（确定奖励）是两套，chest 型奖励可引用池
- **触发条件不统一**：统一的是"发奖动作"，触发（任务提交/成就判定/对话节点）留在各调用方

## 三、后续建议（待鱼鱼拍板）
1. 收藏册 bonus 实装：title_bonus() 加收藏册集齐源（集齐→永久属性自动生效）
2. 对话/任务等存量 reward 字段 → REWARD 统一格式视图（当前是"旧字段读出来转 REWARD"，
   未物理改数据——后续可让数据层直接存统一格式）
3. 更多来源接入：开箱(tpl_open_chest 内容)、调查点(inst_investigate_reward)
