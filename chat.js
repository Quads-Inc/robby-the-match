// ========================================
// ナースロビー - AI Chat Widget v3.0
// 行動経済学ドリブン コンバージョン設計
// 即時性 + サンクコスト + 損失回避 + アンカリング
// ========================================

(function () {
  "use strict";

  // --------------------------------------------------
  // Configuration
  // --------------------------------------------------
  var CHAT_CONFIG = {
    brandName: typeof CONFIG !== "undefined" ? CONFIG.BRAND_NAME : "ナースロビー",
    workerEndpoint: typeof CONFIG !== "undefined" ? CONFIG.API.workerEndpoint : "",
    hospitals: typeof CONFIG !== "undefined" ? CONFIG.HOSPITALS : [],
  };

  // --------------------------------------------------
  // 行動経済学: 年収推定データ（アンカリング用）
  // --------------------------------------------------
  var SALARY_ESTIMATES = {
    kensei:       { min: 380, max: 520, avg: 440, top: 560 },
    shonan_west:  { min: 400, max: 540, avg: 460, top: 580 },
    shonan_east:  { min: 410, max: 560, avg: 470, top: 600 },
    kenoh:        { min: 400, max: 550, avg: 465, top: 590 },
    undecided:    { min: 390, max: 540, avg: 450, top: 570 },
  };

  // 経験年数別の補正係数
  var EXP_MULTIPLIER = {
    "1-3": 0.85, "3-5": 0.95, "5-10": 1.05, "10+": 1.15,
  };

  // --------------------------------------------------
  // Pre-scripted flow data (行動経済学: 選択のパラドックス=3択以内)
  // --------------------------------------------------
  var PRESCRIPTED = {
    intents: [
      { label: "年収が相場より低いか知りたい", value: "search", emoji: "" },
      { label: "転職すべきか診断したい", value: "consult", emoji: "" },
      { label: "まずは情報だけほしい", value: "browse", emoji: "" },
    ],
    areas: [
      { label: "県西（小田原・南足柄）", value: "kensei" },
      { label: "湘南西部（平塚・秦野・伊勢原）", value: "shonan_west" },
      { label: "湘南東部（藤沢・茅ヶ崎）", value: "shonan_east" },
      { label: "県央（厚木・海老名）", value: "kenoh" },
      { label: "まだ決めていない", value: "undecided" },
    ],
    areaLabels: {
      kensei: "県西",
      shonan_west: "湘南西部",
      shonan_east: "湘南東部",
      kenoh: "県央",
      undecided: "神奈川県西部",
    },
    areaCities: {
      kensei: ["小田原", "南足柄", "開成", "大井", "大磯", "二宮", "松田", "山北", "箱根", "真鶴", "湯河原"],
      shonan_west: ["平塚", "秦野", "伊勢原"],
      shonan_east: ["藤沢", "茅ヶ崎", "寒川"],
      kenoh: ["厚木", "海老名", "座間", "綾瀬", "大和", "愛川"],
    },
    priorities: [
      { label: "お給料・待遇", value: "salary" },
      { label: "通勤のしやすさ", value: "commute" },
      { label: "ワークライフバランス", value: "wlb" },
      { label: "職場の雰囲気・人間関係", value: "environment" },
    ],
    experiences: [
      { label: "1年未満", value: "1年未満" },
      { label: "1〜3年", value: "1〜3年" },
      { label: "3〜5年", value: "3〜5年" },
      { label: "5〜10年", value: "5〜10年" },
      { label: "10年以上", value: "10年以上" },
    ],
  };

  // --------------------------------------------------
  // GA4 Event Tracking
  // --------------------------------------------------
  function trackEvent(eventName, params) {
    if (typeof gtag === "function") {
      try { gtag("event", eventName, params || {}); } catch (e) { /* ignore */ }
    }
  }

  // --------------------------------------------------
  // Demo mode responses (when API unavailable)
  // --------------------------------------------------
  var DEMO_RESPONSES = [
    {
      reply: "お話しいただきありがとうございます。\n\n差し支えなければ、今回転職をお考えになったきっかけを教えていただけますか？",
      done: false,
    },
    {
      reply: "なるほど、そうだったのですね。\n\nちなみに、月収やお休みの日数など、特に重視されている条件はありますか？",
      done: false,
    },
    {
      reply: "ありがとうございます。いただいた条件をもとに、エリアの施設をいくつか候補として整理しています。\n\n夜勤の有無や通勤時間について、ご希望があればお聞かせください。",
      done: false,
    },
    {
      reply: "詳しくお聞かせいただきありがとうございました。\n\nお伺いした内容をもとに、条件に合う求人をお探しします。LINEで詳しい情報をお届けしますので、ぜひ友だち追加してくださいね。",
      done: true,
    },
  ];

  // --------------------------------------------------
  // State
  // --------------------------------------------------
  function generateSessionId() {
    return "sess_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 9);
  }

  var CLIENT_RATE_LIMIT = {
    sendCooldownMs: 2000,
    maxSessionMessages: 15,
  };

  var chatState = {
    isOpen: false,
    messages: [],
    apiMessages: [],
    sessionId: generateSessionId(),
    demoIndex: 0,
    score: null,
    done: false,
    isTyping: false,
    lastSendTime: 0,
    userMessageCount: 0,
    sendCooldown: false,
    demoMode: false,
    lineCtaShown: false,
    peekShown: false,
    peekDismissed: false,
    // Conversational flow state
    phase: "greeting", // "greeting" | "intent" | "area" | "experience" | "priority" | "value" | "ai" | "done"
    intent: null,
    area: null,
    experience: null,
    priority: null,
    // 行動経済学: サンクコスト
    conversationStartTime: null,
    sunkCostShown: false,
    estimatedSalary: null,
  };

  // --------------------------------------------------
  // localStorage persistence
  // --------------------------------------------------
  var STORAGE_KEY = "nurserobby_chat";

  function saveState() {
    try {
      var toSave = {
        messages: chatState.messages,
        apiMessages: chatState.apiMessages,
        sessionId: chatState.sessionId,
        phase: chatState.phase,
        intent: chatState.intent,
        area: chatState.area,
        experience: chatState.experience,
        priority: chatState.priority,
        userMessageCount: chatState.userMessageCount,
        score: chatState.score,
        done: chatState.done,
        lineCtaShown: chatState.lineCtaShown,
        demoIndex: chatState.demoIndex,
        conversationStartTime: chatState.conversationStartTime,
        sunkCostShown: chatState.sunkCostShown,
        estimatedSalary: chatState.estimatedSalary,
        savedAt: Date.now(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
    } catch (e) { /* storage full or disabled */ }
  }

  function loadState() {
    try {
      var data = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (!data || !data.savedAt) return false;
      // Expire after 24 hours
      if (Date.now() - data.savedAt > 24 * 60 * 60 * 1000) {
        localStorage.removeItem(STORAGE_KEY);
        return false;
      }
      chatState.messages = data.messages || [];
      chatState.apiMessages = data.apiMessages || [];
      chatState.sessionId = data.sessionId || chatState.sessionId;
      chatState.phase = data.phase || "greeting";
      chatState.intent = data.intent || null;
      chatState.area = data.area || null;
      chatState.experience = data.experience || null;
      chatState.priority = data.priority || null;
      chatState.userMessageCount = data.userMessageCount || 0;
      chatState.score = data.score || null;
      chatState.done = data.done || false;
      chatState.lineCtaShown = data.lineCtaShown || false;
      chatState.demoIndex = data.demoIndex || 0;
      chatState.conversationStartTime = data.conversationStartTime || null;
      chatState.sunkCostShown = data.sunkCostShown || false;
      chatState.estimatedSalary = data.estimatedSalary || null;
      return true;
    } catch (e) {
      return false;
    }
  }

  function clearState() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
  }

  // --------------------------------------------------
  // DOM References
  // --------------------------------------------------
  var els = {};

  // --------------------------------------------------
  // Initialization
  // --------------------------------------------------
  function init() {
    els = {
      toggle: document.getElementById("chatToggle"),
      window: document.getElementById("chatWindow"),
      body: document.getElementById("chatBody"),
      input: document.getElementById("chatInput"),
      sendBtn: document.getElementById("chatSendBtn"),
      closeBtn: document.getElementById("chatCloseBtn"),
      minimizeBtn: document.getElementById("chatMinimizeBtn"),
      chatView: document.getElementById("chatView"),
    };

    if (!els.toggle || !els.window) return;

    // Event listeners
    els.toggle.addEventListener("click", toggleChat);
    els.closeBtn.addEventListener("click", closeChat);
    if (els.minimizeBtn) els.minimizeBtn.addEventListener("click", closeChat);
    els.sendBtn.addEventListener("click", sendMessage);

    els.input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea
    els.input.addEventListener("input", function () {
      els.input.style.height = "auto";
      els.input.style.height = Math.min(els.input.scrollHeight, 100) + "px";
      scrollToBottom();
    });

    // iOS virtual keyboard handling
    if (window.visualViewport) {
      var lastVPHeight = window.visualViewport.height;
      window.visualViewport.addEventListener("resize", function () {
        if (!chatState.isOpen || window.innerWidth > 640) return;
        var vpHeight = window.visualViewport.height;
        if (vpHeight !== lastVPHeight) {
          lastVPHeight = vpHeight;
          els.window.style.height = vpHeight + "px";
          scrollToBottom();
        }
      });
      window.visualViewport.addEventListener("scroll", function () {
        if (!chatState.isOpen || window.innerWidth > 640) return;
        els.window.style.top = window.visualViewport.offsetTop + "px";
      });
    }

    // Escape key to close
    document.addEventListener("keydown", function (e) {
      if (!chatState.isOpen) return;
      if (e.key === "Escape") {
        e.preventDefault();
        closeChat();
        return;
      }
      // Focus trap
      if (e.key === "Tab") {
        var focusable = els.window.querySelectorAll(
          'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([tabindex="-1"]), [tabindex]:not([tabindex="-1"])'
        );
        var visible = [];
        for (var i = 0; i < focusable.length; i++) {
          if (focusable[i].offsetParent !== null) visible.push(focusable[i]);
        }
        if (visible.length === 0) return;
        var first = visible[0];
        var last = visible[visible.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) { e.preventDefault(); last.focus(); }
        } else {
          if (document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
      }
    });

    // Proactive peek message after 20 seconds
    setTimeout(function () {
      if (!chatState.isOpen && !chatState.peekDismissed) {
        showPeekMessage();
      }
    }, 20000);
  }

  // --------------------------------------------------
  // Proactive Peek Message
  // --------------------------------------------------
  function showPeekMessage() {
    if (chatState.peekShown || chatState.isOpen) return;
    chatState.peekShown = true;

    var peek = document.createElement("div");
    peek.className = "chat-peek";
    peek.id = "chatPeek";
    peek.innerHTML =
      '<div class="chat-peek-text">あなたの年収、相場より低いかも？<br><strong>30秒で無料診断</strong></div>' +
      '<button class="chat-peek-close" aria-label="閉じる">&times;</button>';

    // Insert before toggle button
    els.toggle.parentElement.insertBefore(peek, els.toggle);

    // Click peek text to open chat
    peek.querySelector(".chat-peek-text").addEventListener("click", function () {
      peek.remove();
      trackEvent("chat_peek_click");
      openChat();
    });

    // Close peek
    peek.querySelector(".chat-peek-close").addEventListener("click", function (e) {
      e.stopPropagation();
      chatState.peekDismissed = true;
      peek.classList.add("chat-peek-hiding");
      setTimeout(function () { peek.remove(); }, 300);
    });

    trackEvent("chat_peek_shown");

    // Auto-dismiss after 10 seconds
    setTimeout(function () {
      var el = document.getElementById("chatPeek");
      if (el && !chatState.isOpen) {
        el.classList.add("chat-peek-hiding");
        setTimeout(function () { if (el.parentElement) el.remove(); }, 300);
      }
    }, 10000);
  }

  // --------------------------------------------------
  // Toggle / Open / Close
  // --------------------------------------------------
  function toggleChat() {
    if (chatState.isOpen) {
      closeChat();
    } else {
      openChat();
    }
  }

  function lockBodyScroll() {
    if (window.innerWidth <= 640) {
      chatState._savedScrollY = window.pageYOffset || document.documentElement.scrollTop;
      document.body.classList.add("chat-open-mobile");
      document.body.style.top = "-" + chatState._savedScrollY + "px";
    }
  }

  function unlockBodyScroll() {
    if (document.body.classList.contains("chat-open-mobile")) {
      document.body.classList.remove("chat-open-mobile");
      document.body.style.top = "";
      window.scrollTo(0, chatState._savedScrollY || 0);
    }
  }

  function openChat() {
    chatState.isOpen = true;
    els.window.classList.add("open");
    lockBodyScroll();
    trackEvent("chat_open");
    els.toggle.classList.add("active");
    els.toggle.querySelector(".chat-toggle-icon").textContent = "\u2715";

    // Remove peek if visible
    var peek = document.getElementById("chatPeek");
    if (peek) peek.remove();

    // Try to restore previous session
    var restored = false;
    if (chatState.messages.length === 0) {
      restored = loadState();
    }

    if (restored && chatState.messages.length > 0) {
      // サンクコスト: 「前回の続きから再開」で離脱を防ぐ
      restoreChatView();
      showResumeNotice();
    } else if (chatState.messages.length === 0) {
      // First open - start conversational flow
      setInputVisible(false);
      startConversation();
    } else {
      // Already has messages (reopening)
      showChatView();
      if (chatState.phase === "ai") {
        setInputVisible(true);
        els.input.focus();
      }
    }
  }

  function closeChat() {
    chatState.isOpen = false;
    els.window.classList.remove("open");
    unlockBodyScroll();
    els.window.style.height = "";
    els.window.style.top = "";
    els.toggle.classList.remove("active");
    els.toggle.querySelector(".chat-toggle-icon").textContent = "\uD83D\uDCAC";
    els.toggle.focus();
    saveState();
  }

  // --------------------------------------------------
  // サンクコスト: セッション復帰通知
  // --------------------------------------------------
  function showResumeNotice() {
    if (!chatState.messages.length) return;
    var notice = document.createElement("div");
    notice.className = "chat-resume-notice";
    notice.innerHTML = '<span>前回の続きから再開しています</span>';
    els.body.appendChild(notice);
    scrollToBottom();
    // 3秒後にフェードアウト
    setTimeout(function () {
      notice.classList.add("chat-resume-hiding");
      setTimeout(function () { if (notice.parentElement) notice.remove(); }, 500);
    }, 3000);
  }

  // --------------------------------------------------
  // サンクコスト: 3分タイマー → 「診断結果を保存しますか？」
  // --------------------------------------------------
  function startSunkCostTimer() {
    if (chatState.sunkCostShown) return;
    chatState.conversationStartTime = chatState.conversationStartTime || Date.now();
    saveState();

    // 3分（180秒）後にLINE保存誘導
    var elapsed = Date.now() - chatState.conversationStartTime;
    var remaining = Math.max(0, 180000 - elapsed);

    setTimeout(function () {
      if (chatState.sunkCostShown || chatState.done || !chatState.isOpen) return;
      if (chatState.phase !== "ai") return;
      chatState.sunkCostShown = true;
      showSunkCostCTA();
      saveState();
    }, remaining);
  }

  function showSunkCostCTA() {
    var cta = document.createElement("div");
    cta.className = "chat-sunk-cost-cta";
    var salaryText = chatState.estimatedSalary
      ? "あなたの推定年収 " + chatState.estimatedSalary + "万円"
      : "ここまでの相談内容";
    cta.innerHTML =
      '<div class="sunk-cost-header">' + escapeHtml(salaryText) + 'の診断結果を保存しませんか？</div>' +
      '<a href="https://lin.ee/HJwmQgp4" target="_blank" rel="noopener" class="sunk-cost-btn">LINEで診断結果＋非公開求人を受け取る</a>' +
      '<div class="sunk-cost-note">専属アドバイザーが条件交渉もサポート・完全無料</div>';

    els.body.appendChild(cta);
    scrollToBottom();
    trackEvent("chat_sunk_cost_shown", { elapsed_min: Math.round((Date.now() - chatState.conversationStartTime) / 60000) });

    cta.querySelector(".sunk-cost-btn").addEventListener("click", function () {
      trackEvent("chat_sunk_cost_line_click");
    });
  }

  // --------------------------------------------------
  // 行動経済学: 年収推定計算
  // --------------------------------------------------
  function estimateSalary(area, priority) {
    var data = SALARY_ESTIMATES[area] || SALARY_ESTIMATES.undecided;
    // アンカリング: 高い数字を先に見せる
    var estimated = data.avg;
    // 優先度によって表示を変える
    if (priority === "salary") {
      estimated = data.top; // 最高値をアンカーに
    }
    // 経験年数による補正（EXP_MULTIPLIER適用）
    var expKey = null;
    if (chatState.experience === "1年未満") expKey = "1-3";
    else if (chatState.experience === "1〜3年") expKey = "1-3";
    else if (chatState.experience === "3〜5年") expKey = "3-5";
    else if (chatState.experience === "5〜10年") expKey = "5-10";
    else if (chatState.experience === "10年以上") expKey = "10+";
    if (expKey && EXP_MULTIPLIER[expKey]) {
      estimated = Math.round(estimated * EXP_MULTIPLIER[expKey]);
    }
    chatState.estimatedSalary = estimated;
    return {
      low: data.min,
      estimated: estimated,
      high: data.top,
      avg: data.avg,
    };
  }

  // --------------------------------------------------
  // プログレスバー（サンクコスト強化）
  // --------------------------------------------------
  function updateProgress(step, total) {
    var existing = document.getElementById("chatProgressBar");
    if (existing) existing.remove();

    var bar = document.createElement("div");
    bar.className = "chat-progress-bar";
    bar.id = "chatProgressBar";
    var pct = Math.round((step / total) * 100);
    bar.innerHTML =
      '<div class="progress-track"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="progress-label">ステップ ' + step + '/' + total + ' 完了</div>';

    // ヘッダーの直後に挿入
    var header = els.window.querySelector(".chat-header");
    if (header && header.nextSibling) {
      header.parentElement.insertBefore(bar, header.nextSibling);
    }
  }

  function showChatView() {
    if (els.chatView) els.chatView.classList.remove("hidden");
    requestAnimationFrame(function () { scrollToBottom(); });
  }

  function restoreChatView() {
    // Rebuild messages from saved state
    var savedMessages = chatState.messages.slice();
    chatState.messages = [];
    els.body.innerHTML = "";

    for (var i = 0; i < savedMessages.length; i++) {
      addMessage(savedMessages[i].role, savedMessages[i].content, true);
    }

    showChatView();

    // Restore input visibility based on phase
    if (chatState.phase === "ai" && !chatState.done) {
      setInputVisible(true);
      els.input.focus();
    } else if (chatState.done) {
      setInputVisible(false);
    } else {
      setInputVisible(false);
      // Resume the flow where we left off
      resumeFlow();
    }
  }

  function resumeFlow() {
    switch (chatState.phase) {
      case "intent":
        showButtonGroup(PRESCRIPTED.intents, handleIntentSelect);
        break;
      case "area":
        showButtonGroup(PRESCRIPTED.areas, handleAreaSelect);
        break;
      case "experience":
        showButtonGroup(PRESCRIPTED.experiences, handleExperienceSelect);
        break;
      case "priority":
        showButtonGroup(PRESCRIPTED.priorities, handlePrioritySelect);
        break;
      case "value":
        // Re-show value and CTA
        showFacilityCards();
        setTimeout(function () { showNaturalLineCTA(); }, 800);
        break;
      default:
        break;
    }
  }

  // --------------------------------------------------
  // Conversational Flow
  // --------------------------------------------------
  function startConversation() {
    chatState.phase = "greeting";
    chatState.conversationStartTime = Date.now();
    setInputVisible(false);
    updateProgress(0, 4);

    showTyping();
    setTimeout(function () {
      hideTyping();
      // 損失回避 + 即時性: 「損してるかも」フック → 30秒で診断
      addMessage("ai", "こんにちは！ナースロビーのロビーです。\n\n看護師5年目の平均年収は480万円。でも、同じ経験年数でも年収に100万円以上の差があるのを知っていますか？");

      setTimeout(function () {
        showTyping();
        setTimeout(function () {
          hideTyping();
          // 即時性: 「30秒で」= 低コスト感
          addMessage("ai", "30秒で、あなたの年収が相場と比べてどうか診断できます。何が気になりますか？");
          chatState.phase = "intent";
          updateProgress(1, 4);
          showButtonGroup(PRESCRIPTED.intents, handleIntentSelect);
          saveState();
        }, 500);
      }, 600);
    }, 800);
  }

  function handleIntentSelect(value, label) {
    chatState.intent = value;
    trackEvent("chat_intent_selected", { intent: value });
    removeButtonGroup();
    addMessage("user", label);

    chatState.phase = "area";

    // 損失回避フレーミング: 「知らないと損」を各意図に埋め込む
    var empathyMap = {
      search: "年収の相場を知らないまま転職すると、年間50万円以上損する可能性があります。\n\nまずエリアを教えてください。地域によって相場が大きく違います。",
      consult: "転職すべきかどうか、まず今の年収が相場と比べてどうかを知ることが大切です。\n\nどのあたりのエリアでお仕事されていますか？",
      browse: "情報を持っているかどうかで、転職の結果が大きく変わります。\n\nどのエリアの相場が気になりますか？",
    };

    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", empathyMap[value] || empathyMap.search);
      updateProgress(1, 4);
      showButtonGroup(PRESCRIPTED.areas, handleAreaSelect);
      saveState();
    }, 600);
  }

  function handleAreaSelect(value, label) {
    chatState.area = value;
    trackEvent("chat_area_selected", { area: value });
    removeButtonGroup();
    addMessage("user", label);

    chatState.phase = "experience";

    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", "ありがとうございます！\n\n看護師としてのご経験年数を教えてください。より正確な年収診断ができます。");
      updateProgress(2, 4);
      showButtonGroup(PRESCRIPTED.experiences, handleExperienceSelect);
      saveState();
    }, 600);
  }

  function handleExperienceSelect(value, label) {
    chatState.experience = value;
    trackEvent("chat_experience_selected", { experience: value });
    removeButtonGroup();
    addMessage("user", label);

    chatState.phase = "priority";

    showTyping();
    setTimeout(function () {
      hideTyping();
      var areaName = getAreaDisplayName(chatState.area);
      var salaryData = SALARY_ESTIMATES[chatState.area] || SALARY_ESTIMATES.undecided;
      // 経験年数に応じた共感メッセージ
      var expMessages = {
        "1年未満": "まだお若いですが、新人さんでも受け入れてくれる職場は意外とたくさんありますよ。",
        "1〜3年": "基本的なスキルが身についてきた時期ですね。選べる求人の幅が広がっています。",
        "3〜5年": "一通りできるようになった頃ですね。リーダー業務の経験は転職市場で大きな強みになります。",
        "5〜10年": "ベテランの域ですね。あなたの経験があれば、かなり好条件の求人が狙えます。",
        "10年以上": "豊富なご経験ですね。管理職や専門ポジションも含めて、最適な職場をお探しできます。",
      };
      var expMsg = expMessages[value] || "";
      // アンカリング: 高い数字を先に見せて「もらえるかも」感を出す
      addMessage("ai", expMsg + "\n\n" + areaName + "エリアの看護師さんの年収は " + salaryData.min + "〜" + salaryData.top + "万円と幅があります。\n\n転職で一番大切にしたいことを教えてください。あなたの市場価値をもっと正確に診断できます。");
      updateProgress(3, 4);
      showButtonGroup(PRESCRIPTED.priorities, handlePrioritySelect);
      saveState();
    }, 600);
  }

  function handlePrioritySelect(value, label) {
    chatState.priority = value;
    trackEvent("chat_priority_selected", { priority: value });
    removeButtonGroup();
    addMessage("user", label);

    // Move to value delivery
    chatState.phase = "value";
    deliverValue();
  }

  function deliverValue() {
    showTyping();
    setTimeout(function () {
      hideTyping();

      var matches = findMatchingHospitals(chatState.area);
      var areaName = getAreaDisplayName(chatState.area);
      var count = matches.length;

      // 行動経済学: 年収推定を即時表示（即時性 + アンカリング）
      var salary = estimateSalary(chatState.area, chatState.priority);
      updateProgress(4, 4);

      // 損失回避: 「今の年収より高い可能性」を強調
      var salaryMsg = "あなたの推定市場価値は年収 " + salary.estimated + "万円前後です。";
      if (chatState.priority === "salary") {
        salaryMsg += "\n条件次第で最大 " + salary.high + "万円も狙えます。";
      }
      salaryMsg += "\n\n" + areaName + "エリアで " + count + "件以上の求人を見つけました。";

      // 年収推定カード表示
      showSalaryEstimateCard(salary);

      addMessage("ai", salaryMsg);

      // Show facility cards
      setTimeout(function () {
        showFacilityCards();

        // Natural LINE CTA after value
        setTimeout(function () {
          showNaturalLineCTA();
          saveState();
        }, 1500);
      }, 800);
    }, 1000);
  }

  // --------------------------------------------------
  // 年収推定カード（即時価値提供 + アンカリング）
  // --------------------------------------------------
  function showSalaryEstimateCard(salary) {
    var card = document.createElement("div");
    card.className = "chat-salary-card";
    card.innerHTML =
      '<div class="salary-card-header">あなたの推定市場価値</div>' +
      '<div class="salary-card-value">' +
        '<span class="salary-card-amount">' + salary.estimated + '</span>' +
        '<span class="salary-card-unit">万円/年</span>' +
      '</div>' +
      '<div class="salary-card-range">' +
        '<span>' + salary.low + '万円</span>' +
        '<span class="salary-card-bar"><span class="salary-card-fill" style="left:' + Math.round((salary.estimated - salary.low) / (salary.high - salary.low) * 100) + '%"></span></span>' +
        '<span>' + salary.high + '万円</span>' +
      '</div>' +
      '<div class="salary-card-note">※経験年数・資格で変動します。詳細はLINEで無料診断</div>';

    els.body.appendChild(card);
    scrollToBottom();
    trackEvent("chat_salary_estimate_shown", { estimated: salary.estimated, area: chatState.area });
  }

  // --------------------------------------------------
  // Facility Cards (Value Delivery)
  // --------------------------------------------------
  function showFacilityCards() {
    var matches = findMatchingHospitals(chatState.area);
    if (matches.length === 0) return;

    var showCount = Math.min(matches.length, 3);
    var container = document.createElement("div");
    container.className = "chat-facility-cards";

    for (var i = 0; i < showCount; i++) {
      var h = matches[i];
      var isReferral = h.referral === true;
      var card = document.createElement("div");
      card.className = "chat-facility-card" + (isReferral ? " chat-facility-card--referral" : " chat-facility-card--info");

      // Highlight tag based on user priority
      var highlightTag = "";
      if (chatState.priority === "salary") highlightTag = h.salary;
      else if (chatState.priority === "commute") highlightTag = h.commute;
      else if (chatState.priority === "wlb") highlightTag = h.holidays;
      else highlightTag = h.features ? h.features.split("・")[0] : "";

      var badgeHtml = isReferral
        ? '<div class="facility-card-badge facility-card-badge--referral">紹介可能</div>'
        : '<div class="facility-card-badge facility-card-badge--info">エリア情報</div>';

      var ctaHtml = isReferral
        ? '<div class="facility-card-cta">LINEで詳しい条件を聞く</div>'
        : '<div class="facility-card-notify">求人状況はLINEでお調べします</div>';

      card.innerHTML =
        badgeHtml +
        '<div class="facility-card-name">' + escapeHtml(h.displayName) + '</div>' +
        '<div class="facility-card-highlight">' + escapeHtml(highlightTag) + '</div>' +
        '<div class="facility-card-details">' +
          '<span>' + escapeHtml(h.salary) + '</span>' +
          '<span>' + escapeHtml(h.holidays) + '</span>' +
        '</div>' +
        ctaHtml;

      container.appendChild(card);
    }

    if (matches.length > showCount) {
      var more = document.createElement("div");
      more.className = "facility-card-more";
      more.textContent = "他にも " + (matches.length - showCount) + " 件以上の求人があります";
      container.appendChild(more);
    }

    els.body.appendChild(container);
    scrollToBottom();
  }

  // --------------------------------------------------
  // Natural LINE CTA (not pushy)
  // --------------------------------------------------
  function showNaturalLineCTA() {
    chatState.lineCtaShown = true;

    showTyping();
    setTimeout(function () {
      hideTyping();
      // 損失回避 + サンクコスト: ここまでの診断結果を「失いたくない」心理
      var salaryText = chatState.estimatedSalary ? "推定年収 " + chatState.estimatedSalary + "万円" : "市場価値";
      addMessage("ai", salaryText + "の診断結果をお送りしました。\n\nLINEでは専属アドバイザーが非公開求人のご紹介、条件交渉、面接対策まで無料でサポートします。もちろん、ここでもう少しお話しすることもできますよ。");

      // 選択のパラドックス: 3択（デフォルト効果: LINEが最初=推奨）
      var options = [
        { label: "LINEで診断結果を受け取る", value: "line" },
        { label: "もう少し相談したい", value: "ai" },
        { label: "今日はここまでで大丈夫", value: "close" },
      ];

      var container = document.createElement("div");
      container.className = "chat-quick-replies";
      container.id = "chatButtonGroup";

      for (var i = 0; i < options.length; i++) {
        (function (opt) {
          var btn = document.createElement("button");
          btn.className = "chat-quick-reply" + (opt.value === "line" ? " chat-quick-reply-line" : "");
          btn.textContent = opt.label;
          btn.addEventListener("click", function () {
            removeButtonGroup();
            addMessage("user", opt.label);
            handlePostValueChoice(opt.value);
          });
          container.appendChild(btn);
        })(options[i]);
      }

      els.body.appendChild(container);
      scrollToBottom();
    }, 600);
  }

  function handlePostValueChoice(choice) {
    if (choice === "line") {
      trackEvent("chat_line_click", { phase: "post_value", area: chatState.area });
      showTyping();
      setTimeout(function () {
        hideTyping();
        // 即時性: 「今すぐ届く」感
        addMessage("ai", "ありがとうございます！\n\n診断結果と非公開求人リストをLINEでお送りします。専属アドバイザーが条件交渉や面接対策もサポートしますよ。友だち追加するとすぐに届きます。");
        showLineCard();
        saveState();
      }, 500);
    } else if (choice === "ai") {
      trackEvent("chat_continue_ai", { area: chatState.area });
      transitionToAIPhase();
    } else {
      trackEvent("chat_close_soft", { area: chatState.area });
      showTyping();
      setTimeout(function () {
        hideTyping();
        // サンクコスト: 診断結果が消えることを暗示
        addMessage("ai", "もちろんです！この診断結果は24時間保存されますので、またいつでも再開できます。\n\n気が向いたら、LINEで専属アドバイザーに非公開求人の相談もできますよ。");
        // Show a subtle LINE card even for close
        setTimeout(function () {
          showSoftLineCard();
          saveState();
        }, 1000);
      }, 500);
    }
  }

  function showLineCard() {
    var card = document.createElement("div");
    card.className = "chat-line-card";
    card.innerHTML =
      '<a href="https://lin.ee/HJwmQgp4" target="_blank" rel="noopener" class="chat-line-card-btn" id="chatLineMainBtn">' +
        'LINEで診断結果を受け取る' +
      '</a>' +
      '<div class="chat-line-card-trust">' +
        '<span>完全無料</span><span>専属アドバイザー付き</span><span>しつこい連絡なし</span>' +
      '</div>';

    els.body.appendChild(card);
    scrollToBottom();

    var btn = document.getElementById("chatLineMainBtn");
    if (btn) {
      btn.addEventListener("click", function () {
        trackEvent("chat_line_card_click", { phase: chatState.phase });
      });
    }
  }

  function showSoftLineCard() {
    var card = document.createElement("div");
    card.className = "chat-line-card chat-line-card-soft";
    card.innerHTML =
      '<div class="chat-line-card-note">非公開求人・条件交渉のご相談はこちら</div>' +
      '<a href="https://lin.ee/HJwmQgp4" target="_blank" rel="noopener" class="chat-line-card-btn chat-line-card-btn-soft">' +
        'LINEで専属アドバイザーに相談' +
      '</a>';

    els.body.appendChild(card);
    scrollToBottom();
  }

  // --------------------------------------------------
  // AI Phase (free conversation)
  // --------------------------------------------------
  function transitionToAIPhase() {
    chatState.phase = "ai";
    setInputVisible(true);

    // サンクコスト: 3分タイマー開始
    startSunkCostTimer();

    // Try API init (no phone required now - anonymous session)
    initAPISession();

    // Build context from pre-scripted flow + 年収推定
    var areaDisplay = getAreaDisplayName(chatState.area);
    var priorityLabels = { salary: "給与・待遇", commute: "通勤のしやすさ", wlb: "ワークライフバランス", environment: "職場の雰囲気" };
    var salaryContext = chatState.estimatedSalary ? " / 推定市場価値: 年収" + chatState.estimatedSalary + "万円前後" : "";
    var expContext = chatState.experience ? " / 経験年数: " + chatState.experience : "";
    var contextMsg = "【事前ヒアリング結果】希望エリア: " + (areaDisplay || "未選択") +
      expContext +
      " / 重視する条件: " + (priorityLabels[chatState.priority] || "未選択") + salaryContext +
      "。\n\n重要ルール:\n1. 質問は1回の返答で必ず1つだけ\n2. 先に推定年収を伝えているので、それを踏まえて「もっと高い年収を狙えるかも」「この条件なら今より○万円アップできそう」のように具体的な数字で会話する\n3. 「知らないと損する」「年間○万円の差がつく」等の損失回避フレーミングを自然に使う\n4. 共感を示しながら、1つずつ質問してください。";
    chatState.apiMessages.push({ role: "user", content: contextMsg });

    showTyping();

    if (isAPIAvailable() && !chatState.demoMode) {
      callAPI(chatState.apiMessages).then(function (response) {
        hideTyping();
        if (response && isValidReply(response.reply)) {
          addMessage("ai", response.reply);
          chatState.apiMessages.push({ role: "assistant", content: response.reply });
        } else {
          var fallback = "ありがとうございます！もう少し詳しくお伺いしますね。\n\n今のお仕事で、特に気になっていることはどんなことですか？（お給料、人間関係、夜勤、通勤…何でもOKです）";
          addMessage("ai", fallback);
          chatState.apiMessages.push({ role: "assistant", content: fallback });
        }
        els.input.focus();
        saveState();
      });
    } else {
      setTimeout(function () {
        hideTyping();
        var response = DEMO_RESPONSES[chatState.demoIndex] || DEMO_RESPONSES[0];
        chatState.demoIndex = Math.min(chatState.demoIndex + 1, DEMO_RESPONSES.length - 1);
        addMessage("ai", response.reply);
        chatState.apiMessages.push({ role: "assistant", content: response.reply });
        els.input.focus();
        saveState();
      }, 800);
    }
  }

  function initAPISession() {
    if (!isAPIAvailable()) return;
    // Try anonymous session init
    fetch(CHAT_CONFIG.workerEndpoint + "/api/chat-init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phone: "anonymous",
        honeypot: "",
        formShownAt: Date.now() - 5000,
      }),
    }).then(function (resp) {
      if (resp.ok) {
        return resp.json();
      }
      chatState.demoMode = true;
      return null;
    }).then(function (data) {
      if (data) {
        chatState.token = data.token || null;
        chatState.tokenTimestamp = data.timestamp || null;
        if (data.sessionId) chatState.sessionId = data.sessionId;
      }
    }).catch(function () {
      chatState.demoMode = true;
    });
  }

  // --------------------------------------------------
  // Messages
  // --------------------------------------------------
  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function addMessage(role, content, skipSave) {
    chatState.messages.push({ role: role, content: content });

    var msgEl = document.createElement("div");
    msgEl.className = "chat-message " + role;

    if (role === "ai") {
      var avatar = document.createElement("div");
      avatar.className = "chat-msg-avatar";
      avatar.textContent = "R";
      msgEl.appendChild(avatar);
    }

    var bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");
    msgEl.appendChild(bubble);

    els.body.appendChild(msgEl);
    scrollToBottom();

    if (!skipSave) saveState();
  }

  function sendMessage() {
    if (chatState.phase !== "ai") return;

    var text = els.input.value.trim();
    if (!text || chatState.isTyping || chatState.done || chatState.sendCooldown) return;

    // Session message limit
    if (chatState.userMessageCount >= CLIENT_RATE_LIMIT.maxSessionMessages) {
      addMessage("ai", "たくさんお話しいただきありがとうございます。\n\nいただいた内容をもとに、ぴったりの求人をLINEでお届けしますね。");
      els.input.disabled = true;
      els.sendBtn.disabled = true;
      showLineCard();
      chatState.done = true;
      saveState();
      return;
    }

    chatState.userMessageCount++;
    trackEvent("chat_message_sent", { message_count: chatState.userMessageCount });
    addMessage("user", text);
    els.input.value = "";
    els.input.style.height = "auto";

    chatState.apiMessages.push({ role: "user", content: text });
    startSendCooldown();
    processResponse();
  }

  function startSendCooldown() {
    chatState.sendCooldown = true;
    chatState.lastSendTime = Date.now();
    els.sendBtn.disabled = true;
    els.input.disabled = true;

    setTimeout(function () {
      chatState.sendCooldown = false;
      if (!chatState.isTyping && !chatState.done) {
        els.sendBtn.disabled = false;
        els.input.disabled = false;
        els.input.focus();
      }
    }, CLIENT_RATE_LIMIT.sendCooldownMs);
  }

  // --------------------------------------------------
  // AI Response Processing
  // --------------------------------------------------
  function processResponse() {
    showTyping();

    if (isAPIAvailable() && !chatState.demoMode) {
      callAPI(chatState.apiMessages).then(function (response) {
        hideTyping();
        if (response && response.isError) {
          addMessage("ai", response.reply);
          if (chatState.userMessageCount > 0) chatState.userMessageCount--;
          chatState.apiMessages.pop();
        } else if (response && isValidReply(response.reply)) {
          handleAIResponse(response);
        } else {
          addMessage("ai", getFallbackMessage());
        }
        maybeShowLineNudge();
        saveState();
      });
    } else {
      var delay = 800 + Math.random() * 1000;
      setTimeout(function () {
        hideTyping();
        var response = DEMO_RESPONSES[chatState.demoIndex] || DEMO_RESPONSES[DEMO_RESPONSES.length - 1];
        chatState.demoIndex = Math.min(chatState.demoIndex + 1, DEMO_RESPONSES.length - 1);
        handleAIResponse(response);
        maybeShowLineNudge();
        saveState();
      }, delay);
    }
  }

  function handleAIResponse(response) {
    addMessage("ai", response.reply);
    chatState.apiMessages.push({ role: "assistant", content: response.reply });

    if (response.score) chatState.score = response.score;

    if (response.done || chatState.userMessageCount >= CLIENT_RATE_LIMIT.maxSessionMessages) {
      chatState.done = true;
      onConversationComplete();
    }
  }

  // --------------------------------------------------
  // Gentle LINE Nudge (after 5 AI messages)
  // --------------------------------------------------
  function maybeShowLineNudge() {
    if (chatState.userMessageCount === 5 && !chatState.lineCtaShown) {
      var nudge = document.createElement("div");
      nudge.className = "chat-line-nudge";
      nudge.innerHTML =
        '<a href="https://lin.ee/HJwmQgp4" target="_blank" rel="noopener" class="chat-line-nudge-btn">' +
          'LINEで非公開求人＋条件交渉サポート' +
        '</a>';

      els.body.appendChild(nudge);
      scrollToBottom();

      nudge.querySelector("a").addEventListener("click", function () {
        trackEvent("chat_line_nudge_click", { message_count: chatState.userMessageCount });
      });
    }
  }

  // --------------------------------------------------
  // Conversation Complete
  // --------------------------------------------------
  function onConversationComplete() {
    els.input.disabled = true;
    els.sendBtn.disabled = true;
    els.input.placeholder = "会話が完了しました";
    setInputVisible(false);

    var summaryData = buildConversationSummary();
    trackEvent("chat_completed", { score: summaryData.score, message_count: summaryData.messageCount, area: chatState.area || "none" });

    // Send to backend
    sendChatComplete(summaryData);

    // サンクコスト + 損失回避のクロージング
    var score = summaryData.score;
    var salaryText = chatState.estimatedSalary ? "年収" + chatState.estimatedSalary + "万円" : "好条件";
    var closingMessages = {
      A: "詳しくお聞かせいただきありがとうございました！今の条件なら" + salaryText + "以上も十分狙えます。今動かないと、この好条件の求人が他の人に決まってしまう可能性もあります。専属アドバイザーが面接対策から条件交渉まで完全サポートします。",
      B: "お話しいただきありがとうございました！あなたの経験なら" + salaryText + "レベルの職場が見つかる可能性が高いです。非公開求人も含めて最適な職場をご提案します。",
      C: "ありがとうございました！相場を知っているだけで、転職の結果は大きく変わります。非公開求人の情報もLINEでお届けできます。",
      D: "お話しいただきありがとうございました。今回の診断結果は24時間保存されます。",
    };

    setTimeout(function () {
      addMessage("ai", (closingMessages[score] || closingMessages.C) + "\n\nここまでの診断結果と非公開求人をLINEでお届けします。");
      setTimeout(function () {
        showLineCard();
        saveState();
      }, 800);
    }, 800);
  }

  // --------------------------------------------------
  // Temperature Score Detection
  // --------------------------------------------------
  function detectTemperatureScore() {
    if (chatState.score) return chatState.score;

    var score = 0;
    var userMessages = [];
    for (var i = 0; i < chatState.messages.length; i++) {
      if (chatState.messages[i].role === "user") {
        userMessages.push(chatState.messages[i].content);
      }
    }
    var allText = userMessages.join(" ");

    var urgentKeywords = ["すぐ", "急ぎ", "今月", "来月", "退職済", "辞めた", "決まっている", "早く", "なるべく早"];
    for (var u = 0; u < urgentKeywords.length; u++) {
      if (allText.indexOf(urgentKeywords[u]) !== -1) { score += 3; break; }
    }

    var activeKeywords = ["面接", "見学", "応募", "給与", "年収", "月給", "具体的", "いつから", "条件"];
    for (var a = 0; a < activeKeywords.length; a++) {
      if (allText.indexOf(activeKeywords[a]) !== -1) { score += 1; }
    }

    if (chatState.userMessageCount >= 5) { score += 2; }
    else if (chatState.userMessageCount >= 3) { score += 1; }

    var totalLen = 0;
    for (var l = 0; l < userMessages.length; l++) { totalLen += userMessages[l].length; }
    if (totalLen > 200) { score += 1; }

    // Intent-based scoring
    if (chatState.intent === "search") score += 2;
    else if (chatState.intent === "consult") score += 1;

    if (score >= 6) return "A";
    if (score >= 3) return "B";
    if (score >= 1) return "C";
    return "D";
  }

  function buildConversationSummary() {
    var score = detectTemperatureScore();
    chatState.score = score;

    return {
      sessionId: chatState.sessionId,
      phone: "anonymous",
      intent: chatState.intent || null,
      area: chatState.area || null,
      priority: chatState.priority || null,
      score: score,
      messageCount: chatState.userMessageCount,
      messages: chatState.messages,
      completedAt: new Date().toISOString(),
    };
  }

  // --------------------------------------------------
  // Button Group Rendering
  // --------------------------------------------------
  function showButtonGroup(options, handler) {
    var container = document.createElement("div");
    container.className = "chat-quick-replies";
    container.id = "chatButtonGroup";

    for (var i = 0; i < options.length; i++) {
      (function (opt) {
        var btn = document.createElement("button");
        btn.className = "chat-quick-reply";
        btn.textContent = (opt.emoji ? opt.emoji + " " : "") + opt.label;
        btn.addEventListener("click", function () {
          handler(opt.value, opt.label);
        });
        container.appendChild(btn);
      })(options[i]);
    }

    els.body.appendChild(container);
    scrollToBottom();
  }

  function removeButtonGroup() {
    var group = document.getElementById("chatButtonGroup");
    if (group) group.remove();
  }

  function setInputVisible(visible) {
    var inputArea = els.input ? els.input.parentElement : null;
    if (inputArea) {
      inputArea.style.display = visible ? "flex" : "none";
      scrollToBottom();
    }
  }

  // --------------------------------------------------
  // Hospital Matching
  // --------------------------------------------------
  function findMatchingHospitals(area) {
    var hospitals = CHAT_CONFIG.hospitals;
    if (!hospitals || hospitals.length === 0) {
      return [
        { displayName: "小田原市立病院（小田原市・417床）", salary: "月給28〜38万円", holidays: "年間休日120日以上", nightShift: "あり（三交代制）", commute: "小田原駅バス10分", features: "2026年新築移転予定" },
        { displayName: "東海大学医学部付属病院（伊勢原市・804床）", salary: "月給29〜38万円", holidays: "年間休日120日以上", nightShift: "あり（三交代制）", commute: "伊勢原駅バス10分", features: "県西最大規模" },
        { displayName: "海老名総合病院（海老名市・479床）", salary: "月給29〜38万円", holidays: "年間休日115日以上", nightShift: "あり（二交代制）", commute: "海老名駅徒歩7分", features: "救命救急センター" },
      ];
    }

    if (!area || area === "undecided" || area === "other") {
      return hospitals;
    }

    var cities = PRESCRIPTED.areaCities && PRESCRIPTED.areaCities[area];
    if (!cities || cities.length === 0) return hospitals;

    var filtered = [];
    for (var i = 0; i < hospitals.length; i++) {
      if (!hospitals[i].displayName) continue;
      for (var c = 0; c < cities.length; c++) {
        if (hospitals[i].displayName.indexOf(cities[c]) !== -1) {
          filtered.push(hospitals[i]);
          break;
        }
      }
    }

    var result = filtered.length > 0 ? filtered : hospitals;
    // 紹介可能施設を先に表示
    result.sort(function (a, b) {
      if (a.referral && !b.referral) return -1;
      if (!a.referral && b.referral) return 1;
      return 0;
    });
    return result;
  }

  function getAreaDisplayName(areaValue) {
    return (PRESCRIPTED.areaLabels && PRESCRIPTED.areaLabels[areaValue]) || areaValue || "";
  }

  // --------------------------------------------------
  // Typing Indicator
  // --------------------------------------------------
  function showTyping() {
    chatState.isTyping = true;
    if (els.sendBtn) els.sendBtn.disabled = true;
    if (els.sendBtn) els.sendBtn.classList.add("loading");

    var typing = document.createElement("div");
    typing.className = "chat-typing";
    typing.id = "chatTypingIndicator";

    var avatar = document.createElement("div");
    avatar.className = "chat-msg-avatar";
    avatar.textContent = "R";
    typing.appendChild(avatar);

    var dots = document.createElement("div");
    dots.className = "chat-typing-dots";
    dots.innerHTML = "<span></span><span></span><span></span>";
    typing.appendChild(dots);

    els.body.appendChild(typing);
    scrollToBottom();
  }

  function hideTyping() {
    chatState.isTyping = false;
    if (els.sendBtn) els.sendBtn.classList.remove("loading");

    if (!chatState.sendCooldown && !chatState.done) {
      if (els.sendBtn) els.sendBtn.disabled = false;
      if (els.input) els.input.disabled = false;
    }

    var indicator = document.getElementById("chatTypingIndicator");
    if (indicator) indicator.remove();
    scrollToBottom();
  }

  // --------------------------------------------------
  // Response Validation
  // --------------------------------------------------
  function isValidReply(reply) {
    if (!reply || typeof reply !== "string") return false;
    if (reply.length < 5) return false;
    if (reply.trim().charAt(0) === "{" || reply.trim().charAt(0) === "[") return false;
    return true;
  }

  // --------------------------------------------------
  // API Integration
  // --------------------------------------------------
  function isAPIAvailable() {
    return CHAT_CONFIG.workerEndpoint && CHAT_CONFIG.workerEndpoint.length > 0;
  }

  function fetchWithTimeout(url, options, timeoutMs) {
    timeoutMs = timeoutMs || 20000;
    return new Promise(function (resolve, reject) {
      var aborted = false;
      var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
      if (controller) {
        options = Object.assign({}, options, { signal: controller.signal });
      }

      var timer = setTimeout(function () {
        aborted = true;
        if (controller) controller.abort();
        reject(new Error("Request timeout"));
      }, timeoutMs);

      fetch(url, options).then(function (res) {
        clearTimeout(timer);
        if (!aborted) resolve(res);
      }).catch(function (err) {
        clearTimeout(timer);
        if (!aborted) reject(err);
      });
    });
  }

  var FALLBACK_MESSAGES = [
    "申し訳ございません。一時的に接続が不安定です。少し時間をおいて再度お試しください。",
    "通信環境をご確認のうえ、再度メッセージを送信してください。",
    "ただいま混み合っております。しばらくお待ちいただいてから再度お試しください。",
  ];

  function getFallbackMessage() {
    return FALLBACK_MESSAGES[Math.floor(Math.random() * FALLBACK_MESSAGES.length)];
  }

  async function callAPI(messages) {
    try {
      var response = await fetchWithTimeout(CHAT_CONFIG.workerEndpoint + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: messages,
          sessionId: chatState.sessionId,
          phone: "anonymous",
          token: chatState.token || null,
          timestamp: chatState.tokenTimestamp || null,
          profession: "看護師",
          area: chatState.area,
          station: null,
          experience: chatState.experience || null,
        }),
      }, 20000);

      if (response.status === 429) {
        var errData = {};
        try { errData = await response.json(); } catch (e) { /* ignore */ }
        return {
          reply: errData.error || "リクエストが多すぎます。少しお待ちください。",
          done: false,
        };
      }

      if (!response.ok) {
        throw new Error("API response " + response.status);
      }

      var data = await response.json();

      if (typeof data.reply === "string") return data;
      if (data.content) {
        try { return JSON.parse(data.content); } catch (e) {
          return { reply: data.content, done: false };
        }
      }
      return null;
    } catch (err) {
      console.error("[Chat API Error]", err);
      if (err.message === "Request timeout") {
        return { reply: "応答に時間がかかっております。もう一度お試しいただけますか？", done: false, isError: true };
      }
      return { reply: getFallbackMessage(), done: false, isError: true };
    }
  }

  async function sendChatComplete(summaryData) {
    if (!CHAT_CONFIG.workerEndpoint || chatState.messages.length < 2) return null;
    try {
      var response = await fetchWithTimeout(CHAT_CONFIG.workerEndpoint + "/api/chat-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: "anonymous",
          sessionId: chatState.sessionId,
          token: chatState.token || null,
          timestamp: chatState.tokenTimestamp || null,
          messages: chatState.messages,
          profession: "看護師",
          area: chatState.area,
          station: null,
          score: summaryData ? summaryData.score : null,
          messageCount: summaryData ? summaryData.messageCount : chatState.userMessageCount,
          completedAt: summaryData ? summaryData.completedAt : new Date().toISOString(),
        }),
      }, 15000);
      if (response.ok) return await response.json();
      return null;
    } catch (err) {
      console.error("[Chat] chat-complete error:", err);
      return null;
    }
  }

  // --------------------------------------------------
  // Utilities
  // --------------------------------------------------
  function scrollToBottom() {
    if (scrollToBottom._t1) clearTimeout(scrollToBottom._t1);
    if (scrollToBottom._t2) clearTimeout(scrollToBottom._t2);
    if (scrollToBottom._t3) clearTimeout(scrollToBottom._t3);

    function doScroll() {
      if (!els.body) return;
      if (els.body.offsetParent === null) return;
      els.body.style.scrollBehavior = "auto";
      els.body.scrollTop = els.body.scrollHeight;
    }
    requestAnimationFrame(function () {
      requestAnimationFrame(doScroll);
    });
    scrollToBottom._t1 = setTimeout(doScroll, 80);
    scrollToBottom._t2 = setTimeout(doScroll, 250);
    scrollToBottom._t3 = setTimeout(doScroll, 450);
  }

  // --------------------------------------------------
  // Initialize
  // --------------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
