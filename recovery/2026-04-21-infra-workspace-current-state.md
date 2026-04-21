# Infra Workspace Current State

Дата: 2026-04-21

## Назначение

Снимок актуального состояния рабочих инфраструктурных проектов в `~/assistant` и связанных recovery-заметок в `~/ai`.

Использовать после перезапуска/потери контекста, чтобы быстро восстановить:

- где лежат документы
- какие решения уже приняты
- какие коммиты важны
- какие файлы намеренно оставлены untracked/dirty
- какие риски не закрыты

## Активные Репозитории

- `/home/admin-al/ai` - control plane, правила, action log, recovery
- `/home/admin-al/assistant` - рабочая документация, проекты, презентации, артефакты
- `/home/admin-al/dotfiles` - локальные пользовательские конфиги

## Важные Dirty/Untracked Файлы

Не трогать без явного запроса пользователя:

- `/home/admin-al/assistant/INFRA_RESTRUCTURING_AND_UPGRADE_OVERVIEW.docx`
- `/home/admin-al/assistant/notes/projects/dc-architecture/rds-storage-bus-weekend-change-plan.docx`
- `/home/admin-al/assistant/notes/projects/global-network/.~lock.proposed-segmentation.csv#`
- `/home/admin-al/assistant/notes/projects/global-network/README.md`
- `/home/admin-al/assistant/notes/projects/global-network/mikrotik-topology.png`
- `/home/admin-al/assistant/notes/projects/global-network/mikrotik-topology.puml`
- `/home/admin-al/assistant/notes/projects/global-network/role-templates.yaml`
- `/home/admin-al/assistant/notes/projects/inventory-wiki/`
- `/home/admin-al/assistant/notes/projects/olimpoks/logs.rar`
- `/home/admin-al/assistant/notes/projects/split-keyboard/cross.csv`
- `/home/admin-al/assistant/notes/projects/split-keyboard/cross.xls`
- `/home/admin-al/assistant/notes/projects/trmm/AL_TRMM-5.msi`
- `/home/admin-al/assistant/notes/projects/trmm/trmm-installwithgpo-new-workstation-amd64_new.exe`

В `~/ai` есть крупная историческая перестройка/архивация с deleted/untracked файлами. Не чистить ее автоматически.

## Global Network / Сегментация

Основные файлы:

- `/home/admin-al/assistant/notes/projects/global-network/proposed-segmentation.csv`
- `/home/admin-al/assistant/notes/projects/global-network/segmentation-assessment.md`
- `/home/admin-al/assistant/notes/projects/global-network/split-dns-target-design.md`

Важные решения:

- AD и Exchange пока оставлены вместе в `CORE-SERVICES`.
- ОТПБ вынесен в `TRAINING-SERVICES`.
- TrueConf, Asterisk и FreePBX заведены в `UC-SERVICES`.
- IP-телефоны и voice endpoints вынесены отдельно в `VOICE-ENDPOINTS`.
- Split-DNS не переносить полной зоной `aurora-logistics.ru` в AD DNS.
- Правильная целевая DNS-схема: отдельная HA-пара split-DNS resolver'ов, AD DNS только для `aurora-logistics.local`.

Актуальные добавленные строки:

```csv
UC-SERVICES,825,10.78.20.176/28,10.78.20.177,"Видеоконференции, телефония и корпоративные коммуникации","TrueConf, Asterisk, FreePBX",USERS/VPN-USERS -> UC required ports; UC -> AD/DNS/NTP/SMTP; admins from VPN-ADMINS; phones/SIP trunks -> Asterisk required ports,"Не смешивать с CORE-SERVICES; для SIP/RTP нужны отдельные firewall rules и QoS; при внешней публикации вести через DMZ/SBC/NAT с allow-list"
VOICE-ENDPOINTS,850,10.78.50.0/24,10.78.50.1,IP-телефоны и голосовые endpoint'ы,"IP phones, softphones, voice gateways",VOICE-ENDPOINTS -> UC-SERVICES SIP/RTP only; DHCP/NTP/DNS by policy,"Отдельный VLAN для телефонов; применить QoS/DSCP; не давать доступ к server/mgmt zones"
```

Открытая проблема:

- `ONE-C = 10.78.22.8/28` некорректно выровнен для `/28` и пересекается с `RDS 10.78.22.0/29`.
- Это замечено при проверке CSV, но не исправлялось, чтобы не смешивать задачи.

Важные коммиты:

- `4d5ae5e` Add split DNS target design
- `f955fae` Document DNS ownership risk
- `fa961bc` Add TrueConf UC services segment
- `887ba57` Add voice services segmentation

## ОТПБ / ОЛИМПОКС

Основные файлы:

- `/home/admin-al/assistant/notes/projects/olimpoks/olimpoks_rukovodstvo_5.4.9.pdf`
- `/home/admin-al/assistant/notes/projects/olimpoks/ldap-authorization-setup.md`
- `/home/admin-al/assistant/notes/projects/olimpoks/logs.rar`

Схема публикации:

```text
Пользователь/VPN
  -> https://otpb.aurora-logistics.ru
  -> nginx 443
  -> ОЛИМПОКС backend 10.78.20.130:9001
```

Что выяснено:

- Для ОЛИМПОКС внешний URL должен быть `https://otpb.aurora-logistics.ru`.
- Backend должен оставаться на внутреннем HTTP `10.78.20.130:9001`.
- В настройках ОЛИМПОКС нужно включать режим прокси/HTTPS, а не переводить backend на 443.
- LDAP для работников заработал.
- Для главной формы входа нужна `Предварительная регистрация` в профиле, а не только наличие LDAP-схемы.
- Для админов используется сопоставление ролей ОЛИМПОКС с LDAP-группами.
- В логах ОЛИМПОКС была LDAP-ошибка:

```text
000004DC: In order to perform this operation a successful bind must be completed on the connection.
```

Вывод по LDAP:

- Нужна bind-учетка, не anonymous bind.
- Bind-учетка должна быть обычной read-only доменной учеткой, например `svc_olimpoks_ldap`.
- Права: чтение пользователей, групп, `member/memberOf`, нужных OU.
- Не нужна Domain Admin / Account Operator / Enterprise Admin.
- Рекомендуемый формат bind login для теста: `svc_olimpoks_ldap@aurora-logistics.local`.

Важные коммиты:

- `e55dcd7` Add Olimpoks LDAP setup notes
- `9e5deca` Clarify Olimpoks login screen setup
- `b36116a` Document Olimpoks LDAP admin group mapping

## TRMM MSI Wrapper

Основные файлы:

- `/home/admin-al/assistant/notes/projects/trmm/AL_TRMM-6.msi`
- `/home/admin-al/assistant/notes/projects/trmm/AL_TRMM-6-build-notes.md`
- `/home/admin-al/assistant/notes/projects/trmm/trmm-installwithgpo-new-workstation-amd64_new.exe`
- `/home/admin-al/assistant/notes/projects/trmm/AL_TRMM-5.msi`

Состояние:

- `AL_TRMM-6.msi` - актуальный MSI-wrapper.
- Внутри `media1.cab` лежит `TRMMInstallerFile`, устанавливаемое имя `Temp/trmminstall.exe`.
- Custom action запускает EXE с параметрами:

```text
/VERYSILENT /SUPPRESSMSGBOXES
```

- Важный исправленный флаг:

```text
Source: 2 (2)
```

Этот флаг нужен, чтобы Windows Installer использовал embedded CAB, а не искал внешний `Temp\trmminstall.exe` рядом с MSI.

Актуальный EXE inside MSI:

```text
9c734aa354e83a8d2ae9f79a2c44c2164560a5246f886dc55c38c87b7d37ec0a  Temp/trmminstall.exe
9c734aa354e83a8d2ae9f79a2c44c2164560a5246f886dc55c38c87b7d37ec0a  trmm-installwithgpo-new-workstation-amd64_new.exe
```

Актуальный MSI:

```text
e6e9805619e8d9e8420bde4ae33031f700be879c9193c193b52542fd91e04fdd  AL_TRMM-6.msi
```

Проверочные команды:

```bash
msiinfo suminfo /home/admin-al/assistant/notes/projects/trmm/AL_TRMM-6.msi
msiextract -C /tmp/trmm-check /home/admin-al/assistant/notes/projects/trmm/AL_TRMM-6.msi
sha256sum /tmp/trmm-check/Temp/trmminstall.exe /home/admin-al/assistant/notes/projects/trmm/trmm-installwithgpo-new-workstation-amd64_new.exe
```

Важные коммиты:

- `441fc20` Build updated TRMM MSI wrapper
- `7c28a9c` Fix TRMM MSI embedded cabinet source flag
- `b65adb9` Repack TRMM MSI with updated installer

## Zabbix

Хост:

- `a.kuznetsov@10.78.3.251`
- Zabbix server `6.0.40`

Проблема:

```text
Zabbix server: Zabbix value cache working in low memory mode
```

Факты:

- RAM ОС была достаточной: около `2.1 GiB available` из `2.9 GiB`.
- `ValueCacheSize` не задан, используется дефолт `8M`.
- Внутренний режим:

```text
zabbix[vcache,cache,mode] = 1
```

- Лог:

```text
value cache is fully used: please increase ValueCacheSize configuration parameter
```

Рекомендация:

```ini
ValueCacheSize=128M
```

После изменения нужен restart:

```bash
sudo systemctl restart zabbix-server
```

Проверка:

```bash
sudo grep -Ei 'value cache|low memory|fully used' /var/log/zabbix/zabbix_server.log | tail -50
```

Ожидаемо после рестарта:

```text
Zabbix server: Value cache operating mode = 0
```

## Split Keyboard / RMK

Файлы и репозитории:

- `/home/admin-al/split-keyboard-rmk`
- `/home/admin-al/assistant/notes/projects/split-keyboard/`
- `/home/admin-al/ai/recovery/2026-04-15-split-keyboard-rmk-bringup.md`

Состояние:

- Правый half handwired split keyboard.
- RMK USB-only firmware flashed successfully.
- Устройство перечислялось как USB HID:

```text
4c4b:534c admin-al Split Keyboard Right Test
```

- BLE/MPSL вариант ранее не стартовал; USB-only использовался как рабочий smoke-test.

Важные коммиты в `~/assistant`:

- `a5704b3` Add split keyboard recovery notes
- `f8d6782` Update split keyboard RMK recovery
- `de86d7e` Correct split keyboard recovery to right half

Важные коммиты в `~/ai`:

- `d91e67e` Document split keyboard RMK bring-up
- `e55468d` Update RMK bring-up notes and inventory
- `4f12eb6` Document RMK nRF52840 build fix
- `fe7db7c` Update split keyboard RMK flashing recovery
- `dc3d37b` Document split keyboard USB-only success

## Полезные SSH Факты

- PVE:
  - `a.kuznetsov@10.78.2.201` = `spb-pve1`
  - `a.kuznetsov@10.78.2.202` = `spb-pve2`
  - `a.kuznetsov@10.78.2.203` = `spb-pve3`
- Zabbix:
  - `a.kuznetsov@10.78.3.251`
- VPN server:
  - `a.kuznetsov@10.78.4.253`
- RouterOS:
  - `admin-al@10.78.3.254`
- H3C:
  - `admin@10.78.2.11`
  - `admin@10.78.2.12`
  - SSH options: `-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa`
- Synology:
  - `a.kuznetsov@10.78.2.210`
- MSA:
  - `manage@10.78.0.21`
  - `manage@10.78.0.23`

Не хранить новые пароли в recovery-файлах.

## Последние Важные Коммиты В `~/assistant`

```text
887ba57 Add voice services segmentation
fa961bc Add TrueConf UC services segment
b65adb9 Repack TRMM MSI with updated installer
7c28a9c Fix TRMM MSI embedded cabinet source flag
441fc20 Build updated TRMM MSI wrapper
b36116a Document Olimpoks LDAP admin group mapping
9e5deca Clarify Olimpoks login screen setup
e55dcd7 Add Olimpoks LDAP setup notes
4d5ae5e Add split DNS target design
```

## Следующие Действия

- Исправить пересечение `RDS/ONE-C` в `proposed-segmentation.csv`.
- При необходимости добавить отдельную матрицу портов для `UC-SERVICES` и `VOICE-ENDPOINTS`.
- Если TRMM MSI снова не ставится, первым делом проверить `Source: 2` и embedded CAB.
- Для ОЛИМПОКС LDAP-админов проверять bind account и group DN, не ломать локальный `sys`.
- Для Zabbix planned change: выставить `ValueCacheSize=128M` и перезапустить `zabbix-server` в согласованное окно.
