# Split Keyboard RMK Bring-Up

Date: 2026-04-15
Scope: RMK firmware bring-up for a handwired split keyboard right half

## Problem

The right half of a custom split keyboard is soldered and needs RMK firmware tooling plus an initial smoke-test firmware.

## Findings

- Controller: SuperMini / Pro Micro-compatible nRF52840.
- Right half matrix: 5 rows x 7 columns.
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
- Configured a 5x7 right-half keymap derived from the KLE JSON.
- Corrected the initial mistaken left-half diagnostic keymap to right-half base keys: `6 7 8 9 0`, `Y U I O P [ ]`, `H J K L ; ' \`, `N M , . /`, plus `Backspace`, `MO(1)`, `Enter`, and `LGui`.
- Generated RMK project at `/home/admin-al/split-keyboard-rmk/generated`.
- Enabled `[ble]` and explicit `[storage]` settings for nRF52840:
  - `start_addr = 0xA0000`
  - `num_sectors = 32`
  This is required because the generated nRF52840 RMK template enables BLE-related Rust features, and the RMK macro unwraps BLE config during compile time.

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
- `rmkit get-project-name --keyboard-toml-path keyboard.toml` returns `Split_Keyboard_Right_Test`.
- `vial.json` passes `jq empty`.
- `cargo make build` in the generated project passes.

## Blocker

`cargo make uf2 --release` requires `cargo-binutils` and `cargo-hex-to-uf2`. The assistant sandbox cannot install them because DNS resolution for `index.crates.io` fails there.

## Next Steps

From a normal terminal:

```bash
cd /home/admin-al/split-keyboard-rmk/generated
source "$HOME/.cargo/env"
cargo install cargo-binutils cargo-hex-to-uf2
cargo make uf2 --release
```

Then copy `Split_Keyboard_Right_Test.uf2` to the controller bootloader USB drive.

## Verification

- Local config files exist.
- RMK can parse chip and project name from `keyboard.toml`.
- `vial.json` is valid JSON.
- Firmware build passes.
- UF2 generation is pending on installing the two cargo helper tools in a normal terminal.

## Rollback

- Remove `/home/admin-al/split-keyboard-rmk` if the generated RMK project is not needed.
- Toolchain rollback is manual: remove rustup-managed Rust from `~/.cargo` and `~/.rustup` only if no longer needed.

## Relogin/Reboot

No reboot required. New shells may need `source "$HOME/.cargo/env"` or PATH setup for `~/.cargo/bin`.
