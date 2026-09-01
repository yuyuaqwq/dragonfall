# HANDOFF_v156：全游戏数值模型搭建（交接文档）

> 交接时间：2026-09-01
> 交接人：格温（上一上下文）
> 给新上下文：**先读本文件 + workspace/v156_NUMERIC_MODEL_PLAN.md（v2.2）**，即可继续，无需重新排查。
> **v2.0 更新（2026-09-01 鱼鱼要求）**：主计划已升级覆盖全部数值维度——
> 职业成长/技能（含技能经济 MP/CD/续航）/装备（含加成层：词条/附魔/宝石/套装/升级）/
> **组队打副本平衡性**（队伍构成梯度表 + team_matrix 构成参数 + 门禁）。
> **v2.1 更新（2026-09-01 鱼鱼点名）**：**分阶段数值成长**——P1新手/P2一职/P3二职/P4三职/P5毕业
> 每阶段职业目标表、成长率约束、副本难度目标（计划 §一.5）+ 阶段扫描工具 + 阶段成长门禁。
> **v2.2 更新（2026-09-01 鱼鱼点名"怪物数值/Boss数值"）**：**怪物/Boss 侧数值**（计划 §一.6）——
> 怪物模板现状、相对强度实测（**发现普通怪太脆 1.5-2.6轮 + Boss 后期无威胁 0.9%**）、
> 修复方向（普通怪 HP 上调 + Boss atk 后期上调）、test_numeric_monster_strength.py 门禁。
> ✅ **全部完成（2026-09-01）**：阶段 1-6 全落地，数值门禁 17/17 + 全量回归 231/231 全绿。
> 插件目录：C:/Users/yuyu/qqbot/data/plugins/dragonfall

---

## 一、任务总目标（鱼鱼拍板）

> "这次你必须把整个游戏的数值模型搭建好"——职业有梯队（S/A/B/C/D）、装备有区分度、数值可验证。
> 鱼鱼特别要求：**计划文档先行**（已写好），表格化展示每职业每维度梯队。

**完整计划文档**：`workspace/v156_NUMERIC_MODEL_PLAN.md`（**v2.2**，含职业梯队/装备区分/转职分支/组队平衡/分阶段/怪物Boss 全维度 + 7 阶段实施）——**先读它**。

---

## 二、当前进度（阶段 1-6 已提交，18 个 commit）

| commit | 内容 |
|---|---|
| `4b9105a` | v156 技能DPS门禁(142/142) + DOT分类重构 + Boss打折 |
| `7f941f1` | v156 formula 通用公式层 |
| `860940c` | 刺客普攻节奏重标定 |
| `e81a246` | 技能基础值 + 普攻节奏 + 拳师红线（阶段 1 完成） |
| `f491e32` | **装备分系**（武器weapon_type + 防具req族 + 门禁） |
| `3daa13a` | **转职分支差异化**（BRANCH_BONUS_BY_CLASS 7职业 + 门禁） |
| `9f746b6` | **职业技能 DPS 梯队**（64 技能 power 按目标表） |
| `b4e24c3` | numeric_lib 补诗人 cls_shi_ren |
| `a3e5bcf` | 计划升级 v2.2（怪物/Boss 数值维度 §一.6） |
| `e6e3bf7` | 怪物修复方向实测校准（普通怪HP + Boss atk） |
| `9093a0a` | **组队承伤轮改职业矩阵**（HP池按各槽位真实面板） |
| `1ca417f` | 子agent合并：mp_budget + make_gear全加成层 + team构成CLI |
| `c9d3b1d` | 新数值门禁测试（gear_full/mp_budget/team_comp） |
| `ad21ea2` | **阶段 5**：STAGES 阶段档位 + stage 命令 + stage_growth(220)/monster_strength 门禁 |
| `(阶段6)` | **阶段 6**：NORMAL_HP_STAGE_MULT + BOSS_ATK_STAGE_MULT（怪物/Boss 数值修复）+ 全量基线更新 |

## 三、已完成（阶段 1-6 主体，勿重复）

- ✅ 技能基础值 flat + 普攻节奏 + 拳师红线（阶段 1）
- ✅ **装备分系**（阶段 2）：武器 atk/matk 分系 + 防具 HP/def/spd 分系 + 门禁测试
- ✅ **make_gear 全加成层**（阶段 2.4）：升级/幸运宝石/套装 + 词条分系常量
- ✅ **技能 DPS 梯队**（阶段 3）：拳师降/刺客升/游侠升/牧师降，64 技能，门禁 142/142
- ✅ **mp_budget 技能经济**（阶段 3）：空蓝轮数 + CLI mp 命令 + 12 断言
- ✅ **转职分支差异化**（阶段 4）：BRANCH_BONUS_BY_CLASS 7 职业×攻守线
- ✅ **组队构成平衡**（阶段 4）：TEAM_COMPS 4 构成 + 奶量模型 + 承伤职业矩阵
- ✅ **分阶段数值成长**（阶段 5）：STAGES 档位 + stage 命令（5阶段 DPS/HP/承伤+增幅+怪物侧）+ stage_growth 门禁 220 断言
- ✅ **怪物/Boss 数值修复**（阶段 6）：NORMAL_HP_STAGE_MULT（普通怪 HP 中后期上调）+ BOSS_ATK_STAGE_MULT（非副本 Boss atk 后期上调）+ monster_strength 门禁 29 断言
- ✅ 数值门禁 **17/17 全绿**、全量回归 **231/231 全绿**

## 四、阶段 6 怪物数值修复细节（2026-09-01）

- **触发**：v2.2 实测——普通怪满装 1.5~2.6 轮被秒杀、Boss 后期单发占 HP 0.9% 无威胁
- **根因**：玩家装备乘区（v136 品质/强化/升级/宝石/套装）成长远超怪物模板；玩家 def 涨 27.9 倍、Boss atk 只涨 6.2 倍
- **鱼鱼口径**：裸装 4~6 轮**只约束前期新手**（P1），中后期玩家穿装备战斗，裸装仅参考
- **方案**（数据表下沉 stat_templates.py）：
  - `NORMAL_HP_STAGE_MULT`：普通怪（tank/dps/caster/speedster/healer）HP 等级段乘区
    ≤15 恒 1.0（P1 裸装 5.8 轮达标）→ 16-30 +0.095/级 → 31-60 +0.005/级 → 61+ -0.02/级
    效果：P2 满装 3.7 轮、P3 4.6、P4 5.5、P5 4.6（目标 4~6）
  - `BOSS_ATK_STAGE_MULT`：**非副本 Boss** atk 等级段乘区（副本 Boss 不吃——走 instances atk_mult + 狂暴机制控难，叠加会打崩 4 人队）
    ≤15 恒 1.0（P1 单发占 HP 9.7% 达标）→ 16-30 +0.032/级 → 31-60 +0.055/级 → 61+ +0.045/级
    效果：P2 7.9%、P3 6.9%、P4 11.4%、P5 11.4%（目标 8~12%）
- **口径函数**：`core/stats.py _stage_mult(segments, lv)` 分段斜率模型（与 hp_stage_mult 同风格，纯数据驱动）
- **影响面**：所有普通怪 HP 上调（战斗略长）+ 野外 Boss 后期变强；副本 Boss 战不变（承伤测试 0/22 红）

## 五、收尾（阶段 6b 进行中）

- [ ] 策划案同步（32_数值设计.md 怪物公式节 + 分阶段数值表）——本批提交前完成
- [ ] 双仓提交（dragonfall + dragonfall-designer）
- [ ] 实机冒烟（野外 Boss 后期强度 / 普通怪战斗手感）——待鱼鱼实机验证

## 六、关键数据/文件速查

| 项 | 位置 |
|---|---|
| 职业基础属性 | game/data/classes.py（base/growth） |
| 职业普攻 cast | game/data/classes.py（cast_atk） |
| 技能表 | game/data/skills_v153.py（294 技能） |
| 技能成长 | game/data/skill_up.py（SKILL_UP + SKILL_FLAT_*） |
| 装备属性模板 | game/data/stat_templates.py（EQUIP_SLOT_BASE/SCALING） |
| 装备属性公式 | game/core/stats.py（equip_stats，36 调用点） |
| 装备名册 | game/data/equip_roster.py（req 区分已有 530 件） |
| 战斗引擎 | game/battle.py（技能伤害段 ~4150、普攻段 ~2780） |
| 公式解释器 | game/engine.py（resolve_formula + skill_flat_value） |
| 数值工具集 | scripts/numeric_lib/（player.py/gear.py/constants.py） |
| 数值门禁 | tests/test_numeric_*.py（run_numeric_tests.py 全跑） |
| 全量回归 | scripts/run_all_tests.py（当前 224 测试） |
| 峰值红线 | scripts/burst_scan.py + tests/test_numeric_burst_redline.py |

## 六、验证命令

```bash
cd C:/Users/yuyu/qqbot/data/plugins/dragonfall
# 数值门禁（10 个测试文件）
python scripts/run_numeric_tests.py
# 全量回归（224 测试）
C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe scripts/run_all_tests.py
# 峰值红线（单职业扫描）
C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe scripts/burst_scan.py --cls cls_ci_ke --lv 30 --loadout naked
```

## 七、铁律提醒

- 改数值前 git status 确认工作区干净（上一步已提交）
- 每阶段改完跑测试 + 提交，再动下一块
- 数值结论必须用数值工具（numeric_lib/burst_scan），不能拍脑袋
- 策划案同步：design/new_world/32_数值设计.md（独立 git 仓库，双仓提交）
- 子 agent 任务卡要写死怎么做，避免过度阅读代码

## 八、工作区文档索引

- `workspace/v156_NUMERIC_MODEL_PLAN.md` ← **主计划（先读）**
- `workspace/v156_CLASS_TIER_REDESIGN.md` ← 职业梯队设计草案
- `workspace/v156_SKILL_REDESIGN_SPEC.md` ← 技能重设计规范（子agent用）
- `workspace/v156_skill_fixes.json` ← 61 技能重标定记录
- `workspace/SKILLS_FULL_v156.md` ← 294 技能全表导出
- `workspace/NUMERIC_ISSUE_20260901.md` ← 初版诊断报告
