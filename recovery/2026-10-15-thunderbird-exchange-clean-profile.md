# Thunderbird: чистый профиль для проверки Exchange IMAP

Дата: 2026-10-15 09:08 MSK  
Статус: ожидается ручная проверка подключения

## Проблема

Thunderbird сообщал об отказе пароля для Exchange IMAP, но OWA с тем же
паролем работал. В диагностическом IMAP protocol log на SPB-MX3 была только
последовательность `OpenSession -> CAPABILITY (OK) -> CloseSession`, без
`AUTH` или `LOGIN`. Следовательно, пароль не доходил до Exchange.

## Что изменено

- Thunderbird на рабочем ПК был остановлен; на момент операции процессов не
  было.
- Сохранена полная копия исходного профиля
  `~/.thunderbird/27fy9wau.default-release` в
  `~/.thunderbird/27fy9wau.default-release.backup-20261015-090739`.
- Создан отдельный пустой профиль `exchange-clean` в
  `~/.thunderbird/exchange-clean`.
- После проверки, что прежний экземпляр Thunderbird закрыт, `exchange-clean`
  назначен профилем по умолчанию для обычного запуска Thunderbird.
- Он запущен изолированно как transient user service
  `thunderbird-exchange-clean.service` с командой
  `thunderbird --no-remote -P exchange-clean`; это сохраняет окно после
  завершения терминальной команды.

Ни исходный профиль, ни сохранённые пароли, ни настройки Exchange не
изменялись.

## Проверка

- `thunderbird` установлен в `/usr/bin/thunderbird`.
- User unit `thunderbird-exchange-clean.service` активен, а его основной
  процесс запущен с параметрами `--no-remote -P exchange-clean`.
- Свободное пространство до копирования: 701 GiB; исходный профиль: 3.0 GiB.

## Следующий шаг

В новом профиле добавить только проблемный ящик вручную, не импортируя
настройки старого профиля. Использовать `mail.aurora-logistics.ru`, IMAP
`993`, `SSL/TLS`, аутентификацию «Обычный пароль» и полный адрес почты как
имя пользователя. SMTP указывать по действующей корпоративной схеме.

Если подключение в новом профиле работает, причина находится в старом
профиле или его локальном окружении. Если вновь нет AUTH/LOGIN, собрать
точный текст ошибки Thunderbird и отдельно проверить локальный TLS-inspection,
прокси и расширения.

## Откат

Обычный запуск Thunderbird уже возвращён к исходному профилю
`default-release` (`27fy9wau.default-release`). Для повторного переключения
на чистый профиль изменить строку `Default` в секции `Install...` файла
`~/.thunderbird/profiles.ini` с `27fy9wau.default-release` на
`exchange-clean`, затем открыть Thunderbird обычным способом.
Для удаления чистого профиля позднее сначала закрыть Thunderbird, затем удалить
только секцию `exchange-clean` из `profiles.ini` и каталог
`~/.thunderbird/exchange-clean`; резервную копию старого профиля сохранять до
подтверждённой стабилизации.

Перелогин или перезагрузка не требуются.
