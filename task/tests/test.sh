#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo "Regenerating pristine database for verification..."
python /app/generate_data.py

if pytest /tests/test_outputs.py --ctrf /logs/verifier/ctrf.json; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi
