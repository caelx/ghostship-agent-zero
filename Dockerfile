# syntax=docker/dockerfile:1.7

FROM agent0ai/agent-zero:latest

ARG BITWARDEN_PLUGIN_REPO=https://github.com/caelx/a0-bitwarden-plugin.git
ARG CLOAKBROWSER_PLUGIN_REPO=https://github.com/caelx/a0-cloakbrowser-plugin.git

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false \
    CLOAKBROWSER_PLUGIN_REPO=${CLOAKBROWSER_PLUGIN_REPO} \
    DISPLAY=:99 \
    GH_PROMPT_DISABLED=1 \
    BITWARDEN_PLUGIN_REPO=${BITWARDEN_PLUGIN_REPO}

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

RUN --mount=type=cache,target=/root/.npm \
    plugin_dir="$(cd /a0 && /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py bitwarden BITWARDEN_PLUGIN_REPO)" \
    && cd "$plugin_dir" \
    && /opt/venv-a0/bin/python execute.py setup --noninteractive \
    && mkdir -p /a0/usr/plugins \
    && if [ "$plugin_dir" != "/a0/usr/plugins/bitwarden" ]; then \
      rm -rf /a0/usr/plugins/bitwarden; \
      cp -a "$plugin_dir" /a0/usr/plugins/bitwarden; \
    fi

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip \
    plugin_dir="$(cd /a0 && /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py cloakbrowser CLOAKBROWSER_PLUGIN_REPO)" \
    && cd "$plugin_dir" \
    && /opt/venv-a0/bin/python execute.py setup --noninteractive \
    && mkdir -p /a0/usr/plugins \
    && if [ "$plugin_dir" != "/a0/usr/plugins/cloakbrowser" ]; then \
      rm -rf /a0/usr/plugins/cloakbrowser; \
      cp -a "$plugin_dir" /a0/usr/plugins/cloakbrowser; \
    fi

COPY usr/plugins/ /tmp/ghostship-plugins/

RUN mkdir -p /git/agent-zero/usr/plugins /a0/usr/plugins \
    && cp -a /tmp/ghostship-plugins/. /git/agent-zero/usr/plugins/ \
    && cp -a /tmp/ghostship-plugins/. /a0/usr/plugins/ \
    && rm -rf /tmp/ghostship /tmp/ghostship-plugins
