
import streamlit as st
import pandas as pd
from pathlib import Path
from discover import discover_itch_games

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="AFTERDARK | Adult Game Discovery",
    page_icon="🌙",
    layout="wide"
)

# ---------------- DESIGN ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background: #090710;
    color: #f8efff;
    font-family: 'Inter', sans-serif;
}

[data-testid="stSidebar"] {
    background: #100b19;
    border-right: 1px solid #452044;
}

h1, h2, h3 {
    color: #ffffff;
    font-family: 'Orbitron', sans-serif;
}

.afterdark-logo {
    font-family: 'Orbitron', sans-serif;
    font-size: clamp(32px, 6vw, 65px);
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -3px;
}

.afterdark-logo span {
    color: #ff1493;
    text-shadow: 0 0 20px #ff1493;
}

.hero {
    padding: 35px 28px;
    border: 1px solid #a51c80;
    border-radius: 20px;
    background: linear-gradient(125deg, #1d1027, #100a19 65%, #35102d);
    box-shadow: 0 0 30px #8d126633;
    margin-bottom: 25px;
}

.hero-subtitle {
    color: #d9b6d8;
    letter-spacing: 5px;
    font-size: 12px;
}

.hero-text {
    color: #e9dbea;
    font-size: 16px;
    line-height: 1.7;
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
    border-color: white;
    box-shadow: 0 0 18px #ff1493;
}

.game-card {
    background: #171020;
    border: 1px solid #54274f;
    border-radius: 13px;
    padding: 12px;
    margin-bottom: 12px;
}

.game-title {
    color: #ffffff;
    font-size: 16px;
    font-weight: 700;
    margin-top: 8px;
}

.game-meta {
    color: #c7a8ce;
    font-size: 12px;
    margin: 5px 0;
}

.neon-line {
    height: 1px;
    background: linear-gradient(90deg, transparent, #ff1493, transparent);
    margin: 25px 0;
}

div[data-testid="stImage"] img {
    border-radius: 10px;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ---------------- AGE VERIFICATION ----------------

if "age_confirmed" not in st.session_state:
    st.session_state.age_confirmed = False

if not st.session_state.age_confirmed:

    st.markdown("""
    <div class="hero">
        <div class="afterdark-logo">
            AFTER<span>DARK</span> 🌙
        </div>
        <div class="hero-subtitle">
            ADULT GAME DISCOVERY
        </div>
        <br>
        <h2>ENTER THE AFTERDARK</h2>
        <p class="hero-text">
            Discover indie visual novels, simulators,
            adventures and more.
        </p>
        <h3 style="color:#ff4db8;">18+ ONLY</h3>
        <p class="hero-text">
            This website contains adult-oriented game listings.
            You must be 18 years or older to continue.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Optional custom hero artwork
    hero_path = Path("assets/hero.png")

    if hero_path.exists():
        st.image(str(hero_path), use_container_width=True)

    st.warning("Adults only. Please confirm your age.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🌙 I AM 18+ | ENTER AFTERDARK"):
            st.session_state.age_confirmed = True
            st.rerun()

    with col2:
        if st.button("EXIT"):
            st.info("You have chosen to exit.")

    st.stop()


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown(
        '<div class="afterdark-logo" style="font-size:25px;">'
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
            "Top Rated",
            "New Releases",
            "Discover Games"
        ]
    )

    st.divider()
    st.caption("AFTERDARK • 18+")


# ---------------- LOAD CATALOGUE ----------------

catalogue_path = Path("catalogue.csv")

if not catalogue_path.exists():
    st.error("catalogue.csv was not found.")
    st.stop()

try:
    df = pd.read_csv(catalogue_path)
except Exception as error:
    st.error(f"Could not load catalogue: {error}")
    st.stop()

required_columns = [
    "title", "platform", "genre", "art_style",
    "rating", "description", "official_url",
    "cover_url", "adult_verified", "listing_status"
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    st.error("Missing catalogue columns: " + ", ".join(missing))
    st.stop()


# Only manually approved listings are public
df["adult_verified"] = (
    df["adult_verified"].astype(str).str.lower() == "true"
)

df["listing_status"] = (
    df["listing_status"].astype(str).str.lower()
)

df = df[
    (df["adult_verified"]) &
    (df["listing_status"] == "approved")
].copy()

for column in ["rating", "views", "downloads", "trend_score"]:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )


# ---------------- HEADER ----------------

st.markdown("""
<div class="hero">
    <div class="afterdark-logo">
        AFTER<span>DARK</span>
    </div>
    <div class="hero-subtitle">
        DISCOVER BEYOND THE ORDINARY
    </div>
    <p class="hero-text">
        Your destination for adult-oriented indie games,
        visual novels, simulations and adventures.
    </p>
    <h4 style="color:#ff4db8;">
        ✦ PC &nbsp;&nbsp; ✦ ANDROID &nbsp;&nbsp; ✦ BROWSER
    </h4>
</div>
""", unsafe_allow_html=True)


# ---------------- DISCOVERY ----------------

with st.expander("🔎 Discover new games from itch.io"):

    st.write(
        "Find recent uploads. All discovered games "
        "remain unverified until manually reviewed."
    )

    if st.button("Explore New Games"):

        with st.spinner("Searching itch.io..."):
            try:
                candidates = discover_itch_games()
                st.session_state["itch_candidates"] = candidates
            except Exception as error:
                st.error(f"Discovery failed: {error}")

    if "itch_candidates" in st.session_state:

        candidates = st.session_state["itch_candidates"]

        st.subheader(
            f"Discovery Candidates ({len(candidates)})"
        )

        if candidates:
            candidate_df = pd.DataFrame(candidates)

            st.dataframe(
                candidate_df[
                    [
                        "title", "platform", "source",
                        "price_type", "official_url"
                    ]
                ],
                use_container_width=True
            )
        else:
            st.info("No candidates returned by the feed.")


# ---------------- SEARCH AND FILTERS ----------------

st.markdown('<div class="neon-line"></div>', unsafe_allow_html=True)

search = st.text_input(
    "🔍 Search games",
    placeholder="Search by game title..."
)

col1, col2, col3 = st.columns(3)

with col1:
    platforms = ["All"] + sorted(
        df["platform"].dropna().astype(str).unique().tolist()
    )
    selected_platform = st.selectbox("Platform", platforms)

with col2:
    genres = ["All"] + sorted(
        df["genre"].dropna().astype(str).unique().tolist()
    )
    selected_genre = st.selectbox("Genre", genres)

with col3:
    sorting = st.selectbox(
        "Sort by",
        [
            "Latest",
            "Highest Rated",
            "Most Viewed",
            "Most Downloaded",
            "Trending"
        ]
    )


# ---------------- FILTER RESULTS ----------------

results = df.copy()

if search:
    results = results[
        results["title"].astype(str).str.contains(
            search, case=False, na=False
        )
    ]

if selected_platform != "All":
    results = results[
        results["platform"] == selected_platform
    ]

if selected_genre != "All":
    results = results[
        results["genre"] == selected_genre
    ]


sort_columns = {
    "Highest Rated": "rating",
    "Most Viewed": "views",
    "Most Downloaded": "downloads",
    "Trending": "trend_score"
}

if sorting in sort_columns:
    column = sort_columns[sorting]

    if column in results.columns:
        results = results.sort_values(
            column,
            ascending=False,
            na_position="last"
        )


# ---------------- PAGE SELECTION ----------------

if page == "Trending":
    if "trend_score" in results.columns:
        results = results.sort_values(
            "trend_score",
            ascending=False,
            na_position="last"
        )

elif page == "Top Rated":
    if "rating" in results.columns:
        results = results.sort_values(
            "rating",
            ascending=False,
            na_position="last"
        )

elif page == "New Releases":
    if "last_verified" in results.columns:
        results = results.sort_values(
            "last_verified",
            ascending=False,
            na_position="last"
        )


# ---------------- GAME CARDS ----------------

def show_games(games):

    if games.empty:
        st.info(
            "No approved games available yet. "
            "The catalogue will display games after review."
        )
        return

    columns = st.columns(3)

    for index, (_, game) in enumerate(games.iterrows()):

        with columns[index % 3]:

            st.markdown('<div class="game-card">', unsafe_allow_html=True)

            cover = str(game.get("cover_url", ""))

            if cover.startswith(("https://", "http://")):
                st.image(cover, use_container_width=True)
            else:
                st.markdown(
                    "<div style='background:#28152d;"
                    "height:160px;border-radius:10px;"
                    "display:flex;align-items:center;"
                    "justify-content:center;color:#ff65c4;'>"
                    "AFTERDARK</div>",
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<div class="game-title">{game["title"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="game-meta">'
                f'{game["platform"]} • {game["genre"]}'
                f'</div>',
                unsafe_allow_html=True
            )

            rating = game.get("rating")

            if pd.notna(rating):
                st.write(f"⭐ {rating:.1f}/5")
            else:
                st.caption("⭐ Rating unavailable")

            st.caption(str(game.get("description", ""))[:140])

            link = str(game.get("official_url", ""))

            if link.startswith(("https://", "http://")):
                st.link_button("View Game ↗", link)

            st.markdown("</div>", unsafe_allow_html=True)


# ---------------- HOME PAGE ----------------

if page == "Home":

    st.subheader("🔥 Featured Games")
    st.caption("Approved listings from the AFTERDARK catalogue.")

    show_games(results.head(12))

elif page == "Discover Games":

    st.subheader("🔎 New Discovery Candidates")

    if "itch_candidates" in st.session_state:
        candidates = st.session_state["itch_candidates"]

        if candidates:
            st.dataframe(
                pd.DataFrame(candidates),
                use_container_width=True
            )
        else:
            st.info("No candidates found.")
    else:
        st.info("Use the discovery panel above to find games.")

else:

    st.subheader(f"🌙 {page}")
    st.caption(f"{len(results)} approved games found.")

    show_games(results)


# ---------------- FOOTER ----------------

st.markdown('<div class="neon-line"></div>', unsafe_allow_html=True)

st.markdown(
    "<center style='color:#a98ba9;'>"
    "AFTERDARK 🌙 • Adult Game Discovery • 18+"
    "</center>",
    unsafe_allow_html=True
)



            
