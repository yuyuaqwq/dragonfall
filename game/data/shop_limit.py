# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - shop_limit.py（v166 商店限购，2026-09-02 鱼鱼拍板）

机制（两层叠加，全数据驱动）：
1. **总库存（店内共享）**：每种上架商品在某子区域(店铺)配 `stock` 上限，
   该店内所有玩家共享扣减（先到先得）——店与店独立，不跨店共享。
2. **每人每日限购**：配 `per_day`，每玩家每自然日在该店该商品最多买 per_day 件，
   防单人扫光店内共享货（跨天重置）。
3. **补货时间配置**：`restock_hours`（每 N 小时恢复满额）/ 可选 `restock_at`（每日固定时刻，
   如 "04:00" 指每天 4 点）+ `restock_hours` 周期补货。

key 设计（商品 key 前缀区分来源）：
- `item:{iid}`      → SHOP_SUBAREA_ITEMS 消耗品/杂物（i_ 前缀）
- `mat:{mid}`       → SHOP_SMITH_MATERIALS 锻造材料（mat_ 前缀）
- `equip:{rid}`     → SHOP_EQUIP 名册装备（eq_ 前缀）
- `weapon:{名}`     → SHOP_WEAPONS 武器（按名，全城镇同款共享配置；店内独立库存）
- 缺省（不在本表）→ 不限购（普通小药/基础食物不配额度，防误伤新手）

⚠️ 数值门禁：本表改动必须跑 scripts/run_numeric_tests.py（含 test_numeric_shop_pricing）
⚠️ 铁律：新增限购商品 = 改本文件一行数据，零代码
"""
from __future__ import annotations

# ================= v166 商店限购配置（每商品） =================
# 结构：
#   SHOP_LIMIT = {
#       "item:i_shuang_bei_jin_bi_fu": {"stock": 5, "per_day": 2, "restock_hours": 6},
#       "equip:eq_pi_jia": {"stock": 3, "per_day": 1, "restock_hours": 6},
#   }
# 可选字段：
#   stock:        总库存上限（None/缺省 = 不限量）
#   per_day:      每玩家每日限购件数（None/缺省 = 不限）
#   restock_hours: 补货周期（小时）；到点库存恢复满额（stock）
#   restock_at:   每日固定补货时刻 "HH:MM"（可选，与 restock_hours 二选一或组合）
#                 示例 "04:00" = 每天 04:00 补满一次
#   max_buy_once: 单次最大可买件数（None = 跟随 per_day/stock 余量）
#                 当 qty 超限时按 min(per_day余量, stock余量, max_buy_once) 钳制

SHOP_LIMIT = {
    # ---------- 强化/养成材料 ----------
    # 强化石/精炼强化石/祝福符石是商店锚（v165 强化石链不动=商店锚），
    # 高阶强化石价值高，防单人囤货扫光 → 每日限 + 补货
    "item:i_stone_upgrade":   {"stock": 10, "per_day": 5, "restock_hours": 6},
    "item:i_stone_refine":    {"stock": 8,  "per_day": 3, "restock_hours": 6},
    "item:i_stone_blessed":   {"stock": 3,  "per_day": 1, "restock_hours": 12},
    # ---------- 高价值 buff 药剂 ----------
    "item:i_def_potion":      {"stock": 5,  "per_day": 2, "restock_hours": 6},
    "item:i_spd_potion":      {"stock": 5,  "per_day": 2, "restock_hours": 6},
    "item:i_str_potion":      {"stock": 5,  "per_day": 2, "restock_hours": 6},
    "item:i_dragon_scale_potion": {"stock": 5, "per_day": 2, "restock_hours": 6},
    # ---------- 稀有消耗品（功能性强） ----------
    "item:i_shuang_bei_jin_bi_fu": {"stock": 5,  "per_day": 2, "restock_hours": 6},
    "item:i_fu_huo_yu_mao":        {"stock": 3,  "per_day": 1, "restock_hours": 12},
    "item:i_holy_charm":           {"stock": 5,  "per_day": 2, "restock_hours": 6},
    "item:i_scroll_purify":        {"stock": 3,  "per_day": 1, "restock_hours": 12},
    "item:i_phoenix_tear":         {"stock": 3,  "per_day": 1, "restock_hours": 12},
    "item:i_life_elixir":          {"stock": 5,  "per_day": 2, "restock_hours": 6},
    # ---------- 高级治疗 ----------
    "item:i_treat_holy":           {"stock": 10, "per_day": 5, "restock_hours": 6},
    "item:i_treat_l":              {"stock": 10, "per_day": 5, "restock_hours": 6},
    "item:i_mana_l":               {"stock": 10, "per_day": 5, "restock_hours": 6},
    # ---------- 传送/回城卷轴 ----------
    "item:i_scroll_escape":        {"stock": 10, "per_day": 5, "restock_hours": 6},
    "item:i_scroll_teleport":      {"stock": 10, "per_day": 5, "restock_hours": 6},
    # ---------- 商店材料（铁匠铺锻造材料，防扫货倒卖） ----------
    # 材料在铁匠铺卖，是锻造刚需；配合 v21 防倒卖半价 + 每日限购
    "mat:mat_tie_kuang_shi":   {"stock": 30, "per_day": 15, "restock_hours": 6},
    "mat:mat_jing_tie":        {"stock": 30, "per_day": 15, "restock_hours": 6},
    "mat:mat_mi_yin":          {"stock": 20, "per_day": 10, "restock_hours": 6},
    "mat:mat_jing_jin":        {"stock": 20, "per_day": 10, "restock_hours": 6},
    "mat:mat_bing_jing":       {"stock": 20, "per_day": 10, "restock_hours": 6},
    # ---------- 商店直售装备（限购防倒卖/防扫货；锻造线已有副业门槛） ----------
    # 新手白装/绿装基础件：每人每种 1 件即可，补货不频繁
    "equip:eq_pi_jia":           {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_jiu_pi_xue":       {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_xiang_mu_hu_tui":  {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_mao_pi_mao":       {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_xiang_mu_jie_zhi": {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_xiang_mu_xiang_lian": {"stock": 5, "per_day": 1, "restock_hours": 12},
    # 白鹿绿装套
    "equip:eq_bai_lu_pi_mao":    {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_bai_lu_xiong_jia": {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_bai_lu_hu_tui":    {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_bai_lu_pi_xue":    {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_bai_lu_zhi_jie":   {"stock": 5,  "per_day": 1, "restock_hours": 12},
    "equip:eq_bai_lu_diao_zhu":  {"stock": 5,  "per_day": 1, "restock_hours": 12},
}

# ================= 校验（import 时自检，防配置写错） =================
def _validate():
    _bad = []
    for key, cfg in SHOP_LIMIT.items():
        if ":" not in key:
            _bad.append(f"{key}: 缺类型前缀")
            continue
        prefix, ident = key.split(":", 1)
        if prefix not in ("item", "mat", "equip", "weapon"):
            _bad.append(f"{key}: 未知前缀 {prefix}")
            continue
        if not isinstance(cfg, dict):
            _bad.append(f"{key}: 配置必须是 dict")
            continue
        if cfg.get("stock") is not None and (not isinstance(cfg.get("stock"), int) or cfg["stock"] < 0):
            _bad.append(f"{key}: stock 必须非负整数")
        if cfg.get("per_day") is not None and (not isinstance(cfg.get("per_day"), int) or cfg["per_day"] < 1):
            _bad.append(f"{key}: per_day 必须正整数")
        if cfg.get("restock_hours") is not None and (not isinstance(cfg.get("restock_hours"), (int, float)) or cfg["restock_hours"] <= 0):
            _bad.append(f"{key}: restock_hours 必须正数")
        ra = cfg.get("restock_at")
        if ra is not None and (not isinstance(ra, str) or len(ra) != 5 or ra[2] != ":"):
            _bad.append(f"{key}: restock_at 必须 'HH:MM' 格式")
    if _bad:
        raise ValueError("SHOP_LIMIT 配置错误:\n  " + "\n  ".join(_bad))


_validate()
del _validate
