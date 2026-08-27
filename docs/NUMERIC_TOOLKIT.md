# 数值工具集 NUMERIC_TOOLKIT（scripts/numeric_lib —— v131 通用化沉淀，2026-08-27）

> **一句话**：多维度、可复用、可扩展、带自检的数值计算工具集。任何数值改动/方案预演/
> 副本校准，都从这里拿"真实玩家模型"的数字，**不再允许临时拼脚本产生残疾结论**。

## 0. 为什么存在（血泪教训）

v131 数值分析发现 `scripts/numeric_calibration.py` 的玩家模型"残疾"：无自由属性点/
无 tier/无词条/无附魔/无药水/技能仅 ×1.5 粗估 → 副本 Boss 结论"110~315 轮全超标"是
假象（真实玩家每轮输出 5~6 倍）；补全乘区后翻盘为"档位分裂"；本轮又在真实引擎裁决下
发现**只算输出不算承伤**会出"48.5 轮可打"的幻觉（35 级玩家实际 5 回合死于 45 级 Boss）。

工具集的设计目标：**默认真实、维度可拆、输出可证、回归有门禁**——不再让下一次分析
从零开始或重复踩坑。

## 1. 架构

```
scripts/numeric_lib/
  __init__.py    统一导出（from numeric_lib import player, team, ...）
  env.py         路径 / GWEN_GAME_DB / UTF-8 引导（与 tests/numeric_sim.py 同口径）
  constants.py   口径常量 + 职业表 + 技能轴 + 档位表（改数值先改这里 + 同步本文档）
  player.py      真实玩家模型：build_player / per_action_dmg / dmg_budget（乘区归因）
  gear.py        装备工厂 make_gear(lv, quality, enhance) + gear_loadout(lv, 档位)
  monster.py     怪物工厂 build(role, lv) + curve_override（预演上下文，自动还原）
  team.py        组队/Boss 模型：boss_hp / team_rounds / team_net_mult / team_matrix（含承伤侧）
  battle.py      真实引擎战斗包装：win_rate / panel（复用 tests/numeric_sim）
  report.py      md_table / to_json / diff_tables（统一输出层）
  cli.py         统一 CLI（player / dmg / calib / team / matrix / diff）
tests/test_numeric_toolkit.py   工具集自检（自动纳入 run_numeric_tests.py 门禁）
scripts/numeric_calibration.py  升级校准工具（默认真实模型，--loadout legacy 对照旧输出）
```

## 2. 玩家模型乘区（默认全开 = 真实玩家）

| 乘区 | 开关 | 默认 | 数值 | 来源 |
|---|---|---|---|---|
| 自由属性点 | opts.attr_points | 开 | 9点+每级3点，按职业主属性 | 27 附章 2.1 |
| tier 转职 | opts.tier | 开 | 30/60/90 → ×1.15/1.30/1.50 | 27 附章 2.2 |
| 攻线分支 | opts.evolve | 开 | atk×1.06（随 tier） | v25 BRANCH_BONUS |
| 技能轴 | opts.skills | 开 | ROTATIONS 循环（替代 ×1.5 粗估） | counts.py 实读 |
| 攻击词条 | opts.affixes | 开 | ×1.20（蓝装 2 条等价收益） | 10 章七 |
| 附魔 | opts.enchant | 开 | crit +4%（蓝装 1 孔上限） | enchant.py |
| 药水 | opts.potion | 开 | 攻击/魔攻 +30% 3 回合 | alchemy.py |
| 暴击期望 | —（crit 参数） | 开 | 暴击×爆伤+幸运一击（legacy 对照可关） | battle.py 引擎路径 |

**归因**：`dmg_budget(cls, lv, gear, edef, mdef)` 逐项开关对比输出每乘区单独倍率。
**验证**：模型预测击杀回合 vs 真实引擎实测 ≤1 回合（tests/test_numeric_toolkit.py 2/6）。

## 3. 组队 / 副本 Boss 模型（32 章三）

```
Boss HP = 模板 × [hp_mult + 0.65 × (人数 - min_players)]   （hp_mult 档位 1.7/2.35/2.85）
组队 DPS = 人均一次行动 × 人数 × TEAM_BUFF(1.10 保守)
击杀轮 = Boss HP / 组队每轮总伤害
承伤轮 = 全队 HP 池 / Boss 单发期望（攻强乘区取 enraged ×1.35 保守）
判定：承伤轮 < 击杀轮×0.9 → 🔴 先死打不过；击杀轮 >60 → 🔴；<15 且多人 → ⚠️ 过速；>30 → 🟡
```

档位（--loadout / LOADOUTS）：
| 档位 | 装备 | 人数 | 用途 |
|---|---|---|---|
| solo_low | 蓝+0 | 1 | 低配可行性下限 |
| solo_mid | 蓝+5 | 1 | 单刷标准（策划案蓝装+3~+5 口径） |
| team_mid | 蓝+5 | 4 | **默认校准档（策划案口径）** |
| team_max | 蓝+9 | 4 | 毕业档（查满配秒杀） |
| legacy | 蓝+0 | 1 | 旧残疾模型（对照升级前输出，防被升级骗） |

## 4. 用法

CLI：
```bash
# 全副本 Boss 轮数表（默认 4人蓝+5 真实模型）
python scripts/numeric_calibration.py [--loadout solo_low|solo_mid|team_mid|team_max|legacy] [--json]
# 面板 + 乘区归因
python scripts/numeric_lib/cli.py player 战士 60 --loadout solo_mid
# 单发伤害 / 击杀回合
python scripts/numeric_lib/cli.py dmg 战士 35 solo_low 16
# 单副本组队矩阵
python scripts/numeric_lib/cli.py team --inst inst_old_king_tomb --loadout solo_mid
# 真实引擎胜率矩阵
python scripts/numeric_lib/cli.py matrix --cls 战士,刺客 --lv 11 --mlv 16,17 --role dps --seeds 8
# 双 JSON diff（方案预演对比）
python scripts/numeric_lib/cli.py diff --before a.json --after b.json
```

代码 API：
```python
from numeric_lib import (PlayerOptions, build_player, per_action_dmg, dmg_budget,
                         gear_loadout, curve_override, team_matrix, win_rate)

opts = PlayerOptions(potion=False)                        # 关药水做敏感性
st = build_player("cls_zhan_shi", 35, gear_loadout(35, "solo_mid"), opts)
d = per_action_dmg("cls_zhan_shi", 35, gear, edef=221, mdef=180)
budget = dmg_budget("cls_zhan_shi", 35, gear, 221, 180)   # 归因表

with curve_override(growth={"dps": {"def": 4.0, "atk": 6.0, "hp": 25}},
                    hp_stage=[(15, 1.0), (30, 1.5), (60, 2.0), (999, 3.0)]):
    rows = team_matrix(loadout="team_mid")                # 方案预演，退出自动还原

wins, avg_round = win_rate("战士", 11, {"str": 39}, {}, "dps", 16, seeds=8)
```

## 5. 已知限制 / 保守口径（重要，用前必读）

1. **技能 Lv.1 保守**：技能倍率按 Lv.1 学得档算，未计技能等级 +10%/级成长 → 真实更高，结论偏悲观（达标=真达标）。
2. **未计**：元素反应、称号、种族天赋、终结技（战士裂地斩等）、控制链/治疗仇恨、法力续航闸门（长局法系打空蓝降级普攻）→ 真实只会更快/更肉，组队结论偏保守。
3. **承伤模型简化**：Boss 单发取物理/魔法高者 ×1.35（enraged），未计 phase_step/low_hp/pv_broken 叠加与技能（倍率 105%~150%）→ 生存侧偏乐观一档，判定留 0.9 缓冲。
4. **组队无全循环实机复测**：instance.py 全状态机（仇恨/CTB 队列/阶段切换）未做端到端模拟；组队 DPS 用"人均×人数×1.1"代码证据估算（策划案公式 + 队伍技能战吼/元素流转）。**待实机复测项**。
5. **dodge 未实装**：build_monster 不产出模板 dodge，PVE 怪闪避恒 0（已知数值 bug，规划修复）。
6. **怪物曲线覆盖只动数据/函数**：curve_override 进程内有效，退出还原（含异常路径）；不落盘。
7. **min_players>1 副本的单刷档**：按最少可进人数算（实际进不去），表内自动 n_eff=mn。

## 6. 验证记录（2026-08-27）

| 验证项 | 结果 |
|---|---|
| legacy 档 vs 升级前 numeric_calibration（22 副本） | 差异 <1.5%（哥布林 119.7 vs 118、老王 280.1 vs 280） |
| 真实模型 vs 真实引擎（战士 11v11，20 seeds） | 击杀回合模型 2.5 vs 引擎 3.0（≤1 回合） |
| 乘区归因单调（6 项全关测试） | 每项关闭伤害必降 |
| curve_override 还原（含异常路径） | 深拷贝还原无污染 |
| 组队公式自洽（32 章三） | 单刷=模板×1.7、4人=模板×4.8、组队净快 ≥20% |
| 真实引擎裁决（35级战士 vs 老王 Boss 蓝+0） | 0/6 全败 5.3 回合死 → 承伤侧必须纳入判定（已实现） |
| 工具集自检 tests/test_numeric_toolkit.py | 25/25 绿（随数值门禁自动跑） |

## 7. 扩展指南（加新维度/乘区）

1. **加乘区**：constants.py 加默认值 → PlayerOptions 加字段 → build_player/per_action_dmg 实现
   → dmg_budget names 表加项 → 本文档口径表更新 → test_numeric_toolkit 3/6 加归因用例。
2. **加档位**：constants.LOADOUTS 加一行（quality/enhance/players/label）→ 表格自动出现。
3. **加副本评估维度**：team.team_matrix 返回 dict 加字段 → numeric_calibration/cli 表列更新 → 测试 6/6 补断言。
4. **改怪物曲线做预演**：永远用 `with curve_override(...)`，禁止直接改数据文件跑脚本（会污染其他调用）。
5. **任何数值改动后**：跑 `python scripts/run_numeric_tests.py` 全绿（含 toolkit 自检）→
   更新 docs/NUMERIC_TEST.md 失衡清单 → 32 章回写（若动策划案表）。