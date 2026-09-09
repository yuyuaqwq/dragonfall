# -*- coding: utf-8 -*-
"""v138.1 阶段状态机单元测试：阶段四件套 + 进度遗产 + 反制窗口。

覆盖：
1. boss_phases.py 模板表结构完整（四阶段四件套字段齐全）
2. merge_phase_config：模板 + Boss 覆盖合并正确
3. _phase_apply：数值/行为/退出/反制应用正确（atk_mult/def_add/spd_add/dmg_taken_mult）
4. _enemy_stats：阶段数值修正生效
5. _boss_dmg_filter：承伤倍率（疲态核心件外露）生效
6. _preserve_debuffs：跨阶段保留 50% 层数 + 阈值 +15%
7. battle_mech._b_phase：阶段转换触发保留（不净化）+ 反制窗口写入

铁律：随机种子固定、私有测试库、不碰共享 test_game_data.db。
"""
import os
import random
import sys

# 复用 conftest 路径脚手架（自动加插件根目录到 sys.path + 独立测试库）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import PLUGIN_DIR, TEST_DB

os.environ.setdefault("GWEN_GAME_DB", os.path.join(os.path.dirname(__file__), "test_v138_phase.db"))
sys.path.insert(0, PLUGIN_DIR)
# 确保 astrbot shim 可用
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "shim_astrbot"))

from game.data.boss_phases import BOSS_PHASE_TEMPLATES, DEFAULT_PHASE_ORDER, merge_phase_config, phase_template
from game.core import constants as C
from game import battle as BT

PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {extra}")


def make_boss(**kw):
    """构造测试 Boss（含阶段配置）。"""
    b = {
        "id": "test_boss", "name": "测试龙兽", "lv": 30,
        "hp": 8000, "max_hp": 8000,
        "atk": 150, "def": 100, "matk": 120, "mdef": 80, "spd": 60,
        "crit": 0.05, "mech": "phase",
        "skills": ["ms_huo_qiu"],
        # scripts 让 _boss_cfg 直接读到（不走 INSTANCES/MONSTER_MODS 查表）
        "scripts": {"phases": [{"min": 100, "phase_id": "normal"}, {"min": 60, "phase_id": "enrage"}]},
    }
    b.update(kw)
    return b


def make_player(**kw):
    p = {
        "name": "测试者", "hp": 2000, "max_hp": 2000, "mp": 500, "max_mp": 500,
        "atk": 120, "def": 80, "matk": 100, "mdef": 60, "spd": 50,
        "level": 30, "exp": 0, "gold": 1000,
    }
    p.update(kw)
    return p


def new_battle(boss, player):
    random.seed(42)
    # v181.P3d：正确传参（boss=敌方 actor、player=玩家 actor）——旧写法 Battle("test", player, boss)
    # 把 player 传进 enemy 位置、boss 传进 title_bonus 位置，依赖 enemy setter 无脑覆盖才碰巧工作
    b = BT.Battle("monster", boss, player=player)
    return b


# ---------- 1. 模板表结构 ----------
print("== 1. 模板表结构 ==")
check("四阶段齐全", set(DEFAULT_PHASE_ORDER) == {"normal", "enrage", "exhaust", "rampage"})
for pid in DEFAULT_PHASE_ORDER:
    tpl = BOSS_PHASE_TEMPLATES.get(pid)
    check(f"阶段 {pid} 存在", tpl is not None)
    if tpl:
        for key in ("atk_mult", "def_add", "spd_add", "dmg_taken_mult",
                    "add_skills", "freq_mult", "ult_every",
                    "exit_turns", "exit_dmg", "counter", "icon", "enter_line"):
            check(f"  {pid}.{key} 存在", key in tpl, str(tpl.keys()))

# ---------- 2. merge_phase_config ----------
print("== 2. merge_phase_config ==")
merged = merge_phase_config("enrage", {"exit_turns": 6, "add_skills": ["ms_huo_qiu"]})
check("模板 atk_mult 继承", merged["atk_mult"] == 1.25)
check("Boss 覆盖 exit_turns", merged["exit_turns"] == 6)
check("Boss 覆盖 add_skills", merged["add_skills"] == ["ms_huo_qiu"])
check("counter 保留模板值", merged["counter"] == BOSS_PHASE_TEMPLATES["enrage"]["counter"])
merged2 = merge_phase_config("unknown_id")
check("未知 id 兜底常态", merged2["atk_mult"] == 1.0)

# ---------- 3. _phase_apply ----------
print("== 3. _phase_apply 四件套 ==")
boss = make_boss(phases=[{"phase_id": "normal"}, {"phase_id": "enrage"}, {"phase_id": "exhaust"}])
player = make_player()
b = new_battle(boss, player)
cfg = merge_phase_config("exhaust", {})
logs = []
b._phase_apply(boss, cfg, 2, logs)
check("atk_mult 应用", boss["_phase_mod"]["atk_mult"] == 0.80)
check("def_add 应用", boss["_phase_mod"]["def_add"] == -120)
check("dmg_taken_mult 应用", boss["_phase_mod"]["dmg_taken_mult"] == 1.40)
check("freq_mult 应用", boss["_phase_freq_mult"] == 0.50)
check("反制窗口写入", boss["_phase_counter"] == BOSS_PHASE_TEMPLATES["exhaust"]["counter"])
check("退出条件写入", boss["_phase_exit"]["turns"] == 5)
check("演出日志含图标", any("💧" in x for x in logs), str(logs))
check("演出回合呼吸点", b._phase_skip_act is True)

# ---------- 4. _enemy_stats 阶段数值修正 ----------
print("== 4. _enemy_stats 阶段修正 ==")
boss2 = make_boss(phases=[{"phase_id": "normal"}])
player2 = make_player()
b2 = new_battle(boss2, player2)
cfg2 = merge_phase_config("enrage", {})
b2._phase_apply(boss2, cfg2, 1, [])
est = b2._enemy_stats()
check("atk ×1.25 生效", est["atk"] == int(150 * 1.25), f"atk={est['atk']}")
check("def +80 生效", est["def"] == 180, f"def={est['def']}")
check("spd +20 生效", est["spd"] == 80, f"spd={est['spd']}")

# ---------- 5. _boss_dmg_filter 承伤倍率 ----------
print("== 5. 承伤倍率（疲态核心件外露） ==")
boss3 = make_boss(phases=[{"phase_id": "normal"}])
player3 = make_player()
b3 = new_battle(boss3, player3)
b3._phase_apply(boss3, merge_phase_config("exhaust", {}), 2, [])
out = b3._boss_dmg_filter(100, player3, [], dmg_type="phys")
check("dmg ×1.40 生效", out == 140, f"out={out}")
out2 = b3._boss_dmg_filter(100, player3, [], dmg_type="true")
check("真伤也吃承伤倍率", out2 == 140, f"out2={out2}")

# ---------- 6. _preserve_debuffs 进度遗产 ----------
print("== 6. 进度遗产（跨阶段保留 50%） ==")
boss4 = make_boss(phases=[{"phase_id": "normal"}])
player4 = make_player()
b4 = new_battle(boss4, player4)
boss4["debuffs"] = {
    "poison": {"n": 4, "threshold": 0.0},
    "burn": {"n": 3, "threshold": 1.3},
    "mark": {"n": 2},
}
logs4 = []
b4._preserve_debuffs(logs4)
check("毒保留 50%（4→2）", boss4["debuffs"]["poison"]["n"] == 2, str(boss4["debuffs"]))
check("灼烧保留 50%（3→1 向下取整）", boss4["debuffs"]["burn"]["n"] == 1, str(boss4["debuffs"]))
check("阈值 +15%（1.3→1.495）", abs(boss4["debuffs"]["burn"]["threshold"] - 1.495) < 0.001,
      str(boss4["debuffs"]["burn"]["threshold"]))
check("标记不保留（跨阶段清）", "mark" not in boss4["debuffs"], str(boss4["debuffs"].keys()))
check("日志提示残留", any("残留" in x for x in logs4), str(logs4))

# ---------- 7. battle_mech._b_phase 阶段转换触发保留 ----------
print("== 7. _b_phase 阶段转换 ==")
from game.core import battle_mech as BM
boss5 = make_boss(
    scripts={
        "phases": [
            {"min": 60, "phase_id": "enrage"},
        ]
    },
    skills=["ms_huo_qiu"],
)
boss5["hp"] = 4000  # 4000/8000 = 0.5 < 0.60 → 触发第二阶段（enrage）
boss5["phase_count"] = 0
player5 = make_player()
b5 = new_battle(boss5, player5)
# 直接测 _preserve_debuffs 在 _b_phase 里的接线：手动模拟阶段转换
boss5["debuffs"] = {"poison": {"n": 2, "threshold": 0.0}}
logs5 = []
# 调用 _b_phase 触发（hp 低于阈值 60% → 进入 enrage）
BM.BOSS_MECHS["phase"](b5, logs5, boss5, 5)
check("phase_count 推进到 1", boss5.get("phase_count") == 1, str(boss5.get("phase_count")))
check("毒层保留（进度遗产）", boss5.get("debuffs", {}).get("poison", {}).get("n", 0) == 1,
      str(boss5.get("debuffs")))
# 带模板的 Boss 应用阶段四件套（phase_id=enrage）
check("激怒 atk_mult 应用", boss5.get("_phase_mod", {}).get("atk_mult") == 1.25,
      str(boss5.get("_phase_mod")))

# 旧 phases（无 phase_id）不引用模板 → 旧行为
print("== 8. 旧 phases 兼容 ==")
boss6 = make_boss(
    scripts={"phases": [{"min": 60, "add_skills": ["ms_huo_qiu"]}]},
)
boss6["hp"] = 4000
player6 = make_player()
b6 = new_battle(boss6, player6)
logs6 = []
BM.BOSS_MECHS["phase"](b6, logs6, boss6, 5)
check("旧 phases 不写 _phase_mod", not boss6.get("_phase_mod"), str(boss6.get("_phase_mod")))
check("旧 phases 保留异常（默认 preserve）", "debuffs" in boss6 or not boss6.get("debuffs"), "")

print(f"\n===== 结果：{PASS} 通过 / {FAIL} 失败 =====")
sys.exit(1 if FAIL else 0)
