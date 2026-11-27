
import re
import time
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse, quote_plus

ITCH_FEEDS = [
    ("Newest", "https://itch.io/games/newest.xml"),
    ("Top rated", "https://itch.io/games/top-rated.xml"),
    ("Top sellers", "https://itch.io/games/top-sellers.xml"),
    ("NSFW", "https://itch.io/games/tag-nsfw.xml"),
    ("Visual novels", "https://itch.io/games/tag-visual-novel.xml"),
    ("Dating sims", "https://itch.io/games/tag-dating-sim.xml"),
    ("Simulation", "https://itch.io/games/tag-simulation.xml"),
    ("Adult", "https://itch.io/games/tag-adult.xml"),
]

MAX_PAGES_PER_FEED = 4
REQUEST_TIMEOUT = 18
USER_AGENT = "AFTERDARK-GameDiscovery/1.0"


def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _platforms(item):
    found = []
    node = item.find("platforms")

    if node is not None:
        for child in list(node):
            if (child.text or "").strip().lower() == "yes":
                tag = child.tag.lower()

                if tag == "html":
                    found.append("Browser")
                elif tag == "android":
                    found.append("Android")
                elif tag in ("windows", "linux", "osx"):
                    found.append("PC")

    return " / ".join(sorted(set(found))) if found else "Unknown"


def discover_itch_games(max_pages=None):
    pages = max_pages or MAX_PAGES_PER_FEED
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    games = []
    seen = set()
    errors = []

    for feed_label, feed_url in ITCH_FEEDS:
        for page in range(1, pages + 1):
            try:
                response = session.get(
                    feed_url,
                    params={"page": page},
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()

                root = ET.fromstring(response.content)
                items = root.findall(".//item")

                if not items:
                    break

                for item in items:
                    title = clean(
                        item.findtext("plainTitle") or item.findtext("title")
                    )

                    link = (
                        item.findtext("link")
                        or item.findtext("guid")
                        or ""
                    ).strip()

                    host = (urlparse(link).hostname or "").lower()

                    if not title or not link:
                        continue

                    if not (
                        host == "itch.io"
                        or host.endswith(".itch.io")
                    ):
                        continue

                    if link in seen:
                        continue

                    seen.add(link)

                    cover = (item.findtext("imageurl") or "").strip()

                    if not cover:
                        description = item.findtext("description") or ""
                        match = re.search(
                            r'<img[^>]+src=["\']([^"\']+)',
                            description,
                            re.I
                        )
                        cover = match.group(1) if match else ""

                    price = (item.findtext("price") or "").strip()

                    if price in ("$0.00", "0.00"):
                        price_type = "Free"
                    elif price:
                        price_type = "Paid / other"
                    else:
                        price_type = "Unknown"

                    games.append({
                        "game_id": link,
                        "title": title,
                        "platform": _platforms(item),
                        "source": "itch.io",
                        "feed": feed_label,
                        "genre": "Unknown",
                        "art_style": "Unknown",
                        "price_type": price_type,
                        "rating": None,
                        "rating_count": None,
                        "views": None,
                        "downloads": None,
                        "trend_score": None,
                        "stats_source": "Not publicly available in this feed",
                        "last_verified": "",
                        "description": clean(
                            item.findtext("description")
                        )[:450],
                        "official_url": link,
                        "cover_url": cover,
                        "adult_verified": False,
                        "listing_status": "unverified",
                    })

                if len(items) < 30:
                    break

                time.sleep(0.15)

            except Exception as exc:
                errors.append(f"{feed_label} page {page}: {exc}")

    if not games and errors:
        raise RuntimeError(
            "itch.io feeds could not be read: "
            + " | ".join(errors[:3])
        )

    return games, errors


F95_SEARCH_TERMS = [
    "visual novel",
    "dating sim",
    "simulation",
    "RPG",
    "adventure",
    "uncensored",
    "Android",
    "Linux",
    "completed",
]


def discover_f95_links():
    links = []

    for term in F95_SEARCH_TERMS:
        links.append({
            "title": f"F95Zone: {term}",
            "source": "F95Zone",
            "description": (
                "Open F95Zone search results for this topic. "
                "Listings remain hosted by F95Zone."
            ),
            "official_url": (
                "https://f95zone.to/search/?q=" + quote_plus(term)
            ),
            "cover_url": "",
            "platform": "F95Zone",
            "listing_status": "external link",
        })

    links.append({
        "title": "Browse all F95Zone game discussions",
        "source": "F95Zone",
        "description": "Browse current game forums and threads on F95Zone.",
        "official_url": "https://f95zone.to/",
        "cover_url": "",
        "platform": "F95Zone",
        "listing_status": "external link",
    })

    return links


def discover_games(max_pages=None):
    itch_games, errors = discover_itch_games(max_pages=max_pages)
    f95_links = discover_f95_links()

    return {
        "itch_games": itch_games,
        "f95_links": f95_links,
        "errors": errors,
    }
