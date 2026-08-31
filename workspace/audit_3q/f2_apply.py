# -*- coding: utf-8 -*-
"""F2 副本入口设施化——命令层落地脚本（Python 行级，CRLF 安全）。

只改 3 个命令层文件：
1. game/commands/instance.py
   - _instance_start（L1749 起）：钥匙检查后、体力扣减前，插入入口位置校验
   - _instance_list（L1166-1193）：每行加 📍 入口显示
2. game/commands/world.py
   - _map_facilities：funcs 含 instance 的子区域显示入口设施行
3. game/commands/base.py（不动——不需要改，见 F2 卡）

兼容红线（R1/R2 确认）：
- 副本 entry 为空 → 免校验（.get 兜底，兼容 F1 未完成）
- 已通关该副本（inst_clear_*）→ 免位置校验（老玩家便利）
- 存量玩家 cur_map 已在副本图 → 视为已在入口（豁免，防旧存档卡死）
- 主线/支线 explore 目标 == 本副本图 → 免位置校验（任务内单人可进图，combat.py 主线击杀目标只挂副本图）
- 撤退恢复（instance_cmd old_row 分支）不加校验（F2 卡明确）
"""
import io
import sys


def read_lines(path: str):
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        return f.readlines()


def write_lines(path: str, lines):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)


def find_line(lines, needle, start=0):
    """返回第一个包含 needle 的行号（0-based），找不到返回 -1"""
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i
    return -1


def patch_instance_start(lines):
    """在 _instance_start 的体力扣减前插入入口位置校验"""
    # 定位体力扣减行（L1853 附近）：'# v94 体力：开本消耗 20 体力'
    anchor = find_line(lines, "# v94 体力：开本消耗 20 体力")
    if anchor < 0:
        raise RuntimeError("找不到体力扣减锚点")
    # 校验块（缩进 8 空格 = 函数体内层）
    block = [
        '        # F2 副本入口设施化：走到入口才能开本（消费 F1 的 entry 字段 + funcs=instance 标记）\n',
        '        # 兼容红线：entry 为空免校验；已通关免校验；cur_map 已在副本图视为已在入口；\n',
        '        # 主线/支线 explore 目标 == 本副本图（任务内单人可进图）免校验。\n',
        '        _entry_cfg = inst.get("entry")\n',
        '        if _entry_cfg:\n',
        '            _entry_map = _entry_cfg.get("map")\n',
        '            _entry_sa = _entry_cfg.get("subarea")\n',
        '            _leader_p = self._player(group_id, qq_id)\n',
        '            _ok_pos = True\n',
        '            if _entry_map and _entry_sa:\n',
        '                _ok_pos = (str(_leader_p.get("cur_map") or "") == str(_entry_map)\n',
        '                           and str(_leader_p.get("cur_subarea") or "") == str(_entry_sa))\n',
        '                # 兼容红线：存量玩家 cur_map 已在副本图（旧存档徒步进图）→ 视为已在入口\n',
        '                if not _ok_pos and str(_leader_p.get("cur_map") or "") == _inst_map_id(kid):\n',
        '                    _ok_pos = True\n',
        '            if not _ok_pos:\n',
        '                # 兼容红线：已通关该副本 → 免位置校验（老玩家便利）\n',
        '                from ..core.instance_gate import instance_cleared_qq\n',
        '                _cleared = instance_cleared_qq(group_id, qq_id, kid)\n',
        '                if not _cleared:\n',
        '                    # 兼容红线：主线/支线 explore 目标 == 本副本图 → 任务内单人可进图，免校验\n',
        '                    _quests = db.get_quests(group_id, qq_id)\n',
        '                    _in_quest = False\n',
        '                    if _quests.get("main_status") == "active":\n',
        '                        _mq = next((q for q in C.MAIN_QUESTS if q["id"] == _quests.get("main_quest")), None)\n',
        '                        if _mq and _mq.get("objective", {}).get("explore") == _inst_map_id(kid):\n',
        '                            _in_quest = True\n',
        '                    if not _in_quest:\n',
        '                        _side = _quests.get("side") or {}\n',
        '                        if any(\n',
        '                            sq.get("status") == "active"\n',
        '                            and next((q for q in C.SIDE_QUESTS if q["id"] == sid), {}).get("objective", {}).get("explore") == _inst_map_id(kid)\n',
        '                            for sid, sq in _side.items()\n',
        '                        ):\n',
        '                            _in_quest = True\n',
        '                    if not _in_quest:\n',
        '                        _em_name = C.MAP_BY_ID.get(_entry_map, {}).get("name", _entry_map)\n',
        '                        _esa_name = ""\n',
        '                        for _esa in (C.MAP_BY_ID.get(_entry_map, {}).get("subareas") or []):\n',
        '                            if _esa.get("id") == _entry_sa:\n',
        '                                _esa_name = _esa.get("name", "")\n',
        '                                break\n',
        '                        yield event.plain_result(\n',
        '                            f"📍 请先到【{_em_name}·{_esa_name or _entry_sa}】副本入口处（『前往』）再开本！\\n"\n',
        '                            f"（副本入口在 {_em_name} 的 {_esa_name or _entry_sa}，走到那里输入『副本 {inst[\'name\']}』）"\n',
        '                        )\n',
        '                        return\n',
        '',
    ]
    lines[anchor:anchor] = block
    return anchor


def patch_instance_list(lines):
    """_instance_list 每行加 📍 入口（读 entry 字段，有才显示）"""
    # 定位 "🔑 需" 行（L1189）——入口行插在钥匙行之后
    anchor = find_line(lines, "🔑 需『")
    if anchor < 0:
        raise RuntimeError("找不到钥匙行锚点")
    # 在钥匙行后插入入口行（注意：钥匙行是 if ki 内的，入口行要每副本都显示 → 放在钥匙 if 块外）
    # 找钥匙 if 块的缩进与结束：钥匙行缩进 12 空格（3 层），其后的行缩进 <= 8 时结束
    indent = len(lines[anchor]) - len(lines[anchor].lstrip())
    j = anchor + 1
    while j < len(lines) and (lines[j].strip() == "" or len(lines[j]) - len(lines[j].lstrip()) > indent):
        j += 1
    # 在 if 块结束后（缩进回落点）插入入口行
    block = [
        '            ent = inst.get("entry")\n',
        '            if ent:\n',
        '                _em = C.MAP_BY_ID.get(ent.get("map", ""), {}).get("name", ent.get("map", ""))\n',
        '                _esa_n = ""\n',
        '                for _esa2 in (C.MAP_BY_ID.get(ent.get("map", ""), {}).get("subareas") or []):\n',
        '                    if _esa2.get("id") == ent.get("subarea"):\n',
        '                        _esa_n = _esa2.get("name", "")\n',
        '                        break\n',
        '                lines.append(f"   📍 入口：{_em}·{_esa_n or ent.get(\'subarea\', \'\')}")\n',
        '',
    ]
    lines[j:j] = block
    return j


def patch_world_facilities(lines):
    """_map_facilities 消费 funcs 含 instance → 显示入口设施行"""
    # 定位 '        # 自然互动（9.3：垂钓点显示特色描述' 前（设施区末尾）插入
    anchor = find_line(lines, "# 自然互动（9.3：垂钓点显示特色描述")
    if anchor < 0:
        raise RuntimeError("找不到自然互动锚点")
    block = [
        '        # F2 副本入口设施化：funcs 含 instance 的子区域 = 副本入口设施（消费 F1 标记）\n',
        '        if sa_obj and "instance" in (sa_obj.get("funcs") or []):\n',
        '            for _ik, _iv in C.INSTANCES.items():\n',
        '                _ie = _iv.get("entry") or {}\n',
        '                if _ie.get("map") == mid and _ie.get("subarea") == sa_id:\n',
        '                    lines.append(f"🏰 此处是【{_iv.get(\'name\', \'副本\')}】入口（『副本 {_iv.get(\'name\', \'\')}』进入）")\n',
        '                    break\n',
        '',
    ]
    lines[anchor:anchor] = block
    return anchor


def main():
    base = "game/commands/"
    changed = []

    # 1. instance.py
    p = base + "instance.py"
    lines = read_lines(p)
    a1 = patch_instance_start(lines)
    a2 = patch_instance_list(lines)
    write_lines(p, lines)
    changed.append(f"{p} (+{a1} 开本校验, +{a2} 列表入口)")

    # 2. world.py
    p = base + "world.py"
    lines = read_lines(p)
    a3 = patch_world_facilities(lines)
    write_lines(p, lines)
    changed.append(f"{p} (+{a3} 入口设施)")

    print("改动完成:")
    for c in changed:
        print(" ", c)


if __name__ == "__main__":
    main()
