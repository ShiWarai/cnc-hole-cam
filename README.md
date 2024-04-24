# cnc-hole-cam
[![Release EXE with PyInstaller](https://github.com/ShiWarai/cnc-hole-cam/actions/workflows/github-actions-build-and-release.yml/badge.svg?branch=main&event=release)](https://github.com/ShiWarai/cnc-hole-cam/actions/workflows/github-actions-build-and-release.yml)

Утилита для создания g-code файла сверления отверстий, которые изначально задаются от угла детали (левый-верхний).

Основной поддерживаемой платформой является Snapmaker 2.0 с CNC насадкой

## Отладка
Для отладки использовалась библиотека [TkDeb](https://github.com/MateuszPerczak/TkDeb), написанная для Python 3.8, но всё ещё работает на новых версиях