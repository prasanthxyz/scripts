#!/usr/bin/env bash
#
# adbsync-since.sh — pull only files modified on/after a given date,
# using better-adb-sync (adbsync) under the hood.
#
# Usage:
#   ./adbsync-since.sh DATE DEVICE_PATH LOCAL_PATH [-- extra adbsync args]
#
# Examples:
#   ./adbsync-since.sh 2025-09-01 /sdcard/DCIM/Camera ~/Pictures/Camera
#   ./adbsync-since.sh "2025-09-01 14:30" /sdcard/Download ~/Downloads -- --del
#
# DATE is anything `touch -d` understands, e.g.:
#   2025-09-01
#   "2025-09-01 14:30"
#   "3 days ago"
#   yesterday
#
# How it works:
#   1. Creates a reference file on the device stamped with DATE's mtime.
#   2. Uses the device's `find DEVICE_PATH -not -newer <ref>` to list every
#      file OLDER than DATE.
#   3. Writes those paths (relative to DEVICE_PATH) to a temp exclude file.
#   4. Runs `adbsync pull DEVICE_PATH LOCAL_PATH --exclude-from <file>`,
#      so only files modified on/after DATE actually get pulled.
#
# Caveat: this filters by modification time (mtime), the only timestamp
# `find` can reliably compare on Android — not a true "creation time".

set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 DATE DEVICE_PATH LOCAL_PATH [-- extra adbsync args]" >&2
  exit 1
fi

DATE="$1"
DEVICE_PATH="$2"
LOCAL_PATH="$3"
shift 3

EXTRA_ARGS=()
if [ "${1:-}" = "--" ]; then
  shift
  EXTRA_ARGS=("$@")
fi

command -v adb >/dev/null 2>&1 || { echo "adb not found in PATH" >&2; exit 1; }
command -v adbsync >/dev/null 2>&1 || { echo "adbsync (better-adb-sync) not found in PATH" >&2; exit 1; }

# Validate the date locally first (adb shell has no access to your local `date`/`touch`).
# Supports both GNU date (Linux) and BSD date (macOS), which take different flags.
parse_date() {
  local input="$1"

  # Try GNU date first (Linux, or `brew install coreutils` gdate on macOS)
  if date -d "$input" +%Y%m%d%H%M.%S 2>/dev/null; then
    return 0
  fi
  if command -v gdate >/dev/null 2>&1 && gdate -d "$input" +%Y%m%d%H%M.%S 2>/dev/null; then
    return 0
  fi

  # Fall back to BSD date (macOS default), which needs an explicit input format
  local fmt
  for fmt in "%Y-%m-%d %H:%M:%S" "%Y-%m-%d %H:%M" "%Y-%m-%d" "%m/%d/%Y %H:%M" "%m/%d/%Y"; do
    if date -j -f "$fmt" "$input" +%Y%m%d%H%M.%S 2>/dev/null; then
      return 0
    fi
  done

  return 1
}

if ! TOUCH_STAMP=$(parse_date "$DATE"); then
  echo "Could not parse DATE: '$DATE'" >&2
  echo "Try a format like: 2026-04-01  or  \"2026-04-01 14:30\"  or  04/01/2026" >&2
  echo "(Tip: 'brew install coreutils' gives you gdate, which accepts things like 'yesterday' or '3 days ago')" >&2
  exit 1
fi

DEVICE_REF="/sdcard/.adbsync_since_ref_$$"
LOCAL_EXCLUDE_FILE=$(mktemp /tmp/adbsync_exclude.XXXXXX)

cleanup() {
  adb shell "rm -f '$DEVICE_REF'" >/dev/null 2>&1 || true
  rm -f "$LOCAL_EXCLUDE_FILE"
}
trap cleanup EXIT

echo "Cutoff: $DATE"
echo "Creating reference timestamp on device..."
adb shell "touch -t $TOUCH_STAMP '$DEVICE_REF'"

echo "Finding files older than cutoff under $DEVICE_PATH ..."
# Strip DEVICE_PATH prefix (with or without trailing slash) so exclude
# patterns are relative to the source, as adbsync --exclude-from expects.
adb shell "find '$DEVICE_PATH' -type f -not -newer '$DEVICE_REF'" \
  | tr -d '\r' \
  | sed -e "s|^${DEVICE_PATH%/}/||" \
  > "$LOCAL_EXCLUDE_FILE"

EXCLUDED_COUNT=$(wc -l < "$LOCAL_EXCLUDE_FILE" | tr -d ' ')
echo "Excluding $EXCLUDED_COUNT file(s) older than cutoff."

echo "Running adbsync pull..."
adbsync --exclude-from "$LOCAL_EXCLUDE_FILE" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}" pull "$DEVICE_PATH" "$LOCAL_PATH"

echo "Done."
