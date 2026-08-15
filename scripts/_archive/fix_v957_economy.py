# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑： v95.7 修复 economy.py：#27 旧存量饰品豁免、#28 装备 diff 称号一致（脚本方式，禁用 patch 工具）"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import io, re

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\economy.py"
with io.open(PATH, "r", encoding="utf-8") as f:
    src = f.read()

orig = src

# ---- #27：_req_check 扩展豁免（v93 商店装饰品旧存量：毛皮帽/橡木戒指/橡木项链） ----
old_req = '''        # v95.4：新手武器（橡木系列 Lv.2-3）需求已从名册移除，旧存量装备快照仍带 req → 一并豁免
        if d.get("slot") == "weapon" and d.get("lv", 99) <= 3:
            return True, ""
'''
new_req = '''        # v95.4：新手武器（橡木系列 Lv.2-3）需求已从名册移除，旧存量装备快照仍带 req → 一并豁免
        if d.get("slot") == "weapon" and d.get("lv", 99) <= 3:
            return True, ""
        # v95.7 #27：v93 商店装饰品（毛皮帽/橡木戒指/橡木项链）名册已去 req，旧存量快照仍带 → 豁免
        if d.get("slot") in ("ring", "necklace", "helm") and d.get("lv", 99) <= 4:
            return True, ""
'''
assert src.count(old_req) == 1, f"req 块匹配数异常: {src.count(old_req)}"
src = src.replace(old_req, new_req)

# ---- #28：equip 穿前 old_stats 称号加成与穿后一致（传真实 title_bonus） ----
old_eq = '''        old_stats = None
        if old:
            old_stats = E.player_final_stats(player["class_name"], player["level"], equipment,
                                             player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), None, player.get("race"))
'''
new_eq = '''        old_stats = None
        if old:
            # v95.7 #28：穿前/穿后必须传同一 title_bonus，否则称号加成混入 diff 导致显示"(无变化)"
            old_stats = E.player_final_stats(player["class_name"], player["level"], equipment,
                                             player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
'''
assert src.count(old_eq) == 1, f"equip 块匹配数异常: {src.count(old_eq)}"
src = src.replace(old_eq, new_eq)

# ---- #28：unequip 同样修正 ----
old_un = '''        # 属性变化对比（复用 equip 逻辑）
        old_stats = E.player_final_stats(player["class_name"], player["level"], equipment,
                                         player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), None, player.get("race"))
'''
new_un = '''        # 属性变化对比（复用 equip 逻辑；v95.7 #28：title_bonus 与卸后一致）
        old_stats = E.player_final_stats(player["class_name"], player["level"], equipment,
                                         player.get("class_tier", 0), player.get("attributes"), player.get("evolve_path", 0), self._title_bonus(group_id, qq_id), player.get("race"))
'''
assert src.count(old_un) == 1, f"unequip 块匹配数异常: {src.count(old_un)}"
src = src.replace(old_un, new_un)

with io.open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)

print("OK: economy.py 三处修改完成")
