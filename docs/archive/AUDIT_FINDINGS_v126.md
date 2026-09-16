# v126 系列审计修复报告（2026-08-17，8-agent 并行）

> 审计范围：v126 副本剧情化 / v126.1 鱼获随机波动 / v126.2 背包 tags / v126.3 item_data 瘦身 / v126.4 物品详情 tags 显示
> 基线：6fe5fda ~ 7ba7d9c；修复提交 40daaf8（代码仓）+ 58af3e1（策划案仓）；全量 160/160 绿

## 审计汇总（8 模块）

| 模块 | 健康度 | P0 | P1 | P2 | 核心发现 |
|------|--------|----|----|----|----------|
| T1 tags 不变量 | 良 | 0 | 3 | 2 | 市场/摆摊/仓库/交换快照回流破坏 len(tags)≤count（幻影 tags 可被加权出售） |
| T2 出售经济 | 良 | 0 | 0 | 3 | sell_atomic 返回值忽略；缺 weight 键崩出售；静默兜底无日志 |
| T3 垂钓链路 | 优 | 0 | 0 | 2 | **珍珠类 4 品种重量 round(1位) 全变 0.0kg**；体力不足吞播报（v55 遗留） |
| T4 物品详情渲染 | 良 | 0 | 0 | 2 | `*` 通配双前缀；垃圾/宝物/鱼王模板死配置 |
| T5 瘦身水合 | 优 | 0 | 0 | 3 | _hydrate 兜底缺 quality；空 dict KeyError 理论缺口；_class_attrs 默认 type 口径 |
| T6 副本剧情化 | 优 | 0 | 0 | 2 | 切怪不渲染 boss_line（未覆盖分支）；旧王陵地理跨城（待拍板） |
| T7 测试兼容 | 良 | 0 | 0 | 3 | gather_map_bind 断言假绿；v126.1/126.2 核心功能零直接测试 |
| T8 策划案同步 | 良 | 0 | 0 | 3 | README 缺 16 章索引；v126.1 残留未标废弃；垃圾映射与文档不符 |

## 已修复（40daaf8）

### P1：快照回流破坏不变量（3 处同源）
- **根因**：命令层把整堆水合快照（含全部 tags）传给 store 原子函数，store 原样 json 进 market/stall/storage 行；买家/回流以 count=1 合并整堆 tags → 实测 count=1/tags=5、count=5/tags=9
- **修复**：`store/inventory.py` 新增 `_snapshot_one()`——单件流转快照只带 1 条个体 tags（FIFO 头）
  - `market_sell_atomic` / `market_buy_atomic`（防御旧行）/ `market_stall_sell_atomic`（含旧摊退回）/ `market_exchange_atomic`（给物+摊主单）
  - `world.home_storage_deposit_atomic` 存仓快照
  - `commands/social.py` 下架/收摊回流防御裁剪

### P2：珍珠类 0.0kg（v126.1 引入真 bug）
- **根因**：湖珍珠/鲛人泪/深渊珍珠/彩虹露珠 weight_range 0.005-0.05kg，`round(weight,1)` 几乎 100% 变 0.0 → 播报 0.0kg、"大鱼更贵"恒按 0.5 保底
- **修复**：`roll_fish_size_weight` 重量精度按量级自适应（<0.1kg → 3 位小数）；显示/播报用 `{weight}` 无格式符（str 自然表示 0.045kg/1.2kg）

### P2（12 项）
- `_sell_one`：缺 weight 键/非 dict tag 不崩（`t.get("weight", 0)` + isinstance 过滤）
- `_hydrate`：tags 分支兜底补 quality；空 dict 配置未命中兜底 name=key
- `add_item` / `_inv_upsert` / `_storage_upsert`：tags 合并保留 slim 非 tags 字段（动态物类属性兜底）
- `ITEM_TAG_DISPLAY`：删垃圾/宝物/鱼王死配置（垂钓渔获仅鱼/材料入包）；`*` 通配去模板自带前缀（渲染端统一加）
- test_v97_02_gather_map_bind：假绿断言修复（`item["data"].get("type") in C.MATERIAL_KIND_TYPES`）
- 策划案：README 补 16 章索引 + v126 注记；v126.1 明细表方案标废弃；23 章措辞"体长/重量"；16 章匹配规则/精度同步

### 测试沉淀（+43 断言）
- `tests/test_v1265_tags_invariant.py`（38 断言）：快照回流四场景（市场/仓库/摆摊/换摊）、珍珠精度、损坏 tag 防御、500 截断、滚动精度、出售加权
- `test_v1264` 17 断言保持

## 待拍板（报鱼鱼）
1. **渔获材料加权**（T2 P3）：海藻等 type=材料 的渔获带 tags 加权（0.83~1.5×）——同材料垂钓所得 vs 采集所得售价不同；语义上"渔获个体波动"可自洽，但"材料按类型折价"设计混叠。是否只对 type=鱼 加权？
2. **旧王陵地理**（T6 P3）：desc 写"晨曦城北"但 key_source="白鹿城铁匠铺购买"，跨城归属疑似 v110 修缮残留。
3. **鱼详情图标**（T4 P3）：鱼走默认消耗品渲染器显示 📦【银鳞鱼】，tags 行 🐟 但不一致；可做鱼专属渲染器（🐟 图标+品质色）。
4. **体力不足吞播报**（T3 P2-2，v55 遗留）：垂钓/采集/挖掘三处，等待轮结算入包后体力不足分支丢弃结算播报，玩家只看到"体力不足"。建议失败分支拼接播报。

## 遗留 P3（未修，可接受）
- sell_item_atomic 返回值忽略（提示误导，无经济漏洞）
- FISH_POOL range 合法性/quality 一致性未进启动校验；FISH_COLLECT 未纳入校验
- max_lines 语义（截 tag 条数非行数）文档已对齐
- 加权系数上限 1.5（w>wmax 配置漂移理论风险）