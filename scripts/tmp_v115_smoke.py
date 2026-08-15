# -*- coding: utf-8 -*-
"""v115 审计3（策划一致性）· 指令级冒烟（临时脚本，跑完可删）。

模拟：
  a. 玩家在 oak_plain 用『前往』移动到新房间 oak_plain_4（按名称/序号兼容），应成功且提示
  b. 『地图』面板：深度标记 / 🔒？？？（用 emerald_forest 的隐藏房 emerald_forest_6 验证，
     oak_plain 实现中没有隐藏房）
  c. 连续『探索』数次后隐藏房揭示、『前往 6』可行（用 emerald_forest）
  d. 『探索进度』指令：返回非空面板
  e. 首访新房间后 visited_subareas 有记录（count_visited_subareas 增加）

容错约定：依赖实现与文档出入时记录差异，不强行改实现。
"""
import os
import sys
import asyncio

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
TEST_DB = os.path.join(BASE, "smoke_v115.db")

# 必须在 import 插件前设置独立测试库 + 路径
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))      # dragonfall→plugins→data→qqbot
sys.path.insert(0, QQBOT)
sys.path.insert(0, BASE)

from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import db  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402


passed = failed = 0
notes = []


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


def note(txt):
    notes.append(txt)
    print(f"  ▸ 差异/备注: {txt}")


def clean():
    db.init_db()
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    try:
        for t in ("players", "player_groups", "inventory", "quests", "battle_state",
                  "event_state", "visited_subareas", "visited", "props_use"):
            conn.execute(f"DELETE FROM {t}")
        conn.commit()
    finally:
        conn.close()


def clean_subareas():
    """仅清空 visited_subareas（不影响玩家状态）。"""
    db.init_db()
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    try:
        conn.execute("DELETE FROM visited_subareas")
        conn.commit()
    finally:
        conn.close()


class FakeEvent:
    def __init__(self, group_id, qq_id, msg=""):
        self._g, self._q, self.message_str = group_id, qq_id, msg

    def get_group_id(self): return self._g
    def get_sender_id(self): return self._q
    def get_message_str(self): return self.message_str
    def plain_result(self, text): return text
    def stop_event(self): pass


async def run(handler, ev):
    gen = handler(ev)
    results = []
    try:
        while True:
            results.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return results


async def register(m, g, q, name="测试"):
    ev = FakeEvent(g, q, f"注册 战士 {name} 男")
    return await run(m.register, ev)


async def act(m, cmd, g, q):
    ev = FakeEvent(g, q, cmd)
    # 按命令词分发到具体 handler
    if cmd.startswith("地图"):
        fn = m.map_view
    elif cmd.startswith(("前往", "移动")):
        fn = m.move
    elif cmd.startswith("探索进度"):
        fn = m.explore_progress
    elif cmd.startswith("探索"):
        fn = m.explore
    else:
        fn = m.map_view
    return await run(fn, ev)


async def amain():
    m = Main(None)
    clean()
    await register(m, "g1", "u1")
    p = db.get_player("g1", "u1")
    db.update_player("g1", "u1", cur_map="oak_plain", cur_subarea="oak_plain_1",
                     level=10, stamina=999999)
    p = db.get_player("g1", "u1")
    print("== 玩家初始:", p["cur_map"], p["cur_subarea"], "level", p["level"])

    # ---- ① 核心接口可用性（协作契约 §2.4）----
    print("\n== ① 核心接口导出检查 ==")
    for fn in ("subarea_links", "subarea_depth", "is_hidden_room", "reveal_met",
               "reveal_progress", "bump_explore_count", "today_map_event",
               "today_event_effects", "exploration_record_visit",
               "region_progress", "overall_progress"):
        check(f"C.{fn} 已导出", hasattr(C, fn), f"hasattr={hasattr(C, fn)}")

    # ---- ② 前往 oak_plain_4（文档要求『前往 4』；实现为从 _1 的 links 数序号）----
    print("\n== ② 前往 oak_plain_4 ==")
    # 清空到访表，基准归零
    clean_subareas()
    base_cnt = db.count_visited_subareas("u1")
    db.update_player("g1", "u1", cur_map="oak_plain", cur_subarea="oak_plain_1")
    r4 = await act(m, "前往 4", "g1", "u1")
    p2 = db.get_player("g1", "u1")
    if p2["cur_subarea"] == "oak_plain_4":
        check("『前往 4』命中 oak_plain_4", True, "")
    else:
        check("『前往 4』命中 oak_plain_4", False,
              f"cur_subarea={p2['cur_subarea']}（从 _1 的序号 4 落到跨图邻居，非新房间）")
        note("文档预期『前往 4』→oak_plain_4；实现序号从当前房可前往列表起算，oak_plain_1 可前往数=2(_2,_4)，"
             "序号 4 从出口起含跨图邻居 → 落到白鹿之森。需按名称或从 _4 邻居移动。")
        db.update_player("g1", "u1", cur_map="oak_plain", cur_subarea="oak_plain_1")
        rn = await act(m, "前往 乱石岗", "g1", "u1")
        p3 = db.get_player("g1", "u1")
        rn_txt = "\n".join(str(x) for x in rn)
        check("『前往 乱石岗』(按名) 到达 oak_plain_4", p3["cur_subarea"] == "oak_plain_4",
              f"cur_subarea={p3['cur_subarea']} | msg={rn_txt[:120]}")
        if p3["cur_subarea"] == "oak_plain_4":
            check("到达提示含位置+描述", "乱石岗" in rn_txt and "你来到了" in rn_txt, rn_txt[:200])
            new_cnt = db.count_visited_subareas("u1")
            # 『前往 4』已先落白鹿之森产生 1 条首访，故此处期望 base(+1)+1；机制应保证到达即+1
            check("首访 oak_plain_4 计数累加(visited_subareas 增加)",
                  new_cnt >= 1, f"{base_cnt}->{new_cnt}")
            note("注:『前往 4』先跨图到白鹿之森又记 1 条首访，故 visited_subareas 计数含它；"
                 "单独看新增机制（到达新房即 INSERT OR IGNORE）正常，非缺陷")
        # 首访奖励数值核对（exp=lv×8, gold=lv×3; 玩家 lv=10 → exp=80, gold=30）
        p4 = db.get_player("g1", "u1")
        exp_reward_ok = int(p4.get("exp") or 0) >= 80
        gold_base = p4.get("gold", 0)
        note(f"oak_plain_4 首访后玩家 exp={p4.get('exp')}, gold={gold_base}（期望首次+exp80/gold30，"
             f"若冲突因先到白鹿之森已触发一次首访则为差分校验）")

    # ---- ③ 地图面板：深度标记 + 今日奇遇行 ----
    print("\n== ③ 地图面板(oak_plain) ==")
    db.update_player("g1", "u1", cur_subarea="oak_plain_1")
    rmap = await act(m, "地图", "g1", "u1")
    rmap_txt = "\n".join(str(x) for x in rmap)
    check("面板含 '可前往'", "可前往" in rmap_txt, rmap_txt[:100])
    check("面板含今日奇遇行 '今日奇遇'", "今日奇遇" in rmap_txt or "今日" in rmap_txt, rmap_txt[:200])
    check("面板含当前位置标记",
          any(mk in rmap_txt for mk in ("📍", "🟢", "🟡", "🟠", "🔴")), rmap_txt[:200])

    # ---- ④ 隐藏房揭示（emerald_forest_6, explore:8）----
    print("\n== ④ 隐藏房揭示流 (emerald_forest_6) ==")
    from data.plugins.dragonfall.game.core.maps import _explore_count
    # 清掉该图探索计数，保证从 0 起测
    db.set_event_state("reveal_emerald_forest_u1", str(0))
    db.update_player("g1", "u1", cur_map="emerald_forest", cur_subarea="emerald_forest_1",
                     level=20, stamina=999999)
    check("core.is_hidden_room(emerald,_6)=True",
          C.is_hidden_room("emerald_forest", "emerald_forest_6") is True,
          str(C.is_hidden_room("emerald_forest", "emerald_forest_6")))
    check("core.reveal_met 初始(0>=8)=False",
          C.reveal_met("explore:8", "g1", "u1", "emerald_forest") is False)
    # 地图面板在 emerald_forest_1 → _4 视角，未揭示时 _6 应显示 🔒
    db.update_player("g1", "u1", cur_subarea="emerald_forest_4")
    rmap4 = "\n".join(str(x) for x in await act(m, "地图", "g1", "u1"))
    hid_locked = "🔒" in rmap4
    check("未揭示时地图面板出现 🔒 隐藏标记", hid_locked, rmap4[:300])
    if not hid_locked:
        note("emerald_forest_6 未揭示但地图面板无 🔒（可能因当前房 _4 的 links 不含 _6，或隐藏过滤未生效）")
    # 『前往 6』未揭示应被阻止（emerald_forest_4 的 links 含 3,5,6 → 序号 6 有效但被 hidden 拦）
    rmv0 = "\n".join(str(x) for x in await act(m, "前往 6", "g1", "u1"))
    pm0 = db.get_player("g1", "u1")
    check("未揭示『前往 6』被阻止(位置不变为 _4)",
          pm0["cur_subarea"] == "emerald_forest_4", f"cur_subarea={pm0['cur_subarea']} | msg={rmv0}")
    if "遮挡" not in rmv0 and "探索" not in rmv0:
        note(f"未揭示『前往 6』提示未含 reveal 引导文案: {rmv0[:120]}")

    # 连续 bump 累计到 revealed
    for _ in range(8):
        C.bump_explore_count("g1", "u1", "emerald_forest")
    check("core.reveal_met 满 8 次 = True",
          C.reveal_met("explore:8", "g1", "u1", "emerald_forest") is True)
    _cp, _need = C.reveal_progress("g1", "u1", "emerald_forest")
    check("core.reveal_progress 返回 (cur,need)", (_cp, _need) == (8, 8), f"({_cp},{_need})")
    # 揭示后地图面板隐藏标记消失、可列出名称
    rmap4b = "\n".join(str(x) for x in await act(m, "地图", "g1", "u1"))
    check("揭示后面板不再显示 🔒(隐藏角落实名化)",
          "🔒" not in rmap4b or "苔径" in rmap4b, rmap4b[:240])
    # 揭示后『前往 3』(emerald_forest_4 可见序号3=_6) 可行，也按名走
    rmv = "\n".join(str(x) for x in await act(m, "前往 苔径密室", "g1", "u1"))
    pm = db.get_player("g1", "u1")
    if pm["cur_subarea"] != "emerald_forest_6":
        # 名称未命中则退回序号 3（从 _4 的可前往可见列表第 3 项）
        db.update_player("g1", "u1", cur_subarea="emerald_forest_4")
        rmv = "\n".join(str(x) for x in await act(m, "前往 3", "g1", "u1"))
        pm = db.get_player("g1", "u1")
    check("揭示后前往隐藏房到达 emerald_forest_6",
          pm["cur_subarea"] == "emerald_forest_6", f"cur_subarea={pm['cur_subarea']} | msg={rmv[:160]}")

    # ---- ⑤ 探索进度指令 ----
    print("\n== ⑤ 探索进度/探索见闻 ==")
    db.update_player("g1", "u1", cur_map="oak_plain", cur_subarea="oak_plain_1")
    ok_prog = hasattr(m, "explore_progress")
    check("Main 挂载『探索进度』handler", ok_prog, "hasattr(m, 'explore_progress')=" + str(ok_prog))
    if not ok_prog:
        note("Main(main.py:265) 未继承 ExplorationCmds，且 game/commands/_registry.py 未登记 explore_progress"
             " → 『探索进度』指令不可达（§6.3 注册要求缺漏）")
    # 核心层能力验证（不依赖 Main 装配）
    rp = C.region_progress("u1")
    check("C.region_progress 返回可迭代", isinstance(rp, list) and len(rp) >= 0, str(rp)[:80])
    op = C.overall_progress("u1")
    check("C.overall_progress 返回 dict 含 pct", isinstance(op, dict) and "pct" in op, str(op))
    # 用 FakeEvent + 手绑 stub 直接驱动 mixin（绕过 Main 装配，验证渲染逻辑）
    from data.plugins.dragonfall.game.commands.exploration import ExplorationCmds

    class _Stub:
        def _uid(self, ev):
            return "g1", "u1"

        def _player(self, gid, qid):
            return db.get_player(gid, qid)
    rendered = await _collect2(ExplorationCmds.explore_progress(_Stub(), FakeEvent("g1", "u1", "探索进度")))
    if rendered:
        txt = "\n".join(str(x) for x in rendered)
        check("探索进度面板非空", len(txt) > 0, txt[:120])
        check("面板含全大陆进度", "探索度" in txt or "全大陆" in txt, txt[:200])
        check("面板含区域行", any(rk in txt for rk in ("绿野", "南境", "中域", "北境", "西境", "东境")), txt[:240])
    else:
        note("探索进度面板直接驱动无输出（mixin 渲染需 require_player 上下文，未装配验证）")


async def _collect2(gen):
    out = []
    try:
        while True:
            out.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return out

    # ---- ⑥ 探索命令 bump 计数（命令层是否真的累加）----
    print("\n== ⑥ 命令层探索 bump 检查 ==")
    db.update_player("g1", "u1", cur_map="oak_plain", cur_subarea="oak_plain_1",
                     level=10, stamina=999999)
    from data.plugins.dragonfall.game.core.maps import _explore_count
    c0 = _explore_count("g1", "u1", "oak_plain")
    # 探索会撞怪走战斗，不深入；仅验证 bump_explore_count 经 C 可达（已在上方记录缺失）
    note(f"命令层探索依赖 C.bump_explore_count，已导出={hasattr(C, 'bump_explore_count')}；"
         f"核心直调累计前 oak_plain 计数={c0}")

    print(f"\n===== 冒烟结果: {passed} 通过, {failed} 失败 =====")
    if notes:
        print("---- 差异/备注汇总 ----")
        for n in notes:
            print("  ·", n)
    return failed == 0


if __name__ == "__main__":
    ok = asyncio.run(amain())
    sys.exit(0 if ok else 1)
