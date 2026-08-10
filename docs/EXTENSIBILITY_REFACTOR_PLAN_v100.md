# 扩展性收尾计划 v100（2026-08-09 鱼鱼授权"不优雅就全改"）

> v99 系列收掉 C 级问题后，鱼鱼授权继续处理 B 级/A 级剩余项。
> 原则不变：行为零差异（除明确 bug 修复）；每阶段先 commit 再验证；单测先行，全量最后后台跑。

## 待办清单

| # | 级别 | 位置 | 问题 | 方案 | 行为影响 |
|---|---|---|---|---|---|
| v100.1 | B | engine.py:237 `passive_stats_bonus` | mp/spd/crit/fire 4 分支 if-elif 分发 | stat→(bonus_key, 操作, 需cond_none) 查表化，循环处理 | 零差异 |
| v100.2 | B | social.py:801 世界事件初始化 | auction/boss 2 分支生成 data（v98.5 只模板化了展示） | core/world_event_templates.py 加 INITIALIZERS 注册表，与 DISPLAYS 对称 | 零差异 |
| v100.3a | A | player.py:280 | "橡木镇" fallback 字符串 | 换 C.START_MAP | 零差异 |
| v100.3b | 🔴bug | core/achievement_conds.py item_has/quest_done | 引用未定义 group_id → NameError→False → **2 个隐藏任务成就 + 星陨之剑成就永远无法解锁** | cond_met 加可选 group_id 参数（内部注入 extra 副本，handler 签名不变），check_achievements 传参；quest_done 查 `side[key].status=="done"`，item_has 查背包 count_item + 已装备槽位 | **正向修复**（成就从不可解锁→可解锁） |
| ~~145 个 @filter.regex~~ | — | 10 文件 | 指令路由装饰器 | **不改**：AstrBot 框架指令路由惯例，非本插件分发硬编码，改=违反框架约定 | — |

## 关键设计决策

1. **cond_met group_id 贯通**（v100.3b）：
   - `cond_met(player, stats, profs, extra, cond, group_id=None)`，签名向后兼容（默认 None 保持旧行为）
   - group_id 非 None 时注入 `extra["_group_id"]`（dict 副本，不污染调用方 extra）
   - 43 个注册表 handler 签名零改动；仅 quest_done/item_has 从 extra 取
   - 判定逻辑：
     - quest_done：`db.get_quests(gid, qq)` 的 `side[key].status == "done"`（world.py:2572 完成标记格式，world.py:2016 已有同款判定）
     - item_has：key 是装备 id（eq_starfall_sword）→ EQUIP_ROSTER 解析 name → `db.count_item(gid, qq, name) > 0` 或 `player["equipment"]` 任意槽位 name 匹配（economy.py:1936 同款双查模式）

2. **世界事件 INITIALIZERS**（v100.2）：`{"auction": fn, "boss": fn}`，fn(evt, rnd) → data dict；social.py 改为遍历注册表；未知 etype → 空 data（与旧 else 一致——旧代码只有两分支，无 else，非 auction/boss 的池子成员会 data={}，行为保持一致）

3. **被动属性查表**（v100.1）：
   ```python
   _PASSIVE_APPLY = {
       "mp":   ("mp_mult", "mul", True),   # 需 cond is None 才生效（原代码特判）
       "spd":  ("spd_mult", "mul", False),
       "crit": ("crit_add", "add", False),
       "fire": None, "chi_gain": None,     # 战斗内机制，面板不结算（原 pass）
   }
   ```
   加新 stat 类型 = 注册表加一行；条件型被动仍由 battle.py 处理（不进本表）

## 验收标准

- 每阶段：`python -m py_compile` + 相关单测全绿 + git commit
- v100.3b 新增验收测试：quest_done/item_has 修复后能解锁对应成就（构造 side/背包数据验证）
- 全部完成后全量回归后台跑（run_all_tests.py），期间不动源文件
