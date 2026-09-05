# 通用战斗引擎改造设计（v177：actor-agnostic + 怪物资源化）

> 状态：设计稿 v0.1（待鱼鱼拍板）
> 触发：鱼鱼指出"战斗引擎应对每个对象一视同仁——玩家职业特色/怪物特色都应该是技能 dict 字段配出来的，为什么怪物不能配资源/机制？"
> 关联：Boss 大改造计划（怪物可配资源→Boss 狂暴/充能/信仰等）

## 1. 现状（代码验证）

### 1.1 好消息：底层已经接近通用
- **伤害公式**：`resolve_formula` 统一解释器（既吃 stat/mult 结构化段，也吃 expr 表达式段）✓
- **机制**：玩家 `MECH_EFFECTS` / 怪物 `MON_CTRL_EFFECTS` / 增益 `MON_BUFF_EFFECTS` / 宠物 `PET_SKILL_EFFECTS` —— 全注册表化 ✓
- **技能效果**：玩家技能 22+ 字段（kind/exprs/mech/cond/effect/aoe/element/res_gain...）全是 dict 声明驱动
- **核心资源**：`CORE_RESOURCES` 纯数据（key/name/max/regen/on_attack/on_hit/on_skill/load_tiers/decay/overflow_shield/focus/dual_form...）；`core_resource_def_by_key`/`core_resource_gain_key` 已按 key 注册（actor-agnostic 通道已存在）
- **self.resources** 本来就是通用 dict（随战斗序列化，不挑玩家/怪物）

### 1.2 问题：结算路径不对称
| | 玩家技能 | 怪物技能 |
|---|---|---|
| 施放入口 | `_do_player_skill`（资源/冷却/蓝耗检查） | `_enemy_turn`→`_enemy_cast_done`（读条/蓄力/AI） |
| 伤害解释 | `resolve_formula` ✓ | `resolve_formula` ✓（已同） |
| 命中后管线 | `_player_skill`→抽出的4阶段（mult装配/段循环/后处理/命中结算） | **`_enemy_cast_done` 内联 if**（免伤×3份复制/元素抗性） |
| 机制 | `MECH_EFFECTS` | `MON_CTRL_EFFECTS`（子集） |
| 资源 | 完整（怒/元素/精力/信仰/连击点/气） | **无**（没有 resources 概念） |
| 怪物技能 schema | — | 仅 10 字段（kind/formula/power/mech/element/effect/aoe/charge/desc/name） |

### 1.3 玩家管线身份耦合点（已验证极少）
玩家攻击管线 4 阶段方法中，指向目标的写死 `self.enemy`/`self.e_buffs` 仅 12 处——大部分已通过 `self._active_target` 或参数化。
来源侧耦合集中在 `_res_gain(player,...)` 用 `player.get("class_name")` 查资源定义。

## 2. 设计目标

**战斗引擎 actor-agnostic**：技能结算对玩家/怪物/宠物/召唤物一视同仁，差异只在数据（技能 dict + 资源定义），不在引擎 if。

```
攻击方(actor) 使用 技能(decl_dict) 命中 目标(target)
   ↓
[入口层] 按 actor 类型走不同"行动规则"（玩家=蓝耗/CD/道具；怪物=读条/蓄力/AI）—— 保留不对称
   ↓
[结算层] 统一：乘区装配 → 段循环 → 总伤后处理 → 命中效果/机制/资源 —— 完全同一套
```

## 3. 分阶段落地

### Phase A：资源系统去职业化（怪物可配资源的前提）
1. **`_res_gain/_res_spend/_res_read/_res_max` 去掉对 `player.get("class_name")` 的依赖**，改为从 **actor 携带的资源定义** 解析：
   ```python
   # actor = 玩家 dict 或怪物 dict，都支持：
   actor["resource_def"] = {"key": "rage", "name": "狂怒", "max": 10, "on_hit": 1, ...}
   # 或引用 CORE_RESOURCES：actor["resource_key"] = "rage" → 查表
   ```
2. **`self.resources` → 每个 actor 各自持有**（现在全 battle 共用一个 dict，绑死"玩家主资源"；副本多玩家其实是玩家层各自快照的 resources。要改成 actor dict 上挂 `resources` 字段，玩家兼容读回 `self.resources`）
   - 兼容策略：玩家 `self.resources` 保留（大量旧代码读它），怪物资源放 `enemy["resources"]`，资源方法优先读 actor 自己的 resources
3. **`on_attack/on_hit/on_skill/on_heal` 攒资源挂点抽通用**：现在玩家侧在 `_do_player_skill`/受击被动里 if 攒怒/连击点——抽成 `_actor_gain_resources_on_event(actor, event, logs)`，按 actor 资源定义的 on_* 字段跑

### Phase B：怪物技能 schema 对齐（声明即能力）
怪物技能 dict 开放玩家同款字段（缺省不启用，旧 205 技能零改动）：
```
kind / exprs(成长表达式) / formula / mech / mech2 / mech_val / cond(条件增伤)
effect / buff_turns / hits(多段) / aoe / element / res_gain / res_cost / consume_all
charge(蓄力,已有) / pierce / lifesteal
```
新怪物技能示例（一个狂暴 Boss）：
```python
"ms_kuang_bao": {
    "kind": "物理",
    "exprs": ["atk*1.6 + mon_lv*12"],          # 怪物等级成长
    "res_gain": {"rage": 3},                    # 命中攒怒
    "mech": "zhan_yi",                          # 复用玩家战意机制
    "cond": {"rage_full": {"mult": 1.5, "label": "狂怒"}},  # 满怒增伤
    "name": "狂暴撕咬",
},
"ms_kuang_bao_zhi": {
    "kind": "物理",
    "exprs": ["atk*2.8"],
    "res_cost": {"rage": 10},                   # 耗怒大招
    "consume_all": {"key": "rage", "per": 0.1}, # 或全耗放大
    "name": "狂怒爆发",
}
```
引擎改动 = 0（字段进既有管线即生效）——需验证怪物侧结算接入这些字段。

### Phase C：怪物结算接入统一管线
1. `_enemy_cast_done` 伤害收尾（免伤×3/元素抗性）→ 抽 `_apply_mitigation(actor_side, dmg, kind, element)` 公共函数，4 条怪物伤害路径共用
2. 怪物技能伤害段 → 复用玩家 4 阶段管线（或至少 cond/mech/res_gain 挂点复用），消灭内联 if
3. 怪物普攻也支持 basic_skill dict 声明（已有雏形）→ 走统一公式

### Phase D：Boss 改造受益验证
用 1-2 个示例 Boss 验证"纯配置做出新机制"（狂暴 Boss 攒怒→大招；会"治疗攒信仰→神迹"的 Boss 牧师）——数值门禁 + 实测。

## 4. 兼容与风险
- **旧 205 怪物技能零改动**：字段缺省不启用
- **玩家资源路径不动**：Phase A 加 actor 分支，玩家走原路（self.resources 兼容层）
- **回归门禁**：36 numeric 门禁 + refactor_regression 摘要对比
- **风险最高点**：资源去职业化（self.resources 改 per-actor）——需要先确认副本多玩家资源怎么存（self.resources 是否已经在 player 快照上）

## 5. 关键事实补充（代码验证，v0.2 定稿）

### 5.1 副本资源存储 = per-player（不是 battle 级单槽）
- `self.resources` 是 Battle **单套字段**，代表"当前焦点玩家"
- 副本里每个玩家的资源**按 qq_id 分 key** 存于 `st["resources"][qq_id]`
- `_load_player_state(qq_id)` 把某玩家状态载入单套字段（p_buffs/resources/cooldown...）——**一次只结算一个玩家**
- 怪物单位是 `self.enemies[i]` dict（自带 buffs/stacks/charging）→ **怪物资源天然挂 `enemy["resources"]` 即可**，与玩家 per-player 存储同构

### 5.2 资源方法现状
- `_res_read/_res_spend` 只读 `self.resources`（不查定义上限，spend 只判够不够）
- `_res_gain/_res_gain_class/_res_max` 查 `player.get("class_name")` → CORE_RESOURCES 定义
- `core_resource_def_by_key/gain_key` 已按 key 注册（副资源通道，actor-agnostic）
- `self.resources` 序列化进 st["resources"]（焦点玩家），随战斗恢复

### 5.3 结论：改造面比想象小
1. 怪物单位 dict 增加 `resources: {}` + `resource_def`（或 resource_key 引用 CORE_RESOURCES）
2. `_res_gain/_res_max` 加一个"actor 资源定义"分支：actor 有 resource_def → 用它；没有 → 回退 class_name（玩家路径不动）
3. `_res_read/_res_spend` 改造为可指向指定 actor 的 resources（默认 self.resources 兼容）
4. 攒资源挂点（on_attack/on_hit/on_skill）从"玩家 if 链"抽成通用 `_actor_res_gain_event(actor, event, logs)`——怪物技能/受击也走它

## 7. 鱼鱼拍板方向（v0.3）：actor 字段即能力，不做身份 if

> "怪物为啥不能有这些，不是扯淡吗，这些属性之类的只是 actor 的字段，actor 没有就不算呗，不就通用了"

**核心原则：结算层永远不 if actor 身份（玩家/怪物），只 if actor 字段。**
actor 声明了什么防御/资源字段，结算就消费什么；没声明 = 跳过（自然等于怪物默认行为，玩家默认全量因为装备/职业喂满字段）。

### 7.1 承伤侧事实（代码验证）
怪物承伤**已经数据驱动**：
- `_enemy_mitigate(dmg, magi_part, element, logs)` —— 玩家打怪消费敌方防守属性：物免(≤40%)/魔免(≤40%)/格挡(≤40%)/元素抗(≤50%)，怪没配=0 无感 ✓
- `_boss_dmg_filter` —— 怪物护盾（boss_shield / e_buffs["shield"]）+ 反伤（reflect）✓
- **缺口1（已证伪）**：~~`_enemy_mitigate` 没消费 dodge~~ —— 实际上怪物 dodge 已由 `_monster_dodge_check` 消费（怪物 dict 声明 dodge → 玩家攻击概率 miss，上限 30%，v105 已有）✓
- **缺口2（真实）**：怪物承伤后没有 on_taken 钩子（受击回资源/受击反击/受击触发减伤/回血）——做"受击回怒 Boss/荆棘 Boss/复仇 Boss"缺的
- 怪物受击能力现状盘点：dodge ✓ / block+物免+魔免+元素抗 ✓（_enemy_mitigate）/ 护盾 ✓（_boss_dmg_filter）/ 反伤 ✓（reflect）/ **on_taken ✗**

玩家承伤 `_damage_player` 630 行 = 事实上的"完整承伤链"，但入口 if 了玩家系统
（从 self.p_buffs/p_shields/装备/被动/套装读——这些恰好是玩家字段，怪物没有就不触发，**天然兼容**）。

### 7.2 目标架构

```
_damage_target(target, dmg, ...)   # 谁都能被打
  1. 挡刀拦截（宠物/召唤物 —— 属召唤侧钩子，target 有才走）
  2. dodge 闪避        # target.stats.dodge / buff dodge_up / 被动 dodge_up
  3. block 格挡        # target.stats.block（物段减半 + 格挡反击钩子）
  4. 减伤            # reduce_all / reduce / 被动 dmg_taken / phys·magic_reduce / 元素抗
  5. 护盾吸收         # target.shields（dict 多源）
  6. 扣血 + 致死钩子   # 复活链（target 声明了才走）
  7. 受击后 on_taken   # 受击资源(资源定义 on_hit) / 反伤 / 反击 / 回血
```

玩家：7 步全触发（因为字段全）；怪物：默认只走 3/4（def/mdef 折算）——配置加 dodge/shields/on_taken/resource_def 即获得对应步。**引擎无身份 if**。

### 7.3 资源侧（Phase A，Boss 改造地基）
- 资源定义挂 actor：玩家 `class_name → CORE_RESOURCES`；怪物 `enemy["resource_def"]`（内联或引用 key）
- `_res_gain/_res_read/_res_spend/_res_max` 加 actor 分支：actor 有 resource_def → 用它的 key/max/on_*；没有 → 回退玩家 class 路径
- 攒资源挂点抽通用 `_actor_res_gain_event(actor, event, logs)`：玩家/怪物技能命中、受击都走它
- 怪物 `resources` 挂 enemy dict（与玩家 per-player 存储同构，随战斗序列化）

## 8. 落地批次（已全部完成 2026-09-05/06）
- **Batch 1 ✅**：build_monster 透传 dodge/block/phys_reduce 等 + 怪物 on_taken 钩子（受击回血/激怒/凝甲）——字段即能力验证
- **Batch 2a ✅**：护盾格式统一 `enemy["shields"]` dict（BOSS_MECHS/MON_BUFF_EFFECTS/on_taken 写入 + _boss_dmg_filter 消费全迁，兼容旧格式）
- **Batch 2b ✅**：承伤核心统一 `_damage_actor`——玩家/怪物共用同一份受击结算（原 _damage_player 624 行 actor 化）
- **Batch 3 ✅**：资源系统一套化——`_res_gain/_res_spend` 统一 actor 路由（删净分叉函数），`_res_cap_of` 含词条/套装加成 + 副资源 key 回退
- **Batch 4 ✅**：怪物技能 res_gain/res_cost 接线（AI 门槛不重抽保 random 流）
- **Batch 5 ✅**：承伤回调化 `_damage_actor` 712→114 行——抽 6 个回调方法（_roll_dodge/_mitigate_chain/_retaliations_and_buffs/_monster_on_taken/_post_hp_lethal/_on_taken_rewards），核心只剩编排骨架

**最终形态（_damage_actor 114 行编排骨架）**：
```
_damage_actor(actor, dmg, ...)
  ① 状态容器路由（玩家=焦点字段/怪=actor dict）
  ② 蓄力打断 + 宠物/召唤挡刀
  ③ _roll_dodge 闪避 → ④ 命中日志 → ⑤ _mitigate_chain 减伤链
  ⑥ _retaliations_and_buffs 反击后效 → ⑦ 护盾吸收
  ⑧ 扣血 + 怪物死亡移除 + _monster_on_taken
  ⑨ _post_hp_lethal 复活链 + _on_taken_rewards 受击奖励
  ⑩ 返回实际扣血
```

## 9. 风险与兼容
- 旧 205 怪物技能零改动（新字段缺省不启用）
- 玩家路径零改动（资源 actor 分支只在 actor 有 resource_def 时走）
- 回归：36 numeric 门禁 + refactor_regression + 数值扫描（monster_curve/strength）

### 9.1 已拍板决策（2026-09-05 鱼鱼）
1. **怪物资源定义**：`resource_def` 内联（怪物是数据文件，内联可读性最好，也支持引用 CORE_RESOURCES key 复用玩家条目）
2. **怪物资源条显示**：暂不做 UI，纯机制内部（Boss 战报附一行由日志层按需加，非引擎硬编码）
3. **优先级**：Batch 1（怪物防御补齐 dodge/on_taken）→ Batch 2（资源通用化）→ Batch 3（schema 对齐）→ Batch 4（回归）
4. **范围控制**：不动旧 205 怪物技能（缺省不启用新字段），零回归风险


