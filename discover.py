

import re
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse

ITCH_FEED = "https://itch.io/feed/new.xml"


def clean_text(value):
    if not value:
        return ""

    value = unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def discover_itch_games():
    """Fetch recent itch.io games for manual review."""

    try:
        response = requests.get(
            ITCH_FEED,
            timeout=25,
            headers={
                "User-Agent": "AFTERDARK-GameFinder/1.0"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(response.content)

        candidates = []
        seen = set()

        for item in root.findall(".//item"):

            title = clean_text(
                item.findtext("plainTitle")
                or item.findtext("title")
                or ""
            )

            link = (
                item.findtext("link")
                or item.findtext("guid")
                or ""
            ).strip()

            description = clean_text(
                item.findtext("description", default="")
            )

            image_url = (
                item.findtext("imageurl") or ""
            ).strip()

            price = (
                item.findtext("price") or ""
            ).strip()

            hostname = urlparse(link).hostname or ""

            if not (
                hostname == "itch.io"
                or hostname.endswith(".itch.io")
            ):
                continue

            if not title or not link or link in seen:
                continue

            seen.add(link)

            platform_tags = item.find("platforms")
            detected_platforms = []

            if platform_tags is not None:
                for platform in platform_tags:
                    if (platform.text or "").strip().lower() == "yes":
                        name = platform.tag.lower()

                        if name == "html":
                            detected_platforms.append("Browser")
                        elif name == "android":
                            detected_platforms.append("Android")
                        elif name in ["windows", "linux", "osx"]:
                            detected_platforms.append("PC")

            platform = (
                " / ".join(sorted(set(detected_platforms)))
                if detected_platforms
                else "Unknown"
            )

            candidates.append({
                "game_id": link,
                "title": title,
                "platform": platform,
                "source": "itch.io",
                "genre": "Unknown",
                "art_style": "Unknown",
                "price_type": (
                    "Free" if price == "0.00"
                    else "Paid / Other" if price
                    else "Unknown"
                ),
                "rating": None,
                "rating_count": None,
                "views": None,
                "downloads": None,
                "trend_score": None,
                "stats_source": "Not available",
                "last_verified": "",
                "description": description[:500],
                "official_url": link,
                "cover_url": image_url,
                "adult_verified": False,
                "listing_status": "pending_review"
            })

        return candidates

    except Exception as error:
        raise RuntimeError(
            f"itch.io discovery failed: {error}"
        ) from error
