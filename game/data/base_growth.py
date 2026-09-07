# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - base_growth.py（P2F-3 F6：player_base_stats 成长声明，新建）

玩家基础属性成长结构声明——player_base_stats 的三段乘区结构声明化（纯 dict 零函数，
参照 stat_templates.py 文档头）。执行器：game/engine.py player_base_stats（结构/截断序保留引擎）。

表语义（与现状逐字段一致，默认值 = 重构前字面量 → 行为零变化）：
  - linear_stats 7 键 = 吃 tier_mult×race_mult 的成长属性——循环只作用于这 7 键
    （growth×(lv-1)×mult×rmult 是一次 int，先浮点后截断；tier/race 不进 base，等级 1 无影响）；
    base dict 中 crit/dodge/职业特色等多余键不在循环内、原样带出。
  - branch_bonus_mode 键声明各属性的分支修正模式：mode "mul" = int(v×倍率)（hp/mp 及其余默认）；
    mode "add" = round(当前值+加值, 3)（crit 百分比加法特例，v25 影舞者暴击，全表仅 cls_ci_ke 路径 1）。
    只声明"某属性若出现在 bb 里怎么修"——不声明分支表里有哪些属性（bb 键集权威仍是
    data/battle_config.py BRANCH_BONUS_BY_CLASS / BRANCH_BONUS 回退，防双数据源）。
  - alias 输出别名键（分支段之后追加，非 base 原始键）。
调数值/加属性 = 改这里。
"""
PLAYER_BASE_GROWTH = {
    # 线性成长循环（现 engine.py L136 硬编码元组）
    "linear_stats": ("hp", "mp", "atk", "def", "matk", "mdef", "spd"),
    # 分支修正模式（现 engine.py L140-150 if-elif 结构）
    "branch_bonus_mode": {
        "hp":   {"mode": "mul"},          # int(base×v)
        "mp":   {"mode": "mul"},          # int(base×v)
        "crit": {"mode": "add", "round": 3},   # ⚠️ 结构特例：round(base+加值, 3)（百分比 3 位小数）
        "_default": {"mode": "mul"},      # 其余属性（atk/def/matk/mdef/spd）→ int(base×v)
    },
    # 输出别名键（现 L151-152：分支段之后追加）
    "alias": {"hp": "max_hp", "mp": "max_mp"},
}
