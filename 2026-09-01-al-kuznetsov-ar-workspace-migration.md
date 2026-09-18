# Перенос рабочих контекстов на AL-KUZNETSOV-AR

Дата: 2026-09-01

## Цель

Подготовить новый ноутбук `AL-KUZNETSOV-AR` (`192.168.203.174`) для работы с
текущими контекстами, разработками и operational trail.

## Перенесено

Под пользователем `admin-al` переданы целиком, с Git-метаданными и
незакоммиченными файлами:

- `/home/admin-al/ai`;
- `/home/admin-al/dotfiles`;
- `/home/admin-al/assistant`;
- `/home/admin-al/ansible_al`;
- `/home/admin-al/pve-backup-validator`.

Перед заменой существующий target-каталог `dotfiles` сохранён как
`/home/admin-al/dotfiles.pre-migration-20260901-154803`.

Не переносились `~/.ssh`, состояние/авторизация Codex и пользовательские
кэши. Ключи и токены должны быть созданы или перенесены отдельно по явному
решению владельца.

Дополнительно, как зависимости рабочих проектов, перенесены:

- `/home/admin-al/apps`, `audit`, `scripts`, `split-keyboard-rmk`, `work`;
- `/home/admin-al/yandex-cloud`, `.cargo`, `.rustup`;
- `~/.config/assistant`, `~/.config/systemd/user`,
  `~/.local/bin/codex-ai-admin`;
- `.bashrc`, `.profile`, `.bash_profile` для PATH Cargo, Yandex Cloud и
  локальных команд.

На target симлинки `~/.config/nvim`, `alacritty`, `fish` приведены к
источнику истины в `~/dotfiles`. Предыдущие target-каталоги сохранены в
`/home/admin-al/pre-live-config-migration-20260901-165356`; предшествующие
зависимые пути — в `/home/admin-al/pre-dependent-migration-20260901-162515`;
предыдущие startup-файлы — в `/home/admin-al/pre-shell-migration-*`.

User units перенесены вместе с enablement-ссылками, но не запускались и не
включались заново.

## Проверка

- `rsync -aHAXn --itemize-changes` для всех пяти каталогов не вывел различий.
- Для `ai`, `dotfiles`, `assistant`, `ansible_al` совпадают Git HEAD и SHA-256
  вывода `git status --porcelain`.
- На target уже доступен `codex-cli 0.152.0`.
- Из нового Bash login shell разрешаются `cargo`, `rustc`, `yc` и
  `codex-ai-admin`.

## Откат

На target, только после сохранения новой работы:

```bash
mv ~/dotfiles ~/dotfiles.migrated-rollback
mv ~/dotfiles.pre-migration-20260901-154803 ~/dotfiles
```

Остальные перенесённые каталоги можно удалить только вручную и адресно;
исходный ноутбук и его данные не изменялись.

Чтобы откатить live-конфиги, сначала вернуть их из
`pre-live-config-migration-20260901-165356`, затем удалить симлинки. Для
toolchain, shell и systemd user-конфигурации восстановить соответствующие
пути из `pre-dependent-migration-20260901-162515` и
`pre-shell-migration-*`.

Перелогин, перезапуск сервисов и перезагрузка не требуются.
