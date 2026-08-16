# v125 内容扩容计划（2026-08-16）

## 目标
鱼鱼要求：严格数据驱动，增加内容尽量避免直接修改代码；代码不支持就做重构优化（通用化），不为单一内容硬编码。

## 现状侦察（已实测）
- 探索事件 EXPLORE_EVENTS：50 条（34 条带 maps 区域限定），模板注册表 18 个（loot_gold/loot_materials/loot_gold_mats/exp_gain/heal_full/damage/set_state/set_flag/dialog/mystery_chest/merchant/wandering/combo/random_choice/stamina_cost/region_lore/stamina_gift/shrine_bless/rare_find）→ **加事件纯数据零代码**（EVENT_WEIGHT_SUM 自动汇总）
- 彩蛋事件 EXPLORE_EGG_EVENTS：30 条，独立 0.5% 概率 → 同样纯数据
- 68 张野外图：29 张无区域事件覆盖、31 张只有 1 个事件
- 世界事件 WORLD_EVENT_POOL：6 条，但**消费端 if/elif 硬编码**（combat.py omen=经验金币+50%/swarm=经验+30%声望双倍/festival=金币+50%、economy.py merchant=8折）→ **需要重构为 effects 数据驱动**
- 副本 INSTANCE_STAGE_MAPS：66 stage desc 全部 >20 字，不缺 → 不做

## 方案
### 探索事件扩容（零代码，数据片段合并）
- A1 南境区域事件 ~10（misty_swamp/hill_mine/harbor_docks/rockfall_gorge/boar_ridge/silver_wind_road + 南境薄覆盖图）
- A2 中域+西境区域事件 ~10（border_castle/silver_river/old_battlefield/west_ridge_wilds + 中域薄覆盖）
- A3 北境+东境区域事件 ~10（forge_valley/cinder_mountain/dwarf_long_gallery/storm_cliff/dragonborn_valley_trail + 薄覆盖）
- A4 幽暗地域+无尽海+群岛区域事件 ~10（fungus_forest/deep_lake/molten_abyss/lava_bed/abyss_altar/whale_domain/black_tide_strait/sunset_isle/mist_tide_passage/cloud_sea/storm_plateau/rainbow_cloud/starlight_terrace/sky_ladder_path）
- A5 通用事件 +8（模板均衡：补 region_lore/dialog/exp_gain/heal_full/stamina_gift/loot_gold_mats，控制 random_choice）
- A6 彩蛋事件 +10（区域 5 + 全局 5）
### 世界事件 effects 重构（代码，通用化）
- A7：WORLD_EVENT_POOL 每条加 effects 字段（exp_mult/gold_mult/rep_mult/shop_discount 等）；combat.py 战斗结算、economy.py 商店折扣读 cur_evt["effects"] 通用应用；auction/boss 特殊流程保留 type 判断但收益部分 effects 化
### 世界事件池扩容（零代码，数据片段）
- A8：+8 条新事件（丰收祭/仲夏夜/流星雨之夜/矮人商队/海风节/极光之夜/熔火脉冲/潮汐祝福），全部带 effects 字段
### 主 agent 收口
- 合并数据片段 → 验证脚本（地图 id 存在/模板注册/id 唯一/材料 resolve/权重合理）→ 全量回归 → 策划案同步（02 章 7.5/7.6、07 章世界事件）→ 双仓提交 → 重启 AstrBot

## 铁律
- 数据片段放 workspace/（不碰插件目录），主 agent 统一合并
- 命名黑名单：灭世/弑神/虚空/血怒/屠戮/金身/不动如山/百裂/气功/金刚/罗汉/内力/内息
- 事件文案：西幻风、活人感、风景点、有温度；地图 id 必须真实存在
- 材料必须 resolve（中文名，MATERIALS 真实存在）
- weight：常规 3-10、稀有 2-3；无 min_level 字段（事件不锁等级，奖励 scale_lv 自动缩放，文案不写死等级）
