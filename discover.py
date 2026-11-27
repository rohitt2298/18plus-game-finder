


import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse
import re

FEEDS = [
    "https://itch.io/feed/new.xml",
    "https://itch.io/games/newest.xml",
    "https://itch.io/games/top-rated.xml",
    "https://itch.io/games/top-sellers.xml",
    "https://itch.io/games/tag-visual-novel.xml",
    "https://itch.io/games/tag-dating-sim.xml",
    "https://itch.io/games/tag-simulation.xml",
    "https://itch.io/games/tag-nsfw.xml",
]

PAGES_PER_FEED = 3

def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def discover_itch_games():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "AFTERDARK-GameFinder/1.0"
    })

    candidates = []
    seen = set()
    errors = []

    for feed in FEEDS:
        for page in range(1, PAGES_PER_FEED + 1):
            try:
                response = session.get(
                    feed,
                    params={"page": page},
                    timeout=20
                )
                response.raise_for_status()

                root = ET.fromstring(response.content)

                for item in root.findall(".//item"):
                    title = clean(
                        item.findtext("plainTitle")
                        or item.findtext("title")
                    )

                    link = (
                        item.findtext("link")
                        or item.findtext("guid")
                        or ""
                    ).strip()

                    host = urlparse(link).hostname or ""

                    if not (
                        host == "itch.io"
                        or host.endswith(".itch.io")
                    ):
                        continue

                    if not title or link in seen:
                        continue

                    seen.add(link)

                    description = clean(
                        item.findtext("description")
                    )

                    image_url = (
                        item.findtext("imageurl") or ""
                    ).strip()

                    price = (
                        item.findtext("price") or ""
                    ).strip()

                    platforms = []
                    platform_node = item.find("platforms")

                    if platform_node is not None:
                        for platform in platform_node:
                            if (platform.text or "").strip().lower() == "yes":
                                name = platform.tag.lower()

                                if name == "html":
                                    platforms.append("Browser")
                                elif name == "android":
                                    platforms.append("Android")
                                elif name in ("windows", "linux", "osx"):
                                    platforms.append("PC")

                    candidates.append({
                        "game_id": link,
                        "title": title,
                        "platform": " / ".join(sorted(set(platforms))) or "Unknown",
                        "source": "itch.io",
                        "genre": "Unknown",
                        "art_style": "Unknown",
                        "price_type": (
                            "Free" if price in ("$0.00", "0.00")
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

            except Exception as error:
                errors.append(f"{feed}, page {page}: {error}")

    if not candidates and errors:
        raise RuntimeError("; ".join(errors[:3]))

    return candidates
