// ========================================
// ナースロビー - AI Chat Widget v4.0
// 心理学ドリブン コンバージョン設計
// 施設探索フック + 好奇心ギャップ + IKEA効果
// 行動経済学 + 動機づけ面接 + UX/CRO
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
  // 年収データ（透明な計算式で信頼感を出す）
  // --------------------------------------------------
  var SALARY_TABLE = {
    kensei:       { base: { min: 24, max: 30 }, nightPer: 10000, nightCount: 4, bonus: 3.5 },
    shonan_west:  { base: { min: 25, max: 32 }, nightPer: 11000, nightCount: 4, bonus: 3.8 },
    shonan_east:  { base: { min: 26, max: 33 }, nightPer: 11000, nightCount: 5, bonus: 4.0 },
    kenoh:        { base: { min: 25, max: 32 }, nightPer: 11000, nightCount: 4, bonus: 3.8 },
    undecided:    { base: { min: 25, max: 31 }, nightPer: 10500, nightCount: 4, bonus: 3.7 },
  };

  // 経験年数別の基本給補正（万円加算）
  var EXP_ADJUSTMENT = {
    "1年未満": 0, "1〜3年": 1, "3〜5年": 3, "5〜10年": 5, "10年以上": 8,
  };

  // --------------------------------------------------
  // Pre-scripted flow data（3ステップ: エリア → 関心事 → 経験年数）
  // --------------------------------------------------
  var PRESCRIPTED = {
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
    // 関心事: 看護師転職理由の実態に基づく順序
    // 1位: 人間関係、2位: 夜勤負担、3位: 給与、4位: 通勤
    concerns: [
      { label: "職場の雰囲気・人間関係", value: "environment", feedback: "転職理由の第1位。実際の雰囲気は外から見えにくいですよね" },
      { label: "夜勤の負担", value: "nightshift", feedback: "体調やプライベートへの影響が大きいですよね" },
      { label: "お給料・待遇", value: "salary", feedback: "同じ経験年数でも施設により月3〜5万円の差があります" },
      { label: "通勤のしやすさ", value: "commute", feedback: "毎日のことだから、通勤は想像以上に大切ですよね" },
    ],
    experiences: [
      { label: "1年未満", value: "1年未満" },
      { label: "1〜3年", value: "1〜3年" },
      { label: "3〜5年", value: "3〜5年" },
      { label: "5〜10年", value: "5〜10年" },
      { label: "10年以上", value: "10年以上" },
    ],
    // エリア別の施設数（ユーザーの好奇心を引くデータ）
    areaFacilityCounts: {
      kensei: 42,
      shonan_west: 24,
      shonan_east: 15,
      kenoh: 16,
      undecided: 97,
    },
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
    // Conversational flow state (v4: 3-step)
    phase: "greeting", // "greeting" | "area" | "concern" | "experience" | "value" | "curiosity_gap" | "ai" | "done"
    area: null,
    concern: null,
    experience: null,
    // Sunk cost tracking
    conversationStartTime: null,
    sunkCostShown: false,
    // Salary calculation results
    salaryBreakdown: null,
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
        area: chatState.area,
        concern: chatState.concern,
        experience: chatState.experience,
        userMessageCount: chatState.userMessageCount,
        score: chatState.score,
        done: chatState.done,
        lineCtaShown: chatState.lineCtaShown,
        demoIndex: chatState.demoIndex,
        conversationStartTime: chatState.conversationStartTime,
        sunkCostShown: chatState.sunkCostShown,
        salaryBreakdown: chatState.salaryBreakdown,
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
      chatState.area = data.area || null;
      chatState.concern = data.concern || null;
      chatState.experience = data.experience || null;
      chatState.userMessageCount = data.userMessageCount || 0;
      chatState.score = data.score || null;
      chatState.done = data.done || false;
      chatState.lineCtaShown = data.lineCtaShown || false;
      chatState.demoIndex = data.demoIndex || 0;
      chatState.conversationStartTime = data.conversationStartTime || null;
      chatState.sunkCostShown = data.sunkCostShown || false;
      chatState.salaryBreakdown = data.salaryBreakdown || null;
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

    // Escape key to close + focus trap
    document.addEventListener("keydown", function (e) {
      if (!chatState.isOpen) return;
      if (e.key === "Escape") {
        e.preventDefault();
        closeChat();
        return;
      }
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

    // Proactive peek message after 15 seconds
    setTimeout(function () {
      if (!chatState.isOpen && !chatState.peekDismissed) {
        showPeekMessage();
      }
    }, 15000);
  }

  // --------------------------------------------------
  // Proactive Peek Message（施設探索フック）
  // --------------------------------------------------
  function showPeekMessage() {
    if (chatState.peekShown || chatState.isOpen) return;
    chatState.peekShown = true;

    var peek = document.createElement("div");
    peek.className = "chat-peek";
    peek.id = "chatPeek";
    // 好奇心ギャップ: 「何件あるか知ってますか？」→ 答えを知りたくなる
    peek.innerHTML =
      '<div class="chat-peek-text">通勤30分圏内の病院、<br><strong>何件あるか知ってますか？</strong></div>' +
      '<button class="chat-peek-close" aria-label="閉じる">&times;</button>';

    els.toggle.parentElement.insertBefore(peek, els.toggle);

    peek.querySelector(".chat-peek-text").addEventListener("click", function () {
      peek.remove();
      trackEvent("chat_peek_click");
      openChat();
    });

    peek.querySelector(".chat-peek-close").addEventListener("click", function (e) {
      e.stopPropagation();
      chatState.peekDismissed = true;
      peek.classList.add("chat-peek-hiding");
      setTimeout(function () { peek.remove(); }, 300);
    });

    trackEvent("chat_peek_shown");

    // Auto-dismiss after 12 seconds
    setTimeout(function () {
      var el = document.getElementById("chatPeek");
      if (el && !chatState.isOpen) {
        el.classList.add("chat-peek-hiding");
        setTimeout(function () { if (el.parentElement) el.remove(); }, 300);
      }
    }, 12000);
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
      restoreChatView();
      showResumeNotice();
    } else if (chatState.messages.length === 0) {
      setInputVisible(false);
      startConversation();
    } else {
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
  // セッション復帰通知
  // --------------------------------------------------
  function showResumeNotice() {
    if (!chatState.messages.length) return;
    var notice = document.createElement("div");
    notice.className = "chat-resume-notice";
    notice.innerHTML = '<span>前回の続きから再開しています</span>';
    els.body.appendChild(notice);
    scrollToBottom();
    setTimeout(function () {
      notice.classList.add("chat-resume-hiding");
      setTimeout(function () { if (notice.parentElement) notice.remove(); }, 500);
    }, 3000);
  }

  // --------------------------------------------------
  // サンクコスト: 3分タイマー → LINE保存誘導
  // --------------------------------------------------
  function startSunkCostTimer() {
    if (chatState.sunkCostShown) return;
    chatState.conversationStartTime = chatState.conversationStartTime || Date.now();
    saveState();

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
    // ツァイガルニク効果: 「まだ確認していない情報がある」
    var cta = document.createElement("div");
    cta.className = "chat-curiosity-card";
    cta.innerHTML =
      '<div class="curiosity-header">ここまでの相談内容を保存しませんか？</div>' +
      '<div class="curiosity-body">担当アドバイザーが、あなたの条件に合う<strong>非公開求人</strong>も含めてお探しします</div>' +
      '<a href="https://lin.ee/oUgDB3x" target="_blank" rel="noopener" class="curiosity-btn">LINEで相談内容を引き継ぐ</a>' +
      '<div class="curiosity-note">完全無料・しつこい連絡なし</div>';

    els.body.appendChild(cta);
    scrollToBottom();
    trackEvent("chat_sunk_cost_shown", { elapsed_min: Math.round((Date.now() - chatState.conversationStartTime) / 60000) });

    cta.querySelector(".curiosity-btn").addEventListener("click", function () {
      trackEvent("chat_sunk_cost_line_click");
    });
  }

  // --------------------------------------------------
  // 年収計算（透明な内訳を表示して信頼感を出す）
  // --------------------------------------------------
  function calculateSalary(area, experience, concern) {
    var data = SALARY_TABLE[area] || SALARY_TABLE.undecided;
    var expAdj = EXP_ADJUSTMENT[experience] || 0;

    // 基本給（経験年数で補正）
    var baseMin = data.base.min + expAdj;
    var baseMax = data.base.max + expAdj;
    var baseMid = Math.round((baseMin + baseMax) / 2);

    // 夜勤手当（月額）
    var nightMonthly = Math.round(data.nightPer * data.nightCount / 10000 * 10) / 10;

    // 資格手当（概算）
    var certMonthly = 1.5; // 万円

    // 月収
    var monthlyMin = baseMin + nightMonthly + certMonthly;
    var monthlyMax = baseMax + nightMonthly + certMonthly;
    var monthlyMid = Math.round((monthlyMin + monthlyMax) / 2 * 10) / 10;

    // 年収（月給×12 + 賞与）
    var annualMin = Math.round(monthlyMin * 12 + baseMid * data.bonus);
    var annualMax = Math.round(monthlyMax * 12 + baseMid * data.bonus);
    var annualMid = Math.round((annualMin + annualMax) / 2);

    var breakdown = {
      baseMin: baseMin,
      baseMax: baseMax,
      baseMid: baseMid,
      nightPer: data.nightPer,
      nightCount: data.nightCount,
      nightMonthly: nightMonthly,
      certMonthly: certMonthly,
      monthlyMin: monthlyMin,
      monthlyMax: monthlyMax,
      monthlyMid: monthlyMid,
      bonusMonths: data.bonus,
      annualMin: annualMin,
      annualMax: annualMax,
      annualMid: annualMid,
    };

    chatState.salaryBreakdown = breakdown;
    return breakdown;
  }

  // --------------------------------------------------
  // プログレスバー
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
      '<div class="progress-label">' + step + ' / ' + total + '</div>';

    var header = els.window.querySelector(".chat-header");
    if (header && header.nextSibling) {
      header.parentElement.insertBefore(bar, header.nextSibling);
    }
  }

  function removeProgress() {
    var existing = document.getElementById("chatProgressBar");
    if (existing) existing.remove();
  }

  function showChatView() {
    if (els.chatView) els.chatView.classList.remove("hidden");
    requestAnimationFrame(function () { scrollToBottom(); });
  }

  function restoreChatView() {
    var savedMessages = chatState.messages.slice();
    chatState.messages = [];
    els.body.innerHTML = "";

    for (var i = 0; i < savedMessages.length; i++) {
      addMessage(savedMessages[i].role, savedMessages[i].content, true);
    }

    showChatView();

    if (chatState.phase === "ai" && !chatState.done) {
      setInputVisible(true);
      els.input.focus();
    } else if (chatState.done) {
      setInputVisible(false);
    } else {
      setInputVisible(false);
      resumeFlow();
    }
  }

  function resumeFlow() {
    switch (chatState.phase) {
      case "area":
        showButtonGroup(PRESCRIPTED.areas, handleAreaSelect);
        break;
      case "concern":
        showButtonGroup(PRESCRIPTED.concerns, handleConcernSelect);
        break;
      case "experience":
        showButtonGroup(PRESCRIPTED.experiences, handleExperienceSelect);
        break;
      case "value":
        deliverValue();
        break;
      case "curiosity_gap":
        showCuriosityGapCTA();
        break;
      default:
        break;
    }
  }

  // --------------------------------------------------
  // Conversational Flow（v4: 3ステップ）
  // --------------------------------------------------
  function startConversation() {
    chatState.phase = "greeting";
    chatState.conversationStartTime = Date.now();
    setInputVisible(false);

    showTyping();
    setTimeout(function () {
      hideTyping();
      // IKEA効果 + 施設探索フック: 「あなたが自分で探せる」感覚
      addMessage("ai", "こんにちは！ナースロビーのロビーです。\n\n神奈川県西部の医療施設データベース（97施設）から、あなたの通勤圏内の病院を探せます。3つ質問するだけで候補が出ます。");

      setTimeout(function () {
        showTyping();
        setTimeout(function () {
          hideTyping();
          // Foot-in-the-door: 最も簡単な質問から始める
          addMessage("ai", "まず、どのエリアで働きたいですか？");
          chatState.phase = "area";
          updateProgress(1, 3);
          showButtonGroup(PRESCRIPTED.areas, handleAreaSelect);
          saveState();
        }, 400);
      }, 500);
    }, 700);
  }

  // --------------------------------------------------
  // Step 1: エリア選択 + 即時フィードバック
  // --------------------------------------------------
  function handleAreaSelect(value, label) {
    chatState.area = value;
    trackEvent("chat_area_selected", { area: value });
    removeButtonGroup();
    addMessage("user", label);

    chatState.phase = "concern";

    showTyping();
    setTimeout(function () {
      hideTyping();
      // 即時フィードバック: 具体的な数字で「データベースの強み」を見せる
      var count = PRESCRIPTED.areaFacilityCounts[value] || 97;
      var areaName = getAreaDisplayName(value);
      addMessage("ai", areaName + "エリアには " + count + " 件の医療施設があります。\n\nあなたの候補を絞り込むために、今の職場で一番気になっていることを教えてください。");
      updateProgress(2, 3);
      showButtonGroup(PRESCRIPTED.concerns, handleConcernSelect);
      saveState();
    }, 500);
  }

  // --------------------------------------------------
  // Step 2: 関心事選択 + 即時フィードバック
  // --------------------------------------------------
  function handleConcernSelect(value, label) {
    chatState.concern = value;
    trackEvent("chat_concern_selected", { concern: value });
    removeButtonGroup();
    addMessage("user", label);

    chatState.phase = "experience";

    // 選択した関心事に合わせたフィードバック
    var selectedConcern = null;
    for (var i = 0; i < PRESCRIPTED.concerns.length; i++) {
      if (PRESCRIPTED.concerns[i].value === value) {
        selectedConcern = PRESCRIPTED.concerns[i];
        break;
      }
    }

    showTyping();
    setTimeout(function () {
      hideTyping();
      var feedbackText = selectedConcern ? selectedConcern.feedback : "";
      addMessage("ai", feedbackText + "\n\n最後に、看護師としてのご経験年数を教えてください。より正確な情報をお出しできます。");
      updateProgress(3, 3);
      showButtonGroup(PRESCRIPTED.experiences, handleExperienceSelect);
      saveState();
    }, 500);
  }

  // --------------------------------------------------
  // Step 3: 経験年数選択 → 価値提供へ
  // --------------------------------------------------
  function handleExperienceSelect(value, label) {
    chatState.experience = value;
    trackEvent("chat_experience_selected", { experience: value });
    removeButtonGroup();
    addMessage("user", label);

    // 経験年数に応じた即時フィードバック
    var expFeedbacks = {
      "1年未満": "新人さんでも受け入れてくれる職場は意外とたくさんありますよ。",
      "1〜3年": "基本スキルが身についた時期ですね。選べる職場の幅が広がっています。",
      "3〜5年": "一通りできる頃ですね。リーダー経験があれば転職市場で強みになります。",
      "5〜10年": "ベテランですね。あなたの経験があれば好条件の求人が狙えます。",
      "10年以上": "豊富なご経験ですね。管理職や専門ポジションも含めて探せます。",
    };

    showTyping();
    setTimeout(function () {
      hideTyping();
      var fb = expFeedbacks[value] || "";
      addMessage("ai", fb + "\n\nお待ちください。条件に合う施設を検索しています...");
      removeProgress();
      chatState.phase = "value";
      saveState();

      // 少し間を置いて価値提供（期待感を高める）
      setTimeout(function () {
        deliverValue();
      }, 800);
    }, 500);
  }

  // --------------------------------------------------
  // 価値提供: 施設カード → 年収内訳 → 好奇心ギャップCTA
  // --------------------------------------------------
  function deliverValue() {
    var matches = findMatchingHospitals(chatState.area);
    var areaName = getAreaDisplayName(chatState.area);
    var count = PRESCRIPTED.areaFacilityCounts[chatState.area] || 97;
    var salary = calculateSalary(chatState.area, chatState.experience, chatState.concern);

    // IKEA効果: 「あなた専用の候補リスト」感
    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", areaName + "エリアで " + matches.length + " 件の施設が見つかりました。あなたの条件に合いそうな施設を紹介します。");

      // 施設カードを先に表示（具体的な価値を先に見せる）
      setTimeout(function () {
        showFacilityCards();

        // 年収内訳カードを表示（透明な計算式で信頼感）
        setTimeout(function () {
          showSalaryBreakdownCard(salary);

          // 好奇心ギャップ LINE CTA
          setTimeout(function () {
            showCuriosityGapCTA();
            saveState();
          }, 1200);
        }, 800);
      }, 600);
    }, 600);
  }

  // --------------------------------------------------
  // 年収内訳カード（透明な計算式で信頼感を出す）
  // --------------------------------------------------
  function showSalaryBreakdownCard(salary) {
    var card = document.createElement("div");
    card.className = "chat-salary-breakdown";
    card.innerHTML =
      '<div class="salary-bd-header">年収シミュレーション（' + getAreaDisplayName(chatState.area) + '・' + chatState.experience + '）</div>' +
      '<div class="salary-bd-items">' +
        '<div class="salary-bd-item">' +
          '<span class="salary-bd-label">基本給</span>' +
          '<span class="salary-bd-value">月' + salary.baseMin + '〜' + salary.baseMax + '万円</span>' +
        '</div>' +
        '<div class="salary-bd-item">' +
          '<span class="salary-bd-label">夜勤手当</span>' +
          '<span class="salary-bd-value">月' + salary.nightMonthly + '万円<span class="salary-bd-detail">（' + (salary.nightPer / 10000).toFixed(1) + '万×' + salary.nightCount + '回）</span></span>' +
        '</div>' +
        '<div class="salary-bd-item">' +
          '<span class="salary-bd-label">資格手当等</span>' +
          '<span class="salary-bd-value">月' + salary.certMonthly + '万円</span>' +
        '</div>' +
        '<div class="salary-bd-item">' +
          '<span class="salary-bd-label">賞与</span>' +
          '<span class="salary-bd-value">' + salary.bonusMonths + 'ヶ月分</span>' +
        '</div>' +
      '</div>' +
      '<div class="salary-bd-total">' +
        '<span class="salary-bd-total-label">推定年収</span>' +
        '<span class="salary-bd-total-value">' + salary.annualMin + '〜' + salary.annualMax + '万円</span>' +
      '</div>' +
      '<div class="salary-bd-note">※施設・勤務形態により変動します。日勤のみの場合は夜勤手当分が減額されます</div>';

    els.body.appendChild(card);
    scrollToBottom();
    trackEvent("chat_salary_breakdown_shown", { annual_mid: salary.annualMid, area: chatState.area });
  }

  // --------------------------------------------------
  // 施設カード（IKEA効果: 自分で選ぶ感覚）
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

      // ユーザーの関心事に合わせたハイライト
      var highlightTag = "";
      if (chatState.concern === "salary") highlightTag = h.salary;
      else if (chatState.concern === "commute") highlightTag = h.commute;
      else if (chatState.concern === "nightshift") highlightTag = h.nightShift ? h.nightShift : "";
      else if (chatState.concern === "environment") highlightTag = h.features ? h.features.split("・")[0] : "";
      else highlightTag = h.features ? h.features.split("・")[0] : "";

      var badgeHtml = isReferral
        ? '<div class="facility-card-badge facility-card-badge--referral">紹介可能</div>'
        : '<div class="facility-card-badge facility-card-badge--info">エリア情報</div>';

      // 好奇心ギャップ: CTAは「内部情報」をフックに
      var ctaHtml = isReferral
        ? '<div class="facility-card-cta">この施設の詳細を聞く</div>'
        : '<div class="facility-card-notify">内部情報はLINEで確認できます</div>';

      // Enriched tags
      var enrichedTags = [];
      if (h.nursingRatio) enrichedTags.push(h.nursingRatio);
      if (h.emergencyLevel) enrichedTags.push(h.emergencyLevel);
      if (h.ownerType) enrichedTags.push(h.ownerType);
      if (h.dpcHospital) enrichedTags.push("DPC対象");
      var enrichedTagsHtml = "";
      if (enrichedTags.length > 0) {
        enrichedTagsHtml = '<div class="facility-card-tags">';
        for (var t = 0; t < enrichedTags.length; t++) {
          enrichedTagsHtml += '<span class="facility-card-tag">' + escapeHtml(enrichedTags[t]) + '</span>';
        }
        enrichedTagsHtml += '</div>';
      }

      // Stats
      var statsItems = [];
      if (h.ambulanceCount && h.ambulanceCount > 0) {
        statsItems.push("救急車 年" + h.ambulanceCount.toLocaleString() + "台");
      }
      if (h.doctorCount && h.doctorCount > 0) {
        statsItems.push("医師" + h.doctorCount + "名");
      }
      var statsHtml = "";
      if (statsItems.length > 0) {
        statsHtml = '<div class="facility-card-stats">';
        for (var s = 0; s < statsItems.length; s++) {
          statsHtml += '<span>' + escapeHtml(statsItems[s]) + '</span>';
        }
        statsHtml += '</div>';
      }

      // Data source
      var sourceHtml = "";
      if (h.dataSource || h.lastUpdated) {
        var sourceText = "出典: " + (h.dataSource || "公開情報");
        if (h.lastUpdated) sourceText += "（" + h.lastUpdated + "）";
        sourceHtml = '<div class="facility-card-source">' + escapeHtml(sourceText) + '</div>';
      }

      card.innerHTML =
        badgeHtml +
        '<div class="facility-card-name">' + escapeHtml(h.displayName) + '</div>' +
        enrichedTagsHtml +
        '<div class="facility-card-highlight">' + escapeHtml(highlightTag) + '</div>' +
        '<div class="facility-card-details">' +
          '<span>' + escapeHtml(h.salary) + '</span>' +
          '<span>' + escapeHtml(h.holidays) + '</span>' +
        '</div>' +
        statsHtml +
        sourceHtml +
        ctaHtml;

      container.appendChild(card);
    }

    if (matches.length > showCount) {
      var more = document.createElement("div");
      more.className = "facility-card-more";
      more.textContent = "他にも " + (matches.length - showCount) + " 件の施設があります";
      container.appendChild(more);
    }

    els.body.appendChild(container);
    scrollToBottom();
  }

  // --------------------------------------------------
  // 好奇心ギャップ LINE CTA（1回目: 価値提供後）
  // --------------------------------------------------
  function showCuriosityGapCTA() {
    chatState.phase = "curiosity_gap";
    chatState.lineCtaShown = true;

    showTyping();
    setTimeout(function () {
      hideTyping();

      // 好奇心ギャップ: 「内部情報」という見えないものへの欲求を刺激
      var concernText = "";
      if (chatState.concern === "environment") {
        concernText = "気になる施設の人間関係や職場の雰囲気は、求人票には載っていません。";
      } else if (chatState.concern === "nightshift") {
        concernText = "夜勤の実態（忙しさ・仮眠の取りやすさ・スタッフ数）は、外からは見えません。";
      } else if (chatState.concern === "salary") {
        concernText = "実際の手取り額や昇給ペースは、求人票の数字だけでは分かりません。";
      } else {
        concernText = "通勤ルートの実際の混雑状況や、車通勤の可否など、細かい情報があります。";
      }

      addMessage("ai", concernText + "\n\n施設の内部情報や非公開求人はLINEでお伝えしています。もちろん、ここでもう少しお話しすることもできますよ。");

      // 選択肢: LINE / もう少し相談 / 今日はここまで
      var options = [
        { label: "LINEで内部情報を聞く", value: "line" },
        { label: "もう少し相談したい", value: "ai" },
        { label: "今日はここまで", value: "close" },
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
    }, 500);
  }

  function handlePostValueChoice(choice) {
    if (choice === "line") {
      trackEvent("chat_line_click", { phase: "curiosity_gap", area: chatState.area, concern: chatState.concern });
      showTyping();
      setTimeout(function () {
        hideTyping();
        addMessage("ai", "ありがとうございます！\n\n施設の内部情報と非公開求人をLINEでお伝えします。友だち追加するとすぐにご連絡しますね。");
        showLineCard();
        saveState();
      }, 400);
    } else if (choice === "ai") {
      trackEvent("chat_continue_ai", { area: chatState.area });
      transitionToAIPhase();
    } else {
      trackEvent("chat_close_soft", { area: chatState.area });
      showTyping();
      setTimeout(function () {
        hideTyping();
        addMessage("ai", "もちろんです！この結果は24時間保存されますので、またいつでもどうぞ。\n\n気が向いたら、LINEで内部情報の相談もできますよ。");
        showSoftLineCard();
        saveState();
      }, 400);
    }
  }

  function showLineCard() {
    var card = document.createElement("div");
    card.className = "chat-line-card";
    card.innerHTML =
      '<a href="https://lin.ee/oUgDB3x" target="_blank" rel="noopener" class="chat-line-card-btn" id="chatLineMainBtn">' +
        'LINEで内部情報を受け取る' +
      '</a>' +
      '<div class="chat-line-card-trust">' +
        '<span>完全無料</span><span>しつこい連絡なし</span><span>手数料10%</span>' +
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
      '<div class="chat-line-card-note">施設の内部情報・非公開求人のご相談</div>' +
      '<a href="https://lin.ee/oUgDB3x" target="_blank" rel="noopener" class="chat-line-card-btn chat-line-card-btn-soft">' +
        'LINEで相談する' +
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

    // API初期化
    initAPISession();

    // Build context from pre-scripted flow
    var areaDisplay = getAreaDisplayName(chatState.area);
    var concernLabels = { salary: "給与・待遇", commute: "通勤のしやすさ", nightshift: "夜勤の負担", environment: "職場の雰囲気・人間関係" };
    var salaryContext = chatState.salaryBreakdown ? " / 推定年収: " + chatState.salaryBreakdown.annualMin + "〜" + chatState.salaryBreakdown.annualMax + "万円" : "";
    var expContext = chatState.experience ? " / 経験年数: " + chatState.experience : "";
    var contextMsg = "【事前ヒアリング結果】希望エリア: " + (areaDisplay || "未選択") +
      expContext +
      " / 一番の関心事: " + (concernLabels[chatState.concern] || "未選択") + salaryContext +
      "。\n\n重要ルール:\n1. 質問は1回の返答で必ず1つだけ\n2. 看護師の転職理由1位は人間関係、2位は夜勤。年収は3位。相手の関心事に合わせた会話をする\n3. 「この施設の内部情報はLINEで確認できます」「実際の夜勤体制はLINEでお伝えしています」のように、内部情報をフックにLINEへ自然に誘導\n4. 共感を示しながら、具体的な施設名・数字を含めて1つずつ質問してください。";
    chatState.apiMessages.push({ role: "user", content: contextMsg });

    showTyping();

    if (isAPIAvailable() && !chatState.demoMode) {
      callAPI(chatState.apiMessages).then(function (response) {
        hideTyping();
        if (response && isValidReply(response.reply)) {
          addMessage("ai", response.reply);
          chatState.apiMessages.push({ role: "assistant", content: response.reply });
        } else {
          var fallback = "ありがとうございます！もう少し詳しくお伺いしますね。\n\n今のお仕事で、特に変えたいなと感じていることはどんなことですか？";
          addMessage("ai", fallback);
          chatState.apiMessages.push({ role: "assistant", content: fallback });
        }
        els.input.focus();
        saveState();
      }).catch(function () {
        hideTyping();
        chatState.demoMode = true;
        var fallback = "ありがとうございます！もう少し詳しくお伺いしますね。\n\n今のお仕事で、特に変えたいなと感じていることはどんなことですか？";
        addMessage("ai", fallback);
        chatState.apiMessages.push({ role: "assistant", content: fallback });
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

    if (chatState.userMessageCount >= CLIENT_RATE_LIMIT.maxSessionMessages) {
      addMessage("ai", "たくさんお話しいただきありがとうございます。\n\nあなたの条件に合う施設の内部情報をLINEでお伝えします。");
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
        saveState();
      });
    } else {
      var delay = 800 + Math.random() * 1000;
      setTimeout(function () {
        hideTyping();
        var response = DEMO_RESPONSES[chatState.demoIndex] || DEMO_RESPONSES[DEMO_RESPONSES.length - 1];
        chatState.demoIndex = Math.min(chatState.demoIndex + 1, DEMO_RESPONSES.length - 1);
        handleAIResponse(response);
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
  // Conversation Complete
  // --------------------------------------------------
  function onConversationComplete() {
    els.input.disabled = true;
    els.sendBtn.disabled = true;
    els.input.placeholder = "会話が完了しました";
    setInputVisible(false);

    var summaryData = buildConversationSummary();
    trackEvent("chat_completed", { score: summaryData.score, message_count: summaryData.messageCount, area: chatState.area || "none" });

    sendChatComplete(summaryData);

    // 2回目のLINE CTA（最終）: 好奇心ギャップで締める
    var score = summaryData.score;
    var closingMessages = {
      A: "詳しくお聞かせいただきありがとうございました！あなたの経験なら、かなり良い条件の施設が見つかりそうです。内部情報と非公開求人を含めて、LINEで詳しくご案内しますね。",
      B: "お話しいただきありがとうございました！条件に合いそうな施設の内部情報をまとめてLINEでお送りしますね。",
      C: "ありがとうございました！気になる施設の詳しい情報はLINEでいつでもお聞きいただけます。",
      D: "お話しいただきありがとうございました。この結果は24時間保存されます。",
    };

    setTimeout(function () {
      addMessage("ai", closingMessages[score] || closingMessages.C);
      setTimeout(function () {
        showLineCard();
        saveState();
      }, 600);
    }, 600);
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

    // Concern-based scoring
    if (chatState.concern === "salary") score += 1;
    if (chatState.concern === "environment") score += 1;

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
      area: chatState.area || null,
      concern: chatState.concern || null,
      experience: chatState.experience || null,
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
      (function (opt, idx) {
        var btn = document.createElement("button");
        btn.className = "chat-quick-reply";
        btn.textContent = (opt.emoji ? opt.emoji + " " : "") + opt.label;
        // Staggered animation
        btn.style.animationDelay = (idx * 0.06) + "s";
        btn.addEventListener("click", function () {
          handler(opt.value, opt.label);
        });
        container.appendChild(btn);
      })(options[i], i);
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
