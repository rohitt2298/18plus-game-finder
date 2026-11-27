
import streamlit as st
import pandas as pd
from pathlib import Path
from urllib.parse import quote_plus
from html import escape
from discover import discover_games

st.set_page_config(
    page_title="AFTERDARK | Game Discovery",
    page_icon="🌙",
    layout="wide"
)

HERO_IMAGE = Path("assets/hero.jpg")
CATALOGUE = Path("catalogue.csv")


# ---------- DESIGN ----------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background: #090710;
    color: #f8efff;
    font-family: Inter, sans-serif;
}

h1, h2, h3 {
    color: #fff;
    font-family: Orbitron, sans-serif;
}

[data-testid="stSidebar"] {
    background: #100b19;
    border-right: 1px solid #54204f;
}

.logo {
    font-family: Orbitron, sans-serif;
    font-size: clamp(36px, 7vw, 64px);
    font-weight: 900;
    letter-spacing: -2px;
}

.logo span {
    color: #ff1493;
    text-shadow: 0 0 20px #ff1493;
}

.hero-box {
    padding: 26px;
    border: 1px solid #a51c80;
    border-radius: 20px;
    background: linear-gradient(125deg, #1d1027, #100a19, #35102d);
    box-shadow: 0 0 25px #8d126633;
    margin-bottom: 20px;
}

.hero-subtitle {
    color: #d9b6d8;
    letter-spacing: 4px;
    font-size: 12px;
}

.game-card {
    background: #171020;
    border: 1px solid #54274f;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 18px;
}

.game-title {
    color: white;
    font-size: 17px;
    font-weight: 700;
    margin: 8px 0;
}

.game-meta {
    color: #c7a8ce;
    font-size: 12px;
}

.neon-line {
    height: 1px;
    background: linear-gradient(90deg, transparent, #ff1493, transparent);
    margin: 25px 0;
}

.stButton > button,
.stLinkButton > a {
    background: linear-gradient(90deg, #d90c86, #8d27d8);
    color: white !important;
    border: 1px solid #ff55bd;
    border-radius: 10px;
    font-weight: 700;
    width: 100%;
}

.stButton > button:hover,
.stLinkButton > a:hover {
    box-shadow: 0 0 18px #ff1493;
    border-color: white;
}

div[data-testid="stImage"] img {
    border-radius: 12px;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ---------- HELPERS ----------

def normalise(data):
    data = data.copy()

    aliases = {
        "style": "art_style",
        "link": "official_url",
        "image_url": "cover_url"
    }

    for old, new in aliases.items():
        if new not in data.columns and old in data.columns:
            data[new] = data[old]

    defaults = {
        "game_id": "",
        "title": "Untitled",
        "platform": "Unknown",
        "source": "Unknown",
        "genre": "Unknown",
        "art_style": "Unknown",
        "rating": None,
        "rating_count": None,
        "views": None,
        "downloads": None,
        "trend_score": None,
        "description": "",
        "official_url": "",
        "cover_url": "",
        "adult_verified": False,
        "listing_status": "pending_review",
        "last_verified": ""
    }

    for column, default in defaults.items():
        if column not in data.columns:
            data[column] = default

    for column in [
        "rating", "rating_count", "views",
        "downloads", "trend_score"
    ]:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    for column in [
        "title", "platform", "source", "genre",
        "art_style", "description", "official_url",
        "cover_url", "listing_status", "last_verified"
    ]:
        data[column] = data[column].fillna(
            defaults[column]
        ).astype(str)

    data["adult_verified"] = (
        data["adult_verified"].astype(str).str.lower()
        .isin(["true", "yes", "1"])
    )

    return data


def load_games():
    frames = []

    if CATALOGUE.exists():
        try:
            frames.append(normalise(pd.read_csv(CATALOGUE)))
        except Exception as error:
            st.error(f"Catalogue loading error: {error}")

    if "discovered_games" in st.session_state:
        frames.append(
            normalise(pd.DataFrame(
                st.session_state["discovered_games"]
            ))
        )

    if not frames:
        return normalise(pd.DataFrame())

    games = pd.concat(frames, ignore_index=True)

    games["_unique"] = games["game_id"].where(
        games["game_id"].astype(str).str.len() > 0,
        games["official_url"]
    )

    games = games.drop_duplicates(
        subset=["_unique"], keep="first"
    ).drop(columns=["_unique"])

    return games


def show_game_cards(data):
    st.caption(f"{len(data)} games found")

    if data.empty:
        st.info(
            "No games found. Use the discovery scanner above "
            "to find new candidates."
        )
        return

    for start in range(0, len(data), 2):
        columns = st.columns(2)

        for offset, column in enumerate(columns):
            index = start + offset

            if index >= len(data):
                break

            game = data.iloc[index]

            with column:
                st.markdown(
                    '<div class="game-card">',
                    unsafe_allow_html=True
                )

                cover = str(game["cover_url"]).strip()

                if cover.startswith(("https://", "http://")):
                    st.image(cover, use_container_width=True)
                else:
                    st.markdown("""
                    <div style="
                        height:180px;
                        background:linear-gradient(135deg,#29132e,#10101a);
                        border-radius:12px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        color:#ff4db8;
                        font-family:Orbitron;
                        font-size:22px;">
                        AFTERDARK
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(
                    f'<div class="game-title">'
                    f'{escape(str(game["title"]))}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="game-meta">'
                    f'{escape(str(game["platform"]))} · '
                    f'{escape(str(game["source"]))}</div>',
                    unsafe_allow_html=True
                )

                st.caption(
                    f'Genre: {game["genre"]} · '
                    f'Art style: {game["art_style"]}'
                )

                if pd.notna(game["rating"]):
                    st.write(f'⭐ {game["rating"]}/5')
                else:
                    st.caption("⭐ Rating unavailable")

                if game["adult_verified"]:
                    st.success("Adult suitability verified")
                else:
                    st.warning(
                        "Unverified candidate · Check content before listing"
                    )

                description = str(game["description"])
                st.write(description[:180])

                official = str(game["official_url"]).strip()

                if official.startswith(("https://", "http://")):
                    st.link_button("View Game ↗", official)

                f95_link = (
                    "https://f95zone.to/search/?q="
                    + quote_plus(str(game["title"]))
                )

                st.link_button("Search on F95Zone ↗", f95_link)

                st.markdown("</div>", unsafe_allow_html=True)


# ---------- AGE VERIFICATION ----------

if "age_confirmed" not in st.session_state:
    st.session_state.age_confirmed = False

if not st.session_state.age_confirmed:
    st.markdown("""
    <div class="hero-box">
        <div class="logo">AFTER<span>DARK</span> 🌙</div>
        <div class="hero-subtitle">ADULT GAME DISCOVERY</div>
        <h2>ENTER THE AFTERDARK</h2>
        <p>Discover indie games, visual novels, simulations and adventures.</p>
        <h3 style="color:#ff4db8">18+ ONLY</h3>
        <p>This platform is intended for adults aged 18 or older.</p>
    </div>
    """, unsafe_allow_html=True)

    if HERO_IMAGE.exists():
        st.image(str(HERO_IMAGE), use_container_width=True)
    else:
        st.warning(
            "Hero image missing. Upload your image as "
            "assets/hero.jpg in GitHub."
        )

    if st.button("🌙 I AM 18+ | ENTER AFTERDARK"):
        st.session_state.age_confirmed = True
        st.rerun()

    st.stop()


# ---------- SIDEBAR ----------

with st.sidebar:
    st.markdown(
        '<div class="logo" style="font-size:27px">'
        'AFTER<span>DARK</span></div>',
        unsafe_allow_html=True
    )

    st.caption("ADULT GAME DISCOVERY")

    page = st.radio(
        "Navigation",
        [
            "Home",
            "All Games",
            "Trending",
            "Highest Rated",
            "Most Viewed",
            "Most Downloaded",
            "Discover"
        ]
    )

    st.divider()
    st.caption("AFTERDARK · 18+")


# ---------- HERO ----------

st.markdown("""
<div class="hero-box">
    <div class="logo">AFTER<span>DARK</span> 🌙</div>
    <div class="hero-subtitle">DISCOVER BEYOND THE ORDINARY</div>
    <p>
        Your destination for adult-oriented indie games,
        visual novels, simulations and adventures.
    </p>
    <h4 style="color:#ff4db8">
        ✦ PC &nbsp; ✦ ANDROID &nbsp; ✦ BROWSER
    </h4>
</div>
""", unsafe_allow_html=True)

if HERO_IMAGE.exists():
    st.image(str(HERO_IMAGE), use_container_width=True)


# ---------- DISCOVERY ----------

with st.expander("🔎 Discover new games · itch.io + Steam"):

    st.write(
        "Scan public discovery feeds and Steam search results. "
        "New entries are candidates, not verified adult-game listings."
    )

    if st.button("🚀 Scan for New Games"):
        with st.spinner("Searching itch.io and Steam..."):
            try:
                found = discover_games()
                st.session_state["discovered_games"] = found
                st.success(f"Found {len(found)} candidates.")
                st.rerun()
            except Exception as error:
                st.error(f"Discovery failed: {error}")

if "discovered_games" in st.session_state:
    found = st.session_state["discovered_games"]

    st.success(f"{len(found)} discovery candidates loaded.")

    if found:
        st.download_button(
            "Download discovery CSV",
            data=pd.DataFrame(found).to_csv(
                index=False
            ).encode("utf-8"),
            file_name="afterdark_discovery.csv",
            mime="text/csv"
        )


# ---------- LOAD GAMES ----------

games = load_games()


# ---------- FILTERS ----------

st.markdown(
    '<div class="neon-line"></div>',
    unsafe_allow_html=True
)

st.subheader("Find your next game")

search = st.text_input(
    "🔍 Search games",
    placeholder="Search title, genre or description..."
)

col1, col2 = st.columns(2)

with col1:
    platforms = ["All"] + sorted(
        games["platform"].unique().tolist()
    )
    selected_platform = st.selectbox("Platform", platforms)

with col2:
    sources = ["All"] + sorted(
        games["source"].unique().tolist()
    )
    selected_source = st.selectbox("Source", sources)

col3, col4 = st.columns(2)

with col3:
    genres = ["All"] + sorted(
        games["genre"].unique().tolist()
    )
    selected_genre = st.selectbox("Genre", genres)

with col4:
    styles = ["All"] + sorted(
        games["art_style"].unique().tolist()
    )
    selected_style = st.selectbox("Art style", styles)

verification = st.selectbox(
    "Verification",
    ["All games", "Verified only", "Unverified only"]
)

sorting = st.selectbox(
    "Rank games by",
    [
        "Latest",
        "Highest Rated",
        "Most Viewed",
        "Most Downloaded",
        "Trending"
    ]
)


# ---------- FILTER RESULTS ----------

results = games.copy()

if search:
    text_to_search = (
        results["title"] + " " +
        results["genre"] + " " +
        results["description"]
    )

    results = results[
        text_to_search.str.contains(
            search, case=False, na=False
        )
    ]

if selected_platform != "All":
    results = results[
        results["platform"].str.contains(
            selected_platform, case=False, na=False
        )
    ]

if selected_source != "All":
    results = results[
        results["source"] == selected_source
    ]

if selected_genre != "All":
    results = results[
        results["genre"] == selected_genre
    ]

if selected_style != "All":
    results = results[
        results["art_style"] == selected_style
    ]

if verification == "Verified only":
    results = results[results["adult_verified"]]

elif verification == "Unverified only":
    results = results[~results["adult_verified"]]


sort_map = {
    "Highest Rated": "rating",
    "Most Viewed": "views",
    "Most Downloaded": "downloads",
    "Trending": "trend_score"
}

if sorting in sort_map:
    results = results.sort_values(
        sort_map[sorting],
        ascending=False,
        na_position="last"
    )

if page == "Trending":
    results = results.sort_values(
        "trend_score", ascending=False, na_position="last"
    )

elif page == "Highest Rated":
    results = results.sort_values(
        "rating", ascending=False, na_position="last"
    )

elif page == "Most Viewed":
    results = results.sort_values(
        "views", ascending=False, na_position="last"
    )

elif page == "Most Downloaded":
    results = results.sort_values(
        "downloads", ascending=False, na_position="last"
    )


# ---------- DISPLAY ----------

if page == "Home":
    st.subheader("🔥 Featured Games")

elif page == "Discover":
    st.subheader("🌐 Discovery Catalogue")

else:
    st.subheader(f"🌙 {page}")

show_game_cards(results)


# ---------- FOOTER ----------

st.markdown(
    '<div class="neon-line"></div>',
    unsafe_allow_html=True
)

st.markdown(
    "<center style='color:#a98ba9'>"
    "AFTERDARK 🌙 · Adult Game Discovery · 18+"
    "</center>",
    unsafe_allow_html=True
)







                
    
                        
