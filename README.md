# Obsidian Anki converter

**Version**: 0.0.1

Something to convert my obsidian notes to Anki flashcards. I have a pretty restrictive format I adhere to so this works.

By default, `obsidianki` prints/writes a CSV for manual import into Anki. Pass
`--anki-connect` to add cards directly to a running Anki instance instead (requires
the AnkiConnect add-on and Anki open). Use `--deck` to choose the target deck
(default: `All::New`) and `--model-name` to choose the note type (default: `PCH Math Basic`).
Use Anki's `Parent::Child` syntax for subdecks; the deck name is passed to
AnkiConnect unchanged.

```zsh
obsidianki notes.md --anki-connect --deck 'All::New'
```
