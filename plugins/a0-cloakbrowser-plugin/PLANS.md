# Plans

## CloakBrowser Plugin v1

- Build a normal GitHub-installable Agent Zero plugin named `cloakbrowser`.
- Keep upstream `_browser` as the only Browser tool.
- Patch only the Playwright launch boundary and shadow-DOM runtime behavior process-locally when the plugin is enabled.
- Resolve setup state from upstream `helpers.plugins.find_plugin_dir("cloakbrowser")`.
- Install CloakBrowser, display dependencies, Xvfb support, and only user-enabled unpacked extensions through explicit setup.
- Keep setup, disable, and uninstall idempotent; cleanup stale `/a0/usr/plugins/cloakbrowser*` roots.
