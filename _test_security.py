# -*- coding: utf-8 -*-
"""智慧食堂 · 安全检查（本地实测，不需要启动服务）

跑法：
    python _test_security.py

覆盖：路径穿越 / 越权访问 / SQL 注入 / AI 输入限制 / 上传类型 / 大文件 /
      限频 / 登录会话重建 / 敏感文件暴露。
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import app as appmod  # noqa: E402

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        for line in str(detail).splitlines():
            print("        " + line)


def fresh_client():
    c = appmod.app.test_client()
    # 匿名身份：正常访问一次即下发
    c.get("/api/whoami")
    return c


def main():
    print("=" * 62)
    print("智慧食堂 · 安全检查")
    print("=" * 62)

    c = fresh_client()

    # 1) 路径穿越：别想从 /uploads 摸到 secret.key
    bad = 0
    for p in ["/uploads/../secret.key", "/uploads/..%2F..%2Fsecret.key",
              "/uploads/%2e%2e%2fsecret.key", "/uploads/....//secret.key"]:
        r = c.get(p)
        if r.status_code == 200 and b"secret" not in r.data[:200].lower():
            pass
        if r.status_code == 200:
            bad += 1
            print("        可疑: %s -> %s %r" % (p, r.status_code, r.data[:60]))
    record("路径穿越（/uploads 摸 secret.key）", bad == 0, "4 种变体，200 命中 %d 次" % bad)

    # 2) 未登录访问管理端 / 商家端
    r1 = c.get("/api/admin/dashboard")
    r2 = c.post("/api/merchant/dishes", json={"name": "x", "price": 1})
    r3 = c.get("/api/admin/logs")
    ok = all(r.status_code in (401, 403) for r in (r1, r2, r3))
    record("未登录访问管理/商家接口被拒", ok,
           "admin=%s merchant=%s logs=%s" % (r1.status_code, r2.status_code, r3.status_code))

    # 3) SQL 注入：搜索参数带引号不能 500，也不能拖库
    payloads = ["' OR 1=1 --", "'; DROP TABLE ratings; --", "%' UNION SELECT password_hash FROM admins --"]
    codes = []
    for q in payloads:
        r = c.get("/api/search", query_string={"q": q})
        codes.append(r.status_code)
    # 注入后库还在？
    with appmod.get_db() as conn:
        n = conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
    record("SQL 注入（搜索参数）", all(x == 200 for x in codes) and n > 0,
           "状态码=%s 注入后 ratings 行数=%d" % (codes, n))

    # 4) AI 输入长度限制
    r = c.post("/api/ai/quick", json={"q": "吃" * 200})
    record("AI 输入超长被拒（>60 字）", r.status_code == 400,
           "status=%s msg=%r" % (r.status_code, (r.get_json() or {}).get("msg")))

    # 5) 上传类型：.html 必须被拒
    data = {"photo": (io.BytesIO(b"<script>alert(1)</script>"), "evil.html")}
    r = c.post("/api/posts/1/photo", data=data, content_type="multipart/form-data")
    record("上传 .html 被拒", r.status_code == 400,
           "status=%s msg=%r" % (r.status_code, (r.get_json() or {}).get("msg")))

    # 6) 超大文件：6MB 上限
    big = io.BytesIO(b"\xff" * (7 * 1024 * 1024))
    r = c.post("/api/posts/1/photo", data={"photo": (big, "big.jpg")},
               content_type="multipart/form-data")
    record("超大上传被拒（>6MB）", r.status_code in (400, 413),
           "status=%s" % r.status_code)

    # 7) 登录成功后会话重建（防会话固定）
    c2 = fresh_client()
    with c2.session_transaction() as sess:
        sess["anon_id"] = 999999          # 伪造一个旧身份
        sess["evil"] = "keep-me"
    r = c2.post("/api/auth/login", json={"role": "admin", "username": "admin",
                                         "password": os.environ.get("ADMIN_PASSWORD", "admin@2026")})
    with c2.session_transaction() as sess:
        still_evil = "evil" in sess
        still_anon = "anon_id" in sess
    record("登录后会话重建", r.status_code == 200 and not still_evil and not still_anon,
           "status=%s 旧字段残留 evil=%s anon_id=%s" % (r.status_code, still_evil, still_anon))

    # 8) 限频：连续 21 次 AI 提问，第 21 次应被拦（限频默认 20/天/设备）
    c3 = fresh_client()
    codes = []
    for i in range(21):
        r = c3.post("/api/ai/quick", json={"q": "今天吃啥"})
        codes.append(r.status_code)
        if r.status_code == 400:
            break
    record("AI 防刷限频（第 21 次拦截）", codes.count(400) >= 1 and len(codes) <= 21,
           "前 20 次状态=%s，第 %d 次返回 400" % (set(codes[:-1]), len(codes)))

    # 9) 敏感文件不在静态目录里
    leaks = []
    for p in ["/secret.key", "/canteen.db", "/app.py", "/database.py", "/.gitignore"]:
        r = c.get(p)
        if r.status_code == 200:
            leaks.append(p)
    record("源码/密钥/数据库不可直接下载", not leaks, "暴露路径=%s" % (leaks or "无"))

    print("-" * 62)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("合计 %d 项：通过 %d，失败 %d" % (len(RESULTS), passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
