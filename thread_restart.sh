#!/bin/bash

# thread_restart.sh - AI Agent Thread Restart Protocol
# Prepares context for new agent thread by reading status, git state, and next steps
# Usage: ./thread_restart.sh [--update] [--session-id <id>]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
STATUS_FILE="$PROJECT_ROOT/AGENT_STATUS.yaml"
SESSION_LOG="$PROJECT_ROOT/.agent/session_logs/$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
UPDATE_STATUS=false
SESSION_ID="session_$(date +%Y%m%d_%H%M%S)"
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --update)
            UPDATE_STATUS=true
            shift
            ;;
        --session-id)
            SESSION_ID="$2"
            shift 2
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ "$HELP" = true ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "AI Agent Thread Restart Protocol"
    echo ""
    echo "Options:"
    echo "  --update           Update AGENT_STATUS.yaml with new timestamps"
    echo "  --session-id ID    Use custom session ID (default: auto-generated)"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "Protocol:"
    echo "  1. Read AGENT_STATUS.yaml for current state"
    echo "  2. Check git status and recent commits"
    echo "  3. Display current task and next steps"
    echo "  4. (Optional) Update status file with new session"
    echo "  5. Output restart summary for agent"
    exit 0
fi

# Ensure session log directory exists
mkdir -p "$(dirname "$SESSION_LOG")"

# Log function
log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

    case "$level" in
        "INFO") echo -e "${GREEN}[INFO]${NC} $message" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "DEBUG") echo -e "${CYAN}[DEBUG]${NC} $message" ;;
        *) echo -e "[$level] $message" ;;
    esac

    # Also log to file
    echo "[$timestamp] [$level] $message" >> "$SESSION_LOG"
}

# Function to extract YAML value
get_yaml_value() {
    local key="$1"
    grep "^${key}:" "$STATUS_FILE" | head -1 | sed 's/^[^:]*:[[:space:]]*//'
}

# Function to extract multi-line YAML array
get_yaml_array() {
    local key="$1"
    sed -n "/^${key}:/,/^[^[:space:]]/p" "$STATUS_FILE" | tail -n +2 | grep -E '^[[:space:]]*-' | sed 's/^[[:space:]]*-[[:space:]]*//'
}

# Function to extract current task section
get_current_task() {
    sed -n '/^current_work:/,/^[^[:space:]]/p' "$STATUS_FILE" | grep -v '^current_work:'
}

# Start session
log "INFO" "================================================"
log "INFO" "AI AGENT THREAD RESTART PROTOCOL"
log "INFO" "Session ID: $SESSION_ID"
log "INFO" "Timestamp: $(date)"
log "INFO" "================================================"

# Check if status file exists
if [ ! -f "$STATUS_FILE" ]; then
    log "ERROR" "AGENT_STATUS.yaml not found at $STATUS_FILE"
    log "INFO" "Creating initial AGENT_STATUS.yaml..."

    cat > "$STATUS_FILE" << 'EOF'
# AGENT_STATUS.yaml - AI Agent Work Status & Context Tracking
# Version: 1.0.0
# Created: $(date -Iseconds)
# Last session: $(date -Iseconds)

metadata:
  agent: "DeepSeek Reasoner"
  project: "Crypto Exchange API Catalog Expansion"
  goal: "Expand from 11 to 25 cryptocurrency exchanges with unified field mapping"
  phase: "Initial setup"
  session_start: "$(date -Iseconds)"
  last_updated: "$(date -Iseconds)"

git_status:
  branch: "main"
  upstream_status: "unknown"
  last_commit: "none"

current_work:
  task: "Initial setup and project assessment"
  status: "starting"
  start_time: "$(date -Iseconds)"

project_status:
  exchanges:
    total_goal: 25
    completed: 0
    in_progress: 0
    remaining: 25

next_steps:
  immediate_1h:
    - "Assess project structure and documentation"
    - "Review existing exchange implementations"
    - "Create initial automation tools"
EOF

    log "INFO" "Created initial AGENT_STATUS.yaml"
fi

# Step 1: Read AGENT_STATUS.yaml
log "INFO" ""
log "INFO" "STEP 1: READING CURRENT STATUS"
log "INFO" "================================"

if [ -f "$STATUS_FILE" ]; then
    PROJECT=$(get_yaml_value "project")
    GOAL=$(get_yaml_value "goal")
    PHASE=$(get_yaml_value "phase")
    LAST_UPDATED=$(get_yaml_value "last_updated")

    log "INFO" "Project: $PROJECT"
    log "INFO" "Goal: $GOAL"
    log "INFO" "Phase: $PHASE"
    log "INFO" "Last Updated: $LAST_UPDATED"

    # Get current task
    CURRENT_TASK=$(get_yaml_value "current_work:" "task")
    TASK_STATUS=$(get_yaml_value "current_work:" "status")

    if [ -n "$CURRENT_TASK" ]; then
        log "INFO" "Current Task: $CURRENT_TASK"
        log "INFO" "Task Status: $TASK_STATUS"
    fi

    # Get project status
    TOTAL_GOAL=$(get_yaml_value "total_goal")
    COMPLETED=$(get_yaml_value "completed")
    IN_PROGRESS=$(get_yaml_value "in_progress")
    REMAINING=$(get_yaml_value "remaining")

    if [ -n "$TOTAL_GOAL" ] && [ -n "$COMPLETED" ]; then
        log "INFO" "Project Progress: $COMPLETED/$TOTAL_GOAL ($(echo "scale=1; $COMPLETED*100/$TOTAL_GOAL" | bc)%)"
        log "INFO" "In Progress: $IN_PROGRESS, Remaining: $REMAINING"
    fi

    # Check for blockers
    if grep -q "blockers:" "$STATUS_FILE"; then
        log "WARN" "BLOCKERS DETECTED:"
        sed -n '/blockers:/,/^[^[:space:]]/p' "$STATUS_FILE" | grep -E "description:|impact:" | while read line; do
            log "WARN" "  $line"
        done
    fi
else
    log "ERROR" "Failed to read AGENT_STATUS.yaml"
    exit 1
fi

# Step 2: Check git status
log "INFO" ""
log "INFO" "STEP 2: CHECKING GIT STATUS"
log "INFO" "============================"

cd "$PROJECT_ROOT"

if [ -d ".git" ]; then
    # Get branch info
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    log "INFO" "Branch: $BRANCH"

    # Get upstream status
    if git remote get-url origin >/dev/null 2>&1; then
        UPSTREAM_STATUS=$(git status -sb | head -1 | sed 's/^## //')
        log "INFO" "Upstream: $UPSTREAM_STATUS"
    fi

    # Get last commit
    LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "No commits")
    log "INFO" "Last Commit: $LAST_COMMIT"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log "WARN" "UNCOMMITTED CHANGES DETECTED:"
        git status --porcelain | while read line; do
            log "WARN" "  $line"
        done
    else
        log "INFO" "No uncommitted changes"
    fi

    # Show recent commits
    log "INFO" ""
    log "INFO" "Recent Commits (last 5):"
    git log --oneline -5 2>/dev/null | while read commit; do
        log "INFO" "  $commit"
    done
else
    log "WARN" "Not a git repository"
fi

# Step 3: Display next steps
log "INFO" ""
log "INFO" "STEP 3: NEXT STEPS FROM STATUS"
log "INFO" "==============================="

# Extract next steps from YAML
if grep -q "next_steps:" "$STATUS_FILE"; then
    # Check for immediate steps
    if grep -q "immediate_1h:" "$STATUS_FILE"; then
        log "INFO" "IMMEDIATE NEXT STEPS (1h):"
        sed -n '/immediate_1h:/,/^[[:space:]]*[^[:space:]:]/p' "$STATUS_FILE" | grep -E '^[[:space:]]*-' | sed 's/^[[:space:]]*-[[:space:]]*/  • /' | while read step; do
            log "INFO" "$step"
        done
    fi

    # Check for short term steps
    if grep -q "short_term_4h:" "$STATUS_FILE"; then
        log "INFO" ""
        log "INFO" "SHORT TERM (4h):"
        sed -n '/short_term_4h:/,/^[[:space:]]*[^[:space:]:]/p' "$STATUS_FILE" | grep -E '^[[:space:]]*-' | sed 's/^[[:space:]]*-[[:space:]]*/  • /' | while read step; do
            log "INFO" "$step"
        done
    fi
fi

# Step 4: Update status if requested
if [ "$UPDATE_STATUS" = true ]; then
    log "INFO" ""
    log "INFO" "STEP 4: UPDATING STATUS FILE"
    log "INFO" "============================="

    # Backup current status file
    BACKUP_FILE="$STATUS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$STATUS_FILE" "$BACKUP_FILE"
    log "DEBUG" "Backup created: $BACKUP_FILE"

    # Update last_updated timestamp
    sed -i "s/^last_updated:.*/last_updated: \"$(date -Iseconds)\"/" "$STATUS_FILE"

    # Update session start if this is a new task
    if grep -q "session_start:" "$STATUS_FILE"; then
        sed -i "s/^\([[:space:]]*\)session_start:.*/\1session_start: \"$(date -Iseconds)\"/" "$STATUS_FILE"
    fi

    # Add session log reference
    if ! grep -q "session_logs:" "$STATUS_FILE"; then
        echo -e "\nsession_logs:" >> "$STATUS_FILE"
    fi

    # Append current session
    if ! grep -q "  - $SESSION_ID" "$STATUS_FILE"; then
        sed -i "/session_logs:/a\  - $SESSION_ID" "$STATUS_FILE"
    fi

    log "INFO" "Updated AGENT_STATUS.yaml with new session: $SESSION_ID"
fi

# Step 5: Generate restart summary
log "INFO" ""
log "INFO" "STEP 5: THREAD RESTART SUMMARY"
log "INFO" "================================"
log "INFO" "For next agent session, focus on:"

# Create a focused summary
echo ""
echo "========================================================"
echo "AGENT THREAD RESTART - READY FOR NEXT SESSION"
echo "========================================================"
echo ""
echo "PROJECT: $PROJECT"
echo "PHASE: $PHASE"
echo "PROGRESS: $COMPLETED/$TOTAL_GOAL exchanges"
echo ""
echo "CURRENT TASK: $CURRENT_TASK ($TASK_STATUS)"
echo ""

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "⚠️  UNCOMMITTED CHANGES: Review git status before continuing"
    echo ""
fi

# Show immediate next steps
if grep -q "immediate_1h:" "$STATUS_FILE"; then
    echo "NEXT IMMEDIATE STEPS:"
    sed -n '/immediate_1h:/,/^[[:space:]]*[^[:space:]:]/p' "$STATUS_FILE" | grep -E '^[[:space:]]*-' | sed 's/^[[:space:]]*-[[:space:]]*/• /' | head -3
    echo ""
fi

# Show any blockers
if grep -q "blockers:" "$STATUS_FILE"; then
    echo "🚨 ACTIVE BLOCKERS:"
    sed -n '/blockers:/,/^[^[:space:]]/p' "$STATUS_FILE" | grep "description:" | sed 's/.*description:[[:space:]]*/  • /' | head -2
    echo ""
fi

echo "GIT CONTEXT:"
echo "  Branch: $BRANCH"
echo "  Last: $(echo "$LAST_COMMIT" | cut -d' ' -f1)"
echo "  Msg: $(echo "$LAST_COMMIT" | cut -d' ' -f2-)"
echo ""
echo "SESSION LOG: $SESSION_LOG"
echo "========================================================"

# Log completion
log "INFO" ""
log "INFO" "Thread restart protocol complete"
log "INFO" "Session log saved to: $SESSION_LOG"
log "INFO" "Next agent can start with this context"

# Create a quick reference file for the agent
QUICK_REF="$PROJECT_ROOT/.agent/quick_ref.txt"
mkdir -p "$(dirname "$QUICK_REF")"

cat > "$QUICK_REF" << EOF
THREAD RESTART REFERENCE - $(date)
================================
Project: $PROJECT
Goal: $GOAL
Phase: $PHASE
Progress: $COMPLETED/$TOTAL_GOAL exchanges

Current Task: $CURRENT_TASK
Status: $TASK_STATUS

Git Context:
  Branch: $BRANCH
  Last Commit: $LAST_COMMIT
  Changes: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ') files

Immediate Next Steps:
$(sed -n '/immediate_1h:/,/^[[:space:]]*[^[:space:]:]/p' "$STATUS_FILE" | grep -E '^[[:space:]]*-' | sed 's/^[[:space:]]*-[[:space:]]*/  • /' | head -3)

Session: $SESSION_ID
Log: $SESSION_LOG
EOF

log "DEBUG" "Quick reference saved to: $QUICK_REF"

exit 0
