# ReStaff News Bot 📰

Telegram-бот для еженедельного дайджеста новостей по теме самозанятых, ГПХ и 289-ФЗ.
Каждый понедельник в 09:00 МСК бот сам ищет свежие новости через Claude и отправляет
красиво отформатированные карточки в Telegram-канал.

---

## Структура

```
restaff-news-bot/
├── send_digest.py              # Основной скрипт
└── .github/
    └── workflows/
        └── weekly_digest.yml   # Расписание запуска (GitHub Actions)
```

---

## Деплой: пошаговая инструкция

### Шаг 1 — Создать Telegram-бота

1. Открой @BotFather в Telegram
2. Отправь `/newbot`
3. Дай имя (напр. `ReStaff News`) и username (напр. `restaff_news_bot`)
4. Скопируй **токен** — он выглядит как `7123456789:AAF...`

### Шаг 2 — Создать канал и добавить бота

1. Создай закрытый Telegram-канал (напр. `ReStaff Новости`)
2. В настройках канала → Администраторы → добавь своего бота
3. Дай боту право **публиковать сообщения**
4. Узнай ID канала одним из способов:
   - Если канал публичный: ID = `@username_канала`
   - Если приватный: перешли любое сообщение из канала боту @userinfobot
     и возьми `Forwarded from chat #XXXXXXXXXX` — это и есть ID (с минусом: `-100XXXXXXXXXX`)

### Шаг 3 — Создать репозиторий на GitHub

```bash
# Вариант А: через GitHub Desktop или сайт
# Создай новый репозиторий restaff-news-bot (можно приватный)
# Загрузи файлы send_digest.py и .github/workflows/weekly_digest.yml

# Вариант Б: через git в терминале
git init restaff-news-bot
cd restaff-news-bot
# скопируй файлы
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/nutfullin61-sys/restaff-news-bot.git
git push -u origin main
```

### Шаг 4 — Добавить секреты в GitHub

Открой репозиторий → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Добавь три секрета:

| Имя | Значение |
|-----|----------|
| `ANTHROPIC_API_KEY` | Твой ключ Claude API (начинается с `sk-ant-...`) |
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `TELEGRAM_CHANNEL_ID` | ID канала (`@username` или `-100XXXXXXXXXX`) |

### Шаг 5 — Проверить что всё работает

1. Открой репозиторий → вкладка **Actions**
2. Слева найди `ReStaff Weekly News Digest`
3. Нажми **Run workflow** → **Run workflow**
4. Смотри логи — должны появиться карточки в Telegram-канале

---

## Настройки

### Изменить расписание
В файле `.github/workflows/weekly_digest.yml` строка:
```yaml
- cron: "0 6 * * 1"   # Понедельник 06:00 UTC = 09:00 МСК
```
Примеры других расписаний:
- `0 6 * * 5` — пятница в 09:00 МСК
- `0 6 * * 1,4` — понедельник и четверг

### Изменить темы поиска
В файле `send_digest.py` массив `TOPICS`:
```python
TOPICS = [
    "самозанятые НПД ФНС изменения 2026",
    "переквалификация самозанятых...",
    ...
]
```

---

## Стоимость

- **GitHub Actions**: бесплатно (2000 минут/месяц на бесплатном плане, скрипт использует ~3 минуты)
- **Anthropic API**: ~$0.05–0.10 за один запуск (claude-sonnet-4-6 + web search)
- **Telegram Bot API**: бесплатно

Итого: **~$0.20–0.40 в месяц** только за Claude API.
