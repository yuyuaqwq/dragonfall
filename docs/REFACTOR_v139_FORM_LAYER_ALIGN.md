# v139 形态层对齐方案（REFACTOR_v139_FORM_LAYER_ALIGN）

> 2026-09-09 深夜侦察（主 agent 直接盘点——子 agent 撞迭代上限零交付后自做）。
> 结论先行：**v139 旧形态（狂暴/focus/vent）在现网无活技能承载 → 不做等职业内容批；
> 真正的现网缺口 = melody 驻留旋律系统（基础诗人 5 技能 + 歌者分支技能已上线但 battle2 零实现 = 空转白板）——P0。**

---

## 1. 现状盘点（技能表全扫 + v139 留档对照）

### 1.1 有现网活依据的真缺口

**melody 驻留旋律系统（P0，技能已上线效果空转）**

| 技能 | 位置 | 机制字段 | desc 承诺 |
|---|---|---|---|
| 战歌 sk_zhan_ge | 基础诗人 Lv1 | mech=melody, melody=atk | 驻留：全队攻击 +12% |
| 守歌 sk_shou_ge | 基础诗人 Lv4 | mech=melody, melody=def | 驻留：全队减伤 +10% |
| 疾歌 sk_ji_ge | 基础诗人 Lv8 | mech=melody, melody=spd | 驻留：全队速度 +12% |
| 拨弦 sk_bo_xian | 基础诗人 Lv12 | mech=melody_chant, mech_val=1 | 吟唱：当前旋律强度 +1 |
| 和声 sk_he_sheng | 基础诗人 Lv28 | mech=melody_chant, mech_val=1, buff_turns 6 | 吟唱：强度 +1，效果翻倍 6 刻 |
| 激昂战歌 | 歌者·咏叹者 Lv32 | mech=melody, melody=atk | 驻留：全队攻 +20%；终章：+45% 8 刻 |
| 英雄赞歌 | 歌者·咏叹者 Lv38 | mech=melody, melody=atk_matk, finale=crit | 驻留：攻魔 +16%；终章：暴击 +25% 8 刻 |
| 二重唱 | 歌者·咏叹者 Lv44 | passive proc melody_duet add 1 | 被动：吟唱强度额外 +1 |

**实现现状**：battle2 引擎零 melody 处理（grep 无命中）；battle_conds.py melody_buff/melody_stacks 条件读旧 `battle._melody`（battle2 无此属性 → 恒 False，旧 battle_mech agent 时代残留，v169.7 TODO 未合并）；passive_procs 为 N10 退役死代码。**技能施放 = 无任何效果（纯耗蓝/进 CD）**。

**旧设计参考**：battle._melody = {name, stack(0-5), finale_ready}（MELODY_CFG max=5；battle_conds 注释：_m_melody 写 mel["kind"]=info.melody、_m_melody_chant 叠 stack）。效果数值=技能 desc（12%/10%/12%/20%/16% + 终章 45%/25%）。终章 finale_ready 触发条件待设计定（旧设计"满层/共振"语义，二重唱 add 1 强化吟唱）。

### 1.2 v139 旧形态：现网无活技能 → 不做（等职业内容批）

| v139 形态 | 现网依据 | 判定 |
|---|---|---|
| 战士 dual_form 狂暴（rage 满 10 入狂暴） | rage 死 key；现网战士技能表无"狂暴"类技能 desc/mech（v151 战意体系无狂暴承诺）；EFFECT_RULES zhan_yi on_threshold {10:{form:fury}} 是无消费死声明 | 不做——等未来战士攻线职业内容 |
| 法师 focus 元素架设/深度冥想 | 现网法师技能表无"架设"技能（奥术 arcane 体系已独立成 R1b 兑现）；element 死 key | 不做——等未来法师职业内容 |
| 游侠 vent 凝神屏息 | v153 已明示废弃（专注流量制取代） | 永不（废弃设计） |
| 歌者 resonance/echo 双资源 | 现网无 res_cost/res_gain 用 resonance/echo 的技能；歌者分支用 melody 系（非资源条） | 不做——资源条形态与现网 melody 体系冲突，歌者后续内容按 melody 走 |
| vow 圣律 | 现网无神谕线技能 | 不做——等守线神谕职业内容 |
| 磐核 guard_core_burst | 技能表 L3488/3635 有 mech=guard_core_burst（拳师 BRANCH？）——子 agent 侦察命中但结构待核 | 待核——若有活技能则独立小批 |

### 1.3 引擎能力现状（形态/驻留所需）

- ✅ effects float 层 / bonus 容器 / channels 渠道 / threshold 钩子 / heal_calc / 事件总线（triggers EVENTS 含 turn_start/act_cast/battle_start/act_done）
- ✅ battle 级状态可挂（_fire_ctx/_now 模式；battle2 Battle 是对象可加属性——但 to_state/from_state 序列化只走 sides/顶层键，battle 级自定义状态要加序列化键）
- ⬜ 无"battle 级光环/驻留状态"现成机制（effects 是 actor 级）——melody 需要 battle 级 melody 状态（battle._melody 同款）或"全队广播"通道

---

## 2. 范围建议

**P0（第一批）：melody 驻留旋律系统实现**（修复现网基础诗人 + 歌者分支已上线技能空转）
- 范围：8 技能（基础 5 + 咏叹者 3）
- 机制：battle 级 melody 状态 {kind(atk/def/spd/atk_matk), stack(0-5), finale_ready} → 全队光环按 desc 数值生效；吟唱叠强度；和声翻倍；终章 finale 爆发（咏叹者 2 大招）
- 依赖：battle 级状态序列化（to_state/from_state 加 melody 键）——引擎小扩展 or 走 battle_state 外壳（副本 st 外壳已有类似 meta 先例）

**后续批（不做/等职业内容）**：狂暴/focus/圣律/双资源——现网无技能承载，v139 字段留档 docs 已够，等对应职业线内容立项时按"现网资源 + desc"重建（不留旧壳）。

**待核**：磐核 guard_core_burst 技能结构（若有活技能 → 独立小批，机制=cond per_core 0.7 乘区 + 消耗清层，与 MECH_CASH 兑现同族可装配）。

---

## 3. 批次拆分建议（P0 melody 内部）

| 批 | 内容 | 量级 |
|---|---|---|
| Melody-1 | battle 级 melody 状态（引擎序列化小扩展 or 外壳）+ 主旋律施放换歌/驻留光环（3+2 歌） | 中 |
| Melody-2 | 吟唱叠强度（拨弦/和声：+1/翻倍 6 刻）+ 被动二重唱 | 小中 |
| Melody-3 | 终章 finale（咏叹者激昂战歌/英雄赞歌的 finale 分支）+ 强度 0-5 满层联动 | 中 |
| Melody-4 | 副本/多人广播语义（全队=玩家 side 全体）+ 展示（资源条/状态行） | 小 |

> 触发 finale 的条件需设计定稿（旧"满层/共振"语义 vs 主动技）；recommend：吟唱叠到满层（stack=5 时再吟唱/特定技）触发或技能自带 finale 字段=施放即终章？——实施前小设计确认。

---

## 4. 待办记录
- [ ] P0 melody 系统实施（Melody-1~4）
- [ ] 磐核技能结构核实（活则独立批）
- [ ] v139 狂暴/focus 等：等职业内容批（不实施）
