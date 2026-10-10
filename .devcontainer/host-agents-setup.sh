#!/usr/bin/env bash
# Run on the Mac host, not in the container. Idempotent.
set -euo pipefail

src="$HOME/Lab/agents"
ts=$(date +%s)
mkdir -p "$src/skills" "$src/claude/agents"

# Adopt a real ~/.agents (e.g. created by devcontainer initializeCommand)
if [ -d ~/.agents ] && [ ! -L ~/.agents ]; then
  cp -Rn ~/.agents/. "$src/"
  mv ~/.agents ~/.agents.bak.$ts
  echo "Moved old ~/.agents to ~/.agents.bak.$ts (check for anything not copied, then delete)"
fi
touch "$src/AGENTS.md"

link() { # link <target> <path>
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    mv "$2" "$2.bak.$ts"
    echo "Backed up $2 to $2.bak.$ts"
  fi
  ln -sfn "$1" "$2"
}

mkdir -p ~/.claude ~/.codex
link "$src"                  ~/.agents
link ~/.agents/AGENTS.md     ~/.claude/CLAUDE.md
link ~/.agents/skills        ~/.claude/skills
link ~/.agents/claude/agents ~/.claude/agents
link ~/.agents/AGENTS.md     ~/.codex/AGENTS.md

ls -la ~/.agents ~/.claude/CLAUDE.md ~/.claude/skills ~/.claude/agents ~/.codex/AGENTS.md
