# syntax=docker/dockerfile:1.7

FROM agent0ai/agent-zero:latest

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false \
    DISPLAY=:99 \
    GH_PROMPT_DISABLED=1 \
    A0_SET_mcp_servers='{"mcpServers":{"bitwarden":{"type":"stdio","command":"mcp-server-bitwarden","args":[],"disabled":false}}}'

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
    --mount=type=cache,target=/root/.cache/uv \
    /tmp/ghostship/install-playwright-cloakbrowser.sh

RUN /opt/venv-a0/bin/python - <<'PY'
import site
import shutil
from pathlib import Path

site_packages = Path(site.getsitepackages()[0])
shutil.copy2(
    "/tmp/ghostship/ghostship_cloakbrowser_playwright_shim.py",
    site_packages / "ghostship_cloakbrowser_playwright_shim.py",
)
(site_packages / "ghostship_cloakbrowser_playwright_shim.pth").write_text(
    "import ghostship_cloakbrowser_playwright_shim\n",
    encoding="utf-8",
)
PY

RUN python3 - <<'PY'
from pathlib import Path

path = Path("/etc/supervisor/conf.d/supervisord.conf")
config = path.read_text(encoding="utf-8")
if "[program:run_xvfb]" not in config:
    config += """

[program:run_xvfb]
command=/usr/bin/Xvfb :99 -screen 0 1440x960x24 -nolisten tcp
environment=
priority=10
stopwaitsecs=1
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
startretries=3
stopasgroup=true
killasgroup=true
"""
config = config.replace(
    "[program:run_ui]\ncommand=/exe/run_A0.sh\nenvironment=",
    "[program:run_ui]\ncommand=/exe/run_A0.sh\nenvironment=DISPLAY=\":99\"\npriority=20",
)
config = config.replace(
    "[program:run_tunnel_api]\ncommand=/exe/run_tunnel_api.sh\nenvironment=",
    "[program:run_tunnel_api]\ncommand=/exe/run_tunnel_api.sh\nenvironment=DISPLAY=\":99\"\npriority=20",
)
path.write_text(config, encoding="utf-8")
PY

RUN mkdir -p /opt/ghostship \
    && /tmp/ghostship/install-ublock-origin-lite.py /opt/ghostship/ublock-origin-lite \
    && /tmp/ghostship/install-chrome-web-store-extension.py edibdbjcniadpccecjdfdjjppcpchdlm /opt/ghostship/i-still-dont-care-about-cookies

COPY usr/plugins/ /tmp/ghostship-plugins/

RUN /tmp/ghostship/patch-browser-runtime.py /git/agent-zero/plugins/_browser/helpers/runtime.py \
    && if [ -f /a0/plugins/_browser/helpers/runtime.py ]; then \
      /tmp/ghostship/patch-browser-runtime.py /a0/plugins/_browser/helpers/runtime.py; \
    fi \
    && /opt/venv-a0/bin/python /tmp/ghostship/seed-cloakbrowser-playwright.py /git/agent-zero/usr/plugins/_browser/playwright \
    && /opt/venv-a0/bin/python /tmp/ghostship/seed-cloakbrowser-playwright.py /a0/usr/plugins/_browser/playwright \
    && mkdir -p /git/agent-zero/usr/plugins /a0/usr/plugins \
    && cp -a /tmp/ghostship-plugins/. /git/agent-zero/usr/plugins/ \
    && cp -a /tmp/ghostship-plugins/. /a0/usr/plugins/ \
    && mkdir -p /git/agent-zero/extensions/python/startup_migration \
    && cp /tmp/ghostship/seed-bitwarden-mcp-settings.py /git/agent-zero/extensions/python/startup_migration/_05_seed_bitwarden_mcp_settings.py \
    && cp /tmp/ghostship/seed-cloakbrowser-playwright.py /git/agent-zero/extensions/python/startup_migration/_06_seed_cloakbrowser_playwright.py \
    && cp /tmp/ghostship/seed-browser-extensions.py /git/agent-zero/extensions/python/startup_migration/_07_seed_browser_extensions.py \
    && if [ -d /a0/extensions/python/startup_migration ]; then \
      cp /tmp/ghostship/seed-bitwarden-mcp-settings.py /a0/extensions/python/startup_migration/_05_seed_bitwarden_mcp_settings.py; \
      cp /tmp/ghostship/seed-cloakbrowser-playwright.py /a0/extensions/python/startup_migration/_06_seed_cloakbrowser_playwright.py; \
      cp /tmp/ghostship/seed-browser-extensions.py /a0/extensions/python/startup_migration/_07_seed_browser_extensions.py; \
    fi \
    && rm -rf /tmp/ghostship /tmp/ghostship-plugins
