审计完成。以下是完整报告。

---

# battle.py 状态容器/序列化重构残留审计报告

审计对象：`game/battle.py`（10133 行）+ 关联 `game/commands/instance.py`、`game/commands/combat.py`、`game/core/tick_effects.py`。未修改任何代码。

## 总览

| # | 严重性 | 位置 | 问题 |
|---|--------|------|------|
| 1 | 🔴 高 | battle.py:9139 | 随从死亡清理段会把无 `hp` 字段的宠物 actor 当尸体从 `companions` 移除 |
| 2 | 🟠 中 | battle.py:9806-9809 | `companions.pop()` 可能把宠物当祭品牺牲 |
| 3 | 🟠 中 | battle.py:1128-1130 + from_state 1439-1461 | tick_effects 序列化 actor_ref 不含宠物/召唤物 actor → 宠物卡每档循环被丢弃（靠补挂兜底） |
| 4 | 🟡 低 | battle.py:1333/1338 vs __init__ 771/776 | `last_element`/`stealth_atk` 序列化丢失，恢复硬编码 None/False |
| 5 | 🟡 低 | battle.py:1219 与 from_state 时序 | 恢复后 tick 卡 actor 引用指向旧空 dict，依赖保险丝同 uid 覆盖，脆弱 |
| 6 | ℹ️ 注意 | battle.py:1084 + instance.py:2568 | `companions` 容器不序列化（summon 走 `summons` 视图、pet 走 `pet` 键重建），设计意图 OK 但需知悉 |
| 7 | ℹ️ 注意 | instance.py:2568-2619 | 副本每行动重建 Battle 且构造 dict 无 `tick_effects` → 所有卡每行动重挂 |

**重点 1（旧焦点字段残留）：通过 5 种正则全量扫描，battle.py 内除注释外已无 `self.p_buffs/self.resources/self.stacks/self.mech_stacks/self.hot` 等直接读/写点，全部收口到 `_p_*` helper 或 `self.player` actor dict。此项干净 ✅**

---

## 🔴 问题 1：随从死亡清理移除"无 hp"的宠物 actor（v180-C 设计破坏）

**文件:行号**: battle.py:9138-9142（调用链：player_turn 尾部 3096-3097 → `_companions_trigger` 9128-9142）

**代码**：
```python
# 清理死亡随从
for c in list(self.companions):
    if c.get("hp", 0) <= 0:
        logs.append(f"💀 {c.get('name', '随从')} 倒下了！")
        self.companions.remove(c)
```

**问题类型**: 容器一致性 bug（宠物 actor 化残留）

**影响**：
- `_pet_ensure_actor`（7672-7696）只补 `side/kind/buffs/hidden/untargetable`，**不补 `hp`**。
- 开战宠物 actor 化进 `companions`（922）→ 玩家第一次行动 → 3096 `companions` 非空 → 清理段把宠物（`hp` 缺省 `get('hp',0)==0 ≤ 0`）当死亡随从移除并刷"💀 宠物 倒下了！"。
- 移除后 `battle.pet` 引用仍在 → pet_act 卡照常出手（`_th_pet_act` 用 `battle.pet`），**功能不崩但 v180-C"宠物 = companions 一员"的统一语义断裂**：治疗广播/增益覆盖/未来 companions 通用逻辑全部失效；且每次玩家行动后宠物反复被踢出容器（同场多次"倒下"文案）。
- 对照：3281 `_process_tick_effects` 用 `get("hp", 1)`（默认 1，不误判），清理段用 `get("hp", 0)`（默认 0）——两处默认值不一致正是病灶。

**建议**: 清理段跳过无 `hp` 字段或 `kind=='pet'` 的实体（`if c.get("hp") is None: continue`）；或在 `_pet_ensure_actor` 补 `pet["hp"] = pet["max_hp"] = 1` 占位（配合 hidden/untargetable 不参与承伤）。倾向前者 + 统一两处 `get` 默认值。

---

## 🟠 问题 2：死亡契约 `companions.pop()` 可能牺牲宠物

**文件:行号**: battle.py:9806-9811

**代码**：
```python
if actor["hp"] <= 0 and self.summons and not self._death_pact_used:
    for _pn, _ps in self._passive_map(actor)["proc"].get("death_pact", []):
        self._death_pact_used = True
        fallen = self.companions.pop()   # ← 弹尾部，不校验 kind
        ...
```

**问题类型**: companions/summons 容器不一致（过滤视图与底层容器混用）

**影响**：
- 守卫条件看的是 `self.summons`（`kind=='summon'` 过滤视图），牺牲时却 `companions.pop()`（底层全量容器尾部）——视图与容器语义错位。
- 宠物 actor 化后是 `companions` 一员且**无 `hp`**：若玩家带召唤物 + 宠物，`pop()` 弹尾部可能把"宠物"当祭品（日志显示"💀 某宠物 替你承受了致命一击"），宠物"死亡"后 `self.pet` 仍活着继续出手——状态矛盾。
- 后续 v169.7 牧师 `death_contract` 链（9826-9827）用 `_skels.pop()` + `companions.remove(fallen)` 则正确（按 tid 过滤后再删）。

**建议**: 改为从 `self.summons` 选牺牲对象（如 `fallen = [s for s in self.companions if s.get("kind")=="summon"][-1]`）后 `companions.remove(fallen)`，与 9826-9827 写法对齐。

---

## 🟠 问题 3：tick_effects 序列化 actor_ref 不覆盖宠物 actor

**文件:行号**: battle.py:1128-1130（to_state）；1439-1461（from_state 恢复）

**代码**：
```python
"actor_ref": ("player" if (e.get("actor") is self.player)
              else next((str(u.get("uid", "")) for u in self.enemies
                         if u is e.get("actor")), ""),
```
```python
if _ref == "player": _actor = b.player
else:  # 只在 enemies 里按 uid 找
    ...
if _actor is None: continue  # 找不到 actor → 丢弃
```

**问题类型**: 序列化 actor 引用丢失（宠物 actor 化后的残留盲区）

**影响**：
- 宠物 `pet_act` 卡 actor = `self.pet`（926/1410/7763）——既不是 `self.player` 也不在 `enemies` → `actor_ref=''` → from_state 恢复时被 `continue` **丢弃**。
- 功能上被 from_state 尾部 1402-1413"池里无 pet_act 卡则补挂"兜底救回 → 宠物卡能恢复，但**下次触发时刻/节奏被重置**（重新从 skill_interval 起步，丢失原 next_at），且每次存档恢复都白白丢一张卡再补一张，属于设计冗余 + 隐患（未来任何"以 companions 成员为 actor"的卡都会踩同坑）。
- 召唤物同理：若未来给召唤物挂周期卡（如光环 tick），actor_ref 无编码路径会直接丢。

**建议**: actor_ref 增加第三态，如 `"pet"` / `"companion:<id>"`（或 pet 用 `"pet"` 字面量），from_state 恢复分支对应绑 `b.pet` / 按索引查 `b.companions`；同时 data 内禁止 actor dict 引用（现状符合）。

---

## 🟡 问题 4：`last_element` / `stealth_atk` 序列化丢失

**文件:行号**: battle.py:1333, 1338（from_state `_restore_pstate` 硬编码）；对比 __init__ 播种 771, 776

**代码**：
```python
"last_element": None,          # 1333 — 永远重置
"stealth_atk": False,          # 1338 — 永远重置
```
（to_state 1057-1134 无此两键输出）

**问题类型**: 字段丢失（老档兼容 + 状态续接）

**影响**：
- **`last_element`**：元素法师「元素凝聚」同系连发判定（5836 `_last_element_set` → 6194 读）依赖跨行动记忆。断线/续战恢复后 `last_element=None` → 恢复后第一次同系施法判定为"非连发"，少 +1 充能一次（影响面小：每个战斗会话一次）。
- **`stealth_atk`**：潜行出手标记是刻内瞬态（6260 出手前复位 / 6264 出手时置位，消费在当刻）→ 丢了对战局几乎无影响（除非恢复点恰在出手标记置位后、命中消费前——P2 读条窗口内存在该可能，但窗口极短）。
- 附带发现：`_load_player_state`（1136-1211）播种快照时（1157-1172）也没补 `last_element/stealth_atk` 键（不过有 `_p_*` helper get 兜底 None/False，不崩）。

**建议**: to_state 补输出 `last_element`（值级，可放顶层）；`stealth_atk` 可接受不序列化（瞬态），但建议注释说明刻意为之。`last_element` 属轻量跨消息状态，建议序列化。

---

## 🟡 问题 5：from_state 恢复的 tick 卡 actor 引用是"占位空 dict"（绑定后悬空）

**文件:行号**: battle.py:1444-1445 + 1446-1461（恢复）；调用方 combat.py:910-911

**代码**：
```python
if _ref == "player":
    _actor = b.player          # from_state 构造时 player 未传 → b.player = __init__ 播种的空 dict {}
```
```python
b = BT.Battle.from_state(battle["state"])   # combat.py:910
b.player = player                            # combat.py:911 换引用 → 卡的 actor 悬空在旧空 dict
```

**问题类型**: actor 引用一致性（恢复时序依赖）

**影响**：
- 所有 `actor_ref=='player'` 的卡（`food_hot`/`regen_*`/玩家侧 `actor_dot`）恢复时 actor 绑到 `b.player`（空 dict 占位）；命令层 911 换绑真实 player 后**卡的 actor 仍是旧空 dict**。
- 目前靠 `_turn_start` 保险丝（2940-2948 food_hot / 8460-8463 DOT / 8466+ regen）以同 uid 幂等补挂真实 actor 的卡 → **覆盖**旧卡，时序上保险丝在行动窗口 `_process_until` 前跑，故实际不炸。但这是"碰巧安全"：任何一次保险丝条件不满足（如 p_hot turns 已在序列化瞬间归零）时，旧空 dict 卡触发 → `_th_food_hot` 写 `actor['hp']` 到空 dict（606-619）→ 回血落空；`_th_actor_dot` 读空 dict debuffs 空转。静默丢失。
- 注：__init__ 单独播种空 dict 的语义就是给 `setdefault` 惰性袋用的，但 tick 卡的 actor 需要的是**真实面板**（max_hp/max_mp 用于算恢复量），空 dict 完全失效。

**建议**: from_state 恢复 `actor_ref=='player'` 的卡时，若 `b.player` 为空 dict 则暂存"待绑卡"（或直接把 actor 置 None + `_apply_restore_pstate`/`_bind_player` 时统一重绑），而不是靠保险丝被动覆盖。至少把恢复 actor 改为 `getattr(b, "_player", None) or b.player` 语义并注释该约束。

---

## ℹ️ 问题 6：`companions` 容器整体不序列化（设计确认，非 bug）

**文件:行号**: battle.py:1084（to_state 只输出 `summons` 过滤视图）；1342（from_state setter 重建）

**要点**：
- `companions` 含两类实体：summon（kind=='summon'，随 to_state `summons` 键输出、setter 1342 重建）与 **pet（kind=='pet'，不走 summons 视图）**。
- pet 重建路径：from_state → `__init__(pet=st['pet'])` → 1406 `_pet_ensure_actor()` 幂等补 actor 字段 + 重进 companions。引用一致性 OK。
- **风险点**：老档 `st['pet']` 与 1342 `b.summons=...` 的执行顺序——若老档同时有 pet + summon，from_state 先 setter 恢复 summon（1326 区域），宠物 1402-1413 才 actor 化，顺序无冲突 ✅。但 to_state 中 `"pet": self.pet` 直传引用 → 存档 dict 序列化时若 DB 层 json 深拷贝则 OK，若浅引用共享则宠物在 companions 内的变更（如未来受击掉 hp）会随 companions（不序列化）丢失、只留 pet 键 → 需知悉 companions 内宠物侧字段变更必须同步回 `self.pet`（当前同对象引用，天然一致；未来若复制则断）。
- **额外注意**：`summons` setter（1025-1039）恢复时对每个实体 `setdefault("kind","summon")`——老档 summon 实体无 kind → 补上 ✅；但 setter 里 `dict(c)` 拷贝意味着**恢复后的 summon 与战斗内其他引用不是同一对象**——目前无外部持引用，安全，但未来若 tick 卡以 summon 为 actor 会踩问题 3 同坑。

---

## ℹ️ 问题 7：副本 instance 每行动重建 Battle，tick_effects 不跨行动（性能/语义注意）

**文件:行号**: instance.py:2568-2619（from_state 构造 dict 无 `tick_effects` 键）；instance.py:2626（每行动 player_turn 后整体写回 st，不调 `b.to_state()`）

**影响**：
- 副本每次玩家行动都从 st 重建全新 Battle → tick_effects 池从空开始 → 所有周期卡（regen/DOT/food_hot/pet_act）靠 `_turn_start` 保险丝（8460-8469）在**当前行动者**身上补挂。
- 跨行动连续性由 actor dict 权威状态兜底：DOT 层数在 `actor['debuffs']`（快照写回 2636）、food_hot turns 在 `actor['hot']`（2640）、宠物节奏在 `st['pets']`（2662）——**数据不丢，但"卡存在性"每行动重建**：
  - 敌方身上的 DOT 卡：只有该行动者窗口内推进到敌方行动才结算，多玩家轮转间 DOT 结算时机被压缩/推迟（每行动一次窗口）。
  - 宠物 pet_act 卡：每行动窗口起步 → 多玩家副本中宠物出手频率可能被"行动重建"节流（每窗口只续排一次）。
- 与野外（to_state/from_state 全量持久化 tick_effects）行为不一致。v179"通用卡序列化随战斗持久化"的设计在副本路径未落地。

**建议**: instance.py 从_state 构造 dict 增加 `"tick_effects": st.get("tick_effects", [])` 透传 + 写回（st 增加 tick_effects 键，注意 uid 需带 player 维度防串号），或至少在架构文档标注"副本每行动重建 Battle，周期效果以 actor dict 为权威、卡仅当行动窗口有效"的既定语义。

---

## 未发现问题（复核确认）

- **旧焦点字段残留**：battle.py 全文件仅 782 行注释提及 `self.p_buffs/self.resources`（历史说明），无实际代码引用 ✅
- **to_state ↔ __init__ 字段映射**：20 个 seed 字段全部有对应输出键（`stacks→mech_stacks`、`eff→eff_data`、`buffs→p_buffs` 等别名），除问题 4 的两个字段外无丢失 ✅
- **老档兼容**：`round→p_acts` 兜底、`e_buffs` 并入主怪、`mech_stacks` 旧毒/灼/印迁移 debuffs、`p_food_affixes` 别名、`_tenacity_left` 默认 3 等兼容路径齐全 ✅
- **append 到 self.summons**：全文件无任何 `self.summons.append/remove/+=` 调用（仅 1205 一处 setter 赋值走整袋替换）——property 视图静默失效风险不存在 ✅
- **pet 与 companions 同引用**：`_pet_ensure_actor` 用 `any(c is pet ...)` 引用判等 + 就地补字段，pet 在 companions 中与 `self.pet` 是同一 dict（问题 1 移除前成立）✅

---

## 修复优先级建议

1. **立即**：问题 1（9139 清理段跳过无 hp / kind=='pet' 实体）——v180-C 宠物 actor 化语义被每行动破坏，且会产生误导性"宠物倒下"文案。
2. **随下个战斗版本**：问题 2（死亡契约 pop 改为 summons 内选择）；问题 3（actor_ref 增加 pet 编码）。
3. **低优先级**：问题 4（last_element 补序列化）；问题 5（恢复卡 actor 待绑机制）；问题 7（副本 tick_effects 透传，或文档标注）。