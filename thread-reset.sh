#!/bin/bash

# thread-reset.sh - Alias for thread_restart.sh
# Provides consistent naming for agent thread restart protocol
# This is an alias file that delegates to thread_restart.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESTART_SCRIPT="$SCRIPT_DIR/thread_restart.sh"

# Check if thread_restart.sh exists
if [ ! -f "$RESTART_SCRIPT" ]; then
    echo "Error: thread_restart.sh not found at $RESTART_SCRIPT" >&2
    echo "Please ensure thread_restart.sh exists in the same directory." >&2
    exit 1
fi

# Make sure thread_restart.sh is executable
if [ ! -x "$RESTART_SCRIPT" ]; then
    echo "Warning: thread_restart.sh is not executable. Attempting to fix..." >&2
    chmod +x "$RESTART_SCRIPT" 2>/dev/null || {
        echo "Error: Could not make thread_restart.sh executable" >&2
        exit 1
    }
fi

# Pass all arguments to thread_restart.sh
echo "thread-reset.sh: Using thread restart protocol..."
echo "=================================================="
exec "$RESTART_SCRIPT" "$@"
