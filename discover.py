



                    
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse
import re

# Browse pages converted to RSS feeds
FEEDS = [
    "https://itch.io/games/newest.xml",
    "https://itch.io/games/top-rated.xml",
    "https://itch.io/games/featured.xml",
    "https://itch.io/games/on-sale.xml",
    "https://itch.io/games/free.xml",
    "https://itch.io/games/tag-visual-novel.xml",
    "https://itch.io/games/tag-dating-sim.xml",
    "https://itch.io/games/tag-simulation.xml",
    "https://itch.io/games/tag-nsfw.xml",
]

PAGES_PER_FEED = 5
TIMEOUT = 15


def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def get_platforms(item):
    platforms = []
    node = item.find("platforms")

    if node is None:
        return "Unknown"

    for platform in node:
        if (platform.text or "").strip().lower() != "yes":
            continue

        name = platform.tag.lower()

        if name == "html":
            platforms.append("Browser")
        elif name == "android":
            platforms.append("Android")
        elif name in ("windows", "linux", "osx"):
            platforms.append("PC")

    return " / ".join(sorted(set(platforms))) or "Unknown"


def discover_itch_games():
    session = requests.Session()

    session.headers.update({
        "User-Agent": "AFTERDARK-GameFinder/1.0"
    })

    candidates = []
    seen = set()
    errors = []
    feed_stats = []

    for feed_url in FEEDS:
        previous_page_links = set()
        feed_count = 0

        for page in range(1, PAGES_PER_FEED + 1):

            try:
                params = {}

                if page > 1:
                    params["page"] = page

                response = session.get(
                    feed_url,
                    params=params,
                    timeout=TIMEOUT
                )

                response.raise_for_status()

                root = ET.fromstring(response.content)
                items = root.findall(".//item")

                if not items:
                    break

                current_page_links = set()

                for item in items:

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

                    if not title or not link:
                        continue

                    current_page_links.add(link)

                # Stop if the feed repeats the previous page
                if (
                    current_page_links
                    and current_page_links == previous_page_links
                ):
                    break

                previous_page_links = current_page_links

                for item in items:

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

                    if not title or not link or link in seen:
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

                    platforms = get_platforms(item)

                    candidates.append({
                        "game_id": link,
                        "title": title,
                        "platform": platforms,
                        "source": "itch.io",
                        "genre": "Unknown",
                        "art_style": "Unknown",
                        "price_type": (
                            "Free"
                            if price in ("$0.00", "0.00")
                            else "Paid / Other"
                            if price
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

                    feed_count += 1

                if len(items) < 30:
                    break

            except Exception as error:
                errors.append(
                    f"{feed_url} page {page}: {error}"
                )
                break

        feed_stats.append({
            "feed": feed_url,
            "unique_games": feed_count
        })

    # Save diagnostic information for Streamlit
    discover_itch_games.last_stats = {
        "total_unique_games": len(candidates),
        "feeds": feed_stats,
        "errors": errors
    }

    return candidates


discover_itch_games.last_stats = {}
