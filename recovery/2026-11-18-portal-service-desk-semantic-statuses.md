# PortalAL: смысловые статусы заявок и досок

Дата: 18.11.2026. PR #14. Production SHA `19524cef5d8764e88bcbf63700ab0c1d470306e0`.

## Изменение и проверка

- Доски ИТ и Legal сохраняют коды `new`, `in_progress`, `waiting`, `awaiting_reply`, `reopened`, `resolved` вместо номеров HESK. Старые настройки преобразуются при первом чтении; названия, цвета и порядок колонок сохраняются.
- Активные экраны заявок используют смысловые коды. Перевод в номера HESK остаётся внутри серверного адаптера.
- Локально: 83 теста и сборка. PR CI `44282730523`; main CI `44283025724`; staging `44283286891`; production `44283488799` прошли. На сервере `10.78.3.149` контейнер `portal-al` работает с указанным образом и состоянием `healthy`, `GET http://127.0.0.1:5180/api/health` вернул HTTP 200.
- Рабочие конфигурации досок ИТ и Legal прочитаны через новый код: версия 2, по шесть колонок, все статусы смысловые. Рабочие заявки и HESK-настройки не изменялись.

## Откат

Предыдущий образ: `portal-al:56811be8f95467c7ff9a2c23d2c58ef38340a70a`. Перед возвратом старого образа преобразовать только `portal_queue_board_configs` для `it` и `legal` обратно в номера HESK, иначе старая доска не распределит заявки по колонкам. Выполнить под миграционной ролью PostgreSQL в БД портала, в одной транзакции; сначала сохранить строки таблицы в резервной копии:

```sql
begin;
update portal_queue_board_configs b
set columns = (
  select jsonb_agg(
    jsonb_set(
      jsonb_set(e.column_data, '{id}', to_jsonb(case e.column_data->>'id'
        when 'stage_new' then 'stage_0' when 'stage_in_progress' then 'stage_1'
        when 'stage_waiting' then 'stage_2' when 'stage_resolved' then 'stage_3'
        when 'stage_reopened' then 'stage_4' when 'stage_awaiting_reply' then 'stage_5'
        else e.column_data->>'id' end)),
      '{statuses}', coalesce((select jsonb_agg(to_jsonb(case s.code
        when 'new' then '0' when 'in_progress' then '1' when 'waiting' then '2'
        when 'resolved' then '3' when 'reopened' then '4' when 'awaiting_reply' then '5'
        else s.code end)) from jsonb_array_elements_text(e.column_data->'statuses') as s(code)), '[]'::jsonb)
    ) order by e.position)
  from jsonb_array_elements(b.columns) with ordinality as e(column_data,position)
), version=version+1, updated_by='rollback', updated_at=now()
where b.queue_id in ('it','legal');
-- Проверить ровно две обновлённые строки и значения columns; затем commit или rollback.
commit;
```

После этого вернуть предыдущий `PORTAL_IMAGE` штатным `deploy/deploy-image.sh`/Compose в `/opt/portal-al` и проверить `docker inspect portal-al` и `/api/health`. Новых миграций схемы БД в выпуске нет. Перезапуск только контейнера портала; relogin и reboot не требуются.
