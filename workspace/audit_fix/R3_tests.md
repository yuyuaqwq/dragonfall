# R3 任务卡：测试沉淀（行为断言补测 + 审计加固 + 空断言修复）

## 背景
v130.2c/d 测试覆盖审计（B- 68/100）：**8 大核心机制 7 项无行为级固化测试**（验收脚本全删，未沉淀）；smoke 存在恒真空断言；审计存在自证式/死参数漏洞。本次把关键机制补成固化测试，防止下次并行改动回归无感。

## 修复清单（全部在 tests/ 下，禁动 game/ 任何文件）

### 1. 新建 tests/test_v1302c_mechanics.py（核心交付，参照 test_v130_resources.py 的脚手架姿势：conftest FakeEvent/run/clean_db/make_player + GWEN_GAME_DB 私有临时库）
断言组：
- **consume_all 统一公式**：4 技能数值断言（无畏冲击 2.2×2.2≈4.84（per 0.12 满怒）、暗影处刑 3.2×1.5=4.8（per 0 + 残血 cond）、破晓之拳 2.4×(1+0.1×10)=4.8、元素湮灭 2.4×(1+0.2×5)=4.8）——用 engine/Battle 黑盒或数据断言（伤害波动归零：封 random 或直接断言 info power 折算逻辑）；加 2 例 `_do_player_skill` 黑盒（满资源施放成功 + 资源扣光）。
- **超标 P1-2 回归**：持 4 怒施放无畏冲击**成功**（不被预检拦截）；持 2 充能施放元素湮灭成功（资源不满可施放）。
- **回声单通道闭环**：歌者（cls_mu_shi tier1 path1）施放战歌 → echo 层 +1；施放英雄叙事诗 → echo 不变；`_turn_start` 满 3 层全队恢复 36（满层翻倍）。
- **六词条行为**：印记铭刻上限 4（含 max_total 帽后 2 件仍 4）；反应催化蒸发 ×1.15；疾风余韵（回合结束精力≥80 → 下回合 +10）；连段护持（roll 固定保连段）；连段之锋阈值 2；蓄势精通 5 气 ×1.20。
- **套装抽样 5 套**：元素使徒（上限 6 + 全耗 -1 留残点）、夜幕合契·影纱（开场 1 cp + 终结暴击 +15%）、圣典日冕（满信仰首次受击免伤 1 次/战）、余烬军团（满怒追击额外伤害）、时之领主（时停领域 CD-1）。
- 断言全部真数值（禁恒真 check）；所需随机点固定/控制分支（参照项目测试确定性铁律：显式处理随机分支、不赌 seed 碰运气）。

### 2. 修 smoke 空断言（tests/_smoke_v130_engine.py≈217-219）
- `check("回合初始回声恢复(3层=18)", True)` 恒真 → 改真断言（3 层回合初始恢复 36，验证满层翻倍）；注释同步 3 层=36。
- 顺手修类名笔误（≈504/509 `cls_wu_sheng` → `cls_wu_seng`——先 grep 确认该测试预期用哪个，若断言实际依赖错误类名请修正为正确类并核对断言仍过）。

### 3. audit 加固（tests/test_v1252_audit_closure.py）
- **SET_EFFECT_CONSUMED 自证式漏洞**：增加「battle.py 源码含消费点」反查——对 SET_EFFECT_CONSUMED 每个 effect 名，读 game/battle.py 源码确认出现次数 ≥1（测试内用 open().read() 读取源码文件做字符串计数，注意 battle.py 是大文件只做简单包含检查）；找不到消费点的 effect 报红。
- **AFFIX_DELISTED_V130_2C 死参数**（≈186 行）：该集合已删除，`getattr(...,[])` 兜底恒空 → 移除 delisted 相关行或改为断言「下架集合不存在」（`not hasattr(DA, "AFFIX_DELISTED_V130_2C")`），防止未来误复活。
- **六词条 4 个 stat-trigger 词条零保护**（sigil_engrave/reaction_catalyst/combo_edge/momentum_mastery）：在 §7 增加 stat-trigger 词条的接线审计（battle.py 源码反查这些词条 ID 出现 ≥1 次），与 SET_EFFECT_CONSUMED 同款思路。

### 4. 既有测试文案过期（P3 顺手）
- test_v87_hidden.py≈151 与 test_stage8_equip_affix.py≈60/305-306 断言文案「167 件/144」→ 实际 208/181（只改文案不改数值）。
- test_v130_resources 的 skip 兜底（行 83/108/140/166/197）：**不改结构**（引擎未就绪时 skip 是设计），但在文件头 docstring 标注「v130.2c/d 机制行为断言见 test_v1302c_mechanics.py」。

## 铁律
- 只改 tests/ 下文件（新建 + 修改），禁动 game/ 任何文件、禁 git commit、禁重启、禁跑 scripts/run_all_tests.py 全量回归。
- 跑测：新文件 + test_v1252_audit_closure.py + _smoke_v130_engine.py + test_v130_resources.py（全部私有库/独立库姿势），全绿后报告。
- 若断言发现真实 bug（修复目标外）→ 报告给主 agent，不擅自改 game/ 代码。

## 报告（中文）
新测试文件断言清单表（组 | 断言数 | 覆盖机制）+ audit 加固前后对比 + 测试结果（文件/断言数/PASS）+ git status 清单 + 发现的非预期问题（如有）。