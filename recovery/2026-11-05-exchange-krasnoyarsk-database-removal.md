# Exchange: вывод базы Krasnoyarsk

Дата: 2026-11-05. Владелец поручил удалить базу и сообщил, что проверил восстановление из Veeam. До операции: основной `bkp_exchange_dag02` завершился Success 05.11 в 01:39; точки MX3/MX4 за 04.11 существуют.

## Финальный preflight

- `Krasnoyarsk` активна на SPB-MX3 (`Mounted`), пассивная копия SPB-MX4 `Healthy`, очереди 0/1.
- Обычных, архивных, arbitration, audit и public folder ящиков, а также пользовательских ссылок на архив базы — 0.
- `SoftDeleted` — 0; `MoveRequest` с source/target `Krasnoyarsk` — 0.
- Четыре `MonitoringMailbox` остаются под управлением Exchange.
- EDB: `E:\ExchangeDatabases\Krasnoyarsk\Krasnoyarsk.edb`; журналы: `E:\ExchangeLogs\Krasnoyarsk`.

## Порядок и откат

Сначала снять пассивную копию `Krasnoyarsk\SPB-MX4`, затем удалить объект `Krasnoyarsk` штатным Exchange cmdlet. После проверки отсутствия объекта и других потребителей удалить только каталоги `E:\ExchangeDatabases\Krasnoyarsk` и `E:\ExchangeLogs\Krasnoyarsk` на MX3/MX4, чтобы завершить вывод базы и освободить место. Удаление файлов обратимо только через восстановление из Veeam; точка Veeam подтверждена, проверку восстановления подтвердил владелец. Перезапуск служб и reboot не планируются.

## Результат

Около 10:36 MSK пассивная копия `Krasnoyarsk\SPB-MX4` штатно удалена; оставшаяся копия MX3 была Mounted. Затем `Remove-MailboxDatabase -Identity Krasnoyarsk` завершился успешно. Readback: объект базы отсутствует, ссылок MonitoringMailbox на него — 0. Пять пользовательских ящиков по-прежнему в `DB-CORP-01`, архивы — в `DB-ARCH-02`; все 20 оставшихся копий Exchange имеют статусы Mounted или Healthy.

После отдельной проверки содержимого каталогов удалены только `E:\ExchangeDatabases\Krasnoyarsk` и `E:\ExchangeLogs\Krasnoyarsk` на MX4 и MX3. До удаления EDB занимала 520 899 526 656 B на MX4 и 521 033 220 096 B на MX3. Оба каталога отсутствуют после операции; свободное место E: выросло с 2 752 562 724 864 до 3 273 703 817 216 B на MX4 и с 2 749 526 282 240 до 3 270 974 386 176 B на MX3.

Откат: повторное создание пустого объекта базу не вернёт; восстановление данных возможно только из сохранённых Veeam-точек по проверенному владельцем процессу. Перезапуск служб, relogin и reboot не выполнялись и не требуются.
