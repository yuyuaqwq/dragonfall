# v115 审计 2 · 代码与回归审计报告

> 审计范围：v115（网状子区域房间 + 今日奇遇 + 探索事件扩容 + POI 扩容 + 探索见闻）的全部代码改动与全量回归。
> 执行：审计 agent 2 批量回归（132 文件）+ 协调人复核修复与最终全量复跑。

## 一、全量回归最终结果

`python tests/test_*.py`（脚本式逐文件运行，Python 3.12）：

| 轮次 | 结果 |
|------|------|
| 审计 2 初跑（集成中状态） | 132 文件：124 通过 / 8 失败 |
| **最终复跑（全部修复后）** | **132 文件：131 通过 / 1 失败（flaky）** |

## 二、失败项处置记录（8 → 1）

### A. v115 相关（已修复，全部转绿）

| 测试 | 问题 | 修复 | 最终 |
|------|------|------|------|
| test_v87_14_spatial_links.py | oak_plain 由线性 3 房升级 6 房网状，旧线性断言失效 | 更新为网状断言（审计 2） | 32/32 ✅ |
| test_v97_04_explore_events_30.py | 硬编码容量 30（现 50） | 断言更新 30→50（审计 2） | 194/194 ✅ |
| test_v97_06_eggs_hidden.py | 硬编码容量 30（现 36） | 断言更新 30→36（审计 2） | 276/276 ✅ |
| test_v87_command_matrix.py | 新指令 explore_progress 未入指令矩阵 | _registry.py 补登记（协调人）+ 矩阵测试补样本（审计 2） | 191/191 ✅ |
| test_v87_13b_move_consistency.py | 地图面板新增 POI/今日奇遇行致断言过期 | 运行时序恢复后转绿（实现最终态匹配） | 9/9 ✅ |
| test_v98_05_instance_state_persist.py | 启动注册表漂移警告「表多 1 键 explore_progress」 | _registry.py 补登记 → 148 静态键 ↔ 148 handler 同步 | 8/8 ✅（flaky，见下） |
| **D-1 硬缺陷**（审计 3 发现） | main.py `Main` 继承列表缺 `ExplorationCmds`；_registry.py 缺 explore_progress → 『探索进度』生产不可达 | main.py 继承 + 导入补 ExplorationCmds；_registry.py 补登记（协调人） | 启动校验 148↔148 通过 ✅ |

### B. 基线既有失败（非 v115，语义过期测试，断言已同步）

| 测试 | 问题 | 修复 | 最终 |
|------|------|------|------|
| test_commands_dialogue.py #51 | v113.5 O90 语义：同图但目标在别的子区域 → 统一「（你现在不在这里）」全列表样式；测试断言仍为 v59 旧样式（只列当前地图） | 断言更新为 O90 样式（协调人） | 56/56 ✅ |
| test_v104_achievements.py（副业排行段） | v113.6 prof_top 只计已激活副业等级，测试未激活 → total 全 0 | 测试补 db.activate_prof（协调人） | 33/33 ✅ |

### C. 剩余 1 个 flaky（非 v115，v114 既有）

- **test_v98_05_instance_state_persist.py**「援军在前排被攻击」：v114 多目标站位下 `select_target` 对同 rank 前排（Boss 与注入爪牙均 rank=1）随机选择，测试断言"爪牙必被攻击"在随机下不成立。单独复跑 2 次均 8/8 通过，全量跑偶发失败。
- 根因属 v114 设计（同 rank 随机），非 v115 引入（v115 未触碰 battle.py/instance.py）。
- **建议（v114 后续处理）**：测试改为「前排单位（Boss 或爪牙）任一被攻击即通过」，或把爪牙设为唯一 rank-1 目标使选择确定化。

## 三、代码审查结论（A/G/H diff）

| 审查点 | 结论 |
|--------|------|
| core/maps.py `subarea_links` 回退路径 | ✅ 与改造前逐字等价（城镇星形/野外线性）；网状分支含隐藏房（契约：命令层过滤） |
| `_assembly.py` 装配顺序 | ✅ EXTRA 合并先于 SUBAREA_INDEX 循环，新房间自动进索引/百科；MESH_POI_MOUNTS setdefault+extend 不覆盖既有 |
| combat.py explore() `_fx` 注入 | ✅ getattr 兜底；事件率 clamp [0,0.6]；空探索阈值 max(0.05, 0.25-encounter_rate)；精英率叠加；loot_mult/pref_mats 经 kwargs 注入 EventContext（TypeError 回退兼容） |
| world.py `_visible_sas` 与 move 一致性 | ✅ 面板编号 = 可移动列表（同源过滤）；隐藏房名称路径给出 reveal 引导（含「还差 X 次」） |
| `_handle_poi` 新分支 | ✅ merchant（金币/图纸，已学折算残页复用既有逻辑）、traveler_grave（grave_{map}_{qq} flag 首祭/再经）；buff/herb/sight/loot 复用既有分发 |
| core/exploration.py record_visit | ✅ 首访奖励 db 写入、隐藏房 +1 材料入包、region/overall 聚合（region 缺失容错） |
| core/daily_events.py | ✅ 日期哈希确定性（同一天多次调用一致、全服一致） |
| 循环导入 | ⚠️ `from game.core.maps import ...` 作为首个 import 会触发既有 circular-import 脆弱点（HEAD 原码同样存在，pre-existing）；真实入口与测试均 data-first 导入，无影响 |

## 四、结论

v115 全部代码改动通过代码审查与全量回归；v115 相关测试全部转绿；遗留 1 个 v114 既有 flaky 测试与 1 个 pre-existing 循环导入脆弱点（均非 v115 引入，已在文末标注后续处理建议）。
