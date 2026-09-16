# battle2 统一效果容器设计方案（actor.effects + EFFECT_RULES）

> 2026-09-08。鱼鱼拍板「做干净」：消灭 state/buffs/hot/debuffs 多容器分裂，
> 统一成一个效果容器 + 一张规则表。触发：I1 用独立 actor["hot"] 实现 HOT 后，
> 鱼鱼质疑「DOT/HOT 本质同构、能否统一、state 是否不够通用」——深挖确认：
> 现状是 4 个效果容器（state/buffs/hot/debuffs）各带一半能力，分裂是历史演化
> 产物非第一性设计。本档给完整字段级方案 + 排期。
>
> 配套口令：「读 docs/archive/REFACTOR_v181P4_EFFECTS_UNIFY_design.md，从第 X 步开始」

---

## 0. 目标与范围

### 0.1 目标

1. **一个效果容器**：`actor["effects"][key] = 条目 dict`——替代 state/buffs/hot/debuffs 四键。
2. **一张规则表**：EFFECT_RULES[key] 声明全部行为（叠层/到期/周期方向/面板/消费/净化），
   引擎零硬编码、零名词。
3. **一套动词**：effects.py 动词收敛为 apply（挂/叠/刷新）+ consume（扣/清/出手消费）。
4. **一个结算段**：schedule._settle_time_effects 统一处理 到期 + 周期跳（damage/heal/mana 方向）。
5. 为「hot 叠层」等未来需求留好：= 数据层一条声明，引擎零改动。

### 0.2 范围

- ✅ 统一：`actor["state"]`（29 key）、`actor["buffs"]`、`actor["hot"]`（I1 新做）、
  `actor["debuffs"]`（死键删除）
- ✅ 规则表合并：STATE_EFFECTS + EFFECT_ACTIONS（buff/control 段）+ CLEANSE_TAGS
  → 单表 EFFECT_RULES
- ⛔ 不并：`shields`（承伤资源，保留独立）、`cooldown`（调度资源）、
  `charging/defending/ct`（行动状态）、`triggers`（事件声明，不是效果存储）
  —— 理由见 §2.5
- ⛔ 事件型 regen（turn_start → heal，装配层）不动（事件语义≠墙钟周期，另行收口）

### 0.3 决策记录（鱼鱼拍板点）

| # | 决策 | 状态 |
|---|---|---|
| D1 | DOT/HOT 不各搞一套，统一周期结算段（方向字段分流） | ✅ 拍板 |
| D2 | 动态数值效果（食物 hot）不进 state int 层数 → 条目 value 内嵌 | ✅ 拍板方向 |
| D3 | state/buff 是否合并为一个 effects 容器 | 本文档给方案，待拍板 |
| D4 | shields/cooldown 保留独立 | 待拍板 |

---

## 1. 现状盘点（字段级，代码证据）

### 1.1 四个效果容器 + 规则表

| 容器 | 条目形态 | 生命周期 | 能力 | 缺失 |
|---|---|---|---|---|
| `state` | `int 层数`（29 key） | **无到期**（除 dot.turns hack） | 叠层/cap/stat_scale/debuff_scale/dot/threshold | 无到期、无动态数值、无消费语义 |
| `buffs` | `dict 快照`（~20 key） | expire 到期自动删 | 到期/stat 面板折算/hit 出手消费/mode 控制/纯状态 | 无叠层（同 key 刷新）、无周期跳 |
| `hot` | `dict {heal,mana,turns}` | 独立倒计时（I1） | 正向周期恢复 | 独立于一切、无叠层、动态数值 |
| `debuffs` | `dict`（播种） | — | 无（battle2 零消费=死键） | 整键删除 |

| 规则表 | 位置 | 内容 |
|---|---|---|
| STATE_EFFECTS | data/battle_rules.py | 29 key 的 cap/stat_scale/dot/debuff_scale/on/on_threshold/guard_hp_pct |
| EFFECT_ACTIONS | 同文件 | 名词效果→动词动作数组（buff_atk/control/stun/shield/heal/cleanse…） |
| CLEANSE_TAGS | 同文件 | 净化控制键清单 |

### 1.2 state 29 key 语义分布（data/battle_rules.py）

```
资源叠层（面板 stat_scale 折算）: zhan_yi(10层 atk+4%/层), rage(10 层 dmg+12%/层),
  chi, arcane, lian_duan(纯计数), shield(减伤 3%/层), time_staff(atk+1.5%/层),
  thunder_weave(spd+2%/atk+1%/层), wind_mark(spd+2%/层)
对敌标记（debuff_scale 承伤）: hunt_mark(承伤+8%/层 cap3), soul_mark(+6%/层 cap3)
DOT（dot 规则，伤害周期）: burn(3%/层), bleed, poison(2%/层), corros(真伤2%/层),
  blaze/ember(1.5%×3跳), blood_trace(当前血2%×4跳), affix_bleed(5%×3跳 cap3)
减伤叠层（stat_scale 负值）: randuin_weary(敌速-6%/层), ice_vein(-8%/层)
消费型: heal_down(禁疗×10%/层 cap5), death_guard(濒死保命 cap1)
放大器（hit/dmg_calc 消费）: rune_amp(5 层), eternal_codex(8 层不清), sage_amp(2 层)
```

### 1.3 buffs 语义分布（effects.py act_buff/act_control + actions.py 消费）

```
属性增益:  {expire, stat, op:mul/add/reduce, mult}        —— stats._apply_buffs 折算
控制:      {expire, mode:skip|no_skill}                    —— battle.act 行动前消费
出手消费:  {expire, hit:{dmg_mult|guaranteed_crit|bonus_atk_pct}} —— actions._consume_hit_buffs
纯状态:    {expire}（cc_immune 免疫）
value 型:  {expire, v}（reduce 减伤）
sleep 唤醒: landing.deal_damage pop sleep
```

### 1.4 写入方（谁在写这些容器）

| 写入方 | 写法 | 例 |
|---|---|---|
| effects.py 动词 | act_buff/act_control/act_state_add/spend/set | EFFECT_ACTIONS 翻译后执行 |
| 技能 mech | effects_from_skill → state_add | 技能 mech_key 命中 STATE_EFFECTS → state_add |
| 装配层 triggers | apply_effects 执行 | affix/武器特效翻译器 |
| 事件火 | fire → apply_effects | dot_tick/on_act_consume 消费 |
| 命令层 | actor 直写 | battle_item_use（I2 翻译器）、bridge 恢复 |
| schedule | 只读结算 | DOT/hot/buffs 到期 |

### 1.5 消费点（谁在读）

| 文件 | 读什么 | 用途 |
|---|---|---|
| stats.py `_apply_buffs` | buffs 条目的 stat/op/mult | 面板折算 |
| stats.py `_apply_state_scale` | state 值 × 表 stat_scale | 每层面板折算 |
| schedule.py | buffs expire / state dot 规则 | 到期删 / 周期跳 |
| battle.py act() | buffs mode=skip/no_skill | 控制消费 |
| actions.py `_consume_hit_buffs` | buffs hit 子键 | 出手消费 |
| landing.py | shields / buffs.sleep / state death_guard/heal_down | 承伤/苏醒/濒死/禁疗 |
| effects.py act_cleanse | state dot/on=target + buffs 控制键 | 净化 |
| serialize.py | 全 actor dict | 落盘（全字段透传，无需特判） |

---

## 2. 目标架构

### 2.1 总览

```
写：名词效果 → EFFECT_RULES 查翻译 → 动词 apply() → actor["effects"][key] = 条目
读：stats 面板折算 / schedule 结算 / actions 消费 / landing 修正 —— 全读 actor["effects"]
表：EFFECT_RULES[key] 声明 cap/on/panel/period/consume/cleanse/tag/threshold/guard…
```

### 2.2 容器条目形态（字段级）

```python
actor["effects"][key] = {
    # ── 核心（引擎读）──
    "stacks": int,        # 叠层数。缺省 1。资源/标记/DOT 用；增益=1
    "expire": float|None, # 到期绝对时刻；None=常驻（纯计数/资源）；到期由 schedule 删除
    # ── 数值（两种来源互斥二选一）──
    # A. 表驱动静态：不存 value，数值查 EFFECT_RULES[key]（burn/rage/atk_up 固定）
    # B. 快照内嵌动态：存 value，覆盖表缺省（食物 hot pct 每件不同 / 药水 effect_data）
    "value": dict|None,   # 可选。动态数值：{"heal":0.06,"mana":0.08} / {"pct":0.5} / …
    # ── 运行时辅助（schedule/消费点自管，可缺省）──
    "last_tick": float,   # 周期效果上一跳时刻（period 用；首挂=now）
    "hits_left": int,     # 受击消费剩余次数（防御类 buff 用，旧 buff_hits 语义）
}
```

字段默认/语义表：

| 字段 | 类型 | 缺省 | 语义 | 谁写 | 谁读 |
|---|---|---|---|---|---|
| stacks | int | 1 | 叠层数；cap 查表 | apply/consume | stats 折算×、schedule 周期×、阈值 |
| expire | float/None | None | 到期绝对时刻 | apply | schedule 到期删 |
| value | dict/None | None | 动态数值覆盖表 | apply（上层带） | stats/schedule/消费点读 value 补表 |
| last_tick | float | =挂载时刻 | 周期跳游标 | schedule | schedule |
| hits_left | int | 表 turns 或 3 | 受击消费剩余 | apply/schedule | landing 受击递减 |

**key 命名统一**：合并后 effects 键空间唯一——同一效果只有一名。
现状 state 与 buffs 键基本不重叠（已核对）；合并后消灭「同语义 half 在 state half 在 buffs」。
> ⚠️ 冲突点：state 表有 "shield"（减伤叠层），与独立 shields 容器 key 命名撞——
> 保留 shields 独立（§2.5），effects 内减伤层改名 `reduce` 或加前缀，见 §4 映射。

### 2.3 EFFECT_RULES 表字段（字段级，合并 STATE_EFFECTS+EFFECT_ACTIONS 行为段）

```python
EFFECT_RULES[key] = {
    # ── 叠层/作用 ──
    "cap": 1,                    # 叠层上限（缺省 1 = 非叠层）
    "on": "caster"|"target",     # 挂自己还是挂目标（affix/skill 施加时决定落点）
    # ── 面板折算（每层或整体）──
    "panel": {"stat": "atk", "op": "mul", "mult": 1.30},   # 静态整体增益（旧 buff_atk）
    "stat_scale": {"atk": 0.04}, # 每层折算（旧 state 资源）
    "debuff_scale": {"dmg_taken": 0.08},  # 每层承伤加成（对敌标记）
    # ── 周期结算（统一 DOT+HOT，方向字段分流）──
    "period": {
        "dir": "damage"|"heal"|"mana",   # 方向
        "interval": 1.0,                 # 跳间隔（秒）
        "pct_max_hp": 0.03,              # damage：每层每跳 max_hp%
        "pct_cur_hp": 0.0,               # damage：每层每跳当前 hp%（败血）
        "heal_pct": 0.0,                 # heal：每跳 max_hp%（value 覆盖）
        "mana_pct": 0.0,                 # mana：每跳 max_mp%（value 覆盖）
        "turns": 0,                      # 限跳数（0=无限直到清层/到期）
        "pct_boss": 0.0,                 # damage：boss 档（旧 pct_boss 语义）
        "pct_cur_boss": 0.0,
    },
    # ── 消费语义 ──
    "consume": {"mode": "skip"}        # 控制：行动整跳+清（stun/freeze/sleep）
             | {"mode": "no_skill"}    # 控制：技能转普攻（silence）
             | {"hit": {...}}          # 出手消费（next_atk_up 等；消费后清）
             | {"on_taken": {"hits": N}} # 受击计数减伤/格挡（旧防御 buff）
             | None,                   # 不消费
    # ── 控制标签 / 净化 / 状态标记 ──
    "tag": "stun",               # 控制标签（consume.mode 存在时用）
    "cleanse": True,             # 可被净化（表声明，替代 CLEANSE_TAGS 硬清单）
    "negative": True,            # 减益标记（on=target 天然 negative 可缺省推导）
    # ── 阈值 / 特殊 ──
    "threshold": {10: {"form": "fury"}},   # 满层触发（旧 zhan_yi on_threshold）
    "guard": {"guard_hp_pct": 0.10, "heal_pct": 0.10},  # 濒死保命（death_guard）
    "heal_down": True,           # 禁疗标记（landing.heal_actor 读）
}
```

### 2.4 动词收敛

| 现状动词 | 目标 |
|---|---|
| act_buff | `apply(battle, holder, key, stacks=1, expire_at=?, value=None)` —— 写 effects 条目 |
| act_control | apply 同 buff（表 consume.mode + tag）—— 特殊：boss 减半保留 |
| act_state_add | apply stacks += amount（cap 查表） |
| act_state_spend | consume stacks -= amount |
| act_state_set | apply stacks = amount（覆盖/刷新；食物"取高"用 max 语义） |
| act_shield | 保留独立容器动词 |
| act_cleanse | 遍历 effects，清 表 negative/cleanse=True 或 on=target 条目 |
| act_heal/damage | 不变（landing 薄包装） |

引擎内新 helper（actors.py 或 effects.py）：
- `effect_get(actor, key) -> int stacks`
- `effect_add(actor, key, amount, expire=None, value=None)`（查表 cap）
- `effect_spend(actor, key, amount)`
- `effect_apply(actor, key, stacks, turns=None, value=None)`（刷新：expire=max、stacks 取 max 或加——语义由参数）
- `effect_remove(actor, key)`

### 2.5 保留独立的容器（理由）

| 容器 | 为什么保留 |
|---|---|
| `shields` | 承伤资源（量值不是效果），landing 承伤链专用；独立 `{value, expire_at, halve}` + 同源叠厚，无 stat_scale/period/consume 需求 |
| `cooldown` | 调度资源（技能下次可用时刻），与效果无关 |
| `charging/defending/ct` | 行动状态（读条/姿态/时间轴），非效果 |
| `triggers` | 事件声明表（何时触发），效果内容最终落 effects——职责正交 |
| `hot` | **删除**（并入 effects：key=`regen_hot`，表 period dir=heal + value 动态） |
| `debuffs` | **删除**（battle2 零消费死键） |

---

## 3. 迁移映射表（29 state key + buffs + hot + debuffs）

### 3.1 state 29 key → EFFECT_RULES

| 现 key | 目标 key | cap | 行为声明 | 备注 |
|---|---|---|---|---|
| zhan_yi | zhan_yi | 10 | stat_scale atk+0.04 + threshold {10:fury} | 资源层 |
| rage | rage | 10 | stat_scale dmg_mult+0.12 | |
| chi | chi | 10 | 纯计数 | |
| arcane | arcane | 10 | 纯计数 | |
| lian_duan | lian_duan | 10 | 纯计数 | |
| shield（减伤层） | reduce_stack | 10 | stat_scale reduce+0.03 | ⚠️ 改名避撞 shields 容器 |
| hunt_mark | hunt_mark | 3 | debuff_scale dmg_taken+0.08 + negative | on=target |
| soul_mark | soul_mark | 3 | debuff_scale +0.06 + negative | |
| burn | burn | 5 | period dir=damage pct_max_hp 0.03 + negative | |
| bleed | bleed | 10 | period dir=damage type=flat | |
| poison | poison | 5 | period dir=damage 0.02 | |
| corros | corros | 5 | period dir=damage 0.02 true | |
| fire_mark/ice_mark/thunder_mark | 同 | 5 | 纯计数（元素印记） | |
| wind_mark | wind_mark | 4 | stat_scale spd+0.02 | |
| blaze | blaze | 3 | period damage 0.015 turns3 | |
| ember | ember | 3 | period damage 0.015 turns3 | |
| blood_trace | blood_trace | 1 | period damage pct_cur 0.02 turns4 | |
| affix_bleed | affix_bleed | 3 | period damage 0.05 turns3 | |
| heal_down | heal_down | 5 | heal_down:True + negative | landing 读 |
| death_guard | death_guard | 1 | guard{...} | landing 读 |
| rune_amp | rune_amp | 5 | 纯计数（dmg_calc 消费） | |
| eternal_codex | eternal_codex | 8 | 纯计数 | |
| sage_amp | sage_amp | 2 | 纯计数 | |
| time_staff | time_staff | 10 | stat_scale atk+0.015 | |
| thunder_weave | thunder_weave | 5 | stat_scale spd+0.02 atk+0.01 | |
| randuin_weary | randuin_weary | 3 | stat_scale spd-0.06 | |
| ice_vein | ice_vein | 3 | stat_scale spd-0.08 | |

> 迁移要点：state 值（int）→ 条目 `{"stacks": N}`；无 expire（资源常驻 None）；
> DOT 类加 `period`；无到期需求的纯计数保留 None expire。

### 3.2 buffs → EFFECT_RULES

| 现语义 | 目标 key | 行为声明 | 条目示例 |
|---|---|---|---|
| 属性增益 atk_up | atk_up | cap1 panel{atk,mul,1.30} | {stacks:1, expire} |
| 食物增益 food_atk_up | food_atk_up | cap1 panel{atk,mul,1.10} | {stacks:1, expire} |
| 减伤 reduce | reduce | cap1 panel{reduce} | {stacks:1, expire, value:{v:0.45}} |
| 控制 stun | stun | cap1 consume{mode:skip} tag:stun negative | {stacks:1, expire} |
| 沉默 silence | silence | cap1 consume{mode:no_skill} tag negative | |
| 免疫 cc_immune | cc_immune | cap1 纯状态 | |
| 出手消费 next_atk_up | next_atk_up | cap1 consume{hit:{dmg_mult:1.5}} | {stacks:1, expire} |
| 必暴 stealth | stealth | consume{hit:{guaranteed_crit}} | |
| value 型 heal_up | heal_up | cap1 纯状态（装配层批读） | {value:{pct}} |
| 防御受击 buff | dodge_pot 等 | cap1 consume{on_taken:{hits:3}} + panel | {hits_left:3} |

### 3.3 hot / debuffs

| 现 | 目标 |
|---|---|
| actor["hot"] | key=`regen_hot`：EFFECT_RULES cap1, period{dir:heal+mana, interval:1.0}；条目 {stacks:1, expire: now+turns×interval, value:{heal:0.06, mana:0.08}}（动态数值走 value） |
| actor["debuffs"] | 删除（零消费） |

### 3.4 EFFECT_ACTIONS 收敛

EFFECT_ACTIONS 名词表保留（名词→动词动作），但动作类型从 act_buff/act_state_add
等收成 apply/control 少数几个 + 字段对齐 EFFECT_RULES key：
```python
# 旧: "buff_atk": [{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.30}]
# 新: "buff_atk": [{"action": "apply", "key": "atk_up"}]        # 数值查 EFFECT_RULES[key].panel
```
动态数值名词（药水 effect_data）由调用方 value 参数传入（apply 内嵌）。

---

## 4. 引擎文件改动清单（字段级）

| 文件 | 改动 |
|---|---|
| `game/battle2/actors.py` | make_actor 播种：删 buffs/debuffs/hot/state 四键 → 单键 `"effects": {}`；helper 族 effect_get/add/spend/apply/remove 替代 state_of/state_add/state_spend/buffs 助手 |
| `game/battle2/effects.py` | 动词重构：register "apply"（原 act_buff+act_state_add/set 语义合流）、"control" 内部改 apply+consume、cleanse 遍历 effects；删 act_state_add/spend/set 独立实现改薄壳调 apply/consume；act_shield 不变 |
| `game/battle2/stats.py` | `_apply_buffs`+`_apply_state_scale` 合并成 `_apply_effects`：遍历 effects，读表 panel/stat_scale/debuff_scale + 条目 stacks/value 折算 |
| `game/battle2/schedule.py` | 到期段：buffs expire + hot 容器 → 统一遍历 effects（expire<=now 删）；周期段：DOT（state 表 dot）+ hot → 统一查 EFFECT_RULES period（dir 分流 damage→deal_damage / heal→heal_actor / mana→mp）；删 I1 hot 段 |
| `game/battle2/landing.py` | heal_down/death_guard/sleep 读点改读 effects；shields 承伤不变；禁疗读 effects.heal_down stacks |
| `game/battle2/battle.py` | 控制消费改读 effects（consume.mode）；sleep 唤醒在 landing 已改 |
| `game/battle2/actions.py` | `_consume_hit_buffs` 改读 effects consume.hit；effect 增益管线对齐 |
| `game/battle2/serialize.py` | 无特判（全字段透传）；_deserialize setdefault effects |
| `game/battle2/effect_triggers.py` | fire 不变（效果名照旧翻译）；事件 dot_tick/buff_expire 改名为 effect_tick/effect_expire 事件（或兼容双名） |
| `game/data/battle_rules.py` | STATE_EFFECTS+EFFECT_ACTIONS+CLEANSE_TAGS 合并为 EFFECT_RULES（迁移映射 §3）；config 挂载点改 |
| `game/battle2/config.py` | 挂载 EFFECT_RULES 替代 state_effects/effect_actions/cleanse_tags 三挂载 |
| `game/services/battle_bridge.py` | player/怪状态键映射改 effects（buffs/hot/state 三键→effects 组装） |
| `game/commands/battle_item_use.py` | hot: 分支改 apply regen_hot；buff: 分支 apply atk_up 等（value 直传） |
| `game/commands/instance_battle.py` | _VIEW_SNAP_KEYS/_VIEW_ST_KEYS 改 effects；sync_views 适配 |
| `tests/*` | v1252/n9_equip/n3_effects/n4_schedule/n5b4* 断言改 effects 读法 + 新增统一回归 |

---

## 5. 分阶段实施 + 验证（每阶段 commit，全绿再下一阶段）

| 阶段 | 内容 | 验证 | 预估 |
|---|---|---|---|
| V1 | 引擎容器切换：actors.py 播种 effects + helper；serialize/config 挂载 EFFECT_RULES | 全套现有测试改读后绿（断言大量同步） | 4h |
| V2 | stats 折算合并（_apply_effects）+ landing/heal_down/death_guard/sleep 读点迁移 | 面板数值回归 v1252 对齐 | 3h |
| V3 | schedule 统一结算：到期 + 周期（period dir 分流）；删 hot 段 | test_battle_hot_regen 重写绿 + DOT 行为不变 | 3h |
| V4 | effects.py 动词重构（apply/control/consume/cleanse）+ actions 消费对齐 | n3_effects/n9_equip 断言绿 | 4h |
| V5 | 数据表迁移：29 state key + buffs + hot + EFFECT_ACTIONS → EFFECT_RULES | 数值/行为对比测试 | 4h |
| V6 | 命令层/桥/视图适配（battle_item_use/instance_battle/bridge sync） | 道具链端到端（I 系列测试）+ cmdflow 绿 | 3h |
| V7 | 全套回归（battle2 21+ 文件 + run_all）+ HANDOFF + 文档同步 + diff 给鱼鱼 | 全绿 + 行为对比 | 2h |

**总计约 23h 主 agent 专注工作量**（≈2.5-3 个工作日，可分派子 agent 并行 V2/V4/V5）。

### 依赖/并行
- V1 是地基（全串行前置）
- V2(stats) / V4(verbs) 改不同文件可并行
- V3(schedule) 依赖 V1；V5(数据表) 依赖 V2+V3 读法定型
- V6 命令层最后（依赖 V2-V5）
- 铁律：每阶段 git 干净先 commit；行为零变化验证；机械迁移多断言同步

---

## 6. 回归策略

1. 现有 battle2 21 文件 + v1252/n9_equip 高断言文件为首要回归对象（读法同步不丢断言）。
2. 新增统一回归文件 `tests/test_battle_effects_unify.py`：
   - 同一效果的 state 式 / buffs 式声明产物等价（叠层+到期+面板）
   - hot=DOT 镜像（同 period 不同 dir，数值符号相反）
   - 动态数值 value 覆盖表缺省
   - 净化/到期/消费/序列化 roundtrip
3. run_all_tests.py 全量对照基线（沙盒非 git 红名单不变）。
4. 数值对拍：旧引擎 vs battle2（V5 后主要技能/词条面板值抽查）。

---

## 7. 风险与对策

| 风险 | 对策 |
|---|---|
| 29 key + buffs 数据迁移漏写 | 迁移映射表逐 key 核对 + 编译期扫描残留 state_of/actor_buffs 引用（grep 清零） |
| 断言大面积同步丢覆盖 | 只改读法不改语义；断言数字保留，必要时加对拍测试 |
| clean/consume 语义边界模糊（纯计数/受击/出手） | EFFECT_RULES 表 consume/negative/cleanse 显式声明，缺省不消费不清 |
| 事件名 dot_tick/buff_expire 漂移 | 事件改 effect_tick/effect_expire 或兼容双名一期（文档注明）；装配层监听同步改 |
| 序列化老档 state/buffs 键残留 | from_state 迁移函数：旧键 → effects 组装（一次性，沙盒跑老档 fixture） |

---

## 8. 本批之后（缺口/后续）

- 事件型 regen（turn_start heal）→ 若要求墙钟制，平移成 EFFECT_RULES period dir=heal（引擎已支持）。
- shields/cooldown 是否最终并入 effects（保留独立派/并入派论证留给 P 系列）。
- effect_actions.py（P2G 主仓线的动作库）与 EFFECT_RULES 的关系（旧引擎线不冲突，文档注明）。

---

## 9. 开工口令

「继续 effects 统一，读 docs/archive/REFACTOR_v181P4_EFFECTS_UNIFY_design.md 从 V1 开始」
