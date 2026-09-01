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
> 插件目录：C:/Users/yuyu/qqbot/data/plugins/dragonfall

---

## 一、任务总目标（鱼鱼拍板）

> "这次你必须把整个游戏的数值模型搭建好"——职业有梯队（S/A/B/C/D）、装备有区分度、数值可验证。
> 鱼鱼特别要求：**计划文档先行**（已写好），表格化展示每职业每维度梯队。

**完整计划文档**：`workspace/v156_NUMERIC_MODEL_PLAN.md`（v1.0，含职业梯队总表、装备区分度方案、转职分支差异化表、6 阶段实施步骤）——**先读它**。

---

## 二、当前进度（已提交 4 个 commit）

| commit | 内容 |
|---|---|
| `4b9105a` | v156 数值修复：技能DPS门禁(142/142) + DOT分类重构(flat/pct/hybrid+Boss打折) |
| `7f941f1` | v156 formula 通用公式层：resolve_formula + _player_dmg_mult（技能/普攻/敌方/装备共用） |
| `860940c` | v156 刺客普攻节奏重标定：cast_atk 0.35→0.8s |
| `e81a246` | v156 技能基础值 + 普攻节奏重标定 + 拳师红线修复（**阶段 1 完成**） |

## 三、阶段 1 已完成（勿重复）

- ✅ 技能基础值 flat：12 + 玩家等级×1 + 技能等级×2（SKILL_FLAT_* 在 skill_up.py）
- ✅ 普攻节奏：战士 1.15s / 游侠 1.0s / 拳师 1.15s / 刺客 0.8s / 法师 1.0s / 牧师 0.6s / 诗人 0.5s
- ✅ 拳师红线修复：钢拳/震地击 power → 1.0（峰值≤40%）
- ✅ 数值工具 _basic_dmg 修正：普攻吃 atk
- ✅ 31 个技能 desc 百分比同步
- ✅ 全量回归 224/224 全绿、数值门禁 10/10 全绿
- ✅ 工作区干净（无未提交改动）

## 四、待做（阶段 2-6，按计划 v2.0 推进）

### 阶段 2（核心）：装备区分度 + 装备加成层
- 武器分系（equip_stats 按 weapon_type）：物理 atk 高 matk 低、法系 matk 高 atk 低
- 防具按 req 分系：重甲(str/vit)HP高、皮甲(agi)spd中、布甲(int)HP低
- 工具集 make_gear 按职业匹配装备
- **make_gear 扩展全加成层**：升级(upgrade.py) + 幸运宝石(gems.py) + 套装(sets.py)（计划 §2.4）
- **词条分系验证**：词条掉落/锻造按职业线加权（计划 §2.4 提案）
- 关键文件：`game/core/stats.py equip_stats()`（36 个调用点，需向后兼容）
- 参考：`game/core/drops.py` 已有 WEAPON_FLAVOR（武器类型特色）

### 阶段 3：职业技能 DPS 梯队 + 技能经济
- 按计划 §1 目标表调 power：拳师降(886→520)、刺客升(481→670)、游侠升(464→570)、牧师降(518→420)
- **新增 mp_budget**：空蓝轮数（MP 池 / 每轮净消耗）（计划 §技能经济）
- **组队矩阵加续航判定**：空蓝轮 < 击杀轮×0.8 → 🔴
- **门禁：法系长盘不断蓝**（满装蓝+5 Lv24）

### 阶段 4：转职分支属性成长差异化 + 组队构成平衡
- BRANCH_BONUS（game/engine.py 第 15 行）扩展为职业×分支表（计划 §3）
- **team.py 支持队伍构成参数**（计划 §4.3）：标准（坦+奶+2输出）/全输出/双坦/无奶
- **奶量模型**：heal_power + 牧师治愈 200% + 诗人 buff → 净承伤
- **门禁 test_numeric_team_comp.py**：标准构成 ✅、边缘构成不无解（计划 §4.4）

### 阶段 5：数值工具完善 + 职业梯队门禁
- numeric_lib 支持职业匹配装备 + 全维度面板（输出+承伤+生存）
- 新增"职业梯队"验证 + 门禁断言

## 五、关键数据/文件速查

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
