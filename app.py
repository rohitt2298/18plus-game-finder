
import streamlit as st
import pandas as pd
from pathlib import Path
from discover import discover_games

st.set_page_config(
    page_title="AFTERDARK | Game Discovery",
    page_icon="🌙",
    layout="wide"
)

ROOT = Path(__file__).parent
CATALOGUE = ROOT / "catalogue.csv"
HERO = ROOT / "assets" / "hero.jpg"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600;700&display=swap');
.stApp {
    background: #090710;
    color: #f8efff;
    font-family: Inter, sans-serif;
}
[data-testid="stSidebar"] {
    background: #100b19;
    border-right: 1px solid #54204f;
}
h1,h2,h3 {
    font-family: Orbitron, sans-serif;
    color: #fff;
}
.hero {
    padding: 26px;
    border: 1px solid #a51c80;
    border-radius: 20px;
    background: linear-gradient(125deg,#1d1027,#100a19,#35102d);
    box-shadow: 0 0 25px #8d126633;
    margin-bottom: 18px;
}
.logo {
    font-family: Orbitron, sans-serif;
    font-size: clamp(36px,7vw,64px);
    font-weight: 900;
    letter-spacing: -3px;
}
.logo span {
    color: #ff1493;
    text-shadow: 0 0 20px #ff1493;
}
.sub {
    color: #d9b6d8;
    letter-spacing: 4px;
    font-size: 12px;
}
.card {
    background: #171020;
    border: 1px solid #54274f;
    border-radius: 14px;
    padding: 12px;
    margin: 4px 0 18px;
}
.meta {
    color: #c7a8ce;
    font-size: 12px;
}
.tag {
    display: inline-block;
    padding: 4px 8px;
    margin: 3px;
    border: 1px solid #a51c80;
    border-radius: 20px;
    color: #ff83cf;
    font-size: 11px;
}
.stButton>button,.stLinkButton>a {
    background: linear-gradient(90deg,#d90c86,#8d27d8);
    color: white !important;
    border: 1px solid #ff55bd;
    border-radius: 10px;
    font-weight: 700;
    width: 100%;
}
hr {
    border-color: #54204f;
}
footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


def safe_text(value, default="Not available"):
    if value is None or pd.isna(value):
        return default
    value = str(value).strip()
    if value.lower() in ("", "nan", "none"):
        return default
    return value


def as_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes")


# Exclude obvious age-risk terms, but show other listings from the adult-tagged
# discovery feeds as Unverified candidates. This is not age verification.
import re

RISK_TERMS = re.compile(
    r"\b(loli|lolita|shota|underage|under.?age|school.?girl|school.?boy|"
    r"child|children|kid|minor|teen(?:age)?|young girl|young boy)\b",
    re.I
)

def is_displayable_candidate(game):
    text = " ".join(
        safe_text(game.get(k), "")
        for k in ("title", "genre", "description")
    ).lower()
    return not bool(RISK_TERMS.search(text))


def load_catalogue():
    if not CATALOGUE.exists():
        return pd.DataFrame()

    try:
        data = pd.read_csv(CATALOGUE)
    except Exception:
        return pd.DataFrame()

    columns = [
        "title", "platform", "source", "genre", "art_style",
        "rating", "description", "official_url", "cover_url",
        "adult_verified", "listing_status", "views", "downloads",
        "trend_score", "last_verified", "price_type"
    ]

    for col in columns:
        if col not in data.columns:
            data[col] = None

    return data


def cover_card(game):
    title = safe_text(game.get("title"), "Untitled game")
    cover = safe_text(game.get("cover_url"), "")
    if not cover:
        import re
        steam_match = re.search(r"/app/(\d+)", safe_text(game.get("official_url"), ""))
        if steam_match:
            cover = f"https://cdn.akamai.steamstatic.com/steam/apps/{steam_match.group(1)}/header.jpg"
    source = safe_text(game.get("source"), "Unknown source")
    platform = safe_text(game.get("platform"), "Platform unknown")
    genre = safe_text(game.get("genre"), "Genre unknown")
    status = "Approved" if (
        as_bool(game.get("adult_verified"))
        and safe_text(game.get("listing_status")).lower() == "approved"
    ) else "Unverified · candidate"
    description = safe_text(
        game.get("description"), "No description supplied."
    )
    url = safe_text(game.get("official_url"), "")
    rating = game.get("rating")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    if cover.startswith(("https://", "http://")):
        st.image(cover, use_container_width=True)
    else:
        st.markdown("""
        <div class="hero" style="text-align:center">
            <div class="logo">AFTER<span>DARK</span></div>
            <div class="sub">GAME COVER UNAVAILABLE</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"**{title}**")
    st.markdown(
        f"<div class='meta'>{platform} · {source} · {genre}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<span class='tag'>{status}</span>",
        unsafe_allow_html=True
    )
    st.caption(description[:190])

    if rating is not None and not pd.isna(rating):
        st.write(f"⭐ {float(rating):.1f}")
    else:
        st.caption("⭐ Rating not supplied")

    if url.startswith(("https://", "http://")):
        st.link_button("Open game / source ↗", url)

    st.markdown("</div>", unsafe_allow_html=True)


# AGE GATE
if "age_ok" not in st.session_state:
    st.session_state.age_ok = False

if not st.session_state.age_ok:
    st.markdown("""
    <div class="hero">
        <div class="logo">AFTER<span>DARK</span> 🌙</div>
        <div class="sub">ADULT GAME DISCOVERY</div>
        <h2>ENTER THE AFTERDARK</h2>
        <p>
            Discover adult-oriented indie games,
            visual novels, simulations and adventures.
        </p>
        <h3 style="color:#ff4db8">18+ ONLY</h3>
        <p>Adult-game discovery. Unverified listings are clearly labelled and may contain inaccurate metadata.</p>
    </div>
    """, unsafe_allow_html=True)

    if HERO.exists():
        st.image(str(HERO), use_container_width=True)

    st.warning("Adults only. Continue only if you are 18 or older.")

    if st.button("🌙 I AM 18+ | ENTER AFTERDARK"):
        st.session_state.age_ok = True
        st.rerun()

    st.stop()


# SIDEBAR
with st.sidebar:
    st.markdown(
        "<div class='logo' style='font-size:27px'>AFTER<span>DARK</span></div>",
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigate",
        [
            "Home",
            "All Games",
            "Trending",
            "Top Rated",
            "New Releases",
            "F95Zone"
        ]
    )

    st.caption("18+ · External listings are not endorsements")


# MAIN HERO
st.markdown("""
<div class="hero">
    <div class="logo">AFTER<span>DARK</span> 🌙</div>
    <div class="sub">DISCOVER BEYOND THE ORDINARY</div>
    <p>
        One discovery hub for itch.io indie games
        and F95Zone game links.
    </p>
    <b style="color:#ff4db8">
        ✦ PC &nbsp; ✦ ANDROID &nbsp; ✦ BROWSER
    </b>
</div>
""", unsafe_allow_html=True)

if HERO.exists():
    st.image(str(HERO), use_container_width=True)


# DISCOVERY
with st.expander("🔎 Discover / refresh listings"):
    st.write(
        "Fetches adult-tagged feed candidates. Only entries with adult-content signals in their title/description are shown as unverified candidates; obvious age-risk terms are excluded. This is not a guarantee of character ages—review each game's official page before opening."
    )

    pages = st.slider(
        "itch.io pages per feed",
        min_value=1,
        max_value=10,
        value=4
    )

    if st.button("Explore itch.io + F95Zone", type="primary"):
        with st.spinner("Fetching public listings..."):
            try:
                payload = discover_games(max_pages=pages)
                st.session_state["discovery"] = payload

                st.success(
                    f"Fetched {len(payload['itch_games'])} itch.io and "
                    f"{len(payload.get('f95_games', []))} F95Zone candidates. "
                    "Adult-signal candidates will appear below with an Unverified label."
                )
            except Exception as exc:
                st.error(f"Discovery failed: {exc}")


# First visit: load a small batch automatically so Home is not empty.
# Users can fetch more from the discovery panel whenever they want.
if "discovery" not in st.session_state:
    try:
        with st.spinner("Loading adult-game discoveries for your home page..."):
            st.session_state["discovery"] = discover_games(max_pages=2)
    except Exception as exc:
        st.session_state["discovery"] = {
            "itch_games": [], "f95_games": [], "f95_links": [],
            "errors": [f"Automatic discovery failed: {exc}"]
        }

payload = st.session_state.get(
    "discovery",
    {"itch_games": [], "f95_games": [], "f95_links": [], "errors": []}
)

discovered = payload.get("itch_games", [])
f95_games = payload.get("f95_games", [])
f95_links = payload.get("f95_links", [])

catalogue = load_catalogue()

rows = []

if not catalogue.empty:
    rows.extend(catalogue.to_dict("records"))

rows.extend(discovered)
rows.extend(f95_games)


# REMOVE DUPLICATES
unique = {}

for game in rows:
    key = (
        safe_text(game.get("official_url"), "")
        or safe_text(game.get("game_id"), "")
    )

    if key:
        unique[key] = game

games = list(unique.values())


# SEARCH AND FILTERS
st.markdown("---")

search = st.text_input(
    "🔍 Search games",
    placeholder="Search by title, source, genre..."
)

c1, c2, c3 = st.columns(3)

with c1:
    platforms = ["All"] + sorted({
        safe_text(g.get("platform"))
        for g in games
        if safe_text(g.get("platform")) != "Not available"
    })

    platform = st.selectbox("Platform", platforms)

with c2:
    source = st.selectbox(
        "Source",
        ["All", "itch.io", "F95Zone"]
    )

with c3:
    genres = ["All"] + sorted({
        safe_text(g.get("genre"))
        for g in games
        if safe_text(g.get("genre"))
        not in ("Not available", "Unknown")
    })

    genre = st.selectbox("Genre", genres)

art_styles = ["All"] + sorted({
    safe_text(g.get("art_style"))
    for g in games
    if safe_text(g.get("art_style")) not in ("Not available", "Unknown")
})
art_style = st.selectbox("Art style", art_styles)


st.caption("Unapproved feed listings are shown as Unverified. Obvious age-risk terms are filtered, but text checks cannot confirm character ages or inspect artwork.")

sort = st.selectbox(
    "Rank games by",
    [
        "Latest",
        "Highest Rated",
        "Most Viewed",
        "Most Downloaded",
        "Trending"
    ]
)


filtered = []

for game in games:
    searchable = " ".join(
        safe_text(game.get(key), "")
        for key in ("title", "genre", "source", "description")
    ).lower()

    if search and search.lower() not in searchable:
        continue

    if platform != "All" and safe_text(game.get("platform")) != platform:
        continue

    if source != "All" and safe_text(game.get("source")) != source:
        continue

    if genre != "All" and safe_text(game.get("genre")) != genre:
        continue

    if art_style != "All" and safe_text(game.get("art_style")) != art_style:
        continue

    verified = (
        as_bool(game.get("adult_verified"))
        and safe_text(game.get("listing_status")).lower() == "approved"
    )

    # Display adult-signalled candidates with an explicit unverified label.
    if not is_displayable_candidate(game):
        continue

    filtered.append(game)


sort_map = {
    "Highest Rated": "rating",
    "Most Viewed": "views",
    "Most Downloaded": "downloads",
    "Trending": "trend_score"
}

if sort in sort_map:
    field = sort_map[sort]

    def sort_value(game):
        value = pd.to_numeric(
            game.get(field), errors="coerce"
        )
        return value if pd.notna(value) else -1

    filtered.sort(
        key=sort_value,
        reverse=True
    )


# PAGE CONTENT
if page == "F95Zone":
    st.subheader("🔗 F95Zone — latest feed listings")
    st.info(
        "Adult-signalled F95Zone candidates appear as unverified. "
        "Text filters cannot guarantee character ages; check the source page."
    )
    f95_filtered = [g for g in filtered if safe_text(g.get("source")) == "F95Zone"]
    if f95_filtered:
        cols = st.columns(2)
        for i, game in enumerate(f95_filtered[:300]):
            with cols[i % 2]:
                cover_card(game)
    else:
        st.warning("No F95Zone candidates passed the adult-content text filter. Try refreshing later.")
elif page == "New Releases":
    st.subheader("🆕 New / recently discovered games")
    st.caption(
        "The itch.io feed provides recent uploads; "
        "catalogue rows may have older dates."
    )

    recent = [
        g for g in filtered
        if safe_text(g.get("source")) == "itch.io"
    ]

    if recent:
        filtered = recent

elif page == "Trending":
    st.subheader("🔥 Trending")
    st.caption(
        "Only source-provided trend values can be ranked."
    )

elif page == "Top Rated":
    st.subheader("⭐ Top rated")
    st.caption(
        "Games without published ratings are not assigned invented scores."
    )

else:
    st.subheader(
        "🔥 Featured Games" if page == "Home"
        else "🎮 All Games"
    )


st.caption(
    f"{len(filtered)} listings shown · "
    f"{len(discovered) + len(f95_games)} raw feed candidates fetched · only adult-signalled candidates shown"
)


if payload.get("errors"):
    with st.expander("Feed notes"):
        for error in payload["errors"][:12]:
            st.caption(error)


if not filtered:
    st.info(
        "No games are currently available in this session. Use Discover / refresh listings to fetch more. "
        "A listing tag or automated text scan cannot prove every character is an adult."
    )

else:
    columns = st.columns(2)

    for index, game in enumerate(filtered[:300]):
        with columns[index % 2]:
            cover_card(game)

    if len(filtered) > 300:
        st.caption(
            "Showing first 300 matches. Narrow your search to see more."
        )


st.markdown("---")

st.markdown(
    "<center style='color:#a98ba9'>"
    "AFTERDARK 🌙 · Adult game discovery · 18+"
    "</center>",
    unsafe_allow_html=True
)
