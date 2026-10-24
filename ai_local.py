# -*- coding: utf-8 -*-
"""本地兜底推荐引擎 —— TeleAgent 不可用时离线推荐（纯规则，零依赖）

对 180 道菜打多维标签（温度/口味/品类/场景/价位），把学生的一句话解析成意图标签，
按「标签匹配 + 窗口评分 + 月榜排名 + 价格」综合打分取 Top3，理由可解释。
"""
import re
import sqlite3

# 食堂序号 -> 中文名。不再写死 3 个：库里已经有 4 个食堂，
# 原来 CN[r["canteen"]-1] 在第 4 食堂直接 IndexError，把 /api/ai/stream 打成 500。
CANTEEN_NAMES = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
CN = CANTEEN_NAMES  # 兼容旧引用


def canteen_name(n):
    """食堂序号转中文名；超出已知范围退回阿拉伯数字，任何输入都不抛异常。"""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "食堂"
    if 1 <= n <= len(CANTEEN_NAMES):
        return CANTEEN_NAMES[n - 1]
    return "%d" % n

# ------------------------------------------------------------ 意图词典：口语 -> 标签
INTENT_RULES = [
    # (正则, 命中后要求的标签集合/排除的标签集合)
    # 「天热」是要凉的，「想吃热的」是要热的 —— 不能都按「热」字一刀切
    (r"天热|好热|太热|有点热|热死|暑|降温|凉|冰|清爽|解腻|渴", {"temp": "cool"}),
    (r"冷|寒|暖|胃寒|冬天|下雪|冻|想吃热|来点热|热的|热乎|热汤|热面", {"temp": "hot"}),
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
    (r"饺子|水饺|蒸饺|煎饺|锅贴|馄饨|饨|盒子|包子|烧麦", {"cat": "dumpling"}),
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
    (r"面|粉|米线|拉面|热干|螺蛳|馄饨|饨|饺子|饺|河粉|肠粉|拌面|炒面|泡馍|宽粉", "cat", "noodle"),
    # dumpling：饺子面点（和面食分开，避免「想吃饺子」推出一堆米粉）
    (r"饺子|水饺|蒸饺|煎饺|锅贴|馄饨|饨|盒子|包子|烧麦|饺", "cat", "dumpling"),
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
    "dumpling": "饺子面点",
    "high_protein": "高蛋白",
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


# ------------------------------------------------------------ 差评归类（避雷）
# 只对已经命中 COMMENT_BAD 的帖子做归类，避免「分量超足」被误判成「分量少」
WARN_RULES = [
    (r"排队|队伍|等(了|快)|人多|挤", "排队久"),
    (r"分量|量少|没给够|少得|太少|缩水|对付一口", "分量偏少"),
    (r"咸|淡|油放|腻|没味|寡淡", "口味不稳"),
    (r"贵|涨价|不值|性价比低", "价格偏高"),
    (r"卖完|没了|售罄", "容易售罄"),
    (r"凉了|温的|不热|凉透", "出餐偏凉"),
    (r"态度|爱答不理|脸色", "服务一般"),
]


def window_warnings(conn):
    """按窗口汇总差评标签 -> {window_id: [tag, ...]}（确定性规则，不经过模型）"""
    out = {}
    for p in conn.execute("SELECT window_id, content FROM posts WHERE status=1"):
        text = p["content"] or ""
        if not any(k in text for k in COMMENT_BAD):
            continue
        for pat, tag in WARN_RULES:
            if re.search(pat, text):
                bucket = out.setdefault(p["window_id"], [])
                if tag not in bucket:
                    bucket.append(tag)
    return out


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
    # 高蛋白只认菜名/简介里的食材证据，不拿窗口名凑
    if PROTEIN_DISH.search("%s %s" % (name, intro)):
        tags.setdefault("nutrition", set()).add("high_protein")
    if price <= 10:
        tags.setdefault("scene", set()).add("cheap")
    if price >= 18:
        tags.setdefault("scene", set()).add("rich")
    return tags


# ------------------------------------------------------------ 否定词与高蛋白
# 「不辣」「不要辣」「少辣」「微辣」里的「辣」会被 INTENT_RULES 的 /辣/ 命中，
# 结果学生说「不辣」反而推麻辣豆腐。所以先剥离否定短语，再解析意图。
NEG_SPICY = re.compile(r"(不|不要|别|少|微|没|无)\s*辣")

# 高蛋白必须有食材证据，不能只靠 scene:diet 软加分
PROTEIN_DISH = re.compile(
    r"鸡胸|鸡腿|鸡排|鸡块|牛肉|牛腩|肥牛|羊肉|里脊|瘦肉|排骨|猪蹄|鱼|虾|蟹|"
    r"蛋(?!糕)|豆腐|豆干|豆皮|腐竹|牛奶|酸奶|鸡|鸭|鹅|肉")


def parse_intent(q):
    """把学生的话解析成意图标签 dict{dim: set(val)}"""
    intent = {}
    avoid_spicy = bool(NEG_SPICY.search(q))
    q2 = NEG_SPICY.sub(" ", q)          # 先把「不辣」整段从原句拿掉
    for pat, want in INTENT_RULES:
        if re.search(pat, q2):
            for dim, val in want.items():
                intent.setdefault(dim, set()).add(val)
    if avoid_spicy:
        intent["avoid_spicy"] = {True}
    if PROTEIN_DISH.search(q2) or re.search(r"高蛋白|增肌|健身|补蛋白", q2):
        intent.setdefault("nutrition", set()).add("high_protein")
    # 数字预算：「10块」「15元」「20块钱」→ budget
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:块|元)", q2)
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
    # 硬约束：说「不辣」就不能出现辣菜（哪怕同时说了「麻辣」也以不辣优先）
    if intent.get("avoid_spicy") and "spicy" in dish_tags.get("taste", set()):
        return -999, []
    for dim, want_vals in intent.items():
        if dim == "budget":
            budget = min(want_vals)
            continue
        if dim == "avoid_spicy":
            continue                    # 已在上面做硬过滤，不参与加分
        if dim == "nutrition":
            if want_vals & dish_tags.get("nutrition", set()):
                s += 30
                matched.append("高蛋白")
            else:
                missed += 1
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


STOP_GRAMS = {"想吃", "来份", "来个", "想要", "吃点", "有点", "一份", "今天", "什么",
              "推荐", "帮我", "现在", "一些", "我想", "觉得", "可以", "一点", "的话"}


def _name_hit(q, bare):
    """学生话里有没有直接点名这道菜；返回命中片段长度（9=整名命中，0=没命中）"""
    if len(bare) >= 2 and bare in q:
        return 9
    best = 0
    for n in (3, 2):
        for i in range(len(q) - n + 1):
            seg = q[i:i + n]
            if seg in STOP_GRAMS:
                continue
            if seg in bare:
                best = max(best, n)
    return best


def recommend(conn, q, limit=3):
    """主入口：conn 为食堂 sqlite 连接；返回推荐列表（与 AI 输出同构）

    数据每次实时查库：菜品/价格/评分/月榜/学生评论。"""
    intent = parse_intent(q)
    win_comment = _comment_signals(conn, intent)
    warns = window_warnings(conn)
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

    # 硬约束：不辣 / 高蛋白 / 预算。三档放宽，先松软约束，最后才松预算
    budget_cap = min(intent["budget"]) if "budget" in intent else None
    semantic = {k: v for k, v in intent.items() if k not in ("budget", "avoid_spicy")}

    def _pass(use_protein, use_budget):
        out = []
        for r in rows:
            tags = _tag_dish(r["dname"], r["intro"], r["wname"], r["price"])
            if intent.get("avoid_spicy") and "spicy" in tags.get("taste", set()):
                continue
            if (use_protein and "high_protein" in intent.get("nutrition", set())
                    and "high_protein" not in tags.get("nutrition", set())):
                continue
            if use_budget and budget_cap and r["price"] > budget_cap:
                continue
            avg = r["avg_score"] or 3.5
            s, matched = _score(tags, intent, avg, ranks.get(r["wid"], 0), r["price"])
            # 学生直接点名了菜名（「来份锅贴」）：这道菜本身要排前面
            bare = re.sub(r"[（(].*?[)）]", "", r["dname"]).strip()
            hit = _name_hit(q, bare)
            if hit:
                s += 60 if hit == 9 else 15 * hit
                matched = ["就是这道"] + matched
            wc = win_comment.get(r["wid"])
            if wc:
                s += max(-4, min(4, wc["sent"]))
                if wc["hits"]:
                    s += 8 * len(wc["hits"])
            # 有语义意图时：至少命中一个维度（菜品标签或评论佐证）才入围
            if semantic:
                dish_hit = any(vals & tags.get(dim, set()) for dim, vals in semantic.items())
                comment_hit = bool(wc and wc["hits"])
                if not (dish_hit or comment_hit):
                    continue
            else:
                matched = ["高分热推"]
            out.append((s, r, matched, tags))
        return out

    scored = _pass(True, True)
    if not scored:                      # 放宽高蛋白，预算仍硬
        scored = _pass(False, True)
    if not scored:                      # 再放宽预算
        scored = _pass(False, False)
    if not scored:  # 最后兜底：确实没有任何菜满足约束，退回按评分+榜单
        for r in rows:
            tags = _tag_dish(r["dname"], r["intro"], r["wname"], r["price"])
            avg = r["avg_score"] or 3.5
            scored.append(((avg - 3.0) * 10 + ranks.get(r["wid"], 0), r, ["高分热推"], tags))
    scored.sort(key=lambda x: -x[0])
    # 没有明确需求（「今天吃啥」）时，别让三条都是主食：
    # 按「主食 / 汤 / 菜」三组轮转重排，凑成一顿饭
    if not intent:
        def _group(tags):
            cats = tags.get("cat", set())
            tastes = tags.get("taste", set())
            if cats & {"rice", "noodle", "dumpling"}:
                return 0                       # 主食
            if "soup" in cats:
                return 1                       # 汤
            if cats & {"meat", "veggie"}:
                return 2                       # 菜
            if "sweet" in tastes:
                return 3                       # 甜品：只有凑不出饭才用
            return 2

        groups = {}
        for item in scored:
            groups.setdefault(_group(item[3]), []).append(item)
        reordered = []
        # 先把 主食/汤/菜 轮转排完，甜品垫在最后
        while groups.get(0) or groups.get(1) or groups.get(2):
            for g in (0, 1, 2):
                if groups.get(g):
                    reordered.append(groups[g].pop(0))
        reordered += groups.get(3, [])
        scored = reordered
    # 多样性：先保证每个窗口最多 1 道，凑不满再放宽到 2 道（避免一个窗口占满 3 个名额）
    picked, win_count, taken = [], {}, set()
    for cap in (1, 2):
        for item in scored:
            if len(picked) >= limit:
                break
            if id(item) in taken:
                continue
            w = item[1]["wid"]
            if win_count.get(w, 0) >= cap:
                continue
            win_count[w] = win_count.get(w, 0) + 1
            taken.add(id(item))
            picked.append(item)
        if len(picked) >= limit:
            break
    scored = picked

    out = []
    for s, r, matched, tags in scored[:limit]:
        reason_bits = []
        if intent.get("avoid_spicy"):
            reason_bits.append("不辣/清淡")
        if not intent:
            # 没明确需求时不要说「符合高分热推」，换成能看懂的依据
            if ranks.get(r["wid"], 0) >= 18:
                reason_bits.append("本月榜前列")
        elif matched:
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
            "loc": "%s食堂%d楼" % (canteen_name(r["canteen"]), r["floor"]),
            "price": round(r["price"], 1),
            "score": round(r["avg_score"] or 3.5, 2),
            "reason": "，".join(reason_bits)[:40],
            "intro": (r["intro"] or "")[:60],
            "dish_id": r["did"], "window_id": r["wid"],
            "warn": "、".join(warns.get(r["wid"], [])[:2]),
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
