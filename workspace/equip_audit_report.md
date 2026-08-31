# 装备/套装改造侦察报告（v151 职业体系重构）

> 侦察时间：2026-08-31 · 项目根 `C:/Users/yuyu/qqbot/data/plugins/dragonfall`
> 范围：装备名册（8 个 equip_*.py）+ affixes.py + sets.py + class_sets.py + classes.py + equipment.py + skills.py + items.py + battle.py 相关耦合点
> 方法：grep/正则定位 + Python 原生读文件（sk_ 字符串未被脱敏，技能 key 为中文名，无 sk_ 前缀问题）
> 依据：docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md（六职业六形式零资源条）、docs/CLASS_REDESIGN_FRAMEWORK_v150.md（隐藏六职业拆解映射）、workspace/v151_field_mapping.md（字段映射）

---

## 0. v151 目标体系速览（改造对齐基准）

- 六职业 = 六形式，**零「攒满→消耗→归零」资源条**（`docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md:3,703,745`）：
  战士=战意叠层(mech_stacks)、法师=元素印记(挂敌身 enemy_buffs)、游侠=精力预算+标记(挂账)、牧师=行为无条、刺客=连段计数(mech_stacks)、拳师=破绽条(挂敌身)
- 旧 `core_resources.py` 的 12 资源条 **rage/element/energy/faith/cp/chi/zen/canticle/dragon_might/time_sand/hunt_mark/shadow_step** 全部废弃（`v151_FULL.md:745`）
- 隐藏六职业拆解并入战术线（`v150.md:100-107`）：
  - 龙裔→战士·血怒线；时咒→法师·时律线；星语→游侠·疾风线；暗影神谕→牧师·幽祷线；暮影→刺客·影舞线；淬势→拳师·破绽线
- **关键：隐藏职业与对应基础职业使用相同 weapon_type**（见 §4），所以"武器类型映射"大部分天然成立，主要是**套装/词条/道具的资源绑定要换**。

---

## 1. 隐藏职业专属装备清单（eq_id / 名称 / 归属）

### 1.1 名称含隐藏职业词的装备（9 件，8 文件全扫）

| eq_id | 名称 | 归属隐藏职业 | 行号 |
| --- | --- | --- | --- |
| eq_xing_yu_xiang_lian | 星语项链 | 星语者→游侠·疾风线 | game/data/equip_roster.py:92 |
| eq_long_lin_tou_kui | 龙鳞头盔 | 龙裔（龙鳞词族） | game/data/equip_roster.py:111 |
| eq_long_lin_xiong_jia | 龙鳞胸甲 | 龙裔（龙鳞词族） | game/data/equip_roster.py:112 |
| eq_long_lin_hu_tui | 龙鳞护腿 | 龙裔（龙鳞词族） | game/data/equip_roster.py:113 |
| eq_long_lin_hai_jia | 龙鳞海甲 | 龙裔（龙鳞词族） | game/data/equip_roster.py:122 |
| eq_mu_ying_zhi_ren | 暮影之刃 | 暮影行者→刺客·影舞线 | game/data/equip_roster.py:149 |
| eq_lei_ming_long_lin_dun | 雷鸣龙鳞（盾） | 龙裔（龙鳞词族） | game/data/equip_roster.py:210 |
| eq_mu_ying_long_hun_jian | 暮影龙魂 | 暮影行者→刺客·影舞线 | game/data/equip_roster.py:214 |
| eq_wang_zhe_zhan_xue | 亡者战靴 | 暗影神谕（亡者词族） | game/data/equip_add_effects.py:619-630 |

> 注：名词族计数（全名册文本）——龙裔×17 / 龙鳞×12 / 暮影×11 / 亡者×7 / 武僧×2 / 神谕×2 / 暗影×2 / 星语×1 / 龙血×1 / 时咒×1 / 苦修×1 / 龙焰×1（equip_roster.py 全文），大部分落在**系列主题文案/注释**而非装备名。

### 1.2 隐藏职业专属套装（`set` 字段挂载，含注释声明）

| 套装 | 归属 | 装备件 | 行号 |
| --- | --- | --- | --- |
| 时之领主（法师·隐藏线 时咒） | 时咒→法师·时律线 | eq_shi_zhi_ling_zhu_mi_yi（秘仪·staff）L250、eq_shi_zhi_ling_zhu_shi_jie（时戒）L251 | equip_roster.py:249-251（注释"法师·隐藏线 时咒"L249） |
| 暗夜圣典（牧师·暗影神谕 悼咏） | 暗影神谕→牧师·幽祷线 | eq_ye_dao_quan_zhang L266 / dou_mao L267 / fa_yi L268 / zhi_jie L269（4 件全部 req int） | equip_roster.py:265-269（注释 L265） |

### 1.3 龙裔词族系列（名字无"龙裔"但同主题，改归属需一并考虑）

- **龙脊系列 14 件**：龙脊大剑(sword L109)、龙语法杖(staff L110)、龙鳞头盔/胸甲/护腿(L111-113)、龙爪手套(fist L114)、龙眼项链(L115)、龙语圣剑(sword L116)、黎明之光(sword L117)、暮影之刃(dagger L149)、石龙拳套(fist L812)、撼岳拳套(fist L813)、龙脊鳞甲(armor L871)、龙语圣剑副本Boss 版(L900)
- **龙裔系列 6 件**：龙裔胸甲/护腿/之靴(单引号 L405-407)、精制龙裔胸甲/护腿/之靴(orange L408-410)，全部 req str
- 龙裔系列套装 = SERIES_SETS 注册 '龙裔': '龙裔套'（equip_roster.py:507 / class_sets.py:154）

### 1.4 隐藏职业技能书 / 专属消耗品（改造装备体系时一并涉及）

- 骷髅海技能书 require_class=cls_hymn（items.py:2785）、气爆技能书 require_class=cls_wu_sheng（items.py:2794）
- 时之沙漏 require_class=cls_chronomancer，恢复 time_sand（items.py:2917-2920）
- 龙息之怒技能书已改挂 cls_zhan_shi（items.py:2776）——v151 前已下放基础线

---

## 2. 装备效果绑定旧资源清单（效果 key / 消费资源 / 现状）

### 2.1 AFFIXES 词条（affixes.py L19-449）绑定旧资源条

| 词条 key | 名称 | 绑定资源 | 行号 | v151 现状 |
| --- | --- | --- | --- | --- |
| war_spirit | 战意 | rage（on_attack/on_skill +1） | affixes.py:256-261 | ❌ 废（rage 条废弃；"战意"概念改为 mech_stacks 叠层，语义迁移） |
| rage_forge | 怒火熔铸 | rage max_bonus +2 | affixes.py:262-267 | ❌ 废 |
| warcry_echo | 战吼回响 | rage +1 on buff_skill | affixes.py:268-273 | ❌ 废 |
| blood_bath | 浴血 | rage +1 on_taken | affixes.py:274-279 | ❌ 废 |
| ember_brand | 残血灼薪 | rage +1 cond hp<30% | affixes.py:280-285 | ❌ 废 |
| boiling_blood | 沸血浇筑 | cond rage_full（减伤+8%） | affixes.py:286-291 | ❌ 废（affix_effects.py:237 读 `_rage_full`） |
| arcana_flux | 充能汲引 | element +1 on_cast | affixes.py:293-304 | ❌ 废（element 条废弃→元素印记挂敌身） |
| sigil_engrave | 印记铭刻 | max_sigil +1 cond element_mage | affixes.py:305-310 | ❌ 废（元素印记改为挂敌身印记） |
| reaction_catalyst | 反应催化 | reaction_dmg +15% cond element_mage | affixes.py:311-317 | ❌ 废 |
| energy_blade | 精力刀刃 | energy cost_reduce | affixes.py:318-323 | ❌ 废（精力改预算型，无消耗扣减） |
| energy_tide | 精力潮汐 | energy regen 5/10 | affixes.py:324-329 | ❌ 废 |
| full_pack | 盈满背囊 | energy max_bonus | affixes.py:330-335 | ❌ 废 |
| crit_charge | 暴击蓄能 | energy +3 on_crit | affixes.py:336-341 | ❌ 废 |
| swift_tailwind | 疾风余韵 | energy regen cond energy≥80 | affixes.py:342-348 | ❌ 废（battle.py:811 登记 turn_start） |
| holy_echo | 圣辉回响 | faith +1 on_heal | affixes.py:349-354 | ❌ 废（牧师无条） |
| divine_radiance | 神赐容光 | faith max_bonus +1 | affixes.py:355-360 | ❌ 废 |
| holy_heart | 圣光之心 | faith max_bonus +2 | affixes.py:361-372 | ❌ 废 |
| pious_charm | 虔诚护符 | faith +1 on_taken | affixes.py:373-379 | ❌ 废 |
| crit_return | 暴击回点 | cp +1 on_crit | affixes.py:380-392 | ❌ 废（刺客改连段计数 mech_stacks） |
| combo_ward | 连段护持 | combo_keep_chance cond 攻线限定 | affixes.py:393-398 | ⚠️ 语义迁移（连段改 mech_stacks.combo，battle.py:812/1168-1177 已消费） |
| combo_edge | 连段之锋 | combo_threshold_reduce | affixes.py:399-404 | ⚠️ 语义迁移（同上，battle.py:1180-1190） |
| rhythm_badge | 节奏之徽 | cp max_bonus +1 | affixes.py:405-411 | ❌ 废 |
| combo_recover | 连段回收 | chi +1 on combo_skill | affixes.py:412-417 | ❌ 废 |
| chi_limit | 气量强化 | chi max_bonus +2 | affixes.py:418-423 | ❌ 废 |
| rock_rest | 磐息 | chi +1 on_taken | affixes.py:424-429 | ❌ 废 |
| burst_break | 爆发贯体 | chi_skill_phys +10% | affixes.py:430-435 | ❌ 废（气力技概念改破绽条/磐核） |
| opening_stance | 起手之势 | chi +1 battle_start | affixes.py:436-441 | ❌ 废 |
| momentum_mastery | 蓄势精通 | momentum_per_chi | affixes.py:442-449 | ❌ 废（禅意→蓄势 Momentum 承接，v150.md:653） |

> 引擎消费登记：battle.py:804-812 `RES_AFFIX_GAIN/MAX/TURN_START/ON_TAKEN` 列出全部上述词条 —— 全部需随资源废弃重写。

### 2.2 LEGENDARY_EFFECTS 中绑定旧资源的传说效果

| 效果 key | 名称 | 绑定 | 行号 | v151 现状 |
| --- | --- | --- | --- | --- |
| dragon_aw | 龙威（对龙系+25%） | 无资源（enemy_contains 龙） | affixes.py:126-130 | ✅ 保留（非资源绑定；龙脊/龙裔系列固定词条引用 L1015-1018, L1235-1240） |
| dragon_tongue | 龙语印记（攻击叠印记） | 无资源（mech_stacks.dragon_mark 敌身侧） | affixes.py:559-563 | ✅ 保留（印记=敌身挂账，v151 兼容；affix_effects.py:213-221 消费） |
| dragon_scale | 龙鳞庇护（全抗+15%） | 无资源 | affixes.py:666-670 | ✅ 保留 |
| dragon_annihilation | 灭龙（对龙系+25%） | 无资源 | affixes.py:956-960 | ✅ 保留 |

> 结论：**传说效果基本不绑资源条**（只有 AFFIXES 通用词条绑），需改的是固定词条里引用上述 28 个废弃词条的名册（见 §6）。

---

## 3. 套装绑定旧资源清单

### 3.1 sets.py 旧资源联动套装（v130.2c 12 套，SETS 块 L31-459）

| 套装 | 绑定资源 | bonus 行号 | v151 现状 |
| --- | --- | --- | --- |
| set_xue_shi_zhan_tuan 血誓战团（战士·通用基础） | res_gain rage | sets.py:382-386（bonus L384） | ❌ 废（怒气条废弃） |
| set_yu_jin_jun_tuan_hui_zhang 余烬军团徽章（战士·攻线） | full_rage_pursuit / rage_cost_reduce | sets.py:387-392（L390） | ❌ 废（battle.py:2067/2537 消费 full_rage_pursuit） |
| set_yuan_su_shi_tu 元素使徒（法师·基础/转职通用） | res_max element / ultimate_cost_reduce element | sets.py:393-399（L395/397） | ❌ 废（元素充能条→元素印记挂敌身） |
| set_shi_zhi_ling_zhu 时之领主（法师·隐藏线时咒） | cdr_set on time_freeze | sets.py:400-404 | ❌ 废（时停领域技能废弃） |
| set_xun_lin_zhang_pi_feng 巡林长披风（游侠·散件） | crit_on_marked（标记暴击） | sets.py:405-409 | ⚠️ 语义迁移（标记保留为游侠挂账） |
| set_lie_shou_yuan_zheng_dui_hui_ji 猎首远征队徽记（游侠·攻线） | res_cost_reduce energy on finisher_marked | sets.py:410-416（L413） | ❌ 废（精力预算制无消耗扣减） |
| set_sheng_dian_ri_mian 圣典·日冕（牧师·平稳/爆发） | heal_team_on_miracle_t2plus（耗 5 信仰）/ first_hit_immune cond faith_full | sets.py:417-423（L419/421） | ❌ 废（牧师无信仰条） |
| set_an_ye_sheng_dian 暗夜圣典（牧师·暗影神谕悼咏） | res_gain canticle / elegy_dmg cond canticle_full | sets.py:424-430（L426/428） | ❌ 废（悼咏并入信仰，信仰也废） |
| set_sheng_hui_shi_yue 圣徽·誓约（牧师·新手保底） | res_gain faith on_taken/on_heal | sets.py:431-437（L433/435） | ❌ 废 |
| set_ye_mu_he_qi_ying_sha 夜幕合契·影纱（刺客·5 件套） | battle_start_cp / finisher_crit / combo_finisher_per_layer | sets.py:438-447（L440/444） | ⚠️ 部分迁移（cp 废；combo 连段改 mech_stacks.combo，battle.py:1193-1207 已消费） |
| set_xu_shi_yong_dong 蓄势涌动（拳师·通用） | battle_start_res chi | sets.py:448-452（L450） | ❌ 废（气条→破绽条/磐核） |
| set_shi_bu_ke_dang 势不可挡（拳师·通用） | chi_skill_phys | sets.py:453-458（L456） | ❌ 废 |

### 3.2 sets.py 标记/印记系套装（非资源条但引用"印记/标记"概念）

| 套装 | 引用 | 行号 | v151 现状 |
| --- | --- | --- | --- |
| set_lei_ting 雷霆 | cond_thunder_mark（雷印记） | sets.py:56-64（L62） | ⚠️ 迁移（雷印记→敌身元素印记） |
| set_lv_ren_gong_hui 旅人公会 | proc_mark 旅人标记 | sets.py:157-167（L165） | ✅ 保留（标记=挂账通用） |
| set_xue_tu 学徒 | mark_key element_marks 雷印记 | sets.py:203-209（L207） | ⚠️ 迁移 |
| set_fu_wen 符文 | cond_thunder_ge2 / consume_thunder | sets.py:210-216（L214） | ⚠️ 迁移 |
| set_lie_shou 猎手 | proc_mark_or_dmg 猎手印记 | sets.py:238-244（L242） | ✅ 保留（游侠标记） |
| set_cang_qiong 苍穹 | cond_mark 标记 | sets.py:266-272（L270） | ✅ 保留 |
| set_yin_ying 阴影 | proc_mark 阴影蚀刻 | sets.py:322-328（L326） | ✅ 保留（通用标记） |

### 3.3 class_sets.py 职业套装（18 条 class 绑定 + 5 区域套）

- 18 条职业套装（铁皮/精铁/百炼=战士，学徒/符文/秘法=法师，布衣/祝福/圣堂=牧师，猎手/风行/暗夜=游侠，轻影/夜行/阴影=刺客，行者/石拳/壁槌=拳师）：class_sets.py:131-148，`class` 字段→职业折扣（本职业 100%/60%，class_sets.py:169-171）
- **旧资源绑定 1 处**：轻影 bonus_4 `proc_res_gain res_key=cp`（class_sets.py:143）→ ❹ 废（cp→连段计数）
- 学徒/符文/秘法 bonus_4 用雷印记（class_sets.py:134-136）→ ⚠️ 元素印记语义迁移
- 区域套 5 条（护林/渡口/巡林/霜猎/龙裔）：class_sets.py:150-154，龙裔套 bonus_3 龙威压制（L154）无资源绑定 ✅

### 3.4 引擎消费端

- battle.py:814-823 `SET_EFFECT_CONSUMED` 列出全部 12 资源联动套 effect —— 废弃资源后整段需重写
- battle.py:2911-2916 `_set_res_gain`（套装 res_gain 走 `_res_gain` 旧资源管线）
- battle.py:2067-2071 / 2537 `full_rage_pursuit`（余烬军团 4 件）

---

## 4. 职业武器类型映射表

### 4.1 现有 6 基础职业 → weapon_type（classes.py）

| 职业 | weapon_type | 行号 |
| --- | --- | --- |
| 战士 cls_zhan_shi | sword | classes.py:112 |
| 法师 cls_fa_shi | staff | classes.py:171 |
| 游侠 cls_you_xia | bow | classes.py:230 |
| 牧师 cls_mu_shi | mace | classes.py:289 |
| 刺客 cls_ci_ke | dagger | classes.py:347 |
| 拳师 cls_wu_seng | fist | classes.py:407 |

### 4.2 WEAPON_TYPES 职业归属表（equipment.py:49-74）

```
sword→战士  staff→法师  bow→游侠  mace→牧师  dagger→刺客  fist→拳师
spear→战士  shield→战士
```

### 4.3 隐藏职业的 weapon_type（classes.py）

| 隐藏职业 | weapon_type | 行号 | 并入线（v150.md:100-107） | 结论 |
| --- | --- | --- | --- | --- |
| 龙裔誓约 cls_dragon_oath | sword | classes.py:456 | 战士·血怒 | ✅ 天然同型，零改 |
| 时咒法师 cls_chronomancer | staff | classes.py:504 | 法师·时律 | ✅ 天然同型 |
| 星语者 cls_wild_hunter | bow | classes.py:556 | 游侠·疾风 | ✅ 天然同型 |
| 暗影神谕 cls_hymn | mace | classes.py:613 | 牧师·幽祷 | ✅ 天然同型 |
| 暮影行者 cls_shadow_blade | dagger | classes.py:666 | 刺客·影舞 | ✅ 天然同型 |
| 淬势者 cls_wu_sheng | fist | classes.py:725 | 拳师·破绽 | ✅ 天然同型 |

> **核心结论：隐藏六职业 weapon_type 与对应基础职业完全一致，武器类型映射天然成立**，无需并入。真正要改的是：
> 1. 锻造/商店按 weapon_type 反查职业列表（economy.py:2501-2504, 2583-2586, 2614-2619, 2652）——现在会显示"龙裔誓约/时咒法师"等旧职业名（C.CLASSES 遍历含隐藏线），v151 后隐藏线并入，需改为只显示 6 职业 12 线
> 2. 龙脊/龙裔系列是"龙"主题武器（含 sword/fist/dagger），归属为战士·血怒线即可（龙裔技能已下放战士）

### 4.4 名册 weapon_type 分布（全 8 文件，456 武器）

sword×46 / staff×38 / bow×35 / dagger×27 / mace×21 / fist×18 / shield×11 / spear×3 —— 与六职业映射一致，无孤儿类型。

---

## 5. 装备 req 属性映射

### 5.1 属性系统（str/vit/agi/int）

- 属性→面板换算（engine.py:393-408）：str→atk×1.0、int→matk×1.0 + mp×1.5、agi→spd×0.8 + crit×0.004、vit→hp×6
- 需求显示名（economy.py:102）：str=力量 agi=敏捷 int=智力 vit=耐力
- **装备穿戴检查 `_req_check`**：economy.py:4635-4658 —— 按 `player.attributes` 校验 req，**不锁职业、只锁属性**（economy.py:206 注释"阶段八：属性需求（不锁职业，只锁力量/智力/敏捷/耐力）"）→ 装备 req 天然与职业解耦 ✅

### 5.2 名册 req 统计（全 8 文件 364 条 req）

| req 属性 | 次数 | 对应主属性职业 |
| --- | --- | --- |
| str | 147 | 战士/拳师（力量系） |
| agi | 131 | 游侠/刺客（敏捷系） |
| int | 84 | 法师/牧师（智力系） |
| vit | 11 | 全职业通用（防具） |

### 5.3 武器类型 → req 主属性现状（名册）

| weapon_type | req 主属性 | 行号 |
| --- | --- | --- |
| sword | str×33（主）+ agi×6 + int×2 | 主 str；例外：铁港弯刀 agi（L46）、金钩弯刀 agi（L56）、银铃剑 agi（L166）、铁港剑 agi（L200）、黎明之光 str+int（L117）、星尘剑 str+int（L164） |
| staff | int×29 + agi×1 | 主 int；例外：银铃杖 agi（L224） |
| bow | agi×27 | 全 agi ✅ |
| dagger | agi×21 | 全 agi ✅ |
| mace | str×10 + agi×2 + int×5 | 主 str；牧师向 int（日冕 L261 / 夜祷 L266 等） |
| fist | str×15 | 全 str ✅ |
| shield | str×11 | 全 str ✅ |
| spear | str×3 + agi×2 | 主 str |

### 5.4 随机装备 req 推导（非名册）

- `random_req`（affix.py:133-142）：weapon 按 `_REQ_STAT_BY_SLOT`（affix.py:31-36）——sword/mace/fist/spear/shield→str，bow/dagger→agi，staff→int；非武器 helm/armor/legs→vit，boots/ring→agi，necklace→int
- 消费端：drops.py:245（掉落）、economy.py:5651/5689（商店武器标注）

### 5.5 六职业主属性映射建议（新体系对齐）

| 职业 | 建议主属性 | 依据 |
| --- | --- | --- |
| 战士 | str（力量） | 现有 sword/spear/shield req str 一致 |
| 法师 | int（智力） | staff req int 一致 |
| 游侠 | agi（敏捷） | bow req agi 一致 |
| 牧师 | int（智力） | mace 牧师向已 int（日冕/夜祷），但 mace 主统计是 str —— **需决策：mace 整体迁 int 还是仅牧师套装迁** |
| 刺客 | agi（敏捷） | dagger req agi 一致 |
| 拳师 | str（力量） | fist req str 一致 |

> 主要缺口：**mace 类型混杂**（str×10 / int×5 / agi×2），v151 牧师=唯一权杖使用者，建议 mace 统一 int（牧师主属性），战士的 str 需求由 sword/spear/shield 承担。

---

## 6. 结论：装备/套装改造的改动清单（按文件分组）

### A. game/data/equip_roster.py（名册 208 件）
1. **隐藏职业词改名/改归属**（9 件）：星语项链 L92、龙鳞头盔/胸甲/护腿/海甲 L111-113/122、暮影之刃 L149、雷鸣龙鳞 L210、暮影龙魂 L214 → 按 §1.1 归属并入对应线（龙鳞→战士·血怒、暮影→刺客·影舞、星语→游侠·疾风）
2. **隐藏职业专属套装保留但改线归属**：时之领主 2 件 L250-251（时咒→法师·时律线）、暗夜圣典 4 件 L266-269（暗影神谕→牧师·幽祷线）——套装效果里的 canticle/时停绑定需改（见 B）
3. **龙脊 14 件 / 龙裔 6 件**：主题保留（龙裔技能已下放战士血怒线），weapon_type 天然归属战士/法师/拳师，仅需确认显示职业列表不含隐藏线（依赖 economy.py 改造）
4. **固定词条引用废弃词条**：龙脊大剑/龙语法杖/龙眼项链/龙语圣剑/黎明之光等引用 dragon_aw（保留✅）但引用 execute/charge/combo/meditate 等（combo→迁移）；具体见 affixes.py:1014-1018, 1235-1240（SERIES_FIXED_AFFIX）

### B. game/data/sets.py（SETS 42 条 + 资源联动 12 条）
1. **12 套资源联动套装效果全重写**（§3.1）：血誓战团 L382、余烬军团徽章 L387、元素使徒 L393、时之领主 L400、巡林长披风 L405、猎首远征队徽记 L410、圣典·日冕 L417、暗夜圣典 L424、圣徽·誓约 L431、夜幕合契·影纱 L438、蓄势涌动 L448、势不可挡 L453
2. **标记/印记系迁移**（§3.2）：雷霆 L56、学徒 L203、符文 L210 的"雷印记"→敌身元素印记；旅人公会/猎手/苍穹/阴影标记保留
3. 附带：class_sets.py 文件头注释已声明"旧 SETS 42 条仍残留在 data/sets.py（兼容旧档 set 字段，待确认后清理）"（class_sets.py:11-13）

### C. game/core/class_sets.py（职业套装 18+5）
1. 轻影 bonus_4 cp→连段（class_sets.py:143）
2. 学徒/符文/秘法 bonus_4 雷印记语义迁移（class_sets.py:134-136）
3. 18 条 class 字段保持（职业折扣体系 v136 保留，class 归属与新六职业一致 ✅）

### D. game/data/affixes.py（词条库）
1. **AFFIXES 28 条废弃资源词条**（§2.1 全表）需重写/移除；battle.py:804-812 的 RES_AFFIX_* 登记同步删改
2. AFFIX_POOL_BY_QUALITY（L455-493）与 AFFIX_AFFINITY_POOLS（L497-517）中引用这些词条的池条目需清理
3. LEGENDARY_EFFECTS 无资源绑定（§2.2）✅ 保留

### E. game/data/equip_add_effects.py（40 件特效装）
1. 亡者战靴（equip_add_effects.py:619-630，暗影神谕词族改名）；龙脊鳞甲/虚空行者等引用龙鳞海甲 desc（equip_add_effects.py:763）
2. 其余特效（不灭意志/苍穹之冠等）无资源绑定 ✅

### F. game/data/items.py（消耗品）
1. **16 件绑定旧资源条的道具失效**（§侦察）：怒火药剂 rage L2900、沸腾战血 L2903、熔核之心 L2906、战前猛火餐 L2909、时之沙漏 time_sand L2917-2920（require_class=cls_chronomancer）、活力原浆 energy L2923、迅捷之核 L2926、满弦烈酒 L2929、圣辉药剂 faith L2933、信仰结晶 L2936、香薰圣烛 L2939、影袭药水 cp L2943、瞬步结晶 L2946、夜枭茶 L2949、斗气凝丸 chi L2953、澎湃烈酒 L2959
2. 消费端 potion_effects.py:221-372（restore_resource/restore_resource_full/resource_amp/battle_start_resource）全走 `_res_gain` 旧管线 → 需随资源废弃改造

### G. game/data/skills.py（技能层，装备改造联动）
- 隐藏六职业技能 res_cost/res_gain 全部绑旧资源条（dragon_might×19/time_sand×15/hunt_mark×10/canticle×48/shadow_step×8/zen×20 等，§侦察）——属技能改造批次（v151_field_mapping.md:76-86），装备改造仅需同步套装效果改名

### H. game/commands/economy.py（显示/过滤层）
1. `_learned_blueprint_list` / `_craft_list_class` / `_recipe_detail` 按 weapon_type 反查职业列表（economy.py:2501-2504, 2583-2586, 2614-2619, 2652）——C.CLASSES 遍历会显示隐藏职业名，v151 后需只显示 6 职业 12 线
2. req 显示/校验（L102, 207-211, 4635-4658, 4661-4669）——属性体系不变 ✅ 无需改

### I. game/battle.py（引擎消费端）
1. RES_AFFIX_GAIN/MAX/TURN_START/ON_TAKEN（L804-812）与 SET_EFFECT_CONSUMED（L814-823）全段重写
2. `_set_res_gain`（L2911-2916）、`full_rage_pursuit`（L2067/2537）、`_rage_full`（L236-237 区）、canticle 满档判定（L2988-2989）、`_res_gain` 旧管线（L673-700）——随资源条废弃整段移除/换 mech_stacks

---

## 附：侦察方法与数据可靠性

- 全部行号为 Python 原生 `open().read()` + 正则定位实测（Hermes 显示层 sk_ 脱敏不影响，技能 key 为中文名）
- 名册解析：8 个 equip_*.py 共 456 条装备（roster 208 + add_early 35 + add_novice 24 + add_mid_late 64 + add_lategame 10 + add_boss_elite 40 + add_effects 70 + add_fist_archer 5）
- 未跑全量回归（铁律），仅静态 grep/正则侦察
