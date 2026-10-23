# -*- coding: utf-8 -*-
"""本地兜底推荐引擎 —— TeleAgent 不可用时离线推荐（纯规则，零依赖）

对 180 道菜打多维标签（温度/口味/品类/场景/价位），把学生的一句话解析成意图标签，
按「标签匹配 + 窗口评分 + 月榜排名 + 价格」综合打分取 Top3，理由可解释。
"""
import re
import sqlite3

CN = ["一", "二", "三"]

# ------------------------------------------------------------ 意图词典：口语 -> 标签
INTENT_RULES = [
    # (正则, 命中后要求的标签集合/排除的标签集合)
    (r"热|暑|降温|凉快|冰|清爽|解腻|渴", {"temp": "cool"}),
    (r"冷|寒|暖|胃寒|降温后|冬天|下雪|冻", {"temp": "hot"}),
    (r"辣|无辣不欢|过瘾|麻辣|香辣|变态辣", {"taste": "spicy"}),
    (r"清淡|油腻|腻|不想油|少油|养生|清淡点", {"taste": "light"}),
    (r"甜|甜品|糖水|解馋|下午茶|奶茶", {"taste": "sweet"}),
    (r"酸|开胃|没胃口|没食欲|食欲不振|胃口", {"taste": "sour"}),
    (r"饿|饿疯|饿死|军训|运动完|管饱|吃饱|吃撑|大量|大份|碳水", {"scene": "filling"}),
    (r"减[肥脂]|轻食|低卡|热量|卡路里|健身|掉秤", {"scene": "diet"}),
    (r"宵夜|夜宵|晚上吃|深夜|夜谈|看球", {"scene": "latenight"}),
    (r"早[上餐]|早八|起床|豆浆|包子|过早", {"scene": "breakfast"}),
    (r"穷|没钱|吃土|便宜|省钱|穷吃|特价|低消", {"scene": "cheap"}),
    (r"请客|聚餐|改善|犒劳|庆祝|生日", {"scene": "rich"}),
    (r"面|粉|拉面|米线|嗦", {"cat": "noodle"}),
    (r"饭|盖浇|拌饭|炒饭", {"cat": "rice"}),
    (r"汤|粥|喝的|暖汤", {"cat": "soup"}),
    (r"肉|吃肉|牛肉|鸡肉|羊肉|猪肉|荤", {"cat": "meat"}),
    (r"素|蔬菜|青菜|不吃肉", {"cat": "veggie"}),
]

# ------------------------------------------------------------ 菜品标签规则（菜名/简介/窗口名关键词）
DISH_TAG_RULES = [
    # cool：凉的
    (r"凉|冰|冷面|凉拌|沙拉|捞|双皮奶|糖水|杨枝甘露|汤圆|雪糕|刨冰|果汁|西瓜|水果|酸奶|三明治|轻食|寿司|果切|鲜果", "temp", "cool"),
    # hot：热乎的
    (r"汤|粥|热|煨|炖|烫|砂锅|石锅|泡馍|锅巴|现出锅|热干|蒸|焖|烩", "temp", "hot"),
    # spicy：辣的
    (r"辣|麻|椒|麻辣|香锅|冒菜|螺蛳|水煮|剁椒|红油|酸辣|变态辣|夫妻肺片|打抛", "taste", "spicy"),
    # light：清淡
    (r"清淡|蒸蛋|粥|汤面|清汤|素|轻食|沙拉|藜麦|低卡|低油|低盐|白切|清炖|营养", "taste", "light"),
    # sweet：甜
    (r"甜|糖|奶|芝士|蛋糕|吐司|牛角|点心|叉烧|蜜汁|豆沙|杨梅|芒果|椰|巧克力|双皮奶|杨枝甘露|汤圆|鲜花饼|菠萝", "taste", "sweet"),
    # sour：酸开胃
    (r"酸|醋|番茄|柠檬|酸菜|酸笋|冬阴功|酸汤|杨梅|山楂", "taste", "sour"),
    # filling：管饱
    (r"大份|管饱|加面|套餐|自助|免费续|量大|双人|一锅出|分享|管够|饭|面|粉|馍|包|饺子|馄饨|炒饭|盖浇|拌饭", "scene", "filling"),
    # diet：轻食减脂
    (r"轻食|沙拉|藜麦|减脂|低卡|高蛋白|粗粮|全麦|水煮|蒸|素|酸奶|果切|轻卡|营养师|卡路里", "scene", "diet"),
    # latenight：适合宵夜
    (r"烧烤|烤串|小龙虾|炸鸡|螺蛳粉|麻辣烫|冒菜|夜宵|泡面|汉堡|薯条|可乐|啤酒", "scene", "latenight"),
    # breakfast：适合早餐
    (r"粥|包子|豆浆|油条|吐司|贝果|咖啡|牛奶|肠粉|早点|蒸饺|小笼|生煎|手抓饼|蛋饼|蛋酒|热干面|汤包|点心", "scene", "breakfast"),
    # noodle：面食粉类
    (r"面|粉|米线|拉面|热干|螺蛳|馄饨|饺子|河粉|肠粉|拌面|炒面|泡馍|宽粉", "cat", "noodle"),
    # rice：米饭类
    (r"饭|盖浇|拌饭|炒饭|卤肉饭|猪脚饭|蛋包饭|套餐|黄焖|烧腊|烧味|叉烧", "cat", "rice"),
    # soup：汤粥类
    (r"汤|粥|煨|砂锅|羹", "cat", "soup"),
    # meat：肉食
    (r"牛肉|鸡肉|鸡腿|羊肉|猪肉|肉|排骨|鸡|鱼|虾|蟹|牛腩|叉烧|烧鸭|肥牛|脑花|田鸡|鹅", "cat", "meat"),
    # veggie：素食
    (r"素|豆腐|蔬菜|时蔬|菌菇|罗汉|藜麦|沙拉|锅贴(?!肉)|凉拌|藕|海带|豆芽", "cat", "veggie"),
]

TAG_ZH = {
    "cool": "清凉解暑", "hot": "热乎暖胃", "spicy": "香辣过瘾", "light": "清淡不腻",
    "sweet": "甜蜜解馋", "sour": "酸爽开胃", "filling": "管饱扛饿", "diet": "轻食低卡",
    "latenight": "适合宵夜", "breakfast": "适合早餐", "cheap": "高性价比", "rich": "犒劳一下",
    "noodle": "面食", "rice": "米饭", "soup": "汤粥", "meat": "肉食", "veggie": "素食",
}

# ------------------------------------------------------------ 评论信号（实时读帖）
COMMENT_GOOD = ["好评", "绝了", "好吃", "推荐", "安利", "暖心", "救星", "在线", "性价比",
                "稳", "不错", "多给", "分量超足", "出餐快", "排队不算长", "烫呼呼"]
COMMENT_BAD = ["油放得有点猛", "队伍基本不动", "慎选", "咸了", "贵了", "卖完了", "对付",
               "一般", "有点凉了", "约等于没有", "踩雷"]
COMMENT_INTENT_KEYWORDS = {
    "cool": ["凉", "冰", "清爽", "解暑", "解腻"],
    "hot": ["热乎", "烫", "暖", "现出锅"],
    "spicy": ["辣", "麻", "过瘾"],
    "light": ["清淡", "不腻", "清爽"],
    "sweet": ["甜"],
    "sour": ["酸", "开胃"],
    "filling": ["分量", "管饱", "多给", "量大"],
    "diet": ["轻食", "低卡", "减脂"],
    "latenight": ["宵夜", "夜宵"],
    "breakfast": ["早餐", "早点"],
    "cheap": ["便宜", "性价比", "学生价"],
    "noodle": ["面", "粉"],
    "rice": ["饭"],
    "soup": ["汤", "粥"],
    "meat": ["肉"],
    "veggie": ["素", "蔬菜"],
}


def _comment_signals(conn, intent):
    """每窗口：评论口碑分（好评-差评）+ 评论对当前意图的关键词佐证"""
    posts_by_win = {}
    for p in conn.execute("SELECT window_id, content FROM posts WHERE status=1"):
        posts_by_win.setdefault(p["window_id"], []).append(p["content"])
    out = {}
    for wid, contents in posts_by_win.items():
        blob = " ".join(contents)
        good = sum(blob.count(w) for w in COMMENT_GOOD)
        bad = sum(blob.count(w) for w in COMMENT_BAD)
        hits = set()
        for vals in intent.values():
            for v in vals:
                if any(k in blob for k in COMMENT_INTENT_KEYWORDS.get(v, [])):
                    hits.add(v)
        out[wid] = {"sent": good - bad, "hits": hits}
    return out


def _tag_dish(name, intro, window_name, price):
    blob = "%s %s %s" % (name, intro, window_name)
    tags = {}
    for pat, dim, val in DISH_TAG_RULES:
        if re.search(pat, blob):
            tags.setdefault(dim, set()).add(val)
    if price <= 10:
        tags.setdefault("scene", set()).add("cheap")
    if price >= 18:
        tags.setdefault("scene", set()).add("rich")
    return tags


def parse_intent(q):
    """把学生的话解析成意图标签 dict{dim: set(val)}"""
    intent = {}
    for pat, want in INTENT_RULES:
        if re.search(pat, q):
            for dim, val in want.items():
                intent.setdefault(dim, set()).add(val)
    # 数字预算：「10块」「15元」「20块钱」→ budget
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:块|元)", q)
    if m:
        try:
            intent["budget"] = {float(m.group(1))}
        except ValueError:
            pass
    return intent


def _score(dish_tags, intent, avg_score, rank_bonus, price):
    """综合打分：意图命中是决定性因素，评分/榜单做排序微调"""
    s = 0.0
    matched = []
    missed = 0
    budget = None
    for dim, want_vals in intent.items():
        if dim == "budget":
            budget = min(want_vals)
            continue
        got = dish_tags.get(dim, set())
        hit = want_vals & got
        if hit:
            s += 45 * len(hit)
            matched += [TAG_ZH.get(v, v) for v in sorted(hit)]
        else:
            missed += 1
    # 反向惩罚：要凉的给了滚烫的（反之轻罚，热菜冷吃还能接受）
    if "temp" in intent:
        if "cool" in intent["temp"] and "hot" in dish_tags.get("temp", set()):
            s -= 35
        if "hot" in intent["temp"] and "cool" in dish_tags.get("temp", set()):
            s -= 15
    # 明确预算：预算内加分，超预算按超出金额重罚
    if budget:
        if price <= budget:
            s += 25
            matched.append("预算内")
        elif price <= budget * 1.15:
            s += 5
        else:
            s -= (price - budget) * 6
    s -= missed * 8                 # 意图越多未命中越靠后
    s += (avg_score - 3.0) * 10     # 评分权重
    s += rank_bonus                 # 月榜加权
    if budget is None and 8 <= price <= 16:
        s += 2                      # 学生价位友好
    return s, matched


def recommend(conn, q, limit=3):
    """主入口：conn 为食堂 sqlite 连接；返回推荐列表（与 AI 输出同构）

    数据每次实时查库：菜品/价格/评分/月榜/学生评论。"""
    intent = parse_intent(q)
    win_comment = _comment_signals(conn, intent)
    rows = conn.execute("""
        SELECT w.id AS wid, w.canteen, w.floor, w.win_no, w.name AS wname,
               d.id AS did, d.name AS dname, d.price, d.intro,
               (SELECT ROUND(AVG(r.score),2) FROM ratings r WHERE r.window_id=w.id) AS avg_score
        FROM dishes d JOIN windows w ON w.id=d.window_id
        WHERE d.status=1 AND w.status=1
    """).fetchall()

    # 月榜排名（当月评分排名 map）
    month = conn.execute(
        "SELECT strftime('%Y-%m', MAX(date)) FROM ratings").fetchone()[0]
    ranks = {}
    if month:
        for i, r in enumerate(conn.execute("""
                SELECT w.id AS wid, AVG(r.score) AS a FROM ratings r
                JOIN windows w ON w.id=r.window_id
                WHERE strftime('%Y-%m', r.date)=? GROUP BY w.id ORDER BY a DESC
            """, (month,))):
            ranks[r["wid"]] = max(0, 20 - i)  # 第1名+20，线性衰减

    scored = []
    for r in rows:
        tags = _tag_dish(r["dname"], r["intro"], r["wname"], r["price"])
        avg = r["avg_score"] or 3.5
        s, matched = _score(tags, intent, avg, ranks.get(r["wid"], 0), r["price"])
        # 评论信号：口碑分 + 评论对意图的佐证
        wc = win_comment.get(r["wid"])
        if wc:
            s += max(-4, min(4, wc["sent"]))
            if wc["hits"]:
                s += 8 * len(wc["hits"])
        # 有明确意图时：至少命中一个意图维度（菜品标签或评论佐证）才有资格入围
        if intent:
            dish_hit = any(vals & tags.get(dim, set()) for dim, vals in intent.items())
            comment_hit = bool(wc and wc["hits"])
            if not (dish_hit or comment_hit):
                continue
        else:
            matched = ["高分热推"]
        scored.append((s, r, matched, tags))
    if not scored:  # 全被过滤（极端口语），回落全量按评分+榜单
        for r in rows:
            tags = _tag_dish(r["dname"], r["intro"], r["wname"], r["price"])
            avg = r["avg_score"] or 3.5
            scored.append(((avg - 3.0) * 10 + ranks.get(r["wid"], 0), r, ["高分热推"], tags))
    scored.sort(key=lambda x: -x[0])
    # 同一窗口最多保留 2 道，保证推荐多样性
    picked, win_count = [], {}
    for item in scored:
        w = item[1]["wid"]
        if win_count.get(w, 0) >= 2:
            continue
        win_count[w] = win_count.get(w, 0) + 1
        picked.append(item)
        if len(picked) >= limit:
            break
    scored = picked

    out = []
    for s, r, matched, tags in scored[:limit]:
        reason_bits = []
        if matched:
            reason_bits.append("符合「%s」" % "、".join(matched[:2]))
        if r["price"] <= 10:
            reason_bits.append("¥%g 学生价" % r["price"])
        reason_bits.append("窗口评分 %.1f" % (r["avg_score"] or 3.5))
        wc = win_comment.get(r["wid"])
        if wc and wc["sent"] >= 2:
            reason_bits.append("评论口碑佳")
        if r["intro"]:
            reason_bits.append(r["intro"][:14])
        out.append({
            "dish": r["dname"], "window": r["wname"],
            "loc": "%s食堂%d楼" % (CN[r["canteen"] - 1], r["floor"]),
            "price": round(r["price"], 1),
            "score": round(r["avg_score"] or 3.5, 2),
            "reason": "，".join(reason_bits)[:40],
            "intro": (r["intro"] or "")[:60],
            "dish_id": r["did"], "window_id": r["wid"],
        })
    return out


if __name__ == "__main__":
    conn = sqlite3.connect("canteen.db")
    conn.row_factory = sqlite3.Row
    for q in ["今天有点热，想吃点凉的", "想吃辣的过过瘾", "最近在减肥，想吃低卡的", "没胃口，想吃点开胃的", "穷学生，10块钱吃啥"]:
        print("Q:", q)
        for d in recommend(conn, q):
            print("   -> %(dish)s @%(window)s %(loc)s ¥%(price)s 评分%(score)s | %(reason)s" % d)
        print()
