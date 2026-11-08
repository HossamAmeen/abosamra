#!/usr/bin/env bash
set -euo pipefail

bash /app/scripts/wait_for_db.sh

if [ "${RUN_MIGRATIONS:-False}" = "True" ]; then
  python manage.py migrate --noinput
fi
if [ "${RUN_COLLECTSTATIC:-False}" = "True" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
