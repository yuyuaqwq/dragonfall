# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 —— 组合 core+store 的跨域编排（v181 P4 命令层抽 services）

ARCHITECTURE.md v47 蓝图：data ← core ← store ← services ← commands ← main。
services 可 import：game.data / game.core（含 C 聚合）/ game.store / game.reward / 同级 services；
services 禁止 import：game.commands.*（任何文件、任何符号——含顶层函数/Mixin/talk_actions）。

每个文件是一个纯函数模块（零类零装饰器零 async generator yield），命令层只留解析+守卫+壳。

本包聚合导出（与 store/__init__.py 同款），命令层可 `from ..services import shop as ...`
或 `from ..services.shop import ...` 直连。

⚠️ db 只在函数体内惰性 import（防 data/_assembly 加载期被 import 时循环——core 样板铁律）。
"""
