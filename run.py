# -*- coding: utf-8 -*-
"""一键启动器：检查依赖 -> 起服务 -> 等服务就绪后自动打开浏览器。

用法：双击 start.bat（或在命令行里 python run.py）。
之所以不在 start.bat 里直接打开浏览器，是因为 Flask 启动要一两秒，
提前打开会看到「无法访问此网站」，很容易被当成打不开。
"""
import os
import sys
import threading
import time
import urllib.request
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

os.environ.setdefault("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "5001"))
URL = "http://127.0.0.1:%d" % PORT

# 国内网络直连 pypi.org 很慢，按顺序试镜像
MIRRORS = [
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://mirrors.cloud.tencent.com/pypi/simple/",
    "https://pypi.org/simple/",
]


def ensure_flask():
    try:
        import flask  # noqa: F401
        return True
    except ImportError:
        pass

    import subprocess
    print("[1/2] 缺少 flask，正在安装（首次运行需要联网，约 10 秒）…")
    for m in MIRRORS:
        print("      尝试镜像：%s" % m)
        rc = subprocess.call([
            sys.executable, "-m", "pip", "install", "flask",
            "-i", m, "--timeout", "20", "--disable-pip-version-check", "-q",
        ])
        if rc == 0:
            try:
                import flask  # noqa: F401
                return True
            except ImportError:
                pass
    return False


def open_when_ready():
    """轮询 /api/health，服务真的起来了才开浏览器。"""
    for _ in range(120):
        try:
            urllib.request.urlopen(URL + "/api/health", timeout=2).read()
            webbrowser.open(URL)
            return
        except Exception:
            time.sleep(0.5)
    print("\n服务好像没起来，请把上面的报错发我。")


def main():
    if not ensure_flask():
        print("\n依赖安装失败。请手动执行：")
        print("  pip install flask -i https://mirrors.aliyun.com/pypi/simple/")
        try:
            input("\n按回车退出…")
        except EOFError:
            pass
        return

    print("[2/2] 启动服务：%s" % URL)
    print("      启动后浏览器会自动打开；关闭本窗口即停止服务。\n")
    threading.Thread(target=open_when_ready, daemon=True).start()

    import app
    try:
        app.run()
    except OSError as e:
        print("\n端口 %d 被占用了（%s）。" % (PORT, e))
        print("换个端口重试，例如：")
        print("  set PORT=5002 && python run.py")
        try:
            input("\n按回车退出…")
        except EOFError:
            pass


if __name__ == "__main__":
    main()
