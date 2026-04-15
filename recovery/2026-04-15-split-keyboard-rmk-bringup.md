# Split Keyboard RMK Bring-Up

Date: 2026-04-15
Scope: RMK firmware bring-up for a handwired split keyboard left half

## Problem

The left half of a custom split keyboard is soldered and needs RMK firmware tooling plus an initial smoke-test firmware.

## Findings

- Controller: SuperMini / Pro Micro-compatible nRF52840.
- Left half matrix: 5 rows x 7 columns.
- Diodes are on rows; initial assumption is `col2row`.
- Rows, top to bottom:
  - D2 = P0.17
  - D3 = P0.20
  - D4 = P0.22
  - D5 = P0.24
  - D6 = P1.00
- Columns, soldered order:
  - D7 = P0.11
  - D8 = P1.04
  - D9 = P1.06
  - D10 = P0.09
  - D16 = P1.10
  - D14 = P1.11
  - D15 = P1.13

## Changes Made

- Created `/home/admin-al/split-keyboard-rmk`.
- Added initial RMK source config files:
  - `/home/admin-al/split-keyboard-rmk/keyboard.toml`
  - `/home/admin-al/split-keyboard-rmk/vial.json`
  - `/home/admin-al/split-keyboard-rmk/README.md`
- Configured a diagnostic 5x7 left-half keymap for matrix testing.

## Toolchain State

- Rust was switched to official rustup-managed toolchain by the user.
- Verified in assistant session:
  - `rustc 1.94.1`
  - `cargo 1.94.1`
  - target `thumbv7em-none-eabihf` installed
  - `rmkit 0.0.21` installed
  - `cargo-make 0.37.24` installed
  - `flip-link` installed
  - `dfu-util 0.11` installed
- `rmkit get-chip --keyboard-toml-path keyboard.toml` returns `nrf52840`.
- `rmkit get-project-name --keyboard-toml-path keyboard.toml` returns `Split_Keyboard_Left_Test`.
- `vial.json` passes `jq empty`.

## Blocker

`rmkit init` cannot download `https://github.com/HaoboGu/rmk-template/archive/refs/heads/main.zip` from the assistant sandbox because DNS resolution for GitHub fails there. Run `rmkit create` or `rmkit init` from a normal terminal with working DNS.

## Next Steps

From a normal terminal:

```bash
cd /home/admin-al/split-keyboard-rmk
source "$HOME/.cargo/env"
rmkit create --keyboard-toml-path keyboard.toml --vial-json-path vial.json --target-dir generated
```

Then inspect generated build instructions and build the left-half smoke-test firmware.

## Verification

- Local config files exist.
- RMK can parse chip and project name from `keyboard.toml`.
- `vial.json` is valid JSON.
- Firmware generation has not completed yet because the template download is blocked in the assistant sandbox.

## Rollback

- Remove `/home/admin-al/split-keyboard-rmk` if the generated RMK project is not needed.
- Toolchain rollback is manual: remove rustup-managed Rust from `~/.cargo` and `~/.rustup` only if no longer needed.

## Relogin/Reboot

No reboot required. New shells may need `source "$HOME/.cargo/env"` or PATH setup for `~/.cargo/bin`.
