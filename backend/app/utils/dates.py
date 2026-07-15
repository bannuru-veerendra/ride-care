from datetime import date, datetime, timedelta, timezone

# Asia/Kolkata (IST) — fixed offset, no DST
APP_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def app_today() -> date:
    """Return today's date in Asia/Kolkata"""
    return datetime.now(APP_TIMEZONE).date()
