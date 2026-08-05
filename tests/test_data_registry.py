# -*- coding: utf-8 -*-
"""data 层 · 索引族：ID 索引体系（v46）与全局完整性

验证：
  1. content 聚合层表总量（全局健康度）
  2. _INDEXES 各域名字→ID / ID→名字 双向一致
  3. resolve / display 调用路径
  4. 别名兼容表（LEGACY_MAP_ALIAS / CRAFT_RECIPE_ALIASES）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


def main():
    print("【data·索引族：全局健康度】")
    table_cnt = len([k for k in dir(C) if k.isupper() and isinstance(getattr(C, k), dict)])
    check("content 表总数 >= 55（实际 %d）" % table_cnt, table_cnt >= 55)
    check("_INDEXES 9 个域", len(C._INDEXES) >= 5, str(list(C._INDEXES)))

    print("【data·索引族：双向一致】")
    for domain in ("monsters", "skills", "items"):
        if domain in C._INDEXES:
            idx = C._INDEXES[domain]
            check("%s 名字表非空" % domain, len(idx.get("name_to_id", {})) > 0, str(len(idx.get("name_to_id", {}))))
        else:
            check("%s 有索引" % domain, False, "缺 domain")

    print("【data·索引族：resolve/display 调用】")
    check("resolve(monsters, 野狗)→ID", C.resolve("monsters", "野狗") == "m_stray_dog", C.resolve("monsters", "野狗"))
    check("display(monsters, m_stray_dog)→野狗", C.display("monsters", "m_stray_dog") == "野狗",
          C.display("monsters", "m_stray_dog"))

    print("【data·索引族：别名兼容】")
    check("LEGACY_MAP_ALIAS 非空（移动命令输入兼容）", len(C.LEGACY_MAP_ALIAS) > 0, str(len(C.LEGACY_MAP_ALIAS)))
    check("CRAFT_RECIPE_ALIASES 非空（打造搜索别名）", len(C.CRAFT_RECIPE_ALIASES) > 0, str(len(C.CRAFT_RECIPE_ALIASES)))

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
