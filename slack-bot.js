// ========================================
// NURSE ROBBY (ナースロビー) - Slack → Claude Code Bridge
// Slackメッセージ = Claude Code入力と同等に処理
// ========================================

const { App } = require("@slack/bolt");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

// .env読み込み
const envPath = path.join(__dirname, "slack-bot.env");
const envContent = fs.readFileSync(envPath, "utf8");
const env = {};
envContent.split("\n").forEach((line) => {
  const [key, ...vals] = line.split("=");
  if (key && vals.length) env[key.trim()] = vals.join("=").trim();
});

const app = new App({
  token: env.SLACK_BOT_TOKEN,
  appToken: env.SLACK_APP_TOKEN,
  socketMode: true,
});

const CHANNEL_ID = "C09A7U4TV4G";
const PROJECT_DIR = __dirname;
let processing = false;

// ---------- プロジェクト固定コンテキスト ----------
const SYSTEM_CONTEXT = `あなたはナースロビープロジェクトの開発エージェントです。
プロジェクトディレクトリ: ${PROJECT_DIR}
このプロジェクトは医療人材紹介LP（はるひメディカルサービス）です。
ボートレースとは無関係です。このプロジェクトのファイルのみを対象に作業してください。
主要ファイル: index.html, style.css, script.js, chat.js, chat.css, config.js, privacy.html, terms.html, api/worker.js
ブランド名: ナースロビー
日本語で回答してください。`;

// ---------- Claude Code実行 ----------
async function runClaude(prompt, say) {
  if (processing) {
    await say(":hourglass_flowing_sand: 前のリクエストを処理中です。少々お待ちください。");
    return;
  }

  processing = true;
  await say(":brain: 処理中...");

  // プロンプトをファイル経由で渡す（引用符の問題回避）
  const promptFile = path.join(PROJECT_DIR, ".slack-prompt.tmp");
  const fullPrompt = `${SYSTEM_CONTEXT}\n\n---\nユーザーからの指示:\n${prompt}`;
  fs.writeFileSync(promptFile, fullPrompt, "utf8");

  try {
    const cmd = `cat "${promptFile.replace(/\\/g, "/")}" | claude -p --output-format text --max-turns 5`;
    const result = execSync(cmd, {
      cwd: PROJECT_DIR,
      encoding: "utf8",
      timeout: 600000,
      maxBuffer: 2 * 1024 * 1024,
      shell: "bash",
      env: { ...process.env, FORCE_COLOR: "0", CLAUDECODE: "" },
    });

    const response = result.trim();
    if (!response) {
      await say("(応答なし)");
    } else if (response.length > 3900) {
      const chunks = splitMessage(response, 3900);
      for (const chunk of chunks) {
        await say(chunk);
      }
    } else {
      await say(response);
    }
  } catch (err) {
    const output = (err.stdout || "").trim();
    const error = (err.stderr || "").trim();

    if (output) {
      const chunks = splitMessage(output, 3900);
      for (const chunk of chunks) {
        await say(chunk);
      }
    } else {
      await say(`:x: エラー: ${error.slice(0, 500) || err.message}`);
    }
  } finally {
    // 一時ファイル削除
    try { fs.unlinkSync(promptFile); } catch (_) {}
    processing = false;
  }
}

// ---------- メッセージ分割 ----------
function splitMessage(text, maxLen) {
  const chunks = [];
  let remaining = text;
  while (remaining.length > 0) {
    if (remaining.length <= maxLen) {
      chunks.push(remaining);
      break;
    }
    let splitAt = remaining.lastIndexOf("\n", maxLen);
    if (splitAt < maxLen * 0.5) splitAt = maxLen;
    chunks.push(remaining.slice(0, splitAt));
    remaining = remaining.slice(splitAt).trimStart();
  }
  return chunks;
}

// ---------- メンション応答 → Claude Code実行 ----------
app.event("app_mention", async ({ event, say }) => {
  const text = event.text.replace(/<@[A-Z0-9]+>/g, "").trim();
  if (!text) {
    await say("メッセージを入力してください。Claude Codeと同じように指示できます。");
    return;
  }

  console.log(`[CLAUDE] ${new Date().toLocaleString("ja-JP")} | ${text}`);
  await runClaude(text, say);
});

// ---------- 起動 ----------
(async () => {
  await app.start();
  console.log("==========================================");
  console.log("  NURSE ROBBY (ナースロビー) - Claude Code Bridge");
  console.log("  Slack message = Claude Code input");
  console.log("  Socket Mode: Active");
  console.log(`  Channel: #平島claudecode`);
  console.log(`  Project: ${PROJECT_DIR}`);
  console.log("  Ctrl+C to stop");
  console.log("==========================================");

  try {
    await app.client.chat.postMessage({
      token: env.SLACK_BOT_TOKEN,
      channel: CHANNEL_ID,
      text: ":zap: *Claude Code Bridge* がオンラインになりました。\n`@平島claude code` にメンションするとClaude Codeが処理します。\n\n例:\n• `index.htmlのヒーローセクションを確認して`\n• `config.jsのブランド名を変更して`\n• `プロジェクトの状態を教えて`",
    });
  } catch (e) {
    console.log("起動通知エラー:", e.message);
  }
})();
