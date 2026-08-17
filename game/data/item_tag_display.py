# -*- coding: utf-8 -*-
"""物品个体属性（tags）显示配置 —— v126.4 数据驱动注册表。

机制：堆叠个体物（垂钓渔获等）入包时带 tag（{...} 个体属性）存 item_data.tags
（见 store/inventory.py add_item(tag=...) / _slim / _hydrate）。『物品详情』在主体
渲染后统一按物品大类查询本表，命中则逐条渲染 tag 行。

【怎么加新 tag 显示】（数据驱动，零代码）：
  1. 入包时在 tag dict 里加字段（如 {"size":.., "weight":.., "spot":"xxx"}）
  2. 本表对应 type 的 line 模板加占位符（{spot}），或新类型加一行：
       ITEM_TAG_DISPLAY["坐骑"] = {"line": ["🐎 脚程 {speed}"]}
  匹配规则：优先按物品 type（_item_kind_type 大类）精确查，未命中回退 "*" 通配。

字段说明：
  line      ：每条 tag 的渲染行模板——str/字符串列表（列表=一条 tag 渲染多行），
              用 str.format(**tag) 填充（格式符如 {size:.1f} 可用）。
  max_lines ：单次渲染行数上限（防 500 条囤鱼刷屏），超出用 omit 省略行。
  omit      ：超出上限时的省略行模板（{left} = 未显示条数）。
未命中任何配置（有 tag 无模板）→ 不显示不报错（模板字段与 tag 不匹配 → 单条跳过）。
"""
ITEM_TAG_DISPLAY = {
    # 垂钓渔获：钓上来都有个体大小/重量（FISH_POOL size_range/weight_range 波动）
    "鱼": {
        "line": "🐟 {size:.1f}cm / {weight:.1f}kg",
        "max_lines": 30,
        "omit": "……还有 {left} 条",
    },
    "垃圾": {
        "line": "🌿 {size:.1f}cm / {weight:.1f}kg",
        "max_lines": 10,
        "omit": "……还有 {left} 个",
    },
    "材料": {
        "line": "🧪 {size:.1f}cm / {weight:.1f}kg",
        "max_lines": 20,
        "omit": "……还有 {left} 份",
    },
    "宝物": {
        "line": "✨ {size:.1f}cm / {weight:.1f}kg",
        "max_lines": 10,
        "omit": "……还有 {left} 颗",
    },
    "鱼王": {
        "line": "🐉 {size:.1f}cm / {weight:.1f}kg",
        "max_lines": 10,
        "omit": "……还有 {left} 尾",
    },
    # 通配兜底：未来新增带 tag 的物品类型没配显式模板时也保证有显示
    "*": {
        "line": "  · {size:.1f}cm / {weight:.1f}kg",
        "max_lines": 20,
        "omit": "……还有 {left} 条",
    },
}