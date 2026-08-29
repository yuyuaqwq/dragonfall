# v136 Phase 6：素材定向 + 职业套装 + 散装 + 区域套 实施详案（2026-08-29）

> 方案源：docs/EQUIP_V136_PLAN.md（v5 定稿）§八装备体系 + §十 Phase 6
> 目标：把名册从 208 件补到 ~300+ 件（职业套装 90 + 散装 50-75 + 区域套 25-35），
>       完成「素材定向」产出闭环（素材→装备绑定 + 产出地可查）。
> 铁律：先策划案→代码→测试→双仓提交；子 agent 只产独立片段文件，主 agent 收尾合并提交。

## 一、范围与数量

| 模块 | 数量 | 说明 |
|---|---|---|
| 职业套装 | 90 件（先 3 阶段） | 6 职业 × 3 阶段 × 5 部位（武器/头盔/胸甲/护腿/战靴） |
| 散装 | 50-75 件 | 每资料片 10-15 件，每件独特词条（词条池大+随机） |
| 区域套 | 25-35 件 | 区域通用装备，过渡/毕业双档 |
| 素材定向 | 补素材 + 产出地 | 系列共享素材组（20:6:1），ENCY_MATERIAL_SOURCE 已有自动构建 |

## 二、职业套装（身份线：软引导，鱼鱼拍板）

### 2.1 命名（复用 sets.py CLASS_SET_THEMES 已拍板命名）

| 职业 | Ⅰ(Lv10) | Ⅱ(Lv30) | Ⅲ(Lv50) | 武器 | 套装主题 |
|---|---|---|---|---|---|
| 战士 cls_zhan_shi | 铁皮 | 精铁 | 骑士 | 长剑(sword) | req力量，攻防 |
| 法师 cls_fa_shi | 学徒 | 符文 | 秘法 | 法杖(staff) | req智力，魔攻冷却 |
| 游侠 cls_you_xia | 猎手 | 风行 | 暗夜 | 长弓(bow) | req敏捷，速度暴击 |
| 牧师 cls_mu_shi | 布衣 | 祝福 | 圣堂 | 权杖(mace) | req智力，治疗护盾 |
| 刺客 cls_ci_ke | 轻影 | 夜行 | 阴影 | 匕首(dagger) | req敏捷，暴击穿透 |
| 拳师 cls_wu_seng | 行者 | 石拳 | 壁槌 | 拳套(fist) | req耐力，格挡反伤 |

### 2.2 装备名册条目（每件 1 条，series=阶段名，set 由 SERIES_SETS 映射）

示例（战士Ⅰ铁皮套）：
```python
"eq_tie_pi_chang_jian": {"name": "铁皮长剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 10, "series": "铁皮", "req": {"str": 10}, "source": "锻造"},
"eq_tie_pi_tou_kui":    {"name": "铁皮头盔", "slot": "helm", "quality": "blue", "lv": 10, "series": "铁皮", "req": {"str": 8}, "source": "锻造"},
"eq_tie_pi_xiong_jia":  {"name": "铁皮胸甲", "slot": "armor", "quality": "blue", "lv": 10, "series": "铁皮", "req": {"str": 10}, "source": "锻造"},
"eq_tie_pi_hu_tui":     {"name": "铁皮护腿", "slot": "legs", "quality": "blue", "lv": 10, "series": "铁皮", "req": {"str": 8}, "source": "锻造"},
"eq_tie_pi_zhan_xue":   {"name": "铁皮战靴", "slot": "boots", "quality": "blue", "lv": 10, "series": "铁皮", "req": {"str": 8}, "source": "锻造"},
```
- 阶段 Ⅱ(Lv30)/Ⅲ(Lv50)：品质 blue→purple 递增（Ⅰ蓝/Ⅱ蓝/Ⅲ紫，对齐 CLASS_SET_STAGES）
- req 按职业主属性：战士 str、法师/牧师 int、游侠/刺客 agi、拳师 str（无 vit req 键？查 random_req 支持——若 vit 不支持用 str）
- **命名唯一性**：与现有名册 208 件比对，杜绝重名（铁皮长剑 vs 铁剑 不冲突；夜行匕首 vs 夜行披风 不同名）

### 2.3 套装效果（_SERIES_SET_BONUS 加 18 条，每条带 class 字段）

| 职业 | bonus_2 | bonus_4_stats | bonus_4.effect |
|---|---|---|---|
| 战士 | atk+8%, def+8% | def+10% | pierce 30%（破甲减防） |
| 法师 | matk+8%, cdr+5% | matk+10% | thunder 25%（追加雷击） |
| 游侠 | spd+8%, crit+3% | spd+8% | dodge_set 闪避+8% |
| 牧师 | heal_power+8%, mdef+5% | mdef+10% | regen（每回合回5%血） |
| 刺客 | crit+5%, atk+8% | crit+5% | execute（低血增伤25%） |
| 拳师 | atk+8%, def+5% | hp+10% | lifesteal_set 30%（吸血15%） |

- **职业折扣（鱼鱼拍板：本职业 100%，非本职业 60%）**：
  - 实现：engine.set_bonus_2 结算时，套装 entry 带 `"class": "cls_zhan_shi"`，
    玩家 `class_name != entry.class` → 属性加成 ×0.6
  - effect 型特效（bonus_4/bonus_5）不打折（机制向非面板向，符合 v136 精神）
- SERIES_SETS 加 18 条："铁皮":"铁皮套" 等；_EQ_SERIES_THEME 加 18 条描述

### 2.4 素材（复用 CLASS_SET_STAGES 素材组，补缺失素材）

| 阶段 | 素材（量产×N + 精英×N + Boss×N） |
|---|---|
| Ⅰ(Lv10) | 狼皮×6 + 野猪皮×5 + 山贼徽章×3 |
| Ⅱ(Lv30) | 鼠狮核心×4 + 兽人獠牙×6 + 座狼犬齿×4 |
| Ⅲ(Lv50) | 圣光结晶×5 + 月影之皮×5 + 龙焰精华×3 |

- 已存在：mat_lang_pi/mat_shou_ren_liao_ya/mat_zuo_lang_quan_chi/mat_sheng_guang_jie_jing
- 需补（items.py）：mat_ye_zhu_pi(野猪皮)/mat_shan_zei_hui_zhang(山贼徽章)/mat_shu_shi_he_xin(鼠狮核心)/mat_yue_ying_zhi_pi(月影之皮)/mat_long_yan_jing_hua(龙焰精华)
- 配方：每件装备 mats = 阶段组（按部位微调数量），gold = lv 对齐现有（约 lv×3+20）
- **素材产出地**：把新素材挂进对应地图怪物的 drops（ENCY_MATERIAL_SOURCE 自动构建 → 『百科 野猪皮』可查）

## 三、散装（自由线：伊甸式开放）

- 不锁职业、不成套、每件独特（词条池大+随机词条）
- 每资料片 10-15 件：橡木白鹿(1-20)/铁港晨曦(15-35)/翡翠月语(30-55)/霜角龙脊(50-75)/龙脊风翼(70-100)
- 命名示例（策划案 8.3 已拍板）：
  - 『猎风披风』= 速度+8%+闪避+3%（谁都能穿）
  - 『熔岩护手』= 火伤+10%+反伤 5%
- 落地：名册 source=锻造/图纸 + 词条走 SERIES_FIXED_AFFIX 固定（独特词条组合）+ 套装不挂 set
- 散装系列：猎风/熔岩/星辉/潮汐/疾风 等独立系列名（不进 SERIES_SETS，避免误入套装体系——equip_roster.py:233 已有注释先例）

## 四、区域套（区域通用）

- 5 资料片 × 过渡/毕业 双档 = 10 套 × 3 件（胸甲/护腿/靴子）= 30 件
- 命名按区域：橡木区(护林套)/铁港区(渡口套)/翡翠区(巡林套)/霜角区(霜猎套)/龙脊区(龙裔套)
  （v136 审计修正：原『水手套』→『渡口』（避开水手系列）、『猎手套』→『霜猎』（避开散装/职业猎手系列），与策划案同步）
- 品质：过渡蓝 / 毕业紫（护林白/蓝、霜猎紫/紫、龙裔紫/橙按 13.8 细表）；req 低（通用，谁都穿得上；霜猎/龙裔高等级段 req 60-90 属区域强度匹配）

## 五、素材定向（产出地可查）

- 现有机制已通：`map 怪物 drops → ENCY_MATERIAL_SOURCE` → 『百科 <素材>』显示产出地
- 本轮：新素材挂地图 drops + 配方 mats 用 20:6:1 结构（量产/精英/Boss 三层）
- 产出地图鉴命令（『百科』已有材料查询，若时间允许补『素材图鉴』聚合页）

## 六、技术方案（防子 agent 冲突）

1. **子 agent 只产独立片段文件**（放 workspace/phase6_frags/）：
   - frag_class_a.py（战士+法师+牧师 45 件）
   - frag_class_b.py（游侠+刺客+拳师 45 件）
   - frag_scatter.py（散装 50-75 件）
   - frag_region.py（区域套 30 件 + 素材）
2. **片段格式**：纯 Python dict 定义（EQUIP_ROSTER 条目 + SERIES_FIXED_AFFIX 条目 + SERIES_SETS 条目 + _EQ_SERIES_THEME 条目 + 素材 items 条目 + 配方 CRAFT_RECIPES 条目）
3. **主 agent 收尾合并**：把片段条目 merge 进 equip_roster.py/craft.py/affixes.py/items.py/sets.py/class_sets.py（先读原内容再拼，铁律）+ 删片段
4. 职业折扣代码：engine.set_bonus_2 加 class 折扣（唯一代码改动，主 agent 亲自做）

## 七、验收

- [ ] 名册新增件数 ≥ 170（90 职业套装 + 50+ 散装 + 30 区域套）
- [ ] 新装备可生成（generate_roster_equip 不抛错）
- [ ] 新配方可锻造（craft_recipe_make 不抛错，素材/金币校验通过）
- [ ] 套装效果结算（set_bonus_2 含职业折扣 ×0.6）
- [ ] 『百科 新素材』有产出地
- [ ] 数值门禁 run_numeric_tests 8/8 + 命令矩阵 + 全量回归（新增测试不破坏既有）
- [ ] 峰值红线：职业套装满配 ≤40%（burst_scan 双约束）
- [ ] 策划案同步（10 章附录三 + 32 章）+ 双仓提交

## 八、风险

- 名册重名冲突（命名比对清单先行）
- 素材 ID 缺失（先补 items.py 再引用）
- 套装效果过强（职业折扣 0.6 + 红线验证兜底）
- 子 agent 产出格式不齐（主 agent 用模板 + 校验脚本兜底）

## 九、审计修正记录（2026-08-29 deleg_b1b886b9 5 路审计 + 主 agent 自查）

### P0（已修复）
1. **游侠套装 id 撞车**：Phase6 新『猎手』装备（eq_lie_shou_pi_mao 等）与旧『猎首远征队』同 id（猎首/猎手同音 pinyin），4 件旧紫装被覆盖（游侠 50-56 断档）。修复：新装备换 id（eq_lie_shou_xin_* / eq_feng_xing_chang_gong / eq_an_ye_chang_gong），旧猎首恢复；配方 key 去重（rec_lie_shou_xin_*）；名册 384→388、配方 348→352、需图纸 200→204。
2. **bonus_4 未注册**：_build_class_sets 漏复制 bonus_4，18 职业套 + 5 区域套 4 件特效静默失效。修复：补 `entry["bonus_4"]`。

### P1（已修复）
3. **区域套 4 件特效不可达**：区域套只有 3 槽位，bonus_4 永远凑不齐 → 新增 bonus_3/bonus_3_stats 档（engine.set_bonus_2 + set_bonus_4 支持），区域套特效 3 件生效。
4. **13 件紫/橙固定词条仅 1 条** → 补足 2 条。
5. **散装月语之戒 series 撞旧月语套** → 改独立系列『月语戒』。
6. **渡口/巡林过渡档无获取渠道** → SHOP_EQUIP.ironharbor（渡口 3 件）+ SHOP_EQUIP.jade_port（巡林 3 件）上架。
7. **霜猎套 element_ice 无效**（非合法 stat）→ 改 crit。
8. **游侠 dodge 10% vs 策划案 8%** → 改 0.08。
9. **素材产出等级错配** → 山贼徽章加挂哥布林斥候 Lv9、鼠狮核心加挂河龙 Lv34、龙焰精华加挂熔岩元素 Lv69（保留高级产出点）。

### P2（已处理/记录）
10. 详案区域套命名滞后（水手→渡口、猎手→霜猎）→ 本文档已同步。
11. 35 件蓝装 2 词条：设计选择保留（蓝装特色，非错误）。
12. 45 件职业套 id 无下划线连写式（eq_tiepichangjian）：风格问题，功能正常，待 v137 统一。
13. 20:6:1 语义 = 量产:精英:Boss 三层掉落权重，非配方 mats 数量（策划案补口径说明）。
