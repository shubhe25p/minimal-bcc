#!/usr/bin/env bash
##############################################################################
# run-basic-with-logs.sh
#   • Compiles test/basic/write.c (output -> test/basic/write)
#   • For each hard‑coded monitor (fs-write-latency, fs-write-throughput, fs-read-latency):
#       – starts it with sudo, log -> <name>_out_<ts>.log
#       – runs test/basic/test.sh once (inside its dir)
#       – records elapsed time (date timing)
#       – stops monitor (SIGINT, up‑to‑10‑s wait, SIGKILL)
#   • Also runs a baseline (no monitor) first
#   • Prints timing table baseline + every monitor at end
##############################################################################

set -euo pipefail
trap 'echo "ERROR on line $LINENO: $BASH_COMMAND" >&2' ERR

mkdir -p test/basic  # ensure dir exists (harmless if it already does)

# ---------- sanity checks --------------------------------------------------
[[ -f test/basic/write.c ]]           || { echo "Missing test/basic/write.c"; exit 1; }
command -v gcc >/dev/null             || { echo "gcc not found"; exit 1; }
[[ -f test/basic/test.sh ]]           || { echo "Missing test/basic/test.sh"; exit 1; }
MONITORS=(fs-write-latency fs-write-throughput fs-read-latency)
for m in "${MONITORS[@]}"; do [[ -f $m ]] || { echo "Missing monitor script: $m"; exit 1; }; done
sudo -n true 2>/dev/null || { echo "sudo needs a password; run 'sudo true' first."; exit 1; }

echo "Compiling write.c → test/basic/write"
gcc test/basic/write.c -o test/basic/write

declare -A TIME=()

# helper: run test/basic/test.sh once and return seconds
run_one() {
  local start end
  start=$(date +%s.%N)
  ( cd test/basic && ./test.sh )
  end=$(date +%s.%N)
  awk -v s="$start" -v e="$end" 'BEGIN{printf "%.3f", e-s}'
}

# baseline ------------------------------------------------------------------
echo "Running baseline (no monitor) …"
TIME[baseline]=$(run_one)
echo "  baseline=${TIME[baseline]}s"

ts=$(date +%Y%m%d_%H%M%S)

for monitor in "${MONITORS[@]}"; do
  log="${monitor}_out_${ts}.log"
  echo "\n=== $monitor (log → $log) ==="
  sudo python3 "$monitor" >"$log" 2>&1 &
  pid=$!
  echo "  PID $pid running …"

  TIME[$monitor]=$(run_one)
  echo "  ${monitor}_time=${TIME[$monitor]}s"

  if sudo kill -0 "$pid" 2>/dev/null; then sudo kill -INT "$pid" || true; fi
  for i in {1..10}; do ! sudo kill -0 "$pid" 2>/dev/null && break; sleep 1; done
  sudo kill -0 "$pid" 2>/dev/null && { echo "    Force‑killing $pid"; sudo kill -9 "$pid"; }
  wait "$pid" 2>/dev/null || true
  echo "  Monitor $monitor stopped"
done

# timing table --------------------------------------------------------------
printf "\nTiming results (single run)\n"
header=(baseline "${MONITORS[@]}")
for h in "${header[@]}"; do printf "%-24s" "$h"; done; printf "\n"
for h in "${header[@]}"; do printf "%-24s" "${TIME[$h]}s"; done; printf "\n"

echo -e "\nAll done ✔"
