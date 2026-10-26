# Отдельная холодная Veeam-копия DB-FIRED-01

Дата: 2026-10-26 (MSK)  
Объекты: Exchange DAG `SPB-MX3`/`SPB-MX4`, Veeam job
`bkp_exchange_fired01_cold`.

## Цель

Сохранить независимую от ежедневной цепочки точку восстановления базы
`DB-FIRED-01` перед её будущим выводом из эксплуатации. Задание намеренно не
имеет расписания: после одного успешного full оно не должно захватывать новую
пустую `DB-FIRED-02` при повторном использовании W:/X:.

## Подтверждённая исходная инвентаризация

- `DB-FIRED-01` смонтирована на MX4, размер EDB 653.8 GB; пассивная копия
  MX3 Healthy, CopyQueue=0, ReplayQueue=0.
- В базе 61 подключённый primary mailbox. 60 учётных записей находятся в
  `OU=DisabledUsers,OU=Archive,DC=aurora-logistics,DC=local`; `adminspb`
  отключён, но остаётся в `CN=Users` и требует отдельного решения перед
  удалением базы.
- Действующих online archive в этой выборке нет. У `m.cherenkov` остаётся
  неактивный (`ArchiveStatus=None`) архивный атрибут, который следует
  перепроверить перед отключением его primary mailbox.
- Все MoveRequest к DB-FIRED-01 имеют статус Completed (8 записей).

## План задания

- backup object: тот же Veeam custom group `Exchange DAG02`, то есть оба
  участника DAG;
- scope: только `W:\` и `X:\` на каждом узле;
- application-aware processing: включён, Exchange log action
  `ProcessLogsWithJob`;
- repository: `SPB-NAS1 Exchange NFS`;
- расписание выключено; запуск — вручную с `FullBackup`.

## Важные ограничения

Эта копия не является основанием для удаления рабочей базы до успешного
завершения, проверки Veeam Exchange item restore/PST и создания второй копии
на физически независимом носителе. Откат конфигурации: удалить только
`bkp_exchange_fired01_cold`; основной DAG job не меняется.

## Выполненное изменение и проверка

- Создано Veeam Agent job `bkp_exchange_fired01_cold`.
- Scope подтверждён: `W:\\`, `X:\\` на custom group `Exchange DAG02`
  (SPB-MX3 и SPB-MX4), то есть активная и пассивная копии DB-FIRED-01.
- `ApplicationProcessingEnabled=True`,
  `GeneralTransactionLogAction=ProcessLogsWithJob`.
- Репозиторий: `SPB-NAS1 Exchange NFS`.
- `ScheduleEnabled=False`: задание не стартует само и не затронет будущую
  DB-FIRED-02. Перед запуском исправлена стартовая retention-настройка:
  установлены `RetentionType=RestorePoints` и `GFSRetentionEnabled=True`,
  как у рабочего DAG job; вариант RestoreDays мог бы удалить единственную
  архивную точку по сроку.

## Следующий шаг

Вручную запустить job с `FullBackup`, дождаться `Success`, проверить Exchange
item restore/PST для одного ящика и сделать независимую вторую копию. Только
после этого отдельно принимать решение об отключении ящиков и удалении
DB-FIRED-01.
