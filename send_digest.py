"""
ReStaff News Bot
Еженедельный дайджест новостей по теме самозанятых, ГПХ и 289-ФЗ.
Отправляет в Telegram-канал красиво отформатированные карточки.
"""

import os
import json
import anthropic
import requests
from datetime import datetime

# ── Конфиг ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]   # напр. @restaff_news или -1001234567890

TOPICS = [
    "самозанятые НПД ФНС изменения 2026",
    "переквалификация самозанятых трудовые отношения суды 2026",
    "289-ФЗ платформенная занятость октябрь 2026",
    "договор ГПХ физическое лицо риски переквалификация 2026",
    "МАРМ ФНС контроль самозанятые 2026",
]

SYSTEM_PROMPT = """Ты — аналитик B2B-продаж компании ReStaff (платформа для легальных выплат самозанятым
и физлицам через гонконгское юрлицо).

Найди 5-7 свежих новостей за последние 2 недели по указанным темам.
Для каждой новости верни строго валидный JSON-массив без markdown-блоков.

Формат каждого элемента:
{
  "title": "заголовок новости (до 100 символов)",
  "summary": "суть в 2-3 предложениях с конкретными цифрами и датами если есть",
  "url": "ссылка на источник или пустая строка",
  "source": "название источника (РБК, Клерк.ру, nalog.ru и т.д.)",
  "date": "дата публикации или период",
  "pitch": "1-2 предложения: как именно использовать эту новость в питче ReStaff клиенту",
  "topic": "одно из: smz | platform | gpx | reclass | law"
}

Верни ТОЛЬКО JSON-массив, без пояснений, без ```json блоков."""

TOPIC_EMOJI = {
    "smz":      "👤",
    "platform": "🏗",
    "gpx":      "📄",
    "reclass":  "⚠️",
    "law":      "⚖️",
}

TOPIC_LABEL = {
    "smz":      "Самозанятые",
    "platform": "289-ФЗ / Платформы",
    "gpx":      "ГПХ / Физлица",
    "reclass":  "Переквалификация",
    "law":      "Изменения в законах",
}


# ── Получение новостей от Claude ──────────────────────────────────────────────
def fetch_news() -> list[dict]:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = (
        "Найди свежие новости (последние 2 недели) по темам:\n"
        + "\n".join(f"- {t}" for t in TOPICS)
        + "\n\nВерни строго JSON-массив."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Собираем текстовые блоки из ответа
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text

    # Чистим возможные markdown-обёртки
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip().rstrip("```").strip()

    news = json.loads(text)
    return news


# ── Форматирование одной карточки в HTML ──────────────────────────────────────
def format_card(item: dict, index: int) -> str:
    emoji = TOPIC_EMOJI.get(item.get("topic", "law"), "📌")
    label = TOPIC_LABEL.get(item.get("topic", "law"), "Новость")
    title = item.get("title", "").strip()
    summary = item.get("summary", "").strip()
    pitch = item.get("pitch", "").strip()
    source = item.get("source", "").strip()
    date = item.get("date", "").strip()
    url = item.get("url", "").strip()

    source_line = f"<i>{source}"
    if date:
        source_line += f" · {date}"
    source_line += "</i>"

    url_line = ""
    if url:
        url_line = f'\n🔗 <a href="{url}">Читать источник</a>'

    card = (
        f"{emoji} <b>[{label}]</b>\n"
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"💼 <b>Питч для клиента:</b>\n"
        f"<i>{pitch}</i>\n\n"
        f"{source_line}"
        f"{url_line}"
    )
    return card


# ── Отправка одного сообщения в Telegram ─────────────────────────────────────
def tg_send(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Telegram error {resp.status_code}: {resp.text}")


# ── Главная функция ───────────────────────────────────────────────────────────
def main():
    today = datetime.now().strftime("%-d %B %Y").replace(
        "January","января").replace("February","февраля").replace(
        "March","марта").replace("April","апреля").replace(
        "May","мая").replace("June","июня").replace(
        "July","июля").replace("August","августа").replace(
        "September","сентября").replace("October","октября").replace(
        "November","ноября").replace("December","декабря")

    print("Запрашиваю новости у Claude...")
    news = fetch_news()
    print(f"Получено {len(news)} новостей")

    # Шапка дайджеста
    header = (
        f"📰 <b>Дайджест ReStaff — {today}</b>\n"
        f"Свежие новости по теме самозанятых, ГПХ и 289-ФЗ для работы с клиентами\n"
        f"{'─' * 30}"
    )
    tg_send(header)

    # Карточки по одной (Telegram лимит 4096 символов на сообщение)
    for i, item in enumerate(news, 1):
        card_text = format_card(item, i)
        print(f"Отправляю карточку {i}/{len(news)}: {item.get('title','')[:50]}")
        tg_send(card_text)

    # Подвал
    footer = (
        "✅ <b>Дайджест готов</b>\n\n"
        "Используй эти новости как повод для первого касания или реанимации отказов.\n"
        "<i>Следующий выпуск — через неделю</i>"
    )
    tg_send(footer)
    print("Готово!")


if __name__ == "__main__":
    main()
