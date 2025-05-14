
import streamlit as st

# Disable streamlit elements and set page config
st.set_page_config(initial_sidebar_state="collapsed")
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Return a simple OK response
st.write("OK")
