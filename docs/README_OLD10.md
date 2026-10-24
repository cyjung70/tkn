# tkn
tonabit-knowledge-nexus

Imports conversation histories from ChatGPT, Claude, Claude Code, and Codex into an Obsidian vault, one Markdown note per conversation.

## Setup

Requires Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
copy tkn.example.toml tkn.toml   # then set vault_path
```

## Usage

```powershell
tkn import chatgpt  path\to\chatgpt-export.zip
tkn import claude   path\to\claude-export.zip
tkn import claude-code
tkn import codex
```

Options: `--dry-run`, `--since YYYY-MM-DD`, `-v` (list created notes), `--config PATH`.

Notes are written to `<vault>/<root_folder>/<Tool>/<YYYY-MM>/<YYYY-MM-DD>_<title>.md`.
Conversations that already exist in the vault (matched by `source` + `id` in the frontmatter) are skipped, so re-running is safe and never overwrites your edits.

## Privacy

Exports, session logs, `tkn.toml`, and vault output are gitignored. Never commit real conversations.
