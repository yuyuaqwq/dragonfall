# T10 存量存档兼容审计报告（v130.2f / v130.2f.1）

- 提交范围：39eeb11（v130.2f）+ 62ca50b（v130.2f.1），基线 426e14f
- 审计方法：只读 SQLite（`file:...?mode=ro` URI）直查生产库 + 只读 Python 导入运行时验证（skills 索引双向解析、Battle.from_state 合成往返）；全程未写任何库
- 审计时间：2026-08-26

## 〇、模块统计（改动面）

| 文件 | 改动量 | 存档相关面 |
|---|---|---|
| game/battle.py | +123 | 战斗序列化新字段 `assassin_refund_used`；`_pre_cost_res` 快照；`_zen_hold_mult`/`_assassin_finisher_refund` 等新挂点 |
| game/core/battle_conds.py | +7 | cond 读施放前快照（HC-12） |
| game/data/battle_config.py | +19 | 新增 ZEN_HOLD_CFG / SHADOW_STEALTH_DMG_MULT；龙脉 0.18→0.10 |
| game/data/classes.py | +12 | 苦修档位展示名改名（key 不动） |
| game/data/core_resources.py | +12 | desc 收敛 + overflow_shield 开放（战士/拳师） |
| game/data/skills.py | +51 | 被动改版×6 + 满溢 cond×3 + desc 收敛（**0 个技能 key 改名**） |

**结论先行：0 个 store/connection 层文件改动 → 0 schema 迁移需求；无 P0 / P1 问题。** 六项必查全部通过，证据如下。

## 一、必查项验证结论

1. **表结构**：`game/store/connection.py` 本批次零改动（git diff name-only 仅 6 源文件）。生产库 `players` 建表字段齐全（含 portals/skill_bar/equipped_title 等 `_ensure_legacy_columns` 补列），新字段全部走 JSON 内部键，无需 ALTER。
2. **learned_skills key**：生产库 4 条存量条目（sk_* id 与 BRANCH_SKILLS 中文名双轨）**4/4 全部经当前 skills 索引解析成功，0 悬空**；受改技能（伴奏/鹰眼/战争咆哮/磐石体/神圣坚韧/墓穴护甲/魔力贯穿/暗影之心/龙焰吐息/时停领域/流星陨落/终结·破影一击/幽影刃等）双向索引 roundtrip 21/21 一致——**本批次确实未动任何技能 key**（git diff 证实 skills.py 仅 value 层改动）。
3. **职业存档**：生产库 4 玩家 class_name 全为 cls_id（cls_zhan_shi/cls_novice/cls_mu_shi），**0 行中文名副本**；全库（生产+测试）扫描无 cls_wu_sheng 行，存储契约与其他职业完全一致 → 苦修士→淬势者改名零影响。
4. **已学技能/技能书/成就解锁**：成就表 ach_key 与 achievements.py 均未动；技能书 learn_skill 中文名（龙息之怒/元素湮灭/毒爆术/骷髅海/安眠曲/收割/气爆）本批次未改名 → 存量解锁状态全部有效。
5. **战斗序列化**：`to_state` 写时 `getattr(self,"_assassin_refund_used",False)`（battle.py:442），`from_state` 读时 `st.get(...,False)`（battle.py:496）双兜底。合成验证：新档往返保留 True；删键模拟旧档恢复得 False 且续战正常、再存自动升级新格式；`battle_start_cp` 初始化在恢复时不重触发（battle.py:845）→ 恢复无双重 CP。**旧战斗中断存档兼容性成立**。
6. **desc 快照**：inventory.item_data 确认存 name/desc 快照（生产样本），但本批次 items/shop/craft/quests 零改动 → **未引入任何过期快照**；技能/资源 desc 变更仅运行时展示（面板实时读数据层）。
7. **装备/词条/套装**：affixes/sets/equip_roster 本批次零改动；生产库 equipment key 校验 0 未知。
8. **常量运行时读取**：MECH_STACK_BONUS 0.18→0.10、ZEN_HOLD_CFG 等全部运行时消费；mech_stacks 序列化存 int 层数（未烘焙倍率），中断旧档恢复后按新常数结算 = 预期再平衡，无需迁移。

## 二、P0-P3 清单

### P0（数据损坏/不可读）
**无。**

### P1（功能偏差/必须迁移）
**无。** 逐项证伪：learned_skills 解析 100%；class_name 无 name 副本；战斗旧档缺键兜底路径经合成档验证；desc 快照无新增过期源。

### P2（覆盖缺口/体验问题）
| 级别 | 现象 | 证据 | 影响 |
|---|---|---|---|
| P2 | 旧格式 battle_state 恢复路径**无真实存档样本**：生产库 0 行、tests 3 库均 0 行；`assassin_refund_used` 缺失键兜底从未被线上档踩过 | battle.py:496；探测 test_v1302f_job_quality.db / test_v1302f2_engine_fix.db rows=0 | 已用合成旧档验证通过（probe3），但建议沉淀一条「旧格式 battle_state 恢复 + 续战再存」回归用例，堵住覆盖缺口 |
| P2 | 被动改版对**已学玩家即时生效**（无迁移、无存储状态）：战争咆哮 atk+8%→怒气+1；鹰眼 crit+3%→15% 印记；神圣坚韧/磐石体/墓穴护甲 治疗类→减伤+资源；伴奏 crit+8%→20% 回声；魔力贯穿 法穿5%→时沙+1；暗影之心 desc 与既有机制对齐 | skills.py 各被动 value 层改动；battle.py:2019-2040 伴奏兼容扣除段 | 面板/手感突变属预期机制迭代，非存档问题；需随版本公告说明。伴奏扣除段设计自证安全：`_bz_ps.get("stat")=="crit"` 条件随数据层移除自动失效，零残留双算 |

### P3（备忘/文案/无实质影响）
| 级别 | 现象 | 证据 | 影响 |
|---|---|---|---|
| P3 | 苦修档位改名仅展示层且双保险：存档 class_name=cls_id 无副本；转职路由走 evolve_branches key（武僧/大地武僧/撼岳者**未动**）+ aliases（旧名苦修/武僧/苦修士保留，新名淬势者/锻势行者追加） | classes.py:482-512；skills.py:3305-3308；player.py:722-740 | 「转职 大地武僧」「转职 淬势者」均可达；零迁移 |
| P3 | 文案残留旧名「苦修士」：成就名称/desc、苦修士试炼任务名、技能升级注释、气爆技能书 desc | achievements.py:248-260；quests.py:3257；skill_up.py:237；items.py:2701 | 纯文本观感差异，功能零影响 |
| P3 | `_pre_cost_res` 单入口写入（battle.py:1862）；cond 消费端 getattr 兜底 + None 防御（battle_conds.py:162-167） | — | 当前全施放路径（含额外行动/连击）均经此入口；未来若新增绕过入口的施放路径，仅回落旧语义少触发，不崩 |
| P3 | 龙脉 0.18→0.10 对中断中的旧战斗档立即生效（运行时读取 int 层数） | battle_config.py:21；mech_stacks 序列化格式 | 预期再平衡；若策划要求旧战斗冻结旧数值才需迁移（不推荐） |
| P3 | 新增 `_assassin_refund_used` 旧档恢复为 False → 恢复后首次终结仍可返还 1CP | battle.py:496 | 设计接受（恢复前已返还场景无法追溯）；防重复依赖存档本身 |

## 三、体验/风险总结

- **存量存档零迁移、零破坏**：六项必查全绿。核心原因是本批次改动全部落在「运行时数据/引擎挂点」面，存档契约（cls_id、技能 key、JSON 结构、desc 快照模板）未触碰。
- **最大风险是玩家感知**：被动改版即时生效 + 龙脉数值收敛，建议随公告给出改版一览与数值说明，避免面板突变引发误解。
- **次要风险**：旧格式战斗档恢复路径无真实样本（全库 0 中断档），已合成验证；建议后续测试沉淀回归用例（P2）。
- 审计限制：生产库仅 4 玩家且无 cls_wu_sheng/无战斗中断档，隐藏线改名与旧档恢复均属「契约级 + 合成档」验证，逻辑闭合但非真实数据踩点。