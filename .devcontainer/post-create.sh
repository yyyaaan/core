#!/usr/bin/env bash
set -euo pipefail

# These two volumes sit on paths the image doesn't own (inside the workspace bind
# and under the Rust feature's CARGO_HOME), so they start out root-owned.
sudo chown vscode:vscode /workspace/.venv /usr/local/cargo/registry

# Personal agent config. ~/.agents is bind-mounted from the host and is the single
# source of truth; Codex reads ~/.agents/skills natively, Claude gets symlinks.
link() { # link <target> <path>
  local target=$1 path=$2
  if [ -e "$path" ] && [ ! -L "$path" ]; then
    mv "$path" "$path.bak.$(date +%s)"
  fi
  ln -sfn "$target" "$path"
}
mkdir -p ~/.agents/skills ~/.agents/claude/agents
link ~/.agents/AGENTS.md     ~/.claude/CLAUDE.md
link ~/.agents/skills        ~/.claude/skills
link ~/.agents/claude/agents ~/.claude/agents
link ~/.agents/AGENTS.md     ~/.codex/AGENTS.md

# Project environment
uv sync --all-packages --all-extras
uv run playwright install chromium
