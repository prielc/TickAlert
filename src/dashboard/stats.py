from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, BlockedUser, Event, Registration, Ticket


async def get_overview_stats(session: AsyncSession) -> dict:
    """Return key metrics for the main dashboard."""
    total_users = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
    active_events = (await session.execute(
        select(func.count()).select_from(Event).where(Event.active == True)
    )).scalar() or 0
    total_registrations = (await session.execute(
        select(func.count()).select_from(Registration)
    )).scalar() or 0
    total_tickets = (await session.execute(
        select(func.count()).select_from(Ticket)
    )).scalar() or 0
    blocked_users = (await session.execute(
        select(func.count()).select_from(BlockedUser)
    )).scalar() or 0

    return {
        "total_users": total_users,
        "active_events": active_events,
        "total_registrations": total_registrations,
        "total_tickets": total_tickets,
        "blocked_users": blocked_users,
    }


async def get_top_events(session: AsyncSession, limit: int = 10) -> list[dict]:
    """Return top events by registration count."""
    result = await session.execute(
        select(
            Event.id, Event.name, Event.date, Event.active,
            func.count(Registration.id).label("reg_count"),
        )
        .outerjoin(Registration, Registration.event_id == Event.id)
        .group_by(Event.id)
        .order_by(func.count(Registration.id).desc())
        .limit(limit)
    )
    return [
        {"id": r.id, "name": r.name, "date": r.date, "active": r.active, "reg_count": r.reg_count}
        for r in result.all()
    ]


async def get_all_users(session: AsyncSession) -> list[dict]:
    """Return all users with their registration counts."""
    result = await session.execute(
        select(
            User.telegram_id, User.username, User.first_name, User.joined_at,
            func.count(Registration.id).label("reg_count"),
        )
        .outerjoin(Registration, Registration.telegram_id == User.telegram_id)
        .group_by(User.telegram_id)
        .order_by(User.joined_at.desc())
    )
    return [
        {
            "telegram_id": r.telegram_id,
            "username": r.username,
            "first_name": r.first_name,
            "joined_at": r.joined_at,
            "reg_count": r.reg_count,
        }
        for r in result.all()
    ]


async def get_user_growth(session: AsyncSession) -> list[dict]:
    """Return daily user signup counts."""
    result = await session.execute(
        select(
            func.date_trunc("day", User.joined_at).label("day"),
            func.count().label("count"),
        )
        .group_by("day")
        .order_by("day")
    )
    return [{"day": str(r.day.date()) if r.day else "N/A", "count": r.count} for r in result.all()]


async def get_all_events(session: AsyncSession) -> list[dict]:
    """Return all events with registration and ticket counts."""
    result = await session.execute(
        select(
            Event.id, Event.name, Event.date, Event.time, Event.location,
            Event.active, Event.created_at,
            func.count(func.distinct(Registration.id)).label("reg_count"),
            func.count(func.distinct(Ticket.id)).label("ticket_count"),
        )
        .outerjoin(Registration, Registration.event_id == Event.id)
        .outerjoin(Ticket, Ticket.event_id == Event.id)
        .group_by(Event.id)
        .order_by(Event.date.desc())
    )
    return [
        {
            "id": r.id, "name": r.name, "date": r.date, "time": r.time,
            "location": r.location, "active": r.active, "created_at": r.created_at,
            "reg_count": r.reg_count, "ticket_count": r.ticket_count,
        }
        for r in result.all()
    ]


async def get_all_tickets(session: AsyncSession) -> list[dict]:
    """Return all tickets with event name and seller info."""
    result = await session.execute(
        select(
            Ticket.id, Ticket.description, Ticket.posted_at,
            Ticket.seller_telegram_id, Ticket.deleted_at,
            Event.name.label("event_name"),
            User.username.label("seller_username"),
            User.first_name.label("seller_first_name"),
        )
        .join(Event, Ticket.event_id == Event.id)
        .join(User, Ticket.seller_telegram_id == User.telegram_id)
        .order_by(Ticket.posted_at.desc())
    )
    return [
        {
            "id": r.id, "description": r.description, "posted_at": r.posted_at,
            "seller_telegram_id": r.seller_telegram_id,
            "deleted_at": r.deleted_at,
            "event_name": r.event_name,
            "seller_username": r.seller_username,
            "seller_first_name": r.seller_first_name,
        }
        for r in result.all()
    ]


async def get_top_sellers(session: AsyncSession, limit: int = 10) -> list[dict]:
    """Return top ticket sellers."""
    result = await session.execute(
        select(
            User.telegram_id, User.username, User.first_name,
            func.count(Ticket.id).label("ticket_count"),
        )
        .join(Ticket, Ticket.seller_telegram_id == User.telegram_id)
        .group_by(User.telegram_id)
        .order_by(func.count(Ticket.id).desc())
        .limit(limit)
    )
    return [
        {
            "telegram_id": r.telegram_id, "username": r.username,
            "first_name": r.first_name, "ticket_count": r.ticket_count,
        }
        for r in result.all()
    ]


async def get_blocked_users(session: AsyncSession) -> list[dict]:
    """Return all blocked users."""
    result = await session.execute(
        select(BlockedUser.telegram_id, BlockedUser.blocked_at, BlockedUser.reason)
        .order_by(BlockedUser.blocked_at.desc())
    )
    return [
        {"telegram_id": r.telegram_id, "blocked_at": r.blocked_at, "reason": r.reason}
        for r in result.all()
    ]
