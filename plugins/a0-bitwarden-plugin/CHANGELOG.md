# Changelog

## 1.0.3

- Add full Agent Zero lifecycle commands for install, update, enable, disable, status, and reconcile.
- Align CI with vanilla Agent Zero API install, toggle, config, execute, and delete flows.

## 1.0.2

- Run plugin-managed cleanup when the Bitwarden plugin is disabled or uninstalled through Agent Zero.
- Preserve custom MCP entries, user-edited skills, global npm packages, Bitwarden CLI data, and vault contents during cleanup.

## 1.0.1

- Make the Execute button run idempotent setup/repair and then report human-readable status.
- Add `--json` for CI and troubleshooting output.
