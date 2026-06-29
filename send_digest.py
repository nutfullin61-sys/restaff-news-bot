"""
ReStaff News Bot — Gemini Edition
Еженедельный дайджест новостей по теме самозанятых, ГПХ и 289-ФЗ.
Использует Google Gemini API (бесплатный tier).
"""

import os
import json
import re
import requests
import google.genai as genai
from google.genai import types
from datetime import datetime

# ── Конфиг ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

TOPICS = [
    "самозанятые НПД ФНС изменения 2026",
    "переквалификация самозанятых трудовые отношения суды 2026",
    "289-ФЗ платформенная занятость октябрь 2026",
    "договор ГПХ физическое лицо риски переквалификация 2026",
    "МАРМ ФНС контроль самозанятые 2026",
]

SYSTEM_PROMPT = """Ты — аналитик B2B-продаж компании ReStaff (платформа для легальных выплат
самозанятым и физлицам через гонконгское юрлицо ReStaff Ltd).

Найди 5-7 свежих новостей за последние 2 недели по указанным темам.
Используй поиск в интернете для поиска актуальных материалов.

Верни СТРОГО валидный JSON-массив. Никаких пояснений до или после. Никаких ```json блоков.

Формат каждого элемента:
[
  {
    "title": "заголовок новости (до 100 символов)",
    "summary": "суть в 2-3 предложениях с конкретными цифрами и датами",
    "url": "прямая ссылка на источник или пустая строка",
    "source": "название источника (РБК, Клерк.ру, nalog.ru и т.д.)",
    "date": "дата публикации",
    "pitch": "1-2 предложения: как использовать эту новость в питче ReStaff клиенту. Конкретно.",
    "topic": "одно из: smz | platform | gpx | reclass | law"
  }
]"""

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


# ── Получение новостей от Gemini ──────────────────────────────────────────────
def fetch_news() -> list[dict]:
    client = genai.Client(api_key=GEMINI_API_KEY)

    user_message = (
        "Найди свежие новости (последние 2 недели) по темам:\n"
        + "\n".join(f"- {t}" for t in TOPICS)
        + "\n\nВерни ТОЛЬКО JSON-массив, без пояснений и без ```json блоков."
    )

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.3,
        ),
    )

    text = response.text.strip()

    # Чистим возможные markdown-обёртки
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Извлекаем JSON-массив если вдруг есть лишний текст
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)

    news = json.loads(text)
    return news


# ── Форматирование карточки в HTML для Telegram ───────────────────────────────
def format_card(item: dict) -> str:
    emoji  = TOPIC_EMOJI.get(item.get("topic", "law"), "📌")
    label  = TOPIC_LABEL.get(item.get("topic", "law"), "Новость")
    title   = item.get("title", "").strip()
    summary = item.get("summary", "").strip()
    pitch   = item.get("pitch", "").strip()
    source  = item.get("source", "").strip()
    date    = item.get("date", "").strip()
    url     = item.get("url", "").strip()

    source_line = f"<i>{source}"
    if date:
        source_line += f" · {date}"
    source_line += "</i>"

    url_line = f'\n🔗 <a href="{url}">Читать источник</a>' if url else ""

    return (
        f"{emoji} <b>[{label}]</b>\n"
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"💼 <b>Питч для клиента:</b>\n"
        f"<i>{pitch}</i>\n\n"
        f"{source_line}{url_line}"
    )


# ── Отправка сообщения в Telegram ─────────────────────────────────────────────
def tg_send(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Telegram error {resp.status_code}: {resp.text}")


# ── Главная функция ───────────────────────────────────────────────────────────
def main():
    months = ["января","февраля","марта","апреля","мая","июня",
              "июля","августа","сентября","октября","ноября","декабря"]
    now = datetime.now()
    today = f"{now.day} {months[now.month - 1]} {now.year}"

    print("Запрашиваю новости у Gemini...")
    news = fetch_news()
    print(f"Получено новостей: {len(news)}")

    # Шапка
    tg_send(
        f"📰 <b>Дайджест ReStaff — {today}</b>\n"
        f"Свежие новости по теме самозанятых, ГПХ и 289-ФЗ\n"
        f"{'─' * 28}"
    )

    # Карточки
    for i, item in enumerate(news, 1):
        card = format_card(item)
        print(f"Отправляю {i}/{len(news)}: {item.get('title','')[:60]}")
        tg_send(card)

    # Подвал
    tg_send(
        "✅ <b>Дайджест готов</b>\n\n"
        "Используй новости как повод для первого касания или реанимации отказов.\n"
        "<i>Следующий выпуск — через неделю</i>"
    )
    print("Готово!")


if __name__ == "__main__":
    main()
