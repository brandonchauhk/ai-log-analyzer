# services/parser.py
import re
from typing import List, Dict
import pandas as pd

def parse_log_file(log_text: str, log_type: str):
    """
    根據 log_type 把原始文字 log 解析成結構化資料（list[dict]），
    再轉成 pandas.DataFrame 回傳，方便在前端顯示。
    """
    lines = [line for line in log_text.splitlines() if line.strip()]

    if log_type == "Windows Event Log":
        records = [parse_windows_event_line(line) for line in lines]
    elif log_type == "Linux syslog":
        records = [parse_linux_syslog_line(line) for line in lines]
    else:  # Application Log
        records = [parse_app_log_line(line) for line in lines]

    # 過濾掉 None（代表解析失敗的行）
    records = [r for r in records if r is not None]

    if not records:
        return []

    return pd.DataFrame(records)

# --- Windows Event Log 解析（簡化版）---

WINDOWS_EVENT_PATTERN = re.compile(
    r"""
    ^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),\s*
    (?P<level>\w+),\s*
    Source=(?P<source>[^,]+),\s*
    EventID=(?P<event_id>\d+),\s*
    (?P<message>.*)$
    """,
    re.VERBOSE,
)

def parse_windows_event_line(line: str) -> Dict:
    """
    範例格式：
    2025-01-02 10:15:32, Error, Source=Service Control Manager, EventID=7000, The XXX service failed to start...
    """
    m = WINDOWS_EVENT_PATTERN.match(line.strip())
    if not m:
        # 不符合格式的行直接略過，或視需要保留為 message-only
        return None
    return {
        "timestamp": m.group("timestamp"),
        "level": m.group("level"),
        "source": m.group("source"),
        "event_id": m.group("event_id"),
        "message": m.group("message"),
    }

# --- Linux syslog 解析 ---

LINUX_SYSLOG_PATTERN = re.compile(
    r"""
    ^(?P<month>\w{3})\s+
    (?P<day>\d{1,2})\s+
    (?P<time>\d{2}:\d{2}:\d{2})\s+
    (?P<host>\S+)\s+
    (?P<process>[\w\-/]+)(?:\[(?P<pid>\d+)\])?:\s+
    (?P<message>.*)$
    """,
    re.VERBOSE,
)

def parse_linux_syslog_line(line: str) -> Dict:
    """
    範例格式：
    Jan  5 10:15:32 web01 sshd[12345]: Failed password for invalid user root from 192.168.1.10 port 54321 ssh2
    """
    m = LINUX_SYSLOG_PATTERN.match(line.strip())
    if not m:
        return None
    return {
        "month": m.group("month"),
        "day": m.group("day"),
        "time": m.group("time"),
        "host": m.group("host"),
        "process": m.group("process"),
        "pid": m.group("pid") or "",
        "message": m.group("message"),
    }

# --- Application Log 解析（常見格式）---

APP_LOG_PATTERN = re.compile(
    r"""
    ^\[(?P<timestamp>[^\]]+)\]\s+
    (?P<level>\w+)\s+
    \[(?P<module>[^\]]+)\]\s+
    (?P<message>.*)$
    """,
    re.VERBOSE,
)

def parse_app_log_line(line: str) -> Dict:
    """
    範例格式：
    [2025-01-02 10:15:32,123] INFO [auth] User login failed for user=brandon ip=1.2.3.4
    """
    m = APP_LOG_PATTERN.match(line.strip())
    if not m:
        return None
    return {
        "timestamp": m.group("timestamp"),
        "level": m.group("level"),
        "module": m.group("module"),
        "message": m.group("message"),
    }
