

import re
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse

ITCH_FEEDS = [
    "https://itch.io/feed/new.xml",
    "https://itch.io/games/newest.xml",
    "https://itch.io/games/top-rated.xml",
    "https://itch.io/games/tag-visual-novel.xml",
    "https://itch.io/games/tag-dating-sim.xml",
    "https://itch.io/games/tag-simulation.xml",
    "https://itch.io/games/tag-nsfw.xml",
]

STEAM_SEARCHES = [
    "adult visual novel",
    "dating simulator",
    "mature visual novel",
    "romance visual novel",
    "NSFW game",
    "adult simulation",
    "eroge",
    "uncensored visual novel",
]

PAGES_PER_FEED = 5
TIMEOUT = 20


def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def get_text(item, *names):
    for name in names:
        node = item.find(name)
        if node is not None and node.text:
            return clean(node.text)
    return ""


def get_itch_platform(item):
    platforms = []
    node = item.find("platforms")

    if node is not None:
        for platform in node:
            if (platform.text or "").strip().lower() == "yes":
                name = platform.tag.lower()

                if name == "html":
                    platforms.append("Browser")
                elif name == "android":
                    platforms.append("Android")
                elif name in ("windows", "linux", "osx"):
                    platforms.append("PC")

    return " / ".join(sorted(set(platforms))) or "Unknown"


def discover_itch_games(session):
    results = []
    seen = set()
    errors = []

    for feed in ITCH_FEEDS:
        for page in range(1, PAGES_PER_FEED + 1):
            try:
                response = session.get(
                    feed,
                    params={"page": page},
                    timeout=TIMEOUT
                )
                response.raise_for_status()

                root = ET.fromstring(response.content)

                for item in root.findall(".//item"):
                    title = get_text(
                        item, "plainTitle", "title"
                    )

                    link = get_text(item, "link", "guid")

                    host = urlparse(link).hostname or ""

                    if not (
                        host == "itch.io"
                        or host.endswith(".itch.io")
                    ):
                        continue

                    if not title or link in seen:
                        continue

                    seen.add(link)

                    image = get_text(
                        item, "imageurl", "imageUrl"
                    )

                    description = get_text(
                        item, "description"
                    )

                    price = get_text(item, "price")

                    results.append({
                        "game_id": link,
                        "title": title,
                        "platform": get_itch_platform(item),
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
                        "cover_url": image,
                        "adult_verified": False,
                        "listing_status": "pending_review"
                    })

            except Exception as error:
                errors.append(f"itch.io page error: {error}")

    return results, errors


def discover_steam_games(session):
    results = []
    seen = set()
    errors = []

    for query in STEAM_SEARCHES:
        try:
            response = session.get(
                "https://store.steampowered.com/api/storesearch/",
                params={
                    "term": query,
                    "l": "english",
                    "cc": "us"
                },
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            for item in data.get("items", []):
                app_id = item.get("id")

                if not app_id or app_id in seen:
                    continue

                seen.add(app_id)

                title = clean(item.get("name", ""))
                cover = item.get("tiny_image", "")

                results.append({
                    "game_id": f"steam-{app_id}",
                    "title": title,
                    "platform": "PC",
                    "source": "Steam",
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
                    "description": (
                        "Steam search result. Check the official "
                        "store page and age/content details."
                    ),
                    "official_url": (
                        f"https://store.steampowered.com/app/{app_id}/"
                    ),
                    "cover_url": cover,
                    "adult_verified": False,
                    "listing_status": "pending_review"
                })

        except Exception as error:
            errors.append(f"Steam search '{query}' failed: {error}")

    return results, errors


def discover_games():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "AFTERDARK-GameDiscovery/1.0"
    })

    itch_results, itch_errors = discover_itch_games(session)
    steam_results, steam_errors = discover_steam_games(session)

    combined = itch_results + steam_results

    # Remove duplicate URLs
    unique = []
    seen = set()

    for game in combined:
        key = game.get("game_id") or game.get("official_url")

        if key and key not in seen:
            seen.add(key)
            unique.append(game)

    if not unique and itch_errors and steam_errors:
        raise RuntimeError(
            "Both discovery sources failed. "
            + " | ".join((itch_errors + steam_errors)[:4])
        )

    return unique



                    

                            
