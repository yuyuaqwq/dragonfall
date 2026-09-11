# v181 随从/召唤线实施方案（2026-09-11）

> **状态：待拍板**（字段级方案；本文把 roadmap 附表里散落的 5 个"召唤类缺口"收敛成**一件事**）
> **结论先说**：随从线**不需要改引擎**——`Battle.add_actor` 已经是齐备的注册入口，
> 缺的是**内容侧的随从 actor 工厂**（属性缩放 / 守卫 / 上限 / 生命周期）。

---

## 一、缺口收敛（5 处 → 1 个工厂）

| 来源 | 现状（已取证） |
|---|---|
| roadmap 附2「召唤 4」 | `death_contract` / `undead_faith` / `skeleton_cap` / `focus_regen_summon` 四条被动声明在表、装配通道在 `passive_procs.py`，但**都要求"场上有随从 / 骷髅"**——场上永远没有随从，所以恒不触发 |
| **世界 Boss 宠物参战** | `combat.py` 曾 `Battle(..., pet=db.pet_get(qq))`——**引擎只存不读**（同一行 bug 见 2026-09-11 修复说明），宠物从未参战；现已去掉该静默传参 |
| 药水召唤 | `potion_effects.eff_summon`（烬灵香炉 / 圣徽替身像 / 荆棘傀儡种 / 战地医者魔偶）**显式拒绝**，属"战斗内效果未迁移" |
| 技能召唤 | `game/data/summons.py::SUMMONS` 模板齐备（骷髅兵 / 藤蔓守卫 / 古树守卫…），**无生成方** |
| 挡刀（`bodyguard` / `absorb_once` / `protect` 技能） | 数据字段齐备（`bodyguard: 0.40`、`absorb_once: True`、`eats_aoe: True`），**无消费方** |

一件事：**`make_companion_actor()` 内容工厂 + `companions` 生命周期管理**。

---

## 二、北极星铁律（鱼鱼已拍板，勿违）

> 宠物/召唤物都是 **companions actor 字段驱动**（`side` / `kind` / `buffs` / `hidden` /
> `untargetable`），**引擎不写专用路径**。

引擎现状核对（2026-09-11）：

| 引擎能力 | 状态 |
|---|---|
| `Battle.add_actor(actor, side, front=False)` | ✅ 注册 + 建 `_skill_index` + 播种 ct；`front=True` 插队首（存活序列第一名 = 默认目标先打它，正是挡刀位） |
| `sides` 动态遍历 | ✅ 调度（`schedule.py`）与存档（`serialize.py`）都动态遍历 → 新 actor 自动纳入行动与存档 |
| 引擎读 `kind` 的唯一处 | `kind == "player"`（找命令层焦点）——**不认识"随从/召唤"** ✅ 无专用路径 |
| 引擎读 `untargetable` / `hidden` | **零处** → 目标策略在内容侧（`target_picker` 注入点 / 命令层仇恨选择器），随从不被选为目标由**内容侧尊重字段**实现 ✅ |
| 召唤物技能索引 | ✅ `add_actor` 已建（对比坑：`boss_script` 早期手搓 `sides.insert` 导致援军技能全退化普攻） |

---

## 三、随从 actor 工厂（内容侧，新增 `game/services/battle_companion_procs.py`）

### 3.1 生成

```python
def make_companion_actor(battle, owner: dict, tmpl_key: str, *,
                         source: str = "skill") -> dict | None:
    """从 SUMMONS[tmpl_key] 造随从 actor 并注册进 owner 同侧。

    规则（全部来自数据字段，零职业名硬编码）：
    - 属性缩放：atk = owner_atk × atk_ratio（hp/def 同款；owner 属性取 stats 聚合面板）
    - side = owner 所在 side；kind = "companion"；uid = f"cmp_{owner_uid}_{i}"
    - rank/reach 取模板（前排挡刀型 rank=1）
    - bodyguard / absorb_once / eats_aoe / dmg_type / limit 原样挂 actor 字段（内容侧消费）
    - untargetable：模板未标 bodyguard 的纯输出召唤 → True（不被敌方目标策略选中）
    - auto_act：{act:{type:"attack", element:dmg_type}}（随从自动普攻；有技能则走技能）
    - 注册：battle.add_actor(actor, side=owner_side, front=(rank==1))
    返回 actor；超上限/无模板/owner 死亡 → None。
    """
```

### 3.2 上限与生命周期

| 项 | 规则 | 落点 |
|---|---|---|
| 同模板上限 | `SUMMONS[k].limit`，`skeleton_cap` 被动放宽为 `min(cap, base+add)` | 生成前计数 `sides[side]` 里同 `tmpl_key` 的 actor |
| 跨模板总上限 | 建议 5（防铺场）；具体数值待拍板 | 同上 |
| 主人死亡 | 同侧随从全部清理（`death_contract` 的"牺牲骷髅复活"正是此语义的反向） | 挂 `on_death` 触发器（引擎事件已有）：主人死 → 移除随从 |
| 战斗结束 | `sides` 随存档丢弃，无需额外清理 | 引擎动态序列化 |
| 挡刀消耗 | `absorb_once=True` 的随从替目标吃下 1 次单体伤害后**自我移除** | 见 §五 |

---

## 四、四条被动的接线（工厂落地后逐个接）

| 被动 | 技能 | 数据 | 判定所需 | 工厂落地后怎么接 |
|---|---|---|---|---|
| `skeleton_cap` | 骷髅海 lv? | `{"cap":5,"add":2}` | 生成时读上限 | 工厂内读 owner 的 `_learned_proc("skeleton_cap")` → 上限 +add |
| `focus_regen_summon` | 森之共鸣 | `{"gain":5}` | "召唤物在场" | 已实装（`passive_procs._tick_regen`），随从出现即自然生效，**零改动** |
| `undead_faith` | 亡灵信仰 | `{"per_undead":0.15}` | "亡灵在场"计数 | 已实装（`tick_faith`），亡灵 = 带 `undead` 标记的随从 → 工厂给模板加 `undead: True` 标记 |
| `death_contract` | 死亡契约 | `{"faith_req":5,"hp_pct":0.20}` | "存活骷髅在场" | 已实装（`passive_procs` 1162 行）；同样只需工厂产出**带 `skeleton` 标记**的随从 |

⇒ **四条被动里三条是"已实装、只缺随从"**：工厂一落地就自动接通。这是本线性价比最高的地方。

---

## 五、挡刀（`bodyguard` / `absorb_once` / `protect` 技能 / 世界 Boss 宠物）

三种"挡刀"其实是同一个机制：**一次承伤被转移到另一个 actor 身上**。

| 场景 | 触发条件 | 转移对象 |
|---|---|---|
| 随从 `bodyguard: 0.40` | 敌方单体攻击己方 actor 时按概率 | 该随从 |
| 随从 `absorb_once: True` | 必定（概率 1.0），且吸收后消失 | 该随从 |
| `protect` 技能（誓约之盾 85 / 守护誓言 90） | 队友被单体攻击时 | 施法者（并反伤 30%/50%） |

**实现选项（需拍板）**：

- **A. 内容侧零引擎改动**：给被保护者挂 `taken_calc` 触发器 → 命中时把 `ctx["mult"]` 压到 ~0
  并对保护者调 `landing.deal_damage(...)` 转移伤害。
  ✅ 不动引擎；❌ 有取整损耗（`max(1, int(dmg*mult))` 至少留 1 点）、要在触发器里做递归保护。
- **B. 引擎加「承伤转移钩子」**（推荐，约 15 行）：在 `landing.deal_damage` 的护盾段**之前**
  加一个查询点：`target` 上有 `guard_refs`（保护者 uid 列表）→ 按内容侧声明的规则转移承伤对象。
  引擎零游戏知识（只读字段 + 调内容侧回调），语义与"护盾先挡"同层，属**战斗物理规则**，
  天然该收口在 `landing`（对齐"伤害落地统一收口"的既有架构原则）。
  ✅ 语义干净、无取整损耗；❌ 需引擎 diff（本方案单独出）。

> 与 `faith_share`（治疗伤害分担）是**同一个钩子的两种用法**：都是"把落地对象换掉"。
> 建议**一次把两个一起做**（钩子做通用，faith_share 只是把"伤害"换成"治疗"）。

---

## 六、阶段划分

| 阶段 | 内容 | 量级 | 依赖 |
|---|---|---|---|
| C1 | `battle_companion_procs.py` 工厂 + 上限/生命周期 + `tests/test_v181_companion.py` | M | — |
| C2 | 四条被动接线验证（3 条自动生效 + `skeleton_cap` 一行） | S | C1 |
| C3 | 世界 Boss 宠物参战（`pet_get` → 工厂；宠物技能按 `PET_SKILL_UNLOCK_LV`） | S | C1 |
| C4 | 药水召唤复活（`eff_summon` 从"显式拒绝"改回装配） | S | C1 |
| C5 | 挡刀机制（方案 A 或 B，见 §五）+ `protect` 技能 + 随从 `bodyguard`/`absorb_once` | M | 拍板 |
| C6 | 数值校直（随从属性缩放倍率、上限、AOE 池）→ 必须过 `run_numeric_tests.py` + 峰值红线 | M | C1-C5 |

**验收口径**：每阶段跑全量（现在 250 文件基线）+ 数值门禁；
C6 必须建模（`scripts/numeric_lib`），禁止手调倍率。
