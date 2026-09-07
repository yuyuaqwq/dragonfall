# v181 架构重构 阶段性交接（2026-09-07 深夜，鱼鱼睡觉，格温自主推进中）

> 触发：26 子 agent 全项目架构审计 → P0~P5 改造路线。鱼鱼拍板北极星 = "配置换=新游戏"
> （docs/ARCHITECTURE_TARGET_STATE_v181.md）。此文件供任意会话/主 agent 接续，随时更新。

## 已完成并合并 master（全部行为零变化，numeric 51/51 守护）

| commit | 内容 |
|---|---|
| 37bdccd | docs: REFACTOR_PLAN_v181.md（P0→P5 路线）|
| b99d678 | docs: 计划补 P2 细节 |
| 14cee59+merge | v181.A engine 三表下沉 data/battle_config（TIER_GROWTH/BRANCH_BONUS*/MECH_STACK_MAX）|
| 8b877bd+merge | v181.D 种族后门下沉 data/races.py（RACE_*_MULT/UNDEAD_KEYWORDS/skeleton）|
| 9925a62+merge | v181.C 被动乘区兜底收口（7 被动读 skills.py 数据）|
| 587b3a8+merge | v181.A1 套装中文名后门清除（星尘/圣光/月语/海神/苍穹→套装 params 声明）|
| e578a4e+merge | v181.B 职业 if 特判族收口（class_name=="cls_*" 清零→资源表驱动）|
| 6cde807 | docs: ARCHITECTURE_TARGET_STATE_v181.md（北极星三层模型）|
| b8435b3 | docs: 目标态补扩展门槛指南 |
| 36b34e9+merge | v181.P2A class_sets 套装表下沉 data/set_bonus_data.py（纯搬移，SETS sha256 一致）|
| ff1c843+merge | docs: REFACTOR_P2D_passive_proc_registry.md（被动 proc 注册表方案 428 行）|
| 8ad06fc+merge | v181.P2B 引擎刻度常量收 core/constants（13 常量，消 7 处 core→battle 反向 import）|
| 724598e+merge | docs: REFACTOR_P2F_formula_skeleton.md（公式骨架方案 241 行）|
| 1795508+merge | docs: REFACTOR_P2E_mech_cfg.md（CFG 收敛方案 391 行）|
| 6b56e8a+merge | v181.P0B-B skill_up 止血（628→305，删 323 行，等价探针+346 断言全绿）|
| 8e10477+merge | v181.P2F1 公式骨架参数化（新建 formula_skeleton.py，F2/F3/F4/F7/F9/F15/F16，372行探针0diff）|
| ff708d8+merge | v181.P2D-D0 被动proc数值回填（37 proc 回填 skills.py，数据=唯一权威）|
| 623f4dc+merge | v181.P0B-C skill_up key 改稳定id+归属根治（305条，0撞车）→ P0B 整个完成 |
| 906fa61+merge | v181.P2D-D1 被动proc注册表基建（passive_procs.py 两层注册表）+ 试点5proc |
| 97cffe9+merge | v181.P2C-C1 weapon_effect_data 表补齐（13族79key标注+缺字段+aux并入，92→79行）|

## 进行中（子 agent 并行，各占 worktree，等合并）

> 2026-09-07 夜续跑中（鱼鱼换 key 后续）。当前批次见下，每批 numeric 51/51 守护。

| worktree/分支 | 任务 | 状态 |
|---|---|---|
| w5 wt_p2dd2 | P2D-D2 暴击/暴伤/面板族迁注册表 | 运行中 |

## 方案文档全齐（已合并 master，待实施）

| 方案 | 文档 | 核心 |
|---|---|---|
| P0B skill_up | REFACTOR_P0B_skill_up_dedup.md (9d9148b) | 628→468；B止血(已实施中)→C根治(id key) |
| P2C weapon | REFACTOR_P2C_weapon_executors.md (43b0075) | 79 key→15族→10执行器；C1-C10 十批 |
| P2D 被动 proc | REFACTOR_P2D_passive_proc_registry.md (ff1c843) | 52 proc→~20族；D1-D7 七批 |
| P2E CFG | REFACTOR_P2E_mech_cfg.md (7083dbe) | 95常量：52消费/41死表；MECH_CFG A29+B14+C7+D45；消费点~150-200行净-400 |
| P2F 公式 | REFACTOR_P2F_formula_skeleton.md (056354a) | 18公式；P2F-1低(✅)/P2F-2中(✅)/P2F-3高(✅ 见下 P2F3a/3b)；calc_damage 专项 |

⚠️ P2E 关键发现：审计"90 常量仅 7 被 import"是**误判**（只数了 data/__init__ 聚合层，漏直连
import）；实际 95 常量 52 真消费/41 死表。教训：AST 扫"被 import"要看全仓直连，不能只看聚合层。


## 实施队列（方案全齐，按序推进）

- P2C 实施：C2 试点→C3-C10（C1 已完成）
- **P2G 效果动作统一收敛（鱼鱼 2026-09-07 拍板）**：消灭各域重复实现（weapon_effects 97 handler/battle_mech 124/affix 46 内联的 shield/dot/buff/control 逻辑抽成 effect_actions 动作，每动作全项目只写一次）；目标 = 新增效果走单一标准路径：①查 effect_actions 有现成动作→data 声明直接用 ②没有→effect_actions 加一个动作（~15 行全域通用）；触发层保持分域薄壳（触发语义不同），1 动作库 + N 薄触发壳；P2C 完成后做（P2C 先收敛 weapon handler 到族执行器，P2G 再把族执行器里的动作抽共享）
- P2E 实施：MECH_CFG 落位 A29+B14+C7+D45（消费点改 ~150-200 行，与 battle.py 撞文件需串行）
- P2F-3：player_base_stats/monster_stats 声明化（✅ b955276 P2F3a F14 MONSTER_ROLE_MODS 表 + 4f705ee P2F3b F6 base_growth.py 声明表；numeric 52/52）
- P3：玩家状态容器收尾（p_meta 槽收纳，需先行为快照测试）
- **P3/P2G 并入项（鱼鱼 2026-09-07 反馈古王"内战"后拍板）：e_buffs 老共享 dict 收口**——敌方 buffs 双路径并存：老代码直写共享 `self.e_buffs`（battle.py L2868/5249/5271/10139 等单怪时代遗留），新代码写每怪 `u["buffs"]`（_enemy_turn L3162 等）；显示层只读共享 e_buffs → 多怪（古王+王冠核心）buff 串/归属错乱。收口方向：全部敌方 buffs 走每怪 actor `u["buffs"]`，`e_buffs` 仅作单怪兼容别名（指向存活主怪 buffs），老写入点逐个迁。属于 actor 状态容器统一（P3）范畴，与 P2G 动作库一起做。
- P4：命令层抽 services（BattleSettlement/Quest/Shop/Crafting/Profession…）
- P5：battle 拆类（最后，需白盒黑盒化）
- **P6（最后做，鱼鱼 2026-09-07 夜拍板）：可视化配置编辑器**——直接编辑游戏配置的可视化编辑器（data/ 各表已 dict/表驱动，编辑器直接读写）。排在 P0~P5 全部完成后，别提前做。
- **P7（收尾审计，鱼鱼 2026-09-07 夜拍板）：终局并发审计**——P0~P6 全部完成后，再开一整轮并发子 agent 审计（对照 26 份初审计报告 + 北极星三层模型），验证"配置和框架分离干净"目标真正达成，产出与 _archive_unused/architecture_audit_20260907/ 可对比的终局报告。

## 关键环境/路径（踩过的坑）

- worktree 真实物理路径 = `/c/c/c/Users/yuyu/AppData/Local/Temp/df_wt_v181b/w<N>`（三层 c，MSYS 嵌套映射）
- git worktree list 显示的 `C:/c/c/...` 是给子 agent 用的（它们 shell 能解析）
- 主 agent 自己 ls 用三层 c；合并用 `git merge wt_XX --no-ff`（按分支名，不依赖路径）
- worktree 里跑测试 = 复制到 `Temp/df_wt_copy*/data/plugins/dragonfall` 沙盒（conftest 需 data/plugins 父链）再跑 uv python
- uv python：`"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"`
- numeric 门禁：`python scripts/run_numeric_tests.py`（51 文件全绿才算过）
- 全量 run_all 要等所有批合并完才跑（不并发污染 test 库）
- 主仓 C:/Users/yuyu/qqbot/data/plugins/dragonfall 是运行中 bot，别热载

## 铁律提醒（每批）

- 行为零变化、数值零变化；改码前 git status 干净
- 每批独立 commit（v181.X 格式）；子 agent 在自己分支 commit，主 agent merge
- 北极星红线：data 不放函数 / core 不放内容名 / 执行器无本地兜底（缺字段=无此行为）
- 新机制族 = 注册 ~20 行 + 数据声明，禁止 if-elif 分发链
