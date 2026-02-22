// ========================================
// ROBBY THE MATCH - AI Chat Widget
// Phone-gated + hybrid pre-scripted/AI chat
// ========================================

(function () {
  "use strict";

  // --------------------------------------------------
  // Configuration
  // --------------------------------------------------
  var CHAT_CONFIG = {
    brandName: typeof CONFIG !== "undefined" ? CONFIG.BRAND_NAME : "ROBBY THE MATCH",
    workerEndpoint: typeof CONFIG !== "undefined" ? CONFIG.API.workerEndpoint : "",
    hospitals: typeof CONFIG !== "undefined" ? CONFIG.HOSPITALS : [],
    stepLabels: [
      "職種の確認",
      "エリアの確認",
      "条件ヒアリング",
      "求人検索中",
      "ご案内準備完了",
    ],
  };

  // --------------------------------------------------
  // Pre-scripted flow data
  // --------------------------------------------------
  var PRESCRIPTED = {
    professions: [
      { label: "看護師", value: "看護師" },
      { label: "リハビリ技師", value: "リハビリ技師" },
      { label: "その他の医療職", value: "その他" },
    ],
    areas: [
      { label: "県西エリア（小田原・南足柄）", value: "kensei" },
      { label: "湘南西部（平塚・秦野・伊勢原）", value: "shonan_west" },
      { label: "湘南東部（藤沢・茅ヶ崎）", value: "shonan_east" },
      { label: "県央エリア（厚木・海老名）", value: "kenoh" },
      { label: "その他のエリア", value: "other" },
    ],
    // Medical district value → display name mapping
    areaLabels: {
      kensei: "県西",
      shonan_west: "湘南西部",
      shonan_east: "湘南東部",
      kenoh: "県央",
      other: "その他",
    },
    // Medical district value → city names for hospital matching
    areaCities: {
      kensei: ["小田原", "南足柄", "開成", "大井", "大磯", "二宮", "松田", "山北", "箱根", "真鶴", "湯河原"],
      shonan_west: ["平塚", "秦野", "伊勢原"],
      shonan_east: ["藤沢", "茅ヶ崎", "寒川"],
      kenoh: ["厚木", "海老名", "座間", "綾瀬", "大和", "愛川"],
    },
    // 最寄り駅候補（エリア別）— 通勤距離計算用
    stations: {
      kensei: [
        { label: "小田原駅", value: "小田原駅" },
        { label: "鴨宮駅", value: "鴨宮駅" },
        { label: "国府津駅", value: "国府津駅" },
        { label: "大雄山駅", value: "大雄山駅" },
        { label: "開成駅", value: "開成駅" },
        { label: "指定しない", value: "none" },
      ],
      shonan_west: [
        { label: "平塚駅", value: "平塚駅" },
        { label: "秦野駅", value: "秦野駅" },
        { label: "東海大学前駅", value: "東海大学前駅" },
        { label: "伊勢原駅", value: "伊勢原駅" },
        { label: "鶴巻温泉駅", value: "鶴巻温泉駅" },
        { label: "指定しない", value: "none" },
      ],
      shonan_east: [
        { label: "藤沢駅", value: "藤沢駅" },
        { label: "辻堂駅", value: "辻堂駅" },
        { label: "湘南台駅", value: "湘南台駅" },
        { label: "茅ヶ崎駅", value: "茅ヶ崎駅" },
        { label: "指定しない", value: "none" },
      ],
      kenoh: [
        { label: "本厚木駅", value: "本厚木駅" },
        { label: "海老名駅", value: "海老名駅" },
        { label: "さがみ野駅", value: "さがみ野駅" },
        { label: "愛甲石田駅", value: "愛甲石田駅" },
        { label: "指定しない", value: "none" },
      ],
    },
  };

  // --------------------------------------------------
  // GA4 Event Tracking Helper
  // --------------------------------------------------
  function trackEvent(eventName, params) {
    if (typeof gtag === "function") {
      try { gtag("event", eventName, params || {}); } catch (e) { /* ignore */ }
    }
  }

  // --------------------------------------------------
  // Demo mode responses (AI phase, after pre-scripted)
  // Used when API is not configured
  // --------------------------------------------------
  var DEMO_RESPONSES = [
    {
      reply: "お話しいただきありがとうございます。\n\n差し支えなければ、今回転職をお考えになったきっかけを教えていただけますか？",
      step: 3,
      score: null,
      done: false,
    },
    {
      reply: "なるほど、そうだったのですね。お気持ちよく分かります。\n\nちなみに、月収やお休みの日数など、特に重視されている条件はありますか？",
      step: 3,
      score: "C",
      done: false,
    },
    {
      reply: "ありがとうございます。いただいた条件をもとに、エリアの病院をいくつか候補として整理しています。\n\n夜勤の有無や通勤時間について、ご希望があればお聞かせください。",
      step: 4,
      score: "B",
      done: false,
    },
    {
      reply: "詳しくお聞かせいただきありがとうございました。\n\nお伺いした内容をもとに、条件に合う求人を担当エージェントがお探しします。24時間以内にお電話でご連絡いたしますので、少々お待ちくださいね。",
      step: 5,
      score: "A",
      done: true,
      summary: "転職希望の方。職種・エリア・希望条件をヒアリング済み。エージェントからの連絡を希望。",
    },
  ];

  // --------------------------------------------------
  // State
  // --------------------------------------------------
  function generateSessionId() {
    return "sess_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 9);
  }

  var CLIENT_RATE_LIMIT = {
    sendCooldownMs: 3000,
    maxSessionMessages: 6,
  };

  var chatState = {
    isOpen: false,
    consentGiven: false,
    phone: "",
    token: null,
    tokenTimestamp: null,
    formShownAt: null,
    currentStep: 1,
    messages: [],
    apiMessages: [],
    sessionId: generateSessionId(),
    demoIndex: 0,
    score: null,
    done: false,
    summary: null,
    isTyping: false,
    lastSendTime: 0,
    userMessageCount: 0,
    sendCooldown: false,
    ctaShown: false,
    demoMode: false, // true when API init fails (AI uses demo responses, but notifications still sent)
    summaryShown: false,
    lineNudgeShown: false,
    // Pre-scripted flow state
    profession: null,
    area: null,
    station: null,
    prescriptedPhase: "profession", // "profession" | "area" | "station" | "summary" | "done"
  };

  // --------------------------------------------------
  // DOM References (set after init)
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
      stepDots: document.querySelectorAll(".chat-step-dot"),
      stepLabel: document.getElementById("chatStepLabel"),
      consentView: document.getElementById("chatConsent"),
      consentBtn: document.getElementById("chatConsentBtn"),
      consentDecline: document.getElementById("chatConsentDecline"),
      phoneGate: document.getElementById("chatPhoneGate"),
      phoneInput: document.getElementById("chatPhoneInput"),
      phoneSubmit: document.getElementById("chatPhoneSubmit"),
      phoneError: document.getElementById("chatPhoneError"),
      honeypot: document.getElementById("chatHoneypot"),
      chatView: document.getElementById("chatView"),
      summaryView: document.getElementById("chatSummary"),
      summaryText: document.getElementById("chatSummaryText"),
      summaryScore: document.getElementById("chatSummaryScore"),
    };

    if (!els.toggle || !els.window) return;

    // Event listeners
    els.toggle.addEventListener("click", toggleChat);
    els.closeBtn.addEventListener("click", closeChat);
    els.minimizeBtn.addEventListener("click", closeChat);
    els.sendBtn.addEventListener("click", sendMessage);
    els.consentBtn.addEventListener("click", grantConsent);
    els.consentDecline.addEventListener("click", closeChat);

    // Phone gate listeners
    if (els.phoneSubmit) {
      els.phoneSubmit.addEventListener("click", handlePhoneSubmit);
    }
    if (els.phoneInput) {
      els.phoneInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          handlePhoneSubmit();
        }
      });
    }

    els.input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea + scroll chat to bottom on resize
    els.input.addEventListener("input", function () {
      els.input.style.height = "auto";
      els.input.style.height = Math.min(els.input.scrollHeight, 100) + "px";
      scrollToBottom();
    });

    // iOS virtual keyboard: adjust chat window height when keyboard appears
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
        // Keep the chat window pinned to the top of the visual viewport
        els.window.style.top = window.visualViewport.offsetTop + "px";
      });
    }

    // Focus trap and Escape key for chat window
    document.addEventListener("keydown", function (e) {
      if (!chatState.isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        closeChat();
        return;
      }

      if (e.key === "Tab") {
        var focusable = els.window.querySelectorAll(
          'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([tabindex="-1"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        var visible = [];
        for (var i = 0; i < focusable.length; i++) {
          if (focusable[i].offsetParent !== null) visible.push(focusable[i]);
        }
        if (visible.length === 0) return;
        var first = visible[0];
        var last = visible[visible.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    });
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

    if (!chatState.consentGiven) {
      showView("consent");
    } else if (!chatState.phone) {
      showView("phone");
    } else if (chatState.done) {
      showView("summary");
    } else {
      showView("chat");
      if (chatState.prescriptedPhase === "done") {
        els.input.focus();
      }
    }
  }

  function closeChat() {
    chatState.isOpen = false;
    els.window.classList.remove("open");
    unlockBodyScroll();
    // Reset visualViewport adjustments
    els.window.style.height = "";
    els.window.style.top = "";
    els.toggle.classList.remove("active");
    els.toggle.querySelector(".chat-toggle-icon").textContent = "\uD83D\uDCAC";
    els.toggle.focus();
  }

  function showView(view) {
    // Toggle each view using .hidden class only (no inline style.display)
    var views = [
      { key: "consent", el: els.consentView },
      { key: "phone", el: els.phoneGate },
      { key: "chat", el: els.chatView },
      { key: "summary", el: els.summaryView },
    ];
    for (var i = 0; i < views.length; i++) {
      if (!views[i].el) continue;
      // Clear any lingering inline display override so CSS classes take effect
      views[i].el.style.display = "";
      if (views[i].key === view) {
        views[i].el.classList.remove("hidden");
      } else {
        views[i].el.classList.add("hidden");
      }
    }

    if (view === "chat") {
      requestAnimationFrame(function () {
        scrollToBottom();
      });
    }
  }

  // --------------------------------------------------
  // Consent
  // --------------------------------------------------
  function grantConsent() {
    chatState.consentGiven = true;
    trackEvent("chat_consent");
    // Value-First: skip phone gate, go straight to pre-scripted flow
    showView("chat");
    chatState.formShownAt = Date.now();
    // Wait one frame for layout to settle after display:none → display:flex
    requestAnimationFrame(function () {
      startPrescriptedFlow();
    });
  }

  // --------------------------------------------------
  // Phone Gate
  // --------------------------------------------------
  function validatePhoneClient(phone) {
    var digits = phone.replace(/[\s\-\(\)\+]/g, "");
    return /^0\d{9,10}$/.test(digits);
  }

  function showPhoneError(msg) {
    if (els.phoneError) {
      els.phoneError.textContent = msg;
      els.phoneError.style.display = "block";
    }
  }

  function hidePhoneError() {
    if (els.phoneError) {
      els.phoneError.textContent = "";
      els.phoneError.style.display = "none";
    }
  }

  async function handlePhoneSubmit() {
    hidePhoneError();

    var phone = (els.phoneInput ? els.phoneInput.value : "").trim();
    var honeypotValue = els.honeypot ? els.honeypot.value : "";

    // Honeypot check (bot detection)
    if (honeypotValue) {
      showPhoneError("送信できませんでした。もう一度お試しください。");
      return;
    }

    // Client-side phone validation
    if (!phone) {
      showPhoneError("電話番号を入力してください。");
      return;
    }

    if (!validatePhoneClient(phone)) {
      showPhoneError("正しい電話番号を入力してください。（例: 090-1234-5678）");
      return;
    }

    // Timing check (too fast = bot)
    if (chatState.formShownAt && (Date.now() - chatState.formShownAt) < 2000) {
      showPhoneError("しばらくお待ちください。");
      return;
    }

    // Disable button during submission
    if (els.phoneSubmit) {
      els.phoneSubmit.disabled = true;
      els.phoneSubmit.textContent = "接続中...";
    }

    // Call /api/chat-init if API is available (graceful fallback to demo mode on failure)
    if (isAPIAvailable()) {
      try {
        var response = await fetch(CHAT_CONFIG.workerEndpoint + "/api/chat-init", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            phone: phone,
            honeypot: honeypotValue,
            formShownAt: chatState.formShownAt,
          }),
        });

        if (response.ok) {
          var data = await response.json();
          chatState.token = data.token || null;
          chatState.tokenTimestamp = data.timestamp || null;
          if (data.sessionId) {
            chatState.sessionId = data.sessionId;
          }
        } else {
          // API returned error - use demo mode for AI chat, but keep endpoint for notifications
          console.warn("[Chat] chat-init returned " + response.status + ", proceeding in demo mode");
          chatState.demoMode = true;
        }
      } catch (err) {
        // API unreachable - use demo mode for AI chat, but keep endpoint for notifications
        console.warn("[Chat] chat-init failed, proceeding in demo mode:", err.message);
        chatState.demoMode = true;
      }
    }

    // Store phone and proceed
    chatState.phone = phone;
    trackEvent("chat_phone_submitted");

    // If pre-scripted flow already completed (Value-First mode), go to AI phase
    if (chatState.prescriptedPhase === "summary" || chatState.area) {
      transitionToAIPhase();
    } else {
      // Fallback: start pre-scripted flow (shouldn't happen in Value-First mode)
      showView("chat");
      startPrescriptedFlow();
    }
  }

  // --------------------------------------------------
  // Pre-scripted Button Flow (Steps 1-2, no API cost)
  // --------------------------------------------------
  function startPrescriptedFlow() {
    chatState.prescriptedPhase = "profession";
    updateStep(1);

    // Hide the text input during pre-scripted phase
    setInputVisible(false);

    // Show greeting + profession question after a brief typing delay
    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", "こんにちは！ロビーです。転職のことで何かお役に立てればと思います。\n\nまず、今どんなお仕事をされていますか？");
      showButtonGroup(PRESCRIPTED.professions, handleProfessionSelect);
    }, 800);
  }

  function handleProfessionSelect(value, label) {
    chatState.profession = value;
    trackEvent("chat_profession_selected", { profession: value });

    // Remove the buttons
    removeButtonGroup();

    // Show user selection as a user message
    addMessage("user", label);

    // Move to area question
    chatState.prescriptedPhase = "area";
    updateStep(2);

    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", "ありがとうございます！通勤圏はどのあたりですか？\n（今お住まいの近くでも、少し離れたエリアでもOKです）");
      showButtonGroup(PRESCRIPTED.areas, handleAreaSelect);
    }, 600);
  }

  function handleAreaSelect(value, label) {
    chatState.area = value;
    trackEvent("chat_area_selected", { area: value });

    // Remove the buttons
    removeButtonGroup();

    // Show user selection as a user message
    addMessage("user", label);

    // 最寄り駅選択ステップ（通勤距離計算のため）
    var stationOptions = PRESCRIPTED.stations && PRESCRIPTED.stations[value];
    if (stationOptions && stationOptions.length > 0) {
      chatState.prescriptedPhase = "station";
      showTyping();
      setTimeout(function () {
        hideTyping();
        addMessage("ai", "通勤しやすい施設をご紹介するために、最寄り駅を教えてください。\n（通勤距離の目安を計算できます）");
        showButtonGroup(stationOptions, handleStationSelect);
      }, 600);
    } else {
      // 駅データがないエリア（other等）→ 直接病院サマリへ
      proceedToHospitalSummary();
    }
  }

  function handleStationSelect(value, label) {
    chatState.station = value === "none" ? null : value;
    trackEvent("chat_station_selected", { station: value });

    // Remove the buttons
    removeButtonGroup();

    // Show user selection as a user message
    if (value !== "none") {
      addMessage("user", label);
    } else {
      addMessage("user", "指定しない");
    }

    proceedToHospitalSummary();
  }

  function proceedToHospitalSummary() {
    // Show matching hospital summary
    chatState.prescriptedPhase = "summary";

    showTyping();
    setTimeout(function () {
      hideTyping();
      showHospitalSummary();

      // Step 2: Summary card reflecting user's selections (sunk-cost activation)
      setTimeout(function () {
        showConditionCard();

        // Step 3: Bridge message → Unified LINE CTA
        setTimeout(function () {
          showBridgeMessageAndCTA();
        }, 1500);
      }, 2000);
    }, 800);
  }

  // --------------------------------------------------
  // Condition Summary Card (reflects user's selections)
  // --------------------------------------------------
  function showConditionCard() {
    var areaLabel = getAreaDisplayName(chatState.area) || "未選択";
    var stationLabel = chatState.station || "指定なし";
    var matchCount = findMatchingHospitals(chatState.area).length;

    var card = document.createElement("div");
    card.className = "chat-condition-card";
    card.innerHTML =
      '<div class="chat-condition-card-header">あなたの転職条件</div>' +
      '<div class="chat-condition-card-body">' +
        '<div class="chat-condition-row"><span class="chat-condition-label">職種</span><span class="chat-condition-value">' + (chatState.profession || "看護師") + '</span></div>' +
        '<div class="chat-condition-row"><span class="chat-condition-label">エリア</span><span class="chat-condition-value">' + areaLabel + '</span></div>' +
        '<div class="chat-condition-row"><span class="chat-condition-label">最寄り駅</span><span class="chat-condition-value">' + stationLabel + '</span></div>' +
        '<div class="chat-condition-row highlight"><span class="chat-condition-label">マッチ求人</span><span class="chat-condition-value">' + matchCount + '件以上</span></div>' +
      '</div>';

    els.body.appendChild(card);
    scrollToBottom();
  }

  // --------------------------------------------------
  // Bridge Message + Unified LINE CTA
  // --------------------------------------------------
  function showBridgeMessageAndCTA() {
    var areaLabel = getAreaDisplayName(chatState.area) || "神奈川県西部";
    var matchCount = findMatchingHospitals(chatState.area).length;

    // Bridge message — natural transition to CTA
    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", areaLabel + "エリアで" + (chatState.profession || "看護師") + "の求人が" + matchCount + "件以上見つかりました。\n\nあなたの経験年数や細かい希望条件に合わせてさらに絞り込めます。LINEで続きをお話ししませんか？");

      // Show unified LINE CTA card after bridge message
      setTimeout(function () {
        showUnifiedLineCTA();
      }, 800);
    }, 600);
  }

  function showUnifiedLineCTA() {
    var ctaCard = document.createElement("div");
    ctaCard.className = "chat-line-cta-card";
    ctaCard.id = "chatLineCTACard";

    ctaCard.innerHTML =
      // Progress steps (Zeigarnik effect)
      '<div class="cta-progress">' +
        '<span class="cta-step done">条件ヒアリング</span>' +
        '<span class="cta-arrow">&#x25B6;</span>' +
        '<span class="cta-step current">LINE登録</span>' +
        '<span class="cta-arrow">&#x25B6;</span>' +
        '<span class="cta-step future">求人ご提案</span>' +
      '</div>' +
      '<p class="cta-heading">あと1ステップで求人をお届けできます</p>' +
      // Primary CTA button
      '<a href="https://lin.ee/HJwmQgp4" target="_blank" rel="noopener" class="chat-line-cta-btn" id="chatUnifiedLineBtn">' +
        '<span>LINEで求人を受け取る<span class="btn-sub">30秒で完了 / 完全無料</span></span>' +
      '</a>' +
      // Trust signals (anxiety reducers)
      '<div class="trust-row">' +
        '<span class="trust-item"><span class="trust-check">&#x2713;</span> 電話なし</span>' +
        '<span class="trust-item"><span class="trust-check">&#x2713;</span> 費用ゼロ</span>' +
        '<span class="trust-item"><span class="trust-check">&#x2713;</span> 手数料10%</span>' +
      '</div>' +
      // Soft dismiss
      '<button class="cta-dismiss" id="chatLineCTADismiss">もう少し自分で調べたい</button>';

    els.body.appendChild(ctaCard);
    scrollToBottom();

    // CTA button tracking
    var lineBtn = document.getElementById("chatUnifiedLineBtn");
    if (lineBtn) {
      lineBtn.addEventListener("click", function () {
        trackEvent("chat_line_cta_unified", { phase: "prescripted_summary", area: chatState.area });
      });
    }

    // Dismiss → show continuation buttons as fallback
    var dismissBtn = document.getElementById("chatLineCTADismiss");
    if (dismissBtn) {
      dismissBtn.addEventListener("click", function () {
        trackEvent("chat_line_cta_dismissed", { phase: "prescripted_summary" });
        ctaCard.style.display = "none";
        // Show continuation buttons (detail/line/stop)
        showContinuationButtons();
      });
    }
  }

  function showContinuationButtons() {
    var options = [
      { label: "もっと詳しく相談したい", value: "detail" },
      { label: "LINEで直接相談する", value: "line" },
      { label: "今はここまでで大丈夫", value: "stop" },
    ];

    var container = document.createElement("div");
    container.className = "chat-quick-replies";
    container.id = "chatContinuationGroup";

    for (var i = 0; i < options.length; i++) {
      (function (opt) {
        var btn = document.createElement("button");
        btn.className = "chat-quick-reply";
        btn.textContent = opt.label;
        btn.addEventListener("click", function () {
          // Remove buttons
          var group = document.getElementById("chatContinuationGroup");
          if (group) group.remove();

          addMessage("user", opt.label);

          if (opt.value === "detail") {
            // Show phone gate with context
            showTyping();
            setTimeout(function () {
              hideTyping();
              addMessage("ai", "ありがとうございます！\n\nより詳しい条件の確認や、非公開求人のご紹介のために、お電話番号を教えていただけますか？\n（専門エージェントから24時間以内にご連絡します）");
              setTimeout(function () {
                chatState.formShownAt = Date.now();
                showPhoneGateAfterValue();
              }, 1500);
            }, 600);
          } else if (opt.value === "line") {
            trackEvent("chat_line_direct", { phase: "pre_phone" });
            window.open("https://lin.ee/HJwmQgp4", "_blank");
            showTyping();
            setTimeout(function () {
              hideTyping();
              addMessage("ai", "LINEでのご相談、お待ちしています！\n友だち追加後にメッセージをお送りくださいね。");
            }, 600);
          } else {
            showTyping();
            setTimeout(function () {
              hideTyping();
              addMessage("ai", "もちろんです！気になることがあればいつでもまたお声がけくださいね。\n\n求人情報が気になったら、いつでもLINEでご相談いただけます。");
              // Show unified LINE CTA card
              setTimeout(function () {
                showUnifiedLineCTA();
              }, 500);
            }, 600);
          }
        });
        container.appendChild(btn);
      })(options[i]);
    }

    els.body.appendChild(container);
    scrollToBottom();
  }

  // --------------------------------------------------
  // Phone Gate After Value (Value-First approach)
  // --------------------------------------------------
  function showPhoneGateAfterValue() {
    // Update the phone gate UI text for post-value context
    var phoneTitle = document.querySelector(".chat-phone-title");
    var phoneDesc = document.querySelector(".chat-phone-desc");
    if (phoneTitle) phoneTitle.innerHTML = "&#x1F4AC; もう少し詳しくお話ししませんか？";
    if (phoneDesc) phoneDesc.innerHTML = "マッチする求人の詳細をお届けするため、<br>お電話番号をご入力ください";

    showView("phone");
    if (els.phoneInput) els.phoneInput.focus();
  }

  function transitionToAIPhase() {
    // Transition to AI phase
    chatState.prescriptedPhase = "done";
    updateStep(3);

    showView("chat");

    // Show the text input for AI conversation
    setInputVisible(true);

    // Explicit scroll after view switch + input area shown
    scrollToBottom();

    // Delay focus to let layout settle (prevents iOS keyboard race condition)
    setTimeout(function () {
      els.input.focus();
    }, 300);

    // Inject context into API messages so AI knows the user's selections
    var areaDisplay = getAreaDisplayName(chatState.area);
    var stationInfo = chatState.station ? " / 最寄り駅: " + chatState.station : "";
    var contextMsg = "【事前ヒアリング結果】職種: " + (chatState.profession || "未選択") +
      " / 希望エリア: " + (areaDisplay || "未選択") + stationInfo +
      "。これらの情報を踏まえて、転職の詳しい希望条件をヒアリングしてください。";
    chatState.apiMessages.push({ role: "user", content: contextMsg });

    // Get AI's first contextual response (API or demo mode)
    if (isAPIAvailable() && !chatState.demoMode) {
      showTyping();
      callAPI(chatState.apiMessages).then(function (response) {
        hideTyping();
        if (response && isValidReply(response.reply)) {
          addMessage("ai", response.reply);
          chatState.apiMessages.push({ role: "assistant", content: response.reply });
        } else {
          addMessage("ai", "ありがとうございます！もう少し詳しくお伺いしたいのですが、今のお仕事で特に気になっていることはありますか？");
        }
      });
    } else {
      // Demo mode: show first AI message
      showTyping();
      setTimeout(function () {
        hideTyping();
        var response = DEMO_RESPONSES[chatState.demoIndex] || DEMO_RESPONSES[0];
        chatState.demoIndex = Math.min(chatState.demoIndex + 1, DEMO_RESPONSES.length - 1);
        addMessage("ai", response.reply);
        chatState.apiMessages.push({ role: "assistant", content: response.reply });
      }, 800);
    }
  }

  function getAreaDisplayName(areaValue) {
    return (PRESCRIPTED.areaLabels && PRESCRIPTED.areaLabels[areaValue]) || areaValue || "";
  }

  function showHospitalSummary() {
    // Find matching hospitals based on area selection
    var matches = findMatchingHospitals(chatState.area);
    var areaName = getAreaDisplayName(chatState.area);

    if (matches.length === 0) {
      addMessage("ai", areaName + "エリアですね！\n\n" + chatState.profession + "の求人、いくつかご紹介できると思います。今の職場で気になっていることや、転職で大事にしたいことはありますか？");
      return;
    }

    // Build summary text with warmth
    var text = areaName + "エリアですね！" + chatState.profession + "の求人、" + matches.length + "件以上ご紹介できます。\n\n";

    // Show top 2-3 briefly
    var showCount = Math.min(matches.length, 3);
    for (var i = 0; i < showCount; i++) {
      var h = matches[i];
      text += h.displayName + "\n";
      text += "  " + h.salary + " / " + h.holidays + "\n";
      if (i < showCount - 1) text += "\n";
    }

    if (matches.length > showCount) {
      text += "\n他にも " + (matches.length - showCount) + " 件以上あります。";
    }

    text += "\n\nあなたに合う求人を絞り込みたいので、今の職場で気になっていることを教えてください。（夜勤のこと、人間関係、給与、通勤…何でもOKです）";

    addMessage("ai", text);
  }

  function findMatchingHospitals(area) {
    var hospitals = CHAT_CONFIG.hospitals;
    if (!hospitals || hospitals.length === 0) {
      // Fallback data when CONFIG.HOSPITALS is empty
      return [
        { displayName: "小田原市立病院（小田原市・417床）", salary: "月給28〜38万円（目安）", holidays: "年間休日120日以上", nightShift: "あり（三交代制）", commute: "小田原駅バス10分" },
        { displayName: "東海大学医学部付属病院（伊勢原市・804床）", salary: "月給29〜38万円（目安）", holidays: "年間休日120日以上", nightShift: "あり（三交代制）", commute: "伊勢原駅バス10分" },
        { displayName: "海老名総合病院（海老名市・479床）", salary: "月給29〜38万円（目安）", holidays: "年間休日115日以上", nightShift: "あり（二交代制）", commute: "海老名駅徒歩7分" },
      ];
    }

    if (!area || area === "other") {
      return hospitals;
    }

    // Get city names for this medical district
    var cities = PRESCRIPTED.areaCities && PRESCRIPTED.areaCities[area];
    if (!cities || cities.length === 0) {
      return hospitals;
    }

    // Filter hospitals by matching any city name in displayName
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

    // If no match, return all (better than showing nothing)
    return filtered.length > 0 ? filtered : hospitals;
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
        btn.textContent = opt.label;
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
      // Flex layout changed (~60px), scroll to compensate
      scrollToBottom();
    }
  }

  // --------------------------------------------------
  // Messages
  // --------------------------------------------------
  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function addMessage(role, content) {
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
  }

  function sendMessage() {
    // Block typed messages during pre-scripted phase
    if (chatState.prescriptedPhase !== "done") return;

    var text = els.input.value.trim();
    if (!text || chatState.isTyping || chatState.done || chatState.sendCooldown) return;

    // Session message limit check
    if (chatState.userMessageCount >= CLIENT_RATE_LIMIT.maxSessionMessages) {
      addMessage("ai", "たくさんお話しいただきありがとうございます。いただいた条件をもとに、ぴったりの求人をLINEでお届けしますね。");
      els.input.disabled = true;
      els.sendBtn.disabled = true;
      showUnifiedLineCTA();
      return;
    }

    chatState.userMessageCount++;
    trackEvent("chat_message_sent", { message_count: chatState.userMessageCount });
    addMessage("user", text);
    els.input.value = "";
    els.input.style.height = "auto";

    // Show remaining message count
    updateRemainingCount();

    // Add to API message history
    chatState.apiMessages.push({ role: "user", content: text });

    // Update step based on AI-phase message count (steps 3-5)
    updateStep(getStepFromMessageCount(chatState.userMessageCount));

    // Start send cooldown
    startSendCooldown();

    processResponse(text);
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
  // Step Progression (AI phase, steps 3-5)
  // Steps 1-2 are handled by pre-scripted flow
  // --------------------------------------------------
  function getStepFromMessageCount(count) {
    if (count <= 2) return 3;  // 条件ヒアリング
    if (count <= 4) return 4;  // 求人検索中
    return 5;                   // ご案内準備完了
  }

  // --------------------------------------------------
  // Response Processing (AI phase)
  // --------------------------------------------------
  function processResponse(userText) {
    showTyping();

    if (isAPIAvailable() && !chatState.demoMode) {
      callAPI(chatState.apiMessages).then(function (response) {
        hideTyping();
        if (response && response.isError) {
          // Error response: show message but don't advance conversation state
          addMessage("ai", response.reply);
          // Undo the user message count increment so errors don't consume turns
          if (chatState.userMessageCount > 0) chatState.userMessageCount--;
          chatState.apiMessages.pop(); // remove the user message from API history
        } else if (response && isValidReply(response.reply)) {
          handleAIResponse(response);
        } else if (response && response.reply) {
          addMessage("ai", "申し訳ございません。もう一度お話しいただけますか？");
        } else {
          addMessage("ai", getFallbackMessage());
        }
        maybeShowInlineCTA();
        maybeShowLineNudge();
      });
    } else {
      // Demo mode
      var delay = 1000 + Math.random() * 1500;
      setTimeout(function () {
        hideTyping();
        var response = DEMO_RESPONSES[chatState.demoIndex] || DEMO_RESPONSES[DEMO_RESPONSES.length - 1];
        chatState.demoIndex = Math.min(chatState.demoIndex + 1, DEMO_RESPONSES.length - 1);
        handleAIResponse(response);
        maybeShowInlineCTA();
        maybeShowLineNudge();
      }, delay);
    }
  }

  function handleAIResponse(response) {
    addMessage("ai", response.reply);

    // Track in API messages
    chatState.apiMessages.push({ role: "assistant", content: response.reply });

    // Update step from response (override if server says so)
    if (response.step) {
      updateStep(response.step);
    }

    // Update score
    if (response.score) {
      chatState.score = response.score;
    }

    // Check if conversation is done (from API or max messages reached)
    if (response.done || chatState.userMessageCount >= CLIENT_RATE_LIMIT.maxSessionMessages) {
      chatState.done = true;
      chatState.summary = response.summary || "";
      onConversationComplete();
    }
  }

  // --------------------------------------------------
  // Inline CTA (after 4+ user messages)
  // --------------------------------------------------
  function maybeShowInlineCTA() {
    if (chatState.userMessageCount >= 4 && !chatState.ctaShown && !chatState.done) {
      chatState.ctaShown = true;
      var cta = document.createElement("button");
      cta.className = "chat-inline-cta";
      cta.textContent = "\uD83D\uDCDD 無料登録で詳しい条件をご案内 \u2192";
      cta.onclick = function () {
        var registerSection = document.getElementById("registerSection") || document.getElementById("register");
        if (registerSection) {
          registerSection.scrollIntoView({ behavior: "smooth" });
        }
        closeChat();
      };
      els.body.appendChild(cta);
      scrollToBottom();
    }
  }

  // --------------------------------------------------
  // Remaining Message Count Display
  // --------------------------------------------------
  function updateRemainingCount() {
    var remaining = CLIENT_RATE_LIMIT.maxSessionMessages - chatState.userMessageCount;
    var existingEl = document.getElementById("chatRemainingCount");

    if (remaining <= 3 && remaining > 0) {
      if (!existingEl) {
        existingEl = document.createElement("div");
        existingEl.id = "chatRemainingCount";
        existingEl.className = "chat-remaining-count";
        var inputArea = els.input ? els.input.parentElement : null;
        if (inputArea && inputArea.parentElement) {
          inputArea.parentElement.insertBefore(existingEl, inputArea);
        }
      }
      existingEl.textContent = "あと" + remaining + "回お話しできます";
      if (remaining <= 2) existingEl.classList.add("low");
    }
  }

  // --------------------------------------------------
  // LINE Nudge (after 4 messages, gentle transition)
  // --------------------------------------------------
  function maybeShowLineNudge() {
    if (chatState.userMessageCount === 4 && !chatState.lineNudgeShown) {
      chatState.lineNudgeShown = true;
      // Show a gentle LINE nudge button (not the full CTA card)
      var nudge = document.createElement("a");
      nudge.className = "chat-inline-cta";
      nudge.style.background = "#06C755";
      nudge.style.textDecoration = "none";
      nudge.style.color = "#FFFFFF";
      nudge.href = "https://lin.ee/HJwmQgp4";
      nudge.target = "_blank";
      nudge.rel = "noopener";
      nudge.textContent = "LINEで続きを相談する";
      nudge.onclick = function () {
        trackEvent("chat_line_nudge_click", { message_count: chatState.userMessageCount });
      };
      els.body.appendChild(nudge);
      scrollToBottom();
    }
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
  // Step Indicator
  // --------------------------------------------------
  function updateStep(step) {
    chatState.currentStep = step;

    els.stepDots.forEach(function (dot, i) {
      dot.classList.remove("active", "completed");
      if (i + 1 < step) {
        dot.classList.add("completed");
      } else if (i + 1 === step) {
        dot.classList.add("active");
      }
    });

    if (els.stepLabel) {
      els.stepLabel.textContent = step + "/5 " + (CHAT_CONFIG.stepLabels[step - 1] || "");
    }
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
  // Temperature Score Auto-Detection
  // --------------------------------------------------
  function detectTemperatureScore() {
    // If server already set a score, use it
    if (chatState.score) return chatState.score;

    var score = 0;
    var userMessages = [];
    for (var i = 0; i < chatState.messages.length; i++) {
      if (chatState.messages[i].role === "user") {
        userMessages.push(chatState.messages[i].content);
      }
    }
    var allText = userMessages.join(" ");

    // Urgency keywords (A-level signals)
    var urgentKeywords = ["すぐ", "急ぎ", "今月", "来月", "退職済", "辞めた", "決まっている", "早く", "なるべく早"];
    for (var u = 0; u < urgentKeywords.length; u++) {
      if (allText.indexOf(urgentKeywords[u]) !== -1) { score += 3; break; }
    }

    // Active interest keywords (B-level signals)
    var activeKeywords = ["面接", "見学", "応募", "給与", "年収", "月給", "具体的", "いつから", "条件"];
    for (var a = 0; a < activeKeywords.length; a++) {
      if (allText.indexOf(activeKeywords[a]) !== -1) { score += 1; }
    }

    // Engagement: message count
    if (chatState.userMessageCount >= 5) { score += 2; }
    else if (chatState.userMessageCount >= 3) { score += 1; }

    // Message length engagement
    var totalLen = 0;
    for (var l = 0; l < userMessages.length; l++) { totalLen += userMessages[l].length; }
    if (totalLen > 200) { score += 1; }

    if (score >= 5) return "A";
    if (score >= 3) return "B";
    if (score >= 1) return "C";
    return "D";
  }

  // --------------------------------------------------
  // Build Structured Conversation Summary
  // --------------------------------------------------
  function buildConversationSummary() {
    var score = detectTemperatureScore();
    chatState.score = score;

    return {
      sessionId: chatState.sessionId,
      phone: chatState.phone,
      profession: chatState.profession || null,
      area: chatState.area || null,
      score: score,
      messageCount: chatState.userMessageCount,
      messages: chatState.messages,
      summary: chatState.summary || null,
      completedAt: new Date().toISOString(),
    };
  }

  // --------------------------------------------------
  // Conversation Complete
  // --------------------------------------------------
  function onConversationComplete() {
    // Disable input
    els.input.disabled = true;
    els.sendBtn.disabled = true;
    els.input.placeholder = "会話が完了しました";

    // Build structured summary and send to backend
    var summaryData = buildConversationSummary();
    trackEvent("chat_completed", { score: summaryData.score, message_count: summaryData.messageCount, area: chatState.area || "none", profession: chatState.profession || "none" });

    // Warm encouragement messages based on engagement level
    var scoreMessages = {
      A: {
        text: "お話を聞かせていただきありがとうございました！あなたにぴったりの職場をお探しします。",
        sub: "24時間以内に専門エージェントの平島からLINEでご連絡します。",
        urgency: "この求人は人気のため、早めのご相談をおすすめします",
      },
      B: {
        text: "詳しくお聞かせいただきありがとうございました！あなたの経験が活きる職場をお探しします。",
        sub: "24時間以内に専門エージェントからLINEでご連絡します。",
        urgency: null,
      },
      C: {
        text: "ご相談ありがとうございました！まずは情報収集からでも大丈夫ですよ。",
        sub: "気になる求人があればいつでもLINEでご相談ください。",
        urgency: null,
      },
      D: {
        text: "お話しいただきありがとうございました。転職は大きな決断ですよね。",
        sub: "気になることがあれば、いつでもLINEでお声がけくださいね。",
        urgency: null,
      },
    };

    var msg = scoreMessages[summaryData.score] || scoreMessages["C"];

    // Send to backend and get matched facilities
    sendChatComplete(summaryData).then(function (responseData) {
      var facilities = (responseData && responseData.matchedFacilities) || [];

      setTimeout(function () {
        if (els.summaryText) {
          els.summaryText.textContent = msg.text;
        }
        if (els.summaryScore) {
          els.summaryScore.textContent = msg.sub;
        }

        // Render recommendation cards
        renderRecommendations(facilities);

        // Show urgency badge for high-intent users
        if (msg.urgency) {
          var urgencyEl = document.getElementById("chatUrgencyBadge");
          if (!urgencyEl) {
            urgencyEl = document.createElement("div");
            urgencyEl.id = "chatUrgencyBadge";
            urgencyEl.className = "chat-urgency-badge";
            var ctaContainer = document.querySelector(".chat-summary-cta");
            if (ctaContainer) ctaContainer.parentElement.insertBefore(urgencyEl, ctaContainer);
          }
          urgencyEl.textContent = msg.urgency;
        }

        // Show social proof
        var socialEl = document.getElementById("chatSocialProof");
        if (!socialEl) {
          socialEl = document.createElement("div");
          socialEl.id = "chatSocialProof";
          socialEl.className = "chat-social-proof";
          var recsContainer = document.getElementById("chatRecommendations");
          if (recsContainer && recsContainer.parentElement) {
            recsContainer.parentElement.insertBefore(socialEl, recsContainer.nextSibling);
          }
        }
        var areaLabel = getAreaDisplayName(chatState.area) || "神奈川県西部";
        socialEl.textContent = areaLabel + "エリアの看護師さんにご利用いただいています";

        // Setup CTA button events
        setupSummaryCTA();

        showView("summary");
      }, 1500);
    });

    // Fallback: if API takes too long, show summary without recommendations after 5s
    setTimeout(function () {
      if (!chatState.summaryShown) {
        chatState.summaryShown = true;
        if (els.summaryText) {
          els.summaryText.textContent = msg.text;
        }
        if (els.summaryScore) {
          els.summaryScore.textContent = msg.sub;
        }
        setupSummaryCTA();
        showView("summary");
      }
    }, 5000);
  }

  // --------------------------------------------------
  // Render Recommendation Cards
  // --------------------------------------------------
  function renderRecommendations(facilities) {
    chatState.summaryShown = true;
    var container = document.getElementById("chatRecommendations");
    if (!container || !facilities || facilities.length === 0) return;

    container.innerHTML = "";

    var title = document.createElement("p");
    title.className = "chat-recommendations-title";
    title.textContent = "あなたにぴったりの求人";
    container.appendChild(title);

    for (var i = 0; i < facilities.length; i++) {
      var f = facilities[i];
      var card = document.createElement("div");
      card.className = "chat-recommendation-card";

      // Header: name + match score
      var header = document.createElement("div");
      header.className = "chat-rec-header";

      var nameEl = document.createElement("span");
      nameEl.className = "chat-rec-name";
      nameEl.textContent = f.name;
      header.appendChild(nameEl);

      var scoreEl = document.createElement("span");
      scoreEl.className = "chat-match-score";
      scoreEl.textContent = f.matchScore + "%";
      header.appendChild(scoreEl);

      card.appendChild(header);

      // Type
      var typeEl = document.createElement("div");
      typeEl.className = "chat-rec-type";
      typeEl.textContent = f.type + (f.beds ? " / " + f.beds + "床" : "");
      card.appendChild(typeEl);

      // Tag badges (highlight key features)
      var tagFeatures = [];
      if (f.nightShift === "なし" || f.nightShift === "オンコール") tagFeatures.push("日勤OK");
      if (f.annualHolidays >= 120) tagFeatures.push("休" + f.annualHolidays + "日");
      if (f.access && f.access.indexOf("徒歩") !== -1) tagFeatures.push("駅近");
      if (tagFeatures.length > 0) {
        var tagsDiv = document.createElement("div");
        tagsDiv.className = "chat-rec-tags";
        for (var t = 0; t < tagFeatures.length; t++) {
          var badge = document.createElement("span");
          badge.className = "chat-tag-badge";
          badge.textContent = tagFeatures[t];
          tagsDiv.appendChild(badge);
        }
        card.appendChild(tagsDiv);
      }

      // Reasons
      if (f.reasons && f.reasons.length > 0) {
        var reasonsList = document.createElement("ul");
        reasonsList.className = "chat-rec-reasons";
        for (var r = 0; r < f.reasons.length; r++) {
          var li = document.createElement("li");
          li.textContent = f.reasons[r];
          reasonsList.appendChild(li);
        }
        card.appendChild(reasonsList);
      }

      // Details
      var details = document.createElement("div");
      details.className = "chat-rec-details";
      var detailParts = [f.salary];
      if (f.annualHolidays) detailParts.push("休" + f.annualHolidays + "日");
      if (f.nightShift) detailParts.push(f.nightShift);
      if (f.access) detailParts.push(f.access);
      details.textContent = detailParts.join(" / ");
      card.appendChild(details);

      container.appendChild(card);
    }
  }

  // --------------------------------------------------
  // Setup Summary CTA Buttons
  // --------------------------------------------------
  function setupSummaryCTA() {
    var lineBtn = document.getElementById("chatCtaLine");
    if (lineBtn) {
      lineBtn.addEventListener("click", function () {
        trackEvent("chat_line_click", { score: chatState.score || "unknown" });
      });
    }
    var registerBtn = document.getElementById("chatCtaRegister");
    if (registerBtn) {
      registerBtn.onclick = function () {
        trackEvent("chat_register_click", { score: chatState.score || "unknown" });
        var registerSection = document.getElementById("registerSection") || document.getElementById("register");
        if (registerSection) {
          registerSection.scrollIntoView({ behavior: "smooth" });
        }
        closeChat();
      };
    }
  }

  // --------------------------------------------------
  // API Integration
  // --------------------------------------------------
  function isAPIAvailable() {
    return CHAT_CONFIG.workerEndpoint && CHAT_CONFIG.workerEndpoint.length > 0;
  }

  // Fetch with timeout wrapper
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

  // Error fallback messages
  var FALLBACK_MESSAGES = [
    "申し訳ございません。一時的に接続が不安定です。少し時間をおいて再度お試しください。",
    "通信環境をご確認のうえ、再度メッセージを送信してください。",
    "ただいま混み合っております。しばらくお待ちいただいてから再度お試しください。",
  ];

  function getFallbackMessage() {
    var idx = Math.floor(Math.random() * FALLBACK_MESSAGES.length);
    return FALLBACK_MESSAGES[idx];
  }

  async function callAPI(messages) {
    try {
      var response = await fetchWithTimeout(CHAT_CONFIG.workerEndpoint + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: messages,
          sessionId: chatState.sessionId,
          phone: chatState.phone,
          token: chatState.token,
          timestamp: chatState.tokenTimestamp,
          profession: chatState.profession,
          area: chatState.area,
          station: chatState.station || null,
        }),
      }, 20000);

      if (response.status === 429) {
        var errData = {};
        try { errData = await response.json(); } catch (e) { /* ignore */ }
        return {
          reply: errData.error || "リクエストが多すぎます。少しお待ちください。",
          step: chatState.currentStep,
          score: null,
          done: false,
        };
      }

      if (!response.ok) {
        throw new Error("API response " + response.status);
      }

      var data = await response.json();

      // Parse the response - the worker should return the AI's JSON
      if (typeof data.reply === "string") {
        return data;
      }

      // If the API returns raw text, try parsing it
      if (data.content) {
        try {
          return JSON.parse(data.content);
        } catch (e) {
          return { reply: data.content, step: chatState.currentStep, score: null, done: false };
        }
      }

      return null;
    } catch (err) {
      console.error("[Chat API Error]", err);
      // Return a user-friendly fallback instead of null
      if (err.message === "Request timeout") {
        return {
          reply: "応答に時間がかかっております。もう一度お試しいただけますか？",
          step: chatState.currentStep,
          score: null,
          done: false,
          isError: true,
        };
      }
      return {
        reply: getFallbackMessage(),
        step: chatState.currentStep,
        score: null,
        done: false,
        isError: true,
      };
    }
  }

  async function sendChatComplete(summaryData) {
    if (!CHAT_CONFIG.workerEndpoint || chatState.messages.length < 2) return null;
    try {
      var response = await fetchWithTimeout(CHAT_CONFIG.workerEndpoint + "/api/chat-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: chatState.phone,
          sessionId: chatState.sessionId,
          token: chatState.token,
          timestamp: chatState.tokenTimestamp,
          messages: chatState.messages,
          profession: chatState.profession,
          area: chatState.area,
          station: chatState.station || null,
          score: summaryData ? summaryData.score : null,
          messageCount: summaryData ? summaryData.messageCount : chatState.userMessageCount,
          completedAt: summaryData ? summaryData.completedAt : new Date().toISOString(),
        }),
      }, 15000);
      if (response.ok) {
        var data = await response.json();
        return data;
      }
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
    // Cancel previous pending timers to avoid stacking
    if (scrollToBottom._t1) clearTimeout(scrollToBottom._t1);
    if (scrollToBottom._t2) clearTimeout(scrollToBottom._t2);
    if (scrollToBottom._t3) clearTimeout(scrollToBottom._t3);

    function doScroll() {
      if (!els.body) return;
      // Skip if chat-body is not visible (parent is display:none)
      if (els.body.offsetParent === null) return;
      els.body.style.scrollBehavior = "auto";
      els.body.scrollTop = els.body.scrollHeight;
      els.body.style.scrollBehavior = "auto";
    }
    // Primary: double-rAF for immediate DOM renders
    requestAnimationFrame(function () {
      requestAnimationFrame(doScroll);
    });
    // Fallback 1: catch slow renders (images, CTA buttons)
    scrollToBottom._t1 = setTimeout(doScroll, 80);
    // Fallback 2: catch flex recalc
    scrollToBottom._t2 = setTimeout(doScroll, 250);
    // Fallback 3: catch CSS animation completion (400ms animations)
    scrollToBottom._t3 = setTimeout(doScroll, 450);
  }

  // --------------------------------------------------
  // Initialize on DOM ready
  // --------------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
