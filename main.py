# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年AstrBot 插件主入口 —— 薄装配层（重构后）

命令处理器已按领域拆至 game/commands/（Mixin 模式）：
  PlayerCmds / WorldCmds / CombatCmds / EconomyCmds / SocialCmds / MiscCmds
本文件只保留：插件生命周期 + 后台任务 + Mixin 装配。
"""
import glob
import threading
import logging

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.message_event_result import MessageChain

from .game import db
from .game.commands import (
    PlayerCmds, WorldCmds, CombatCmds, EconomyCmds, SocialCmds, MiscCmds,
    InstanceCmds, GmCmds, ExplorationCmds,  # v115 探索进度指令
)


def _fix_handler_module_paths():
    """修复 Mixin 重构后 handler 模块路径问题（必须保留的 hack，勿删）。

    AstrBot 通过 handler.handler_module_path 在 star_map 中精确查找插件实例
    （star_manager: star_map[path]=metadata，path=插件主模块；分发时
    star_map.get(handler.handler_module_path) 精确匹配），而 Mixin 拆分后
    handler 注册为 game.commands.* 子模块路径（注册时取 handler.__module__），
    与 Main 类所在的 main 模块不匹配，导致全部指令 handler 被过滤、
    消息全部落入 LLM 回复。

    官方机制仅有 LLM tools 的子模块重映射（star_manager 加载插件时对
    llm_tools 执行 ft.handler_module_path = metadata.module_path），对指令
    handler 无子模块→主模块映射，故本 hack 无法移除；若未来 AstrBot
    改为前缀匹配/官方支持子模块映射，可删除本函数（届时下方
    matched==0 告警会提示）。

    这里在插件加载完成后，把本插件所有 handler 的模块路径统一改写到
    main 模块（__name__），保证 star_map 能正确关联到 Main 实例。
    失败绝不静默：输出 ERROR 日志（后果=全部指令落入 LLM），并附带
    注册表同步校验（P3）差集日志。
    """
    _LOGGER = logging.getLogger(__name__)
    try:
        from astrbot.core.star.star_handler import star_handlers_registry

        pkg = __name__.rsplit(".", 1)[0]  # data.plugins.dragonfall
        matched = 0
        for h in star_handlers_registry._handlers:
            if h.handler_module_path and h.handler_module_path.startswith(pkg + "."):
                h.handler_module_path = __name__
                matched += 1
        if matched == 0:
            # 注册机制若变化导致 0 命中，必须大声告警而非静默失效
            _LOGGER.warning(
                "handler 模块路径改写命中 0 个 handler：Mixin 子模块 handler 将无法"
                "关联 Main 实例，指令会全部落入 LLM 回复。请检查 AstrBot 版本兼容性；"
                "若官方已支持子模块映射，可删除本 hack。"
            )
        else:
            _LOGGER.info("已改写 %d 个 handler 模块路径 -> %s", matched, __name__)

        # ---- P3 注册表同步校验：已注册公开 handler 名 vs _registry 静态表键 ----
        from .game.commands._registry import COMMAND_REGEX

        # 私有 handler（_ 前缀，如 _maint_gate）按 base.py v96 设计不进静态表，
        # 两侧统一排除，只校验公开指令名
        table_keys = {k for k in COMMAND_REGEX if not k.startswith("_")}
        registered = {
            h.handler_name
            for h in star_handlers_registry._handlers
            if h.handler_module_path == __name__ and not h.handler_name.startswith("_")
        }
        missing = sorted(table_keys - registered)  # 表有、实际未注册
        extra = sorted(registered - table_keys)    # 实际注册、表里没有
        if not missing and not extra:
            _LOGGER.info(
                "注册表同步校验通过：%d 静态键 ↔ %d 已注册公开 handler",
                len(table_keys), len(registered),
            )
        else:
            _LOGGER.warning(
                "注册表同步校验发现漂移：表缺 %d 键 %s；表多 %d 键 %s。"
                "请同步 game/commands/_registry.py（半自动维护，见该文件头注释）。",
                len(missing), missing, len(extra), extra,
            )
    except Exception:
        _LOGGER.error(
            "handler 模块路径改写/注册表校验失败——指令将全部落入 LLM 回复，"
            "请立即检查 AstrBot 版本兼容性", exc_info=True
        )

_fix_handler_module_paths()


# ---- v92 文件转发体验通道 ----
# 后台线程监控 scripts/playthrough_cmd.txt：读到命令 → 进程内构造 fake 事件
# → _run_shortcut 转发给真实 handler → 结果追加写 scripts/playthrough_out.txt。
# 身份固定 gm_playtest（私聊），GM 指令自然放行；完全在 AstrBot 进程内，无跨进程锁。
import asyncio
import os
import threading
import time as _time

_PLAYTEST_QQ = "gm_playtest"  # 体验专用身份（QQ 不存在的测试号）
_PLAY_CMD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "playthrough_cmd.txt")
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


def _file_loopback_start():
    """启动文件转发监控线程（幂等，AstrBot 与测试脚本共用同一 Main 时只起一次）。"""
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
        # v94.1 修复：插件热重载窗口期 Main._loopback_instance 尚未设置 → 短重试
        for _attempt in range(3):
            try:
                from .main import Main  # 延迟拿类，避免循环 import
                inst = Main._loopback_instance if hasattr(Main, "_loopback_instance") else None
                if inst is None:
                    _time.sleep(1.5)
                    continue
                # v55 轮（playtest）：main 通道也进统一测试群 gm_test_group——#47b 需要 2 真人组队打副本，
                # main 在 private 群无法与 gm_test_group 的小蓝组队（party/副本按 group_id 隔离）。
                # GM 权限不受影响：gm_ 前缀身份恒放行（gm.py _gm_auth），与群上下文无关。
                ev = _LoopbackEvent(cmd, _ident_of(out_file), "gm_test_group")
                # v101.28q：必须在主事件循环执行 handler——worker 线程 asyncio.run 的新 loop 里
                # await Quart websocket（bot API 发送）会跨 loop 挂死。提交主 loop 等结果。
                loop = getattr(inst, "_main_loop", None)
                if loop is None or loop.is_closed():
                    _append_out("❌ 未找到主事件循环（插件未初始化或重载中）", out_file)
                    return
                fut = asyncio.run_coroutine_threadsafe(_collect(inst, ev, cmd, out_file), loop)
                fut.result(timeout=120)
                return
            except Exception as e:
                if _attempt == 2:
                    _append_out(f"❌ 转发异常: {type(e).__name__}: {e}", out_file)
                else:
                    _time.sleep(1.5)
        _append_out("❌ 未找到 Main 实例（插件未初始化或重载中）", out_file)

    def _ident_of(out_file: str) -> str:
        """输出文件反推身份：主通道 → gm_playtest；带身份 → 文件名中的 ident。"""
        name = os.path.basename(out_file)
        if name == "playthrough_out.txt":
            return _PLAYTEST_QQ
        return name[len("playthrough_out_"):-len(".txt")]

    async def _collect(inst, ev, cmd, out_file):
        lines = [f"\n{'='*50}\n▶ 『{cmd}』"]
        try:
            async for r in inst._run_shortcut(ev, cmd):
                lines.append(str(r))
        except StopAsyncIteration:
            pass
        except Exception as e:
            lines.append(f"❌ 异常: {type(e).__name__}: {e}")
        _append_out("\n".join(lines), out_file)

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
    try:
        from .game.store.world import cleanup_stale_event_state
        n = cleanup_stale_event_state()
        if n:
            logging.getLogger(__name__).info("已清理 %d 个流失玩家残留 event_state 键", n)
    except Exception:
        logging.getLogger(__name__).warning(
            "event_state 残留键清理跳过（DB 未就绪或异常，不影响启动）", exc_info=True
        )


class Main(
    star.Star,
    PlayerCmds,
    WorldCmds,
    CombatCmds,
    EconomyCmds,
    SocialCmds,
    MiscCmds,
    InstanceCmds,
    GmCmds,
    ExplorationCmds,  # v115 探索进度指令
):
    """奥兰迪亚·余烬纪年西幻文字RPG——在QQ群里冒险吧！"""

    def __init__(self, context: star.Context) -> None:
        self.context = context
        # v101.28q：记录主事件循环——loopback worker 线程里的 handler 执行必须提交到主 loop，
        # 否则 await Quart websocket（aiocqhttp bot API）会跨 loop 挂死（gm_窥探 投递卡住的根因）
        try:
            self._main_loop = asyncio.get_event_loop()
        except RuntimeError:
            self._main_loop = None
        # v93 修复：仅真实 AstrBot 实例注册回环通道（测试脚本 Main(None) 会覆盖类变量 → 通道查 test 库）
        if context is not None:
            Main._loopback_instance = self  # v92: 文件转发通道拿当前实例
        db.init_db()
        # v104 M24 P2-5：启动时清理流失玩家残留 event_state 键（幂等，见 _event_state_cleanup_once）
        _event_state_cleanup_once()
        # v92: 文件转发体验通道——后台线程监控命令文件，
        # 在 AstrBot 进程内把命令转发给游戏引擎（真实 handler 链路），结果写回文件。
        # 用途：格温（Hermes）写 playthrough_cmd.txt → 进程内执行 → playthrough_out.txt 读结果，
        # 绕开跨进程 sqlite 锁竞争，以玩家身份逐条体验完整流程。
        # v94.1 修复：仅真实 AstrBot 实例启动 worker——测试脚本 Main(None) 若启动 worker，
        # 会抢走回环指令并在测试进程里报"未找到 Main 实例"（与 #40 同类问题）。
        if context is not None:
            _file_loopback_start()
        # v36: 广播任务已停用（意见改为 cron 汇总报告给鱼鱼，不回复玩家）
