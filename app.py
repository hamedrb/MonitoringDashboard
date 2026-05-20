import streamlit as st

from src.main import load_app


# ============================================================================================
# Page style

st.set_page_config(
    page_title="Monitoring Dashboard",
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-bottom: 4rem;
}

.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    text-align: center;
    color: gray;
    padding: 8px;
    font-size: 0.85rem;
    background-color: white;
    z-index: 100;
}
</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown(
    """
    <div class="footer">
        Developed by <b>Hamed</b> @ B&amp;A Biomedical
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================================================

load_app()
