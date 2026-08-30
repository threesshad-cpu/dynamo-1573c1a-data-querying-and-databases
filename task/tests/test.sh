#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier

# The verification database must be regenerated from the exact task generator
# and deterministic held-out fixture. Harbor preserves /app from the agent run,
# so both inputs are pinned before verification data is rebuilt.
GENERATOR=/app/generate_data.py
EXPECTED_GENERATOR_BLOB=591ea82bbd4a16d8f286e53e3b9c0fe82bd81cea
AUGMENT=/usr/local/libexec/dynamo/augment_data.py
EXPECTED_AUGMENT_BLOB=3c4d87d73d929ce431f1daadbc671b096c782324

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

ACTUAL_AUGMENT_BLOB="$(python - "$AUGMENT" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = path.read_bytes()
header = f"blob {len(data)}\0".encode()
print(hashlib.sha1(header + data).hexdigest())
PY
)"

if [[ "$ACTUAL_GENERATOR_BLOB" != "$EXPECTED_GENERATOR_BLOB" ]] || [[ "$ACTUAL_AUGMENT_BLOB" != "$EXPECTED_AUGMENT_BLOB" ]]; then
    echo "Verification fixture integrity check failed" >&2
    echo "generator expected: $EXPECTED_GENERATOR_BLOB" >&2
    echo "generator actual:   $ACTUAL_GENERATOR_BLOB" >&2
    echo "augment expected:   $EXPECTED_AUGMENT_BLOB" >&2
    echo "augment actual:     $ACTUAL_AUGMENT_BLOB" >&2
    echo "0" > /logs/verifier/reward.txt
    exit 1
fi

echo "Regenerating pristine database for verification..."
python /app/generate_data.py
python "$AUGMENT"

if pytest /tests/test_outputs.py --ctrf /logs/verifier/ctrf.json; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi
