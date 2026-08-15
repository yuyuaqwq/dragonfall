# CTB 重构规格（v121：速度机制全面改造）

> 目标：把「固定轮次 + v61 差值进度条」的速度机制整体替换为 **CTB（Charge Time Battle）全局行动时间轴**。
> 范围：**全部 PVE 战斗统一**——野外遇怪（monster）、世界 Boss（worldboss）、副本组队（instance）。
> 例外：**PVP 不介入**（1v1 真人轮流异步，速度机制不生效，保持现状）。
> 允许：存档不兼容（后续删档）；无用老代码直接删除。

## 一、CTB 模型

### 1.1 基本公式

每个战斗单位（玩家侧每个玩家 / 敌方阵列每个单位）维护一个 `ct`（float，距离下次行动还需的时间，**越小越先行动**）。

```
cost = BASE_DELAY / max(1, spd_effective)      # 行动消耗（BASE_DELAY 常量，初值 100，待模拟标定）
```

- 单位**行动后**：自身 `ct += cost`；**其余所有存活单位 `ct -= cost`**（时间流逝，纯增量实现，无绝对值漂移）。
- **下一个行动者** = 所有存活单位中 `ct` 最小者。
- **开局初始化**：`ct = -spd`（更快者更负 → 先行动；同速玩家方先，保底与现状一致）。
- 速度增益/减益直接作用于 `spd_effective`：`spd_up ×1.40`、`spd_down ×0.5`、符文疾风、疾风药剂、食物等——沿用现有 `_player_stats`/`_enemy_stats` 算出的 spd 即可。
- **速度频率数学等价性**（标定依据）：v61 下快方行动比 = `spd_fast/spd_slow`（每攒够慢方速度得 1 次额外行动）；CTB 下 cost 反比于 spd，行动比同为 `spd_fast/spd_slow`。数值风险主要在分布差异（v61 封顶每回合 2 次额外 = 快方最多 3 动；CTB 无轮、极端速度比会如实呈现）。
- **防极端**：参与 ct 计算的 spd 取软上限 `min(spd, 80)`（初值，Agent D 模拟后定稿）。不加 cost 下限。

### 1.2 调度流程（battle.py，单机/野外/世界 Boss）

```
玩家行动（player_turn 正常回合，round += 1，_turn_start 结算照旧）
  → 玩家 ct += cost_p（其余敌方单位 ct -= cost_p）
  → 敌方行动段：while 敌方存活单位中最小 ct < 玩家 ct：
       该单位行动一次（_enemy_turn(player, unit)），行动后该单位 ct += cost_e、其余单位（含玩家）ct -= cost_e
  → _end_round()（buff 回合/护盾/冷却递减，与现状同频：每玩家行动 1 次结算 1 次）
```

- 敌方单位**可能连动**（速度快者），也可能**零动**（速度慢者本轮轮不到）——这是 CTB 的核心体验，取代 v61 额外行动与 e_first。
- 敌方单位死亡 → 移出 ct 池；玩家死亡 → 战斗结束判定不变。
- `_enemy_phase` 从「每个存活敌方单位各行动一次」改为上述 while 判定。
- 保护：while 循环必须有硬上限（如单次玩家行动后敌方最多连动 8 次，防御极端配速死循环），上限内正常结算。

### 1.3 控制语义（CTB 化）

- 敌方 `stun/freeze`：ct 判定轮到它行动时 → 跳过行动 + **该单位 `ct += cost`**（行动被浪费，下次更晚）；保留「行动消费点」pop 语义（现状 v95.24 的吞掉问题在 CTB 下天然消失——敌方总会轮到行动）。
- 玩家 `stun/freeze`：轮到该玩家行动时 → 跳过 + `ct += cost`，随后进入敌方行动段判定。
- `sleep`：受击解除 + 回合递减（_end_round），语义不变。
- 敌方蓄力 `_enemy_charge_tick`：在其行动时 left-1（不变）；玩家蓄力 `_player_charge_release`：玩家行动时 left-1（不变）。

### 1.4 副本调度（instance.py，多对多轮流）

```
每个玩家快照有独立 ct（存 st["players"][qq]["ct"]）；敌方单位 ct 存单位字段 u["ct"]。
每次行动后（玩家或敌方）：
  写回该单位 ct（玩家 ct 写快照；敌方 ct 随敌人阵列持久化）
  重算下一行动者 = 存活玩家与存活敌方单位中 ct 最小者
    · 敌方最小 → 执行 _instance_enemy_one_act（可连续多个敌方行动，直到玩家侧最小 ct 更小或敌方全灭）→ 展示 → 继续重算
    · 玩家最小 → st["turn"] 指向该玩家（真人操作，超时 60s 自动防御照旧）
```

- 行动顺序展示：开本/每次行动后展示动态队列预览（按当前 ct 排序前 ~8 名，标注敌我），替换 `⚡ 行动顺序(按速度)`。
- 超时自动防御：轮到某玩家超时 → 自动防御结算（含该玩家 ct 结算）→ 重算下一行动者 → 转给下一个该行动的人。
- 仇恨/嘲讽/目标选择、击杀奖励、切怪/分层/通关流程全部不变。

## 二、字段与存档（v3，不兼容）

### 2.1 battle.py 删除字段

- `p_progress` / `e_progress` / `p_extra_left` / `e_extra_left` / `e_first`（含 `__init__` 初始化、`to_state`/`from_state`、`_speed_plan`、`_speed_advice`、`player_turn` 内全部相关分支：额外行动阶段 573-603、`_speed_plan` 调用 635-639、e_first 先手 684-692、速度优势提示 705-713、`_enemy_phase` 的 batches 额外批次 740-742、`_do_defend`/`_do_flee` 的 e_extra 参数）。

### 2.2 battle.py 新增字段

- `p_ct: float`（玩家侧，单机 = 玩家自己；序列化键 `"p_ct"`）。
- 敌方单位 ct：直接存单位 dict 字段 `u["ct"]`（enemies 阵列本已序列化，无需额外键）。
- `to_state` 加 `"p_ct": self.p_ct`；`from_state` 读 `st.get("p_ct", 0.0)`，并为老敌人单位兜底 `u.setdefault("ct", -u.get("spd", 0))`。
- `__init__` 初始化：`self.p_ct = -p_spd`（开局快者先手；p_spd 用 `_player_stats` 现值，若无 player 则 0）。

### 2.3 instance.py 字段

- 玩家快照加 `"ct"`：开本时 `st["players"][qq]["ct"] = -spd`。
- 删除：`st["p_progress"]` / `st["e_progress"]` / `st["p_extra_left"]` / `st["e_extra_left"]` / `st["e_first"]` 的全部透传与写回（from_state 构造 1393-1402、写回 1417-1423、`_instance_enemy_one_act` 构造 1811-1816、写回 1841-1846）。
- 删除 v57 Boss 多动（`_instance_boss_turn` 的 avg_spd/boss_spd/extra 逻辑 1722-1748）——被 CTB 敌方连动天然取代。
- `_instance_boss_turn` 改为 `_instance_enemy_ct_acts`：while 敌方最小 ct < 玩家侧最小 ct → 该单位 `_instance_enemy_one_act` → 更新 ct → 循环。

### 2.4 其他引用清理（全项目 grep）

- `game/commands/combat.py:1695-1696`（p_extra_left 提示）→ 删除或替换为 CTB 队列提示。
- `game/store/battle_state.py`：检查是否有进度条字段清单。
- `game/commands/social.py:352-364`（行动顺序按 spd 显示）→ 改为按 ct 排序或保留 spd 排序（展示语义，可选）。
- `game/battle.py` 内 `_speed_advice`、额外行动相关文案全部删除。

## 三、保留不变的语义（铁律）

1. `round` 语义：玩家正常行动 1 次 +1（battle.py:620）；副本 st["round"] 透传同口径。
2. `_turn_start`（DOT/回血/核心资源）在玩家行动时结算；`_end_round`（buff/护盾/冷却递减）在玩家行动后的敌方段结束时结算。
3. 伤害公式、暴击/闪避/格挡/穿透/韧性、装备词条、被动、符文、药水、食物、宠物、召唤、蓄力、AOE、站位/射程/仇恨/嘲讽、Boss 机制（mech/phase/stacks/狂暴/低血反制）——全部不动。
4. 技能冷却（回合制）、连招序列、核心资源——不动。
5. 战斗条件 `speed_gt`/`speed_ratio`（battle_conds.py）——保留（速度值本身仍有意义）。
6. PVP（btype=="pvp"）——不介入 CTB，保持真人轮流现状。
7. 玩家额外行动的「自由选择出手」提示全部移除——CTB 下没有额外行动概念，快 = 更频繁轮到，每轮都是完整回合。

## 四、数值标定（Agent D）

- 初值 `BASE_DELAY = 100`；spd 软上限 80。
- 用新引擎跑与旧 sim 等价的场景（参照 `scripts/sim_v57_normal.py`、`scripts/sim_lv2_vs_elite4.py` 的场景与胜率基线），验证胜率不崩。
- 测极端配速（3:1、5:1）行动分布与战斗时长，决定软上限最终值。
- 产出 `scripts/sim_ctb_balance.py` + 结论写回本规格第五节。

## 五、测试（Agent C）

- 删除 `tests/test_v61_speed_progress.py`，新建 `tests/test_ctb_speed.py`：
  1. 开局先手：快者先动（ct=-spd）
  2. 行动频率：spd 20 vs 10 → 长程模拟行动比 ≈ 2:1
  3. 速度 buff（spd_up ×1.4）/减速（spd_down ×0.5）改变行动频率
  4. 敌方连动：速度碾压时同段多个敌方行动；慢怪零动
  5. 控制：眩晕跳过行动且 ct 照走
  6. 存档往返：p_ct 与单位 ct 保留；老存档兜底
  7. 副本：下一行动者判定（敌我穿插）、超时自动防御后重算
  8. PVP 不介入
- 全量回归：跑 `python tests/test_*.py`（或 pytest），修复因 CTB 破坏的既有测试；与 CTB 无关的既有失败只报告不修。

## 六、验收标准

1. `grep -r "p_extra_left\|e_extra_left\|p_progress\|e_progress\|e_first\|_speed_plan\|_speed_advice" game/ scripts/ tests/` 无残留（test 文件删除后）。
2. 全量测试通过（CTB 无关的既有失败除外，需报告）。
3. 野外/世界 Boss/副本三条路径冒烟可用（命令层 player_turn 返回值结构不变：logs, ended）。
4. 模拟脚本产出标定结论。
