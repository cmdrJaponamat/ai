# Обновление TrueConf, 2026-10-03

## Проблема

`yay` завершил обновление с ошибкой `trueconf - exit status 1` после удаления временной зависимости `udf-http-range-proxy`. Пользователь предположил, что мешают остатки прошлой установки.

## Выводы и действия

- Установленный `trueconf 8.6.0.1717-1` был цел; его файлы принадлежали пакету. `udf-http-range-proxy` уже удалён.
- В `~/.cache/yay/trueconf-client/` найден собранный пакет `trueconf-8.6.0.1978-1-x86_64.pkg.tar.zst`. Его зависимости установлены.
- Установлен этот пакет командой `pkexec pacman -U --noconfirm /home/japonamat/.cache/yay/trueconf-client/trueconf-8.6.0.1978-1-x86_64.pkg.tar.zst`. Ручной очистки файлов не потребовалось.
- Обновлён системный инвентарь командой `~/.local/bin/ai-system-inventory refresh`.

## Проверка

- `pacman -Q trueconf`: `8.6.0.1978-1`.
- `pacman -Qkk trueconf`: 165 файлов, 0 изменённых.
- `pacman -Qo /opt/trueconf/client/TrueConf`: файл принадлежит `trueconf 8.6.0.1978-1`.
- Инвентарь пакетов свежий. Запуск графического приложения не проверялся.

## Откат

Предыдущий пакет сохранён в `~/.cache/yay/trueconf-client/trueconf-8.6.0.1717-1-x86_64.pkg.tar.zst`; при необходимости установить его через `pkexec pacman -U` с полным путём. Повторный вход или перезагрузка не нужны.
