# -*- coding: utf-8 -*-
"""v181.P2D-D5（准备）对照参考：battle.py 顶部模块级 tick handler 迁移前的 OLD 逻辑副本。

P2D-D6 迁移 _th_passive_heal 内 focus_regen_summon 分支 / _th_mech_charge 内
arcane_intuition 分支 / _th_faith_decay 内 undead_faith + faith_overload_heal 分支
到 passive_procs 注册表族后，本模块保留**迁移前三个 handler 逐字副本**供
OLD-vs-NEW 差分探针（tests/test_p2dd6_tick_families.py 用）——OLD handler 返回
(logs, keep)，与 NEW 现引擎同名模块级 handler 同签名同语义。

铁律：本文件只读参考，不参与运行路径（无 import 方）。OLD 副本引用的模块级依赖
（E = engine、_battle_warn = battle.py 模块函数、focus_active 相对导入在 tests 包
下失效 → 全部由探针 _bind_ref() 注入 OLD.E/OLD._BATTLE_WARN/OLD._focus_active）。
"""
from __future__ import annotations

E = None
_BATTLE_WARN = None
_FOCUS_ACTIVE = None


def _battle_warn(site, exc):
    if _BATTLE_WARN is not None:
        _BATTLE_WARN(site, exc)
        return
    import logging as _lg
    _lg.getLogger("dragonfall.battle").warning("[OLD-ref] %s: %r", site, exc)


# ==== OLD: _th_passive_heal（294-332 迁移前逐字副本）====
def OLD_th_passive_heal(battle, actor, eff, logs):
    """被动回复族：气力调和(turn_heal)/生命之泉(team_regen)/森之共鸣(focus_regen_summon)。条件：对应被动存在。"""
    try:
        _pm = battle._passive_map(actor)["proc"]
        out = []
        _alive_ok = True
        _th = _pm.get("turn_heal") or []
        for _pn, _ps in _th:
            if actor.get("hp", 0) < actor.get("max_hp", 1):
                heal = int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("pct", 0.02)))
                battle._heal_actor(actor, heal, out)  # v180E 统一落地
                out.append(f"🍃 {_pn}生效，你回复了 {heal} 点生命！")
            break
        _tr = _pm.get("team_regen") or []
        for _pn, _ps in _tr:
            if actor.get("hp", 0) < actor.get("max_hp", 1):
                heal = int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("mult", 0.05)))
                battle._heal_actor(actor, heal, out)  # v180E 统一落地
                out.append(f"💧 {_pn}：生命之泉涌动，你回复了 {heal} 点生命！")
            break
        try:
            if battle.summons:
                for _pn, _ps in _pm.get("focus_regen_summon", []):
                    _sr_gain = int(_ps.get("gain", 5) or 5)
                    _sr_old = int(actor.setdefault('resources', {}).get("energy", 0) or 0)
                    _sr_new = battle._res_gain(actor, "energy", _sr_gain)
                    if _sr_new > _sr_old:
                        out.append(f"🌳 {_pn}：召唤物在场，专注充能 +{_sr_gain}（{_sr_new}）")
                    break
        except Exception as _sw_e:
            _battle_warn('_th_passive_heal', _sw_e)
            pass
        # 无任何被动 → 通道关闭
        if not (_th or _tr or _pm.get("focus_regen_summon")):
            return [], False
        return out, True
    except Exception:
        return [], False


# ==== OLD: _th_mech_charge（334-373 迁移前逐字副本）====
def OLD_th_mech_charge(battle, actor, eff, logs):
    """奥术/魔剑充能族：arcane_regen/arcane_intuition/spellblade_regen。条件：对应被动存在。"""
    try:
        _pm = battle._passive_map(actor)
        out = []
        _alive = False
        for _pn, _ps in _pm["proc"].get("arcane_regen", []):
            _mech = _ps.get("mech") or "arcane"
            actor.setdefault('stacks', {})[_mech] = E.mech_stack_gain(_mech, actor.setdefault('stacks', {}), 1)
            out.append(f"📖 {_pn}：充能自动+1(当前 {actor.setdefault('stacks', {})[_mech]} 层)")
            _alive = True
            break
        for _pn, _ps in _pm["proc"].get("arcane_intuition", []):
            _mech2 = _ps.get("mech") or "arcane"
            _gain2 = int(_ps.get("gain", 1) or 1)
            try:
                if _FOCUS_ACTIVE is not None and _FOCUS_ACTIVE(actor):
                    _gain2 += int(_ps.get("focus_gain", 1) or 1)
            except Exception as _sw_e:
                _battle_warn('_th_mech_charge', _sw_e)
                pass
            _before2 = int(actor.setdefault('stacks', {}).get(_mech2, 0) or 0)
            actor.setdefault('stacks', {})[_mech2] = E.mech_stack_gain(_mech2, actor.setdefault('stacks', {}), _gain2)
            if int(actor.setdefault('stacks', {}).get(_mech2, 0) or 0) > _before2:
                out.append(f"📖 {_pn}：每刻充能自动+{_gain2}(当前 {actor.setdefault('stacks', {})[_mech2]} 层)")
            _alive = True
            break
        for _pn, _ps in _pm["stat"]:
            if _ps.get("stat") == "spellblade_regen":
                _mech = _ps.get("mech") or "spellblade"
                actor.setdefault('stacks', {})[_mech] = E.mech_stack_gain(_mech, actor.setdefault('stacks', {}), 1)
                out.append(f"⚔️ {_pn}：魔能自动+1(当前 {actor.setdefault('stacks', {})[_mech]} 层)")
                _alive = True
                break
        if not _alive:
            return [], False
        return out, True
    except Exception:
        return [], False


# ==== OLD: _th_faith_decay（404-457 迁移前逐字副本）====
def OLD_th_faith_decay(battle, actor, eff, logs):
    """牧师信念衰减/亡灵祭仪/过载状态机。条件：职业核心资源是 faith 且带 decay。"""
    try:
        _crd_f = E.core_resource_def(actor.get("class_name", ""))
        if not (_crd_f and _crd_f.get("key") == "faith"):
            return [], False  # 非信念职业 → 通道关闭
        out = []
        # 亡灵祭仪（先产后衰）
        try:
            if _crd_f.get("key") == "faith":
                for _pn, _ps in battle._passive_map(actor)["proc"].get("undead_faith", []):
                    _uf_n = battle._undead_count()
                    if _uf_n > 0 and not actor.setdefault('buffs', {}).get("faith_exhausted"):
                        _uf_gain = float(_ps.get("per_undead", 0.15) or 0.15) * _uf_n
                        _f0 = float(actor.setdefault('resources', {}).get("faith", 0) or 0)
                        actor.setdefault('resources', {})["faith"] = min(float(_crd_f.get("max", 10) or 10), _f0 + _uf_gain)
                        out.append(f"🕯️ {_pn}：{_uf_n} 只亡灵在场，信念 +{_uf_gain:.2f}（{actor.setdefault('resources', {})['faith']:.2f}）")
                    break
        except Exception as _sw_e:
            _battle_warn('_th_faith_decay', _sw_e)
            pass
        if _crd_f.get("decay_per_tick"):
            _f_before = float(actor.setdefault('resources', {}).get("faith", 0) or 0)
            if _f_before >= float(_crd_f.get("max", 10)):
                _ov_pct = float(_crd_f.get("overload_heal_pct", 0.015) or 0.015)
                _ov_heal = int(actor.get("max_hp", 1) * _ov_pct * _f_before)
                actor.setdefault('resources', {})["faith"] = 0
                _foheal = False
                try:
                    for _pn_fh, _ps_fh in battle._proc_pm(actor)["proc"].get("faith_overload_heal", []):
                        _ov_heal = int(_ov_heal * (1.0 + float(_ps_fh.get("heal_up", 0.30) or 0.30)))
                        _foheal = True
                        break
                except Exception as _sw_e:
                    _battle_warn('_th_faith_decay', _sw_e)
                    pass
                out.append(f"⚡ 信念过载！信仰之力迸发，全队回复 {_ov_heal} 点生命！")
                if not _foheal:
                    actor.setdefault('buffs', {})["faith_exhausted"] = 6
                else:
                    out.append("✨ 信念·圣化：信念过载化为圣辉，无力竭反噬！")
                if actor.get("hp", 0) < actor.get("max_hp", 1):
                    battle._heal_actor(actor, _ov_heal, out)  # v180E 统一落地
                    out.append(f"✨ 过载回响：你回复了 {_ov_heal} 点生命！")
            elif _f_before > 0:
                _f_decay = float(_crd_f.get("decay_per_tick", 0.7) or 0.7)
                actor.setdefault('resources', {})["faith"] = max(0.0, _f_before - _f_decay)
                if float(actor.setdefault('resources', {})["faith"]) < _f_before:
                    out.append(f"🕯️ 信念衰减：{_f_before:.1f} → {float(actor.setdefault('resources', {})['faith']):.1f}")
            if actor.setdefault('buffs', {}).get("faith_exhausted"):
                actor.setdefault('buffs', {})["faith_exhausted"] = int(actor.setdefault('buffs', {})["faith_exhausted"]) - 1
        return out, True
    except Exception:
        return [], False
