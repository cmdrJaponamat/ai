# Исправление тестового startup script машинного VPN

**Дата:** 2026-11-03. **Статус:** исправлено; повторный стартовый тест AL-TEST успешен.

## Причина

- AL-TEST загрузился 13:56:50, получил компьютерную GPO с DC1 в 13:57:10, а GroupPolicy/Operational зарегистрировал запуск Startup script в 13:57:14.
- Первоначально `WS-TEST-DEV-VPN` ссылалась на пользовательский диск `S:\IT\kuznetsov\tmp\vpn-gpo-canary.cmd`, недоступный `SYSTEM` при старте. Владелец перенастроил её на `\\aurora-logistics.local\SYSVOL\aurora-logistics.local\scripts\vpn-gpo-canary.cmd`. Файл отчёта после этого создался от `SYSTEM`; Site, DC1 и SYSVOL доступны.
- Вывод `ipconfig` содержит справку, потому что `^|` внутри блока скрипта передано `ipconfig` как аргумент. При чтении OEM-вывода через PowerShell без `-Encoding OEM` русские строки отображаются неверно.
- Поиск `scripts.ini` в SYSVOL показал единственную ссылку на этот файл — GPO `{B3FD8456-32F0-49B5-A43E-B4FE72648FB7}` (`WS-TEST-DEV-VPN`).

## Изменение и проверка

- На DC1 исходный файл скопирован в `C:\ProgramData\Aurora\GPOBackups\vpn-gpo-canary-20261103-before-ipconfig-fix.cmd`.
- В `C:\Windows\SYSVOL\sysvol\aurora-logistics.local\scripts\vpn-gpo-canary.cmd` только строка `ipconfig ^| findstr ...` заменена на `ipconfig`; остальная логика сохранена. SHA-256 после записи и через `\\aurora-logistics.local\SYSVOL\aurora-logistics.local\scripts\vpn-gpo-canary.cmd` совпал: `5EA9BA929864A0190EED4BF582532FBCC4FCE76CC375D933836C9410E83D5C5D`.
- По выводу клиента до исправления: скрипт уже создал отчёт от `NT AUTHORITY\\SYSTEM`, `nltest` вернул `SITE-SPB-DC` и DC1, SYSVOL доступен (`True`). Проверка IP в отчёте была ошибочной из-за синтаксиса.
- Повторный холодный старт AL-TEST: загрузка Windows `14:15:04`; сервер OpenVPN подтвердил сертификат компьютера и выдал `10.253.91.3` в `14:15:20`; исправленный startup script записал отчёт `14:15:30` (файл `14:15:31`) от `SYSTEM`. Отчёт содержит адаптер OpenVPN Data Channel Offload с `10.253.91.3/24`, `SITE-SPB-DC`, DC1 `10.78.3.50` и `SYSVOL=True`. Порядок «VPN → DC → startup script» подтверждён.
- Русский вывод команд в `startup.txt` записан в OEM-кодировке; читать его в Windows PowerShell 5.1 командой `Get-Content 'C:\ProgramData\Aurora\VpnPilot\startup.txt' -Encoding OEM`.
- Дополнительная проверка: у `WS-TEST-DEV-VPN` сейчас `Authenticated Users` имеет `GpoApply`; GPO связана с `OU=TEST`, где пять ПК. Если целью был только AL-TEST, Security Filtering нужно сузить. GPO `WS-VPNCertAutoenroll` существует, но не входит в применённые к AL-TEST политики по предоставленному `gpresult`.

## Откат

Вернуть сохранённую копию на DC1 в исходный путь SYSVOL. Перезапуск служб и перезагрузка DC не требуются; AL-TEST нужно перезагрузить для нового startup-теста.
