# syntax=docker/dockerfile:1.7

FROM agent0ai/agent-zero:latest

ARG GHOSTSHIP_CACHE_BUST=local

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false \
    BITWARDENCLI_APPDATA_DIR=/a0/usr/bitwarden-cli

COPY scripts/ /tmp/ghostship/

RUN chmod +x /tmp/ghostship/*.sh /tmp/ghostship/*.py

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    test -n "$GHOSTSHIP_CACHE_BUST" \
    && /tmp/ghostship/install-tools.sh apt

RUN --mount=type=cache,target=/root/.npm \
    test -n "$GHOSTSHIP_CACHE_BUST" \
    && /tmp/ghostship/install-tools.sh npm

RUN --mount=type=cache,target=/root/.cache/uv \
    test -n "$GHOSTSHIP_CACHE_BUST" \
    && /tmp/ghostship/install-tools.sh uv

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/uv \
    test -n "$GHOSTSHIP_CACHE_BUST" \
    && /tmp/ghostship/install-playwright-cloakbrowser.sh

RUN test -n "$GHOSTSHIP_CACHE_BUST" \
    && /tmp/ghostship/install-ublock-origin-lite.py /usr/local/share/ublock-origin-lite

RUN /tmp/ghostship/patch-browser-runtime.py /git/agent-zero/plugins/_browser/helpers/runtime.py \
    && if [ -f /a0/plugins/_browser/helpers/runtime.py ]; then \
      /tmp/ghostship/patch-browser-runtime.py /a0/plugins/_browser/helpers/runtime.py; \
    fi \
    && rm -rf \
      /tmp/ghostship \
      /a0/usr/plugins/_browser/playwright \
      /git/agent-zero/usr/plugins/_browser/playwright
