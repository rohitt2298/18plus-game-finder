

import streamlit as st
import pandas as pd

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
    "Adults only (18+). Listings are restricted to "
    "lawful adult games featuring clearly adult characters."
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

try:
    df = pd.read_csv("games.csv")
except Exception:
    st.error("Could not load games.csv. Check your repository.")
    st.stop()

search = st.text_input("🔍 Search games", placeholder="Enter game title...")

platforms = ["All"] + sorted(df["platform"].dropna().unique().tolist())
genres = ["All"] + sorted(df["genre"].dropna().unique().tolist())
styles = ["All"] + sorted(df["style"].dropna().unique().tolist())

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
        results["title"].str.contains(search, case=False, na=False)
    ]

if selected_platform != "All":
    results = results[results["platform"] == selected_platform]

if selected_genre != "All":
    results = results[results["genre"] == selected_genre]

if selected_style != "All":
    results = results[results["style"] == selected_style]

results["rating"] = pd.to_numeric(results["rating"], errors="coerce")
results = results.sort_values("rating", ascending=False)

st.divider()
st.subheader(f"Discover Games ({len(results)} results)")

if results.empty:
    st.info("No matching games found. Try different filters.")

for _, game in results.iterrows():
    with st.container(border=True):
        st.subheader(str(game["title"]))
        st.caption(
            f'{game["platform"]} • {game["genre"]} • {game["style"]}'
        )
        st.write(game["description"])
        st.write(f'⭐ Rating: {game["rating"]:.1f}/5')

        link = str(game["link"])
        if link.startswith("https://") or link.startswith("http://"):
            st.link_button("Visit Game Page", link)

st.divider()
st.caption("AFTERDARK • Game Discovery Platform")
