ticket_prices = [
    {
        "name": "General Admission",
        "price": "$149",
        "tax_total": "$157.11 with all taxes & fees",
        "notes": [],
        "highlight": True,
    },
    {
        "name": "Youth (Under 12)",
        "price": "$99",
        "tax_total": "$105.16 with all taxes & fees",
        "notes": [],
        "highlight": False,
    },
    {
        "name": "VIP Seats",
        "price": "$349",
        "tax_total": "$364.91 with all taxes & fees",
        "notes": [
            "VIP badge",
            "Reserved box seating",
            "In-suite food service",
            "Space limited",
        ],
        "highlight": False,
    },
    {        "name": "Group Rate",
        "price": "+10 or more\n15% off",
        "tax_total": None,
        "notes": [
            "Save 15% off general admission",
            "Valid for groups of 10\u2013200 people",
            "For friend groups & men\u2019s ministries",
            "Use the group promo code at checkout to redeem",
            "Reach out to us for your group code if you haven\u2019t received it",
        ],
        "highlight": False,
    },
    {        "name": "Pastor VIP",
        "price": "25% off",
        "tax_total": None,
        "notes": [
            "25% off general admission",
            "Pastor Swag Bag",
            "Private Freedom Con Lounge Pass",
            "Exclusive meet & greet with speakers",
            "Off-record Q/A with speaker panel",
            "Signed book by Eric Metaxas",
            "Enter code PASTOR at checkout",
        ],
        "highlight": False,
    },
]

ticket_meta = {
    "event_title": "Freedom Con",
    "subtitle": "Rise Of The Statesman",
    "kicker": "An American Congress of Christian Men",
    "dates": "June 19-20",
    "notice": "General Admission early pricing ends May 1!!",
    "cta_label": "Get Your Ticket",
    "cta_href": "#",
}


def get_ticket_context() -> dict[str, dict | list]:
    return {
        "ticket_meta": ticket_meta,
        "ticket_prices": ticket_prices,
    }
