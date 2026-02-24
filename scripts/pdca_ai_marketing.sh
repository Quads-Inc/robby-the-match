#!/bin/bash
# ==========================================================================
# ROBBY THE MATCH / Nurse Robby
# Autonomous AI Marketing PDCA Loop v1.0
# cron: 0 6 * * * (daily at 06:00, before manual review window)
#
# PLAN:  Analyze queue state, decide content generation needs
# DO:    Generate content (carousel images + captions) via content_pipeline
# CHECK: Review quality, verify slides, detect issues
# ACT:   Prepare today's post, send Slack report, update agent state
#
# Dependencies:
#   - utils.sh (common functions)
#   - content_pipeline.py (--auto / --force / --status)
#   - sns_workflow.py (--prepare-next / --status)
#   - slack_bridge.py (--send)
#   - posting_queue.json (queue data)
#   - content/stock.csv (content stock)
# ==========================================================================

set -euo pipefail

source "$(dirname "$0")/utils.sh"
init_log "pdca_ai_marketing"

SCRIPT_NAME="pdca_ai_marketing"
AGENT_NAME="ai_marketing_orchestrator"

echo "[INFO] =============================================" >> "$LOG"
echo "[INFO] AI Marketing PDCA Loop v1.0 - $TODAY $NOW" >> "$LOG"
echo "[INFO] =============================================" >> "$LOG"

# --- Agent state: running ---
update_agent_state "$AGENT_NAME" "running"

# --- Check for Slack instructions ---
check_instructions "$AGENT_NAME"

# --- Consume any inter-agent tasks ---
TASKS=$(consume_agent_tasks "$AGENT_NAME")
echo "$TASKS" >> "$LOG"

# Track overall success/failure
PLAN_OK=true
DO_OK=true
CHECK_OK=true
ACT_OK=true

ERRORS=""
WARNINGS=""

# ===================================================================
# PLAN: Analyze current queue and stock state
# ===================================================================

echo "" >> "$LOG"
echo "[PLAN] ========== PLAN Phase ==========" >> "$LOG"

# Gather queue statistics
QUEUE_STATS=$(python3 -c "
import json, sys
from pathlib import Path

project = Path('$PROJECT_DIR')
queue_path = project / 'data' / 'posting_queue.json'
stock_path = project / 'content' / 'stock.csv'

# Queue stats
if queue_path.exists():
    with open(queue_path) as f:
        q = json.load(f)
    posts = q.get('posts', [])
    pending = sum(1 for p in posts if p['status'] == 'pending')
    ready = sum(1 for p in posts if p['status'] == 'ready')
    posted = sum(1 for p in posts if p['status'] == 'posted')
    failed = sum(1 for p in posts if p['status'] == 'failed')
    total = len(posts)
else:
    pending = ready = posted = failed = total = 0

# Stock stats
import csv
stock_dist = {}
mix_ratios = {'aruaru': 0.40, 'career': 0.25, 'salary': 0.20, 'service': 0.05, 'trend': 0.10}
# Map Japanese category names to English for consistent handling
cat_map = {'あるある': 'aruaru', '転職': 'career', '給与': 'salary', '紹介': 'service', 'トレンド': 'trend'}
stock_total = 0
if stock_path.exists():
    with open(stock_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row.get('category', '')
            mapped = cat_map.get(cat, cat)
            stock_dist[mapped] = stock_dist.get(mapped, 0) + 1
            stock_total += 1

# Content type distribution for queue posts (using content_type or heuristic)
type_counts = {}
for p in (q.get('posts', []) if queue_path.exists() else []):
    ct = p.get('content_type', p.get('cta_type', 'unknown'))
    type_counts[ct] = type_counts.get(ct, 0) + 1

# Determine generation need
need_generate = max(0, 7 - pending) if pending < 7 else 0

# Output as structured JSON
result = {
    'queue': {'pending': pending, 'ready': ready, 'posted': posted, 'failed': failed, 'total': total},
    'stock': {'total': stock_total, 'distribution': stock_dist},
    'need_generate': need_generate,
    'queue_healthy': pending >= 3,
}
print(json.dumps(result, ensure_ascii=False))
" 2>> "$LOG") || {
    echo "[ERROR] PLAN: Queue analysis failed" >> "$LOG"
    PLAN_OK=false
    QUEUE_STATS='{"queue":{"pending":0,"ready":0,"posted":0,"failed":0,"total":0},"stock":{"total":0,"distribution":{}},"need_generate":7,"queue_healthy":false}'
}

echo "[PLAN] Queue stats: $QUEUE_STATS" >> "$LOG"

# Extract values for later use
PENDING=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue']['pending'])" 2>/dev/null || echo "0")
READY=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue']['ready'])" 2>/dev/null || echo "0")
POSTED=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue']['posted'])" 2>/dev/null || echo "0")
FAILED=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue']['failed'])" 2>/dev/null || echo "0")
TOTAL=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue']['total'])" 2>/dev/null || echo "0")
NEED_GENERATE=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['need_generate'])" 2>/dev/null || echo "0")
QUEUE_HEALTHY=$(echo "$QUEUE_STATS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue_healthy'])" 2>/dev/null || echo "False")

echo "[PLAN] Pending: $PENDING, Ready: $READY, Posted: $POSTED, Failed: $FAILED" >> "$LOG"
echo "[PLAN] Need to generate: $NEED_GENERATE posts" >> "$LOG"

# Check for emergency tasks from other agents
FORCE_COUNT=0
if echo "$TASKS" | grep -q "emergency_generate"; then
    FORCE_COUNT=10
    echo "[PLAN] Emergency generation task detected -> force 10 posts" >> "$LOG"
elif echo "$TASKS" | grep -q "generate_batch"; then
    FORCE_COUNT=7
    echo "[PLAN] Batch generation task detected -> force 7 posts" >> "$LOG"
fi

# ===================================================================
# DO: Generate content via content_pipeline.py
# ===================================================================

echo "" >> "$LOG"
echo "[DO] ========== DO Phase ==========" >> "$LOG"

GENERATED_COUNT=0
GENERATION_FAILED=0

if [ "$FORCE_COUNT" -gt 0 ]; then
    echo "[DO] Force generating $FORCE_COUNT posts (inter-agent task)" >> "$LOG"
    python3 "$PROJECT_DIR/scripts/content_pipeline.py" --force "$FORCE_COUNT" >> "$LOG" 2>&1
    PIPELINE_EXIT=$?
elif [ "$NEED_GENERATE" -gt 0 ]; then
    echo "[DO] Auto-generating content (need $NEED_GENERATE posts)" >> "$LOG"
    python3 "$PROJECT_DIR/scripts/content_pipeline.py" --auto >> "$LOG" 2>&1
    PIPELINE_EXIT=$?
else
    echo "[DO] Queue is healthy ($PENDING pending). Skipping generation." >> "$LOG"
    PIPELINE_EXIT=0
fi

if [ "${PIPELINE_EXIT:-0}" -ne 0 ]; then
    echo "[ERROR] DO: content_pipeline.py failed (exit=$PIPELINE_EXIT)" >> "$LOG"
    DO_OK=false
    ERRORS="${ERRORS}\n- Content pipeline failed (exit $PIPELINE_EXIT)"
else
    echo "[DO] Content pipeline completed successfully" >> "$LOG"
fi

# Re-read queue stats after generation
POST_GEN_PENDING=$(python3 -c "
import json
from pathlib import Path
qp = Path('$PROJECT_DIR') / 'data' / 'posting_queue.json'
if qp.exists():
    with open(qp) as f:
        q = json.load(f)
    print(sum(1 for p in q['posts'] if p['status'] == 'pending'))
else:
    print(0)
" 2>/dev/null || echo "$PENDING")

if [ "$POST_GEN_PENDING" -gt "$PENDING" ]; then
    GENERATED_COUNT=$((POST_GEN_PENDING - PENDING))
    echo "[DO] Generated $GENERATED_COUNT new posts (pending: $PENDING -> $POST_GEN_PENDING)" >> "$LOG"
fi

# ===================================================================
# CHECK: Quality review of pending content
# ===================================================================

echo "" >> "$LOG"
echo "[CHECK] ========== CHECK Phase ==========" >> "$LOG"

# Check 1: Verify slides exist for all pending posts
QUALITY_REPORT=$(python3 -c "
import json
from pathlib import Path

project = Path('$PROJECT_DIR')
qp = project / 'data' / 'posting_queue.json'
issues = []
stats = {'slides_ok': 0, 'slides_missing': 0, 'caption_ok': 0, 'caption_issue': 0}

if qp.exists():
    with open(qp) as f:
        q = json.load(f)
    for post in q.get('posts', []):
        if post['status'] not in ('pending', 'ready'):
            continue
        pid = post.get('id', '?')
        cid = post.get('content_id', '?')

        # Check slides
        slide_dir = post.get('slide_dir', '')
        if slide_dir:
            sd = Path(slide_dir) if Path(slide_dir).is_absolute() else project / slide_dir
            slides = sorted(sd.glob('slide_*.png')) if sd.exists() else []
            if len(slides) >= 4:
                stats['slides_ok'] += 1
            else:
                stats['slides_missing'] += 1
                issues.append(f'Post #{pid} ({cid}): slides missing ({len(slides)} found)')
        else:
            stats['slides_missing'] += 1
            issues.append(f'Post #{pid} ({cid}): no slide_dir set')

        # Check caption
        caption = post.get('caption', '')
        if len(caption) < 10:
            stats['caption_issue'] += 1
            issues.append(f'Post #{pid} ({cid}): caption too short ({len(caption)} chars)')
        elif len(caption) > 200:
            stats['caption_issue'] += 1
            issues.append(f'Post #{pid} ({cid}): caption too long ({len(caption)} chars)')
        else:
            stats['caption_ok'] += 1

        # Check hashtags
        hashtags = post.get('hashtags', [])
        if len(hashtags) > 5:
            issues.append(f'Post #{pid} ({cid}): too many hashtags ({len(hashtags)})')

result = {'stats': stats, 'issues': issues, 'issue_count': len(issues)}
print(json.dumps(result, ensure_ascii=False))
" 2>> "$LOG") || {
    echo "[ERROR] CHECK: Quality review failed" >> "$LOG"
    CHECK_OK=false
    QUALITY_REPORT='{"stats":{},"issues":[],"issue_count":0}'
}

echo "[CHECK] Quality report: $QUALITY_REPORT" >> "$LOG"

ISSUE_COUNT=$(echo "$QUALITY_REPORT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['issue_count'])" 2>/dev/null || echo "0")

if [ "$ISSUE_COUNT" -gt 0 ]; then
    echo "[CHECK] Found $ISSUE_COUNT quality issues" >> "$LOG"
    WARNINGS="${WARNINGS}\n- $ISSUE_COUNT quality issues found (see log for details)"
else
    echo "[CHECK] No quality issues found" >> "$LOG"
fi

# Check 2: Content mix balance analysis
MIX_REPORT=$(python3 -c "
import json
from pathlib import Path

project = Path('$PROJECT_DIR')
qp = project / 'data' / 'posting_queue.json'

target_ratios = {
    'aruaru': 0.40, 'career': 0.25, 'salary': 0.20, 'service': 0.05, 'trend': 0.10
}
# Map content_type values
type_map = {
    'aruaru': 'aruaru', 'career': 'career', 'salary': 'salary',
    'service': 'service', 'trend': 'trend',
    'soft': 'unknown', 'hard': 'unknown',
}
type_counts = {k: 0 for k in target_ratios}
total = 0

if qp.exists():
    with open(qp) as f:
        q = json.load(f)
    for post in q.get('posts', []):
        ct = post.get('content_type', '')
        mapped = type_map.get(ct, ct)
        if mapped in type_counts:
            type_counts[mapped] += 1
        total += 1

mix_lines = []
for cat, target in target_ratios.items():
    actual = type_counts.get(cat, 0)
    actual_pct = (actual / total * 100) if total > 0 else 0
    target_pct = target * 100
    deviation = abs(actual_pct - target_pct)
    status = 'OK' if deviation < 15 else 'IMBALANCED'
    mix_lines.append(f'{cat}: {actual_pct:.0f}% (target {target_pct:.0f}%) [{status}]')

print('\\n'.join(mix_lines))
" 2>/dev/null || echo "Mix analysis unavailable")

echo "[CHECK] Content mix balance:" >> "$LOG"
echo "$MIX_REPORT" >> "$LOG"

# ===================================================================
# ACT: Prepare today's post and send Slack report
# ===================================================================

echo "" >> "$LOG"
echo "[ACT] ========== ACT Phase ==========" >> "$LOG"

# Act 1: Prepare next post for Buffer upload
echo "[ACT] Preparing next post..." >> "$LOG"
PREPARE_OUTPUT=$(python3 "$PROJECT_DIR/scripts/sns_workflow.py" --prepare-next 2>&1) || true
PREPARE_EXIT=$?
echo "$PREPARE_OUTPUT" >> "$LOG"

TODAYS_POST="No post prepared"
if [ $PREPARE_EXIT -eq 0 ]; then
    # Extract post info from output
    TODAYS_POST=$(echo "$PREPARE_OUTPUT" | grep -E "投稿準備|content_id|#[0-9]+" | head -5 || echo "Post preparation completed")
    echo "[ACT] Post preparation successful" >> "$LOG"
else
    echo "[WARN] ACT: Post preparation returned non-zero (exit=$PREPARE_EXIT)" >> "$LOG"
    # Check if it's just "no posts remaining" vs actual error
    if echo "$PREPARE_OUTPUT" | grep -q "キューに残りなし\|全投稿完了"; then
        TODAYS_POST="All posts completed. Queue empty."
        echo "[ACT] Queue is empty, no posts to prepare" >> "$LOG"
    else
        WARNINGS="${WARNINGS}\n- Post preparation issue (exit $PREPARE_EXIT)"
    fi
fi

# Act 2: Build Slack report
echo "[ACT] Building Slack report..." >> "$LOG"

# Get today's scheduled post preview (if ready)
POST_PREVIEW=$(python3 -c "
import json
from pathlib import Path

project = Path('$PROJECT_DIR')
qp = project / 'data' / 'posting_queue.json'

if qp.exists():
    with open(qp) as f:
        q = json.load(f)
    # Find next ready post
    for post in q.get('posts', []):
        if post['status'] == 'ready':
            cid = post.get('content_id', '?')
            caption = post.get('caption', '')[:80]
            hashtags = ' '.join(post.get('hashtags', []))
            cta = post.get('cta_type', '?')
            print(f'#{post[\"id\"]} {cid}')
            print(f'Caption: {caption}...')
            print(f'Tags: {hashtags}')
            print(f'CTA: {cta}')
            break
    else:
        print('No ready posts. Run --prepare-next first.')
else:
    print('Queue file not found.')
" 2>/dev/null || echo "Preview unavailable")

# Compile quality issues text
QUALITY_ISSUES_TEXT=$(echo "$QUALITY_REPORT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    issues = d.get('issues', [])
    if issues:
        for i in issues[:5]:
            print(f'  - {i}')
        if len(issues) > 5:
            print(f'  ... and {len(issues) - 5} more')
    else:
        print('  No issues found')
except:
    print('  Check unavailable')
" 2>/dev/null || echo "  Check unavailable")

# Determine overall status emoji/text
OVERALL_STATUS="Healthy"
if [ "$DO_OK" != "true" ] || [ "$CHECK_OK" != "true" ]; then
    OVERALL_STATUS="Issues Detected"
fi
if [ "$QUEUE_HEALTHY" == "False" ] && [ "$POST_GEN_PENDING" -lt 3 ]; then
    OVERALL_STATUS="Queue Low"
fi

# Send structured Slack report
SLACK_MESSAGE="AI Marketing PDCA Daily Report [$TODAY]
━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: $OVERALL_STATUS

[Queue Status]
  Pending: ${POST_GEN_PENDING:-$PENDING}
  Ready: $READY
  Posted: $POSTED
  Failed: $FAILED
  Total: $TOTAL
  Generated today: $GENERATED_COUNT

[Content Mix Balance]
$MIX_REPORT

[Today's Post Preview]
$POST_PREVIEW

[Quality Check ($ISSUE_COUNT issues)]
$QUALITY_ISSUES_TEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Append errors/warnings if any
if [ -n "$ERRORS" ]; then
    SLACK_MESSAGE="${SLACK_MESSAGE}

[ERRORS]
$(echo -e "$ERRORS")"
fi

if [ -n "$WARNINGS" ]; then
    SLACK_MESSAGE="${SLACK_MESSAGE}

[WARNINGS]
$(echo -e "$WARNINGS")"
fi

echo "[ACT] Sending Slack report..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/slack_bridge.py" --send "$SLACK_MESSAGE" >> "$LOG" 2>&1 || {
    echo "[WARN] ACT: Slack report send failed, trying notify_slack fallback" >> "$LOG"
    slack_notify "$SLACK_MESSAGE"
}

# Act 3: Update agent state and shared context
write_shared_context "lastMarketingPDCA" "$TODAY $NOW"
write_shared_context "queuePending" "$POST_GEN_PENDING"
write_shared_context "dailyGeneratedCount" "$GENERATED_COUNT"

# Act 4: Update progress log
update_progress "$SCRIPT_NAME" "AI Marketing PDCA:
  Queue: pending=$POST_GEN_PENDING ready=$READY posted=$POSTED failed=$FAILED
  Generated today: $GENERATED_COUNT
  Quality issues: $ISSUE_COUNT
  Status: $OVERALL_STATUS"

# Act 5: Queue depletion warning
if [ "${POST_GEN_PENDING:-0}" -lt 3 ]; then
    echo "[WARN] Queue critically low (${POST_GEN_PENDING} pending)!" >> "$LOG"
    create_agent_task "$AGENT_NAME" "content_creator" "emergency_generate" "Queue critically low (${POST_GEN_PENDING} pending). Emergency generation needed."
    slack_notify "[AI Marketing] Queue critically low: ${POST_GEN_PENDING} pending posts. Emergency generation requested."
fi

# ===================================================================
# Finalize
# ===================================================================

# Determine final agent state
if [ "$DO_OK" == "true" ] && [ "$CHECK_OK" == "true" ]; then
    update_agent_state "$AGENT_NAME" "completed"
    echo "[INFO] AI Marketing PDCA completed successfully" >> "$LOG"
else
    handle_failure "$AGENT_NAME" "PDCA completed with issues: DO=$DO_OK CHECK=$CHECK_OK"
    echo "[WARN] AI Marketing PDCA completed with issues" >> "$LOG"
fi

# Update STATE.md timestamp
update_state "AI Marketing PDCA"

echo "" >> "$LOG"
echo "=== [$TODAY $NOW] $SCRIPT_NAME completed ===" >> "$LOG"
