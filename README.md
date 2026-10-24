# 食堂评分墙 · Canteen Rating Wall

> 一个为大学食堂做的**匿名评分社区**：学生每天能匿名给窗口打分、发带图的美食帖，榜单把当月最受欢迎的窗口推上「C 位」，并自动生成可分享的月度海报。手机 / 电脑双端适配，开箱即用，零外部依赖。

---

## ✨ 功能特性

- **AI 点菜助手**：一句话说想吃啥（如「今天有点热，想吃点凉的」），由本机 TeleAgent 引擎结合菜品、评分、月榜和学生评论推荐，每道菜带**推荐理由**和**菜品介绍**；结果**流式输出**（推理过程实时滚动），通常 4~10 秒。桌面端未运行时自动切换离线标签引擎兜底，功能永不掉线。数据每次实时查库，商家改菜、学生新发评论，下一次提问立刻生效。
- **C 位榜单**：按当月平均分实时排名，第一名独占一张大卡片，其余分两列展示，一屏看完 30+ 个窗口。
- **月度海报区**：自动取出上月第一名，生成可直接转发到班级群 / 朋友圈的「月度最佳窗口」海报。
- **匿名打分**：学生免注册，系统自动分配一个随机昵称；每人每天最多打 3 次分，防刷分。
- **美食帖 + 配图**：可以给某个窗口发带照片的帖子（吐槽 / 安利都行），支持回复、点赞、举报。
- **商家后台**：每个窗口一个商家账号，能看自家评分、上传菜品图、回复学生帖子、重置登录口令。
- **管理员后台**：统一账号，可管理窗口、重置商家口令、处理举报、撤下不当帖子。
- **双端适配**：手机用底部导航栏，电脑端榜单自动分两列、信息密度更高。
- **零依赖运维**：Flask + SQLite，纯前端无构建步骤，一个 `python app.py` 就能跑。

---

## 🧱 技术栈

| 层 | 选型 |
|----|------|
| 后端 | Python 3 + Flask |
| 数据库 | SQLite（WAL 模式，自带并发保护） |
| 前端 | 原生 HTML / CSS / JavaScript（无框架、无打包） |
| AI 推理 | 本机 TeleAgent 引擎直连（`127.0.0.1:4397`，OpenCode 兼容 API + SSE 流式） + 离线标签引擎兜底 |
| 部署 | 任意支持 Python 的环境；也可一键发布到云端 |

---

## 🚀 快速开始

环境要求：Python 3.8 及以上。

**Windows 最省事**：双击 `start.bat` —— 自动建虚拟环境、装依赖、起服务、等服务就绪后自动打开浏览器。

**手动启动**：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动（首次启动会自动建库并写入演示数据）
python run.py          # 推荐：起服务并自动打开浏览器
# 或
python app.py          # 只起服务，自己开浏览器

# 3. 浏览器打开
#    本机：  http://127.0.0.1:5001
#    局域网：设 HOST=0.0.0.0 环境变量后重新运行
```

> ⚠️ **双击 `static/index.html` 是打不开的**（一片空白）。
> 这个项目是 Flask 应用，页面必须由后端 `http://127.0.0.1:5001` 提供；
> `index.html` 里引用的是 `/style.css`、`/app.js` 这样的绝对路径，直接从硬盘打开会全部加载失败。
> 必须先启动服务，再访问 `127.0.0.1:5001`。

---

## 🔑 默认账号（演示用）

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin@2026` |
| 商家（示例） | `c1-1-01` | `shop123456` |

> ⚠️ **安全提醒**：以上均为演示默认口令，仓库里的演示数据也是虚构的。
> **公网部署前务必改掉**：
> - 管理员：设环境变量 `ADMIN_PASSWORD=你的强口令` 后删掉 `canteen.db` 重启，或在后台「修改密码」里改；
> - 商家口令：登录管理员后台，对每个窗口点「重置商家口令」即可生成新密码。

---

## 📁 项目结构

```
canteen/
├── app.py                # Flask 后端：接口、鉴权、页面路由、AI 推荐接口
├── teleagent_client.py   # TeleAgent 桥接：调本机桌面端智能体（仅 Windows）
├── ai_local.py           # 离线标签推荐引擎（兜底，跨平台）
├── database.py           # 建库、种子数据、时间/时区工具
├── static/               # 前端（无构建）
│   ├── index.html
│   ├── app.js
│   └── style.css
├── uploads/              # 演示菜品图与帖子配图（已随仓库提供）
├── tool.py               # 版本管理：save / rollback / db 快照
├── requirements.txt
├── start.bat             # Windows 一键启动（双击即可）
├── run.py                # 启动器：查依赖 -> 起服务 -> 自动开浏览器
└── README.md
```

`canteen.db` 随仓库提供（含演示数据，开箱即用）；`secret.key`、`backups/` 不入库——密钥每台机器自行生成。

---

## ⚙️ 配置项（环境变量）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `5001` | 监听端口 |
| `HOST` | `0.0.0.0` | 监听地址（`127.0.0.1` 仅本机） |
| `ADMIN_PASSWORD` | `admin@2026` | 管理员口令；设置后下次建库生效 |
| `AI_ENGINE_MODEL` | `chat-lite` | TeleAgent 引擎模型档位（`chat-lite` / `chat-pro` / `chat-flagship`） |
| `AI_ENGINE_PROVIDER` | `NewApi` | TeleAgent 引擎 provider 名 |

---

## 🛠 版本与数据管理

`tool.py` 提供本地版本快照（与 git 互补，git 管代码、它管数据库）：

```bash
python tool.py save "改了榜单样式"   # 提交代码 + 打标签 + 备份数据库
python tool.py list                  # 看历史版本
python tool.py rollback v20261022-xxx # 回退代码到某版本
python tool.py db                    # 列出数据库快照
python tool.py dbrestore db-xxx.db   # 恢复某份数据库
```

---

## 📡 接口概览（RESTful JSON）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 学生 / 商家 / 管理员登录 |
| POST | `/api/ai/stream` | AI 点菜（SSE 流式）：本地秒回 + 引擎流式 + 最终结构化推荐 |
| POST | `/api/ai/quick` | AI 点菜（非流式）：本地秒回 + 后台升级任务 |
| GET  | `/api/leaderboard` | 当月榜单 + 上月第一名 |
| GET  | `/api/windows` | 窗口列表 |
| GET  | `/api/windows/<id>` | 窗口详情与菜品 |
| POST | `/api/rate` | 匿名打分（需学生身份，每日限 3 次） |
| POST | `/api/posts` | 发帖（可带图） |
| POST | `/api/posts/<id>/reply` | 回复 |
| POST | `/api/posts/<id>/like` | 点赞 |
| POST | `/api/posts/<id>/report` | 举报 |
| 管理员 / 商家 | `/api/admin/*`、`/api/merchant/*` | 后台管理 |

---

## 🤖 AI 点菜助手工作原理

学生输入一句话后，后端按以下优先级给出推荐：

1. **TeleAgent 引擎直连（首选，仅 Windows 本机）**
   `teleagent_client.py` 连接 TeleAgent 桌面端内置的 OpenCode 兼容引擎（`127.0.0.1:4397`），
   用 `POST /session/{id}/message` 同步执行，并订阅 `GET /event` 的 SSE 事件流取回正文。
   - **免配置**：引擎凭据（Basic + `local-v1` HMAC 签名）由桌面端注入子进程环境变量，
     代码从进程内存自动发现，不落盘、不上传、不需要 API Key。
   - **流式**：推理过程与正文分段返回，前端边收边渲染，2 秒内就有文字在动。
   - **耗时**：实测 4~10 秒（模型档位默认 `chat-lite`，可用环境变量 `AI_ENGINE_MODEL` 调整）。
   - **要求**：Windows + 已安装并登录、运行 TeleAgent 桌面端。
2. **调度器投递（兜底）**：引擎不可用但桌面端在跑时，改用调度器 HTTP API 投递任务，约 40 秒返回。
3. **离线标签引擎（最终兜底，跨平台）**：`ai_local.py` 对 180 道菜打温度/口味/场景/价位
   多维标签，把学生的话解析成意图标签，结合窗口评分、月榜排名与学生评论口碑
   （好评/差评关键词 + 意图佐证）综合打分取 Top3，**1 秒内**响应。

响应中的 `engine` 字段标明本次推荐由哪个引擎生成（`engine` / `teleagent` / `local`），
前端徽章如实展示。

**自检**：

```bash
python teleagent_client.py "请只回复四个字：桥接正常"
```

**没有 TeleAgent 也能用**：直接 `python app.py`，AI 点菜会自动走本地标签引擎，
其余功能（打分、发帖、榜单、搜索）完全不受影响。

---

## 📦 部署提示

- 生产环境建议在反向代理（Nginx / Caddy）后运行，并关闭 `debug`。
- **正式投入使用前**：把 `canteen.db` 从版本库移除并加入 `.gitignore`，避免学生评分与发帖数据随 git 提交泄露；同时重置管理员与全部商家密码。
- 数据库文件 `canteen.db` 请定期备份（`tool.py db` 已自动保留最近 40 份快照）。
- 上传目录 `uploads/` 需保证可写。

---

## 📄 开源协议

[MIT License](./LICENSE) —— 可自由用于学习、二次开发、校内推广，欢迎提 Issue 和 PR。

---

Made with ☕ for campus canteens everywhere.
