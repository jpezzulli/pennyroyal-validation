#!/usr/bin/env python3
"""Check OpenAI-compatible model discovery without running inference."""

import argparse
import json
import os
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BASE_URL", "http://127.0.0.1:8001"),
    )
    parser.add_argument(
        "--served-model-name",
        default=os.environ.get("SERVED_MODEL_NAME", "pennyroyal"),
    )
    args = parser.parse_args()
    url = args.base_url.rstrip("/") + "/v1/models"
    with urllib.request.urlopen(url, timeout=15) as response:
        payload = json.load(response)
    ids = [
        item.get("id")
        for item in payload.get("data", [])
        if isinstance(item, dict)
    ]
    result = {
        "url": url,
        "status": "ok" if args.served_model_name in ids else "model_missing",
        "expected_model": args.served_model_name,
        "available_models": ids,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
