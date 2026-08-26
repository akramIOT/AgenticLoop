"""验证本地模型端点是否可达 — V4 实验前置检查."""

import sys

import requests

from experiments.v4.config.model_client import ModelClient, load_config


def verify():
    config = load_config()
    endpoint = config["endpoint"]
    print(f"Checking endpoint: {endpoint}")

    try:
        resp = requests.get(f"{endpoint}/models", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", [])
        print(f"  OK — {len(models)} model(s) available:")
        for m in models:
            print(f"    - {m.get('id', 'unknown')}")
    except Exception as exc:
        print(f"  FAIL — {exc}")
        return 1

    # Smoke test: single chat call
    client = ModelClient(config)
    try:
        result = client.chat([{"role": "user", "content": "Say hello"}])
        content = result.get("content", "") if result else ""
        print(f"  OK — chat smoke test passed (response length: {len(content)} chars)")
    except Exception as exc:
        print(f"  FAIL — chat smoke test: {exc}")
        return 1

    print("All checks passed. V4 can proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(verify())
