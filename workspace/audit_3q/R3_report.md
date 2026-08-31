# R3 装备属性差异化审查报告

## 覆盖范围（摸了哪些文件）
- `game/core/drops.py`（420+ 行）：`generate_equip`(L165)、`generate_roster_equip`(L264)、掉落入口 `drop_equip`(L130-163)、`_merge_legendary_stats`(L25)
- `game/core/stats.py`（150+ 行）：`equip_stats`(L74)、`equip_value`(L94)
- `game/core/affix.py`（230+ 行）：`roll_affixes`(L78)、`fixed_affixes`(L102)、`stat_affix_stats`(L107)、`random_req`(L133)、`_affix_base_value`(L21)
- `game/data/equip_roster.py`（946 行）：EQUIP_ROSTER 名册 **631 件**（630 个唯一名，`精铁短杖` 重名 1 例）
- `game/data/affixes.py`：SERIES_FIXED_AFFIX（L669，180+ 条固定词条）、AFFIX_POOL_BY_QUALITY（L455）
- `game/data/equipment.py`：QUALITY(L13)、AFFIX_COUNT(L280)
- `game/data/stat_templates.py`：EQUIP_SLOT_BASE(L59)、EQUIP_SLOT_SCALING(L68)
- `game/data/shop.py`（557 行）：SHOP_EQUIP(L432)、SHOP_WEAPONS(L251)
- `game/data/craft.py`：CRAFT_RECIPES **352 个配方全部带 roster_id**（0 个无名册兜底）
- `game/core/craft.py`：`craft_recipe_make`(L9)
- `game/commands/economy.py`（6134 行）：锻造 L2208/2371、强化 L2673、升级 L2879、进化 L3505、炼成 L3598、附魔 L3664、商店购买 L5934-5945/L6060-6074、`_buy_weapon`(L4717)、`_shop_equip_roster`(L4692)
- `game/core/smith_stock.py`：`buy_stock_item`(L341)、`roll_stock`(L132)
- `game/core/enchant.py`：`enchant_value`(L7)
- `game/engine.py`：`player_final_stats` 装备属性聚合 L425-465
- 动态验证：Python 实跑生成函数（seed 固定对比、100 次重复统计）

## 结论摘要

### 问题 1：不同的装备是不是都存在不同的属性？→ **是，属性按"部位+等级+品质"公式区分，各装备差异化充分**
- 属性体系 = 确定性公式（部位模板 base/scaling × 品质倍率 × 等级）+ 名册/随机差异化层（前缀风味、武器类型风味、词条、传说专属、套装）。
- **部位间区分**：`equip_stats`（stats.py L74-87）按 EQUIP_SLOT_BASE/SCALING 给 7 个部位不同属性键——武器 atk/matk、头盔 def/hp、护甲 def/hp、护腿 def/hp、靴子 def/spd、戒指 atk/matk、项链 mdef/hp（stat_templates.py L59-75）。武器/戒指额外带 crit、项链额外带 mdef（stats.py L83-86）。
- **品质间区分**：QUALITY mult 白1.0/绿1.3/蓝1.55/紫1.75/橙2.0（equipment.py L13+）直接缩放属性；crit 加成也只对蓝+品质生效（stats.py L82）。
- **等级间区分**：`(base + scaling*lv)` 线性成长（stats.py L79）。
- **名册内区分**：631 件名册装备，每件有独立 name/slot/lv/quality/series/source/req（equip_roster.py L12+），572/631 件挂固定词条（SERIES_FIXED_AFFIX），74 件橙装带专属 legendary（实测 roster 数据）。
- **白装全确定**：白装无词条（AFFIX_COUNT.white=0，equipment.py L281）、无随机加成 → 同一件白装每次生成 stats 完全相同（实测 `eq_tie_jian` 50 次 (stats,affixes) 组合唯一）。

### 问题 2：装备给的数值有没有随机一个范围的？→ **基础属性无随机范围；随机性来自"词条选择"而非"数值区间"**
- **基础属性（equip_stats）纯确定性**：`equip_stats` 源码无任何 random 调用（实测 `inspect` 确认），数值 = int((base + scaling*lv) × mult)，固定点值、无 ±x% 浮动区间。
- **词条选择随机**：随机装备 `roll_affixes`（affix.py L78-100）从 AFFIX_POOL_BY_QUALITY 按品质/部位过滤后 `random.sample` 抽取；名册装备 `generate_roster_equip`（drops.py L315）固定词条 + `random.sample` 随机补足到品质标准数（蓝 2/紫 3/橙 3，橙 20% 概率 4 条，drops.py L300-303）。
- **词条数值固定**：`stat_affix_stats`（affix.py L107-130）折算值为固定常量（crit_up=+0.05、hp_up=白板基础 5% 等，_STAT_AFFIX_FX L32-73）——同一条词条对同一件装备加的数值相同，随机只在"抽中哪些词条"。
- **附魔/炼成有随机**：附魔大成功 5%（Lv.10 大师 10%）1.5 倍（economy.py L3883-3886、enchant.py L7-22）；炼成 90% 正面 +3% / 10% 负面 -1% 随机属性（economy.py L3640-3643、calamity.py L18-23）。
- **铁匠铺货架价格随机**：price_mult uniform(0.8, 1.2)（smith_stock.py L389、L242）。

### 问题 3：每件装备有没有设定独特的属性数值？→ **"独特性"分层：名册有独特配方，数值本身是共享公式；同一名册装备多次获得属性不同（词条组合随机），白装完全相同**
- **名册装备无手写 stats**：EQUIP_ROSTER 每件只配置 name/slot/quality/lv/series/req/legendary/source（equip_roster.py L12+），**不含 stats 字段**（实测 0 处 "stats" 键）——数值全由 `equip_stats` 公式推导，没有"每件手写的独特数值"。
- **同一名册装备 100 人锻造/掉落 → 基础属性完全相同，词条组合不同**：实测 `eq_xiang_mu_dun` 50 次得 16 种 (stats,affixes) 组合、`eq_sheng_guang_chang_jian` 15 种、`eq_jin_gou_wan_dao` 51 种（橙 20% 4 词条拉大差异）；`eq_tie_jian`（白装）1 种。stats 字典本身在无随机词条时逐位相同（如圣光长剑固定 atk48/matk48/crit0.046），随机只体现在词条→折算进 stats 的小数加值。
- **随机装备独特**：`generate_equip` 名字随机（前缀池+后缀池，drops.py L176-187）、套装随机（L190-198）、橙装随机挂 1 个传说专属（L253）、词条随机 → 200 次实跑 131 个不同名字，每件几乎不重复。
- **锻造/商店/Boss/图纸全部走名册**：352 个锻造配方 100% 带 roster_id（craft.py 数据实测）→ `craft_recipe_make` → `generate_roster_equip`（craft.py L19-21）；商店 SHOP_EQUIP/SHOP_WEAPONS 也是名册 ID 引用（shop.py L432+、economy.py L5934-5945/L6060-6074、L4717-4719）；Boss/精英掉落从名册就近抽取（drops.py L151-162）。**唯一的"非名册"路径是掉落兜底 `generate_equip`（drops.py L161）**。
- **强化/升级/进化/炼成改的是同一份 stats**：强化 +N 只写 `d["enhance"]` 标记（economy.py L2769 附近），升级写 `d["upgrade_lv"]`（L2913），引擎聚合时乘 mult（engine.py L425-436）；进化=重造新名册装备并继承 enhance/upgrade_lv（economy.py L3576-3582）；炼成写 `d["calamity_bonus"]` 独立叠加（economy.py L3644-3647、engine.py L458-462）；附魔写 `d["enchant"]` 列表（economy.py L3888）。均不动生成公式本身。

## 证据清单（文件:行号）
1. **stats.py:74-87** `equip_stats`：`stats[k] = int((base[k] + scaling[k]*lv) * mult)`——纯公式、无 random，数值为固定点值。
2. **stat_templates.py:59-75** EQUIP_SLOT_BASE/SCALING：7 部位各自属性键（weapon atk/matk、helm def/hp、armor def/hp、legs def/hp、boots def/spd、ring atk/matk、necklace mdef/hp）→ 部位区分。
3. **equipment.py:13-30** QUALITY mult（白1.0/绿1.3/蓝1.55/紫1.75/橙2.0）→ 品质区分。
4. **stats.py:82-86**：weapon/ring 蓝+品质加 crit、necklace 蓝+加 mdef → 部位/品质额外差异化。
5. **affix.py:78-100** `roll_affixes`：`random.sample(pool, min(n, len(pool)))`，AFFIX_COUNT 白0/绿1/蓝2/紫3/橙[3,4]（20% 4 条）→ 随机装备词条数随机。
6. **affix.py:102-105** `fixed_affixes`：SERIES_FIXED_AFFIX 按名称查，无随机 → 名册固定词条。
7. **affix.py:107-130** `stat_affix_stats`：词条折算值 = _STAT_AFFIX_FX 固定常量（crit_up 0.05/hp_up 白板 5%/pene_flat max(2, lv*0.5)）→ 词条数值无随机范围。
8. **drops.py:264-330** `generate_roster_equip`：base stats=equip_stats 公式（L276），随机仅 `random.sample` 补词条（L315）、橙 20% 4 词条（L300-303）。
9. **drops.py:165-261** `generate_equip`：名字随机（L176-187）、套装随机（L190-198）、橙装随机 legendary（L253）、词条随机。
10. **drops.py:151-162**：掉落兜底才走 `generate_equip`，正常走名册就近抽取（±15 → ±30）。
11. **craft.py(L9-27, core)**：`craft_recipe_make` 有 roster_id → `generate_roster_equip`；**实测 352/352 配方带 roster_id**（game/data/craft.py 全量统计）→ 锻造 100% 名册生成。
12. **economy.py:5934-5945 / 6060-6074**：商店装备购买 = `C.generate_roster_equip(rid)`。
13. **economy.py:4717-4719** `_buy_weapon`：名册名走 `generate_roster_equip`。
14. **shop.py:432-470** SHOP_EQUIP：key = 名册 ID 列表；**shop.py:251+** SHOP_WEAPONS：(名字,类型,等级,品质) 四元组 → 也经名册解析。
15. **economy.py:2225-2239**：品质升华重算 `equip_stats`（换品质 mult）；**MASTERPIECE_CHANCE=0.02**（battle_config.py L227）精良 ×1.15 全属性。
16. **economy.py:2769 / 2913 / 3576-3582 / 3644-3647**：强化/升级/进化/炼成只写标记字段（enhance/upgrade_lv/继承/calamity_bonus），不另算属性。
17. **engine.py:425-436 / 444-447 / 458-462**：装备 stats 聚合 = item["stats"] × 强化 mult × 升级 mult + enchant 列表 + calamity_bonus → 同一份 stats 被直接消费。
18. **smith_stock.py:389 / 242**：货架价格 random.uniform(0.8,1.2)（价格随机，属性不随机）。
19. **equip_roster.py 全文件**：631 件名册，0 个 "stats" 字段（实测 grep）→ 无手写独特数值，数值全推导。
20. **实测数据**：`eq_tie_jian` 50 次 (stats,affixes) 唯一（白装全确定）；`eq_xiang_mu_dun` 16 种/50 次、`eq_sheng_guang_chang_jian` 15 种、`eq_jin_gou_wan_dao` 51 种（橙 4 词条拉大）；`generate_equip` 200 次 131 个不同名。

## 影响面评估（若按"每件装备独特数值"改造）
- 当前"独特"由 名册配置（lv/slot/quality/req/legendary/series）+ 固定词条 + 随机补足词条 共同实现，已具备差异化。若追求"每件装备手写独特数值"（类似暗黑传奇装）：
  1. `game/data/equip_roster.py` 每件加 stats 覆盖字段 + `generate_roster_equip`（drops.py L264+）改读 r["stats"] 优先；
  2. `equip_stats` 公式（stats.py L74）保持不变作为白板基准；
  3. 需同步价格推导 `equip_value`（stats.py L94）与 强化/升级 mult（engine.py L425-436）口径；
  4. 随机装备路径（generate_equip）可加"数值波动 ±%"——当前无此设计，是三个问题里唯一"无随机范围"的点。
- 若维持现状：属性差异化已经由 部位×品质×等级×词条×专属 五层保证，唯一弱点是**白装（35 件）完全同质**（无词条、纯公式），以及**同品质同级同名册装备基础属性逐位相同**（差异化只靠词条组合）。

## 收尾验证
- git status：无 tracked 改动（仅他人审计遗留 untracked 文件）；无临时脚本残留；未跑全量回归（仅单文件数据统计 + 生成函数实跑，只读）。
