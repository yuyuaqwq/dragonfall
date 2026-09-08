# 副本战斗内道具 use_item battle2 化设计方案（N5b4-5a 道具链）

> 2026-09-08。鱼鱼要求"详细到能落地"。本文档解决 R3 删除 `_instance_act`
> 前必须处理的 economy use_item 依赖链——战斗内使用道具（治疗/料理/药水）
> 在 battle2 引擎下的完整实现方案。
> 新会话口令：「读 docs/REFACTOR_v181P4_N5B5a_use_item_design.md，从第 X 步开始」

---

## 0. 现状与问题（为什么这条链必须现在处理）

### 0.1 当前调用链（旧引擎）

```
玩家『使用 <道具>』 → economy.use()（economy.py 5741）
  ├─ inst_battling（副本战斗内，5837-5897）
  │    1. IT.TEMPLATES[tpl](ctx)   # battle=st，模板只算 payload，不改状态
  │    2. db.remove_item
  │    3. payload 拼 cast
  │    4. self._instance_act(..., "use_item", payload)   ← 5895，旧引擎
  └─ 普通野外战斗（5902-5956）
       1. b = BT.Battle.from_state(state)   ← 5909，旧引擎
       2. 模板算 payload
       3. b.actor_act("use_item", payload, player)   ← 旧引擎 _do_use_item
```

### 0.2 问题

1. **R2 后副本战斗 state 已 battle2 化**（`st["battle"]` = B2 to_state 权威，
   `sync_views` 单点同步）——economy use_item 却还调 `_instance_act`：
   `_instance_act` 内 `BT.Battle.from_state({...旧键...})` 从 battle2 化的 st
   恢复旧引擎战斗对象 → **玩家副本战斗内喝药实际已崩/语义分裂**（不是将来时，
   是现在进行时）。
2. **普通野外战斗同病**（N5b4-2 后 state=battle2 to_state；旧 `BT.Battle.from_state`
   对 sides-only state "成功"但不认（enemy={}）→ 道具效果静默失效）。
3. **R3 删除清单**要删 `_instance_act` 整段——5895 行悬空，必须在本链解决后
   才能执行 R3。

### 0.3 已落地地基（勿重复）

- **commit f0199d6**：battle2 引擎 `action_override` 通用行动驱动回调
  （鱼鱼拍板方案：告诉引擎"做一次行动+耗时"，回调写功能）：
  - Battle 构造参数 `action_override=None`
  - `act()` 遇到非引擎内置 action（use_item/自定义）→ 先问外部
    `action_override(battle, action, actor, payload, target) -> (logs, cast)`
  - cast：str=内置基准（defend/skill/attack 按 spd 缩放）｜数字=绝对耗时秒
  - consumed 才推 ct + advance 敌方段（use_item 占刻语义）
  - 引擎零道具名词；测试 test_battle2_n5b4e_hooks.py 19 断言（+2 override 用例）

---

## 1. 目标架构

```
economy.use() 『使用 <道具>』
  │
  ├─ 副本战斗内（inst_battling & battle.battle 已 battle2）
  │    └─ IT.TEMPLATES 算 payload（模板 battle 非空只算不改）
  │         └─ _instance_router(..., "use_item", payload)     [R2 已接 router]
  │              └─ instance_battle.act(st, gid, qq, "use_item", payload)
  │                   └─ B2.human_act("use_item", payload)
  │                        └─ act() else 分支 → action_override 回调
  │                             └─ 道具翻译器 battle2_item_use.translate()
  │                                  ├─ heal/mana/hm → actor hp/mp 直改（landing.heal_actor）
  │                                  ├─ buff/food_buff → EFFECT_ACTIONS 查表 → act_buff
  │                                  ├─ special/shield 族 → EFFECT_ACTIONS/装配层查表
  │                                  ├─ hot → actor["hot"] + schedule 周期结算（新增基建）
  │                                  └─ 机制型真缺口 → 明确提示+不扣道具（清单见 §6）
  │
  └─ 普通野外战斗（battle2 state，N5b4-2 后）
       └─ 同上 router → instance_battle.act（需把 override 也注入野外战斗）

instance.py `_instance_act` 整段删除（R3，本链完成后）
```

**核心不变式**：道具效果全部落到 battle2 actor（hp/mp/buffs/hot/shields），
旧引擎 `_do_use_item`（battle.py 4026-4163）退役；翻译器只调 battle2 动词
（landing.heal_actor / effects.act_* / schedule），引擎零道具名词。

---

## 2. payload 全谱 → battle2 映射表（翻译器核心）

旧引擎 `_do_use_item`（battle.py 4026-4163）解析的 payload 共 8 类。
模板（item_templates）算好 payload 后交翻译器。逐类映射：

| # | payload 形态 | 来源模板 | 语义 | battle2 翻译 | 状态 |
|---|---|---|---|---|---|
| 1 | 纯数字 `"123"` | heal | 绝对恢复 HP | `landing.heal_actor(b, actor, n, logs, label="💊...恢复 {_real} 点生命！")`；race item_effect 加成同旧 | ✅ 直译 |
| 2 | `mana:N` | mana | 回蓝 | `actor["mp"]=min(max_mp, mp+N)` + log | ✅ 直译 |
| 3 | `hm:hp,mp` | heal_mana | 双恢复 | heal_actor + mp 直改 | ✅ 直译 |
| 4 | `buff:k1,k2` | food_buff / 药水 | 属性增益 3 刻 | 拆逗号 → EFFECT_ACTIONS 逐键 `effects.apply_effects(b, actor, actor, actions, logs)`（act_buff 写 `actor.buffs[key]={expire,stat,op,mult}`） | ✅ 查表 |
| 5 | `special:kind[:json]` | 药水/机制道具 | 特殊分发 | 查 POTION_EFFECTS → 拆到 battle2：shield/cleanse/heal/reduce/next_atk_up 等见 §3 子表；真机制缺口见 §6 | ⚠️ 分诊 |
| 6 | `foodfx:id,id` | food_effect | 食物效果（词条族） | actor["food_effects"] 记录 + 装配层挂卡（battle2_equip_proc 词条管线） | ⚠️ 基建 |
| 7 | `hot:hp%,mp%,turns` | food | 持续恢复 | `actor["hot"]={heal,mana,turns}` + schedule 周期结算（见 §4） | 🆕 基建 |
| 8 | `"0"` | stamina/purify | 无数值效果 | stamina 已由 economy 层处理；purify 模板已直接改状态（见 §5） | ✅ 特殊 |
| — | `;cast:N` 尾缀 | 全部 | 行动耗时 | 解析出 cast → override 返回数字秒（见 §2.2） | ✅ |

### 2.1 模板哪些已"直接改状态"（不用翻译器）

- **purify**：模板 `tpl_purify` 直接改 `ctx.battle`（st）里 p_buffs 删负面键
  ——但 battle2 负面在 **actor.buffs**（mode=skip/no_skill 条目），模板读
  st["p_buffs"] 已过时 → **purify 需改走翻译器**（清 actor.buffs 负面：
  effects 有 cleanse 动词 + CLEANSE_TAGS 表）。§5 详述。
- **stamina**：economy.use() 5886 已 `_add_stamina` 处理体力，payload="0"
  不翻译（占刻仍走）。

### 2.2 cast 耗时解析

- 旧 `_item_payload_cast(payload)` 从 `;cast:N`/`;recovery:N` 取动作时长。
- 翻译器：payload 尾部剥离 `cast:N` → override 返回 `N`（数字秒）；
  无 cast → 返回 `"defend"`（0.6 基准，吃药快速档，对齐旧默认）。

---

## 3. special 族分诊子表（第 5 类展开）

battle_ok 道具 effect 键实测 57 类去重。分诊：

### 3.1 battle2 EFFECT_ACTIONS 直映射（20 类，零新增，查表即用）

```
next_atk_up/buff_atk/buff_atk_big/buff_atk_small/buff_atk_food/
buff_def/buff_def_food/buff_spd/buff_spd_small/buff_spd_food/
buff_crit/buff_crit_big/buff_crit_small/buff_crit_food/
buff_matk/buff_matk_strong/buff_matk_food/
buff_phys_next/food_spd_up_small/cc_immune
```
→ 翻译器把 `special:next_atk_up`（或 `buff:...`）映射到
`EFFECT_ACTIONS[key]` 动作数组 → `effects.apply_effects`。
注意特例：`next_atk_up/buff_phys_next` 是 hit 型（dmg_mult），
`cc_immune` 无面板（纯状态），`buff_atk_def`=atk_up+def_up 复合→拆分。

### 3.2 battle2 动词可写翻译（shield/cleanse/heal/reduce 族）

| 旧 effect | 翻译目标 |
|---|---|
| shield_big/holy_shield/rock_shield | effects shield 动词（value 型，expire_at + 叠厚） |
| armor_break_pot/def_down | 对敌 control/debuff（写入 target buffs spd_down 等；battle2 控键） |
| magic_resist | buff stat=mdef add |
| heal_up | buff（受疗+%）→ 无现成键则用 heal amp 语义→ 记缺口或扩展动作 |
| restore_resource/resource_amp/resource_charge/restore_resource_full | act_state_add（resources/state 容器加值）——注意 target 在 actor["state"] |
| purify/purify_immune | cleanse / 免疫 buff（cc_immune） |
| dot_amp/apply_mark | 装配层扩展动作（battle2_we_procs 同款注册）→ 本批记缺口 |
| thorns_pot/dodge_pot/block_pot/crit_dmg_pot/lifesteal_pot/execute_pot | 见装配层效果注册（多数可走 hit/on_taken 声明）；本批若已有装配层键则映射，否则记缺口 |

### 3.3 机制型真缺口（本批不翻译，列 HANDOFF 清单，见 §6）

summon（召唤）/ trap（陷阱）/ phoenix（复活）/ morph（变身）/
invuln（无敌）/ reaction（反应）/ steal_buff / buff_extend /
mana_cost_down / full_tension / vuln —— 这些是**战斗机制本体**，
battle2 引擎无对应钩子或属上层职业/内容批；**进入副本战斗时给出明确提示
「该道具的战斗内效果尚未迁移，请在战斗外使用」且不扣道具不占刻**。

---

## 4. hot 持续恢复基建（battle2 schedule 缺失项）

现状：battle2 `_settle_time_effects`（schedule.py 161）只处理
buffs 到期 / shields 到期 / state DOT——**无正向周期恢复（hot/regen）结算**。
旧引擎 `_apply_hot` 每刻开头按 `p_hot{heal%,mana%,turns}` 回血回蓝。

方案（引擎小扩展，对齐现有 DOT 机制对称实现）：
1. actor 容器：`make_actor` 已播种 `actor["hot"]`（actors.py 51/110）——
   形态沿用旧 `{"heal": pct, "mana": pct, "turns": n}`。
2. schedule `_settle_time_effects` 增加 hot 段（循环各 side actor）：
   - actor["hot"] 非空 → 按 actor_stats max_hp/max_mp 百分比 heal/mana
     （调 landing.heal_actor + mp 直改），`turns -= 1`，归零清容器；
   - 事件：可选 fire("hot_tick")（N8 总线已有，观察者侧记）；
   - **触发时机对齐旧语义**：旧 hot 在"该玩家行动刻开始"结算 → battle2 在
     `advance()` 推进到该玩家决策点时结算该玩家 hot（见 schedule._next_player_due
     前钩子），避免全员每时刻都跳。
3. 测试：tests/test_battle2_hot_regen.py——吃食物挂 hot → 行动轮转 → 每到自己
   回血回蓝 → turns 递减 → 归零。

> 备选：把 hot 表达成 STATE_EFFECTS 里带 `dot` 的反向规则（负 pct=回血）——
> 否决：state 语义是"叠层"，hot 是"到期容器"，混入会破坏 cap/threshold 语义。
> 用 actor["hot"] 独立容器最贴旧语义。

---

## 5. purify 改法（模板直改 st → 翻译器）

现状 `tpl_purify` 删 `st["p_buffs"][member]` 负面键——battle2 下负面在
actor.buffs（结构化条目 mode=skip/no_skill）。改法：
1. `tpl_purify` 保留"满血/无负面可净化拦截"判定，但**负面检查与清除移到翻译器**：
   - 翻译器收到 purify payload → 遍历本 side 存活 actor.buffs，
     清 CLEANSE_TAGS（stun/silence/freeze/spd_down/reduce）对应条目 + 日志；
2. economy.use() 调用前模板只做"是否 consume"判定（有负面才 consume），
   模板需能从 actor 读到负面状态 → ctx.battle 需暴露 actor 视图（router 传
   st，模板读 `st["battle"]["sides"]` 或命令层先同步 actor 到 st players）。
   **更稳**：purify 不在模板改状态，模板统一返回 payload="purify:1"，
   拦截判定前移 economy.use()（读 actor）——见 §5.1。

### 5.1 拦截判定统一（economy.use 前置）

所有 battle_ok 模板的"满血/满蓝/无负面拦截"逻辑都读 ctx._focus / ctx.battle
（旧引擎快照）。battle2 下**权威是 actor**。为减少模板双轨，方案：
- economy.use() 战斗内分支：模板执行前先经 bridge 把当前 actor 状态同步进
  player dict（sync_player_from_actor 已有）→ 模板读 player 判定拦截照旧；
- 模板返回 consume/不 consume 后，扣道具与 payload 照旧；
- **payload 的应用永远在翻译器（actor 侧）**。

---

## 6. 文件改动清单（落地级）

| 文件 | 改动 |
|---|---|
| `game/battle2/schedule.py` | +hot 周期结算段（§4）；`_next_player_due` 前调 hot tick |
| `game/battle2/effects.py` 或新 `game/battle2/hot.py` | +`apply_hot(battle, actor, logs)`（hot 语义不进 state 表，独立动词） |
| 新 `game/commands/battle2_item_use.py` | 道具翻译器：`translate(battle, actor, payload) -> (logs, cast)`；内置 §2/§3 全表；未覆盖 → 返回 None（调用方提示不扣道具） |
| `game/commands/instance_battle.py` | `build_battle` 与 `act` 的 from_state 后注入 `b.action_override`（指向翻译器）；`act()` 支持 action="use_item" |
| `game/commands/combat.py`（N5b4-6 或本批） | 野外 from_state 恢复后同样注入 override（`_restore_battle2`） |
| `game/commands/economy.py` | ① 5895 行副本分流：`_instance_act` → `_instance_router(..., "use_item", payload)`（R3 前提）；② 普通战斗 5909 段改 battle2（b.human_act + override）；③ 翻译器返回未覆盖时**不扣道具不占刻**提示 |
| `game/core/item_templates.py` | purify 模板负面清除移翻译器（保留 consume 判定）；`_do_use_item` 相关注释 |
| `game/battle.py` | 只删不补（`_do_use_item` 等由 N10 删旧统一清；本批先无人调用） |
| `tests/test_battle2_item_use.py`（新） | heal/mana/hm/buff/hot/special 分诊逐类断言 |
| `tests/test_battle2_hot_regen.py`（新） | hot 周期结算（§4） |
| `tests/test_battle2_n5b4_instance_router.py` | +use_item 端到端（副本战斗内喝药/吃料理） |
| `docs/HANDOFF_battle2_effect_v2.md` | §0.5 追加记录 9 |

---

## 7. 分步执行 + 验证（每步 commit）

| 步 | 内容 | 验证 |
|---|---|---|
| I1 | schedule hot 周期结算 + effects.apply_hot + 测试 | test_battle2_hot_regen 绿 |
| I2 | 新翻译器 battle2_item_use：heal/mana/hm/buff/hot/常见 special 查表 | test_battle2_item_use 绿（不含引擎调用，纯函数单测） |
| I3 | instance_battle 注入 action_override + act 支持 use_item；economy 5895 副本分流改 router | battle2 全套 + 命令层冒烟 + router 测试补 use_item 端到端 |
| I4 | economy 普通野外战斗 use_item 段改 battle2 + override 注入 | cmdflow/野外 use_item 冒烟 |
| I5 | purify 改翻译器 + 模板调整；机制型缺口提示路径 | 净化用例绿 |
| I6 | 回 R3：instance.py 删除清单 + footer/world 残留改读 battle state + BT import 清零 | grep 验证 + 全套绿 + commit |
| I7 | HANDOFF 更新 + diff 给鱼鱼过目 | — |

> 建议：I1-I5 独立批次（每批小、全绿、commit），I6 是原 R3；全部完成才动
> instance.py 删除清单，避免悬空。I4 若想压缩可并 I3（economy 两条 use_item
> 分流同批），但普通战斗 state 恢复路径要一并验证。

---

## 8. 缺口清单（本批明确不做，HANDOFF 记录）

- 机制型 special：summon/trap/phoenix/morph/invuln/reaction/steal_buff/
  buff_extend/mana_cost_down/full_tension/vuln → 战斗内明确提示"战斗内效果
  未迁移，请在战斗外使用"，不扣道具不占刻（N10/上层职业批）。
- foodfx 词条族挂卡完整翻译 → 装配层词条管线批（部分走 N9.7 已建 affix 链路）。
- hot 周期结算的"受击打断/净化"语义若旧引擎有 → 本批仅实现基础恢复+到期。
- N5b4-6（economy/player/tower 轻文件 + 删 import）保持原排期。

---

## 9. 行为差异（本批完成后 vs 旧引擎）

- 道具效果权威 = battle2 actor；快照/DB 同步由 sync_views 每刻写回（无变化）。
- 治疗/回蓝数值口径对齐 landing.heal_actor（含 max_hp clamp），buff 时长 =
  battle2 绝对时刻 expire（旧 3 刻 ≈ now+3s 刻度语义，N9 已统一）。
- purify 负面判定改读 actor.buffs（结构化条目），清毒范围同 CLEANSE_TAGS。
- 机制型特殊道具战斗内不可用（明确提示，不静默失效——现状是静默失效）。
- 副本/野外 use_item 都占刻 + 敌方段照旧（action_override consumed 语义）。
