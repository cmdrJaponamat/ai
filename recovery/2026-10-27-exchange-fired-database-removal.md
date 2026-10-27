# Окончательный вывод базы fired

Дата: 2026-10-27 (MSK)  
Объект: Exchange database `fired`, SPB-MX3/SPB-MX4.

## Допуск и preflight

Владелец явно поручил вывести и удалить базу. Перед операцией подтверждено:

- активная копия `fired\SPB-MX3` — `Mounted`, пассивная MX4 — `Healthy`,
  Copy/Replay queue = 0;
- connected mailbox = 0, MoveRequest с source/target `fired` = 0;
- остаётся 34 `SoftDeleted` store entries (около 258 GiB); их 30-дневный
  быстрый rollback будет утрачен по воле владельца;
- 5 monitoring HealthMailbox привязаны к базе, иных arbitration/audit/public
  folder mailbox нет;
- активные пути: `E:\ExchangeDatabases\fired\fired.edb` и
  `E:\ExchangeLogs\fired`; идентичные каталоги существуют на MX4.

## Точные физические цели

| Узел | EDB | Logs |
| --- | ---: | ---: |
| MX3 | 270,717,157,376 B | 407,019,520 B |
| MX4 | 270,582,939,648 B | 352,329,728 B |

## План операции

1. Удалить пассивную копию MX4.
2. Dismount и удалить объект `fired` на MX3.
3. Только после отсутствия объекта удалить два указанных каталога на каждой
   ноде; не удалять том E: и другие Exchange-каталоги.

## Восстановление и ограничение

После удаления EDB/логов локального восстановления и soft-delete retention не
останется. До удаления подтверждена недавняя успешная ежедневная Veeam
application-aware цепочка `bkp_exchange_dag02`; она остаётся единственным
источником восстановления базы/ящика в пределах retention. Восстановление
потребует отдельной recovery database или целевой базы Exchange.

## Результат

- Пассивная копия `fired\SPB-MX4` удалена успешно.
- Активная база MX3 размонтирована и удалена штатным
  `Remove-MailboxDatabase`; объекта и DAG-копий `fired` больше нет.
- На MX3 удалены `E:\ExchangeDatabases\fired` (270,717,157,376 B) и
  `E:\ExchangeLogs\fired` (390,078,464 B).
- На MX4 удалены `E:\ExchangeDatabases\fired` (270,582,939,648 B) и
  `E:\ExchangeLogs\fired` (352,329,728 B).
- Всего удалено 542,042,505,216 B (около 505 GiB). Каталоги отсутствуют;
  тома E: и остальные базы не затрагивались.
- Финальная проверка: `DB_OBJECT_EXISTS=False`, `COPY_COUNT=0`,
  `HEALTH_REFERENCES=0`; остальные 12 активных и 12 пассивных копий имеют
  статусы `Mounted`/`Healthy`, плохих копий нет.
