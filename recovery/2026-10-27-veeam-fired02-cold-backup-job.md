# Подготовка cold backup job для DB-FIRED-02

Дата: 2026-10-27 (MSK)  
Объект: Veeam `bkp_exchange_fired02_cold`.

## Назначение

Подготовить отдельную неизменяемую по смыслу конфигурацию для будущей холодной
точки DB-FIRED-02, не затрагивая уже проверенную цепочку DB-FIRED-01.

## Конфигурация

Пользователь создал клон `bkp_exchange_fired01_cold`. Клон получил собственный
Veeam job ID `1cb5c326-fcaa-4726-bc78-0327ae9ad73e` и был переименован в
`bkp_exchange_fired02_cold`. В description добавлено предупреждение не
изменять исходный `bkp_exchange_fired01_cold`.

- репозиторий: `SPB-NAS1 Exchange NFS`;
- охват: `W:\`, `X:\`, protection group `Exchange DAG02`;
- application-aware processing включён;
- Exchange log action: `ProcessLogsWithJob`;
- schedule выключен;
- retention: 7 restore points, GFS включён.

## Проверка и гарантия разделения

У клона пока нет backup chain. В репозитории существует только
`bkp_exchange_fired01_cold` от 26.10.2026 19:20. Новый job имеет другой ID и
другое имя, поэтому при первом ручном Full создаст отдельную chain; исходная
точка DB-FIRED-01 не будет перезаписана.

## Условия запуска

Запускать вручную только после заполнения DB-FIRED-02 и завершения MoveRequest.
После `Success` проверить restore ящика в PST, затем не включать расписание.
`bkp_exchange_fired01_cold` не запускать и не менять: W:/X: уже содержат
другую базу, а его задача — хранить прежнюю cold chain.

## Откат

До первого запуска можно удалить только `bkp_exchange_fired02_cold`; исходную
цепочку DB-FIRED-01 это не затронет. После первого запуска удаление job и
chain требует отдельного решения о сроке хранения.
