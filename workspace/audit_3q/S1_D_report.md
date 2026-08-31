# S1-D 吸血族去模板化设计报告（9 套专属 4 件效果）

> 任务卡：`workspace/audit_3q/S1_D.md`（吸血族 9 套）｜公共框架：`workspace/audit_3q/S1_FRAMEWORK.md`
> 插件根：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（报告按框架约定写于 `workspace/audit_3q/S1_D_report.md`）
> 只设计不改代码。

---

## 0. 现状核验（动手前必读结论）

- 9 套当前 **全部** 共享 `effect: "lifesteal_set"`（攻击 30% 概率吸血 15% 伤害，期望 E = 30%×15% = **4.5% 伤害/命中**）。
- **实际可触达性**（grep EQUIP_ROSTER / SET_THEMES / SERIES_SETS 后确认）：
  | 套装 key | 名称 | 品质 | 触达方式 | 状态 |
  |---|---|---|---|---|
  | set_hei_zhao | 黑沼 | 紫 | SET_THEMES.purple 随机掉落 | **live** |
  | set_xing_zhe_tao | 行者套 | 蓝 | SERIES_SETS 行者→名册（_build_class_sets 注册） | **live** |
  | set_shi_quan_tao | 石拳套 | 蓝 | SERIES_SETS 石拳→名册 | **live** |
  | set_bi_chui_tao | 壁槌套 | 紫 | SERIES_SETS 壁槌→名册 | **live** |
  | set_xing_zhe | 行者 | 蓝 | CLASS_SET_THEMES 废弃旧档 | legacy（兼容旧档） |
  | set_tie_shou | 石拳 | 蓝 | 同上 | legacy（兼容旧档） |
  | set_hu_xiao | 壁槌 | 紫 | 同上 | legacy（兼容旧档） |
  | set_pan_shi | 磐石 | 紫 | 同上（磐石王冠 series=磐石 但无 set 字段、磐石 ∉ SERIES_SETS） | legacy（兼容旧档） |
  | set_anvil_guard | 铁砧拳套 | 橙 | 同上 | legacy（兼容旧档） |

  → 9 套全部保留并各自重设计（任务卡要求）；legacy 5 套为旧档 set 字段兼容，改数据零成本、必须同步改，否则旧档玩家白穿套装。
- **数据源双写点**：live 3 名册套效果定义在 `game/core/class_sets.py` 的 `_SERIES_SET_BONUS`（'行者'/'石拳'/'壁槌' 三条，经 `_build_class_sets()` 注册/覆盖 `SETS`）；legacy 6 套在 `game/data/sets.py` 的 SETS 字面量。**两处都要改**。
- **新 effect 名必须避开 27 个既有 effect 名**（SET_PROC_EFFECTS 6 键 + 全档 bonus_4/bonus_5 effect 键，已程序化核验，见下节）。

---

## 1. 专属效果设计表（9 套 × 唯一 effect）

> 数值守恒基准：原模板期望 **4.5% 伤害/命中**；铁律 ΔE ≤ 原模板 +5pp（绝对加值）。

### 1.1 set_hei_zhao 黑沼（紫，live 随机掉落）——方向：暗蚀
- **新 effect 名**：`hei_zhao_erode`（唯一性已核验）
- **desc**：攻击 30% 概率附加【暗蚀】(2 回合，每回合 1% 敌方最大生命暗属性伤害)，暗蚀伤害全额转化为自身生命
- **trigger**：on_hit（走 `_set_attack_proc` → SET_PROC_EFFECTS）
- **数值**：30% × (1%×2 回合 max_hp 暗伤 + 同量回血) ≈ 0.6% 敌方 max_hp ≈ **5~6% dmg**（ΔE≈+1.5pp ✓）
- **机制**：dot+吸血合一（区别于 burn=5% 火伤无回血、lifesteal_set=纯概率吸血）；对敌挂 `enemy["debuffs"]["erode"]`（目标级，走 DOT 结算链 `_tick_dots`，可被适应机制/驱散）
- **2件套**：保留 `atk 0.18 + pene_phys 0.05`（v106.1 特色已差异化，且 `test_v106_1_attributes.py:75` 断言此值，不动）

### 1.2 set_xing_zhe_tao 行者套（蓝，live 名册）——方向：游走吸血（稳定）
- **新 effect 名**：`xing_zhe_flow`
- **desc**：攻击命中 100% 吸血 6% 伤害（行云流水，绵绵不绝）
- **trigger**：on_hit（SET_PROC_EFFECTS）
- **数值**：100% × 6% dmg = **6%**（ΔE≈+1.5pp ✓；机制从"概率大额"改为"稳定小额"）
- **2件套**：`atk 0.08 + def 0.05` → `spd 0.10 + atk 0.05`（游走=身法，速度主题；总值 0.15 vs 原 0.13，微强可接受）

### 1.3 set_shi_quan_tao 石拳套（蓝，live 名册）——方向：硬抗反打
- **新 effect 名**：`shi_quan_retort`
- **desc**：受击后 15% 概率以 30% 攻击立即反击（硬抗反打，石拳回敬）
- **trigger**：受击（battle.py `_damage_player` 段，反击被动池后）
- **数值**：15% × 30% atk ≈ **4.5%** ✓（受击频率≈攻击频率 1:1，与攻击吸血同频换算）
- **2件套**：`atk 0.08 + def 0.05` → `def 0.10 + atk 0.05`（硬抗=防御，总值 0.15）

### 1.4 set_bi_chui_tao 壁槌套（紫，live 名册）——方向：格挡反击
- **新 effect 名**：`bi_chui_wall`
- **desc**：格挡成功时 100% 反弹 30% 本次伤害（拳如铁壁，以壁还击）
- **trigger**：受击-格挡段（battle.py 5611-5623 block roll 成功分支内）
- **数值**：block 率×30% ≈ **4~6%** ✓（区别于龙鳞 25%×25%=6.25% 任意受击反弹：壁槌=格挡成功后必反，条件更严）
- **2件套**：`atk 0.08 + def 0.05` → `def 0.08 + block 0.06`（格挡主题，总值 0.14）

### 1.5 set_pan_shi 磐石（紫，legacy 旧档）——方向：稳如山（受击减伤）
- **新 effect 名**：`pan_shi_steady`
- **desc**：受击时伤害 -5%（磐石不动，稳如山岳）
- **trigger**：受击（battle.py `_damage_player` 被动减伤区 5688-5717）
- **数值**：5% 受击 dmg ≈ **4~6%** ✓（区别于 dmg_reduce 词条 3%/铁壁被动：数值独立、来源独立，可叠加）
- **2件套**：`atk 0.12 + hp 0.15` → `def 0.15 + hp 0.10`（稳=防御，总值 0.25 vs 0.27）

### 1.6 set_anvil_guard 铁砧拳套（橙，legacy 旧档）——方向：铁壁格挡（概率免疫，限次）
- **新 effect 名**：`anvil_parry`
- **desc**：受击时 20% 概率完全免疫本次伤害（铁壁格挡，每场战斗最多 3 次）
- **trigger**：受击（battle.py 5583-5588 first_hit_immune 区后；限次计数存 `p_eff["anvil_parry_left"]`，随战斗序列化）
- **数值**：20% × 全额减免 ≈ 0.2×受击 dmg（减免向，橙套强效；**带每场 3 次限制** = 强效果有代价 ✓）
- **2件套**：`atk 0.12 + hp 0.15` → `def 0.12 + hp 0.15 + block 0.04`（铁壁，橙套三项，总值 0.31）

### 1.7 set_xing_zhe 行者（蓝，legacy 旧档）——方向：猎血（概率高额吸血）
- **新 effect 名**：`xing_zhe_hunt`
- **desc**：攻击 40% 概率吸血 12% 伤害（猎血者，咬住不放）
- **trigger**：on_hit（SET_PROC_EFFECTS）
- **数值**：40% × 12% = **4.8%** ✓（ΔE≈+0.3pp；旧 30%×15% 的"概率大额"灵魂保留，与行者套"稳定小额"区分）
- **2件套**：`atk 0.12 + hp 0.15` → `atk 0.10 + lifesteal 0.02 + hp 0.08`（吸血属性主题，总值 0.20；lifesteal 属性面板化 cap 30% 叠加无溢出）

### 1.8 set_tie_shou 石拳（蓝，legacy 旧档）——方向：受击回血
- **新 effect 名**：`tie_shou_blood`
- **desc**：受击后 30% 概率回复 3% 最大生命（拳心回流，以伤养身）
- **trigger**：受击（battle.py 5904-5909 dmg_taken_heal 被动区后）
- **数值**：30% × 3% max_hp ≈ 0.9% max_hp ≈ **4~5% dmg**（受击频率≈1/2 攻击频率换算）✓
- **2件套**：`atk 0.12 + hp 0.15` → `hp 0.15 + def 0.08`（养身主题，总值 0.23）

### 1.9 set_hu_xiao 壁槌（紫，legacy 旧档）——方向：壁立千仞（回合护盾）
- **新 effect 名**：`hu_xiao_barrier`
- **desc**：每回合开始获得 3% 最大生命的护盾（持续 1 回合）（壁立千仞，风雨不侵）
- **trigger**：回合开始（battle.py `_turn_start` regen 分支 4989-4995 后；`_add_shield("hu_xiao_barrier", int(max_hp×0.03), 1)` 走既有 p_shields 多来源体系）
- **数值**：3% max_hp/回合 防御值 ≈ **4~6% dmg**（防御向守恒；区别于铁砧=概率免疫、磐石=固定减伤）✓
- **2件套**：`atk 0.12 + hp 0.15` → `hp 0.12 + mdef 0.10`（壁垒主题，总值 0.22）

### 1.10 唯一性 + 方向矩阵核验
- 9 个新 effect 名与既有 27 个 effect 名 **零碰撞**（已程序化验证：`sorted(new_names & existing) == []`）。
- 9 套 9 个方向互不重复：
  稳定吸血(行者套) / 概率高额吸血(行者) / 受击反击(石拳套) / 受击回血(石拳) / 格挡后反弹(壁槌套) / 回合护盾(壁槌) / 受击减伤(磐石) / 概率免疫限次(铁砧) / 暗蚀dot吸血(黑沼)。
- 原 lifesteal 主题"吸血"以 6 种不同机制保留：稳定吸血 / 概率吸血 / dot吸血 / 受击回血（反向吸血）/ 护盾（防吸等价物）/ 免疫（最高防御吸血替代）。

---

## 2. 引擎改动清单

### 2.1 game/core/affix_effects.py（on_hit 注册表）
| 动作 | 内容 |
|---|---|
| 新增 | `@register(SET_PROC_EFFECTS, "hei_zhao_erode")` — 30% 附加 enemy debuffs erode(2 回合 1% max_hp 暗伤)，伤害全额回血；DOT 结算复用 `_tick_dots`（需在 DOT_DEFS/battle_config 或 handler 内声明 erode 的每回合 1% max_hp 公式，建议走既有 DOT 表结构） |
| 新增 | `@register(SET_PROC_EFFECTS, "xing_zhe_flow")` — 100% 吸血 6% dmg（heal=min(max_hp, hp+int(dmg×0.06))，日志「🩸 行者游血」） |
| 新增 | `@register(SET_PROC_EFFECTS, "xing_zhe_hunt")` — 40% 吸血 12% dmg |
| 删除 | `@register(SET_PROC_EFFECTS, "lifesteal_set")`（390-396 行）— 全部 9 套不再引用，保留会成为孤儿键触发 `test_v1252_audit_closure.py:211`「SET_PROC_EFFECTS 键 ⊆ 套装数据 effect 键」红断言。**必须删**。 |

### 2.2 game/battle.py（受击/回合开始直连消费，沿用 SET_EFFECT_CONSUMED 房风格）
| 位置（行号锚点） | 新增分支 |
|---|---|
| `_damage_player` 5583-5588（first_hit_immune 区后） | `anvil_parry`：`_set_eff(player,"anvil_parry",4)` 且 `p_eff["anvil_parry_left"]>0` 且 20% roll → 免疫本次伤害（return）+ 计数 -1 |
| `_damage_player` 5611-5623（block roll 成功分支内） | `bi_chui_wall`：`_set_eff(player,"bi_chui_wall",4)` → rd=int(原始 dmg×0.30)，走 `_boss_dmg_filter` + `_damage_enemy`，日志「🧱 壁槌反震」 |
| `_damage_player` 5688-5717（被动减伤区 reduce_total 汇总处） | `pan_shi_steady`：`_set_eff(player,"pan_shi_steady",4)` → reduce_total += int(dmg×0.05)，日志「⛰️ 磐石不动」 |
| `_damage_player` 5730-5752（反击被动池后） | `shi_quan_retort`：`_set_eff(player,"shi_quan_retort",4)` 且 15% roll → `E.calc_damage(int(atk×0.30), est.def)` 反击，走 `_boss_dmg_filter`+`_damage_enemy`，日志「🥊 石拳反打」 |
| `_damage_player` 5904-5909（dmg_taken_heal 被动区后） | `tie_shou_blood`：`_set_eff(player,"tie_shou_blood",4)` 且 30% roll → 回 3% max_hp，日志「🩸 拳心回流」 |
| `_turn_start` 4989-4995（regen 分支后） | `hu_xiao_barrier`：`_set_eff(player,"hu_xiao_barrier",4)` → `_add_shield("hu_xiao_barrier", int(max_hp×0.03), 1)`，日志「🧱 壁立千仞」 |
| `Battle.SET_EFFECT_CONSUMED`（802-806 元组） | **追加 6 个直连 effect 名**：`shi_quan_retort / bi_chui_wall / pan_shi_steady / anvil_parry / tie_shou_blood / hu_xiao_barrier`（供 `test_v1252_audit_closure` 覆盖审计 + battle.py 源码反查消费点） |

### 2.3 game/data/sets.py（legacy 6 套）
- set_hei_zhao / set_xing_zhe / set_tie_shou / set_hu_xiao / set_pan_shi / set_anvil_guard：`bonus_4` 改新 effect（见设计表），`bonus_2` 按设计表差异化（黑沼不动）。
- **注意**：`test_v98_05_registry.py:236` 用正则扫 sets.py 源文件抓 bonus_4 effect —— 改完 legacy 6 套后 sets.py 源内 `lifesteal_set` 彻底消失。

### 2.4 game/core/class_sets.py（live 3 名册套）
- `_SERIES_SET_BONUS` 的 '行者'/'石拳'/'壁槌' 三条：`bonus_4` 改 `xing_zhe_flow / shi_quan_retort / bi_chui_wall`（保留 `chance` 字段或按新语义去除——on_hit 类沿用 `chance`；受击/回合开始类无需 chance），`bonus_2` 按设计表差异化。

### 2.5 引擎新增能力（如需最小实现）
- 受击/回合开始 4 件套装直连消费是**新增消费点**（此前 battle.py 只有 on_hit 的 `_set_attack_proc` 总线 + regen/reflect 两个硬编码分支）。本设计不新增注册表，直接按 `full_rage_pursuit`(2501)/`first_hit_immune`(5584) 同款 `_set_eff(player, name, 4)` 内联分支，共 6 个 3-8 行小块 —— 与房风格一致、可被 SET_EFFECT_CONSUMED 审计覆盖。
- `anvil_parry` 限次计数建议放 `p_eff`（随战斗序列化，v130.2 先例），初始化 3。

---

## 3. 受影响测试

| 测试文件 | 断言位置 | 影响 | 需要的改动 |
|---|---|---|---|
| **tests/test_v98_05_registry.py** | L239-246 | `implemented` 硬编码含 `lifesteal_set`；删除 handler 后 `lifesteal_set ∉ SET_PROC_EFFECTS` → **必红** | `implemented` 改为 `{"frost","burn","thunder","pierce","execute"} ∪ {hei_zhao_erode, xing_zhe_flow, xing_zhe_hunt}`（sets.py 源内 3 个新 on_hit 名）；`non_attack` 断言逻辑不变（新受击/回合开始 effect 不进 SET_PROC_EFFECTS 即自动通过） |
| **tests/test_v1252_audit_closure.py** | L204-231 | ① `no_stats_eff` 全覆盖断言：6 个直连新 effect 必须 ∈ SET_EFFECT_CONSUMED（会加，见 2.2）→ 通过；② `SET_PROC_EFFECTS 键 ⊆ data`：删 lifesteal_set 后无孤儿键 → 通过；③ SET_EFFECT_CONSUMED 键全在数据中 + battle.py 源码含消费点（6 个新名会写入 battle.py）→ 通过 | 无需改断言；若实现走"新注册表"路线（非直连），需在此处把新注册表名加入豁免集 —— **推荐直连路线，零测试改动** |
| tests/test_v136_phase6_equip.py | L167-189（test_set_effects） | 只断言 铁皮套(pierce)/护林套(regen)，不含 9 套 | 不受影响；（建议）补 3 名册套 bonus_4 新 effect 注册断言 |
| tests/test_v106_1_attributes.py | L75 | 断言黑沼 2 件 `pene_phys 0.05` | 不受影响（黑沼 bonus_2 保留不动） |
| tests/audit_result.txt | L705-711 | 静态结果记录（曾含 lifesteal_set） | 不执行不红；建议随本次改动刷新 |
| 词条吸血类测试（test_aoe_multi_target / test_dot_refactor / test_stage8_equip_affix / test_v98_04_battle_registry） | — | 引用 `lifesteal` 均为词条属性/吸血属性（st["lifesteal"]），非套装 effect 名 | 不受影响 |

---

## 4. 备注

- 数值守恒逐套核验（见 1.x 各条 ΔE），全部 ≤ 原模板 +1.5pp（远低于 +5pp 红线）；橙套 anvil_parry 属减免向强效，以"每场 3 次"为代价平衡。
- 2 件套差异化仅动 8 套（黑沼保留），总值区间 0.14~0.31 与原体系同量级。
- legacy 5 套（行者/石拳/壁槌/磐石/铁砧拳套）虽为废弃毕业套残留，但旧档 set 字段仍会命中 `_set_info`，必须同步改，否则旧档玩家 4 件套直接白板。
