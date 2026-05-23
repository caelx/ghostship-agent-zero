# syntax=docker/dockerfile:1.7

FROM agent0ai/agent-zero:latest

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false \
    DISPLAY=:99 \
    GH_PROMPT_DISABLED=1 \
    DOCKER_HOST=unix:///var/run/docker.sock \
    DOCKERD_STORAGE_DRIVER=overlay2 \
    DOCKERD_STORAGE_FALLBACK=true \
    DOCKERD_DATA_ROOT=/var/lib/docker

ENV PATH=/nix/var/nix/profiles/default/bin:$PATH

COPY scripts/ /tmp/ghostship/

RUN chmod +x /tmp/ghostship/*.sh /tmp/ghostship/*.py

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    /tmp/ghostship/install-tools.sh apt

RUN --mount=type=cache,target=/root/.npm \
    /tmp/ghostship/install-tools.sh npm

RUN --mount=type=cache,target=/root/.cache/uv \
    /tmp/ghostship/install-tools.sh uv

RUN /tmp/ghostship/install-tools.sh github

RUN /tmp/ghostship/install-tools.sh nix

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    /tmp/ghostship/install-tools.sh docker

RUN install -m 0755 /tmp/ghostship/entrypoint-dind.sh /usr/local/bin/ghostship-entrypoint-dind

RUN rm -rf /tmp/ghostship

ENTRYPOINT ["/usr/local/bin/ghostship-entrypoint-dind"]
CMD ["/exe/initialize.sh", "$BRANCH"]
