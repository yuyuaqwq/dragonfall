# D3-D 末期（70-89 级）独特装备设计方案

> 任务卡：workspace/audit_3q/D3_D.md · 公共框架：D3_FRAMEWORK.md · 2026-08-30 · 只设计不改代码
> 必读：D2_design.md / equip_roster.py / affixes.py:518-665 / battle.py 消费链 / weapon_effects.py（v140 特效注册表）

## 一、核心结论

末期（Lv.70-89）独特装备 **49 件** = 橙装 33 件全挂 + 紫装 16 件选挂（52 件里挑高难来源）。
- 橙装挂载通道：`legendary` 专属 key（`LEGENDARY_EFFECTS`，装备生成器 `generate_roster_equip` 自动写入装备并折算 stat 型效果 → 零代码生效）
- 紫装挂载通道：`weapon_effect` 特效 key（v140 注册表 `core/weapon_effects.py`，78 个现成特效 key 可复用 → 数据层字段即消费，零代码）
- **华丽化主题**：减伤/免死/冰冻/防线/深渊——与末期高难副本/隐藏线/灰烬守卫套主题严格贴合
- 新效果 6 个（全部 stat 型 + 元素/抗性键，**格式与 LEGENDARY_EFFECTS 完全兼容、零引擎改动**）

## 二、新效果清单（6 个，全部末期主题：守护/死亡/冰冻/深渊）

> ⚠️ 实现注记：6 个新效果中 5 个将作为**名册 leg 字段同名 key**（xing_hui_zhi_guan / xing_he_fa_zhang / shuang_lang_zhi_wang_ya / bing_hao_zhan_ren / frozen_heart）补入 `LEGENDARY_EFFECTS`（零改名册）；第 6 个 `death_wall` 死亡防线为效果库扩容（供其他阶段/后期批次复用）。全部 stat 型 + 既有 effect 键，零引擎改动。

| key（入库名） | 名 | kind | trigger | effect | desc | 数值健康 |
|---|---|---|---|---|---|---|
| `xing_hui_zhi_guan` | 星辉守护（star_guardian） | defense | stat | `crit_dmg:0.15, dodge:0.05` | 暴击伤害＋15%、闪避＋5% | crit_dmg 0.15<既有 gold_hook 0.30；dodge 0.05<cap0.4；ΔE≈+5% |
| `xing_he_fa_zhang` | 冰嚎（frost_howl） | attack | stat | `ice_dmg:0.20, crit:0.05` | 冰属性伤害＋20%、暴击率＋5% | ice_dmg 0.20 同档 lang_tear；crit 0.05<cap0.5；ΔE≈+6% |
| `shuang_lang_zhi_wang_ya` | 霜墙防线（frost_wall） | defense | stat | `elem_resist:0.10, tenacity:0.05` | 全元素抗性＋10%、韧性＋5%——以寒霜筑起无形防线 | 纯 stat 零代码；elem_res 0.10<cap0.5、tenacity 0.05<cap0.5；ΔE≈+4% |
| `bing_hao_zhan_ren` | 永冻之心（frozen_heart） | defense | stat | `ice_dmg:0.15, tenacity:0.05` | 冰属性伤害＋15%、韧性＋5% | ice_dmg 0.15 与澜歌/敖澜同档；`_affix_element_dmg` 遍历消费零代码 |
| `frozen_heart` | 深渊守望（abyss_ward） | defense | stat | `abyss_resist:0.10, hp_pct:0.05` | 深渊抗性＋10%、最大生命＋5% | abyss_res 0.10<cap0.5；深渊怪场景 Δ+6%、物理怪场景 Δ−2%（条件型价值） |
| `death_wall` | 死亡防线 | defense | stat | `tenacity:0.08, hp_pct:-0.05` | 韧性＋8%，代价最大生命－5%——以血肉为墙 | 强效果带代价；tenacity 0.08<cap0.5；ΔE≈+2% |

**设计铁律核验**：
- trigger 全部为 `stat`（六种合法 trigger 之一），effect 键全部复用既有语义（`elem_resist/abyss_resist/tenacity/ice_dmg/crit_dmg/dodge/crit/hp_pct`），零新增消费点 → 零引擎改动
- 强效果带代价：`death_wall` 以 −5% 最大生命换韧性 +8%
- 总强度锚定：全部 ΔE ∈ [−2%, +6%]，绝对上界未超 ±15% 铁律（D2 §五）
- 全部落在 PCT_CAPS 内（crit 0.5 / dodge 0.4 / tenacity 0.5 / elem_res 0.5 / abyss_res 0.5 / crit_dmg 1.0）

## 三、橙装挂载表（33 件全挂）

### 3.1 已有 LEGENDARY_EFFECTS 专属（19 件，0 新增）

| 装备名 | rid | 等级 | 效果 key | 效果说明 | 获得方式 |
|---|---|---|---|---|---|
| 月神之弓 | eq_yue_shen_zhi_gong | 70 | moon_bow | 暴击率＋10% | legend |
| 敖澜之珠 | eq_ao_lan_zhi_zhu | 72 | ao_lan_pearl | 冰属性伤害＋20% | boss |
| 符文战锤·大地之心 | eq_da_di_zhi_xin | 78 | earth_heart | 受击伤害－5%、最大生命＋5% | legend |
| 灰烬长剑 | eq_hui_jin_chang_jian | 85 | ember_ward | 受击 20% 反弹 50% 伤害（灰烬守卫套） | boss |
| 灰烬铠甲 | eq_hui_jin_kai_jia | 85 | ember_ward | 同上（灰烬守卫套） | boss |
| 灰烬之盔 | eq_hui_jin_zhi_kui | 85 | ember_ward | 同上（灰烬守卫套） | boss |
| 灰烬之盾 | eq_hui_jin_zhi_dun | 85 | ember_ward | 同上（灰烬守卫套） | boss |
| 灰烬护腿 | eq_hui_jin_hu_tui | 85 | ember_ward | 同上（灰烬守卫套） | boss |
| 灰烬战靴 | eq_hui_jin_zhan_xue | 85 | ember_ward | 同上（灰烬守卫套） | boss |
| 熔炉之心 | eq_rong_lu_zhi_xin | 85 | rong_lu_heart | 暴击率＋6%、最大生命＋8% | 图纸 |
| 元素使徒之冠 | eq_yuan_su_shi_tu_zhi_guan | 85 | element_apostle_crown | 最大生命＋6% | boss |
| 烬核之心 | eq_jin_he_zhi_xin_zhang | 86 | jin_he_heart | 暴击伤害＋25% | 图纸 |
| 元素使徒长袍 | eq_yuan_su_shi_tu_chang_pao | 86 | element_apostle_robe | 受击伤害－5% | boss |
| 苍穹之靴 | eq_cang_qiong_zhi_xue | 86 | element_apostle_robe | 受击伤害－5% | 图纸 |
| 赫尔加的祭器 | eq_he_er_jia_de_ji_qi | 88 | helga_relic | 冰属性伤害＋15% | boss |
| 暮影龙魂 | eq_mu_ying_long_hun_jian | 88 | mu_ying_soul | 暴击率＋8% | 图纸 |
| 元素使徒法杖 | eq_yuan_su_shi_tu_fa_zhang | 88 | element_apostle_wand | 雷/冰属性伤害＋15% | boss |
| 时之领主时戒 | eq_shi_zhi_ling_zhu_shi_jie | 88 | time_lord_ring | 暴击伤害＋18% | boss |
| 苍穹之翼 | eq_cang_qiong_zhi_yi | 88 | element_apostle_robe | 受击伤害－5% | 图纸 |

### 3.2 已有 v140 装备级特效（9 件，缺 legendary key 但特效已注册，无需补）

| 装备名 | rid | 等级 | 特效 key（weapon_effect） | 效果说明 | 获得方式 |
|---|---|---|---|---|---|
| 永霜秘杖 | eq_yong_shuang_mi_zhang | 70 | everfrost_domain | 冰系技能后 30% 冻结目标 1 回合（Boss 减速 2 回合），冷却 3 回合 | 任务 |
| 不灭意志 | eq_bu_mie_yi_zhi | 72 | undying_will | 每场 1 次，生命 <20% 触发，本回合免疫致死并回复 10% 生命 | 副本Boss |
| 海妖之牙 | eq_hai_yao_zhi_ya | 72 | siren_fang | 每第 3 次攻击额外 40% 攻击力无视防御伤害 | legend |
| 噬魂短刃 | eq_shi_hun_duan_ren | 75 | soul_eater | 攻击附加目标当前生命 2% 伤害（上限=攻击力 100%）并回复等量 | legend |
| 蚀月之冠 | eq_shi_yue_zhi_guan | 78 | eclipse_crown | 开战 15% 生命护盾，持盾时速度+10%，盾破后下次攻击+15% | legend |
| 暮裂之刃 | eq_mu_lie_zhi_ren | 85 | dusk_blade | 击杀后潜行，下一次攻击 +30% 且无视闪避（每场 1 次） | legend |
| 岁月之杖 | eq_sui_yue_zhi_zhang | 86 | time_staff | 每回合结束攻击+1.5%、回 1.5% 生命（上限 10 层） | legend |
| 咒刃之誓 | eq_zhou_ren_zhi_shi | 88 | oath_blade | 释放技能后，下一次攻击伤害+25%（每回合限 1 次） | legend |
| 烬火壁垒 | eq_jin_huo_bi_lei | 88 | ember_bulwark | 受击对攻击者造成自身 5% 最大生命伤害并叠灼烧（每回合限 1 次） | legend |

### 3.3 缺专属且无特效（5 件，用 5 个新效果补）★ 本阶段核心补挂

> ⚠️ 实现注记：以下 5 个新效果 key **采用名册 leg 字段同名**（xing_hui_zhi_guan / xing_he_fa_zhang / shuang_lang_zhi_wang_ya / bing_hao_zhan_ren / frozen_heart），实现时仅在 `LEGENDARY_EFFECTS` 补 5 条数据即可，**零改名册**（名册 leg 字段已就位，缺的只是效果定义）。已核验 5 个 key 与既有 29 个效果零冲突。

| 装备名 | rid | 等级 | 效果 key（新） | 效果说明 | 获得方式 |
|---|---|---|---|---|---|
| 星辉之冠 | eq_xing_hui_zhi_guan | 70 | `xing_hui_zhi_guan`（星辉守护 star_guardian） | 暴击伤害＋15%、闪避＋5% | boss |
| 星河法杖 | eq_xing_he_fa_zhang | 72 | `xing_he_fa_zhang`（冰嚎 frost_howl） | 冰属性伤害＋20%、暴击率＋5% | legend |
| 霜狼之王牙 | eq_shuang_lang_zhi_wang_ya | 76 | `shuang_lang_zhi_wang_ya`（霜墙防线 frost_wall） | 全元素抗性＋10%、韧性＋5% | boss |
| 冰嚎战刃 | eq_bing_hao_zhan_ren | 80 | `bing_hao_zhan_ren`（永冻之心 frozen_heart） | 冰属性伤害＋15%、韧性＋5% | legend |
| 永冻之心 | eq_yong_dong_zhi_xin | 84 | `frozen_heart`（深渊守望 abyss_ward） | 深渊抗性＋10%、最大生命＋5% | boss |

## 四、紫装挂载表（16 件，52 件里挑高难来源 + 主题名）

> 通道：weapon_effect 特效 key（v140 注册表 78 个现成 key 复用，数据层字段即消费，零代码）
> 挑法：副本Boss/boss/精英专属/任务/宝藏/支线/图纸 优先；商店 3 件（龙裔胸甲/护腿/之靴）不挂（低难来源）
> 唯一性：16 个 key 全阶段唯一（跨阶段标注复用来源），本阶段无重复

| 装备名 | rid | 等级 | 效果 key | 效果说明 | 获得方式 |
|---|---|---|---|---|---|
| 石炉战锤 | eq_shi_lu_zhan_chui | 84 | gargoyle_heart | 每场 1 次，生命 <30% 获得 25% 最大生命护盾并回复 15% 生命 | boss |
| 古树枝杖 | eq_gu_shu_zhi_zhang | 70 | echo_bless | 治疗溢出 30% 转护盾（上限 10% 最大生命） | 精英专属 |
| 霜巨魔战锤 | eq_shuang_ju_mo_zhan_chui | 72 | frost_ring | 命中 25% 减速 2 回合（速度-40%），已减速则冻结 1 回合 | 精英专属 |
| 熔岩重剑 | eq_rong_yan_zhong_jian | 76 | ember_burn | 技能命中 30% 使目标 3 回合每回合损 1.5% 最大生命（Boss 1%） | 精英专属 |
| 霜牙冰刃 | eq_shuang_ya_bing_ren | 84 | frost_crown | 受击 10% 使敌人冻结 1 回合（每场最多 2 次） | 精英专属 |
| 烬山守望者之徽 | eq_jin_shan_shou_wang_zhe_zhi_hui | 82 | atonement_shield | 治疗溢出转盾（上限 15% 最大生命），持盾时受击-10% | 任务 |
| 守夜者徽章 | eq_shou_ye_zhe_hui_zhang | 70 | guardian_will | 受击 8% 使敌人下一次攻击伤害-25% | 支线 |
| 深渊头盔 | eq_shen_yuan_tou_kui | 70 | abyss_barrier | 战斗开始获得最大生命+8%（持续整场） | 图纸 |
| 深渊战刃 | eq_shen_yuan_zhan_ren | 75 | blood_trace | 命中 25% 使目标 4 回合每回合损 2% 当前生命（Boss 1.5%），对败血目标+10% 伤害 | 图纸 |
| 黑曜胸甲 | eq_hei_yao_xiong_jia | 78 | deeprock_aegis | 受击 10% 获得护盾（吸收 8% 最大生命），冷却 2 回合 | 图纸 |
| 守望者护符 | eq_shou_wang_zhe_hu_fu | 78 | undying_band | 每回合开始回复 1.5% 最大生命 | 图纸 |
| 龙鳞头盔 | eq_long_lin_tou_kui | 80 | dragon_spine_mail | 受击 15% 反弹 25% 伤害并使其重伤（治疗-30%，2 回合） | 图纸 |
| 龙眼项链 | eq_long_yan_xiang_lian | 80 | randuin_weary | 敌人每次行动后速度-6%（最多 3 层） | 图纸 |
| 龙爪手套 | eq_long_zhao_shou_tao | 82 | hunter_open | 每 3 次攻击后，下一次攻击附带 12% 攻击力真伤 | 图纸 |
| 龙脊大剑 | eq_long_ji_da_jian | 85 | star_pierce | 每 4 次攻击后，下一次攻击附真伤=20% 攻击力+目标已损生命 3%（上限 5%） | 图纸 |
| 苍穹之枪 | eq_cang_qiong_zhi_qiang | 88 | wind_split | 命中 25% 追加一次 50% 攻击力攻击，优先打召唤物 | 图纸 |

## 五、套装协同（灰烬守卫套 6 件全挂已定）

- 灰烬守卫套 6 件（灰烬长剑/铠甲/之盔/之盾/护腿/战靴，Lv.85 橙，H7 灰烬回廊隐藏线 Boss）全挂 `ember_ward` 专属（受击 20% 反弹 50% 伤害）——与套装 5 件效果（残血增攻）叠加构成"反伤+爆发"双线，末期高难副本主力防线
- 元素使徒 4 件（法杖/之冠/长袍/坠饰，Lv.85-90 橙，团本/世界 Boss）各自独立专属（element_apostle_*），本阶段挂 3 件 + 苍穹之翼/苍穹之靴复用 element_apostle_robe（苍穹之翼系列）——跨系列复用标注

## 六、数值健康（核对）

1. **强度锚定**：所有挂载效果 ΔE ∈ [−2%, +6%]（新效果）或与既有专属同档（复用），绝对上界未超 ±15% 铁律
2. **新效果全部 stat 型 + 元素/抗性键**：`elem_resist/abyss_resist/tenacity/ice_dmg/crit_dmg/dodge/crit/hp_pct` 全部为引擎既有消费键（drops._merge_legendary_stats 折算 / battle._affix_element_dmg 遍历 / 元素抗性词条名匹配），**零引擎改动**
3. **PCT_CAPS 全部落内**：crit 0.5 / dodge 0.4 / tenacity 0.5 / elem_res 0.5 / abyss_res 0.5 / crit_dmg 1.0——无一件超 cap
4. **强效果必有代价/条件**：death_wall（−5% 生命换韧性）、undying_will（每场 1 次）、bedrock_crown（每场 1 次）、time_freeze（每场 1 次）——全部次数限制或条件生效
5. **无全面碾压**：星辉之冠（暴伤+闪避）vs 元素使徒之冠（生命+6%）——输出向 vs 生存向场景分化；霜墙防线（元素抗+韧性）vs 深渊守望（深渊抗+生命）——元素图 vs 深渊图分化
6. **同一效果同阶段不重复**：橙装 33 件效果 key 两两不同（灰烬守卫套共享 ember_ward 为套件既定设计，元素使徒/苍穹之翼跨系列共享 element_apostle_robe 为套装既定）；紫装 16 件 we key 全部唯一且与 v140 已挂 9 件不重叠
7. **跨阶段复用标注**：紫装复用的 16 个 we key 均已在其他阶段 1 处占用（v140 落地），本设计为末期补挂（数据层复用，框架第 5 条允许跨阶段复用但标注）

## 七、与 D2 的关系

- D2 末期设计 17 件（灰烬守卫套 6 件全挂、永霜秘杖、蚀月之冠、不灭意志、赫尔加的祭器等）——本方案全覆盖并保留
- D2 效果库 24 个新效果（龙鳞庇护/黑曜壁垒/铁壁意志/磐石之心等）为后期/终局效果预留——本阶段不重复设计，6 个新效果主题（守护/死亡/冰冻/深渊）与 D2 24 个不重名
- 紫装补挂策略：D2 末期 17 件全为橙装；本方案新增 16 件紫装（高难来源优先），把"独特装备"从橙装垄断扩展为"橙全挂+紫高难挑挂"的金字塔结构

## 八、统计

- 独特装备总数：**49 件**（橙 33 + 紫 16）
- 新效果：**6 个**（入库 key：xing_hui_zhi_guan 星辉守护 / xing_he_fa_zhang 冰嚎 / shuang_lang_zhi_wang_ya 霜墙防线 / bing_hao_zhan_ren 永冻之心 / frozen_heart 深渊守望 / death_wall 死亡防线）
- 覆盖率：末期 95 件装备中 49 件独特（52%）；橙 33/33 = 100%；紫 16/52 ≈ 31%（目标 15-18 件，取 16）
- 白/绿/蓝 0 件独特（蓝 10 件保持普通，新手阶梯不破）
