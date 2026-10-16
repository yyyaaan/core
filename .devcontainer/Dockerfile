# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/base:2-trixie

# Fail a RUN when any command in a pipe fails (curl | tar, curl | bash)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG USERNAME=vscode
# Bump deliberately; see https://github.com/openai/codex/releases
ARG CODEX_VERSION=0.162.1

# uv / uvx (pinned to a minor line)
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /usr/local/bin/

# ripgrep: code search for the agents. bubblewrap: Codex's Linux sandbox.
# tmux: only for Claude Code agent-team split panes; drop it if unused.
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends ripgrep bubblewrap tmux \
    && rm -rf /var/lib/apt/lists/*

# Codex CLI: single static binary in /usr/local/bin, so the ~/.codex volume never
# shadows it (the standalone installer would keep the binary inside ~/.codex).
RUN arch="$(uname -m)" \
    && curl -fsSL "https://github.com/openai/codex/releases/download/rust-v${CODEX_VERSION}/codex-${arch}-unknown-linux-musl.tar.gz" \
       | tar -xz -C /usr/local/bin \
    && mv "/usr/local/bin/codex-${arch}-unknown-linux-musl" /usr/local/bin/codex \
    && codex --version

ENV UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/home/${USERNAME}/.local/share/uv/python \
    CARGO_TARGET_DIR=/home/${USERNAME}/.cache/cargo-target \
    CLAUDE_CONFIG_DIR=/home/${USERNAME}/.claude \
    CODEX_HOME=/home/${USERNAME}/.codex \
    PATH=/home/${USERNAME}/.local/bin:${PATH}

# Pre-create volume mount points so fresh named volumes inherit vscode ownership.
RUN mkdir -p \
        /home/${USERNAME}/.cache/uv \
        /home/${USERNAME}/.cache/cargo-target \
        /home/${USERNAME}/.local/share/uv/python \
        /home/${USERNAME}/.config/gh \
        /home/${USERNAME}/.claude \
        /home/${USERNAME}/.codex \
        /home/${USERNAME}/.agents \
    && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

# Claude Code: native installer (no Node.js, self-updating).
USER ${USERNAME}
RUN curl -fsSL https://claude.ai/install.sh | bash
USER root
