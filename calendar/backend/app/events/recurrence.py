from datetime import datetime, timedelta
import re
from typing import List
from app.models import Event


def parse_rrule(rrule_str: str) -> dict:
    """
    Parses simple RRULE strings like 'FREQ=DAILY;UNTIL=20261231' or 'FREQ=WEEKLY;INTERVAL=2'.
    """
    params = {}
    if not rrule_str:
        return params
    for part in rrule_str.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.strip().upper()] = v.strip().upper()
    return params


def expand_event_recurrence(event: Event, from_date: datetime, to_date: datetime) -> List[dict]:
    """
    Expands a recurring event into instances that fall between from_date and to_date.
    """
    if not event.recurrence_rule:
        # One-off event
        if event.end_at >= from_date and event.start_at <= to_date:
            return [{
                "id": str(event.id),
                "calendar_id": str(event.calendar_id),
                "organizer_id": str(event.organizer_id),
                "title": event.title,
                "description": event.description,
                "location": event.location,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "all_day": event.all_day,
                "recurrence_rule": event.recurrence_rule,
                "reminder_minutes_before": event.reminder_minutes_before,
                "meeting_id": str(event.meeting_id) if event.meeting_id else None,
                "meeting_link": event.meeting_link,
                "source": event.source,
                "color": event.color,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "attendees": event.attendees,
                "is_recurring_instance": False,
            }]
        return []

    rrule = parse_rrule(event.recurrence_rule)
    freq = rrule.get("FREQ", "WEEKLY")
    interval = int(rrule.get("INTERVAL", 1))

    until_date = None
    if "UNTIL" in rrule:
        until_str = rrule["UNTIL"]
        try:
            if len(until_str) == 8:
                until_date = datetime.strptime(until_str, "%Y%m%d").replace(tzinfo=event.start_at.tzinfo)
            else:
                until_date = datetime.fromisoformat(until_str.replace("Z", "+00:00"))
        except Exception:
            pass

    duration = event.end_at - event.start_at
    instances = []

    curr_start = event.start_at
    max_count = 365  # Safety bound to prevent infinite loops
    count = 0

    while count < max_count:
        curr_end = curr_start + duration

        if until_date and curr_start > until_date:
            break
        if curr_start > to_date:
            break

        if curr_end >= from_date and curr_start <= to_date:
            instances.append({
                "id": f"{event.id}_{curr_start.strftime('%Y%m%d%H%M%S')}" if count > 0 else str(event.id),
                "calendar_id": str(event.calendar_id),
                "organizer_id": str(event.organizer_id),
                "title": event.title,
                "description": event.description,
                "location": event.location,
                "start_at": curr_start,
                "end_at": curr_end,
                "all_day": event.all_day,
                "recurrence_rule": event.recurrence_rule,
                "reminder_minutes_before": event.reminder_minutes_before,
                "meeting_id": str(event.meeting_id) if event.meeting_id else None,
                "meeting_link": event.meeting_link,
                "source": event.source,
                "color": event.color,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "attendees": event.attendees,
                "is_recurring_instance": count > 0,
                "parent_id": str(event.id),
            })

        # Advance step
        if freq == "DAILY":
            curr_start = curr_start + timedelta(days=interval)
        elif freq == "WEEKLY":
            curr_start = curr_start + timedelta(weeks=interval)
        elif freq == "MONTHLY":
            # Advance ~30 days
            curr_start = curr_start + timedelta(days=30 * interval)
        elif freq == "YEARLY":
            curr_start = curr_start + timedelta(days=365 * interval)
        else:
            break

        count += 1

    return instances
