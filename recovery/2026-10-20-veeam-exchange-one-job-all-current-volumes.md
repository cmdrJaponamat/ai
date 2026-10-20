# Veeam: консолидация Exchange в одно задание

## Исходное состояние и цель

20.10.2026 владелец поручил оставить одно Veeam-задание для всех актуальных
дисков Exchange DAG. Перед изменением на Veeam 12.2 проверено:

- `bkp_exchange_dag02` включено, использует объект `Exchange DAG02`,
  репозиторий `SPB-NAS1 Exchange NFS`, application-aware processing и
  `ProcessLogsWithJob`, но его scope содержит лишь `E:, F:, G:, H:`;
- `bkp_exchange_archive_mx4` включено отдельно только для SPB-MX4 и хранит
  собственную успешную цепочку восстановления;
- на обоих членах DAG совпадает актуальный набор Exchange-томов:
  `E:, F:, G:, H:, I:, J:, K:, L:, S:, T:, U:, V:, W:, X:, Y:, Z:`.
  Устаревшие `M:, N:` есть только на MX4 и активных баз не содержат.

Неполный scope объясняет прежнее исключение Microsoft Exchange Writer:
writer видит файлы баз и журналов на томах, которых нет в snapshot. Пока
writer исключён, успешный backup не имеет права усекать Exchange transaction
logs.

## План изменения

Расширить `bkp_exchange_dag02` ровно на перечисленные общие актуальные тома,
сохранив его repository, retention, schedule, AAP и `ProcessLogsWithJob`.
После readback выключить расписание отдельного
`bkp_exchange_archive_mx4`, но не удалять job или его backup chain: это
сохраняет возможность restore до отдельного согласованного решения по
устаревшей цепочке. Затем запустить/дождаться полноценной точки общего job и
проверить участие Exchange Writer и фактическое усечение журналов.

## Откат

До первой успешной новой точки вернуть `bkp_exchange_dag02` к scope
`E:, F:, G:, H:` и снова включить `bkp_exchange_archive_mx4`. Никакие EDB,
журналы Exchange, VM-диски или уже существующие restore points этим действием
не удаляются.
