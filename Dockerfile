# syntax=docker/dockerfile:1.7

FROM agent0ai/agent-zero:latest

ARG BITWARDEN_PLUGIN_REPO=https://github.com/caelx/a0-bitwarden-plugin.git
ARG CLOAKBROWSER_PLUGIN_REPO=https://github.com/caelx/a0-cloakbrowser-plugin.git
ARG OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-ollama-cloud-provider-plugin.git
ARG OPENCODE_GO_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-opencode-go-provider-plugin.git
ARG NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git
ARG OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git
ARG OPENROUTER_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-openrouter-free-provider-plugin.git
ARG BITWARDEN_PLUGIN_REV=latest
ARG CLOAKBROWSER_PLUGIN_REV=latest
ARG OLLAMA_CLOUD_PROVIDER_PLUGIN_REV=latest
ARG OPENCODE_GO_PROVIDER_PLUGIN_REV=latest
ARG NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REV=latest
ARG OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REV=latest
ARG OPENROUTER_FREE_PROVIDER_PLUGIN_REV=latest

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false \
    CLOAKBROWSER_PLUGIN_REPO=${CLOAKBROWSER_PLUGIN_REPO} \
    DISPLAY=:99 \
    GH_PROMPT_DISABLED=1 \
    BITWARDEN_PLUGIN_REPO=${BITWARDEN_PLUGIN_REPO} \
    OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO=${OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO} \
    OPENCODE_GO_PROVIDER_PLUGIN_REPO=${OPENCODE_GO_PROVIDER_PLUGIN_REPO} \
    NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO=${NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO} \
    OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO=${OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO} \
    OPENROUTER_FREE_PROVIDER_PLUGIN_REPO=${OPENROUTER_FREE_PROVIDER_PLUGIN_REPO}

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

RUN printf '%s\n' \
    "bitwarden=${BITWARDEN_PLUGIN_REV}" \
    "cloakbrowser=${CLOAKBROWSER_PLUGIN_REV}" \
    "provider_ollama_cloud=${OLLAMA_CLOUD_PROVIDER_PLUGIN_REV}" \
    "provider_opencode_go=${OPENCODE_GO_PROVIDER_PLUGIN_REV}" \
    "provider_nvidia_build_free=${NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REV}" \
    "provider_opencode_zen_free=${OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REV}" \
    "provider_openrouter_free=${OPENROUTER_FREE_PROVIDER_PLUGIN_REV}" \
    > /tmp/ghostship/plugin-revisions.txt

RUN --mount=type=cache,target=/root/.npm \
    /tmp/ghostship/setup-agent-zero-plugin.sh bitwarden BITWARDEN_PLUGIN_REPO

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip \
    /tmp/ghostship/setup-agent-zero-plugin.sh cloakbrowser CLOAKBROWSER_PLUGIN_REPO setup --noninteractive --force

RUN /tmp/ghostship/patch-browser-ui.py

RUN if [ -f /etc/supervisor/conf.d/cloakbrowser_xvfb.conf ] \
    && ! grep -q 'program:cloakbrowser_xvfb' /etc/supervisor/conf.d/supervisord.conf; then \
        printf '\n' >> /etc/supervisor/conf.d/supervisord.conf; \
        cat /etc/supervisor/conf.d/cloakbrowser_xvfb.conf >> /etc/supervisor/conf.d/supervisord.conf; \
    fi

RUN /tmp/ghostship/setup-agent-zero-plugin.sh provider_ollama_cloud OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO \
    && /tmp/ghostship/setup-agent-zero-plugin.sh provider_opencode_go OPENCODE_GO_PROVIDER_PLUGIN_REPO \
    && /tmp/ghostship/setup-agent-zero-plugin.sh provider_nvidia_build_free NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO \
    && /tmp/ghostship/setup-agent-zero-plugin.sh provider_opencode_zen_free OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO \
    && /tmp/ghostship/setup-agent-zero-plugin.sh provider_openrouter_free OPENROUTER_FREE_PROVIDER_PLUGIN_REPO

RUN rm -rf /tmp/ghostship
