# Manji Valley

Арена из TEKKEN 6 для TEKKEN 8. На карте есть замёрзшее озеро, скалы, святилище, ворота тории и подвесной мост. Идёт снег. Карта заменяет Coliseum of Fate (ST04).

[**Скачать Manji Valley**](downloads/Manji-Valley.zip?raw=true)

Сборка рассчитана на Steam-версию TEKKEN 8 (3.02.02).

## Установка карты

1. Полностью закройте TEKKEN 8.
2. В Steam откройте **Библиотека → TEKKEN 8 → Управление → Просмотреть локальные файлы**.
3. Сохраните копии прежних файлов Manji Valley, если мод уже установлен.
4. Распакуйте архив. Скопируйте шесть файлов карты в `Polaris/Content/Paks/Mods` внутри папки игры.

```text
Polaris/Content/Paks/Mods/
├── ManjiValleyColosseum_P.pak
├── ManjiValleyColosseum_P.ucas
├── ManjiValleyColosseum_P.utoc
├── ManjiValleySnowFloor_P.pak
├── ManjiValleySnowFloor_P.ucas
└── ManjiValleySnowFloor_P.utoc
```

Создайте папку `Mods`, если её нет. При обновлении замените все шесть файлов. Отключите другие моды, которые заменяют Coliseum of Fate. В игре выберите ячейку этой арены.

### Название и превью

1. Скопируйте `ManjiValleyUI_P.pak`, `ManjiValleyUI_P.ucas` и `ManjiValleyUI_P.utoc` в ту же папку `Polaris/Content/Paks/Mods`.
2. Сохраните копии двух роликов из `Polaris/Content/Movies/usm/StageSelect`. Затем замените их одноимёнными файлами из архива.

```text
Mov_UI_SS_Stage_04_Colosseum.usm
Mov_UI_SS_Stage_Decide_04_Colosseum.usm
```

### Подсветка границы

Для подсветки нужен отдельно установленный совместимый UE4SS. Скопируйте папку `ManjiValleySnow` из архива в `Polaris/Binaries/Win64/Mods`. В существующем `mods.txt` добавьте или включите строку `ManjiValleySnow : 1`. Видимость обновлённой границы в бою ещё предстоит проверить.

## Рендеры карты

Рендеры сделаны в Blender. Освещение, снегопад и огонь в игре могут выглядеть иначе.

![Превью Manji Valley](docs/renders/manji-valley-preview.png)

| Замёрзшее озеро и ледяные колонны | Ворота и мост с арены |
| --- | --- |
| ![Озеро и ледяные колонны](docs/renders/valley-and-shrine.png) | ![Вид на ворота и мост со льда](docs/renders/torii-and-bridge.png) |
| **Святилище с жаровнями** | **Подвесной мост крупным планом** |
| ![Святилище с жаровнями](docs/renders/shrine-preview.png) | ![Настил и тросы моста](docs/renders/gate-rope-full.png) |
| **Ледяная колонна у святилища** | **Ряд ворот тории на скале** |
| ![Основание ледяной колонны](docs/renders/ice-base-grounded.png) | ![Ряд ворот тории](docs/renders/torii-spacing.png) |

## Удаление и откат

Закройте игру. Для удаления карты уберите шесть файлов из списка установки. Для удаления интерфейса уберите три файла `ManjiValleyUI_P` и верните сохранённые исходные `.usm`. Для отключения подсветки поставьте `ManjiValleySnow : 0` в списке UE4SS.

Для отката верните полный сохранённый комплект одной сборки. Если в нём была только карта, уберите файлы нового интерфейса, верните исходные ролики и отключите подсветку отдельно.

## Авторы

**FedorPorshen** ставил задачи, проверял мод в игре и давал правки. **Codex** выполнил весь перенос, написал скрипты и собрал мод. Проект сделан вайбкодингом.

Это неофициальный фанатский мод. TEKKEN и оригинальные игровые материалы принадлежат их правообладателям.

В работе использовались Blender, Unreal Engine 5.2, FModel, retoc, repak и UE4SS.

**English:** Manji Valley from TEKKEN 6 replaces Coliseum of Fate in the Steam version of TEKKEN 8. The archive contains the stage, menu previews and an optional boundary highlight script for UE4SS. Back up the two stage-select movies before replacing them. All images above are Blender renders.

