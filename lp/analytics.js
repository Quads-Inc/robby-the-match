/**
 * ナースロビー — Google Analytics 4 共通スニペット
 *
 * 設置方法:
 *   <script async src="https://www.googletagmanager.com/gtag/js?id=G-X4G2BYW13B"></script>
 *   <script src="/analytics.js"></script>
 *
 * 機能:
 *   - GA4の基本設定 (gtag config)
 *   - LINE登録ボタンクリックトラッキング
 *   - ページスクロール深度トラッキング (25%, 50%, 75%, 100%)
 *   - 電話番号クリックトラッキング
 *   - フォーム送信トラッキング
 *   - UTMパラメータ解析・セッション保存
 *   - 外部リンククリックトラッキング
 */

(function () {
  'use strict';

  // ===================================================================
  // 測定ID（プレースホルダー — GA4プロパティ作成後に置き換えること）
  // ===================================================================
  var GA_MEASUREMENT_ID = 'G-X4G2BYW13B';

  // ===================================================================
  // gtag 初期化
  // ===================================================================
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  gtag('js', new Date());
  gtag('config', GA_MEASUREMENT_ID, {
    send_page_view: true,
  });

  // グローバルにgtagを公開（他のスクリプトから呼び出し可能にする）
  window.gtag = gtag;

  // ===================================================================
  // UTMパラメータ解析・セッション保存
  // ===================================================================
  function parseUTMParams() {
    var params = new URLSearchParams(window.location.search);
    var utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
    var utmData = {};
    var hasUTM = false;

    utmKeys.forEach(function (key) {
      var value = params.get(key);
      if (value) {
        utmData[key] = value;
        hasUTM = true;
      }
    });

    if (hasUTM) {
      // セッションストレージに保存（同一セッション内でページ遷移しても保持）
      try {
        sessionStorage.setItem('robby_utm', JSON.stringify(utmData));
      } catch (e) {
        // Private browsing 等でsessionStorageが使えない場合は無視
      }

      // GA4にカスタムイベントとして送信
      gtag('event', 'utm_captured', {
        event_category: 'acquisition',
        utm_source: utmData.utm_source || '',
        utm_medium: utmData.utm_medium || '',
        utm_campaign: utmData.utm_campaign || '',
        utm_term: utmData.utm_term || '',
        utm_content: utmData.utm_content || '',
      });
    }

    return utmData;
  }

  /**
   * 保存済みのUTMパラメータを取得する
   * @returns {Object} UTMパラメータオブジェクト
   */
  function getSavedUTM() {
    try {
      var saved = sessionStorage.getItem('robby_utm');
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      return {};
    }
  }

  // 公開関数
  window.robbyGetUTM = getSavedUTM;

  // ===================================================================
  // LINE登録ボタンクリックトラッキング
  // ===================================================================
  function trackLineClick(element) {
    var utm = getSavedUTM();
    gtag('event', 'line_click', {
      event_category: 'engagement',
      event_label: 'LINE登録ボタン',
      page_location: window.location.href,
      page_title: document.title,
      utm_source: utm.utm_source || 'direct',
      utm_medium: utm.utm_medium || '',
      utm_campaign: utm.utm_campaign || '',
    });

    // TikTok→LINE conversion tracking with full UTM context
    gtag('event', 'line_registration_intent', {
      event_category: 'conversion',
      event_label: 'LINE登録意向',
      page_location: window.location.href,
      page_title: document.title,
      utm_source: utm.utm_source || 'direct',
      utm_medium: utm.utm_medium || '',
      utm_campaign: utm.utm_campaign || '',
      utm_term: utm.utm_term || '',
      utm_content: utm.utm_content || '',
    });
  }

  function bindLineButtons() {
    // LINE登録ボタンを自動検出してバインド
    // 対象: href に "line.me" を含むリンク、class に "line" を含む要素
    var selectors = [
      'a[href*="line.me"]',
      'a[href*="lin.ee"]',
      '.line-btn',
      '.line-button',
      '[data-action="line-register"]',
    ];

    var selector = selectors.join(', ');
    var buttons = document.querySelectorAll(selector);

    buttons.forEach(function (btn) {
      if (btn.dataset.robbyTracked) return; // 二重バインド防止
      btn.dataset.robbyTracked = 'true';

      btn.addEventListener('click', function (e) {
        trackLineClick(btn);
      });
    });
  }

  // 公開関数
  window.robbyTrackLineClick = trackLineClick;

  // ===================================================================
  // ページスクロール深度トラッキング
  // ===================================================================
  function initScrollTracking() {
    var thresholds = [25, 50, 75, 100];
    var reached = {};

    function getScrollPercent() {
      var docHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      var winHeight = window.innerHeight;
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;

      if (docHeight <= winHeight) return 100;
      return Math.round((scrollTop / (docHeight - winHeight)) * 100);
    }

    function checkScroll() {
      var percent = getScrollPercent();

      thresholds.forEach(function (threshold) {
        if (percent >= threshold && !reached[threshold]) {
          reached[threshold] = true;
          gtag('event', 'scroll_depth', {
            event_category: 'engagement',
            event_label: threshold + '%',
            value: threshold,
            page_location: window.location.href,
          });
        }
      });
    }

    // スクロールイベント（throttle付き）
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          checkScroll();
          ticking = false;
        });
        ticking = true;
      }
    });

    // 初回チェック（短いページの場合即座に100%になる可能性）
    checkScroll();
  }

  // ===================================================================
  // 電話番号クリックトラッキング
  // ===================================================================
  function bindPhoneLinks() {
    var phoneLinks = document.querySelectorAll('a[href^="tel:"]');
    phoneLinks.forEach(function (link) {
      if (link.dataset.robbyTracked) return;
      link.dataset.robbyTracked = 'true';

      link.addEventListener('click', function () {
        gtag('event', 'phone_click', {
          event_category: 'lead',
          event_label: link.href.replace('tel:', ''),
          page_location: window.location.href,
        });
      });
    });
  }

  // ===================================================================
  // フォーム送信トラッキング
  // ===================================================================
  function bindForms() {
    var forms = document.querySelectorAll('form');
    forms.forEach(function (form) {
      if (form.dataset.robbyTracked) return;
      form.dataset.robbyTracked = 'true';

      form.addEventListener('submit', function () {
        var formId = form.id || form.name || 'unknown_form';
        gtag('event', 'form_submit', {
          event_category: 'lead',
          event_label: formId,
          page_location: window.location.href,
        });
      });
    });
  }

  // ===================================================================
  // 外部リンククリックトラッキング
  // ===================================================================
  function bindExternalLinks() {
    var currentHost = window.location.hostname;
    var links = document.querySelectorAll('a[href^="http"]');

    links.forEach(function (link) {
      if (link.dataset.robbyTracked) return;

      try {
        var linkHost = new URL(link.href).hostname;
        if (linkHost !== currentHost) {
          link.dataset.robbyTracked = 'true';
          link.addEventListener('click', function () {
            gtag('event', 'outbound_click', {
              event_category: 'engagement',
              event_label: link.href,
              page_location: window.location.href,
            });
          });
        }
      } catch (e) {
        // URL解析エラーは無視
      }
    });
  }

  // ===================================================================
  // 初期化
  // ===================================================================
  function init() {
    parseUTMParams();
    bindLineButtons();
    initScrollTracking();
    bindPhoneLinks();
    bindForms();
    bindExternalLinks();
  }

  // DOM準備完了後に初期化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
