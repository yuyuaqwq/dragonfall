# R4 装备属性-策划案对照报告（固定 vs 随机设计意图）

> 审计时间：2026-08-30 · 审计方式：只读对照（未改任何代码/数据，未 commit）
> 对照对象：design 仓库 `design/new_world/`（10 章装备体系 / 32 章数值设计）↔ 插件代码 `game/`

## 覆盖范围

- `design/new_world/10_装备体系.md`（901 行）：装备属性/词条章节全文核读
- `design/new_world/32_数值设计.md`（748 行）：装备数值/品质/价格章节核读
- `game/data/equip_roster.py`（946 行）：名册 180+ 条装备定义
- `game/core/drops.py`（502 行）：`generate_roster_equip` / `generate_equip` / 掉落引擎
- `game/core/affix.py`（148 行）：`roll_affixes` / `fixed_affixes` / `stat_affix_stats` / `random_req`
- `game/data/affixes.py`（1195 行）：AFFIXES 45 词条 + AFFIX_POOL_BY_QUALITY + SERIES_FIXED_AFFIX + LEGENDARY_EFFECTS
- `game/data/equipment.py`（334 行）：QUALITY 倍率 / WEAPON_FLAVOR / AFFIX_COUNT
- `game/data/stat_templates.py`：EQUIP_SLOT_BASE / EQUIP_SLOT_SCALING（装备属性公式底座）
- `game/core/stats.py`（117 行）：`equip_stats` 装备属性公式
- `game/core/craft.py`（67 行）：锻造走名册精确生成
- `game/commands/economy.py`（6134 行，抽样）：`_buy_weapon` 商店装备生成（4714-4726 行）
- `game/core/smith_stock.py`（406 行，抽样）：铁匠铺货架生成（300-334 行）
- `game/data/gems.py`（67 行）：原石系统（护石式随机属性，装备之外的另一系统）

## 结论摘要

1. **策划案设计意图 = 基础数值确定性 + 词条随机**。策划案明确：基础数值按「品质倍率 × 等级基数」的确定性公式计算，「保证同品质同级装备数值平衡」（10_装备体系.md:319）；随机性只放在**词条**（固定词条 + 随机补足）与获取流程（掉落哪件/锻造品质跳级/价格浮动）上——**策划案从未设计"属性数值随机范围"**，最硬证据是 10 章"设计保证 #1：词条是'风格差异'不是'强度碾压'——同品质装备词条总强度相近，玩家选的是风格不是数值"（10_装备体系.md:626）。
2. **代码与策划案一致，无随机扰动**。`equip_stats` 是确定性公式 `int((base + scaling*lv) * mult)`（game/core/stats.py:74-86）；名册装备的 stats 全部由该公式派生，名册 dict 里**没有 stats 字段**（equip_roster.py 全文件），`generate_roster_equip` 对 stats **不做任何随机扰动**（drops.py:264-352）——随机仅存在于：随机补足词条 ID（random.sample，drops.py:315）、橙装 20% 概率 4 词条（drops.py:300）、掉落选哪件名册装备（drops.py:148-162）、锻造品质 5% 跳级（32_数值设计.md:609）。
3. **鱼鱼问题直接回答**：
   - 「装备数值有没有随机范围？」→ **没有**。同品质同级同部位装备的基础数值完全相同（唯一个体差异来自随机词条折算，而词条折算值本身也是固定值，affix.py:41-75 `_STAT_AFFIX_FX` 固定 flat/pct）。
   - 「每件装备有没有独特属性数值？」→ 名册装备的"独特"来自固定词条/武器类型风味/传说专属折算进 stats（drops.py:277-324），**数值本身不是手工填写的独特值**；随机生成装备（generate_equip）存在词条个体差异，但同一件名册装备（同 rid）反复生成，stats 完全相同、只有补足词条 ID 不同。
   - 「如果要每件装备独特数值」→ 当前"名册固定 + 词条随机"已兑现策划案的流派区分度；**数值范围 roll 是策划案之外的新增层**，需策划背书（与"同品质同级数值平衡"设计保证有张力），最自然改法是 `generate_roster_equip`/`generate_equip` 生成 stats 后加 ±范围 roll 并同步重算价格（价格已按 stats 实时推导，drops.py:332）。

## 证据清单

### 一、策划案：装备属性设计原文

| # | 证据 | 内容 | 含义 |
|---|------|------|------|
| P1 | design/new_world/10_装备体系.md:3 | 「落地时装备字段：基础数值（品质倍率）+ `affix`（词条）+ `req`（属性需求）」 | 装备=确定性基础数值+词条，无"随机范围"字段 |
| P2 | design/new_world/10_装备体系.md:10 | 「4. **锻造配方确定性**：材料+图纸，装备名=配方名，不随机」 | 名册/锻造装备确定性是顶层设计原则 |
| P3 | design/new_world/10_装备体系.md:314,319 | 「攻击 +8 ← 基础数值（品质倍率 × 等级基数）」「**基础数值**：按品质倍率算（白1.0/绿1.3/蓝1.6/紫1.8/橙2.0），**保证同品质同级装备数值平衡**」 | 基础数值=确定性公式，明确"平衡"而非"浮动" |
| P4 | design/new_world/10_装备体系.md:320 | 「**特色词条**：每件装备 1-3 条（品质越高条数越多），**词条决定装备的'性格'**，同部位同级不同词条 = 不同流派选择」 | 装备差异性的载体是**词条**，不是数值浮动 |
| P5 | design/new_world/10_装备体系.md:423-434 | 「2.3 词条分配规则：白 0 条 / 绿 1 条（固定）/ 蓝 2 条（固定+随机 1 条）/ 紫 2+特效 / 橙 3+专属」；「固定词条：系列主题…」「随机词条：锻造/掉落时从词条库随机」 | 随机粒度 = **词条条数与词条种类**，与数值无关 |
| P6 | design/new_world/10_装备体系.md:571-578 | 「4.1 掉落词条：**商店/固定锻造：固定词条（系列主题），无随机**；普通怪掉落：绿 1 条（固定）、蓝 2 条（固定+随机）；精英/Boss：紫 2+特效、橙 3+专属；图纸锻造：固定 + 按图纸品质带随机词条」 | 策划案对"随机"的全部表述都指向词条 |
| P7 | design/new_world/10_装备体系.md:580-592 | 「4.2 随机词条池（按品质）：蓝 19 项 / 紫 / 橙全部」「4.3 锻造时『锻造 <装备> <词条倾向>』从对应池随机」 | 随机池 = 词条池（AFFIX_POOL_BY_QUALITY），无数值范围池 |
| P8 | design/new_world/10_装备体系.md:626 | 「设计保证 #1：**数值不爆炸**：词条是'风格差异'不是'强度碾压'——同品质装备词条总强度相近，玩家选的是风格不是数值」 | **核心证据**：数值刻意做平、随机只在风格维度 |
| P9 | design/new_world/32_数值设计.md:527-539 | 「11.9 装备成长与品质：部位 base + 每级成长（武器 atk/matk 3 +1.0、胸甲 def4 hp15 +0.9/+6…）」「品质倍率：白1.0/绿1.3/蓝1.6/紫1.8/橙2.0」 | 数值权威文档给的也是**确定性公式表**，无任何区间 |
| P10 | design/new_world/32_数值设计.md:607-610 | 「12.4 锻造品质随机：锻造 5% 概率品质+1（蓝→紫→橙，橙不变）；橙装 2% 出'精良'前缀（×1.15）」 | "随机"在锻造处体现为**品质跳级**，仍非属性数值范围 |
| P11 | design/new_world/32_数值设计.md:593 / 10_装备体系.md:729 | 「价格：推导价 × 品质系数 × 0.8~1.2 浮动」 | 唯一的数值范围随机是**价格**，不是属性 |
| P12 | design/new_world/32_数值设计.md:193 | 「显示价与购买价同源（同一函数），**防词条随机导致价格漂移**」 | 连词条随机都只影响"是否漂移"，数值随机无存在空间 |
| P13 | design/new_world/10_装备体系.md:617 | 落地映射：「装备生成：`generate_equip` 扩展：基础数值 × 品质倍率 + 按品质挂词条（固定 + 随机池）」 | 策划案亲自指定实现 = 确定性数值 + 随机词条池 |

### 二、代码实现

| # | 证据 | 内容 | 说明 |
|---|------|------|------|
| C1 | game/core/stats.py:74-86 | `equip_stats`: `stats[k] = int((base[k] + scaling[k]*lv) * mult)`；crit/mdef 附加同为确定性公式 | **基础数值纯确定性，无 random 调用** |
| C2 | game/data/stat_templates.py:59-79 | `EQUIP_SLOT_BASE`（weapon atk/matk 3…）/ `EQUIP_SLOT_SCALING`（weapon +1.0…） | 与 32 章 11.9 表一一对应，公式底座 |
| C3 | game/data/equipment.py:13-39,280-289 | `QUALITY` mult：白1.0/绿1.3/蓝1.55/紫1.75/橙1.95；`AFFIX_COUNT`：白0/绿1/蓝2/紫3/橙[3,4] | 品质倍率落地（与策划案 1.0/1.3/1.6/1.8/2.0 近似取整口径） |
| C4 | game/data/equip_roster.py:15-471 | `EQUIP_ROSTER` 每件 = 固定 dict：name/slot/weapon_type/quality/lv/series/req/legendary/set/source——**全文件无 stats 字段** | 名册不存数值，数值全由 C1 公式派生 |
| C5 | game/core/drops.py:264-352 | `generate_roster_equip`：`stats = equip_stats(...)`（275 行）→ 武器风味（277-295）→ 词条折算（317-321）→ 传说专属折算（323-324）→ 直接作为装备 stats（331 行）。**全程无 random 扰动数值**；唯一 random 在 300-315 行：橙装 20% 4 词条 + `random.sample` 补足词条 ID | 直接回答任务卡问题：**generate_roster_equip 不对名册 stats 做随机扰动** |
| C6 | game/core/drops.py:165-261 | `generate_equip`（随机兜底装备）：名字/套装/词条/传说专属随机，但 stats 仍是 `equip_stats` 公式值（200 行）+ 前缀/风味/词条固定折算 | 随机装备数值同样无范围 roll |
| C7 | game/core/affix.py:78-104 | `roll_affixes`：按 AFFIX_COUNT 随机抽样词条 ID；`fixed_affixes`：按名称查 `SERIES_FIXED_AFFIX`（无随机） | 随机粒度=词条 ID，与策划案 P5/P6 完全一致 |
| C8 | game/data/affixes.py:19-79,455-528,669+ | AFFIXES 词条 effect 全为**固定值**（bleed chance 0.20/dot_pct 0.05、crit_up crit 0.05…）；AFFIX_POOL_BY_QUALITY 随机池；SERIES_FIXED_AFFIX 按装备名固定词条 | 词条数值固定，无范围字段 |
| C9 | game/core/affix.py:41-75,107-130 | `_STAT_AFFIX_FX`：属性词条折算固定 flat（0.05 等）/pct（5%）/lv_flat（0.5/lv） | 折算值固定 → 同词条个体无差异 |
| C10 | game/core/drops.py:148-162 | `roll_drop_equip`：随机选名册 ID（|lv差|≤15 优先 → ±30 → 兜底 generate_equip），选中后 `generate_roster_equip` 精确生成 | 掉落随机 = **选哪件**，不是数值 |
| C11 | game/core/craft.py:9-29 | 锻造：`roster_id` 配方 → `generate_roster_equip(rid, affinity)` 精确生成（词条倾向 20 章 4.3 落地） | 锻造确定性 + 词条随机，兑现 P2/P7 |
| C12 | game/commands/economy.py:4714-4726 | `_buy_weapon`：名册名 → `generate_roster_equip` 精确生成（正确 req + 固定词条）；非名册兜底 → `generate_equip` 随机 + 覆盖名 | 商店同源，名册装备数值确定 |
| C13 | game/core/smith_stock.py:300-334 | 铁匠铺货架：随机选名册装备 + `price_mult: round(random.uniform(0.8, 1.2), 1)` | 0.8~1.2 浮动 = **价格**（P11 落地），装备 stats 本身仍确定 |
| C14 | game/data/gems.py:44-67 | 原石：护石式**随机属性**（"怪猎护石式随机属性"）+ Boss 固定倾向 | 若玩家要"随机属性"体验，系统已通过**原石**提供，装备本体未做 |

### 三、差距/结论

1. **设计意图 vs 实现：一致，无设计性偏离**。策划案（P1-P13）与代码（C1-C13）在"固定 vs 随机"上完全对齐：**固定 = 基础数值（品质倍率 × 等级基数）、名册 req、固定词条、传说专属、词条数值；随机 = 词条 ID 选取、掉落选件、锻造品质跳级、价格 0.8~1.2**。装备属性区分度当前由"词条随机 + 系列固定词条 + 武器类型风味"提供——与策划案 10 章 626 行"选风格不是选数值"的设计保证一致。
2. **鱼鱼问题核实结果**：
   - 「装备数值有没有随机范围？」→ **无**。equip_stats 确定性公式（C1），同品质同级同部位数值恒定；全链路 grep 未发现任何装备属性数值 roll（唯一数值 random 是 smith_stock 的价格 mult，C13）。
   - 「每件装备有没有独特属性数值？」→ 名册装备**没有手工 stats**（C4），数值=公式派生+词条/风味/专属折算（C5），故"独特"体现在词条组合而非数值；随机装备（generate_equip）同样如此。
3. **若要实现"每件装备独特数值"（数值范围 roll）**：
   - 现状评估：**名册固定 + 词条随机已满足策划案全部随机性要求**；数值范围 roll 是策划案未设计的扩展，直接加会与 P3「保证同品质同级装备数值平衡」和 P8「选风格不是选数值」冲突，**应先获策划背书**。
   - 最自然的改法：`generate_roster_equip`/`generate_equip` 在 `stats = equip_stats(...)`（drops.py:275/200）之后加 `per-instance` 浮动（如各主属性 ×random.uniform(0.95,1.05)），价格自动跟随（`equip_value(stats)` 实时推导，drops.py:332）无需改定价链路；锻造/商店/掉落三渠道共用这两个函数，改一处全渠道生效。
   - 已存在的替代路径：原石系统（C14）已提供"护石式随机属性"追求，可作为"数值随机"需求的既有承载，不必动装备本体。
4. **收尾验证**：插件主仓库 `git status` 无 tracked 改动（仅历史遗留 untracked 文件，非本次产生）；design 仓库干净。未创建临时脚本。

## 影响面评估（R4 相关，仅提示不执行）

- 若决定加数值范围 roll：只动 `game/core/drops.py` 两个生成函数 + 可能同步 `smith_stock._smith_equip_price`（312-333 行，价格推导需与生成口径一致，防显示价≠购买价——P11/32 章 193 行铁律）。
- 需策划更新：10 章 1.1（319 行）、32 章 11.9（527-539 行）补"数值浮动区间"说明，并修订 10 章 626 行设计保证。
