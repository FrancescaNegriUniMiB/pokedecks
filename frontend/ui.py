import os

import streamlit as st


def render_exit_button(label: str = "Exit") -> None:
    '''Stop the Streamlit server (same effect as Ctrl+C in the terminal).'''
    with st.sidebar:
        st.divider()
        st.caption("Server")
        if st.button(label, type="primary", use_container_width=True):
            os._exit(0)
