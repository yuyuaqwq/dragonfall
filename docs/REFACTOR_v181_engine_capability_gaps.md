# v181 引擎能力缺口清单（2026-09-11 盘点 · 字段级方案）

> **状态：待拍板**。本文是**需要动引擎**的全部剩余项——逐项给了字段级改法、
> 影响面与替代方案。除这 4 项外，其余"未完成项"都在内容侧（数据/装配层），
> 引擎不需要改。
>
> 盘点方法：`grep` 引擎全部模块 + 内容侧消费点双向核对（**只认消费端，不认声明端**）。

---

## G1 · 承伤/治疗的「落地对象替换」钩子（挡刀 + `faith_share` 共用）

### 现状

- 内容侧声明了三种"挡刀"，**全部零消费方**：
  - 随从 `SUMMONS[*].bodyguard`（0.40）/ `absorb_once`（True）——`game/data/summons.py`
  - `protect` 技能（誓约之盾 85 / 守护誓言 90，"为队友挡刀并反伤 30%/50%"）——**在 20 个静默 no-op 名单里**
- `faith_share`（牧师，"治疗伤害分担"）：`passive_procs` 已把它登记进 `KNOWN_GAPS`，事实是引擎没有这个概念。

### 为什么必须动引擎

伤害/治疗**落地是引擎收口**（`saintess_engine/battle/landing.py::deal_damage` / `heal_actor`）。
内容侧拿不到"这次落地要打谁"的决定权——`taken_calc` 触发器只能改**数值**（`ctx["mult"]`），
改不了**对象**。内容侧硬做的唯一办法是"把 mult 压到 ~0 + 自己再调一次 deal_damage"，
会有 `max(1, …)` 的取整损耗与递归风险（不推荐，但零引擎改动，可作为过渡）。

### 建议改法（约 15 行，`landing.deal_damage` 护盾段之前）

```python
# 承伤/治疗对象替换钩子（引擎零游戏知识：只读字段 + 调内容侧回调）
_redirect = target.get("_redirect_to")            # 内容侧写入的保护者 uid
if _redirect:
    _guard = battle.find_actor(_redirect)         # 需补一个按 uid 查 actor 的只读方法
    if _guard and actor_alive(_guard) and _guard is not target:
        # 回调让内容侧决定"这次是否真的转移"（概率 / 次数 / 反伤）
        _rule = battle.redirect_hook or (lambda b, t, g, amount, kind: True)
        if _rule(battle, target, _guard, amount, dmg_kind):
            return deal_damage(battle, source, _guard, amount, logs,
                               dmg_kind=dmg_kind, element=element)
```

- `heal_actor` 同款加一个（`faith_share` = 治疗转移）。
- `Battle` 加两个成员：`redirect_hook` / `heal_redirect_hook`（构造参数注入，与既有
  `target_picker` / `on_event` / `script_hook` **同构**——这是引擎既有的"决策注入点"模式，
  不引入新范式）。
- 递归保护：转移后的落地**不再查 `_redirect_to`**（或加深度上限 1）。

### 影响面

- 引擎：`landing.py` + `battle.py`（`find_actor` + 两个 hook 字段）。
- 内容：`battle_companion_procs.py`（C5 阶段）+ `protect` 技能映射。
- 数值：转移 = 把伤害从脆皮挪给坦克，属**生存乘区扩张** → 过数值门禁 + 峰值红线。

---

## G2 · 控制免疫查询点（`cc_immune` 写了没人读）

### 现状（已取证）

- 内容侧 `EFFECT_ACTIONS` 里 **有** `cc_immune` / `purify_immune` → 写 `effects["cc_immune"]`。
- 引擎里 `grep cc_immune` → **零命中**。控制落地处（`effects.act_apply` 的 `mode=skip`、
  状态条目）**不查任何免疫字段**。
- 受影响技能：`all_stat_cc`（永恒赞歌 98「全队全属性 +30% + 免疫控制」）、
  `stealth_cc`（影遁 85「强制潜行并免疫控制」）、以及"免控"类装备/料理。

### 建议改法

引擎在**控制类效果落地**处加一个查询点（不是新增机制，是把"读数据字段"补上）：

```python
# effects.py：控制条目（mode=skip / 已知控制族 key）写入前
if _is_control_entry(key, params):
    if (holder.get("effects") or {}).get("cc_immune"):
        logs.append(f"🛡️ 免疫控制：{...}")
        return
```

`_is_control_entry` 不写死名词表——**从 `EFFECT_RULES[key]` 的数据声明里读**
（新增可选字段 `control: True`，由内容侧在声明表标注），保持"引擎只查表、不认名词"。

### 影响面

- 引擎：`effects.py` 一处前置判断（约 8 行）+ 可选的 `EFFECT_RULES` 透传字段。
- 内容：`battle_rules.py` 给 stun/freeze/silence 三条声明加 `control: True`。
- 数值：免控会削弱控制类副本难度 → 过门禁。

---

## G3 · DOT 的 `dmg_kind` 透传（`period.dmg_type` 声明无效）

### 现状（已取证）

- `EFFECT_RULES["corros"].period.dmg_type = "true"`（注释「真伤 DOT」）——**无消费方**。
- 引擎 DOT 落地 `schedule.py:288`：`deal_damage(battle, None, a, dmg, logs)` —— **不传 `dmg_kind`**
  → 吃类型免伤/格挡（因为 kind 为空），**不是因为它是真伤**。

### 建议改法

`schedule.py` DOT 结算处把 `period["dmg_type"]` 映射成 `deal_damage(..., dmg_kind=...)`：

```python
_kind = {"true": "true", "phys": "phys", "magi": "magi", "physical": "phys",
         "magic": "magi"}.get(str(period.get("dmg_type", "")).lower(), "")
deal_damage(battle, None, a, dmg, logs, dmg_kind=_kind)
```

映射表放引擎（是**通道枚举**，不是游戏名词）；未声明 → `""` 保持现状（零行为变化）。

### 影响面

- 引擎：`schedule.py` 一处（约 6 行）+ 一个通道映射常量。
- 内容：无需改数据（`corros` 的 `dmg_type` 一填就真生效）；**但会让 corros 从"打不满"变成"打满"**
  → 数值变化，必须过门禁（预期：`corros` 打真伤后伤害上升）。

---

## G4 · （可选）随从可见性字段的引擎侧尊重

### 现状

引擎**不读** `untargetable` / `hidden`——这是**按设计**的（目标策略在内容侧
`target_picker` / 命令层仇恨选择器）。所以严格说**不是缺口**。

### 但有一个隐患

敌方 AOE 的"目标 side 全体结算"若走引擎默认（`sides` 全体），会打到 `untargetable` 的随从
（旧引擎有 `_side_aoe_pool` + `eats_aoe` 语义：只有吃 AOE 的随从进池）。
→ **建议**：AOE 目标池查询点同样走内容侧回调（复用 G1 的 `target_picker` 家族），
或引擎在 AOE 结算处跳过显式 `untargetable=True and not eats_aoe` 的 actor
（两行，读字段不算游戏知识）。**待拍板**：保持内容侧实现（更纯）还是引擎兜底（更稳）。

---

## 附：不在这 4 项里的（已定案，无需引擎）

| 项 | 定案 |
|---|---|
| 引擎里的内容词汇（`kinds` 中文值 / `role=="boss"` / `sides["player"]` / 固定效果键） | 见框架仓 `docs/engine-vocabulary-contract.md`——**定为公开契约**，可注入列为 v0.2 backlog |
| `gauge.charge_*` | 已删（职业机制残留、零消费） |
| `Battle.dmg_mult/pet/st`、`_cast_ctx`、`_events`、`DEFAULT_CT_WAIT`、`schedule.CAST_ITEM/HOT_INTERVAL` | 已删（零消费，2026-09-11） |
| 世界 Boss GM 伤害倍率 | ✅ 已于 2026-09-11 用 `taken_calc` 承伤乘区接回（零引擎改动），测试 13/13 |
| `support`/`formation`/`expr` 里零消费的公开函数（`reachable_units`/`expr_or`/`stat_scale_of`/`next_ct`/`set_hook`） | **保留**：属引擎**公开 API 面**（`next_ct`/`stat_scale_of` 已被游戏侧测试当便捷工具使用），在 wiki 的 API 页登记为公开契约，不按死代码删 |
