FROM mcr.microsoft.com/devcontainers/base:debian

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 1. Install tmux, node, unzip, and Playwright OS dependencies for Chromium
# Grouping apt-get commands is a Docker best practice to reduce image size
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    tmux nodejs npm unzip curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install Bun globally
RUN curl -fsSL https://bun.sh/install | bash && \
    mv /root/.bun/bin/bun /usr/local/bin/bun && \
    ln -s /usr/local/bin/bun /usr/local/bin/bunx

# 3. Bake Playwright Chromium into the image globally
# This prevents downloading ~150MB on every single rebuild
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN npx -y playwright@latest install chromium \
    && chmod -R 777 /ms-playwright

# 4. Install OpenCode as the VSCODE user
USER vscode
RUN curl -fsSL https://opencode.ai/install | bash

# 5. Devcontainers default to the remoteUser (vscode) upon startup,
# but switching back to root at the end of a Dockerfile is standard practice.
USER root

CMD ["sleep", "infinity"]