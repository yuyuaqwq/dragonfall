# -*- coding: utf-8 -*-
"""Phase 6 片段模板（子 agent 产物格式）

所有子 agent 必须产出一个独立 .py 文件，结构如下：
1. 顶部 docstring 说明模块
2. 定义 MERGE dict（纯数据，无执行代码）
3. 用 if __name__ == '__main__' 做自检

MERGE = {
    "EQUIP_ROSTER": {...},          # 名册条目
    "SERIES_FIXED_AFFIX": {...},    # 固定词条（名→词条id列表）
    "SERIES_SETS": {...},           # 系列→套装名
    "EQ_SERIES_THEME": {...},       # 系列描述
    "MATERIALS": {...},             # 新素材
    "CRAFT_RECIPES": {...},         # 锻造配方
    "MAT_DROP_MAP": {...},          # 素材→地图/怪物（供主 agent 挂 drops）
}

文件放到: C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/phase6_frags/<名字>.py
不要直接改源文件！主 agent 负责合并 + 测试 + 提交。
"""
