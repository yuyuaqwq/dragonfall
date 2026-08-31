# v153 职业重做差距分析 + 任务卡总依据（2026-09-01 主 agent 侦察）

> 鱼鱼睡前交代：按 v153 重做职业，适配 CTB 战斗引擎；玩家技能已重置，老技能直接删；
> 严格数据驱动；可以开子 agent 但先分析好避免重复；配套内容（道具/装备/材料/任务/剧情）对齐；
> 回合制遗留数值审计（道具效果/装备效果等）。
>
> **本文件是任务卡唯一依据**——子 agent 不允许全量读项目，只读本文件 + 指定数据文件。

---

## 一、引擎现状盘点（已侦察确认）

### 1.1 职业定义 classes.py（419 行）
- 现有：`cls_novice` + 6 基础职业（`cls_zhan_shi / cls_fa_shi / cls_you_xia / cls_mu_shi / cls_ci_ke / cls_wu_seng`）
- **没有独立诗人职业**（v151 把「吟游诗人」放在牧师 B 线转职：`evolve=["吟游诗人(30)","灵魂歌者(60)","黎明颂者(90)"]`）
- 转职线现状 vs v153 目标：

| 职业 | 现有 Lv30/Lv60/Lv90 | v153 目标 | 动作 |
|---|---|---|---|
| 战士 A | 狂战士/狂战统领/战争领主 | 同左 | ✅ 无需改 |
| 战士 B | 盾卫士/坚盾卫士/坚城统帅 | 同左 | ✅ 无需改 |
| 法师 A | 元素法师/元素术士/元素贤者 | **元素使**/元素术士/元素贤者 | 改 Lv30 |
| 法师 B | 奥秘法师/奥秘术士/奥秘贤者 | **奥术学者/奥术大师/奥秘主宰** | 整线改名 |
| 游侠 A | 林语者/自然行者/万木之灵 | **森语者/自然守望者**/万木之灵 | 改 Lv30+Lv60 |
| 游侠 B | 风行者/疾风射手/疾风猎手 | 风行者/疾风射手/**狂风之猎** | 改 Lv90 |
| 牧师 A | 吟游诗人/灵魂歌者/黎明颂者 | **神谕者/大主教/圣光先知** | 整线改（从歌者改神职） |
| 牧师 B | 神谕者/大主教/圣光先知 | **死灵祭司/亡魂引渡者/黯灵君主** | 整线改（B 线改死灵） |
| 刺客 A | 影舞者/暗影之刃/无影之刃 | 同左 | ✅ 无需改 |
| 刺客 B | 毒刃者/淬毒师/蚀骨者 | 同左 | ✅ 无需改 |
| 拳师 A | 格斗士/拳术师/破晓者 | 同左 | ✅ 无需改 |
| 拳师 B | 磐石行者/铁壁行者/磐岩壁垒 | 磐石行者/铁壁行者/**不破之壁** | 改 Lv90 |
| **诗人（新）** | — | **咏叹者/晨曦歌者/天籁颂者**（A）| **新增独立职业 cls_shi_ren** |
| | | **挽歌者/安魂歌者/镇魂挽者**（B）| |

- cast_atk 现状：只有战士(1.4)/刺客(0.7)配了；v153 §0.3 要求全部职业配齐：
  战士 1.4/0.8/2.2、刺客 0.7/0.5/1.6、法师 2.0/0.9/2.4、游侠 0.8/0.5/1.6、牧师 1.2/0.7/2.0、拳师 0.6/0.5/1.8、诗人 1.0/0.7/2.0

### 1.2 技能表（skills.py 3414 行 + skills_v151_overrides.py 2140 行）
- 生效表：`game/data/skills_v151_overrides.py`（`_V151_PLAYER_SKILLS` / `_V151_BRANCH_SKILLS`），**不是** skills.py！
- skills.py 底部有 `PLAYER_SKILLS.update(_V151_PLAYER_SKILLS)` 整体覆盖（v152 大坑：改 skills.py 无效）
- 现状技能数：战士 9+分支、法师 8+分支、游侠 8+分支、牧师 7+分支、刺客 11+分支、拳师 8+分支（v151 表）
- 分支结构：`BRANCH_SKILLS[cls]["branches"] = {1: {分支名: {技能名: info}}, 2: {...}, 3: {...}}`（3-key=30/60/90 级）
- 基础技能 key 用 `sk_` + 拼音 ID；**分支技能 key 用中文名**
- **v153 要整体替换为 7 职业 × 42 技能 = 294 技能**（每职业 8 基础 + 17 A线 + 17 B线）

### 1.3 核心资源 core_resources.py
- 现有：cls_zhan_shi(rage 0-10) / cls_fa_shi(element 0-5) / cls_you_xia(energy 0-100) / cls_mu_shi(faith 0-10) / cls_ci_ke(cp 0-5) / cls_wu_seng(chi?) + 副资源 resonance/echo/vow
- v153 资源口径：
  - 战意 rage 0-10 ✅（引擎一致）
  - 连段 cp 0-5 ✅（引擎一致）
  - 信念 faith 0-10 ✅（引擎一致，v153 改四档负载语义）
  - 破绽 shaken 0-50 ✅（enemy_bar，引擎 `decay_per_turn=4` 要改 1.7）
  - 磐核 GUARD_CORE 0-5 ✅（引擎一致）
  - 专注 energy → **改流量制**：每刻 +18，技能用 `focus_cost` 字段（**引擎 0 处消费，待新增**）
  - 元素亲和 element → **废弃**（v153 元素线改「元素印记」挂敌身）

### 1.4 战斗引擎 battle.py（6423 行，v152 已 CTB 化）
- ✅ 已支持：`_action_cast`（skill.cast/recovery）、`shaken_gain`（推条）、faith/rage/cp/energy 资源、dual_form（狂暴）、mech_stacks、consume_all、召唤、heal、cond、element、multi、pierce、lifesteal
- ❌ **待新增/接线**（v153 新机制，引擎 0 处）：
  - `focus_cost`（游侠专注消耗字段）→ 0 处
  - `enemy_buffs`（元素印记挂敌身）→ 0 处
  - `battle_aura` / `aura_stack`（诗人旋律 + 强度层）→ 0 处
  - `discharge` / `guard_core` 消费（拳师磐核）→ HANDOFF_v151 已知断链
  - `shield_val` 盾值消费 → 0 处（v151 P4.5 已补 13 个 shield 技能但引擎可能没读）
  - DOT（毒/灼烧/流血/腐蚀）刻制化 → 需要核对 §9.3
  - 牧师信念「负载档位」（0-3/4-7/8-9/10 + 每刻 −0.7）→ 需新增
  - 战士狂暴维持（每刻 −0.6）→ dual_form 已有，核对 maintain_cost 语义

### 1.5 其他机制配置
- battle_config.py：ENEMY_BAR_CFG.shaken.decay_per_turn=4 → **改 1.7**（C-13）
- GUARD_CORE_CFG：max=5 / discharge_base=1.0 / discharge_per_core=0.7（✅ 已对齐 v153 §6）
- CURSE_CFG / SOUL_MARK_CFG / DIRGE_CFG / BONE_RUSH_CFG：**死灵线机制全保留**（v151 删入口未删机制）✅

### 1.6 测试
- `scripts/run_all_tests.py`（252 测试文件），AstrBot uv python 跑
- 已有 `scripts/audit_v153.py`（294 技能 16 段校验 0 告警）✅
- 已有 `scripts/calibrate_v153.py`（数值反解标定）✅

---

## 二、v153 差距清单（7 大工作项）

### P1 引擎新字段接线（主 agent 亲写，不派子 agent）
1. **C-13**：`decay_per_turn: 4 → 1.7`（一行改动，先做）
2. **C-12**：4 职业 cast_atk/cast_defend/cast_flee 补录 + 诗人新增（classes.py 数据）
3. **C-16**：游侠专注流量制——`focus_cost` 字段消费 + energy 每刻 +18（替换旧 regen 30/刻）
4. **C-18**：牧师信念四档负载——faith 0-10 + 每刻 −0.7 + 档位（0-3/4-7/8-9/10）
5. **C-17**：诗人 battle_aura + 强度层 + 终章机制（起手/吟唱/终章三档 cast）
6. **元素印记**：enemy_buffs 挂敌身（火/冰/雷 0-3 层 + 结算反应）
7. **磐核 discharge**：guard_core 消费接线（磐岩释能/磐核爆发/气力万法）
8. **DOT 刻制化**：毒/灼烧/流血/腐蚀按 §9.3 每刻一跳 + adapt 耐受
9. **shield_val**：盾值消费核对

### P2 技能数据落库（7 职业 × 42 = 294 技能）
- 生成 `skills_v153.py`（新 override 表，替代 v151 override）
- 数据源：`workspace/skills_v153_parsed.json`（主 agent 已解析）+ v153 文档 §1-§7
- 每技能字段：lv/mp/kind/power(=base)/hits/cast/cd/mech/mech_val/desc + 职业专属（focus_cost/信念/推条）
- 7 个子 agent 各写一个职业，任务卡给字段映射 + 样例 + 技能 JSON 路径

### P3 职业定义（classes.py + core_resources.py + battle_config.py）
- 新增诗人 `cls_shi_ren`（咏叹/挽歌两线，3-key 转职）
- 牧师 B 线改死灵（3 个转职名）+ A 线改神职名
- 法师/游侠/拳师转职改名
- cast_atk 等 6 字段补录
- core_resources 资源表对齐 v153（energy 改流量、element 废弃、新增诗人资源）
- 诗人武器类型：现有 weapon_type 是否有琴/乐器类装备？需侦察（P4 配套）

### P4 配套内容对齐（道具/装备/材料/任务/剧情）
- 侦察：现有道具/装备/套装里引用旧职业名/旧技能名的部分（歌者→诗人独立后归属变化）
- 牧师 B 线死灵化后：暗影神谕相关装备/套装/材料/任务/剧情还原
- 诗人新增：武器/装备/套装/技能学习 NPC/任务/剧情
- v153 §8 召唤物表（骷髅/藤蔓/古树/火元素/雷元素）核对 summons.py
- v153 §9 元素属性/抗性：怪物侧 elem_res/dot_res/immune_dots 数据补录

### P5 回合制遗留数值审计（道具效果/装备效果/套装效果）
- 全项目 grep "N 回合" / "每回合" / "回合" 效果描述 → 判定时刻制化
- 道具 buff 效果（防御药水 3 刻等）核对 cast 字段
- 装备/套装效果（词条 buff 持续刻数）核对
- 依赖 P1 引擎改造完成后才能验证

### P6 测试适配 + 全量回归 + 双仓库提交 + 策划案同步
- 测试断言旧职业名/技能数/机制 → 适配
- `run_all_tests.py` 全绿
- 双仓库提交（dragonfall + design/new_world）
- 策划案同步（09_职业体系.md v153 更新）

---

## 三、字段映射表（子 agent 写技能表唯一依据）

### 3.1 技能 info dict 字段（引擎已消费）
| v153 列 | 引擎字段 | 说明 |
|---|---|---|
| 技能名 | `name` | 中文名，全表唯一 |
| lv | `lv` | 学习等级 |
| mp | `mp` | 蓝耗 |
| kind | `kind` | 物理/魔法/魔法·火/增益/治疗/召唤/嘲讽/真伤 |
| base | `power` | Lv.1 裸倍率（唯一真值源） |
| hits | `hits` | 段数（v153 新增独立字段；无则缺省 1） |
| cast | `cast` | 动作耗时（刻）；缺省走 CAST_SKILL=1.6 |
| cd | `cd` | 冷却（刻） |
| 机制 | `mech` + `mech_val` + 专属字段 | 见 3.2 |

### 3.2 机制字段（v153 → 引擎）
| v153 机制 | 引擎字段 | 状态 |
|---|---|---|
| 命中 +1 战意 | `mech: 'zhan_yi', mech_val: 1` | ✅ 已有 |
| 连段 | `mech: 'lian_duan', mech_val: 1` | ✅ 已有 |
| 元素印记（火/冰/雷） | `element_mark: 'fire'` 等 | ❌ 待新增 |
| 破绽推条 | `shaken_gain: N` | ✅ 已有 |
| 磐核 | `guard_core_gain: N` / `consume_all` | ⚠️ 半支持 |
| 专注消耗 | `focus_cost: N` | ❌ 待新增 |
| 信念 | `faith: N`（+−） | ✅ 已有（档位待改） |
| 诗人旋律 | `melody: '战歌'` + `aura_stack` | ❌ 待新增 |
| 流血/毒/灼烧 | `dot: 'bleed', dot_layers: N, dot_dur: N` | ⚠️ 半支持（核对） |
| 治疗 | `heal: X` 或 kind=治疗 | ✅ 已有 |
| 护盾 | `shield_val: N` | ⚠️ 半支持 |
| 条件倍率 | `cond: {type, mult, label}` | ✅ 已有 |
| AOE | `aoe: 'front'/'all'` | ✅ 已有 |
| 破防 | `pierce: True` | ✅ 已有 |
| 吸血 | `lifesteal: X` | ✅ 已有 |
| 召唤 | `summon: '骷髅兵'` | ✅ 已有 |
| 嘲讽 | kind='嘲讽' | ✅ 已有 |
| 眩晕/定身 | `mech: 'stun', mech_chance: X, mech_val: 2.0` | ✅ 已有 |

> ⚠️ **子 agent 写技能表时，机制字段必须以引擎现有消费为准**。不确定的字段先 grep battle.py
> 确认有消费再写，写错字段 = 静默失效（try/except 吞掉）。机制无法表达的先标 `TODO_ENGINE`，
> 主 agent 统一接线。

---

## 四、任务卡索引（P2 生成后回填）

| 任务卡 | 内容 | 负责人 |
|---|---|---|
| P1-引擎 | 引擎新字段接线（9 项） | 主 agent 亲写 |
| P2-战士 | 战士 42 技能落库 | 子 agent |
| P2-法师 | 法师 42 技能落库 | 子 agent |
| P2-游侠 | 游侠 42 技能落库 | 子 agent |
| P2-牧师 | 牧师 42 技能落库 | 子 agent |
| P2-刺客 | 刺客 42 技能落库 | 子 agent |
| P2-拳师 | 拳师 42 技能落库 | 子 agent |
| P2-诗人 | 诗人 42 技能落库 | 子 agent |
| P3-职业 | 职业定义改（新诗人+转职改名+cast补录+资源表） | 主 agent 亲写 |
| P4-配套 | 配套内容对齐（装备/任务/剧情/怪物） | 子 agent |
| P5-审计 | 回合制遗留数值审计 | 子 agent 审计 + 主 agent 收尾 |
| P6-测试 | 测试适配 + 回归 + 双仓提交 | 主 agent 收尾 |

---

## 五、执行顺序依赖

1. **P1 引擎**（主 agent）→ 引擎支持所有 v153 字段
2. **P2 技能落库**（7 子 agent 并行）→ 294 技能数据就绪
3. **P3 职业定义**（主 agent）→ 诗人/改名/cast 补录
4. **P4 配套内容**（子 agent）→ 装备/任务/剧情对齐
5. **P5 审计**（子 agent 审计 + 主 agent 收尾）→ 回合制效果清理
6. **P6 测试**（主 agent 收尾）→ 回归全绿 + 双仓提交 + 策划案同步

> ⚠️ P2 与 P3 有依赖：技能表按 cls_id 挂载，P3 改职业名不影响 P2（技能表 key 是 cls_id）。
> P2 可以先行。P1 先行是因为 P2 子 agent 需要知道哪些机制字段引擎支持。
