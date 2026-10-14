// Топология схемы «Метро связок». Координаты в единицах viewBox (0 0 360 670).
// Станции привязаны к реальным подразделам posts.json (поле level3_subcategory),
// поэтому каждая станция ведёт на настоящие материалы базы.
window.METRO_MAP = {
  viewBox: { w: 360, h: 670 },

  lines: {
    ai:    { short: 'ИИ',      full: 'Нейросети и ИИ',     color: '#06B6D4' },
    mkt:   { short: 'Трафик',  full: 'Маркетинг и трафик', color: '#A855F7' },
    biz:   { short: 'Бизнес',  full: 'Бизнес и управление', color: '#10B981' },
    tools: { short: 'Платежи', full: 'Сервисы и оплаты',   color: '#F59E0B', dashed: true },
    mp:    { short: 'WB/Ozon', full: 'Маркетплейсы WB и Ozon', color: '#F43F5E' }
  },

  // Порядок точек вдоль линии: id станции или угол [x, y].
  routes: {
    ai:    ['ai_utils', 'ai_prompt', 'ai_code', 'x_funnel', 'ai_visual', 'x_avatar', 'ai_auto', 'x_payai', 'x_seller'],
    mkt:   ['mkt_reels', 'mkt_b2b', 'x_funnel', 'mkt_landing', [310, 140], 'mkt_traffic', 'x_avatar'],
    biz:   ['biz_cases', 'x_import', 'biz_fin', 'biz_mgmt', 'x_seller', 'biz_gov'],
    tools: ['tools_sheets', 'x_import', 'tools_contractors', [180, 360], 'x_payai', 'tools_connect', [280, 360], 'x_seller', 'tools_vpn'],
    mp:    ['x_seller', [330, 490], 'mp_niche', 'mp_cards', 'mp_ff']
  },

  // label: сторона подписи (r, l, t, b, tr, tl, br, bl); \n переносит строку.
  stations: {
    ai_prompt:   { name: 'Промпты и LLM', x: 200, y: 40, label: 'r',
                   subs: ['Промпт-инжиниринг & Шаблоны', 'Флагманские LLM (Claude, ChatGPT, Gemini, DeepSeek)', 'Настройка контекста & Проектные файлы (CLAUDE.md)'] },
    ai_code:     { name: 'Код и скиллы', x: 200, y: 90, label: 'r',
                   subs: ['Скиллы, MCP & Коннекторы', 'AI-редакторы & IDE (Cursor, v0, Spec Builder)', 'Терминальные агенты & CLI (Claude Code)'] },
    ai_visual:   { name: 'Визуал и видео', x: 200, y: 195, label: 'l',
                   subs: ['Видео-генерация & Монтаж', 'Генерация изображений & Графика', 'Обработка изображений & Апскейл'] },
    ai_auto:     { name: 'Автоматизация\nи агенты', x: 200, y: 305, label: 'r',
                   subs: ['Сценарии n8n & No-code интеграции', 'Автономные AI-Агенты & Мультиагенты'] },
    ai_utils:    { name: 'AI-утилиты', x: 200, y: -10, label: 'r',
                   subs: ['Универсальные AI-утилиты под задачи', 'No-code генераторы сайтов', 'Ассистенты встреч & Заметки', 'Презентации & Документы'] },

    mkt_reels:   { name: 'Reels\nи охваты', x: 40, y: 140, label: 't',
                   subs: ['Алгоритмы & Охваты в Reels'] },
    mkt_b2b:     { name: 'Лиды B2B', x: 120, y: 140, label: 't',
                   subs: ['Поиск контактов ЛПР & Скрипты'] },
    mkt_landing: { name: 'Лендинги', x: 260, y: 140, label: 't',
                   subs: ['Figma, WebGPU & Продающие лендинги'] },
    mkt_traffic: { name: 'Трафик\nи реклама', x: 255, y: 195, label: 'br',
                   subs: ['Яндекс.Директ, SEO, Авито & GEO'] },

    biz_cases:   { name: 'Кейсы ниш', x: 40, y: 440, label: 'b',
                   subs: ['Кейсы ниш & Проверенные связки'] },
    biz_fin:     { name: 'Финансы', x: 160, y: 440, label: 'b',
                   subs: ['Налоги, 115-ФЗ & Безопасность счетов', 'Управленческий учет (P&L, ДДС & Юнит-экономика)'] },
    biz_mgmt:    { name: 'Команда', x: 220, y: 440, label: 't',
                   subs: ['Делегирование, Регламенты & Отчетность'] },
    biz_gov:     { name: 'Госзакупки', x: 340, y: 440, label: 'b',
                   subs: ['Госзакупки & Электронные тендеры'] },

    tools_sheets:      { name: 'Таблицы\nи Sheets', x: 40, y: 500, label: 'b',
                         subs: ['Автоматизация в Excel & Google Sheets'] },
    tools_contractors: { name: 'Подрядчики', x: 140, y: 400, label: 'r',
                         subs: ['Услуги, Продвижение & Подрядчики'] },
    tools_connect:     { name: 'Связь', x: 240, y: 360, label: 't',
                         subs: ['Сервисы, Связь & VPN'] },
    tools_vpn:         { name: 'VPN и OSINT', x: 280, y: 500, label: 'l',
                         subs: ['VPN, OSINT & Веб-сервисы'] },

    mp_niche: { name: 'Аналитика ниш', x: 330, y: 545, label: 'l',
                subs: ['Аналитика ниш & Топ-позиции (MPStats)'] },
    mp_cards: { name: 'Карточки и СПП', x: 330, y: 600, label: 'l',
                subs: ['Оптимизация карточек & СПП'] },
    mp_ff:    { name: 'Фулфилмент\nи FBS', x: 330, y: 655, label: 'l',
                subs: ['Фулфилмент, Сборка FBS & Маркировка'] },

    x_funnel: { name: 'Автоворонка\nс ИИ', x: 200, y: 140, label: 'bl', interchange: true,
                title: 'Автоворонка с ИИ в Telegram',
                about: 'Как трафик превращается в заявки без менеджера: чат-боты и автоответы в Direct и Telegram на нейросетях.',
                subs: ['Автоворонки в Direct & Чат-боты'] },
    x_avatar: { name: 'ИИ-аватары\nдля Reels', x: 200, y: 250, label: 'r', interchange: true,
                title: 'ИИ-аватары для Reels',
                about: 'Голос и сценарии для роликов без студии: клонирование голоса, озвучка и контент-завод для Reels.',
                subs: ['Синтез речи & Голос', 'Контент-завод & Сценарии'] },
    x_payai:  { name: 'Оплата\nзарубежных ИИ', x: 200, y: 360, label: 'tl', interchange: true,
                title: 'Оплата зарубежных ИИ',
                about: 'Чем платить за зарубежные сервисы: карты, крипто-шлюзы, P2P и приём платежей.',
                subs: ['Платежки, Крипта & Зарубежные карты', 'Финтех, P2P & Прием платежей'] },
    x_seller: { name: 'Селлер\nWB 360°', x: 280, y: 440, label: 'tr', interchange: true,
                title: 'Селлер WB 360°',
                about: 'Товарный бизнес на маркетплейсах: закупка на 1688 и карго, нейросети для карточек и кабинета селлера. Отсюда начинается ветка WB и Ozon.',
                subs: ['AI-автоматизация селлеров', 'Закупки 1688, Фабрики & Карго'] },
    x_import: { name: 'Импорт\nи авто', x: 100, y: 440, label: 'tl', interchange: true,
                title: 'Параллельный импорт и автобизнес',
                about: 'Доставка и подбор коммерческих авто и техники, логистика и карго.',
                subs: ['Логистика, Карго & Авто'] }
  },

  // Готовый пример маршрута с пересадкой: визуал на нейросетях → реклама (через «ИИ-аватары»).
  routePreset: { from: 'ai_visual', to: 'mkt_traffic' }
};
