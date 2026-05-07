#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

run_bash_in_image 'test ! -e /tmp/ghostship'
run_bash_in_image 'test ! -e /opt/ghostship'
run_bash_in_image '! grep -R "Ghostship" /exe/run_A0.sh /exe/initialize.sh'
run_bash_in_image '! find / -xdev -type f \( -name install-tools.sh -o -name install-playwright-cloakbrowser.sh -o -name patch-browser-runtime.py \) -print -quit | grep .'

run_bash_in_image 'grep -q "Ghostship CloakBrowser humanize patch" /git/agent-zero/plugins/_browser/helpers/runtime.py'
run_bash_in_image 'grep -q "launch_persistent_context_async" /git/agent-zero/plugins/_browser/helpers/runtime.py'
run_bash_in_image 'grep -q "\"humanize\": True" /git/agent-zero/plugins/_browser/helpers/runtime.py'
run_bash_in_image '! grep -q "ensure_playwright_binary" /git/agent-zero/plugins/_browser/helpers/runtime.py'
run_bash_in_image 'if [ -f /a0/plugins/_browser/helpers/runtime.py ]; then grep -q "Ghostship CloakBrowser humanize patch" /a0/plugins/_browser/helpers/runtime.py; fi'
run_bash_in_image 'test ! -d /a0/usr/plugins/_browser/playwright'
run_bash_in_image 'test ! -d /git/agent-zero/usr/plugins/_browser/playwright'
