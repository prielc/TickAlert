"""Fetch future Beitar Jerusalem games from 365scores API."""

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

API_URL = (
    "https://webws.365scores.com/web/games/current/"
    "?langId=2&timezoneName=Asia/Jerusalem&userCountryId=6"
    "&appTypeId=5&competitors=559"
)

BEITAR_NAME = "בית\"ר ירושלים"
STATUS_NOT_STARTED = 2


@dataclass
class ScrapedGame:
    name: str       # e.g. "ביתר ירושלים נגד מכבי נתניה"
    date: str       # e.g. "2026-02-23"
    time: str       # e.g. "20:30"
    location: str   # e.g. "אצטדיון מרים"


async def fetch_future_beitar_games() -> list[ScrapedGame]:
    """Fetch upcoming Beitar Jerusalem games from 365scores."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(API_URL)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        logger.error("Failed to fetch 365scores data: %s", e)
        return []

    games: list[ScrapedGame] = []

    for game in data.get("games", []):
        if game.get("statusGroup") != STATUS_NOT_STARTED:
            continue

        home = game.get("homeCompetitor", {}).get("name", "")
        away = game.get("awayCompetitor", {}).get("name", "")
        name = f"{home} נגד {away}"

        start_time = game.get("startTime", "")
        try:
            dt = datetime.fromisoformat(start_time)
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")
        except (ValueError, TypeError):
            logger.warning("Bad startTime for game %s: %s", game.get("id"), start_time)
            continue

        venue = game.get("venue", {})
        location = venue.get("name", "") if venue else ""

        games.append(ScrapedGame(
            name=name,
            date=date_str,
            time=time_str,
            location=location,
        ))

    games.sort(key=lambda g: g.date)
    games = games[:5]

    logger.info("Fetched %d upcoming Beitar games from 365scores", len(games))
    return games
