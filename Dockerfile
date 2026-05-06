FROM agent0ai/agent-zero:latest

ENV CLOAKBROWSER_CACHE_DIR=/opt/cloakbrowser \
    CLOAKBROWSER_AUTO_UPDATE=false

COPY scripts/install-tools.sh /tmp/ghostship/install-tools.sh
RUN bash /tmp/ghostship/install-tools.sh && rm -rf /tmp/ghostship

COPY overlay/ /

RUN chmod +x \
      /ins/install_playwright.sh \
      /exe/run_A0.sh \
      /opt/ghostship/apply-overlay.sh \
      /opt/ghostship/patch-browser-runtime.py \
    && bash /ins/install_playwright.sh local \
    && rm -rf /a0/usr/plugins/_browser/playwright /git/agent-zero/usr/plugins/_browser/playwright
