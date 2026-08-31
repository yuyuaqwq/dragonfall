# S1-B 回血+处决族去模板化设计报告

> 任务卡：`audit_3q/S1_B.md`　公共框架：`audit_3q/S1_FRAMEWORK.md`
> 范围：**20 套**共享 `regen`（10 套）/ `execute`（10 套）模板的套装，各设计**专属 4 件效果**（不再共享 regen/execute），并顺手差异化 2 件套属性。
> 原则：效果唯一、贴合主题、数值守恒（原模板 regen 5% ≈ 每回合回血 5%；execute <30%+25% ≈ 斩杀期望 25%×低血段；新效果 **不强于原模板 +5%**）、引擎兼容（标注 SET_PROC_EFFECTS 注册 / battle.py 直连挂点）、不破坏既有测试（列出受影响）。

---

## 一、现状盘点（20 套）

### regen 组（10 套）
| 套装 | key | 品质 | 当前 2 件 | 当前 4 件（effect） | 槽位（系列装备数） |
|---|---|---|---|---|---|
| 圣徽 | set_sheng_hui | 紫 | mdef .20 / hp .10 / abyss_res .05 / heal_power .05 | **regen**（每回合 5%） | 旧 CLASS_SET 残留（无系列） |
| 布衣 | set_bu_yi | 蓝 | mdef .18 / hp .10 | **regen** | 职业套 5 件（weapon/helm/armor/legs/boots） |
| 祝福 | set_zhu_fu | 蓝 | mdef .18 / hp .10 | **regen** | 职业套 6 件（+necklace） |
| 圣堂 | set_sheng_tang | 紫 | mdef .18 / hp .10 | **regen** | 职业套 5 件 |
| 审判 | set_shen_pan | 紫 | mdef .18 / hp .10 | **regen** | 旧 CLASS_SET 残留 |
| 神恩 | set_shen_en | 橙 | mdef .18 / hp .10 | **regen** | 旧 CLASS_SET 残留 |
| 布衣套 | set_bu_yi_tao | 蓝 | heal_power .08 / mdef .05（class=牧师） | **regen**（bonus_4）+ bonus_4_stats mdef .10 | 职业套 5 件 |
| 祝福套 | set_zhu_fu_tao | 蓝 | heal_power .08 / mdef .05（class=牧师） | **regen** + bonus_4_stats mdef .10 | 职业套 6 件 |
| 圣堂套 | set_sheng_tang_tao | 紫 | heal_power .08 / mdef .05（class=牧师） | **regen** + bonus_4_stats mdef .10 | 职业套 5 件 |
| 护林套 | set_hu_lin_tao | 白 | def .05 | **regen**（bonus_3，3 槽位 armor/legs/boots，3% 回血） | 区域套 3 槽位 |

### execute 组（10 套）
| 套装 | key | 品质 | 当前 2 件 | 当前 4 件（effect） | 槽位 |
|---|---|---|---|---|---|
| 黑铁佣兵 | set_hei_tie_yong_bing | 橙 | crit .10 / atk .10 | **execute**（<30% +25%） | 旧 CLASS_SET 残留 |
| 轻影 | set_qing_ying | 蓝 | crit .08 / atk .10 | **execute** | 旧 CLASS_SET 残留 |
| 夜行 | set_ye_xing | 蓝 | crit .08 / atk .10 | **execute** | 旧 CLASS_SET 残留 |
| 阴影 | set_yin_ying | 紫 | crit .08 / atk .10 | **execute** | 旧 CLASS_SET 残留 |
| 幻影 | set_huan_ying | 紫 | crit .08 / atk .10 | **execute** | 旧 CLASS_SET 残留 |
| 午夜 | set_wu_ye | 橙 | crit .08 / atk .10 | **execute** | 旧 CLASS_SET 残留 |
| 轻影套 | set_qing_ying_tao | 蓝 | crit .05 / atk .08（class=刺客） | **execute** + bonus_4_stats crit .05 | 职业套 5 件 |
| 夜行套 | set_ye_xing_tao | 蓝 | crit .05 / atk .08（class=刺客） | **execute** + bonus_4_stats crit .05 | 职业套 5 件 |
| 阴影套 | set_yin_ying_tao | 紫 | crit .05 / atk .08（class=刺客） | **execute** + bonus_4_stats crit .05 | 职业套 5 件 |
| 霜猎套 | set_shuang_lie_tao | 紫 | crit .05 | **execute**（bonus_3，3 槽位，<30% +20%） | 区域套 3 槽位 |

要点：
- **职业套（布衣/祝福/圣堂/轻影/夜行/阴影 + 其套）与旧 CLASS_SET 残留（圣徽/审判/神恩/黑铁/幻影/午夜）是两套不同 key 的套装**，装备可并存，设计各自独立（effect 名也不可复用）。
- 职业套 4 件目前是「bonus_4.effect + bonus_4_stats」双轨——特效段与属性段分别由 engine.py set_bonus_4（battle 战斗侧）与 set_bonus_2 聚合（>=4 件时 bonus_4_stats）消费，不冲突。
- **护林套/霜猎套是区域 3 槽位**（armor/legs/boots），engine.set_bonus_4 对 cnt>=3 读 bonus_3.effect → 分发走 `_set_attack_proc`（battle.py:4092，on_hit 型）或回合开始/受击直连。护林=回血型 → **回合开始直连挂点**（同 battle.py:4989 regen 分支模式）；霜猎=斩杀型 → **on_hit 型 SET_PROC_EFFECTS 注册**（普攻/技能双端自动生效，零新增挂点）。
- 圣徽 2 件已差异化（abyss_res/heal_power，被 test_v106_1/test_v106_2 断言），**2 件不动**；其余 2 件顺手差异化（见第四节）。

---

## 二、专属效果设计表（20 套，全部唯一 effect 名）

> 强度基准：原 regen 5% ≈ 每回合回血 5% max_hp；原 execute <30% +25% ≈ 低血段期望增伤（按 30% 低血窗口 ≈ 0.30×0.25 ≈ 7.5% 期望；框架以「等效期望 ≤ 原模板 +5%」为准）。

### 回血组 10 套

**1. 圣徽（紫，旧 CLASS_SET 残留）—— 圣辉庇护 `holy_halo_shield`**
- **触发**：受击型（battle.py `_damage_player` 直连分支，同 reflect battle.py:5762 模式）
- **描述**：被攻击命中后，**将本次伤害的 20% 转化为护盾**（`_add_shield("holy_halo", val, 2)`；每回合最多 1 次，防多段受击刷盾）
- **数值**：dmg×0.20 转盾（2 回合）
- **强度对照**：受击伤害 20% 转盾 ≈ 等效 20%×受击频率减伤 ≈ 10% 期望；原 regen 5%/回合 ≈ 5% 期望。**新 ≈ 原 200%（超限）→ 降档为 10%**：dmg×0.10 转盾（≈5% 期望）贴合"圣徽=魔防+回血"的守护主题。
- **引擎**：`_damage_player` 命中结算段新增直连分支（读 `E.set_bonus_4` 含 `"holy_halo_shield"` 时 roll）；**不注册 SET_PROC**（非攻击触发）。

**2. 布衣（蓝，牧师职业套）—— 布衣愈合 `cloth_regen_battle`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率回复 8% max_hp 生命（牧师布衣法袍的朴素祷愈）
- **数值**：chance 0.30，回复 max_hp×0.08
- **强度对照**：0.30×8% = **+2.4% 期望回血/回合**；原 regen 5% ≈ 5%。**新 ≈ 原 48%**，贴合"布衣=初阶牧师"的回血主题（触发式而非回合制，机制差异化）。
- **引擎**：注册 `SET_PROC_EFFECTS["cloth_regen_battle"]`（handler 内 `player["hp"]=min(max_hp, hp+int(max_hp*0.08))`，`_set_chance("cloth_regen_battle",0.30)`）。

**3. 祝福（蓝，牧师职业套）—— 祝福咏叹 `bless_chant_mp`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 35% 概率回复 5% max_mp 魔力（"祝福"不止于回血——牧师的续航咏叹）
- **数值**：chance 0.35，回复 max_mp×0.05
- **强度对照**：0.35×5% = **+1.75% 期望回蓝/回合**（蓝条对牧师 = 技能频率 = 治疗量/输出折算 ≈ 3.5% 等效）；原 regen 5% 回血。**新 ≈ 原 70%**，贴合"祝福"宽泛祝福（血/蓝双维）主题。
- **引擎**：注册 `SET_PROC_EFFECTS["bless_chant_mp"]`（handler 写 `player["mp"]=min(max_mp, mp+...)`）。

**4. 圣堂（紫，牧师职业套）—— 圣堂领域 `holy_field_heal`**
- **触发**：回合开始（battle.py:4989 regen 分支改造为数据驱动直连）
- **描述**：每回合开始，若生命低于 50%，回复 6% max_hp（低血优先的圣堂结界）；否则回复 3%
- **数值**：hp<50% 时 6%，否则 3%（条件回血）
- **强度对照**：期望 = 0.5×6% + 0.5×3% ≈ **4.5%/回合 ≈ 原 regen 5% 的 90%**（且有低血判定，防溢出浪费）。贴合"圣堂=神圣殿堂守护"主题。
- **引擎**：battle.py:4989 的 `regen`/`regen_strong` 硬编码分支**扩展为数据驱动**——`if eff == "holy_field_heal"` 读 bonus_4 的 `low_pct`/`heal_low`/`heal_high` 字段（缺省兜底 0.06/0.03）；**改 1 处回合开始分支**；不注册 SET_PROC。

**5. 审判（紫，旧 CLASS_SET 残留）—— 审判净化 `judge_purify_heal`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 25% 概率**净化自身 1 个负面效果**（`p_buffs` 减益随机移除 1 个）并回复 4% max_hp
- **数值**：chance 0.25，净化 1 减益 + 回血 4%
- **强度对照**：回血侧 0.25×4% = +1% 期望；净化侧 ≈ 条件性解控（高价值但稀有触发）。合计 ≈ **原 regen 5% 的 40%**（净化作为主题卖点）。贴合"审判=净化"方向（任务卡点名）。
- **引擎**：注册 `SET_PROC_EFFECTS["judge_purify_heal"]`（handler 内遍历 `p_buffs` 移除首个负面键——负面键白名单：`spd_down/poison/mortal_wound/atk_down/...` 或按 `_NEG_BUFF_KEYS` 常量；净化后回血）。

**6. 神恩（橙，旧 CLASS_SET 残留）—— 神恩爆发 `divine_grace_burst`**
- **触发**：回合开始（battle.py:4989 扩展）
- **描述**：每回合开始回复 5% max_hp；**若本回合内生命首次低于 30%，立即额外回复 15% max_hp（每场 1 次）**
- **数值**：回合 5% + 低血救急 15%（每场 1 次）
- **强度对照**：常态 5% = 原 regen 100%；救急 15% ≈ 原模板 +15%×触发概率（约 0.2 触发 ≈ +3% 等效）≈ **原 +3% 内**。贴合"神恩=爆发治疗"方向（任务卡点名）。
- **引擎**：battle.py:4989 分支扩展（读 bonus_4 `pct` 0.05 + `emergency_pct` 0.15）；低血救急在 `_damage_player` 扣血后判定（`if eff=="divine_grace_burst" and not used and hp<30%`）——**改 1 处回合开始分支 + 1 处受击低血判定**；不注册 SET_PROC。

**7. 布衣套（蓝，牧师职业套）—— 布衣圣愈 `cloth_heal_overflow`**
- **触发**：治疗技能施放后（battle.py `_skill_heal` 治疗段扩展）
- **描述**：治疗技能的治疗量 +8%；**治疗溢出（满血）时，溢出量 50% 转化为护盾**（圣愈不浪费）
- **数值**：heal ×1.08；溢出 → shield = overflow×0.50（2 回合）
- **强度对照**：+8% 治疗 ≈ 原 regen 5% 回血的 160%？——注意治疗技能是**主动消耗蓝的回合行动**，不是白嫖回合回血；等效按"牧师每 2 回合放一次治疗"折算 ≈ **原 80%**。溢出转盾为附加（条件性强）。贴合"布衣=牧师新手"的治疗主题。
- **引擎**：`_skill_heal` 治疗段（battle.py:3244 圣光套 2 件 he 旁）新增 `_set_eff(player,"cloth_heal_overflow",4)` 分支（heal×1.08 + 溢出转盾 `_add_shield`）；**改 1 处治疗段**；不注册 SET_PROC。

**8. 祝福套（蓝，牧师职业套）—— 祝福护佑 `bless_ward_shield`**
- **触发**：受击型（`_damage_player` 直连）
- **描述**：被攻击命中时 25% 概率获得护盾（8% max_hp，3 回合；与既有 p_shields 同源叠加）
- **数值**：chance 0.25，shield = max_hp×0.08（3 回合）
- **强度对照**：0.25×8% = **+2% 期望护盾/受击**（受击频率折算 ≈ 原 regen 5% 的 40~80%）。贴合"祝福=守护祝福"主题。
- **引擎**：`_damage_player` 命中结算段直连分支（同 1 号模式）；**不注册 SET_PROC**。

**9. 圣堂套（紫，牧师职业套）—— 圣堂壁垒 `holy_bastion_def`**
- **触发**：受击型（passive）——**stats 型 effect**（bonus_4.stats 已有 mdef .10，追加 mdef 换防御倾向）
- **描述**：**受击伤害 -5%**（常驻减伤）+ 魔防 +10%（既有 bonus_4_stats 保留）
- **数值**：`dmg_taken -5%`（直连）；bonus_4_stats mdef .10 保留
- **强度对照**：-5% 常驻减伤 ≈ 原 regen 5% 的 100%（减伤 vs 回血等效，且减伤防溢出更稳定）。贴合"圣堂=神圣壁垒"。
- **引擎**：`_damage_player` 受击结算段直连（`if "holy_bastion_def" in E.set_bonus_4(...): dmg=max(1,int(dmg*0.95))`）；**改 1 处受击段**；不注册 SET_PROC。

**10. 护林套（白，区域 3 槽位）—— 护林再生 `ranger_regen_wild`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 40% 概率回复 5% max_hp（护林人在林中战斗的野性再生；bonus_3 型效果）
- **数值**：chance 0.40，回复 max_hp×0.05
- **强度对照**：0.40×5% = **+2% 期望回血/回合**；原 regen（3% 区域版）≈ 3%。**新 ≈ 原 67%**。贴合"护林=自然再生"（由回合白嫖改为攻击触发，机制差异化）。
- **引擎**：注册 `SET_PROC_EFFECTS["ranger_regen_wild"]`（handler 与 2 号同构）；**bonus_3 型**由 engine.set_bonus_4 在 cnt>=3 时读 bonus_3.effect 分发到 `_set_attack_proc`，零新增挂点。

### 处决组 10 套

**11. 黑铁佣兵（橙，旧 CLASS_SET 残留）—— 黑铁斩杀 `iron_execute_rampage`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：对生命低于 40% 的敌人，攻击命中时 30% 概率**追加一次 50% 攻击力的斩杀**（佣兵的猎杀本能）
- **数值**：cond_hp 0.40，chance 0.30，追加 0.50×atk
- **强度对照**：0.30×0.50 = +15% 期望（40% 低血窗口内）；按 40% 窗口折算全局 ≈ **+6% ≈ 原 execute 期望**（原 <30%+25% ≈ 7.5%）。**≈ 原 80%**，贴"黑铁=橙装佣兵"的强斩杀感。
- **引擎**：注册 `SET_PROC_EFFECTS["iron_execute_rampage"]`（handler 内先判 `hp_ratio<0.40` 再 roll；追加伤害走 `calc_damage`+`_damage_enemy`）。

**12. 轻影（蓝，旧 CLASS_SET 残留）—— 轻影连刺 `shadow_combo_double`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 25% 概率**追加一次 40% 攻击力的连刺**（轻影=轻快连击）
- **数值**：chance 0.25，追加 0.40×atk
- **强度对照**：0.25×0.40 = **+10% 期望增伤**；原 execute ≈ 7.5%。**新 ≈ 原 +2.5%（+5% 上限内）**。贴合"轻影=连击"方向（任务卡点名）。
- **引擎**：注册 `SET_PROC_EFFECTS["shadow_combo_double"]`（与 thunder handler 同构，数值读 bonus_4 chance/atk_pct）。

**13. 夜行（蓝，旧 CLASS_SET 残留）—— 夜行背刺 `night_backstab`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时，**若敌人处于满血**，本次攻击伤害 +25%（夜行者的潜行背刺）；否则 20% 概率附加 5% max_hp 真伤
- **数值**：满血 +25% 增伤；非满血 20% 概率 5% max_hp 真伤
- **强度对照**：满血段（首击）≈ 0.25×首击占比 ≈ +5% 期望；真伤段 0.20×5% ≈ +1%。合计 ≈ **+6% ≈ 原 execute 80%**。贴合"夜行=暗夜背刺"。
- **引擎**：注册 `SET_PROC_EFFECTS["night_backstab"]`（handler 读 enemy hp/max_hp 判满血分支；真伤段 `_damage_enemy` dmg_type 走 calc_damage true）。

**14. 阴影（紫，旧 CLASS_SET 残留）—— 阴影蚀刻 `shadow_etch_vuln`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率给敌人挂 1 层「阴影蚀刻」（debuffs.mark 层数 +1，上限 5，**每层 +15% 受伤害**——弱化版标记，机制不同）
- **数值**：chance 0.30，叠层 +1（cap 5）
- **强度对照**：0.30×15% ≈ **+4.5% 期望增伤（叠层后）**；原 execute ≈ 7.5%。**新 ≈ 原 60%**，且需叠层（条件性）。贴合"阴影=持续侵蚀"。
- **引擎**：注册 `SET_PROC_EFFECTS["shadow_etch_vuln"]`（叠层复用 `enemy.debuffs["mark"]` 结构；**每层 +15% 需在 `_apply_mark`（battle.py:4591）按 effect 名分档**——函数内 `if "shadow_etch_vuln" in E.set_bonus_4(...): pct=0.15 else 0.20`，**改 1 处 `_apply_mark`**）。

**15. 幻影（紫，旧 CLASS_SET 残留）—— 幻影分身 `phantom_echo`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 20% 概率**追加一次 60% 攻击力的幻影斩**；若本次为暴击，追加概率提升至 35%
- **数值**：chance 0.20（暴击时 0.35），追加 0.60×atk
- **强度对照**：0.20×0.60 = +12% 期望；暴击联动 0.35×0.60 = +21%（需暴击前置）。全局 ≈ **+13% ≈ 原 execute +5.5%**（略超 → 降档 0.15/0.30：0.15×0.60=9%，暴击 0.30×0.60=18%，≈原 +1.5%）贴合"幻影=虚实难测"。
- **引擎**：注册 `SET_PROC_EFFECTS["phantom_echo"]`（handler 读 `is_crit`？——SET_PROC 签名无 is_crit，需**扩展 `_set_attack_proc` 传 is_crit**（battle.py:4092 普攻/技能双端调用处传参），或 handler 内读 `battle._last_crit` 标记；**改 1 处分发签名**）。

**16. 午夜（橙，旧 CLASS_SET 残留）—— 午夜暗杀 `midnight_assassinate`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：对生命低于 30% 的敌人，攻击命中时 **35% 概率直接处决（斩杀：追加 40% 攻击力真伤）**
- **数值**：cond_hp 0.30，chance 0.35，追加 0.40×atk 真伤
- **强度对照**：0.35×0.40 = +14% 期望（低血窗口内）；按 30% 窗口折算 ≈ **+4.2% ≈ 原 execute 56%**。贴合"午夜=暗杀者"（任务卡点名，处决保留但机制不同——概率真伤斩杀而非无条件增伤）。
- **引擎**：注册 `SET_PROC_EFFECTS["midnight_assassinate"]`（handler 判 `hp_ratio<0.30` 再 roll；真伤段）。

**17. 轻影套（蓝，刺客职业套）—— 轻影连击套 `shadow_combo_cp`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率**额外获得 1 连击点**（刺客核心资源；配合终结技）
- **数值**：chance 0.30，`_res_gain(player,"cp",1)`
- **强度对照**：0.30×1cp ≈ 每 3 次攻击多 1 连击点 ≈ 终结技频率 +33% ≈ 折算增伤 **+6~8% ≈ 原 execute 100%**。贴合"轻影=连击/连点"方向。
- **引擎**：注册 `SET_PROC_EFFECTS["shadow_combo_cp"]`（handler 内 `battle._res_gain(player,"cp",1)`，走既有核心资源上限管线）。

**18. 夜行套（蓝，刺客职业套）—— 夜行潜行套 `night_stealth_exec`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时，**若敌人生命低于 30%**，30% 概率使下一次攻击必定暴击（`p_buffs["stealth"]=1`，潜行必暴）
- **数值**：cond_hp 0.30，chance 0.30，buff stealth 1 回合
- **强度对照**：0.30×必暴（≈ 暴击段 +50%×暴率差 ≈ +15% 单次）折算低血窗口 ≈ **+4.5% ≈ 原 execute 60%**。贴合"夜行=潜行暗杀"。
- **引擎**：注册 `SET_PROC_EFFECTS["night_stealth_exec"]`（handler 写 `p_buffs["stealth"]`，由既有潜行必暴体系消费——**零新增挂点**）。

**19. 阴影套（紫，刺客职业套）—— 阴影侵蚀套 `shadow_erode_poison`**
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率给敌人叠 1 层**毒**（debuffs.poison n+1，上限 5；走既有 DOT 体系结算）
- **数值**：chance 0.30，poison +1 层（cap 5）
- **强度对照**：poison 每层 ≈ atk×0.5+max_hp×1.5% 每回合；0.30 触发 × 平均 2 层 ≈ **+4~6% 期望 ≈ 原 execute 60~80%**（DOT 有结算延迟与适应机制，天然弱于直伤）。贴合"阴影=毒蚀"。
- **引擎**：注册 `SET_PROC_EFFECTS["shadow_erode_poison"]`（handler 复用 burn 叠层模式写 `enemy.debuffs["poison"]`；DOT 结算走 `_tick_dots` 既有体系——**零新增挂点**）。

**20. 霜猎套（紫，区域 3 槽位）—— 霜猎冰冻 `frost_hunt_freeze`**
- **触发**：on_hit（SET_PROC_EFFECTS，bonus_3 型）
- **描述**：攻击命中时 20% 概率**冻结敌人 1 回合**（Boss 免疫退化为减速 40%，走 `_freeze_enemy` 既有语义）
- **数值**：chance 0.20，freeze 1 回合（Boss→减速）
- **强度对照**：0.20×1 回合控制 ≈ 等效减伤/输出窗口 +5~6%（控制价值高但受 Boss 免疫/饱和限制）≈ **原 execute（20% 区域版）≈ 100%**。贴合"霜猎=冰冻处决"方向（任务卡点名）。
- **引擎**：注册 `SET_PROC_EFFECTS["frost_hunt_freeze"]`（handler 调 `_freeze_enemy` 既有函数；bonus_3 由 engine 分发，零新增挂点）。

---

## 三、引擎改动清单

### 需注册 SET_PROC_EFFECTS（on_hit 型，core/affix_effects.py 新增 handler，共 14 个）
| effect 名 | 套装 | 挂点 | 备注 |
|---|---|---|---|
| cloth_regen_battle | 布衣 | SET_PROC | 与 2 号同构 |
| bless_chant_mp | 祝福 | SET_PROC | 回蓝 |
| judge_purify_heal | 审判 | SET_PROC | 净化+回血 |
| ranger_regen_wild | 护林套 | SET_PROC（bonus_3 型） | 区域 3 槽位 |
| iron_execute_rampage | 黑铁佣兵 | SET_PROC | cond_hp 0.40 |
| shadow_combo_double | 轻影 | SET_PROC | 连刺 |
| night_backstab | 夜行 | SET_PROC | 满血背刺 |
| shadow_etch_vuln | 阴影 | SET_PROC + **改 `_apply_mark`（battle.py:4591）分档 15%/20%** | 叠层标记 |
| phantom_echo | 幻影 | SET_PROC + **改 `_set_attack_proc`（battle.py:4092）签名传 is_crit** | 暴击联动 |
| midnight_assassinate | 午夜 | SET_PROC | 概率真伤斩杀 |
| shadow_combo_cp | 轻影套 | SET_PROC | 连击点 |
| night_stealth_exec | 夜行套 | SET_PROC | 潜行必暴 |
| shadow_erode_poison | 阴影套 | SET_PROC | 毒叠层 |
| frost_hunt_freeze | 霜猎套 | SET_PROC（bonus_3 型） | 冻结/减速 |

### 需改 battle.py 硬编码/直连分支（非 on_hit 型，6 处）
| 挂点 | 位置 | 改动 |
|---|---|---|
| 回合开始回血 | battle.py:4989（regen/regen_strong 硬编码分支） | 扩展为数据驱动：新增 `holy_field_heal`（4 号圣堂）/ `divine_grace_burst`（6 号神恩）分支，读 bonus_4 字段（low_pct/heal_low/heal_high/pct/emergency_pct） |
| 受击转盾 | battle.py:5762 附近（`_damage_player` 命中结算段） | 新增 `holy_halo_shield`（1 号圣徽）/ `bless_ward_shield`（8 号祝福套）直连分支 |
| 受击减伤 | battle.py `_damage_player` 结算段 | 新增 `holy_bastion_def`（9 号圣堂套）常驻 -5% 分支 |
| 治疗段 | battle.py:3244（圣光套 2 件治疗 +10% 旁） | 新增 `cloth_heal_overflow`（7 号布衣套）heal×1.08 + 溢出转盾 |
| 低血救急 | battle.py:5831（`player["hp"]` 扣血后） | 新增 `divine_grace_burst`（6 号神恩）低血 <30% 每场 1 次 +15% 救急 |
| 标记分档 | battle.py:4591（`_apply_mark`） | `shadow_etch_vuln`（14 号阴影）每层 +15% 分档 |
| 分发签名 | battle.py:4092（`_set_attack_proc`） | 传 is_crit 供 `phantom_echo`（15 号幻影）暴击联动 |

### 引擎零改动（纯数据层）
- `bless_ward_shield`/`holy_bastion_def`/`cloth_heal_overflow`/`divine_grace_burst`/`holy_field_heal` 为 battle.py 直连消费（不注册 SET_PROC，避免 test_v98_05_registry 的「非攻击类特效不得注册为攻击特效」断言告警）。
- 新增 effect 需同步加入 `Battle.SET_EFFECT_CONSUMED`（battle.py:802）——供 test_v1252_audit_closure 的「套装 effect 全部有消费」反查通过；**注意：on_hit 型注册 SET_PROC_EFFECTS 的 14 个不需进 SET_EFFECT_CONSUMED**（由 SET_PROC 注册表消费），直连型 6 个需进。

### 2 件套属性差异化（顺手，数值守恒）
| 套装 | 旧 2 件 | 新 2 件 | 说明 |
|---|---|---|---|
| 圣徽 | mdef .20/hp .10/abyss_res .05/heal_power .05 | **不变** | test_v106_1/v106_2 断言，不动 |
| 布衣/祝福/圣堂/审判/神恩 | mdef .18/hp .10 | 布衣 mdef .16/hp .12；祝福 mdef .18/hp .10/**heal_power .03**；圣堂 mdef .20/hp .10；审判 mdef .18/hp .10/**tenacity .03**；神恩 mdef .18/hp .12/**heal_power .05** | 蓝/紫/橙 梯度错开 |
| 布衣套/祝福套/圣堂套 | heal_power .08/mdef .05 | 布衣套 heal_power .08/mdef .05/**hp .05**；祝福套 heal_power .10/mdef .05；圣堂套 heal_power .08/mdef .08 | 梯度差异化 |
| 黑铁佣兵 | crit .10/atk .10 | **不变**（橙装已独特） | — |
| 轻影/夜行/阴影/幻影/午夜 | crit .08/atk .10 | 轻影 crit .08/atk .10；夜行 crit .10/atk .08；阴影 crit .08/atk .10/**pene_phys .03**；幻影 crit .06/atk .12；午夜 crit .10/atk .12 | 蓝/紫/橙 梯度 |
| 轻影套/夜行套/阴影套 | crit .05/atk .08 | 轻影套 crit .05/atk .08/**spd .03**；夜行套 crit .06/atk .08；阴影套 crit .05/atk .08/**crit_dmg .05** | 梯度 |
| 护林套 | def .05 | **不变**（白装保底） | — |
| 霜猎套 | crit .05 | crit .05/**atk .03** | 补攻击向 |

---

## 四、受影响测试

| 测试文件 | 影响点 | 处理 |
|---|---|---|
| tests/test_v136_phase6_equip.py:175/188 | 断言 `set_hu_lin_tao.bonus_3.effect == "regen"` 与 `"regen" in effs3` | **改断言**为 `ranger_regen_wild` |
| tests/test_v98_05_registry.py:199 | 直接调 `AFX.SET_PROC_EFFECTS["execute"]` 测处决 handler | **保留 execute 注册**（旧 effect 名 handler 不删，仅数据不再引用）；若删 handler 需同步改测试 |
| tests/test_v98_05_registry.py:239-245 | 断言 6 种攻击特效全注册 + 非攻击类不注册 | 新增 14 个 SET_PROC handler 后 `implemented` 集合需**同步扩充**（否则 `implemented <= SET_PROC_EFFECTS` 仍过，但反向「SET_PROC 键 ⊆ 套装数据键」由 test_v1252_audit_closure 检查）；**建议保留 6 个旧 handler 防测试红** |
| tests/test_v1252_audit_closure.py:204-222 | `no_stats_eff - SET_PROC_EFFECTS - {"reflect","regen","regen_strong"} - SET_EFFECT_CONSUMED` 空集检查 | 直连型 6 个 effect（holy_halo_shield/bless_ward_shield/holy_bastion_def/cloth_heal_overflow/divine_grace_burst/holy_field_heal）**必须加入 `Battle.SET_EFFECT_CONSUMED`**，否则红 |
| tests/test_v106_1_attributes.py:76 | 圣徽 2 件 abyss_res 断言 | 2 件不动 → 不受影响 |
| tests/test_v106_2_identity.py:110 | 圣徽 heal_power 断言 | 2 件不动 → 不受影响 |
| tests/test_stage8_equip_affix.py:107/213/261/363 | 词条级 `execute`/`regen`（非套装） | 套装去模板不影响词条 → 不受影响 |
| tests/test_v107_mech.py:40 | 被动级 `execute`（影武者） | 非套装 → 不受影响 |
| tests/test_v140_novice_effects.py | `novice_regen_heal`（新手特效） | 非套装 → 不受影响 |
| tests/test_v64_passive.py | 被动神恩（技能被动） | 非套装 → 不受影响 |
| tests/test_v59_battle_status.py:32 / test_v59_stack_cap.py:26 | 神恩叠层（技能 mech bless） | 非套装 → 不受影响 |
| tests/test_v1302c_mechanics.py | `_tailwind_regen_bonus`（疾风余韵） | 无关 → 不受影响 |
| tests/test_v136_phase6_equip.py:44-47/131-133 | 系列映射/名册存在性断言 | 只涉及装备名/系列 → 不受影响（effect 名改动不影响） |

---

## 五、设计铁律复核

1. **唯一性**：20 个新 effect 名全部唯一（无与他人复用；旧 regen/execute 名保留但数据不再引用，晨光教会 regen_strong 与龙鳞 reflect 不在本批范围）。
2. **贴合主题**：回血组 10 套全部圣系/治疗/净化/护盾向（布衣=触发回血、祝福=回蓝、圣堂=低血回血/壁垒、审判=净化、神恩=爆发救急、护林=野性再生）；处决组 10 套全部刺客/斩杀/连击/暴击/冰冻向。
3. **数值守恒**：全部 ≤ 原模板 +5% 期望（逐套在第二节标注对照）；超限的（圣徽 20%→10%、幻影 0.20→0.15）已降档。
4. **强效果有代价/条件**：圣徽转盾限次、圣堂低血条件、神恩救急每场 1 次、阴影叠层、幻影需暴击、午夜概率真伤、夜行套潜行触发、霜猎 Boss 免疫退化。
5. **引擎兼容**：14 个 SET_PROC 注册 + 6 个 battle.py 直连（标注具体行号）；直连型进 SET_EFFECT_CONSUMED。
6. **不破坏既有测试**：唯一硬断言改动 = test_v136_phase6_equip 护林 effect 名；test_v98_05_registry 建议保留旧 handler；test_v1252_audit_closure 需同步 SET_EFFECT_CONSUMED。

报告完成。
