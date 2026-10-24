# -*- coding: utf-8 -*-
"""智慧食堂 · AI 后端回归测试（对应《AI 修复指导报告书》PART 3）

跑法：
    python _test_ai.py

不依赖 TeleAgent 是否启动：需要引擎的用例用 mock，另有一条真实引擎的可选用例。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import app as appmod          # noqa: E402
import teleagent_client       # noqa: E402
import ai_local               # noqa: E402

client = appmod.app.test_client()

# 独立的辣味词表（不复用 ai_local 的规则，避免自己验自己）
SPICY_WORDS = ["辣", "麻", "椒", "香锅", "冒菜", "螺蛳", "水煮", "剁椒", "红油", "打抛", "冬阴功"]

RESULTS = []


def record(no, name, ok, detail=""):
    RESULTS.append((no, name, ok, detail))
    print("  [%s] #%s %s" % ("PASS" if ok else "FAIL", no, name))
    if detail:
        for line in str(detail).splitlines():
            print("        " + line)


def is_spicy(text):
    """「不辣/清淡」这种自我声明不算辣，先剔掉再判断"""
    return any(w in (text or "").replace("不辣", "") for w in SPICY_WORDS)


def budget_of(q):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:块|元)", q or "")
    return float(m.group(1)) if m else None


def sse(q):
    """POST /api/ai/stream，返回 (status, [(event, data), ...])"""
    r = client.post("/api/ai/stream", json={"q": q})
    body = r.get_data(as_text=True)
    events = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        ev = data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if ev:
            try:
                events.append((ev, json.loads(data) if data else None))
            except Exception:
                events.append((ev, data))
    return r.status_code, events


def local_off():
    teleagent_client.engine_available = lambda: False


def local_on(full_text):
    """mock 引擎：可用 + 直接吐一段文本"""
    teleagent_client.engine_available = lambda: True

    def gen(prompt, model=None, timeout=12):
        yield {"type": "delta", "text": "（mock 推理）", "part": "reasoning"}
        yield {"type": "done", "full": full_text}

    teleagent_client.engine_stream = gen


def get_local_items(events):
    for ev, data in events:
        if ev == "local":
            return (data or {}).get("items") or []
    return []


def get_done(events):
    for ev, data in events:
        if ev == "done":
            return data or {}
    return {}


# ------------------------------------------------------------------ 用例
def case1():
    q = "10块不辣，想吃点高蛋白的"
    local_off()
    status, events = sse(q)
    items = get_local_items(events)
    done = get_done(events)
    budget = budget_of(q)
    names = "、".join(i["dish"] for i in items)
    ok = (status == 200
          and len(items) == 3
          and len(done.get("items") or []) == 3
          and all(i["price"] <= budget for i in items)
          and not any(is_spicy(i["dish"]) or is_spicy(i.get("intro")) for i in items)
          and not any(is_spicy(i.get("reason")) for i in items))
    record(1, "不辣·高蛋白（引擎关闭）",
           ok, "status=%s local=%d done=%d\n%s" % (status, len(items), len(done.get("items") or []), names))


def case2():
    """4 食堂全量：244 道菜名逐个当 query，不能有 500 / IndexError"""
    local_off()
    import sqlite3
    conn = sqlite3.connect(os.path.join(BASE, "canteen.db"))
    conn.row_factory = sqlite3.Row
    names = [r["name"] for r in conn.execute(
        "SELECT DISTINCT name FROM dishes WHERE status=1 ORDER BY id")]
    max_canteen = conn.execute("SELECT MAX(canteen) FROM windows").fetchone()[0]
    conn.close()

    bad = []
    for n in names:
        status, events = sse(n)
        if status != 200:
            bad.append((n, status))
        elif not get_local_items(events):
            bad.append((n, "local 空"))
    record(2, "4 食堂全量（%d 道菜逐个 query）" % len(names),
           not bad,
           "最大食堂序号=%s；失败 %d 个%s" % (max_canteen, len(bad), ("：" + str(bad[:5])) if bad else ""))


def case3():
    q = "今天有点热，想吃点凉的"
    local_off()
    status, events = sse(q)
    done = get_done(events)
    ok = (status == 200 and done.get("engine") == "local"
          and len(done.get("items") or []) == 3)
    record(3, "引擎关闭仍出 3 条", ok,
           "status=%s engine=%s items=%d" % (status, done.get("engine"), len(done.get("items") or [])))


def case4():
    q = "10块不辣"
    local_on("这不是 JSON，模型跑偏了")
    status, events = sse(q)
    done = get_done(events)
    ok = (status == 200 and done.get("engine") == "local"
          and len(done.get("items") or []) == 3 and done.get("note"))
    record(4, "JSON 不合法 → 不 500，自动 local", ok,
           "status=%s engine=%s note=%r" % (status, done.get("engine"), done.get("note")))


def case5():
    """AI 报 price=999：接口必须返回数据库真实价格"""
    q = "想吃黄焖鸡"
    fake = json.dumps([{"dish": "黄焖鸡米饭(大份)", "window": "黄焖鸡",
                        "loc": "九食堂9楼", "price": 999, "score": 9.9,
                        "reason": "肉多"}], ensure_ascii=False)
    local_on(fake)
    status, events = sse(q)
    done = get_done(events)
    items = done.get("items") or []
    ok = status == 200 and bool(items) and all(i["price"] != 999 for i in items)
    detail = "status=%s\n" % status + "\n".join(
        "  %s ¥%s @%s" % (i["dish"], i["price"], i.get("loc")) for i in items)
    if items:
        ok = ok and all(i.get("score") is None or i["score"] <= 5 for i in items)
    record(5, "AI 报错价格 999 → 用数据库价格", ok, detail)


def case6():
    """菜名不存在：该条丢弃，用本地补齐到 3 条"""
    q = "想吃点热的"
    fake = json.dumps([{"dish": "不存在的菜", "window": "不存在",
                        "loc": "零食堂", "price": 1, "score": 5, "reason": "编的"}],
                      ensure_ascii=False)
    local_on(fake)
    status, events = sse(q)
    done = get_done(events)
    items = done.get("items") or []
    names = [i["dish"] for i in items]
    ok = status == 200 and len(items) == 3 and "不存在的菜" not in names
    record(6, "菜名不存在 → 丢弃并本地补齐", ok, "status=%s items=%s" % (status, "、".join(names)))


def case7():
    q = "12块以内，不辣，高蛋白"
    local_off()
    r = client.post("/api/ai/stream", json={"q": q})
    body = r.get_data(as_text=True)
    n_local = body.count("event: local")
    n_done = body.count("event: done")
    ok = (r.status_code == 200 and n_local == 1 and n_done == 1
          and "<html" not in body.lower() and "internal server error" not in body.lower())
    record(7, "SSE 格式（local/done 各 1 次、无 HTML）", ok,
           "status=%s local=%d done=%d bytes=%d" % (r.status_code, n_local, n_done, len(body)))


def case8():
    """约束冲突：不辣 + 想吃麻辣 → 按不辣优先，不返回辣菜"""
    q = "不辣但想吃麻辣的"
    local_off()
    status, events = sse(q)
    items = get_local_items(events)
    ok = status == 200 and bool(items) and not any(is_spicy(i["dish"]) for i in items)
    record(8, "约束冲突（不辣+麻辣）按不辣优先", ok,
           "items=%s" % "、".join(i["dish"] for i in items))


def case9():
    """真实引擎冒烟（可选）：没启动 TeleAgent 就跳过"""
    import importlib
    importlib.reload(teleagent_client)
    if not teleagent_client.engine_available():
        record(9, "真实引擎冒烟（跳过：TeleAgent 未运行）", True, "engine_available=False")
        return
    q = "12块以内，不辣，高蛋白"
    status, events = sse(q)
    done = get_done(events)
    items = done.get("items") or []
    ok = (status == 200 and len(items) == 3
          and done.get("engine") in ("engine", "local"))
    record(9, "真实引擎冒烟", ok,
           "status=%s engine=%s items=%d\n%s" % (
               status, done.get("engine"), len(items),
               "、".join("%s ¥%s" % (i["dish"], i["price"]) for i in items)))


def main():
    print("=" * 62)
    print("智慧食堂 · AI 后端回归测试")
    print("=" * 62)
    for fn in [case1, case2, case3, case4, case5, case6, case7, case8, case9]:
        try:
            fn()
        except Exception as e:
            record(fn.__name__, fn.__name__ + " 异常", False, repr(e))
    print("-" * 62)
    passed = sum(1 for r in RESULTS if r[2])
    print("合计 %d 项：通过 %d，失败 %d" % (len(RESULTS), passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
