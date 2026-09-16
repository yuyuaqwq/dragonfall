# battle2 效果系统 + 时效系统收口方案（v181.P4-N7）

> 2026-09-08 鱼鱼拍板：效果系统（buffs/护盾/控制/DOT/一次性）必须一次性改好引擎，
> 不许留到"以后"。"护盾也是持续 N 刻的""buff 挂载的到底是什么、效果系统收敛了吗"
> "层数×10%是什么""固定×1.3也不对——数值不该藏在名字表"——本文档回答并定稿。
>
> **排期决策（鱼鱼 2026-09-08）：先完全收敛效果系统（N7），再继续命令层切换（N5b-4）——
> 展示辅助依赖效果语义定稿，先收敛避免命令层返工。N7 全部完成后才回到 N5b-4。**
>
> **实施方式（鱼鱼 2026-09-08 纠正）：不迁移旧代码/旧配置——效果系统 v2 全新写，
> 配置重新填充（策划案为准，旧 BUFF_MULT 仅作对照参考——策划案可能过时，两边对比）。
> 旧 battle_mech/weapon_effects/affix 三套完全不动、保留可跑，v2 验证后整体切换。**
>
> 目标：battle2 引擎代码一次收口，字段级定稿，对拍旧引擎行为，测试固化。
> 北极星不变：引擎零游戏知识（只执行动词/查配置表），配置换=新游戏。

---

## 1. 现状诊断（实测数据）

### 1.1 效果系统收敛度（实测）
| 数据面 | 总数 | battle2 已映射 | 未覆盖 |
|---|---|---|---|
| 技能数据 effect 名词（全库 grep） | 187 | ~23（rules EFFECT_ACTIONS + STATE_EFFECTS） | **181**（含大量非战斗：生活/开箱/诱饵等需分诊） |
| 技能数据 mech 名词 | 13 | 8 | 5（enrage/heal/interrupt/summon/thunder） |

- battle2 rules `EFFECT_ACTIONS` 23 名词 vs 旧引擎 `SKILL_BUFF_EFFECTS`（7 效果注册表）+ `battle_mech.py` 各 mech handler + `affix_effects.py`/`_we_executors.py` 词条武器效果 → **战斗效果主干远未收口**。
- 注意：187 个 effect 里相当一部分是非战斗/生活技能 effect（open_chest/bag_expand/loot/bait_*/return_vila 等）——不进效果系统，需分诊表排除。

### 1.2 面板折算模型冲突（实测）+ 根因
| | 旧引擎 | battle2 现状 |
|---|---|---|
| 表 | BUFF_MULT 26 键（data/battle_config.py） | BUFF_STAT_KEYS 7 键（rules） |
| 语义 | **固定倍率乘算/加算**（atk_up→atk×1.30；crit_up→crit+0.20；mon_atk_down→atk×0.70） | **int 刻数 → ×(1+n×0.10)**（把 buff 当叠层） |
| 例 | atk_up_strong → atk×**1.75** | 3 刻 → ×1.30 ❌ |
| 例 | matk_up → matk×**1.50** | 3 刻 → ×1.30 ❌ |
| 例 | magic_resist → magic_reduce+**0.15** | 无此键 ❌ |

**根因（鱼鱼 2026-09-08 指出）**：旧引擎 BUFF_MULT 本身就是坏味道——
技能数据只有 effect 名（战吼 dict 无数值，desc 写 +30%），倍率藏在全局名字表
（`BUFF_MULT: atk_up → atk×1.30`），靠枚举键名表达强度档位
（atk_up/atk_up_small/big/strong/food_atk_up 26 键）。**名字即数值 = 配置与效果耦合**，
换配置要改表+改键名。battle2 不复制此模式。

**结论：效果数值必须从效果数据/动作配置读，引擎里一个 1.30/0.45 都不该有。**
正确形态 = 数值是 EFFECT_ACTIONS 动作的参数（mult/value/stat/op），
act_buff 执行时把 mult 快照进 buff 条目，stats 折算读条目快照——引擎不查名字表。
铁壁已是此模式（数据自带 reduce_pct=0.45）✓。

### 1.3 buffs 值语义（旧引擎自混乱，新引擎必须定稿）
旧引擎 `_decay_buff_table` 注释自认"兼容三种形态"：expire_at(dict 时刻) / turns(dict 刻) / 原始 int(剩余刻)。
历史残留，**battle2 不复制**。

### 1.4 护盾（旧引擎全带刻数，battle2 缺 expire）
- 旧引擎 shields 写点 ~28 处（技能盾/词条盾/食物盾/套装盾/武器特效盾/资源溢出盾/符文盾），**全部带 turns**（1/2/3/4/99 永久）。
- 结构：`player["shields"][来源key] = {"value": N, "expire_at": now + turns×ACT_TICK}`（v101.28d 起）；`halve` 布尔（怪护盾受伤减半）。
- 叠加规则：同源 `_add_shield` 叠厚取 max value + 刷新 expire；异源并存。
- battle2 `act_shield` 只写 `{value, halve}`，**无 expire_at → 永久盾 bug**；landing 承伤已读 value ✓。

### 1.5 控制/一次性/受击消费（battle2 全缺）
| 类型 | 旧引擎行为 | battle2 |
|---|---|---|
| 控制（stun/freeze/silence/sleep/spd_down） | 行动级消费：被控者轮到行动跳过 + 清除 | act_control 只写 buffs[tag]=turns，**无跳过逻辑** |
| 一次性攻击（next_atk_up/stealth/buff_phys_next/arcane_echo/oath_blade_next/we_oath） | 出手命中消费 + 增伤/必暴 | **无消费点** |
| 受击计数（buff_hits 防御型：格挡计数等） | _damage_actor 受击递减 | 无 |
| 元素印记（fire/ice/thunder_mark） | 触发反应清除 | 走 state ✓（on=target 已有） |
| reduce_all/reduce 减伤 | 独立计时（_left 键）+ 百分比存 buffs | act_buff value 型写了 reduce_left？部分 ✓ |

---

## 2. 目标架构（定稿）

### 2.1 actor 状态容器分工（不变 + 补全）
| 容器 | 内容 | 生命周期 | 声明表 |
|---|---|---|---|
| `actor["state"]` | 数值叠层/资源/DOT（战意/怒气/灼烧层） | 层数，cap 声明；DOT 按 interval 跳 | STATE_EFFECTS |
| `actor["buffs"]` | **时间型效果**（增益/控制/一次性/减伤/免疫） | **绝对到期时刻**；on_act/on_hit 型消费删 | BUFF_MULT（折算）+ BUFF_RULES（消费/到期） |
| `actor["shields"]` | 护盾实体（多来源并存） | `expire_at` 到期删；承伤扣 value；halve 减半 | —（字段自带） |
| `actor["debuffs"]` | 敌方持续减益（旧契约 §7：毒/灼烧/标记/流血层数） | 每刻跳（n 层） | DEBUFF_RULES（复用 STATE_EFFECTS dot 段？） |

> ⚠️ debuffs vs state 关系：旧引擎 v180 起敌方 DOT 是 `enemy["debuffs"]={key:{n,mult,...}}`；
> battle2 state_effects 已用 `on=target` + dot 段表达同一件事（burn/poison/corros 在 STATE_EFFECTS）。
> **收口决定：DOT 只走 state（on=target + dot 声明），debuffs 容器不建**——命令层展示读 state 折算即可（见 §7 决策）。

### 2.2 buffs 值语义（唯一干净定义，v2 含 mult 快照）
```python
# actor["buffs"][key] 两种合法形态：
# 形态 A（默认，时间型）：{ "expire": float 绝对到期时刻, "mult": 倍率快照 }
#     写入：actor["buffs"][key] = {"expire": battle._now + turns, "mult": 由动作参数给}
#     到期：battle._now >= 值 → 删（schedule._settle_time_effects 每推进查）
#     展示：剩余 = expire - _now；面板折算 = mult（快照，不查表）
# 形态 B（value 型，百分比/固定值）：{ "expire": 到期时刻, "v": 0.45|N, "hits": 0|N }
#     例 reduce=45% 减伤、受击计数 buff（无面板乘区，纯状态）
#     到期：同 A；hits>0 → 受击/行动消费减；展示：读 "v"
```
写入 helper（effects 动词统一调）：
```python
def buff_put(battle, actor, key, turns=None, value=None, hits=None) -> None
    # 时间型：key = {"expire": now+turns, "mult": 动作参数 mult}
    #   mult 从 EFFECT_ACTIONS 动作参数来（配置给；技能数据可覆盖——_merge_params 已支持）
    # value/hits 型：key = {"v":…, "expire": now+turns(默认∞), "hits":…}
    # 同 key 刷新规则：expire 取 max（长 buff 不缩短）；mult 取新值（动作给什么是什么）
```
> 理由：
> 1. 绝对时刻制 = 旧 v152 的最终意图（"不再有每刻-1，一切按绝对时刻到期"），干净单义
> 2. mult 快照进条目 = 数值跟着效果动作配置走，引擎折算读快照、**不查任何名字表**
>    ——引擎里不出现 1.30/0.45；换配置 = 改 EFFECT_ACTIONS 参数，引擎零改动

### 2.3 shields 字段（定稿）
```python
# actor["shields"][来源key] = {
#     "value": int,          # 剩余护盾量
#     "expire_at": float,    # 绝对到期时刻（秒）；turns=99 永久 → 大数或 None
#     "halve": bool,         # 受伤减半盾（怪盾）
# }
# 写入：act_shield 补 expire_at = battle._now + turns
# 叠加：同源刷新 value = max(value, 新盾值) 且 expire 刷新（对齐 _add_shield）
# 到期：schedule 每推进扫 shields expire_at <= now → 删
# 承伤：landing._apply_damage 已有 ✓（读 shields[sk]["value"]）
```

### 2.4 配置表（全部字段定稿，v2：数值进动作参数，BUFF_MULT 退役）
```python
# ---- data/battle_rules.py ----

# ① 名词效果 → 动词动作序列（EFFECT_ACTIONS，数值是动作参数——不是独立名字表）
#    每个动作可带 stat/op/mult|value（面板折算参数，引擎执行时快照进 buff 条目）
EFFECT_ACTIONS = {
    # ---- 属性增益（写 caster.buffs[key]，mult 快照进条目）----
    "atk_all":     [{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.30}],
    "atk_up":      [{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.30}],
    "atk_up_small":[{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.20}],
    "atk_up_big":  [{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.40}],
    "atk_up_strong":[{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.75}],
    "food_atk_up": [{"action": "buff", "key": "atk_up", "stat": "atk", "op": "mul", "mult": 1.10}],
    "matk_up":     [{"action": "buff", "key": "matk_up", "stat": "matk", "op": "mul", "mult": 1.50}],
    "def_up":      [{"action": "buff", "key": "def_up", "stat": "def", "op": "mul", "mult": 1.45}],
    "spd_up":      [{"action": "buff", "key": "spd_up", "stat": "spd", "op": "mul", "mult": 1.40}],
    "crit_up":     [{"action": "buff", "key": "crit_up", "stat": "crit", "op": "add", "mult": 0.20}],
    "mon_atk_down":[{"action": "buff", "key": "mon_atk_down", "stat": "atk", "op": "mul", "mult": 0.70}],
    "magic_resist":[{"action": "buff", "key": "magic_resist", "stat": "magic_reduce", "op": "add", "mult": 0.15}],
    # ... 旧 BUFF_MULT 26 键数值全量摊进对应 effect 动作参数（脚本化迁移，表本身退役）
    # 技能数据可覆盖 mult（_merge_params：调用方显式参数优先）→ 同名词不同技能不同强度
}

# ② buff 到期/消费规则（引擎执行；缺省 = 时间型到期）
BUFF_RULES = {
    # 控制类：轮到该 actor 行动 → 跳过行动 + 删（若 turns 已到 0）/ 持续 N 次行动
    "stun":    {"expire": "on_act"},      # 行动级消费（轮到跳过 + 删）
    "freeze":  {"expire": "on_act"},
    "silence": {"expire": "on_act", "skip_skill_only": True},  # 只禁技能不禁普攻
    "sleep":   {"expire": "on_act", "wake_on_hit": True},      # 被打醒（landing 已有 sleep 逻辑 ✓）
    "spd_down": {"expire": "time"},        # 纯减速 → 时间型到期（面板折算 spd_down 特殊）
    # 一次性攻击消费：caster 出手命中后消费 + 增伤/必暴（actions 管线查）
    "next_atk_up":    {"expire": "on_hit", "effect": "atk_mult", "val": 1.20},
    "buff_phys_next": {"expire": "on_hit", "effect": "phys_mult", "val": 1.50},
    "stealth":        {"expire": "on_hit", "effect": "guaranteed_crit"},
    "arcane_echo":    {"expire": "on_hit", "effect": "echo"},
    "oath_blade_next": {"expire": "on_hit", "effect": "atk_mult", "val": 1.15},
    "we_oath":        {"expire": "on_hit", "effect": "atk_mult", "val": 1.15},
    # 永久/整场型
    "echo_bless": {"expire": "forever"},
    "stance_guard": {"expire": "forever"},
    # value 型（无面板乘区、纯状态/特殊计时）：减伤独立计时（reduce_left 键）
    "reduce":     {"expire": "time", "value_type": True},
    "reduce_all": {"expire": "time", "value_type": True},
}

# ③ 技能 mech → state 声明（已有 STATE_EFFECTS）扩展 mech 未映射 5 键：
#    enrage/heal/interrupt/summon/thunder —— 分诊见 §6
```

> ⚠️ BUFF_STAT_KEYS（7 键旧表）一并删除——面板折算只读 buff 条目快照 mult/stat/op。
> stats._apply_buffs 逻辑变为：遍历 actor.buffs，条目含 stat/op/mult → 折算；
> 无 stat 的纯状态/控制 buff 不折算（只到期/消费）。

### 2.5 引擎改动文件清单（一次收口）
| 文件 | 改动 |
|---|---|
| `battle2/effects.py` | act_buff 动作参数 stat/op/mult → buff 条目快照；act_control 走 on_act 规则；act_shield 补 expire_at；新增 `buff_put` helper |
| `battle2/config.py` | 删 BUFF_STAT_KEYS 挂载/接口；BUFF_RULES 挂载 + getter |
| `battle2/schedule.py` | `_settle_time_effects` 扩展：buffs 到期扫（time/on_act 判断）、shields 到期扫、DOT interval；advance 前查 on_act 控制 |
| `battle2/actions.py` | 攻击管线：出手前/命中后查 caster on_hit 一次性 buff → 消费 + 效果；命中后查受击方 value_type hits |
| `battle2/stats.py` | `_apply_buffs` 读 buff 条目快照（stat/op/mult），删"×(1+n×0.10)"叠层逻辑与 BUFF_STAT_KEYS 查表 |
| `battle2/landing.py` | sleep 唤醒已有 ✓；受击 hits 计数消费（可选，N7.2） |
| `game/data/battle_rules.py` | EFFECT_ACTIONS 动作参数补数值（26 键数值摊进）；BUFF_RULES 全表；删 BUFF_STAT_KEYS |
| `tools/cov_*.py` | 覆盖率门禁照跑 |

---

## 3. 执行顺序（每步可验证）

### N7.1 buff 数值动作参数化 + 面板快照折算（effects.py + stats.py + rules）
1. **全新填 EFFECT_ACTIONS 配置**：每个 buff 名词动作补 stat/op/mult 参数——
   数值以策划案/技能 desc 为准（如战吼 desc「攻击+30%」→ mult=1.30），
   旧 battle_config.BUFF_MULT 26 键仅作对照（导出对照表，两边不一致时以策划案为准并记录）
2. effects.act_buff 读动作参数 stat/op/mult → buff 条目 `{expire, stat, op, mult}` 快照
3. stats._apply_buffs 读条目快照折算：mul → st[stat]×=mult；add → st[stat]+=mult
4. BUFF_STAT_KEYS 旧表不再使用（v2 配置不含它；旧表留在旧配置不动）
5. 对拍：裸装 + 各 buff 键 → 旧引擎 vs battle2 面板（差异=配置更新点，逐条裁决）
6. 测试固化（test_battle_n3_effects 扩展）

### N7.2 buffs 绝对到期 + 到期扫（effects.py + schedule.py）
1. effects 写入改 helper；控制 act_control 走 on_act 规则
2. schedule._settle_time_effects：每推进扫全场 actor buffs/shields 到期删
3. advance 决策前查 on_act 控制 → 跳过 + 删 + 日志（"🌀 X 被眩晕，无法行动"）
4. 测试：挂 3 刻 buff → 推 3 刻消失；盾 2 刻 → 2 刻消失；stun 挂上 → 轮到跳过

### N7.3 一次性 on_hit 消费（actions.py）
1. 攻击管线命中段查 caster on_hit 键 → 应用效果（乘区/必暴）+ 删
2. 对拍：潜行/next_atk_up/蓄力 旧引擎同输入行为
3. 测试固化

### N7.4 DOT interval（schedule.py + STATE_EFFECTS）
1. dot 声明加 interval（缺省 1 刻 = 每次推进结算；>1 按累计时刻）
2. 对拍 DOT 总跳数与旧引擎一致
3. 测试固化

### N7.5 效果名词收敛分诊（大表 → 分批）
1. 跑分诊脚本：187 effect + 13 mech 分类输出
   - A 战斗效果 → 需进 EFFECT_ACTIONS/STATE_EFFECTS（本期做）
   - B 生活/非战斗 effect → 排除（open_chest/bag_expand/loot/bait 等）
   - C 词条/武器/被动独有 → 属上层（不进引擎，上层 proc 调动词）
2. 分批实施 + 每批对拍/测试（参考 P2E 机械替换纪律，小步 commit）
3. 死表清理：EFFECT_ACTIONS 无用条目删

### N7.6 护盾 expire 收口（effects.py act_shield）
（并入 N7.2；单独列出强调）——补 expire_at + 同源叠厚规则

---

## 8. 排期（鱼鱼 2026-09-08 拍板：先收敛效果系统，再继续命令层）

```
当前 ──► N7 效果系统收口（引擎内，对拍 + 测试 + 覆盖率门禁逐批验证）
           N7.1 buff 数值动作参数化 + 面板快照折算
           N7.2 buffs 绝对到期 + shields expire_at + 控制 on_act 行动级消费
           N7.3 一次性 on_hit 出手消费（actions.py）
           N7.4 DOT interval（schedule.py + STATE_EFFECTS）
           N7.5 187 effect 名词分诊收敛（A 战斗→规则 / B 生活→排除 / C 词条→上层）
           ─► 验收：效果全通对拍 + 全套测试绿 + numeric 门禁 + 覆盖门禁
      ──► N5b-4 命令层切换（展示辅助按 N7 定稿语义一次写对，不返工）
      ──► N6 删旧 battle.py + 全量回归
```

**为什么效果系统先于命令层**：
1. N5b-4 展示辅助（_status_line 折算 buff 剩余刻/盾刻数/资源）依赖 buffs/shields
   值语义定稿——效果不定稿，展示改两遍，命令层是返工重灾区
2. N1-N5a 对拍全过是"无效果场景"假象（裸普攻/裸技能）；带 buff/盾/控制即露馅——
   效果系统是引擎正确性地基
3. 效果收敛纯引擎内、独立可验证（对拍+测试），命令层是依赖方——先做零浪费

**排期纪律**：N7 子步逐批 commit（v181.N7.X 格式），每批对拍/测试/覆盖门禁后才进下一批；
N7.5 分诊表产出后才允许回 N5b-4（展示辅助依赖分诊后 EFFECT_ACTIONS 全量）。

---

## 4. 验收（每批）
- 行为对拍：同输入（技能/词条/被动）→ 旧引擎 vs battle2 面板/buff 状态/护盾/DOT 全等
- numeric 门禁：`scripts/run_numeric_tests.py` 全绿（52 文件）
- battle2 全套测试绿（含新增）
- 覆盖率门禁：函数 0 未调用、行 ≥90.6%

---

## 5. 与 master 线关系
- 本方案全部落在 wt_ebuffs 分支（battle2 新引擎侧）
- 旧 battle.py **零改动**；master 线 P2G/P3 继续并行（效果动作统一/玩家状态容器收口）
- 合并 master 时：battle2 引擎成熟后再 N6 删旧 battle.py

---

## 6. 待分诊清单（187 effect 名词，需跑脚本后补全明细）
占位：N7.5 第一步产出 `docs/archive/EFFECT_TRIAGE_v181P4.md` 全量分类表（A/B/C 三档 + 每档落地位置）。

---

## 7. 架构决策记录（鱼鱼拍板/本方案定）
| # | 决策 | 说明 |
|---|---|---|
| D1 | buffs 用绝对到期时刻（float），不做三形态兼容 | 干净单义；旧 v152 混乱不复制 |
| D2 | 面板折算用固定倍率表（BUFF_MULT 26 键），不用叠层×10% | 旧引擎语义即固定倍率 |
| D3 | 护盾必须带 expire_at（turns 1~99/永久），同源叠厚 | 修 battle2 永久盾 bug |
| D4 | 控制 on_act 行动级消费；一次性 on_hit 出手消费 | 消费语义入 BUFF_RULES 表 |
| D5 | DOT 只走 state（on=target+dot 声明），不建 debuffs 容器 | 旧契约 §7 语义由展示折算呈现 |
| D6 | 非战斗 effect（生活/开箱/诱饵）不进效果系统 | 分诊排除 |
