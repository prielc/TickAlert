import logging
from datetime import date, datetime

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.db.models import User, BlockedUser, Event, Registration, Ticket

logger = logging.getLogger(__name__)


def _parse_event_date(date_str: str) -> date | None:
    """Parse event date string into a date object. Handles YYYY-MM-DD and D.M.YY formats."""
    for fmt in ("%Y-%m-%d", "%d.%m.%y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _is_future_event(event: "Event") -> bool:
    parsed = _parse_event_date(event.date)
    if parsed is None:
        return True  # keep events with unparseable dates visible
    return parsed >= date.today()


# --- Users ---

async def upsert_user(session: AsyncSession, telegram_id: int, username: str | None, first_name: str | None):
    stmt = pg_insert(User).values(
        telegram_id=telegram_id, username=username, first_name=first_name,
    ).on_conflict_do_update(
        index_elements=[User.telegram_id],
        set_={"username": username, "first_name": first_name},
    )
    await session.execute(stmt)
    await session.commit()


async def is_blocked(session: AsyncSession, telegram_id: int) -> bool:
    result = await session.execute(
        select(BlockedUser).where(BlockedUser.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none() is not None


async def block_user(session: AsyncSession, telegram_id: int, reason: str | None = None):
    stmt = pg_insert(BlockedUser).values(
        telegram_id=telegram_id, reason=reason,
    ).on_conflict_do_update(
        index_elements=[BlockedUser.telegram_id],
        set_={"reason": reason},
    )
    await session.execute(stmt)
    await session.commit()


async def unblock_user(session: AsyncSession, telegram_id: int):
    await session.execute(
        sa_delete(BlockedUser).where(BlockedUser.telegram_id == telegram_id)
    )
    await session.commit()


# --- Events ---

async def add_event(session: AsyncSession, name: str, date: str, time: str | None = None, location: str | None = None) -> int:
    event = Event(name=name, date=date, time=time, location=location)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event.id


async def get_active_events(session: AsyncSession) -> list[Event]:
    result = await session.execute(
        select(Event).where(Event.active == True).order_by(Event.date)
    )
    events = list(result.scalars().all())
    return [e for e in events if _is_future_event(e)]


async def get_event(session: AsyncSession, event_id: int) -> Event | None:
    result = await session.execute(
        select(Event).where(Event.id == event_id)
    )
    return result.scalar_one_or_none()


async def remove_event(session: AsyncSession, event_id: int):
    event = await get_event(session, event_id)
    if event:
        event.active = False
        await session.commit()


async def sync_scraped_events(session: AsyncSession, games: list) -> int:
    """Insert scraped games that don't already exist. Returns count of new events."""
    existing = await get_active_events(session)
    existing_keys = {(e.name, e.date) for e in existing}

    added = 0
    for g in games:
        if (g.name, g.date) in existing_keys:
            continue
        event = Event(name=g.name, date=g.date, time=g.time, location=g.location)
        session.add(event)
        added += 1

    if added:
        await session.commit()
    logger.info("Synced events: %d new, %d already existed", added, len(games) - added)
    return added


# --- Registrations ---

async def register_for_event(session: AsyncSession, telegram_id: int, event_id: int) -> bool:
    stmt = pg_insert(Registration).values(
        telegram_id=telegram_id, event_id=event_id,
    ).on_conflict_do_nothing()
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def unregister_from_event(session: AsyncSession, telegram_id: int, event_id: int) -> bool:
    result = await session.execute(
        sa_delete(Registration).where(
            Registration.telegram_id == telegram_id,
            Registration.event_id == event_id,
        )
    )
    await session.commit()
    return result.rowcount > 0


async def get_user_registrations(session: AsyncSession, telegram_id: int) -> list[Event]:
    result = await session.execute(
        select(Event)
        .join(Registration, Registration.event_id == Event.id)
        .where(Registration.telegram_id == telegram_id, Event.active == True)
        .order_by(Event.date)
    )
    events = list(result.scalars().all())
    return [e for e in events if _is_future_event(e)]


async def get_registered_users(session: AsyncSession, event_id: int) -> list[int]:
    result = await session.execute(
        select(Registration.telegram_id).where(Registration.event_id == event_id)
    )
    return list(result.scalars().all())


# --- Tickets ---

async def add_ticket(session: AsyncSession, event_id: int, seller_telegram_id: int, description: str | None = None) -> int:
    ticket = Ticket(event_id=event_id, seller_telegram_id=seller_telegram_id, description=description)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket.id


async def get_ticket(session: AsyncSession, ticket_id: int) -> Ticket | None:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def get_active_tickets(session: AsyncSession, event_id: int) -> list[dict]:
    result = await session.execute(
        select(Ticket, User.username, User.first_name)
        .join(User, Ticket.seller_telegram_id == User.telegram_id)
        .where(Ticket.event_id == event_id, Ticket.deleted_at.is_(None))
        .order_by(Ticket.posted_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": t.id,
            "description": t.description,
            "seller_telegram_id": t.seller_telegram_id,
            "username": username,
            "first_name": first_name,
        }
        for t, username, first_name in rows
    ]


async def get_seller_tickets(session: AsyncSession, seller_telegram_id: int) -> list[dict]:
    """Return all active (non-deleted) tickets for a seller, with event info."""
    result = await session.execute(
        select(Ticket, Event.name.label("event_name"))
        .join(Event, Ticket.event_id == Event.id)
        .where(Ticket.seller_telegram_id == seller_telegram_id, Ticket.deleted_at.is_(None))
        .order_by(Ticket.posted_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": t.id,
            "event_name": event_name,
            "description": t.description,
            "posted_at": t.posted_at,
        }
        for t, event_name in rows
    ]


async def delete_ticket(session: AsyncSession, ticket_id: int):
    ticket = await get_ticket(session, ticket_id)
    if ticket:
        ticket.deleted_at = datetime.utcnow()
        await session.commit()
