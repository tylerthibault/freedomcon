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

def test_homepage_og_image_uses_featured_speakers(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    expected = "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/img/guys_rise_of_the_statesmen_2.webp?v=20260602"
    assert f'<meta property="og:image" content="{expected}">' in html
    assert f'<meta name="twitter:image" content="{expected}">' in html


# ---------------------------------------------------------------------------
# 404 handler
# ---------------------------------------------------------------------------

def test_404_handler(client):
    """Requesting a non-existent page should return 404, not 500."""
    response = client.get("/this-page-does-not-exist-xyz")
    assert response.status_code == 404
