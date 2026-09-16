# v181 架构重构 阶段性交接（2026-09-08 更新：P2E 完成）

> 触发：26 子 agent 全项目架构审计 → P0~P7 改造路线。鱼鱼拍板北极星 = "配置换=新游戏"
> （docs/ARCHITECTURE_TARGET_STATE_v181.md）。此文件供任意会话/主 agent 接续，随时更新。
> 当前 master HEAD：`b1e6c6d`（P2E-P3b 合并，2026-09-07 晚 P2E 整个收官）。numeric 52/52 守护。

## ✅ 已完成并合并 master（全部行为零变化，numeric 52/52）

### P0 / P1（首批数据下沉 + 后门清除）
| commit | 内容 |
|---|---|
| 37bdccd / b99d678 | docs: REFACTOR_PLAN_v181.md（P0→P7 路线）+ P2 细节 |
| 14cee59 | v181.A engine 三表下沉 data/battle_config |
| 8b877bd | v181.D 种族后门下沉 data/races.py |
| 9925a62 | v181.C 被动乘区兜底收口（7 被动读 skills.py） |
| 587b3a8 | v181.A1 套装中文名后门清除 |
| e578a4e | v181.B 职业 if 特判族收口 |
| 6b56e8a + 623f4dc | P0B-B 止血 + P0B-C skill_up 稳定 id 根治 → **P0B 完成** |

### P2（注册表收编）——**P2A-F 全完成，P2E 于 2026-09-07 收官**
| 批次 | 内容 | 状态 |
|---|---|---|
| P2A | class_sets 表下沉 data/set_bonus_data.py | ✅ 36b34e9 |
| P2B | 引擎常量收 core/constants | ✅ 8ad06fc |
| P2C | weapon 79→族执行器（C1-C10 十批） | ✅ 25e3a75（C10） |
| P2D | 被动 proc 注册表（D0-D7 八批） | ✅ 2c246fe（D7）→ **P2D 完成** |
| P2E | **battle_config→MECH_CFG 单表（P1a→P3c 全批，见下）** | ✅ **b1e6c6d 收官** |
| P2F | 公式骨架（F1/F2/F3，含 F6 base_growth/F14 role_mods） | ✅ 6f8b3ae |

**P2E 详细批次（2026-09-07 深夜格温推完）**：
| commit | 批次 | 内容 |
|---|---|---|
| 28a687d + 7d3c8a2 | P1a/P1c | 43 死表清理（41 死表 + GUARD_CORE_CFG/RANGER_CHARGE_CFG 注释-only + ZEN_HOLD_CFG）+ P2E 任务书存档 |
| f6c57ca | P1b | BARD_BRANCHES 消费链退役+删除（恒 False 死判定） |
| b81301d | P2a | classes.combo 双源归一（删零读 dict）+ echo.max 标注展示用 |
| 6c5d50f | P2b | 职业字段兜底族复核 + classes.charge 死字段标注 |
| 492105e | P3a | **MECH_CFG 单表成型** + engine/battle_bars/battle_modes/data __init__ 迁移 + ELEMENT_MARK_GAIN_PER_HIT 死链删 |
| facc0bf | P3c | scripts/numeric_lib DOT 读点迁 MECH_CFG + 5 docs 已删常量标注 |
| d46b730 | P3b | **battle.py ~110 读点全量迁移 MECH_CFG** + v1252 断言同步 |

> ⚠️ P2E 关键坑（机械替换翻车记录）：`_MC['dot']` 混入 5 个 float 标量配置子键
> （boss_pct_mult/pct_cap/bleed_double_hp_pct/adapt_decay_step/resist_cap），原 `DOT_DEFS.items()`
> 只遍历 4 个类型 dict → 整名替换后 `_tick_actor_dots` 遍历 float 崩（test_v138_dot 抓出 TypeError）。
> 修法：`_dot_types` 视图 = `{_k: _v for _k,_v in _MC['dot'].items() if isinstance(_v, dict)}`，
> 遍历/查 key 全走视图。教训：**表结构聚合（dict 展开进带标量子键的表）后，原 dict 的 items()/遍历
> 语义变了，机械替换必须测到遍历点**。

### P4（命令层抽 services）——全 9 模块完成
| commit | 内容 |
|---|---|
| e0ac8e6→f9aca10 | P4-1/P4-2 QuestService（每日 + 主线支线状态机） |
| b1ce51c | P4-3 ShopService |
| a424a15 | P4-4 CraftingService |
| bca4338 | P4-5 AuctionService |
| 9f7b31f | P4-6 Party+GuildService |
| ba61ae2 | P4-7 ProfessionService |
| cce53eb | P4-8 TravelService |
| f6f5754 + 0626bb5 | P4-9 BattleSettlementService（victory/defeat 510 行，快照 38 断言） |

## ⬜ 剩余实施队列（按依赖顺序）

1. **P2G 效果动作统一收敛**（鱼鱼 2026-09-07 拍板；前置 P2C 已完成 ✅ 可开工）——消灭各域重复实现：
   weapon_effects 97 handler / battle_mech 124 / affix 46 内联的 shield/dot/buff/control 逻辑抽成
   effect_actions 动作，每动作全项目只写一次；新增效果走单一标准路径
   （①查 effect_actions 现成动作→data 声明直接用 ②没有→加一个动作 ~15 行全域通用）；
   触发层保持分域薄壳。**P2G 无现成任务书**（上次侦察 agent 烧 109 分钟零产出，
   教训：别再派纯只读侦察——让主 agent 快速摸重复矩阵写精简任务书再派实施）。
   ⚠️ 候选首批动作 = effect_actions 现有 12 个动作补齐 shield/dot/buff/control 四族。
2. **P3 玩家状态容器收尾**（需先行为快照测试）：p_meta 槽收纳 + Battle 实例残留字段迁 actor dict。
3. **P3/P2G 并入项：e_buffs 老共享 dict 收口**（古王"内战"bug 根因）——敌方 buffs 双路径并存：
   老代码直写共享 `self.e_buffs`（battle.py 单怪时代遗留），新代码写每怪 `u["buffs"]`（_enemy_turn）；
   显示层只读共享 e_buffs → 多怪 buff 串/归属错乱。收口方向：全部敌方 buffs 走每怪 actor `u["buffs"]`，
   `e_buffs` 仅作单怪兼容别名（指向存活主怪 buffs），老写入点逐个迁。属于 P3 范畴，与 P2G 动作库一起做。
4. **P5 battle 拆类**（最后，需白盒黑盒化 + 行为快照）。
5. **P6 可视化配置编辑器**（鱼鱼拍板最后做，P0~P5 全完成后）。
6. **P7 终局并发审计**（全部完成后开一整轮并发子 agent，对照 26 份初审计报告 + 北极星）。

## 方案文档全齐（docs/，已合并 master）
| 方案 | 文档 | 状态 |
|---|---|---|
| P0B skill_up | REFACTOR_P0B_skill_up_dedup.md | ✅ 已实施完 |
| P2C weapon | REFACTOR_P2C_weapon_executors.md | ✅ C1-C10 已实施完 |
| P2D 被动 proc | REFACTOR_P2D_passive_proc_registry.md | ✅ D0-D7 已实施完 |
| P2E CFG | REFACTOR_P2E_mech_cfg.md + REFACTOR_P2E_task.md（执行任务书） | ✅ P1a-P3c 已实施完（附录回写批次表） |
| P2F 公式 | REFACTOR_P2F_formula_skeleton.md | ✅ F1-F3 已实施完 |
| P4 services | REFACTOR_P4_services.md + REFACTOR_P49_task.md | ✅ P4-1~9 已实施完 |
| P2G | **无方案文档**（需先出） | ⬜ |

## 关键环境/路径（踩过的坑）
- worktree 目录：`C:/Users/yuyu/AppData/Local/Temp/df_wt_v181i/w2e(wt_p2e)/w3(wt_p3b)/w4(wt_p3c)`——**均已合并完可清**；
  P2E 收尾后 3 个 worktree（w2e/w3/w4）无子 agent 占用，新会话可 `git worktree remove` + `git branch -d wt_p2e wt_p3b wt_p3c` 清理。
- git worktree list 显示的 `C:/c/...` 是给子 agent 用的；主 agent 合并用 `git merge wt_XX --no-ff`（按分支名）。
- worktree 里跑测试 = 复制到 `Temp/df_wt_copy2e/data/plugins/dragonfall` 沙盒（conftest 需 data/plugins 父链）再跑 uv python；主仓 C:/Users/yuyu/qqbot/... 是运行中 bot 别热载。
- uv python：`"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"`（简称 PY）。
- numeric 门禁：`PY scripts/run_numeric_tests.py`（52 文件全绿）；全量：`PY scripts/run_all_tests.py`（323 文件，~100s 并行）。
- ⚠️ run_all 的 11 个固定红 = 基线 pre-existing（10 个 test_p2cc*/p2dd4a probe 需 git HEAD 旧实现对比=沙盒非 git 天然红 + test_v1252 1 个 cloth_heal_overflow 套装白名单）；**沙盒跑全量对照以"与基线同名单"为准**。

## 铁律提醒（每批）
- 行为零变化、数值零变化；改码前 git status 干净（先 commit 再动）。
- 每批独立 commit（v181.X 格式）；子 agent 在自己分支 commit，主 agent merge；合并后 git push 双仓（GitHub yuyuaqwq）。
- 北极星红线：data 不放函数 / core 不放内容名 / 执行器无本地兜底（缺字段=无此行为）。
- 新机制族 = 注册 ~20 行 + 数据声明，禁止 if-elif 分发链。
- **派工铁律：不派纯只读侦察子 agent（token 烧掉零产出）；方案文档已齐直接派实施；侦察由主 agent 快速做。**
