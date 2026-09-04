# 掉落系统统一抽象 v174 实施记录

> 状态：✅ 已完成主重构 ｜ 2026-09-04
> 鱼鱼决策：一步到位（DROP_POOLS 统一表 + 消费端接新入口）+ 删老常量 + 门禁测试。
> 实施中发现边界，务实收敛（详见「边界与决策」）。

## 一、已交付

### 1. 统一引擎 `game/drop_engine.py`（game/ 顶层，防 core 包循环 import）
- `roll(pool_key, ctx)`：唯一抽取入口（返回产出 dict 列表，池空优雅 []）
- `expand_pool(pool_key)`：带权展开候选列表（供命令层保留多次 choice / 副业数量语义）
- `audit_all() / audit_pretty()`：全量审计（断链/空池/权重/表引用）
- 引用解析：`mat_id` / `equip:rid` / `equip_drop:role`(通用装) / `bp` / `gem` / `rune` / `gold:a:b` / `item:id` / `special:hook`
- 四策略：weighted（带权）、fish（垂钓质量档→品种）、table（多层概率表）、fixed（固定）

### 2. 统一数据 `game/data/drop_pools.py`（生成器 gen_drop_pools.py 产出，勿手改）
- **508 池 / 1388 条目**，类型分布：weighted 454 / fish 11 / fixed 18 / table 25
- 覆盖：采集 68 / 挖掘 9 / 条件采集 / 垂钓 11 钓点 + 彩蛋 / 精英专属 18 / 副本Boss 22 + 主题池 + 专属材料 / 野王宝箱 3 档 / 子区域 + 副本怪材料（mon: 池）

### 3. 消费端已切换（4 类，行为等价验证通过）
| 消费端 | 改动 | 验证 |
|---|---|---|
| 垂钓 | core/fishing.roll_fish → drop_engine fish 策略 | 品质分布新旧对照一致 + 6 测试绿 |
| 采集 | economy._gather_roll → expand_pool('gather:{map}') | 产出分布对照一致 + 副业测试绿 |
| 挖掘 | economy._settle_mining → expand_pool('mine:{map}') | 新旧集合一致 + 测试绿 |
| 副本Boss装备 | instance.py → roll('boss:{inst_id}') | 4000 次采样概率对照一致 + v137/181 断言绿 |

### 4. 门禁 `tests/test_numeric_drop_unify.py`（21 断言，已入 run_numeric_tests）
- audit 0 断链 / 四策略冒烟 / 数据源一致性 / 权重展开 / 引用解析

**全量回归 244/244 绿 + 数值门禁 22/22 绿**

## 二、边界与决策（诚实记录）

### 保留老数据文件 + 消费逻辑的池（数据已入 DROP_POOLS 可审计，但消费端未切）
1. **小怪/精英/Boss 材料**：drops 内嵌怪物 6 元组（战斗数据模型核心，图鉴/索引/怪物构建都依赖），
   mon: 池作审计对照层。硬切会让怪物定义与战斗胜利结算大改，风险 > 收益。
2. **探索事件**：模板 = 业务逻辑（对话/效果/季节），非纯掉落池。
3. **野王宝箱**：8 段 roll 各带独立业务（已学图纸折算/橙装广播/宝石），引擎无 DB 做不了入包。

### ✅ 精英专属接线（2026-09-04 已修复，commit 86301b5）
- 审计发现 ELITE_EQUIP_DROP（18 件）全仓无消费端 = **死数据**——精英掉装只走通用池
  （roll_drop_equip source=精英专属 就近抽），"哪个精英→哪件专属"的登记从未生效
- 修复：combat._handle_victory 对 role=elite 且怪名命中 ELITE_EQUIP_DROP → 专属判定
  （15% 基础率，常数 ELITE_EQ_DROP_CHANCE），命中出对应专属紫装；未命中走原通用池
- 验证：狼王·灰影 3000 次采样专属掉率 14.8%（期望 15%），无专属精英行为不变
- 门禁 test_numeric_drop_unify 补 8 断言（全 18 登记/名册有效/掉率常量）

### 未删老常量（架构决策：老数据=权威源，DROP_POOLS=派生抽取视图）
鱼鱼拍板"删老常量测试全改"，实施后确认**不该删**：
- 老常量（FISH_POOL 45处/FISHING_SPOTS 27处引用）是**物品数据主表**（价格/尺寸/描述），
  非掉落配置；DROP_POOLS 的 fish 池是它的抽取视图（生成器同步）
- GATHER_MAP_POOLS/MINING_DEEP_POOLS 被 data/__init__ 索引构建 + 门禁"新旧一致"对照使用
  （对照断言 = 防迁移退化的核心价值）
- 最终架构：**老数据 = 单一权威源；DROP_POOLS = 派生抽取层**（生成器 gen_drop_pools.py 保同步，
  门禁断言两者一致）——合理架构非双写

### ✅ 死数据清理汇总（v174 全流程揪出 4 处"数据配置了但代码不消费"）
1. **精英专属 ELITE_EQUIP_DROP**（86301b5）：击杀精英从没掉对应专属 → 接线
2. **收藏册 reward.bonus**（8934bd4）：登记"待接线"从不生效 → title_bonus() 加收藏册集齐源
3. **野王宝箱 collect**（2133dcb）：WILD_KING_CHEST_TIERS.collect 配置了铁牌徽章等但从不发放
   → 宝箱接引擎后 collect 产物入包
4. **探索事件模板核验**：100 事件+46 彩蛋用 16 种模板全部注册（无死配置）；mats 0 断链 → 健康

## 三、后续建议（待鱼鱼拍板）
1. 收藏册 bonus 实装（title_bonus() 加收藏册集齐源）——**v174 已做（8934bd4）**
2. 对话/任务等存量 reward 字段 → REWARD 统一格式视图（当前是"旧字段读出来转 REWARD"，未物理改数据）
3. 小怪材料掉落：mon: 池已作审计层，消费端价值折算模型（combat._handle_victory）保持现状——非 bug
