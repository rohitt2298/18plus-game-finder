


import streamlit as st
import pandas as pd
from discover import discover_itch_games
from pathlib import Path

st.set_page_config(
    page_title="AFTERDARK | Game Finder",
    page_icon="🌙",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #101014;
    color: #ffffff;
}
h1, h2, h3 {
    color: #eee5ff;
}
div.stButton > button {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🌙 AFTERDARK")
st.caption("18+ GAME DISCOVERY | ANDROID & PC")

st.warning(
    "Adults only (18+). Only lawful games featuring clearly "
    "adult characters may be listed."
)

if "age_confirmed" not in st.session_state:
    st.session_state.age_confirmed = False

if not st.session_state.age_confirmed:
    st.subheader("Age Verification")
    st.write("Please confirm that you are 18 or older.")

    if st.button("I am 18 or older"):
        st.session_state.age_confirmed = True
        st.rerun()

    st.stop()

CATALOGUE = Path("catalogue.csv")

if not CATALOGUE.exists():
    st.error("catalogue.csv not found in your repository.")
    st.stop()

try:
    df = pd.read_csv(CATALOGUE)
except Exception as error:
    st.error(f"Could not load catalogue: {error}")
    st.stop()

required = [
    "title", "platform", "genre", "art_style",
    "description", "rating", "official_url",
    "adult_verified", "listing_status"
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error(f"Missing catalogue columns: {', '.join(missing)}")
    st.stop()

df["adult_verified"] = (
    df["adult_verified"].astype(str).str.lower() == "true"
)

df = df[
    (df["adult_verified"]) &
    (df["listing_status"].astype(str).str.lower() == "approved")
].copy()

df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

search = st.text_input(
    "🔍 Search games",
    placeholder="Enter game title..."
)

platforms = ["All"] + sorted(df["platform"].dropna().unique().tolist())
genres = ["All"] + sorted(df["genre"].dropna().unique().tolist())
styles = ["All"] + sorted(df["art_style"].dropna().unique().tolist())

col1, col2, col3 = st.columns(3)

with col1:
    selected_platform = st.selectbox("Platform", platforms)

with col2:
    selected_genre = st.selectbox("Genre", genres)

with col3:
    selected_style = st.selectbox("Art Style", styles)

results = df.copy()

if search:
    results = results[
        results["title"].astype(str).str.contains(
            search, case=False, na=False
        )
    ]

if selected_platform != "All":
    results = results[results["platform"] == selected_platform]

if selected_genre != "All":
    results = results[results["genre"] == selected_genre]

if selected_style != "All":
    results = results[results["art_style"] == selected_style]

sort_options = {
    "Highest rated": "rating",
    "Most viewed": "views",
    "Most downloaded": "downloads",
    "Trending": "trend_score"
}

sort_choice = st.selectbox("Rank games by", list(sort_options.keys()))

sort_column = sort_options[sort_choice]

if sort_column not in results.columns:
    st.error(f"Missing ranking data: {sort_column}")
    st.stop()

results[sort_column] = pd.to_numeric(
    results[sort_column], errors="coerce"
)

results = results.sort_values(
    sort_column, ascending=False, na_position="last"
)

st.divider()
st.subheader(f"Discover Games ({len(results)} results)")

if results.empty:
    st.info("No approved games yet. Try again after the catalogue is populated.")

for _, game in results.iterrows():
    with st.container(border=True):
        st.subheader(str(game["title"]))

        st.caption(
            f'{game["platform"]} • {game["genre"]} • {game["art_style"]}'
        )

        st.write(game["description"])

        rating = game["rating"]
        st.write(
            f"⭐ Rating: {rating:.1f}/5"
            if pd.notna(rating) else "⭐ Rating: Not available"
        )

        views = game.get("views")
        downloads = game.get("downloads")

        st.write(
            f"👁️ Views: {views if pd.notna(views) else 'N/A'}"
        )
        st.write(
            f"⬇️ Downloads: {downloads if pd.notna(downloads) else 'N/A'}"
        )

        link = str(game["official_url"])

        if link.startswith(("https://", "http://")):
            st.link_button("Visit Game Page", link)

st.divider()
st.caption("AFTERDARK • Game Discovery Platform")
