#!/bin/bash
# ==========================================================================
# ROBBY THE MATCH / Nurse Robby
# Weekly Content Planning & Generation v1.0
# cron: 0 6 * * 0 (Sunday 06:00)
#
# Purpose:
#   1. Analyze last week's content performance
#   2. Plan next week's content mix (7 posts)
#   3. Batch-generate all 7 posts via content_pipeline.py
#   4. Quality-review and auto-approve passing content
#   5. Send weekly content plan to Slack
#
# Dependencies:
#   - utils.sh (common functions)
#   - content_pipeline.py (--auto / --force / --status)
#   - sns_workflow.py (--status)
#   - slack_bridge.py (--send)
#   - posting_queue.json, content/stock.csv
# ==========================================================================

set -euo pipefail

source "$(dirname "$0")/utils.sh"
init_log "pdca_weekly_content"

SCRIPT_NAME="pdca_weekly_content"
AGENT_NAME="weekly_content_planner"
WEEKLY_TARGET=7

echo "[INFO] =============================================" >> "$LOG"
echo "[INFO] Weekly Content Planning v1.0 - $TODAY (Week $WEEK_NUM)" >> "$LOG"
echo "[INFO] =============================================" >> "$LOG"

# --- Agent state: running ---
update_agent_state "$AGENT_NAME" "running"

# --- Check for Slack instructions ---
check_instructions "$AGENT_NAME"

# --- Consume inter-agent tasks ---
TASKS=$(consume_agent_tasks "$AGENT_NAME")
echo "$TASKS" >> "$LOG"

# Track phases
PLAN_OK=true
GENERATE_OK=true
REVIEW_OK=true
REPORT_OK=true
TOTAL_GENERATED=0
TOTAL_APPROVED=0
TOTAL_REJECTED=0
ERRORS=""

# ===================================================================
# Phase 1: PLAN - Analyze last week and plan next week
# ===================================================================

echo "" >> "$LOG"
echo "[PHASE 1] ========== Weekly Planning ==========" >> "$LOG"

# Analyze last week's performance and current stock balance
WEEKLY_ANALYSIS=$(python3 -c "
import json, csv
from pathlib import Path
from datetime import datetime, timedelta

project = Path('$PROJECT_DIR')

# --- Last week's posting stats ---
qp = project / 'data' / 'posting_queue.json'
last_week_posts = []
this_week_start = datetime.now() - timedelta(days=7)

if qp.exists():
    with open(qp) as f:
        q = json.load(f)
    for post in q.get('posts', []):
        posted_at = post.get('posted_at', '')
        if posted_at:
            try:
                dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00').split('+')[0])
                if dt >= this_week_start:
                    last_week_posts.append(post)
            except (ValueError, TypeError):
                pass

last_week_count = len(last_week_posts)

# --- Current queue state ---
pending = sum(1 for p in q.get('posts', []) if p['status'] == 'pending') if qp.exists() else 0
ready = sum(1 for p in q.get('posts', []) if p['status'] == 'ready') if qp.exists() else 0
posted_total = sum(1 for p in q.get('posts', []) if p['status'] == 'posted') if qp.exists() else 0

# --- Stock distribution analysis ---
stock_path = project / 'content' / 'stock.csv'
stock_dist = {}
stock_total = 0
mix_ratios = {
    'あるある': 0.40, '転職': 0.25, '給与': 0.20, '紹介': 0.05, 'トレンド': 0.10
}

if stock_path.exists():
    with open(stock_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row.get('category', '')
            stock_dist[cat] = stock_dist.get(cat, 0) + 1
            stock_total += 1

# --- Determine optimal generation plan ---
# Calculate which categories are underrepresented
deficits = []
for cat, ratio in mix_ratios.items():
    current = stock_dist.get(cat, 0)
    current_ratio = current / stock_total if stock_total > 0 else 0
    deficit = ratio - current_ratio
    deficits.append({'category': cat, 'current': current, 'target_ratio': ratio,
                     'current_ratio': round(current_ratio, 3), 'deficit': round(deficit, 3)})

deficits.sort(key=lambda x: x['deficit'], reverse=True)

# Build generation plan: 7 posts distributed by deficit
plan = []
target_count = $WEEKLY_TARGET

# CTA 8:2 rule: 5-6 soft, 1-2 hard out of 7
soft_count = round(target_count * 0.8)
hard_count = target_count - soft_count

idx = 0
for i in range(target_count):
    cat = deficits[idx % len(deficits)]['category']
    cta = 'soft' if i < soft_count else 'hard'
    plan.append({'category': cat, 'cta_type': cta, 'slot': i + 1})
    idx += 1

# --- Performance insights (from agent memory) ---
insights = []
perf_path = project / 'data' / 'performance_analysis.json'
if perf_path.exists():
    try:
        with open(perf_path) as f:
            perf = json.load(f)
        best = perf.get('content_performance', {}).get('best_performing', [])
        if best:
            insights.append(f'Top performer: {best[0].get(\"content_id\", \"?\")}'
                          f' ({best[0].get(\"views\", \"?\")} views)')
        recs = perf.get('recommendations', [])
        if recs:
            insights.extend(recs[:3])
    except Exception:
        pass

result = {
    'last_week': {'posted': last_week_count},
    'queue': {'pending': pending, 'ready': ready, 'posted_total': posted_total},
    'stock': {'total': stock_total, 'distribution': stock_dist},
    'deficits': deficits,
    'plan': plan,
    'insights': insights,
    'soft_count': soft_count,
    'hard_count': hard_count,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
" 2>> "$LOG") || {
    echo "[ERROR] PHASE 1: Weekly analysis failed" >> "$LOG"
    PLAN_OK=false
    ERRORS="${ERRORS}\n- Weekly analysis failed"
}

echo "[PHASE 1] Analysis result:" >> "$LOG"
echo "$WEEKLY_ANALYSIS" >> "$LOG"

# Extract plan summary
LAST_WEEK_POSTED=$(echo "$WEEKLY_ANALYSIS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['last_week']['posted'])" 2>/dev/null || echo "?")
CURRENT_PENDING=$(echo "$WEEKLY_ANALYSIS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queue']['pending'])" 2>/dev/null || echo "0")
STOCK_TOTAL=$(echo "$WEEKLY_ANALYSIS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['stock']['total'])" 2>/dev/null || echo "0")
SOFT_COUNT=$(echo "$WEEKLY_ANALYSIS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['soft_count'])" 2>/dev/null || echo "5")
HARD_COUNT=$(echo "$WEEKLY_ANALYSIS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['hard_count'])" 2>/dev/null || echo "2")

echo "[PHASE 1] Last week posted: $LAST_WEEK_POSTED, Current pending: $CURRENT_PENDING, Stock: $STOCK_TOTAL" >> "$LOG"

# Calculate how many we actually need to generate
# If we already have enough pending, reduce generation count
ACTUAL_GENERATE=$WEEKLY_TARGET
if [ "$CURRENT_PENDING" -ge "$WEEKLY_TARGET" ]; then
    # Already have enough for next week, generate fewer to build buffer
    ACTUAL_GENERATE=3
    echo "[PHASE 1] Queue already has $CURRENT_PENDING pending. Generating $ACTUAL_GENERATE buffer posts." >> "$LOG"
elif [ "$CURRENT_PENDING" -gt 0 ]; then
    ACTUAL_GENERATE=$((WEEKLY_TARGET - CURRENT_PENDING + 2))  # +2 buffer
    if [ "$ACTUAL_GENERATE" -gt 10 ]; then
        ACTUAL_GENERATE=10
    fi
    echo "[PHASE 1] Adjusted generation: $ACTUAL_GENERATE posts (pending=$CURRENT_PENDING + buffer)" >> "$LOG"
fi

# ===================================================================
# Phase 2: GENERATE - Batch generate content
# ===================================================================

echo "" >> "$LOG"
echo "[PHASE 2] ========== Batch Content Generation ==========" >> "$LOG"
echo "[PHASE 2] Generating $ACTUAL_GENERATE posts..." >> "$LOG"

# Record pre-generation queue state
PRE_GEN_PENDING=$CURRENT_PENDING

# Run content pipeline with force count
python3 "$PROJECT_DIR/scripts/content_pipeline.py" --force "$ACTUAL_GENERATE" >> "$LOG" 2>&1
PIPELINE_EXIT=$?

if [ $PIPELINE_EXIT -ne 0 ]; then
    echo "[ERROR] PHASE 2: Content pipeline failed (exit=$PIPELINE_EXIT)" >> "$LOG"
    GENERATE_OK=false
    ERRORS="${ERRORS}\n- Content pipeline failed (exit $PIPELINE_EXIT)"
else
    echo "[PHASE 2] Content pipeline completed" >> "$LOG"
fi

# Calculate how many were actually generated
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
" 2>/dev/null || echo "$PRE_GEN_PENDING")

TOTAL_GENERATED=$((POST_GEN_PENDING - PRE_GEN_PENDING))
if [ "$TOTAL_GENERATED" -lt 0 ]; then
    TOTAL_GENERATED=0
fi
echo "[PHASE 2] Generated $TOTAL_GENERATED new posts (pending: $PRE_GEN_PENDING -> $POST_GEN_PENDING)" >> "$LOG"

# ===================================================================
# Phase 3: REVIEW - Quality review and auto-approve
# ===================================================================

echo "" >> "$LOG"
echo "[PHASE 3] ========== Quality Review & Auto-Approve ==========" >> "$LOG"

REVIEW_RESULT=$(python3 -c "
import json
from pathlib import Path

project = Path('$PROJECT_DIR')
qp = project / 'data' / 'posting_queue.json'

approved = 0
rejected = 0
issues = []

if qp.exists():
    with open(qp) as f:
        q = json.load(f)

    for post in q.get('posts', []):
        if post['status'] != 'pending':
            continue
        if post.get('verified', False):
            continue

        pid = post.get('id', '?')
        cid = post.get('content_id', '?')
        passed = True
        post_issues = []

        # Quality Gate 1: Caption exists and is reasonable length
        caption = post.get('caption', '')
        if len(caption) < 10:
            post_issues.append('caption too short')
            passed = False
        if len(caption) > 250:
            post_issues.append('caption too long')
            # Auto-fix: trim caption
            post['caption'] = caption[:200]

        # Quality Gate 2: Hashtags within limit
        hashtags = post.get('hashtags', [])
        if len(hashtags) > 5:
            # Auto-fix: trim to 5
            post['hashtags'] = hashtags[:5]
            post_issues.append(f'hashtags trimmed from {len(hashtags)} to 5')

        # Quality Gate 3: Slides directory exists
        slide_dir = post.get('slide_dir', '')
        if slide_dir:
            sd = Path(slide_dir) if Path(slide_dir).is_absolute() else project / slide_dir
            slides = sorted(sd.glob('slide_*.png')) if sd.exists() else []
            if len(slides) < 4:
                post_issues.append(f'insufficient slides ({len(slides)})')
                passed = False
        else:
            post_issues.append('no slide_dir')
            passed = False

        # Quality Gate 4: CTA type is valid
        cta = post.get('cta_type', '')
        if cta not in ('soft', 'hard'):
            post_issues.append(f'invalid cta_type: {cta}')
            post['cta_type'] = 'soft'  # default

        if passed:
            post['verified'] = True
            approved += 1
        else:
            rejected += 1
            issues.append(f'#{pid} ({cid}): {\" | \".join(post_issues)}')

    # Save updated queue
    q['updated'] = __import__('datetime').datetime.now().isoformat()
    with open(qp, 'w', encoding='utf-8') as f:
        json.dump(q, f, ensure_ascii=False, indent=2)

result = {
    'approved': approved,
    'rejected': rejected,
    'issues': issues,
}
print(json.dumps(result, ensure_ascii=False))
" 2>> "$LOG") || {
    echo "[ERROR] PHASE 3: Quality review failed" >> "$LOG"
    REVIEW_OK=false
    ERRORS="${ERRORS}\n- Quality review failed"
    REVIEW_RESULT='{"approved":0,"rejected":0,"issues":[]}'
}

echo "[PHASE 3] Review result: $REVIEW_RESULT" >> "$LOG"

TOTAL_APPROVED=$(echo "$REVIEW_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['approved'])" 2>/dev/null || echo "0")
TOTAL_REJECTED=$(echo "$REVIEW_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['rejected'])" 2>/dev/null || echo "0")
REVIEW_ISSUES=$(echo "$REVIEW_RESULT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
issues = d.get('issues', [])
if issues:
    for i in issues[:10]:
        print(f'  - {i}')
else:
    print('  All content passed quality gates')
" 2>/dev/null || echo "  Review data unavailable")

echo "[PHASE 3] Approved: $TOTAL_APPROVED, Rejected: $TOTAL_REJECTED" >> "$LOG"

# ===================================================================
# Phase 4: REPORT - Send weekly content plan to Slack
# ===================================================================

echo "" >> "$LOG"
echo "[PHASE 4] ========== Weekly Report ==========" >> "$LOG"

# Build next week's schedule preview
SCHEDULE_PREVIEW=$(python3 -c "
import json
from pathlib import Path
from datetime import datetime, timedelta

project = Path('$PROJECT_DIR')
qp = project / 'data' / 'posting_queue.json'

if qp.exists():
    with open(qp) as f:
        q = json.load(f)
    pending = [p for p in q['posts'] if p['status'] in ('pending', 'ready') and p.get('verified', False)]
    # Also include unverified pending as backup
    unverified = [p for p in q['posts'] if p['status'] == 'pending' and not p.get('verified', False)]

    lines = []
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    today = datetime.now()
    # Next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)

    all_ready = pending + unverified
    for i, day_name in enumerate(days):
        date = next_monday + timedelta(days=i)
        date_str = date.strftime('%m/%d')
        if i < len(all_ready):
            p = all_ready[i]
            cid = p.get('content_id', '?')
            cta = p.get('cta_type', '?')
            verified_mark = 'v' if p.get('verified') else '?'
            caption_preview = (p.get('caption', '')[:40] + '...') if len(p.get('caption', '')) > 40 else p.get('caption', '')
            lines.append(f'{day_name} {date_str}: [{verified_mark}] #{p[\"id\"]} {cid} ({cta}) {caption_preview}')
        else:
            lines.append(f'{day_name} {date_str}: [EMPTY] No content assigned')

    scheduled = min(len(all_ready), 7)
    lines.append(f'')
    lines.append(f'Scheduled: {scheduled}/7 days covered')
    if scheduled < 7:
        lines.append(f'WARNING: {7 - scheduled} days without content')

    print('\\n'.join(lines))
else:
    print('Queue file not found')
" 2>/dev/null || echo "Schedule preview unavailable")

# Get performance insights
INSIGHTS_TEXT=$(echo "$WEEKLY_ANALYSIS" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    insights = d.get('insights', [])
    if insights:
        for i in insights:
            print(f'  - {i}')
    else:
        print('  No performance data yet')
except:
    print('  Insights unavailable')
" 2>/dev/null || echo "  Insights unavailable")

# Stock distribution text
STOCK_DIST_TEXT=$(echo "$WEEKLY_ANALYSIS" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    deficits = d.get('deficits', [])
    for item in deficits:
        cat = item['category']
        current = item['current']
        target_pct = item['target_ratio'] * 100
        current_pct = item['current_ratio'] * 100
        deficit = item['deficit']
        indicator = 'LOW' if deficit > 0.1 else ('HIGH' if deficit < -0.1 else 'OK')
        print(f'  {cat}: {current} posts ({current_pct:.0f}% / target {target_pct:.0f}%) [{indicator}]')
except:
    print('  Distribution data unavailable')
" 2>/dev/null || echo "  Distribution data unavailable")

# Build comprehensive Slack report
SLACK_REPORT="Weekly Content Plan - Week $WEEK_NUM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Last Week Summary]
  Posts published: $LAST_WEEK_POSTED
  Current queue: $POST_GEN_PENDING pending

[This Week's Generation]
  Generated: $TOTAL_GENERATED new posts
  Quality approved: $TOTAL_APPROVED
  Quality rejected: $TOTAL_REJECTED
  CTA mix: $SOFT_COUNT soft / $HARD_COUNT hard

[Stock Distribution]
$STOCK_DIST_TEXT

[Next Week Schedule]
$SCHEDULE_PREVIEW

[Quality Review]
$REVIEW_ISSUES

[Performance Insights]
$INSIGHTS_TEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Append errors if any
if [ -n "$ERRORS" ]; then
    SLACK_REPORT="${SLACK_REPORT}

[ERRORS]
$(echo -e "$ERRORS")"
fi

echo "[PHASE 4] Sending Slack report..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/slack_bridge.py" --send "$SLACK_REPORT" >> "$LOG" 2>&1 || {
    echo "[WARN] PHASE 4: Slack bridge failed, trying fallback" >> "$LOG"
    slack_notify "$SLACK_REPORT"
}

# Also send structured report if available
slack_report_structured "content" || true

# ===================================================================
# Finalize
# ===================================================================

echo "" >> "$LOG"
echo "[FINAL] ========== Finalization ==========" >> "$LOG"

# Update agent memory with this week's generation stats
write_agent_memory "$AGENT_NAME" "lastWeeklyRun" "$TODAY"
write_agent_memory "$AGENT_NAME" "lastGeneratedCount" "$TOTAL_GENERATED"
write_agent_memory "$AGENT_NAME" "lastApprovedCount" "$TOTAL_APPROVED"

# Update shared context
write_shared_context "weeklyContentPlan" "Week${WEEK_NUM}: generated=${TOTAL_GENERATED}, approved=${TOTAL_APPROVED}, rejected=${TOTAL_REJECTED}"
write_shared_context "lastWeeklyContentRun" "$TODAY"

# Update progress log
update_progress "$SCRIPT_NAME" "Weekly Content Plan (Week $WEEK_NUM):
  Last week posted: $LAST_WEEK_POSTED
  Generated this run: $TOTAL_GENERATED
  Quality approved: $TOTAL_APPROVED / rejected: $TOTAL_REJECTED
  Queue pending: $POST_GEN_PENDING
  Stock total: $STOCK_TOTAL"

# Determine final state
if [ "$GENERATE_OK" == "true" ] && [ "$REVIEW_OK" == "true" ] && [ "$TOTAL_GENERATED" -gt 0 ]; then
    update_agent_state "$AGENT_NAME" "completed"
    echo "[INFO] Weekly content planning completed successfully" >> "$LOG"
elif [ "$TOTAL_GENERATED" -eq 0 ] && [ "$GENERATE_OK" == "true" ]; then
    # Pipeline ran but generated nothing (possible if Claude CLI is down)
    handle_failure "$AGENT_NAME" "Pipeline ran but generated 0 posts. Check Claude CLI availability."
else
    handle_failure "$AGENT_NAME" "Weekly content planning had issues: GEN=$GENERATE_OK REV=$REVIEW_OK generated=$TOTAL_GENERATED"
fi

# Update STATE.md timestamp
update_state "Weekly Content Plan"

# git sync (commit generated content)
git_sync "weekly-content: Week${WEEK_NUM} content plan ($TOTAL_GENERATED generated, $TOTAL_APPROVED approved)"

echo "" >> "$LOG"
echo "=== [$TODAY $NOW] $SCRIPT_NAME completed ===" >> "$LOG"
