#!/bin/bash
# Runs the pinned wawatch HTTP server and the inbound bridge in this container.
# The backend is not a parent of either process.
set -euo pipefail

cd /opt/wawatch
node dist/cli.js --port "${WAWATCH_PORT:-3001}" --data "${WAWATCH_DATA:-/data}" &
wa_pid=$!
node /opt/deala/bridge.mjs &
bridge_pid=$!

stop() {
  kill "$wa_pid" "$bridge_pid" 2>/dev/null || true
  wait "$wa_pid" "$bridge_pid" 2>/dev/null || true
}
trap stop INT TERM

# If either process exits, stop the other so the container does not look healthy
# while only half of the sidecar is up.
wait -n "$wa_pid" "$bridge_pid"
status=$?
stop
exit "$status"
