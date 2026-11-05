# Годовая политика архивации для ящиков mmk

Дата: 2026-11-05, около 14:42 MSK. Владелец поручил заменить только политику хранения с периодом более года; шестимесячные назначения сохранить.

## Исходное состояние

- В `mmk` 32 действующих `UserMailbox`, все 32 имеют Online Archive.
- 24 ящика использовали `Default MRM Policy` с DPT `Default 2 year move to archive` (`MoveToArchive`, 730 дней).
- 6 ящиков уже использовали `Default + 1year move to archive` (`MoveToArchive`, 360 дней).
- `a.kopyakov` и `d.tromza` использовали `Default + 6month move to archive` (`MoveToArchive`, 180 дней).
- Целевая политика существует и содержит 11 ожидаемых тегов; её годовой DPT включён.

## Изменение

Через `Set-Mailbox -RetentionPolicy 'Default + 1year move to archive'` изменены только 24 ящика, у которых до операции была `Default MRM Policy`:

`agent`, `a.kochnev`, `sklad.mmk`, `n.brodnikov`, `m.barkar`, `a.nikulina`, `n.dektyarev`, `n.afanaseva`, `s.laskiy`, `s.danishevskiy`, `d.kisil`, `a.lavrenov`, `d.serdyukov`, `n.shulepin`, `p.titov`, `m.shevchenko`, `v.chiburun`, `p.voloshenko`, `o.yureva`, `v.spinul`, `n.smirnova`, `1C_uat_sync`, `o.milovidova`, `o.fedorovich`.

Перед каждым изменением проверялись база `mmk` и прежняя политика. Для остальных 8 ящиков изменения не выполнялись. Принудительный запуск Managed Folder Assistant не выполнялся.

## Проверка и откат

- Повторное чтение Exchange с MX3 и MX4: 32 ящика, из них 30 на годовой и 2 (`a.kopyakov`, `d.tromza`) на шестимесячной политике; Online Archive есть у всех 32.
- Для точечного отката назначить перечисленным 24 ящикам `Default MRM Policy`, предварительно проверив, что они ещё в `mmk` и их политику не меняли повторно. Возврат политики не переместит обратно письма, которые успеет обработать Managed Folder Assistant.
- Службы и ВМ не перезапускались; relogin/restart/reboot не требуются.
