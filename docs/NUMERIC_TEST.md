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

## 测试清单总览

| 文件 | 覆盖什么 | 防什么回归 |
|---|---|---|
| `test_numeric_battle_matrix.py` | 6 基础职业 × 4 种跨级怪（同级 / +5 / -5 / +11 级 dps）胜率矩阵，seeds=8 纯普攻，39 点标准加点 | 防玩家碾压/被碾压极端失衡（最耗时项，`--fast` 即此文件） |
| `test_numeric_ctb_freq.py` | CTB 行动频率比：spd72 刺客 vs spd31 怪、spd41 vs spd31、同级对抗三组，计数“玩家每行动 N 次怪动 1 次” | 防站桩回归（速度差 → 频率差非线性放大） |
| `test_numeric_panel_snapshot.py` | 12 职业（含隐藏）1/11/30/60 级裸装面板快照（max_hp/atk/def/spd/crit/dodge）+ 刺客/战士/法师加点收益快照 | 防无意识成长公式改动、防单属性超模回归 |
| `test_numeric_equip_dependency.py` | 战士 11 级裸装 vs 满装：面板提升幅度 + 同级胜率对比（seeds=6） | 防装备无意义（裸装=满装）或数值爆炸 |
| `test_numeric_monster_curve.py` | 6 种 role（tank/dps/caster/speedster/elite/boss）在 1/11/22/30/60 级 hp/atk/def/spd 成长曲线（对照 stat_templates 模板公式） | 防怪物成长公式误改（含等级段修正/三阶乘区） |
| `test_numeric_skill_power.py` | 12 职业各 2 个代表技能（基础技 + 成型技）的 power/mp/lv/成长率快照 | 防技能倍率误调 |

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

| 文件 | 预计耗时 | 建议频度 |
|---|---|---|
| `test_numeric_battle_matrix.py` | 最重（24 格 × 8 seeds 战斗，估 1~3 分钟） | 每次数值改动必跑；日常开发快检用 `--fast`（即此文件） |
| `test_numeric_equip_dependency.py` | 估 30~60s（含两场 6-seeds 战斗） | 改动装备/战斗公式时必跑 |
| 其余 4 个（panel/monster/skill/ctb） | 各估 <30s | 提交前全量必跑；日常按改到哪个系统跑对应文件 |
| **全量合计** | 估 2~4 分钟 | **任何数值改动提交前必跑全量** |

> 注：脚本每次运行都会打印各文件实际耗时；首轮全量跑完后按实测回填本表。运行期间不要改动任何源文件/数据表（避免中间态误判）。

## 已知失衡基线清单（⚠️ 当前锁定现状，修复后必须收紧断言）

「当前基线 = 当前代码锁定」，含已知失衡点——测试先锁现状保证门禁全绿，**CTB 修复后由主 agent 统一更新断言**（无需也不用个人修代码）。

| # | 失衡点 | 当前基线（锁定） | 修复目标 | 涉及测试 |
|---|---|---|---|---|
| 1 | CTB 行动频率：速度差 2.3 倍 → 频率差 15 倍 | spd72（刺客 11 级 39 全敏）vs spd31（22 级 dps）约 **15:1**（20 回合内怪几乎不动）；spd41 vs spd31 锁定当前实测值 | **≤ 3:1**（CTB 修复后收紧断言） | `test_numeric_ctb_freq.py` |
| 2 | 刺客跨 11 级胜率：本应打不过却碾压 | 11 级全敏刺客 vs 22 级 dps 约 **5~6/8**（跨 11 级正常预期 ≤ 2/8） | **≤ 2/8**（CTB 修复后收紧，断言现按实测宽值锁定并注释“⚠️已知失衡基线”） | `test_numeric_battle_matrix.py` |
| 3 | 同级对抗正常区间 | 11 vs 11 胜率 3/8~7/8（正常对抗，不一边倒） | 保持区间即可（收紧 = 防一边倒回归） | `test_numeric_battle_matrix.py` |

> 其他测试建立过程中浮现的新失衡点：先按“当前实测值锁定 + 注释标注”入基线，再统一排队修复。