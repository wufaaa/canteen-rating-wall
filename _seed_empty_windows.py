# -*- coding: utf-8 -*-
"""给零数据的窗口补演示评分与评论（幂等：只处理一条评分都没有的窗口）

用法：
    python _seed_empty_windows.py <canteen.db 路径>

当前会补：四食堂 10 个窗口 + 一/二食堂的两个「自选餐」窗口。
数据全部是**演示数据**，口径与既有数据一致（均分 3.8~3.9，与前三食堂持平）。
"""
import os
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta

SEED = 20261024
RATINGS_PER_WINDOW = 12
POSTS_PER_WINDOW = 4

# 好评 / 中评 / 差评（{dish} 与 {price} 会替换成该窗口真实菜品）
GOOD = [
    "{dish}皮薄馅大，{price}块挺实在。",
    "现包的，{dish}咬开还有汤。",
    "{dish}这个价位在食堂算良心了。",
    "连着吃三天{dish}，没腻。",
    "阿姨给得多，{dish}一份就管饱。",
    "{dish}调味正，蘸醋更香。",
    "刚出锅的{dish}，热乎。",
]
MID = [
    "{dish}还行，皮稍微厚了点。",
    "味道正常，{dish}不算惊艳但稳。",
    "{dish}今天偏咸了一点。",
    "排队不算长，{dish}出得挺快。",
    "{dish}跟上次比馅少了些。",
]
BAD = [
    "{dish}这次馅有点少。",
    "等了十分钟，{dish}上来是温的。",
    "{dish}皮有点硬，可能是放久了。",
]
SPECIFIC = {
    "酸汤水饺": ["酸汤够味，天冷来一碗舒服。", "汤比饺子还好喝。"],
    "煎饺锅贴": ["底儿焦脆，趁热吃。", "锅贴一咬冒油，香。"],
    "熏酱凉菜拼": ["凉菜拼盘解腻，配饺子刚好。", "酱味够，量一般。"],
}
BUFFET = [
    "自选随便夹，二十块能吃撑。",
    "菜色偏少，吃久了有点腻。",
    "称重算钱，手一抖就超预算。",
    "荤菜补得慢，去晚了只剩素。",
    "米饭管够，这点好评。",
    "汤是免费的，还行。",
]


def pick_dates(n, rng):
    """最近 45 天，七成落在 10 月（保证能进本月榜）"""
    out = []
    today = date(2026, 10, 23)
    for _ in range(n):
        if rng.random() < 0.72:
            d = today - timedelta(days=rng.randint(0, 22))       # 10-01 ~ 10-23
        else:
            d = today - timedelta(days=rng.randint(24, 46))      # 09-07 ~ 09-29
        out.append(d)
    return out


def build_score_pool(n, rng):
    """构造 n 个分数，使整体均分恰好落在 3.85（与前三食堂 3.82~3.89 持平）

    比例 5星30% / 4星38% / 3星22% / 2星7% / 1星3% → 均分 3.85
    """
    ratio = [(5, 0.30), (4, 0.38), (3, 0.22), (2, 0.07), (1, 0.03)]
    pool = []
    for score, p in ratio:
        pool += [score] * int(round(n * p))
    while len(pool) < n:          # 四舍五入的零头用 4 星补
        pool.append(4)
    pool = pool[:n]
    rng.shuffle(pool)
    return pool


def main(db_path):
    rng = random.Random(SEED)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    anons = [r["id"] for r in conn.execute("SELECT id FROM anons ORDER BY id")]
    if not anons:
        sys.exit("anons 表为空，无法生成")

    empty = conn.execute("""
        SELECT w.id, w.canteen, w.floor, w.name, w.is_buffet
        FROM windows w
        WHERE w.status=1 AND NOT EXISTS (SELECT 1 FROM ratings r WHERE r.window_id=w.id)
        ORDER BY w.canteen, w.floor, w.win_no
    """).fetchall()

    if not empty:
        print("没有零评分窗口，无需处理")
        return

    print("待补窗口 %d 个：" % len(empty))
    for w in empty:
        print("  #%s 食堂%s %s楼 %s" % (w["id"], w["canteen"], w["floor"], w["name"]))

    r_add = p_add = d_add = 0
    score_pool = build_score_pool(len(empty) * RATINGS_PER_WINDOW, rng)
    score_i = 0
    for w in empty:
        wid = w["id"]
        dishes = [dict(r) for r in conn.execute(
            "SELECT id, name, price FROM dishes WHERE window_id=? AND status=1 ORDER BY id", (wid,))]
        if not dishes:
            print("  跳过 #%s（无菜品）" % wid)
            continue

        is_buffet = bool(w["is_buffet"])
        # ---------- 评分 ----------
        dates = pick_dates(RATINGS_PER_WINDOW, rng)
        used = set()
        for d in dates:
            ds = d.isoformat()
            pool = [a for a in anons if (a, ds) not in used]
            if not pool:
                continue
            anon = rng.choice(pool)
            used.add((anon, ds))
            score = score_pool[score_i]
            score_i += 1
            ts = "%s %02d:%02d:%02d" % (ds, rng.choice([7, 11, 12, 17, 18, 20]),
                                        rng.randint(0, 59), rng.randint(0, 59))
            cur = conn.execute(
                "INSERT OR IGNORE INTO ratings(anon_id, window_id, score, date, created_at) "
                "VALUES (?,?,?,?,?)", (anon, wid, score, ds, ts))
            r_add += cur.rowcount

        # ---------- 评论 ----------
        for i in range(POSTS_PER_WINDOW):
            d = pick_dates(1, rng)[0]
            ds = d.isoformat()
            anon = rng.choice(anons)
            if is_buffet:
                content = rng.choice(BUFFET)
                dish_id = None
            else:
                dish = rng.choice(dishes)
                special = SPECIFIC.get(w["name"])
                if special and rng.random() < 0.5:
                    content = rng.choice(special)
                else:
                    bucket = rng.choices([GOOD, MID, BAD], weights=[58, 28, 14])[0]
                    content = rng.choice(bucket).format(
                        dish=dish["name"], price=("%g" % dish["price"]))
                dish_id = dish["id"]
            ts = "%s %02d:%02d:%02d" % (ds, rng.choice([11, 12, 12, 17, 18]),
                                        rng.randint(0, 59), rng.randint(0, 59))
            conn.execute(
                "INSERT INTO posts(window_id, parent_id, dish_id, anon_id, content, created_at, status) "
                "VALUES (?,NULL,?,?,?,?,1)", (wid, dish_id, anon, content, ts))
            p_add += 1

        # ---------- 菜品点赞（少量） ----------
        for dish in rng.sample(dishes, min(2, len(dishes))):
            ds = pick_dates(1, rng)[0].isoformat()
            anon = rng.choice(anons)
            cur = conn.execute(
                "INSERT OR IGNORE INTO dish_ratings(anon_id, dish_id, vote, date, created_at) "
                "VALUES (?,?,1,?,?)", (anon, dish["id"], ds, ds + " 12:00:00"))
            d_add += cur.rowcount

    conn.commit()

    print("\n新增：评分 %d 条、评论 %d 条、菜品点赞 %d 条" % (r_add, p_add, d_add))
    print("\n=== 各食堂均分（补完后）===")
    for cid, a, n in conn.execute("""
            SELECT w.canteen, ROUND(AVG(r.score),2), COUNT(*)
            FROM ratings r JOIN windows w ON w.id=r.window_id
            GROUP BY w.canteen ORDER BY w.canteen"""):
        print("  食堂%s  均分 %-5s  %s 条" % (cid, a, n))
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法：python _seed_empty_windows.py <canteen.db>")
    main(sys.argv[1])
