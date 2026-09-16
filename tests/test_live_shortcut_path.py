#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W-L9 冒烟：**线上链路**端到端 —— 『快捷绑定 → 触发』必须真的发得出去（非空回话）。

为什么要走这条链路、而不是模块级直调
------------------------------------
本测试驱动的是 **AstrBot 装载插件时的真实对象**：

    main.AstrMain(context=None)                     ← AstrBot 实例化的插件主类（EngineShell）
      → host/registration.py::register_from_declarations()  ← 包内声明 → AstrBot handler
      → AstrBot 管道口径跑 handler（activated_handlers，priority 降序、clear_result 语义）
      → EngineChannel.dispatch_declaration(key, event)
      → QQAdapter.platform_replies → EngineShell.shortcut_trigger（壳只转发）
      → 包内 content/player_cmds.py::shortcut_trigger → EngineShell._run_shortcut（二次派发）
      → QQAdapter.route_plan → Host.accept → 包内 handler → 回话段

**判据 = AstrBot 会不会发出去**（这是本 bug 的盲区，也是本测试的牙）：

* `pipeline/context_utils.py::call_handler` —— handler 的 yield **只有**
  `MessageEventResult` / `CommandResult` 才 `event.set_result(ret)`；裸 `str` 只 `yield ret`，
  **不设 result**；
* `pipeline/process_stage/stage.py` —— StarRequestSubStage 的 yield 值在 `else: yield` 处被丢弃；
* `pipeline/respond/stage.py::process` —— `event.get_result() is None` → 直接 `return`（不发）。

⇒ 「handler 产出了文本段」≠「玩家收得到」。
  2026-09-15 线上真 bug：注册驱动的 **async 族** handler（71/195 条声明，含快捷/翻页/gm_play）
  yield 的是**裸字符串** ⇒ 全部静默丢包（玩家零回话、日志里连异常都没有，
  只剩 npc_quick_dialog 那条 `Prepare to send - …: ` 空消息）。本文件把这条判据钉成常驻牙。

判据（全部当次实测，数字不写死）
--------------------------------
① 线上链路可达：`AstrMain` 装配后 195 条声明 → 195 条 handler（module_path == main）；
② 有角色档：`注册 <名> <性别>` 经线上链路回非空（存档半边落库，读回有角色）；
③ 绑定：`快捷绑定 0 探索` 回非空 + DB `shortcuts == {"0": "探索"}`；
④ **触发非空**：发 `0` 必须产出**非空可见回话**（改前 = 静默空回，本测试的靶心）；
   字母键 `n → 角色` 同理（回话须含角色名，证明「二次派发确实执行了被绑指令」）；
⑤ 逐段投递：每次触发期间 handler **不得 yield 裸值**（= async 族回归牙）；
⑥ 反证：`快捷清除` 后再发 `0` / `n` → **零可见回话**（且 DB 绑定已空）——证明 ④ 不空过。

跑法：`python tests/test_live_shortcut_path.py`（exit=0 = 全绿）。
"""
import asyncio
import functools
import json
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(_HERE)


def _find_qqbot_dir():
    """AstrBot 根（含 `data/plugins/<plugin>`）—— 真布局 = 插件根上三级。

    沙箱副本的形状（插件根是 junction 的**目标** `work/host`，而不是
    `<qqbot>/data/plugins/dragonfall`）上三级会落到工作区根 ⇒ 再在兄弟目录里找
    `<x>/data/plugins/<本插件名>`（本工作区 = `work/qqbot`）。两条路都走不通 → 返回上三级
    （import 失败会当场报红，不静默跳过）。
    """
    cand = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
    if os.path.isdir(os.path.join(cand, "data", "plugins")):
        return cand
    parent = os.path.dirname(PLUGIN_DIR)
    try:
        names = sorted(os.listdir(parent))
    except OSError:
        return cand
    real_me = os.path.realpath(PLUGIN_DIR)
    for name in names:
        plugins = os.path.join(parent, name, "data", "plugins")
        if not os.path.isdir(plugins):
            continue
        try:
            entries = sorted(os.listdir(plugins))
        except OSError:
            continue
        for entry in entries:                    # 插件目录名（本仓 = dragonfall）≠ 副本目录名
            if os.path.realpath(os.path.join(plugins, entry)) == real_me:
                return os.path.join(parent, name)
    return cand


QQBOT_DIR = _find_qqbot_dir()

TEST_DB = os.path.join(_HERE, "test_live_shortcut_path.db")
GID, QID = "live_smoke_group", "live_smoke_player"
CHAR = "链路冒烟"


def _find_package_dir():
    """包目录：环境变量优先；否则在 `framework/games/*` 里挑**声明表最大**的那个（不写包名）。"""
    env = str(os.environ.get("GWEN_PACKAGE_DIR") or "").strip()
    if env and os.path.isdir(env):
        return env
    games = os.path.join(PLUGIN_DIR, "framework", "games")
    best, best_n = None, -1
    if os.path.isdir(games):
        for name in sorted(os.listdir(games)):
            decl = os.path.join(games, name, "content", "data", "commands.json")
            if not os.path.isfile(decl):
                continue
            try:
                with open(decl, encoding="utf-8") as fh:
                    n = len(json.load(fh) or {})
            except (OSError, ValueError):
                continue
            if n > best_n:
                best, best_n = os.path.join(games, name), n
    return best


PKG_DIR = _find_package_dir()

# ★ QQBOT_DIR 必须排在 sys.path **最前**：插件根（沙箱副本 = `work/host`）自己带一个
#   `data/` 目录，若它排在前面，`import data.plugins.dragonfall` 会命中 `work/host/data`
#   ⇒ `No module named 'data.plugins'`（真布局下 `<qqbot>/data/plugins/<plugin>` 无此问题）。
for _p in (_HERE, os.path.join(PLUGIN_DIR, "framework"), PLUGIN_DIR, QQBOT_DIR):
    if _p and _p in sys.path:
        sys.path.remove(_p)
    if _p:
        sys.path.insert(0, _p)
if os.environ.get("GWEN_NO_SHIMMED_ASTRBOT") != "1":
    _SHIM = os.path.join(_HERE, "shim_astrbot")
    if os.path.isdir(_SHIM) and _SHIM not in sys.path:
        sys.path.insert(0, _SHIM)

os.environ["GWEN_PACKAGE_DIR"] = PKG_DIR
os.environ.setdefault("GWEN_TEST_MODE", "1")
# 自带私有库（远离共享 test_game_data.db；每次跑先删 → 可复现）。
# 只认**显式覆盖** `GWEN_LIVE_SHORTCUT_DB`：不吞外层 `GWEN_GAME_DB`（防误指生产库后被删）。
_DB = os.environ.get("GWEN_LIVE_SHORTCUT_DB") or TEST_DB
os.environ["GWEN_GAME_DB"] = _DB

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


# ============================================================
# AstrBot 管道替身（**只**保留「会不会发出去」这一条判据）
# ============================================================
class _Result(object):
    """`MessageEventResult` 的最小替身：真 AstrBot 里 `event.plain_result(t)` 就是它。"""

    def __init__(self, text):
        self.text = str(text)

    def plain_text(self):
        return self.text


class _Event(object):
    """平台事件（形状照 AstrBot：message_str / stop_event / set_result / clear_result）。"""

    def __init__(self, msg, gid=GID, qid=QID):
        self.message_str = msg
        self._g, self._q, self._stopped = gid, qid, False
        self._result = None

    def get_group_id(self):
        return self._g

    def get_sender_id(self):
        return self._q

    def get_self_id(self):
        return "3473145972"

    def get_message_str(self):
        return self.message_str

    def plain_result(self, text):
        return _Result(text)

    def stop_event(self):
        self._stopped = True

    def set_result(self, r):
        self._result = r

    def get_result(self):
        return self._result

    def clear_result(self):
        self._result = None


def _drive_handler(md, instance, event):
    """照 AstrBot `call_handler` 跑一个注册 handler。

    返回 `(sent, raw, exc)`：`sent` = 每个 MessageEventResult yield（respond 会发，
    空串 = 线上那条 `The message is empty` 日志）；`raw` = 裸值 yield（**玩家看不到**）。
    """
    fn = md.handler
    if isinstance(fn, functools.partial):
        gen = fn(event)
    else:
        try:
            gen = fn(instance, event)
        except TypeError:
            gen = fn(event)
    sent, raw, exc = [], [], None
    loop = asyncio.new_event_loop()
    try:
        if hasattr(gen, "__anext__"):
            async def _run():
                async for item in gen:
                    if isinstance(item, _Result):
                        event.set_result(item)
                        sent.append(item.plain_text())
                    else:
                        raw.append(item)
            loop.run_until_complete(_run())
        elif hasattr(gen, "__await__"):
            ret = loop.run_until_complete(gen)
            if isinstance(ret, _Result):
                event.set_result(ret)
                sent.append(ret.plain_text())
            elif ret is not None:
                raw.append(ret)
    except BaseException as e:                                   # noqa: BLE001
        exc = e
    finally:
        loop.close()
    return sent, raw, exc


def run_live(instance, REG, M, text, gid=GID, qid=QID):
    """一条消息的**线上路径**：AstrBot activated_handlers（priority 降序）逐个跑。

    口径 = `waking_check`（filter 命中）+ `star_request`（逐个跑、不 stop 则 clear_result）+
    `respond`（只看 MessageEventResult）。返回 `(visible, trace)`。
    """
    ev = _Event(text, gid, qid)
    acts = []
    for md in REG._handlers:
        if md.handler_module_path != M.__name__ or not md.enabled or not md.event_filters:
            continue
        try:
            if all(bool(f.filter(ev, None)) for f in md.event_filters):
                acts.append(md)
        except Exception:                                        # noqa: BLE001
            continue
    visible, trace = [], []
    for md in acts:
        if ev._stopped:
            break
        sent, raw, exc = _drive_handler(md, instance, ev)
        visible.extend(t for t in sent if t and t.strip())
        trace.append((md.handler_name, list(sent), len(raw), exc))
        if ev._stopped:
            break
        ev.clear_result()
        ev.message_str = text                # 转发型 handler 会改 message_str → 还原（事件级语义）
    return visible, trace


def main():
    print("== W-L9 冒烟：线上链路『快捷绑定 → 触发』（有角色档 + 反证）==")
    if os.path.exists(_DB):
        try:
            os.remove(_DB)
        except OSError:
            pass

    try:
        from astrbot.core.star.star_handler import star_handlers_registry as REG
        from data.plugins.dragonfall import main as M
    except Exception:
        print(traceback.format_exc())
        check("import data.plugins.dragonfall.main", False)
        return 1
    check("import data.plugins.dragonfall.main", True,
          "legacy_shells=%s" % getattr(M, "_LEGACY_SHELLS", "?"))

    # ---- ① 线上装配：AstrMain（AstrBot 实例化的插件类）+ 注册驱动 ----
    try:
        inst = M.AstrMain(context=None)
    except Exception as exc:                                     # noqa: BLE001
        print(traceback.format_exc())
        check("AstrMain 装配（含注册驱动）", False, repr(exc))
        return 1
    check("AstrMain 装配（含注册驱动）", True)

    channel = M.engine_channel()
    pkg = channel.pkg
    declared = M._registration.declaration_count(pkg)
    mine = [md for md in REG._handlers if md.handler_module_path == M.__name__]
    check("线上装配：注册条数 == 包内声明条数（%d）" % declared, len(mine) == declared,
          "实际 %d" % len(mine))
    check("执行面 = 引擎通道（EngineShell 已 bind_engine_channel）",
          channel.shell is not None and channel.shell._engine_channel is channel,
          "shell=%r" % (type(getattr(channel, "shell", None)).__name__,))

    all_raw = []
    all_visible = []

    def live(text, label):
        visible, trace = run_live(inst, REG, M, text)
        all_visible.extend(visible)
        for hname, sent, raw_n, exc in trace:
            all_raw.append((text, hname, raw_n))
            if exc is not None:
                print("      ⚠️ %s 异常：%r" % (hname, exc))
        print("    [%s] %r → 可见回话 %d 段 · handler 轨迹 %s"
              % (label, text, len(visible),
                 [(h, len(s), r) for h, s, r, _e in trace]))
        for seg in visible:
            print("        | %s" % seg.split("\n")[0][:90])
        return visible

    # ---- ② 有角色档（存档半边真落库）----
    vis = live("注册 %s 男" % CHAR, "① 建档")
    check("有角色档：『注册』线上回非空", bool(vis))
    player = channel.store.load_player(GID, QID) or {}
    check("有角色档：存档半边读回有角色（name=%r）" % (player.get("name"),),
          str(player.get("name") or "") == CHAR and bool(player.get("cls") or player.get("class_name")),
          "player keys=%d" % len(player))

    # ---- ③ 绑定（数字键 + 字母键）----
    vis = live("快捷绑定 0 探索", "② 绑定数字键")
    check("绑定：『快捷绑定 0 探索』线上回非空", bool(vis))
    vis = live("快捷绑定 n 角色", "② 绑定字母键")
    check("绑定：『快捷绑定 n 角色』线上回非空", bool(vis))
    shortcuts = (channel.store.load_player(GID, QID) or {}).get("shortcuts") or {}
    check("绑定：DB shortcuts == {'0': '探索', 'n': '角色'}",
          shortcuts == {"0": "探索", "n": "角色"}, "实际 %r" % (shortcuts,))

    # ---- ④ 触发：**必须发得出去**（本测试靶心）----
    trig_digit = live("0", "③ 触发『0』(0→探索)")
    check("★ 触发『0』：线上产出**非空可见回话**", bool(trig_digit),
          "改前症状 = 静默空回（handler 产出了文本段，但 yield 裸串 ⇒ AstrBot 丢弃）")

    trig_letter = live("n", "③ 触发『n』(n→角色)")
    check("★ 触发『n』：线上产出非空可见回话且含角色名", bool(trig_letter) and
          any(CHAR in t for t in trig_letter),
          "visible=%r" % ([t[:40] for t in trig_letter],))

    # ---- ⑤ 逐段投递牙：任何被激活的 handler 都不得 yield 裸值 ----
    raw_hits = [(t, h, n) for t, h, n in all_raw if n]
    check("逐段投递：所有 handler 均 yield MessageEventResult（裸值 0 个）", not raw_hits,
          "裸值落点=%r（async 族 handler 不包 plain_result 时就是这一条报红）" % (raw_hits,))

    # ---- ⑤b 交付面牙：回话必须是**文案**，不是平台结果对象的 repr ----
    #   改前（包内 `_event(env) → env.raw`）交付面 = `str(MessageEventResult)` 的 dataclass repr
    #   （实测 `MessageEventResult(chain=[Plain(...)])`）—— 非空但玩家看不懂，属"假绿"。
    leak = [t for t in all_visible
            if "object at 0x" in t or "MessageEventResult(" in t or "MessageChain(" in t]
    check("交付面：回话是文案（无平台对象 repr 泄漏）", not leak, "泄漏段=%r" % (leak[:3],))
    check("交付面：触发『0』的回话是成句文案（>=6 字）",
          bool(trig_digit) and len(trig_digit[0].strip()) >= 6,
          "实际 %r" % (trig_digit[:1],))

    # ---- ⑥ 反证：清掉绑定后必须**零可见回话** ----
    vis = live("快捷清除", "④ 清除绑定")
    check("反证前置：『快捷清除』线上回非空", bool(vis))
    check("反证前置：DB shortcuts 已清空",
          not ((channel.store.load_player(GID, QID) or {}).get("shortcuts") or {}),
          "实际 %r" % ((channel.store.load_player(GID, QID) or {}).get("shortcuts"),))
    rev_digit = live("0", "④ 反证 触发『0』")
    rev_letter = live("n", "④ 反证 触发『n』")
    check("★ 反证：无绑定时发『0』→ 零可见回话", not rev_digit, "实际 %r" % (rev_digit,))
    check("★ 反证：无绑定时发『n』→ 零可见回话", not rev_letter, "实际 %r" % (rev_letter,))

    # ---- ⑦ 对照：sync 族（走另一条分支）本来就能发出去 → 证明判据不是"全都发不出去" ----
    vis = live("位置", "⑤ 对照 sync 族")
    check("对照：sync 族『位置』线上回非空（判据非恒假）", bool(vis))

    print("-" * 60)
    print("通过 %d · 失败 %d" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
