#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PORT="${PORT:-8091}"
PID_FILE="$ROOT/.hot_item_collection_server.pid"
LOG_FILE="$ROOT/.hot_item_collection_server.log"
PYTHON="$ROOT/.venv/bin/python"
FOREGROUND="${FOREGROUND:-0}"

if [ "${1:-}" = "--foreground" ]; then
    FOREGROUND="1"
fi

if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

stop_pid() {
    local pid="$1"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "已停止旧服务（PID: $pid）"
    fi
}

if [ -f "$PID_FILE" ]; then
    stop_pid "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"
fi

PORT_PID="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [ -n "$PORT_PID" ]; then
    stop_pid "$PORT_PID"
fi

echo "正在启动爆款采集 Web 控制台..."
cd "$ROOT"
if [ "$FOREGROUND" = "1" ]; then
    echo "以前台模式启动，访问 http://localhost:$PORT"
    exec "$PYTHON" -m app.module.hot_item_collection.server --port "$PORT"
fi

nohup "$PYTHON" -m app.module.hot_item_collection.server --port "$PORT" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

sleep 1
if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "服务已重启（PID: $SERVER_PID），访问 http://localhost:$PORT"
    echo "日志文件：$LOG_FILE"
else
    echo "服务启动失败"
    if [ -f "$LOG_FILE" ]; then
        tail -n 20 "$LOG_FILE"
    fi
    rm -f "$PID_FILE"
    exit 1
fi
