// ========================================
// ナースロビー - KPI Dashboard
// Canvas charts + dummy data + animations
// ========================================

(function () {
  "use strict";

  // ---------- Login Gate ----------
  var LOGIN_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"; // sha256 of "password" - change in production

  async function sha256(text) {
    var encoder = new TextEncoder();
    var data = encoder.encode(text);
    var hash = await crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(hash)).map(function(b) { return b.toString(16).padStart(2, "0"); }).join("");
  }

  var loginOverlay = document.getElementById("loginOverlay");
  var loginForm = document.getElementById("loginForm");
  var loginError = document.getElementById("loginError");

  // Check session
  if (sessionStorage.getItem("dash_auth") === "1") {
    if (loginOverlay) loginOverlay.classList.add("hidden");
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async function(e) {
      e.preventDefault();
      var id = document.getElementById("loginId").value.trim();
      var pass = document.getElementById("loginPass").value;
      if (!id || !pass) {
        loginError.textContent = "IDとパスワードを入力してください";
        return;
      }
      var hash = await sha256(pass);
      if (id === "admin" && hash === LOGIN_HASH) {
        sessionStorage.setItem("dash_auth", "1");
        loginOverlay.classList.add("hidden");
        loginError.textContent = "";
        initDashboard();
      } else {
        loginError.textContent = "IDまたはパスワードが正しくありません";
      }
    });
  }

  // Only init dashboard if already authenticated
  if (sessionStorage.getItem("dash_auth") === "1") {
    document.addEventListener("DOMContentLoaded", function() { initDashboard(); });
  }

  function initDashboard() {

  // ---------- Dummy Data ----------

  // Past 30 days registration (1-5 per day random, seeded)
  function generateDailyRegistrations(days) {
    const data = [];
    const seed = 42;
    let s = seed;
    for (let i = 0; i < days; i++) {
      s = (s * 16807 + 0) % 2147483647;
      data.push(1 + (s % 5));
    }
    return data;
  }

  const DAILY_REGISTRATIONS = generateDailyRegistrations(30);

  const TRAFFIC_SOURCES = [
    { label: "直接", value: 30, color: "#38BDF8" },
    { label: "SEO", value: 25, color: "#34D399" },
    { label: "広告", value: 20, color: "#F59E0B" },
    { label: "SNS", value: 15, color: "#A78BFA" },
    { label: "紹介", value: 10, color: "#FB7185" },
  ];

  const FUNNEL_STAGES = [
    { label: "登録", value: 100 },
    { label: "AI完了", value: 82 },
    { label: "架電接続", value: 60 },
    { label: "面接設定", value: 38 },
    { label: "内定", value: 20 },
    { label: "入職", value: 15 },
  ];

  const MONTHLY_REVENUE = [
    { label: "9月", value: 120 },
    { label: "10月", value: 145 },
    { label: "11月", value: 160 },
    { label: "12月", value: 175 },
    { label: "1月", value: 185 },
    { label: "2月", value: 200 },
  ];

  const REGISTRANTS = [
    { date: "2/16 14:32", name: "田X XX", profession: "看護師", status: "AI対話中", temp: "hot" },
    { date: "2/16 11:08", name: "佐X XX", profession: "理学療法士", status: "架電待ち", temp: "warm" },
    { date: "2/15 18:45", name: "鈴X XX", profession: "看護師", status: "面接調整中", temp: "hot" },
    { date: "2/15 10:20", name: "高X XX", profession: "看護師", status: "AI完了", temp: "warm" },
    { date: "2/14 16:55", name: "山X XX", profession: "作業療法士", status: "面接設定済", temp: "cool" },
    { date: "2/14 09:12", name: "中X XX", profession: "看護師", status: "入職決定", temp: "hot" },
    { date: "2/13 15:30", name: "小X XX", profession: "看護師", status: "内定承諾", temp: "warm" },
    { date: "2/13 08:45", name: "渡X XX", profession: "理学療法士", status: "架電済み", temp: "cool" },
  ];

  const TASKS = [
    { task: "田X様 初回架電", assignee: "担当A", deadline: "2/16", status: "urgent" },
    { task: "佐X様 AI対話フォロー", assignee: "AI", deadline: "2/16", status: "progress" },
    { task: "鈴X様 面接日程調整", assignee: "担当B", deadline: "2/17", status: "progress" },
    { task: "高X様 求人提案作成", assignee: "担当A", deadline: "2/17", status: "pending" },
    { task: "月次レポート作成", assignee: "管理者", deadline: "2/28", status: "pending" },
    { task: "山X様 入職後フォロー", assignee: "担当B", deadline: "2/20", status: "done" },
  ];

  // ---------- Utilities ----------

  function getDevicePixelRatio() {
    return window.devicePixelRatio || 1;
  }

  function setupCanvas(canvas, width, height) {
    const dpr = getDevicePixelRatio();
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    var ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    return ctx;
  }

  function resizeCanvasToParent(canvas) {
    var parent = canvas.parentElement;
    var w = parent.clientWidth;
    var h = parent.clientHeight || 220;
    return { width: w, height: h };
  }

  // ---------- Count-Up Animation ----------

  function animateCountUp() {
    var elements = document.querySelectorAll("[data-count]");
    elements.forEach(function (el) {
      var target = parseInt(el.getAttribute("data-count"), 10);
      var suffix = el.getAttribute("data-suffix") || "";
      var duration = 1200;
      var start = performance.now();

      function update(now) {
        var elapsed = now - start;
        var progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = Math.round(eased * target);
        el.textContent = current + suffix;
        if (progress < 1) {
          requestAnimationFrame(update);
        }
      }
      requestAnimationFrame(update);
    });
  }

  // ---------- Line Chart: Registration Trend ----------

  function drawRegistrationChart() {
    var canvas = document.getElementById("registrationChart");
    if (!canvas) return;
    var size = resizeCanvasToParent(canvas);
    var ctx = setupCanvas(canvas, size.width, size.height);
    var w = size.width;
    var h = size.height;
    var data = DAILY_REGISTRATIONS;
    var maxVal = Math.max.apply(null, data) + 1;
    var padTop = 20;
    var padBottom = 36;
    var padLeft = 40;
    var padRight = 16;
    var chartW = w - padLeft - padRight;
    var chartH = h - padTop - padBottom;

    // Grid lines
    ctx.strokeStyle = "rgba(42, 63, 95, 0.3)";
    ctx.lineWidth = 1;
    for (var i = 0; i <= 5; i++) {
      var y = padTop + (chartH / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();
      // Y labels
      ctx.fillStyle = "#94A3B8";
      ctx.font = "500 11px Inter Tight, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(Math.round(maxVal - (maxVal / 5) * i), padLeft - 8, y + 4);
    }

    // X labels (every 5 days)
    ctx.fillStyle = "#94A3B8";
    ctx.font = "500 10px Inter Tight, sans-serif";
    ctx.textAlign = "center";
    for (var d = 0; d < data.length; d += 5) {
      var xPos = padLeft + (chartW / (data.length - 1)) * d;
      ctx.fillText((d + 1) + "日", xPos, h - 8);
    }

    // Gradient fill
    var gradient = ctx.createLinearGradient(0, padTop, 0, padTop + chartH);
    gradient.addColorStop(0, "rgba(56, 189, 248, 0.2)");
    gradient.addColorStop(1, "rgba(56, 189, 248, 0)");

    ctx.beginPath();
    for (var j = 0; j < data.length; j++) {
      var x = padLeft + (chartW / (data.length - 1)) * j;
      var yVal = padTop + chartH - (data[j] / maxVal) * chartH;
      if (j === 0) ctx.moveTo(x, yVal);
      else ctx.lineTo(x, yVal);
    }
    // Close fill path
    ctx.lineTo(padLeft + chartW, padTop + chartH);
    ctx.lineTo(padLeft, padTop + chartH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    for (var k = 0; k < data.length; k++) {
      var xL = padLeft + (chartW / (data.length - 1)) * k;
      var yL = padTop + chartH - (data[k] / maxVal) * chartH;
      if (k === 0) ctx.moveTo(xL, yL);
      else ctx.lineTo(xL, yL);
    }
    ctx.strokeStyle = "#38BDF8";
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Dots
    for (var m = 0; m < data.length; m++) {
      var xD = padLeft + (chartW / (data.length - 1)) * m;
      var yD = padTop + chartH - (data[m] / maxVal) * chartH;
      ctx.beginPath();
      ctx.arc(xD, yD, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#38BDF8";
      ctx.fill();
      ctx.strokeStyle = "#0D1B2A";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  // ---------- Donut Chart: Traffic Sources ----------

  function drawTrafficChart() {
    var canvas = document.getElementById("trafficChart");
    if (!canvas) return;
    var size = 180;
    var ctx = setupCanvas(canvas, size, size);
    var cx = size / 2;
    var cy = size / 2;
    var outerR = 80;
    var innerR = 52;
    var total = 0;
    TRAFFIC_SOURCES.forEach(function (s) { total += s.value; });

    var startAngle = -Math.PI / 2;
    TRAFFIC_SOURCES.forEach(function (source) {
      var sliceAngle = (source.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.arc(cx, cy, outerR, startAngle, startAngle + sliceAngle);
      ctx.arc(cx, cy, innerR, startAngle + sliceAngle, startAngle, true);
      ctx.closePath();
      ctx.fillStyle = source.color;
      ctx.fill();
      startAngle += sliceAngle;
    });

    // Legend
    var legendContainer = document.getElementById("trafficLegend");
    if (legendContainer) {
      legendContainer.innerHTML = "";
      TRAFFIC_SOURCES.forEach(function (source) {
        var item = document.createElement("div");
        item.className = "dash-legend-item";
        item.innerHTML =
          '<span class="dash-legend-dot" style="background:' + source.color + '"></span>' +
          source.label + " " + source.value + "%";
        legendContainer.appendChild(item);
      });
    }
  }

  // ---------- Funnel Chart ----------

  function drawFunnelChart() {
    var canvas = document.getElementById("funnelChart");
    if (!canvas) return;
    var size = resizeCanvasToParent(canvas);
    var ctx = setupCanvas(canvas, size.width, size.height);
    var w = size.width;
    var h = size.height;
    var padLeft = 90;
    var padRight = 50;
    var padTop = 10;
    var padBottom = 10;
    var barHeight = 28;
    var gap = 10;
    var maxVal = FUNNEL_STAGES[0].value;
    var chartW = w - padLeft - padRight;

    var colors = ["#38BDF8", "#34D399", "#A78BFA", "#F59E0B", "#FB7185", "#22D3EE"];

    FUNNEL_STAGES.forEach(function (stage, idx) {
      var y = padTop + idx * (barHeight + gap);
      var barW = (stage.value / maxVal) * chartW;

      // Bar
      var barGrad = ctx.createLinearGradient(padLeft, 0, padLeft + barW, 0);
      barGrad.addColorStop(0, colors[idx % colors.length]);
      barGrad.addColorStop(1, colors[idx % colors.length] + "88");

      ctx.beginPath();
      var r = 4;
      ctx.moveTo(padLeft + r, y);
      ctx.lineTo(padLeft + barW - r, y);
      ctx.quadraticCurveTo(padLeft + barW, y, padLeft + barW, y + r);
      ctx.lineTo(padLeft + barW, y + barHeight - r);
      ctx.quadraticCurveTo(padLeft + barW, y + barHeight, padLeft + barW - r, y + barHeight);
      ctx.lineTo(padLeft + r, y + barHeight);
      ctx.quadraticCurveTo(padLeft, y + barHeight, padLeft, y + barHeight - r);
      ctx.lineTo(padLeft, y + r);
      ctx.quadraticCurveTo(padLeft, y, padLeft + r, y);
      ctx.closePath();
      ctx.fillStyle = barGrad;
      ctx.fill();

      // Label
      ctx.fillStyle = "#E0E0E0";
      ctx.font = "600 12px Inter Tight, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(stage.label, padLeft - 10, y + barHeight / 2 + 4);

      // Value
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "700 12px Inter Tight, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(stage.value, padLeft + barW + 8, y + barHeight / 2 + 4);

      // Conversion rate
      if (idx > 0) {
        var rate = Math.round((stage.value / FUNNEL_STAGES[idx - 1].value) * 100);
        ctx.fillStyle = "#94A3B8";
        ctx.font = "500 10px Inter Tight, sans-serif";
        ctx.fillText(rate + "%", padLeft + barW + 30, y + barHeight / 2 + 4);
      }
    });
  }

  // ---------- Bar Chart: Revenue ----------

  function drawRevenueChart() {
    var canvas = document.getElementById("revenueChart");
    if (!canvas) return;
    var size = resizeCanvasToParent(canvas);
    var ctx = setupCanvas(canvas, size.width, size.height);
    var w = size.width;
    var h = size.height;
    var padTop = 20;
    var padBottom = 36;
    var padLeft = 48;
    var padRight = 16;
    var chartW = w - padLeft - padRight;
    var chartH = h - padTop - padBottom;
    var maxVal = 250;
    var data = MONTHLY_REVENUE;
    var barCount = data.length;
    var barGap = 12;
    var barW = (chartW - barGap * (barCount + 1)) / barCount;

    // Grid
    ctx.strokeStyle = "rgba(42, 63, 95, 0.3)";
    ctx.lineWidth = 1;
    for (var i = 0; i <= 5; i++) {
      var y = padTop + (chartH / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();
      ctx.fillStyle = "#94A3B8";
      ctx.font = "500 10px Inter Tight, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(Math.round(maxVal - (maxVal / 5) * i), padLeft - 8, y + 4);
    }

    // Bars
    data.forEach(function (item, idx) {
      var x = padLeft + barGap + idx * (barW + barGap);
      var barH = (item.value / maxVal) * chartH;
      var y = padTop + chartH - barH;

      var grad = ctx.createLinearGradient(0, y, 0, y + barH);
      var isLast = idx === data.length - 1;
      grad.addColorStop(0, isLast ? "#38BDF8" : "#34D399");
      grad.addColorStop(1, isLast ? "#38BDF888" : "#34D39966");

      // Rounded top
      var r = 4;
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + barW - r, y);
      ctx.quadraticCurveTo(x + barW, y, x + barW, y + r);
      ctx.lineTo(x + barW, padTop + chartH);
      ctx.lineTo(x, padTop + chartH);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // X label
      ctx.fillStyle = "#94A3B8";
      ctx.font = "500 10px Inter Tight, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(item.label, x + barW / 2, h - 8);

      // Value on top
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "700 11px Inter Tight, sans-serif";
      ctx.fillText(item.value, x + barW / 2, y - 6);
    });
  }

  // ---------- Speed Gauges ----------

  function drawSpeedGauge(canvasId, value, max, color) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var size = 140;
    var ctx = setupCanvas(canvas, size, size);
    var cx = size / 2;
    var cy = size / 2;
    var r = 56;
    var lineWidth = 10;
    var startAngle = 0.75 * Math.PI;
    var endAngle = 2.25 * Math.PI;
    var totalAngle = endAngle - startAngle;

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.strokeStyle = "rgba(42, 63, 95, 0.4)";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.stroke();

    // Value arc
    var ratio = Math.min(value / max, 1);
    var valueAngle = startAngle + totalAngle * ratio;
    var grad = ctx.createLinearGradient(cx - r, cy, cx + r, cy);
    grad.addColorStop(0, color);
    grad.addColorStop(1, color + "88");
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, valueAngle);
    ctx.strokeStyle = grad;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.stroke();
  }

  // ---------- Tables ----------

  function populateRegistrantsTable() {
    var tbody = document.getElementById("registrantsTable");
    if (!tbody) return;
    var html = "";
    REGISTRANTS.forEach(function (r) {
      var tempClass = "dash-badge-" + r.temp;
      var tempLabel = r.temp === "hot" ? "高" : r.temp === "warm" ? "中" : "低";
      html +=
        "<tr>" +
        "<td>" + r.date + "</td>" +
        "<td>" + r.name + "</td>" +
        "<td>" + r.profession + "</td>" +
        "<td>" + r.status + "</td>" +
        '<td><span class="dash-badge ' + tempClass + '">' + tempLabel + "</span></td>" +
        "</tr>";
    });
    tbody.innerHTML = html;
  }

  function populateTasksTable() {
    var tbody = document.getElementById("tasksTable");
    if (!tbody) return;
    var statusMap = {
      urgent: { label: "緊急", cls: "dash-badge-urgent" },
      progress: { label: "進行中", cls: "dash-badge-progress" },
      pending: { label: "未着手", cls: "dash-badge-pending" },
      done: { label: "完了", cls: "dash-badge-done" },
    };
    var html = "";
    TASKS.forEach(function (t) {
      var s = statusMap[t.status] || statusMap.pending;
      html +=
        "<tr>" +
        "<td>" + t.task + "</td>" +
        "<td>" + t.assignee + "</td>" +
        "<td>" + t.deadline + "</td>" +
        '<td><span class="dash-badge ' + s.cls + '">' + s.label + "</span></td>" +
        "</tr>";
    });
    tbody.innerHTML = html;
  }

  // ---------- Period Selector ----------

  function setupPeriodSelector() {
    var buttons = document.querySelectorAll(".dash-period-btn");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        // In production, this would reload data for the selected period
      });
    });
  }

  // ---------- Responsive Resize ----------

  var resizeTimer;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      drawRegistrationChart();
      drawTrafficChart();
      drawFunnelChart();
      drawRevenueChart();
      drawSpeedGauge("speedGauge1", 18, 24, "#34D399");
      drawSpeedGauge("speedGauge2", 5, 7, "#38BDF8");
    }, 150);
  }

  // ---------- Init ----------

  function init() {
    animateCountUp();
    drawRegistrationChart();
    drawTrafficChart();
    drawFunnelChart();
    drawRevenueChart();
    drawSpeedGauge("speedGauge1", 18, 24, "#34D399");
    drawSpeedGauge("speedGauge2", 5, 7, "#38BDF8");
    populateRegistrantsTable();
    populateTasksTable();
    setupPeriodSelector();
    window.addEventListener("resize", onResize);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  } // end initDashboard

})();
