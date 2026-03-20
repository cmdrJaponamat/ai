# Environment Migration Plan

Date: 2026-03-20
Topic: moving current OS/user environment to another PC via git

## Goal

- Recreate the working environment on another Linux machine with minimal manual steps.
- Keep machine-specific hardware details out of the core repo as much as possible.
- Avoid dependence on the current broken home path layout.

## Constraints

- Current storage layout includes symlinked and legacy paths such as `~/study -> /home/home/japonamat/study`.
- Some current config state is mixed between:
  - `~/.config`
  - `~/dotfiles`
  - user home files
- Hardware-dependent settings must not dominate the portable setup.

## Direction

Use `~/dotfiles` as the canonical migration project.

It should eventually contain:

- portable configs;
- bootstrap scripts for package install and symlink setup;
- systemd user unit setup;
- optional machine overlays for host-specific settings.

## Recommended Structure

- portable base config tracked in `~/dotfiles`
- bootstrap scripts for:
  - package install
  - config linking
  - user service enablement
- machine-specific overlays in separate files not required for core setup

## Path Strategy

- Prefer deriving all paths from `$HOME`.
- Avoid hardcoding `/home/home/...`.
- Where legacy paths still exist, document them and progressively migrate to clean paths.
- Keep migration helpers tolerant of both current and future path layouts.

## Hardware Strategy

- Split settings into:
  - portable defaults
  - optional hardware overlays
- Examples of hardware-bound areas:
  - monitor layout
  - audio device names
  - GPU-specific tweaks
  - battery or power tuning

## Next Steps

- inventory what in `~/dotfiles` is already portable;
- identify host-specific pieces;
- design bootstrap scripts for a fresh machine;
- define one canonical install path model based on `$HOME`.
