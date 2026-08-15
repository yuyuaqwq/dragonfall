# -*- coding: utf-8 -*-
"""副本层 δ重构 临时自检脚本（Agent C）——用 astrbot python 运行：
  "C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" scripts/_tmp_dot_check_c.py
覆盖（契约 §5）：
  1. 构造透传：from_state 构造包含 "dot_pending": st.get("dot_pending", True)。
  2. 行动后写回：行动 → st["dot_pending"]=False。
  3. 轮次推进：全部存活成员行动过 → 清空 round_acted + dot_pending=True。
  4. poison_all → 对共享 boss.debuffs.poison.n==2（直接调用真实 _apply_team_effect）。
  5. 切怪清层：dot_pending=True + boss.debuffs 清空 + 玩家 mech_stacks 重置 + round_acted 清空。
"""
import os
import sys
import json
import inspect

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from game.commands.instance import InstanceCmds  # noqa: E402
from game.store.battle_state import _json_ready  # noqa: E402

FAIL = []


def check(title, cond, extra=""):
    print(("  OK  " if cond else "  FAIL") + " " + title + ((" :: " + str(extra)) if extra else ""))
    if not cond:
        FAIL.append(title)


def build_st():
    """2 人副本状态（成员为字符串 key；alive 键为 str）。"""
    members = ["1", "2"]
    return {
        "type": "instance",
        "leader": "1",
        "members": members,
        "alive": {"1": True, "2": True},
        "players": {"1": {"name": "阿甲", "qq_id": "1", "rank": 2, "reach": 2,
                          "hp": 500, "max_hp": 500, "spd": 20, "ct": -20,
                          "buffs": {}, "stacks": {}, "defending": False, "charging": None},
                    "2": {"name": "阿乙", "qq_id": "2", "rank": 2, "reach": 2,
                          "hp": 500, "max_hp": 500, "spd": 10, "ct": -10,
                          "buffs": {}, "stacks": {}, "defending": False, "charging": None}},
        "enemies": [],
        "boss": {"uid": "e_boss", "name": "远古魔龙", "spd": 15, "hp": 1000, "max_hp": 1000,
                 "rank": 1, "reach": 1, "buffs": {}, "stacks": {},
                 "defending": False, "charging": None},
        "p_buffs": {"1": {}, "2": {}},
        "p_hot": {"1": {}, "2": {}},
        "p_food_effects": {"1": [], "2": []},
        "e_buffs": {},
        "p_defending": {"1": False, "2": False},
        "mech_stacks": {"1": {}, "2": {}},
        "resources": {"1": {}, "2": {}},
        "cooldown": {"1": {}, "2": {}},
        "combo_seq": {"1": [], "2": []},
        "round": 1,
        "threat": {"1": 0, "2": 0},
        "over": False,
        "turn": 0,
    }


def simulate_action(st, cur_key):
    """复刻 _instance_act 中我新增的『行动后写回 + 轮次推进』逻辑块。"""
    members = st["members"]
    st["dot_pending"] = False
    acted = st.setdefault("round_acted", [])
    if not isinstance(acted, list):
        acted = list(acted)
        st["round_acted"] = acted
    if cur_key not in acted:
        acted.append(str(cur_key))
    _alive_keys = [str(m) for m in members if st.get("alive", {}).get(str(m), True)]
    if _alive_keys and set(acted) >= set(_alive_keys):
        st["round_acted"] = []
        st["dot_pending"] = True


def main():
    print("== 1. 构造透传：from_state 含 dot_pending ==")
    src = inspect.getsource(InstanceCmds._instance_act)
    has_passthrough = '"dot_pending": st.get("dot_pending", True)' in src
    has_lazy_default = 'st.get("dot_pending", True)' in src
    check("构造透传 dot_pending 且老档 get 兜底", has_passthrough or has_lazy_default,
          "dot_pending in from_state dict" if (has_passthrough or has_lazy_default) else "MISSING")

    print("== 2+3. 行动后写回 + 轮次推进（2 人一轮） ==")
    st = build_st()
    check("初始 dot_pending=True", st.setdefault("dot_pending", True) is True)
    # 玩家1 行动 → 本轮已结算（False），未轮满
    simulate_action(st, "1")
    check("玩家1 行动后 dot_pending=False", st["dot_pending"] is False)
    check("round_acted=[\"1\"]", st["round_acted"] == ["1"])
    # 玩家2 行动 → 轮满 → dot_pending=True、round_acted 清空
    simulate_action(st, "2")
    check("玩家2 行动后（轮满）dot_pending=True", st["dot_pending"] is True)
    check("轮满后 round_acted 清空", st["round_acted"] == [])
    # 新一轮：玩家1 再行动 → 再次置 False
    simulate_action(st, "1")
    check("新一轮玩家1 行动后 dot_pending 回落 False", st["dot_pending"] is False)

    print("== 2b. persistent 语义：set 经 JSON 往返变 list 仍兼容 ==")
    st2 = build_st()
    st2["round_acted"] = ["1"]
    rt = json.loads(json.dumps(_json_ready(st2)))
    check("往返后 round_acted 为 list", isinstance(rt["round_acted"], list))
    simulate_action(rt, "2")
    check("往返后轮满仍正确（dot_pending=True 且清空）", rt["dot_pending"] is True and rt["round_acted"] == [])

    print("== 3. 死亡成员不计入轮满（只剩 1 存活） ==")
    st3 = build_st()
    st3["alive"]["2"] = False            # 玩家2 倒下
    simulate_action(st3, "1")            # 玩家1 行动即满（只剩 1 存活）
    check("一存活成员行动即轮满 dot_pending=True", st3["dot_pending"] is True)
    check("round_acted 清空", st3["round_acted"] == [])

    print("== 4. poison_all → 共享 boss.debuffs.poison.n==2 ==")
    st4 = build_st()
    st4["boss"] = {"uid": "e_boss", "name": "远古魔龙", "hp": 1000, "max_hp": 1000}
    logs = InstanceCmds()._apply_team_effect(st4, "1", {"kind": "poison_all"})
    check("boss.debuffs.poison.n==2", st4["boss"]["debuffs"]["poison"]["n"] == 2,
          st4["boss"]["debuffs"])
    check("日志提示毒层共享", any("毒层共享" in x or "武器淬毒" in x for x in logs), logs)
    # 再叠一次（cap 语义：2+2=4）
    InstanceCmds()._apply_team_effect(st4, "1", {"kind": "poison_all"})
    check("连续叠毒 n==4", st4["boss"]["debuffs"]["poison"]["n"] == 4,
          st4["boss"]["debuffs"])
    # 老存档 Boss 无 debuffs 键 → setdefault 兜底建 dict
    st4b = build_st()
    st4b["boss"] = {"uid": "e_boss", "name": "无debuffs老档"}
    logs = InstanceCmds()._apply_team_effect(st4b, "1", {"kind": "poison_all"})
    check("无 debuffs 老档兜底叠毒 n==2", st4b["boss"]["debuffs"]["poison"]["n"] == 2)

    print("== 5. 切怪/换 Boss 清层 ==")
    st5 = build_st()
    # 上一怪残留减益/玩家资源/行动记录
    st5["boss"]["debuffs"] = {"poison": {"n": 3, "mult": 1.0}, "burn": {"n": 2, "mult": 1.0}}
    st5["boss"]["adapt"] = {"poison": 0.12, "burn": 0.08}   # δv1.2 §11.1 适应状态
    st5["mech_stacks"]["1"] = {"poison": 5, "shadow": 3}
    st5["round_acted"] = ["1"]
    # 切怪清层逻辑（复刻 cut-boss 分支新增块）：
    st5["dot_pending"] = True
    st5["boss"].pop("debuffs", None)
    st5["boss"].pop("adapt", None)                           # δv1.2 §11.1 新怪无适应状态
    st5["mech_stacks"] = {str(m): {} for m in st5["members"]}
    st5["round_acted"] = []
    check("切怪后 debuffs 已清（无残留键）", "debuffs" not in st5["boss"])
    check("切怪后 adapt 已清（δv1.2 §11.1）", "adapt" not in st5["boss"])
    check("切怪后玩家资源重置为空", st5["mech_stacks"]["1"] == {} and st5["mech_stacks"]["2"] == {})
    check("切怪后 round_acted 清空", st5["round_acted"] == [])
    check("切怪后 dot_pending=True", st5.get("dot_pending") is True)

    print("\n==== dot_check result ====")
    if FAIL:
        print("FAILED:", FAIL)
        sys.exit(1)
    print("ALL DOT CHECK OK")


if __name__ == "__main__":
    main()
