# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/base:2-trixie

# Fail a RUN when any command in a pipe fails (curl | tar, curl | bash)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG USERNAME=vscode
# Bump deliberately; see https://github.com/openai/codex/releases
ARG CODEX_VERSION=0.162.1
# Keep in step with tofu_version in .github/workflows/tofu.yml
ARG TOFU_VERSION=1.13.9

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

# OpenTofu: fmt/validate/lock for infra/terraform only. No Cloudflare or state
# credentials here; plan and apply run in GitHub Actions.
RUN arch="$(dpkg --print-architecture)" \
    && base="https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}" \
    && file="tofu_${TOFU_VERSION}_linux_${arch}.tar.gz" \
    && cd /tmp \
    && curl -fsSLO "${base}/${file}" \
    && curl -fsSL "${base}/tofu_${TOFU_VERSION}_SHA256SUMS" | grep " ${file}\$" | sha256sum -c - \
    && tar -xzf "${file}" -C /usr/local/bin tofu \
    && rm "${file}" \
    && tofu version

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
