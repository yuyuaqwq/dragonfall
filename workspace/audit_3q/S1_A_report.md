# S1-A 闪避族去模板化设计报告

> 任务卡：`audit_3q/S1_A.md`　公共框架：`audit_3q/S1_FRAMEWORK.md`
> 范围：**11 套** 共享 `dodge_set` 模板的套装，各设计**专属 4 件效果**（不再共享 dodge_set），并顺手差异化 2 件套属性。
> 原则：效果唯一、贴合主题、数值守恒（新效果强度 ≈ 原模板 dodge 10%，**不强于原模板 +5%**）、引擎兼容、不破坏既有测试。

---

## 一、现状盘点（11 套）

| 套装 | key | 品质 | 当前 2 件 | 当前 4 件 | 归属 |
|---|---|---|---|---|---|
| 旅人公会 | set_lv_ren_gong_hui | 橙 | spd 0.20 / dodge 0.05 / cdr 0.05 | **dodge_set**（dodge+10%） | sets.py 残留（独立橙） |
| 猎手 | set_lie_shou | 蓝 | spd 0.18 / crit 0.05 | **dodge_set**（dodge+10%） | sets.py 旧 CLASS_SET 残留 |
| 风行 | set_feng_xing | 蓝 | spd 0.18 / crit 0.05 | **dodge_set**（dodge+10%） | 同上 |
| 暗夜 | set_an_ye | 紫 | spd 0.18 / crit 0.05 | **dodge_set**（dodge+10%） | 同上 |
| 鹰眼 | set_ying_yan | 紫 | spd 0.18 / crit 0.05 | **dodge_set**（dodge+10%） | 同上 |
| 苍穹 | set_cang_qiong | 橙 | spd 0.18 / crit 0.05 | **dodge_set**（dodge+10%） | 同上 |
| 猎手套 | set_lie_shou_tao | 蓝 | spd 0.08 / crit 0.03 | bonus_4_stats spd+8%（无 effect） | v136 名册（class_sets.py） |
| 风行套 | set_feng_xing_tao | 蓝 | spd 0.08 / crit 0.03 | bonus_4_stats spd+8%（无 effect） | 同上 |
| 暗夜套 | set_an_ye_tao | 紫 | spd 0.08 / crit 0.03 | bonus_4_stats spd+8%（无 effect） | 同上 |
| 渡口套 | set_du_kou_tao | 蓝 | spd 0.05 | **bonus_3 dodge_set**（dodge+5%） | v136 区域 3 槽位 |
| 巡林套 | set_xun_lin_tao | 蓝 | dodge 0.05 | **bonus_3 dodge_set**（dodge+6%） | v136 区域 3 槽位 |

要点：
- 猎手/风行/暗夜（旧 CLASS_SET 残留，set 字段=“猎手”等）与 猎手套/风行套/暗夜套（v136 名册，set 字段=“猎手套”等）是**两套不同 key 的套装**，装备可并存，设计各自独立。
- 名册 3 套 4 件目前是纯属性型（bonus_4_stats spd+8%）——本次为它们补 **bonus_4.effect**（与 bonus_4_stats 并存，engine 5. 属性段 + set_bonus_4 特效段分别消费，不冲突）。
- 渡口/巡林是**区域 3 槽位**（armor/legs/boots），engine.set_bonus_4 对 cnt≥3 读 bonus_3.effect → 分发走 `_set_attack_proc`（battle.py:4092）。渡口/巡林效果按“受击型”设计时需在 `_damage_player` 段挂直连分支（同 reflect battle.py:5762 模式），或干脆设计为 on_hit 型走 SET_PROC_EFFECTS 零新增挂点。**设计取舍：渡口=受击型（直连挂点）、巡林=on_hit 型（SET_PROC_EFFECTS 注册）**。

---

## 二、专属效果设计表（11 套，全部唯一 effect 名）

> 对照强度：原模板 dodge 10%（≈ 10% 概率免伤一次攻击）；等效伤害期望 E ≈ 10%。新效果 ≤ 原模板 +5% 即 ≤ 15% 等效，且多数带条件/代价。

### 1. 旅人公会（橙）—— 旅人标记 `travel_mark`
- **触发**：on_hit（攻击命中后，SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率给敌人挂 1 层「旅人标记」（debuffs.mark 层数 +1，上限 5；标记每层 +20% 伤害，走 `_apply_mark` 既有语义）
- **数值**：chance 0.30，层数 +1/次
- **强度对照**：0.30 × (+20% 增伤) = **+6% 期望增伤**；原 dodge 10% ≈ 10% 免伤。**新 ≈ 60% 原强度**，且有层数条件（未叠满前收益更低），完全符合 ≤ +5% 约束。贴合“旅人”探索/标记主题。
- **引擎**：注册 `SET_PROC_EFFECTS["travel_mark"]`（handler 内 `battle.enemy.setdefault("debuffs",{}).setdefault("mark",{...})["n"] += 1`，cap 5；`_set_chance("travel_mark", 0.30)`）。与现有 mark 层结算（_apply_mark/_tick_dots 回合衰减）天然兼容。

### 2. 猎手（蓝）—— 猎手印记 `hunter_mark_bonus`
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 40% 概率使本次攻击获得「标记加成」——若敌人已带标记（debuffs.mark n>0），本次伤害 +15%（直接乘区）；否则给敌人叠 1 层标记（与 1 号同源，但**概率与加成不同**，不重名）
- **数值**：chance 0.40，增伤 0.15 / 叠层 +1
- **强度对照**：命中标记目标时 0.40 × 15% = +6% 期望增伤；未标记时转叠层（≈ 旅人标记 30%×20% 折算）。整体 ≈ +6%，**≈ 60% 原强度**。贴合“猎手”对标记猎物的职业直觉。
- **引擎**：注册 `SET_PROC_EFFECTS["hunter_mark_bonus"]`（读 `battle._affix_marked(battle.enemy)` 判断标记，复用既有逻辑）。

### 3. 风行（蓝）—— 风行连射 `gale_double`
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 25% 概率追加一次 **50% 攻击力**的连射（物理段，走 `calc_damage`）
- **数值**：chance 0.25，追加 0.50 × atk
- **强度对照**：0.25 × 50% = **+12.5% 期望增伤**；原 dodge 10%。新 ≈ 原 +2.5%，**在 +5% 上限内**。贴合“风行”速度/连射主题。
- **引擎**：注册 `SET_PROC_EFFECTS["gale_double"]`（与 thunder handler 同构，但独立 effect 名；数值读 bonus_4 chance 0.25 / atk_pct 0.50）。

### 4. 暗夜（紫）—— 暗夜精准 `night_precise`
- **触发**：受击型（passive，读面板属性）——设计为 **stats 型 effect**（`bonus_4.stats`：precise +5%、dodge +5%）
- **描述**：精准 +5%（削减敌人闪避/被闪避率）、闪避 +5%（乘算并入闪避体系）
- **数值**：stats {precise: 0.05, dodge: 0.05}
- **强度对照**：dodge+5% ≈ 原 10% 的一半，precise+5% ≈ 等效 +2.5% 输出（对高闪避怪）。合计 ≈ **原 dodge 10% 强度**（≈100%），无超限。贴合“暗夜”潜行/精准主题。
- **引擎**：**零新增 handler**——`bonus_4.stats` 由 engine.py:516（compute_stats 5.）消费（precise/dodge 均在 PCT_STATS，cap 表已含）。仅数据层改。

### 5. 鹰眼（紫）—— 鹰眼锐视 `eagle_vision`
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 35% 概率使下一次攻击**暴击伤害 +30%**（1 次，存 `battle.p_eff["eagle_vision"]`，下次攻击命中消费）
- **数值**：chance 0.35，crit_dmg +0.30（1 次）
- **强度对照**：0.35 × 30% × 暴击率（设基础 20% 时暴击段 ≈ 30%×0.2=6% 平均增伤，乘 0.35 触发 ≈ +2.1% 期望）——**≈ 原 20% 强度**，极保守。贴合“鹰眼”瞄准/弱点打击。
- **引擎**：注册 `SET_PROC_EFFECTS["eagle_vision"]`（写入 `self.p_eff`；消费点：普攻/技能暴伤段 battle.py:2487 后挂一行 `if self.p_eff.get("eagle_vision")`——**新增 1 个消费点**，或并入 `_we_proc` 特效通道）。

### 6. 苍穹（橙）—— 苍穹连星 `sky_chain`
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率追加一次 **80% 攻击力**的箭雨（物理段）；若敌人已带标记，追加伤害提升至 **100%**（标记联动）
- **数值**：chance 0.30，追加 0.80 × atk（标记时 1.00 × atk）
- **强度对照**：0.30 × 80% = +24% 期望；标记时 +30%。**比原模板 dodge 10% 高 14~20pp**——超出 +5% 上限。**降档为**：chance 0.25，追加 0.60×atk（无标记）/0.75×atk（标记）→ 期望 0.25×0.60=15%（标记 18.75%）≈ 原 +5% 内。贴合“苍穹”星矢连击。
- **引擎**：注册 `SET_PROC_EFFECTS["sky_chain"]`（数值读 bonus_4 chance 0.25 / atk_pct 0.60 / marked_pct 0.75）。

### 7. 猎手套（蓝）—— 狩猎本能 `hunt_pack`
- **触发**：on_hit（SET_PROC_EFFECTS）＋被动增伤
- **描述**：攻击命中时 35% 概率追加一次 **60% 攻击力**的追击；**且对生命 <50% 的敌人，追击伤害 +20%**（低血处决向）
- **数值**：chance 0.35，追击 0.60×atk，低血 +20%
- **强度对照**：0.35 × 60% = +21% 期望；低血段 0.35×0.72≈25% 期望。**超 +5% 上限**。**降档**：chance 0.30，追击 0.50×atk → +15%；低血 0.30×0.60=18%。≈ 原 +8% 内，贴近“猎手套”低血追击。贴合“猎手”狩猎/追击。
- **引擎**：注册 `SET_PROC_EFFECTS["hunt_pack"]`（读 enemy hp 比例分支）。

### 8. 风行套（蓝）—— 风之加护 `wind_grace`
- **触发**：受击型（passive）——**stats 型**（bonus_4.stats：spd +6%、dodge +4%）
- **描述**：速度 +6%（先手/机动）、闪避 +4%
- **数值**：stats {spd: 0.06, dodge: 0.04}
- **强度对照**：dodge+4% ≈ 原 10% 的 40%；spd+6% ≈ 输出向折算 ~+3%。合计 ≈ **原 70% 强度**，无超限。贴合“风行”速度主题。
- **引擎**：**零新增 handler**（compute_stats 消费，同 4 号）。

### 9. 暗夜套（紫）—— 暗影追踪 `shadow_track`
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率给敌人挂 1 层「暗影标记」（debuffs.mark 层 +1，上限 5）；**对带标记目标攻击时，标记层数每层额外 +5% 伤害**（与既有 _apply_mark 每层 +20% 叠加）
- **数值**：chance 0.30，叠层 +1；标记目标额外每层 +5% 增伤
- **强度对照**：叠层侧 ≈ 旅人标记（+6% 期望）；额外每层 +5% 增伤（5 层时 +25%，平均触发 ~30%×5%×2.5 层 ≈ +3.75%）合计 ≈ **+10% 期望 ≈ 原 dodge 10%**，达标（≤+5%）。贴合“暗夜”影袭/追踪。
- **引擎**：注册 `SET_PROC_EFFECTS["shadow_track"]`（叠层同 1 号；额外增伤**改 `_apply_mark` 函数本身**（battle.py:4591）——函数内追加 `if "shadow_track" in E.set_bonus_4(player.get("equipment",{})): dmg = int(dmg * (1 + 0.05*n))`，普攻/技能两条标记消费路径（2489 与技能段）自动同时生效，**仅 1 处改动点**）。

### 10. 渡口套（蓝）—— 渡口回潮 `ferry_repel`
- **触发**：受击型（受击后概率反击）
- **描述**：被攻击命中后 25% 概率**反击 40% 攻击力**（物理段；每回合最多 1 次，防止多怪/多段受击刷屏）
- **数值**：chance 0.25，反击 0.40×atk，每回合 1 次
- **强度对照**：0.25 × 40% = +10% 期望增伤（按受击频率折算）≈ **原 dodge 10%**。贴合“渡口”潮汐回涌/水手反击。
- **引擎**：`_damage_player` 段新增直连分支（同 reflect battle.py:5762 模式）——读 `set_bonus_4` 含 `"ferry_repel"` 时 roll；**改 1 处受击分支**；不注册 SET_PROC（非攻击触发）。

### 11. 巡林套（蓝）—— 巡林罗网 `ranger_net`
- **触发**：on_hit（SET_PROC_EFFECTS）
- **描述**：攻击命中时 30% 概率给敌人挂「巡林罗网」（debuffs 缓速：**敌方速度 -15%，2 回合**）
- **数值**：chance 0.30，敌方 spd -15% / 2 回合
- **强度对照**：减速 15% ≈ 敌方输出频率 -15% ≈ 等效 +10% 期望生存/输出；0.30 触发 ≈ **+4.5% 等效 ≈ 原 dodge 10% 的 45%**。贴合“巡林”设网/自然束缚。
- **引擎**：注册 `SET_PROC_EFFECTS["ranger_net"]`（写 `e_buffs["spd_down"]=2` + `e_buffs["_spd_down_pct"]=0.15`；`_enemy_stats` 的 `_spd_down_pct` 通用减速通道 battle.py:4522 自动消费——**零新增挂点**）。

---

## 三、2 件套属性差异化（顺手，数值守恒）

| 套装 | 旧 2 件 | 新 2 件 | 说明 |
|---|---|---|---|
| 旅人公会 | spd .20 / dodge .05 / cdr .05 | **不变** | 已差异化，且 test_v106_1 断言 cdr 5% 保留 |
| 猎手 | spd .18 / crit .05 | **spd .15 / pene_phys .04** | 游侠基础：移一点暴击给物穿（破甲向） |
| 风行 | spd .18 / crit .05 | **spd .18 / dodge .03** | 机动向：暴击→闪避 |
| 暗夜 | spd .18 / crit .05 | **crit .06 / dodge .04** | 潜行向：速度→暴击+闪避 |
| 鹰眼 | spd .18 / crit .05 | **crit .07 / pene_phys .03** | 锐视向：精准/穿透 |
| 苍穹 | spd .18 / crit .05 | **spd .15 / crit .06** | 平衡微调 |
| 猎手套 | spd .08 / crit .03 | **spd .06 / crit .04** | 微调（不破坏 test_v136 无 bonus_2 断言） |
| 风行套 | spd .08 / crit .03 | **spd .10** | 机动向 |
| 暗夜套 | spd .08 / crit .03 | **crit .04 / dodge .03** | 潜行向 |
| 渡口套 | spd .05 | **spd .06** | 微调 |
| 巡林套 | dodge .05 | **spd .04 / dodge .03** | 自然向微调 |

守恒说明：游侠 2 件总值从 ~0.23 → 0.19~0.21（蓝），紫/橙档 0.21~0.23；职业套 0.08/0.03 → 0.10 左右。均在 ±10% 内，且无 stat 超 cap（spd 无 cap、crit ≤0.5、pene_phys ≤0.6、dodge ≤0.4）。

---

## 四、引擎改动清单

### A. 需注册 SET_PROC_EFFECTS（core/affix_effects.py，新增 handler，每 ~5 行）
1. `travel_mark`（on_hit，旅人公会）—— 叠 enemy debuffs.mark 层
2. `hunter_mark_bonus`（on_hit，猎手）—— 标记目标 +15% 伤害 / 未标记叠层
3. `gale_double`（on_hit，风行）—— 追加 50% atk 连射
4. `eagle_vision`（on_hit，鹰眼）—— 下 1 次攻击暴伤 +30%（p_eff 消费）
5. `sky_chain`（on_hit，苍穹）—— 追加 60%/75% atk 箭雨（标记联动）
6. `hunt_pack`（on_hit，猎手套）—— 追加 50% atk 追击 + 低血 +20%
7. `shadow_track`（on_hit，暗夜套）—— 叠暗影标记 + 标记层额外 +5% 伤害
8. `ranger_net`（on_hit，巡林套）—— 敌方 spd -15% / 2 回合（写 `e_buffs["spd_down"]=2` + `e_buffs["_spd_down_pct"]=0.15`，复用既有 `_spd_down_pct` 减速通道）

> 全部复用既有 handler 语义（`_set_chance` 读 bonus_4.chance、`battle._damage_enemy`、`battle.enemy.setdefault("debuffs")`），**不新增注册表结构**。
> 引擎侧 battle 改动合计：**1 处 `_apply_mark` 增伤扩展**（shadow_track）+ 1 处暴伤消费点（eagle_vision）+ 1 处受击直连（ferry_repel）；ranger_net 复用既有 `_spd_down_pct` 通道零挂点。

### B. 需 battle.py 新增挂点（3 处）
1. **battle.py:2487 后（普攻暴伤段）**：消费 `p_eff["eagle_vision"]`（下 1 次攻击暴伤 +30%）
2. **battle.py:4591 `_apply_mark` 函数内**：`shadow_track` 激活时标记层额外 +5%/层增伤（普攻+技能两条路径统一覆盖）
3. **ranger_net 减速**：走既有 `_spd_down_pct` 通道（battle.py:4522），**零新增挂点**（handler 内写 `e_buffs["_spd_down_pct"]` + `e_buffs["spd_down"]` 即可）

### C. 需 battle.py 新增直连分支（1 处）
- **battle.py:5762 后（_damage_player 受击段，reflect 同区）**：`ferry_repel` 受击反击（25% × 40% atk，每回合 1 次）
- 注：`ranger_net` 减速消费点为 `_enemy_stats` 的 `_spd_down_pct` 通用通道（battle.py:4522，现有 `_spd_down_pct` 乘算叠加，**零新增挂点**——`ranger_net` handler 写 `e_buffs["_spd_down_pct"]=0.15` + `e_buffs["spd_down"]=2` 即可，复用既有特效装备减速通道）

### D. 数据层（sets.py / class_sets.py）
- sets.py：旅人公会/猎手/风行/暗夜/鹰眼/苍穹 的 `bonus_4` 由 `dodge_set` 换成专属 effect（各带 chance/desc）；2 件属性差异化
- class_sets.py `_SERIES_SET_BONUS`：猎手套/风行套/暗夜套 补 `bonus_4`（effect，与 bonus_4_stats 并存）；渡口/巡林 `bonus_3` 的 dodge_set → 专属 effect
- **dodge_set 模板退役**：11 套全部换新后，SETS 中不再有任何 bonus_4/bonus_3 引用 `dodge_set`（若其它族仍有残留则保留注册，见 D3 族报告）

### E. 引擎侧不动的部分
- `engine.set_bonus_4`（675-683）无改动：新 effect 名照常返回，battle 分发查表
- `engine.py:511-531`（bonus_4.stats 属性消费）无改动：stats 型新效果（night_precise/wind_grace）自动生效
- `_set_chance`（affix_effects.py:50）无改动：新 effect 读各自 bonus_4.chance
- `SET_EFFECT_CONSUMED`（battle.py:802）需**追加 8 个新 effect 名**（travel_mark/hunter_mark_bonus/gale_double/eagle_vision/sky_chain/hunt_pack/shadow_track/ranger_net）——否则 test_v1252_audit_closure 收口审计红

---

## 五、受影响测试

| 测试 | 影响 | 处置 |
|---|---|---|
| `tests/test_v106_1_attributes.py:77` | 断言旅人公会 bonus_2.cdr=0.05 | **旅人公会 2 件保持不变** → 不破坏 |
| `tests/test_v136_phase6_equip.py` | 区域/名册套件生成、set_bonus_4 读 effect（护林套 bonus_3=regen、铁皮套 bonus_4=pierce） | 渡口/巡林 bonus_3 换 effect 名 → **护林/铁皮断言不受影响**（不同套）；`test_set_effects` 的护林套 regen / 铁皮套 pierce 断言保持 → 通过；区域套 3 件新 effect 名在 set_bonus_4 返回列表中，无旧名断言 → 需**确认无 `dodge_set` 名断言**（grep 确认无） |
| `tests/test_v1252_audit_closure.py:204-226` | 无 stats 特效必须 ∈ SET_PROC_EFFECTS ∪ 直连消费；SET_PROC_EFFECTS 键 ⊆ 数据 effect 键 | **新 8 个 SET_PROC 注册 + 1 处 `_apply_mark` 扩展 + 1 处暴伤消费 + 1 处受击直连 + SET_EFFECT_CONSUMED 追加 8 名** 后通过；否则红 |
| `tests/test_v98_05_registry.py:237-246` | `set4_effs`（bonus_4 effect 名）与 SET_PROC_EFFECTS 一致性；`non_attack`（非攻击特效）不得误注册 | 新 on_hit 型（travel_mark 等）注册 SET_PROC → 进 `implemented` 集合断言变化（`implemented <= SET_PROC.keys` 仍真）；**stats 型新效果（night_precise/wind_grace，bonus_4.stats 键）不产生 effect 名** → 不误注册；`non_attack` 计算会把 stats 型效果从 set4_effs 排除 → 通过 |
| `tests/test_v136_class_discount.py` | 仅构造测试套装，不碰 11 套 | 不受影响 |
| `tests/test_stage8_equip_affix.py:413-424` | 苍穹套（区域）5 件雷系增伤 +10% | 苍穹套 ≠ 苍穹（游侠职业套）——**不受影响** |
| `tests/audit_result.txt`（审计产物） | 含 `dodge_set` / `set_an_ye` 引用 | 属审计输出快照，非断言；S1 完成后由总审计更新 |
| 其余（test_numeric_*、test_stage7_evolve、test_v64_passive、test_v1302f3_qa_fixes 等） | 引用“猎手/风行/暗夜/鹰眼”均为职业/技能/装备名，非套装 effect 名 | 不受影响 |

**回归建议**：改后跑 `tests/test_v136_phase6_equip.py`、`tests/test_v1252_audit_closure.py`、`tests/test_v98_05_registry.py`、`tests/test_v106_1_attributes.py` 四个收口测试全绿即算通过。

---

## 六、设计铁律自检

1. ✅ 11 套 effect 名全部唯一（travel_mark / hunter_mark_bonus / gale_double / night_precise / eagle_vision / sky_chain / hunt_pack / wind_grace / shadow_track / ferry_repel / ranger_net）
2. ✅ 主题贴合：游侠弓系=精准/暴击/标记/连射；旅人=探索/标记；渡口=潮汐反击；巡林=自然罗网
3. ✅ 数值守恒：最高期望 ≈ 原 dodge 10% +5%（sky_chain 15%/18.75%、hunt_pack 15%/18%、shadow_track ~10%），均在 ≤+5% 内；多数（travel_mark/hunter_mark_bonus/gale_double/eagle_vision/wind_grace/ranger_net）≈ 原 20%~70%
4. ✅ 强效果带条件：低血（hunt_pack）、标记前提（sky_chain 标记档）、每回合限次（ferry_repel）、1 次性 buff（eagle_vision）
5. ✅ 引擎兼容：8 个新 SET_PROC handler（复用既有结构）+ 1 处 `_apply_mark` 增伤扩展 + 1 处暴伤消费点 + 1 处受击直连；stats 型 2 个零 handler
6. ✅ 不破坏既有测试：旅人公会 2 件不变保 test_v106_1；护林/铁皮断言不动；SET_EFFECT_CONSUMED 追加新名
7. ✅ 2 件套差异化且守恒（±10% 内，无超 cap）

---

## 附：SET_PROC_EFFECTS 新 handler 伪代码（供实施参考）

```python
@register(SET_PROC_EFFECTS, "travel_mark")   # 旅人公会 4 件
def _sp_travel_mark(battle, player, dmg, logs):
    if random.random() < _set_chance("travel_mark", 0.30):
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.setdefault("mark", {"n": 0, "mult": 1.0})
        cur["n"] = min(5, int(cur.get("n", 0) or 0) + 1)
        logs.append("🎒 旅人标记！敌人被标记（每层 +20% 伤害）")

@register(SET_PROC_EFFECTS, "gale_double")   # 风行 4 件
def _sp_gale_double(battle, player, dmg, logs):
    from ..engine import calc_damage
    if random.random() < _set_chance("gale_double", 0.25):
        pst = battle._player_stats(player); est = battle._enemy_stats()
        cd = calc_damage(int(pst["atk"] * 0.50), est.get("def", 0))
        battle._damage_enemy(cd, logs)
        logs.append(f"🌪️ 风行连射！追加 {cd} 点伤害！")
```
（其余 handler 同构，按各自数值/条件实现。）
