# battle2 周期效果统一机制（DOT/HOT 合并）设计方案

> 2026-09-08。鱼鱼拍板「做干净」：消灭多套周期效果实现，统一成一个引擎概念。
> 触发：I1 用独立容器 `actor["hot"]` 实现 HOT，鱼鱼质疑「DOT/HOT 本质同构
> （一个加一个减），能不能基于 buff/state 统一」。深挖后发现引擎里周期效果
> 实际有 2.5 套实现，本文档给统一方案。
> 新会话口令：「读 docs/archive/REFACTOR_v181P4_N5B5a_unified_periodic.md，从第 X 步开始」

---

## 0. 现状盘点（代码证据）——为什么必须统一

battle2 当前周期/持续效果实际存在 **2.5 套**实现：

| # | 机制 | 载体 | 数值形态 | 结算点 | 现状 |
|---|---|---|---|---|---|
| 1 | DOT（掉血） | `actor["state"][key]=层数` + STATE_EFFECTS 表 dot 规则 | **静态**（表声明每层 pct） | schedule `_settle_time_effects` DOT 段 | 已建好（N7.4/N9），v1252 断言在 |
| 2 | HOT（回血，I1 新做） | `actor["hot"]={heal%,mana%,turns}` 独立容器 | **动态**（每件食物自带） | schedule 独立 hot 段（I1 616431e） | 刚做，不干净 |
| 2.5 | 装备回春/冥想 | `actor["triggers"]["turn_start"]` 事件 → heal 动词 | 静态（装配层翻译） | 事件总线（turn_start） | 事件语义，非墙钟周期 |

**核心矛盾（鱼鱼问题的答案）**：
- 引擎需要**一个**"周期效果"概念（挂载 → 每 interval 结算 → 耗尽/到期移除），
  方向伤害/治疗只是声明不同。
- 但数值形态分两类，决定了承载容器**不能全塞 state**：
  - **静态数值（每层强度查表）** → state 层数天然匹配（burn cap5 每层 3%）
  - **动态数值（每件道具自带）** → state 的 int 层数放不下 → 需要能内嵌数值的
    快照容器 = **buff 条目**

证据（items.py 食物 hot 数值分布——连续多变，静态表无法表达）：
```
hot: 0.03×4 / 0.05×2 / 0.06×9 / 0.08×8 / 0.1×1      （每件食物各自不同）
hot_mana: 0.04×3 / 0.06×3 / 0.08×6 / 0.12×3
hot_turns: 3×29 / 4×2 / 5×1
```
若硬塞 state：每档数值一个 key（hot_06/hot_08…）→ 表爆炸且失去数据驱动意义。

**结论：不是「DOT/HOT 全并进 state」，而是「周期效果统一成一个引擎结算段，
声明载体按数值形态分工」：**
- state = 叠层 + 静态表驱动（DOT 现状；未来可叠层 HOT 也走这里，加 heal 方向规则）
- buff 条目 = 到期快照 + 动态数值（食物 HOT 迁这里）

---

## 1. 目标架构

```
引擎概念：周期效果 periodic effect（唯一）
  声明载体 A：actor["state"][key] 层数 + STATE_EFFECTS 表规则
              （dot 伤害 / 未来 heal 方向叠层恢复——静态每层强度，多源叠加）
  声明载体 B：actor["buffs"][key] 条目带 tick 声明
              （食物 HOT——动态数值内嵌条目，expire 到期自动删）

schedule._settle_time_effects —— 统一周期结算（一段代码）：
  遍历 actor：
    ① buffs 到期删（现状保留）
    ② buffs 条目带 tick 声明 → 每 interval 结算一次
       （方向 heal/mana：landing.heal_actor + mp 直改）
    ③ shields 到期删（现状保留）
    ④ state 规则带周期声明（dot 现状 + 未来 heal）→ 每 interval 结算
       （方向 damage：deal_damage / 方向 heal：heal_actor）
  方向、interval、数值全部由声明/表给出 —— 引擎零硬编码、零名词
```

**核心不变式**：
1. 一个结算段，不再有 "hot 段 / DOT 段" 的平行实现。
2. 周期声明只有两个落点：state（静态叠层）或 buffs（动态快照）。
3. 引擎不认识"食物/料理/灼烧/回春"任何名词——只认声明的方向与数值。
4. buff 到期机制复用（expire 自动删）→ hot 不需要自己的 turns 递减逻辑：
   食物 hot 的 turns 直接折算进 expire（now + turns×interval），tick 跳完
   自然到期删除——**比 I1 容器版更简**。

---

## 2. 具体设计

### 2.1 buff 条目扩展：tick 声明（新增引擎能力）

buff 条目增加可选 `tick` 字段（现有 act_buff 动词扩展参数）：

```python
# 食物 HOT 落点（动态数值内嵌 + expire 到期自动删）：
actor["buffs"]["regen_hot"] = {
    "expire": now + turns * interval,        # 复用 buff 到期段
    "tick": {"interval": 1.0, "heal": 0.06, "mana": 0.08},
    # 首次挂载 last_tick 缺省 = 挂载时刻（同刻不跳，对齐旧首跳延迟）
}
```

- 结算：`now >= last_tick + interval` → heal_actor + mp 直改 → `last_tick += interval`
  → 循环补跳跨多刻（同 DOT 现状）
- 到期：`expire <= now` → 删条目（现有 buff 到期段，零新增）
- 同 key 刷新：act_buff 现有 expire max 逻辑自然生效（重复吃取 expire 大者）
- **可选 value 型 tick**（后续需要）：`"tick": {"interval": 1.0, "value": 50}` 固定量恢复

### 2.2 act_buff 动词扩展

```python
# params 带 tick dict → 快照进条目（turns 折算 expire 与 interval 乘积）
{"action": "buff", "key": "regen_hot", "turns": 3,
 "tick": {"interval": 1.0, "heal": 0.06, "mana": 0.08}, "on": "caster"}
```
引擎动词一处支持，翻译器/上层只需声明。act_buff 逻辑：
- tick 声明存在 → 条目加 `tick` + `last_tick`（=now）
- expire 计算兼容 tick：`now + turns*interval`（turns 仍是"跳数"语义，数据层友好）

### 2.3 state 周期规则扩展（为未来可叠层 HOT 预留，本批做表/结算支持）

STATE_EFFECTS 表周期声明从 dot 泛化为支持方向：

```python
# 现状（伤害方向，兼容不动）：
"burn": {"cap": 5, "on": "target", "dot": {"pct_max_hp": 0.03, "interval": 1.0}}
# 未来可叠层 HOT（示例——本批只做引擎支持，不建具体 key）：
"regenerative": {"cap": 5, "on": "caster",
                 "period": {"heal_pct_max_hp": 0.01, "interval": 1.0, "turns": 4}}
```
结算段同时认 `dot` / `period` 声明，按子键方向分流（damage/heal/mana）。
**收益：鱼鱼问的「hot 以后要叠层」= 数据层加一条声明，引擎零改动。**

### 2.4 翻译器 hot 段改挂 buff tick（I2 文件小改）

`battle_item_use.translate()` 收到 `hot:hp%,mp%,turns` → 不再写
`actor["hot"]`，改构造 buff tick 动作调 apply_effects：

```python
apply_effects(battle, actor, actor,
    [{"action": "buff", "key": "regen_hot", "turns": turns,
      "tick": {"interval": 1.0, "heal": hpct, "mana": mpct}, "on": "caster"}], logs)
```
数值仍动态来自 payload；不叠加取高语义由 act_buff expire max + 覆盖处理
（本批保持旧「不叠加取高」：同 key 刷新，数值取新值——旧引擎是取 max，
见 §5 行为差异；如需严格取高，翻译器先读现有条目再 max，一行逻辑）。

### 2.5 actor["hot"] 容器与 bridge/视图处置

- 引擎侧：schedule hot 段删除，引擎不再读 `actor["hot"]`。
- actors.py：`"hot": dict` 播种保留（旧档兼容透传无害）还是删？
  **本批保留播种 + bridge/instance_battle 透传**（st["p_hot"] 视图、旧档
  battle.py 玩家快照仍可能携带），但 battle2 引擎零消费。
  彻底清除并入 N10 删旧引擎批（旧 battle.py 还在跑普通野外战斗，p_hot 不能动）。
- 注释标明「battle2 引擎不消费 hot 容器——HOT 统一走 buffs tick 声明」。

### 2.6 事件型 regen（第 2.5 套）处理

装配层 turn_start → heal（装备回春/冥想）是**事件语义**（每行动触发一次），
非墙钟周期。本方案**不动**（与 affix 装配层批一起收口，已在 N9.7 范围）。
文档记录：未来若要求回春改墙钟秒制，可平移成 buff tick（同 2.1）。

---

## 3. 行为差异（本批完成后 vs I1 容器版/旧引擎）

| 维度 | 旧引擎 / I1 容器版 | 新 buff tick 版 |
|---|---|---|
| hot 首跳 | 挂载后 1s（墙钟） | 挂载后 interval=1s（同刻不跳，一致） |
| 跳数 | turns 递减容器 | turns 折算 expire，跳完自然到期（总跳数一致） |
| 重复吃食物 | 不叠加取高（max） | 同 key 刷新：expire 取 max；数值覆盖（需 §2.4 取高微调对齐） |
| 中途净化 | 无（hot 不被清） | buffs 条目可能被 cleanse 清？——cleanse 只清 CLEANSE_TAGS 控制键，regen_hot 不在清单 → 不被清（一致） |
| 序列化 | hot/hot_next 字段 | buffs 条目天然序列化（零新增） |
| 多来源并存 | 一个容器互斥 | buffs 多 key 并存（更强，未来扩展自由） |
| heal_actor/on_heal 事件 | 有 | 有（一致） |

---

## 4. 文件改动清单（落地级）

| 文件 | 改动 |
|---|---|
| `game/battle2/effects.py` | act_buff 扩展 tick 参数（条目写 tick + expire 折算跳数×interval + last_tick 播种） |
| `game/battle2/schedule.py` | 删 I1 hot 独立段；buff tick 结算并入现有 buffs 段或独立小子段；state 周期段认 period 声明（heal 方向分流）；DOT 段保留行为零变化 |
| `game/commands/battle_item_use.py` | hot: 分支改 buff tick 动作（删 actor["hot"] 直写）；重复吃取高微调 |
| `game/data/battle_rules.py` | STATE_EFFECTS 注释/声明支持 period（可加 1 条示例但不建游戏 key，等数值设计） |
| `tests/test_battle_hot_regen.py` | 重写：buff tick 语义（首跳/到期/补跳/同 key 刷新/clamp/auto_run 集成） |
| `tests/test_battle_item_use.py` | hot 断言改（actor["buffs"]["regen_hot"] tick 条目） |
| `docs/archive/REFACTOR_v181P4_N5B5a_use_item_design.md` | §4 hot 段落修正（容器版 → buff tick 版）；§2.2 cast 默认修正（1.0 非 defend） |

---

## 5. 分步执行 + 验证（每步 commit）

| 步 | 内容 | 验证 |
|---|---|---|
| U1 | effects.act_buff 扩展 tick（动词一处）+ actors 无改动 | 单测：buff tick 条目写入/expire 折算/重复刷新 |
| U2 | schedule：删 hot 段 → buff tick 结算 + state period 方向分流（DOT 行为零变化） | test_battle_hot_regen 重写绿 + battle2 全套绿（含 n4 DOT/v1252 断言） |
| U3 | battle_item_use hot 分支改 buff tick（取高微调） | test_battle_item_use hot 断言绿 |
| U4 | bridge/instance_battle/actors hot 键注释 + 回归 | 全套绿 + 序列化 roundtrip（buff tick 透传） |
| U5 | 设计文档 §4/§2.2 修正 + HANDOFF + diff 给鱼鱼过目 | — |

> U1-U2 是引擎侧，需鱼鱼把关；U3-U5 命令层收尾。
> I1 commit 616431e 的 hot 容器代码在 U2 中被替换（git 历史保留，无需 revert）。

---

## 6. 缺口记录（本批不做）

- 事件型 regen（turn_start heal）仍走装配层事件（§2.6）。
- state period heal 方向仅引擎支持 + 示例声明，不建正式游戏 key（数值设计另开）。
- actor["hot"] 容器键保留透传，彻底删除并 N10 删旧引擎批。
- cleanse 对 tick 型 buff 的显式净化规则（当前不在 CLEANSE_TAGS → 不清，一致即可）。
