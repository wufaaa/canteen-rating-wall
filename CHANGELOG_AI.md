# CHANGELOG_AI.md

> 修复对象：`食堂评分墙_当前目录_20261023(1).zip` 的副本（原包未动）
> 范围：**只改 AI 后端**。UI / CSS / 前端交互 / 商家端 / 打包 / 日志表 / `canteen.db` 全部未动。
> 日期：2026-10-24

## 改动文件清单

| 文件 | 改动 | 行数 |
|---|---|---|
| `ai_local.py` | 食堂名动态化、否定词处理、高蛋白硬约束、饺子品类、菜名命中、推荐多样性 | +113 / −14 |
| `app.py` | 只动 AI 段（`_ai_data_summary` ~ `/api/ai/stream`） | +180 / −58 |
| `_test_ai.py` | **新增**，9 条回归用例，可重复跑 | 新增文件 |
| `_seed_empty_windows.py` | **新增**，给零数据窗口补演示评分/评论（幂等） | 新增文件 |
| `canteen.db` | **仅追加** 144 条评分 / 48 条评论 / 24 条点赞（见第五节） | 数据 |

未改动：`teleagent_client.py`、`static/*`、`database.py`、`start.bat`、`requirements.txt`。
统一保持原文件的 LF 换行，diff 里没有整文件重排。

---

## P0-1 · `/api/ai/stream` 500 + 本地兜底

### 根因

1. `ai_local.py:10` 写死 `CN = ["一", "二", "三"]`，而库里 `windows.canteen` 最大是 **4**；
2. `ai_local.py:268` 用 `CN[r["canteen"] - 1]`，第 4 食堂 → `IndexError`；
3. `app.py:1222` 在 `gen()` **外面**调 `_ai_compact_prompt(c, q)`，异常直接冒到 Flask，SSE 还没开始就被打成 500，本地兜底根本没机会发出去。

### 改法

**`ai_local.py`**
- `CN` 改为 `CANTEEN_NAMES`（一~十）+ `canteen_name(n)`：超出范围退回阿拉伯数字，**任何输入都不抛异常**；
- `recommend()` 的 `loc` 改用 `canteen_name(r["canteen"])`。

**`app.py`**
- `_ai_data_summary()` / `_ai_data_summary_fast()` 里第二份硬编码 `cn = ["一","二","三"]` 全部删除，统一走 `ai_local.canteen_name()`（不再有两份真相）；
- `/api/ai/stream` 重写：
  - 本地兜底先算（`_local_fallback_items`），**先 yield `local`**，再考虑引擎；
  - `_ai_compact_prompt()` 包进 `try/except`，失败置 `prompt=None`，直接发 `local` + `done`；
  - `engine_available()`、`engine_stream()` 整段包 `try/except`，异常也发 `done` 而不是断流；
  - 引擎流结束但没收到 `done` 事件时补发 `done`；
  - 新增 `_local_fallback_items()`：本地引擎为空时按评分从库里取 Top3，**保证 `local` 事件永远有 3 条**；
  - 原来 `local_items` 为空会 `return err(...)`（400），现在改为兜底出 3 条。

> 事件名 `local` / `delta` / `done` 与 `engine` 字段值（`local`/`engine`/`teleagent`/`cloud`）**完全没变**，前端零改动。

---

## P0-2 · 「不辣」推荐辣菜

### 根因

1. `ai_local.py:17` 的 `辣|麻辣|香辣...` 正则会命中「**不**辣」里的「辣」；
2. 没有否定词处理，`intent` 里同时出现 `spicy` 和 `light`，理由会写成「清淡不腻、香辣过瘾」；
3. `高蛋白` 只是 `scene:diet` 的软加分（+45），不是硬约束，辣菜照样能进 Top3。

### 改法（`ai_local.py`）

- 新增 `NEG_SPICY = re.compile(r"(不|不要|别|少|微|没|无)\s*辣")`；
- `parse_intent()`：**先用 `NEG_SPICY.sub(" ", q)` 把否定短语整段剔除**，再跑 `INTENT_RULES`，并打 `intent["avoid_spicy"] = {True}`；
- 新增 `PROTEIN_DISH` 食材正则（鸡胸/牛肉/鱼/虾/蛋/豆腐/…，用 `蛋(?!糕)` 排除蛋糕），`_tag_dish()` 给命中菜品打 `nutrition: high_protein`；「高蛋白/增肌/健身/补蛋白」也直接触发；
- `recommend()` 在打分前做**硬过滤**：
  - 有 `avoid_spicy` 且菜带 `spicy` 标签 → 直接 `continue`，不参与排序；
  - 要 `high_protein` 且菜没有蛋白证据 → 直接 `continue`；
- `_score()` 兜底再判一次（`avoid_spicy` + `spicy` → `-999`），双保险；
- 放宽兜底逻辑：没有候选时**只放宽高蛋白，「不辣」仍然硬保留**；确实无解才退回按评分（避免"全被过滤就破功"）；
- 理由里加 `不辣/清淡`，且**不出现**香辣/麻辣。

---

## P0-3 · AI 数字未被数据库覆盖

### 根因

- `_parse_ai_items()` 只检查 `dish`，`price`/`score` 只做类型转换；
- `_attach_dish_info()` 按菜名 `LIKE` 回查，只**补** `dish_id/window_id/photo`，不**覆盖** AI 返回的价格/窗口/评分；
- 结果：AI 说 12 元、实际 16 元，前端照实显示 12 元。

### 改法（`app.py`）

- `_parse_ai_items()` 加 schema：`dish` 必填；`price` 限 `0~100`；`score` 限 `0~5`；越界或非数字置 `None`（`bool` 单独排除，避免 `True` 被当成 1）；
- `_attach_dish_info()` 重写：
  - 菜名**精确匹配**（原来是 `LIKE`，会误配），且要求 `dishes.status=1 AND windows.status=1`；
  - 同名菜优先取 AI 说的那个窗口；
  - **强制覆盖** `price` / `score` / `window` / `loc` / `intro` / `photo`，全部以数据库为准；
  - 菜名对不上 → **丢弃该条**，不再保留 AI 编的数据；
  - 最多取 3 条；
- 新增 `_finalize_ai_items(conn, items, q)`：`_attach_dish_info` + **不足 3 条用本地引擎补齐**；若 query 含否定词，还会把理由里的「辣」字句剔掉；
- 所有调用点（`/api/ai/recommend`、`/api/ai/quick` 云端通道、`_run_teleagent_job`、`_run_engine_job`、`/api/ai/stream`）统一改用 `_finalize_ai_items`；
- `_run_engine_job()` 增加 `q` 参数，用于补齐时保持约束一致。

---

## 没做的（明确声明）

- **后端多轮 `/api/ai/chat` 没做**。报告里标为「可选、不阻塞」，本次只做 3 个 P0。答辩**不要讲"多轮对话"**。
- 没加 `search_logs` / `recommend_logs` / `merchant_replies` / `prep_advice`，没改商家端，没换 Waitress、没打包 —— 均属报告 4.1「不能改」。
- 没改 `teleagent_client.py` 的 4397 协议。

---

## 五、追加改动：让一二三四食堂效果一致（博 10/24 授权）

原包里 **四食堂 10 个窗口、一/二食堂的两个「自选餐」窗口，一条评分都没有**。后果是：
榜单不显示（榜单是 `ratings JOIN windows`）、AI 推荐永远排不上（默认 3.5 分垫底）、
「想吃饺子」推出来是冬阴功汤粉。博授权「需要数据自己生成」，所以补了演示数据。

### 5.1 演示数据（`_seed_empty_windows.py`，幂等）

| 项 | 数量 |
|---|---|
| 补数据的窗口 | 12 个（四食堂 10 + 自选餐 2） |
| 新增评分 | 144 条（每窗口 12 条，散在 9/7–10/23） |
| 新增评论 | 48 条（每窗口 4 条，按窗口真实菜品写） |
| 新增菜品点赞 | 24 条 |

评分分布刻意对齐前三食堂：5星30% / 4星38% / 3星22% / 2星7% / 1星3%。

补完后各食堂均分：**一 3.90 / 二 3.82 / 三 3.85 / 四 3.83**，本月有评分的窗口 **72/72**。

> ⚠️ 这些是**演示数据**，答辩要如实说明（报告 4.2 也要求）。脚本幂等，重跑只处理「一条评分都没有」的窗口，不会重复灌。

### 5.2 「饺子」意图（`ai_local.py`）

原来 `INTENT_RULES` 里根本没有饺子类词，`DISH_TAG_RULES` 的 noodle 也只认「饺子」不认「水饺 / 蒸饺」。

- `INTENT_RULES` 增加 `饺子|水饺|蒸饺|煎饺|锅贴|馄饨|饨|盒子|包子|烧麦 → cat:dumpling`；
- `DISH_TAG_RULES` 增加独立的 `dumpling` 品类（**不并进 noodle**，否则「想吃饺子」会推出一堆米粉）；
- `TAG_ZH` 增加「饺子面点」。

### 5.3 菜名命中加权（`ai_local.py`）

学生直接点名时（「来份锅贴」），命中的那道菜要排前面：

- 整名命中 `+60`；片段命中（2~3 字，排除「想吃/来份/有点」等停用词）`+15×长度`；
- 结果：「来份锅贴」→ 素三鲜锅贴 / 牛肉锅贴 / 酸汤水饺，而不是冬阴功汤粉。

### 5.4 推荐多样性（`ai_local.py`）

原来「同一窗口最多 2 道」，一个高分窗口会占满 3 个名额。改成**两轮**：
第一轮每窗口最多 1 道，凑不满 3 条再放宽到 2 道。

### 5.5 实测覆盖

| 查询 | 结果 |
|---|---|
| 想吃饺子 | 酸汤饺子+拌菜套餐 / 饺子+小米粥套餐 / 熏酱+饺子套餐（四食堂） |
| 来份锅贴 | 素三鲜锅贴（三食堂）/ 牛肉锅贴（四食堂）/ 酸汤水饺（四食堂） |
| 想吃馄饨 | 三鲜大馄饨（二食堂）/ 酸汤水饺（四食堂）/ 粥+包子套餐（一食堂） |
| 想吃面 | 二食堂 / 一食堂 / 三食堂 |

16 条常见查询跑下来，四个食堂出现次数：一 11 / 二 16 / 三 15 / 四 6。
四食堂只卖饺子和凉菜，只在饺子类查询里出现，这是菜单决定的，不是权重问题。

### 5.6 一个已知遗留（**不是这次引入的**）

`recommend()` 原有的入围门槛是「菜品命中 **或** 评论命中」，评论命中太宽松，会出现
「想吃素的」推出「荤菜冒菜套餐」、「今天想吃点甜的」推出「冬阴功汤粉」。
这段逻辑是原包就有的，本次未改（改它会影响全部排序，超出 3 个 P0 范围）。要不要收紧，另说。

## 兼容性

- 事件名、`engine` 字段、返回结构（`items[].dish/window/loc/price/score/reason/intro/dish_id/window_id/photo`）与原来一致，**前端不用改**。
- 本地兜底纯 Python + SQLite，跨平台可用。
- 未新增任何第三方依赖（`requirements.txt` 仍是 `flask>=3.0`）。
