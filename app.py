
import streamlit as st

st.set_page_config(
    page_title="AFTERDARK | Game Finder",
    page_icon="🎮",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #101014;
    color: white;
}
h1, h2, h3 {
    color: #f2e9ff;
}
</style>
""", unsafe_allow_html=True)

st.title("🌙 AFTERDARK")
st.caption("18+ GAME DISCOVERY • ANDROID & PC")

st.warning("Adults only (18+). This catalogue is for lawful adult games featuring clearly adult characters.")

search = st.text_input("🔍 Search games", placeholder="Search by game title...")

platform = st.selectbox(
    "Platform",
    ["All", "Android", "PC"]
)

st.subheader("Discover Games")

st.info(
    "Your game catalogue will appear here. "
    "Next we'll add verified game listings, artwork and filters."
)
