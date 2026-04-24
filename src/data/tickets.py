ticket_prices = [
    {
        "name": "Under 12 Years Old",
        "price": "$99",
        "tax_total": "$105.16 with all taxes & fees",
        "notes": [],
        "highlight": False,
    },
    {
        "name": "General Admission",
        "price": "$149",
        "tax_total": "$157.11 with all taxes & fees",
        "notes": [],
        "highlight": True,
    },
    {
        "name": "VIP Admission",
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
    {
        "name": "Group Rate",
        "price": "+10 or more\n15% off",
        "tax_total": None,
        "notes": [
            "Valid for groups of 10–200",
            "For friend groups & men's ministries",
        ],
        "highlight": False,
    },
    {
        "name": "VIP Pastor Experience",
<<<<<<< HEAD
        "price": "$112",
=======
        "price": "25% off",
>>>>>>> main
        "tax_total": None,
        "notes": [
            "25% off general ticket — code PASTOR",
            "Exclusive Swag Bag",
            "Freedom Lounge Pass",
            "Meet & Greet with all speakers",
            "Q & A panel with speakers",
            "Signed book by Eric Metaxas",
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
