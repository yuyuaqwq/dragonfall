#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚 · 配置编辑器 —— 战斗模拟 **worker**（在独立子进程里跑引擎）。

⚠️ 为什么必须是子进程（见 editor/simulate.py 顶部说明）：
  1. 本仓库存在循环导入陷阱（`game.data ↔ game.core`），且引擎装配 `load_game_defaults()`
     有**全局副作用**（把公式/面板/kind 常量往 `battle2.config` 的 hook 面 mount）。
     编辑器主进程一旦 import game 就会被污染，且与「编辑器的数据层只读 py 源码字面量、
     绝不 import game」这条已定纪律冲突。
  2. 引擎装配/战斗推进可能抛异常甚至死循环 —— 丢进子进程可以用超时兜底、失败不拖垮编辑器。
  3. 模拟是**纯内存**的：不写任何游戏数据、不写工作副本、不碰数据库。

协议（父 ↔ 子）
---------------
  stdin  : 一行 JSON —— {"skill": {...}, "attacker": {...}, "defender": {...},
                          "skill_lv": 1, "seed": 1}
  stdout : 最终结果写成一行   __DF_SIM_RESULT__<json>
           （前面可能有引擎/内容的零星 print —— 父进程只认这个 marker 行）
  stderr : 异常栈（父进程失败时取摘要回传）

单独手跑（调试用）：
  echo '{"skill":{"name":"挥砍","kind":"物理","lv":1,"mp":6,"exprs":["atk*1.0+10"],"desc":"x"}}' \
      | python editor/simulate_worker.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import traceback

MARKER = "__DF_SIM_RESULT__"

EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(EDITOR_DIR)                       # dragonfall/
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))  # qqbot/

# 引擎不在这些面板字段上做玩家聚合；模拟透传它们
_PANEL_KEYS = ("atk", "matk", "def", "mdef", "spd", "crit", "dodge", "crit_dmg",
               "pene", "block", "tenacity", "luck")


def _emit(obj: dict) -> None:
    """把结果写到 stdout 的 marker 行（JSON 单行、UTF-8）。"""
    sys.stdout.write("\n" + MARKER + json.dumps(obj, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()


def _tail(text: str, n: int = 25) -> str:
    lines = (text or "").replace("\r\n", "\n").strip().splitlines()
    return "\n".join(lines[-n:])


# --------------------------------------------------------------------- env setup
def _setup_paths() -> None:
    """照 tests/ 里的 sys.path 补丁写法：qqbot 根 + 插件根 + 引擎框架根 + astrbot shim。"""
    for p in (QQBOT_DIR, PLUGIN_DIR, os.path.join(PLUGIN_DIR, "framework")):
        # ↑ framework：引擎框架包（S8 物理分离，`battle2` 在该目录下）
        if p and p not in sys.path:
            sys.path.insert(0, p)
    shim = os.path.join(PLUGIN_DIR, "tests", "shim_astrbot")
    if os.path.isdir(shim) and shim not in sys.path:
        sys.path.insert(0, shim)
    # 绝对不碰生产库：把 DB 路径指到一个临时（且不会真正被打开的）文件。
    # 实测引擎装配 + 起战斗全程零 DB 访问（不创建文件）；这里只是保险栓。
    os.environ.setdefault("GWEN_TEST_MODE", "1")
    if not os.environ.get("GWEN_GAME_DB"):
        os.environ["GWEN_GAME_DB"] = os.path.join(
            tempfile.gettempdir(), f"df_editor_sim_{os.getpid()}.db")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ------------------------------------------------------------------ actor builders
def _build_attacker(E, make_actor, spec: dict) -> dict:
    """模拟施法者：默认按「职业面板 × 等级」聚合（与命令层同口径 player_final_stats）。"""
    spec = spec or {}
    cls = spec.get("class_name") or spec.get("cls_name") or spec.get("class") or "战士"
    level = int(spec.get("level") or 20)
    st = {}
    try:
        st = E.player_final_stats(cls, level, {}, 0, {}, 1) or {}
    except Exception:
        st = {}
    panel = {k: st[k] for k in _PANEL_KEYS if k in st}
    # 显式面板覆盖（前端可传 {"atk": 200} 之类临时调参）
    panel.update({k: v for k, v in (spec.get("panel") or {}).items() if k in _PANEL_KEYS})
    max_hp = int(spec.get("max_hp") or max(int(st.get("max_hp") or 0) * 3, 9999))
    max_mp = int(spec.get("max_mp") or max(int(st.get("max_mp") or 0), 999))
    # 施法者默认不满血（60%）——治疗类技能要留出回血空间，否则被 max_hp clamp 成 0
    hp = int(spec.get("hp") or round(max_hp * 0.6))
    a = make_actor(
        uid="sim_atk", name=spec.get("name") or "模拟者", side="player", kind="player",
        human_controlled=True, class_name=cls, level=level,
        hp=hp, max_hp=max_hp, mp=max_mp, max_mp=max_mp,
        skills=[], learned_skills=[], race=None, evolve_path=0, class_tier=0,
        attributes={}, **panel)
    # 预置效果/资源（如 {"rage": 5} → effects["rage"]={"stacks":5}；预览消费类技能的足额判定）
    for k, v in (spec.get("effects") or {}).items():
        stacks = v.get("stacks", v) if isinstance(v, dict) else v
        a.setdefault("effects", {})[str(k)] = {"stacks": stacks}
    return a, {"class_name": cls, "level": level, "panel": panel,
               "max_hp": max_hp, "max_mp": max_mp}


def _build_defender(make_actor, spec: dict, atk_level: int) -> tuple:
    """模拟目标：默认是一根「不还手、不闪避」的标准木桩（便于读数）。

    引擎等级压制（landing._lv_pressure）按双方 level 比较 → 默认与施法者同级。
    """
    spec = spec or {}
    level = int(spec.get("level") or atk_level or 20)
    hp = int(spec.get("hp") or 10_000_000)
    panel = {"atk": int(spec.get("atk", 10)), "matk": int(spec.get("matk", 10)),
             "def": int(spec.get("def", 80)), "mdef": int(spec.get("mdef", 80)),
             "spd": int(spec.get("spd", 5)), "crit": float(spec.get("crit", 0.0)),
             "dodge": float(spec.get("dodge", 0.0))}
    panel.update({k: v for k, v in (spec.get("panel") or {}).items() if k in _PANEL_KEYS})
    d = make_actor(uid="sim_def", name=spec.get("name") or "木桩", side="enemy",
                   kind="monster", level=level, hp=hp, max_hp=hp, **panel)
    return d, {"name": d["name"], "level": level, "hp": hp, "panel": panel}


# ------------------------------------------------------------------------ runner
def _condense_event_ctx(ctx) -> dict:
    out = {}
    if not isinstance(ctx, dict):
        return out
    for k, v in ctx.items():
        if isinstance(v, dict):
            if "name" in v:
                out[k] = v.get("name")
            elif "uid" in v:
                out[k] = v.get("uid")
            elif k == "info":
                out["info"] = v.get("name")
        elif isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
    return out


def run(payload: dict) -> dict:
    skill = payload.get("skill")
    if not isinstance(skill, dict) or not skill:
        return {"ok": False, "stage": "input", "message": "缺少技能数据（skill）"}
    name = skill.get("name")
    if not name:
        return {"ok": False, "stage": "input", "message": "技能缺少 name 字段，无法施放"}

    skill_lv = int(payload.get("skill_lv") or 1)
    seed = payload.get("seed")
    seed = 1 if seed in (None, "") else int(seed)

    # ---- 装配引擎（第一处 import game —— 只发生在子进程里） ----
    from battle2 import config as _b2c
    from game.content_rules.apply import ensure_engine_configured as _eng_cfg; _eng_cfg()
    from game import engine as E
    from battle2 import Battle, make_actor

    # 技能等级：模拟固定为指定等级（引擎默认查玩家已学等级，模拟的临时技能查不到 → 0）
    try:
        _b2c.mount(skill_level_of_fn=lambda actor, sname: skill_lv)
    except Exception:
        pass  # 装配面不支持时回落默认（lv 0 → 引擎内部按 1 处理）

    atk_spec = payload.get("attacker") or {}
    def_spec = payload.get("defender") or {}
    attacker, atk_info = _build_attacker(E, make_actor, atk_spec)
    defender, def_info = _build_defender(make_actor, def_spec, atk_info["level"])

    events: list = []

    def _on_event(_battle, event, ctx, _logs):
        try:
            events.append({"event": event, "ctx": _condense_event_ctx(ctx)})
        except Exception:
            events.append({"event": event, "ctx": {}})

    b = Battle(btype="monster", sides={"player": [attacker], "enemy": [defender]},
               on_event=_on_event)

    # 关键：把「传进来的技能 dict」直接挂进施法者的技能索引
    # （ActCtx 在 action=skill 且 info 为空时从 caster["_skill_index"][skill_name] 取 info）
    attacker.setdefault("_skill_index", {})[name] = skill
    if name not in (attacker.get("skills") or []):
        attacker.setdefault("skills", []).append(name)

    mp_before = int(attacker.get("mp", 0) or 0)
    atk_hp_before = int(attacker.get("hp", 0) or 0)
    def_hp_before = int(defender.get("hp", 0) or 0)

    random.seed(seed)
    logs, ended, _who = b.human_act("skill", name, attacker)

    def_hp_after = int(defender.get("hp", 0) or 0)
    atk_hp_after = int(attacker.get("hp", 0) or 0)
    delta = def_hp_before - def_hp_after            # >0 = 对目标造成伤害
    self_delta = atk_hp_before - atk_hp_after       # <0 = 施法者自己回血

    warnings = []
    kind = str(skill.get("kind") or "")
    if delta <= 0 and self_delta <= 0 and not (skill.get("mech") or skill.get("effect")):
        warnings.append(f"本次施放未造成伤害（kind={kind or '未填'}）——若为增益/控制/被动技能，请看下方战斗日志。")
    if kind == "被动":
        warnings.append("该技能 kind=被动，通常无主动施放效果；模拟仅按技能管道跑一次，结果可能为空。")
    if any("不足" in x or "无法使用技能" in x for x in logs):
        warnings.append("施放被前置校验拦下（资源/蓝量不足？）——可给施法者预置资源后再试。")
    if any("不存在" in x or "没有可攻击的目标" in x for x in logs):
        warnings.append("技能未命中目标或技能识别失败，请检查技能字段。")

    return {
        "ok": True,
        "damage": int(delta),
        "self_heal": int(-self_delta) if self_delta < 0 else 0,
        "mp_used": int(mp_before - int(attacker.get("mp", 0) or 0)),
        "hp": {"target_before": def_hp_before, "target_after": def_hp_after,
               "caster_before": atk_hp_before, "caster_after": atk_hp_after},
        "logs": logs,
        "events": events,
        "ended": bool(ended),
        "result": b.result,
        "skill": {"name": name, "kind": kind, "lv": skill_lv,
                  "mp": skill.get("mp"), "cd": skill.get("cd")},
        "attacker": atk_info,
        "defender": def_info,
        "seed": seed,
        "warnings": warnings,
        "engine": {"configured": True},
    }


def main() -> int:
    _setup_paths()
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except Exception as exc:
        _emit({"ok": False, "stage": "input",
               "message": f"入参不是合法 JSON：{exc}"})
        return 0
    try:
        res = run(payload)
    except Exception:
        tb = traceback.format_exc()
        first = tb.strip().splitlines()[-1] if tb.strip() else "未知异常"
        _emit({"ok": False, "stage": "engine",
               "message": f"引擎模拟失败：{first}",
               "traceback": _tail(tb, 20)})
        return 0
    _emit(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
