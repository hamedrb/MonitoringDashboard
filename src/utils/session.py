
import streamlit as st


def invalidate_results():
    # Hide generated results and report
    st.session_state["results_generated"] = False
    st.session_state["report_generated"] = False


def invalidate_report():
    # Hide generated report
    st.session_state["report_generated"] = False