# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年AstrBot 插件主入口 —— 薄装配层（重构后）

命令处理器已按领域拆至 game/commands/（Mixin 模式）：
  PlayerCmds / WorldCmds / CombatCmds / EconomyCmds / SocialCmds / MiscCmds
本文件只保留：插件生命周期 + 后台任务 + Mixin 装配。

★ R3（2026-09-15）：AstrBot 指令注册**改为宿主驱动**
----------------------------------------------------
指令注册不再依赖 `game/commands/**` 的 `@declared` 装饰器（那份是待删树），
而由宿主 `host/registration.py` 从**包内声明表**（引擎 `Package.command_declarations()`）
逐条注册（`register_commands()`，在 `AstrMain.__init__` 装配）。见 out/W-R3.md：
删掉 `game/commands/**` 后 import 仍通过、但注册 194 → 0 的静默哑掉态由本批关闭。

★ 终态（2026-09-19 · 审计尾巴 #8）：过渡态遗留**已删净** —— 旧壳树 `game/commands/**`
（P5C）、Mixin 汇编类 `Main`、`_LEGACY_SHELLS` 双路开关、`_fix_handler_module_paths()`
路径改写 hack、`_legacy_store_init()` 建表口一律不再存在。本文件只剩：插件生命周期
+ 后台任务 + 引擎 host 通道装配（薄装配层）。
"""
import glob
import importlib
import threading
import logging

from astrbot.api import star  # 仅 AstrMain 壳需要（生产命中真实 astrbot；测试命中 tests/shim_astrbot）

# 库/建表一律走**宿主工厂** `host/store_factory`（存档半边按名取）：宿主里不再有任何
# `from .game import ...` 取件（P5F 前置⑤ 的终态口径）。


def _weekly_reward_selfcheck(pkg=None, *, strict=True):
    """★ 启动自检（fail-closed）：周常达标发奖的宿主注入面必须在位。

    背景（RPT 实测的静默失效）：`game/services/weekly_progress.py` 这个注入点消失后，
    包内 `content/flow/weekly_progress.py::_grant_rewards` 取不到宿主 `reward.grant_reward`，
    而 `weekly_bump_kill` 的旧宽容兜底会把它吞掉 ⇒ **玩家达标不发奖、进度不落库、零日志**。
    按「fail-closed 优先」口径：启动时就大声报错，绝不静默。

    * 通过 → INFO 一行留痕（可见地证明链路在位）；
    * 失败 → ERROR + **抛**（拒绝带着静默坏掉的发奖链路启动）。

    幂等（热重载 / 多次实例化都安全）。

    ★ P5F 前置⑤（去壳）：原实现写死**包内模块路径字面量**导入周常进度半边 —— 终态判据②
    「宿主零包知识」因此在 `main.py` 里恒差 1 处。改为按**半边名**经引擎包契约取：
    `Package.optional_submodule("flow")` 拿到包内 flow 半边对象，再用它自己的 `__name__`
    前缀导入 `weekly_progress` —— 宿主里**不出现任何包内模块路径字面量**
    （与 `host/shell.py::_sub` / `host/tlog_setup.attach_tlog` 同口径）。

    `pkg` 缺省 = 宿主存档口上绑定的包（`host/store_factory.store().package`）；
    `strict=False`（过渡态 import 期）取不到包只留 ERROR 痕迹**不抛** —— 真正的装配期门在
    `register_commands()`（`strict=True`），那时引擎通道已 boot、包必然在位。
    """
    _LOGGER = logging.getLogger(__name__)
    if pkg is None:
        from .host import store_factory as _sf      # 惰性：模块 import 期本行之前尚未绑定
        pkg = _sf.store().package
    _WP = None
    if pkg is not None:
        try:
            _flow = pkg.optional_submodule("flow")
            if _flow is not None:
                _WP = importlib.import_module(_flow.__name__ + ".weekly_progress")
        except Exception:
            _LOGGER.error("周常发奖启动自检失败：包内周常进度半边不可导入", exc_info=True)
            raise
    if _WP is None:
        if strict:
            _LOGGER.error(
                "周常发奖启动自检失败：包未绑定 / 周常进度半边取不到 —— 缺注入时玩家达标会"
                "静默不发奖，故拒绝启动（fail-closed）。请检查宿主装配处的 bind_store(pkg)。")
            raise RuntimeError(
                "周常发奖启动自检失败：包内周常进度半边取不到（拒绝静默不发奖）")
        _LOGGER.error(
            "周常发奖启动自检本次跳过：包尚未装配（过渡态 import 期）——"
            "装配期 register_commands() 会重跑同一次自检（fail-closed），此处只留痕不抛。")
        return
    try:
        _LOGGER.info(_WP.selfcheck())
    except Exception as exc:
        _LOGGER.error(
            "周常发奖启动自检失败：%s —— 缺注入时玩家达标会静默不发奖，故拒绝启动（fail-closed）。"
            "请在宿主装配处把 db / grant_reward 注入包内周常进度半边。", exc)
        raise


# ---- v92 文件转发体验通道 ----
# 后台线程监控 scripts/playthrough_cmd.txt：读到命令 → 进程内构造 fake 事件
# → _run_shortcut 转发给真实 handler → 结果追加写 scripts/playthrough_out.txt。
# 身份固定 gm_playtest（私聊），GM 指令自然放行；完全在 AstrBot 进程内，无跨进程锁。
import os
import time as _time

_PLAYTEST_QQ = "gm_playtest"  # 体验专用身份（QQ 不存在的测试号）
_PLAY_OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "playthrough_out.txt")
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep + "scripts"


def _loopback_files():
    """所有待处理命令文件（含多身份 playthrough_cmd_<ident>.txt），按名排序保证主通道优先。"""
    return sorted(glob.glob(os.path.join(_SCRIPTS_DIR, "playthrough_cmd*.txt")))


def _out_file_for(cmd_path: str) -> str:
    """命令文件对应的输出文件：playthrough_cmd.txt → playthrough_out.txt；带身份 → playthrough_out_<ident>.txt。"""
    name = os.path.basename(cmd_path)
    if name == "playthrough_cmd.txt":
        return _PLAY_OUT_FILE
    ident = name[len("playthrough_cmd_"):-len(".txt")]
    return os.path.join(_SCRIPTS_DIR, f"playthrough_out_{ident}.txt")


class _LoopbackEvent:
    """模拟 AstrBot 消息事件（私聊，测试身份）。"""

    def __init__(self, msg: str, sender_id: str = None, group_id: str = None):
        self.message_str = msg
        self._sender = sender_id or _PLAYTEST_QQ
        # v95.1：多号联测支持——带身份通道进统一测试群，可组队/开副本；主通道保持 private（GM 权限）
        self._group_id = group_id or "private"
        self._stopped = False            # P5A：平台 gate（`_maint_gate`）的 stop_event 语义

    def get_group_id(self):
        return self._group_id

    def get_sender_id(self):
        return self._sender

    def get_self_id(self):
        # v101.28s：合并转发节点 uin 用（bot 自身 QQ = NapCat 3473145972，
        # 前端显示为"格温"发送的聊天记录）
        return "3473145972"

    def get_message_str(self):
        return self.message_str

    def plain_result(self, text):
        return text

    def stop_event(self):
        """v96 停服 gate / 翻页快捷键用：标记「本事件不再向下传播」。"""
        self._stopped = True

    async def send(self, message):
        return message


def _file_loopback_start():
    """启动文件转发监控线程（幂等，装配期只起一次）。"""
    if getattr(_file_loopback_start, "_started", False):
        return
    _file_loopback_start._started = True

    def worker():
        # v94.1 修复：AstrBot 热重载（watchfiles）会重新执行本模块 → 防多 worker 竞态。
        # 锁文件记录 PID；已有存活 worker 则本线程直接退出（旧 worker 处理逻辑相同）。
        lock_path = os.path.join(_SCRIPTS_DIR, ".loopback_worker.lock")
        try:
            if os.path.exists(lock_path):
                with open(lock_path, "r", encoding="utf-8") as f:
                    old_pid = int(f.read().strip() or "0")
                if old_pid > 0:
                    try:
                        os.kill(old_pid, 0)  # 存活检查
                        return  # 已有 worker 在跑，本线程退出
                    except OSError:
                        pass  # 旧进程已死，抢占
            with open(lock_path, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            # q11：锁失败不阻塞（极端情况容忍多 worker），留痕便于排查
            logging.getLogger(__name__).warning(
                "loopback worker 锁文件读写失败（容忍多 worker 继续）", exc_info=True
            )
        while True:
            try:
                for cmd_path in _loopback_files():
                    if os.path.exists(cmd_path):
                        with open(cmd_path, "r", encoding="utf-8") as f:
                            cmd = f.read().strip()
                        try:
                            os.remove(cmd_path)
                        except OSError:
                            pass
                        if cmd:
                            _dispatch(cmd, _out_file_for(cmd_path))
            except Exception:
                # q11：单轮轮询失败不中断线程，留痕便于定位
                logging.getLogger(__name__).warning(
                    "loopback worker 单轮轮询失败（已跳过，1s 后重试）", exc_info=True
                )
            _time.sleep(1.0)

    def _dispatch(cmd: str, out_file: str):
        """P5A：本通道 = **引擎 host 通道**（`adapter_qq` 三函数 + inject）。

        v55 轮口径保留：main 通道也进统一测试群 gm_test_group（#47b 需要 2 真人组队打副本，
        main 在 private 群无法与 gm_test_group 的小蓝组队 —— party/副本按 group_id 隔离）；
        GM 权限不受影响（gm_ 前缀身份恒放行）。

        与改造前的差异（**有意**，见 out/W-P5A.md）：
          · 执行面从「宿主注册表 `Main._run_shortcut`」改成「引擎通道 `EngineChannel.collect_event`」
            （包内声明路由 → 守卫 → `Env` → 包内处理器 → 逐段回话）；
          · 于是也不再需要「提交主事件循环」那一步（引擎通道自带 async 桥，见
            `host/adapter_qq.py::run_sync`）；平台发送在引擎通道的 loop 上完成。
        """
        lines = [f"\n{'='*50}\n▶ 『{cmd}』"]
        try:
            channel = engine_channel()
            ev = _LoopbackEvent(cmd, _ident_of(out_file), "gm_test_group")
            lines.extend(str(seg) for seg in channel.collect_event(ev))
        except Exception as e:
            lines.append(f"❌ 异常: {type(e).__name__}: {e}")
            logging.getLogger(__name__).error(
                "引擎 host 通道转发失败（命令=%r）", cmd, exc_info=True)
        _append_out("\n".join(lines), out_file)

    def _ident_of(out_file: str) -> str:
        """输出文件反推身份：主通道 → gm_playtest；带身份 → 文件名中的 ident。"""
        name = os.path.basename(out_file)
        if name == "playthrough_out.txt":
            return _PLAYTEST_QQ
        return name[len("playthrough_out_"):-len(".txt")]

    def _append_out(text: str, out_file: str = None):
        with open(out_file or _PLAY_OUT_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    t = threading.Thread(target=worker, daemon=True, name="file-loopback")
    t.start()


def _event_state_cleanup_once():
    """v104 M24 P2-5：启动时清理流失玩家残留的 event_state 键（>30 天未活跃）。
    幂等（多实例/热重载只跑一次）；仅清五类后缀键，talkflags_ 等持久键不动。"""
    if getattr(_event_state_cleanup_once, "_started", False):
        return
    _event_state_cleanup_once._started = True
    # ★ P5F 前置⑤（去壳）：原实现写死**包内模块路径字面量**导入两只清理函数
    #   （存档半边 world 的 `cleanup_stale_event_state` / 内容域 worlds 的
    #   `cleanup_stale_instances`，各写成一条待删壳路径上的 `from … import …`）——
    #   终态判据②「宿主零包知识」因此在 `main.py` 里恒差 2 处，且删壳后两条 import
    #   必然 ModuleNotFoundError 被外围 `except Exception` 吞掉 ⇒ 启动清理**静默哑掉**
    #   （只剩一行 warning，清理实际不执行）。改为按**半边名**经引擎包契约取：
    #   `store_factory.store().package`（装配处 `bind_store(pkg)` 已绑）→
    #   `Package.optional_submodule("persistence"/"worlds")`，宿主里**不出现任何包内
    #   模块路径字面量**（与 `_weekly_reward_selfcheck` / `host/shell.py::_sub` 同口径）。
    try:
        from .host import store_factory as _sf      # 惰性：模块 import 期本行之前尚未绑定
        _pkg = _sf.store().package
        if _pkg is None:
            raise RuntimeError(
                "引擎包未绑定（装配处应先 bind_store(pkg) / boot()）")
        n = _pkg.optional_submodule("persistence").cleanup_stale_event_state()
        if n:
            logging.getLogger(__name__).info("已清理 %d 个流失玩家残留 event_state 键", n)
        # v141 大陆回收（P0-3，2026-08-30 审计）：启动兜底清理超龄大陆实例
        # （内存 dict + DB event_state 孤儿键，24h 默认；幂等）
        try:
            _nw = _pkg.optional_submodule("worlds").cleanup_stale_instances()
            if _nw:
                logging.getLogger(__name__).info("已清理 %d 个超龄大陆实例", _nw)
        except Exception:
            logging.getLogger(__name__).warning(
                "大陆实例清理跳过（异常不影响启动）", exc_info=True
            )
    except Exception:
        logging.getLogger(__name__).warning(
            "event_state 残留键清理跳过（DB 未就绪或异常，不影响启动）", exc_info=True
        )


# ============================================================================
# 引擎 host 通道（P5A）
# ----------------------------------------------------------------------------
# 契约真源：`framework/docs/engine-wiki/reference/host-api.md`
#   （三函数 / ctx 七字段 / 六钩子 / `Env` 字段表 / 命令通道 / `inject` 一个 dict 两处用）
# 形状真源：`overnight/B19a_HOST_CONTRACT_DESIGN.md` §2.1（宿主终态文件清单）
#
# ★ 终态：P5C 删壳后，**生产分发就是本通道**（`AstrMain.__init__` → `register_commands()`
# → `host/registration.py` 按包内声明表注册 handler）。`game/commands/**` 旧路径已不存在；
# 文件回环调试通道同样走本通道（`engine_channel().collect_event`）。
#
# 宿主面五件（`host/**`）：adapter_qq（三函数 + 钩子）· _platform · _identity ·
# store_factory（库路径 + 连接 + 单进程锁 + 存档半边取用口）· log_setup / tlog_setup。
# ============================================================================

import json as _json  # noqa: E402
import os as _os_sp  # noqa: E402
import sys as _sys_sp  # noqa: E402

# —— 引擎框架包接线（S8 物理分离）：引擎在独立仓、本仓以 submodule 接入 `framework/`，
# 包名 `saintess_engine`。**生产路径（AstrBot 真实进程）没有 conftest 铺路**，故在此接线一次
# （与 `tests/conftest.py:37` 同款）；缺这一步的实测后果：`Failed to import plugin dragonfall:
# No module named 'saintess_engine'`（2026-09-15 重启冒烟抓到，测试侧因 conftest 铺路而全绿）。
_ENGINE_ROOT = _os_sp.path.join(_os_sp.path.dirname(_os_sp.path.abspath(__file__)), "framework")
if _os_sp.path.isdir(_os_sp.path.join(_ENGINE_ROOT, "saintess_engine")) and _ENGINE_ROOT not in _sys_sp.path:
    _sys_sp.path.insert(0, _ENGINE_ROOT)

from saintess_engine.host import Host as _EngineHostBase  # noqa: E402

from .host import adapter_qq as _adapter_qq  # noqa: E402
from .host import store_factory as _store_factory  # noqa: E402
from .host import _platform  # noqa: E402
from .host import registration as _registration  # noqa: E402
from .host.shell import HostShell as _HostShell  # noqa: E402

#: 包目录配置项（环境变量优先；插件配置文件同名键次之）
_PACKAGE_CFG_ENV = "GWEN_PACKAGE_DIR"
_PACKAGE_CFG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def resolve_package_dir(package_dir: str = None):
    """包目录（`game.json` 所在）—— **只从配置来**；代码里不写死任何包名。

    配置来源（按序）：
      ① 显式入参（测试 / 对拍脚本）；
      ② 环境变量 `GWEN_PACKAGE_DIR`；
      ③ 插件配置 `<插件根>/config.json` 的 `package_dir`（相对路径按插件根解析）。

    都没有 → 记 ERROR 并返回 `None`（引擎通道**不启动**：fail-closed —— 换包 = 换配置 + 重启进程，
    宿主的可替换性要求「包路径」不许在代码里猜）。
    """
    raw = str(package_dir or os.environ.get(_PACKAGE_CFG_ENV) or "").strip()
    if not raw:
        try:
            with open(_PACKAGE_CFG_FILE, encoding="utf-8") as fh:
                raw = str((_json.load(fh) or {}).get("package_dir") or "").strip()
        except OSError:
            raw = ""
        except ValueError:
            logging.getLogger(__name__).error(
                "插件配置不是合法 JSON：%s（包目录取不到 → 引擎通道不启动）", _PACKAGE_CFG_FILE)
            raw = ""
    if not raw:
        logging.getLogger(__name__).error(
            "未配置包目录（环境变量 %s 或 %s 的 package_dir）——引擎 host 通道不启动。"
            "换包 = 换配置 + 重启进程（一个进程一个包）。", _PACKAGE_CFG_ENV, _PACKAGE_CFG_FILE)
        return None
    if not os.path.isabs(raw):
        raw = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), raw))
    return raw


class EngineHost(_EngineHostBase):
    """引擎 host 的宿主子类 —— 只加三处宿主侧必需面（**引擎一行未改**）。

    ① `env.state["shell"]`：包内取宿主面的**唯一过渡能力口**（包内 `content/guards.py` 与
       `cmds_*.py` 都经它取 `_strip_cmd` / `_player` / `_tip` / `_is_gm` / `_broadcast` …）。
       本类只负责把调用方给的宿主壳透传进 `Env.state`（与旧桥 `game/commands/_host_bridge.py`
       的 `state={"shell": host_shell}` 同形同值 ⇒ 包内行为逐字不变）。
    ② async 处理器：包内战斗族处理器是 `async def`（返回 `list[str]`），引擎 `_as_replies`
       不 await ⇒ 会把协程对象当回话投出去。本类在 `_as_replies` 里 await / 收 async 流
       （编辑器试玩通道 `editor/play_worker.py` 已有同款先例）。
    ③ 新玩家**不代造档**：引擎缺省会给一份「最小档」；本包策略是「先注册」（包内没有
       `initial_save`）—— 代造档会让包侧 `player` 守卫失效、还会凭空落一行玩家档。
       故：包**没有**声明 `initial_save` ⇒ 空档（由包内 `player` 守卫按**包内文案**拦截）。
    """

    def __init__(self, *args, shell=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.shell = shell

    # ---- ① 宿主壳能力口 ----
    def build_env(self, key, spec, ctx, player, *, raw=None):
        env = super().build_env(key, spec, ctx, player, raw=raw)
        if self.shell is not None:
            env.state["shell"] = self.shell
        return env

    # ---- ② async 处理器 ----
    @staticmethod
    def _as_replies(out) -> list:
        """处理器返回值 → 文本段（`str` / list / 生成器 / `None` 都收）。

        与引擎原实现的**唯一差异**：**空串段保留**。包内排版空行是 `raw("")`（`content/commands.py`
        `render_panel` → 空串段），旧路径 `_BRIDGE.run` 的 `"\\n".join` 会把它变成空行；引擎原实现
        在 `_as_replies` 里把空串滤掉，等价于**吃掉空行** ⇒ 两条通道的成品文本不再逐字节相同。
        这里只滤 `None`（保真）；空串是否投递由投递侧决定（见 `handle`：收集面保真、平台面不空发）。
        """
        if hasattr(out, "__await__") or hasattr(out, "__anext__"):
            out = _adapter_qq.run_sync(out)
        if out is None:
            return []
        if isinstance(out, str):
            return [out]
        if isinstance(out, (list, tuple, set)):
            return [str(x) for x in out if x is not None]
        if hasattr(out, "__iter__") and not isinstance(out, (dict, bytes)):
            return [str(x) for x in out if x is not None]
        return [str(out)]

    # ---- ③ 新玩家建档策略 + 逐段投递 ----
    def accept(self, ctx: dict, spec=None) -> None:
        """一条消息：读档（含「不代造档」策略）→ 指定声明或引擎路由 → **逐段投递**。

        与引擎原实现的两处差异（理由见本类文档串）：
          · 新玩家不代造档（包没声明 `initial_save` ⇒ 空档，由包侧 `player` 守卫拦截）；
          · 投递走 `adapter.say`（**不经** `Host.say` 的 `if text:` 过滤）：空串段是包内排版空行，
            收集面必须保真（对拍/回放），平台面由适配器 `say` 自己决定不空发。

        `spec` 显式给出时按该声明执行（适配器对**不可见声明**的路由落点，见
        `host/adapter_qq.py::route_plan`）；缺省 = 引擎可见路由。
        """
        ctx = ctx or {}
        uid = str(ctx.get("uid") or "")
        to = {"uid": uid, "group_id": ctx.get("group_id")}
        text = str(ctx.get("text") or "").strip()
        player = self.load_player(uid)
        if player is None:
            if self.stack is not None and self.stack.entry_fn("initial_save") is not None:
                player = self.stack.initial_save(uid, ctx, id_key=self.id_key) or {}
                if not isinstance(player, dict):
                    player = {}
                if player:                       # 建档是引擎级副作用（新档必须落库一次）
                    self.save_player(uid, player)
            else:
                player = {}                      # 包要求先注册 → 空档（`player` 守卫拦截）
        if spec is not None:
            replies = self.invoke(spec, ctx, player)
        else:
            replies = self.route(ctx, player, text)
        for part in replies:
            self.adapter.say(to, part)

    def handle(self, ctx: dict) -> None:
        """引擎契约的 `handle`（= `accept` 的缺省形态：走引擎可见路由）。"""
        self.accept(ctx)


class EngineShell(_HostShell):
    """引擎通道的**宿主壳** —— 终态宿主壳 `host/shell.py::HostShell`（P5C 交付）的宿主子类。

    ★ R3：本类**从不继承** Mixin 汇编类 `Main`（旧壳树 `game/commands/**` 已于 P5C 删净）
    ——`import main` / 建通道 / 注册 / 跑命令全走本类 + 引擎通道。宿主壳的通用那一半（分页 /
    剥参 / 认人 / 读档 / 广播 / 平台 gate / 平台例外 4 条）在 `host/shell.py`，内容那一半转引包内真源。

    旧壳 `shortcut_trigger` / `page_flip` / `gm_play` 正文里调 `self._run_shortcut(event, text)`
    的那一步（把消息转给另一条指令执行）现接到 `EngineChannel.collect_event`（`ctx` 由同一平台
    事件重建，`text` = 重建后的指令文本）⇒「5 条平台例外」也走在引擎通道上（§11.3 / P5A 作业书 §2③）。
    """

    _engine_channel = None

    def bind_engine_channel(self, channel) -> None:
        self._engine_channel = channel

    async def _run_shortcut(self, event, text: str):
        """转发另一条指令执行 —— **改走引擎通道**（P5A §2③），并保留框架转发的换文语义。

        与 `saintess_engine.command.router.run_shortcut` 同款：转发期间**临时把事件的
        `message_str` 换成重建后的指令文本**，结束后还原（否则包内处理器经 `env.raw`
        取到的还是原消息，参数解析会错 —— 实测：`n3` → 转发『前往 3』时拿到 `n3`）。
        """
        channel = self._engine_channel
        if channel is None:
            raise RuntimeError(
                "引擎通道未装配：EngineShell._run_shortcut 需要 bind_engine_channel() ——拒绝静默走旧路径")
        had = hasattr(event, "message_str")
        orig = getattr(event, "message_str", None)
        try:
            if had:
                event.message_str = text
            for seg in channel.collect_event(event, text=text):
                yield seg
        finally:
            if had:
                event.message_str = orig


class EngineChannel:
    """引擎通道装配 + 驱动口（宿主唯一「跑一条消息」入口）。

        channel = EngineChannel(package_dir)      # package_dir **由配置给**
        channel.boot()                            # 加载包（bind/inject）→ 建表 → 绑存档半边
        channel.collect_event(event)              # 平台事件 → 引擎通道 → 回话段（list[str]）

    `collect_event` / `collect_ctx` 的顺序 = 平台门 → 平台例外命令 → 引擎路由：

        ① 平台 gate（`_maint_gate`）：命停服 → 本次不路由、零回话；
        ② 平台例外（`gm_play` / `gm_spy` / `shortcut_trigger` / `page_flip`）：交给适配器派发
           （包内没有也不应有处理器；转发经 `EngineShell._run_shortcut` 回到本通道）；
        ③ 其余：`Host.handle(ctx)`（引擎按**包内声明**路由 → 守卫 → `Env` → 包内处理器）。
    """

    def __init__(self, package_dir: str, *, context=None, shell=None, sink=None, seed=None,
                 inject=None):
        self.package_dir = package_dir
        self.store = _store_factory.store()
        self.shell = shell if shell is not None else EngineShell()
        self.shell.bind_engine_channel(self)
        self.adapter = _adapter_qq.QQAdapter(
            store=self.store, shell=self.shell, context=context, sink=sink, seed=seed)
        self.host = EngineHost(self.adapter, package_dir, shell=self.shell,
                               inject=inject if inject is not None else _store_factory.inject_handles(),
                               id_key="uid")
        self.stack = None

    def boot(self):
        """加载包（→ 包侧 `bind_host(**inject)`，import 命令模块**之前**）+ 建表 + 绑存档口。

        ★ R3：另加两处**声明驱动**接线（都是宿主件、零包知识，值全部来自包内声明表）：
          · `_GameCmdFilter` 的「游戏指令正则」供体（停服 gate 的命中判定）；
          · `HostShell._static_source`（命令转发的静态兜底表）。
        """
        self.stack = self.host.boot()
        _store_factory.bind_store(self.stack)          # 存档半边（`content/persistence`）
        self.store.init()                            # 建表 / 迁移（幂等）
        self.adapter.attach(pkg=self.stack, host=self.host)
        self.shell.bind_package(self.stack)            # 宿主壳取包内半边的落点
        _platform._GameCmdFilter.set_pattern_source(
            lambda: _registration.declaration_patterns(self.stack))
        _HostShell._static_source = lambda: _registration.static_handlers(self.stack)
        _HostShell._STATIC_HANDLERS = None           # 换包 / 重载 → 旧缓存作废
        return self.stack

    def dispatch_declaration(self, key: str, event, text: str = None) -> list:
        """**按声明 key** 跑一条指令 → 回话段（`list[str]`）—— 注册驱动 handler 的执行体。

        与 `collect_ctx` 的区别：**不重新路由**，直接执行这条声明（旧壳 `_BRIDGE.run(self, key, …)`
        同义）。AstrBot 已按正则把消息分发到本 key 的 handler，重路由会引入第二套命中口径。
        三段：① 平台 gate（`_maint_gate`）→ 零回话；② 平台例外四条 → 宿主壳实现；
        ③ 其余 → `Host.accept(ctx, spec)`（守卫 → `Env` → 包内处理器）。
        """
        ctx = self.adapter.to_ctx(event, text=text)
        self.adapter.begin(ctx)
        if key == _adapter_qq.GATE_KEY:
            self.adapter.gate(ctx)
            return []
        out: list = []
        with self.adapter.collecting(out):
            if key in _adapter_qq.PLATFORM_ROUTES:
                out.extend(self.adapter.platform_replies(key, ctx))
            else:
                spec = self.host.commands.get(key)
                if spec is None:
                    raise KeyError(
                        "包内声明表没有 key=%r ——注册驱动的 pattern 与声明表不同源？" % (key,))
                self.host.accept(ctx, spec)
        return out

    def collect_ctx(self, ctx: dict) -> list:
        """一条消息 → 回话段（`list[str]`，元素顺序 = 投递顺序）。

        三段式（§11.3）：① 平台 gate（`_maint_gate`，停服拦截时零回话）→
        ② 适配器那半路由（平台例外四条 / 不可见声明）→ ③ 引擎可见路由。
        """
        self.adapter.begin(ctx)
        out: list = []
        with self.adapter.collecting(out):
            if self.adapter.gate(ctx):
                return []                            # 停服拦截：不路由、零回话
            plan = self.adapter.route_plan(ctx.get("text") or "")
            if plan is not None and plan[0] == "platform":
                out.extend(self.adapter.platform_replies(plan[1].key, ctx))
            elif plan is not None and plan[0] == "invoke":
                self.host.accept(ctx, plan[1])       # 不可见声明 → 包内处理器
            else:
                self.host.accept(ctx)                # 引擎可见路由
        return out

    def collect_event(self, event, text: str = None) -> list:
        """平台事件 → 回话段（`text` 显式给出 = 快捷/翻页重建的指令文本）。"""
        return self.collect_ctx(self.adapter.to_ctx(event, text=text))


#: 进程唯一引擎通道（loopback 测试通道用；对拍脚本可自行 `EngineChannel(...)` 另建）
_ENGINE_CHANNEL = {"channel": None}


def engine_channel(package_dir: str = None, **kwargs) -> EngineChannel:
    """取（或建）进程唯一引擎通道。配置缺包目录 → **抛**（调用方决定怎么报，绝不静默）。"""
    channel = _ENGINE_CHANNEL["channel"]
    if channel is None:
        resolved = resolve_package_dir(package_dir)
        if not resolved:
            raise RuntimeError(
                "引擎 host 通道未配置包目录（%s / %s.package_dir）——拒绝猜包名"
                % (_PACKAGE_CFG_ENV, _PACKAGE_CFG_FILE))
        channel = EngineChannel(resolved, **kwargs)
        channel.boot()
        _ENGINE_CHANNEL["channel"] = channel
    return channel


def register_commands(package_dir: str = None, *, module_path: str = None) -> int:
    """★ R3：**AstrBot 指令注册**入口（声明驱动）——返回注册条数。

    流程（fail-closed，任一步失败都抛，绝不静默留一个「注册 0 条」的哑机器人）：

        ① 起（或取）引擎通道（包目录**由配置给**）→ 加载包 → 声明表就位；
        ② `reset_plugin_handlers`：接管本插件名下旧 handler（过渡态 `game/commands/**`
           的 `@declared` 装饰器仍在 import 期注册 —— 不清掉就会两套并存、每条消息跑两遍）；
        ③ `register_from_declarations`：包内声明 × 1 → AstrBot 正则 handler × 1；
        ④ 自检：注册条数 == 包内声明条数（不等 → 抛）。

    `module_path` 缺省 = 本模块（AstrBot `star_map` 按它精确关联插件实例）。
    """
    channel = engine_channel(package_dir)
    # 终态：注入面自检挪到装配期（同一 fail-closed 语义）。★ P5F 前置⑤：包句柄**显式传入**
    # （不再靠包内模块路径字面量取件）；此处 strict=True = 真门。
    _weekly_reward_selfcheck(channel.stack)
    # 启动清理（v104 M24 P2-5「启动时清理流失玩家残留 event_state 键」）的**唯一执行点**：
    #   过渡态 `Main.__init__` 里那次已随壳删除，装配期这里就是终态位。
    #   函数自身幂等（模块级哨兵）、失败只留痕不阻塞启动（见其 docstring）。
    _event_state_cleanup_once()
    # 文件回环调试通道的**唯一启动点**（走引擎 host 通道 `engine_channel().collect_event`，
    #   不依赖任何宿主实例）。幂等；worker 自带 pid 锁文件（热重载防多 worker）、daemon 线程、
    #   无命令文件时零动作。
    _file_loopback_start()
    target = str(module_path or __name__)
    _registration.bind_dispatcher(channel.dispatch_declaration)
    cleared = _registration.reset_plugin_handlers(target)
    count = _registration.register_from_declarations(channel.stack, module_path=target)
    expected = _registration.declaration_count(channel.stack)
    logging.getLogger(__name__).info(
        "AstrBot 指令注册（声明驱动）：清旧 %d 条 → 注册 %d 条 / 声明 %d 条（module_path=%s）",
        cleared, count, expected, target)
    if count != expected:
        raise RuntimeError(
            "注册条数 %d != 包内声明条数 %d ——注册驱动有漏（拒绝带着哑掉的指令表启动）"
            % (count, expected))
    return count


def registration_teeth_probe(module_path: str = None) -> tuple:
    """**门禁牙齿**用探针：清掉本插件 handler → 旁路注册驱动 → 数一遍。

    返回 `(cleared, registered, remaining)`：`registered` == 0 而 `remaining` == 0
    ⇒ 「旁路驱动必须报红」成立（`tests/test_command_registration.py` 用它做有牙实测）。
    """
    target = str(module_path or __name__)
    cleared = _registration.reset_plugin_handlers(target)
    return cleared, 0, count_plugin_handlers(target)


def count_plugin_handlers(module_path: str = None) -> int:
    """本插件在 AstrBot 注册表里的指令 handler 条数（门禁量尺）。"""
    target = str(module_path or __name__)
    try:
        from astrbot.core.star.star_handler import star_handlers_registry as _reg
    except Exception:                                            # noqa: BLE001
        return -1
    return sum(1 for md in getattr(_reg, "_handlers", ())
               if str(getattr(md, "handler_module_path", "") or "") == target)


# ================= astrbot 插件壳（v117.5 解耦后薄层） =================
# ★ R3 起：指令注册由宿主 `host/registration.py` 驱动（`AstrMain.__init__` → `register_commands()`），
# 不再依赖 `game/commands/_platform` 的装饰器双注册。
# 本壳仍做两件事：① 提供 class X(star.Star) 让 astrbot 发现插件（main.py 是固定入口）；
# ② context 翻译——核心回复数据类（MessageChain/Plain/Node/Nodes）→ astrbot 类型。
# 平台类型真源 = 宿主 `host/_platform.py`（P5C 交付），**不再 import 待删树**。
from .host import _platform as _pf  # noqa: E402


def _to_astrbot_node(node):
    """核心 Node → astrbot Node（OneBot 合并转发节点）。"""
    from astrbot.core.message.components import Node as ANode
    from astrbot.core.message.components import Nodes as ANodes
    from astrbot.core.message.components import Plain as APlain

    content = []
    for comp in node.content:
        if isinstance(comp, _pf.Plain):
            content.append(APlain(comp.text))
        elif isinstance(comp, _pf.Node):
            content.append(_to_astrbot_node(comp))
        elif isinstance(comp, _pf.Nodes):
            content.append(ANodes([_to_astrbot_node(n) for n in comp.nodes]))
        else:
            content.append(comp)
    return ANode(uin=node.uin, name=node.name, content=content)


def _to_astrbot_chain(chain):
    """核心 MessageChain → astrbot MessageChain。"""
    from astrbot.core.message.components import Nodes as ANodes
    from astrbot.core.message.components import Plain as APlain
    from astrbot.core.message.message_event_result import MessageChain as AChain

    out = []
    for comp in chain.chain:
        if isinstance(comp, _pf.Plain):
            out.append(APlain(comp.text))
        elif isinstance(comp, _pf.Node):
            out.append(_to_astrbot_node(comp))
        elif isinstance(comp, _pf.Nodes):
            out.append(ANodes([_to_astrbot_node(n) for n in comp.nodes]))
        else:
            out.append(comp)
    return AChain(out)


class _ContextProxy:
    """把核心 MessageChain 翻译成 astrbot MessageChain 后转发（其余属性透传）。"""

    def __init__(self, real):
        self._real = real

    def send_message(self, target, chain):
        return self._real.send_message(target, _to_astrbot_chain(chain))

    def __getattr__(self, name):
        return getattr(self._real, name)


class AstrMain(star.Star, EngineShell):
    """astrbot 插件壳：继承**终态宿主壳** `EngineShell`（`host/shell.py::HostShell` 子类）。

    ★ R3：本类**不再继承**已删的 Mixin 汇编类 `Main`——AstrBot 装载插件时实例化本类，
    实例化期间调 `register_commands()` 完成「包内声明 → AstrBot handler」注册（star_manager
    的 handler 绑定发生在实例化**之后**，故注册时机正确），并注入 context 翻译代理。

    注册失败**当场抛**（fail-closed）：宁可不启动，也不带着 0 条注册的哑指令表上线。
    """

    def __init__(self, context=None, **kwargs):
        proxy = _ContextProxy(context) if context is not None else None
        EngineShell.__init__(self, context=proxy)
        register_commands(module_path=__name__)


def is_game_command(msg: str) -> bool:
    """v134.1 私聊延迟修复：判断消息是否为本插件能处理的游戏指令。

    供 AstrBot RateLimitStage（only_llm 模式）调用：命中任一注册指令
    pattern → 该消息走规则匹配秒回，跳过限流；未命中 → 走 LLM 才限流。

    ★ R3：判定口径从待删的 `game/commands/_registry.COMMAND_REGEX` 改口到**宿主注册驱动**
    （`host/registration.py::is_game_command`，正则池 = 包内声明表，注册时刷新）——删壳后
    这条判定照常有效（否则 only_llm 模式下游戏指令会被限流 stall）。
    """
    return _registration.is_game_command(msg)
