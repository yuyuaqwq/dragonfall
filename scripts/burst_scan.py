# -*- coding: utf-8 -*-
"""v133 爆发峰值扫描（只读，真实引擎采样）

用法：
  python scripts/burst_scan.py --cls cls_ci_ke --lv 20 --loadout naked --diff 0
  python scripts/burst_scan.py --cls cls_fa_shi --lv 40 --loadout blue5 --diff 3

输出 CSV（stdout）：
  cls,lv,loadout,diff,skill,peak_dmg,target_hp,peak_pct,target_lv

口径：
  玩家：主属性全投，技能 lv3，种族 human（中性），tier 按等级自动（30/60/90），
        装备档位 naked={} / blue5=七部位蓝装+5（走 EQUIP_SLOT_BASE×QUALITY×ENHANCE）
  目标：dps 普通怪（build_monster 真实血量，lv = 玩家lv + diff，无 FIELD_TIER_MULT）
  峰值：每个攻击技能跑 25 seeds Battle 采样取 max（含暴击/幸运/波动上限）；
        刺客先放潜行（必暴）；武僧碎骨拳先普攻 3 次攒气。
"""
import sys, argparse, random, json

sys.path.insert(0, 'C:/Users/yuyu/qqbot/data/plugins')
from game.content_rules.panel import player_final_stats
from dragonfall.game.core.drops import build_monster
from dragonfall.game.battle import Battle
from dragonfall.game.data import skills as SK_DATA

CLS_MAIN = {
    # 峰值口径：物理职业投 str、魔法职业投 int（单发伤害最大化）
    'cls_zhan_shi': 'str', 'cls_you_xia': 'str', 'cls_fa_shi': 'int',
    'cls_mu_shi': 'int', 'cls_ci_ke': 'str', 'cls_wu_seng': 'str',
}
TIER = {30: 1, 60: 2, 90: 3}

def attr_alloc(cls, lv):
    pts = 9 + 3 * (lv - 1)
    return {CLS_MAIN[cls]: pts}

def slot_stats(slot, lv, quality_mult, enhance_mult):
    s = {}
    # 直接读数据表
    from dragonfall.game.data.stat_templates import EQUIP_SLOT_BASE, EQUIP_SLOT_SCALING
    from dragonfall.game.data import QUALITY
    qmult = QUALITY.get(quality_mult, {}).get('mult', 1.0) if isinstance(quality_mult, str) else quality_mult
    for k, base in EQUIP_SLOT_BASE.get(slot, {}).items():
        sc = EQUIP_SLOT_SCALING.get(slot, {}).get(k, 0)
        s[k] = int((base + sc * lv) * qmult * enhance_mult)
    return s

def make_equipment(lv, loadout):
    if loadout == 'naked':
        return {}
    from dragonfall.game.data.stat_templates import EQUIP_SLOT_BASE
    from dragonfall.game.data import QUALITY, ENHANCE_TABLE
    qmult = QUALITY['blue']['mult'] if isinstance(QUALITY.get('blue'), dict) else 1.0
    emult = ENHANCE_TABLE.get(5, {}).get('mult', 1.0)
    eq = {}
    for slot in EQUIP_SLOT_BASE:
        stats = slot_stats(slot, lv, qmult, emult)
        eq[slot] = {'name': '扫描用' + slot, 'slot': slot, 'quality': 'blue',
                    'lv': lv, 'stats': stats, 'affixes': []}
    return eq

def player_dict(cls, lv, loadout):
    tier = TIER.get(lv, 0)
    return dict(level=lv, class_name=cls, class_tier=tier,
                equipment=make_equipment(lv, loadout),
                attributes=attr_alloc(cls, lv), evolve_path=0, race='human',
                skill_levels={}, learned_skills=[],
                hp=500, mp=200, max_hp=500, max_mp=200, exp=0, gold=0, cur_map='x')

def attack_skills(cls, lv, branch=False):
    """该职业所有攻击技能（kind ∈ 物理/魔法/真伤，且学习等级 ≤ 玩家等级——
    合理玩家口径：低等级玩家不会/不能放高等级大招，修正低等级假超限）
    branch=True 时收集转职分支技能（BRANCH_SKILLS 全分支）"""
    out = []
    if branch:
        br = getattr(SK_DATA, 'BRANCH_SKILLS', {}).get(cls, {})
        for bno, branches in br.get('branches', {}).items():
            for bname, skills in branches.items():
                for k, info in skills.items():
                    name = info.get('name', k)
                    need_lv = int(info.get('lv', 1) or 1)
                    if info.get('kind') in ('物理', '魔法', '真伤') and info.get('power', 0) > 0 \
                            and need_lv <= lv:
                        out.append((name, info))
        return out
    cls_data = SK_DATA.PLAYER_SKILLS.get(cls, {})
    for k, info in cls_data.get('skills', {}).items():
        name = info.get('name', k)
        need_lv = int(info.get('lv', 1) or 1)
        if info.get('kind') in ('物理', '魔法', '真伤') and info.get('power', 0) > 0 \
                and need_lv <= lv:
            out.append((name, info))
    return out

def peak_of(cls, lv, loadout, diff, seeds=25, branch=False):
    p = player_dict(cls, lv, loadout)
    skills = attack_skills(cls, lv, branch=branch)
    tlv = lv + diff
    base_mon = ('m_scan', '扫描靶', 'dps', tlv, [], [])
    mon = build_monster(base_mon, {'name': '靶场', 'id': 'scan_range', 'area': 'field'})
    rows = []
    learned = [s[0] for s in skills]
    # v151：自带"满血必暴"窗口的技能名集合（cond.type=enemy_full_hp，如 v151 暗杀）——
    # 采样时不再额外叠潜行必暴（潜行必暴 + 满血必暴 = 双必暴窗口假峰值）
    _own_crit = {n for n, i2 in skills
                 if (i2.get("cond") or {}).get("type") in ("enemy_full_hp", "full_hp")}
    for name, info in skills:
        pd = dict(p)
        pd['learned_skills'] = learned
        pd['skill_levels'] = {name: 3}
        best = 0
        for sd in range(seeds):
            random.seed(sd * 131 + lv * 7 + diff * 3 + len(rows))
            m2 = build_monster(base_mon, {'name': '靶场', 'id': 'scan_range', 'area': 'field'})
            b = Battle('monster', enemy=m2, player=pd)
            # 资源给满（峰值口径：按旧 core_resources 上限注入——R2c 退役，上限值同 EFFECT_RULES cap；
            # 禁 999 防"层数×倍率"爆炸）
            RES_MAX = {'rage': 10, 'element': 5, 'energy': 100, 'faith': 10, 'cp': 5,
                       'chi': 10, 'dragon_might': 10, 'time_sand': 5, 'hunt_mark': 5,
                       'canticle': 10, 'shadow_step': 5, 'zen': 10, 'resonance': 10, 'echo': 3}
            rc = info.get('res_cost') or {}
            cc = info.get('consume_all') or {}
            for rk, rv in list(rc.items()) + [(cc.get('key'), 1)]:
                if rk:
                    b._p_res()[rk] = RES_MAX.get(rk, 5)
            if cls == 'cls_ci_ke' and name != '潜行' and name not in _own_crit:
                # 先潜行（必暴窗口）
                # v151 修正：自带"满血必暴"窗口的技能（cond.type=enemy_full_hp，如 v151 暗杀）
                # 不再额外叠潜行必暴——潜行必暴 + 满血必暴是双必暴窗口（实战中潜行会被
                # 其他攻击先消耗，暗杀只能享受其自身窗口），叠两层会得到假峰值。
                # 仅对无自带必暴窗口的技能维持潜行采样（v133 刺客口径）。
                b._p_buffs_bag()['stealth'] = 1
            if cls == 'cls_wu_seng' and name == '碎骨拳':
                # 攒 3 气：普攻 3 次
                for _ in range(3):
                    b.actor_turn('attack', None, pd)
            res, ended = b.actor_turn('skill', name, pd)
            line = [x for x in res if isinstance(x, str) and ('造成' in x or '共造成' in x)]
            import re
            mm = re.search(r'(?:共造成|造成) (\d+) 点伤害', ' '.join(line))
            if mm:
                d = int(mm.group(1))
                if d > best:
                    best = d
        rows.append((name, best, mon['hp'], mon['lv']))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cls', required=True)
    ap.add_argument('--lv', type=int, required=True)
    ap.add_argument('--loadout', default='naked')
    ap.add_argument('--diff', type=int, default=0)
    ap.add_argument('--branch', action='store_true')
    a = ap.parse_args()
    print('cls,lv,loadout,diff,skill,peak_dmg,target_hp,peak_pct,target_lv')
    rows = peak_of(a.cls, a.lv, a.loadout, a.diff, branch=a.branch)
    for name, d, hp, tlv in rows:
        print(f'{a.cls},{a.lv},{a.loadout},{a.diff},{name},{d},{hp},{round(d * 100 / hp, 1)},{tlv}')

if __name__ == '__main__':
    main()