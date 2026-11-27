
import re
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse

ITCH_FEED = "https://itch.io/feed/new.xml"

ADULT_KEYWORDS = [
    "18+", "adult", "nsfw", "mature",
    "uncensored", "explicit", "adult-only"
]

def discover_itch_games():
    """Fetch recent itch.io uploads for manual review."""

    try:
        response = requests.get(
            ITCH_FEED,
            timeout=20,
            headers={"User-Agent": "AFTERDARK-GameFinder/1.0"}
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)
        candidates = []

        for item in root.findall(".//item"):
            title = unescape(
                item.findtext("title", default="")
            ).strip()

            link = item.findtext("link", default="").strip()

            description = unescape(
                item.findtext("description", default="")
            )
            description = re.sub(
                r"<[^>]+>", " ", description
            )

            searchable = (title + " " + description).lower()

            if not any(word in searchable for word in ADULT_KEYWORDS):
                continue

            if urlparse(link).hostname != "itch.io":
                continue

            candidates.append({
                "game_id": link,
                "title": title,
                "platform": "PC / Browser",
                "source": "itch.io",
                "genre": "Unknown",
                "art_style": "Unknown",
                "price_type": "Unknown",
                "rating": None,
                "rating_count": None,
                "views": None,
                "downloads": None,
                "trend_score": None,
                "stats_source": "Not available",
                "last_verified": "",
                "description": "Pending manual review",
                "official_url": link,
                "cover_url": "",
                "adult_verified": False,
                "listing_status": "pending_review"
            })

        return candidates

    except Exception as error:
        raise RuntimeError(
            f"itch.io discovery failed: {error}"
        ) from error
