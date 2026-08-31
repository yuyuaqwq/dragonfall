# T11【套装/词条/资源数据完整性审计】报告（v130.2 系）

- 日期：2026-08-26　卡号：T11　状态：完成（只读审计，未改任何文件）
- 审计对象：sets.py 12 资源联动套装 / affixes.py 31 资源联动词条 / core_resources.py 12 职业核心资源（+歌者双资源）/ v130.2f 新增表项（SHADOW_STEALTH_DMG_MULT、ZEN_HOLD_CFG、overflow_shield）
- 验证手段：read_file + 只读 Python 脚本（workspace/qa_v1302f/t11_audit.py、t11_audit2.py、t11_craft_check.py、t11_final_check.py），未触碰生产库/源码
- 结论文案：全量 12/12 套装、31/31 词条、41 件装备均配齐；新增表项 key/数值 6/6 一致；发现 **P1×2、P2×2、P3×6**（详见清单）

---

## 一、模块统计

| 模块 | 数量 | 消费点覆盖 | 结论 |
|---|---|---|---|
| 资源联动套装（sets.py v130.2c 段，12 套） | 12 | 15 种 effect 全在 SET_EFFECT_CONSUMED（battle.py:687-691），17 条效果各有实体消费调用 | ✅ 无缺失 |
| 资源联动词条（affixes.py v130.2 段，31 个） | 31 | 31/31 有消费（12 gain 统一读取器 + 6 max 统一读取器 + 13 直连挂点） | ✅ 无缺失 |
| 套装件（SERIES_FIXED_AFFIX + 名册，41 件） | 41 | 名册 41/41、set 字段 12/12 匹配、图纸/商店链路 41/41 | ⚠️ 1 件链路断（P1-2） |
| 核心资源（core_resources.py 12 职业 + 2 副资源） | 14 | 获取/消耗渠道全接通（见 §五 渠道表） | ✅ 无缺失 |
| SHADOW_STEALTH_DMG_MULT（技能名→倍率） | 2 | skills.py 双 key 存在、desc 数值一致、battle 消费时序正确 | ✅ 一致 |
| ZEN_HOLD_CFG（per_zen/cap_zen） | 1 | _zen_hold_mult 双通道消费（普攻/技能），数值与 desc/注释一致 | ✅ 一致 |
| overflow_shield（三线开关） | 3 | 配置 3 处 + 引擎溢出段消费 | ⚠️ 见 P3-5/P3-6 |
| desc 版本记号（12 套 + 31 词条 name/desc） | 43 | 正则扫描 vXX.X / B\d / R\d | ✅ 0 命中 |
| 苦修档位改名（classes.py 展示层） | 2 | 淬势者/锻势行者，key 不动，旧名留别名 | ✅ 一致 |

## 二、① 套装消费点特检（12 套 × 2/4/5 件）

| 套装 | 档位 effect | 消费点（battle.py） |
|---|---|---|
| 血誓战团 | 2: res_gain rage/on_taken | _set_res_proc@2503-2525，事件 on_taken@4822 |
| 余烬军团徽章 | 4: full_rage_pursuit | consume_all 减免@1889-1891；普攻满怒二段追击@2197-2201 |
| 元素使徒 | 2: res_max；4: ultimate_cost_reduce | _set_res_max_bonus@2527（_res_max@742/619 生效）；残点留 1@1885-1893 |
| 时之领主 | 2: cdr_set | 时停领域 CD-1 最低 1@971-975 |
| 巡林长披风 | 2: crit_on_marked | _set_crit_bonus@2538（普攻@2122/技能@3017 并入暴击判定） |
| 猎首远征队徽记 | 4: res_cost_reduce | _energy_cost_after_sets@2565-2568（预检@1828/扣费@1906 同源） |
| 圣典·日冕 | 2: heal_team_on_miracle_t2plus；4: first_hit_immune | _set_miracle_team_heal@2574-2589；受击免伤@4773-4774 |
| 暗夜圣典 | 2: res_gain canticle/undead_on_field；4: elegy_dmg | 回合初亡灵在场@4257；_set_skill_dmg_mult@2595-2599（→3212） |
| 圣徽·誓约 | 2: res_gain on_taken；4: res_gain on_heal | @4822 / @2934 |
| 夜幕合契·影纱 | 2: battle_start_cp；4: finisher_crit；5: combo_finisher_per_layer | 战斗开始@317-319；终结技暴击@2543（→3017）；连段增伤@1070-1075 |
| 蓄势涌动 | 2: battle_start_res | 战前 2 气@320-322 |
| 势不可挡 | 4: chi_skill_phys | _set_skill_dmg_mult@2600-2607（→3212） |

- 空 bonus_2（余烬军团/猎首/势不可挡 3 套）= 无 2 件效果，非缺失。
- 全耗减免「留残点」口径：元素使徒读 value=1（battle.py:1887），余烬军团读 value=1/rage_cost_reduce（1891），与 sets.py desc「-1 最低消耗 1」一致。

## 三、② 词条消费点特检（31 个）

- **gain 类 12**（战意/战吼回响/浴血/残血灼薪/充能汲引/圣辉回响/虔诚护符/暴击回点/暴击蓄能/连段回收/磐息/起手之势）：统一读取器 _affix_res_proc@748-794，事件挂点全接通——battle_start@313、on_attack@2223、on_crit@2225 & 3475、on_skill@2926 & 3454、on_heal@2932、buff_skill@2975、on_cast@3456、combo_skill@3458、on_taken@4991。残血灼薪 cond=hp_lt_30 按怒气三路事件判定（775-777）；圣辉回响 tier 覆盖 gain（785-786）；暴击回点 tier 覆盖 chance（781-784）。
- **max 类 6**（怒火熔铸/神赐容光/圣光之心/盈满背囊/气量强化/节奏之徽）：_res_affix_max_bonus@715-737，rhythm_badge max_total=2 总帽、full_pack tier 10/20 均生效。
- **直连 13**：凝神塑能@806-809、圣徽之佑@811-817、爆发贯体@828-832、终结之技@834-838、沸血浇筑（affix_effects.py:205）、精力潮汐（affix_effects.py:285-298）、精力刀刃@2553-2556、疾风余韵@4230-4233、连段护持@1039-1042（受击@5005）、连段之锋@1052-1055、蓄势精通@1088-1094、印记铭刻@1159-1165、反应催化@1265-1268。
- 词条 effect.res 引用的资源 key（rage/element/energy/faith/cp/chi）全部已注册，_res_max/_res_gain 按 class 回落正确。

## 四、③ 41 件配齐特检

- SERIES_FIXED_AFFIX（affixes.py:774-813）41 件 ↔ 名册（equip_roster.py）41/41 全在，`set` 字段与 SETS 中文名 12/12 匹配；每套 ≥2 件（配齐 2 件效果可达）。
- 品质一致性抽查 8/8：日冕权杖 purple、誓约权杖 blue、元素使徒×4 orange、时之领主×2 orange（与固定词条品质档一致，v130.2d R2 修复生效）。
- 发放链路：37 件紫/橙走图纸（CRAFT_RECIPES 181 条中有 180 条带 roster_id，其中指向 41 件的 36 条全通）；誓约 4 件蓝装商店直售（shop.py，oak_town）。
- ❌ **破竹布靴**：配方 `rec_po_zhu_bu_xue`（craft.py 末尾）**缺 roster_id 字段**（181 条 recipe 中唯一缺失，左邻右舍 rec_po_zhu_hu_tui 等均有）→ drops.py:18 `_BLUEPRINT_RECIPE_RIDS` 过滤后图纸永不产出（Boss 5%/宝箱/垂钓/商店图纸池全途径死，drops.py:92-94 候选判定）→ **势不可挡 4 件效果（chi_skill_phys +15%）实际不可凑齐**（拳套/武袍/护腿 3 件可取，第 4 件不可得）。

## 五、③′ 12 职业核心资源消费点渠道表（core_resources.py）

| 资源 (key) | 获取渠道（引擎消费点） | 消耗渠道（skills.py res_cost/consume_all） |
|---|---|---|
| 怒气 rage | on_attack@2221/2293、on_skill@3452、on_hit@4985、词条/套装增益 | 13 处 res_cost + consume_all(狂怒爆发) @1880-1895 |
| 元素亲和 element | 技能 res_gain dict@2320-2325、元素凝聚@1187、词条 | 10 处 res_cost + consume_all(元素湮灭)，4 件套残点@1884 |
| 精力 energy | regen 30@4327、技能 res_gain、词条/套装 | 30 处 res_cost（50/100 档终结） |
| 信仰值 faith | on_heal@2338/2934、on_hit@4985、词条/套装 | 8 处 res_cost + consume_all(神迹)，二档判定@2581 |
| 连击点 cp | on_attack/on_skill、致命预谋返还@2376-2390 | 10 处 res_cost + consume_all(暗影处刑) |
| 气 chi | on_attack/on_skill、反击回气+2@4891-4895 | 9 处 res_cost + consume_all(破晓之拳) |
| 龙力 dragon_might | on_attack/on_skill/on_hit、regen@4327、龙焰吐息返还 | 4 处 res_cost（终曲/吐息）；MECH_STACK_BONUS 施放前快照放大@3496-3507 |
| 时之沙 time_sand | regen@4327、on_hit/on_skill | 5 处 res_cost（裂隙-1/领域-3 等）；满沙 cond×1.3 快照 |
| 猎印 hunt_mark | 任意命中+1@2340-2343、暴击额外@2371-2372 | 3 处 res_cost（流星陨落-5 满印 cond×1.15） |
| 悼咏 canticle | on_heal/on_hit/on_skill、亡灵祭仪@4258-4266、套装 | 5 处 res_cost（安魂曲-10/献祭暗焰-5），满档 elegy_dmg |
| 影步 shadow_step | on_crit@2360-2364、on_dodge_success@4762-4767、受击清空@4993-4996 | 3 处 res_cost（破影一击-5/幽影刃-3）；潜行乘区@3047-3049 |
| 禅意 zen | on_attack/on_hit/on_skill | 4 处 res_cost（撼岳·终焉-10）；ZEN_HOLD 持有加伤@2157/3197 |
| 共鸣 resonance（副） | 歌类技 res_gain dict@2320-2325 | 4 处 res_cost（启明圣咏-3/终章-5） |
| 回声 echo（副） | 歌类技 res_gain@1195-1206、歌者伴奏 20%@1950-1956 | ECHO_CFG 回合初全队恢复@4343、增益续时@2955（驻留叠层不消耗） |

## 六、④⑤⑥ 新增表项特检

- **SHADOW_STEALTH_DMG_MULT**（battle_config.py:174）：`终结·破影一击`×1.5 / `幽影刃`×1.25 双 key 在 skills.py 均存在（skill_name 与玩家施放名一致），技能 desc「潜行×1.5」「潜行下 ×1.25」与表值一致；引擎消费 battle.py:3029-3049（先捕获 _stealth_hit 再删 buff，时序正确，非潜行恒 1.0），🌙 标签@3358-3359。✅
- **ZEN_HOLD_CFG**（battle_config.py:159 `{per_zen:0.04, cap_zen:10}`）：_zen_hold_mult@1098-1107，消费普攻@2157/技能@3197 双通道；满 10 禅意 +40% 与 core_resources 注释（4%×10）一致；苦修改名 classes.py:482-511（淬势者/锻势行者，key 不动、别名保留）。✅
- **overflow_shield 三线**：cls_zhan_shi（core_resources.py:29）/ cls_wu_seng（:74）/ cls_hymn（:109）配置 True；引擎消费 _res_gain_class@626-628（溢出×5 转 1 回合护盾）。⚠️ 细节问题见 P3-5/P3-6。
- **v130.2f 其余引擎挂点**：cond 施放前快照 _pre_cost_res（battle.py:1862 拍、battle_conds.py:162 读）、亡灵祭仪@4258-4266、致命预谋@1898/1915→2376、反击回气@4891-4895、歌者伴奏@1950-1956 全部接通。✅

## 七、P0-P3 清单

### P0（阻塞上线）
无。

### P1（上线前必修）
| 级别 | 现象 | 证据 | 影响 |
|---|---|---|---|
| P1 | **龙脉终曲/龙力 desc 数值过期**：v130.2f 已把 MECH_STACK_BONUS.dragon_might 0.18→0.10（终曲 EQ 8.96→6.4），但玩家可见文本仍写 +18% | battle_config.py:21（0.10）；skills.py:3074 desc「每点龙力+18%伤害」；core_resources.py:84 desc「每层 +18% 增伤」；真实结算 battle.py:3496-3507（1+10×0.10=×2.0，非 ×2.8） | 战斗面板技能 desc 与实际伤害不符（满龙力终曲实际 ×2.0，展示 ×2.8），数值误导玩家 |
| P1 | **破竹布靴配方缺 roster_id，图纸链路断裂**：`rec_po_zhu_bu_xue` 是 181 条 CRAFT_RECIPES 中唯一无 roster_id 的配方（同段左邻 rec_po_zhu_hu_tui craft.py:2188 有） | craft.py:2191-2200（rec_po_zhu_bu_xue 仅 name/blueprint，无 roster_id）；equip_roster.py:288 声明 source=图纸；drops.py:18 图纸池 = roster_id 过滤、drops.py:92-94 候选判定 | 破竹布靴图纸永不产出（Boss/宝箱/垂钓/商店全途径死），势不可挡仅 3/4 件可得，**4 件效果 chi_skill_phys +15% 实际不可达** |

### P2（尽快处理）
| 级别 | 现象 | 证据 | 影响 |
|---|---|---|---|
| P2 | **影步「潜行出手额外 +1」静默失效（时序死点）**：技能攻击在伤害段先消费并删除 stealth buff，后到的暴击结算读不到潜行状态 | battle.py:3030-3033（删 buff）→ 3473（_on_crit_resource）→ 2362-2363（检查 p_buffs["stealth"] 恒 False）；SHADOW_STEP_CFG.stealth_extra（battle_config.py:166）；core_resources.py:116 desc 承诺「潜行出手额外+1」 | 表项空转，潜行影步出手少了 +1 影步（每次潜行技亏 1 点），desc 承诺未兑现；普攻路径又不消费潜行（见 P3-8） |
| P2 | **灼伤回响条件未落地**：core_resources 注释承诺「命中燃烧目标额外回力（引擎批次 2 挂点）」，实际龙焰吐息为无条件返还 | core_resources.py:82 注释；skills.py 龙焰吐息 res_gain {dragon_might:1}（无条件）；battle.py:2316-2325 无条件结算 | 设计承诺与实现不符（对非燃烧目标也返还 1 龙力；玩家 desc「命中返还」与实际一致，属机制层偏差，⚠️ 以策划定夺是否收紧条件） |

### P3（低优先/说明）
| 级别 | 现象 | 证据 | 影响 |
|---|---|---|---|
| P3 | overflow_shield 护盾 key 硬编码 `"canticle_overflow"`，战士/拳师转盾也顶悼咏名 | battle.py:628 | p_shields 键名/日志语义错位（功能无碍，同 key 叠加刷新） |
| P3 | overflow_shield「冷却 1 回合」注释无实现：每次溢出即转盾，无冷却状态跟踪 | core_resources.py:26/71 注释 vs battle.py:626-628 | 同回合多次溢出可多次转盾（一般受击每回合至多 1-2 次，影响极小） |
| P3 | 词条/套装 res_gain 渠道（_res_gain@592 封顶）不触发满溢转盾，仅 _res_gain_class@626 转化 | battle.py:592 vs 626；血誓战团受击回怒走 _set_res_proc→_res_gain | 满怒后血誓战团/圣徽·誓约等渠道的溢出不转盾（主渠道受击 on_hit 走 _res_gain_class@4985 正常转盾） |
| P3 | battle_config.py:155 注释引用「core_resources.py 禅意 desc 每 1 禅意…」，实际 cls_wu_sheng desc 字段未含该数值（仅注释行 121 有） | battle_config.py:155 vs core_resources.py:121-124 | 注释引用漂移，改 desc 时易漏 |
| P3 | 成就文案「苦修士」与展示层新名「淬势者」不一致 | achievements.py:248-260 vs classes.py:488/510 | 历史固化条目，玩家观感（可不动） |
| P3 | battle.py:3485-3486 注释「dragon_might +18%/终曲满力 ×2.8」过期（与 P1-1 同根因，注释级） | battle.py:3485-3486 | 仅注释误导，不影响结算 |
| P3 | 普攻路径不消费潜行 buff（必暴/乘区仅技能路径生效） | battle.py:2110-2234（_player_attack 无 stealth 引用）vs 3026-3033 | 影步玩家普攻时潜行状态白白保留/浪费（v104 遗留行为，非 v130.2f 回归） |

## 八、体验/风险总结

1. **数据完整性主链路全部打通**：12 套 17 条效果、31 词条、12+2 资源、潜行乘区、禅意乘区、满溢转盾三线，消费点无一缺失（对比早期"纯展示无效果"阶段，v130.2c/d/f 的接线完成度高）。
2. **最大风险 = 破竹布靴**：一张 roster_id 缺失让整套 4 件效果锁死，且是配置型错误（加一行字段即修复），上线前必须补。
3. **次大风险 = 龙力 desc 两处 18% 残留**：v130.2f 收敛数值时漏改玩家可见文本，终曲这类旗舰技能误导性强。
4. 影步 stealth_extra 时序死点属于"表项在、消费点无效"的典型静默失效，建议引擎侧把潜行出手标记（_stealth_hit）传给资源结算而非二次查 buff。
5. ⚠️ 不确定项：灼伤回响是否按设计收条件由策划口径决定；overflow_shield 冷却语义建议与文档对齐。

---
*证据脚本：workspace/qa_v1302f/t11_audit.py / t11_audit2.py / t11_craft_check.py / t11_final_check.py（只读）*