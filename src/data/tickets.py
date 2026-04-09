from datetime import date


EARLY_BIRD_END = date(2026, 4, 15)
EVENT_START = date(2026, 6, 19)
EVENT_END = date(2026, 6, 20)


ticket_prices = [
    {
        "name": "General Admission",
        "price": "$149",
        "notes": [],
        "highlight": False,
    },
    {
        "name": "VIP Admission",
        "price": "$349",
        "notes": [
            "VIP badge",
            "Reserved box seating",
            "In-suite food service",
            "Space limited",
        ],
        "highlight": True,
    },
    {
        "name": "Under 12 Years Old",
        "price": "$99",
        "notes": [],
        "highlight": False,
    },
    {
        "name": "Group Rate",
        "price": "+10 or more\n15% off",
        "notes": [],
        "highlight": False,
    },
]

ticket_meta = {
    "event_title": "Freedom Con",
    "subtitle": "Rise Of The Statesman",
    "kicker": "An American Congress of Christian Men",
    "dates": "June 19-20",
    "notice": "General Admission early pricing ends April 15",
    "cta_label": "Get Your Ticket",
    "cta_href": "#",
}


def build_urgency(today: date | None = None) -> dict[str, str | bool]:
    current_day = today or date.today()

    if current_day <= EARLY_BIRD_END:
        return {
            "phase": "early_bird",
            "countdown_target": "2026-04-16T00:00:00-07:00",
            "countdown_label": "Early Price Ends In",
            "headline": "Early pricing closes April 15",
            "body": "Lock in your rate before pricing updates.",
            "tickets_notice": "General Admission early pricing ends April 15.",
            "nav_line": "Early bird pricing through April 15.",
            "show_countdown": True,
        }

    if current_day < EVENT_START:
        return {
            "phase": "event_ramp",
            "countdown_target": "2026-06-19T17:00:00-07:00",
            "countdown_label": "Kickoff Starts In",
            "headline": "Freedom Con starts June 19",
            "body": "Secure current online pricing before event weekend.",
            "tickets_notice": "Current online pricing is live now. Reserve your ticket before June 19.",
            "nav_line": "June 19–20 at The Gorge",
            "show_countdown": True,
        }

    if current_day <= EVENT_END:
        return {
            "phase": "event_live",
            "countdown_target": "2026-06-19T17:00:00-07:00",
            "countdown_label": "Freedom Con Is Live",
            "headline": "Freedom Con is happening now",
            "body": "Join us this weekend at The Gorge.",
            "tickets_notice": "Event weekend is live now. Register while spots remain.",
            "nav_line": "Now live at The Gorge",
            "show_countdown": False,
        }

    return {
        "phase": "post_event",
        "countdown_target": "2026-06-19T17:00:00-07:00",
        "countdown_label": "Freedom Con 2026 Complete",
        "headline": "Freedom Con 2026 is complete",
        "body": "Thanks for standing with us. Watch for upcoming announcements.",
        "tickets_notice": "Freedom Con 2026 has concluded.",
        "nav_line": "See you next year",
        "show_countdown": False,
    }


def get_ticket_context(today: date | None = None) -> dict[str, dict | list]:
    urgency = build_urgency(today=today)
    resolved_meta = {**ticket_meta, "notice": urgency["tickets_notice"]}
    return {
        "ticket_meta": resolved_meta,
        "ticket_prices": ticket_prices,
        "urgency": urgency,
    }
