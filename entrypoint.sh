#!/bin/sh
set -a
. /run/secrets/my_bot_env
set +a
exec python main.py
