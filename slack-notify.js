// ========================================
// ナースロビー - Slack通知ユーティリティ
// プロジェクト進捗・指示受付用
// ========================================
// Usage: node slack-notify.js [command]
//   send "message"  - メッセージ送信
//   status          - プロジェクト状態送信
//   read            - 最新メッセージ読み取り
//   listen          - メッセージ監視（5秒ごと）

const https = require("https");
const fs = require("fs");
const path = require("path");

// .envから読み込み
const envPath = path.join(__dirname, "slack-bot.env");
const envContent = fs.readFileSync(envPath, "utf8");
const env = {};
envContent.split("\n").forEach((line) => {
  const [key, ...vals] = line.split("=");
  if (key && vals.length) env[key.trim()] = vals.join("=").trim();
});

const BOT_TOKEN = env.SLACK_BOT_TOKEN;
const CHANNEL_ID = "C09A7U4TV4G"; // 平島claudecode

// ---------- Slack API ----------
function slackAPI(method, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const options = {
      hostname: "slack.com",
      path: `/api/${method}`,
      method: "POST",
      headers: {
        Authorization: `Bearer ${BOT_TOKEN}`,
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": Buffer.byteLength(data),
      },
    };
    const req = https.request(options, (res) => {
      let chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        try {
          resolve(JSON.parse(Buffer.concat(chunks).toString()));
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

// ---------- メッセージ送信 ----------
async function sendMessage(text) {
  const result = await slackAPI("chat.postMessage", {
    channel: CHANNEL_ID,
    text: text,
  });
  if (result.ok) {
    console.log("[OK] Message sent:", result.ts);
  } else {
    console.error("[ERROR]", result.error);
  }
  return result;
}

// ---------- Block Kit メッセージ送信 ----------
async function sendBlocks(text, blocks) {
  const result = await slackAPI("chat.postMessage", {
    channel: CHANNEL_ID,
    text: text,
    blocks: blocks,
  });
  if (result.ok) {
    console.log("[OK] Block message sent:", result.ts);
  } else {
    console.error("[ERROR]", result.error);
  }
  return result;
}

// ---------- プロジェクト状態送信 ----------
async function sendStatus() {
  const blocks = [
    {
      type: "header",
      text: { type: "plain_text", text: "ナースロビー - Project Status" },
    },
    { type: "divider" },
    {
      type: "section",
      text: {
        type: "mrkdwn",
        text:
          "*Phase 1: LP / MVP*\n" +
          ":white_check_mark: LP\u5236\u4f5c\u5b8c\u4e86\uff08\u6700\u5148\u7aefUI\u5b9f\u88c5\u6e08\u307f\uff09\n" +
          ":white_check_mark: \u30b3\u30d4\u30fc\u30e9\u30a4\u30c6\u30a3\u30f3\u30b0\u6539\u5584\u6e08\u307f\n" +
          ":white_check_mark: AI\u30c1\u30e3\u30c3\u30c8\u30dc\u30c3\u30c8UI\u5b9f\u88c5\u6e08\u307f\n" +
          ":white_check_mark: Slack/Sheets\u9023\u643aAPI\u69cb\u7bc9\u6e08\u307f\n" +
          ":white_check_mark: \u6cd5\u7684\u30da\u30fc\u30b8\u5b8c\u6210\n" +
          ":white_check_mark: \u30c7\u30d3\u30eb\u30ba\u30a2\u30c9\u30dc\u30b1\u30a4\u30c8\u30ec\u30d3\u30e5\u30fc\u5b8c\u4e86",
      },
    },
    { type: "divider" },
    {
      type: "section",
      text: {
        type: "mrkdwn",
        text:
          "*\u6b21\u306e\u30b9\u30c6\u30c3\u30d7:*\n" +
          ":point_right: Cloudflare Workers\u30c7\u30d7\u30ed\u30a4\n" +
          ":point_right: Slack Webhook URL\u8a2d\u5b9a\n" +
          ":point_right: OGP\u753b\u50cf\u4f5c\u6210\n" +
          ":point_right: \u5b9f\u30c7\u30fc\u30bf\u5165\u529b\uff08\u8a31\u53ef\u756a\u53f7\u30fb\u9023\u7d61\u5148\uff09",
      },
    },
    {
      type: "context",
      elements: [
        {
          type: "mrkdwn",
          text: `:clock3: Updated: ${new Date().toLocaleString("ja-JP")}`,
        },
      ],
    },
  ];

  return sendBlocks("ナースロビー - Project Status Update", blocks);
}

// ---------- メッセージ読み取り ----------
async function readMessages(limit = 10) {
  const result = await slackAPI("conversations.history", {
    channel: CHANNEL_ID,
    limit: limit,
  });

  if (!result.ok) {
    console.error("[ERROR]", result.error);
    return [];
  }

  const messages = result.messages.reverse();
  console.log(`\n--- Latest ${messages.length} messages ---\n`);

  messages.forEach((msg) => {
    const time = new Date(parseFloat(msg.ts) * 1000).toLocaleString("ja-JP");
    const user = msg.bot_id ? "[BOT]" : `[USER:${msg.user}]`;
    console.log(`${time} ${user}`);
    console.log(`  ${msg.text || "(no text)"}\n`);
  });

  return messages;
}

// ---------- メッセージ監視 ----------
async function listen(interval = 5000) {
  let lastTs = (Date.now() / 1000).toFixed(6);
  console.log("[LISTEN] Watching for new messages... (Ctrl+C to stop)\n");

  const check = async () => {
    try {
      const result = await slackAPI("conversations.history", {
        channel: CHANNEL_ID,
        oldest: lastTs,
        limit: 10,
      });

      if (result.ok && result.messages && result.messages.length > 0) {
        const newMsgs = result.messages
          .filter((m) => !m.bot_id)
          .reverse();

        newMsgs.forEach((msg) => {
          const time = new Date(parseFloat(msg.ts) * 1000).toLocaleString("ja-JP");
          console.log(`\n[NEW] ${time} User:${msg.user}`);
          console.log(`  ${msg.text}`);
          lastTs = msg.ts;
        });
      }
    } catch (e) {
      console.error("[ERROR]", e.message);
    }
  };

  setInterval(check, interval);
}

// ---------- CLI ----------
const args = process.argv.slice(2);
const command = args[0] || "status";

(async () => {
  switch (command) {
    case "send":
      const msg = args.slice(1).join(" ") || "Hello from Claude Code!";
      await sendMessage(msg);
      break;
    case "status":
      await sendStatus();
      break;
    case "read":
      await readMessages(parseInt(args[1]) || 10);
      break;
    case "listen":
      await listen(parseInt(args[1]) || 5000);
      break;
    default:
      console.log("Usage: node slack-notify.js [send|status|read|listen]");
  }
})();
