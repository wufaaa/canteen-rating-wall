# -*- coding: utf-8 -*-
"""接口与权限回归测试"""
import io
import requests

B = "http://127.0.0.1:5200"
PASS = FAIL = 0
FAILS = []


def chk(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS  " + name)
    else:
        FAIL += 1
        FAILS.append(name)
        print("FAIL  " + name + (("  -> " + str(extra)[:160]) if extra else ""))


def j(r):
    try:
        return r.json()
    except Exception:
        return {"ok": False, "msg": "非 JSON"}


def main():
    # ---------- 学生 A ----------
    stu = requests.Session()
    r = j(stu.get(B + "/api/bootstrap"))
    chk("学生自动获得匿名身份", r.get("ok") and r["data"].get("nickname"), r)
    nick = r["data"]["nickname"]
    chk("匿名昵称不泄露真实信息", "stu" not in nick.lower() and "@" not in nick, nick)

    lb = j(stu.get(B + "/api/leaderboard"))
    chk("榜单返回 72 条", lb.get("ok") and len(lb["data"]["rows"]) == 72, len(lb["data"]["rows"]) if lb.get("ok") else lb)
    chk("榜单含上月数据", lb["data"].get("last_month") == "2026-09", lb["data"].get("last_month"))
    chk("榜单行含封面字段", "photo" in lb["data"]["rows"][0])

    bad_month = stu.get(B + "/api/leaderboard?month=abc")
    chk("非法月份被拒", bad_month.status_code == 400, bad_month.status_code)

    ct = j(stu.get(B + "/api/canteens"))
    chk("食堂接口 72 窗口", ct.get("ok") and len(ct["data"]["windows"]) == 72)

    wd = j(stu.get(B + "/api/windows/1"))
    chk("窗口详情含菜品", wd.get("ok") and len(wd["data"]["dishes"]) > 0)
    chk("窗口详情含今日额度", "quota_left" in wd["data"], list(wd["data"].keys()))

    miss = stu.get(B + "/api/windows/99999")
    chk("不存在的窗口返回 404", miss.status_code == 404, miss.status_code)

    # ---------- 打分规则 ----------
    q0 = j(stu.get(B + "/api/my"))["data"].get("quota_left")
    r = j(stu.post(B + "/api/rate", json={"window_id": 60, "score": 5}))
    chk("正常打分成功", r.get("ok"), r)
    r2 = j(stu.post(B + "/api/rate", json={"window_id": 60, "score": 3}))
    chk("同窗口当天重复打分被拒", not r2.get("ok"), r2)
    r3 = j(stu.post(B + "/api/rate", json={"window_id": 59, "score": 9}))
    chk("非法星级被拒", not r3.get("ok"), r3)
    r4 = j(stu.post(B + "/api/rate", json={"window_id": "abc", "score": 4}))
    chk("非法窗口参数被拒", not r4.get("ok"), r4)

    # 用完 3 次额度
    stu.post(B + "/api/rate", json={"window_id": 59, "score": 4})
    stu.post(B + "/api/rate", json={"window_id": 58, "score": 4})
    r5 = j(stu.post(B + "/api/rate", json={"window_id": 57, "score": 4}))
    chk("每日 3 次额度生效", not r5.get("ok"), r5)

    # ---------- 发帖 ----------
    r = j(stu.post(B + "/api/posts", json={"window_id": 60, "content": "测试留言，分量还行。"}))
    chk("发帖成功", r.get("ok"), r)
    pid = r["data"]["post"]["id"] if r.get("ok") else None

    r = j(stu.post(B + "/api/posts", json={"window_id": 60, "content": ""}))
    chk("空内容被拒", not r.get("ok"), r)

    r = j(stu.post(B + "/api/posts", json={"window_id": 60, "content": "x" * 501}))
    chk("超长内容被拒", not r.get("ok"), r)

    # 学生发帖配图
    if pid:
        png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
               b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00"
               b"\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
        r = j(stu.post(B + "/api/posts/%d/photo" % pid,
                       files={"photo": ("t.png", io.BytesIO(png), "image/png")}))
        chk("学生给帖子配图", r.get("ok"), r)
        photo = r["data"].get("photo") if r.get("ok") else None
        if photo:
            img = stu.get(B + "/uploads/" + photo)
            chk("配图可访问", img.status_code == 200, img.status_code)
        # 别人不能给这条帖子加图
        other = requests.Session()
        other.get(B + "/api/bootstrap")
        r2 = j(other.post(B + "/api/posts/%d/photo" % pid,
                          files={"photo": ("t.png", io.BytesIO(png), "image/png")}))
        chk("别人不能给他人帖子加图", not r2.get("ok"), r2)

        # 回帖 / 点赞 / 举报
        r = j(stu.post(B + "/api/posts/%d/reply" % pid, json={"content": "同意，米饭有点硬。"}))
        chk("回帖成功", r.get("ok"), r)
        r = j(stu.post(B + "/api/posts/%d/like" % pid))
        chk("点赞成功", r.get("ok"), r)
        r = j(stu.post(B + "/api/posts/%d/like" % pid))
        chk("再点取消赞", r.get("ok"), r)
        r = j(stu.post(B + "/api/posts/%d/report" % pid, json={"reason": "垃圾广告"}))
        chk("举报成功", r.get("ok"), r)

    # ---------- 越权 ----------
    chk("学生不能进商家概览", stu.get(B + "/api/merchant/overview").status_code in (401, 403))
    chk("学生不能进管理看板", stu.get(B + "/api/admin/dashboard").status_code in (401, 403))
    chk("学生不能删帖", stu.delete(B + "/api/admin/posts/1").status_code in (401, 403))

    # ---------- 路径穿越 ----------
    t = stu.get(B + "/uploads/../app.py")
    chk("uploads 目录穿越被拦", t.status_code in (400, 403, 404), t.status_code)
    t2 = stu.get(B + "/uploads/%2e%2e%2fapp.py")
    chk("URL 编码穿越被拦", t2.status_code in (400, 403, 404), t2.status_code)

    # ---------- 商家 ----------
    shop = requests.Session()
    r = shop.post(B + "/api/auth/login", json={"role": "merchant", "username": "c1-1-01", "password": "wrong"})
    chk("商家错误密码被拒", r.status_code in (400, 401), r.status_code)
    r = j(shop.post(B + "/api/auth/login", json={"role": "merchant", "username": "c1-1-01", "password": "shop123456"}))
    chk("商家登录成功", r.get("ok"), r)

    mo = j(shop.get(B + "/api/merchant/overview"))
    chk("商家概览可用", mo.get("ok"), mo)

    r = j(shop.post(B + "/api/merchant/dishes", json={"name": "测试新菜", "price": 12.5, "intro": "测试"}))
    chk("商家新增菜品", r.get("ok"), r)
    new_did = None
    if r.get("ok"):
        d = r["data"]
        new_did = (d.get("dish") or {}).get("id") or d.get("id")

    chk("商家不能给学生打分", shop.post(B + "/api/rate", json={"window_id": 1, "score": 5}).status_code in (401, 403))
    chk("商家不能进管理看板", shop.get(B + "/api/admin/dashboard").status_code in (401, 403))

    # 商家改别人窗口的菜
    if new_did:
        other_shop = requests.Session()
        other_shop.post(B + "/api/auth/login", json={"role": "merchant", "username": "c1-1-02", "password": "shop123456"})
        r = other_shop.put(B + "/api/merchant/dishes/%d" % new_did, json={"name": "篡改", "price": 1, "intro": "x"})
        chk("商家不能改别家菜品", r.status_code in (400, 403, 404), r.status_code)

    # ---------- 管理员 ----------
    adm = requests.Session()
    r = j(adm.post(B + "/api/auth/login", json={"role": "admin", "username": "admin", "password": "admin@2026"}))
    chk("管理员登录成功", r.get("ok"), r)

    dash = j(adm.get(B + "/api/admin/dashboard"))
    chk("管理看板可用", dash.get("ok"), dash)

    wins = j(adm.get(B + "/api/admin/windows"))
    chk("管理员窗口列表 72 条", wins.get("ok") and len(wins["data"]["windows"]) == 72)

    r = j(adm.put(B + "/api/admin/windows/1", json={"name": "兰州拉面(改)", "status": 1}))
    chk("管理员改窗口名", r.get("ok"), r)

    # 停用窗口后学生不能打分/发帖
    adm.put(B + "/api/admin/windows/2", json={"status": 0})
    r = j(stu.post(B + "/api/rate", json={"window_id": 2, "score": 5}))
    chk("停用窗口不能打分", not r.get("ok"), r)
    r = j(stu.post(B + "/api/posts", json={"window_id": 2, "content": "停用窗口发帖"}))
    chk("停用窗口不能发帖", not r.get("ok"), r)
    adm.put(B + "/api/admin/windows/2", json={"status": 1})

    if pid:
        r = j(adm.delete(B + "/api/admin/posts/%d" % pid))
        chk("管理员删帖", r.get("ok"), r)
        after = j(stu.get(B + "/api/windows/60/posts"))
        chk("删帖后学生看不到", all(p["id"] != pid for p in after["data"]["posts"]))
        r = j(adm.post(B + "/api/admin/posts/%d/restore" % pid))
        chk("管理员恢复帖子", r.get("ok"), r)

    reps = j(adm.get(B + "/api/admin/reports"))
    chk("举报列表可读", reps.get("ok"), reps)

    # 商家重置密码接口
    r = j(adm.post(B + "/api/admin/windows/3/reset-merchant-password"))
    chk("管理员重置商家密码", r.get("ok"), r)

    # ---------- 汇总 ----------
    print("\n结果：%d 通过 / %d 失败" % (PASS, FAIL))
    if FAILS:
        print("失败项：")
        for f in FAILS:
            print("  - " + f)


if __name__ == "__main__":
    main()
