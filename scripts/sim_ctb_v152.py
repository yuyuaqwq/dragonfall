# v152 CTB 事件队列数值标定模拟
# 验证：v152 事件队列下行动频率是否仍保持 spd 比例（v121 已验证 3:1/5:1）
# 对比对象：v152 引擎（battle.py 新事件队列）
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from game import battle as BT

def run_combat(p_spd, e_spd, p_acts_target=100, seed=42):
    """跑一场战斗，统计玩家/敌方行动次数直到玩家行动 p_acts_target 次或战斗结束。"""
    random.seed(seed)
    player = {'name': '模拟', 'hp': 100000, 'max_hp': 100000, 'mp': 1000, 'max_mp': 1000,
              'atk': 50, 'def': 20, 'spd': p_spd, 'class_name': '战士', 'level': 30,
              'equipment': {}, 'learned_skills': [], 'skill_levels': {}, 'qq_id': 'sim'}
    enemy = {'name': '模拟怪', 'hp': 10000000, 'max_hp': 10000000, 'atk': 10, 'def': 5, 'spd': e_spd}
    b = BT.Battle('monster', enemy, player=player)
    # 用 _player_stats 的真实 spd（职业成长可能覆盖传入值）
    real_p_spd = b._player_stats(player).get('spd', p_spd)
    real_e_spd = b._enemy_stats().get('spd', e_spd)
    p_acts = 0
    e_acts = 0
    for i in range(500):
        logs, ended = b.actor_turn('attack', None, player)
        p_acts += 1
        # 统计敌方行动：从日志数敌方攻击行
        for l in logs:
            if '攻击你' in l:
                e_acts += 1
        if ended:
            break
        if p_acts >= p_acts_target:
            break
    return p_acts, e_acts, real_p_spd, real_e_spd

print("=" * 60)
print("v152 事件队列：行动频率标定（理论比 = spd_p/spd_e）")
print("=" * 60)

cases = [
    ("1:1  (20 vs 20)", 20, 20, 1.0),
    ("2:1  (20 vs 10)", 20, 10, 2.0),
    ("3:1  (60 vs 20)", 60, 20, 3.0),
    ("5:1  (100 vs 20, cap80)", 100, 20, 4.35),  # cap=80 压缩
    ("1:2  (10 vs 20)", 10, 20, 0.5),
    ("1:3  (20 vs 60)", 20, 60, 0.333),
]
print(f"{'场景':<28} {'玩家动':<6} {'敌动':<6} {'实测比':<8} {'理论比':<8} {'偏差'}")
for name, ps, es, theory in cases:
    p, e, rps, res = run_combat(ps, es, p_acts_target=60)
    # 理论比 = 新模型公式：频率 = 1/(间隔+动作耗时)，间隔 = BASE_DELAY/spd
    # （v152 鱼鱼拍板：总耗时 = 速度间隔 + 固定动作耗时，动作耗时稀释极端速度差）
    p_cycle = BT.BASE_DELAY / max(1.0, rps) + BT.CAST_ATK
    e_cycle = BT.BASE_DELAY / max(1.0, res) + BT.CAST_ATK
    theory_real = e_cycle / p_cycle
    ratio = p / max(1, e)
    dev = (ratio - theory_real) / theory_real * 100 if theory_real else 0
    flag = "OK" if abs(dev) < 25 else "!!"
    print(f"{name:<28} {p:<6} {e:<6} {ratio:<8.2f} {theory_real:<8.2f} {dev:+.0f}% {flag} (spd {rps}/{res})")

print()
print("=" * 60)
print("行为时长验证：不同行为的 p_ct 推进（玩家 spd 30 → cost 3.33）")
print("=" * 60)
player = {'name': '模拟', 'hp': 500, 'max_hp': 500, 'mp': 100, 'max_mp': 100,
          'atk': 50, 'def': 20, 'spd': 30, 'class_name': '战士', 'level': 5,
          'equipment': {}, 'learned_skills': [], 'skill_levels': {}, 'qq_id': 'sim'}
enemy = {'name': '怪', 'hp': 300, 'max_hp': 300, 'atk': 10, 'def': 5, 'spd': 10}
b = BT.Battle('monster', enemy, player=player)
spd = b._player_stats(player).get('spd', 0)
cost = b._ct_cost(spd)
print(f"玩家 spd={spd} cost={cost:.2f}")
for act, mult, label in [('attack', BT.CAST_ATK, '普攻'), ('skill', BT.CAST_SKILL, '技能'),
                          ('defend', BT.CAST_DEFEND, '防御'), ('flee', BT.CAST_FLEE, '逃跑')]:
    b2 = BT.Battle('monster', dict(enemy), player=dict(player))
    if act == 'skill':
        # 无技能可放 → 会转普攻，直接测 _after_actor_ct 的 cast_mult
        b2._after_actor_ct('p', player=player, cast_mult=mult)
    else:
        b2._after_actor_ct('p', player=player, cast_mult=mult)
    # v152 新模型（鱼鱼拍板）：p_ct 推进 = cost（间隔）+ 固定动作耗时（cast_mult）
    expect = cost + mult
    print(f"  {label:<6} cast_mult={mult:<4} p_ct推进={b2.p_ct:.2f} (期望 {expect:.2f}) {'OK' if abs(b2.p_ct - expect) < 0.01 else '!!'}")
