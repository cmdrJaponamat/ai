# Восстановление выполнения команд QEMU Guest Agent на AL-VEEAM

## Проблема и диагностика

20.10.2026 на VM 131 `spb-veeam` (AL-VEEAM, `10.78.20.99`) QEMU Guest Agent отвечал на ping, сетевые и файловые запросы. `guest-info` сообщил версию 108.0.2 и объявил `guest-exec` включённым. Но запуск даже `C:\Windows\System32\cmd.exe /c echo ...` через `qm guest exec` и прямой API PVE завершался: `Failed to execute helper program (No such file or directory)`.

Через безопасный QGA file-read подтверждено, что существует
`C:\Program Files\qemu-ga\qemu-ga.exe`, но отсутствует
`C:\Program Files\qemu-ga\gspawn-win64-helper.exe`. Этот helper обязателен для
Windows GLib `g_spawn`, которым QGA реализует `guest-exec`; без него запуск
любого процесса невозможен. Это не ошибка пути PowerShell, Veeam или PVE.

## План исправления

Взять только `gspawn-win64-helper.exe` из официального `qemu-ga-x86_64.msi`
версии 108.0.2-1.el9 (соответствует установленному агенту), записать его через
поддерживаемый QGA file-write прямо в каталог QGA и немедленно проверить
`guest-exec`. Не менять Veeam jobs, службу Veeam, сетевые настройки или Exchange.

## Откат

Если проверка после записи неуспешна или обнаружена несовместимость, удалить
только добавленный `C:\Program Files\qemu-ga\gspawn-win64-helper.exe` через
интерактивную консоль Windows либо штатный reinstall MSI. Перезагрузка VM не
нужна: QGA ищет helper при каждом запуске дочернего процесса. Полный repair
MSI остаётся запасным вариантом, если одного файла недостаточно.

## Выполнение и результат

Из официального архива virtio-win извлечён именно matching-пакет
`qemu-ga-x86_64.msi` версии `108.0.2-1.el9`:

- MSI SHA-256: `22a80d9f715b0df944a1513496cae4258baa35f0eaa70b9abe22abfc6ca24841`;
- добавленный файл SHA-256:
  `86c624a9ff91d2d59de1b2bd1d4d58c7f0da0025d34fb8aa165ce101c62649bc`.

Файл записан только в `C:\Program Files\qemu-ga\gspawn-win64-helper.exe`
через QGA file-write. Перезагрузка VM и служб не выполнялась. Немедленная
проверка `qm guest exec 131 -- C:\Windows\System32\cmd.exe /c echo
QGA_EXEC_OK` завершилась с кодом 0 и вывела `QGA_EXEC_OK`. Канал выполнения
команд PVE → guest agent → AL-VEEAM восстановлен.
