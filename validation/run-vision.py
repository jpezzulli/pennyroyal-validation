#!/usr/bin/env python3
"""Run the public spatial-comment multimodal validation case."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from common import base_url, served_model_name, write_json  # noqa: E402


CASE_PATH = ROOT / "cases" / "vision-spatial-comments.json"


def load_case() -> dict:
    return json.loads(CASE_PATH.read_text(encoding="utf-8"))


def load_font(size: int, bold: bool = False):
    from PIL import ImageFont

    names = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def render_fixture(case: dict, output: Path) -> dict:
    from PIL import Image, ImageDraw

    width, height = 1400, 1040
    image = Image.new("RGB", (width, height), "#f4f5f7")
    draw = ImageDraw.Draw(image)
    author_font = load_font(30, bold=True)
    body_font = load_font(27)
    top = 38
    for comment in case["comments"]:
        lines = wrap_text(draw, comment["text"], body_font, width - 150)
        card_height = 92 + 42 * len(lines)
        draw.rounded_rectangle(
            (42, top, width - 42, top + card_height),
            radius=20,
            fill="#ffffff",
            outline="#8a94a6",
            width=3,
        )
        draw.text((72, top + 24), comment["author"], fill="#111827", font=author_font)
        y = top + 69
        for line in lines:
            draw.text((72, y), line, fill="#202631", font=body_font)
            y += 42
        top += card_height + 22
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False)
    data = output.read_bytes()
    return {
        "path": str(output),
        "width": width,
        "height": height,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def evaluate_visible(text: str, finish_reason: str | None, expected: dict) -> dict:
    lower = text.casefold()
    top_author = expected["top_author"].casefold()
    bottom_author = expected["bottom_author"].casefold()
    top_index = lower.find(top_author)
    bottom_index = lower.find(bottom_author)
    ordered = top_index >= 0 and bottom_index > top_index
    top_region = lower[top_index:bottom_index] if ordered else ""
    bottom_region = lower[bottom_index:] if bottom_index >= 0 else ""
    checks = {
        "natural_stop": finish_reason == "stop",
        "top_author": top_index >= 0,
        "bottom_author": bottom_index >= 0,
        "spatial_order": ordered,
        "top_context": bool(re.search(r"512\s*k", top_region)),
        "top_decode": bool(re.search(r"100\s*\+\s*(?:tps|tok)", top_region)),
        "top_stack": all(
            term.casefold() in top_region for term in expected["top_stack"]
        ),
        "bottom_claim": all(
            term.casefold() in bottom_region
            for term in expected["bottom_claim_terms"]
        ),
    }
    checks["passed"] = all(checks.values())
    return checks


def canonical_smoke(case: dict) -> dict:
    text = (
        "Topmost: Turbulent-Alps4046 says they get 512k context and 100+ tps "
        "using sglang + dflash2. Bottommost: ComposerGen says an RTX Pro 6000 "
        "can reach 200 tps with SGLang and asks whether it was tried."
    )
    return evaluate_visible(text, "stop", case["expected"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", "--base-url", dest="base", default=base_url())
    parser.add_argument(
        "--model", "--served-model-name", dest="model", default=served_model_name()
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--render-fixture", type=Path)
    args = parser.parse_args()
    case = load_case()

    if args.list:
        print(f"{case['id']}\ttop/bottom spatial OCR and claim separation")
        return 0
    if args.smoke:
        result = canonical_smoke(case)
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    if args.dry_run:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "case": case["id"],
                    "base_url": args.base,
                    "served_model_name": args.model,
                    "prompt": case["prompt"],
                    "reasoning_effort": args.reasoning_effort,
                    "max_tokens": args.max_tokens,
                    "expected": case["expected"],
                },
                indent=2,
            )
        )
        return 0
    if args.render_fixture:
        print(json.dumps(render_fixture(case, args.render_fixture), indent=2))
        return 0

    output = args.output_dir or Path(
        "validation-results", time.strftime("vision-%Y%m%d-%H%M%S")
    )
    output.mkdir(parents=True, exist_ok=False)
    fixture = render_fixture(case, output / "fixture.png")
    encoded = base64.b64encode((output / "fixture.png").read_bytes()).decode()
    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": case["prompt"]},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}"},
                    },
                ],
            }
        ],
        "reasoning_effort": args.reasoning_effort,
        "temperature": 0.0,
        "max_tokens": args.max_tokens,
    }
    write_json(output / "request.json", payload)
    request = urllib.request.Request(
        args.base + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=args.timeout) as response:
        status = response.status
        result = json.load(response)
    wall = time.monotonic() - started
    write_json(output / "response.json", result)
    choice = (result.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    visible = str(message.get("content") or "")
    checks = evaluate_visible(visible, choice.get("finish_reason"), case["expected"])
    manifest = {
        "schema_version": 1,
        "case": case["id"],
        "base_url": args.base,
        "served_model_name": args.model,
        "fixture": fixture,
        "http_status": status,
        "wall_seconds": wall,
        "usage": result.get("usage"),
        "finish_reason": choice.get("finish_reason"),
        "visible_content": visible,
        "reasoning_content": message.get("reasoning_content") or message.get("reasoning"),
        "checks": checks,
        "passed": checks["passed"],
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if manifest["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
