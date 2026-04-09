FROM mcr.microsoft.com/devcontainers/base:debian

# 1. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Install tmux, node, and unzip (required for Bun)
RUN apt-get update && apt-get install -y tmux nodejs npm unzip curl

# 3. Install Bun globally
RUN curl -fsSL https://bun.sh/install | bash && \
    mv /root/.bun/bin/bun /usr/local/bin/bun && \
    ln -s /usr/local/bin/bun /usr/local/bin/bunx

# 4. Install OpenCode as the VSCODE user
# This ensures ~/.opencode is created in /home/vscode, not /root
USER vscode
RUN curl -fsSL https://opencode.ai/install | bash

# 5. Switch back to root if you need to do more system setup, 
# but usually, you can stay as vscode now.
USER root

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]