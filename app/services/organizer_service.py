from app.core.config import settings


def is_organizer(telegram_id: int) -> bool:
    return telegram_id in settings.organizer_telegram_ids