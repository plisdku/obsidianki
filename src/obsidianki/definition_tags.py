import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from obsidianki.convert import extract_flashcard_blocks, get_flashcard_fields, parse_tags

MODEL = "gemini-3.6-flash"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PROMPT = """Classify each flashcard as is_definition=true or false.

Use true only when the card introduces and states the meaning of a term or named concept.
Use false for proofs, theorems, formulas, examples, characterizations, and consequences.
Return one result for every card, using only card_index and is_definition.

Cards:
"""
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "card_index": {"type": "INTEGER"},
                    "is_definition": {"type": "BOOLEAN"},
                },
                "required": ["card_index", "is_definition"],
            },
        }
    },
    "required": ["results"],
}


def _classify(cards: list[dict[str, object]], model: str) -> set[int]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Export it first, for example: export GEMINI_API_KEY='...'")
    payload = {
        "contents": [{"parts": [{"text": PROMPT + json.dumps(cards)}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": SCHEMA},
    }
    request = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Gemini request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Gemini: {exc.reason}") from exc
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    return {item["card_index"] for item in json.loads(text)["results"] if item["is_definition"]}


def _add_tag(block: str) -> str:
    match = re.search(r"^T:\s*(.*)$", block, re.MULTILINE)
    if match:
        tags = parse_tags(match.group(1))
        if "definition" not in tags:
            tags.append("definition")
        return block[: match.start(1)] + " ".join(tags) + block[match.end(1) :]

    field = re.search(r"^(A|Answer|X|Extra|R|Reference|Book|C|Chapter|P|Page):", block, re.MULTILINE)
    insertion = "T: definition\n"
    return block[: field.start()] + insertion + block[field.start() :] if field else block + insertion


def _tagged_text(text: str, indices: set[int]) -> str:
    lines = text.splitlines(keepends=True)
    ranges: list[tuple[int, int]] = []
    start: int | None = None
    for index, line in enumerate(lines):
        marker = line.rstrip("\r\n")
        if marker == ":flashcard:":
            if start is not None:
                ranges.append((start, index))
            start = index + 1
        elif marker == "::" and start is not None:
            ranges.append((start, index))
            start = None

    replacements = {
        start: _add_tag("".join(lines[start:end]))
        for card_index, (start, end) in enumerate(ranges)
        if card_index in indices
    }
    output: list[str] = []
    for index, line in enumerate(lines):
        if index in replacements:
            output.append(replacements[index])
        if not any(start <= index < end for start, end in ranges if start in replacements):
            output.append(line)
    return "".join(output)


def tag_definitions(input_file: str | Path, model: str = MODEL) -> int:
    path = Path(input_file)
    text = path.read_text(encoding="utf-8")
    cards = []
    for index, block in enumerate(extract_flashcard_blocks(text)):
        fields = get_flashcard_fields(block)
        if "definition" not in parse_tags(fields.get("T", "")):
            cards.append({"card_index": index, "front": fields.get("Q", ""), "back": fields.get("A", "")})
    if not cards:
        return 0
    indices = _classify(cards, model)
    path.write_text(_tagged_text(text, indices), encoding="utf-8")
    return len(indices)
