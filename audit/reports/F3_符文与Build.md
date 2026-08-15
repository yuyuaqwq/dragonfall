# F3 符文与Build — 子审计报告

## 0. 审计范围（文件清单 / 行数 / 未覆盖原因）

| 文件 | 行数 | 说明 |
|---|---|---|
| `game/core/runes.py` | 52 | rune_value / rune_conflict / rune_item 外层逻辑 |
| `game/data/runes.py` | 276 | RUNES 16 枚 / RUNE_CONFLICTS / RUNE_DROP / RUNE_LEVEL_ROMAN |
| `game/data/builds.py` | 163 | BUILDS：6 基础(每 3 套) + 6 隐藏(每 1 套) 流派方案 |
| `game/data/summons.py` | 39 | SUMMONS 三模板（骷髅/藤蔓/古树） |
| `game/core/formation.py` | 164 | rank/reach 站位纯函数（阵型工具） |
| `tests/test_v107_summon.py` | 207 | 召唤系统单测 |

已交叉核对（非负责清单，仅作链路验证）：`game/battle.py`（符文/召唤消费端：_apply_enchant_attack / _summon_entity / _summons_act / _summon_evolve / _summon_block_check）、`game/commands/combat.py`（掉落/收益）、`game/commands/economy.py`（附魔刻印/冲突）、`game/commands/player.py`（build_view）、`game/core/item_templates.py`（符文匣）、`game/data/skills.py`（技能字段）、`design/new_world/09/12/27/19`（设计文档）。
未运行游戏本体/脚本/写库（只读静态审计）。

## 1. S级

| # | 位置 | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| — | — | 未发现会导致崩溃/数据损坏/卡死/刷资源/规则性失效的 S 级问题。判定依据：rune_value/rune_item 均有兜底（get 默认 / except 包 desc 格式化）；rune_conflict 对等效应答 False 避免误伤；_summon_entity 有 try/except 与 limit 上限；battle 调用点参数均与返回结构匹配。 | — | — |

## 2. A级

| # | 位置 | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| — | — | 未发现明显体验破坏/重大数值失衡/文档与实现重大偏差级的 A 问题。符文-技能加成链路（F3↔F2）逐条核对通过：magic_break 仅对 kind==魔法(magic)与magic_break技能路径生效、brutal 叠 crit_dmg、chain 概率/倍率解包正确。 | — | — |

## 3. B级

| # | 位置 | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| B1 | `game/commands/player.py:1427` | 流派展示硬编码 `已学 {learned_cnt}/6`，但隐藏线 5 套 build 只有 5 枚技能（暗影流/暗杀流/武僧流，见 `builds.py:143-162` 各 5 项）。玩家最多只能学满 5/6，展示 `X/6` 误导。 | UI 计数显示错误，易让玩家误以为少学了技能 | 改为 `/{len(info['skills'])}` |
| B2 | `game/battle.py:3305-3333` `_summon_evolve` | v113 删除狼三形态（SUMMONS 无 wolf_cub/wolf_king/shadow_wolf），该方法 `SUMMONS.get(target)` 恒 None 返回 False；当前无任何技能再带 `summon_evolve` 字段（skills.py 已 0 引用）。 | 遗留死代码，一旦误触发静默失败，误导后续维护 | 删除该方法及 battle.py:1888-1889 挂点 |
| B3 | `game/battle.py:3524 / 3526 / 3528` | `barrier` 壁垒符文在 `_damage_player` 内用 player 当前 max_hp×pct 生成护盾，`pct` 由 `rune_value("barrier",lvl)` 返回 `[prob,pct]` 二元素列表解包，数据正确但依赖隐性契约（列表顺序=prob,pct），链式 1468 同理。 | 若日后把某符文 lvl 从 list 改成单值会静默解包错 | 对两处列表解包加结构断言/注释 |
| B4 | `game/data/runes.py:247-251` + `battle.py` | 符文数值绕过 `PCT_CAPS`（constants.py:73-80）加权上限：疾风/铁壁/聚能等按 lvl 直接乘算叠加在聚合属性上，不参与面板 cap。能力虽可说是独立乘区，但设计文档未说明符文豁免封顶。 | 极满配置下速度/减耗可能超上限预期 | 设计文档补充符文封顶规则或纳入 cap |

## 4. C级

| # | 位置 | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| C1 | `game/core/runes.py:9-12` | `rune_value` 每调用线性遍历 RUNES（17 项），battle 攻击结算内每回合调多次（_apply_enchant_attack 最高 ~8 次） | 微性能开销，可忽略 | 构建 effect→数值 预索引 dict |
| C2 | `tests/test_v107_summon.py:8 / 106-125` | docstring 仍提「真伤召唤物（影狼）」、测试用 synthetic_true 手动构造真伤段；兽群模板已删，文档/测试注释名实不符 | 测试仍有效（逻辑未坏），仅注记过时 | 更新 docstring 移除「影狼」字样 |
| C3 | `game/core/formation.py:89` | `select_aoe_targets` 分支 `scope in ("front","rank")`，`"rank"` 不在文档（27 章）列出的 scope 枚举内，文件头 74 行也仅写 front/all/rankN | 语义冗余，无用户路径触发 | 删除或文档补注 |
| C4 | `game/battle.py:1889` | 血魔法 `hp_cost` 分支在 `summon_evolve` 之后、`kind` 分支前，先扣血再结算，逻辑顺序合理但依赖注释说明（行 1890 起） | 仅可读性 | 保留 |

## 5. 亮点（≥2 条）

1. **符文获取闭环完整且可控**：普通怪只掉蓝（combat.py:1904）、精英/Boss 分层加权（×3 + 品质分层，commbat.py:1897-1917），配套符文匣（item_templates.py:546-557 蓝+紫 40/60 加权）与附魔刻印等级门槛（economy.py:2346-2353），防止"低级怪爆传说 III"失衡，反通胀设计到位。
2. **v113 召唤重构成代码/文档/数据三方高度一致**：SUMMONS 三模板与 09 章 §10.2 / 27 章 §2.6 匹配（藤蔓 limit2、古树 limit1、rank1 前排），`_summon_block_check` 按文档保留为 PVE 补充挡刀；test_v107_summon 覆盖召唤/上限/真伤/挡刀/死亡移除/序列化 9 组，并验证 wolves 已删。
3. **BUILDS 与 PLAYER_SKILLS 全量交叉核对通过**：6 基础 ×3 + 6 隐藏 ×1 全部技能名均可解析（逐名 grep skills.py 命中），描述文案与技能改版（v112.3 诗人线 / v113 林语者）同步更新，build_view 的「已学计数」能真实反映掌握度。

## 6. 相邻切面核对结论（交叉核对矩阵 4.1 相关行）

| 核对项 | 结论 | 证据 |
|---|---|---|
| F3↔F2 符文/技能加成链路 | 一致，无问题 | magic_break 仅魔法段（battle.py:1954）、brutal 进 crit_dmg（1328/2115）、chain 概率/倍率解包（1468）、barrier 解包（3524）与 data/runes.py 数值结构完全对应 |
| F3↔F2 流派技能名有效性 | 一致，无断链 | 6 基础 build 技能（裂地斩/元素爆发/追猎/治愈术/奥术弹幕/直拳 系）与隐藏线技能（龙焰吐息/时滞术/星陨/召唤骷髅/幽影袭/裂岩冲）全部在 skills.py 命中 |
| F3↔F2 召唤物与技能 `summon` 字段 | 一致 | 召唤藤蔓守卫→vine_guard、召唤古树守卫→treant、召唤骷髅→skeleton（skills.py:1744/1956/3077）与 SUMMONS key 全对上 |

共建议：请经组长转告 F2——BUILDS 技能名经本切面全量核对无断链，F2 可重点核对 skill 字段（element/summon/res_cost）消费端正交性；另 `_summon_evolve` 死代码（B2）建议与 F2 技能表清理一并处理。

## 7. 待组长裁决

1. **B4（符文豁免 PCT_CAPS）**：是否属设计意图（独立乘区）？若否需在 constants/cap 收敛层补符文封顶规则。
2. **B2（_summon_evolve 死代码）**：可直接删除，但需确认无任何外部/存档触发入口（当前 battle 内仅 1888-1889 一处挂点，skills.py 无 summon_evolve 字段，判定安全）。
3. **B1（/6 计数）**：隐藏线 5 技能 build 的展示口径，是否统一改为 `/N`。

## 8. 切面健康度（0-100）+ 一句话评语

**86 / 100** — 符文闭环、流派 skill 有效性、召唤重构三块都很扎实，仅剩 UI 计数、狼系死代码与 cap 边界等 C/B 级瑕疵待清理。
