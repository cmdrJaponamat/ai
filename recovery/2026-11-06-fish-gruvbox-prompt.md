# Fish Gruvbox prompt

Date: 2026-11-06
Host: AL-KUZNETSOV-DE

## Problem

Fish printed an error because `~/.config/fish/conf.d/omf.fish` sourced a missing Oh My Fish installation. The requested prompt should use Powerline segments in Gruvbox colors.

## Findings

- `~/.config/fish` is a symlink to `~/dotfiles/fish`.
- Oh My Fish is absent; fish 4.9.3 and JetBrainsMono Nerd Font are present.
- `fish/config.fish` and `fish/functions/pokemon-colorscripts.fish` already had unrelated local changes; they were preserved.

## Changes

- Guarded the OMF source command with a file existence check in `fish/conf.d/omf.fish`.
- Added `fish/functions/fish_prompt.fish`: Gruvbox path and Git branch segments with Powerline arrows, dirty worktree marker, and nonzero exit status.

## Verification

- `fish -n` passed for both changed fish files.
- `fish -c` displayed the prompt inside and outside a Git repository, including dirty and nonzero status states, without OMF errors.
- `fish -ic` started without OMF errors.
- `git diff --check` passed.

## Rollback

Revert the two changed fish files in `~/dotfiles` with `git revert` of the dedicated commit. A new fish session will pick up the previous prompt.

## Relogin / Restart / Reboot

Open a new fish session to see the prompt. No relogin, service restart, or reboot is required.
