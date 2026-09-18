# Clash Verge: правило для Fiverr

- Дата: 2026-03-25
- Область: system work

## Проблема

Нужно было добавить `www.fiverr.com` и другие поддомены `fiverr.com` в маршрут через группу `🚫 Недоступные сайты` в Clash Verge.

## Что найдено

- Рабочая директория Clash Verge: `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev`
- Активный профиль: `alexey_k`
- Для активного профиля подключён локальный rules-слой: `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/rtBxJA1UhmGc.yaml`
- Для активного профиля подключён локальный merge-слой: `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/m9avkBFXPZvM.yaml`
- В основном удалённом профиле уже существует proxy group `🚫 Недоступные сайты`
- Итоговый собранный конфиг: `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml`
- Логи показали, что правило для `fiverr` матчится корректно, но трафик уходил через `🚫 Недоступные сайты[🇸🇪 Швеция, Стокгольм]`, а этот выходной узел ранее уже давал timeout и на других правилах
- Дополнительно по логам выяснилось, что часть ассетов сайта грузится с `npm-assets.fiverrcdn.com`, а не с `*.fiverr.com`

## Изменения

Вместо одиночного доменного правила сделана схема, ближе к основному профилю:

Файл `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/m9avkBFXPZvM.yaml`:

```yaml
dns:
  nameserver-policy:
    rule-set:fiverr-inline:
      - https://1.1.1.1/dns-query#🚫 Недоступные сайты
      - https://8.8.8.8/dns-query#🚫 Недоступные сайты

rule-providers:
  fiverr-inline:
    type: inline
    behavior: classical
    payload:
      - DOMAIN-SUFFIX,fiverr.com
      - DOMAIN-SUFFIX,fiverrcdn.com
```

Файл `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/rtBxJA1UhmGc.yaml`:

```yaml
prepend:
  - RULE-SET,fiverr-inline,🚫 Недоступные сайты
```

Использован `prepend`, чтобы локальное правило применялось раньше правил из удалённой подписки, а `merge`-слой добавляет DNS-policy и inline rule-set в том же стиле, как это сделано в основном профиле для других категорий.

## Проверка

- Проверены итоговые YAML-файлы локальных overlays
- Подтверждено, что группа `🚫 Недоступные сайты` существует в активном профиле
- Подтверждено, что для `fiverr-inline` добавлены и DNS-policy, и routing rule
- Подтверждено по логу `service_latest.log`, что есть совпадение `match RuleSet(fiverr-inline) using 🚫 Недоступные сайты`
- Подтверждено по логам, что до последней правки `npm-assets.fiverrcdn.com` шёл через `🌍 Остальные сайты`, потому что не входил в правило

## Дополнительное исправление

Для исключения проблем с авто-выбором выходного узла в файле `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml` переключена выбранная цель группы `🚫 Недоступные сайты`:

```yaml
- name: 🚫 Недоступные сайты
  now: 🇱🇻 Латвия, Рига
```

Раньше там был `🎲 Любой доступный сервер`.

## Откат

Удалить:

- секцию `rule-providers.fiverr-inline` из `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/m9avkBFXPZvM.yaml`
- секцию `dns.nameserver-policy.rule-set:fiverr-inline` из `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/m9avkBFXPZvM.yaml`
- строку `RULE-SET,fiverr-inline,🚫 Недоступные сайты` из `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/rtBxJA1UhmGc.yaml`
- при необходимости вернуть в `/home/japonamat/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml` значение группы `🚫 Недоступные сайты` обратно на `🎲 Любой доступный сервер`

## Нужен ли relogin/reboot

Нет. При необходимости достаточно нажать обновление профиля или перезапустить Clash Verge.
