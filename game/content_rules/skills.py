# -*- coding: utf-8 -*-
"""内容侧技能表读取（S5：自 `game/engine.py` 拆出，docs/ENGINE_CONTENT_SPLIT_PLAN.md §6.4）。

读《奥兰迪亚》专属表 / 职业名：
  - `C.PLAYER_SKILLS` / `C.BRANCH_SKILLS` / `C.TUTOR_SKILLS`（技能详情查询链）
  - `C.SKILL_UP`（每技能升级成长/独立满级配置）
  - `C.resolve("skills", …)`（技能中文名 ↔ id）

判据：**凡读游戏表或职业名 → 内容侧**。故这些函数不得留在引擎包内；
引擎（game/battle2/）需要技能数值时经 `battle2.config` 注入 hook 取纯公式
（见 game/bootstrap.py 的 `skill_up_fn` / `skill_level_of_fn`）。

旧路径 `game.engine.*` 保留 shim re-export（S9 收口时删）。
"""
from .. import content as C
from ..battle2.formulas import skill_max_level  # noqa: F401  （升级消耗用；纯公式在引擎侧）


# ============================================================
# 技能表读取
# ============================================================

# v48：职业/技能均用 ID 访问。表结构已变 {cls_id: {"name":.., "skills": {sk_id: def}}}
# 兼容 v48 前旧结构 {职业: {技能: def}} 的读取辅助。
def _sk_table(class_name: str) -> dict:
    class_name = C.resolve("classes", class_name)  # v48：统一转 ID
    t = C.PLAYER_SKILLS.get(class_name, {})
    if isinstance(t, dict) and "skills" in t:
        return t["skills"]
    return t


def _br_table(class_name: str) -> dict:
    class_name = C.resolve("classes", class_name)
    t = C.BRANCH_SKILLS.get(class_name, {})
    if isinstance(t, dict) and "branches" in t:
        return t["branches"]
    return t


# v177 怪物引用玩家技能：技能 key 全局唯一 → 扫全表缓存 {sk_id: (cls_id, info)}
_SKILL_KEY_INDEX: dict | None = None


def _build_skill_key_index() -> dict:
    """全量玩家技能索引：{sk_id: (所属职业, info)}——覆盖基础职业 + 分支 + 导师。
    供怪物技能引用玩家技能（存储分离、解析一套）与全局技能 key 反查。"""
    idx = {}
    for cls_id, cls in (C.PLAYER_SKILLS or {}).items():
        if not isinstance(cls, dict):
            continue
        for sk, info in (cls.get("skills") or {}).items():
            if sk not in idx:
                idx[sk] = (cls_id, info)
    for cls_id, brs in (C.BRANCH_SKILLS or {}).items():
        if not isinstance(brs, dict):
            continue
        for tier, branches in (brs.get("branches") or {}).items():
            for bname, skills in (branches or {}).items():
                for sk, info in (skills or {}).items():
                    if sk not in idx:
                        idx[sk] = (cls_id, info)
    for cls_id, t_skills in (C.TUTOR_SKILLS or {}).items():
        for sk, info in (t_skills or {}).items():
            if sk not in idx:
                idx[sk] = (cls_id, info)
    return idx


def skill_by_key(key: str) -> dict | None:
    """v177 按技能 key 全局查玩家技能（怪物引用玩家技能用）。查不到返回 None。"""
    global _SKILL_KEY_INDEX
    if _SKILL_KEY_INDEX is None:
        _SKILL_KEY_INDEX = _build_skill_key_index()
    hit = _SKILL_KEY_INDEX.get(key)
    return hit[1] if hit else None


def skill_owner_cls(key: str) -> str | None:
    """v177 技能 key 所属职业（怪物引用需知道怪物有没有该技能时用）。"""
    global _SKILL_KEY_INDEX
    if _SKILL_KEY_INDEX is None:
        _SKILL_KEY_INDEX = _build_skill_key_index()
    hit = _SKILL_KEY_INDEX.get(key)
    return hit[0] if hit else None


def skills_for_level(class_name: str, level: int) -> list[str]:
    """返回该职业当前等级已解锁的技能 id"""
    skills = _sk_table(class_name)
    return [name for name, info in skills.items() if info["lv"] <= level]


def is_skill_learned(class_name: str, level: int, skill_name: str, learned_skills: list | None = None) -> bool:
    """技能是否已学会(v12：必须『技能学习』花技能点学会才能使用，不再按等级自动解锁)"""
    info = skill_info(class_name, skill_name)
    if not info:
        return False
    # v48：learned_skills 是中文名（store 读回），skill_name 可能是 ID——统一 resolve 比较
    sid = C.resolve("skills", skill_name)
    return sid in [C.resolve("skills", s) for s in (learned_skills or []) if s]


def skill_info(class_name: str, skill_name: str):
    """技能详情：先查基础职业技能表，再查分支专属技能表（v26），最后查导师进阶技能（v95.23）
    v48：skill_name 接受中文名或 ID，统一 resolve 为 ID 再查（表 key 已是 sk_xxx）"""
    skill_name = C.resolve("skills", skill_name)
    info = _sk_table(class_name).get(skill_name)
    if info:
        return info
    for tier, branches in _br_table(class_name).items():
        for bname, skills in branches.items():
            if skill_name in skills:
                return skills[skill_name]
    # v95.23 职业导师进阶技能（TUTOR_SKILLS 并入查询链，battle/面板共用）
    t_info = (C.TUTOR_SKILLS or {}).get(class_name, {}).get(skill_name)
    if t_info:
        return t_info
    return None


def branch_skill_owner(class_name: str, skill_name: str):
    """分支专属技能归属：(tier, 分支名)；非分支技能返回 None(v26)"""
    skill_name = C.resolve("skills", skill_name)
    for tier, branches in _br_table(class_name).items():
        for bname, skills in branches.items():
            if skill_name in skills:
                return tier, bname
    return None


def branch_path_index(class_name: str, tier: int, branch_key: str):
    """分支 key 在该 tier 分支组内的 index（0/1）；找不到返回 None。

    v174：显示层用——BRANCH_SKILLS 分支 key 保持 B1 名（系统约定，如牧师 B2 key 仍
    "神谕者"），需按 tier 内位置映射到 classes.evolve_branches 的档位名（大主教/圣光先知等）。
    """
    try:
        branches = _br_table(class_name)
        blist = list((branches.get(int(tier)) or {}).keys())
        for i, bk in enumerate(blist):
            if bk == branch_key:
                return i
    except Exception:
        return None
    return None


# ============================================================
# 技能升级配置（C.SKILL_UP 表读）
# ============================================================

# v181 P0B-C：SKILL_UP key 已改稳定 id（见 game/data/skill_up.py 头注）。中文名→id 反查索引，
# 懒构建缓存（SKILL_UP 条目 name 字段 = 技能中文名，构建期自检保证全局唯一）。
_SKILL_UP_NAME_INDEX: dict | None = None


def _skill_up_name_index() -> dict:
    global _SKILL_UP_NAME_INDEX
    if _SKILL_UP_NAME_INDEX is None:
        _idx = {}
        for _sid, _cfg in (C.SKILL_UP or {}).items():
            _nm = _cfg.get("name") if isinstance(_cfg, dict) else None
            if _nm and _nm not in _idx:  # 首个赢（自检已保证 name 唯一，防御性 setdefault）
                _idx[_nm] = _sid
        _SKILL_UP_NAME_INDEX = _idx
    return _SKILL_UP_NAME_INDEX


def _skill_up(info: dict | None) -> dict:
    """按技能 info 查升级配置（v181 P0B-C：key 用稳定 id，不再用中文显示名）。

    v180 隔离：仅玩家可升级技能（带 lv 学习等级字段）参与 SKILL_UP 查表——
    怪技能（MONSTER_SKILLS，无 lv）即使 name 与玩家技能撞名（圣光弹/雷击/龙爪等 14 个）
    也不会误配玩家成长曲线（v180 P4 删默认成长后，撞名怪技能曾吃到玩家同名配置 p=10~12）。

    v181 P0B-C（方案 C，docs/REFACTOR_P0B_skill_up_dedup.md §4 Step2）：
    SKILL_UP key 已从中文名改为稳定 id（基础/导师 = 技能表现存 sk_id；分支 = sk_br_<pinyin>），
    每条条目带 name=中文名。skill_info 返回的 info 不带 id 字段（三表查询链只给 info dict），
    故在此用 info['name'] 经『中文名→id』索引反查稳定 id 后按 id 查表；查不到（无配置/防御）
    再回落 SKILL_UP.get(name)——data 层当前无中文 key，此处为兼容历史语义（将来若有人
    把旧中文名当 key 塞回 SKILL_UP 不至于静默失效）。"""
    if not info:
        return {}
    if info.get("lv") is None:
        return {}
    _name = info.get("name", "")
    _sid = _skill_up_name_index().get(_name)
    if _sid:
        _hit = C.SKILL_UP.get(_sid)
        if _hit is not None:
            return _hit
    return C.SKILL_UP.get(_name) or {}


def skill_upgrade_cost(cur_lv: int, info: dict | None = None) -> int:
    """升级消耗（递增）：Lv.1→2 花1点，2→3 花2点，3→4 花3点，4→5 花4点
    v56.4：达到该技能独立满级（max）后返回 0"""
    mx = skill_max_level(info)
    if cur_lv < 1 or cur_lv >= mx:
        return 0
    return cur_lv


# ============================================================
# 技能等级查询（玩家档 + 技能 id resolve）
# ============================================================

def skill_level_of(player: dict, skill_name: str) -> int:
    """技能等级查询（v46+ 兼容）：store 读库后 skill_levels 的 key 是中文名（players.py:113 display 转换），
    入参可能是 ID 或中文名——统一 resolve 后匹配，查不到按未升级 Lv.1。
    修复 #259：技能列表/详情/战斗内此前用 ID 直接查 key 恒 fallback Lv.1（战斗内实际按 Lv.1 计算）。"""
    levels = player.get("skill_levels") or {}
    if not levels:
        return 1
    sid = C.resolve("skills", skill_name)
    for k, v in levels.items():
        if k and C.resolve("skills", k) == sid:
            return int(v or 1)
    return 1
