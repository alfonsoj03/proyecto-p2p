import json
import urllib.request
from typing import Any, Dict, Tuple

def post_json(url: str, data: Dict[str, Any] | None = None, timeout: int = 10) -> Tuple[int, str]:
    body = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def get(url: str, timeout: int = 10) -> Tuple[int, str]:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")
