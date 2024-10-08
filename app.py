import streamlit as st

pg = st.navigation([
    st.Page("home_page.py", title="Home page"),
    st.Page("des_page.py", title="Run Simulation"),
    st.Page("map_page.py", title="Map")
])

pg.run()