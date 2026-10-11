"""Add converted cards directly to a running Anki instance via AnkiConnect.

Requires the AnkiConnect add-on installed and Anki open. See
https://foosoft.net/projects/anki-connect/
"""

import json
import urllib.error
import urllib.request

import pandas as pd

ANKICONNECT_URL = "http://127.0.0.1:8765"
DEFAULT_DECK = "All::New"


class AnkiConnectError(Exception):
    pass


def _invoke(action: str, url: str = ANKICONNECT_URL, **params):
    payload = {"action": action, "version": 6, "params": params}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            response = json.load(resp)
    except urllib.error.URLError as exc:
        raise AnkiConnectError(
            f"Could not reach AnkiConnect at {url}. Is Anki open with the AnkiConnect add-on installed?"
        ) from exc

    if response.get("error") is not None:
        raise AnkiConnectError(response["error"])
    return response["result"]


def add_notes_via_ankiconnect(
    df: pd.DataFrame,
    deck: str = DEFAULT_DECK,
    model_name: str = "PCH Math Basic",
    url: str = ANKICONNECT_URL,
) -> list[bool]:
    """
    Send each row of df (columns: Front, Back, Reference, Chapter, Page, Tags) to Anki
    as a new note in `deck`, using the `model_name` note type. Use Anki's
    ``Parent::Child`` syntax for a subdeck. Skips notes Anki considers
    duplicates (by first field, scoped to the collection).
    """
    notes = [
        {
            "deckName": deck,
            "modelName": model_name,
            "fields": {
                "Front": row.Front,
                "Back": row.Back,
                "Reference": row.Reference,
                "Chapter": row.Chapter,
                "Page": row.Page,
            },
            "options": {"allowDuplicate": False},
            "tags": getattr(row, "Tags", []) or [],
        }
        for row in df.itertuples(index=False)
    ]

    if not notes:
        print("No cards to add.")
        return []

    can_add = _invoke("canAddNotes", url=url, notes=notes)
    addable = [note for note, ok in zip(notes, can_add) if ok]
    skipped = len(notes) - len(addable)

    results = _invoke("addNotes", url=url, notes=addable) if addable else []
    added = sum(1 for r in results if r is not None)

    exported = [not ok for ok in can_add]
    result_index = 0
    for note_index, ok in enumerate(can_add):
        if ok:
            exported[note_index] = results[result_index] is not None
            result_index += 1

    print(f"Added {added} card(s) to deck '{deck}' using note type '{model_name}'.")
    if skipped:
        print(f"Skipped {skipped} likely-duplicate card(s) (already present in the collection).")
    return exported
