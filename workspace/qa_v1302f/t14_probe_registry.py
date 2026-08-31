# -*- coding: utf-8 -*-
"""T14 只读侦查：dragonfall handler 注册表顺序与 '6'/'对话 6'/'拳师' 的匹配结果。"""
import re, sys, os
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

try:
    from astrbot.core.star.star_handler import star_handlers_registry
    from astrbot.core.star.star_handler import EventType
    from astrbot.core.star.filter.regex import RegexFilter
    print("astrbot registry type:", type(star_handlers_registry))
except Exception as e:
    print("import astrbot registry failed:", type(e).__name__, e)
    sys.exit(0)

# 模拟 base._find_handler 遍历
def first_match(text):
    out = []
    for md in star_handlers_registry._handlers:
        if md.event_type != EventType.AdapterMessageEvent:
            continue
        name = getattr(md.handler, "__name__", "")
        if isinstance(md.handler, __import__("functools").partial):
            name = getattr(md.handler.func, "__name__", "")
        if name.startswith("shortcut") or name.startswith("_"):
            continue
        for f in md.event_filters:
            if isinstance(f, RegexFilter):
                try:
                    if f.regex.search(text):
                        out.append((name, md.extras_configs.get("priority"), str(f.regex.pattern)[:60]))
                except re.error:
                    continue
    return out

for txt in ["6", "对话 6", "拳师", "0", "对话 小艾", "角色"]:
    hits = first_match(txt)
    print(f"[{txt}] -> {[(n,p) for n,p,_ in hits[:6]]}")
    for n,p,pat in hits[:6]:
        print(f"    {n} prio={p} pattern={pat}")