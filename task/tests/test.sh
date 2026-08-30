#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier

# The verification database must be regenerated from the exact task generator.
# Harbor preserves /app from the agent run, so pin the generator by its Git blob
# identity before executing it. This prevents an agent from replacing the
# generator and manufacturing a matching ground truth database.
GENERATOR=/app/generate_data.py
EXPECTED_GENERATOR_BLOB=591ea82bbd4a16d8f286e53e3b9c0fe82bd81cea
ACTUAL_GENERATOR_BLOB="$(python - "$GENERATOR" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = path.read_bytes()
header = f"blob {len(data)}\0".encode()
print(hashlib.sha1(header + data).hexdigest())
PY
)"

if [[ "$ACTUAL_GENERATOR_BLOB" != "$EXPECTED_GENERATOR_BLOB" ]]; then
    echo "Generator integrity check failed" >&2
    echo "expected: $EXPECTED_GENERATOR_BLOB" >&2
    echo "actual:   $ACTUAL_GENERATOR_BLOB" >&2
    echo "0" > /logs/verifier/reward.txt
    exit 1
fi

echo "Regenerating pristine database for verification..."
python /app/generate_data.py

if pytest /tests/test_outputs.py --ctrf /logs/verifier/ctrf.json; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi
