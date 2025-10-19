import hashlib
import json
import time
from dataclasses import dataclass


@dataclass
class RunClock:
    start: float

    def __init__(self) -> None:
        self.start = time.perf_counter()

    def seconds(self) -> int:
        return int(time.perf_counter() - self.start)


def seed_from_payload(payload: dict) -> int:
    """Stable seed from important fields of the request."""
    s = json.dumps(payload, sort_keys=True).encode("utf-8")
    return int(hashlib.sha256(s).hexdigest()[:8], 16)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def estimate_cost(tokens_used: int, unit_cost_per_1k_tokens: float = 0.003) -> float:
    return round(tokens_used / 1000.0 * unit_cost_per_1k_tokens, 4)
