# syntax=docker/dockerfile:1.7

FROM agent0ai/agent-zero:latest

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false

COPY scripts/ /tmp/ghostship/

RUN chmod +x /tmp/ghostship/*.sh /tmp/ghostship/*.py

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    /tmp/ghostship/install-tools.sh apt

RUN --mount=type=cache,target=/root/.npm \
    /tmp/ghostship/install-tools.sh npm

RUN --mount=type=cache,target=/root/.cache/uv \
    /tmp/ghostship/install-tools.sh uv

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/uv \
    /tmp/ghostship/install-playwright-cloakbrowser.sh

RUN /tmp/ghostship/patch-browser-runtime.py \
      /a0/plugins/_browser/helpers/runtime.py \
      /git/agent-zero/plugins/_browser/helpers/runtime.py \
    && rm -rf \
      /tmp/ghostship \
      /a0/usr/plugins/_browser/playwright \
      /git/agent-zero/usr/plugins/_browser/playwright
