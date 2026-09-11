# N10-B7 food 战斗效果装配批（缺口补完）——设计文档

> 2026-09-09 格温推 N10-C 删旧前置侦察时发现：N9_migration §4 删除清单里
> "food_effects 相关（如并入）"写进了 N10，但 **battle2 覆盖从未排期**——B1-B6c
> 缺口批（吸血/defend/element/reflect/承伤/ct）都不含 food。这是漏网批。
>
> 状态：⬜ 待鱼鱼审。审过才动代码（工作流铁律：引擎/装配改动前先出字段级方案）。

## 1. 缺口实锤（battle2 food 战斗效果全线静默失效）

### 现状链路（battle2 已接管命令层，真实玩家路径）
```
战斗内吃效果料理（蛇羹/烬火辣椒/树蜜糖/月光饼/极光花蜜...）
  → item_templates tpl_food_effect（battle_ok=True）
  → payload="foodfx:lifesteal,bleed,..."
  → battle_item_use.translate foodfx 分支
  → actor["food_effects"].append(aid)   ← 只挂容器
  → "shield" in aids → 立即给盾（唯一生效的特判）
  → 🍲 你吃下了料理，获得【吸血、流血】效果！(本场战斗)   ← 文案照播
  → ❌ 之后 battle2 引擎/装配层无人读 actor["food_effects"]
```

### 旧引擎 6 个消费挂点（battle.py，N10 要删）
| 挂点 | 旧函数 | 时机 |
|---|---|---|
| `_th_affix_food_we` tick 卡 (509) | `_food_turn_start` | 每刻开始（回春/冥想/晨曦） |
| `_affix_dmg_mult` foods 分支 (5679) | — | 伤害乘区（处决 execute/精准 precise/龙语印记层） |
| `_skill_finalize` 命中尾 (6296) | `_food_on_hit` | 普攻/技能命中（吸血/流血/破甲/连击/火冰附加/贯穿/蓄力/静电/龙语叠层） |
| `_food_on_taken` (10516) | — | 受击（反击/反伤/极光庇护减伤） |
| `_regen_needed` (9073) | — | 挂回春 tick 卡判据 |
| `_ensure_regen_effects` (9221) | — | 同上 |

### 受影响食物效果（17 种，data/food_effect_data.py FOOD_EFFECT_PARAMS 全表）
- **HIT 命中类 10**：lifesteal 吸血8% / bleed 20%流血 / armor_break 25%破甲 /
  combo 15%追加50% / dragon_tongue 龙语叠层+2%/层 / element_fire 火附5% /
  element_ice 冰附5%+减速 / pierce 20%贯穿60% / charge 10%追加50% / static 静电减速
- **TAKEN 受击类 3**：counter 20%反击60% / thorns 10%反弹30% / aurora_guard 受击-15%
- **TURN_START 刻开始类 3**：regen 回1%血 / meditate 回1%蓝 / dawn_crown 回2%血
- **乘区类 2**：execute 处决<30%×1.3 / precise 精准×1.1
- **已生效 1**：shield 圣餐面包（battle_item_use 特判已做 ✅）

## 2. 方案：food → actor["triggers"] 装配（复用 affix 迁移先例）

battle2 装配层已具备全部能力（N9 装备特效/词条迁移），food 是"词条管线的漏网之鱼"：
- `services/battle_equip_proc.py` 有 affix 翻译注册器 `_register_affix`（regen/bleed/counter/execute 同语义词条已迁）
- `services/battle_we_procs.py` 有扩展动作注册中心（we_dot/we_reflect/we_extra_dmg/we_dmg_mult_cond/we_taken_mult_cond 等 20+）
- 事件映射表 `_EVENT_MAP`：hit→attack_hit+skill_hit / taken→on_taken / turn_start→turn_start / dmg_calc/taken_calc 直通

### 落点：battle_item_use.translate foodfx 分支扩展
吃料理时（不再只挂死容器），**同步把 aid 翻译成 actor["triggers"] 声明**：
```python
# battle_item_use.py translate foodfx 分支（改动点唯一，~40 行）
_actor_triggers = actor.setdefault("triggers", {})
for a in aids:
    _effs = _FOOD_TRIGGER_DECLS.get(a)      # 查表翻译（见 §3）
    if not _effs:
        continue                             # 未知 aid 静默（防拼写漂移）
    for ev, decls in _effs.items():
        for d in decls:
            _actor_triggers.setdefault(ev, []).append({**d, "_owner": actor})
# shield 特判保留；文案不变
```
- actor["food_effects"] 容器**保留**（图鉴/面板/存档兼容 + 吃重复去重判断仍读它）
- 触发时机由 battle2 事件总线 fire() 消费（skill_hit/on_taken/dmg_calc/taken_calc 引擎已插桩）
- **回春类特殊**：regen/meditate/dawn_crown 不进 triggers，吃入时直写 effects period
  条目（schedule 时间驱动每刻跳，同 regen_hot 先例）——见 §3 修正表
- 效果执行 = apply_effects 名词翻译 / we_* 扩展动作（引擎零知识不动）

### 为什么落 translate 而不是装配时
- food 是**战斗中动态吃**才挂（战斗外吃=即时回复 _food_out_battle，无战斗效果）
- 开战装配 make_actor 时玩家还没有本场 food（food_effects 是战斗内加餐）
- battle_item_use 是吃料理唯一入口（_instance_router + _restore_battle2 都走它）→ 单点扩展全覆盖

## 3. 翻译表（food aid → triggers 声明，数值全部读 FOOD_EFFECT_PARAMS 权威表）

### HIT 命中类（skill_hit 事件；旧 _food_on_hit 语义 = 普攻+技能命中都触发）
| aid | triggers 声明 | 对应 we/动词 | 复用的 affix 先例 |
|---|---|---|---|
| lifesteal | `skill_hit: [{type:"we_extra_dmg", heal_pct}]`（吸血即治疗） | we_extra_dmg | affix lifesteal（equip_proc §_af） |
| bleed | `skill_hit: [{type:"we_affix_dot", key:"bleed", chance:0.20, state_key:"food_bleed"}]` | we_affix_dot | affix bleed 同款 |
| armor_break | `skill_hit: [{type:"we_affix_defdown", ...}]` | we_affix_defdown | affix armor_break 同款 |
| combo | `skill_hit: [{type:"we_affix_bonus", pct:0.50}]` | we_affix_bonus | affix 追加伤害族 |
| charge | 同上（chance 0.10） | we_affix_bonus | — |
| dragon_tongue | `skill_hit: [{type:"we_stack_prod", key:"dragon_mark"}]` + dmg_calc 层数乘区 | we_stack_prod | affix 龙语印记 |
| element_fire | `skill_hit: [{type:"we_affix_element", elem:"fire", pct:0.05}]` | we_affix_element | affix element 同款 |
| element_ice | 同上 elem:"ice" + slow | we_affix_element | — |
| pierce | `skill_hit: [{type:"we_affix_bonus"/we_extra_dmg, ignore_def}]` | we_extra_dmg | affix pierce 族 |
| static | `skill_hit: [{type:"we_control", tag:"spd_down"}]` | we_control | affix slow 族 |

### TAKEN 受击类（on_taken 事件）
| aid | triggers 声明 | 复用先例 |
|---|---|---|
| counter | `on_taken: [{type:"we_affix_counter", chance:0.20, atk_pct:0.60}]` | affix counter 同款 |
| thorns | `on_taken: [{type:"we_reflect", chance:0.10, pct:0.30}]` | we_reflect（N10-B3 反伤） |
| aurora_guard | `taken_calc: [{type:"we_taken_mult_cond", cond:"always", mult:0.85}]` | affix 全减伤（equip_proc §_af reduce） |

### TURN_START 刻开始类 → ⚠️ 改为 effects period 时间驱动（非 turn_start！）
**修正（鱼鱼 2026-09-09 追问）**：效果料理描述 =「每刻回复 X%」——旧引擎实现是 tick 卡
（ACT_TICK=1 刻=1 游戏秒，interval=1s **时间驱动**，keep=True 常驻到战斗结束），
**不是行动帧触发**。battle2 同构通道 = effects 条目 + period 声明（schedule 周期段
时间驱动，dir=heal 已支持 heal_pct + mana_pct 双资源，见 hot: 分支 regen_hot 先例）。
因此 regen/meditate/dawn_crown **不走 turn_start 事件、不进 triggers**，吃入时直接写
effects period 条目（首跳 1s + 每 1 刻跳 + 战斗全程常驻）：

| aid | 落点 | 条目形态（schedule 周期段消费） |
|---|---|---|
| regen | `effects["food_regen"]` | `{stacks:1, period:{dir:"heal", interval:1.0, heal_pct:0.01}, expire:战斗结束}` |
| meditate | `effects["food_meditate"]` | `{stacks:1, period:{dir:"heal", interval:1.0, mana_pct:0.01}, expire:...}` |
| dawn_crown | `effects["food_dawn_crown"]` | `{stacks:1, period:{dir:"heal", interval:1.0, heal_pct:0.02}, expire:...}` |

- 对齐 battle2 hot: 分支 regen_hot 写法（`entry["period"] = {...}`，schedule 周期段消费）
- **无 turns**：旧效果料理回春战斗全程常驻（keep=True），不是普通食物 hot 的 N 刻限时
  → 条目不设 djump turns 清层（turns 缺省 0 = 不按跳数清）；expire 由战斗结束 actor
  销毁自然消失（regen_hot 用 expire 兜底，food 全程型可留 expire=None 依赖 actor 销毁）
- 文案：`🍲 你吃下了料理，获得【回春】效果！(每刻恢复 1% 生命)`

### 乘区类（dmg_calc 事件；旧 _affix_dmg_mult foods 分支）
| aid | triggers 声明 | 复用先例 |
|---|---|---|
| execute | `dmg_calc: [{type:"we_dmg_mult_cond", cond:"hp_target_lt", ratio:0.30, mult:1.30}]` | affix execute（equip_proc N9.7d） |
| precise | `dmg_calc: [{type:"we_dmg_mult_cond", cond:"always", mult:1.10}]` | affix precise |

## 4. 语义对齐细节（不陪葬旧 bug / 对齐 v2 定稿）
1. **AOE**：旧引擎 AOE 独立路径无 _food_on_hit（不触发食物命中效果）；battle2
   skill_hit 事件对 AOE 每目标是否 fire → 需查 battle2 actions/landing AOE 路径
   （对齐：若 fire 则 food 生效更广——以 battle2 v2 语义为准，v181 北极星）
2. **真伤不触发**：旧 v107 真伤不吸血/不触发词条；battle2 dmg_calc/skill_hit 插桩点
   是否含真伤路径需核对（对齐旧语义）
3. **回合开始 vs 1 秒 tick（已修正）**：旧回春类效果走 tick 卡（ACT_TICK=1 刻=1 游戏秒，
   **时间驱动**每刻跳，keep=True 常驻到战斗结束）——battle2 同构通道 = effects period
   声明（schedule 周期段同样时间驱动、首跳 1s + interval 每刻跳），**不是 turn_start
   行动帧**。regen/meditate/dawn_crown 已改为 effects period 落点（见 §3）。普通食物
   hot（regen_hot）已有 turns 限时先例；效果料理回春无 turns（战斗全程，对齐旧 keep=True）。
4. **效果期**：food = 本场战斗（actor 随战斗销毁即消失，无需 expire 管理）
5. **吃重复**：同 aid 不重复 append（现有 if a not in _fe 逻辑保留；triggers 同幂等）

## 5. 改动面 & 测试计划
- 改动：`game/commands/battle_item_use.py`（translate foodfx 分支 ~40 行）
  + `game/services/battle_food_proc.py`（新，翻译表 _FOOD_TRIGGER_DECLS + 吃入挂载函数；
  数值 import data/food_effect_data.FOOD_EFFECT_PARAMS，不复制数值）
  + battle2 引擎/**零改动**（事件插桩已有）
- 复用：battle_we_procs 扩展动作 we_affix_dot/defdown/bonus/element/counter/regen/
  dmg_mult_cond/taken_mult_cond 等（缺哪个补哪个，单 action ~15 行全域通用）
- 测试：`tests/test_battle_n10_b7_food.py`
  ① 吃蛇羹 → 普攻吸血回血（hp 上升断言）
  ② 吃烬火辣椒 → 命中目标挂 food_bleed dot（period 跳伤）
  ③ 吃狼肉干 → 受击触发反击
  ④ 吃树蜜糖 → turn_start 回血
  ⑤ 吃海鲜浓汤 → 伤害 ×1.1 精准
  ⑥ 吃海盗炖鱼 → 目标 <30% ×1.3 处决（>30% 不触发）
  ⑦ 圣餐面包 → 立即护盾（回归现有特判）
  ⑧ 吃重复 → 不重复 append/不重复挂 triggers
  ⑨ 战斗结束 actor 销毁无残留；纯怪零行为
  ⑩ battle2 全套回归零新增红 + 旧引擎线基线红不变
- 前置侦察（实施时）：
  a. battle2 AOE/真伤路径 skill_hit/dmg_calc 插桩行为（决定 4.1/4.2 对齐）
  b. we_affix_bonus vs we_extra_dmg 差异（pierce/combo 用哪个语义最贴）
  c. affix regen 翻译器读哪个数据源（对齐 food pct 覆盖层）

## 6. 为什么必须 N10-C 前做
- N10-C 删 battle.py 时 _food_on_hit/_food_on_taken/_food_turn_start/_affix_dmg_mult
  foods 分支 6 挂点全删 → food 效果永久丢失（当前 battle2 已接管，玩家已在受害）
- 此批 = N9_migration §4 清单里"food_effects 相关（如并入）"的正式并入
- 做完 food 装配 → N10-C 删 battle.py 时 food_effects.py 旧注册表可安全删除
  （装配翻译表替代旧 handler；FOOD_EFFECT_NAMES 保留给 item_templates/展示）
