# -*- coding: utf-8 -*-
"""预生成高频问题的 AI 答案，写进 canteen.db 的 ai_answers 表。

用途：演示时点预设问题 → 直接命中缓存秒回，不再等模型 5~20 秒。

用法：
    python _warm_answers.py                          # 用当前目录的 canteen.db，只补没有的
    python _warm_answers.py --force                  # 全部重算
    python _warm_answers.py D://path//canteen.db       # 指定库（推荐：直接对桌面库跑，不要整库覆盖）

每一条都是真跑大模型生成的（不是编的），只是把结果存下来了。
"""
import os
import sqlite3
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import app as appmod          # noqa: E402
import teleagent_client       # noqa: E402

# 与前端 AI_CHIPS 保持一致 —— 字不一样就命中不了缓存
QUERIES = [
    "今天有点热，想吃点凉的",
    "想吃辣的过过瘾",
    "没胃口，吃点开胃的",
    "减肥期，想吃低卡的",
    "穷学生，10块钱吃啥",
    "宵夜走起",
    "今天吃啥",
    "12块以内，不辣，高蛋白",
]


def main():
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    db_path = args[0] if args else os.path.join(BASE, "canteen.db")
    print("目标库：%s" % db_path)
    if not teleagent_client.engine_available():
        sys.exit("TeleAgent 引擎没起来（4397），先启动桌面端")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    appmod._ensure_ai_answers(conn)
    conn.commit()

    ok = skip = fail = 0
    for q in QUERIES:
        if not force and appmod._answer_get(conn, q):
            print("跳过（已有）：%s" % q)
            skip += 1
            continue
        t0 = time.time()
        try:
            prompt = appmod._ai_compact_prompt(conn, q)
            raw = teleagent_client.engine_ask(prompt, model="chat-lite", timeout=40)
            items = appmod._parse_ai_items(raw)
            items = appmod._finalize_ai_items(conn, items, q)
            if not items:
                print("失败（模型没返回有效结果）：%s" % q)
                fail += 1
                continue
            appmod._answer_put(conn, q, items)
            conn.commit()
            ok += 1
            print("%5.1fs  %s" % (time.time() - t0, q))
            for it in items:
                warn = (" ⚠" + it["warn"]) if it.get("warn") else ""
                print("        %-16s ¥%-5s %s%s" % (it["dish"], it["price"], it["reason"], warn))
        except Exception as e:
            print("异常：%s -> %r" % (q, e))
            fail += 1

    total = conn.execute("SELECT COUNT(*) FROM ai_answers").fetchone()[0]
    conn.close()
    print("\n完成：新增 %d，跳过 %d，失败 %d | 表内共 %d 条" % (ok, skip, fail, total))


if __name__ == "__main__":
    main()
