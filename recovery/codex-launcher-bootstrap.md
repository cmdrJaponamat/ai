# Загрузка Codex С Контекстом Из ~/ai

Дата: 2026-03-20
Постановка задачи:
- Нужен глобальный hotkey, который открывает терминал с Codex и заранее подгруженным постоянным контекстом из `~/ai/`.

Наблюдения:
- В роли Wayland-композитора используется `niri`, его живой конфиг лежит в `~/.config/niri/config.kdl`.
- `alacritty` установлен и доступен.
- `~/ai/WORKFLOW.md` уже содержит постоянные правила рабочего процесса.

Что сделано:
- Добавлен `~/ai/ASSISTANT_BOOTSTRAP.md` с общими стартовыми правилами для LLM.
- Добавлен `~/ai/PROJECT_CONTEXTS.md` как реестр ссылок на project recovery-файлы.
- Добавлен launcher-скрипт для запуска `codex` внутри `alacritty` с bootstrap-контекстом из `~/ai/`.
- Добавлена вспомогательная утилита для инициализации проекта, которая создает recovery-файл и регистрирует его в `~/ai/PROJECT_CONTEXTS.md`.
- Добавлен hotkey в `niri` для запуска launcher'а.
- Базовые правила оформлены в `~/ai/RULES.json` и `~/ai/RULES_HUMAN.md`.
- `~/ai` оформлен как отдельный git-репозиторий и запушен в `cmdrJaponamat/ai`.
- Для GitHub настроен отдельный automation key через alias `github-auto`, и репозитории `cmdrJaponamat` переведены на него.
- Добавлен отдельный JSON-driven launcher `~/.local/bin/codex-ai-launcher-json`.
- Для JSON-driven launcher добавлен отдельный hotkey `Mod+Shift+A`, не затрагивающий рабочий `Mod+Shift+C`.
- JSON-driven launcher теперь:
  - читает `~/ai/RULES.json`
  - использует `~/ai/projects.db`
  - предлагает выбор проекта через `rofi`
  - умеет режим `Без проекта`
  - умеет автоопределение проекта по текущему `cwd`
  - запускает `codex` из каталога выбранного проекта
  - подмешивает `.ai-recovery.md` только выбранного проекта
- Добавлен `~/ai/system_inventory.json` и `~/ai/system_inventory_human.md` как первичный кэш сведений о пакетах, версиях, бинарях и user services.
- Добавлен `~/.local/bin/ai-system-inventory` с командами:
  - `refresh`
  - `status`
  - `mark-stale <section> <reason>`
- Добавлен `~/.local/bin/ai-system-change`, который пишет system action в `~/ai/actions.log` и помечает system inventory как stale.
- Подготовлен переносимый `pacman` hook в `~/dotfiles/system/pacman-hooks/`, который после транзакции пакетов помечает секцию `package_versions` в inventory как stale.

Статус проверки:
- Пользователь подтвердил, что базовый hotkey работает.
- JSON-driven launcher синтаксически валиден и опирается на реальный индекс проектов.
- Старый и новый launcher разведены по разным hotkey и не мешают друг другу.
- `ai-system-inventory` поддерживает TTL, секционную invalidation и явный статус fresh/stale.
- `ai-system-change` работает и корректно ставит inventory в stale.
- Переносимый `pacman` hook лежит в репозитории, но live-install в `/etc/pacman.d/hooks` еще не выполнен, потому что для этого нужен root с интерактивным вводом пароля.

Следующие шаги:
- Довести JSON-driven launcher до поведения, при котором он сможет заменить старый путь без регрессий.
- Установить live `pacman` hook в `/etc/pacman.d/hooks` через root и проверить, что после реальной пакетной транзакции секция `package_versions` становится stale автоматически.
- Постепенно уточнить project recovery-файлы в реальных репозиториях.
