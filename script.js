// ========================================
// NURSE ROBBY (ナースロビー) - Cutting-Edge UI Script
// Particles / Animations / Form / Slack
// ========================================

document.addEventListener("DOMContentLoaded", () => {

  // ============================================================
  // 1. Loading Screen (with progress animation)
  // ============================================================
  const loadingScreen = document.getElementById("loadingScreen");
  if (loadingScreen) {
    // 静的サイトなので即非表示（遅延不要）
    loadingScreen.classList.add("hidden");
  }

  // ============================================================
  // 2. Custom Cursor (Desktop only)
  // ============================================================
  const cursor = document.getElementById("customCursor");
  if (cursor && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    let cursorX = 0, cursorY = 0;
    let currentX = 0, currentY = 0;

    document.addEventListener("mousemove", (e) => {
      cursorX = e.clientX;
      cursorY = e.clientY;
    });

    function animateCursor() {
      currentX += (cursorX - currentX) * 0.15;
      currentY += (cursorY - currentY) * 0.15;
      cursor.style.left = currentX + "px";
      cursor.style.top = currentY + "px";
      requestAnimationFrame(animateCursor);
    }
    animateCursor();

    // Hover effect on interactive elements
    const hoverTargets = document.querySelectorAll("a, button, input, select, textarea, .feature-card, .flow-step, .trust-item");
    hoverTargets.forEach((el) => {
      el.addEventListener("mouseenter", () => cursor.classList.add("cursor-hover"));
      el.addEventListener("mouseleave", () => cursor.classList.remove("cursor-hover"));
    });
  }

  // ============================================================
  // 3. Scroll Progress Bar
  // ============================================================
  const scrollProgress = document.getElementById("scrollProgress");
  function updateScrollProgress() {
    if (!scrollProgress) return;
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    scrollProgress.style.width = scrollPercent + "%";
  }

  // ============================================================
  // 4. Particle Background (DISABLED for warm theme redesign)
  // ============================================================
  const canvas = document.getElementById("particleCanvas");
  if (canvas) {
    canvas.style.display = "none";
  }

  // --- Hero Slideshow ---
  (function() {
    var slides = document.querySelectorAll(".hero-slide");
    if (slides.length < 2) return;
    var current = 0;
    setInterval(function() {
      slides[current].classList.remove("hero-slide-active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("hero-slide-active");
    }, 5000);
  })();

  // ============================================================
  // 5. Hamburger Menu
  // ============================================================
  const hamburger = document.getElementById("hamburger");
  const mobileMenu = document.getElementById("mobileMenu");

  if (hamburger && mobileMenu) {
    function closeMobileMenu() {
      hamburger.classList.remove("active");
      mobileMenu.classList.remove("active");
      hamburger.setAttribute("aria-expanded", "false");
      hamburger.setAttribute("aria-label", "メニューを開く");
      hamburger.focus();
    }

    hamburger.addEventListener("click", () => {
      hamburger.classList.toggle("active");
      mobileMenu.classList.toggle("active");
      const isOpen = hamburger.classList.contains("active");
      hamburger.setAttribute("aria-expanded", isOpen);
      hamburger.setAttribute("aria-label", isOpen ? "メニューを閉じる" : "メニューを開く");
      if (isOpen) {
        var firstLink = mobileMenu.querySelector("a");
        if (firstLink) firstLink.focus();
      }
    });

    mobileMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        closeMobileMenu();
      });
    });

    // Focus trap and Escape key for mobile menu
    document.addEventListener("keydown", (e) => {
      if (!mobileMenu.classList.contains("active")) return;

      if (e.key === "Escape") {
        e.preventDefault();
        closeMobileMenu();
        return;
      }

      if (e.key === "Tab") {
        var focusable = mobileMenu.querySelectorAll("a, button, [tabindex]:not([tabindex='-1'])");
        if (focusable.length === 0) return;
        var first = focusable[0];
        var last = focusable[focusable.length - 1];

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

  // ============================================================
  // 6. Smooth Scroll
  // ============================================================
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const href = anchor.getAttribute("href");
      if (href === "#") return;
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        const headerOffset = 64;
        const elementPosition = target.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.scrollY - headerOffset;
        window.scrollTo({ top: offsetPosition, behavior: "smooth" });
      }
    });
  });

  // ============================================================
  // 7. Header Scroll Effect
  // ============================================================
  const header = document.getElementById("siteHeader") || document.querySelector(".header");

  function handleHeaderScroll() {
    if (!header) return;
    if (window.scrollY > 50) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  }

  // ============================================================
  // 8. Scroll Animations (IntersectionObserver - Enhanced)
  // ============================================================
  const animObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        animObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: "0px 0px -60px 0px",
  });

  // Feature cards with stagger (shimmer injection disabled for warm theme)
  document.querySelectorAll(".feature-card").forEach((el, i) => {
    el.classList.add("fade-in");
    el.style.transitionDelay = (i * 0.12) + "s";
    animObserver.observe(el);
    // Shimmer injection disabled for warm theme redesign
    // if (!el.querySelector(".feature-shimmer")) {
    //   const shimmer = document.createElement("div");
    //   shimmer.className = "feature-shimmer";
    //   shimmer.setAttribute("aria-hidden", "true");
    //   el.appendChild(shimmer);
    // }
  });

  // Flow steps with alternating direction
  document.querySelectorAll(".flow-step").forEach((el, i) => {
    el.classList.add(i % 2 === 0 ? "fade-in-left" : "fade-in-right");
    el.style.transitionDelay = (i * 0.1) + "s";
    animObserver.observe(el);
  });

  // Flow connectors
  document.querySelectorAll(".flow-connector").forEach((el) => {
    animObserver.observe(el);
  });

  // Mission items with stagger
  document.querySelectorAll(".cycle-item").forEach((el, i) => {
    el.classList.add("fade-in");
    el.style.transitionDelay = (i * 0.15) + "s";
    animObserver.observe(el);
  });

  document.querySelectorAll(".mission-statement").forEach((el) => {
    el.classList.add("fade-in");
    el.style.transitionDelay = "0.3s";
    animObserver.observe(el);
  });

  // Trust items with scale-in stagger
  document.querySelectorAll(".trust-item").forEach((el, i) => {
    el.classList.add("scale-in");
    el.style.transitionDelay = (i * 0.12) + "s";
    animObserver.observe(el);
  });

  // Testimonial cards with alternating slide
  document.querySelectorAll(".testimonial-card").forEach((el, i) => {
    el.classList.add(i % 2 === 0 ? "testimonial-slide-left" : "testimonial-slide-right");
    el.style.transitionDelay = (i * 0.15) + "s";
    animObserver.observe(el);
  });

  // Stats bar items
  document.querySelectorAll(".stat-item").forEach((el, i) => {
    el.style.transitionDelay = (i * 0.1) + "s";
    animObserver.observe(el);
  });

  // Section titles - clip-path reveal animation
  document.querySelectorAll(".section-title").forEach((el) => {
    el.classList.add("reveal-clip");
    animObserver.observe(el);
  });

  // Section descriptions
  document.querySelectorAll(".section-desc").forEach((el) => {
    el.classList.add("fade-in");
    el.style.transitionDelay = "0.2s";
    animObserver.observe(el);
  });

  // Table and form sections
  document.querySelectorAll(".table-wrapper, .form-section").forEach((el, i) => {
    el.classList.add("fade-in");
    el.style.transitionDelay = (i * 0.1) + "s";
    animObserver.observe(el);
  });

  // Hospital cards (mobile)
  document.querySelectorAll(".hospital-card").forEach((el, i) => {
    el.classList.add("fade-in");
    el.style.transitionDelay = (i * 0.1) + "s";
    animObserver.observe(el);
  });

  // ============================================================
  // 9. Count-Up Animation
  // ============================================================
  const countUpElements = document.querySelectorAll(".count-up");
  const countObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute("data-target"), 10);
        const suffix = el.getAttribute("data-suffix") || "";
        let current = 0;
        const duration = 1500;
        const startTime = performance.now();

        function updateCount(now) {
          const elapsed = now - startTime;
          const progress = Math.min(elapsed / duration, 1);
          // Ease out cubic
          const eased = 1 - Math.pow(1 - progress, 3);
          current = Math.round(target * eased);
          el.textContent = current + suffix;
          if (progress < 1) {
            requestAnimationFrame(updateCount);
          }
        }
        requestAnimationFrame(updateCount);
        countObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  countUpElements.forEach((el) => countObserver.observe(el));

  // ============================================================
  // 10. 3D Tilt Effect (DISABLED for warm theme redesign)
  // ============================================================
  // if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
  //   const tiltCards = document.querySelectorAll("[data-tilt]");
  //   tiltCards.forEach((card) => { ... });
  // }

  // ============================================================
  // 11. Parallax Scroll Effect
  // ============================================================
  let ticking = false;

  // Sticky mobile CTA
  const stickyCta = document.getElementById("stickyCta");

  function handleScroll() {
    updateScrollProgress();
    handleHeaderScroll();

    // Sticky CTA: show after scrolling past hero
    if (stickyCta) {
      const heroBottom = document.getElementById("hero");
      if (heroBottom) {
        const heroRect = heroBottom.getBoundingClientRect();
        if (heroRect.bottom < 0) {
          stickyCta.classList.add("visible");
        } else {
          stickyCta.classList.remove("visible");
        }
      }
    }

    // Parallax for sections
    const scrollY = window.scrollY;
    document.querySelectorAll(".parallax-section").forEach((section) => {
      const rect = section.getBoundingClientRect();
      const speed = 0.03;
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        const offset = (rect.top - window.innerHeight / 2) * speed;
        section.style.transform = "translateY(" + offset + "px)";
      }
    });
  }

  window.addEventListener("scroll", () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        handleScroll();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  // ============================================================
  // 12. Hero Subtitle (relies on heroElementIn CSS animation)
  // ============================================================
  // Typing animation removed to avoid visual flash when restoring
  // original HTML markup. The heroElementIn CSS animation already
  // provides a smooth fade-in for the subtitle.

  // ============================================================
  // 13. Form Validation & Submission (Preserved)
  // ============================================================
  const form = document.getElementById("registerForm");
  const submitBtn = document.getElementById("submitBtn");

  if (!form) return;

  const validators = {
    lastName: {
      test: (v) => v.trim().length > 0,
      msg: "姓を入力してください",
    },
    firstName: {
      test: (v) => v.trim().length > 0,
      msg: "名を入力してください",
    },
    profession: {
      test: (v) => v !== "",
      msg: "資格・職種を選択してください",
    },
    age: {
      test: (v) => {
        const n = parseInt(v, 10);
        return !isNaN(n) && n >= 18 && n <= 70;
      },
      msg: "18〜70の年齢を入力してください",
    },
    phone: {
      test: (v) => {
        const digits = v.replace(/[\s\-\(\)\+]/g, "");
        return /^0\d{9,10}$/.test(digits);
      },
      msg: "正しい電話番号を入力してください（ハイフンあり・なしどちらでも可）",
    },
    email: {
      test: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
      msg: "正しいメールアドレスを入力してください",
    },
    experience: {
      test: (v) => v !== "",
      msg: "経験年数を選択してください",
    },
    currentStatus: {
      test: (v) => v !== "",
      msg: "現在の勤務状況を選択してください",
    },
    transferTiming: {
      test: (v) => v !== "",
      msg: "希望転職時期を選択してください",
    },
    desiredSalary: {
      test: (v) => v !== "",
      msg: "希望給与レンジを選択してください",
    },
  };

  function validateField(name) {
    const el = document.getElementById(name);
    const errorEl = document.getElementById(name + "Error");
    const rule = validators[name];

    if (!el || !rule) return true;

    const valid = rule.test(el.value);
    if (!valid) {
      el.classList.add("error");
      if (errorEl) errorEl.textContent = rule.msg;
    } else {
      el.classList.remove("error");
      if (errorEl) errorEl.textContent = "";
    }
    return valid;
  }

  // Real-time validation on blur
  Object.keys(validators).forEach((name) => {
    const el = document.getElementById(name);
    if (el) {
      el.addEventListener("blur", () => validateField(name));
      el.addEventListener("input", () => {
        if (el.classList.contains("error")) {
          validateField(name);
        }
      });
    }
  });

  function validateAll() {
    let allValid = true;
    Object.keys(validators).forEach((name) => {
      if (!validateField(name)) {
        allValid = false;
      }
    });

    const agree = document.getElementById("agreeTerms");
    const agreeError = document.getElementById("agreeTermsError");
    if (agree && !agree.checked) {
      allValid = false;
      if (agreeError) agreeError.textContent = "利用規約への同意が必要です";
    } else {
      if (agreeError) agreeError.textContent = "";
    }

    return allValid;
  }

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validateAll()) {
      const firstError = form.querySelector(".error");
      if (firstError) {
        firstError.scrollIntoView({ behavior: "smooth", block: "center" });
        firstError.focus();
      }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "送信中...";

    const formData = {
      lastName: document.getElementById("lastName").value.trim(),
      firstName: document.getElementById("firstName").value.trim(),
      profession: document.getElementById("profession").value,
      age: document.getElementById("age").value,
      phone: document.getElementById("phone").value.trim(),
      email: document.getElementById("email").value.trim(),
      experience: document.getElementById("experience").value,
      currentStatus: document.getElementById("currentStatus").value,
      transferTiming: document.getElementById("transferTiming").value,
      desiredSalary: document.getElementById("desiredSalary").value,
      workStyle: document.getElementById("workStyle").value || "未回答",
      nightShift: document.getElementById("nightShift").value || "未回答",
      holidays: document.getElementById("holidays").value.trim() || "未回答",
      commuteRange: document.getElementById("commuteRange").value.trim() || "未回答",
      notes: document.getElementById("notes").value.trim() || "なし",
      registeredAt: new Date().toLocaleString("ja-JP"),
    };

    try {
      const endpoint = typeof CONFIG !== "undefined" && CONFIG.API.workerEndpoint
        ? CONFIG.API.workerEndpoint + "/api/register"
        : "";

      if (!endpoint) {
        console.log("[Register] Worker endpoint未設定。送信データ:", formData);
        showThanks();
        return;
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const result = await res.json();

      if (result.success) {
        showThanks();
      } else {
        console.error("登録エラー:", result.error);
        showFormError();
      }
    } catch (err) {
      console.error("送信エラー:", err);
      showFormError();
    }
  });

  function calcUrgency(data) {
    const timing = data.transferTiming;
    if (timing === "すぐにでも") return "A";
    if (timing === "1ヶ月以内") return "B";
    if (timing === "3ヶ月以内") return "C";
    return "D";
  }

  async function sendToSlack(data, urgency) {
    const webhookUrl = typeof CONFIG !== "undefined" ? CONFIG.API.slackWebhookUrl : "";

    if (!webhookUrl) {
      console.log("[Slack] Webhook URL未設定。送信データ:", data);
      return;
    }

    const urgencyEmoji = { A: "\uD83D\uDD34", B: "\uD83D\uDFE1", C: "\uD83D\uDFE2", D: "\u26AA" };
    const channelNotify = urgency === "A" ? "<!channel> " : "";

    const message = {
      text: channelNotify + "\uD83C\uDFE5 *新規求職者登録*\n\n" +
        "*温度感: " + urgencyEmoji[urgency] + " " + urgency + "*\n\n" +
        "*基本情報*\n" +
        "氏名：" + data.lastName + " " + data.firstName + "さん（" + data.age + "歳）\n" +
        "経験：" + data.experience + "\n" +
        "現在：" + data.currentStatus + "\n" +
        "連絡先：" + data.phone + " / " + data.email + "\n\n" +
        "*希望条件*\n" +
        "給与：" + data.desiredSalary + "\n" +
        "転職時期：" + data.transferTiming + "\n" +
        "勤務形態：" + data.workStyle + "\n" +
        "夜勤：" + data.nightShift + "\n" +
        "休日：" + data.holidays + "\n" +
        "通勤：" + data.commuteRange + "\n\n" +
        "*備考*\n" + data.notes + "\n\n" +
        "*要対応*\n" +
        "\u25A1 24時間以内に初回架電\n" +
        "\u25A1 希望条件に合う求人確認\n" +
        "\u25A1 面接日程調整\n\n" +
        "登録日時：" + data.registeredAt,
    };

    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message),
    });
  }

  async function sendToSheets(data) {
    const sheetsId = typeof CONFIG !== "undefined" ? CONFIG.API.googleSheetsId : "";

    if (!sheetsId) {
      console.log("[Sheets] シートID未設定。送信データ:", data);
      return;
    }

    console.log("[Sheets] サーバーサイド連携で送信予定:", data);
  }

  function showFormError() {
    submitBtn.disabled = false;
    submitBtn.textContent = "無料で相談する";
    let banner = document.getElementById("formErrorBanner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "formErrorBanner";
      banner.className = "form-error-banner";
      banner.innerHTML = "送信に失敗しました。通信環境をご確認のうえ、再度お試しください。<br><button type=\"button\" id=\"retrySubmitBtn\">もう一度送信する</button>";
      form.insertBefore(banner, form.firstChild);
      document.getElementById("retrySubmitBtn").addEventListener("click", () => {
        banner.classList.remove("visible");
        form.dispatchEvent(new Event("submit", { cancelable: true }));
      });
    }
    banner.classList.add("visible");
    banner.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function showThanks() {
    document.getElementById("register").classList.add("hidden");
    var thanks = document.getElementById("thanks");
    thanks.classList.remove("hidden");
    thanks.scrollIntoView({ behavior: "smooth" });
  }

  // Back to top button (Thanks screen)
  const backToTop = document.getElementById("backToTop");
  if (backToTop) {
    backToTop.addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("thanks").classList.add("hidden");
      document.getElementById("register").classList.remove("hidden");
      form.reset();
      submitBtn.disabled = false;
      submitBtn.textContent = "無料で相談する";
      document.querySelectorAll(".error").forEach((el) => el.classList.remove("error"));
      document.querySelectorAll(".error-msg").forEach((el) => (el.textContent = ""));
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Initial scroll handling
  handleScroll();

  // ============================================================
  // 14. Magnetic Button Effect (Vanilla JS, no GSAP)
  // ============================================================
  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    const magneticButtons = document.querySelectorAll(".btn-primary, .hero-cta, .nav-cta");
    const MAGNETIC_AREA = 120;
    const MAGNETIC_STRENGTH = 0.3;

    magneticButtons.forEach((btn) => {
      btn.classList.add("magnetic-btn");

      btn.addEventListener("mousemove", (e) => {
        const rect = btn.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const distX = e.clientX - centerX;
        const distY = e.clientY - centerY;
        const dist = Math.sqrt(distX * distX + distY * distY);

        if (dist < MAGNETIC_AREA) {
          btn.classList.remove("magnetic-reset");
          const pull = (MAGNETIC_AREA - dist) / MAGNETIC_AREA;
          const tx = distX * pull * MAGNETIC_STRENGTH;
          const ty = distY * pull * MAGNETIC_STRENGTH;
          btn.style.transform = "translate(" + tx + "px, " + ty + "px) translateY(-2px)";
        }
      });

      btn.addEventListener("mouseleave", () => {
        btn.classList.add("magnetic-reset");
        btn.style.transform = "";
      });
    });
  }

  // ============================================================
  // 15. Button Glow Elements Injection (DISABLED for warm theme redesign)
  // ============================================================
  // document.querySelectorAll(".btn-primary").forEach((btn) => {
  //   if (!btn.querySelector(".btn-glow")) {
  //     const glow = document.createElement("span");
  //     glow.className = "btn-glow";
  //     glow.setAttribute("aria-hidden", "true");
  //     btn.appendChild(glow);
  //   }
  // });

  // ============================================================
  // 16. Button Ripple Effect
  // ============================================================
  document.querySelectorAll(".btn, .btn-primary, .btn-outline, .btn-animated-border, .nav-cta").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const existing = btn.querySelector(".btn-ripple");
      if (existing) existing.remove();

      const ripple = document.createElement("span");
      ripple.className = "btn-ripple";
      ripple.setAttribute("aria-hidden", "true");

      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
      ripple.style.top = (e.clientY - rect.top - size / 2) + "px";

      btn.appendChild(ripple);
      ripple.addEventListener("animationend", () => ripple.remove());
    });
  });

  // ============================================================
  // 17. Enhanced Parallax with Depth Layers
  // ============================================================
  // Add parallax depth classes to specific elements
  document.querySelectorAll(".feature-number, .feature-icon, .step-number").forEach((el) => {
    el.classList.add("parallax-depth-1");
  });

  document.querySelectorAll(".testimonial-quote").forEach((el) => {
    el.classList.add("parallax-depth-2");
  });

  // ============================================================
  // 18. Facility Matching Engine
  // ============================================================

  // --- Helper: Get all facilities flattened with area context ---
  function getAllFacilities() {
    if (typeof AREA_DATABASE === "undefined") return [];
    var results = [];
    for (var i = 0; i < AREA_DATABASE.length; i++) {
      var area = AREA_DATABASE[i];
      var facilities = area.majorFacilities || [];
      for (var j = 0; j < facilities.length; j++) {
        results.push({ facility: facilities[j], area: area });
      }
    }
    return results;
  }

  // --- Helper: Parse salary select value to numeric range ---
  function parseSalaryRange(selectValue) {
    if (!selectValue) return { min: 0, max: 999999 };
    if (selectValue === "25万以下" || selectValue === "25万未満")
      return { min: 0, max: 250000 };
    if (selectValue === "25-30万")
      return { min: 250000, max: 300000 };
    if (selectValue === "30-35万")
      return { min: 300000, max: 350000 };
    if (selectValue === "35-40万")
      return { min: 350000, max: 400000 };
    if (selectValue === "40万以上")
      return { min: 400000, max: 999999 };
    // "相談したい" or unknown
    return { min: 0, max: 999999 };
  }

  // --- Helper: Parse salary string like "月給28〜38万円" to numeric range ---
  function parseFacilitySalary(area, profession) {
    var salaryStr = "";
    if (profession && (profession === "理学療法士" || profession === "作業療法士" || profession === "言語聴覚士")) {
      salaryStr = area.ptAvgSalary || "";
    } else {
      salaryStr = area.nurseAvgSalary || "";
    }
    // Extract numbers from string like "月給28〜38万円"
    var nums = salaryStr.match(/(\d+)/g);
    if (nums && nums.length >= 2) {
      return { min: parseInt(nums[0], 10) * 10000, max: parseInt(nums[1], 10) * 10000 };
    }
    if (nums && nums.length === 1) {
      return { min: parseInt(nums[0], 10) * 10000, max: parseInt(nums[0], 10) * 10000 };
    }
    return { min: 0, max: 999999 };
  }

  // --- Helper: Determine nightShift type from facility data ---
  function getFacilityNightShift(facility) {
    // Use enhanced field if Task #1 has added it
    if (facility.nightShiftType) return facility.nightShiftType;
    // Infer from features/type
    var features = (facility.features || "").toLowerCase();
    var functions = facility.functions || [];
    if (features.includes("慢性期") || functions.indexOf("慢性期") >= 0) {
      if (functions.length === 1 && functions[0] === "慢性期") return "optional";
    }
    if (features.includes("回復期") && functions.length === 1) return "optional";
    if (features.includes("高度急性期") || features.includes("救命救急")) return "required";
    if (functions.indexOf("高度急性期") >= 0 || functions.indexOf("急性期") >= 0) return "required";
    return "optional";
  }

  // --- Helper: Map experience string to numeric years ---
  function parseExperienceYears(expValue) {
    if (!expValue) return 0;
    if (expValue === "未経験") return 0;
    if (expValue === "1年未満") return 0.5;
    if (expValue === "1-3年") return 2;
    if (expValue === "3-5年") return 4;
    if (expValue === "5-10年") return 7;
    if (expValue === "10-20年") return 15;
    if (expValue === "20年以上") return 25;
    return 0;
  }

  // --- Helper: Find medical region for an area ---
  function getAreaRegion(area) {
    // Use enhanced field if Task #1 has added it
    if (area.medicalRegion) return area.medicalRegion;
    // Fallback: infer from areaId
    var regionMap = {
      odawara: "kensei",
      hadano: "kensei",
      minamiashigara_kaisei_oi: "kensei",
      oiso_ninomiya: "shonan_west",
      hiratsuka: "shonan_west",
      chigasaki: "shonan_east",
      fujisawa: "shonan_east",
      isehara: "kenoh",
      atsugi: "kenoh",
      ebina: "kenoh",
    };
    return regionMap[area.areaId] || "other";
  }

  // --- Adjacent regions mapping ---
  var ADJACENT_REGIONS = {
    kensei: ["shonan_west"],
    shonan_west: ["kensei", "shonan_east"],
    shonan_east: ["shonan_west", "kenoh"],
    kenoh: ["shonan_east", "kensei"],
  };

  // --- Score a single facility (100 points max) ---
  function scoreFacility(facility, areaData, criteria) {
    var breakdown = {};
    var reasons = [];

    // 1. Commute Score (30 points)
    var commuteScore = 0;
    if (criteria.commuteArea) {
      var userRegion = null;
      // Find the user's area from commuteRange text
      var userArea = null;
      for (var i = 0; i < AREA_DATABASE.length; i++) {
        if (criteria.commuteArea === AREA_DATABASE[i].areaId ||
            criteria.commuteArea.includes(AREA_DATABASE[i].name) ||
            AREA_DATABASE[i].name.includes(criteria.commuteArea)) {
          userArea = AREA_DATABASE[i];
          break;
        }
      }
      if (userArea) {
        userRegion = getAreaRegion(userArea);
        var facilityRegion = getAreaRegion(areaData);

        if (userArea.areaId === areaData.areaId) {
          commuteScore = 30;
          reasons.push("希望エリア内の施設です");
        } else if (userRegion === facilityRegion) {
          commuteScore = 20;
          reasons.push("同一医療圏の施設です（" + areaData.name + "）");
        } else if (ADJACENT_REGIONS[userRegion] && ADJACENT_REGIONS[userRegion].indexOf(facilityRegion) >= 0) {
          commuteScore = 10;
          reasons.push("隣接医療圏の施設です（" + areaData.name + "）");
        } else {
          commuteScore = 0;
        }
      } else {
        // Could not determine user area; give partial score
        commuteScore = 15;
      }
    } else {
      // No commute preference: give full points
      commuteScore = 30;
    }
    breakdown.commute = commuteScore;

    // 2. Salary Score (25 points)
    var salaryScore = 0;
    if (criteria.salaryRange) {
      var fSalary = null;
      // Use enhanced fields if available (Task #1)
      if (facility.nurseMonthlyMin && criteria.profession !== "理学療法士" && criteria.profession !== "作業療法士" && criteria.profession !== "言語聴覚士") {
        fSalary = { min: facility.nurseMonthlyMin, max: facility.nurseMonthlyMax || facility.nurseMonthlyMin };
      } else if (facility.ptMonthlyMin && (criteria.profession === "理学療法士" || criteria.profession === "作業療法士" || criteria.profession === "言語聴覚士")) {
        fSalary = { min: facility.ptMonthlyMin, max: facility.ptMonthlyMax || facility.ptMonthlyMin };
      } else {
        // Fallback: use area-level salary data
        fSalary = parseFacilitySalary(areaData, criteria.profession);
      }

      var userSalary = criteria.salaryRange;

      // Check overlap between user desired range and facility range
      var overlapMin = Math.max(userSalary.min, fSalary.min);
      var overlapMax = Math.min(userSalary.max, fSalary.max);

      if (overlapMin <= overlapMax) {
        // Ranges overlap
        salaryScore = 25;
        reasons.push("希望給与レンジに適合");
      } else {
        // No direct overlap; check how close
        var gap = Math.min(Math.abs(userSalary.min - fSalary.max), Math.abs(userSalary.max - fSalary.min));
        if (gap <= 50000) {
          salaryScore = 15;
          reasons.push("希望給与に近い水準（差額5万円以内）");
        } else {
          salaryScore = 5;
        }
      }
    } else {
      salaryScore = 25;
    }
    breakdown.salary = salaryScore;

    // 3. Work Style / Night Shift Score (20 points)
    var workStyleScore = 0;
    var nightShiftType = getFacilityNightShift(facility);

    if (criteria.nightShift) {
      if (criteria.nightShift === "可能") {
        // User can do night shift; prefer facilities that have night shifts
        if (nightShiftType === "required") {
          workStyleScore = 20;
          reasons.push("夜勤あり（希望に合致）");
        } else {
          workStyleScore = 15;
        }
      } else if (criteria.nightShift === "不可") {
        // User does not want night shift
        if (nightShiftType === "none" || (facility.functions && facility.functions.length === 1 && facility.functions[0] === "慢性期")) {
          workStyleScore = 20;
          reasons.push("夜勤なしの勤務が可能");
        } else if (nightShiftType === "optional") {
          workStyleScore = 10;
          reasons.push("夜勤は応相談");
        } else {
          workStyleScore = 0;
        }
      } else {
        // "相談したい" or other
        workStyleScore = 15;
      }
    } else {
      workStyleScore = 20;
    }
    breakdown.workStyle = workStyleScore;

    // 4. Facility Size / Experience Match Score (15 points)
    var facilitySizeScore = 0;
    var expYears = parseExperienceYears(criteria.experience);
    var beds = facility.beds || 0;
    var hasEducation = (facility.features || "").includes("教育") ||
                       (facility.features || "").includes("研修") ||
                       (facility.features || "").includes("プリセプター");

    if (expYears <= 1) {
      // New grad / minimal experience -> prefer large hospitals with education
      if (beds >= 300 && hasEducation) {
        facilitySizeScore = 15;
        reasons.push("教育体制が充実した大規模病院");
      } else if (beds >= 300) {
        facilitySizeScore = 12;
        reasons.push("大規模病院で学びの機会が豊富");
      } else if (beds >= 100) {
        facilitySizeScore = 8;
      } else {
        facilitySizeScore = 4;
      }
    } else if (expYears <= 5) {
      // Mid-career -> flexible, slightly prefer medium-large
      if (beds >= 200 && beds <= 500) {
        facilitySizeScore = 15;
        reasons.push("経験を活かせる中〜大規模病院");
      } else if (beds >= 100) {
        facilitySizeScore = 12;
      } else {
        facilitySizeScore = 8;
      }
    } else {
      // Veteran -> flexible, can handle any size; mid-size may be best
      if (beds >= 100 && beds <= 400) {
        facilitySizeScore = 15;
        reasons.push("豊富な経験を活かせる環境");
      } else if (beds > 400) {
        facilitySizeScore = 12;
      } else {
        facilitySizeScore = 10;
      }
    }
    breakdown.facilitySize = facilitySizeScore;

    // 5. Demand Score (10 points) - does the facility employ this profession?
    var demandScore = 0;
    var isRehab = criteria.profession === "理学療法士" || criteria.profession === "作業療法士" || criteria.profession === "言語聴覚士";

    if (isRehab) {
      if (facility.ptCount && facility.ptCount > 0) {
        demandScore = 10;
        reasons.push("リハビリスタッフ配置あり（" + facility.ptCount + "名）");
      } else if ((facility.features || "").includes("リハビリ") || (facility.features || "").includes("PT")) {
        demandScore = 7;
        reasons.push("リハビリ機能あり");
      } else {
        demandScore = 2;
      }
    } else {
      // Nurse-type profession
      if (facility.nurseCount && facility.nurseCount > 0) {
        demandScore = 10;
      } else {
        demandScore = 5;
      }
    }
    breakdown.demand = demandScore;

    var totalScore = commuteScore + salaryScore + workStyleScore + facilitySizeScore + demandScore;

    return {
      score: totalScore,
      breakdown: breakdown,
      reasons: reasons,
    };
  }

  // --- Main matching function ---
  function matchFacilities(formData) {
    var allFacilities = getAllFacilities();
    if (allFacilities.length === 0) return [];

    // Build criteria from form data
    var salaryRange = parseSalaryRange(formData.desiredSalary);

    // Attempt to extract area from commuteRange free text
    var commuteArea = "";
    if (formData.commuteRange && formData.commuteRange !== "未回答") {
      // Try to match known area names
      for (var i = 0; i < AREA_DATABASE.length; i++) {
        var aName = AREA_DATABASE[i].name.replace(/市|町/g, "");
        if (formData.commuteRange.includes(aName) || formData.commuteRange.includes(AREA_DATABASE[i].name)) {
          commuteArea = AREA_DATABASE[i].areaId;
          break;
        }
      }
      // Also check station names
      if (!commuteArea) {
        for (var k = 0; k < AREA_DATABASE.length; k++) {
          var stations = AREA_DATABASE[k].majorStations || [];
          for (var s = 0; s < stations.length; s++) {
            // Extract station name before the parenthesis
            var stationName = stations[s].split("（")[0].replace(/駅$/, "");
            if (formData.commuteRange.includes(stationName)) {
              commuteArea = AREA_DATABASE[k].areaId;
              break;
            }
          }
          if (commuteArea) break;
        }
      }
    }

    var criteria = {
      profession: formData.profession,
      experience: formData.experience,
      salaryRange: salaryRange,
      nightShift: formData.nightShift,
      commuteArea: commuteArea,
    };

    // Score all facilities
    var scored = [];
    for (var j = 0; j < allFacilities.length; j++) {
      var entry = allFacilities[j];
      var result = scoreFacility(entry.facility, entry.area, criteria);
      scored.push({
        facility: entry.facility,
        area: entry.area,
        score: result.score,
        breakdown: result.breakdown,
        reasons: result.reasons,
      });
    }

    // Sort by score descending
    scored.sort(function(a, b) { return b.score - a.score; });

    // Return top 5
    return scored.slice(0, 5);
  }

  // --- Display match results in DOM ---
  function showMatchResults(results) {
    var container = document.getElementById("matchResults");
    var section = document.getElementById("matchSection");
    if (!container || !section || results.length === 0) return;

    container.innerHTML = "";

    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var pct = Math.round(r.score);
      var f = r.facility;

      var card = document.createElement("div");
      card.className = "match-card";

      // Build recommendation comment from reasons
      var comment = r.reasons.length > 0 ? r.reasons.join("。") : "";

      card.innerHTML =
        '<div class="match-card-header">' +
          '<span class="match-card-rank">#' + (i + 1) + "</span>" +
          '<div class="match-card-score">' +
            '<div class="match-card-score-bar">' +
              '<div class="match-card-score-fill" style="width:' + pct + '%"></div>' +
            "</div>" +
            '<span class="match-card-score-value">' + pct + "%</span>" +
          "</div>" +
        "</div>" +
        '<div class="match-card-name">' + f.name + "</div>" +
        '<div class="match-card-details">' +
          '<div class="match-card-detail">' +
            '<span class="match-card-detail-label">エリア</span>' +
            '<span class="match-card-detail-value">' + r.area.name + "</span>" +
          "</div>" +
          '<div class="match-card-detail">' +
            '<span class="match-card-detail-label">病床数</span>' +
            '<span class="match-card-detail-value">' + (f.beds ? f.beds + "床" : "-") + "</span>" +
          "</div>" +
          '<div class="match-card-detail">' +
            '<span class="match-card-detail-label">種別</span>' +
            '<span class="match-card-detail-value">' + (f.type || "-") + "</span>" +
          "</div>" +
          '<div class="match-card-detail">' +
            '<span class="match-card-detail-label">アクセス</span>' +
            '<span class="match-card-detail-value">' + (f.access || "-") + "</span>" +
          "</div>" +
        "</div>" +
        (comment ? '<div class="match-card-comment">' + comment + "</div>" : "");

      container.appendChild(card);
    }

    // Make section visible
    section.style.display = "block";
  }

  // --- Hook into form submission ---
  // Override showThanks to chain matching after thanks display
  var _originalShowThanks = showThanks;
  showThanks = function() {
    _originalShowThanks();

    // Collect form data for matching (form elements may be hidden, read from collected data)
    var matchFormData = {
      profession: (document.getElementById("profession") || {}).value || "",
      experience: (document.getElementById("experience") || {}).value || "",
      desiredSalary: (document.getElementById("desiredSalary") || {}).value || "",
      nightShift: (document.getElementById("nightShift") || {}).value || "",
      commuteRange: (document.getElementById("commuteRange") || {}).value || "",
    };

    try {
      var matches = matchFacilities(matchFormData);
      if (matches.length > 0) {
        showMatchResults(matches);
      }
    } catch (err) {
      console.error("マッチングエラー:", err);
    }
  };

});
