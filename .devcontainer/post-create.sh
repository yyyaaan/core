#!/usr/bin/env bash
set -euo pipefail

# Named volumes keep the owner they were created with. Two sit on paths the image
# doesn't own, and the shared ones outlive a rebuild that changes vscode's UID, so
# re-own any whose top directory isn't ours (recursive only then: the caches are big).
for dir in /workspace/.venv /usr/local/cargo/registry \
    ~/.cache/uv ~/.cache/cargo-target ~/.local/share/uv/python \
    ~/.config/gh ~/.claude ~/.codex; do
  if [ -d "$dir" ] && [ "$(stat -c %u "$dir")" != "$(id -u)" ]; then
    sudo chown -R "$(id -u):$(id -g)" "$dir"
  fi
done

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
