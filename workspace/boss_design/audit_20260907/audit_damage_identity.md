我已完成对该战斗引擎四个审计维度的全面检查，以下是逐项审计结果。

---

## 审计总结

**审计范围**：`game/battle.py`（10,133 行，全文分片精读）+ `game/engine.py`（calc_damage/resolve_formula 全文）+ 交叉核对了全部 `_damage_enemy`/`_damage_actor`/`_player_skill`/`_skill_heal` 等伤害与治疗结算路径。**未改动任何代码**。

总体结论：经过 v177→v180-B/v180-C 的多轮 actor 化，**伤害落地（承伤）侧已经收敛得相当干净**——玩家与怪共用 `_damage_actor` 统一承伤核心，dot 也用 actor-agnostic 的 `_tick_actor_dots`，身份判定已迁移到 `_is_focus_player`（side→引用→兼容兜底三级）。但**伤害制造（attacker）侧存在明显的半迁移残留**，同时**治疗结算完全没有 actor 化**（仍是玩家专属一套、无 actor-agnostic 治疗核心）。分项如下：

---

### 一、`_damage_enemy` 玩家被动乘区与 attacker 路由残留

#### ★问题 1【硬编码·数值分裂】`battle.py:8801/8810` — 猎印/魂标"基础 8%/6% 每层"游离于数据表
```python
8801|  _hm_pct = 0.08          # ← 猎印基础 8%/层（soul_mark 6%/层在 8810 行）
8802|  for _pn, _ps in _pm_d["proc"].get("hunt_mark_up", []):
8803|      _hm_pct += float(_ps.get("per_layer", 0.06) or 0.06)   # 缺省 0.06 也是硬编码
```
- **硬编码**：基础值与两个 fallback（0.08/0.06、0.06/0.08）都写死在 `_damage_enemy` 乘区内。但**同一数值的"权威"其实在 `data/battle_config.py` DOT_DEFS / 技能 passive 数据里**（如 `hunt_mark_up per_layer`、6602-6636 行的 cap 逻辑读 `_ps.get("add")`）——文档化的数值（猎印 8%/层 是旧"星语猎手职业"时代写死在代码里的，数据化后没迁干净）与被动增强各管一段，调数值必须同时改数据表和这 3 个魔法数字，极易"调了数据没调代码"导致实机/文案失配。
- 同类残留：`8810`（`soul_mark` 基础 0.06 + fallback 0.08）、`8820/8828/8834-8835`（破绽 bar_at/mult、broken_mult 0.50、dirge per_debuff/cap 均有 `or 0.xx` 兜底常数）。
- **建议改法**：把这些"标记基础层增伤"下沉到数据（DOT_DEFS 标记条目的 `per_layer` 或被动条目的基础字段），此处只 `_ps.get("per_layer", DEFAULT)` 或读数据表；基础值放一处。

#### ★问题 2【设计不良·判定不一致】`battle.py:8797-8806, 8850-8862` — 等级压制仍无条件读 `self.player`
```python
8791|  _atk_actor = attacker if attacker is not None else (self.player or {})   # ✅ 乘区已按 attacker 路由
...
8850|  if self.btype != "pvp" and self.player and target.get("lv"):
8852|      _plv = int(self.player.get("level", 0) or 0)      # ❌ 仍无条件读 self.player
```
- 同一函数内**已分叉**：`v180-C S3` 把被动乘区改成按 `attacker` 路由（宠物/随从攻击不再白嫖玩家乘区），但紧接着的**等级压制段仍无条件取 `self.player` 的等级**——宠物/随从攻击打高等级怪，压制按玩家等级算（多数情况反而**少压/不压**），攻击者路由不一致。
- **影响**：`_psk_atk_pct`（battle.py:138 `attacker=battle.pet`）等已传 attacker 的调用点，伤害乘区正确但等级压制基准错；PVP 侧 `_enemy_lv_pressure` 内部已把 btype=pvp 归一为 1.0，这里又重复判断 btype（`self.btype != "pvp"`）——语义可合入统一函数。
- **建议改法**：等级差用 `_atk_actor.get("level")`（与乘区同一 actor）；把"等级压制"抽成 `_lv_pressure(attacker, target)`，并让 PVP/无 level 目标内部返回 1.0，去掉外层散落 btype 判断。

#### ★问题 3【扩展性·语义丢失】`battle.py:7913-7915` — DOT caster 回落 `_last_player/self.player`
```python
7913|  if caster is None and not _tgt_is_player:
7914|      _act_pl = getattr(self, "_last_player", None) or self.player
7915|      caster = _act_pl if not self.btype == "pvp" else None
```
- 这是**唯一一条无条件读 `self.player` 的残留路径**（注释自认"现状语义"）：怪身上 dot 的强度按"最近行动玩家"算。**随从给怪挂的 dot 会白嫖玩家面板强度**（宠物/召唤物 pdot 的 `atk` 快照来自挂载时的 source，但老档/缺 caster 时回落玩家）——与问题 1 同源的半迁移。副本里 `_last_player` 更是"最近行动者"，可能不是当前焦点玩家。
- **建议改法**：caster 缺省优先按"dot 挂载快照"（debuffs 里已有施法者 atk/matk，7936-7942 已在读），把 7914 的"实时玩家面板回落"降级为真正兜底；随从挂的 dot 若 source 是随从，快照即可覆盖，不再需要 `self.player`。

---

### 二、class_name 判身份的残留

**结论：伤害/结算路径已基本清干净**（主判读 `_is_focus_player`，其兜底才碰 class_name，且排除 enemies 阵列）。真正残留的是**纯职业能力判定误用 `class_name`**——这类代码参数叫 `player`，实战只有玩家会进来，但若走 actor 化管线（怪施法玩家技能、PVP 敌我快照带 class_name）就会出错：

- ★【身份误判·风险】`battle.py:2074` `_affix_skill_dmg_mult`：`if kind == K_PHYS and player.get("class_name", "") == "cls_wu_seng":` —— 攻击方带词条时按职业名特判爆发贯体词条，`cls_wu_seng` 是硬编码 class id（非数据化）。若带职业的怪走管线，会误判吃玩家词条。
- ★【身份误判·风险】`battle.py:2303` `_combo_active`：`return bool(player.get("class_name","") == COMBO_CFG.get("class_id") and ...)` —— 已被 **v176 部分数据化**（class_id/path 进 COMBO_CFG），但 class_name 直判仍在（只对攻击方有意义，怪进管线有风险）。
- 可接受项：`1507`（`_is_element_mage` 判定 cls_fa_shi+攻线，v176 已注释"单点收口"——职业能力判定用职业名本属正常）；`2497`（歌者判 cls_mu_shi+BARD_BRANCHES）；`4858`（chi 终结判，含 `_rc.get("chi")` 资源键兜底）；`9879`（怒气受击按资源键 `k=="rage"`+_is_path，已非职业名）。

**判"玩家 vs 怪"的 class_name 残留：无**。`_is_focus_player`（9926-9957）本身先看 `side`、再看引用相等，class_name 只是带 enemies 排除的兼容兜底——这是有意设计且注释详尽。另外注意 `_res_gain`/`_res_spend`（1745/1774/1815）用 `actor.get("class_name")` 区分"玩家完整资源链路 vs 怪裸资源袋"，与身份判定正交（数据路由），但注释自称"玩家判定"——怪扮职业会误走玩家链路，属已知口径可留待 v180 后续统一。

---

### 三、calc_damage 直调点（应否统一走 resolve_formula）

**结论：主攻击路径已统一**（技能 `_skill_seg_damage`、怪物普攻/技能 `_enemy_cast_done` 都走 `E.resolve_formula` 或公式表达式管道；engine.py:1102-1179 `resolve_formula` 内部才调 `calc_damage` 分段落地）。仍残留 ~20 个**裸 `E.calc_damage` 直调点**，分散在 battle.py 与 core/*.py。battle.py 内重点：

| 位置 | 代码 | 类型 |
|---|---|---|
| `battle.py:9111` `_companion_act` basic_atk | `E.calc_damage(actor.get("atk",0), est.get("def",0), dmg_type=dmg_type)` | **硬编码物伤口径+重复实现**：随从普攻手动实现"dmg_type/防御/波动"三段，resolve_formula 一段搞定；`dmg_type` 仅透传 calc_damage 类型参数，variance 默认 0.15 被忽略（1107-1109 行 true 分支还自己重写一遍 `atk*(1+U(-0.15,0.15))`——**公式与 calc_damage 漂移**：calc_damage 的 true 分支是 `dmg=max(1, atk)` 然后统一乘波动+暴击，此处先乘波动再 max(1,·)，边界语义不同） |
| `battle.py:6878` `_reactive_extra_attack` | `E.calc_damage(est.get("atk",0), pst.get("def",0), False)` | 敌方反扑追加一击，重写普攻口径（已在 _enemy_cast_done 7046 改成 expr 管道） |
| `battle.py:7363` `_pvp_enemy_turn` | `E.calc_damage(est["atk"], pst["def"], is_crit, ...)` | 僵尸代码（函数自注 7353-7355 "真实 PVP 不可达"），仍用旧裸公式 |
| `battle.py:8741` `_aoe_damage` | 手动反推等效 atk 再 `E.calc_damage(...)` | 因 _damage_enemy 只收"已算好的 dmg"不得不反推；若 _damage_enemy 改收攻击方面板+目标，AOE/挡刀都不再需要反推 |
| `battle.py:9245` `_guard_redirect_check` | 同上反推 | 同上 |
| `battle.py:9630/9640/9659/9688` `_retaliations_and_buffs` | 石拳反打/反击/盾反 各自手写 `E.calc_damage(int(atk×系数), est def, crit)` | 4 处重复的"以攻×系数对敌防御结算"口径 |
| `battle.py:135/137` `_pet_skill_dmg` | `E.calc_damage(int(st["atk"]*pdef["skill_value"]), est.get("def",0))` | 宠物技能伤害仍走旧裸公式，且**未透传 variance/穿透** |

- **扩展性影响**：裸 calc_damage 直调点全都不吃穿透/等级/公式级倍率封装，未来伤害类型扩展（如新增 dmg_type 或公式段能力）要改 20 个调用点；resolve_formula 统一管道后新增能力只需改解释器。
- **建议改法（非本次范围，仅建议）**：battle.py 内 6-7 类直调点收敛到统一"攻击方面板×系数×类型→目标"的薄封装（如 `_dmg_of(attacker_stats, coeff, kind, target)` → 内部 resolve_formula）；core/affix_effects.py、weapon_effects.py 等模块的直调点属通用执行器/模块内，保留亦可（它们本身就是最小封装）。

---

### 四、伤害/治疗是否对玩家/怪物分两套代码

**承伤（被伤害）侧：已统一，验收通过。**
- `_damage_actor`（10009-10122）是唯一承伤核心：玩家/怪共用减伤链/护盾/扣血/on_taken 钩子，`_is_focus_player` 只用于路由"玩家被打时反击目标/挡刀只服务主人"两个玩家专属语义；玩家被打与怪被打都调它。
- DOT：`_tick_actor_dots`（7888+）是 actor-agnostic 统一结算器；落地处仍有两个 if/else 分叉（8037-8065：玩家走 `_damage_actor(e,...)`、怪走 `_enemy_mitigate+_damage_enemy`）——这是**结算链不同阶段的口径差异**（玩家的防守属性在 _damage_actor 链内消费，怪的免伤在 `_enemy_mitigate` 攻击端消费），分叉有注释说明，属结构化遗留而非"两套逻辑"，但要彻底 actor 化需把怪防守属性的消费也挪进 _damage_actor 链。
- 反伤/反击回击（`_retaliations_and_buffs` 9587-9597）：已统一 `_hit_back → _damage_actor`（注释明确修复了旧的 RecursionError 两套代码根）。

**治疗结算侧：❌ 未 actor 化（最显著缺口）。**
- 全引擎**只有玩家向治疗**：`_skill_heal`（5273-5492）治疗目标=玩家/队友（allies 快照），全程 `target_unit["hp"] = min(max_hp, hp_before+heal)` 直接 clamp；**怪物治疗**（怪给怪回血 / 玩家给怪回血 / 带 heal 的敌方召唤）**没有统一入口**——`_monster_cast_playerskill` 把怪的治疗兜进 `_player_skill`，经 `_resolve_ally_target(None)` 时 target_ally=None → target_unit=player 自身（施法者=怪），管线跑"玩家向治疗公式+玩家被动治疗加成"（5375 `heal_power`、5382 `_race_bonus(target_unit)`、5396 禁疗 `self._tgt_buffs()` 等），**怪的治疗量被玩家的治疗强度/受疗天赋/圣光套件/溢出转盾逻辑污染**；且怪治疗走的是 `target_unit["hp"]` 但 `_player_stats`/`_race_bonus` 却用 player 职业——怪没有装备槽时 `_player_stats(怪)` 也会崩或返回战士面板（v180-B 注释已自认怪可配 class_name）。
- **核心缺口**：无 `_heal_actor(actor, amount)` actor-agnostic 治疗核心。回血实现散落 20+ 处（`_skill_heal` 5415、`_psk_lifesteal` 171、`_psk_heal_pct` 190、宠物吸血、各类词条/套装/武器 heal 直写 `hp=min(max_hp,hp+heal)`），互不复用、无统一"受疗/禁疗/溢出转盾"钩子——与伤害侧 `_damage_actor` 一统后形成鲜明对比。
- **建议改法**：新增 `_heal_actor(actor, amount, logs, source)` 作为唯一治疗落地核心（clamp+受疗天赋+禁疗/重伤+溢出转盾统一在核心内），`_skill_heal`/`_psk_*`/weapon_effects 的 `_heal_player` 全部改调它；怪/随从回血走同一核心后，`_monster_cast_playerskill` 的兜底语义自然消除。

---

### 五、其他顺手发现

- **僵尸代码**：`_pvp_enemy_turn`（7350-7376）函数体自注"真实 PVP 不可达……僵尸分支"，仍保留 ~27 行裸 calc_damage 简化结算。
- **反推 hack 两处**：`_aoe_damage`（8740）与 `_guard_redirect_check`（9244）都靠"解一元二次方程反推等效 atk"来套目标防御，是 `_damage_enemy` 只收 dmg 不收攻击方面板的直接恶果。
- **`_is_focus_player` 兜底仍有 class_name 分支**（9947-9954）：side 缺失+引用不等时靠 class_name+不在 enemies 判玩家——老档兼容所需，但新 actor 若既无 side 又恰在 allies 之外带职业，仍可能误判（已在注释中自我标注）。

---

**优先级建议**：① 修 `_damage_enemy` 等级压制读 `self.player`（问题 2，一行级修复+行为一致）；② `_companion_act` true 分支公式漂移（1107-1109 与 calc_damage true 语义不一致，是隐 bug）；③ 猎印/魂标基础值下沉数据（问题 1，防数值失配）；④ 新增 `_heal_actor` 统一治疗核心（问题 4，结构性缺口，工程量最大，建议作为独立重构批次）。

**未创建/修改任何文件**。