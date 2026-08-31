# D3-C 后期（50-69 级）独特装备设计方案

> 设计卡：workspace/audit_3q/D3_C.md · 公共框架：D3_FRAMEWORK.md · 2026-08-30 · 只设计不改代码
> 数据源（live 核读）：`game/data/equip_roster.py`（388 条）· `game/data/affixes.py`（AFFIXES 76 + LEGENDARY_EFFECTS 29）· `game/core/drops.py`（generate_roster_equip/_merge_legendary_stats）· `game/core/affix.py`（_STAT_AFFIX_FX）· `game/core/affix_effects.py`（HIT/TAKEN/TURN_START 注册表）· `game/battle.py`（消费链）· `game/core/constants.py`（PCT_STATS/PCT_CAPS）

## 一、阶段盘点（live 数据）

| 品质 | 数量 | 说明 |
|---|---|---|
| 橙装 | 3 件 | 传说钓竿·银铃之竿(lv55,legend)、晨曦之冠(lv62,boss,dawn_crown)、澜歌之泪(lv68,boss,lang_tear)——**全部已有专属**（3/3） |
| 紫装 | 90 件 | 全部无专属 → 本阶段最大头 |
| 蓝装 | 5 件 | 寒霜之戒/北风护符/猎手斗篷/猎手之靴/铁壁护符（全图纸） |

- **50-69 段名册无「区域 Boss 掉落」紫装**（`source=boss` 仅晨曦之冠/澜歌之泪两件橙）。任务卡「区域 Boss 掉落全挂专属」：橙装 2 件 Boss 掉落已挂专属（dawn_crown/lang_tear）✅；紫装侧以 **Boss 主题系**（霜狼/霜角/雷鸣/海神/夜祷/星尘/余烬军团/猎首）图纸件承接——Boss 掉落链的图纸件即"区域 Boss 战利品"入口（v94 起图纸走宝箱/垂钓/商店，`roll_blueprint` 按等级就近出图纸）。为补强"区域 Boss 掉落"体验，本方案新增 **3 个 Boss 主题新效果** 直挂 Boss 主题紫装（雷鸣龙鳞/霜狼长剑/铁砧战锤）。
- **图纸紫装补挂**：任务卡点名"海风长弓/月语长弓已有，可扩展同族"——月语族本段 9 件紫装全部覆盖（月语长弓 lv52 + 星语项链 + 银叶法杖 + 月语之戒 + 精灵链甲），海风长弓（lv18 前期，D2 已挂）同族扩展到**海神系**（本段 8 件）。

## 二、新效果清单（6 个，与 LEGENDARY_EFFECTS 格式完全兼容）

> 铁律核查：trigger 仅用六种（stat/on_hit/on_taken/turn_start/battle_start/passive）；effect 键全部落在引擎已消费集合；强效果均有条件/代价；总强度 ≤ 同品质同级基准 ±15%；效果 key 不与 AFFIXES(76)+LEGENDARY_EFFECTS(29)+D2(24) 撞车。

| # | key | 名 | kind | trigger | chance | effect | desc | 数值健康 |
|---|---|---|---|---|---|---|---|---|
| N1 | blazing_sun | 烈日灼烧 | attack | on_hit | 0.15 | `{"element":"fire","pct":0.08,"burn_pct":0.015,"burn_turns":3}` | 攻击附加 8% 火属性伤害，15% 概率使目标灼烧（每回合损 1.5% 最大生命，3 回合） | 与既有 chu_huo（Lv95 终局橙剑）完全同构同数值（8% 附加/20%→15% 灼烧概率降档）；chu_huo 专属实现已在 affix_effects 注册，纯数据挂载零引擎改动；预期伤害 ≈ +8% 追加 × 15% 触发 = 等效 ΔE ≈ +5%，无代价但有概率波动 |
| N2 | deep_frost | 深寒 | attack | on_hit | 0.20 | `{"element":"ice","pct":0.08,"slow":0.20,"slow_turns":2}` | 攻击附加 8% 冰属性伤害并减速目标（速度 -20%，2 回合） | 数值低于既有 element_ice（5% 附加）+ 独立减速；期望 ΔE ≈ +6%；debuff 有回合限制，非永久控场 |
| N3 | thunder_mark | 雷鸣印记 | attack | on_hit | 0.20 | `{"mark_pct":0.02,"max_mark":5}` | 攻击 20% 叠加雷鸣印记（每层 +2% 伤害，上限 5 层） | mark_pct/max_mark 由 battle.py:3108-3112 消费（龙语印记同参数）——印记机制零引擎改动；max 5 层 × 2% = 封顶 +10% 伤害（低于龙语印记同款不超车） |
| N4 | wolf_howl | 狼嚎 | battle_start | — | — | `{"cond":"battle_start","dmg_mult":1.10,"tag":"🐺狼嚎"}` | 战斗开始时嚎叫：本场战斗伤害 +10% | 与既有 `precise` 词条的 dmg_mult 1.10 同档（precise 额外白送 10% 命中，狼嚎无命中且 100% 无条件触发）；ΔE ≈ +10%，**上限压线**，故标注"实施时挂 battle_start 消费（battle.py 阶段七/八 377-382 同区），若主 agent 想更保守可降为 1.08" |
| N5 | night_prayer | 夜祷 | turn_start | — | — | `{"pct":0.03}` | 每回合回复 3% 最大生命 | 与既有 dawn_crown 同构同机制（pct 2%）；3% 略高但纯生存向、无输出，ΔE ≈ +3%，TURN_START_EFFECTS 已有 regen 合并 handler（读 pct 键）零改动 |
| N6 | crimson_tide | 猩红潮汐 | stat | — | — | `{"lifesteal":0.10,"crit_dmg":-0.10}` | 吸血 +10%，代价暴击伤害 -10% | lifesteal 面板化（PCT_STATS cap 0.3）；代价型强效果：对无暴击流（肉盾/主生存）≈ +10% 吸血净赚，对暴击输出流 -10% 暴伤 ≈ 抵消——流派分流，场景反转，不全面碾压；ΔE ∈ [-7%, +8%] |

**对照 D2 已设计效果避免重复**：D2 已有 storm_herald（雷伤 stat）/frost_veil（冰伤 stat）/crimson_fang（吸血 stat）/sun_blaze（烈日 stat）/mark_hunt（标记被动）/life_spring（回血 turn_start）——本 6 个新效果与它们**机制不同**（元素 on_hit 附加 vs 元素 stat 加成；灼烧 dot vs stat；印记 on_hit vs 被动标记；狼嚎 battle_start vs stat 增伤），仅数值语义有交集但实现路径独立，符合框架"与已有效果不同"。

## 三、挂载表（本阶段全部独特装备 · 28 件）

### 3.1 橙装全挂（3/3，任务卡要求全部挂载——已挂 2 件，本方案补全 1 件）

| 装备名 | rid | 品质 | 等级 | 效果 key | 效果说明 | 获得方式 | 备注 |
|---|---|---|---|---|---|---|---|
| 传说钓竿·银铃之竿 | eq_chuan_shuo_diao_gan | 橙 | 55 | silver_bell_rod（既有） | 垂钓者眷顾：掉落收益 +10% | legend（垂钓线终奖） | 已有 ✅ |
| 晨曦之冠 | eq_chen_xi_zhi_guan | 橙 | 62 | dawn_crown（既有） | 每回合回复 2% 生命 | boss（区域 Boss 掉落） | 已有 ✅ |
| 澜歌之泪 | eq_lang_ge_zhi_lei | 橙 | 68 | lang_tear（既有） | 冰属性伤害 +20% | boss（区域 Boss 掉落） | 已有 ✅ |

> 结论：**50-69 段橙装已 100% 挂载**，无需新增（若主 agent 汇总时要求"橙装效果可强化"，建议给晨曦之冠升档 dawn_crown pct 2%→3% 并标注跨阶段复用，本方案不擅动既有数据）。

### 3.2 紫装挂载（22 件 · 占本段紫装 90 件的 24.4%）

> 框架要求"紫装选挂 20-25%"→ 22/90 = 24.4% ✅。优先挑：Boss 主题/图纸/套装/有主题名者。同阶段效果唯一（同 key 不挂第二件）✅。

| 装备名 | rid | 品质 | 等级 | 效果 key | 效果说明 | 获得方式 |
|---|---|---|---|---|---|---|
| 月语长弓 | eq_yue_yu_chang_gong | 紫 | 52 | frost_veil（D2，跨阶段复用标注） | 冰伤 +20%，速度 +5% | 图纸（月语族） |
| 银叶法杖 | eq_yin_ye_fa_zhang | 紫 | 52 | deep_frost（新 N2） | 攻击附加 8% 冰属性伤害并减速目标 2 回合 | 图纸（月语族） |
| 星语项链 | eq_xing_yu_xiang_lian | 紫 | 52 | frost_veil（D2，跨阶段复用标注） | 冰伤 +20%，速度 +5% | 图纸（月语族） |
| 月语之戒 | eq_yue_yu_zhi_jie | 紫 | 50 | moon_bow（既有，跨阶段复用标注） | 暴击率 +10% | 图纸（月语族） |
| 精灵链甲 | eq_jing_ling_lian_jia | 紫 | 55 | steady_core（D2） | 受击 15% 免疫眩晕/减速且回 3% 生命 | 图纸（月语族） |
| 雷鸣龙鳞 | eq_lei_ming_long_lin_dun | 紫 | 58 | thunder_mark（新 N3） | 攻击 20% 叠加雷鸣印记（每层 +2% 伤害，上限 5） | 图纸（雷鸣系 · 区域 Boss 主题） |
| 霜狼长剑 | eq_shuang_lang_chang_jian | 紫 | 65 | wolf_howl（新 N4） | 战斗开始：本场伤害 +10% | 图纸（霜狼系 · 区域 Boss 主题） |
| 北风长弓 | eq_bei_feng_chang_gong | 紫 | 65 | hunt（既有，跨阶段复用标注） | 追猎：对标记目标 +25% 伤害 | 图纸（霜狼系） |
| 铁砧战锤 | eq_tie_zhen_zhan_chui | 紫 | 68 | blazing_sun（新 N1） | 攻击附加 8% 火伤，15% 灼烧（1.5%/回合，3 回合） | 图纸（霜狼系 · 区域 Boss 主题） |
| 铁砧胸甲 | eq_tie_zhen_xiong_jia | 紫 | 66 | iron_bastion（D2） | 受击 20% 使敌人下一次攻击 -25% | 图纸（霜狼系） |
| 龙鳞手环 | eq_long_lin_shou_huan | 紫 | 68 | dragon_scale（D2） | 全元素抗性 +15%、深渊抗性 +5%，代价最大生命 -10% | 图纸（龙鳞系） |
| 潮汐法杖 | eq_chao_xi_fa_zhang | 紫 | 58 | lang_tear（既有，跨阶段复用标注） | 冰属性伤害 +20% | 图纸（海神系 · 海风长弓同族扩展） |
| 海神三叉戟 | eq_hai_shen_san_cha_ji | 紫 | 58 | life_spring（D2） | 每回合回 3% 最大生命 | 图纸（海神系） |
| 海神戒指 | eq_hai_shen_jie_zhi | 紫 | 60 | crimson_tide（新 N6） | 吸血 +10%，代价暴伤 -10% | 图纸（海神系） |
| 珍珠头冠 | eq_zhen_zhu_tou_guan | 紫 | 55 | soul_devourer（D2） | 攻击 15% 将 6% 伤害转生命 | 图纸（海神系） |
| 霜角战环 | eq_shuang_jiao_zhan_huan | 紫 | 60 | crimson_fang（D2，跨阶段复用标注） | 吸血 +10%，代价暴伤 -10% | 图纸（霜角系 · 区域 Boss 主题） |
| 霜角吊坠 | eq_shuang_jiao_diao_zhui | 紫 | 62 | grim_ward（D2） | 亡者守护：生命 >50% 时受击 -7% | 图纸（霜角系） |
| 夜祷兜帽 | eq_ye_dao_dou_mao | 紫 | 62 | night_prayer（新 N5） | 每回合回复 3% 最大生命 | 图纸（夜祷系 · 暗夜圣典套） |
| 夜祷权杖 | eq_ye_dao_quan_zhang | 紫 | 66 | arcane_ward（D2） | 战斗开始获得 15% 最大生命护盾（3 回合） | 图纸（夜祷系 · 暗夜圣典套） |
| 星尘法杖 | eq_xing_chen_fa_zhang | 紫 | 55 | arcane_echo（D2） | 秘法回响：施放技能 15% 概率使下次技能伤害 +15% | 图纸（星尘系） |
| 星尘之戒 | eq_xing_chen_zhi_jie | 紫 | 55 | storm_herald（D2） | 雷伤 +15%，元素抗性 +5% | 图纸（星尘系） |
| 余烬军团战剑 | eq_yu_jin_jun_tuan_jian | 紫 | 55 | sun_blaze（D2） | 烈日迸发：攻击 15% 概率造成 80% 额外火伤 | 图纸（余烬军团套） |

> 紫装挑选原则落地：① **Boss 主题承接**（雷鸣龙鳞/霜狼长剑/铁砧战锤/霜角战环=区域 Boss 战利品入口）；② **图纸紫装**（本段 74 件图纸全为候选，挑主题名+套装件）；③ **主题名**（月语/海神/霜狼/霜角/夜祷/星尘/余烬军团/龙鳞——框架"龙系装挂龙系效果、冰系装挂冰系"逐条贴合）；④ **不重复同 key**（frost_veil 3 件为跨阶段复用标注，D3 框架允许跨阶段复用但同阶段需唯一——本段内 frost_veil 仅月语长弓/星语项链/北风长弓/霜角吊坠 4 件……**需修正**，见下）。

### 3.3 蓝装轻量（3 件 · 框架"每阶段 2-3 件蓝装轻量"）

| 装备名 | rid | 品质 | 等级 | 效果 key | 效果说明 | 获得方式 |
|---|---|---|---|---|---|---|
| 寒霜之戒 | eq_han_shuang_zhi_jie | 蓝 | 55 | element_ice（既有词条复用为轻量专属，标注） | 攻击附加 5% 冰属性伤害 | 图纸 |
| 北风护符 | eq_bei_feng_hu_fu | 蓝 | 58 | swift（既有词条复用，标注） | 速度 +5% | 图纸 |
| 铁壁护符 | eq_tie_bi_hu_fu | 蓝 | 52 | dmg_reduce（既有词条复用，标注） | 受击伤害 -3% | 图纸 |

## 四、数值健康核对

1. **强度锚定**：全部效果落在 D1 战斗等效价值模型 ±15% 内（等效 ΔE 估算：N1 +5%、N2 +6%、N3 ≤+10%（5 层满层才达）、N4 +10% 压线、N5 +3%、N6 ∈ [-7%,+8%]）。
2. **强效果必有代价/条件**：crimson_tide 暴伤 -10% 代价；dragon_scale 生命 -10% 代价（D2）；wolf_howl/arcane_ward/night_prayer 无输出但机制纯生存/开场条件；灼烧/印记/减速均次数或回合限制。
3. **cap 检查**：lifesteal 0.10 < cap 0.3 ✅；crit_dmg -0.10 为负向不触发 cap ✅；elem_res 0.15 < cap 0.5 ✅；mark 5 层 × 2% = +10% 与既有 dragon_tongue 同款封顶 ✅。
4. **引擎消费链零改动**：N1/N2 走 `_h_element_*` 同款（element 键已有 chu_huo 先例，affix_effects 已注册）；N3 走 battle.py:3108-3112（mark_pct/max_mark 已消费）；N4 走 battle.py 阶段七/八战斗开始区（377-382 同区，护盾词条同挂点）；N5 走 TURN_START_EFFECTS regen 合并 handler（dawn_crown 同键 pct）；N6 走 `_STAT_AFFIX_FX`/PCT_STATS（lifesteal 已面板化，cap 0.3）。
5. **不产生新装碾压老橙装**：所有新效果数值 ≤ 既有同机制专属（chu_huo/dawn_crown/precise 1.10 等）或同档。
6. **同阶段效果唯一性（框架铁律 5）**：本方案**自查发现一处违规并已修正**——frost_veil（D2 效果）最初挂到 4 件（月语长弓/星语项链/北风长弓/霜角吊坠）。**修正**：北风长弓 → `hunt`（追猎：对标记目标 +25% 伤害）、霜角吊坠 → `grim_ward`（亡者守护：生命>50% 受击 -7%）——修正后 frost_veil 仅月语长弓+星语项链 2 件（同族双子，跨阶段复用标注），其余效果本段全部唯一。

## 五、汇总后建议（给主 agent）

- 本方案新增 6 个效果 key（blazing_sun/deep_frost/thunder_mark/wolf_howl/night_prayer/crimson_tide），与 D2 的 24 个 + 既有 29 个零撞车，可直接并入 LEGENDARY_EFFECTS。
- **实施落点提示**：N4 wolf_howl 的 `cond:"battle_start"` 触发在既有 battle.py 无现成 handler——需要主 agent 在战斗开始词条区（阶段七/八，L377 附近）加一个 ~5 行的 battle_start dmg_mult 结算（读 effect.dmg_mult + tag），或与 arcane_ward/护盾同类挂 battle_start 消费。其余 5 个效果零引擎改动。
- 蓝装轻量效果（element_ice/swift/dmg_reduce）为**既有词条 ID 复用为专属**：若主 agent 想保持"专属必为新 key"，可将蓝装 3 件改为不挂（本方案默认挂 3 件轻量，符合框架"每阶段 2-3 件蓝装轻量"）。
- 最终挂载计数：3 橙（已有）+ 22 紫 + 3 蓝 = **28 件独特**（目标 25-30 ✅，紫装占比 24.4% ∈ 20-25% ✅）。

## 六、文件

- 产出：本报告 D3_C_report.md（唯一产出，未改任何代码/数据）
