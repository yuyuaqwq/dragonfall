# -*- coding: utf-8 -*-
"""怪物工厂 + 曲线覆盖（方案预演）：build 任一 role 面板；curve_override 在进程内
临时替换 MONSTER_ROLE_GROWTH / hp_stage_mult / atk_stage_mult 做"参数预演"，
退出上下文自动还原 —— 预演绝不污染后续调用。

验证：200 页 v131 预演脚本（_tmp_boss_preview.py）同口径；dodge 未实装
（build_monster 不产出模板 dodge，PVE 怪闪避恒 0 —— 已知问题记录在案）。
"""
import contextlib

from .env import setup_env  # noqa: F401
from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game.data import stat_templates as S  # noqa: E402


def build(role: str, lv: int, mid: str | None = None, map_obj: dict | None = None) -> dict:
    """C.build_monster 展开一只怪（role ∈ tank/dps/caster/speedster/healer/elite/boss）。

    mid 缺省自动生成（m_sim_<role>_<lv>）；map_obj 给副本 ID 用（build_monster 内部依赖）。
    """
    mid = mid or "m_sim_%s_%d" % (role, lv)
    return C.build_monster(
        (mid, "测试%s" % role, role, lv, [], []),
        map_obj or {"id": "sim", "name": "sim", "area": "sim"},
    )


def panel(role: str, lv: int, mid: str | None = None) -> dict:
    """面板别名：返回 {max_hp, hp, atk, def, spd, matk, mdef, lv, role} 关键字段。"""
    m = build(role, lv, mid)
    return {k: m.get(k) for k in ("max_hp", "hp", "atk", "def", "spd", "matk", "mdef", "lv")}


@contextlib.contextmanager
def curve_override(growth: dict | None = None, hp_stage: list | None = None,
                   atk_stage: list | None = None):
    """进程内临时覆盖怪物曲线（预演标准用法）：
      growth   : {role: {attr: 值}} 覆盖 MONSTER_ROLE_GROWTH（如 {"dps": {"def": 4.0, "atk": 6.0, "hp": 25}}）
      hp_stage : [(max_lv, mult), ...] 覆盖 stats.hp_stage_mult 函数（≤15 恒 1.0 / 16-30 +8%...）
      atk_stage: 同上覆盖 stats.atk_stage_mult 函数
    退出 with 块自动还原（含异常路径）。注意：精英/boss 共享 hp_stage/atk_stage 曲线。
    ⚠️ 绑定链：data.stat_templates 的 MONSTER_ROLE_BASE/GROWTH 被 core.stats **from-import 绑定**
    （stats 模块内直接用绑定名），因此必须同时覆盖 data 模块属性 + core.stats 绑定名，
    否则预演数字与现状完全相同（v131 教训：monster_stats 走 stats 绑定）。
    """
    from data.plugins.dragonfall.game.core import stats as ST
    saved = {}
    try:
        if growth is not None:
            saved["growth"] = {r: dict(v) for r, v in S.MONSTER_ROLE_GROWTH.items()}
            saved["growth_binding"] = {r: dict(v) for r, v in ST.MONSTER_ROLE_GROWTH.items()}
            for role, attrs in growth.items():
                if role not in S.MONSTER_ROLE_GROWTH:
                    raise KeyError(f"未知 role: {role}")
                for attr, val in attrs.items():
                    S.MONSTER_ROLE_GROWTH[role][attr] = val
                    ST.MONSTER_ROLE_GROWTH[role][attr] = val
        if hp_stage is not None:
            saved["hp_stage"] = ST.hp_stage_mult
            ST.hp_stage_mult = _make_stage_fn(hp_stage)
        if atk_stage is not None:
            saved["atk_stage"] = ST.atk_stage_mult
            ST.atk_stage_mult = _make_stage_fn(atk_stage)
        yield
    finally:
        if "growth" in saved:
            S.MONSTER_ROLE_GROWTH = {
                r: dict(v) for r, v in saved["growth"].items()
            }  # 深拷贝还原：原表在 with 内被就地改过，浅拷贝引用会带出脏值
            ST.MONSTER_ROLE_GROWTH = {
                r: dict(v) for r, v in saved["growth_binding"].items()
            }
        if "hp_stage" in saved:
            ST.hp_stage_mult = saved["hp_stage"]
        if "atk_stage" in saved:
            ST.atk_stage_mult = saved["atk_stage"]


def _make_stage_fn(segments: list):
    """[(max_lv, mult), ...] → 分段函数（lv ≤ 段 max 取对应 mult）。"""
    seg = sorted(segments)

    def _fn(lv: int) -> float:
        for max_lv, mult in seg:
            if lv <= max_lv:
                return mult
        return seg[-1][1] if seg else 1.0
    return _fn