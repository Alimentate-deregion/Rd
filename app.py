import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(page_title="METAREC — República Dominicana",
    page_icon="🇩🇴", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.block-container{padding:0!important}
header{display:none!important}
footer{display:none!important}
#MainMenu{display:none!important}
iframe{border:none!important}
</style>""", unsafe_allow_html=True)

html_path = os.path.join(os.path.dirname(__file__), "visor_metarec_v10.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()
components.html(html, height=1250, scrolling=True)
