"""
Smoke tests — verifies every page returns the expected HTTP status
and does not throw an unhandled exception.

Run with:
    pytest tests/ -v
"""

import pytest


# ---------------------------------------------------------------------------
# Pages that must return 200 OK
# ---------------------------------------------------------------------------

PAGES_200 = [
    "/",
    "/faqs",
    "/speakers",
    "/speakers/gen-z",
    "/artists",
    "/past-conferences",
    "/accommodations",
    "/travel",
    "/the-venue",
    "/vendors",
    "/sponsor",
    "/press",
    "/worship",
    "/tickets",
    "/venue-map",
    "/pastors",
    "/vision",
    "/experience",
    "/thankyou",
    "/videos",
    "/story",
    "/robots.txt",
    "/sitemap.xml",
    "/wives",
    "/prayer_guide",
    "/invite",
    "/schedule",
    "/the-play",
    "/camping",
    "/hotels",
    "/food-and-drinks",
    "/churches",
    "/security",
]


@pytest.mark.parametrize("path", PAGES_200)
def test_page_ok(client, path):
    """Every standard page should return 200 with a non-empty body."""
    response = client.get(path)
    assert response.status_code == 200, (
        f"{path} returned {response.status_code}"
    )
    assert len(response.data) > 0, f"{path} returned an empty body"


# ---------------------------------------------------------------------------
# Pages that must redirect (do NOT follow the redirect)
# ---------------------------------------------------------------------------

REDIRECTS = [
    ("/faq",           301, "/faqs"),
    ("/venue-map-svg", 301, "/venue-map"),
    ("/drinks",        301, "/food-and-drinks#drinks"),
]


@pytest.mark.parametrize("path,expected_status,expected_location", REDIRECTS)
def test_redirect(client, path, expected_status, expected_location):
    """Redirect routes should return the correct status and Location header."""
    response = client.get(path, follow_redirects=False)
    assert response.status_code == expected_status, (
        f"{path} returned {response.status_code}, expected {expected_status}"
    )
    location = response.headers.get("Location", "")
    assert expected_location in location, (
        f"{path} Location was '{location}', expected it to contain '{expected_location}'"
    )


# ---------------------------------------------------------------------------
# /press/download — proxy endpoint security checks (no live CDN requests)
# ---------------------------------------------------------------------------

TRUSTED_CDN = "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/"


def test_press_download_forbidden_when_no_url(client):
    """/press/download with no url param should be forbidden."""
    response = client.get("/press/download")
    assert response.status_code == 403


def test_press_download_forbidden_when_untrusted_url(client):
    """/press/download with an untrusted URL should be forbidden."""
    response = client.get("/press/download?url=https://evil.example.com/file.webp&name=test")
    assert response.status_code == 403


def test_press_download_forbidden_when_partial_cdn_prefix(client):
    """/press/download should not allow domain-spoofing the CDN prefix."""
    fake = "https://evil.com/" + TRUSTED_CDN[8:]  # strips https://
    response = client.get(f"/press/download?url={fake}&name=test")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Content-type spot checks
# ---------------------------------------------------------------------------

def test_robots_txt_content_type(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.content_type


def test_sitemap_xml_content_type(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.content_type


# ---------------------------------------------------------------------------
# Share preview metadata
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/", "/venue-map"])
def test_shareable_pages_use_featured_speakers_image(client, path):
    response = client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    expected = "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/img/guys_rise_of_the_statesmen.webp"
    assert f'<meta property="og:image" content="{expected}">' in html
    assert f'<meta name="twitter:image" content="{expected}">' in html


# ---------------------------------------------------------------------------
# Ticket promo / price update checks
# ---------------------------------------------------------------------------

def test_sticky_banner_uses_freedom10_discount_copy(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Save 10% on tickets with code" in html
    assert "FREEDOM10" in html
    assert "Ticket prices go up" not in html
    assert "June 5th" not in html


def test_landing_price_change_popup_removed(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "price-popup-overlay" not in html
    assert "data-promo-modal" not in html
    assert "promo.js" not in html


def test_general_admission_price_updated(client):
    response = client.get("/tickets")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<p class="ticket-card__price">$199</p>' in html
    assert "$209.06 with all taxes &amp; fees" in html
    assert '<p class="ticket-card__price">$179</p>' not in html
    assert "$188.72 with all taxes" not in html


# ---------------------------------------------------------------------------
# Security page
# ---------------------------------------------------------------------------

def test_security_page_contains_revised_safety_copy_and_gorge_link(client):
    response = client.get("/security")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Security and Safety at Freedom Conference" in html
    assert "A comprehensive plan for a layered security and safety approach has been developed through extensive coordination between venue staff, event organizers, private security, medical teams, and local law enforcement agencies." in html
    assert "While specific tactical procedures remain confidential for operational integrity" in html
    assert "This disciplined preparation ensures the protection of all attendees, speakers, and staff while preserving the mission of the conference." in html
    assert "Guests can generally expect the following security and safety measures:" in html
    assert "Comprehensive security screening at all primary guest ingress points, including physical bag inspections, walk-through metal detection, and secondary screening as required." in html
    assert "Strict enforcement of bag policies and prohibited item lists; attendees are encouraged to review the" in html
    assert 'href="https://www.gorgeamphitheatre.com/safety-and-rules"' in html
    assert "GORGE SAFETY page" in html
    assert "Deployment of specialized K9 units trained for the detection of firearms and explosives." in html
    assert "Advanced surveillance capabilities, including CCTV monitoring and drone-based operational monitoring of campgrounds, parking lots, and venue perimeters." in html
    assert "Dedicated medical support, including ambulances, EMTs, and paramedics to address health emergencies throughout the event." in html
    assert "All attendees are encouraged to report any safety concerns to venue staff or security personnel immediately." in html


def test_security_expectation_copy_wraps_link_inline(client):
    response = client.get("/security")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<li><span class="security-expectations__text">Strict enforcement of bag policies and prohibited item lists; attendees are encouraged to review the <a href="https://www.gorgeamphitheatre.com/safety-and-rules" target="_blank" rel="noopener noreferrer">GORGE SAFETY page</a> for specific details.</span></li>' in html


def test_more_dropdown_links_to_security_page(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'href="/security"' in html
    assert ">Security</a>" in html


# ---------------------------------------------------------------------------
# 404 handler
# ---------------------------------------------------------------------------

def test_404_handler(client):
    """Requesting a non-existent page should return 404, not 500."""
    response = client.get("/this-page-does-not-exist-xyz")
    assert response.status_code == 404
