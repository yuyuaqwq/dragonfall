#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R3 门禁：**本插件 AstrBot 指令 handler 条数 == 包内声明条数**。

为什么要有这条门禁（P5C 报的结构性卡点 A）
------------------------------------------
删掉宿主 `game/commands/**` 之后 `import ...main` 照样通过，但 AstrBot 注册表里本插件的
指令 handler **195 → 0** —— 玩家所有消息掉进 LLM 兜底，机器人**静默哑掉**。
既有五道门禁 + 三哨兵**没有一条**量「注册条数」，所以这种坏态一路绿灯。
本文件把「注册条数」变成可执行的判据。

判据（全部当次实测，数字不写死）
--------------------------------
① `main.AstrMain(...)` 装配后，本插件在 AstrBot 注册表里的指令 handler 条数
   **== `pkg.command_declarations()` 条数**（删壳前 = 195）；
② 每条声明恰好一个 handler（按名对齐），且都带至少一条正则 filter；
③ **单注册者**：本插件名下不存在「非本模块路径」的残留 handler（旧壳装饰器注册的那批
   已被注册驱动 `reset_plugin_handlers` 接管清掉）；
④ 真能跑：`注册` / `属性` / `攻击` / `副本` 四条命令经**注册出来的 handler**跑出非空回话；
⑤ **有牙**：把注册驱动临时旁路 → 注册条数必须掉到 0（报红）→ 还原后复绿；
⑥ 幂等：再装配一次（热重载同款）条数不变。

跑法：`python tests/test_command_registration.py`（exit=0 = 全绿）。
"""
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
# ★ T8（单源化）：qqbot 部署根 / shim 目录 = **宿主布局适配层**（`tests/_host_layout.py`）。
#   旧写法死算 `dirname³(PLUGIN_DIR)` 只在部署布局成立（本工作副本的 qqbot 名面在兄弟目录
#   `<ws>/_run_home`）⇒ `import data.plugins.<pkg>` 当场失败；shim 旧写法只认
#   `host/tests/shim_astrbot`，T8 后宿主侧不再自留该副本（回落到包仓那份）。
from _host_layout import QQBOT_DIR, SHIM_DIR as _SHIM_DIR  # noqa: E402


def _find_package_dir():
    """包目录：环境变量优先；否则在 `framework/games/*` 里挑**声明表最大**的那个。

    （不在测试里写死包名：换包 = 换配置/换这棵树，判据「注册 == 声明」与包无关。）
    """
    import json
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


PKG_DIR = os.environ.get("GWEN_PACKAGE_DIR") or _find_package_dir()
TEST_DB = os.path.join(_HERE, "test_command_registration.db")

for _p in (QQBOT_DIR, PLUGIN_DIR, os.path.join(PLUGIN_DIR, "framework"), _HERE):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)
if os.environ.get("GWEN_NO_SHIMMED_ASTRBOT") != "1":
    _SHIM = _SHIM_DIR
    if _SHIM and os.path.isdir(_SHIM) and _SHIM not in sys.path:
        sys.path.insert(0, _SHIM)

os.environ["GWEN_PACKAGE_DIR"] = PKG_DIR
os.environ.setdefault("GWEN_TEST_MODE", "1")
# 本门禁自带私有库（远离共享 test_game_data.db；每次跑先清 → 可复现）
os.environ["GWEN_GAME_DB"] = os.environ.get("GWEN_REG_TEST_DB") or TEST_DB

passed = failed = skipped = 0


from _check import bind_check  # noqa: E402  P0-1 断言助手单源：tests/_check.py

check = bind_check(globals(), "passed", "failed")


# ---------------------------------------------------------------- 分发（AstrBot 口径）
import asyncio  # noqa: E402
import functools  # noqa: E402


def _run_handler(md, instance, event):
    """跑一个注册 handler（async generator / coroutine 都收）→ yield 值列表。

    形状照 AstrBot：注册表里的 handler 是**未绑定**函数，真 AstrBot 用
    `functools.partial(raw, star_cls)` 绑定；这里同款手工绑。
    """
    fn = md.handler
    if isinstance(fn, functools.partial):
        gen = fn(event)
    else:
        try:
            gen = fn(instance, event)
        except TypeError:
            gen = fn(event)
    out, loop = [], asyncio.new_event_loop()
    try:
        if hasattr(gen, "__anext__"):
            async def _drive():
                async for item in gen:
                    out.append(item)
            loop.run_until_complete(_drive())
        elif hasattr(gen, "__await__"):
            out.append(loop.run_until_complete(gen))
        else:
            out.append(gen)
    finally:
        loop.close()
    return [x for x in out if x is not None]


def _text_of(value):
    if isinstance(value, str):
        return value
    chain = getattr(value, "chain", None)
    if chain is not None:
        return "".join(str(getattr(c, "text", "")) for c in chain)
    return str(value)


def main():
    global skipped
    print("== R3 门禁：AstrBot 指令注册条数 == 包内声明条数 ==")
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass

    from astrbot.core.star.star_handler import star_handlers_registry as REG

    try:
        from data.plugins.dragonfall import main as M
        from data.plugins.dragonfall import host as _host_pkg  # noqa: F401  （宿主面可导入）
    except Exception:
        print(traceback.format_exc())
        check("import data.plugins.dragonfall.main", False)
        return 1
    check("import data.plugins.dragonfall.main", True,
          "legacy_shells=%s" % getattr(M, "_LEGACY_SHELLS", "?"))

    # ---- ① 装配（= AstrBot 装载插件时实例化主类）----
    try:
        inst = M.AstrMain(context=None)
    except Exception as exc:                                     # noqa: BLE001
        print(traceback.format_exc())
        check("AstrMain 装配（含注册驱动）", False, repr(exc))
        return 1
    check("AstrMain 装配（含注册驱动）", True)

    pkg = M.engine_channel().pkg
    declared = M._registration.declaration_count(pkg)
    count = M.count_plugin_handlers()
    print("  包内声明 %d 条 · 插件 handler %d 条" % (declared, count))

    # ---- ② 条数：注册 == 声明 ----
    check("注册条数 == 包内声明条数（%d）" % declared, count == declared,
          "实际 %d" % count)

    mine = [md for md in REG._handlers if md.handler_module_path == M.__name__]
    check("注册表里本模块 handler 数一致", len(mine) == declared,
          "registry=%d" % len(mine))

    # ---- ③ 每条声明一个 handler + 都有正则 filter ----
    by_name = {}
    for md in mine:
        by_name.setdefault(md.handler_name, []).append(md)
    keys = list(pkg.command_declarations())
    missing = [k for k in keys if k not in by_name]
    extra = [k for k in by_name if k not in keys]
    dup = [k for k, v in by_name.items() if len(v) != 1]
    check("声明 → handler 一一对应", not missing and not extra and not dup,
          "缺=%s 多=%s 重复=%s" % (missing[:6], extra[:6], dup[:6]))
    no_filter = [k for k, v in by_name.items()
                 if not any(getattr(f, "regex", None) is not None for f in v[0].event_filters)]
    check("每条 handler 都带正则 filter", not no_filter, "无 filter：%s" % no_filter[:6])

    # ---- ④ 单注册者：本插件名下没有旧模块路径残留 ----
    prefix = M.__name__.rsplit(".", 1)[0] + "."
    strays = [md for md in REG._handlers
              if str(getattr(md, "handler_module_path", "") or "").startswith(prefix)
              and md.handler_module_path != M.__name__]
    check("旧壳注册已被接管清掉（无残留 handler）", not strays,
          "残留 %d 条：%s" % (len(strays), sorted({md.handler_module_path for md in strays})[:4]))

    # ---- ⑤ 真跑：普通 / 战斗 / 副本 / 建档 ----
    class _Ev(object):
        def __init__(self, msg, gid="r3_gate", qid="gm_r3"):
            self.message_str = msg
            self._g, self._q, self._stopped = gid, qid, False

        def get_group_id(self):
            return self._g

        def get_sender_id(self):
            return self._q

        def get_self_id(self):
            return "3473145972"

        def get_message_str(self):
            return self.message_str

        def plain_result(self, text):
            return str(text)

        def stop_event(self):
            self._stopped = True

    for text, label in (("注册 门禁 男", "建档(register)"), ("属性", "普通(attributes)"),
                        ("攻击", "战斗(attack)"), ("副本", "副本(instance_cmd)")):
        ev = _Ev(text)
        target = by_name.get({
            "注册 门禁 男": "register", "属性": "attributes",
            "攻击": "attack", "副本": "instance_cmd"}[text])
        if not target:
            check("真跑 %s" % label, False, "没有该 key 的 handler")
            continue
        md = target[0]
        try:
            acted = all(bool(f.filter(ev, None)) for f in md.event_filters)
            segs = [_text_of(x) for x in _run_handler(md, inst, ev)]
            body = "\n".join(s for s in segs if s)
            check("真跑 %s（filter 命中 + 有回话）" % label,
                  acted and bool(body.strip()), "acted=%s segs=%d" % (acted, len(segs)))
        except Exception:                                        # noqa: BLE001
            print(traceback.format_exc())
            check("真跑 %s" % label, False, "异常")

    # ---- ⑥ 有牙：旁路注册驱动 → 必须掉到 0 ----
    orig = M._registration.register_from_declarations
    teeth_ok = False
    try:
        M._registration.register_from_declarations = lambda *a, **k: 0
        try:
            M.register_commands()
            raised = False
        except RuntimeError:
            raised = True
        zero = M.count_plugin_handlers() == 0
        teeth_ok = raised and zero
        print("  旁路驱动：注册条数=%d · 自检抛错=%s" % (M.count_plugin_handlers(), raised))
    finally:
        M._registration.register_from_declarations = orig
    check("有牙（旁路驱动 → 报红）", teeth_ok)

    # ---- ⑦ 还原 + 幂等 ----
    n2 = M.register_commands()
    check("还原复绿（再注册 == 声明数）", n2 == declared, "实际 %d" % n2)
    n3 = M.register_commands()
    check("幂等（连续装配条数不变）", n3 == declared and M.count_plugin_handlers() == declared,
          "n3=%d count=%d" % (n3, M.count_plugin_handlers()))

    # ---- ⑧ is_game_command 口径（RateLimit 面）----
    check("is_game_command('属性') / 闲聊 判对",
          M.is_game_command("属性") and not M.is_game_command("今天天气不错"),
          "attr=%s chat=%s" % (M.is_game_command("属性"), M.is_game_command("今天天气不错")))

    print("-" * 56)
    print("通过 %d · 失败 %d · 跳过 %d" % (passed, failed, skipped))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
