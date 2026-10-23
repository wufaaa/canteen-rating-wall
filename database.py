# -*- coding: utf-8 -*-
"""食堂匿名打分系统 —— 数据库初始化与种子数据"""
import os
import random
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

CN_TZ = timezone(timedelta(hours=8))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canteen.db")
random.seed(20261021)  # 固定随机种子，保证示例数据可复现

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS anons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    nickname TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canteen INTEGER NOT NULL,
    floor INTEGER NOT NULL,
    win_no INTEGER NOT NULL,
    name TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    merchant_user TEXT UNIQUE NOT NULL,
    merchant_pass_hash TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    is_buffet INTEGER NOT NULL DEFAULT 0,
    UNIQUE(canteen, floor, win_no)
);
CREATE TABLE IF NOT EXISTS dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    intro TEXT NOT NULL DEFAULT '',
    photo TEXT NOT NULL DEFAULT '',
    stall TEXT NOT NULL DEFAULT '',
    status INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anon_id INTEGER NOT NULL,
    window_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(anon_id, window_id, date)
);
CREATE INDEX IF NOT EXISTS idx_ratings_win_date ON ratings(window_id, date);
CREATE INDEX IF NOT EXISTS idx_ratings_date ON ratings(date);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_id INTEGER NOT NULL,
    parent_id INTEGER,
    dish_id INTEGER,
    anon_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    photo TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_posts_window ON posts(window_id, status);
CREATE TABLE IF NOT EXISTS post_likes (
    post_id INTEGER NOT NULL,
    anon_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(post_id, anon_id)
);
CREATE TABLE IF NOT EXISTS dish_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anon_id INTEGER NOT NULL,
    dish_id INTEGER NOT NULL,
    vote INTEGER NOT NULL,
    date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(anon_id, dish_id, date)
);
CREATE INDEX IF NOT EXISTS idx_dish_ratings_dish ON dish_ratings(dish_id);
CREATE TABLE IF NOT EXISTS dish_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anon_id INTEGER NOT NULL,
    dish_id INTEGER NOT NULL,
    vote INTEGER NOT NULL,
    date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(anon_id, dish_id, date)
);
CREATE INDEX IF NOT EXISTS idx_dish_ratings_dish ON dish_ratings(dish_id);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    anon_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# ---------------------------------------------------------------- 窗口（3 食堂 × 2 层 × 10 窗口 + 第四食堂·东油饺子园 × 1 层 × 10 窗口
#                + 一/二食堂自选餐档口）自选餐档口开启菜品级好评/差评投票
# (canteen, floor, win_no, 窗口名, 商家名)
WINDOWS = [
    (1, 1, 1, "兰州拉面", "马记面馆"), (1, 1, 2, "黄焖鸡米饭", "杨铭宇黄焖鸡"), (1, 1, 3, "川湘小炒", "川妹子餐饮"),
    (1, 1, 4, "东北饺子馆", "老边饺子坊"), (1, 1, 5, "麻辣香锅", "锅色天香"), (1, 1, 6, "老式蛋炒饭", "阿强炒饭"),
    (1, 1, 7, "广式烧腊", "陈师傅烧腊"), (1, 1, 8, "早餐粥铺", "晨光早点"), (1, 1, 9, "番茄鸡蛋盖饭", "好味盖浇"),
    (1, 1, 10, "铁板炒面", "老金炒面"),
    (1, 1, 11, "自选餐", "一食堂自选餐档口"),
    (1, 2, 1, "蜀香麻辣烫", "蓉城麻辣烫"), (1, 2, 2, "韩式石锅拌饭", "首尔厨房"), (1, 2, 3, "柳州螺蛳粉", "螺味轩"),
    (1, 2, 4, "瓦罐煨汤", "赣味煨汤"), (1, 2, 5, "甜品糖水铺", "顺记糖水"), (1, 2, 6, "炸鸡汉堡", "麦肯基"),
    (1, 2, 7, "西北羊肉泡馍", "老孙家泡馍"), (1, 2, 8, "川味冒菜", "冒菜大叔"), (1, 2, 9, "潮汕砂锅粥", "潮汕兄弟粥铺"),
    (1, 2, 10, "水煮鱼窗口", "渔村人家"),
    (2, 1, 1, "沙县小吃", "沙县小吃"), (2, 1, 2, "隆江猪脚饭", "隆江老字号"), (2, 1, 3, "淮南牛肉汤", "淮南张记"),
    (2, 1, 4, "手抓饼卷饼", "饼叔"), (2, 1, 5, "快餐自助", "大众快餐"), (2, 1, 6, "粤式烧味", "广府烧味"),
    (2, 1, 7, "韩式炸鸡", "桥村炸鸡"), (2, 1, 8, "老家馄饨", "千里香馄饨"), (2, 1, 9, "肉夹馍凉皮", "秦味轩"),
    (2, 1, 10, "营养套餐", "营养配餐中心"),
    (2, 1, 11, "自选餐", "二食堂自选餐档口"),
    (2, 2, 1, "重庆小面", "渝记小面"), (2, 2, 2, "东北铁锅炖", "关东大院"), (2, 2, 3, "新疆大盘鸡", "天山食府"),
    (2, 2, 4, "云南过桥米线", "滇香园"), (2, 2, 5, "咖喱蛋包饭", "洋风厨房"), (2, 2, 6, "泰式简餐", "曼谷小馆"),
    (2, 2, 7, "健身轻食", "轻卡餐吧"), (2, 2, 8, "果切鲜榨", "鲜果时光"), (2, 2, 9, "夜宵烧烤", "炭火故事"),
    (2, 2, 10, "武汉热干面", "汉口过早"),
    (3, 1, 1, "清真美食窗口", "清真餐厅"), (3, 1, 2, "素食专区", "禅意素斋"), (3, 1, 3, "精品小炒", "大厨小灶"),
    (3, 1, 4, "汤面世家", "面面俱到"), (3, 1, 5, "盖浇饭大王", "饭当家"), (3, 1, 6, "广式肠粉", "粤式肠粉王"),
    (3, 1, 7, "五谷渔粉", "五谷渔粉"), (3, 1, 8, "卤味凉菜", "卤香居"), (3, 1, 9, "手工大包", "包子天下"),
    (3, 1, 10, "风味蒸菜", "沔阳蒸菜馆"),
    (3, 2, 1, "江南点心", "江南点心行"), (3, 2, 2, "苏式面馆", "姑苏面庄"), (3, 2, 3, "湘菜小炒", "湘江人家"),
    (3, 2, 4, "东北乱炖", "翠花上菜"), (3, 2, 5, "台湾卤肉饭", "宝岛风味"), (3, 2, 6, "港式烧饭", "港岛茶餐厅"),
    (3, 2, 7, "轻食沙拉吧", "绿洲沙拉"), (3, 2, 8, "鲜果捞", "甜心果捞"), (3, 2, 9, "烘焙工坊", "麦子熟了"),
    (3, 2, 10, "咖啡轻食", "校园咖啡角"),
    (4, 1, 1, "酸菜猪肉饺", "老坛酸菜馆"), (4, 1, 2, "三鲜水饺", "海味三鲜居"), (4, 1, 3, "牛肉大葱饺", "北疆饺庄"),
    (4, 1, 4, "韭菜鸡蛋饺", "农家韭香园"), (4, 1, 5, "玉米猪肉饺", "金穗饺子屋"), (4, 1, 6, "虾仁蒸饺", "鲜虾蒸饺王"),
    (4, 1, 7, "煎饺锅贴", "金底锅贴铺"), (4, 1, 8, "酸汤水饺", "老陕酸汤坊"), (4, 1, 9, "香菇青菜饺", "素香饺子斋"),
    (4, 1, 10, "熏酱凉菜拼", "关东熏酱坊"),
]

# ---------------------------------------------------------------- 每个窗口的菜品示例（窗口名 -> [(菜名, 价格, 简介, 照片)]）
DISH_MAP = {
    "兰州拉面": [("招牌牛肉拉面", 13.0, "一清二白三红四绿，汤鲜面弹，大片牛肉", "dish-01.jpg"), ("凉拌拉面", 11.0, "夏日限定，麻酱拌匀配黄瓜丝", ""), ("卤蛋加面套餐", 15.0, "拉面+卤蛋+小菜，管饱", "")],
    "黄焖鸡米饭": [("黄焖鸡米饭(大份)", 16.0, "鸡腿肉土豆青椒现焖，汤汁拌饭一绝", "dish-02.jpg"), ("香辣鸡煲饭", 15.0, "加辣版黄焖鸡，够劲", ""), ("素焖豆腐饭", 10.0, "嫩豆腐焖汁，素食友好", "")],
    "川湘小炒": [("农家小炒肉", 14.0, "五花肉配螺丝椒，下饭神器", ""), ("麻婆豆腐", 9.0, "麻辣鲜香烫，嫩滑入味", ""), ("蒜苔炒腊肉", 15.0, "湘味腊肉，香而不腻", "")],
    "东北饺子馆": [("猪肉白菜水饺(15只)", 12.0, "手工现包，皮薄馅大", "dish-05.jpg"), ("酸菜猪肉水饺(15只)", 13.0, "东北酸菜发酵足，酸香开胃", ""), ("饺子+凉菜套餐", 15.0, "水饺配拍黄瓜，解腻", "")],
    "麻辣香锅": [("自助香锅(称重)", 2.2, "40+种食材自由搭配，荤素同价每50g", ""), ("肥牛香锅套餐", 18.0, "肥牛卷+午餐肉+宽粉标配", ""), ("全素香锅", 12.0, "时蔬菇菌大满贯", "")],
    "老式蛋炒饭": [("招牌蛋炒饭", 10.0, "猪油炒制，粒粒分明", ""), ("扬州什锦炒饭", 13.0, "虾仁火腿青豆，豪华版", ""), ("炒饭加烤肠套餐", 13.0, "炒饭配爆汁烤肠", "")],
    "广式烧腊": [("蜜汁叉烧饭", 15.0, "肥瘦相间，蜜香四溢", ""), ("烧鸭腿饭", 16.0, "皮脆肉嫩，浇烧汁", ""), ("双拼饭", 18.0, "叉烧+烧鸭一次满足", "")],
    "早餐粥铺": [("皮蛋瘦肉粥", 6.0, "绵密顺滑，现熬4小时", ""), ("小米南瓜粥", 5.0, "养胃首选，微甜", ""), ("粥+包子套餐", 8.0, "任选一粥两包", "")],
    "番茄鸡蛋盖饭": [("番茄鸡蛋盖浇饭", 11.0, "浓汁嫩蛋，酸甜开胃", "dish-04.jpg"), ("番茄牛腩盖浇饭", 17.0, "牛腩炖足两小时", ""), ("木须肉盖浇饭", 12.0, "肉片滑嫩配木耳黄瓜", "")],
    "铁板炒面": [("招牌铁板炒面", 11.0, "铁板现炒，锅气十足", ""), ("孜然羊肉炒面", 15.0, "孜然香浓，配洋葱", ""), ("炒面加蛋", 12.5, "现煎太阳蛋盖顶", "")],
    "蜀香麻辣烫": [("招牌麻辣烫", 14.0, "骨汤底+红油，丸子青菜宽粉任选", "dish-03.jpg"), ("清汤麻辣烫", 13.0, "不辣版本，骨汤原味", ""), ("冒苕粉", 12.0, "红油宽粉，麻辣入味", "")],
    "韩式石锅拌饭": [("牛肉石锅拌饭", 18.0, "滋滋作响锅巴香，配煎蛋辣酱", "dish-06.jpg"), ("鸡肉石锅拌饭", 16.0, "照烧鸡肉版，甜咸口", ""), ("大酱汤套餐", 14.0, "豆腐西葫芦大酱汤+米饭", "")],
    "柳州螺蛳粉": [("原味螺蛳粉", 13.0, "酸笋够味，腐竹花生脆", ""), ("加辣加臭螺蛳粉", 15.0, "双倍酸笋，闻着臭吃着香", ""), ("炒螺蛳粉", 15.0, "干香版，锅气更足", "")],
    "瓦罐煨汤": [("莲藕排骨汤", 12.0, "瓦罐煨足6小时，藕粉汤浓", ""), ("墨鱼猪肚汤", 15.0, "滋补首选，汤色奶白", ""), ("汤+拌粉套餐", 14.0, "任选煨汤配南昌拌粉", "")],
    "甜品糖水铺": [("红豆双皮奶", 9.0, "奶皮嫩滑，红豆绵密", "dish-08.jpg"), ("杨枝甘露", 12.0, "芒果西柚西米露", ""), ("手工芝麻糊", 8.0, "石磨现磨，香浓细腻", "")],
    "炸鸡汉堡": [("香辣鸡腿堡套餐", 18.0, "堡+薯条+可乐", ""), ("全鸡分享桶", 32.0, "3-4人份，现炸出锅", ""), ("鸡排饭", 15.0, "大鸡排盖饭配酸辣土豆丝", "")],
    "西北羊肉泡馍": [("传统羊肉泡馍", 22.0, "手掰馍块，浓汤配糖蒜", ""), ("优质牛肉泡馍", 20.0, "牛肉厚切，汤醇馍筋", ""), ("羊肉小炒泡馍", 21.0, "干香版，配粉丝木耳", "")],
    "川味冒菜": [("荤菜冒菜套餐", 16.0, "十几种荤素现冒，冒菜就是一个人的火锅", ""), ("全素冒菜", 11.0, "时蔬藕片土豆海带", ""), ("冒脑花", 14.0, "嫩滑入口即化，老饕限定", "")],
    "潮汕砂锅粥": [("招牌虾蟹粥", 26.0, "鲜虾蟹膏熬粥，2-3人份", ""), ("田鸡砂锅粥", 22.0, "肉质细嫩，粥底绵滑", ""), ("皮蛋瘦肉粥(小份)", 10.0, "一人食小砂锅", "")],
    "水煮鱼窗口": [("招牌水煮鱼", 28.0, "现杀活鱼，麻辣鲜香", ""), ("番茄水煮鱼", 26.0, "酸汤版，不辣口", ""), ("鱼片单人份", 18.0, "轻量版，米饭管够", "")],
    "沙县小吃": [("飘香拌面+扁食", 10.0, "花生酱拌面配现包扁食", ""), ("蒸饺(10只)", 8.0, "薄皮蒸饺，蘸醋绝配", ""), ("飘香拌面(加大)", 9.0, "花生酱+葱油，管饱", "")],
    "隆江猪脚饭": [("招牌猪脚饭", 16.0, "卤汁浸润，皮糯肉酥", ""), ("双拼饭(猪脚+卤蛋卷)", 18.0, "经典搭配，肥瘦相间", ""), ("卤肉饭", 13.0, "碎卤肉拌饭，学生价", "")],
    "淮南牛肉汤": [("淮南牛肉汤+饼", 15.0, "粉丝牛肉汤配现烤烧饼", ""), ("牛杂汤", 16.0, "牛肚牛筋，料足", ""), ("牛肉粉丝汤", 13.0, "牛肉薄片，汤清味浓", "")],
    "手抓饼卷饼": [("原味手抓饼", 7.0, "外酥里软，千层起酥", ""), ("培根蛋手抓饼", 11.0, "现煎蛋+培根，热乎管饱", ""), ("鸡柳卷饼", 12.0, "生菜甜酱鸡柳一卷到底", "")],
    "快餐自助": [("两荤两素自助", 13.0, "现炒自选，米饭免费续", ""), ("一荤两素自助", 10.0, "基础配置，经济实惠", ""), ("半份菜窗口", 6.0, "半价半份，光盘行动", "")],
    "粤式烧味": [("叉烧滑蛋饭", 15.0, "蜜汁叉烧配滑蛋", ""), ("油鸡饭", 14.0, "白切鸡葱姜蓉", ""), ("四宝饭", 17.0, "四种烧味一次打卡", "")],
    "韩式炸鸡": [("蜂蜜芥末炸鸡", 19.0, "外酥里嫩，双酱蘸食", ""), ("甜辣炸鸡年糕", 20.0, "炸鸡配年糕，韩剧同款", ""), ("无骨炸鸡块", 16.0, "追剧神器，一口一个", "")],
    "老家馄饨": [("三鲜大馄饨(12只)", 12.0, "虾仁鲜肉馅，汤鲜皮薄", ""), ("荠菜馄饨(12只)", 11.0, "时令荠菜，清香", ""), ("馄饨+小笼套餐", 15.0, "经典组合", "")],
    "肉夹馍凉皮": [("腊汁肉夹馍", 11.0, "白吉馍夹卤肉，馍脆肉香", ""), ("秦镇米皮", 9.0, "红油醋汁，酸辣爽口", ""), ("肉夹馍+凉皮套餐", 17.0, "三秦套餐标配冰峰另购", "")],
    "营养套餐": [("A级套餐(两荤一素)", 15.0, "营养师配比，低油低盐", ""), ("减脂餐盒", 16.0, "鸡胸肉+粗粮+时蔬", ""), ("学生特惠套餐", 12.0, "一荤一素一汤", "")],
    "重庆小面": [("招牌豌杂面", 13.0, "豌豆软糯，杂酱浓香", ""), ("红烧牛肉面", 16.0, "大块牛肉，麻辣汤底", ""), ("素小面", 9.0, "麻辣鲜香基础版", "")],
    "东北铁锅炖": [("铁锅炖大鹅(双人)", 48.0, "贴饼子配炖鹅，量大管饱", ""), ("小鸡炖蘑菇(单人)", 22.0, "榛蘑炖鸡，汤汁拌饭", ""), ("排骨炖豆角", 20.0, "油豆角炖排骨，东北味", "")],
    "新疆大盘鸡": [("大盘鸡配皮带面", 32.0, "双人份，土豆绵软汤汁挂面", ""), ("单人小盘鸡", 18.0, "一人食版，含面", ""), ("新疆炒米粉", 14.0, "辣度可选，鸡肉芹菜", "")],
    "云南过桥米线": [("招牌过桥米线", 16.0, "滚汤现烫，配菜十碟", ""), ("小锅米线", 12.0, "酸汤肉末，一人锅", ""), ("鲜花饼+米线套餐", 18.0, "饭后配玫瑰鲜花饼", "")],
    "咖喱蛋包饭": [("经典牛肉咖喱蛋包饭", 17.0, "现摊蛋皮裹饭，牛肉咖喱浇汁", ""), ("猪排咖喱饭", 19.0, "现炸猪排咔滋脆", ""), ("儿童咖喱(微辣)", 15.0, "甜口温和，不辣", "")],
    "泰式简餐": [("泰式打抛饭", 16.0, "罗勒炒肉配溏心煎蛋", ""), ("冬阴功汤粉", 15.0, "酸辣开胃，椰香汤底", ""), ("菠萝炒饭", 16.0, "咖喱香口配肉松腰果", "")],
    "健身轻食": [("鸡胸藜麦碗", 18.0, "高蛋白低脂，健身党首选", ""), ("金枪鱼全麦三明治", 15.0, "轻卡饱腹", ""), ("牛油果鸡胸沙拉", 20.0, "当日鲜制，酱料低卡", "")],
    "果切鲜榨": [("当日鲜果切盒", 9.0, "应季水果现切，满500g", ""), ("鲜榨橙汁", 10.0, "现剥现榨，无添加", ""), ("西瓜汁(大杯)", 7.0, "夏日冰爽", "")],
    "夜宵烧烤": [("烤串组合(10串)", 20.0, "羊肉板筋鸡翅任选", ""), ("烤茄子+烤馒头片", 13.0, "锡纸烤蒜蓉茄", ""), ("小龙虾(麻辣)半份", 38.0, "当季限定，麻辣入味", "")],
    "武汉热干面": [("正宗热干面", 9.0, "芝麻酱拌碱面，配酸豆角", ""), ("热干面+蛋酒", 12.0, "经典过早组合", ""), ("三鲜豆皮", 10.0, "糯米鲜肉笋丁，金黄脆香", "")],
    "清真美食窗口": [("牛肉拉面(清真)", 12.0, "清真认证，汤清味正", ""), ("羊肉抓饭", 16.0, "胡萝卜黄萝卜配葡萄干", ""), ("清炖羊肉汤", 18.0, "清汤配白馍", "")],
    "素食专区": [("素三鲜锅贴", 10.0, "白菜香干木耳馅", ""), ("罗汉斋盖饭", 11.0, "八种时蔬菌菇", ""), ("素麻婆豆腐饭", 10.0, "豆腐仿肉口感", "")],
    "精品小炒": [("招牌红烧肉套餐", 16.0, "肥而不腻，入口即化", "dish-07.jpg"), ("宫保鸡丁饭", 13.0, "荔枝口糊香，花生脆", ""), ("糖醋里脊饭", 14.0, "外酥里嫩，酸甜适口", "")],
    "汤面世家": [("雪菜肉丝面", 11.0, "汤头清爽，雪菜提鲜", ""), ("现炒浇头面", 15.0, "现炒青椒肉丝盖面", ""), ("葱油拌面", 9.0, "葱油熬足，焦香", "")],
    "盖浇饭大王": [("鱼香肉丝盖饭", 12.0, "酸甜微辣经典款", ""), ("回锅肉盖饭", 13.0, "蒜苗豆瓣回锅香", ""), ("土豆牛肉盖饭", 15.0, "土豆沙糯牛肉酥烂", "")],
    "广式肠粉": [("鲜虾肠粉", 12.0, "米浆现蒸，虾仁弹嫩", ""), ("牛肉肠粉", 10.0, "豉油汁是灵魂", ""), ("艇仔粥+肠粉", 14.0, "广式经典早午餐", "")],
    "五谷渔粉": [("招牌五谷渔粉", 15.0, "五谷杂粮粉配酸菜鱼", ""), ("番茄渔粉", 14.0, "番茄浓汤，微酸开胃", ""), ("麻辣渔粉", 15.0, "麻辣汤底鱼片嫩", "")],
    "卤味凉菜": [("卤鸭腿", 9.0, "卤香入味，配饭神器", ""), ("夫妻肺片(小份)", 14.0, "麻辣鲜香，红油透亮", ""), ("卤蛋海带拼盘", 8.0, "下饭小菜组合", "")],
    "手工大包": [("鲜肉大包", 3.0, "现包现蒸，皮松馅足", ""), ("酱肉包", 3.0, "甜面酱香浓", ""), ("豆沙包", 2.5, "细腻甜沙", "")],
    "风味蒸菜": [("粉蒸肉", 15.0, "米粉裹肉，软糯咸香", ""), ("蒸排骨糯米饭", 14.0, "排骨蒸糯米，吸饱肉汁", ""), ("蒸蛋羹", 6.0, "嫩滑如布丁", "")],
    "江南点心": [("鲜肉小笼(6只)", 10.0, "皮薄汁多，小心烫口", ""), ("蟹黄汤包(2只)", 12.0, "插管吸汤，鲜掉眉毛", ""), ("生煎馒头(4只)", 8.0, "底脆汁多，芝麻葱花", "")],
    "苏式面馆": [("枫镇大肉面", 16.0, "白汤焖肉，苏式头牌", ""), ("虾仁两面黄", 18.0, "面脆虾仁弹", ""), ("爆鱼面", 15.0, "爆鱼酥香汤浓", "")],
    "湘菜小炒": [("辣椒炒肉盖码饭", 14.0, "螺丝椒配土猪肉，湘味十足", ""), ("紫苏炒田螺", 18.0, "香辣入味，嗦螺大赛", ""), ("擂辣椒皮蛋", 9.0, "开胃下饭神器", "")],
    "东北乱炖": [("小鸡炖蘑菇(单人)", 20.0, "大骨汤底，榛蘑香浓", ""), ("排骨炖豆角贴饼子", 22.0, "一锅出，主食菜全有", ""), ("酸菜白肉炖粉条", 18.0, "东北酸菜发酵足", "")],
    "台湾卤肉饭": [("经典卤肉饭", 14.0, "红葱酥卤汁，肥而不腻", ""), ("卤肉饭+卤蛋+笋丝", 16.0, "台式标配三件套", ""), ("盐酥鸡(小份)", 12.0, "九层塔香气扑鼻", "")],
    "港式烧饭": [("豉汁排骨蒸饭", 15.0, "豉香浓郁，排骨嫩", ""), ("蜜汁叉烧煎蛋饭", 17.0, "双蛋叉烧，港式经典", ""), ("白切鸡饭", 16.0, "姜葱蓉是灵魂", "")],
    "轻食沙拉吧": [("凯撒鸡肉沙拉", 16.0, "罗马生菜+帕玛森+现煎鸡", ""), ("地中海藜麦碗", 18.0, "鹰嘴豆烤蔬菲达芝士", ""), ("烟熏三文鱼沙拉", 22.0, "高配款，鲜香不腻", "")],
    "鲜果捞": [("缤纷水果捞", 13.0, "六种应季水果+酸奶", ""), ("杨梅冰汤圆", 12.0, "当季杨梅，酸甜爆汁", ""), ("椰奶芒果捞", 14.0, "椰浆浓郁", "")],
    "烘焙工坊": [("现烤吐司(2片)", 6.0, "现点现烤，黄油焦香", ""), ("岩烧乳酪蛋糕", 9.0, "芝士流心，限售每日30份", ""), ("海盐牛角包", 7.0, "外脆内软层层酥", "")],
    "咖啡轻食": [("美式咖啡(中杯)", 10.0, "现磨豆，学生价第二杯半价", ""), ("拿铁+贝果套餐", 18.0, "早八救星组合", ""), ("挂耳咖啡包(10包)", 25.0, "自习室续命装", "")],
    "酸菜猪肉饺": [("酸菜猪肉水饺(15只)", 12.0, "东北酸菜现拌馅，酸香开胃", ""), ("酸菜猪肉蒸饺(10只)", 12.0, "现包现蒸，汁水足", ""), ("饺子+黑酱小碟套餐", 16.0, "水饺配重酱小碟", "")],
    "三鲜水饺": [("三鲜水饺(15只)", 14.0, "虾仁鸡蛋韭菜，皮薄馅大", ""), ("三鲜饨饨", 11.0, "大馅饨饨，紫菜虾皮汤", ""), ("全家福水饺(20只)", 19.0, "四种馅料拼一盘", "")],
    "牛肉大葱饺": [("牛肉大葱水饺(15只)", 15.0, "牛肉现剁，大葱提香", ""), ("牛肉蒸饺(10只)", 15.0, "个头大，咬一口爆汁", ""), ("牛肉汤饺套餐", 18.0, "水饺配牛肉原汤", "")],
    "韭菜鸡蛋饺": [("韭菜鸡蛋水饺(15只)", 10.0, "头茬韭菜配土鸡蛋", ""), ("韭菜盒子", 6.0, "现烙，外皮酥脆", ""), ("素馅蒸饺(10只)", 9.0, "韭菜鸡蛋粉丝馅", "")],
    "玉米猪肉饺": [("玉米猪肉水饺(15只)", 12.0, "甜玉米粒，清甜多汁", ""), ("玉米蒸饺(10只)", 12.0, "蒸笼现出，口感弹嫩", ""), ("饺子+小米粥套餐", 14.0, "水饺配现熬粥", "")],
    "虾仁蒸饺": [("虾仁蒸饺(8只)", 16.0, "整只虾仁，鲜甜弹牙", ""), ("蟹黄蒸饺(8只)", 15.0, "蟹黄风味，鲜香浓郁", ""), ("蒸饺+骨汤套餐", 18.0, "蒸饺配海带骨汤", "")],
    "煎饺锅贴": [("冰花煎饺(10只)", 12.0, "底壳金黄脆亮，蘸醋更香", ""), ("牛肉锅贴(8只)", 14.0, "外脆里嫩，汤汁丰盈", ""), ("煎饺+豆浆套餐", 13.0, "现磨豆浆解腻", "")],
    "酸汤水饺": [("酸汤水饺(12只)", 12.0, "酸辣汤底，饺子现煮", ""), ("酸汤饨饨", 11.0, "香醋辣油，开胃暖身", ""), ("酸汤饺子+拌菜套餐", 15.0, "配东北大拉皮", "")],
    "香菇青菜饺": [("香菇青菜水饺(15只)", 10.0, "菌菇清香，素食友好", ""), ("香菇蒸饺(10只)", 10.0, "鲜嫩多汁", ""), ("素馅饺子+拌木耳套餐", 13.0, "清淡不腻", "")],
    "熏酱凉菜拼": [("东北熏酱拼盘", 16.0, "熏肠酱肚，下酒下饭", ""), ("大拉皮", 9.0, "麻酱芥末，爽滑筋道", ""), ("熏酱+饺子套餐", 17.0, "拼盘配10只水饺", "")],
    "自选餐": [("红烧肉", 6.0, "肥瘦相间，酱香浓郁", ""), ("糖醋里脊", 6.0, "外酥里嫩，酸甜口", ""), ("宫保鸡丁", 5.0, "花生脆，微辣带甜", ""), ("鱼香肉丝", 5.0, "经典下饭菜，酸甜咸香", ""), ("可乐鸡翅", 6.0, "甜咸口，先到先得", ""), ("辣子鸡", 6.0, "香辣过瘾，越吃越上头", ""), ("木须肉", 5.0, "肉片鸡蛋木耳，清淡口", ""), ("干煸豆角", 4.0, "干香入味，注意烫嘴", ""), ("红烧茄子", 4.0, "油润软糯，拌饭一绝", ""), ("麻婆豆腐", 3.5, "麻辣鲜香，嫩滑", ""), ("番茄炒蛋", 3.5, "国民家常菜，汤汁拌饭", ""), ("蒜蓉油麦菜", 3.0, "清爽解腻", ""), ("番茄麻辣烫", 13.0, "酸甜汤底，煮菜吸味", ""), ("骨汤麻辣烫", 14.0, "大骨汤底，麻辣适中", ""), ("藤椒麻辣烫", 14.0, "藤椒麻香，微微舌麻", ""), ("干拌麻辣烫", 13.0, "无汤干拌，酱料裹满", ""), ("自助称重麻辣烫", 15.0, "荤素自选称重，丰俭由人", "")],
}

# 自选餐档口（窗口级标记，页面展示菜品级好评/差评投票）
BUFFET_WINDOWS = {(1, 1, 11), (2, 1, 11)}

# 自选餐分档：档口名 -> 该档口菜品名（未列出的自选餐菜品归入 BUFFET_DEFAULT_STALL）
BUFFET_STALLS = {
    "自选麻辣烫": ["番茄麻辣烫", "骨汤麻辣烫", "藤椒麻辣烫", "干拌麻辣烫", "自助称重麻辣烫"],
}
BUFFET_DEFAULT_STALL = "自选菜"


def buffet_stall_of(name):
    """按菜名返回所属自选档口"""
    for stall, names in BUFFET_STALLS.items():
        if name in names:
            return stall
    return BUFFET_DEFAULT_STALL

# ---------------------------------------------------------------- 匿名昵称生成
ADJECTIVES = ["爱吃拌面的", "干饭超快的", "中午抢饭的", "无辣不欢的", "碳水战士", "汤底守护",
              "食堂常驻", "口味挑剔的", "嗜甜如命的", "夜宵派", "清淡主义", "米饭免费续碗的",
              "天天换窗口的", "敢试新菜的", "专挑人少队的", "军训饿疯的", "图书馆卷完来吃的",
              "宿舍楼下来的", "认准一家不换的", "青椒必须挑出去的", "实验课摸鱼干饭的", "早八强撑的"]
ANIMALS = ["橘猫", "海獭", "柯基", "大熊猫", "仓鼠", "刺猬", "柴犬", "羊驼", "水豚", "企鹅",
           "白鲸", "小鹿", "狐狸", "树懒", "章鱼", "蜜蜂", "白鹤", "布偶猫", "短腿猫", "田园犬"]


def gen_nickname():
    return random.choice(ADJECTIVES) + random.choice(ANIMALS) + "#" + secrets.token_hex(2).upper()


def now_str(offset_seconds=0):
    t = datetime.now(CN_TZ) + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%d %H:%M:%S")


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ---------------------------------------------------------------- 帖子内容模板池
POST_GOOD = [
    "今天{dish_hint}分量超足，师傅还多给舀了一勺，好评！",
    "排队不算长，出餐快，味道在线，中午的救星。",
    "阿姨/叔叔人超好，看我犹豫还主动推荐了搭配，暖心。",
    "新出的这个菜绝了，这周已经连吃三天，室友被我安利了。",
    "性价比之王，{dish_hint}这个价还要什么自行车。",
    "今天来得早，{dish_hint}刚出锅，烫呼呼的香。",
    "汤底是真的用心了，喝到最后一口都不腻。",
    "窗口小哥记性真好，我上次说少辣这次直接安排。",
]
POST_BAD = [
    "今天{dish_hint}油放得有点猛，吃完干了整杯水。",
    "等了快半个小时，队伍基本不动，赶时间的慎选。",
    "感觉{dish_hint}味道比上学期咸了一点，希望调整下。",
    "中午去晚了，好几个菜都卖完了，只能随便对付一口。",
    "价格比上周贵了一块，味道倒是没变，就……嗯。",
    "吃到一半发现有点凉了，出餐到取餐之间的保温要加强啊。",
    "辣椒给得太含蓄了，标注的微辣约等于没有，无辣不欢的记得加辣。",
]
POST_NEUTRAL = [
    "中规中矩，赶时间可以吃，专门跑一趟没必要。",
    "今天人多，建议错峰11:20前来。",
    "个人口味原因吧，觉得还行，同去的室友倒是说好吃。",
    "蹲一个测评，有人试过新出的那个菜吗？",
    "老样子，稳定发挥，不惊艳也不踩雷。",
]
REPLIES = [
    "同感！昨天吃的也觉得不错。",
    "蹲一个后续，下周去试试。",
    "求师傅多放点辣，谢谢。",
    "真的，这家一直挺稳的。",
    "楼上+1，我也遇到过。",
    "别去吧，我觉得一般，去隔壁那家。",
    "哈哈哈哈笑死，太真实了。",
    "谢谢提醒，明天错峰去。",
    "试过了，楼主讲的都是真的。",
    "哭了，今天去已经卖完了。",
]
BAD_POSTS = [
    "说实话一楼其他窗口都是垃圾，就这家能吃，不服来辩。",
    "老板手抖成这样也配打分？大家别去，避雷避雷避雷。",
    "加我V免费拉你进外卖优惠群，顺便说下这家也就那样。",
]

REPORT_REASONS = ["引战攻击其他窗口", "疑似广告推广", "煽动抵制、言辞过激"]


def seed_ratings(cur, anon_ids, window_ids_with_quality, today):
    """近45天评分：9月与10月都有数据，保证月榜有差异与历史榜可看"""
    rating_rows = []
    for win_id, quality in window_ids_with_quality:
        # 每个窗口近45天被评 12~30 次
        n = random.randint(12, 30)
        used_days = set()
        for _ in range(n):
            # 近45天内随机一天（保证一定量落在当月）
            days_ago = random.choice([random.randint(0, 20), random.randint(21, 44)])
            d = today - timedelta(days=days_ago)
            anon = random.choice(anon_ids)
            key = (anon, d.isoformat())
            if key in used_days:  # 同一学生同一天不重复打同窗口
                continue
            used_days.add(key)
            score = max(1, min(5, round(quality + random.gauss(0, 0.55))))
            rating_rows.append((anon, win_id, score, d.isoformat(), now_str()))
    cur.executemany(
        "INSERT OR IGNORE INTO ratings(anon_id, window_id, score, date, created_at) VALUES (?,?,?,?,?)",
        rating_rows,
    )


def seed_posts(cur, anon_ids, window_rows, today):
    """每窗口 0~3 条主帖 + 部分回帖 + 点赞 + 3条待处理举报"""
    post_ids = []
    for w in window_rows:
        quality = w["quality"]
        for _ in range(random.randint(0, 3)):
            if random.random() < quality - 2.6:  # 分数高的窗口好评概率更大
                tpl = random.choice(POST_GOOD)
            elif random.random() < (5 - quality) / 3:
                tpl = random.choice(POST_BAD)
            else:
                tpl = random.choice(POST_NEUTRAL)
            days_ago = random.randint(0, 18)
            created = (datetime.now() - timedelta(
                days=days_ago, hours=random.randint(0, 8), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
            content = tpl.format(dish_hint="招牌菜")
            cur.execute(
                "INSERT INTO posts(window_id, parent_id, dish_id, anon_id, content, created_at, status) VALUES (?,?,?,?,?,?,1)",
                (w["id"], None, random.choice(w["dish_ids"]) if w["dish_ids"] and random.random() < 0.3 else None,
                 random.choice(anon_ids), content, created))
            post_ids.append(cur.lastrowid)
    # 回帖
    for _ in range(45):
        if not post_ids:
            break
        pid = random.choice(post_ids)
        created = (datetime.now() - timedelta(
            hours=random.randint(0, 200), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("SELECT window_id FROM posts WHERE id=?", (pid,))
        win_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO posts(window_id, parent_id, dish_id, anon_id, content, created_at, status) VALUES (?,?,?,?,?,?,1)",
            (win_id, pid, None, random.choice(anon_ids), random.choice(REPLIES), created))
    # 点赞
    like_rows = []
    for pid in post_ids:
        for _ in range(random.randint(0, 12)):
            like_rows.append((pid, random.choice(anon_ids), now_str()))
    cur.executemany("INSERT OR IGNORE INTO post_likes(post_id, anon_id, created_at) VALUES (?,?,?)", like_rows)
    # 3 条违规帖 + 待处理举报（供管理员端演示）
    bad_win = random.sample(window_rows, 3)
    for i, w in enumerate(bad_win):
        cur.execute(
            "INSERT INTO posts(window_id, parent_id, dish_id, anon_id, content, created_at, status) VALUES (?,?,?,?,?,?,1)",
            (w["id"], None, None, random.choice(anon_ids), BAD_POSTS[i], now_str()))
        bad_pid = cur.lastrowid
        for _ in range(random.randint(1, 3)):  # 有人点赞，更逼真
            cur.execute("INSERT OR IGNORE INTO post_likes(post_id, anon_id, created_at) VALUES (?,?,?)",
                        (bad_pid, random.choice(anon_ids), now_str()))
        cur.execute("INSERT INTO reports(post_id, anon_id, reason, created_at, status) VALUES (?,?,?,?,0)",
                    (bad_pid, random.choice(anon_ids), REPORT_REASONS[i], now_str()))


def _migrate():
    """对已存在的旧库做增量升级（幂等）"""
    conn = get_conn()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(posts)")]
        if "photo" not in cols:
            conn.execute("ALTER TABLE posts ADD COLUMN photo TEXT NOT NULL DEFAULT ''")
        if "category" not in cols:
            conn.execute("ALTER TABLE posts ADD COLUMN category TEXT NOT NULL DEFAULT ''")
        wcols = [r[1] for r in conn.execute("PRAGMA table_info(windows)")]
        if "is_buffet" not in wcols:
            conn.execute("ALTER TABLE windows ADD COLUMN is_buffet INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS dish_ratings ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, anon_id INTEGER NOT NULL, dish_id INTEGER NOT NULL,"
            " vote INTEGER NOT NULL, date TEXT NOT NULL, created_at TEXT NOT NULL,"
            " UNIQUE(anon_id, dish_id, date))")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dish_ratings_dish ON dish_ratings(dish_id)")
        dcols = [r[1] for r in conn.execute("PRAGMA table_info(dishes)")]
        if "stall" not in dcols:
            conn.execute("ALTER TABLE dishes ADD COLUMN stall TEXT NOT NULL DEFAULT ''")
        # 增量补充新增的食堂/窗口（如：第四食堂·东油饺子园、一/二食堂自选餐档口）
        _seed_missing_windows(conn)
        # 自选餐分档：补插新档口菜品并回填归属（幂等）
        for wid, in conn.execute("SELECT id FROM windows WHERE is_buffet=1").fetchall():
            for (dname, price, intro, photo) in DISH_MAP.get("自选餐", []):
                row = conn.execute("SELECT id FROM dishes WHERE window_id=? AND name=?", (wid, dname)).fetchone()
                if row:
                    conn.execute("UPDATE dishes SET stall=? WHERE id=?", (buffet_stall_of(dname), row["id"]))
                else:
                    conn.execute(
                        "INSERT INTO dishes(window_id, name, price, intro, photo, stall, status, updated_at)"
                        " VALUES (?,?,?,?,?,?,1,?)",
                        (wid, dname, price, intro, photo, buffet_stall_of(dname), now_str()))
        conn.commit()
    finally:
        conn.close()


def _seed_missing_windows(conn, only_canteen=None):
    """向已有库补充 WINDOWS 清单里缺失的窗口与菜品（幂等）"""
    cur = conn.cursor()
    for c, f, n, name, mch in WINDOWS:
        if only_canteen is not None and c != only_canteen:
            continue
        if cur.execute("SELECT 1 FROM windows WHERE canteen=? AND floor=? AND win_no=?",
                       (c, f, n)).fetchone():
            continue
        user = "c%d-%d-%02d" % (c, f, n)
        cur.execute(
            "INSERT INTO windows(canteen, floor, win_no, name, merchant_name, merchant_user, merchant_pass_hash, status, is_buffet)"
            " VALUES (?,?,?,?,?,?,?,1,?)",
            (c, f, n, name, mch, user, generate_password_hash("shop123456"),
             1 if (c, f, n) in BUFFET_WINDOWS else 0))
        win_id = cur.lastrowid
        for (dname, price, intro, photo) in DISH_MAP.get(name, []):
            stall = buffet_stall_of(dname) if (c, f, n) in BUFFET_WINDOWS else ""
            cur.execute(
                "INSERT INTO dishes(window_id, name, price, intro, photo, stall, status, updated_at) VALUES (?,?,?,?,?,?,1,?)",
                (win_id, dname, price, intro, photo, stall, now_str()))


def init_db(force=False):
    if os.path.exists(DB_PATH) and not force:
        _migrate()
        return False
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    now = now_str()
    today = datetime.now().date()

    # 管理员（口令可用环境变量 ADMIN_PASSWORD 覆盖；未设置时使用默认开发口令）
    admin_pw = os.environ.get("ADMIN_PASSWORD", "admin@2026")
    cur.execute("INSERT INTO admins(username, password_hash, created_at) VALUES (?,?,?)",
                ("admin", generate_password_hash(admin_pw), now))

    # 窗口 + 商家账号（初始密码统一 shop123456，登录后管理员可重置）
    win_cur_rows = []
    for c, f, n, name, mch in WINDOWS:
        user = "c%d-%d-%02d" % (c, f, n)
        cur.execute(
            "INSERT INTO windows(canteen, floor, win_no, name, merchant_name, merchant_user, merchant_pass_hash, status)"
            " VALUES (?,?,?,?,?,?,?,1)",
            (c, f, n, name, mch, user, generate_password_hash("shop123456")))
        win_id = cur.lastrowid
        if (c, f, n) in BUFFET_WINDOWS:
            cur.execute("UPDATE windows SET is_buffet=1 WHERE id=?", (win_id,))
        # 菜品
        dish_ids = []
        for (dname, price, intro, photo) in DISH_MAP[name]:
            cur.execute(
                "INSERT INTO dishes(window_id, name, price, intro, photo, status, updated_at) VALUES (?,?,?,?,?,1,?)",
                (win_id, dname, price, intro, photo, now))
            dish_ids.append(cur.lastrowid)
        win_cur_rows.append({"id": win_id, "name": name, "quality": round(random.uniform(3.1, 4.9), 2),
                             "dish_ids": dish_ids})

    # 匿名学生（示例数据中的虚拟身份，仅存随机代号，无任何真实信息）
    anon_ids = []
    for _ in range(55):
        cur.execute("INSERT INTO anons(token, nickname, created_at) VALUES (?,?,?)",
                    (secrets.token_hex(16), gen_nickname(), now))
        anon_ids.append(cur.lastrowid)

    seed_ratings(cur, anon_ids, [(w["id"], w["quality"]) for w in win_cur_rows], today)
    seed_posts(cur, anon_ids, win_cur_rows, today)

    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    created = init_db(force="--force" in sys.argv)
    print("数据库已初始化" if created else "数据库已存在（如需重置请加 --force）")
    print("路径:", DB_PATH)
