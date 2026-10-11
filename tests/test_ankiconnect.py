import pandas as pd

from obsidianki import ankiconnect


def test_add_notes_via_ankiconnect_propagates_tags(monkeypatch):
    calls = []

    def invoke(action, url=ankiconnect.ANKICONNECT_URL, **params):
        calls.append((action, params))
        if action == "canAddNotes":
            return [True]
        if action == "addNotes":
            return [123]
        raise AssertionError(f"Unexpected action: {action}")

    monkeypatch.setattr(ankiconnect, "_invoke", invoke)

    exported = ankiconnect.add_notes_via_ankiconnect(
        pd.DataFrame(
            [
                {
                    "Front": "Question",
                    "Back": "Answer",
                    "Reference": "Book",
                    "Chapter": "1",
                    "Page": "2",
                    "Tags": ["proof", "measure-theory"],
                }
            ]
        )
    )

    assert exported == [True]
    assert calls[0][1]["notes"][0]["tags"] == ["proof", "measure-theory"]
