# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - index.py

索引归属说明：
- `_INDEXES` 是 ID 索引活容器（build_index 等写入，data/_assembly.py 与 __init__.py 均 import）。
- 历史上此处曾声明 _SKILL_FLAT/_MONSTER_INDEX/_FISH_INDEX/_NPC_INDEX/_SHOP_W_INDEX 五个空 dict，
  v104+ 已由 data/_assembly.py 重新声明并填充、经 __init__.py 从 _assembly 再导出，本文件无需再声明。
"""
_INDEXES = {}
