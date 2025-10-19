import re


def get_counter(text: str, name: str) -> float:
    # Prometheus exposition format: "<name> <value>"
    m = re.search(rf"^{re.escape(name)}\s+([0-9]+(?:\.[0-9]+)?)\s*$", text, re.M)
    return float(m.group(1)) if m else 0.0
