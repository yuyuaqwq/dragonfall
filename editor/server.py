#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚 · 配置编辑器 —— 后端（Python stdlib http.server，零第三方依赖）

启动
----
    python editor/server.py                 # 默认 http://127.0.0.1:8765
    python editor/server.py --port 9000
    python editor/server.py --host 0.0.0.0  # 局域网可访问（默认只绑本机）

API
---
    GET  /                        → editor/web/index.html（单页应用）
    GET  /<静态文件>               → editor/web/ 下的文件
    GET  /api/domains             → 可编辑域列表 + 写入模式/source 信息
    GET  /api/domain/<域>          → 条目列表（分组 + 元信息）
    GET  /api/domain/<域>/<key>    → 单条完整 dict + schema + 该条校验结果
    POST /api/domain/<域>/<key>    → 收 JSON、**先过 schema 校验**、合法才写工作副本
    GET  /api/schema/<域>          → <域>.schema.json 原文（表单渲染用）
    POST /api/simulate            → 战斗模拟预览（子进程跑引擎，见 editor/simulate.py）

域：`skills`（技能）/ `affixes`（词条）。加新域见 editor/README.md「新增一个域」。

写入策略：JSON 工作副本（editor/.workdir/<域>.json），绝不改 game/data/*.py。

安全：只绑 127.0.0.1、只读 game/ 数据、静态文件做路径逃逸防护；不提供任何删除/执行接口。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_io  # noqa: E402  （同目录模块）
import simulate  # noqa: E402  （同目录模块；只起子进程，不 import game）

EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(EDITOR_DIR, "web")

# 域列表（顺序 = UI 顺序）来自 data_io.DOMAIN_DEFS —— 加域只改 data_io 一处
DOMAINS = list(data_io.DOMAINS)
DOMAIN_LABELS = {d: data_io.DOMAIN_DEFS[d]["label"] for d in DOMAINS}

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _simulate_supported(domain: str) -> bool:
    return domain == "skills"


class Handler(BaseHTTPRequestHandler):
    server_version = "DragonfallEditor/0.2"
    protocol_version = "HTTP/1.1"

    # ------------------------------------------------------------------ helpers
    def _send(self, status: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, status: int = 200):
        self._send(status, json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))

    def _ok(self, **kw):
        self._json({"ok": True, **kw})

    def _err(self, status: int, message: str, **kw):
        self._json({"ok": False, "message": message, **kw}, status=status)

    def log_message(self, fmt, *args):                        # 精简访问日志
        sys.stderr.write("  · %s\n" % (fmt % args))

    # --------------------------------------------------------------------- GET
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/" or path == "/index.html":
                return self._serve_static("index.html")
            if path.startswith("/api/"):
                return self._api_get(path)
            return self._serve_static(path.lstrip("/"))
        except BrokenPipeError:
            pass
        except Exception as exc:                              # pragma: no cover
            self._err(500, f"{type(exc).__name__}: {exc}")

    def do_HEAD(self):
        self.do_GET()

    def _serve_static(self, rel: str):
        target = os.path.normpath(os.path.join(WEB_DIR, rel))
        if not (target == WEB_DIR or target.startswith(WEB_DIR + os.sep)):
            return self._err(403, "路径越界")
        if not os.path.isfile(target):
            return self._err(404, f"未找到 {rel}")
        ext = os.path.splitext(target)[1].lower()
        with open(target, "rb") as fh:
            self._send(200, fh.read(), _CONTENT_TYPES.get(ext, "application/octet-stream"))

    def _api_get(self, path: str):
        rest = path[len("/api/"):]
        if rest == "domains":
            info = data_io.source_info("skills")
            return self._ok(
                domains=[{"id": d, "label": DOMAIN_LABELS.get(d, d), "writable": True,
                          "primary": data_io.DOMAIN_DEFS[d]["primary"],
                          "flat": data_io.DOMAIN_DEFS[d]["flat"],
                          "capabilities": {"simulate": _simulate_supported(d)}}
                         for d in DOMAINS],
                simulate_available=simulate.available(),
                **info)
        if rest.startswith("schema/"):
            domain = rest[len("schema/"):]
            if not self._valid_domain(domain):
                return self._err(404, f"未知域: {domain}")
            return self._ok(domain=domain, title=DOMAIN_LABELS.get(domain, domain),
                            primary=data_io.DOMAIN_DEFS[domain]["primary"],
                            schema=data_io.load_schema(domain))
        if rest.startswith("domain/"):
            parts = rest[len("domain/"):].split("/")
            domain = parts[0]
            if not self._valid_domain(domain):
                return self._err(404, f"未知域: {domain}")
            if len(parts) == 1 or not parts[1]:
                return self._ok(**data_io.list_payload(domain))
            key = "/".join(parts[1:])
            meta, data = data_io.get_entry(domain, key)
            if data is None:
                return self._err(404, f"条目不存在: {key}")
            return self._ok(key=key, meta=meta, data=data,
                            schema=data_io.load_schema(domain),
                            primary=data_io.DOMAIN_DEFS[domain]["primary"],
                            validation=data_io.validate_entry(domain, data),
                            capabilities={"simulate": _simulate_supported(domain)},
                            **data_io.source_info(domain))
        return self._err(404, f"未知 API: /{rest}")

    # -------------------------------------------------------------------- POST
    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        if not path.startswith("/api/"):
            return self._err(404, "只支持 /api/ 下的 POST")
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception as exc:
            return self._err(400, f"请求体不是合法 JSON: {exc}")

        rest = path[len("/api/"):]
        if rest == "simulate":
            return self._api_simulate(payload)
        if rest.startswith("domain/"):
            parts = rest[len("domain/"):].split("/")
            domain = parts[0]
            if not self._valid_domain(domain):
                return self._err(404, f"未知域: {domain}")
            if len(parts) < 2 or not parts[1]:
                return self._err(400, f"缺少条目 key（域 {domain}）")
            key = "/".join(parts[1:])
            body = payload.get("data", payload) if isinstance(payload, dict) else payload
            if not isinstance(body, dict):
                return self._err(400, "条目数据必须是 JSON 对象")
            # ---- 先校验，合法才写盘
            result = data_io.validate_entry(domain, body)
            if not result["ok"]:
                return self._err(422, "schema 校验未通过，未写盘",
                                 domain=domain, key=key, validation=result)
            before_meta, before = data_io.get_entry(domain, key)
            created = before is None
            try:
                info = data_io.set_entry(domain, key, body)
            except Exception as exc:
                return self._err(500, f"写盘失败: {type(exc).__name__}: {exc}")
            changed = [] if created else data_io.diff_values(before, body)
            return self._ok(key=key, created=created, changed=changed,
                            saved_to=info["copy_path"], validation=result,
                            **data_io.source_info(domain))
        return self._err(404, f"未知 API: /{rest}")

    # ---------------------------------------------------------------- simulate
    def _api_simulate(self, payload: dict):
        if not isinstance(payload, dict):
            return self._err(400, "模拟入参必须是 JSON 对象")
        skill = payload.get("skill")
        if not isinstance(skill, dict) or not skill:
            return self._err(400, "缺少技能数据（skill），无法模拟")
        # 入口先过 schema 校验 —— 非法技能给「友好、可定位」的报错，不进子进程
        result = data_io.validate_entry("skills", skill)
        if not result["ok"]:
            return self._err(422, "技能未通过 schema 校验，未模拟",
                             skill_name=skill.get("name"), validation=result)
        try:
            timeout = float(payload.get("timeout") or 0) or None
        except Exception:
            timeout = None
        res = simulate.simulate(payload, timeout=timeout)
        if res.get("ok"):
            return self._ok(**{k: v for k, v in res.items() if k != "ok"})
        # 引擎/超时/崩溃：仍返回 200 + ok:false（让前端在预览面板内展示原因，而不是当网络错误）
        return self._json(res, status=200)

    # -------------------------------------------------------------------- utils
    @staticmethod
    def _valid_domain(domain: str) -> bool:
        return domain in DOMAINS


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="奥兰迪亚配置编辑器（技能 / 词条域）")
    ap.add_argument("--host", default="127.0.0.1", help="绑定地址（默认 127.0.0.1，仅本机）")
    ap.add_argument("--port", type=int, default=8765, help="端口（默认 8765）")
    args = ap.parse_args(argv)

    info = data_io.source_info("skills")
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{'127.0.0.1' if args.host in ('0.0.0.0', '') else args.host}:{args.port}/"
    print("=" * 68)
    print("  奥兰迪亚 · 配置编辑器")
    print("=" * 68)
    print(f"  本地地址   : {url}")
    print(f"  服务目录   : {WEB_DIR}")
    print(f"  数据来源   : {info['source']}  ({info['source_path']})")
    print(f"  写入目标   : {info['write_mode']}  ({info['copy_path']})")
    print(f"  校验器引擎 : {info['validator']}")
    print(f"  可编辑域   : {', '.join(f'{d}({DOMAIN_LABELS[d]})' for d in DOMAINS)}")
    print(f"  战斗模拟   : {'可用（子进程跑引擎）' if simulate.available() else '不可用（缺 simulate_worker.py）'}")
    print("  Ctrl+C 停止")
    print("=" * 68)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止。")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
