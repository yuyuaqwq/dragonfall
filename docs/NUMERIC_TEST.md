# 数值测试规范（NUMERIC_TEST）

> **一句话目标：任何数值改动（技能 / 怪物 / 装备 / 属性加点 / CTB / 掉落 / 伤害公式 / 成长公式 / 数据表）→ 跑 `python scripts/run_numeric_tests.py` 全绿才允许提交。**

数值测试 = 平衡快照 + 区间约束，防止“动了数值不知道动了”。机制于 v130.9 建立，框架见 `workspace/numeric_tests/FRAMEWORK.md`。

## 运行方式

| 命令 | 说明 |
|---|---|
| `python scripts/run_numeric_tests.py` | 全量：串行跑全部 `tests/test_numeric_*.py`，**提交前必跑** |
| `python scripts/run_numeric_tests.py --fast` | 只跑胜率矩阵（最耗时项），日常开发快检 |
| `python scripts/run_numeric_tests.py --list` | 只列当前发现/缺失的数值测试文件，不运行 |

- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`（必须用它，带项目依赖）
- 退出码：有任何失败（断言红/崩溃/超时）→ exit 1；**全部通过 → exit 0**
- 缺失容忍：测试文件未建全时只提示跳过、不算失败；全部缺失时警告并 exit 0（无门禁意义），待文件就绪后重跑
- 每个文件独立可跑：`python tests/test_numeric_xxx.py`；全部用真实引擎（`E.player_final_stats` / `C.build_monster` / `BT.Battle`），不 mock 核心公式

### 隔离与确定性（2026-09-11 flaky 修复）

门禁只应因**真实数值退化**变红，不能因运行方式变红。三条已修的通道：

| 隐患 | 原状 | 修法 |
|---|---|---|
| **共享库互踩** | 3 个文件（`drop_unify` / `instance_reward` / `reward_unify`）各自 `setdefault` 到同一个 `tests/test_game_data.db`；并发/与全量回归同时跑时互相覆盖写入 → 断言读到被踩过的库（实测复现：两份 `reward_unify` 共享该库并发跑，一份 `exp+gold 入账 / 物品入包 / 宠物蛋入包` 三红） | 运行器**预置** `GWEN_GAME_DB` 到按文件私有库（`tests/.numeric_workers_<pid>_<ts>/`，空白 schema 模板复制，同 `run_all_tests.py` 机制）→ `setdefault` 不再覆盖 |
| **worker 目录同名** | worker 目录固定名 → 两份门禁并发时互相覆盖模板/库文件（实测复现：4 份并发全红） | worker 目录按调用唯一（`<pid>_<timestamp>`）；`run_all_tests.py` 同款修复 |
| **未固定随机种子** | `test_numeric_drop_unify.py` 用全局 `random` 做抽样断言但未 seed | 固定 `random.seed(20260911)`（沿用 `test_v135_quality_roll` / `test_battle_n9_equip` 的既有做法） |

并发验收：1 份全量回归 + 2 份探针 + 4 份数值门禁**同时跑** → 全绿（`scripts/_tmp_concurrent_verify.py` 为一次性验证脚本，未入库）。

### 随机性审计结论（2026-09-11 全量核查 249 个测试文件）

「测试用 random 却没 seed」曾被列为隐患，全量核查后**只见 1 处真问题**（已修）。
三种合法做法（按优先级）：

| 做法 | 说明 | 用例 |
|---|---|---|
| **钉死随机源**（首选） | `random.random = lambda: 0.0` / `mock.patch.object(mod.random, "random", return_value=...)` —— 比 seed 更强：任何种子下行为一致 | `test_v104_prof_enhance` `test_v1308_lv_jitter` `test_v136_gem_drops` `test_v1307_zone_risk` |
| 固定 seed | `random.seed(20260911)` —— 用在需要"随机但可复现"的场景 | `test_numeric_drop_unify` `test_v135_quality_roll` `test_battle_n9_equip` |
| 随机仅用于造数据 | 不断言随机结果（只借它生成输入）→ 无需处理 | `test_commands_world` `test_v104_npc_dialogue` `test_v97_01_notice_board` 等 |

**已修的真问题**：`test_v135_bp_drop.py` 原用 `sum(1 for _ in range(40000) if random.random() < C.INSTANCE_BP_CHANCE)`
**抽样去"测"一个常量** —— 测的其实是 Python 随机数分布，不是游戏常量，且是未 seed 的概率性断言。
已改为直断常量值（同 `FISH_RARE_CHANCE` 写法），并移除不再使用的 `import random`。

> 教训：**抽样测常量 = 测错了对象**。常量就该直断数值；只有"概率分布本身"才需要抽样，
> 且那种测试必须自带显式容差与固定种子。

## 测试清单总览

> **2026-09-12**：`battle_matrix` / `ctb_freq` / `equip_dependency` 三个文件已建齐
> （此前"清单里列了但从未建"，详见文末「工具链修复记录」），全量不再有跳过项。

| 文件 | 覆盖什么 | 防什么回归 |
|---|---|---|
| `test_numeric_battle_matrix.py` | 6 基础职业 × 4 种跨级怪（同级 / +5 / -5 / +11 级 dps）胜率矩阵，seeds=8 纯普攻，39 点标准加点 | 防玩家碾压/被碾压极端失衡（最耗时项，`--fast` 即此文件） |
| `test_numeric_ctb_freq.py` | CTB 行动频率比：spd72 刺客 vs spd31 怪、spd41 vs spd31、同级对抗三组，计数“玩家每行动 N 次怪动 1 次” | 防站桩回归（速度差 → 频率差非线性放大） |
| `test_numeric_panel_snapshot.py` | 12 职业（含隐藏）1/11/30/60 级裸装面板快照（max_hp/atk/def/spd/crit/dodge）+ 刺客/战士/法师加点收益快照 | 防无意识成长公式改动、防单属性超模回归 |
| `test_numeric_equip_dependency.py` | 战士 11 级裸装 vs 满装：面板提升幅度 + 同级胜率对比（seeds=6） | 防装备无意义（裸装=满装）或数值爆炸 |
| `test_numeric_monster_curve.py` | 6 种 role（tank/dps/caster/speedster/elite/boss）在 1/11/22/30/60 级 hp/atk/def/spd 成长曲线（对照 stat_templates 模板公式） | 防怪物成长公式误改（含等级段修正/三阶乘区） |
| `test_numeric_skill_power.py` | 12 职业各 2 个代表技能（基础技 + 成型技）的 power/mp/lv/成长率快照 | 防技能倍率误调 |
| `test_numeric_economy_toolkit.py` | 经济模型 economy_lib 分阶段体检（6 阶段收入/装备/锻造/掉落账本 + 副业成本-价值 + 掉落数量 cap 生效） | 防经济数值改动脱离健康带（v165 起） |
| `test_numeric_bar_decay.py` | 挂敌身条（破绽）时间制：每刻 −1.7 连续衰减（非 int 截断）、连招三连 ≈4.5 次出手触发（v153 §六 验算）、阈值序列 50→67→90→121→125、条上限 ≥ 阈值封顶、免疫窗口 2 刻不积蓄/到期可再触发、触发当帧注入=0、条键不与 EFFECT_RULES 撞键、条条目不触发容器自动化（expire/period/mode/stacks/stat） | 防「衰减被取整/挂回行动制」「阈值递增与条上限打架（第二次触发死锁）」「免疫窗口丢防连控」「条被 DOT/面板折算误伤」（v181 破绽时间化） |

## 基线更新流程

数值设计调整（鱼鱼拍板 / 策划案同步）后：

1. **先跑一遍** `python scripts/run_numeric_tests.py`，拿到新实测输出（断言失败信息自带实际值，可直接抄用）
2. **审视输出是否与设计意图一致**——不一致说明改错了，回去查代码；一致才进入下一步
3. 用新实测值**更新对应测试的断言**（锁定新基线，失衡格子的宽区间/精确值注释同步更新）
4. 跑全量确认**全绿** → 提交

铁律：

- **禁止不更新断言直接改数值**（否则门禁形同虚设）
- 已知失衡基线（见下）的收紧/放宽，由**主 agent 统一更新**，个人不得私自改断言放水
- 禁止改 `game/` 源码绕过测试；测试文件之间不互相 import（`tests/numeric_sim.py` 是唯一共享助手）

## 耗时与建议频度

| 文件 | 实测耗时（2026-09-12 回填） | 建议频度 |
|---|---|---|
| `test_numeric_battle_matrix.py` | 0.1s（24 格 × 8 seeds；纯普攻每场仅数回合） | 每次数值改动必跑；日常快检用 `--fast`（即此文件） |
| `test_numeric_equip_dependency.py` | 0.0s（含 2×6 场战斗） | 改动装备/战斗公式时必跑 |
| `test_numeric_ctb_freq.py` | 0.0s（3 组 × 20 次出手窗口） | 改动 CTB/速度相关时必跑 |
| 其余（panel/monster/skill/…） | 各 ≤1s | 提交前全量必跑；日常按改到哪个系统跑对应文件 |
| **全量合计（18 文件）** | **7s** | **任何数值改动提交前必跑全量** |

> 注：初版估算「胜率矩阵 1~3 分钟」基于旧包装层（`game/battle.py`）的模拟开销；
> 迁到新引擎签名后实测快两个数量级。脚本每次运行仍会打印各文件实际耗时，显著变慢时请更新本表。

## 失衡基线清单（v130.10 CTB 修复后更新）

v130.10 已将 CTB 从旧相对时钟（玩家初始 -spd、行动广播回拽 → 速度差 15 倍放大/慢怪站桩）改为**绝对时刻模型**（单位 ct 初始 = cost=100/spd，判定 min_e_ct > 0；行动频率线性 = spd 比）。修复后重标定：

**✅ 已修复（断言已按新基线收紧）**
| 项 | 修复前 | 修复后实测 |
|---|---|---|
| CTB 频率 spd72 vs 31 | 15:1（20 回合怪动 3 次、首动 15 回合） | **2.50:1**（20 回合怪动 8 次、首动 3 回合）≤3:1 ✅ |
| 刺客全敏 11v22 | 7/8 赢（跨 11 级碾压） | **0/8** 全败（跨 11 级必死）✅ |
| 全部职业 11v22 | 刺客 7/8 其余 0/2 | **全 0/8** ✅ |

**⚠️ 仍待平衡标定（非 CTB，独立议题，目标值在断言注释）**
| 项 | 现状 | 目标 |
|---|---|---|
| 同级 11v11 dps 怪 | 物理系 8/8 满胜（dps 怪偏脆）、法/牧全智普攻 0/8 | 3/8~7/8；法牧普攻体系需强化 |
| +5 级 11v16 | 物理系仍 8/8 碾压 | ≤6/8 |
| 法师 11v6 | 仅 2/8（普攻体系弱） | ≥5/8 |

> 流程：新失衡点先按“当前实测锁定 + 注释目标”入基线排队修复；数值改动后跑 `run_numeric_tests.py` + `numtool.py` 实验标定。

---

## 2026-09-12 重标定（**现行基线**）

`tests/numeric_sim.py` 迁到新引擎签名（`Battle(sides=…)` + `human_act`）、并让开战装配与生产
同源（`battle_bridge.apply_battle_loadout`）后的首轮实测。**三个新门禁按此锁定。**

| 项 | 实测 | 门禁断言 |
|---|---|---|
| 11v11 dps（纯普攻 39 点） | 战士 3/8 · 法师 3/8 · 牧师 1/8 · 刺客 0/8 · 游侠 0/8 · 拳师 4/8 | 快照锁定 + 逐职业单调性 |
| 11v16（+5） | **全职业 0/8** | ≤2/8（防碾压） |
| 11v6（−5） | **全职业 8/8** | ≥7/8（防成长无感） |
| 11v22（+11） | **全职业 0/8** | ≤1/8（防跨级碾压） |
| CTB spd72 vs spd31 | 怪/玩家出手比 **0.600** | 0.35~0.75（防慢怪站桩） |
| CTB 同级 31 v 31 | 0.950 | 0.85~1.15（同级同频） |
| 裸装 vs 满装（铁港套装） | 面板 +92.7% hp / +70.8% atk / +170% def / +137.5% spd；胜率 2/6 → 6/6 | 快照 + 健康带 + ≥+3 场 |

> 与上一节（v130.10）的差异是**数值重标定的结果**（v131 怪 HP/防御上调、v169.3 怪攻击上调、
> v181 元素/团队效果接线等）：同级 dps 怪对**纯普攻**玩家已不再"碾压"，+5 级即全败。
> 纯普攻口径本来就该吃力（技能才是主要输出手段），故对「同级偏难」**不设下限断言**。

## 附：工具链修复记录（2026-09-12）

**症状**：`run_numeric_tests.py` 长期只报「跳过 3 个」——`battle_matrix` / `ctb_freq` /
`equip_dependency` 三个文件"清单里规划了，却从未建起来"。

**真因（两层）**：

1. **误归档**：共享助手 `tests/numeric_sim.py` 在 v181.N10-C 退役旧引擎时被一并搬进
   `_archive_unused/retired_old_engine_20260911/`，但**活消费方还在**（`scripts/numeric_lib/*`、
   `scripts/numtool.py`、`gen_numeric_matrix.py`）→ 整个数值工具集 import 即崩，
   三个门禁等于没有底座（**判"零引用"漏了 scripts/ 侧**）。
2. **接口过时**：文件里 `BT.Battle(btype=, enemy=, player=)` / `actor_turn` /
   `advance_until_next_decision` 来自旧包装层 `game/battle.py`（同一批次已删）→
   即便放回去也跑不起来。

**修法**：

- `git mv` 放回 `tests/numeric_sim.py`；战斗循环迁到新引擎签名
  （`B2("monster", sides=…)` + `human_act`）；回合数口径 `int(battle._now / ACT_TICK) + 1`（同旧 `_tick_no`）
- **开战装配收敛**：新增 `battle_bridge.apply_battle_loadout(actor, title_bonus)`
  （外部增幅容器 + 装备词条 + 职业机制），`combat._open_battle` / `combat._open_pvp` / `tower`
  三处逐行重复序列改为调它 —— 目的是**让数值门禁与生产同源**（否则门禁自测一套口径，数字好看但与线上不一致）
- 口径复核：迁移前后数值逐格一致（裸装场景装配中性），跨级必败等设计意图保持

**遗留**：`scripts/numeric_lib/battle2.py`（v175 副本 Boss 多技能矩阵线）用同一批旧签名，**仍未迁移**；
它属「副本平衡矩阵」议题，不在本次三个门禁范围内。