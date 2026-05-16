"""In-process runtime stats for the inference API (local demo)."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

_latencies_ms: deque[float] = deque(maxlen=500)
_request_count = 0
_error_count = 0
_started_at = time.time()


def record_predict(latency_ms: float, *, error: bool = False) -> None:
    global _request_count, _error_count
    _request_count += 1
    if error:
        _error_count += 1
    else:
        _latencies_ms.append(latency_ms)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = int(len(sorted_v) * p)
    idx = min(idx, len(sorted_v) - 1)
    return sorted_v[idx]


def get_runtime_stats(model_ready: bool) -> dict[str, Any]:
    latencies = list(_latencies_ms)
    avg = sum(latencies) / len(latencies) if latencies else 0.0
    error_rate = (_error_count / _request_count * 100) if _request_count else 0.0

    return {
        "endpoint_health": "healthy" if model_ready else "degraded",
        "api_status": "ok" if model_ready else "starting",
        "uptime_seconds": int(time.time() - _started_at),
        "request_volume_total": _request_count,
        "error_count": _error_count,
        "error_rate_pct": round(error_rate, 2),
        "avg_latency_ms": round(avg, 1),
        "p95_latency_ms": round(_percentile(latencies, 0.95), 1),
        "recent_latency_ms": [round(x, 1) for x in latencies[-24:]],
    }
