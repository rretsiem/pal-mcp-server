"""Parser for Claude CLI JSON output."""

from __future__ import annotations

import json
from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


class OpencodeJSONParser(BaseParser):
    """Parse stdout produced by `opencode --output-format json`."""

    name = "opencode_json"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        lines = [line.strip() for line in (stdout or "").splitlines() if line.strip()]
        events: list[dict[str, Any]] = []
        extracted_content_parts: list[str] = []
        errors: list[str] = []
        usage: dict[str, Any] | None = None

        for line in lines:
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            events.append(event)
            event_type = event.get("type")

            if event_type == "text":
                part = event.get("part")
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        extracted_content_parts.append(text.strip())
            elif event_type == "error":
                message = event.get("message")
                if isinstance(message, str) and message.strip():
                    errors.append(message.strip())
            elif event_type == "step_finish": # Assuming usage info is in step_finish
                step_finish_data = event.get("part")
                if isinstance(step_finish_data, dict):
                    tokens_data = step_finish_data.get("tokens")
                    if isinstance(tokens_data, dict):
                        usage = tokens_data


        if not extracted_content_parts and errors:
            extracted_content_parts.extend(errors)

        if not extracted_content_parts:
            # If no content, but there's stderr, include it
            if stderr.strip():
                return ParsedCLIResponse(
                    content="Opencode CLI returned no textual result. Raw stderr was preserved for troubleshooting.",
                    metadata={"stderr": stderr.strip(), "events": events, "errors": errors}
                )
            raise ParserError("Opencode CLI JSONL output did not include any text events or errors")

        content = "\n\n".join(extracted_content_parts).strip()
        metadata: dict[str, Any] = {"events": events}
        if errors:
            metadata["errors"] = errors
        if usage:
            metadata["usage"] = usage
        if stderr and stderr.strip():
            metadata["stderr"] = stderr.strip()

        return ParsedCLIResponse(content=content, metadata=metadata)


