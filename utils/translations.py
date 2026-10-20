#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import locale
from typing import Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_DIR = os.path.join(BASE_DIR, "locales")

DEFAULT_LANG = 'es'
CURRENT_LANG = DEFAULT_LANG

# Spanish (default)
ES = {
    'app_title': 'SchematicBuq — Buscador Inteligente de Esquemáticos',
    'subtitle': '  Busca componentes, entiende su función y sigue las conexiones',
    'add_files': '📁  Añadir archivos',
    'add_folder': '📂  Añadir carpeta',
    'add_url': '🌐  Importar PDF (URL)',
    'new_device': '➕  Nuevo aparato',
    'assign_device': '📦  Guardar en el aparato',
    'help': '❓  Ayuda',
    'clear': '🗑️  Limpiar',
    'analyze': '⚙️  Analizar',
    'analyze_tooltip': 'Lee los esquemáticos y guarda todos sus componentes.\nLa primera vez tarda un poco; después es instantáneo.',
    'active_device': 'Aparato/equipo activo:',
    'open_folder': 'Abrir carpeta',
    'ocr_scan': 'Leer esquemáticos escaneados (más lento)',
    'search_placeholder': 'Busca designador (R46, C12, U5...) o valor (10k, 100uF...)',
    'search': '🔍 Buscar',
    'back': '← Volver',
    'clear_results': 'Borrar resultados',
    'export': '💾 Exportar índice',
    'import': '📥 Importar índice',
    'system_ready_ocr': 'Sistema listo — OCR activo ({langs}) — Tesseract: {path}',
    'system_ready_noocr': 'Sistema listo — OCR NO disponible (instala Tesseract para escaneos). Los PDF con texto funcionan igual.',
    'error_unexpected': 'Error inesperado',
    'files': 'Archivos',
    'results': 'Resultados',
    'viewer': 'Visor',
    'tools': 'Herramientas',
    # --- interfaz ampliada ---
    'back_tooltip': 'Vuelve al componente que estabas viendo antes (navegar por el circuito)',
    'on_select': 'Al seleccionar:',
    'multimeter': 'Multímetro',
    'interaction': 'Interacción',
    'diagnostic': 'Diagnóstico',
    'no_change': 'No cambiar',
    'auto_tab_tooltip': 'Qué pestaña se abre automáticamente al hacer clic en un resultado',
    'hint': ('💡 Escribe el componente y pulsa Buscar · clic en un resultado para '
             'ver cómo medirlo · «🔄 Interacción» muestra con quién se relaciona · '
             'doble clic para verlo en el esquemático.'),
    'device_files': '📄 Esquemáticos del aparato',
    'device_files_tooltip': ('Archivos del aparato seleccionado.\n'
                             'Clic: muestra todos sus componentes.\n'
                             'Doble clic: abre el esquemático en el visor.'),
    'col_designator': 'Designador', 'col_value': 'Valor', 'col_type': 'Tipo',
    'col_file': 'Archivo', 'col_page': 'Pág.', 'col_source': 'Origen',
    'col_device': 'Aparato',
    'tab_viewer': '🧭  Visor del esquemático',
    'tab_component': '🧩  Componente',
    'tab_interaction': '🔄  Interacción y comportamiento',
    'tab_multimeter': '🔌  Multímetro',
    'tab_diagnostic': '🔬  Diagnóstico y pruebas',
    'tab_connections': '🔗  Conexiones del componente',
    'tab_nomenclature': '📚  Nomenclatura y diagnóstico',
    'tab_divider': '🧮  Divisor de tensión',
    'tab_help': '🆘  Cómo usar (ayuda)',
    'status_ready': 'Listo. Añade un esquemático para empezar.',
    'files_in_queue': '{n} archivo(s) en cola',
    'none': '(Ninguno)',
    'no_device_selected': 'Aparato: (ninguno) — cola vacía. Añade archivos o elige un aparato.',
    'device_name_prompt': 'Nombre del aparato o equipo\n(ej.: Fuente ATX 500W, TV Samsung, Amplificador Yamaha):',
    'device_created': 'Aparato creado',
    'device_created_msg': "Se creó el aparato '{name}'.\n\nCarpeta de esquemáticos:\n{folder}\n\nLos esquemáticos que guardes se organizarán aquí.",
    'device_registered': "Aparato '{name}' registrado desde la carpeta",
    'no_device': 'Sin aparato',
    'select_device_first': 'Selecciona primero un aparato.',
    'create_device_first': 'Crea o selecciona un aparato primero.',
    'saved': 'Guardado',
    'saved_msg': '{n} archivo(s) guardados en:\n{folder}\n\nReindexa para incluir los archivos con el nombre del aparato.',
    'select_schematics': 'Seleccionar esquemáticos',
    'select_folder': 'Seleccionar carpeta con esquemáticos',
    'import_url': 'Importar PDF desde URL',
    'import_url_prompt': 'Pega la URL directa del PDF del esquemático:',
    'downloading_pdf': 'Descargando PDF...',
    'error': 'Error',
    'open_failed': 'No se pudo abrir: {err}',
    # --- compartir / base de datos local ---
    'share': '📤  Compartir esquemáticos',
    'share_tooltip': ('Exporta un paquete .sbq con esquemáticos y metadatos.\n'
                      'Solo viajan esquemáticos: nunca ejecutables ni scripts.'),
    'import_pkg': '📥  Importar esquemáticos',
    'import_pkg_tooltip': ('Importa un paquete .sbq de otro usuario.\n'
                           'Se validan los archivos para bloquear virus.'),
    'share_done': 'Paquete exportado:\n{path}\n\nCompártelo con otros usuarios. Solo contiene esquemáticos y metadatos, sin ejecutables.',
    'import_failed': 'No se pudo importar: {err}',
    'import_done': 'Se importaron {n} esquemático(s) a tu almacén local.',
    'import_skipped': 'Se omitieron {n} archivo(s) por seguridad (no son esquemáticos).',
    'cleared': 'Todo limpio',
    'reset': '♻️  Restablecer',
    'reset_tooltip': 'Borra todos los datos locales (aparatos, esquemáticos y caché) y deja el programa como recién instalado.',
    'reset_title': 'Restablecer el programa',
    'reset_confirm': 'Se borrarán TODOS los datos locales: aparatos registrados, esquemáticos guardados y caché.\n\nEsta acción no se puede deshacer. ¿Continuar?',
    'reset_done': 'Datos restablecidos. El programa está como recién instalado.',
}

# English
EN = {
    'app_title': 'SchematicBuq — Intelligent Schematic Search',
    'subtitle': '  Search components, understand function and follow connections',
    'add_files': '📁  Add files',
    'add_folder': '📂  Add folder',
    'add_url': '🌐  Import PDF (URL)',
    'new_device': '➕  New device',
    'assign_device': '📦  Save to device',
    'help': '❓  Help',
    'clear': '🗑️  Clear',
    'analyze': '⚙️  Analyze',
    'analyze_tooltip': 'Parse schematics and index all components.\nFirst time takes longer; subsequent times are instant.',
    'active_device': 'Active device/equipment:',
    'open_folder': 'Open folder',
    'ocr_scan': 'Read scanned schematics (slower)',
    'search_placeholder': 'Search designator (R46, C12, U5...) or value (10k, 100uF...)',
    'search': '🔍 Search',
    'back': '← Back',
    'clear_results': 'Clear results',
    'export': '💾 Export index',
    'import': '📥 Import index',
    'system_ready_ocr': 'System ready — OCR active ({langs}) — Tesseract: {path}',
    'system_ready_noocr': 'System ready — OCR NOT available (install Tesseract for scans). Text PDFs work fine.',
    'error_unexpected': 'Unexpected error',
    'files': 'Files',
    'results': 'Results',
    'viewer': 'Viewer',
    'tools': 'Tools',
    # --- extended UI ---
    'back_tooltip': 'Go back to the component you were viewing (navigate the circuit)',
    'on_select': 'On select:',
    'multimeter': 'Multimeter',
    'interaction': 'Interaction',
    'diagnostic': 'Diagnostic',
    'no_change': 'Do not change',
    'auto_tab_tooltip': 'Which tab opens automatically when you click a result',
    'hint': ('💡 Type the component and press Search · click a result to '
             'see how to measure it · «🔄 Interaction» shows what it relates to · '
             'double click to view it on the schematic.'),
    'device_files': '📄 Device schematics',
    'device_files_tooltip': ('Files of the selected device.\n'
                             'Click: shows all its components.\n'
                             'Double click: opens the schematic in the viewer.'),
    'col_designator': 'Designator', 'col_value': 'Value', 'col_type': 'Type',
    'col_file': 'File', 'col_page': 'Pg.', 'col_source': 'Source',
    'col_device': 'Device',
    'tab_viewer': '🧭  Schematic viewer',
    'tab_component': '🧩  Component',
    'tab_interaction': '🔄  Interaction and behavior',
    'tab_multimeter': '🔌  Multimeter',
    'tab_diagnostic': '🔬  Diagnostics and tests',
    'tab_connections': '🔗  Component connections',
    'tab_nomenclature': '📚  Nomenclature and diagnostics',
    'tab_divider': '🧮  Voltage divider',
    'tab_help': '🆘  How to use (help)',
    'status_ready': 'Ready. Add a schematic to start.',
    'files_in_queue': '{n} file(s) queued',
    'none': '(None)',
    'no_device_selected': 'Device: (none) — empty queue. Add files or pick a device.',
    'device_name_prompt': 'Device or equipment name\n(e.g.: ATX PSU 500W, Samsung TV, Yamaha amplifier):',
    'device_created': 'Device created',
    'device_created_msg': "Device '{name}' was created.\n\nSchematic folder:\n{folder}\n\nThe schematics you save will be organized here.",
    'device_registered': "Device '{name}' registered from the folder",
    'no_device': 'No device',
    'select_device_first': 'Select a device first.',
    'create_device_first': 'Create or select a device first.',
    'saved': 'Saved',
    'saved_msg': '{n} file(s) saved to:\n{folder}\n\nReindex to include the files under the device name.',
    'select_schematics': 'Select schematics',
    'select_folder': 'Select folder with schematics',
    'import_url': 'Import PDF from URL',
    'import_url_prompt': 'Paste the direct URL of the schematic PDF:',
    'downloading_pdf': 'Downloading PDF...',
    'error': 'Error',
    'open_failed': 'Could not open: {err}',
    # --- sharing / local database ---
    'share': '📤  Share schematics',
    'share_tooltip': ('Export a .sbq package with schematics and metadata.\n'
                      'Only schematics travel: never executables or scripts.'),
    'import_pkg': '📥  Import schematics',
    'import_pkg_tooltip': ('Import a .sbq package from another user.\n'
                           'Files are validated to block viruses.'),
    'share_done': 'Package exported:\n{path}\n\nShare it with other users. It only contains schematics and metadata, no executables.',
    'import_failed': 'Could not import: {err}',
    'import_done': 'Imported {n} schematic(s) into your local store.',
    'import_skipped': 'Skipped {n} file(s) for safety (not schematics).',
    'cleared': 'All clear',
    'reset': '♻️  Reset',
    'reset_tooltip': 'Deletes all local data (devices, schematics and cache) and leaves the program freshly installed.',
    'reset_title': 'Reset the program',
    'reset_confirm': 'ALL local data will be deleted: registered devices, saved schematics and cache.\n\nThis cannot be undone. Continue?',
    'reset_done': 'Data reset. The program is now freshly installed.',
}

# Russian
RU = {
    'app_title': 'SchematicBuq — Умный поиск схем',
    'subtitle': '  Поиск компонентов, понимание функций и отслеживание соединений',
    'add_files': '📁  Добавить файлы',
    'add_folder': '📂  Добавить папку',
    'add_url': '🌐  Импорт PDF (URL)',
    'new_device': '➕  Новое устройство',
    'assign_device': '📦  Сохранить в устройство',
    'help': '❓  Помощь',
    'clear': '🗑️  Очистить',
    'analyze': '⚙️  Анализировать',
    'analyze_tooltip': 'Анализирует схемы и индексирует компоненты.\nПервый раз дольше, далее мгновенно.',
    'active_device': 'Активное устройство:',
    'open_folder': 'Открыть папку',
    'ocr_scan': 'Читать отсканированные схемы (медленнее)',
    'search_placeholder': 'Поиск по обозначению (R46, C12, U5...) или значению (10k, 100uF...)',
    'search': '🔍 Поиск',
    'back': '← Назад',
    'clear_results': 'Очистить результаты',
    'export': '💾 Экспорт индекса',
    'import': '📥 Импорт индекса',
    'system_ready_ocr': 'Система готова — OCR активен ({langs}) — Tesseract: {path}',
    'system_ready_noocr': 'Система готова — OCR недоступен (установите Tesseract для сканов). PDF с текстом работают нормально.',
    'error_unexpected': 'Неожиданная ошибка',
    'files': 'Файлы',
    'results': 'Результаты',
    'viewer': 'Просмотр',
    'tools': 'Инструменты',
    # --- расширенный интерфейс ---
    'back_tooltip': 'Вернуться к предыдущему компоненту (навигация по схеме)',
    'on_select': 'При выборе:',
    'multimeter': 'Мультиметр',
    'interaction': 'Взаимодействие',
    'diagnostic': 'Диагностика',
    'no_change': 'Не менять',
    'auto_tab_tooltip': 'Какая вкладка открывается автоматически при выборе результата',
    'hint': ('💡 Введите компонент и нажмите Поиск · клик по результату — '
             'как его измерить · «🔄 Взаимодействие» показывает связи · '
             'двойной клик — показать на схеме.'),
    'device_files': '📄 Схемы устройства',
    'device_files_tooltip': ('Файлы выбранного устройства.\n'
                             'Клик: показать все компоненты.\n'
                             'Двойной клик: открыть схему в просмотрщике.'),
    'col_designator': 'Обозначение', 'col_value': 'Значение', 'col_type': 'Тип',
    'col_file': 'Файл', 'col_page': 'Стр.', 'col_source': 'Источник',
    'col_device': 'Устройство',
    'tab_viewer': '🧭  Просмотр схемы',
    'tab_component': '🧩  Компонент',
    'tab_interaction': '🔄  Взаимодействие и поведение',
    'tab_multimeter': '🔌  Мультиметр',
    'tab_diagnostic': '🔬  Диагностика и тесты',
    'tab_connections': '🔗  Соединения компонента',
    'tab_nomenclature': '📚  Номенклатура и диагностика',
    'tab_divider': '🧮  Делитель напряжения',
    'tab_help': '🆘  Как пользоваться (справка)',
    'status_ready': 'Готово. Добавьте схему, чтобы начать.',
    'files_in_queue': '{n} файл(ов) в очереди',
    'none': '(Нет)',
    'no_device_selected': 'Устройство: (нет) — очередь пуста. Добавьте файлы или выберите устройство.',
    'device_name_prompt': 'Название устройства или оборудования\n(напр.: БП ATX 500W, телевизор Samsung, усилитель Yamaha):',
    'device_created': 'Устройство создано',
    'device_created_msg': "Устройство '{name}' создано.\n\nПапка схем:\n{folder}\n\nСохранённые схемы будут храниться здесь.",
    'device_registered': "Устройство '{name}' зарегистрировано из папки",
    'no_device': 'Нет устройства',
    'select_device_first': 'Сначала выберите устройство.',
    'create_device_first': 'Сначала создайте или выберите устройство.',
    'saved': 'Сохранено',
    'saved_msg': '{n} файл(ов) сохранено в:\n{folder}\n\nПереиндексируйте, чтобы включить файлы под именем устройства.',
    'select_schematics': 'Выбрать схемы',
    'select_folder': 'Выбрать папку со схемами',
    'import_url': 'Импорт PDF по URL',
    'import_url_prompt': 'Вставьте прямую ссылку на PDF схемы:',
    'downloading_pdf': 'Загрузка PDF...',
    'error': 'Ошибка',
    'open_failed': 'Не удалось открыть: {err}',
    # --- обмен / локальная база данных ---
    'share': '📤  Поделиться схемами',
    'share_tooltip': ('Экспорт пакета .sbq со схемами и метаданными.\n'
                      'Передаются только схемы: никогда исполняемые файлы или скрипты.'),
    'import_pkg': '📥  Импорт схем',
    'import_pkg_tooltip': ('Импорт пакета .sbq от другого пользователя.\n'
                           'Файлы проверяются для блокировки вирусов.'),
    'share_done': 'Пакет экспортирован:\n{path}\n\nПоделитесь им с другими. Он содержит только схемы и метаданные, без исполняемых файлов.',
    'import_failed': 'Не удалось импортировать: {err}',
    'import_done': 'Импортировано {n} схема(ы) в локальное хранилище.',
    'import_skipped': 'Пропущено {n} файл(ов) для безопасности (не схемы).',
    'cleared': 'Всё очищено',
    'reset': '♻️  Сброс',
    'reset_tooltip': 'Удаляет все локальные данные (устройства, схемы и кэш) и возвращает программу в исходное состояние.',
    'reset_title': 'Сброс программы',
    'reset_confirm': 'Будут удалены ВСЕ локальные данные: устройства, сохранённые схемы и кэш.\n\nЭто нельзя отменить. Продолжить?',
    'reset_done': 'Данные сброшены. Программа как после установки.',
}

TRANSLATIONS = {
    'es': ES,
    'es_ES': ES,
    'es_EC': ES,
    'es_MX': ES,
    'en': EN,
    'en_US': EN,
    'en_GB': EN,
    'ru': RU,
    'ru_RU': RU,
}


def detect_language() -> str:
    # Permite forzar el idioma: SCHEMATICBUQ_LANG=es|en|ru
    forced = (os.environ.get('SCHEMATICBUQ_LANG') or '').strip().lower()
    if forced:
        if forced.startswith('es'):
            return 'es'
        if forced.startswith('ru'):
            return 'ru'
        if forced.startswith('en'):
            return 'en'
    try:
        lang, enc = locale.getlocale()
        if lang:
            if lang.startswith('es'):
                return 'es'
            elif lang.startswith('ru'):
                return 'ru'
            elif lang.startswith('en'):
                return 'en'
    except Exception:
        pass
    env = os.environ.get('LANG', '').lower()
    if 'es' in env:
        return 'es'
    if 'ru' in env:
        return 'ru'
    if 'en' in env:
        return 'en'
    return DEFAULT_LANG


def set_language(lang: str = None):
    global CURRENT_LANG
    if lang is None:
        lang = detect_language()
    CURRENT_LANG = lang if lang in TRANSLATIONS else DEFAULT_LANG


def tr(key: str, **kwargs) -> str:
    trans = TRANSLATIONS.get(CURRENT_LANG, ES)
    text = trans.get(key, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text
