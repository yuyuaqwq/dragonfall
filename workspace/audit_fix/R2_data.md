# R2 任务卡：数据层修复（死数据删除 + 材料倒挂 + 定价 + desc 术语）

## 背景
v130.2d 审计发现（跨表/数据驱动/文案三份审计汇总）：
- P1：affixes.py 的 V130_RESOURCE_SET_BONUSES 与 sets.py 双处定义且前者**零消费**（死数据炸弹）
- P2：4 张套装配方**材料等级倒挂**（低级装备用高级材料，图纸到手锻不出）
- P1：圣徽·誓约「新手保底」套定价 2676 金背离新手曲线
- P2×2：desc 与实现不符（元素风暴→元素湮灭、满档限定、气力技、沸血二段术语）；holy_heart 传说词条上蓝装（品质外溢）；precise 词条 desc 未披露伤害加成
- 数据字段补充（供 R1 消费端读取）：猎首 min_cost、日冕 miracle_min、影纱 max_layers、暗夜圣典 cond、sigil_engrave max_total

## 修复清单

### 1. 删除死数据（P1）
- affixes.py≈813-900 整段 `V130_RESOURCE_SET_BONUSES`（含标题注释「# ==== v130.2 装备-资源联动：套装效果…」）删除——已 100% 迁入 sets.py（sets.py:575-645 逐字段与之一致）。
- sets.py:576 附近注释改写为「效果定义已自 affixes.py V130 段迁入（v130.2d）；战斗侧消费见 battle.py SET_EFFECT_CONSUMED」。
- 删后验证：`grep -rn "V130_RESOURCE_SET_BONUSES" game/` 零命中（仅测试无引用）。

### 2. 配方材料等级倒挂（P2，craft.py）
- 巡林长披风（40，craft.py≈1949）与巡林长弓（42，≈1959）：现用月狼毛皮/精灵鹿角（Lv.55+ 材料）→ 换 Lv.30-45 带材料（参照：圣光结晶/海妖鳞片/水手·白鹿系材料，读 game/data/items.py MATERIALS 找 30-45 级材料 ID）。
- 影纱面巾（50，≈2099）与影纱轻靴（50，≈2129）：现用霜巨魔血（Lv.62+）→ 换 Lv.50 带材料（精灵鹿角/海妖鳞片或同级）。
- 破竹护腿/布靴（52，≈2179/2189）低材高用（精铁×4/史莱姆黏液×4，Lv.1-18 带）→ 换圣殿铁块/海妖鳞片同级材料，对齐破竹武袍成本曲线。
- 每张配方改完核对：材料 exist、数量合理、成本曲线对齐同级（lv×8+20 曲线）。

### 3. 圣徽·誓约定价（P1，shop.py + equip_roster.py）
- 目标：新手 15-16 级可负担整套（4 件总价 ≤800 金，权杖由 s1 任务免费发放，另 3 件商店价 150-280/件）。
- 读 shop.py SHOP_EQUIP["oak_town"] 与价格生成链路（drops.py≈292 公式 equip_value×(3+lv×0.5)×1.6 或商店 override 字段），选合理改法（商店条目加 override price 字段最稳，若结构不支持则改 equip_roster 对应条目基础价）。
- 对齐参照：白鹿镇绿装 72-100 金档。

### 4. desc 与实现对齐（sets.py + affixes.py）
- sets.py≈595 元素使徒 desc「全耗奥义(元素风暴)」→「全耗奥义(元素湮灭)」（实机匹配的是元素湮灭，skills.py:1539 全耗充能技；元素风暴是高耗纯蓝 AOE 不耗充能）。
- 设计仓 10_装备体系.md≈696 同行同样错误——**设计仓由 R4 改**，你不用动 design/（但报告里记录确认）。
- sets.py≈588 余烬军团 desc「满怒(沸血二段)时」→「满怒时」；battle.py 日志「沸血二段」由 R1 改，你只改 sets.py desc。
- sets.py≈625 暗夜圣典 desc「满档安魂曲/献祭暗焰」：若 R1 实现加 cond（canticle_full）则 desc 保留「满档」；若 R1 未做到则 desc 删「满档」改「安魂曲/献祭暗焰」。**你在本卡先给 effect 加 `"cond": "canticle_full"` 字段，desc 保留**（R1 会读取）。
- sets.py≈652 势不可挡 desc「气力技/终结技」→ 保持，**判定由 R1 收窄为 chi 相关**；desc 改「气力技(耗气) 物理伤害 +15%」让玩家理解。
- sets.py≈616 圣典日冕 desc「二档以上神迹」→ 加 `"miracle_min": 5` 字段 + desc 改「施放耗 5 点以上信仰的神迹技时」。
- sets.py 猎首 effect 加 `"min_cost": 50`；影纱 bonus_5 加 `"max_layers": 8`；元素使徒/余烬军团的 ultimate_cost_reduce/full_rage_pursuit 保持 value 字段（R1 读）。
- affixes.py precise（≈71-75）desc 补伤害披露：「命中＋10%（无视闪避），伤害＋10%」。
- affixes.py sigil_engrave（≈305-310）加 `"max_total": 1`（防多件无帽叠加；R1 消费端按此封顶）。
- affixes.py holy_heart 品质外溢（A4 P3-3）：誓约权杖/日冕权杖固定词条含 orange 品质 holy_heart → 换同级可上皮词条（读该件品质蓝/紫再选适配词条）或降 holy_heart 品质；**选换固定词条方案**（不动词条定义）。

### 5. 顺手
- sets.py 新 12 套条目 `line` 字段加注释「非运行字段，策划说明」（可留原文不动，只加注释）。

## 铁律
- 只改：affixes.py/sets.py/craft.py/shop.py/equip_roster.py（如需）。禁动 battle.py（R1 专）、skills.py（R4 专）、design/（R4 专）。
- 禁 git commit、禁重启 AstrBot、禁跑全量回归。
- 改完 py_compile 全部改动文件 + 验证脚本（GWEN_GAME_DB 私有临时库，用完删）：
  ① grep V130_RESOURCE_SET_BONUSES 零命中 ② 6 张配方材料可解析且等级带合理 ③ 誓约 3 件商店单价（读 SHOP 配置实算/实读）④ sets.py 12 套 effect 含新字段（min_cost/miracle_min/max_layers/cond/max_total 按套核对）⑤ precise desc 含伤害披露。
- 跑相关单测（私有库）：tests/test_stage8_equip_affix.py、tests/test_data_items.py、tests/test_v104_shop_auction_mount.py（若涉及商店）。

## 报告（中文）
修复清单表（问题 | 文件:行 | 改前→改后 | 验证证据）+ 新增字段清单（sets/affixes 字段名表，供主 agent 与 R1 核对）+ 测试结果 + git status 清单。