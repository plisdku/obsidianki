# Obsidian Anki converter

**Version**: 0.0.1

Something to convert my obsidian notes to Anki flashcards. I have a pretty restrictive format I adhere to so this works.

By default, `obsidianki` prints/writes a CSV for manual import into Anki. Pass
`--anki-connect` to add cards directly to a running Anki instance instead (requires
the AnkiConnect add-on and Anki open). Use `--deck` to choose the target deck
(default: `All::New`) and `--model-name` to choose the note type (default: `PCH Math Basic`).
Use Anki's `Parent::Child` syntax for subdecks; the deck name is passed to
AnkiConnect unchanged. Successfully exported questions are marked with `✅` in
the source Markdown; duplicate notes are considered already exported.

```zsh
obsidianki notes.md --anki-connect --deck 'All::New'
```

Cards may include a `T:` field containing space- or comma-separated Anki tags:

```markdown
:flashcard:
What is a sigma-algebra?
T: definition measure-theory
A:
...
::
```

Tags are emitted as a `Tags` column in CSV output and are sent as note tags when
using `--anki-connect`.
