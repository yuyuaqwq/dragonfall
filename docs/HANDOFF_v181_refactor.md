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

## 进行中（子 agent 并行，各占 worktree，等合并）

| worktree/分支 | 任务 | 状态 |
|---|---|---|
| w2 wt_p2b | P2B 引擎刻度常量收 core/constants（消 core→battle 反向 import）| 改码中（battle.py/battle_mech.py/constants.py/weapon_effects.py 4 文件）|
| w4 wt_p2f | P2F 底层公式骨架公式化侦察（calc_damage/exp/monster_exp/equip_stats…）| 侦察中，将出 REFACTOR_P2F_formula_skeleton.md |
| w5 wt_p2c | P2C weapon_effects 96→~10 执行器侦察 | 侦察中，将出 REFACTOR_P2C_weapon_executors.md |
| w6 wt_p2e | P2E battle_config CFG→MECH_CFG 单表侦察 | 侦察中，将出 REFACTOR_P2E_mech_cfg.md |

## 队列（等侦察方案回来 → 主 agent 审 → 派实施）

- P2D 实施：被动 proc 反射化注册表（按 ff1c843 方案；前置=45 无参 proc 数值回填 skills.py）
- P2F 实施：公式骨架参数化/表达式化（方案回来鱼鱼审或主 agent 按北极星执行）
- P2C 实施：weapon 96→~10 族执行器
- P2E 实施：CFG 收敛 MECH_CFG 单表（死表清理需谨慎）
- P0-B：skill_up.py 中文 key 消重（160 组同名，112 组冲突——高风险数据迁移）
- P3：玩家状态容器收尾（p_meta 槽收纳，需先行为快照测试）
- P4：命令层抽 services（BattleSettlement/Quest/Shop/Crafting/Profession…）
- P5：battle 拆类（最后，需白盒黑盒化）

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
