# 《剑与魔法》可扩展性重构设计文档（v99 系列）

> 日期：2026-08-10（v98 系列完结后二次审计）
> 背景：v98.1~v98.5 已完成数据下沉/常量收敛/六大注册表（对话/称号/天赋/隐藏怪/战斗机制/词条/世界事件展示），
> 全项目 **>=6 分支 if-elif 长链归零**。本次审计剩余点位：死代码、命令层数据表、成就条件链、
> 词条概率硬编码、魔法数字。
> 原则：**行为零变化**（重构不改数值/文案/概率），测试兜底，全量回归后台跑，全量期间不动源文件。

---

## 一、审计结果（2026-08-10 v98 后全模块扫描）

### ✅ 已消灭（v97+v98 成果，不再处理）
- >=6 分支 if-elif 链：0 处（探索事件/道具/规则/战斗机制/词条/称号/天赋/对话/世界事件展示全注册表化）
- main.py：210 行 0 elif；数据表下沉 data/；"oak_town" 魔法字符串收敛 constants.py

### 🔴 P1 死代码（零调用点，最优先）
- `engine.py:798-873` `player_attack()` + `engine.py:874-918` `monster_turn()`：
  v9 统一战斗引擎（battle.py）接管后的历史遗留，全项目 **0 调用点**（grep 验证）。
  内含怪物技能 elif 链 + 魔法数字（0.3/0.1），误导后人改错地方，直接删除。

### 🟠 P2 词条触发概率硬编码（17 处，数据已有 chance 字段！）
- `core/affix_effects.py`：HIT/TAKEN/TURN_START/SET_PROC 的触发概率 0.10~0.30 写死在 handler。
- **affixes.py 数据已带 `chance` 字段**（bleed=0.20/armor_break=0.25/combo=0.15…）——
  抽查一致，但 handler 没读。改造：handler 读 `C.AFFIXES[aid]["chance"]`，套装特效读
  `data/sets.py` bonus_4 的 `chance` 字段（缺失则补数据，与现概率一致）。
- 扩展收益：调概率 = 改数据，零代码。

### 🟠 P3 魔法数字（~20 处，抽常量/数据字段）
| 位置 | 数字 | 含义 | 方案 |
|---|---|---|---|
| battle.py:538 | 0.75 | 逃跑成功率 | constants.py `FLEE_CHANCE` |
| battle.py:1294 | 0.3 | 怪物技能使用概率 | 怪物数据字段或常量 |
| battle.py:1308 | 0.1 | 怪物技能暴击率 | 常量 |
| battle.py:1597/1605/1648 | 0.6/0.25/0.20 | 宠物技能/各类概率 | 常量 |
| combat.py:95/125/144/202 | 0.35/0.05/0.5/0.05 | 遇怪/SA Boss/探索事件/彩蛋 | maps 数据字段或常量 |
| economy.py:211/240/280/306 | 0.5/0.15/0.10/0.3 | 钓鱼/稀有概率 | 常量 |
| economy.py:1130-1138 | 10/30/50/70/90 | 配方等级阶梯 | `RECIPE_LV_TIERS` 常量 |
| instance.py:278 | 0.5 | 副本事件概率 | 常量 |
| world.py:2026 | 0.25 | 移动撞怪概率 | 常量 |

### 🟠 P4 荣誉商店兑换硬编码
- `combat.py:1813-1900`：HONOR_SHOP 4 件商品数据写在命令层 + `_honor_buy` 的
  `num==1/2/3/4` 兑换逻辑硬编码（勋章/披风/药剂/清券各自一段）。
- 方案：商品数据下沉 `data/honor_shop.py` + 每件商品加 `reward` 字段
  （`{"title": "荣誉勋章"}` / `{"item": {...}}` / `{"item_template": "heal50"}`），
  `_honor_buy` 查表执行。加商品 = 数据加一行。

### 🟠 P5 成就条件链（41 种类型）
- `core/achievements.py:50-185` `cond_met()`：41 种 cond type 的 if-elif（~135 行）。
- 方案：`core/achievement_conds.py` 注册表（照 battle_conds 模式），cond_met 查表化。
  扩展：加成就类型 = register 一个函数。

### 🟡 B 级（本次不做，记录）
- 145 个 `@filter.regex` 分散注册 + misc.py 帮助手写（P6 远期大工程）
- 世界事件执行链（social.py:801 auction/boss 数据生成，2 分支）
- engine.py:237 被动属性结算（4 分支，固定属性类型）
- 4-5 分支小链 7 处（物品类型展示/任务 objective 等，固定类型可接受）
- player.py:280 `"橡木镇"` fallback → 顺手改 `C.START_MAP` 对应名

---

## 二、阶段方案（按风险从低到高）

### v99.1 死代码清除（P1）—— 零风险
- 删 `engine.py` 的 `player_attack()`（798-873）+ `monster_turn()`（874-918）。
- 前置：grep 全项目确认 0 调用点；删后全量回归兜底。
- 附带：engine.py 顶部 docstring 若引用旧战斗 API 一并清理。

### v99.2 词条概率数据化（P2）—— 行为零变化
- `affix_effects.py` 各 handler 概率改为读数据：
  - HIT/TAKEN/TURN_START：`C.AFFIXES[aid].get("chance", 旧值)`（数据缺失用旧值兜底，防漂移）
  - 元素附加三兄弟：数据补 `chance`（1.0？——原代码元素附加**无条件触发**，补 1.0）
  - 净化：judgment_chain/purify 读各自 chance
  - SET_PROC：`data/sets.py` bonus_4 补 `chance` 字段（frost=0.30/burn=0.30/thunder=0.25/
    pierce=0.30/lifesteal_set=0.30/execute 无条件）
- 验收：test_stage8_equip_affix（384 项）全绿 + 概率抽样一致。

### v99.3 魔法数字收敛（P3）
- `core/constants.py` 新增一批常量（见上表），替换散落引用。
- `economy.py` 配方等级阶梯抽 `RECIPE_LV_TIERS = (10, 30, 50, 70, 90)`。
- 验收：相关测试全绿；`grep -c "random.random() < 0" game/` 显著下降。

### v99.4 荣誉商店数据化（P4）
- 新建 `data/honor_shop.py`（4 件商品 + reward 字段），`C.HONOR_SHOP` 导出。
- `combat.py` 删除类内 HONOR_SHOP + `_honor_buy` 的 if-elif 改为查表执行 reward。
- reward 执行器：`{"title": "荣誉勋章"}` → set_event_state 称号标记；
  `{"item": {...}}` → db.add_item；`{"effect": "clear_red"}` 等复用现成模板思路。
- 验收：荣誉商店相关测试（若有）全绿；新增扩展性测试（加第 5 件商品零代码）。

### v99.5 成就条件注册表化（P5）—— 最大一块
- 新建 `core/achievement_conds.py`：`COND_CHECKS` 注册表，41 类型逐一搬运
  （函数签名 `fn(player, stats, profs, extra, cond) -> bool`，与 cond_met 参数一致）。
- `achievements.py` `cond_met()` 改为查表 + 未知 type 安全降级 False。
- 验收：成就相关测试全绿 + 扩展性测试（注册新类型立即生效 + 41 全覆盖检查）。

---

## 三、测试与回归策略

1. 每个阶段独立提交，提交信息标注 `v99.x`
2. 阶段内：相关测试单跑 → 全量后台跑（`run_all_tests.py`，notify_on_complete）
3. **全量跑期间绝不改源文件**（v97.5/v98 教训：中间态误判）
4. 每阶段完成后更新本文档（勾选状态）

## 四、验收标准

- 所有既有测试全绿（79 文件）
- 新增测试：词条概率读数据、荣誉商店扩展性、成就注册表扩展性
- `git log` 每个 v99.x 一个干净提交
- 全项目 `random.random() < 裸数字` 计数下降（P3 目标：从 ~20 处降到 ~5 处以内，
  剩余为 GM 校验等合理场景）
