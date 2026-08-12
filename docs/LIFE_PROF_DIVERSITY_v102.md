# 生活技能差异化设计 v102.3（垂钓/烹饪/炼金/挖掘/采集）

> 2026-08-12 鱼鱼："问个问题，垂钓，烹饪，炼金，挖掘，采集，值得玩家选择的有意义的点是什么"→"你来调整和优化以及丰富"
> 原则：数据驱动扩展（加内容不改代码），稀缺品走生活渠道不走战斗掉落，掉率按"一天刷几个"反推。

## 现状盘点（侦察结论）

| 技能 | 已有 | 缺口 |
|---|---|---|
| 垂钓 | 品质权重表/钓点禁出/图鉴/鱼王/宝物/彩蛋鱼/宠物蛋/坐骑/生活渠道稀有品（v101.13-15） | 无大缺口；补"鱼饵"技能互链 |
| 烹饪 | 13 个食物效果注册器（吸血/破甲/连击/元素/回春/冥想等）+ hot 持续恢复（v101.28e） | 高级食谱缺稀有材料链 |
| 炼金 | 16 配方：治疗/魔力/强化石/回城/攻防速暴药水/蛟人之泪/龙涎药剂（v101.28f special/buff 机制） | 缺稀有材料链闭环 |
| 采集 | 地图绑定池 61+ 图（v97.2）+ 稀有判定彩蛋（月光兔蛋/驯鹿缰绳） | **无时机钩子**：任何时段采到的都一样 |
| 挖掘 | 地图矿石池 + 稀有矿脉（Lv.4+ 15%/Lv.7+ 30%，v101.28k） | **无地点钩子**：矿洞图无专属矿 |

## 设计目标：每个技能一个"只有它能给的" + 一个"独有的过程乐趣"

1. **采集 = 时机**：特定时段/季节/天气才出的限定材料（月光草只在夜晚…）
2. **挖掘 = 地点**：矿洞类地图专属深矿（秘银/精金只在矿洞挖到）
3. **烹饪 = 备战**：高级 buff 料理需要限定材料（采集/垂钓供给）
4. **炼金 = 续航**：高级药水需要限定材料 + 深矿（采集/挖掘供给）
5. **垂钓 = 收集**：已有图鉴/鱼王；新增鱼饵（烹饪/炼金产出）提升稀有档概率 → 技能互链

## 新增数据（全部数据驱动）

### 1. 限定采集物 GATHER_COND_POOLS（新表，gather_pools.py）
地图 → [(材料, 权重, 条件)]；条件：`night`(20:00-05:00) / `morning`(05:00-08:00) / `winter`(季节) / `rain`(天气)
```
silverwood:      [(mat_night_mushroom, 8, night), (mat_moon_dew, 6, night)]
misty_swamp:     [(mat_night_mushroom, 10, night)]
permafrost_field:[(mat_aurora_flower, 6, winter+night)]  # 冬季夜晚专属
emerald_forest:  [(mat_thunder_vine, 8, rain)]
redridge_plateau:[(mat_thunder_vine, 8, rain)]
white_deer_forest:[(mat_moon_dew, 8, night)]
```
新增材料（items.py）：
- mat_night_mushroom 夜雾菇 120 金（夜晚，银木林/迷雾沼泽）
- mat_aurora_flower 极光花 300 金（冬季夜晚，永冻原野）
- mat_thunder_vine 雷雨藤 250 金（雨天，翡翠森林/红脊高原）
- mat_moon_dew 月露 180 金（夜晚，白鹿森林/银木林）

### 2. 深矿池 MINING_DEEP_POOLS（新表，prof_config.py）
矿洞类地图专属深矿（替代价格区间兜底）：
```
hill_mine:    [mat_mi_yin(秘银), mat_jing_jin(精金), mat_deep_crystal(深渊水晶)]
deep_tunnel:  [mat_jing_jin, mat_deep_crystal, mat_star_iron(星铁)]
sea_cave:     [mat_shui_jing(水晶), mat_deep_crystal]
```
新增材料：mat_deep_crystal 深渊水晶 350 金、mat_star_iron 星铁 600 金

### 3. 烹饪稀有食谱（cooking.py 新增 5 配方）
| 配方 | 材料 | 效果 |
|---|---|---|
| 夜雾菇浓汤 | mat_night_mushroom×2 | food_effect: regen + hot 回血 |
| 月光草茶 | mat_yue_guang_cao×2 | food_effect: meditate（回蓝） |
| 极光花蜜 | mat_aurora_flower×1 + mat_mian_fen×1 | food_effect: aurora_guard（新：受击减伤） |
| 龙血火锅 | mat_long_xue_cao×1 + mat_shou_rou×3 | food_effect: charge + hot |
| 雷雨藤烤串 | mat_thunder_vine×2 | food_effect: static（新：攻击附带麻痹减速） |

### 4. 炼金稀有药水（alchemy.py 新增 3 配方）
| 配方 | 材料 | 效果 |
|---|---|---|
| 月露精华 | mat_moon_dew×2 + mat_kong_ping×1 | special: heal_up 强化治疗（v101.28f 已有机制） |
| 深渊水晶药剂 | mat_deep_crystal×1 + mat_kong_ping×1 | special: magic_resist 魔抗（已有机制） |
| 星铁强化剂 | mat_star_iron×1 + 强化石×1 | 精炼强化石：强化成功率提升（强化链） |

### 5. 垂钓鱼饵（新消耗品 + 轻量机制）
| 鱼饵 | 产出 | 效果（使用后下次垂钓） |
|---|---|---|
| it_glow_bait 萤光鱼饵 | 炼金：mat_yue_guang_cao×1+mat_kong_ping×1 | 紫/橙档概率 ×2 |
| it_dough_bait 面团鱼饵 | 烹饪：mat_mian_fen×2 | 绿/蓝档概率 ×1.5 |
| it_blood_bait 血饵 | 烹饪：mat_shou_xue×2 | 稀有鱼种概率提升（spot 限定） |

## 机制改动（最小挂点）

1. `_gather_roll`/`_settle_gather`：读 GATHER_COND_POOLS → 当前条件满足时低权重追加限定材料；限定材料特殊文案
2. `_settle_mining`：当前地图 ∈ MINING_DEEP_POOLS → 深矿池优先
3. `_settle_fishing`：读鱼饵状态（event_state key `bait_<qq>`）→ 品质权重临时加权
4. `use`/item_templates：新增 `bait` 模板（battle_ok=False，使用后写鱼饵状态 + 播报）
5. `food_effects.py`：新增 aurora_guard（TAKEN 减伤）、static（HIT 附带减速）两个注册效果

## 掉率按"一天刷几个"反推

- 采集限定材料：每次采集 5-10% 概率出（夜晚采集 10 次 ≈ 1 个夜雾菇；一天夜晚时段能采 3-5 轮 → 一天 1-2 个）→ 稀有但不绝望
- 深矿：Lv.4+ 稀有矿脉已 15%/30%；深矿图普通矿也有 15% 概率出秘银级 → 矿洞图"挖矿必有所值"
- 鱼饵：一次 1 个，垂钓 1 次消耗；萤光鱼饵 20% 概率钓到紫/橙（基准紫 ~8%/橙 ~3% → 翻倍 ~16%/6%）

## 验收清单

- [ ] 新材料 6 种（4 采集限定 + 2 深矿）入 items.py，价格/名称规范
- [ ] GATHER_COND_POOLS 生效：夜晚采集银木林可出夜雾菇，白天不出
- [ ] 深矿池生效：山丘矿洞可挖秘银/精金/深渊水晶
- [ ] 新配方 8 个（烹饪 5 + 炼金 3）可学习/可制作，材料扣减正确
- [ ] 新食物效果 2 个在战斗中生效（aurora_guard 减伤 / static 减速）
- [ ] 鱼饵 3 种：制作→使用→垂钓品质加权→消耗
- [ ] 单测全过 + 实机验证
