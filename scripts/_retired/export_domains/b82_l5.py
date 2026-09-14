# -*- coding: utf-8 -*-
"""B8.2 线5 域插件 —— `boss_phases`（Boss 四阶段模板表）真源 → 包 JSON。

契约见 `scripts/export_domains/README.md`：本文件只**读真源、返回内存表**，落盘由宿主
（`scripts/export_game_package.py`：UTF-8 / LF / indent=2 / 原子替换 + `sort_table` 外层键字典序）统一做。
**不许 import `export_game_package`**（宿主会扫本目录 → 循环导入）。公用小工具走 `_helpers.py`。

================================================================================
域：`boss_phases` Boss 阶段模板 —— 4 条（表键 = 阶段 id normal/enrage/exhaust/rampage）
================================================================================
真源（2026-09-13 实测）：`game/data/boss_phases.py`（110 行 / 5,218 B —— 注意：B8.2 派单里
写的「5,218 行」是**字节数**误读，实为 110 行 / 4 条模板）：
    `:26 BOSS_PHASE_TEMPLATES`   4 条四阶段通用模板（v138.1 阶段状态机；借鉴《云海猎团》03 章 M3.2）
    `:91 DEFAULT_PHASE_ORDER`    阶段推进顺序常量（["normal","enrage","exhaust","rampage"]）
    `:94-97 PHASE_NUMERIC_KEYS / PHASE_BEHAVIOR_KEYS / PHASE_EXIT_KEYS / PHASE_SCRIPT_KEYS`
                                 引擎 `_phase_apply` 的字段白名单（**未进包**，见「留作引用」）
    `:95 phase_template(id)`     取模板（未知 id 回落 "normal"）
    `:100 merge_phase_config(phase_id, overrides)`  模板为底 + Boss 内联逐键覆盖

消费者（游戏侧；导出只搬运不改语义）：
    `game/commands/boss_script.py:193`（**本批移出仓**）`from ..data.boss_phases import merge_phase_config`
        —— 阶段 `phase_id` → 模板合并：`atk_mult` 覆盖式乘区 / `add_skills` 换招 /
        `preserve_debuffs` 净化开关（dedicated 测试 `tests/test_boss_script_p1.py` 断言
        「merge enrage 模板 atk ×1.25」）。**包内端口** `content/flow/boss_script.py` 把这一步改成
        **调用方传参** `phase_templates=`（本域导出后由 `content.tables.merge_phase_config` 提供）。
    `game/data/monster_mods.py` / `game/data/instances.py` 的 `phases[].phase_id` 引用这些 id
        （实测 phase_id 取值只出现 normal/enrage，`None` 表示不引用模板）。

映射口径（**本域只做一件事：把模板表原样搬进包**）
    * 一条 = 一个阶段模板，键 = 阶段 id；条目**原样**：不改类型、不补默认值、不动字段顺序。
      `None` 是**源侧合法值**（`ult_every` / `exit_turns` / `exit_dmg` / `warn_line` 的「无」），
      JSON 落 `null`，读回来仍是 `None` —— 与真源同义，**不许改写成 0/""**（那是「有」）。
    * 字段 census（4 条实测，并集 16 个）：`id` / `name` / `icon` / `atk_mult` / `def_add` /
      `spd_add` / `dmg_taken_mult` / `add_skills` / `freq_mult` / `ult_every` / `exit_turns` /
      `exit_dmg` / `counter` / `enter_line` / `warn_line` / `preserve_debuffs` —— **16/16 条全有**
      （四条模板字段集完全相同，形状稳定）。叶类型：str / int / float / bool / list[str] / None。
    * 空/坏表 → `raise`（空表在编辑器里 = 「0 条」且不报错，是本项目最怕的静默失效）。

留作引用、不展开 / 未进包（见报告 §遗留）
    产物 `add_skills` 的元素       → 引擎侧技能 id 串（**本表实测 4/4 条都是空列表 `[]`**：
                                     逐 Boss 换招写在 `MONSTER_MODS` / `INSTANCES` 的 phases 内联，
                                     不落在通用模板里），故本域**不声明 ref**。
    `DEFAULT_PHASE_ORDER` 与四个 `*_KEYS` 白名单常量 → 不是条目形状（引擎侧词汇），未进包；
    `phase_template()` / `merge_phase_config()` 两个函数 → 逻辑不在数据域里，由
      `content/tables.py` 的 `phase_template` / `merge_phase_config`（读本 JSON）提供（逐行同义）。
"""

from _helpers import import_game_data, sort_table, as_table  # noqa: F401

# 真源位置（写进报错文案，便于定位「形状变了」时是哪个文件哪张表）
PHASES_SRC = "game/data/boss_phases.py:26 BOSS_PHASE_TEMPLATES"

# 四阶段模板的字段白名单（真源 :94-97 的四个 *KEYS 元组的并集 + id/name/icon/counter 等）；
# 不在这里的字段 = 源侧新增了本域没预期的键 → 也照搬（只断言**必备键**，不锁死形状）。
_PHASE_REQUIRED = ("id", "name", "icon", "atk_mult", "def_add", "spd_add",
                   "dmg_taken_mult", "add_skills", "freq_mult", "ult_every",
                   "exit_turns", "exit_dmg", "counter", "enter_line", "warn_line",
                   "preserve_debuffs")


def derive_boss_phases(src_root: str = None) -> dict:
    """`boss_phases` 域：`BOSS_PHASE_TEMPLATES` 原样导出（4 条）。**零注入、不筛、不补默认值**。

    条目里的 `None` 是源侧合法值（`ult_every` / `exit_turns` / `exit_dmg` / `warn_line` 的「无」），
    原样落 `null`；`add_skills` 实测 4/4 条是空列表。
    """
    mod = import_game_data("boss_phases", src_root) if src_root else import_game_data("boss_phases")
    tbl = as_table(getattr(mod, "BOSS_PHASE_TEMPLATES", None), PHASES_SRC)
    if not tbl:
        raise ValueError(f"boss_phases：{PHASES_SRC} 是空表 —— 源形状变了/表被删，拒绝导出"
                         f"（空表 = 编辑器显示 0 条且不报错）")

    out: dict = {}
    for pid, ent in tbl.items():
        if not isinstance(pid, str) or not pid:
            raise ValueError(f"boss_phases：{PHASES_SRC} 的键 {pid!r} 不是非空字符串 —— 拒绝导出")
        if not isinstance(ent, dict):
            raise ValueError(f"boss_phases：{PHASES_SRC}[{pid!r}] 不是 dict"
                             f"（{type(ent).__name__}）—— 源形状变了，拒绝导出")
        if ent.get("id") != pid:
            raise ValueError(f"boss_phases：{PHASES_SRC}[{pid!r}].id = {ent.get('id')!r} 与键不一致"
                             f" —— 拒绝导出（引擎按 id 引用模板）")
        miss = [f for f in _PHASE_REQUIRED if f not in ent]
        if miss:
            raise ValueError(f"boss_phases：{PHASES_SRC}[{pid!r}] 缺字段 {miss} —— 拒绝导出"
                             f"（四阶段模板字段集实测 100% 一致）")
        if not isinstance(ent["name"], str) or not ent["name"].strip():
            raise ValueError(f"boss_phases：{PHASES_SRC}[{pid!r}].name 不是非空字符串 —— 拒绝导出")
        if not isinstance(ent["add_skills"], list):
            raise ValueError(f"boss_phases：{PHASES_SRC}[{pid!r}].add_skills 不是 list"
                             f"（{type(ent['add_skills']).__name__}）—— 拒绝导出")
        if not isinstance(ent["preserve_debuffs"], bool):
            raise ValueError(f"boss_phases：{PHASES_SRC}[{pid!r}].preserve_debuffs 不是 bool —— 拒绝导出")
        out[pid] = dict(ent)                    # 字段顺序原样

    if len(out) != 4:
        raise ValueError(f"boss_phases：{PHASES_SRC} 实测 4 条四阶段模板，本次得到 {len(out)} 条"
                         f"（{sorted(out)}）—— 源形状变了，拒绝导出")
    return sort_table(out)


DOMAINS = {
    "boss_phases": derive_boss_phases,
}
