import streamlit as st
from sdk.client import AIAnalystClient

class StateManager:
    @staticmethod
    def initialize():
        if "analyst_client" not in st.session_state:
            api_key = None
            try:
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass
            st.session_state.analyst_client = AIAnalystClient(api_key=api_key)
            
        if "analyst_session" not in st.session_state:
            st.session_state.analyst_session = None

        if "data_source" not in st.session_state:
            st.session_state.data_source = None

    @staticmethod
    def save_dataframe(df, file_name, source):
        st.session_state.analyst_session = st.session_state.analyst_client.create_session(df, file_name=file_name)
        st.session_state.data_source = source

    @staticmethod
    def get_dataframe():
        if st.session_state.get("analyst_session"):
            return st.session_state.analyst_session.df
        return None

    @staticmethod
    def get_file_name():
        if st.session_state.get("analyst_session"):
            return st.session_state.analyst_session.file_name
        return None

    @staticmethod
    def get_conversation():
        if st.session_state.get("analyst_session"):
            return st.session_state.analyst_session.get_conversation()
        return []

    @staticmethod
    def update_conversation(conversation):
        if st.session_state.get("analyst_session"):
            st.session_state.analyst_session.set_conversation(conversation)