#!/bin/bash
# Daily runner for austin-events pipeline.
# Called by launchd at 7am; safe to run manually too.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/Library/Logs/austin-events"

mkdir -p "$LOG_DIR"
# Keep 14 days of logs
ls -t "$LOG_DIR"/run-*.log 2>/dev/null | tail -n +15 | xargs rm -f 2>/dev/null || true

exec > >(tee -a "$LOG_DIR/run-$(date +%Y-%m-%d).log") 2>&1

echo "═══════════════════════════════════════════"
echo "Austin Events — $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════"

cd "$SCRIPT_DIR"
/usr/bin/python3 parse_and_deploy.py

echo "Done at $(date '+%H:%M:%S')"
