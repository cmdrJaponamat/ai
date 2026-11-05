# Перенаправление VIP-заявки из mmk

Дата: 2026-11-05, около 15:11 MSK. Владелец поручил проверить MoveRequest на соответствие VIP-списку и направить VIP-ящики в VIP-базу.

## Проверка

- Список `~/assistant/notes/projects/aurora-logistics-mail/exchange-database-reorganisation/vip-mailbox-candidates-2026-10-30.md` включает три ящика из `mmk`: `s.danishevskiy`, `a.kochnev`, `o.fedorovich`. Первые два весят не менее 20 GiB, поэтому заявок в текущем пакете для них нет.
- `o.fedorovich` (ExchangeGuid `aaf86d5c-c32b-4c59-b65b-49a15e9ccb5b`) имела заявку `mmk` → `DB-CORP-03`, `MoveOnlyPrimaryMailbox`, около 20%, `StalledDueToTarget_DiskLatency`; основной ящик ещё оставался в `mmk`, архив — в `DB-ARCH-01`.
- VIP-база `DB-EXEC-01` Mounted на MX3, копия MX4 Healthy, очереди 0/0; квота приёма 30 GiB, основной ящик `o.fedorovich` около 1.12 GiB.
- Согласно документации Exchange, `Set-MoveRequest -TargetDatabase` меняет цель только при статусе `Queued`. Исходная заявка уже была `InProgress`.

## Изменение

1. Для `o.fedorovich` установлен флаг приостановки старой заявки. Из-за состояния ожидания диска её видимый статус оставался `InProgress` при `Suspend=True`.
2. После повторной проверки GUID, источника и цели старый MoveRequest отменён через `Remove-MoveRequest -Confirm:$false`.
3. Создан новый `New-MoveRequest -TargetDatabase DB-EXEC-01 -PrimaryOnly -BatchName mmk-vip-correction-20261105 -Priority Low`.

## Результат и откат

- В Exchange всего 21 заявка: прежний пакет `mmk-lt20-20261105` содержит 20 (9 в `DB-CORP-02`, 11 в `DB-CORP-03`), отдельная VIP-заявка — 1 в `DB-EXEC-01`. Среди трёх VIP-ящиков `mmk` заявка есть только у `o.fedorovich`, и она направлена в VIP-базу.
- Новая VIP-заявка Queued, `MoveOnlyPrimaryMailbox`; основной ящик пока в `mmk`, архив в `DB-ARCH-01`. Обе копии `DB-EXEC-01` Mounted/Healthy, очереди 0/0.
- При необходимости отмены до завершения — приостановить и удалить только новую заявку после проверки состояния. После завершения обратный перенос требует новой заявки `-PrimaryOnly`. Остальные 20 заявок не менялись.
- Службы и ВМ не перезапускались; relogin/restart/reboot не требуются.
