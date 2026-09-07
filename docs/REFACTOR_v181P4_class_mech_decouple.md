# 职业机制与引擎解耦方案（battle2 北极星架构落地）

> 2026-09-08 鱼鱼拍板：职业机制不应该依赖战斗系统；战斗系统提供足够通用的接口给职业，
> 而不是职业每次要做个东西都要动引擎。本文档把这条原则落成可执行设计。

## 1. 问题现状（旧引擎的病根）

旧 battle_mech.py 的 MECH_EFFECTS 有 65 个 handler，其中大量是**职业专属逻辑硬编码进引擎**：

| handler 示例 | 职业专属逻辑 | 问题 |
|---|---|---|
| `_m_zhan_yi_fury`（血祭） | 花 4 层战意强制进狂暴形态 | 战士形态逻辑写在引擎里 |
| `_m_faith_unload`（卸负） | 牧师信念资源扣 3 回血 15% | 牧师资源语义写引擎里 |
| `_m_sacrifice`（骸骨祭仪） | 献祭骷髅召唤物 | 召唤物计数逻辑写引擎里 |
| `_m_melody`（旋律） | 诗人驻留旋律状态机 | 整台状态机在引擎里 |
| `_m_guard_core_burst`（磐核爆发） | 拳师磐核资源 × 倍率 | 职业资源写引擎里 |

每次加新职业/新机制 = 往引擎里塞 handler = 引擎越滚越大、越不可维护。
**这正是 battle.py 11000+ 行的成因，battle2 不能再犯。**

## 2. 目标架构（三层分离）

```
┌─────────────────────────────────────────────┐
│  data 层（技能/装备/职业数据）                  │
│  技能 = 效果声明列表 effects: [{type, params}]  │
│  职业机制 = 效果声明的组合，不在代码里           │
├─────────────────────────────────────────────┤
│  battle 引擎 = 通用原语执行器                    │
│  只提供能力原语：damage/heal/buff/debuff/       │
│  stack/resource/shield/control/cleanse/       │
│  summon/transform/aura/...                    │
│  引擎不认识"战意""信念""旋律"，只认识             │
│  "资源 key 增减""叠层 key 增减""形态 key 切换"    │
├─────────────────────────────────────────────┤
│  数据驱动层（content/职业定义）                  │
│  「战士 = {资源: rage, 机制: {耗层换效果...}}」    │
└─────────────────────────────────────────────┘
```

### 关键原则（鱼鱼原话展开）

1. **引擎只有通用能力接口，不含职业语义**
   - 引擎认识：`给 actor X 叠 Y 层 Z`、`扣 actor X 资源 R 若干`、`把 actor X 形态切到 F`
   - 引擎不认识：`战意`、`信念`、`旋律`、`狂暴形态是战士的`
2. **职业要做什么 = 查数据声明，不是改引擎**
   - 技能数据声明「消耗 stacks.zhan_yi 4 层 → 切 dual_form 到 fury」
   - 引擎照着执行，职业加技能 = 加数据，不碰引擎
3. **机制注册表仍可扩展，但注册的是"原语组合器"不是"职业逻辑"**
   - 特殊结算规则（如"连击段数增伤"）可以注册为效果类型，但参数全来自数据

## 3. 引擎通用原语接口（battle2 对外能力面）

新引擎 effects.py 作为**原语解释器**，每个 effect type = 一个通用能力，**不绑定职业**：

### 3.1 状态类原语（已实现 ✓）

| 原语 | 签名 | 通用语义 |
|---|---|---|
| `add_stack` | (actor, key, n, cap) | 任意叠层 key 增减（不关心 key 是战意还是连段） |
| `spend_stack` | (actor, key, n) | 任意叠层消耗 |
| `add_resource` | (actor, key, n, cap) | 任意资源增减 |
| `spend_resource` | (actor, key, n) | 任意资源消耗 |
| `set_buff` | (actor, key, turns) | 任意 buff 刻数写入 |
| `set_debuff` | (target, key, {...}) | 任意 debuff 状态写入 |
| `add_shield` | (actor, value, halve) | 护盾 |
| `heal` | (target, amount) | 治疗落地（clamp） |
| `deal_damage` | (target, dmg) | 伤害落地（承伤链） |
| `cleanse` | (actor) | 净化减益 |
| `set_form` | (actor, form_key) | 形态切换（狂暴/影舞/...，key 由数据给） |
| `summon` | (owner, template) | 召唤物生成（模板由数据给） |

### 3.2 效果声明格式（技能数据 effects 字段）

```python
# 旧格式（职业语义在 mech key 里）→ 新格式（通用原语 + 数据参数）
# 旧: {"mech": "zhan_yi_fury", "mech_val": 4}   # 引擎要知道 zhan_yi_fury 是战士的什么
# 新: {"type": "spend_stack", "key": "zhan_yi", "amount": 4,
#      "then": {"type": "set_form", "form": "fury"}}   # 引擎照做，语义在数据
```

**关键**：`key`/`form`/`template` 等参数全由数据声明，引擎只执行通用动作。

## 4. mech 字段怎么处理（落地路径）

### 4.1 分类迁移

对现有技能数据 mech 字段做三分类：

| 类别 | 例子 | 处理 |
|---|---|---|
| A. 通用状态（引擎原语直接表达） | burn/bleed/poison/stun/silence/spd_down/hunt_mark/元素印记 | 保留 effect type，进 effects.py 原语表 ✓（已做） |
| B. 通用动作组合（原语可组合） | zhan_yi(叠层)/lian_duan(叠层)/rage(资源)/arcane(资源) | 数据化：mech → 通用 `add_stack/add_resource` 声明 |
| C. 职业专属机制（有职业语义/条件逻辑） | zhan_yi_fury(进狂暴)/faith_unload(信念卸负)/melody(状态机)/sacrifice(献祭骷髅)/bone_rush/guard_core_burst | **不迁进引擎**。由上层机制层（见 §5）实现，或数据化声明 |

### 4.2 迁移优先级

1. **A 类已迁**（burn/bleed/poison/stun/freeze/silence/slow/spd_down/sleep/hunt_mark/soul_mark/fire_mark/ice_mark/thunder_mark/zhan_yi/lian_duan/rage/chi/arcane）——这些本来就是通用状态，保留 ✓
2. B 类：确认 zhan_yi/lian_duan/rage/chi/arcane 叠层/资源原语化（已实现 add_stack/add_resource 语义，key 由数据给）✓
3. **C 类不迁**：从迁移清单移除，写进「职业机制层」待办（§5）

### 4.3 新增通用原语（补齐 C 类背后的能力）

C 类背后暴露的**通用能力缺口**，在引擎补通用原语（不补职业逻辑）：

| 缺口能力 | 通用原语 | 谁消费 |
|---|---|---|
| "花资源/叠层换治疗" | `spend_stack_then_heal`? → 不，用组合：`spend_stack` + `heal` 两个 effect | 战士冷静、牧师卸负 |
| "耗层进形态" | `set_form`（通用形态切换） | 战士血祭、刺客影舞 |
| "驻留光环" | `aura`（通用光环：挂 buff 到 side 全体，带持续） | 诗人旋律（但保留在职业数据层） |
| "引爆层数结算倍率" | `burst_mult`（读某 key 层数 → 本次伤害倍率） | 各类终结技 |
| "消耗召唤物计数" | `count_summons(template)` + `kill_summon` | 牧师骷髅系 |

这些通用原语注册进 effects.py 后，职业技能用**数据声明组合**它们，不再需要引擎理解职业。

## 5. 职业机制层（上层，非引擎）

旋律状态机、骷髅计数这类**多步跨行动的职业状态**，放上层 `game/content/class_mechs/` 或类似：
- 每个职业一个模块，注册自己的"机制钩子"（在引擎的通用事件点上挂）
- 引擎只发通用事件：`on_skill_cast` / `on_hit` / `on_turn_end` / `on_stack_change(key)`...
- 职业模块监听自己关心的事件，用引擎通用接口实现机制

```
事件总线（引擎发）              职业模块（上层收）
─────────────────              ──────────────────
on_skill_cast(skill, caster) → 诗人模块: melody_chant 叠强度
on_hit(target, dmg, caster)  → 刺客模块: 毒爆消费层数加伤
on_turn_end(actor)           → 战士模块: 连段断连清零
```

引擎保持零职业知识；加职业 = 新增上层模块 + 数据，引擎零改动。

## 6. actor 字段契约（引擎白名单 + 外部扩展区）

### 6.1 问题（旧引擎）

旧引擎 actor/玩家 dict 顶层被职业状态占满：`dual_form` / `v139_modes` / `_melody` /
`tailwind_prev_energy` / `stealth_atk` / `overflow_shield_cd` ... 每个字段都配一段引擎
消费代码 → 职业越多顶层越脏，字段语义互相踩踏。

### 6.2 契约

actor dict 分两片：

```
actor = {
  # ── 引擎白名单（引擎只消费这些；缺字段 = 无此行为）──
  # ① 身份/标签: uid/name/side/kind/human_controlled
  # ② 面板: hp/max_hp/mp/max_mp/atk/matk/def/mdef/spd/crit/...（公式 input）
  # ③ 通用状态容器: buffs/debuffs/stacks/resources/shields/cooldown/hot/
  #                 charging/defending/ct
  #   容器内部 key 由数据驱动（stacks["zhan_yi"] 只是数据，引擎不认识"战意"）
  # ④ 配置: class_name/level/equipment/skills/learned_skills/auto_act

  # ── 外部扩展区（引擎绝不读）──
  "ext": {
    # 职业机制层/外部插件自由读写，命名空间自己管
    # 例: 诗人模块存 {"melody": {...}}；战士模块存 {"fury_state": ...}
  },
}
```

### 6.3 规则

1. **引擎读字段 = 白名单内**；白名单外顶层字段引擎视为不存在（不主动读、不假设）。
2. **职业/机制自定义状态一律写 `actor["ext"]`**（惰性播种 dict），引擎逻辑零感知。
3. `ext` 可序列化（随 actor dict 落盘）；跨战斗持久需要时由职业模块自己管理。
4. 引擎提供通用访问器 `actor_ext(actor)`（惰性建 dict），不暴露其它 ext 知识。
5. 审计：引擎代码里搜不到职业字段名（dual_form/melody/faith/... 直接读 = 违规），
   一律经 ext 或数据驱动容器。

### 6.4 对比旧引擎

| 状态 | 旧引擎 | battle2 |
|---|---|---|
| 战士狂暴形态 | actor["dual_form"] + 引擎消费 | actor["ext"]["zhan_shi"]["dual_form"] + 职业模块 |
| 诗人旋律 | battle._melody + 引擎状态机 | actor["ext"]["shi_ren"]["melody"] + 诗人模块 |
| 牧师信念 | actor.resources["faith"]（引擎特判） | actor.resources["faith"]（数据驱动，引擎无特判） |
| 通用叠层 | 引擎按 key 特判 handler | stacks[key]（引擎只提供 add_stack/spend_stack） |

## 6.5 落地清单

- [ ] actors.py：make_actor 播种 `"ext": {}`（惰性扩展区）+ `actor_ext(actor)` helper
- [ ] 序列化：ext 随 actor 一起序列化/恢复
- [ ] 审计规则：引擎代码不出现职业字段直读

---

## 7. 落地清单（battle2）

- [x] effects.py：通用状态原语（A 类 + 通用叠层/资源）——N3a 已做
- [ ] effects.py：补通用原语 `set_form` / `aura` / `burst_mult` / `count_summons`（能力面补齐）
- [ ] effects.py：`effects_from_skill` 兼容层——mech key → 通用原语映射表（数据驱动，映射在 data 不在代码）
- [ ] 技能数据逐步迁 effects 列表（脚本化，把 mech 声明转成通用原语组合）
- [ ] 职业机制层框架（事件总线 + 职业模块注册）——N6 后或独立阶段
- [ ] 死表清理：旧 battle_mech 的 C 类 handler 不迁（旧引擎保留期间仍可跑，切换后删除）

## 7. 验收标准

1. effects.py 无任何职业名/职业资源名硬编码（搜 zhan_yi/faith/melody 等词在引擎 = 违规）
2. 任意职业加新技能（用现有原语组合）不需改引擎代码
3. 旧 battle_mech 的 C 类 handler 在 battle2 中不存在（零迁移）
4. 技能数据 effects 声明可完整解析执行（数据完整性断言）
