# Exchange: первая волна Online Archive для MailBoxDB_AL_new

Дата: 2026-11-11 MSK. Владелец прямо поручил включить архивы по утверждённому списку `/home/admin-al/assistant/notes/projects/aurora-logistics-mail/exchange-database-reorganisation/archive-wave-01-mailboxdb-al-new-2026-11-11.md`.

## Предоперационная проверка

- В списке 20 уникальных действующих UserMailbox: 12 назначены в `DB-ARCH-01`, восемь — в `DB-ARCH-02`. У всех основной ящик остаётся в `MailBoxDB_AL_new`, `ArchiveGuid=Empty`, `RetentionPolicy` отсутствует, `UseDatabaseQuotaDefaults=True`, размер основного ящика 5–10 GiB. AD-учётные записи включены, открытых MoveRequest нет.
- Обе архивные базы на MX4 Mounted, на MX3 Healthy, очереди копирования/воспроизведения 0/0. На MX4 свободно J: 616.1 GiB, K: 149.3 GiB, Y: 456.0 GiB, Z: 148.8 GiB; обе БД имеют LastFullBackup.
- План: на каждом ящике `Enable-Mailbox -Archive -ArchiveDatabase <target>`, затем `Set-Mailbox -ArchiveWarningQuota 27GB -ArchiveQuota 30GB`. RetentionPolicy и основные ящики не менять. Выполнение партиями по пять с readback после каждой.

## Откат и ограничения

Если архив ещё пуст и включён ошибочно, точечный `Disable-Mailbox -Identity <alias> -Archive` возможен только после проверки, что в нём нет данных: команда удаляет архивное содержимое. Массовый откат не выполнять. Квоты можно изменить отдельно через `Set-Mailbox`. Включение пустого архива не переносит письма без MRM-политики; запуск Managed Folder Assistant не входит в задачу. Рестарт Exchange/Windows и reboot не планируются.

## Выполнение и результат

Первый ящик `m.darii` получил архив в DB-ARCH-01 и квоты 27/30 GiB. Автоматический readback остановил партию: `Enable-Mailbox -Archive` назначил ему `Default MRM Policy`, хотя до операции политика была пустой. Немедленно выполнено `Set-Mailbox -Identity m.darii -RetentionPolicy $null`; повторная проверка подтвердила исходное отсутствие политики, правильный ArchiveGuid/DB и квоты. Остальные четыре ящика первой подгруппы на этом этапе не изменялись. Дальнейшие команды после включения каждого архива явно возвращают `RetentionPolicy=$null` и проверяют это.

Финальный результат в 15:36 MSK: все 20 архивов включены по списку, 12 в `DB-ARCH-01` и восемь в `DB-ARCH-02`. У всех `ArchiveGuid` непуст, ArchiveDatabase совпадает с планом, `ArchiveWarningQuota=27 GiB`, `ArchiveQuota=30 GiB`, `RetentionPolicy=$null`, `UseDatabaseQuotaDefaults=True`; основные ящики остались в `MailBoxDB_AL_new`. Ошибок итоговой поимённой сверки нет. В исходной базе по-прежнему 262 основных ящика, число ящиков с архивом увеличилось с 13 до 33. Обе архивные DAG-копии Mounted/Healthy, очереди 0/0; свободное место J/K/Y/Z после операции 616.1/149.3/456.0/148.8 GiB. MRM и Managed Folder Assistant не запускались, письма не переносились. Рестарт, relogin и reboot не требуются.

При возможном последующем изменении архивной политики сначала оценивать фактический объём старых писем и свободную ёмкость: сама активация архива место под будущие письма не резервирует. Откат включения архивов уничтожил бы их содержимое; без необходимости не выполнять.
