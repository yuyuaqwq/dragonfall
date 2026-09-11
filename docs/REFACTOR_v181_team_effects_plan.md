# v181 团队/护盾/减伤类 effect 名词实装方案（2026-09-11）

> **状态：待拍板**（本文是字段级施工图，不是已落地记录）
> **为什么单独出方案**：这 20 个 `effect=` 名词是**玩家可见的静默 no-op**（技能 desc 承诺的效果
> 一个字都不生效），但它们的实装会**整体抬高全队承伤能力**（护盾/减伤/易伤都是生存乘区）
> → 按铁律必须过 `scripts/run_numeric_tests.py` 门禁 + 峰值红线，且属数值维度扩张，
> 需鱼鱼拍板口径后再动手。

---

## 一、根因（已取证，非推断）

引擎执行链是 `apply_effects` → `resolve_actions(etype)` → `ACTION_HANDLERS[action]`：

```python
# saintess_engine/battle/effects.py:162-164
actions = resolve_actions(etype)
if not actions and etype not in ACTION_HANDLERS:
    continue      # 未知名词/动词：跳过（引擎容错）
```

`resolve_actions` 查的是 `game/data/battle_rules.py::EFFECT_ACTIONS`。**技能 `effect=` 里的名字
不在 EFFECT_ACTIONS、也不是引擎动词 → 返回 `[]` → 整条效果静默跳过**（连日志都没有）。
实测：`game/data/skills.py` 里有 **20 个**这样的名字，覆盖 **26 条技能**（含 4 个 90+ 级大招）。

核对脚本（可复现）；`EFFECT_ACTIONS` 用 `ast` 解析后与 `skills.py` 的 `effect=` 取值求差集：

```
差集 = {disengage_dodge, shield_all, shield_block, taunt, protect, reduce_all,
        shield_all_reduce, arcane_shield, element_switch, arcane_matrix, arcane_field,
        star_lock, dodge_reduce_all, hunt_team_dmg, vuln, stealth_cc, block_reflect,
        reduce_shield_all, all_stat_cc, def_up}
```

> ✅ **`def_up` 已修**（2026-09-11 当日）：它是最特殊的一个——`EFFECT_RULES["def_up"]` 面板
> 早就声明了（def ×1.45），只是 `EFFECT_ACTIONS` **漏了那一行映射**。已补
> `"def_up": [{"action": "apply", "key": "def_up"}]`（磐石之躯 lv10 恢复生效）。
> 剩下 **19 个**是本方案的对象。

另外 4 个未声明名词（`game/data/monster_mods.py` / `instances.py`）：
`freeze_self`（boss_script 已按剧本效果实现）/ `mortal_wound` / `stacks_clear` / `vulnerable`
—— 属**怪物侧**数据，本方案不覆盖，单独登记（见 §六）。

---

## 二、逐技能清单（26 条）

| # | `effect=` | 技能 | lv | 职业线 | desc 承诺的数值 | 机制组 |
|---|---|---|---|---|---|---|
| 1 | `disengage_dodge` | 烟雾弹 | 20 | 游侠·风行者线 | 脱战 + 全队闪避 +25% / 8 刻 | C |
| 2 | `shield_all` | 坚盾壁垒 | 44 | 战士·盾卫士 | 花 5 战意：全队护盾（每层 6% 施法者生命上限）/ 12 刻 | A |
| 3 | `shield_all` | 圣盾 | 62 | 战士·盾卫士 | 全队战意之盾（每层 +6%，不消耗）/ 12 刻 | A |
| 4 | `shield_all` | 气力守御 | 80 | 武僧·磐石行者 | 全队护盾（磐核数 ×4% 施法者最大生命）/ 12 刻 | A |
| 5 | `shield_block` | 铁壁·誓 | 54 | 战士·盾卫士 | 自身护盾 + 格挡率 +30% / 10 刻 | A+G |
| 6 | `shield_all_reduce` | 守护圣域 | 97 | 战士·盾卫士 | 花满 10 战意：全队护盾 + 减伤 30% / 12 刻 | A+B |
| 7 | `reduce_shield_all` | 大地守护 | 93 | 武僧·磐石行者 | 全队减伤 30–50%（按磐核数）+ 护盾 / 12 刻 | A+B |
| 8 | `reduce_all` | 战吼·守 | 88 | 战士·盾卫士 | 全队减伤 20% / 10 刻 + 自身 2 战意 | B |
| 9 | `reduce_all` | 不破壁垒 | 93 | 战士·盾卫士 | 全队减伤 30% / 12 刻，战意 ≥8 → 50%（不消耗） | B |
| 10 | `reduce_all` | 死歌·悼 | 50 | 牧师·死灵祭司 | 死歌光环：全队减伤 15% / 12 刻 | B |
| 11 | `reduce_all` | 圣光庇护 | 74 | 牧师·神谕者 | 全队减伤 20% + 持续回血 / 10 刻 | B |
| 12 | `dodge_reduce_all` | （林语者 lv88） | 88 | 游侠·林语者 | 全队闪避 +15%、减伤 10% / 12 刻 | B+C |
| 13 | `arcane_matrix` | 奥术矩阵 | 85 | 法师·奥术线 | 全队奥术/魔法伤害 +20% / 12 刻 | D |
| 14 | `all_stat_cc` | 永恒赞歌 | 98 | 诗人·咏叹线 | 全队全属性 +30% + 免疫控制 / 8 刻 | D+E |
| 15 | `hunt_team_dmg` | 猎手本能 | 90 | 游侠·林语者 | 全队对猎印目标增伤 +30% / 12 刻 | D+F |
| 16 | `vuln` | 死亡标记 | 58 | 刺客·毒刃线 | 目标受到伤害 +25% / 8 刻 | F |
| 17 | `taunt` | 嘲讽 | 58 | 战士·盾卫士 | 强制敌人攻击自己 / 8 刻（数据：仇恨×3 + 锁 3 刻） | F |
| 18 | `protect` | 誓约之盾 | 85 | 战士·盾卫士 | 为队友挡刀并反伤 30% / 12 刻 | **G（引擎新能力）** |
| 19 | `protect` | 守护誓言 | 90 | 战士·盾卫士 | 为队友挡刀并反伤 50% / 12 刻 | **G** |
| 20 | `block_reflect` | 铁山靠 | 58 | 武僧 | 格挡 1 次攻击并反伤 40% / 8 刻 | G |
| 21 | `star_lock` | 星轨锁定 | 54 | 游侠·风行者 | 锁定目标无视站位，全队对其伤害 +12% / 12 刻 | F+D |
| 22 | `stealth_cc` | 影遁 | 85 | 刺客·影舞者 | 强制潜行 + 免疫控制 / 6 刻 | E |
| 23 | `element_switch` | 元素流转 | 62 | 法师·元素线 | 切换当前主系（影响下次挂印系别） | H |
| 24 | `arcane_shield` | 相位偏折 | 58 | 法师·奥术线 | 消耗全部充能，每层转 8% 魔攻护盾 | A |
| 25 | `arcane_field` | 奥术力场 | 88 | 法师·奥术线 | 消耗 2 充能，选护盾 **或** 下次奥术技 ×1.3 | A+I（需选择态） |
| 26 | `def_up` | 磐石之躯 | 10 | 通用 | 防御 +45% / 2 刻 | ✅ 已修 |

---

## 三、共享机制与落点（8 组）

落点全部在**内容侧**（`game/services/*` 新增装配层模块 + `game/data/battle_rules.py` 映射），
除注明者外**引擎零改动**——理由：引擎已有护盾/乘区事件/触发器/刻数机制，缺的是"团队面幅"这层内容编排。

| 组 | 机制 | 落点 | 引擎现状 |
|---|---|---|---|
| **A** | 护盾（按 max_hp%/资源层数，带刻数、同源叠厚） | `act_shield`（引擎已有） + 新增内容动作 `team_shield` 做面幅 | ✅ `shields[key]={value,expire_at,halve}` 齐备（N7.2） |
| **B** | 全队减伤（带刻数） | 新增内容动作 `team_taken_reduce`：给同侧 actor 挂 `taken_calc` 触发器（复用 `passive_taken_reduce` 的 `ctx.mult *= (1-reduce)` 口径） | ✅ `taken_calc` 事件 + `_fire_ctx["mult"]` 齐备 |
| **C** | 全队闪避 | `apply` + `EFFECT_RULES` 面板 `dodge`（op=add） | ✅ 面板维度已有 `dodge_up` 先例 |
| **D** | 全队面板/伤害类型乘区 | 面板→`apply` 现成；「奥术/魔法伤害 +N%」走 `dmg_calc` 触发器按 `kind` 过滤（复用 `dmg_mult_cond` / `we_dmg_mult_cond` 模式） | ✅ 乘区事件齐备 |
| **E** | 免疫控制 / 潜行 | 潜行：`EFFECT_ACTIONS["stealth"]` 已有；免疫控制需**先查控制落地处是否读免疫 flag**（`_selfcheck` §4-B2 记录：`landing.py` 硬编码 `sleep`/`death_guard` 等固定键）→ 若引擎不读，**需引擎加"控制免疫查询点"（T2）** | ⚠️ 部分缺 |
| **F** | 目标易伤 / 仇恨锁定 | 易伤：写 `target["_dmg_taken_mult"]`（`landing` 已读 >1）+ 刻数过期（`boss_script` 有自管过期先例，抽成内容动作 `timed_vuln`）<br>仇恨：`hate_taunt_mult`/`hate_lock_turns` 数据已在，引擎有 `target_picker` 注入点 → **命令层仇恨选择器接线**（不含引擎改动） | ✅ 机制齐备，属接线 |
| **G** | 挡刀 / 格挡反伤 | 格挡 1 次：`taken_calc` 一次性 flag（有 `on_hit_consume` 一次性先例）+ 反伤复用 `we_reflect` / `passive_reflect_bar` 口径<br>**挡刀（伤害转移）= 引擎无通道** → 需新能力（或 `on_taken` 里改判承伤对象） | ❌ 挡刀需引擎 |
| **H** | 主元素系切换 | 内容字段 + 挂印系别读取点 | ⚠️ 需先侦察"主系"数据现状 |
| **I** | 二选一选择态（奥术力场） | 需要"施法时选择"的交互 → **命令层 UI 改动**（非引擎） | ⚠️ 交互层 |

---

## 四、过期（刻数）统一设计

所有带刻数的效果**一律挂 `time_advance` 自清触发器**，不新造计时器：

```
actor.triggers["time_advance"] += [{"action": "team_effect_expire", "key": <效果键>}]
# 效果条目自带 expire_at = now + N（引擎 clock 事件广播 {dt, now}）
```

这与 `game/services/battle_bar_procs.py::_ensure_tick`（破绽条按刻结算 + 免疫窗口绝对时刻）
**同一套写法**，好处：不依赖宿主动作节奏、存档可续、跨消息不丢。

---

## 五、门禁与平衡影响（为什么必须先拍板）

- 这批效果**整体抬高玩家生存**（护盾 + 减伤 + 闪避），会改变副本难度曲线 →
  必须过 `scripts/run_numeric_tests.py` + `tests/test_numeric_burst_redline.py`（峰值红线）。
- 建议同批新增门禁 `tests/test_v181_team_effects.py`：逐效果断言
  （装配齐 / 面幅正确（只作用于同侧 / 不重复挂）/ 刻数到期自动清 / 数值口径取 desc 字段）。
- **口径需鱼鱼拍板的两点**：
  1. 「全队减伤」是否**乘算叠加**（战士 30% + 牧师 20% → ×0.7×0.8 = 44%）还是**取最高**？
     （乘算 = 组队收益爆炸，取最高 = 单刷收益不变。**建议取最高**，与旧引擎 `reduce_all` 口径对齐前需核。）
  2. 「护盾按施法者生命上限」在多人副本里是否按**目标自身生命**换算上限（防止奶盾给脆皮超模）？

---

## 六、不在本方案内的相关项（单独登记）

| 项 | 现状 | 去向 |
|---|---|---|
| `freeze_self`（instances.py） | boss_script 已按剧本效果实现（`effects["boss_frozen"] mode=skip`） | 数据侧改用声明式写法或标注等价 |
| `mortal_wound` / `stacks_clear` / `vulnerable`（monster_mods / instances） | 零映射，怪物侧静默 no-op | 并入本方案批（怪物侧） |
| `on_threshold`（`battle_rules.py:27` `{10:{"form":"fury"}}`） | 引擎无消费方；狂暴由内容层 `class_mech_proc` 的 `zhan_yi_fury` 走技能路径实现 | 删映射 or 接线（见 `_selfcheck` §1.1） |
| `period.dmg_type`（corros「真伤 DOT」） | 无消费方；DOT 落地统一 `deal_damage(..., dmg_kind="")` | 二选一：接 `dmg_kind` 或改注释 |
| `debuff_scale`（hunt_mark/soul_mark/curse 每层承伤 +N%） | 无消费方 → 三个印记的「每层承伤」承诺不生效 | 并入本方案批（同属乘区） |
| `finisher.crit_at`（`battle_rules.py:531`） | 装配器不读，注释自承「声明先行」 | 接线 or 删声明 |
| `def_up` | ✅ 已修（2026-09-11） | — |
