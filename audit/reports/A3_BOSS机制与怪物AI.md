# A3 BOSS机制与怪物AI — 子审计报告

## 0. 审计范围（文件清单 / 行数 / 未覆盖原因）

| 文件 | 行数 | 说明 |
|---|---|---|
| design/new_world/参考/BOSS战编排设计.md | 574 | 设计文档，全读 |
| design/new_world/参考/怪物行动AI_博弈体验设计.md | 428 | 设计文档，全读 |
| design/new_world/参考/怪物行动AI_规则完整性.md | 736 | 设计文档，按章节/关键字浏览 |
| design/new_world/参考/怪物行动AI设计定稿.md | 299 | 设计文档，全读 |
| tests/test_v83_boss_mech.py | 141 | 测试，全读 |
| tests/test_v116_boss_trigger_phase.py | 196 | 关联测试（phase 剧本化），全读 |
| game/core/wild.py | 304 | 实为「野外 NPC 判定引擎」，与 BOSS 机制无直接关系（grep 证），纳入核对 |
| game/core/monsters.py | 3 | 仅 3 行占位，无实现 |
| game/data/monsters.py | 1303 | MONSTER_SKILLS，抽查 |
| game/core/battle_mech.py | 723 | **BOSS 机制实际实现**，全读 |
| game/battle.py | 3585 | 抽取 _boss_dmg_filter/_boss_mech/_boss_cfg/_enemy_stats/_enemy_turn/to_state 精读 |
| game/data/monster_mods.py | 240 | 全读（BOSS mech / phases 配置） |
| game/data/instances.py | 1845 | 抽取 mech/phases 相关节，全 grep |

**路径勘误**：任务清单的 `game/core/wild.py` 与 `game/core/monsters.py` 与 BOSS 机制无关——本切面 BOSS 机制的真实归属在 `game/core/battle_mech.py`（v98.4 数据化注册表）+ `game/battle.py`，两条路径已在报告各发现处标注。

**未覆盖**：未运行任何 Python/测试（只读审计铁律）；战斗主流程细分（伤害/暴击/援军）不在本切面，仅核对与本切面交界的 4 个方法。

---

## 1. S级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| S1 | game/core/battle_mech.py:475-485 写入 set；game/battle.py:267 整 enemy 进 to_state；game/store/battle_state.py:42 json.dumps(state) | 多阶段 BOSS（mech 含 phase）进入第 2 阶段后，`_b_phase` 把 `_phase_warned` 存为 **Python set** 挂在 enemy dict 上；`to_state()` 原样带出 enemy，`save_battle` 对 state 直接 `json.dumps`（无 try/except）→ **TypeError: Object of type set is not JSON serializable**。任何对 2 阶段以上 phase BOSS 的碎片化中断保存 / 战斗结束保存都会抛异常。 | 中断续玩/结算保存崩溃（TypeError 冒泡），phase BOSS 战无法保存续档，直接破坏"碎片化"核心体验与结算。 | `_phase_warned` 改为 `list`（`e["_phase_warned"]=[pc+1]`）或序列化时转 list；并给 enemy 序列化加 set→list 兜底清洗；加 test 覆盖「phase BOSS 战斗中 save_battle」。 |

---

## 2. A级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| A1 | game/core/battle_mech.py:466-470；game/data/monster_mods.py:201-206；设计 BOSS战编排设计.md §1.1/§1.5、AI设计定稿 §6.1 | 阶段**触发阈值硬编码为 `0.5**(pc+1)`（50%/25%）**，`phases[].min`（b_moro 配 60/30、副本配 60/30）**完全不消费**——只被用作 `phases[npc-1]` 位置索引取 add_skills/script。设计与 v116 测试意图均为 P1 100-60 / P2 60-30 / P3 30-0。 | 阶段节奏与设计（60/30）偏差：BOSS 在 50%/25% 才转阶段，玩家血线预期（设计预告 63%/33%）对不上；`min` 字段是"内容定义了用不上"死数据。 | `_b_phase` 改为读 `phases[pc].min` 作为下一阶段阈值（缺省退回 0.5^n）；同步更新 v83/v116 测试断言阈值。 |
| A2 | game/data/instances.py:675 "phase,phase,phase"、:1010/1660 "phase,phase" | 用**重复 mech token 编码"多阶段"**，但 `_boss_mech` 逐 token 调用 `_b_phase`（无去重/无 break）。`phase,phase,phase` 在 boss 血量一次跌破 25% 的回合内 phase_count 1→3 连跳（幻影第 4 阶段，无 phases[n-1] 配置 → 无脚本无换招），攻击 +20%/阶段直接跳 +60%。测试只校验 mech 名合法、不校验重复。 | 多阶段 BOSS 阶段计数/强化错乱：某阶段被整段跳过、出现未配置的"第 4 阶段"、换招表不按设计追加。 | 数据改用单一 `phase` + `phases` 数组承载多阶段；`_boss_mech` 对同一 handler 去重；校验器拦截重复 mech token。 |
| A3 | game/core/battle_mech.py:133-152（_m_stun/_m_freeze/_m_silence 无条件作用于敌）；game/data/skills.py:3020-3021（时停领域 mech_chance 1.0）；设计 规则完整性 §三3.4/BOSS编排 §五 霸体段 | **BOSS 无任何控制免疫/霸体段**：玩家眩晕/冻结/沉默直接写 e_buffs，`_enemy_turn` 无条件跳过 Boss 回合；"时停领域"100% 眩晕可稳定连控。设计明确应配 BOSS 霸体段（finisher 免疫打断、霸体蓄力）防无脑控。 | BOSS 战可被眩晕/冻结锁死（"时停流"每 CD 一轮稳定晕），挑战性与悬念被掏空（A2 交叉核对项：BOSS 免疫控制=无实现）。 | 给 BOSS 加"霸体/控制抗性"（如 is_boss 高等级免疫、阶段硬直免疫/减半）；或给怪物控制技能加 BOSS 减抗；落地 armor 字段。 |
| A4 | game/battle.py:2484-2501；grep 证实 chains/zone_change/action_count/teach_map 无消费 | 设计核心「连招链（火球→尾扫锚点）」「换区追击」「多行动（P3 双行动）」「教学映射（精英镜像）」**全部未实现**：`_enemy_turn` 只有 "30% 随机技能(choice 均匀)/70% 普攻"、`_boss_cfg` 只解析 chains 字段但无任何消费；zone_change/action_count/teach_map 在代码库零引用。 | 设计中的可读性/压迫感/空间化换区等核心体验整体缺失，BOSS 战="值堆伤害随机循环"，与"读招博弈/长盘编排"总设计目标重大偏差。 | 属"设计先行、实现未跟进"还是"故意收敛"待组长裁决（见第 7 节）；若需实现，优先连招链 + 阶段换招表 + 多行动。 |

---

## 3. B级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| B1 | game/battle.py:2701-2719 | `_enemy_stats` 中 enrage ×1.35、phase ×(1+0.2·n)、stacks ×(1+0.08·n)、player_low ×1.25、pv_broken ×1.30 与 e_buffs(mon_atk_up) 全乘式叠加且无总帽。极端（phase3+stacks5+双触发+mon_atk_up）atk 可达约 4-5× 基础，叠加副本 hp_mult×3/atk_mult×2.7 会瞬秒玩家。 | 高难端数值暴增无封顶，个别满配置 BOSS 可能一击去世（"极限装备也扛不住"）。 | 加敌方攻击强化总帽（如 ≤3.0×）或在 `_enemy_stats` 末尾 clamp。 |
| B2 | game/core/battle_mech.py:470-479 | 阶段阈值预告窗口 `nxt<=ratio<=nxt+0.03`（3%），且只在触发判定同一处读数；高伤回合可能从 28% 一笔打到 <25% 直接转段，预告形同虚设（设计§1.3要求≥2回合窗口）。 | 血线挫败保护名存实亡，预告常被跳过。 | 预告改为"持续 N 回合的短预告状态"而非单回合命中即发。 |
| B3 | game/core/battle_mech.py:480-502 + _enemy_stats | `_b_phase` 每次进入新阶段先 `logs.append("进入第 N 阶段！力量再度攀升！")` 又被 phases.script 追加第二条文案，且 script 缺失时兜底"鳞片泛起暗红…狂暴"永远输出——多阶段文案重复/语义冲突（第 2 阶段就报"狂暴"字样）。 | 文案冗余、易误导"刚狂暴"。 | 二处文案合并为一处；script 缺席时不输出兜底狂暴文案。 |
| B4 | game/data/monster_mods.py:337 + grep | 野外 BOSS 的 mech 仅从 MONSTER_MODS（build_monster drops.py:337）读取，大量"role=boss"的野外怪若未登记 mod 则完全无 mech；机制覆盖靠人工登记，缺统一兜底。 | 野外 BOSS 机制覆盖参差，部分高难野外 BOSS"裸奔"无机制。 | 提供 Boss 模板级 mech 兜底 + 校验器告警未配 mech 的 boss。 |

---

## 4. C级

| # | 位置(文件:行) | 描述 | 建议 |
|---|---|---|---|
| C1 | game/battle.py:2351-2367 | 破盾那一击仍然减半（dmg=real）——"最后一击破盾但仍半伤"逻辑可接受但可再优化（破盾一击通常应全额）。 | 明确设计取舍并加注释。 |
| C2 | game/core/battle_mech.py:427-436 | `summon` 固定 r%3==0 召唤，与 stacks 固定 r%2 叠层均以 total round 为轴，会对齐后某回合同时爆发。 | 可用阶段/随机错峰避免"齐爆"。 |
| C3 | game/battle.py:2355-2359 | 真伤走护盾吸收分支但 `dmg_type=="true"` 时无独立 break，与物理同代码路径只差 -50% 分支——可读性略差。 | 抽独立子函数。 |
| C4 | game/core/battle_mech.py:554-585 | player_low 首触发与原重复触发的文案两套（"本回合攻击大幅提升" vs "狞笑着扑来"），cooldown 分支写两遍。 | 合并触发路径、去重文案。 |
| C5 | game/core/battle_mech.py:83/95 | `_enemy_stats` 的 stacks 每层 +8% 与 v83 测试一致，但设计未给 stacks 数值上限的文案提示（层数/效果不透明）。 | 图鉴/日志补"叠层数值"说明。 |

---

## 5. 亮点（≥2 条）

1. **数据化注册表重构（battle_mech.py BOSS_MECHS/MECH_EFFECTS/MON_CTRL_EFFECTS）**：把 game/battle.py 的 if-elif 硬编码抽成带 `register` 装饰器、签名统一 `(battle, logs, e, r)` 的注册表，新增机制挂 5 行即可，扩展性与可维护性优秀（**事实**）。
2. **反伤保底 1HP 设计（battle.py:2373-2375）**：reflect 对玩家写 `max(1, hp-rb)`，明确"反伤是代价不是处决"，避免残血被反弹补刀——是刻意的数值防挫败取舍，注释完整（**事实**）。
3. **多机制逗号组合 + 数据兜底（_boss_mech / _boss_cfg）**：`enrage,summon` 等组合由逗号解析、缺省返回默认配置，稳健降级，测试 test_v83 覆盖组合场景（**事实**）。
4. **v116.1 条件反制（phase_open/player_low/pv_broken）带 once/cooldown 防刷屏**：`_open_played/_low_hp_cd/_pv_broken_cd` 计数器 + 阶段演出回合 `_phase_skip_act` 呼吸点，是把"转换=剧情时刻/呼吸点"落地的努力（**事实**）。

---

## 6. 相邻切面核对结论（交叉核对矩阵 4.1）

| 核对项 | 结论（事实/推断） |
|---|---|
| A2↔A3：BOSS 技能是否走同一套状态系统 | **是**：BOSS 用技能走 `_enemy_turn` 的 MONSTER_SKILLS/MON_BUFF_EFFECTS/MON_CTRL_EFFECTS 同一套状态机（e_buffs/p_buffs/freeze/stun/silence 与玩家侧共用同键名，battle.py:233-239 e_buffs 即 enemy["buffs"]）。推论：不引入并行状态系统。（事实） |
| A2↔A3：BOSS 免疫控制是否有实现 | **无实现**：玩家眩晕/冻结/沉默直接写 e_buffs 且 `_enemy_turn` 无条件跳过 Boss 回合，无 armor/霸体/控制抗性分支（battle_mech.py:133-152、battle.py:2463-2472）。此即本报告 A3，需提示 A2。【处理建议：经组长转达，不直接阻塞】 |
| I1↔A3：副本 BOSS 是否复用本切面 BOSS 机制 | **是**：副本 BOSS 由 instances.py 提供 mech/phases，经 `_boss_mech`/`_boss_cfg` 复用同一 battle_mech 注册表；爪牙 `_scale_enemy_copy`/`_summon_minions` mech="" 防逐单位重复触发（instance.py:498）。副本 BOSS 与本切面机制同源。（事实） |
| I1↔A3：副本阶段阈值 | 副本 phases min 字段同样不被触发阈值消费（同 A1），副本 BOSS 阶段节奏同样与设计 60/30 偏差。（事实） |

---

## 7. 待组长裁决

1. **A4 归因**：BOSS 编排核心（连招链 / 换区 / 多行动 / 教学映射）全部未实现。请裁决是"漏实现"(需排期补齐) 还是"设计先行、v1 故意收敛为 7 机制 + 条件反制子集"。若收敛，建议在 A3 设计文档标注"以 7 机制实现为准"避免审计误判。
2. **A2 的 `phase,phase` / `phase,phase,phase` 数据编码**：是历史遗留的"多阶段声明"hack 还是无意义笔误？两种情形该玩法都需改为单一 `phase` + phases 数组。
3. **A1 阶段阈值口径**：以设计 60/30/0 为准还是维持实现 50/25/0？二者选一并统一文档/测试/数据三段。
4. **BOSS 控制免疫优先级**：请求裁决是否在 v1 引入轻量 BOSS 控制削减（避免时停流锁死），还是视高难端玩家水平接受。
5. **设计方案文档与实现差异的审计口径**：design/参考/*.md 均为 2026-08-15 的"设计定稿"，但无到实现的追溯说明；建议补一页"实现落地状态表"减少跨切面误报。

---

## 8. 切面健康度（0-100）+ 一句话评语

**68 / 100**

评语：BOSS 7 机制 + 条件反制子集实现良好且数据化清晰，但存在一个会崩存档的 set 序列化 S 级缺陷、阶段阈值与设计 60/30 脱节、以及"连招链/换区/多行动"等编排核心整块未落地——机制骨架在，编排灵魂缺，且有一段必须先修的崩溃点。
