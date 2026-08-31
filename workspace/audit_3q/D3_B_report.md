# D3-B 中期（30-49 级）独特装备设计方案

> 设计卡：workspace/audit_3q/D3_B.md · 2026-08-30 · 只设计不改代码
> 依据：D3_FRAMEWORK.md（公共框架）+ D2_design.md（前期成果，24 效果 + 44 件挂载）+ 代码实况核读
> 消费链核对：game/battle.py `_affix_on_hit`(3139)/`_affix_on_taken`(3158)/`_affix_turn_start`(3170)/`_affix_dmg_mult`(2997)/`_equip_affix_ids`(2795)；game/core/affix_effects.py（HIT/TAKEN/TURN_START 注册表）；game/core/weapon_effects.py（v140 装备级特效注册表，78 个 key，11 类事件）；game/core/drops.py `_merge_legendary_stats`(25，stat 型并入 stats 口径)

## 一、阶段装备池实况（已核实，合并 6 个装备数据文件）

- 中期 30-49 级共 **122 件**：紫 50 / 蓝 50 / 绿 11 / 白 8 / 橙 3
- **橙装 3 件（全挂，且 3/3 已实装战斗效果）**：
  - 时光沙漏 `eq_shi_guang_sha_lou` lv32 副本Boss —— `weapon_effect=time_freeze`（threshold：每场 1 次，生命 <30% 跳过敌人下一次行动，已注册 ✓）；`legendary=time_hourglass` 为装饰性（无战斗消费，保留作显示与故事）
  - 审判之链 `eq_shen_pan_zhi_lian` lv40 boss —— `legendary=judgment_chain`（on_hit 25% 驱散 2 层增益，HIT_EFFECTS 已注册 ✓）
  - 古王剑 `eq_gu_wang_jian` lv42 boss —— `legendary=ancient_king`（passive 对 <30% 目标 +35% 伤害，battle.py:3033 消费 ✓）
  - 任务卡点名「金钩弯刀/古王剑/审判之链已有」——金钩弯刀 lv26 属前期段（A agent 范围），古王剑/审判之链在中期已挂 ✓
- **紫装 50 件**：已有武器特效（weapon_effect 字段）或 desc 声明机制的 17 件（碎冰长弓/荆棘战甲/寒霜之冠/兰顿之戒/石心拳套/回响之刃/秘法典籍之杖/圣辉权杖/夜枭双匕/铁牙战盔/要塞幽灵之盔/黑鸦面巾/红棘珊瑚戒/试炼徽章/克罗的罗盘/血潮短刃/铸火头盔）——其中**试炼徽章等 desc 已写但无 weapon_effect/legendary = 未接线**；纯白板紫装 33 件
- **蓝装 50 件**：4 件已有特效（圣光之握/圣光庇护之盾/圣堂卫士护腿/迅捷战靴），46 件白板

## 二、挂载表（15 件 = 橙 3 + 紫 10 + 蓝 2）

### 橙装 3 件（全挂，任务卡硬要求；3/3 已实装，本批仅确认/补 desc 教学文案）

| # | 装备名 | rid | 品质 | 等级 | 效果 key | 触发时机（教学） | 获得方式 |
|---|--------|-----|------|------|----------|------------------|----------|
| O1 | 时光沙漏 | eq_shi_guang_sha_lou | 橙 | 32 | time_freeze（weapon_effect，已注册） | 生命 <30% 时触发，每场 1 次：跳过敌人下一次行动（阈值时机） | 副本Boss |
| O2 | 审判之链 | eq_shen_pan_zhi_lian | 橙 | 40 | judgment_chain（LEGENDARY_EFFECTS，已注册） | 攻击命中 25% 驱散 2 层增益（命中时机） | 主线Boss |
| O3 | 古王剑 | eq_gu_wang_jian | 橙 | 42 | ancient_king（LEGENDARY_EFFECTS，已注册） | 目标 <30% 生命时 +35% 伤害（斩杀时机） | 主线Boss |

### 紫装 10 件（图纸 8 / Boss 1 / 宝藏系 0，Boss/图纸/支线优先 + 主题名优先，全部为纯白板选件）

| # | 装备名 | rid | 品质 | 等级 | 效果 key | 触发时机（教学） | 获得方式 |
|---|--------|-----|------|------|----------|------------------|----------|
| P1 | 裂鬃獠牙 | eq_lie_zong_liao_ya | 紫 | 30 | **beast_ward**（新·stat） | 常驻：反伤 +5%（兽皮倒刺，受击反打） | 图纸 |
| P2 | 船长的望远镜 | eq_chuan_zhang_de_wang_yuan_jing | 紫 | 30 | **captain_insight**（新·stat） | 常驻：幸运 +6%（发现/宝藏主题） | 图纸 |
| P3 | 深渊之锚 | eq_shen_yuan_zhi_mao | 紫 | 32 | **abyss_anchor**（新·stat） | 常驻：深渊抗性 +8% / 元素抗性 +6% | 图纸 |
| P4 | 圣殿战锤 | eq_sheng_dian_zhan_chui | 紫 | 34 | **sanctum_light**（新·on_hit） | 攻击命中 15%：敌人攻击 -8%（1 回合）（**命中时机教学**） | 图纸 |
| P5 | 血誓战剑 | eq_xue_shi_zhan_jian | 紫 | 36 | **blood_oath_echo**（新·on_taken） | 受击 20%：回复 2% 生命 + 下次攻击 +10%（**受击时机教学**） | 图纸 |
| P6 | 蓄势拳套 | eq_xu_shi_quan_tao | 紫 | 40 | **surge_ready**（新·battle_start） | 战斗开始：下一次攻击 +15%（**开战时机教学**） | 图纸 |
| P7 | 巡林长弓 | eq_xun_lin_chang_gong | 紫 | 42 | **ranger_precision**（新·stat） | 常驻：精准 +6%（无视闪避） | 图纸 |
| P8 | 熔岩护手 | eq_rong_yan_hu_shou | 紫 | 45 | **ember_furnace**（新·on_hit） | 攻击命中 20%：灼烧 1% 最大生命×2 回合（**命中时机教学·灼烧**） | 图纸 |
| P9 | 月影斗篷 | eq_yue_ying_dou_peng | 紫 | 48 | **moon_shadow**（新·stat） | 常驻：闪避 +4% | 图纸 |
| P10 | 试炼徽章 | eq_shi_lian_hui_zhang | 紫 | 46 | **kingdom_lion_heart**（新·passive 条件） | 生命 >70% 时伤害 +8%（**条件触发时机教学**） | Boss |

### 蓝装 2 件（轻量，教学触发时机，小数值）

| # | 装备名 | rid | 品质 | 等级 | 效果 key | 触发时机（教学） | 获得方式 |
|---|--------|-----|------|------|----------|------------------|----------|
| B1 | 长夜徽记 | eq_chang_ye_hui_ji | 蓝 | 40 | **night_watch**（新·on_taken 轻量） | 受击 5%：回复 1% 最大生命（**受击时机教学·入门级**） | 支线 |
| B2 | 翡翠之心 | eq_fei_cui_zhi_xin | 蓝 | 40 | **jade_wealth**（新·stat 轻量） | 常驻：金币收益 +5% | 图纸 |

> 挂载合计：15 件（橙 3 / 紫 10 / 蓝 2），落在任务卡 12-15 目标内；紫 10 件落在 8-10 上限。
> 唯一性铁律：10 个新 key 均为本阶段首挂；无同阶段重复挂载同一效果。试炼徽章 desc 已声明「生命>70% 伤害+8%」，kingdom_lion_heart 语义完全对应（实现即兑现既有文案，非新增冲突）。

## 三、新效果清单（10 个：6 触发/条件型 + 4 常驻 stat 轻量）

> 计数口径：框架「设计 4-6 个新效果」= 触发/条件机制型 6 个（#1-#6）；4 个 stat 常驻轻量（#7-#10）为「既有语义键复用、零引擎改动」的轻量效果，附于清单便于主 agent 汇总去重。全部 trigger 在六种白名单内，effect 键全部复用既有语义。

| # | key | 名 | kind | trigger | chance | effect | desc | 消费端（实现注记） |
|---|-----|----|------|---------|--------|--------|------|------------------|
| 1 | kingdom_lion_heart | 王狮之心 | attack | passive | - | dmg_mult:1.08, cond:"hp_gt_70", tag:"🦁王狮之心" | 生命 >70% 时伤害 +8% | 挂试炼徽章；需在 `_affix_dmg_mult` id 列表（battle.py:3033）追加该 id 并支持 hp_gt 条件；或实现为 weapon_effect passive handler（推荐，分发已存在） |
| 2 | blood_oath_echo | 血誓回响 | defense | on_taken | 0.20 | heal_pct:0.02, atk_up:0.10 | 受击 20%：回复 2% 最大生命，下次攻击 +10% | 需在 affix_effects.py TAKEN_EFFECTS 注册新 handler（沿 tenacity_cc/ember_ward 模式，约 5 行） |
| 3 | sanctum_light | 圣殿辉光 | attack | on_hit | 0.15 | enemy_atk_down:0.08, turns:1 | 攻击命中 15%：敌人攻击 -8%（1 回合） | 需在 affix_effects.py HIT_EFFECTS 注册（沿 armor_break/moro_crown 模式） |
| 4 | ember_furnace | 熔炉余烬 | attack | on_hit | 0.20 | burn_pct:0.01, burn_turns:2 | 攻击命中 20%：灼烧 1% 最大生命×2 回合 | 需在 affix_effects.py HIT_EFFECTS 注册（沿 chu_huo 模式，数值弱化） |
| 5 | surge_ready | 蓄势待发 | attack | battle_start | - | next_atk_up:0.15 | 战斗开始：下一次攻击 +15% | 建议实现为 weapon_effect（battle_start 事件分发已存在 battle.py:400）；或 battle.py:379 'shield' 特判旁加同款特判 |
| 6 | night_watch | 长夜守望 | defense | on_taken | 0.05 | heal_pct:0.01 | 受击 5%：回复 1% 最大生命 | 需在 TAKEN_EFFECTS 注册（轻量入门版，教学用） |
| 7 | beast_ward | 兽性庇护 | defense | stat | - | thorns:0.05 | 反伤 +5% | 零引擎改动：PCT_STATS 含 thorns，`_merge_legendary_stats` 直接并入 stats |
| 8 | captain_insight | 船长洞察 | attack | stat | - | luck:0.06 | 幸运 +6% | 零引擎改动：luck ∈ PCT_STATS |
| 9 | abyss_anchor | 深渊锚护 | defense | stat | - | abyss_res:0.08, elem_res:0.06 | 深渊抗性 +8%，元素抗性 +6% | 零引擎改动：abyss_res/elem_res ∈ PCT_STATS（cap 0.5，远离） |
| 10 | moon_shadow | 月影庇护 | defense | stat | - | dodge:0.04 | 闪避 +4% | 零引擎改动：dodge ∈ PCT_STATS（cap 0.4） |
| 11 | ranger_precision | 巡林精准 | attack | stat | - | precise:0.06 | 精准 +6% | 零引擎改动：precise ∈ PCT_STATS |
| 12 | jade_wealth | 翡翠生财 | attack | stat | - | gold_bonus:0.05 | 金币收益 +5% | 零引擎改动：gold_bonus ∈ PCT_STATS |

## 四、教学「触发时机」覆盖（任务卡要求 2-3 件 on_hit/on_taken 触发型）

| 触发时机 | 装备 | 效果 | 教学要点 |
|----------|------|------|----------|
| 攻击命中（on_hit） | 圣殿战锤 | 15% 敌人攻击 -8% | 第一次感知「命中后结算」：打中才触发，miss 不触发 |
| 攻击命中（on_hit） | 熔岩护手 | 20% 灼烧 1%×2 | 第二次命中时机教学，附带 DOT 概念（持续伤害） |
| 受击（on_taken） | 血誓战剑 | 20% 回 2% 生命 + 下次攻击 +10% | 受击时机教学：挨打也能反打（防具收益） |
| 受击（on_taken） | 长夜徽记 | 5% 回 1% 生命 | 入门级受击教学（低概率低数值，蓝装不破平衡） |
| 战斗开始（battle_start） | 蓄势拳套 | 下一次攻击 +15% | 开战时机教学：先手布局型效果 |
| 条件（passive） | 试炼徽章 | 生命 >70% 时 +8% | 条件触发教学：血量阈值判断（与斩杀线相反方向） |

战斗日志文案建议：触发时输出带 emoji 的明确提示（如 `🦁 王狮之心！生命高于 70%，伤害 +8%`），让玩家把「效果 - 时机 - 触发条件」对应起来（与既有 处决/追猎 文案风格一致）。

## 五、数值健康

1. **强度锚定**：全部效果 ΔE ∈ [−3%, +8%]，远在框架 ±15% 铁律内。参照系：既有 hunt 追猎（标记目标 +20%，条件宽）、execute（<30% +30%，条件极端）、combo（15%×50%）、bleed（20%×5%×3）、moro_crown（15% 攻-10%×2）、regen（1%）。
2. **触发型单次价值**：攻降 8%（< moro_crown 10%）、灼烧 1%×2（< chu_huo 1.5%×3）、回 2% 血 + 下次 +10%（概率 20%，弱于既有 血誓战团 套装 2 件受击回怒 的纯收益型）、next_atk +15%（弱于狂怒药剂 50%）。无一件超过既有同档专属。
3. **条件代价**：王狮之心 +8% 需生命 >70%（与试炼徽章既有 desc 完全一致）——高血才强、低血失效，天然防「满血斩杀」无脑叠。
4. **cap 体检**（PCT_CAPS）：thorns 0.05/0.5、luck 0.06/0.5、abyss_res 0.08+0.06 elem/0.5、dodge 0.04/0.4、precise 0.06/0.6、gold_bonus 0.05/0.5 —— 全部距 cap 极远，叠满整套也不会触发 cap 截断。
5. **无碾压**：深渊之锚（法系/深渊图）vs 月影斗篷（物理闪避）vs 圣殿战锤（控制弱化）——三件防御向效果场景互换；裂鬃獠牙反伤 vs 荆棘战甲（既有 15% 反伤）数值更低不重复。
6. **蓝装不破新手指南**：长夜徽记 5%×1%、翡翠之心 5% 金币——框架 3「蓝装轻量」口径，绿/白 0 独特（本阶段 0 挂载绿白）。
7. **跨阶段重复检查**：本批 10 个 key 与 D2 24 个、既有 LEGENDARY_EFFECTS 29 个、weapon_effects 78 个零重名（已程序核对）。

## 六、实现注记（主 agent 合并时）

- **零引擎改动**：P1/P2/P3/P7/P9/B2（stat 型）直接按 `_merge_legendary_stats` 口径并入 stats，挂 `legendary` 字段即可。
- **需注册 handler**：P4/P5/P8/B1（on_hit/on_taken 型）→ affix_effects.py 的 HIT_EFFECTS/TAKEN_EFFECTS 各加一个注册函数（~5 行/个，模式见现有 handler）；P6（battle_start）→ 推荐 weapon_effect 注册（v140 既有通道）。
- **被动条件型**：P10 推荐 weapon_effect passive 通道（battle_start 登记 hp>70% 状态 + hit 时按条件结算），或扩展 battle.py:3033 id 列表。D2 的 grim_ward 同为此类，合并时统一决策。
- 挂载落地方式：给名册条目加 `legendary`（stat 型）/ `weapon_effect` 字段，与 v140 波1/波3.1 既有模式一致；desc 同步补触发时机说明（名册 desc 优先保留手写）。
- 本阶段橙装 3/3 已实装战斗效果，无需新动作；试炼徽章/克罗的罗盘等「desc 已写未接线」装备由本批补接线（克罗的罗盘已有 weapon_effect=幽航指引 实装 ✓，试炼徽章由 P10 补上）。
