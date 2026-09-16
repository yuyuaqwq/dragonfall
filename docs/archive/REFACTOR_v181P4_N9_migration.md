# battle2 N9 施工方案：weapon/affix 族化迁移（效果系统 v2 全量收编）

> 2026-09-08 鱼鱼拍板：N9 自主推进，**最终验收 = N10 老战斗引擎 + 老效果系统
> 整体删除、不留兼容壳**。本文档 = N9 施工图（盘点 + 架构 + 批次 + 删除清单）。
> 配套：docs/archive/DESIGN_effect_system_v2.md（主方案）、docs/archive/EFFECT_TRIAGE_v181P4.md（分诊表）

---

## 1. 现状盘点（2026-09-08 实测，全库扫描）

### 1.1 三套旧注册表规模

| 注册表 | 文件 | 规模 | 数据形态 | battle2 现状 | N9 动作 |
|---|---|---|---|---|---|
| MECH_EFFECTS | game/core/battle_mech.py | **65** | 技能 mech handler | A 类通用已迁（N7：STATE_EFFECTS + control 动词） | C 类职业专属不迁（HANDOFF §2.1 拍板，上层族化） |
| SKILL_BUFF_EFFECTS | game/core/battle_mech.py | 36 | 技能 effect 名词 | N7 已迁 EFFECT_ACTIONS ✓ | 无 |
| BOSS_MECHS | game/core/battle_mech.py | 9 | Boss 机制 | N8 事件已留 phase/player_low/pv_broken | 上层 Boss 机制模块（不在本期） |
| MON_BUFF/CTRL | game/core/battle_mech.py | 12 | 怪物 buff/控制 | 死表 | **删**（N7.5 已定） |
| WEAPON_EFFECTS | game/core/weapon_effects.py + game/data/weapon_effect_data.py | **79 key / 13 族** | 全参数化（family + chance/数值/turns/log） | 数据表已 ready | **族化迁移**（本期主体） |
| AFFIXES | game/data/affixes.py + game/core/affix_effects.py | **76 词条**（HIT 29 + TAKEN 11 + stat/passive 常驻） | trigger 字段 stat/on_hit/on_taken/... | 消费端在旧 battle.py | **族化迁移**（下批） |
| BUFF_MULT | game/data/battle_config.py | 26 键 | 倍率名字表 | N7.1 已退役 | 旧表随旧引擎删除 |

### 1.2 weapon 13 族（79 key）事件需求

数据表 WEAPON_EFFECT_DATA[key] 自带 family + 参数；部分 key 自带 event 数组（缺省族默认事件见旧 proc 分发）。

| 族 | key 数 | 代表 | 事件落点 | battle2 表达 |
|---|---|---|---|---|
| proc_buff | 7 | gale_step/swift_boots | battle_start/turn_start 给自身 buff | `buff` 动词（扩展动作 or 纯动词） |
| proc_control | 9 | frost_ring/holy_judgment_field | skill_hit 命中给目标控制/减疗 | `control`/`state_add` |
| proc_dot | 4 | smith_blaze_wound/rong_lu_yu_wen | hit/skill_hit 挂 DOT | `state_add`(on=target dot) |
| proc_dr_revive | 2 | undying_will/death_dance_armor | 受击阈值/致死免疫 | 复杂状态机（上层扩展动作） |
| proc_extra_dmg | 11 | wind_split/hunter_open | hit/skill_hit 追加伤害 | **需 `damage` 动词**（引擎 N9.1 补） |
| proc_heal | 8 | vital_band/guard_regen | 治疗/时刻回复 | `heal`/扩展 |
| proc_next_atk_mark | 5 | trinity_rhythm/mountain_break | skill_hit 挂下次攻击标记 | `buff` hit 子键（N7.3 已有机制） |
| proc_passive_mult | 4 | arcane_firmament/combo_end | 常驻面板乘区 | stats 折算层（非事件） |
| proc_reflect | 5 | thorn_armor/iron_echo | on_taken 反弹 | `damage` + ctx.caster |
| proc_retort_mark | 4 | gargoyle_retort/guardian_will | taken 标记下次攻击 | `buff` hit 子键 |
| proc_shield | 10 | starlight_bulwark/eclipse_crown | battle_start/taken 上盾 | `shield` |
| proc_special | 3 | death_dance 缓伤池 | 多回合状态机 | 上层扩展动作 |
| proc_stack | 7 | thunder_weave/wind_mark | hit 叠层 | `state_add` + stats 折算 |

### 1.3 事件映射（旧事件集 → battle2 19 事件）

| 旧事件 | battle2 事件 | 备注 |
|---|---|---|
| battle_start | battle_start | ✓ 引擎已插桩 |
| hit（普攻+技能通用） | attack_hit + skill_hit | 装配层展开两个事件 |
| skill_hit | skill_hit | ✓ |
| skill_cast | act_cast | ✓ |
| taken | on_taken | ✓ |
| taken_after | （on_taken 后由上层标记） | 装配层处理 |
| heal | on_heal | ✓ |
| turn_start | turn_start | ✓ |
| turn_end | — | 无引擎点（N9 收编为 turn_start 后置或上层） |
| enemy_act | — | 上层（怪行动后）——第一批不做 |
| threshold | threshold | ✓ |
| crit | crit | ✓ |
| kill | on_kill | ✓ |
| passive | stats/面板折算 或 act_cast 前 | 常驻型不走事件 |
| dot_taken | dot_tick | ✓ |

---

## 2. 架构落点（定稿）

### 2.1 效果源 = actor["triggers"]（N8 已建）

装备特效/词条在**装配层**翻译成 actor["triggers"] = {事件: [效果 dict]}：
```python
# 效果 dict 两种形态：
# ① 纯动词（引擎原生能力可表达）：{"type": "shield"/"state_add"/"buff"/"control", ...参数}
# ② 族扩展动作（复杂机制）：{"type": "we_shield", "key": "starlight_bulwark", ...}
#    type=we_xxx → ACTION_HANDLERS 扩展注册表（装配层启动时注册）
```

### 2.2 族执行器 = 游戏侧扩展动作（引擎零知识不破坏）

- battle2/effects.py 的 `ACTION_HANDLERS`/`register_action` 是**开放注册表**（与 config 挂载同构）
- 游戏侧装配模块（battle2 包外 services）启动时注册扩展动作：
  `register_action("we_shield")` 等（fn 签名与引擎动词一致 (battle, caster, target, params, logs)）
- 族执行器内部通过引擎公开 API 落地：landing.deal_damage/heal_actor、effects 动词、
  actor state/buffs/shields 容器——**不碰旧 battle.py 私有方法**
- 引擎不认识 we_xxx 语义、不 import 装配层 → 北极星（引擎零游戏知识）保持

### 2.3 装配函数（命令层/测试开战前调用）

```python
# game/services/battle_equip_proc.py（新）
def install_ext_actions() -> None        # 启动注册族扩展动作（幂等）
def triggers_for_actor(actor) -> dict    # 读 actor.equipment → 事件→效果 dict（含 affix/weapon）
def apply_to_actor(actor) -> None        # install + actor["triggers"] 合并（命令层 build_sides 后调）
```

### 2.4 引擎前置缺口（N9.1）

- effects.py 补 **`damage` 动词**（DESIGN 动词表 143 行已承诺，N7.5 未落地）：
  `{"action":"damage","value"/"pct", "kind": phys/magi/true, "on": target}` → landing.deal_damage
- （可选）hit 子键已支持 next_atk_up 类（N7.3）✓ 无需新增

---

## 3. 批次计划（每批：实现 + 行为对拍测试 + 覆盖门禁 + commit）

| 批次 | 内容 | 规模 | 依赖 |
|---|---|---|---|
| N9.1 | 引擎补 damage 动词 + 测试 | 1 动词 | — |
| N9.2 | 装配层骨架：install_ext_actions/triggers_for_actor + 事件映射表 | 框架 | N9.1 |
| N9.3 | **试点族**：proc_shield(10) + proc_dot(4) + proc_buff(7) = 21 key | 21 | N9.2 |
| N9.4 | 纯动词族铺开：proc_heal(8) + proc_control(9) + proc_stack(7) | 24 | N9.3 验证后 |
| N9.5 | damage 族：proc_extra_dmg(11) + proc_reflect(5) | 16 | N9.1 |
| N9.6 | 复杂机制族：proc_next_atk_mark(5) + proc_retort_mark(4) + proc_special(3) + proc_passive_mult(4→stats) | 16 | N9.5 |
| N9.7 | affix 76 词条族化（stat 常驻→面板；on_hit/on_taken→事件；battle_start/passive） | 76 | N9.6 |
| N9.8 | 命令层 N5b-4 切换后真实数据路径装配（开战 install_ext_actions + apply_to_actor） | — | N5b-4 |
| N10 | **删旧**：battle.py / battle_mech.py / weapon_effects.py / _we_executors.py / affix_effects.py / food_effects 相关 / BUFF_MULT 等 + 全量回归 | 删除 | 全部 |

**对拍策略**：同输入同输出 = 行为快照断言（不跑旧引擎构造）——每个 key 的族行为按
旧 handler 语义 + 数据表参数固化期望（例：thorn_armor 受击反 15% 实际扣血）。
master P2C 已核过"表值 = handler 硬编码值，diff=0"——参数权威在数据表，读表即对拍。

**数值权威**：全部读 weapon_effect_data / affixes 数据表，代码零默认值（沿用 master
P2C "读表参数铁律"）。缺字段 = 无此行为，绝不补默认值。

---

## 4. 最终删除清单（N10，鱼鱼验收"清干净"）

| 删除对象 | 文件/表 | 替代 |
|---|---|---|
| 旧战斗引擎 | game/battle.py（11000+ 行） | battle2 包 + 命令层切换 |
| 技能 mech 注册表 | game/core/battle_mech.py MECH_EFFECTS（C 类残留） | 上层职业模块（battle2 外） |
| Boss 机制 | BOSS_MECHS | 上层 Boss 机制模块（后续迭代，不在 N9） |
| 怪 buff/控制死表 | MON_BUFF_EFFECTS / MON_CTRL_EFFECTS | 无（battle2 rules 已覆盖） |
| 武器特效引擎 | game/core/weapon_effects.py + _we_executors.py | services/battle_equip_proc.py 装配 |
| 词条效果引擎 | game/core/affix_effects.py HIT/TAKEN | 同上 |
| 词条效果数据 | game/core/affix.py（若仅服务旧 proc） | 装配层 |
| 食物战斗效果 | food_effects.py FOOD_HIT/TAKEN（如并入） | 装配层/生活排除 |
| 倍率名字表 | battle_config.py BUFF_MULT / BUFF_STAT_KEYS | EFFECT_ACTIONS 动作参数（N7 已退役） |
| 旧效果系统散件 | 旧 battle.py 内 _affix_*/_set_*proc/_we_proc 等私有方法 | battle2 + 装配层 |

> ⚠️ 纪律：N10 删除 = 每删一块跑全量回归（battle2 全套 + numeric 52 + 命令层服务测试），
> 删除只发生在对应能力已由 battle2 路径验证后。不保留兼容壳/开关/兜底参数（鱼鱼铁律）。
