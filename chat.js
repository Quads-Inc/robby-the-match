// ========================================
// ナースロビー - AI Chat Widget v2.0
// World-class conversion design
// No consent gate, no phone gate, value-first
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
  // Pre-scripted flow data
  // --------------------------------------------------
  var PRESCRIPTED = {
    intents: [
      { label: "求人を探したい", value: "search", emoji: "" },
      { label: "転職の相談がしたい", value: "consult", emoji: "" },
      { label: "まずは情報収集だけ", value: "browse", emoji: "" },
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
    phase: "greeting", // "greeting" | "intent" | "area" | "priority" | "value" | "ai" | "done"
    intent: null,
    area: null,
    priority: null,
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
        priority: chatState.priority,
        userMessageCount: chatState.userMessageCount,
        score: chatState.score,
        done: chatState.done,
        lineCtaShown: chatState.lineCtaShown,
        demoIndex: chatState.demoIndex,
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
      chatState.priority = data.priority || null;
      chatState.userMessageCount = data.userMessageCount || 0;
      chatState.score = data.score || null;
      chatState.done = data.done || false;
      chatState.lineCtaShown = data.lineCtaShown || false;
      chatState.demoIndex = data.demoIndex || 0;
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
      '<div class="chat-peek-text">転職のこと、気軽に相談できますよ</div>' +
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
      // Restore chat view from saved state
      restoreChatView();
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
    setInputVisible(false);

    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", "こんにちは！ナースロビーのロビーです。\n\n神奈川県西部で看護師さんの転職をお手伝いしています。手数料は業界最安の10%なので、病院にも看護師さんにも喜ばれています。");

      setTimeout(function () {
        showTyping();
        setTimeout(function () {
          hideTyping();
          addMessage("ai", "今日はどんなことが気になりますか？");
          chatState.phase = "intent";
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

    var empathyMap = {
      search: "求人をお探しなんですね！\n\n通勤のしやすさは大事ですよね。どのあたりのエリアをお考えですか？",
      consult: "転職のご相談ですね。一緒に考えましょう。\n\nまず、どのあたりのエリアでお仕事を探されていますか？",
      browse: "もちろんです！情報収集は大事な第一歩ですね。\n\nどのエリアの情報が気になりますか？",
    };

    showTyping();
    setTimeout(function () {
      hideTyping();
      addMessage("ai", empathyMap[value] || empathyMap.search);
      showButtonGroup(PRESCRIPTED.areas, handleAreaSelect);
      saveState();
    }, 600);
  }

  function handleAreaSelect(value, label) {
    chatState.area = value;
    trackEvent("chat_area_selected", { area: value });
    removeButtonGroup();
    addMessage("user", label);

    chatState.phase = "priority";

    showTyping();
    setTimeout(function () {
      hideTyping();
      var areaName = getAreaDisplayName(value);
      addMessage("ai", areaName + "エリアですね！\n\n転職で一番大切にしたいことを教えてください。あなたに合った求人を見つけやすくなります。");
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

      // Empathy + value message
      var priorityMessages = {
        salary: "お給料は大切ですよね。" + areaName + "エリアの看護師さんの求人を調べました。",
        commute: "通勤時間は毎日のことですもんね。" + areaName + "エリアでアクセスの良い求人を集めました。",
        wlb: "プライベートの時間も大事ですよね。" + areaName + "エリアで休日が多い求人を集めました。",
        environment: "職場の雰囲気は実際に働く上で一番大事かもしれませんね。" + areaName + "エリアの求人をご紹介します。",
      };

      addMessage("ai", (priorityMessages[chatState.priority] || priorityMessages.salary) + "\n\n" + count + "件以上の求人があります。一部をご紹介しますね。");

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
      var card = document.createElement("div");
      card.className = "chat-facility-card";

      // Highlight tag based on user priority
      var highlightTag = "";
      if (chatState.priority === "salary") highlightTag = h.salary;
      else if (chatState.priority === "commute") highlightTag = h.commute;
      else if (chatState.priority === "wlb") highlightTag = h.holidays;
      else highlightTag = h.features ? h.features.split("・")[0] : "";

      card.innerHTML =
        '<div class="facility-card-name">' + escapeHtml(h.displayName) + '</div>' +
        '<div class="facility-card-highlight">' + escapeHtml(highlightTag) + '</div>' +
        '<div class="facility-card-details">' +
          '<span>' + escapeHtml(h.salary) + '</span>' +
          '<span>' + escapeHtml(h.holidays) + '</span>' +
        '</div>';

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
      addMessage("ai", "気になる求人はありましたか？\n\nもっと詳しい条件や非公開求人の情報は、LINEでお伝えできます。もちろん、ここでもう少しお話しすることもできますよ。");

      // Show options
      var options = [
        { label: "LINEで詳しく聞く", value: "line" },
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
        addMessage("ai", "ありがとうございます！\n\nLINEでは、あなたの経験年数や細かい希望に合わせて、ぴったりの求人をお探しします。友だち追加後にメッセージをお送りくださいね。");
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
        addMessage("ai", "もちろんです！またいつでもお気軽にお声がけくださいね。\n\n気になることが出てきたら、いつでもここで相談できますよ。");
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
        'LINEで相談する' +
      '</a>' +
      '<div class="chat-line-card-trust">' +
        '<span>完全無料</span><span>手数料10%</span><span>しつこい電話なし</span>' +
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
      '<div class="chat-line-card-note">求人情報が気になったら</div>' +
      '<a href="https://lin.ee/HJwmQgp4" target="_blank" rel="noopener" class="chat-line-card-btn chat-line-card-btn-soft">' +
        'LINEで気軽に聞いてみる' +
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

    // Try API init (no phone required now - anonymous session)
    initAPISession();

    // Build context from pre-scripted flow
    var areaDisplay = getAreaDisplayName(chatState.area);
    var priorityLabels = { salary: "給与・待遇", commute: "通勤のしやすさ", wlb: "ワークライフバランス", environment: "職場の雰囲気" };
    var contextMsg = "【事前ヒアリング結果】希望エリア: " + (areaDisplay || "未選択") +
      " / 重視する条件: " + (priorityLabels[chatState.priority] || "未選択") +
      "。これらの情報を踏まえて、転職の詳しい希望条件を丁寧にヒアリングしてください。共感を示しながら、1つずつ質問してください。";
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
          'LINEでもっと詳しく相談する' +
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

    // Warm closing message
    var score = summaryData.score;
    var closingMessages = {
      A: "お話を聞かせていただきありがとうございました！あなたにぴったりの職場をお探しします。",
      B: "詳しくお聞かせいただきありがとうございました！あなたの経験が活きる職場をお探しします。",
      C: "ご相談ありがとうございました！まずは情報収集からでも大丈夫ですよ。",
      D: "お話しいただきありがとうございました。転職は大きな決断ですよね。",
    };

    setTimeout(function () {
      addMessage("ai", (closingMessages[score] || closingMessages.C) + "\n\nLINEで詳しい求人情報をお届けできます。気になったらいつでもどうぞ。");
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

    return filtered.length > 0 ? filtered : hospitals;
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
