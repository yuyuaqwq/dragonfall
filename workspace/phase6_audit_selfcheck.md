# v136 Phase 6 五路审计结果汇总（deleg_b1b886b9，2026-08-29）

## 审计发现总览
5 路只读审计（数据完整性/职业折扣/三方一致性/素材定向/测试覆盖）+ 主 agent 自查。
无 P0 崩溃级（审计前）；但发现 2 个 P0 级数据损失 + 7 个 P1 + 多个 P2，全部已修复（commit 1b4bce3 + 46e162b + 8b7710d + 2a8119c）。

## P0（已修复）
1. **游侠套装 id 撞车（最严重）**：Phase6 新『猎手』装备 eq_lie_shou_* 与旧『猎首远征队』同 pinyin id（猎首/猎手同音），4 件旧紫装被 dict 覆盖（游侠 50-56 断档，battle.py 猎首折扣变死代码）。合并脚本只校验中文名唯一，没校验 pinyin_id。
   - 修复：新装备换 id（eq_lie_shou_xin_pi_mao/pi_jia/chang_xue、eq_feng_xing_chang_gong Lv30、eq_an_ye_chang_gong Lv50）+ 旧猎首恢复 + 配方 key 去重（rec_lie_shou_xin_*）
   - 数量修正：名册 384→388、配方 348→352、需图纸 200→204
2. **_build_class_sets 漏注册 bonus_4**：只复制 bonus_4_stats/bonus_5/bonus_5_cond，没复制 bonus_4 → 18 职业套 + 5 区域套 4 件特效静默失效（set_bonus_4 读不到 effect 返回空）。

## P1（已修复）
3. **区域套 4 件特效不可达**：区域套只有 3 槽位（armor/legs/boots），bonus_4 永远凑不齐 → engine 新增 bonus_3/bonus_3_stats 档（set_bonus_2 + set_bonus_4 支持），区域套特效 3 件生效（实测护林套 3 件 → def+5%/hp+8% + regen）。
4. **13 件紫/橙固定词条仅 1 条**（暗夜长靴/护腿/壁槌护腿/苍狼之爪/苍穹之靴/龙鳞手环/龙翼戒指/熔岩之靴/天穹之冠/星辉吊坠/星辉戒指/星火戒指/阴影护腿）→ 补足 2 条（注意：天穹之冠原用 spd_up 不存在，改 crit_dmg）。
5. **散装月语之戒 series 撞旧月语套** → 改独立系列『月语戒』（不再误触发月语套加成）。
6. **渡口/巡林过渡档无获取渠道**：source=商店但 SHOP_EQUIP 没上架 → ironharbor（渡口 3 件）+ jade_port（巡林 3 件）。注意：SHOP_WEAPONS 与 SHOP_EQUIP 都有同城 key，别加错（曾误加 SHOP_WEAPONS 导致 v104 测试 unpack 崩）。
7. **霜猎套 element_ice 无效**（∉ PCT_STATS/PENE_PCT_STATS）→ 改 crit（冰霜猎杀=暴击倾向）。
8. **游侠 dodge 10% vs 策划案 8%** → 改 0.08（文档权威=策划案 32 章:718）。
9. **素材产出等级错配**（低阶素材挂高阶怪）：
   - 山贼徽章（Ⅰ档 Lv6-10 配方）Lv42 盗贼 → 加挂哥布林斥候 Lv9（白鹿之森）
   - 鼠狮核心（Ⅱ档 Lv26-30 配方）Lv40 兽人 → 加挂河龙 Lv34（银铃河）
   - 龙焰精华（Ⅲ档 Lv46-50 配方）Lv84-89 石龙 → 加挂熔岩元素 Lv69（龙脊古道）
   - 保留原高级产出点（高难图=稀有素材第二来源）

## P2（已处理/记录）
- 详案区域套命名滞后（水手→渡口、猎手→霜猎）→ docs 已同步
- 35 件蓝装 2 词条：设计选择保留（蓝装特色）
- 45 件职业套 id 无下划线连写式（eq_tiepichangjian）：风格问题，待 v137 统一
- 20:6:1 语义 = 量产:精英:Boss 三层掉落权重，非配方 mats 数量
- 散装橙装 3 件 vs 策划案 2 件 → 设计仓已同步说明
- 星尘套 bonus_2 4 键（atk/matk/def/spd 0.05）= 历史设计，非丢失

## 验证（全部通过）
- test_v136_phase6_equip 105/105（新增猎首恢复/武器链/bonus_3/散装防套断言）
- test_v136_class_discount 3/3、test_v104_shop_auction_mount 30/0、stage8 385/0、v87_hidden 54/0
- 数值门禁 8/8、命令矩阵 221/0、全量 215/217（2 历史遗留 v1303/v96）

## 关键教训
1. **pinyin_id 唯一性必须纳入命名校验**（同音不同字：猎首/猎手、首/手），不能只看中文名
2. **合并脚本必须校验"目标 dict 已有同名 key"**——静默覆盖 = 数据损失
3. **测试盲区**：test_v136_phase6_equip 最初只测 2 件套属性，没测 4 件套 effect 注册 → 补 test_set_effects
4. **SHOP_WEAPONS / SHOP_EQUIP 同城 key 并存**——改商店数据前先确认属于哪个 dict
