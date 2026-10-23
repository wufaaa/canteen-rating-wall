# -*- coding: utf-8 -*-
"""TeleAgent 桥接模块 —— 让本网页调用本机 TeleAgent 桌面端的智能体

原理（全部在本机完成，不联网）：
  1. 找到 TeleAgent 桌面端拉起的调度器守护进程（node scheduler/index.cjs daemon）
  2. 从该进程的内存环境块读取 SCHEDULER_API_TOKEN（仅同用户进程可读，不落盘）
  3. 调调度器本地 HTTP API：创建一次性任务 -> 立即执行
  4. 任务被 TeleAgent 桌面端派发给智能体会话（即网页调用“星辰”大模型本身）
  5. 从 teleagent.db 读回会话中助手的回答文本
  6. 清理临时任务

依赖：仅 Python 标准库（ctypes/sqlite3/urllib），Windows x64。
"""
import base64
import ctypes
import ctypes.wintypes as wintypes
import hashlib
import hmac
import json
import os
import sqlite3
import struct
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

# ---------------------------------------------------------------- 路径发现
_HOME = os.path.expanduser("~")
_SHARE = os.path.join(_HOME, ".local", "share", "TeleAgent")
_STATE_CANDIDATES = []          # 填充见 _state_file()
TA_DB_CANDIDATES = []           # teleagent.db 候选路径

_TOKEN_CACHE = {"pid": None, "token": None, "ts": 0.0}


def _data_roots():
    """TeleAgent 用户数据根目录候选（多账号时全部尝试）"""
    roots = []
    users_dir = os.path.join(_SHARE, "users")
    if os.path.isdir(users_dir):
        for name in os.listdir(users_dir):
            p = os.path.join(users_dir, name)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "scheduler", "scheduler-daemon-state.json")):
                roots.append(p)
    return roots


def _state_file():
    global _STATE_CANDIDATES, TA_DB_CANDIDATES
    if not _STATE_CANDIDATES:
        for root in _data_roots():
            _STATE_CANDIDATES.append(os.path.join(root, "scheduler", "scheduler-daemon-state.json"))
            TA_DB_CANDIDATES.append(os.path.join(root, "teleagent.db"))
    return _STATE_CANDIDATES[0] if _STATE_CANDIDATES else None


def _ta_dbs():
    _state_file()
    return [p for p in TA_DB_CANDIDATES if os.path.exists(p)]


# ---------------------------------------------------------------- Windows 进程内存读取（同用户进程，无需管理员）
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ntdll = ctypes.WinDLL("ntdll")

_PROCESS_QUERY_INFORMATION = 0x0400
_PROCESS_VM_READ = 0x0010

_k32.OpenProcess.restype = wintypes.HANDLE
_k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_k32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
_k32.CloseHandle.argtypes = [wintypes.HANDLE]


class _PBI(ctypes.Structure):
    _fields_ = [("r1", ctypes.c_void_p), ("peb", ctypes.c_void_p),
                ("r2", ctypes.c_void_p), ("r3", ctypes.c_void_p),
                ("pid", ctypes.c_void_p), ("r5", ctypes.c_void_p)]


_ntdll.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                              ctypes.POINTER(_PBI), ctypes.c_ulong,
                                              ctypes.POINTER(ctypes.c_ulong)]


def _read_mem(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t(0)
    if not _k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
        return None
    return buf.raw[:n.value]


def _read_ptr(h, addr):
    data = _read_mem(h, addr, 8)
    return struct.unpack("<Q", data)[0] if data else None


def _peb_params(h):
    """PEB -> ProcessParameters 指针（x64）"""
    pbi = _PBI()
    ln = ctypes.c_ulong(0)
    if _ntdll.NtQueryInformationProcess(h, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(ln)) != 0:
        return None
    if not pbi.peb:
        return None
    return _read_ptr(h, pbi.peb + 0x20)


def _read_cmdline(pid):
    """读进程命令行：ProcessParameters+0x70 的 UNICODE_STRING"""
    h = _k32.OpenProcess(_PROCESS_QUERY_INFORMATION | _PROCESS_VM_READ, False, pid)
    if not h:
        return None
    try:
        params = _peb_params(h)
        if not params:
            return None
        us = _read_mem(h, params + 0x70, 16)
        if not us or len(us) < 16:
            return None
        length, _, _, bufptr = struct.unpack("<HHIQ", us)
        if not bufptr:
            return ""
        raw = _read_mem(h, bufptr, length) if length else b""
        return raw.decode("utf-16-le", errors="replace") if raw else ""
    finally:
        _k32.CloseHandle(h)


def _read_env(pid):
    """读进程完整环境变量块 -> dict"""
    h = _k32.OpenProcess(_PROCESS_QUERY_INFORMATION | _PROCESS_VM_READ, False, pid)
    if not h:
        return {}
    try:
        params = _peb_params(h)
        if not params:
            return {}
        env = _read_ptr(h, params + 0x80)
        if not env:
            return {}
        chunks, off, text = [], 0, ""
        while off < (1 << 20):
            data = _read_mem(h, env + off, 4096)
            if not data:
                break
            chunks.append(data)
            off += len(data)
            text = b"".join(chunks).decode("utf-16-le", errors="replace")
            if "\x00\x00" in text:
                break
        end = text.find("\x00\x00")
        if end > 0:
            text = text[:end]
        out = {}
        for kv in text.split("\x00"):
            if "=" in kv:
                k, _, v = kv.partition("=")
                out[k] = v
        return out
    finally:
        _k32.CloseHandle(h)


def _find_scheduler_pids():
    """枚举 node.exe，找调度器守护进程（命令行含 scheduler/index.cjs + daemon）"""
    class PE32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]

    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = _k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snap or snap == wintypes.HANDLE(-1).value:
        return []
    entry = PE32W()
    entry.dwSize = ctypes.sizeof(PE32W)
    pids = []
    try:
        if _k32.Process32FirstW(snap, ctypes.byref(entry)):
            while True:
                if entry.szExeFile and entry.szExeFile.lower() == "node.exe":
                    cmd = _read_cmdline(entry.th32ProcessID) or ""
                    low = cmd.lower()
                    if "scheduler" in low and "index.cjs" in low and "daemon" in low:
                        pids.append(entry.th32ProcessID)
                if not _k32.Process32NextW(snap, ctypes.byref(entry)):
                    break
    finally:
        _k32.CloseHandle(snap)
    return pids


def _get_token():
    """获取调度器 API token（带缓存；进程换了会自动重读）"""
    pids = _find_scheduler_pids()
    if not pids:
        return None, None
    pid = pids[0]
    now = time.time()
    if _TOKEN_CACHE["pid"] == pid and _TOKEN_CACHE["token"] and now - _TOKEN_CACHE["ts"] < 30:
        return pid, _TOKEN_CACHE["token"]
    env = _read_env(pid)
    tok = env.get("SCHEDULER_API_TOKEN")
    if tok:
        _TOKEN_CACHE.update(pid=pid, token=tok, ts=now)
        return pid, tok
    return pid, None


# ---------------------------------------------------------------- 调度器 HTTP API
def _daemon_base():
    sf = _state_file()
    if not sf or not os.path.exists(sf):
        return None
    try:
        with open(sf, "r", encoding="utf-8") as f:
            return json.load(f).get("baseUrl")
    except Exception:
        return None


def _call(method, path, body=None, timeout=15):
    """调调度器 API；返回 (ok, data_or_errmsg)"""
    pid, token = _get_token()
    if not token:
        return False, "未找到 TeleAgent 调度器令牌（桌面端未运行或已重启）"
    base = _daemon_base()
    if not base:
        return False, "未找到调度器状态文件"
    req = urllib.request.Request(base + path, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("x-scheduler-client", "desktop-main")
    data = None
    if body is not None:
        req.add_header("Content-Type", "application/json; charset=utf-8")
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8"))
            return True, payload.get("data", payload)
    except urllib.error.HTTPError as e:
        if e.code == 401:  # token 过期（桌面端重启过），清缓存重试一次
            _TOKEN_CACHE.update(pid=None, token=None, ts=0)
        return False, "调度器拒绝访问（HTTP %d）" % e.code
    except Exception as e:
        return False, "调度器连接失败：%s" % e


# ---------------------------------------------------------------- 会话回读
def _read_session_answer(session_id):
    """从 teleagent.db 读会话里助手最后的完整文本回答。

    模型是流式写入的：一条助手消息生成完才会出现 step-finish 部分。
    最新助手消息若还没有 step-finish，说明仍在生成，返回 None 让上层继续等。
    """
    for db in _ta_dbs():
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True, timeout=5)
        except Exception:
            continue
        try:
            conn.row_factory = sqlite3.Row
            msgs = conn.execute(
                "SELECT id, data FROM message WHERE session_id=? ORDER BY time_created DESC",
                (session_id,)).fetchall()
            for m in msgs:
                try:
                    if json.loads(m["data"]).get("role") != "assistant":
                        continue
                except Exception:
                    continue
                parts = conn.execute(
                    "SELECT data FROM part WHERE message_id=? ORDER BY time_created",
                    (m["id"],)).fetchall()
                texts, has_finish = [], False
                for p in parts:
                    try:
                        d = json.loads(p["data"])
                    except Exception:
                        continue
                    if d.get("type") == "step-finish":
                        has_finish = True
                    if d.get("type") == "text" and d.get("text"):
                        texts.append(d["text"].strip())
                if not has_finish:
                    return None  # 最新助手消息还在生成中
                if texts:
                    return "\n".join(texts)
                # 完成但没有文本（罕见），继续找更早的助手消息
        finally:
            conn.close()
    return None


# ---------------------------------------------------------------- 对外主入口
def available():
    """TeleAgent 桥是否可用（桌面端在跑 + token 可读）"""
    pid, token = _get_token()
    return bool(pid and token and _daemon_base())


def ask(prompt, timeout=150):
    """把 prompt 发给本机 TeleAgent 智能体，返回回答文本。

    失败/超时返回 None（调用方应走本地兜底）。
    """
    # 1. 创建一次性任务（run_at 设在未来，仅靠手动触发执行）
    run_at = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    ok, data = _call("POST", "/api/v1/jobs", {
        "name": "ai-dish-recommend", "type": "once", "run_at": run_at,
        "prompt": prompt, "agent": "general"})
    if not ok:
        return None
    job_id = data.get("id")

    try:
        # 2. 立即触发
        ok, data = _call("POST", "/api/v1/jobs/%s/run" % job_id, {}, timeout=30)
        if not ok:
            return None
        run_id = data.get("run_id")

        # 3. 轮询派发结果（拿 session_id）
        deadline = time.time() + min(timeout, 90)
        session_id = None
        while time.time() < deadline:
            time.sleep(1.2)
            ok, data = _call("GET", "/api/v1/jobs/%s/runs?limit=1&offset=0" % job_id)
            if not ok:
                continue
            runs = data.get("runs") or []
            if not runs:
                continue
            run = runs[0]
            if run.get("status") == "dispatch_success":
                session_id = run.get("session_id")
                break
            if run.get("status") in ("failed", "error", "cancelled"):
                return None
        if not session_id:
            return None

        # 4. 轮询会话回答
        deadline = time.time() + timeout
        while time.time() < deadline:
            answer = _read_session_answer(session_id)
            if answer:
                return answer
            time.sleep(2)
        return None
    finally:
        # 5. 清理临时任务（尽力而为）
        try:
            _call("DELETE", "/api/v1/jobs/%s" % job_id)
        except Exception:
            pass


# ---------------------------------------------------------------- 引擎直连（127.0.0.1:4397）
# 桌面端内置的 OpenCode 兼容引擎。相比调度器投递（8080），这条路跳过 20~25 秒的
# 「渲染器领任务」派发，同步执行到完成，实测点菜 4~14 秒（取决于模型档位）。
_ENGINE_BASE = "http://127.0.0.1:4397"
_ENGINE_DIR = os.path.join(os.environ.get("TEMP", "C:/tmp"), "canteen-ai-ws")
_ENGINE_PROVIDER = os.environ.get("AI_ENGINE_PROVIDER", "NewApi")
_ENGINE_CREDS = {}
_ENGINE_SESSION = None


def _all_pids():
    class PE32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]
    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = _k32.CreateToolhelp32Snapshot(0x2, 0)
    e = PE32W()
    e.dwSize = ctypes.sizeof(PE32W)
    out = []
    if _k32.Process32FirstW(snap, ctypes.byref(e)):
        while True:
            out.append(e.th32ProcessID)
            if not _k32.Process32NextW(snap, ctypes.byref(e)):
                break
    _k32.CloseHandle(snap)
    return out


def _engine_creds(force=False):
    """从进程环境发现引擎凭据（Basic + HMAC），结果缓存。"""
    global _ENGINE_CREDS
    if _ENGINE_CREDS and not force:
        return _ENGINE_CREDS
    keys = ["SUPER_AGENT_OPENCODE_USERNAME", "SUPER_AGENT_OPENCODE_PASSWORD",
            "OPENCODE_SERVER_USERNAME", "OPENCODE_SERVER_PASSWORD",
            "SUPER_AGENT_LOCAL_SESSION_KEY"]
    found = {}
    for pid in _all_pids():
        env = _read_env(pid)
        if not env:
            continue
        for k in keys:
            if env.get(k):
                found.setdefault(k, env[k])
    _ENGINE_CREDS = {
        "user": found.get("SUPER_AGENT_OPENCODE_USERNAME")
                or found.get("OPENCODE_SERVER_USERNAME") or "",
        "pwd": found.get("SUPER_AGENT_OPENCODE_PASSWORD")
               or found.get("OPENCODE_SERVER_PASSWORD") or "",
        "sk": found.get("SUPER_AGENT_LOCAL_SESSION_KEY") or "",
    }
    return _ENGINE_CREDS


def engine_available(timeout=3):
    """引擎是否就绪（/ready 无需鉴权）"""
    try:
        with urllib.request.urlopen(_ENGINE_BASE + "/ready", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _engine_sign(method, pq):
    ts = str(int(time.time() * 1000))
    nonce = os.urandom(12).hex()
    payload = "\n".join(["local-v1", method.upper(), pq, ts, nonce])
    sig = base64.urlsafe_b64encode(
        hmac.new(_ENGINE_CREDS["sk"].encode(), payload.encode(),
                 hashlib.sha256).digest()).decode().rstrip("=")
    return {"X-SA-Sign-Version": "local-v1", "X-SA-Timestamp": ts,
            "X-SA-Nonce": nonce, "X-SA-Signature": sig}


def _engine_headers(method, pq):
    c = _engine_creds()
    h = {}
    if c["user"] and c["pwd"]:
        h["Authorization"] = "Basic " + base64.b64encode(
            ("%s:%s" % (c["user"], c["pwd"])).encode()).decode()
    if c["sk"]:
        h.update(_engine_sign(method, pq))
    return h


def _engine_call(method, path, body=None, timeout=60):
    pq = path if "?" in path else path + "?directory=" + _ENGINE_DIR.replace("\\", "/")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(_ENGINE_BASE + pq, data=data, method=method)
    for k, v in _engine_headers(method, pq).items():
        r.add_header(k, v)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as ex:
        return ex.code, ex.read().decode("utf-8", "replace")
    except Exception as ex:
        return None, str(ex)


def engine_ask(prompt, model="chat-lite", timeout=30):
    """引擎直连：同步发一条消息，返回助手文本；失败返回 None。"""
    global _ENGINE_SESSION
    if not engine_available():
        return None
    if not _ENGINE_SESSION:
        os.makedirs(_ENGINE_DIR, exist_ok=True)
        st, body = _engine_call("POST", "/session", {"title": "ai-diancai"})
        if st != 200:
            return None
        try:
            _ENGINE_SESSION = json.loads(body)["id"]
        except Exception:
            return None
    st, body = _engine_call("POST", "/session/%s/message" % _ENGINE_SESSION, {
        "parts": [{"type": "text", "text": prompt}],
        "model": {"providerID": _ENGINE_PROVIDER, "modelID": model}}, timeout=timeout)
    if st != 200:
        _ENGINE_SESSION = None
        return None
    try:
        node = json.loads(body).get("data", {})
        info = node.get("info", {})
        if (info.get("error") or {}).get("data", {}).get("message"):
            return None
        return "\n".join(p.get("text", "") for p in node.get("parts", [])
                         if p.get("type") == "text") or None
    except Exception:
        return None


def engine_stream(prompt, model="chat-lite", timeout=30):
    """流式版本：订阅 /event，逐段 yield 正文 delta。

    产出事件：
      {"type": "delta", "text": "..."}     逐段正文
      {"type": "done",  "full": "..."}     结束（full 为完整正文，可能为空）
      {"type": "error", "message": "..."}  出错
    """
    import queue
    import threading
    global _ENGINE_SESSION
    if not engine_available():
        yield {"type": "error", "message": "引擎未就绪"}
        return
    # 每次流式都新建会话，避免长驻会话过期（建会话约 0ms）
    os.makedirs(_ENGINE_DIR, exist_ok=True)
    st, body = _engine_call("POST", "/session", {"title": "ai-diancai"})
    if st != 200:
        yield {"type": "error", "message": "会话创建失败"}
        return
    try:
        sid = json.loads(body)["id"]
        _ENGINE_SESSION = sid
    except Exception:
        yield {"type": "error", "message": "会话解析失败"}
        return
    q = queue.Queue()
    state = {"full": ""}

    def sse_reader():
        pq = "/event?directory=" + _ENGINE_DIR.replace("\\", "/")
        try:
            req = urllib.request.Request(_ENGINE_BASE + pq, method="GET")
            for k, v in _engine_headers("GET", pq).items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout + 20) as resp:
                part_types = {}
                for raw in resp:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    try:
                        d = json.loads(line[5:].strip())
                    except Exception:
                        continue
                    t = d.get("type")
                    props = d.get("properties") or {}
                    if t == "message.part.updated":
                        p = props.get("part") or {}
                        p_sid = p.get("sessionID") or props.get("sessionID")
                        if p_sid and p_sid != sid:
                            continue
                        if p.get("id"):
                            part_types[p["id"]] = p.get("type")
                        continue
                    if props.get("sessionID") and props.get("sessionID") != sid:
                        continue
                    if t == "message.part.delta":
                        pt = part_types.get(props.get("partID"))
                        if props.get("field") == "text" and pt in ("text", "reasoning"):
                            delta = props.get("delta") or ""
                            if delta:
                                q.put(("delta", pt, delta))
                    elif t == "session.status":
                        if (props.get("status") or {}).get("type") == "idle":
                            q.put(("idle", None, None))
                            return
        except Exception as ex:
            q.put(("error", None, repr(ex)))

    def sender():
        st, body = _engine_call("POST", "/session/%s/message" % sid, {
            "parts": [{"type": "text", "text": prompt}],
            "model": {"providerID": _ENGINE_PROVIDER, "modelID": model}}, timeout=timeout)
        if st != 200:
            q.put(("error", None, "HTTP %s: %s" % (st, str(body)[:150])))
            return
        try:
            node = json.loads(body).get("data", {})
            info = node.get("info", {})
            err = (info.get("error") or {}).get("data", {}).get("message")
            if err:
                q.put(("error", None, err))
                return
            state["full"] = "\n".join(
                p.get("text", "") for p in node.get("parts", []) if p.get("type") == "text")
        except Exception as ex:
            q.put(("error", None, repr(ex)))
            return
        q.put(("sent", None, None))

    threading.Thread(target=sse_reader, daemon=True).start()
    time.sleep(0.4)
    st_th = threading.Thread(target=sender, daemon=True)
    st_th.start()

    while True:
        try:
            kind, part, val = q.get(timeout=timeout + 8)
        except queue.Empty:
            yield {"type": "error", "message": "等待超时"}
            return
        if kind == "delta":
            yield {"type": "delta", "part": part, "text": val}
        elif kind == "error":
            yield {"type": "error", "message": val}
            return
        elif kind in ("idle", "sent"):
            break
    st_th.join(timeout=2)
    yield {"type": "done", "full": state["full"]}


if __name__ == "__main__":
    # 自检：python teleagent_client.py "你好，请回复：桥接正常"
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "请只回复四个字：桥接正常"
    print("TeleAgent 可用:", available())
    t0 = time.time()
    a = ask(q)
    print("耗时 %.1fs" % (time.time() - t0))
    print("回答:", a)
