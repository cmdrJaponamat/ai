# Exchange mmk: проверка готовности к выводу

Дата: 2026-11-11 MSK. Цель: ответить, можно ли удалить `mmk` после вывода активных ящиков. Подробный контекст: `/home/admin-al/assistant/notes/projects/aurora-logistics-mail/exchange-database-reorganisation/JOURNAL.md`.

## Проверено

- Только чтение Exchange на SPB-MX3 через гостевой агент PVE. `mmk` Mounted на MX3, копия MX4 Healthy, очереди 0/0. Последняя полная копия по маркеру Exchange: 10.11.2026 20:52.
- Regular, archive, arbitration, audit, public folder и migration mailbox: 0; MonitoringMailbox: 4. Store statistics: 9 connected внутренних/health записей и 49 SoftDeleted.
- 32 SoftDeleted имеют действующий ящик с тем же GUID в DB-CORP-02/03 или DB-EXEC-01. 17 SoftDeleted (268.26 GiB) не имеют действующего ящика с тем же GUID или именем; все 17 AD-учётных записей отключены. Source-disconnect: 22–29.10.
- По времени 4 записи отключены до cold backup DB-FIRED-01 от 26.10, 13 — до cold backup DB-FIRED-02 от 29.10. Veeam live-каталог содержит по две точки этих jobs; последние сессии Success, расписания выключены. Поимённая сверка содержимого холодных копий не проводилась. Ранее документировано восстановление в PST из FIRED-01, но не из FIRED-02.
- После удаления завершённых заявок владельцем повторно проверено: MoveRequest со ссылкой на `mmk` = 0. SoftDeleted = 49; MailboxRetention = 30 дней.

## Решение и следующий шаг

Технических привязок действующих ящиков и MoveRequest нет. Удаление базы до истечения retention уничтожит локальные SoftDeleted-копии. Перед удалением следует подтвердить достаточность холодной цепочки для 17 уволенных или явно принять потерю этой возможности быстрого отката. При отдельном поручении на удаление повторить preflight, снять пассивную DAG-копию, удалить объект штатным Exchange cmdlet; EDB/журналы и тома рассматривать отдельно после проверки путей. В этом эпизоде ничего не удалялось и не менялось; откат не требуется, relogin/restart/reboot не нужны.
