# 《剑与魔法》可扩展性重构设计文档（v102 系列）

> 日期：2026-08-10（第三轮审计后）
> 背景：v100/v101 收掉前两轮审计的 A/B/C 级问题后，第三轮换了 **8 个全新维度**扫描（字符串当 key / 中文名当 key / 职业 ID 散落 / 数据表住逻辑层 / 数值模板硬编码 / 属性 key 组合 / 超大函数 / 动态列名 SQL），挖出一批之前没碰过的硬编码。
> 原则：**行为零变化**（重构不改数值/文案/概率），每阶段先 commit 再验证，单测先行，全量最后后台跑（443s）。

---

## 一、第三轮审计问题清单（2026-08-10）

### 🟠 C 级：真·硬编码隐患（本次已全部处理 ✅）

| # | 问题 | 位置 | 影响 | 处理版本 |
|---|---|---|---|---|
| C1 | 地图 type 用中文字符串做逻辑 key（`"城镇区域"`/`"城镇外郊"`/`"城镇街道"`/`"城镇出口"`） | combat.py:53/117/278/1894、economy.py:217/531、world.py:600/733/838/926/971/975、core/maps.py 6 处 | 15+ 处比较散落，改文案逻辑全断 | **v102.1** |
| C2 | 中文物品名/类型做逻辑判断（`rw == "回城卷轴"`、`type == "宠物蛋"`） | event_templates.py:272、item_templates.py:89/91 | 改物品名/类型文案就静默失效 | **v102.2** |
| C3 | 职业 ID 硬编码散落逻辑层（cls_novice/cls_bard/cls_spellblade） | battle.py、commands/player.py:167/220/479/517/879、world.py:2116、core/dialogue_conds.py:140/147 | 加新职业要改 4 个逻辑文件 | **v102.3** |
| C4 | 数据表住在逻辑层：SKILL_UP 164 行技能升级参数、CORE_RESOURCES 31 行职业战斗资源 | engine.py:537 / engine.py:24 | 加技能要改核心逻辑文件 | **v102.4** |
| C5 | 怪物/装备数值模板硬编码在 core：base+growth 两大 dict | core/stats.py:33-51 / 68-75 | 加怪物角色/装备部位要改公式文件（审计报的重复块） | **v102.5** |
| C6 | 属性 key 组合反复硬编码（`in ['crit','dodge']` ×15+、`['heal','mana','effect','stamina']`、'weapon'/'ring'/'necklace'） | engine.py、economy.py、player.py、drops.py、enchant.py、stats.py | 加新属性/装备部位要改十几个文件 | **v102.6** |

### 🟡 B 级：值得做但工作量大（**未做，记录在案**）

| # | 问题 | 位置 | 现状（2026-08-10 验证） |
|---|---|---|---|
| B1 | 超大函数（150-316 行）：init_db 317、_handle_victory 305、_player_skill 296、_instance_start 271、move 226、buy 214、craft 180、_instance_act 179、enchant 155 | battle.py、combat.py、economy.py、instance.py、world.py、store/connection.py | ✅ 仍存在（9 个 ≥150 行，实测；explore 已从 199 缩至 147 脱离清单） |
| B2 | store 层动态列名 SQL：`f"UPDATE professions SET {key}_lv=?"`、`f"DELETE FROM {tbl}"`、`f"SELECT {key}_lv AS lv..."` 等 **8 处**（含 2 处 SELECT，审计原记录 6 处漏了 SELECT） | store/professions.py:64/80/161/165、players.py:208/330、social.py:491、stats.py:24 | ✅ 仍存在（8 处，重跑审计实测）——key 来自白名单 dict，安全但约定式脆弱 |
| B3 | 整数魔法数字：30×26、20×19、50×16、99×10、300×6、500×6（等级阈值/容量/奖励量） | engine.py:839、combat.py:332、battle.py:262 等 | ✅ 仍存在（重跑审计 top50 与初报一致） |

### 🆕 D 维度复核发现（审计脚本重跑 2026-08-10 晚）
- `world.py:453 map_view()` 内重复语句块 ×2（共 12 行）——初版报告未记录
- `core/rule_engine.py:78 _match_cond()` 内重复语句块 ×2（共 16 行）——初版报告未记录

### 🟢 A 级：合理，不动 ✅
- dict 字段访问（d["name"]×458）——数据结构访问，非硬编码
- 模块级 dict（BUFF_MULT/ELEMENT_REACTIONS/_SERIES_SET_BONUS/COMMAND_REGEX）——v98-v101 注册表
- db.update_player 传参——非 SQL 拼接（H 扫描误报）
- 状态值字符串（pending/ready/done/victory）——协议值，合理
- F 扫描零发现：无 TODO/FIXME/bare except/eval 🎉

---

## 二、版本明细（v102.1 ~ v102.7）

| 版本 | 内容 | 验收 |
|---|---|---|
| **v102.1** | C1 地图/子区域类型常量收敛：代码层 15+ 处裸中文比较 → `C.MAP_TYPE_TOWN`/`SUB_TYPE_*`；core/maps.py 5 处子区域类型改用常量；清理 `"城镇外郊"` 恒 False 死分支（数据无此类型，历史遗留自 82abbde） | 单测全绿 |
| **v102.2** | C2 中文物品名/类型判断收敛：wandering 奖励池回城卷轴改 key 判断（`i_scroll_escape`，改中文名不断）；infer_template 宠物蛋/坐骑 type 改 `C.ITEM_TYPE_*` 常量（加延迟导入防环） | 单测全绿 |
| **v102.3** | C3 职业 ID 判断收敛：7 处 `class_name == 'cls_novice'` 裸比较 → `C.CLASS_NOVICE`（player 注册/技能学习/world 就职/dialogue 条件）；转职业务内 cls_bard 等保留（改职业 ID 本就需改转职逻辑） | 单测全绿 |
| **v102.4** | C4 数据表下沉：SKILL_UP（164 行技能升级参数）+ CORE_RESOURCES（31 行职业战斗资源）从 engine.py 移至 data/；engine 改 `C.SKILL_UP`/`C.CORE_RESOURCES` 引用 | 单测全绿；**踩坑：中途 del 行号偏移 → git 恢复重做（从后往前删）** |
| **v102.5** | C5 数值模板下沉：怪物角色 base/growth + 经验金币基数 + 装备部位 base/scaling 6 张表从 core/stats.py 移至 data/stat_templates.py；公式留 core | 新旧输出全量对比零差异（7 角色×6 级×7 部位×4 品质） |
| **v102.6** | C6 属性集合常量收敛：19 处裸写 `("crit","dodge")` 百分比显示判断 → `C.PCT_STATS`；顺修 test_commands_skills 对 SKILL_UP 的旧引用（v102.4 下沉遗漏） | 38 项通过，全局无残留 |
| **v102.7** | 修复 test_v83_bard 对 `E.SKILL_UP` 的旧引用（v102.4 下沉 data/skill_up.py 遗漏，全量回归 79/80 失败项）；全局已搜无其他残留 | 全量 **80/80 全绿**（443s） |

---

## 三、关键设计决策

1. **字符串当 key 统一改 key/常量，中文只做展示**（C1/C2/C3）：
   - 地图 type：比较一律用英文 key（`MAP_TYPE_TOWN` 等），中文文案只留在数据展示层
   - 物品判断：按物品 id key（`i_scroll_escape`/`pet_egg`）而非 `name == "回城卷轴"`——改中文名不再断逻辑
   - 职业 ID：`C.CLASS_NOVICE` 常量；转职业务流程内保留字符串（改职业 ID 本就需改转职逻辑，属业务语义）

2. **数据表下沉引用方式**（C4/C5）：逻辑层一律 `C.SKILL_UP`/`C.CORE_RESOURCES`/`C.STAT_TEMPLATES`（data/__init__.py 聚合导出）；公式留在 core，数据全在 data/。加技能/怪物/装备部位 = 改 data 层，零逻辑改动。

3. **延迟导入防环**（v102.2）：item_templates.py 引用 `C.ITEM_TYPE_*` 时在函数内延迟导入 constants，避免模块级循环导入（data ↔ core 双向引用场景）。

---

## 四、踩坑记录（后人必读）

1. **del 行号偏移**（v102.4）：脚本按行号删 engine.py 里的表时，从前往后删会导致行号错位删错内容 → 当场 git 恢复重做，**改为从后往前删**（或 AST 定位）。教训：批量删行永远倒序。
2. **下沉后旧引用残留**（v102.6/102.7）：SKILL_UP 移到 data/ 后，tests/ 里 test_commands_skills 和 test_v83_bard 还引用 `E.SKILL_UP`，全量回归才暴露。教训：**数据表下沉后必须全局 grep 旧引用（含 tests/）再提交**，不能只改生产代码。

---

## 五、后续规划（B 级，建议单独一轮）

### ✅ B1 超大函数拆分（2026-08-10 深夜完成 3/9 + 6 个评估不拆）

| 函数 | 行数 | 处置 | 理由 |
|---|---|---|---|
| init_db（connection.py） | 317→17 | ✅ **v103.5 拆分** | 建表 SQL 按域拆 _SQL_CORE/_SQL_SOCIAL/_SQL_PROF 三常量 + ALTER 段提取 _ensure_legacy_columns |
| _player_skill（battle.py） | 296→202 | ✅ **v103.6 拆分** | 治疗→_skill_heal(43)/增益→_skill_buff(56) 独立方法（巨型 kind 分支） |
| _instance_start（instance.py） | 271→161 | ✅ **v103.7 拆分** | stages 分层/地图模式判定/st 初始 dict → _instance_build_state(114) |
| _handle_victory（combat.py） | 305 | ⏭️ **评估不拆** | 线性结算流程：exp/gold 连续修正 + 10+ 局部变量互传 + db 副作用，提取需巨型签名，强拆降低可读性、回归风险高 |
| move（world.py） | 226 | ⏭️ **评估不拆** | async generator 线性流程（全程 yield 返回错误/结果），提取需 async for 转发 + 多参数 |
| buy（economy.py） | 214 | ⏭️ **评估不拆** | 数字索引分支虽 86 行但 10 参数 + async generator yield |
| craft（economy.py） | 180 | ⏭️ **评估不拆** | 输入解析分支均 yield 返回错误，提取收益低 |
| _instance_act（instance.py） | 179 | ⏭️ **评估不拆** | 回合状态机流程（轮转/Boss 结算/存档交错），无纯逻辑段 |
| enchant（economy.py） | 155 | ⏭️ **评估不拆** | 已是最小一档；符文分支 55 行可拆但收益边际 |

> **拆分原则（本次定稿）**：只拆"巨型分发/纯数据构建"（天然边界 + 参数少）；命令层 async generator yield 流程函数不拆（提取需 async for 转发，行为等价但可读性不升反降）。B1 剩余项关闭，非偷懒——评估结论如上。

### ⏳ B2 动态列名 SQL 加固（✅ v103.1 已完成）
8 处动态 SQL 白名单校验（update_player/pet_update/bump_stats/add_prof_exp/forget_prof/delete_player），详见上文 B 级清单。

### ⏳ B3 整数魔法数字（✅ v103.3 已完成）
7 组常量 17 处替换（EVOLVE_LEVELS/EVOLVE_FEES/RESET_SKILL_COST/DEFAULT_MAX_MP/PVP_TIMEOUT_SEC/GUILD_EXP_BASE/PROF_EXP_BASE），详见上文。

> 原则不变：行为零差异、每阶段独立 commit、全量后台跑、跑完前不动源文件。
