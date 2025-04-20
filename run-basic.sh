#!/usr/bin/env bash
# run-basic.sh
set -euo pipefail

# ---------- sanity checks --------------------------------------------------
[[ -f test/basic/write.c ]]           || { echo "Missing test/basic/write.c"; exit 1; }
command -v gcc >/dev/null             || { echo "gcc not found"; exit 1; }
[[ -f test/basic/test.sh ]]           || { echo "Missing test/basic/test.sh"; exit 1; }
for m in fs-write-latency fs-write-throughput fs-read-latency; do
    [[ -f $m ]] || { echo "Missing monitor script: $m"; exit 1; }
done
sudo -n true 2>/dev/null || { echo "sudo needs a password; run 'sudo true' first."; exit 1; }

# ---------- 1. compile -----------------------------------------------------
echo "Compiling write.c → test/basic/write"
gcc test/basic/write.c -o test/basic/write

# ---------- 2–4. monitor / test loop --------------------------------------
MONITORS=(fs-write-latency fs-write-throughput fs-read-latency)

for monitor in "${MONITORS[@]}"; do
    TS=$(date +%Y%m%d_%H%M%S)
    LOG="{$monitor}_out.${TS}"

    echo "=== ${monitor} (log → ${LOG}) ==="
    sudo python3 "${monitor}" > "${LOG}" 2>&1 &
    PID=$!
    echo "PID ${PID} running…"

    # run tests *inside* test/basic so ./write and read.py resolve
    ( cd test/basic && ./test.sh )

    echo "Stopping ${monitor}"
    sudo kill -INT "${PID}"
    wait "${PID}" 2>/dev/null || true
    echo "${monitor} finished."
done

echo "All done."
