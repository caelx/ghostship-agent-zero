# Agent Zero Plugin Installation Contract

This repo follows the plugin layout observed from a real `agent0ai/agent-zero:latest`
container using the upstream plugin installer API.

## Observed Runtime Layout

Agent Zero copies its repository from `/git/agent-zero` into `/a0` before the UI
starts. The UI process runs from `/a0`, and `helpers.files.get_base_dir()` must
resolve to `/a0` for plugin operations.

Observed through both ZIP and Git API installs:

- Custom plugins install under `/a0/usr/plugins/<plugin_name>`.
- Built-in plugins are resolved from `/a0/plugins/<plugin_name>`.
- The API returns plugin paths relative to `/a0`, for example
  `usr/plugins/provider_opencode_go`.
- ZIP installs create a non-git plugin directory.
- Git installs retain the plugin `.git` directory.

Do not import Agent Zero helpers from `/git/agent-zero` for plugin installation
or lifecycle work. That resolves user plugin paths under
`/git/agent-zero/usr/plugins`, which is not the runtime tree used by the UI.

## Installer API

All mutating API calls require a CSRF token. Call `GET /api/csrf_token` with an
`Origin` header that matches the Agent Zero URL, then send the returned token in
`X-CSRF-Token` while preserving the session cookie.

Install from Git:

```http
POST /api/plugins/_plugin_installer/plugin_install
Content-Type: application/json

{
  "action": "install_git",
  "git_url": "https://github.com/caelx/a0-example-plugin.git",
  "plugin_name": "example_plugin",
  "git_token": "",
  "thumbnail_url": ""
}
```

Install from ZIP:

```http
POST /api/plugins/_plugin_installer/plugin_install
Content-Type: multipart/form-data

action=install_zip
plugin_file=@plugin.zip
```

## Lifecycle API

Plugin list:

```http
POST /api/plugins_list
Content-Type: application/json

{"filter":{"custom":true,"builtin":false}}
```

Plugin config, toggle, execute, and delete use `POST /api/plugins`:

- `{"action":"get_default_config","plugin_name":"<name>"}`
- `{"action":"get_config","plugin_name":"<name>"}`
- `{"action":"save_config","plugin_name":"<name>","settings":{...}}`
- `{"action":"get_toggle_status","plugin_name":"<name>"}`
- `{"action":"toggle_plugin","plugin_name":"<name>","enabled":false}`
- `{"action":"run_execute_script","plugin_name":"<name>"}`
- `{"action":"delete_plugin","plugin_name":"<name>"}`

`delete_plugin` calls the plugin uninstall hook before removing the custom
plugin directory.

## Manual Install Helper Rule

Ghostship image builds do not install Agent Zero plugins by default. When using
repo helper scripts for manual installs, mirror the API implementation:

1. Make sure `/a0` contains the Agent Zero runtime tree.
2. Run from `cd /a0` with `/a0` first on `PYTHONPATH`.
3. Call upstream `plugins._plugin_installer.helpers.install.install_from_git`.
4. Resolve installed paths with `/a0` Agent Zero helpers.
5. Never manually copy plugin directories into place.
