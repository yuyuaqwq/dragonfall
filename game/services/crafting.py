# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - crafting.py（v181 P4-4 CraftingService 装备养成域）

economy.py 锻造-强化区纯规则段服务化（逐行 copy 零变化）——命令层只留解析 +
守卫 + async yield 壳 + 文案拼装，掷骰-结算纯逻辑走本模块（services 禁 import
commands/*）。

本批搬入（P4-4 首刀：纯规则段先抽，命令层按结构化结果出文案）：
  - 强化石 key 字面量收敛：ENHANCE_STONE_REFINE / ENHANCE_STONE_BLESSED /
    ENHANCE_STONE_PROTECT（原散落 economy.py enhance 命令内的 "i_stone_refine"/
    "i_stone_blessed"/"i_stone_upgrade" 字面量单点化，数值/语义零变化——
    均为 v101.30 炼金强化材料：精炼强化石 +25%、祝福符石 +15%、强化石失败保护）
  - compute_enhance_rate：强化成功率纯规则（原 economy.enhance 内联段
    L3085-3105 逐行 copy）——输入 基础率/强化副业等级/星铁必成/背包存量标记，
    返回结构化结果（最终率/手艺加成行/实际消耗石料清单），命令层按结果扣料拼
    文案；是否消耗石料由命令层查 count 后以 has_* 标记传入，消耗动作由命令层
    逐项 remove（行为零变化：原代码 = 判存量→加率→扣料→拼文案行）。
  - enhance_fail_floor：强化失败保级/降级纯规则（原 economy.enhance 失败分支
    L3144-3145 逐行 copy）——输入 当前强化等级/失败保护存量标记，返回
    (new_enh, protect_used)。保护石消耗由命令层执行。

db 一律函数体内惰性 import（防 data/_assembly 加载期循环，core 样板同款铁律）。
"""
from .. import content as C

# ============ 强化石 key 收敛（原 economy.py enhance 散点字面量单点化） ============

# v101.30 炼金强化材料接入（economy.py enhance 原内联字面量，逐字符等价收敛）：
#   "i_stone_refine"   精炼强化石 = 成功率 +25%（自动消耗）
#   "i_stone_blessed"  祝福符石   = 成功率 +15%（自动消耗，与精炼石叠加，上限 100%）
#   "i_stone_upgrade"  强化石     = 失败保护（失败不掉级，消耗 1 个）
ENHANCE_STONE_REFINE = "i_stone_refine"
ENHANCE_STONE_BLESSED = "i_stone_blessed"
ENHANCE_STONE_PROTECT = "i_stone_upgrade"


def compute_enhance_rate(base_rate, prof_lv, *, boost=False,
                         has_refine=False, has_blessed=False):
    """强化成功率纯规则（v113.3 副业渐进加成 + v101.30/v105/v113.3 强化石叠加）。

    原 economy.enhance L3085-3105 内联段逐行 copy（行为零变化）：
      - 副业加成：强化师每级 +0.5%（Lv.10 = +5%，原仅 Lv.10 一档）
      - 精炼强化石：成功率 +25%（星铁必成(_boost)或成功率已 100% 时不再消耗）
      - 祝福符石：成功率 +15%（自动消耗，与精炼石叠加，上限 100%）
    返回 dict：
      rate        最终成功率（0~1）
      craft_line  手艺加成行文案（无加成 = ""；原 _craft_line，升级当次重算用）
      stones_used 实际消耗的石料 key 列表（按原判定顺序：refine → blessed），
                  命令层逐项 remove 等价于原内联扣料
      boost       星铁必成标记（原样透传，成功判定用）
    """
    rate = base_rate
    _rate_bonus = min(prof_lv, 10) * 0.005
    # O108 修复：手艺加成行单独存（_craft_line），升级当次用新等级重算后再拼回
    _craft_line = ""
    if _rate_bonus > 0:
        rate = min(1.0, rate + _rate_bonus)
        _craft_line = f"\n🛠️ 强化师 Lv.{prof_lv} 的手艺：成功率 +{_rate_bonus*100:.1f}%！"
    # v105 M11 P2：星铁必成(_boost)或成功率已 100% 时不再消耗精炼强化石（+25% 纯浪费）
    stones_used = []
    if not boost and rate < 1.0 and has_refine:
        rate = min(1.0, rate + 0.25)
        stones_used.append(ENHANCE_STONE_REFINE)
    # v113.3 祝福符石：成功率 +15%（自动消耗，与精炼石叠加，上限 100%）
    if not boost and rate < 1.0 and has_blessed:
        rate = min(1.0, rate + 0.15)
        stones_used.append(ENHANCE_STONE_BLESSED)
    return {"rate": rate, "craft_line": _craft_line, "stones_used": stones_used,
            "boost": boost}


def enhance_fail_floor(cur_enh, *, has_protect=False):
    """强化失败结算纯规则（原 economy.enhance 失败分支 L3144-3145 逐行 copy）。

    - v104 M11：+1~+4 失败不掉级（策划 19 章"纯亏金币"），+5 起才掉级
    - v113.3：+5/+6 失败掉 1 级；+7/+8 失败不掉级（大师工艺保底）
      保级/降级 = ENHANCE_FAIL_DROP 表查当前等级；保护石存在且会掉级时 → 保住等级。
    返回 (new_enh, protect_used)：
      new_enh      结算后强化等级（失败但保护/不掉级 = cur_enh）
      protect_used 是否消耗保护石（True → 命令层 remove 1 个 i_stone_upgrade）
    """
    drop = C.ENHANCE_FAIL_DROP.get(cur_enh, 0)
    new_enh = max(0, cur_enh - drop)
    if has_protect and new_enh != cur_enh:
        return cur_enh, True
    return new_enh, False
