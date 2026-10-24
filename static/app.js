/* ============================================================ 食堂评分墙 —— 前端 SPA（原生 JS，零依赖） */
"use strict";

const $ = (s, p) => (p || document).querySelector(s);
const $$ = (s, p) => Array.from((p || document).querySelectorAll(s));

/* ------------------------------------------------------------ 工具 */
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const CN = ["一", "二", "三", "四"];
const CANTEEN_NAMES = { 4: "第四食堂（东油饺子园）" };
function cname(c) { return CANTEEN_NAMES[c] || (CN[c - 1] + "食堂"); }
function loc(w) { return `${cname(w.canteen)} ${w.floor === 1 ? "一" : "二"}楼 ${String(w.win_no).padStart(2, "0")}号`; }

function fmtTime(t) {
  const d = new Date(t.replace(" ", "T"));
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return "刚刚";
  if (diff < 3600) return Math.floor(diff / 60) + " 分钟前";
  if (diff < 86400) return Math.floor(diff / 3600) + " 小时前";
  if (diff < 86400 * 30) return Math.floor(diff / 86400) + " 天前";
  return d.toLocaleDateString("zh-CN");
}
function fmtDate(t) {
  const d = new Date(t.replace(" ", "T"));
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/* ------------------------------------------------------------ 图标（Lucide 内联） */
const ICONS = {
  star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
  heart: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
  message: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
  reply: '<polyline points="15 10 20 15 15 20"/><path d="M4 4v7a4 4 0 0 0 4 4h12"/>',
  flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  chevronRight: '<path d="m9 18 6-6-6-6"/>',
  back: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  trophy: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
  utensils: '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>',
  timer: '<line x1="10" x2="14" y1="2" y2="2"/><line x1="12" x2="15" y1="14" y2="11"/><circle cx="12" cy="14" r="8"/>',
  grid: '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
  store: '<path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/>',
  image: '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>',
  edit: '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  calendar: '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
  chart: '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  eyeOff: '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
  thumbsUp: '<path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
  thumbsDown: '<path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>',
  clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  key: '<path d="m21 2-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0 3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
  restore: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  trending: '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
  crown: '<path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7Z"/><path d="M5 20h14"/>',
  award: '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
  camera: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z"/><circle cx="12" cy="13" r="3"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  sparkles: '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
  cpu: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
};
function icon(name, cls) { return `<svg class="ic ${cls || ""}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`; }

function stars(score, cls) {
  let h = `<span class="stars ${cls || ""}">`;
  const v = Math.round(score || 0);
  for (let i = 1; i <= 5; i++) h += icon("star", i <= v ? "on" : "");
  return h + "</span>";
}

/* ------------------------------------------------------------ API */
async function api(path, method, body) {
  const opts = { method: method || "GET", headers: {} };
  if (body !== undefined && body !== null) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  try {
    const r = await fetch(path, opts);
    return await r.json();
  } catch (e) {
    return { ok: false, msg: "网络异常，请重试" };
  }
}
async function apiUpload(path, formData) {
  try {
    const r = await fetch(path, { method: "POST", body: formData });
    return await r.json();
  } catch (e) { return { ok: false, msg: "上传失败，请重试" }; }
}

function compressImage(file, maxDim, quality) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, (maxDim || 800) / Math.max(img.width, img.height));
      const cv = document.createElement("canvas");
      cv.width = Math.max(1, Math.round(img.width * scale));
      cv.height = Math.max(1, Math.round(img.height * scale));
      cv.getContext("2d").drawImage(img, 0, 0, cv.width, cv.height);
      cv.toBlob(b => {
        URL.revokeObjectURL(url);
        b ? resolve(new File([b], "photo.jpg", { type: "image/jpeg" })) : reject(new Error("压缩失败"));
      }, "image/jpeg", quality || 0.82);
    };
    img.onerror = () => reject(new Error("图片读取失败"));
    img.src = url;
  });
}

/* ------------------------------------------------------------ toast / modal / confirm */
function toast(msg, type) {
  const t = document.createElement("div");
  t.className = "toast " + (type || "ok");
  const ic = type === "err" ? "alert" : type === "info" ? "info" : "check";
  t.innerHTML = icon(ic) + "<span>" + esc(msg) + "</span>";
  $("#toastRoot").appendChild(t);
  setTimeout(() => { t.style.transition = "all .3s"; t.style.opacity = "0"; t.style.transform = "translateY(-6px)"; setTimeout(() => t.remove(), 320); }, 2600);
}

function modal(html, wide) {
  $("#modalRoot").innerHTML =
    `<div class="modal-backdrop" data-act="backdrop"><div class="modal ${wide ? "wide" : ""}">${html}</div></div>`;
  const firstInput = $(".modal input, .modal select, .modal textarea");
  if (firstInput) setTimeout(() => firstInput.focus(), 60);
}
function closeModal() { $("#modalRoot").innerHTML = ""; }

function confirmBox(title, text, okText, danger) {
  return new Promise(res => {
    App._cf = v => res(v);
    modal(`<h3>${icon(danger ? "alert" : "info")} ${esc(title)}</h3>
      <div class="m-sub">${text}</div>
      <div class="m-actions">
        <button class="btn btn-ghost" data-act="confirm-cancel">取消</button>
        <button class="btn ${danger ? "btn-danger" : "btn-primary"}" data-act="confirm-ok">${esc(okText || "确定")}</button>
      </div>`);
  });
}

/* ------------------------------------------------------------ 全局状态 */
const S = {
  boot: null,          // bootstrap 数据
  route: "leaderboard",
  winSel: { canteen: 1, floor: 1 },
  curWindowId: null,
  curWindowData: null,
  lbMonth: null,
  adminTab: "dashboard",
  merchantTab: "overview",
  postsFilter: "1",
  reportsTab: 0,
  hoverScore: 0,
  countdownTimer: null,
  postPhotoFile: null,
  searchQ: "",
  prevRoute: null,     // 上一个路由（返回键用）
  _routed: false,
};

/* ------------------------------------------------------------ 设备自动识别
   UA + 触屏 + 视口宽度三重判断，写入 body[data-device]，
   并监听旋转/尺寸变化自动切换（平板横竖屏可自适应） */
const DEVICE = { type: "desktop", label: "电脑端", ua: "" };
function detectDevice() {
  const ua = navigator.userAgent || "";
  DEVICE.ua = ua;
  const uaMobile = /Android|iPhone|iPad|iPod|Mobile|HarmonyOS|Windows Phone/i.test(ua);
  const touch = (navigator.maxTouchPoints || 0) > 1;
  const narrow = window.innerWidth <= 820;
  // 手机：UA 明确为移动设备；平板（iPad/Android 平板）：UA 命中 + 触屏；窄窗口也按手机体验
  const isPad = /iPad|Tablet|PlayBook|Silk/i.test(ua) || (/(Android)/.test(ua) && !/Mobile/.test(ua));
  const mobile = uaMobile || isPad || (touch && narrow) || narrow;
  DEVICE.type = mobile ? "mobile" : "desktop";
  DEVICE.label = isPad && mobile ? "平板端" : mobile ? "手机端" : "电脑端";
  document.body.dataset.device = DEVICE.type;
  const h = new Date().getHours();
  document.body.dataset.slot = h < 6 ? "night" : h < 10 ? "morning" : h < 17 ? "day" : h < 21 ? "evening" : "night";
  refreshHeroTime();
  document.body.dataset.deviceLabel = DEVICE.label;
  const badge = $("#deviceBadge");
  if (badge) badge.innerHTML = `${mobile ? "📱" : "💻"} ${DEVICE.label}`;
  return DEVICE.type;
}
window.addEventListener("resize", () => { detectDevice(); });

/* ------------------------------------------------------------ 主题（暗色模式）：自动跟随系统 + 手动三态 */
const THEME_KEY = "canteen_theme";
function applyTheme() {
  const pref = localStorage.getItem(THEME_KEY) || "auto";
  document.body.dataset.theme = pref;   // css 用 [data-theme="light"] 覆盖系统暗色
  const btn = document.querySelector(".theme-toggle");
  if (btn) {
    btn.innerHTML = pref === "dark" ? "🌙" : pref === "light" ? "☀️" : "🖥️";
    btn.title = "显示主题：" + (pref === "dark" ? "暗色" : pref === "light" ? "亮色" : "跟随系统") + "（点击切换）";
  }
}
function cycleTheme() {
  const cur = localStorage.getItem(THEME_KEY) || "auto";
  const next = cur === "auto" ? "dark" : cur === "dark" ? "light" : "auto";
  try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
  applyTheme();
}
applyTheme();
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (!localStorage.getItem(THEME_KEY)) applyTheme(); });
window.addEventListener("orientationchange", () => { setTimeout(detectDevice, 300); });

/* ------------------------------------------------------------ 顶栏 */
function renderTopbar() {
  const b = S.boot || {};
  const role = b.role || "anon";
  const route = S.route;
  let nav = "";
  if (role === "admin") {
    nav = `<a href="#/admin" class="${route === "admin" ? "active" : ""}">管理看板</a>
           <a href="#/leaderboard">学生视角</a>`;
  } else if (role === "merchant") {
    nav = `<a href="#/merchant" class="${route === "merchant" ? "active" : ""}">商家中心</a>
           <a href="#/leaderboard">学生视角</a>`;
  } else {
    nav = `<a href="#/leaderboard" class="${route === "leaderboard" ? "active" : ""}">${icon("trophy")} 榜单</a>
           <a href="#/canteens" class="${route === "canteens" ? "active" : ""}">${icon("grid")} 食堂</a>
           <a href="#/avoid" class="${route === "avoid" ? "active" : ""}">${icon("alert")} 避雷</a>
           <a href="#/my" class="${route === "my" ? "active" : ""}">${icon("user")} 我的</a>`;
  }
  $("#mainNav").innerHTML = nav;
  $("#mainNav").querySelectorAll("a").forEach(a => {
    if (a.querySelector("svg")) a.classList.add("withIcon");
  });

  let idz = "";
  if (role === "anon") {
    const left = b.quota_left, total = b.quota_total;
    idz = `<span class="pill gray">${icon("timer")} 今日打分 ${total - left}/${total}</span>
      <span class="pill" title="你的匿名代号，任何人都无法查到你的真实信息">${icon("shield")} ${esc(b.nickname)}</span>
      <button class="btn btn-ghost btn-sm" data-act="anon-reset" title="换一个新的匿名身份">${icon("refresh")} 换身份</button>
      <a class="icon-link only-pc" href="#/merchant" title="商家中心">${icon("store")}</a>
      <a class="icon-link only-pc" href="#/admin" title="管理看板">${icon("shield")}</a>
      <button class="theme-toggle" data-act="theme-cycle" title="显示主题（自动/暗色/亮色，点击切换）">🖥️</button>
      <span class="pill gray device-badge" id="deviceBadge" title="已自动识别设备">${DEVICE.type === "mobile" ? "📱" : "💻"} ${DEVICE.label}</span>`;
  } else if (role === "admin") {
    idz = `<span class="pill">${icon("shield")} 管理员 ${esc(b.admin_name || "")}</span>
      <button class="btn btn-ghost btn-sm" data-act="admin-changepw">${icon("key")} 改密码</button>
      <button class="btn btn-ghost btn-sm" data-act="logout">${icon("logout")} 退出</button>`;
  } else {
    idz = `<span class="pill">${icon("store")} ${esc(b.merchant_window || "商家")}</span>
      <button class="btn btn-ghost btn-sm" data-act="logout">${icon("logout")} 退出</button>`;
  }
  $("#identity").innerHTML = idz;
  applyTheme();
  renderTabbar(role, route);
}

/** 手机端底部导航（PC 端隐藏） */
function renderTabbar(role, route) {
  const el = $("#tabbar");
  if (!el) return;
  let items = [];
  if (role === "admin") {
    items = [
      { href: "#/admin", key: "admin", ic: "chart", text: "看板" },
      { href: "#/leaderboard", key: "leaderboard", ic: "trophy", text: "榜单" },
      { href: "#/canteens", key: "canteens", ic: "grid", text: "食堂" },
    ];
  } else if (role === "merchant") {
    items = [
      { href: "#/merchant", key: "merchant", ic: "store", text: "商家" },
      { href: "#/leaderboard", key: "leaderboard", ic: "trophy", text: "榜单" },
      { href: "#/canteens", key: "canteens", ic: "grid", text: "食堂" },
    ];
  } else {
    items = [
      { href: "#/leaderboard", key: "leaderboard", ic: "trophy", text: "榜单" },
      { href: "#/canteens", key: "canteens", ic: "grid", text: "食堂" },
      { href: "#/avoid", key: "avoid", ic: "alert", text: "避雷" },
      { href: "#/my", key: "my", ic: "user", text: "我的" },
    ];
  }
  el.innerHTML = items.map(it =>
    `<a href="${it.href}" class="tab-item ${route === it.key ? "on" : ""}">
       ${icon(it.ic)}<span>${it.text}</span></a>`).join("");
}

async function refreshBoot() {
  const r = await api("/api/bootstrap");
  if (r.ok) {
    S.boot = r.data;
    renderTopbar();
  }
  return r;
}

/* ------------------------------------------------------------ 榜单页 */
async function renderLeaderboard() {
  if (!S._lbLoaded) {
    $("#view").innerHTML = `<div class="page-head"><div><h1>${icon("trophy")} 月度评分榜</h1></div></div>` +
      '<div class="skeleton skel-block"></div><div class="skeleton skel-block"></div><div class="skeleton skel-line" style="width:60%"></div>';
  }
  const month = S.lbMonth || (S.boot ? S.boot.this_month : null);
  const r = await api("/api/leaderboard" + (month ? "?month=" + month : ""));
  const wr = await api("/api/warnings");
  if (!r.ok) { $("#view").innerHTML = `<div class="empty">${icon("alert")} ${esc(r.msg)}</div>`; return; }
  const d = r.data;
  S.lbMonth = d.month;
  const rows = d.rows || [];
  S._lbLoaded = true;
  const champion = rows[0] || null;
  const runners = rows.slice(1, 3);
  const rest = rows.slice(3);
  const monthOpts = (d.months || []).map(m => `<option value="${m}" ${m === d.month ? "selected" : ""}>${m} 月榜</option>`).join("");
  const photoUrl = p => "/uploads/" + p;

  /* C 位冠军 */
  const champHtml = champion ? `
    <div class="champ-card ${champion.photo ? "has-photo" : ""}"
         ${champion.photo ? `style="--cover:url('${photoUrl(champion.photo)}')"` : ""}
         data-act="go-window" data-id="${champion.window_id}">
      <div class="champ-inner">
        <div class="champ-crown">${icon("crown")} 本月 C 位</div>
        <div class="champ-name">${esc(champion.name)}</div>
        <div class="champ-loc">${loc(champion)} · ${esc(champion.merchant_name)}</div>
        <div class="champ-bottom">
          <div class="champ-score"><b>${champion.avg_score.toFixed(1)}</b><span>/ 5.0</span></div>
          <div class="champ-side">
            <div class="champ-stars">${stars(champion.avg_score)}</div>
            <div class="champ-meta">${icon("users")} ${champion.cnt} 人评分</div>
          </div>
        </div>
      </div>
    </div>` : `<div class="empty">${icon("trophy")} 本月还没有评分数据，快去给你吃过的窗口打分吧</div>`;

  /* 亚军 / 季军 */
  const runnerHtml = runners.map((w, i) => `
    <div class="runner-card r${i + 2}" data-act="go-window" data-id="${w.window_id}">
      <div class="runner-top">
        <span class="runner-rank">${i + 2}</span>
        <span class="runner-score">${w.avg_score.toFixed(1)}</span>
      </div>
      <div class="runner-name">${esc(w.name)}</div>
      <div class="runner-loc">${loc(w)}</div>
      <div class="runner-meta">${stars(w.avg_score)} <span>${w.cnt} 人</span></div>
    </div>`).join("");

  /* 上月冠军海报区 */
  const lastRows = d.last_rows || [];
  const lastLabel = d.last_month ? d.last_month.replace("-", " 年 ") + " 月" : "";
  const posterHtml = lastRows.length ? `
    <div class="poster-zone">
      <div class="poster-head">
        <div>
          <div class="poster-eyebrow">${icon("award")} 往期封榜</div>
          <h2 class="poster-title">${lastLabel} · 冠军海报</h2>
        </div>
        <div class="poster-note">该月已封榜，成绩不再变动</div>
      </div>
      <div class="poster-body">
        <div class="poster-hero ${lastRows[0].photo ? "has-photo" : ""}"
             ${lastRows[0].photo ? `style="--cover:url('${photoUrl(lastRows[0].photo)}')"` : ""}
             data-act="go-window" data-id="${lastRows[0].window_id}">
          <div class="poster-ribbon">NO.1</div>
          <div class="poster-content">
            <div class="poster-month">${lastLabel}</div>
            <div class="poster-window">${esc(lastRows[0].name)}</div>
            <div class="poster-loc">${loc(lastRows[0])} · ${esc(lastRows[0].merchant_name)}</div>
            <div class="poster-score-big">${lastRows[0].avg_score.toFixed(1)}<small>分</small></div>
            <div class="poster-foot">${stars(lastRows[0].avg_score)} · ${lastRows[0].cnt} 人评分</div>
          </div>
        </div>
        <div class="poster-list">
          ${lastRows.slice(1, 5).map(w => `
            <div class="poster-item" data-act="go-window" data-id="${w.window_id}">
              <span class="pi-rank">${w.rank}</span>
              <span class="pi-name">${esc(w.name)}</span>
              <span class="pi-score">${w.avg_score.toFixed(1)}</span>
            </div>`).join("")}
        </div>
      </div>
    </div>` : "";

  $("#view").innerHTML = `
    <div class="hero-card">
      <div class="hero-top">
        <div>
          <div class="hero-greet">${heroGreet()}</div>
          <div class="hero-title">${icon("sparkles")} ${heroSlogan()}</div>
        </div>
        <div class="hero-right">
          <span class="hero-slot-badge">${heroSlotBadge()}</span>
          <button class="hero-ai-btn" data-act="ai-open">${icon("sparkles")} AI 点菜助手</button>
        </div>
      </div>
      <div class="hero-search" data-act="hero-search">
        <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
        <input id="heroSearchInput" placeholder="搜菜名、窗口、口味…（如：黄焖鸡、不辣、10元以内）" aria-label="搜索">
      </div>
      <div class="hero-chips">
        <button class="hero-chip" data-act="hero-chip" data-q="黄焖鸡">黄焖鸡</button>
        <button class="hero-chip" data-act="hero-chip" data-q="低卡">低卡</button>
        <button class="hero-chip" data-act="hero-chip" data-q="不辣">不辣</button>
        <button class="hero-chip" data-act="hero-chip" data-q="10 元以内">10 元以内</button>
        <button class="hero-chip" data-act="hero-chip" data-q="牛肉面">牛肉面</button>
      </div>
    </div>
    <div class="page-head">
      <div><h1>${icon("trophy")} 月度评分榜</h1>
        <div class="sub">按自然月自动更新 · 窗口平均分排序（评分人数为 tie-breaker）</div></div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <span class="countdown" id="lbCountdown">${icon("timer")} 计算中…</span>
        <select class="month-sel" id="lbMonthSel">${monthOpts}</select>
      </div>
    </div>

    <div class="champ-wrap">
      ${champHtml}
      ${runners.length ? `<div class="runners">${runnerHtml}</div>` : ""}
    </div>

    <div class="avoid-banner" data-act="go-avoid">
      <div>${icon("alert")} <b>差评避雷</b> · ${wr.ok && wr.data.month_bad_cnt
        ? `本月已有 <b>${wr.data.month_bad_cnt}</b> 条差评、涉及 <b>${wr.data.window_cnt}</b> 个窗口，选窗口前先看看`
        : `本月暂无差评，欢迎大家有理有据地反馈问题`}</div>
      ${icon("chevronRight")}
    </div>

    ${posterHtml}

    <div class="card rank-2col" style="padding:8px 10px;margin-top:14px">
      ${rest.map(w => `
        <div class="rank-row ${w.status !== 1 ? "closed" : ""}" ${w.status === 1 ? `data-act="go-window" data-id="${w.window_id}"` : ""}>
          <div class="rank-no ${w.rank <= 3 ? "r" + w.rank : ""}">${w.rank}</div>
          <div class="rank-main"><div class="rn">${esc(w.name)} ${w.status !== 1 ? '<span class="tag off">已停用</span>' : ""}</div>
            <div class="rl">${loc(w)} · ${esc(w.merchant_name)}</div></div>
          ${stars(w.avg_score)}
          <div class="rank-score">${w.avg_score.toFixed(1)}</div>
          <div class="rank-cnt">${w.cnt} 人评</div>
          ${icon("chevronRight")}
        </div>`).join("") || (champion ? '<div class="empty">暂时只有前 3 名有数据</div>' : "")}
    </div>`;
  $("#lbMonthSel").addEventListener("change", e => { S.lbMonth = e.target.value; renderLeaderboard(); });
  const heroInp = $("#heroSearchInput");
  if (heroInp) heroInp.addEventListener("keydown", e => {
    if (e.key === "Enter") { location.hash = "#/canteens"; setTimeout(() => { const si = $("#winSearch"); if (si) si.focus(); }, 300); }
  });
  startCountdown(d.next_update);
}

function startCountdown(target) {
  if (S.countdownTimer) clearInterval(S.countdownTimer);
  const el = $("#lbCountdown");
  if (!el) return;
  const tgt = new Date(target.replace(" ", "T"));
  const tick = () => {
    const s = Math.max(0, Math.floor((tgt - new Date()) / 1000));
    const dd = Math.floor(s / 86400), hh = Math.floor(s % 86400 / 3600), mm = Math.floor(s % 3600 / 60), ss = s % 60;
    el.innerHTML = icon("timer") + ` 距 <b>${tgt.getMonth() + 1}月榜</b> 更新还有 <b>${dd}天${hh}时${mm}分${ss}秒</b>`;
  };
  tick();
  S.countdownTimer = setInterval(tick, 1000);
}

/* ------------------------------------------------------------ 食堂浏览页 */
async function renderCanteens() {
  const r = await api("/api/canteens");
  if (!r.ok) { $("#view").innerHTML = `<div class="empty">${icon("alert")} ${esc(r.msg)}</div>`; return; }
  const d = r.data;
  const sel = S.winSel;
  const todayRated = new Set(d.today_rated || []);
  const canteenTabs = [1, 2, 3, 4].map(c => {
    const wins = d.windows.filter(w => w.canteen === c);
    const on = wins.filter(w => w.status === 1).length;
    return `<div class="ctab ${sel.canteen === c ? "active" : ""}" data-act="sel-canteen" data-v="${c}">
      <div class="ci">${CN[c - 1]}</div>
      <div><div class="cn">${cname(c)}</div><div class="cs">营业中 ${on}/${wins.length} 窗口</div></div></div>`;
  }).join("");
  const floors = [...new Set(d.windows.filter(w => w.canteen === sel.canteen).map(w => w.floor))].sort();
  if (!floors.includes(sel.floor)) sel.floor = floors[0] || 1;
  const floorTabs = floors.map(f =>
    `<button class="${sel.floor === f ? "active" : ""}" data-act="sel-floor" data-v="${f}">${f === 1 ? "一楼" : f === 2 ? "二楼" : f + "楼"}</button>`).join("");
  const wins = d.windows.filter(w => w.canteen === sel.canteen && w.floor === sel.floor);
  const cards = wins.map(w => {
    const rated = todayRated.has(w.id);
    return `<div class="win-card ${w.status !== 1 ? "closed" : ""}" ${w.status === 1 ? `data-act="go-window" data-id="${w.id}"` : ""}>
      ${w.rank && w.rank <= 10 ? `<div class="rank-badge ${w.rank === 1 ? "top1" : ""}">月榜 #${w.rank}</div>` : ""}
      <div class="wc-top"><span class="wno">${String(w.win_no).padStart(2, "0")}</span><span class="wname2">${esc(w.name)}</span></div>
      <div class="wmer">商家：${esc(w.merchant_name)} ${w.status !== 1 ? '<span class="tag off">停业</span>' : ""}</div>
      <div class="wscore">${stars(w.avg_score)} <b>${w.avg_score != null ? w.avg_score.toFixed(1) : "—"}</b>
        <span>（${w.month_cnt} 人评）</span></div>
      <div class="wmeta"><span>${icon("utensils")} ${w.dish_cnt} 道菜</span>
        <span>${icon("users")} ${w.month_cnt} 人评</span></div>
      ${rated ? '<span class="rated-mark">✓ 今日已打分</span>' : ""}
    </div>`;
  }).join("");

  $("#view").innerHTML = `
    <div class="page-head"><div><h1>${icon("grid")} 食堂窗口</h1>
      <div class="sub">4 个食堂 · 今日剩余 ${d.quota_left} 次评价机会</div></div></div>
    <div class="search-bar">
      <span class="sb-ico">${icon("search")}</span>
      <input id="winSearch" type="search" placeholder="搜窗口名、菜品，如「清真」「麻辣香锅」「12」" value="${esc(S.searchQ || "")}" autocomplete="off" spellcheck="false">
      <button class="sb-clear" data-act="search-clear" title="清空" ${S.searchQ ? "" : "hidden"}>${icon("x")}</button>
    </div>
    <div id="browseArea">
      <div class="canteen-tabs">${canteenTabs}</div>
      <div class="floor-tabs">${floorTabs}</div>
      <div class="win-grid">${cards}</div>
    </div>
    <div id="searchArea" class="hidden"></div>`;
  const heroQ = sessionStorage.getItem("heroQ");
  if (heroQ) {
    sessionStorage.removeItem("heroQ");
    S.searchQ = heroQ;
    $("#winSearch").value = heroQ;
    doSearch(heroQ);
  }
  wireSearch();
  if (S.searchQ) doSearch(S.searchQ, true);
}

/* 关键词搜索：输入防抖 + 结果渲染 */
function wireSearch() {
  const input = $("#winSearch");
  if (!input) return;
  let timer = null;
  const clearBtn = $(".sb-clear");
  input.addEventListener("input", () => {
    const v = input.value.trim();
    S.searchQ = v;
    if (clearBtn) clearBtn.hidden = !v;
    clearTimeout(timer);
    timer = setTimeout(() => doSearch(v), 220);
  });
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") { clearTimeout(timer); doSearch(input.value.trim(), true); }
    else if (e.key === "Escape") { input.value = ""; S.searchQ = ""; if (clearBtn) clearBtn.hidden = true; doSearch(""); }
  });
}

async function doSearch(q, immediate) {
  const browse = $("#browseArea"), area = $("#searchArea");
  if (!browse || !area) return;
  if (!q) { browse.classList.remove("hidden"); area.classList.add("hidden"); area.innerHTML = ""; return; }
  browse.classList.add("hidden");
  area.classList.remove("hidden");
  if (!immediate) area.innerHTML = `<div class="search-loading">${icon("search")} 搜索中…</div>`;
  const r = await api("/api/search?q=" + encodeURIComponent(q));
  if (!r.ok) { area.innerHTML = `<div class="empty">${icon("alert")} ${esc(r.msg)}</div>`; return; }
  const d = r.data;
  if (!d.windows.length) {
    area.innerHTML = `<div class="empty">${icon("search")} 没找到和「${esc(q)}」相关的窗口，换个关键词试试</div>`;
    return;
  }
  const todayRated = new Set((S.boot && S.boot.today_rated) || []);
  const list = d.windows.map(w => {
    const rated = todayRated.has(w.id);
    const dishes = (w.matched_dishes || []).map(dh =>
      `<span class="hit-dish">${icon("utensils")} ${esc(dh.name)}<b>¥${dh.price}</b></span>`).join("");
    return `<div class="search-hit ${w.status !== 1 ? "closed" : ""}" ${w.status === 1 ? `data-act="go-window" data-id="${w.id}"` : ""}>
      <div class="sh-main">
        <div class="sh-top">
          <span class="sh-loc">${loc(w)}</span>
          ${w.rank ? `<span class="rank-badge ${w.rank === 1 ? "top1" : ""}">月榜 #${w.rank}</span>` : ""}
          ${w.status !== 1 ? '<span class="tag off">停业</span>' : ""}
        </div>
        <div class="sh-name">${esc(w.name)}</div>
        <div class="sh-mer">商家：${esc(w.merchant_name)}</div>
        ${dishes ? `<div class="sh-dishes">${dishes}</div>` : ""}
      </div>
      <div class="sh-side">
        <div class="sh-score">${w.avg_score != null ? w.avg_score.toFixed(1) : "—"}</div>
        <div class="sh-score-l">${stars(w.avg_score)} 本月 ${w.month_cnt} 人评</div>
        <div class="sh-go">${rated ? "今日已打分" : "查看 / 打分"} ${icon("chevronRight")}</div>
      </div>
    </div>`;
  }).join("");
  area.innerHTML = `<div class="search-meta">找到 <b>${d.total}</b> 个相关窗口${d.total > d.windows.length ? `（显示前 ${d.windows.length} 个）` : ""}</div>
    <div class="search-list">${list}</div>`;
}

/* ------------------------------------------------------------ 自选餐档口 */
const BUFFET_TIPS = [
  ["👍 看好评数", "菜品按好评数排序，好评多的基本不踩雷；差评多的先看看讨论区的差评理由再决定"],
  ["🥗 荤素搭配", "一荤 + 一半荤 + 一素，好吃不贵营养全；重口味菜配清淡绿叶菜"],
  ["⏰ 挑时间", "饭点前 10 分钟到档口，菜品刚补齐最新鲜；临近打烊的菜可能已回锅多次"],
  ["👁 看色泽", "菜叶发黄、肉色发暗、汤汁浑浊的要谨慎；现炒的菜有镆气"],
  ["📝 会评价", "吃到好菜给个好评鼓励商家；踩雷了差评要有理有据（哪道菜、什么问题），每人每菜每天一票"],
];

function buffetDishHtml(dh) {
  const myGood = dh.my_vote === "good", myBad = dh.my_vote === "bad";
  return `
    <div class="buffet-dish ${myGood || myBad ? "voted" : ""}">
      <div class="bd-main">
        <div class="bd-name">${esc(dh.name)}<span class="bd-price">¥${dh.price.toFixed ? dh.price.toFixed(1) : dh.price}</span>
          ${myGood ? '<span class="post-cat good">我评的好评</span>' : myBad ? '<span class="post-cat bad">我评的差评</span>' : ""}</div>
        <div class="bd-intro">${esc(dh.intro) || '<span class="faint">商家暂未填写简介</span>'}</div>
      </div>
      <div class="bd-vote">
        ${starBtn(dh.id)}
        <button class="bd-btn good ${myGood ? "on" : ""}" data-act="dish-vote" data-id="${dh.id}" data-v="good"
          title="这道菜好评，点击投票">${icon("thumbsUp")} <b>${dh.good_cnt || 0}</b></button>
        <button class="bd-btn bad ${myBad ? "on" : ""}" data-act="dish-vote" data-id="${dh.id}" data-v="bad"
          title="这道菜差评，点击投票">${icon("thumbsDown")} <b>${dh.bad_cnt || 0}</b></button>
      </div>
    </div>`;
}

/* ------------------------------------------------------------ 菜品收藏与随机点菜（本地优化） */
const FAV_KEY = "canteen_favs";

/* 时段标签：和后端 _time_slot 保持同一套划分，用于摇菜弹窗文案 */
function slotLabel() {
  const h = new Date().getHours();
  if (h >= 6 && h < 10) return { name: "早餐", tip: "🌅 清晨时光，来点热乎的开启一天" };
  if (h >= 10 && h < 14) return { name: "午餐", tip: "🍽️ 午餐时段，吃点正经的" };
  if (h >= 14 && h < 17) return { name: "下午茶", tip: "🍵 下午茶时间，犒劳一下认真上课的自己" };
  if (h >= 17 && h < 21) return { name: "晚餐", tip: "🍽️ 晚餐时段，好好吃饭" };
  return { name: "夜宵", tip: "🌙 深夜食堂开张，来点慰藉心灵的" };
}

/* 差评理由快捷标签：一键填入，帮同学把情况说清楚 */
const BAD_TAGS = ["分量偏少", "排队太久", "口味偏咸", "口味偏淡", "不太新鲜", "价格偏贵", "出餐太慢", "有点油腻", "米饭夹生", "服务一般"];

/* 价位档位：按在售菜品实际价格分布划分 */
const PRICE_TIERS = [
  { label: "不限", min: null, max: null },
  { label: "≤8元", min: null, max: 8 },
  { label: "8~12元", min: 8, max: 12 },
  { label: "12~18元", min: 12, max: 18 },
  { label: "18元+", min: 18, max: null },
];
function favList() { try { return JSON.parse(localStorage.getItem(FAV_KEY)) || []; } catch (e) { return []; } }
function favHas(id) { return favList().indexOf(Number(id)) >= 0; }
function favToggle(id) {
  const l = favList(), n = Number(id), i = l.indexOf(n);
  if (i >= 0) l.splice(i, 1); else l.push(n);
  try { localStorage.setItem(FAV_KEY, JSON.stringify(l)); } catch (e) {}
  return i < 0;
}
function starBtn(id) {
  const on = favHas(id);
  return `<button class="fav-btn ${on ? "on" : ""}" data-act="fav-toggle" data-id="${id}" title="${on ? "取消收藏" : "收藏这道菜"}">${on ? "★" : "☆"}</button>`;
}

function refreshHeroTime() {
  /* 长驻页面跨时段后自动更新时段徽章与文案（免刷新） */
  const b1 = document.querySelector(".hero-slot-badge");
  if (b1) b1.textContent = heroSlotBadge();
  const g = document.querySelector(".hero-greet");
  if (g) g.textContent = heroGreet();
  const t = document.querySelector(".hero-title");
  if (t) t.innerHTML = icon("sparkles") + " " + heroSlogan();
}
setInterval(() => { if (!document.hidden) { const h = new Date().getHours(); const want = h < 6 ? "night" : h < 10 ? "morning" : h < 17 ? "day" : h < 21 ? "evening" : "night"; if (document.body.dataset.slot !== want) { document.body.dataset.slot = want; refreshHeroTime(); } } }, 60000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) refreshHeroTime(); });

function heroGreet() {
  const h = new Date().getHours();
  if (h < 6) return "夜深了，还饿着呢？";
  if (h < 9) return "早上好！";
  if (h < 12) return "中午好！";
  if (h < 14) return "午安～";
  if (h < 18) return "下午好！";
  if (h < 21) return "晚上好！";
  return "晚上好，夜宵党～";
}
function heroSlogan() {
  const h = new Date().getHours();
  if (h < 6) return "深夜食堂还开着，来碗热乎的？";
  if (h < 9) return "早餐吃什么，问我就好";
  if (h < 12) return "提前 5 分钟想好，饭点不排队";
  if (h < 14) return "午高峰尾声，还能赶上热菜";
  if (h < 17) return "下午茶时间，犒劳一下自己";
  if (h < 21) return "晚饭吃什么，问我就好";
  return "夜宵走起，管饱不腻的那种";
}
function heroSlotBadge() {
  const h = new Date().getHours();
  if (h < 6) return "🌙 夜宵时段";
  if (h < 9) return "🌅 早餐时段";
  if (h < 12) return "🍚 午餐时段";
  if (h < 14) return "🍚 午餐时段";
  if (h < 17) return "🍵 下午茶";
  if (h < 21) return "🍲 晚餐时段";
  return "🌙 夜宵时段";
}

async function rollRandomDish() {
  const btn = $("#diceFab");
  if (btn) btn.disabled = true;
  const ti = S.rollPrice ?? 0;
  const tier = PRICE_TIERS[ti] || PRICE_TIERS[0];
  const qs = [];
  if (tier.min != null) qs.push("min_price=" + tier.min);
  if (tier.max != null) qs.push("max_price=" + tier.max);
  const r = await api("/api/random-dish" + (qs.length ? "?" + qs.join("&") : ""));
  if (btn) btn.disabled = false;
  if (!r.ok) { toast(r.msg || "摇菜失败，稍后再试", "err"); return; }
  const it = r.data;
  const slot = slotLabel();
  const slotTip = slot.tip + (it.slot_matched === false ? " · 该价位这个时段没菜，摇了道别的" : "");
  modal(`
    <div class="roll-box">
      <div class="roll-price-row">${PRICE_TIERS.map((t, i) =>
        `<button class="roll-price ${i === ti ? "on" : ""}" data-act="roll-price" data-i="${i}" title="按${t.label}价位摇菜">${t.label}</button>`).join("")}</div>
      <div class="roll-slot">${slotTip}</div>
      <div class="roll-title">🎲 ${slot.name}就吃它！</div>
      <div class="roll-name">${esc(it.dish_name)}<span class="dish-price">¥${Number(it.price).toFixed(1)}</span>${it.stall ? `<span class="pill">${esc(it.stall)}</span>` : ""}</div>
      <div class="roll-where">${icon("store")} ${loc({ canteen: it.canteen, floor: it.floor, win_no: it.win_no })} · ${esc(it.wname)} · 累计好评 <b class="good-num">${it.good_cnt}</b></div>
      <div class="roll-intro">${esc(it.intro) || '<span class="faint">商家暂未填写简介</span>'}</div>
      <div class="roll-actions">
        <button class="btn btn-ghost" data-act="roll-again">🎲 再摇一次</button>
        <button class="btn btn-primary" data-act="roll-go" data-id="${it.wid}">去窗口看看 ${icon("chevronRight")}</button>
      </div>
    </div>`);
}

/* ------------------------------------------------------------ 窗口详情页 */
async function renderWindow(id) {
  const [wr, pr] = await Promise.all([api("/api/windows/" + id), api("/api/windows/" + id + "/posts")]);
  if (!wr.ok) { $("#view").innerHTML = `<div class="empty">${icon("alert")} ${esc(wr.msg)}</div>`; return; }
  const d = wr.data, w = d.window;
  S.curWindowId = id; S.curWindowData = d; S.hoverScore = 0;
  const closed = w.status !== 1;
  const canRate = !closed && d.my_today_score == null && d.quota_left > 0;

  const favOnly = !!S.favOnly;
  const visibleDishes = favOnly ? d.dishes.filter(dh => favHas(dh.id)) : d.dishes;
  document.title = `${w.name} · 智慧食堂`;
  const buffet = !!w.is_buffet;
  let dishes = "", buffetStallHtml = "";
  if (buffet) {
    const order = ["自选麻辣烫", "自选菜"];
    const groups = [], gmap = {};
    visibleDishes.forEach(dh => {
      const s = dh.stall || "自选菜";
      if (!gmap[s]) { gmap[s] = []; groups.push({ name: s, list: gmap[s] }); }
      gmap[s].push(dh);
    });
    groups.sort((a, b) => {
      const ia = order.indexOf(a.name), ib = order.indexOf(b.name);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    });
    buffetStallHtml = groups.map(g => {
      const list = [...g.list].sort((a, b) => (b.good_cnt || 0) - (a.good_cnt || 0) || (a.bad_cnt || 0) - (b.bad_cnt || 0) || a.id - b.id);
      const sg = list.reduce((s, x) => s + (x.good_cnt || 0), 0);
      const sb = list.reduce((s, x) => s + (x.bad_cnt || 0), 0);
      return `
      <div class="stall-block">
        <div class="stall-head"><span class="stall-name">${icon("store")} ${esc(g.name)}</span>
          <span class="stall-sum">好评 <b class="good-num">${sg}</b> · 差评 <b class="${sb ? "bad-num" : ""}">${sb}</b></span></div>
        ${list.map(dh => buffetDishHtml(dh)).join("")}
      </div>`;
    }).join("");
  } else {
    dishes = visibleDishes.map(dh => `
    <div class="dish-card">
      <div class="dish-photo">${dh.photo ? `<img src="/uploads/${esc(dh.photo)}" alt="${esc(dh.name)}">`
        : `<div class="ph">${icon("image")}</div>`}</div>
      <div class="dish-body">
        <div class="dish-name"><span>${esc(dh.name)}</span><span class="dish-price">¥${dh.price.toFixed ? dh.price.toFixed(1) : dh.price}</span>${starBtn(dh.id)}</div>
        <div class="dish-intro">${esc(dh.intro) || '<span class="faint">商家暂未填写简介</span>'}</div>
        <div class="dish-updated">更新于 ${fmtDate(dh.updated_at)}</div>
      </div>
    </div>`).join("");
  }

  const buffetSumGood = d.dishes.reduce((s, x) => s + (x.good_cnt || 0), 0);
  let fqBadge = "";
  if (w.weight_min != null && w.weight_max != null) {
    const pMin = Math.min(98, Math.round(w.weight_min / 5));          /* 条形刻度 0~500g */
    const pW = Math.max(4, Math.round((w.weight_max - w.weight_min) / 5));
    const pWc = Math.min(100 - pMin, pW);
    fqBadge = `
    <div class="fq-badge" title="商家自报的主要食材重量区间，仅供参考">
      <span class="fq-label">⚖️ 食材重量</span>
      <span class="fq-val">${w.weight_min}g~${w.weight_max}g</span>
      <div class="fq-track"><div class="fq-fill" style="left:${pMin}%;width:${pWc}%"></div></div>
    </div>`;
  }
  const buffetSumBad = d.dishes.reduce((s, x) => s + (x.bad_cnt || 0), 0);

  const dishOpts = ['<option value="">不关联菜品</option>']
    .concat(d.dishes.map(x => `<option value="${x.id}">${esc(x.name)}</option>`)).join("");

  let rateBox = "";
  if (closed) {
    rateBox = `<span class="pill gray">${icon("info")} 窗口已停用，暂不能打分</span>`;
  } else if (d.my_today_score != null) {
    const myCat = d.my_today_score >= 4 ? "好评 👍" : "差评 👎";
    rateBox = `<span class="pill ok">${icon("check")} 今天已评价：${myCat}，明天再来</span>`;
  } else if (d.quota_left <= 0) {
    rateBox = `<span class="pill warn">${icon("timer")} 今日 3 次评价机会已用完</span>`;
  } else {
    rateBox = `<div class="rate-btns">
      <button class="rate-btn good" data-act="rate-good" title="好评，点击即提交">${icon("thumbsUp")} 好评</button>
      <button class="rate-btn bad" data-act="rate-bad" title="差评，需填写理由">${icon("thumbsDown")} 差评</button>
    </div>
    <div class="rate-tip">好评点击即提交；差评需填写理由，<b>有理有据</b>的反馈才能帮食堂改进 · 今天还能评价 <b>${d.quota_left}</b> 个窗口</div>`;
  }

  const posts = pr.ok ? pr.data.posts : [];
  const postHtml = posts.map(p => postHtml_(p)).join("");

  $("#view").innerHTML = `
    <div class="crumb">
      <button class="btn btn-ghost btn-sm btn-back" data-act="go-back" title="返回上一页">${icon("back")} 返回</button>
      <span class="crumb-sep"></span>
      <span data-act="go-canteens" class="link">${icon("grid")} 食堂</span>
      ${icon("chevronRight")} <span>${loc(w)}</span></div>
    <div class="card" style="margin-bottom:14px">
      <div class="win-head">
        <div><h2>${icon("utensils")} ${esc(w.name)} ${buffet ? '<span class="pill">自选餐档口</span>' : ""} ${closed ? '<span class="tag off">已停用</span>' : ""}
          ${w.rank ? `<span class="rank-badge" style="position:static;display:inline-flex;vertical-align:middle;margin-top:4px">本月 #${w.rank}</span>` : ""}</h2>
          <div class="wm">${loc(w)} · 商家：${esc(w.merchant_name)}</div>
          ${fqBadge}</div>
        <div class="win-stats">
          <div class="ws-item"><div class="v">${w.avg_score != null ? w.avg_score.toFixed(1) : "—"}</div><div class="l">本月均分 ${stars(w.avg_score)}</div></div>
          <div class="ws-item"><div class="v">${w.month_cnt}</div><div class="l">本月评分人数</div></div>
          <div class="ws-item"><div class="v good-num">${w.good_cnt || 0}</div><div class="l">本月好评</div></div>
          <div class="ws-item"><div class="v ${w.bad_cnt ? "bad-num" : ""}">${w.bad_cnt || 0}</div><div class="l">本月差评</div></div>
          <div class="ws-item"><div class="v">${w.total_cnt}</div><div class="l">累计评分</div></div>
          <div class="ws-item"><div class="v">${w.post_cnt}</div><div class="l">讨论帖</div></div>
        </div>
      </div>
      <div class="rate-panel">${rateBox}</div>
    </div>
    ${buffet ? `
    <div class="card tips-card">
      <div class="tips-title">${icon("info")} 选菜技巧 <span class="cnt">（自选餐档口专用）</span></div>
      <div class="tips-list">${BUFFET_TIPS.map(t => `<div class="tip-item"><b>${t[0]}</b><span>${t[1]}</span></div>`).join("")}</div>
      <div class="tips-sum">本档口累计收到好评 <b class="good-num">${buffetSumGood}</b> · 差评 <b class="${buffetSumBad ? "bad-num" : ""}">${buffetSumBad}</b>，你的投票会直接帮同学选菜、帮档口改进</div>
    </div>` : ""}
    <div class="sec-title">${icon("utensils")} ${buffet
      ? `自选菜品 <span class="cnt">（按档口分组 · 组内按好评数排序 · 点 👍👎 帮同学选菜，每人每菜每天一票）</span>`
      : `今日菜品 <span class="cnt">（价格以商家当日发布为准）</span>`}
      <button class="btn btn-sm btn-ghost fav-filter-btn ${favOnly ? "on" : ""}" data-act="fav-filter" title="只显示我收藏的菜品">${favOnly ? "★" : "☆"} 只看收藏</button></div>
    ${buffet
      ? (buffetStallHtml || `<div class="empty">${icon("utensils")} ${favOnly ? "还没有收藏的菜品，点菜品旁的 ☆ 收藏吧" : "商家还未上架菜品"}</div>`)
      : `<div class="dish-grid">${dishes || `<div class="empty" style="grid-column:1/-1">${icon("utensils")} ${favOnly ? "还没有收藏的菜品，点菜品旁的 ☆ 收藏吧" : "商家还未上架菜品"}</div>`}</div>`}
    <div class="sec-title">${icon("message")} 匿名讨论区 <span class="cnt">（发帖无需登录、不显示任何真实信息）</span></div>
    ${closed ? "" : `
    <div class="card post-box">
      <textarea id="postContent" maxlength="500" placeholder="说说这家窗口的味道、分量、排队情况…（匿名发布）"></textarea>
      <div id="postPhotoPreview"></div>
      <div class="post-tools">
        <select id="postCat" title="评论类别">
          <option value="">讨论</option>
          <option value="good">好评</option>
          <option value="bad">差评</option>
        </select>
        <select id="postDish">${dishOpts}</select>
        <label class="photo-pick" id="postPhotoPick">${icon("camera")} <span>加张照片</span>
          <input type="file" id="postPhotoInput" accept="image/*"></label>
        <span class="char-count" id="charCount">0/500</span>
        <button class="btn btn-primary" data-act="submit-post">${icon("send")} 匿名发布</button>
      </div>
    </div>`}
    <div id="postsWrap">${postHtml || `<div class="empty">${icon("message")} 还没有讨论，来抢个沙发？</div>`}</div>`;

  const ta = $("#postContent");
  if (ta) ta.addEventListener("input", () => { $("#charCount").textContent = ta.value.length + "/500"; });
  const pin = $("#postPhotoInput");
  if (pin) pin.addEventListener("change", async () => {
    const f = pin.files && pin.files[0];
    if (!f) return;
    try {
      const small = await compressImage(f, 1280, 0.82);
      S.postPhotoFile = small;
      $("#postPhotoPreview").innerHTML =
        `<div class="photo-preview"><img src="${URL.createObjectURL(small)}" alt="">
          <button class="photo-del" data-act="clear-post-photo" title="移除照片">${icon("x")}</button></div>`;
      const pick = $("#postPhotoPick");
      if (pick) pick.querySelector("span").textContent = "换一张";
    } catch (e) { toast("图片处理失败，换一张试试", "err"); }
  });
  bindRateHover();
}

function postHtml_(p, isReply) {
  const nick = esc(p.nickname);
  const initial = p.nickname ? p.nickname.slice(0, 1) : "匿";
  return `
  <div class="post" data-pid="${p.id}">
    <div class="post-head"><span class="avatar">${esc(initial)}</span>
      <div><span class="post-nick">${nick}</span>
        ${p.category === "bad" ? '<span class="post-cat bad">差评</span>' : p.category === "good" ? '<span class="post-cat good">好评</span>' : ""}
        <span class="post-time">${fmtTime(p.created_at)}</span></div></div>
    ${p.dish ? `<div class="dish-tag">${icon("utensils")} ${esc(p.dish.name)}（¥${p.dish.price}）</div>` : ""}
    <div class="post-content">${esc(p.content)}</div>
    ${p.photo ? `<img class="post-photo" src="/uploads/${esc(p.photo)}" alt="留言照片" loading="lazy"
        data-act="view-photo" data-src="/uploads/${esc(p.photo)}">` : ""}
    <div class="post-actions">
      <button class="pa ${p.liked ? "liked" : ""}" data-act="like" data-id="${p.id}">${icon("thumbsUp")} <span class="n">${p.likes}</span></button>
      ${isReply ? "" : `<button class="pa" data-act="reply-toggle" data-id="${p.id}">${icon("reply")} 回复 <span class="n">${p.reply_count || 0}</span></button>`}
      <button class="pa" data-act="report" data-id="${p.id}" title="举报">${icon("flag")} 举报</button>
    </div>
    ${isReply ? "" : `
    <div class="reply-area" id="ra-${p.id}" style="display:none">
      <div class="replies">${(p.replies || []).map(r => postHtml_(r, true)).join("")}</div>
      <div class="reply-form">
        <input id="ri-${p.id}" maxlength="500" placeholder="匿名回复…">
        <button class="btn btn-primary btn-sm" data-act="reply-send" data-id="${p.id}">${icon("send")}</button>
      </div>
    </div>`}
  </div>`;
}

function bindRateHover() {
  const box = $("#rateBox");
  if (!box) return;
  const btns = $$("button", box);
  const paint = v => btns.forEach(b => { const s = +b.dataset.v; $("svg", b).classList.toggle("on", s <= v); });
  btns.forEach(b => {
    b.addEventListener("mouseover", () => paint(+b.dataset.v));
    b.addEventListener("mouseout", () => paint(S.hoverScore));
  });
}

/* ------------------------------------------------------------ 我的页 */
async function renderMy() {
  const r = await api("/api/my");
  if (!r.ok) { $("#view").innerHTML = `<div class="empty">${icon("alert")} ${esc(r.msg)}</div>`; return; }
  const d = r.data;
  const initial = d.nickname ? d.nickname.slice(0, 1) : "匿";
  const ratings = d.ratings.map(x => `
    <div class="rank-row" data-act="go-window" data-id="${x.window_id}">
      <div class="rank-no ${x.score >= 4 ? "good" : "bad"}">${x.score >= 4 ? "好评" : "差评"}</div>
      <div class="rank-main"><div class="rn">${esc(x.window_name)}</div><div class="rl">${loc(x)}</div></div>
      <div class="rank-cnt">${x.date}</div>${icon("chevronRight")}</div>`).join("");
  const posts = d.posts.map(x => `
    <div class="rank-row" data-act="go-window" data-id="${x.window_id}">
      <div class="rank-no">${icon(x.parent_id ? "reply" : "message")}</div>
      <div class="rank-main"><div class="rn" style="font-weight:400;font-size:13px">${x.category === "bad" ? '<span class="post-cat bad">差评</span> ' : x.category === "good" ? '<span class="post-cat good">好评</span> ' : ""}${esc(x.content)}</div>
        <div class="rl">${esc(x.window_name)} · ${fmtTime(x.created_at)}</div></div></div>`).join("");
  $("#view").innerHTML = `
    <div class="page-head"><div><h1>${icon("user")} 我的</h1></div>
      <button class="btn btn-ghost" data-act="anon-reset">${icon("refresh")} 换一个匿名身份</button></div>
    <div class="profile-hero">
      <span class="avatar">${esc(initial)}</span>
      <div><h2>${esc(d.nickname)}</h2>
        <div class="anon-note">${icon("shield")} 你的身份是系统随机生成的代号，不绑定学号、姓名、手机号，任何其他同学、商家、管理员都无法查到你的真实信息。</div>
        <div style="font-size:11.5px;opacity:.75;margin-top:6px">身份创建于 ${esc(d.created_at)}</div></div>
    </div>
    <div class="stat-grid" style="margin-top:14px">
      <div class="stat-card"><div class="sv">${d.quota_left}</div><div class="sl">${icon("timer")} 今日剩余打分次数</div></div>
      <div class="stat-card"><div class="sv">${d.ratings.length}</div><div class="sl">${icon("star")} 我的评分记录</div></div>
      <div class="stat-card"><div class="sv">${d.posts.length}</div><div class="sl">${icon("message")} 我的发帖回复</div></div>
      <div class="stat-card"><div class="sv">${d.likes_given}</div><div class="sl">${icon("thumbsUp")} 我点过的赞</div></div>
    </div>
    ${tasteProfileHtml(d)}
    <div class="sec-title">${icon("star")} 我的评分历史</div>
    <div class="card" style="padding:8px 10px">${ratings || '<div class="empty">还没有打过分，去食堂页逛逛吧</div>'}</div>
    <div class="sec-title">${icon("message")} 我的发帖记录</div>
    <div class="card" style="padding:8px 10px">${posts || '<div class="empty">还没有发过帖</div>'}</div>
    <div class="sec-title">${icon("key")} 身份入口</div>
    <div class="card" style="padding:14px">
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <a class="btn btn-ghost" href="#/merchant">${icon("store")} 商家登录</a>
        <a class="btn btn-ghost" href="#/admin">${icon("shield")} 管理员登录</a>
      </div>
      <div style="font-size:11.5px;color:var(--faint);margin-top:9px;line-height:1.7">
        商家账号形如 <b>c1-1-01</b>（食堂-楼层-窗口），初始密码 shop123456，登录后可改。<br>
        管理员账号由学校统一分配。
      </div>
    </div>`;
}

/* ------------------------------------------------------------ 口味画像：从我的评分自动归纳 */
const TASTE_DIMS = [
  ["🍜 面食党", ["面", "粉", "米线", "馄饨", "饺子", "拉面", "螺蛳", "炒面"]],
  ["🍚 米饭党", ["饭", "盖浇", "套餐", "烧腊", "黄焖", "炒饭", "拌饭", "便当"]],
  ["🌶️ 无辣不欢", ["辣", "麻", "川", "湘", "冒菜", "火锅", "小炒"]],
  ["🍰 甜品控", ["甜", "糖水", "果捞", "烘焙", "咖啡", "点心", "奶茶", "冰淇淋", "蛋糕", "茶"]],
  ["🥬 清淡养生", ["粥", "汤", "轻食", "素食", "蒸", "沙拉", "养生"]],
  ["🍖 肉食动物", ["烧", "烤", "鸡", "肉", "卤", "牛", "羊", "鱼", "虾", "肘"]],
];

function tasteProfileHtml(d) {
  const rs = d.ratings || [];
  if (rs.length < 3) return `
    <div class="sec-title">${icon("sparkles")} 我的口味画像</div>
    <div class="card taste-card"><div class="taste-empty">评 3 个以上窗口后，这里会自动生成你的口味画像 🥢</div></div>`;
  const scored = {};
  rs.forEach(r => { (scored[r.window_id] = scored[r.window_id] || []).push(r); });
  const wins = Object.values(scored).map(list => ({
    name: list[0].window_name,
    avg: list.reduce((s, x) => s + x.score, 0) / list.length,
  }));
  const dimCnt = TASTE_DIMS.map(([label, kws]) => {
    const n = wins.filter(w => kws.some(k => (w.name || "").indexOf(k) >= 0)).length;
    return { label, n };
  }).sort((a, b) => b.n - a.n);
  const top = dimCnt.filter(x => x.n > 0).slice(0, 3);
  const goodRate = Math.round(rs.filter(r => r.score >= 4).length / rs.length * 100);
  const badge = rs.length >= 10 && goodRate >= 70 ? "资深鉴味官"
    : rs.length >= 5 ? "干饭常客" : "食堂新面孔";
  const max = top.length ? top[0].n : 1;
  return `
    <div class="sec-title">${icon("sparkles")} 我的口味画像 <span class="cnt">（根据 ${rs.length} 次评分自动归纳）</span></div>
    <div class="card taste-card">
      <div class="taste-hero">你是一位 <b>${top.length ? top[0].label : "均衡干饭人"}</b>，称号：<b class="taste-badge">${badge}</b></div>
      <div class="taste-bars">${top.map(x => `
        <div class="taste-bar">
          <span class="tb-name">${x.label}</span>
          <div class="tb-track"><div class="tb-fill" style="width:${Math.round(x.n / max * 100)}%"></div></div>
          <span class="tb-cnt">${x.n} 窗口</span>
        </div>`).join("")}</div>
      <div class="taste-note">你的好评率 ${goodRate}% · 评价过 ${wins.length} 个窗口 · 最常吃：${esc((wins[0] || {}).name || "")}${wins.length > 1 ? " 等窗口" : ""}</div>
    </div>`;
}

/* ------------------------------------------------------------ 差评避雷页 */
async function renderAvoid() {
  const r = await api("/api/warnings");
  if (!r.ok) { $("#view").innerHTML = `<div class="empty">${icon("alert")} ${esc(r.msg)}</div>`; return; }
  const d = r.data;
  const items = d.items || [];
  $("#view").innerHTML = `
    <div class="page-head"><div><h1>${icon("alert")} 差评避雷</h1>
      <div class="sub">集中收录全食堂差评 · 选窗口前先看看，少踩雷</div></div></div>
    <div class="card warn-notice">
      <b>${icon("info")} 差评须知：</b>不要随意差评。差评要有理有据地说明情况（哪道菜、什么问题、什么时间），平台<b>支持合理差评</b>——它是食堂改进的重要依据；恶意差评、情绪化攻击将被管理员删除处理。
    </div>
    <div class="stat-grid">
      <div class="stat-card"><div class="sv">${d.month_bad_cnt}</div><div class="sl">${icon("flag")} 本月差评数</div></div>
      <div class="stat-card"><div class="sv">${d.window_cnt}</div><div class="sl">${icon("store")} 涉及窗口数</div></div>
    </div>
    ${(d.top_windows || []).length ? `
    <div class="sec-title">${icon("flame")} 本月差评最多的窗口</div>
    <div class="card" style="padding:8px 10px">${d.top_windows.map(w => `
      <div class="rank-row" data-act="go-window" data-id="${w.id}">
        <div class="rank-no bad">${w.bad_cnt}</div>
        <div class="rank-main"><div class="rn">${esc(w.name)}</div><div class="rl">${loc(w)}</div></div>
        <div class="rank-cnt">${w.bad_cnt} 条差评</div>${icon("chevronRight")}</div>`).join("")}</div>` : ""}
    <div class="sec-title">${icon("message")} 最新差评</div>
    ${items.map(p => `
      <div class="card avoid-item" data-act="go-window" data-id="${p.window_id}">
        <div class="ai-head"><span class="post-cat bad">差评</span>
          <b>${esc(p.window_name)}</b><span class="rl">${loc(p)}</span>
          <span class="ai-time">${fmtTime(p.created_at)}</span></div>
        <div class="ai-content">${esc(p.content)}</div>
        ${p.photo ? `<img class="ai-photo" src="/uploads/${esc(p.photo)}" alt="差评照片" loading="lazy">` : ""}
        <div class="ai-foot"><span>${icon("thumbsUp")} ${p.likes}</span><span>${icon("message")} ${p.reply_count}</span><span>${icon("shield")} 匿名同学：${esc(p.nickname)}</span></div>
      </div>`).join("") || `<div class="empty">${icon("check")} 本月还没有差评，都是好口碑</div>`}`;
}

/* ------------------------------------------------------------ 登录页 */
function renderLogin(kind) {
  const isAdmin = kind === "admin";
  const mobileTip = (document.body.dataset.device === "mobile")
    ? `<div class="login-device-tip">${icon("info")} 已识别到你在用<b>${document.body.dataset.deviceLabel || "手机端"}</b>：工作台建议用电脑访问，手机可继续但操作受限</div>`
    : "";
  $("#view").innerHTML = `
    <div class="login-wrap"><div class="card">
      <div class="login-back"><button class="btn btn-ghost btn-sm" data-act="go-back-login" title="返回上一页">${icon("back")} 返回</button></div>
      <h2>${icon(isAdmin ? "shield" : "store")} ${isAdmin ? "管理员登录" : "商家登录"}</h2>
      <div class="sub">${isAdmin ? "窗口管理 · 帖子审核 · 商家账号维护" : "管理本窗口的菜品、菜价与照片"}</div>
      ${mobileTip}
      <form id="loginForm">
        <div class="field"><label>账号</label><input id="lgUser" autocomplete="username" placeholder="${isAdmin ? "admin" : "如 c1-1-01（一食堂一楼01号）"}"></div>
        <div class="field"><label>密码</label><input id="lgPass" type="password" autocomplete="current-password" placeholder="请输入密码"></div>
        <button class="btn btn-primary" style="width:100%" type="submit">${icon("lock")} 登录</button>
      </form>
      <div class="login-tip">${isAdmin
        ? "演示环境默认账号：admin / admin@2026（上线后请立即在「改密码」中修改）"
        : "商家账号由管理员预建后线下发放，格式：c食堂-楼层-窗口号，初始密码 shop123456，登录后可请管理员重置"}</div>
      <div style="text-align:center;margin-top:14px"><a class="link" href="#/leaderboard">← 返回学生视角（无需登录）</a></div>
    </div></div>`;
  $("#loginForm").addEventListener("submit", async e => {
    e.preventDefault();
    const r = await api("/api/auth/login", "POST", { role: isAdmin ? "admin" : "merchant",
      username: $("#lgUser").value.trim(), password: $("#lgPass").value });
    if (!r.ok) { toast(r.msg, "err"); return; }
    toast("登录成功");
    await refreshBoot();
    location.hash = isAdmin ? "#/admin" : "#/merchant";
    route();
  });
}

/* ------------------------------------------------------------ 管理员端 */
async function renderAdmin() {
  if (!S.boot || S.boot.role !== "admin") { renderLogin("admin"); return; }
  const tabs = [["dashboard", "chart", "数据看板"], ["windows", "store", "窗口管理"], ["posts", "message", "帖子管理"],
    ["reports", "flag", "举报处理"], ["logs", "clock", "操作日志"]];
  $("#view").innerHTML = `
    <div class="page-head"><div><h1>${icon("shield")} 管理中心</h1>
      <div class="sub">窗口与商家账号维护 · 违规帖子处理 · 数据总览</div></div></div>
    <div class="tabs">${tabs.map(t => `<button class="${S.adminTab === t[0] ? "active" : ""}" data-act="admin-tab" data-v="${t[0]}">${icon(t[1])} ${t[2]}</button>`).join("")}</div>
    <div id="adminBody"></div>`;
  const body = $("#adminBody");
  if (S.adminTab === "dashboard") {
    const r = await api("/api/admin/dashboard");
    if (!r.ok) { body.innerHTML = `<div class="empty">${esc(r.msg)}</div>`; return; }
    const d = r.data;
    body.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card"><div class="sv">${d.active_cnt}/${d.window_cnt}</div><div class="sl">${icon("store")} 营业窗口 / 总窗口</div></div>
        <div class="stat-card"><div class="sv">${d.dish_cnt}</div><div class="sl">${icon("utensils")} 在售菜品数</div></div>
        <div class="stat-card"><div class="sv">${d.month_ratings}</div><div class="sl">${icon("star")} 本月评分数</div></div>
        <div class="stat-card"><div class="sv">${d.today_ratings}</div><div class="sl">${icon("timer")} 今日评分数</div></div>
        <div class="stat-card"><div class="sv">${d.month_posts}</div><div class="sl">${icon("message")} 本月发帖数</div></div>
        <div class="stat-card"><div class="sv ${d.pending_reports ? "warn" : ""}">${d.pending_reports}</div><div class="sl">${icon("flag")} 待处理举报 ${d.pending_reports ? "（需关注）" : ""}</div></div>
        <div class="stat-card"><div class="sv">${d.anon_cnt}</div><div class="sl">${icon("users")} 匿名同学数（无真实信息）</div></div>
      </div>
      <div class="sec-title">${icon("flame")} ${d.month} 月榜 Top 5</div>
      <div class="card" style="padding:8px 10px">${d.top5.map((w, i) => `
        <div class="rank-row" data-act="go-window" data-id="${w.id}">
          <div class="rank-no ${i < 3 ? "r" + (i + 1) : ""}">${i + 1}</div>
          <div class="rank-main"><div class="rn">${esc(w.name)}</div><div class="rl">${loc(w)}</div></div>
          ${stars(w.avg_score)}<div class="rank-score">${w.avg_score.toFixed(1)}</div>
          <div class="rank-cnt">${w.cnt} 人评</div></div>`).join("")}</div>`;
  } else if (S.adminTab === "windows") {
    const wr = await api("/api/admin/windows");
    if (!wr.ok) { body.innerHTML = `<div class="empty">${esc(wr.msg)}</div>`; return; }
    body.innerHTML = `<div class="card tbl-wrap"><table class="tbl">
      <tr><th>位置</th><th>窗口名</th><th>商家</th><th>商家账号</th><th>在售菜品</th><th>本月评分</th><th>状态</th><th>操作</th></tr>
      ${wr.data.windows.map(w => `<tr class="${w.status === 1 ? "" : "off"}">
        <td>${loc(w)}</td><td><b>${esc(w.name)}</b></td><td>${esc(w.merchant_name)}</td>
        <td><code>${esc(w.merchant_user)}</code></td><td>${w.dish_cnt}</td><td>${w.month_cnt}</td>
        <td><span class="tag ${w.status === 1 ? "on" : "off"}">${w.status === 1 ? "营业" : "停用"}</span></td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-act="admin-edit-window" data-id="${w.id}">${icon("edit")} 编辑</button>
          <button class="btn btn-ghost btn-sm" data-act="admin-reset-pw" data-id="${w.id}">${icon("key")} 重置商家密码</button>
        </td></tr>`).join("")}</table></div>`;
  } else if (S.adminTab === "posts") {
    const pr = await api("/api/admin/posts" + (S.postsFilter !== "all" ? "?status=" + S.postsFilter : ""));
    if (!pr.ok) { body.innerHTML = `<div class="empty">${esc(pr.msg)}</div>`; return; }
    body.innerHTML = `
      <div class="tabs">
        ${[["1", "正常帖子"], ["0", "已删除"], ["all", "全部"]].map(f =>
          `<button class="${S.postsFilter === f[0] ? "active" : ""}" data-act="admin-post-filter" data-v="${f[0]}">${f[1]}</button>`).join("")}
      </div>
      <div class="card tbl-wrap"><table class="tbl">
      <tr><th>时间</th><th>窗口</th><th>匿名昵称</th><th>内容</th><th>赞</th><th>待处理举报</th><th>状态</th><th>操作</th></tr>
      ${pr.data.posts.map(p => `<tr>
        <td style="white-space:nowrap">${fmtDate(p.created_at)}</td>
        <td style="white-space:nowrap">${esc(p.window_name)}</td>
        <td>${esc(p.nickname)}</td>
        <td style="max-width:300px">${esc(p.content)}</td>
        <td>${p.likes}</td>
        <td>${p.pending_reports ? `<span class="tag warn">${p.pending_reports} 条</span>` : "—"}</td>
        <td><span class="tag ${p.status === 1 ? "on" : "del"}">${p.parent_id ? "回复·" : ""}${p.status === 1 ? "正常" : "已删"}</span></td>
        <td style="white-space:nowrap">${p.status === 1
          ? `<button class="btn btn-danger btn-sm" data-act="admin-del-post" data-id="${p.id}">${icon("trash")} 删除</button>`
          : `<button class="btn btn-ok btn-sm" data-act="admin-restore-post" data-id="${p.id}">${icon("restore")} 恢复</button>`}</td>
      </tr>`).join("") || '<tr><td colspan="8" class="empty">暂无帖子</td></tr>'}</table></div>`;
  } else if (S.adminTab === "reports") {
    const rr = await api("/api/admin/reports?status=" + S.reportsTab);
    if (!rr.ok) { body.innerHTML = `<div class="empty">${esc(rr.msg)}</div>`; return; }
    body.innerHTML = `
      <div class="tabs">${[[0, "待处理"], [1, "已删帖"], [2, "已驳回"]].map(t =>
        `<button class="${S.reportsTab === t[0] ? "active" : ""}" data-act="admin-report-tab" data-v="${t[0]}">${t[1]}</button>`).join("")}</div>
      ${rr.data.reports.map(rp => `
        <div class="report-card">
          <div class="rc-head"><span>${icon("flag")} 举报理由：<b>${esc(rp.reason)}</b></span>
            <span>${fmtTime(rp.report_time)} · ${esc(rp.window_name)} · 举报人：${esc(rp.nickname)}</span></div>
          <div class="rc-content">${esc(rp.content)} ${rp.post_status !== 1 ? '<span class="tag del">帖子已删除</span>' : ""}</div>
          ${S.reportsTab === 0 ? `<div style="display:flex;gap:8px">
            <button class="btn btn-danger" data-act="report-resolve" data-rid="${rp.report_id}" data-v="delete">${icon("trash")} 属实，删除帖子</button>
            <button class="btn btn-ghost" data-act="report-resolve" data-rid="${rp.report_id}" data-v="dismiss">不属实，驳回举报</button>
          </div>` : `<span class="tag ${rp.status === 1 ? "del" : "off"}">${rp.status === 1 ? "已删除帖子" : "已驳回"}</span>`}
        </div>`).join("") || `<div class="empty">${icon("check")} 这里空空如也，一切正常</div>`}`;
  } else if (S.adminTab === "logs") {
    const lr = await api("/api/admin/logs");
    if (!lr.ok) { body.innerHTML = `<div class="empty">${esc(lr.msg)}</div>`; return; }
    body.innerHTML = `<div class="card">${lr.data.logs.map(l => `
      <div class="log-item"><span class="lt">${l.created_at}</span>
        <span><b>${esc(l.action)}</b> · <span class="muted">${esc(l.detail)}</span></span></div>`).join("")
      || '<div class="empty">暂无操作日志</div>'}</div>`;
  }
}

function adminEditWindowModal(w) {
  modal(`<h3>${icon("edit")} 编辑窗口信息</h3>
    <div class="m-sub">${loc(w)} · 商家账号 <code>${esc(w.merchant_user)}</code></div>
    <div class="field"><label>窗口名称</label><input id="mWinName" value="${esc(w.name)}" maxlength="30"></div>
    <div class="field"><label>商家名称</label><input id="mMerName" value="${esc(w.merchant_name)}" maxlength="30"></div>
    <div class="field"><label>营业状态</label>
      <select id="mWinStatus"><option value="1" ${w.status === 1 ? "selected" : ""}>营业中</option>
        <option value="0" ${w.status !== 1 ? "selected" : ""}>停用</option></select></div>
    <div class="m-actions"><button class="btn btn-ghost" data-act="modal-close">取消</button>
      <button class="btn btn-primary" data-act="admin-save-window" data-id="${w.id}">保存</button></div>`);
}

function adminChangePwModal() {
  modal(`<h3>${icon("key")} 修改管理员密码</h3>
    <div class="field"><label>原密码</label><input id="pwOld" type="password"></div>
    <div class="field"><label>新密码（至少 8 位）</label><input id="pwNew" type="password"></div>
    <div class="field"><label>确认新密码</label><input id="pwNew2" type="password"></div>
    <div class="m-actions"><button class="btn btn-ghost" data-act="modal-close">取消</button>
      <button class="btn btn-primary" data-act="admin-save-pw">保存</button></div>`);
}

/* ------------------------------------------------------------ 商家端 */
async function renderMerchant() {
  if (!S.boot || S.boot.role !== "merchant") { renderLogin("merchant"); return; }
  const r = await api("/api/merchant/overview");
  if (!r.ok) {
    $("#view").innerHTML = `<div class="empty">${icon("alert")} ${esc(r.msg)} <div style="margin-top:10px"><button class="btn btn-ghost btn-sm" data-act="logout">退出登录</button></div></div>`;
    return;
  }
  const d = r.data, w = d.window;
  const trendMax = Math.max(...d.trend.map(t => t.avg_score || 0), 5);
  $("#view").innerHTML = `
    <div class="page-head"><div><h1>${icon("store")} 商家中心 · ${esc(w.name)}</h1>
      <div class="sub">${loc(w)} · 账号 ${esc(w.merchant_user)}</div></div>
      <button class="btn btn-primary" data-act="dish-add">${icon("plus")} 上架新菜品</button></div>
    <div class="grid" style="grid-template-columns:2fr 1fr;margin-bottom:16px">
      <div class="card"><div class="sec-title" style="margin:2px 0 10px">${icon("trending")} 近 7 天评分趋势</div>
        ${d.trend.length ? `<div class="trend-bars">${d.trend.map(t => `
          <div class="tb"><div class="bar" style="height:${Math.max(4, (t.avg_score || 0) / trendMax * 100)}%">
            <span>${t.avg_score ? t.avg_score.toFixed(1) : ""}</span></div>
            <div class="bd">${t.date.slice(5)}<br>${t.cnt} 评</div></div>`).join("")}</div>`
          : `<div class="empty">近 7 天暂无评分</div>`}</div>
      <div class="card">
        <div style="text-align:center;padding:8px 0">
          <div class="score-big" style="font-size:34px">${w.avg_score != null ? w.avg_score.toFixed(1) : "—"}</div>
          <div style="margin:6px 0">${stars(w.avg_score, "lg")}</div>
          <div class="muted" style="font-size:12px">本月 ${w.month_cnt} 人评分<br>累计 ${w.total_cnt} 人评分</div>
        </div></div>
    </div>
    <div class="card fq-card" style="margin-bottom:16px">
      <div class="sec-title" style="margin:2px 0 8px">${icon("info")} 食材重量标注 <span class="cnt">（向同学诚实展示每份餐主要食材的克重区间）</span></div>
      <div class="fq-form">
        <label>下限 <input type="number" id="fwMin" min="1" max="3000" value="${w.weight_min ?? ""}" placeholder="如 280"></label>
        <span class="fq-sep">~</span>
        <label>上限 <input type="number" id="fwMax" min="1" max="3000" value="${w.weight_max ?? ""}" placeholder="如 350"></label>
        <span class="fq-unit">（克）</span>
        <button class="btn btn-primary btn-sm" data-act="fw-save">${icon("check")} 保存标注</button>
        ${w.weight_min != null ? `<button class="btn btn-ghost btn-sm" data-act="fw-clear">清除标注</button>` : ""}
      </div>
      <div class="fq-hint">填写本窗口每份餐<b>主要食材</b>（肉/面/饭/菜）的大致生重区间：拉面窗口可标「面量 280g~350g」，荤菜窗口标「肉类 120g~150g」。保存后窗口页向所有同学展示重量区间条——分量实打实可称，标注诚实分量是拉好感最直接的方式。</div>
    </div>
    <div class="sec-title">${icon("utensils")} 菜品管理 <span class="cnt">（当日菜价、味道简介、照片随时可更新）</span></div>
    <div class="card tbl-wrap"><table class="tbl">
      <tr><th>照片</th><th>菜品</th><th>当日菜价</th><th>味道简介</th><th>状态</th><th>更新时间</th><th>操作</th></tr>
      ${d.dishes.map(x => `<tr>
        <td>${x.photo ? `<img src="/uploads/${esc(x.photo)}" style="width:52px;height:40px;object-fit:cover;border-radius:6px">` : `<span class="faint">无</span>`}</td>
        <td><b>${esc(x.name)}</b></td><td style="color:#d97706;font-weight:700">¥${x.price}</td>
        <td style="max-width:220px" class="muted">${esc(x.intro) || "—"}</td>
        <td><span class="tag ${x.status === 1 ? "on" : "off"}">${x.status === 1 ? "在售" : "下架"}</span></td>
        <td style="white-space:nowrap">${fmtDate(x.updated_at)}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-ghost btn-sm" data-act="dish-edit" data-id="${x.id}">${icon("edit")} 编辑</button>
          <label class="btn btn-ghost btn-sm" style="cursor:pointer">${icon("image")} 传照片
            <input type="file" accept="image/png,image/jpeg,image/webp" style="display:none"
              data-photo-dish="${x.id}"></label>
          <button class="btn ${x.status === 1 ? "btn-danger" : "btn-ok"} btn-sm" data-act="dish-status" data-id="${x.id}" data-v="${x.status === 1 ? 0 : 1}">
            ${x.status === 1 ? "下架" : "上架"}</button>
        </td></tr>`).join("")}</table></div>
    <div class="sec-title">${icon("message")} 最新学生反馈 <span class="cnt">（只读，无法删除；违规内容由管理员处理）</span></div>
    <div class="card">${d.feedback.map(f => `
      <div class="log-item"><span class="lt">${fmtTime(f.created_at)}</span>
        <span><b>${esc(f.nickname)}</b>：<span class="muted">${esc(f.content)}</span></span></div>`).join("")
    || '<div class="empty">暂无反馈</div>'}</div>`;

  $$("input[data-photo-dish]").forEach(inp => inp.addEventListener("change", async e => {
    const did = +e.target.dataset.photoDish;
    const file = e.target.files[0];
    if (!file) return;
    toast("正在上传照片…", "info");
    try {
      const cf = await compressImage(file, 800, 0.82);
      const fd = new FormData();
      fd.append("photo", cf);
      const res = await apiUpload(`/api/merchant/dishes/${did}/photo`, fd);
      if (res.ok) { toast("照片已更新"); renderMerchant(); }
      else toast(res.msg, "err");
    } catch (err2) { toast(err2.message || "上传失败", "err"); }
  }));
}

function dishFormModal(dish) {
  const isNew = !dish;
  dish = dish || { name: "", price: "", intro: "" };
  modal(`<h3>${icon(isNew ? "plus" : "edit")} ${isNew ? "上架新菜品" : "编辑菜品"}</h3>
    <div class="field"><label>菜品名称</label><input id="dName" value="${esc(dish.name)}" maxlength="40" placeholder="如：招牌黄焖鸡米饭"></div>
    <div class="field"><label>当日菜价（元）</label><input id="dPrice" value="${dish.price}" placeholder="如 16.5"></div>
    <div class="field"><label>味道简介</label><textarea id="dIntro" maxlength="200" style="min-height:70px;width:100%;border:1px solid var(--line);border-radius:9px;padding:9px 12px" placeholder="如：鸡腿肉土豆青椒现焖，汤汁拌饭一绝">${esc(dish.intro)}</textarea></div>
    ${isNew ? "" : `<div class="field"><label>状态</label><select id="dStatus">
      <option value="1" ${dish.status === 1 ? "selected" : ""}>在售</option>
      <option value="0" ${dish.status !== 1 ? "selected" : ""}>下架</option></select></div>`}
    <div class="m-actions"><button class="btn btn-ghost" data-act="modal-close">取消</button>
      <button class="btn btn-primary" data-act="dish-save" data-id="${isNew ? "" : dish.id}">${isNew ? "上架" : "保存"}</button></div>`);
}

/* ------------------------------------------------------------ 路由 */
function route() {
  if (S._routed) S.prevRoute = S.route;   // 记录上一个页面，供返回键使用
  S._routed = true;
  const h = location.hash || "#/leaderboard";
  const parts = h.replace(/^#\//, "").split("/");
  if (S.countdownTimer) { clearInterval(S.countdownTimer); S.countdownTimer = null; }
  const map = { leaderboard: "leaderboard", canteens: "canteens", my: "my", admin: "admin", merchant: "merchant", avoid: "avoid" };
  if (parts[0] === "window" && parts[1]) {
    S.route = "window";
    renderTopbar();
    renderWindow(parts[1]);
  } else {
    S.route = map[parts[0]] || "leaderboard";
    renderTopbar();
    if (S.route === "leaderboard") renderLeaderboard();
    else if (S.route === "canteens") renderCanteens();
    else if (S.route === "my") renderMy();
    else if (S.route === "avoid") renderAvoid();
    else if (S.route === "admin") renderAdmin();
    else if (S.route === "merchant") renderMerchant();
  }
  if (S.route !== "window") document.title = (({ leaderboard: "月度榜单", canteens: "食堂导航", my: "我的", admin: "管理后台", merchant: "商家中心", avoid: "差评避雷" }[S.route] || "") ? ({ leaderboard: "月度榜单", canteens: "食堂导航", my: "我的", admin: "管理后台", merchant: "商家中心", avoid: "差评避雷" }[S.route]) + " · " : "") + "食堂评分墙";
  const TITLES = { leaderboard: "月度榜单", canteens: "食堂导航", avoid: "差评避雷", my: "我的", admin: "管理看板", merchant: "商家中心" };
  document.title = (TITLES[S.route] || "智慧食堂") + " · 智慧食堂";
  window.scrollTo(0, 0);
}

/* ------------------------------------------------------------ AI 点菜助手 */
const AI_CHIPS = [
  "今天有点热，想吃点凉的",
  "想吃辣的过过瘾",
  "没胃口，吃点开胃的",
  "减肥期，想吃低卡的",
  "穷学生，10块钱吃啥",
  "宵夜走起",
];
const AI_TIPS = ["星辰正在翻评分和评论…", "看看本月榜单谁在前列…", "学生评论里找口碑线索…", "快好了，正在排序…"];

function openAiBox() {
  modal(`
    <h3>${icon("sparkles")} AI 点菜助手</h3>
    <div class="m-sub">一句话说你现在想吃啥，结合评分、评论、榜单帮你点菜（由本机星辰大模型驱动）</div>
    <div class="ai-form">
      <input id="aiQ" maxlength="60" placeholder="比如：今天有点热，想吃点凉的">
      <button class="btn btn-primary" data-act="ai-ask">${icon("send")} 问问</button>
    </div>
    <div class="ai-chips">${AI_CHIPS.map(c =>
      `<button class="ai-chip" data-act="ai-chip" data-q="${esc(c)}">${esc(c)}</button>`).join("")}</div>
    <div id="aiResult"></div>
  `);
  const inp = $("#aiQ");
  inp.addEventListener("keydown", e => { if (e.key === "Enter") askAi(); });
  setTimeout(() => { inp.focus(); try { inp.scrollIntoView({ block: "center", behavior: "smooth" }); } catch (e2) {} }, 80);
}

function aiCardsHtml(items, t0) {
  return items.map((it, i) => `
      <div class="ai-card ${it.window_id ? "clickable" : ""}" ${it.window_id ? `data-act="go-window" data-id="${it.window_id}"` : ""}>
        <div class="ai-rank">${i + 1}</div>
        <div class="ai-main">
          <div class="ai-dish">${esc(it.dish)}<span class="ai-price">¥${it.price != null ? it.price : "-"}</span></div>
          <div class="ai-meta">${esc(it.window)} · ${esc(it.loc)}${it.score != null ? ` · 评分 ${it.score}` : ""}</div>
          <div class="ai-reason">${esc(it.reason)}</div>
          ${it.intro ? `<div class="ai-intro">${esc(it.intro)}</div>` : ""}
        </div>
      </div>`).join("");
}

function aiBadgeHtml(engine) {
  if (engine === "teleagent" || engine === "engine") return `<span class="ai-badge ai-badge-star">${icon("sparkles")} 大模型</span>`;
  if (engine === "cloud") return `<span class="ai-badge ai-badge-star">${icon("sparkles")} 云端大模型</span>`;
  return `<span class="ai-badge">${icon("cpu")} 本地智能推荐</span>`;
}

async function askAi(preset) {
  const inp = $("#aiQ");
  const q = (preset || (inp ? inp.value : "") || "").trim();
  if (!q) { toast("先说说你想吃点啥", "err"); if (inp) inp.focus(); return; }
  if (inp) inp.value = q;
  const box = $("#aiResult");
  if (!box) return;

  box.innerHTML = `<div class="ai-loading">
    <div class="ai-spin">${icon("sparkles")}</div>
    <div class="ai-load-text"><b>${esc(q)}</b><span>正在秒查评分/评论/榜单…</span></div>
  </div>`;

  const t0 = performance.now();
  let resp;
  try {
    resp = await fetch("/api/ai/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q }),
    });
  } catch (e) {
    box.innerHTML = `<div class="ai-error">${icon("alert")} 网络异常，请重试</div>`;
    return;
  }
  if (!resp.ok || !resp.body) {
    box.innerHTML = `<div class="ai-error">${icon("alert")} 推荐失败，请重试</div>`;
    return;
  }

  let localShown = false, reasoning = "", text = "", textStarted = false;
  const reader = resp.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!box.isConnected) { try { reader.cancel(); } catch (e) {} return; }
      buf += dec.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const frame = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        const em = frame.match(/^event: (.+)$/m);
        const dm = frame.match(/^data: ([\s\S]+)$/m);
        if (!em || !dm) continue;
        let data;
        try { data = JSON.parse(dm[1]); } catch (e) { continue; }
        const ev = em[1];

        if (ev === "local" && !localShown && data.items) {
          localShown = true;
          const sec = Math.max(1, Math.round((performance.now() - t0) / 1000));
          box.innerHTML = `<div class="ai-done">${aiBadgeHtml("local")}<span class="ai-sec">${sec}s</span></div>` +
            aiCardsHtml(data.items) +
            `<div class="ai-upgrading" id="aiUpgrading">
               <div class="ai-up-spin">${icon("sparkles")}</div>
               <div class="ai-up-text" style="flex:1;min-width:0">
                 <b>AI 正在结合评分/评论/榜单生成推荐…</b>
                 <div class="ai-stream is-think" id="aiStream"></div>
               </div>
             </div>`;
        } else if (ev === "delta") {
          if (data.part === "reasoning") {
            reasoning += data.text;
            const el = $("#aiStream");
            if (el) {
              el.textContent = reasoning.slice(-500);
              el.scrollTop = el.scrollHeight;
            }
          } else {
            if (!textStarted) {
              textStarted = true;
              const el = $("#aiStream");
              if (el) el.textContent = "正在整理推荐…";
            }
            text += data.text;
          }
        } else if (ev === "done") {
          const sec = Math.max(1, Math.round((performance.now() - t0) / 1000));
          const eng = data.engine || "local";
          const items = data.items || [];
          if (eng === "engine" && items.length) {
            box.innerHTML = `<div class="ai-done">${aiBadgeHtml("engine")}<span class="ai-upgraded">${icon("sparkles")} 已升级</span><span class="ai-sec">${sec}s</span></div>` +
              aiCardsHtml(items) +
              `<div class="ai-foot">${icon("sparkles")} 大模型结合评分、评论、榜单的深度推荐</div>`;
          } else if (items.length) {
            box.innerHTML = `<div class="ai-done">${aiBadgeHtml(eng)}<span class="ai-sec">${sec}s</span></div>` +
              aiCardsHtml(items) +
              `<div class="ai-foot">${icon("cpu")} 本机推荐引擎（结合评分、评论、榜单，离线可用）</div>`;
          }
        }
      }
    }
  } catch (e) {
    /* 流中断，保留已渲染内容 */
  }
}

async function startAiUpgrade(btn) {
  const q = (btn && btn.dataset.q) || "";
  const box = $("#aiResult");
  if (!q || !box) return;
  btn.disabled = true;
  const old = box.querySelector(".ai-upgrade-btn");
  if (old) old.remove();

  const bar = document.createElement("div");
  bar.className = "ai-upgrading";
  bar.id = "aiUpgrading";
  bar.innerHTML = `<div class="ai-up-spin">${icon("sparkles")}</div>
    <div class="ai-up-text"><b>星辰大模型正在深度分析评分/评论/榜单…</b>
    <span id="aiUpTip">${AI_TIPS[0]}</span><em id="aiUpTimer">0s</em></div>`;
  box.appendChild(bar);

  let r;
  try { r = await api("/api/ai/upgrade", "POST", { q }); }
  catch (e) { r = { ok: false, msg: "网络异常" }; }
  if (!r.ok) {
    bar.innerHTML = `<div class="ai-up-fail">${icon("info")} ${esc(r.msg || "无法深度分析")}</div>`;
    return;
  }
  const jobId = r.data.job_id;
  let tipI = 0, sec = 0;
  const timer = setInterval(() => {
    sec += 1;
    const t = $("#aiUpTip"), m = $("#aiUpTimer");
    if (t && sec % 5 === 0) t.textContent = AI_TIPS[++tipI % AI_TIPS.length];
    if (m) m.textContent = sec + "s";
  }, 1000);

  const poll = async () => {
    if (!box.isConnected) { clearInterval(timer); return; }
    let s;
    try { s = await api("/api/ai/status/" + jobId); }
    catch (e) { clearInterval(timer); return; }
    if (!s.ok || !box.isConnected) { clearInterval(timer); return; }
    const st = s.data;
    if (st.status === "running") { setTimeout(poll, 1500); return; }
    clearInterval(timer);
    if (st.status === "done" && st.items && st.items.length) {
      box.innerHTML = `<div class="ai-done">${aiBadgeHtml("teleagent")}<span class="ai-upgraded">${icon("sparkles")} 已升级</span><span class="ai-sec">${sec}s</span></div>` +
        aiCardsHtml(st.items) +
        `<div class="ai-foot">${icon("sparkles")} 星辰大模型结合评分、评论、榜单的深度推荐</div>`;
    } else {
      const up = $("#aiUpgrading");
      if (up) up.innerHTML = `<div class="ai-up-fail">${icon("info")} 深度分析未完成，以上为本地推荐结果</div>`;
    }
  };
  setTimeout(poll, 1500);
}

/* ------------------------------------------------------------ 事件分发 */
document.addEventListener("click", async e => {
  const el = e.target.closest("[data-act]");
  if (!el) return;
  const act = el.dataset.act, id = el.dataset.id, v = el.dataset.v;
  switch (act) {
    case "backdrop": if (e.target === el) closeModal(); break;
    case "modal-close": closeModal(); break;
    case "confirm-cancel": closeModal(); App._cf(false); break;
    case "confirm-ok": closeModal(); App._cf(true); break;
    case "go-window": location.hash = "#/window/" + id; break;
    case "go-canteens": location.hash = "#/canteens"; break;
    case "go-back": {
      const from = S.prevRoute;
      location.hash = ["leaderboard", "canteens", "my", "admin", "merchant"].includes(from) ? "#/" + from : "#/canteens";
      break;
    }
    case "go-back-login": {
      const from = S.prevRoute;
      location.hash = ["leaderboard", "canteens", "my"].includes(from) ? "#/" + from : "#/leaderboard";
      break;
    }
    case "dish-vote": {
      el.classList.remove("pop"); void el.offsetWidth; el.classList.add("pop");
      const r = await api(`/api/dishes/${id}/vote`, "POST", { vote: v });
      if (!r.ok) { toast(r.msg, "err"); return; }
      toast(v === "good" ? "已记好评，帮同学们避开了踩雷" : "已记差评，感谢真实反馈");
      renderWindow(S.curWindowId);
      break;
    }
    case "go-avoid": location.hash = "#/avoid"; break;
    case "theme-cycle": cycleTheme(); break;
    case "hero-search": {
      const hv = ($("#heroSearchInput") || {}).value || "";
      if (hv.trim()) sessionStorage.setItem("heroQ", hv.trim());
      location.hash = "#/canteens";
      setTimeout(() => { const si = $("#winSearch"); if (si) si.focus(); }, 300);
      break;
    }
    case "hero-chip": {
      const q = el.dataset.q;
      sessionStorage.setItem("heroQ", q);
      openAiBox();
      setTimeout(() => { const ai = $("#aiQ"); if (ai) { ai.value = q; ai.focus(); } }, 250);
      break;
    }
    case "ai-open": openAiBox(); break;
    case "fav-toggle": {
      const on = favToggle(id);
      el.classList.toggle("on", on);
      el.textContent = on ? "★" : "☆";
      el.title = on ? "取消收藏" : "收藏这道菜";
      toast(on ? "已收藏，窗口页可开启「只看收藏」" : "已取消收藏");
      break;
    }
    case "fav-filter": S.favOnly = !S.favOnly; renderWindow(S.curWindowId); break;
    case "roll-again": rollRandomDish(); break;
    case "roll-price": S.rollPrice = +el.dataset.i; rollRandomDish(); break;
    case "fw-save": {
      const mn = $("#fwMin"), mx = $("#fwMax");
      const r = await api("/api/merchant/food-weight", "POST", { min: mn ? mn.value : "", max: mx ? mx.value : "" });
      if (!r.ok) { toast(r.msg, "err"); return; }
      toast(r.data.cleared ? "已清除食材重量标注" : "食材重量区间已更新，同学在窗口页可见");
      renderMerchant();
      break;
    }
    case "fw-clear": {
      const r = await api("/api/merchant/food-weight", "POST", { min: "", max: "" });
      if (!r.ok) { toast(r.msg, "err"); return; }
      toast("已清除食材重量标注");
      renderMerchant();
      break;
    }
    case "roll-go": closeModal(); location.hash = "#/window/" + id; break;
    case "ai-ask": askAi(); break;
    case "ai-chip": askAi(el.dataset.q); break;
    case "ai-upgrade": startAiUpgrade(el); break;
    case "sel-canteen": S.winSel.canteen = +v; renderCanteens(); break;
    case "sel-floor": S.winSel.floor = +v; renderCanteens(); break;
    case "search-clear": {
      const input = $("#winSearch");
      if (input) input.value = "";
      S.searchQ = "";
      const c = $(".sb-clear"); if (c) c.hidden = true;
      doSearch("");
      break;
    }
    case "anon-reset": {
      const yes = await confirmBox("更换匿名身份？", "你将以一个<b>全新的随机代号</b>继续使用。旧代号下的评分和发帖记录仍会保留（无法与新身份关联），但「我的」页面将看不到它们。", "换新身份", false);
      if (!yes) return;
      const r = await api("/api/anon/reset", "POST");
      if (r.ok) { toast("新身份：" + r.data.nickname); await refreshBoot(); if (S.route === "my") renderMy(); }
      else toast(r.msg, "err");
      break;
    }
    case "rate-good": {
      el.classList.remove("pop"); void el.offsetWidth; el.classList.add("pop");
      const r = await api("/api/rate", "POST", { window_id: S.curWindowId, score: 5 });
      if (!r.ok) { toast(r.msg, "err"); return; }
      toast("好评已提交，谢谢鼓励");
      await refreshBoot();
      renderWindow(S.curWindowId);
      break;
    }
    case "rate-bad": {
      modal(`<h3>${icon("alert")} 提交差评</h3>
        <div class="warn-line">${icon("info")} <b>不要随意差评。</b>请有理有据地说明情况（哪道菜、什么问题、什么时间），平台<b>支持合理差评</b>——它是食堂改进的重要依据；恶意差评、情绪化攻击会被管理员删除。</div>
        <div class="bad-tags">${BAD_TAGS.map(t => `<button class="bad-tag" data-act="bad-tag" data-t="${t}">${t}</button>`).join("")}</div>
        <div class="field"><label>差评理由（可先点上方标签，再补充具体情况，至少 10 个字，匿名发布到该窗口讨论区）</label>
          <textarea id="badReason" maxlength="300" style="min-height:90px;width:100%;border:1px solid var(--line);border-radius:9px;padding:9px 12px" placeholder="例如：今天点的红烧肉肥肉太多、米饭有点夹生，希望改进"></textarea></div>
        <div class="m-actions"><button class="btn btn-ghost" data-act="modal-close">取消</button>
          <button class="btn btn-danger" data-act="rate-bad-submit">提交差评</button></div>`);
      break;
    }
    case "bad-tag": {
      el.classList.toggle("on");
      const ta = $("#badReason");
      if (!ta) break;
      const onTags = [...document.querySelectorAll(".bad-tag.on")].map(b => b.dataset.t);
      const rest = (ta.value || "").replace(/^【[^】]*】\s*/, "");
      ta.value = onTags.length ? "【" + onTags.join("、") + "】" + rest : rest;
      ta.focus();
      break;
    }
    case "rate-bad-submit": {
      const ta = $("#badReason");
      const reason = (ta.value || "").trim();
      if (reason.length < 10) { toast("差评理由至少 10 个字，请把情况说清楚（有理有据）", "err"); return; }
      const r1 = await api("/api/rate", "POST", { window_id: S.curWindowId, score: 1 });
      if (!r1.ok) { toast(r1.msg, "err"); return; }
      const r2 = await api("/api/posts", "POST", { window_id: S.curWindowId, content: reason, category: "bad" });
      closeModal();
      if (!r2.ok) toast("差评已计入，但差评帖发布失败：" + (r2.msg || ""), "err");
      else toast("差评已提交，感谢有理有据的反馈");
      await refreshBoot();
      renderWindow(S.curWindowId);
      break;
    }
    case "submit-post": {
      const ta = $("#postContent");
      const content = ta.value.trim();
      if (!content && !S.postPhotoFile) { toast("写点内容或加张照片再发布吧", "err"); return; }
      const dishSel = $("#postDish");
      const catSel = $("#postCat");
      const category = catSel ? catSel.value : "";
      if (category === "bad" && content.length < 10) {
        toast("差评需要有理有据：请至少用 10 个字说明情况", "err"); return;
      }
      const r = await api("/api/posts", "POST", {
        window_id: S.curWindowId,
        content: content || "分享一张实拍照片",
        dish_id: dishSel.value ? +dishSel.value : null,
        category,
      });
      if (!r.ok) { toast(r.msg, "err"); return; }
      if (S.postPhotoFile) {
        const fd = new FormData();
        fd.append("photo", S.postPhotoFile);
        const up = await apiUpload("/api/posts/" + r.data.post.id + "/photo", fd);
        if (!up.ok) toast("照片没传上去：" + (up.msg || "请重试"), "err");
      }
      S.postPhotoFile = null;
      toast("已匿名发布");
      renderWindow(S.curWindowId);
      break;
    }
    case "clear-post-photo": {
      S.postPhotoFile = null;
      const box = $("#postPhotoPreview");
      if (box) box.innerHTML = "";
      const pick = $("#postPhotoPick");
      if (pick) pick.querySelector("span").textContent = "加张照片";
      break;
    }
    case "close-modal": { closeModal(); break; }
    case "view-photo": {
      modal(`<div class="lightbox"><img src="${el.dataset.src}" alt=""><button class="lb-close" data-act="close-modal">${icon("x")}</button></div>`);
      break;
    }
    case "like": {
      const r = await api(`/api/posts/${id}/like`, "POST");
      if (!r.ok) { toast(r.msg, "err"); return; }
      el.classList.toggle("liked", r.data.liked);
      $(".n", el).textContent = r.data.likes;
      break;
    }
    case "reply-toggle": {
      const area = $("#ra-" + id);
      area.style.display = area.style.display === "none" ? "block" : "none";
      if (area.style.display === "block") { const inp = $("#ri-" + id); if (inp) inp.focus(); }
      break;
    }
    case "reply-send": {
      const inp = $("#ri-" + id);
      const content = inp.value.trim();
      if (!content) { toast("回复内容不能为空", "err"); return; }
      const r = await api(`/api/posts/${id}/reply`, "POST", { content });
      if (!r.ok) { toast(r.msg, "err"); return; }
      toast("回复成功");
      renderWindow(S.curWindowId);
      break;
    }
    case "report": {
      modal(`<h3>${icon("flag")} 举报这条帖子</h3>
        <div class="m-sub">举报完全匿名，管理员不会知道举报人身份。多次恶意举报可能影响社区氛围，请谨慎使用。</div>
        <div class="field"><label>举报理由</label><select id="rpReason">
          <option>垃圾广告</option><option>人身攻击/引战</option><option>不实信息</option><option>色情低俗</option><option>其他</option></select></div>
        <div class="field"><label>补充说明（可选）</label><textarea id="rpNote" maxlength="80" style="min-height:56px;width:100%;border:1px solid var(--line);border-radius:9px;padding:8px 12px" placeholder="简单说明情况"></textarea></div>
        <div class="m-actions"><button class="btn btn-ghost" data-act="modal-close">取消</button>
          <button class="btn btn-danger" data-act="report-submit" data-id="${id}">提交举报</button></div>`);
      break;
    }
    case "report-submit": {
      const reason = $("#rpReason").value + ($("#rpNote").value.trim() ? "：" + $("#rpNote").value.trim() : "");
      const r = await api(`/api/posts/${id}/report`, "POST", { reason });
      closeModal();
      if (r.ok) toast("举报已提交，管理员会尽快处理");
      else toast(r.msg, "err");
      break;
    }
    case "logout": {
      const yes = await confirmBox("退出登录？", "退出后将以<b>匿名学生身份</b>继续浏览。", "退出", false);
      if (!yes) return;
      await api("/api/auth/logout", "POST");
      await refreshBoot();
      location.hash = "#/leaderboard";
      route();
      break;
    }
    /* ---- 管理员 ---- */
    case "admin-tab": S.adminTab = v; renderAdmin(); break;
    case "admin-post-filter": S.postsFilter = v; renderAdmin(); break;
    case "admin-report-tab": S.reportsTab = +v; renderAdmin(); break;
    case "admin-edit-window": {
      const r = await api("/api/admin/windows");
      const w = r.ok && r.data.windows.find(x => x.id === +id);
      if (w) adminEditWindowModal(w);
      break;
    }
    case "admin-save-window": {
      const r = await api(`/api/admin/windows/${id}`, "PUT", {
        name: $("#mWinName").value.trim(), merchant_name: $("#mMerName").value.trim(),
        status: $("#mWinStatus").value === "1" ? 1 : 0 });
      if (!r.ok) { toast(r.msg, "err"); return; }
      closeModal(); toast("窗口信息已更新"); renderAdmin();
      break;
    }
    case "admin-reset-pw": {
      const yes = await confirmBox("重置该窗口商家的登录密码？", "重置后原密码立即失效，请将新密码线下告知商家。", "重置", false);
      if (!yes) return;
      const r = await api(`/api/admin/windows/${id}/reset-merchant-password`, "POST");
      if (!r.ok) { toast(r.msg, "err"); return; }
      modal(`<h3>${icon("key")} 商家密码已重置</h3>
        <div class="m-sub">请复制后线下发放给商家（关闭后无法再次查看）：</div>
        <div class="pw-box">商家账号：<code>${esc(r.data.username)}</code><br>新密码：<code>${esc(r.data.password)}</code>
          <div style="margin-top:8px"><button class="btn btn-ghost btn-sm" data-act="copy-pw" data-pw="${esc(r.data.username)} ${esc(r.data.password)}">${icon("check")} 复制</button></div></div>
        <div class="m-actions"><button class="btn btn-primary" data-act="modal-close">我已保存，关闭</button></div>`);
      break;
    }
    case "copy-pw": {
      try { navigator.clipboard.writeText(el.dataset.pw); toast("已复制到剪贴板"); } catch (e2) { toast("复制失败，请手动选择文本", "err"); }
      break;
    }
    case "admin-del-post": {
      const yes = await confirmBox("删除这条帖子？", "删除后学生端立即不可见（其下所有回复一并隐藏），可在「已删除」中恢复。", "删除", true);
      if (!yes) return;
      const r = await api(`/api/admin/posts/${id}`, "DELETE");
      if (r.ok) { toast("已删除"); renderAdmin(); } else toast(r.msg, "err");
      break;
    }
    case "admin-restore-post": {
      const r = await api(`/api/admin/posts/${id}/restore`, "POST");
      if (r.ok) { toast("已恢复"); renderAdmin(); } else toast(r.msg, "err");
      break;
    }
    case "report-resolve": {
      const action = v;
      const rid = el.dataset.rid;
      const yes = await confirmBox(action === "delete" ? "删除被举报的帖子？" : "驳回这条举报？",
        action === "delete" ? "帖子将连同其回复一起对学生端隐藏。" : "帖子保持可见，举报标记为已驳回。", action === "delete" ? "删除帖子" : "驳回", action === "delete");
      if (!yes) return;
      const r = await api(`/api/admin/reports/${rid}/resolve`, "POST", { action });
      if (r.ok) { toast(action === "delete" ? "帖子已删除" : "举报已驳回"); renderAdmin(); } else toast(r.msg, "err");
      break;
    }
    case "admin-changepw": adminChangePwModal(); break;
    case "admin-save-pw": {
      const o = $("#pwOld").value, n1 = $("#pwNew").value, n2 = $("#pwNew2").value;
      if (n1 !== n2) { toast("两次输入的新密码不一致", "err"); return; }
      const r = await api("/api/admin/change-password", "POST", { old: o, new: n1 });
      if (!r.ok) { toast(r.msg, "err"); return; }
      closeModal(); toast("密码已修改，下次登录生效");
      break;
    }
    /* ---- 商家 ---- */
    case "dish-add": dishFormModal(null); break;
    case "dish-edit": {
      const r = await api("/api/merchant/overview");
      const dish = r.ok && r.data.dishes.find(x => x.id === +id);
      if (dish) dishFormModal(dish);
      break;
    }
    case "dish-save": {
      const name = $("#dName").value.trim(), price = $("#dPrice").value, intro = $("#dIntro").value.trim();
      if (!id) {
        const r = await api("/api/merchant/dishes", "POST", { name, price, intro });
        if (!r.ok) { toast(r.msg, "err"); return; }
        toast("菜品已上架");
      } else {
        const body = { name, price, intro, status: $("#dStatus") ? +$("#dStatus").value : undefined };
        const r = await api(`/api/merchant/dishes/${id}`, "PUT", body);
        if (!r.ok) { toast(r.msg, "err"); return; }
        toast("菜品已更新");
      }
      closeModal(); renderMerchant();
      break;
    }
    case "dish-status": {
      const r = await api(`/api/merchant/dishes/${id}`, "PUT", { status: +v });
      if (r.ok) { toast(v === "1" ? "已上架" : "已下架"); renderMerchant(); } else toast(r.msg, "err");
      break;
    }
  }
});

/* ------------------------------------------------------------ 随便吃点悬浮球 */
const _diceFab = document.getElementById("diceFab");
if (_diceFab) _diceFab.addEventListener("click", rollRandomDish);

/* ------------------------------------------------------------ 启动 */
window.App = { _cf: () => {} };
(async function init() {
  detectDevice();
  const bt = document.createElement("button");
  bt.className = "back-top"; bt.title = "回到顶部";
  bt.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>';
  bt.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  window.addEventListener("scroll", () => { bt.classList.toggle("show", window.scrollY > 600); }, { passive: true });
  document.body.appendChild(bt);
  $("#brandLogo").innerHTML = icon("utensils");
  await refreshBoot();
  window.addEventListener("hashchange", route);
  window.addEventListener("scroll", () => {
    const tb = document.querySelector(".topbar");
    if (tb) tb.classList.toggle("scrolled", window.scrollY > 8);
  }, { passive: true });
  route();
})();
