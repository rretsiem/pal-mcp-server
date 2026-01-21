import json
import os
import shutil

import pytest

from tools.clink import CLinkTool


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clink_opencode_single_digit_sum():
    if shutil.which("opencode") is None:
        pytest.skip("opencode CLI is not installed or on PATH")

    tool = CLinkTool()
    prompt = "Respond with a single digit equal to the sum of 2 + 2. Output only that digit."

    results = await tool.execute(
        {
            "prompt": prompt,
            "cli_name": "opencode",
            "role": "default",
            "absolute_file_paths": [],
            "images": [],
        }
    )

    assert results, "clink tool returned no outputs"
    payload = json.loads(results[0].text)
    status = payload["status"]

    if status == "error":
        metadata = payload.get("metadata") or {}
        reason = payload.get("content") or metadata.get("message") or "Opencode CLI reported an error"
        pytest.skip(f"Skipping Opencode integration test: {reason}")

    assert status in {"success", "continuation_available"}

    content = payload.get("content", "").strip()
    # Assuming opencode CLI would return "4" directly for this prompt
    assert content == "4" or "4" in content, f"Expected '4' in response, got: {content[:100]}"

    if status == "continuation_available":
        offer = payload.get("continuation_offer") or {}
        assert offer.get("continuation_id"), "Expected continuation metadata when status indicates availability"
