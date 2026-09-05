我已完成对 6 个文件（含 battle.py 消费端、data 声明端交叉验证）的全量审计。下面是完整报告。

---

# 战斗效果系统剩余重复/硬编码审计报告

## 一、跨文件同语义效果重复（未收敛到 effect_actions.py）

### 1.1 破甲 def_down：potion 还有自己的实现，与 effect_actions.action_def_down 逐行重复
- 文件:行号: `core/potion_effects.py:126-134`
```python
@register("def_down")
def eff_def_down(battle, player, value):
    v = _resolve(value, "def_down")
    pct = float(v.get("pct", 0.15)); turns = int(v.get("turns", 2))
    battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), turns)
    battle.e_buffs["_armor_break_pct"] = pct
    return f"🛡️ 破甲！敌人防御下降 {int(pct * 100)}%！({turns} 刻)"
```
对比 `core/effect_actions.py:45-49` `action_def_down(battle, logs, turns=2, pct=0.15)` 一模一样（仅返回日志串 vs append）。
- 问题类型: 跨文件同语义效果重复——破甲"动作"共 3 份：affix `_h_armor_break`(已收敛)、food `_f_h_armor_break`(已收敛)、potion 这 1 份漏网。药剂 handler 还把自己数值逻辑写进 e_buffs，一旦 DOT/破甲引擎改字段（如 v151 heal_down 消费端那次）需改 3 处。
- 影响: 药水破甲与词条/食物破甲行为分叉风险；未来改动易漏（本次统一只覆盖了 affix/food）。
- 建议: potion `eff_def_down` 改为调 `action_def_down(battle, logs, turns=turns, pct=pct, label="破甲")`，只保留数值解析（读 value/DEFAULTS）。同理检查 `eff_lifesteal_pot`（吸血 buff 型，语义为乘算并入吸血率，与 action_lifesteal 每击直回不同——**不建议**收敛，但要注释区分）。

### 1.2 元素附加·雷 / 初火 / 烈日 / 深寒 / 熔炉 等"火/冰/雷属性附加 + 追加段"在 affix 内部各写一份，未复用共享底座
- 文件:行号:
  - `affix_effects.py:164-175` `_h_element_thunder`（雷附加：dmg×pct 直伤 + chance 追加 dmg×thunder_bonus，两段都 `_damage_enemy`，不走 `action_element_dmg`/`_bonus_dmg_apply`——**漏了 Boss 护盾过滤 + 援军挡刀**）
  - `affix_effects.py:178-197` `_h_chu_huo`、`:978-993` `_h_blazing_sun`、`:996-1007` `_h_deep_frost`、`:964-975` `_h_ember_furnace`、`:1131-1137` `_h_sun_blaze`——同一"dmg×pct 附加伤害"形状手写 5 份。
- 问题类型: 文件内重复（同语义未收敛）。effect_actions.py 注释明确写了 `action_element_dmg` 是"affix/food element_fire/element_ice 共用底座"，但 **element_thunder 及其它带附带的词条没有走它**。
- 影响: `affix_effects.py:169-171` 的雷附加段直接 `_damage_enemy`，与 v104 M02 P1-5 修过的 bug（词条附加伤害绕过 Boss 护盾）同款——`_h_element_thunder` 主附加段、`_h_chu_huo/blazing_sun/deep_frost/sun_blaze` 的附带段全部绕过 `_boss_dmg_filter`。打盾 Boss 时这部分伤害不减半。
- 建议: 统一改走 `action_element_dmg`（需给它加 `extra_bonus_pct`/二次触发参数）或至少让附带段经 `_bonus_dmg_apply` 落地。

### 1.3 反伤/荆棘/灼烧-叠层/减速：四个文件各写一套"小形状"，未收敛（且数值 100% 硬编码）
反伤家族（**语义相同、数值各写**）：
- `affix_effects.py:303-309` `_h_ember_ward`：`rd = int(ctx["dmg"] * 0.50)` 直伤（50%，读数据 effect pct）
- `food_effects.py:130-137` `_f_t_thorns`：`rd = int(ctx["dmg"] * 0.30)` + boss 过滤（30%）
- `weapon_effects.py:674-683` `_we_thorn_armor`（15%）、`:719-729` `_we_dragon_spine_mail`（25%）、`:732-741` `_we_retribution_ring`（30%）——3 个 handler 正文仅 pct 不同，**全是裸 `int(dmg * 0.15/0.25/0.30)`**
- `battle.py:9606-9608`：荆棘药剂 buff 消费 `th = 1 - (1 - th) * (1 - 0.30)` 硬编码 0.30
- 另有**第四套**反伤系统：`battle.py:9610-9613` `block_reflect_val`（技能反伤 40/50%）与 `thorns` 并行。

减速 spd_down 家族：affix `_h_deep_frost`(1005)、`action_element_dmg`(105)、food static(116)、weapon `_we_frost_ring`(111-116 `_slow_enemy`)、battle_mech `_m_spd_down`/`_m_slow`(189-248) + `_mc_slow`(1016-1026)、旋律 `_melody_apply_e_buffs`(1613-1638)——7 个入口都写 `e_buffs/buffs["spd_down"] = max(...)` 同一键。**键统一是好事**，但"减速几刻"在 weapon 是纯硬编码（见 §2.3），在旋律是 handler 内 switch 硬编码（0.15/0.18/0.20/0.25，见 §2.4）。
- 问题类型: 跨文件/文件内同语义多份。
- 影响: 反伤在 4 个系统各有实现，将来统一走主结算路径/护盾过滤（v104 那次）得改 4 处；DOT 类同理（§1.4）。
- 建议: 反伤收敛为一个共享 action（`action_reflect(battle, player, ctx_dmg, pct, logs)`，内部统一 `_boss_dmg_filter → _damage_enemy`）；数值从数据行读取（现在 weapon 侧连数据字段都没有，见 §2.3）。

### 1.4 灼烧/毒/流血"叠层"写法分散 3+ 套，且层语义与 DOT 引擎不一致（重要）
- 文件:行号:
  - affix 手写 burn 栈：`affix_effects.py:190-197`（chu_huo）、`:969-975`（ember_furnace）、`:987-993`（blazing_sun）——`cur = deb.get("burn") or {"n":0,"mult":1.0}; cur["n"] = min(3, ...)`，max 上限**3**，写 `pct/turns` 字段
  - 数据驱动执行器 `_sp_burn`：`affix_effects.py:604-614`（上限 `max_stacks` 默认 3，写 pct/turns）
  - weapon `_apply_dot`：`weapon_effects.py:132-140`——`cur["n"] = min(int(cur.get("n",0))+stacks, stacks)`，注意这个写法**把 n 钳到当次 stacks**（叠 1 层时 n 恒 ≤1，多段叠不上），上限逻辑与 affix/mech 的 min(5,…) 完全不同
  - weapon `_we_blood_trace`：`:369-380` 手写第 4 套
  - battle_mech `_m_burn/_m_poison/_m_bleed/_m_corros`：`:116-152 / 492-531 / 563-582 / 2140-2149`——第 5 套（含免疫/被动 mult/适应等 mech 专属逻辑，但叠层核心仍是"debuffs[k].n 自增钳位"）
  - 玩家侧 Boss 挂 dot（净化清 debuffs 那条链）还有 battle_mech `_sb_cleanse_p:1231-1248` 读写玩家 `debuffs` 容器。
- 问题类型: 同语义（往 enemy.debuffs[k] 叠 n）跨文件 5 套实现；**上限参数漂移**：词条 burn 3 层 vs mech burn 5 层 vs weapon `_apply_dot` 每次覆盖式钳位 vs DOT_DEFS 注释"层数上限 5 层双保险"。
- **附带重大发现（§2.1 一并讲）：battle.py `_tick_actor_dots`（7950-8013）结算伤害完全只读 `DOT_DEFS` 系数 × n，从不读 `d["pct"]`、`d["turns"]`** → 所有 handler 写进 debuff 的 `pct/turns` 字段全是**死字段**。
- 影响: 同是"灼烧"，词条 3 层封顶、技能 5 层封顶、武器 `_apply_dot` 叠不上去；伤害倍率却统一走 DOT_DEFS（burn=matk×0.6+0.5%max_hp/层）——数据里 `burn_pct: 0.01/0.015`、affix `dot_pct: 0.05`（"每刻 5% 生命"）与引擎实际（1.5%/层）不一致，纯装饰。鱼鱼的数据驱动铁律下这是最该收的一处。
- 建议: 收敛一个 `stack_dot(battle, key, n, max_n=5, mult=None)` 动作（叠层+免疫检查），全部 handler 改调它；删掉 `pct/turns` 死字段写入；若"灼烧 1.5%"确实是设计，把 per-layer 系数数据化进 DOT_DEFS 或 per-affix。

---

## 二、handler 内部硬编码数值（数据声明有字段却不读 / 数据无字段代码裸写）

### 2.1 DOT 引擎不读 `debuff.pct/turns`，所有写入者白写（全文件）
- 文件:行号: `battle.py:7950-8013`（伤害 = `(atk_part+hp_part) × n × mult`，全由 `DOT_DEFS` 系数决定）；写端 `affix_effects.py:194-195, 610-611, 972-973, 990-991`、`weapon_effects.py:137-138, 377-378`、`potion_effects.py:667-671`、`battle_mech.py:139-140`（写 `cur["pct"]`/`cur["turns"]`）。
- 问题类型: 死数据 + 语义脱钩（数据声明了 burn_pct/burn_turns/dot_pct，代码从不消费）。
- 影响: 加新 DOT 效果时按既有模板写 `pct` 会以为调了数值，实际无效；affix bleed 的 `dot_pct:0.05`、chu_huo 的 `burn_pct` 全部失效但 desc 还在宣称。
- 建议: 要么引擎读 `d["pct"]`（per-来源伤害），要么删字段并把数值并入 DOT_DEFS；先删写入端防误导。

### 2.2 affix D2/D3 专属 handler 裸数值、与数据 effect 字段脱节/错位
逐个（数据声明见 `data/affixes.py` 对应行）：
1. **mortal_wound 致伤重击** — `affix_effects.py:1153-1159`
```python
battle.e_buffs["_anti_heal_pct"] = 0.50
battle.e_buffs["anti_heal_turns"] = max(..., 2)
```
数据 `{"heal_down": 2}`（desc"受治疗-30%"）。代码写 50%、还写了个全引擎无人消费的 `anti_heal_turns` 键（battle.py 只在 5393-5403 消费 `heal_down` 层×10% 与 `_anti_heal_pct`，`anti_heal_turns` 零引用）。**数值(50 vs 30)、通道(heal_down vs _anti_heal_pct)双脱钩**。影响: 玩家吃 50% 重伤而非 desc 的 30%。
2. **memory_tear 记忆撕裂** — `affix_effects.py:1162-1168`：数据 `{"silence":1}`（desc：沉默 1 刻），代码却写 `mon_atk_down=2 / _weaken_val=0.15`（降攻 15%）。**效果类型都变了**（数据想沉默、代码做降攻）。battle.py 无任何 `silence` 语义被触发 → 数据声明的沉默效果从未发生。
3. **arcane_echo 秘法回响** — `affix_effects.py:1171-1176`：`player['eff']["arcane_echo_next"] = 1.15`。数据 `{"next_skill_dmg": 0.15}`。键名(arcane_echo_next vs next_skill_dmg)、值形(1.15 vs 0.15)与数据全不一致；且全引擎（含 battle.py）检索 `arcane_echo_next` = **0 处消费** → 效果完全空转（写了没人读）。同类 **sanctum_light 圣殿辉光** — `:954-961` 写 `enemy_atk_down/_enemy_atk_down_pct`，这两个键在 battle.py 消费数 = 0（敌方攻降统一走 `mon_atk_down/_weaken_val`）→ 圣殿辉光 8% 降攻从未生效。
4. **siphon 汲魂** — `:1179-1185`：`heal = max_hp * 0.05` 硬编码 5%，数据 `{"purge":1, "heal_pct":0.03}`（3%），且代码根本没做"驱散 1 层增益"。
5. **summon_pact 召唤契约** — `:1188-1198`：`pst.atk * 0.30` 硬编码 30%，数据只有 `{"summon":1}`，召唤强度无字段承载。
6. **sun_blaze 烈日迸发 / chain_overload 连锁过载** — `:1131-1137 / 1140-1150`：`dmg*0.80`、`matk*0.60` 裸写（数据 effect `pct:0.80`/`extra_atk:0.60` 恰好同值，属于"碰巧一致"，改数据即脱钩）。
7. **iron_bastion/steady_core/obsidian_aegis/night_watch/blood_oath_echo/soul_devourer** 等 D2/D3（`:1021-1049, 1074-1103`）：`_armor_break_pct`/`heal_pct` 等大部分已走 `_affix_effect().get(key, default)` 读数据 ✓，但 default 形参即硬编码副本（可接受，注释已注明"数据缺失兜底"），风险低于 1-6。
8. **element_thunder / chu_huo / blazing_sun / deep_frost / ember_furnace / thunder_mark / star_shatter / gale_dirge / shadow_raid**：读数据 ✓（`_affix_effect().get(...)`），但其中 burn 栈的 `min(3,…)`、`pct_dot = 0.01 if boss else 0.015`（chu_huo `:190`）仍是裸写——boss/精英打折数值不在数据里。
9. **mark_pct=0.02 文案**（dragon_tongue `:253`、thunder_mark 数据 `mark_pct:0.02` 只用于日志）——每层增伤实际消费点 battle.py `_extra_dmg_mult`（5105-5106）读的是数据 mark_pct ✓，但 affix handler 侧传 0.02 进 `action_mark` 仅文案用，若数据改 0.03 日志仍显示 2%，轻微不一致。

- 问题类型: 硬编码 + 键/值/通道与数据声明错位 + 死消费。
- 影响: 上面 1/2/3 三个是**实打实的效果错误**（数值翻倍、效果类型错乱、写了没人读=白板装备）；其余是改数据不生效的隐性坑。
- 建议: 逐条对齐到数据 effect 字段 + 统一写键（降攻→`mon_atk_down/_weaken_val`、禁疗→`heal_down`）；arcane_echo 消费端（若设计为"下次技能增伤"）挂到 `_consume_v169_buff_dmg` 或 `we_*` 同款乘区；删 `anti_heal_turns`/`enemy_atk_down` 死键。

### 2.3 weapon_effects.py 全文件数值无数据字段、全部硬编码（结构性）
- 文件:行号（代表）：`weapon_effects.py:218`(星辉 10%盾/3刻/5刻CD)、`:343-346`(裂伤 pct 0.01/0.015、turns 3 裸写)、`:352-355`(熔炉 0.03/0.015/2)、`:377-379`(blood_trace 0.015/0.02、turns 4 裸写)、`:411/424/441`(暴击满层/幻影 0.3/0.5 防御/海妖 0.4)、`:452`(噬魂 2% 当前血)、`:519-520`(烬燃)、`:575-578`(无尽辉光 5%盾/2刻/3刻CD)、`:643`(哨兵 6+0.5×lv 盾)、`:657-658`(铁壁 40%反击+2%回血)、`:680/725/738`(反伤 15/25/30%)、`:752-758`(烬火燎原 5%max_hp、burn cap 5)、`:866-892`(三刻回血 2%已损/2%max/1.5%max)、`:905-914`(死亡之舞 35%/10%/10 刻)、`:939-954`(兰顿/冰脉 6%/8%/层×3)、`:971-973`(时光 30% 阈值)、`:1049-1056`(暮裂 30%)、`:1066-1070`(暮光 40% 阈值+25%)、`:1238-1249`(新手吸血 5%)、`:1326`(晨星 10 点 mp)…
- 数据侧：`data/equip_roster.py` 每行只有 `weapon_effect: "key"` + `special/desc`（中文文案），**没有任何数字字段**——数值唯一权威在 handler 代码（文件头注释第 28-29 行也承认："数值以本文档 handler 内 DEFAULT 为准——special 仅作展示"）。文件头自己标注这是"为可控实现"，但**与鱼鱼"数值/配置不硬编码在代码里"铁律直接冲突**。
- 问题类型: 结构性硬编码（80 个武器特效 ≈ 全部数值在代码）。
- 影响: 调一件装备的数值 = 改代码行 + 改 desc 两处，且同类特效（减速 15/20/25%、反伤 15/25/30%、每刻回血 2%/1.5%、盾 10/15/12/20/25%）各写各的常数，改一档要改一个 handler。
- 建议: 给 weapon_effect 数据行加 `effect_data`（{chance, pct, turns, cd…}），handler 从 `has_effect` 处一并取参（affix 的 `_affix_effect` 模式现成可抄）；至少先把 5 个 gale_step 变体（`:224-282`，仅 pct/turns 不同、正文逐字重复）合并成一个 handler 读参。

### 2.4 battle_mech.py 数值/语义硬编码（技能数据 mech_val 之外裸写）
- 文件:行号:
  - `:2121/2128/2135-2136` 诗人哀歌/破碎和音/哀悼之音：`mon_atk_down = 8`、`def_down = 8` **硬编码 8 刻**，且 def_down 只写刻数不写 `_armor_break_pct`（走 _enemy_stats 7492 行 DEF_DOWN_MULT 兜底——兜底值藏在 battle.py）；`_m_all_down` desc 说"全属性-20%"实际只降攻防两项。
  - `:1619/1622/1630/1634/1636/1638` 旋律 `_melody_apply_e_buffs`：0.15/0.18/0.20/0.25/0.25/0.25 全硬编码。**对照 data/skills.py 的 desc**：镇魂歌"速度-15%"✓、挽歌"攻击-18%"✓ 恰好一致，但终章数值（-35%/-40%/-50%，`:1709-1732` 0.35/0.40/0.50）与 `finale` 数据字段无任何绑定——调 desc 不改这里就脱钩。
  - `:967/980` `_mc_freeze/_mc_stun` 概率公式 `min(0.75, 0.25+mval*0.15)` 等（v113.1 后本可用数据 mech_chance，怪物技能大多没配，代码兜底 OK，但兜底值集中在这里写死，与 `_m_freeze/_m_stun` 玩家侧同公式重复）。
  - `:1025` `_mc_slow` 硬编码 2 刻（有注释承认"旧 MON_CTRL slow 固定 2 刻"）。
  - `:1404/1419` 技能反伤 40% 走 `block_reflect_val`：`_sb_block_reflect` 处 `battle._add_shield` 后的 `_brv` 数值从哪来需再核（注释里 "40% 超上限，记 p_eff"——疑似 handler 内硬编码 0.4）。
  - 叠层系数：`_m_rage` 12%、`_m_zhan_yi` 4%、`_m_burn`/`_m_poison`"每层 3%/每刻"（日志文案）、`min(5, …)` 上限、`poison_burst 0.30×n`、`burn_burst 0.40×n`、易燃 `0.10×(n-2)`——系数在代码里，技能侧 mech_val 只管层数。注释多处自证（"与 poison 同构"）。
- 问题类型: 技能 mech 语义的数值仍在 handler 内（mech_val=层数，百分比系数靠代码）。
- 影响: 调"灼爆 40%"这类 = 改代码；诗人旋律档位 desc/代码双源。
- 建议: 优先把旋律 e_* 档位读技能数据（melody 技能已有 `melody:"e_atk"` kind，加 pct 字段即可）；mech 系数可加 `mech_pct` 数据字段兜底参数。

---

## 三、effect_actions.py 死代码 / 收敛缺口

- **无死代码**：10 个 action（regen_hp/regen_mp/dot/def_down/mark/bonus_pct/element_dmg/pierce_dmg/counter/lifesteal）全部被 affix/food 引用（各 2-8 处），无一闲置。
- **收敛缺口（反向）**：§1.2/§1.4 列出的同类动作仍绕开共享底座——特别是 **element_thunder（affix_effects.py:164）与 element_fire/ice 同语义却不走 `action_element_dmg`**；`affix_effects.py:169-175` 两段直伤 `_damage_enemy` 均无 Boss 护盾过滤（对比 `effect_actions._bonus_dmg_apply` docstring：food 侧原实现有过滤、affix 漏了——**这次漏的是 affix 自己内部的 thunder 分支**）。
- 另外 `food_effects.py` 内 thorns/aurora_guard/static 三个效果仍是手写直伤/ctx 修改（`:130-147, 112-117`），如果按 §1.3 建反伤 action 也应一并收敛；但它们没有 affix/weapon 对应物可证伪，属"可选收敛"。

---

## 四、额外发现的注册表/数据断链（顺带，供参考）

| 位置 | 问题 |
|---|---|
| `data/equip_roster.py`（3 件：辰光法杖/深渊骑枪/黑渊之眼 `weapon_effect: divine_execution / dragon_annihilation / star_destruction`） | 这三个 weapon_effect 键在 weapon_effects.py **无 handler**（79 注册键全查无此 3 个），行上也无 affixes/legendary 字段。特效走 weapon proc 通道时被静默跳过 → 装备效果疑似**死数据**（若装备实例化另有词条注入则需确认） |
| `data/items.py` 圣餐面包 food `shield` | 效果在 battle.py `_do_use_item:3511-3513` **硬编码 10% 盾/3 刻**，数据行无 effect_data——加新护盾食物只能改代码 |
| `battle.py:5089-5094`（_extra_dmg_mult 食物处决/精准） | 处决 +30%/阈值 30%、精准 +10% **硬编码**，数据行只有 desc 文案；与 2.3 同类 |
| `core/item_templates.py:381 + potion_effects.py DEFAULTS 首胜扫描` | `i_ironwall_salve`（shield_big effect_data **pct:0.30**）被 `_scan_defaults` 的"首个命中"规则坑了——`i_holy_shield_pot`(0.15) 映射同 kind 且排在前面 → **铁壁药膏实际只给 15% 盾**，0.30 数据被静默吞掉 |
| `potion_effects.py:81-87` 龙鳞/深渊药剂 `magic_resist` | handler 只把 turns 写进 `p_buffs["magic_resist"]`，**pct 0.15 从不持久化**；全仓库检索 `magic_resist` 无任何消费代码 → 该药剂效果**纯日志空转** |
| `affix_effects.py:1179-1185`（siphon）等 §2.2 若干 | 见上 |

---

## 优先级建议排序
1. **P0 效果错误**：§2.2-1/2/3（mortal_wound 50% vs 30%、memory_tear 沉默变降攻、arcane_echo/sanctum_light 写了没人读）+ §1.2 element_thunder 绕盾 + §2.1 DOT pct/turns 死字段。
2. **P1 数据驱动违例**：§2.3 weapon_effects 全文件数值下沉数据行（可先做 §2.3 里 gale_step/反伤/回血/盾 4 组同类合并）。
3. **P2 收敛**：§1.1 potion def_down → action_def_down；§1.4 叠层动作统一。
4. **P3 数据断链**：§4 三件死 weapon_effect、铁壁药膏 30% 被吞、magic_resist 空转、食物 shield/处决/精准数值数据化。

全程只读审计，未改动任何代码。