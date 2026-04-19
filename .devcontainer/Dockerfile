FROM mcr.microsoft.com/devcontainers/base:debian

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 1. Install tmux, node, unzip, and Playwright OS dependencies for Chromium
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    tmux nodejs npm unzip curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    libcairo2 libpango-1.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install Bun globally
RUN curl -fsSL https://bun.sh/install | bash && \
    mv /root/.bun/bin/bun /usr/local/bin/bun && \
    ln -s /usr/local/bin/bun /usr/local/bin/bunx

# 3. Prepare the global Playwright browser path
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p /ms-playwright && chmod 777 /ms-playwright

# 4. Install OpenCode as the VSCODE user
USER vscode
RUN curl -fsSL https://opencode.ai/install | bash

# 5. Switch back to root
USER root

CMD ["sleep", "infinity"]