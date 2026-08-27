from datetime import timedelta
from icalendar import Alarm, Calendar, Event as ICSEvent, vCalAddress, vText


def generate_ics(event, attendees, organizer_email: str) -> bytes:
    """
    Generates a standard RFC 5545 iCalendar (.ics) file byte content for an event.
    """
    cal = Calendar()
    cal.add("prodid", "-//Sidanex//Meridian Calendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "REQUEST")

    ie = ICSEvent()
    ie.add("uid", f"event-{event.id}@meridian.sidanex.com")
    ie.add("summary", event.title)
    if event.description:
        ie.add("description", event.description)
    if event.location:
        ie.add("location", event.location)
    if event.meeting_link:
        ie.add("url", event.meeting_link)

    ie.add("dtstart", event.start_at)
    ie.add("dtend", event.end_at)
    ie.add("status", "CONFIRMED")

    # Organizer
    organizer = vCalAddress(f"MAILTO:{organizer_email}")
    organizer.params["cn"] = vText(organizer_email)
    ie.add("organizer", organizer)

    # Attendees
    for att in attendees:
        attendee = vCalAddress(f"MAILTO:{att.email}")
        attendee.params["cn"] = vText(att.email)
        partstat = "ACCEPTED" if att.rsvp_status == "yes" else "DECLINED" if att.rsvp_status == "no" else "TENTATIVE" if att.rsvp_status == "maybe" else "NEEDS-ACTION"
        attendee.params["partstat"] = vText(partstat)
        attendee.params["role"] = vText("REQ-PARTICIPANT")
        ie.add("attendee", attendee, encode=0)

    # Reminder Alarm
    if event.reminder_minutes_before:
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Reminder: {event.title}")
        alarm.add("trigger", timedelta(minutes=-event.reminder_minutes_before))
        ie.add_component(alarm)

    cal.add_component(ie)
    return cal.to_ical()
