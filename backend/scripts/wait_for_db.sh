#!/usr/bin/env bash
# Block until the database in DATABASE_URL accepts connections (PostgreSQL only).
set -euo pipefail

case "${DATABASE_URL:-}" in
  postgres*) ;;
  *) exit 0 ;;
esac

python - <<'PY'
import os
import sys
import time

import psycopg

url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))
deadline = time.monotonic() + timeout
while True:
    try:
        psycopg.connect(url, connect_timeout=3).close()
        break
    except psycopg.OperationalError:
        if time.monotonic() > deadline:
            print("Database did not become ready in time", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
PY
