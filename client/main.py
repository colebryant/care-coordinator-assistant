import json
import os
import time
from typing import Generator

import requests
import streamlit as st

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def stream_chat_response(
    message: str, thread_id: str = None, reset: bool = False
) -> Generator[str, None, None]:
    """Stream chat response from backend API using Server-Sent Events"""
    payload = {"message": message}
    if thread_id:
        payload["thread_id"] = thread_id
    if reset:
        payload["reset"] = reset

    try:
        with requests.post(
            f"{API_BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            headers={"Accept": "text/plain"},
        ) as response:
            response.raise_for_status()

            # Parse Server-Sent Events
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "content" in data:
                            yield data["content"]
                            time.sleep(0.03)
                        elif "error" in data:
                            yield f"Error: {data['error']}"
                    except json.JSONDecodeError:
                        continue

    except requests.exceptions.RequestException as e:
        yield f"API Error: {e}"


def main():
    st.set_page_config(
        page_title="Care Coordinator Assistant", page_icon="🏥", layout="wide"
    )

    st.title("🏥 Care Coordinator Assistant")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None  # will be set after starting a session
    if "patient_id" not in st.session_state:
        st.session_state.patient_id = None
    if "patient_name" not in st.session_state:
        st.session_state.patient_name = None

    # Sidebar
    with st.sidebar:
        st.header("Session")
        # Start or switch patient session
        if st.session_state.thread_id is None:
            with st.form("start_session_form", clear_on_submit=False):
                pid = st.text_input("Patient ID", value="")
                submitted = st.form_submit_button("Start Session")
                if submitted and pid.strip():
                    try:
                        resp = requests.post(
                            f"{API_BASE_URL}/api/session/start",
                            json={"patient_id": pid.strip()},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            payload = resp.json()
                            st.session_state.thread_id = payload["thread_id"]
                            st.session_state.patient_id = payload["patient_id"]
                            st.session_state.patient_name = payload["patient_name"]
                            st.success("Session started.")
                            st.rerun()
                        elif resp.status_code == 400:
                            st.error("Invalid patient ID or patient not found.")
                        else:
                            st.error(f"Failed to start session: {resp.status_code}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"API error: {e}")
        else:
            st.write(f"Patient: {st.session_state.patient_name}")
            st.write(f"Patient ID: {st.session_state.patient_id}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset Conversation"):
                    st.session_state.messages = []
                    # Reset backend memory but keep thread and patient context as-is
                    list(
                        stream_chat_response(
                            "",
                            thread_id=st.session_state.thread_id,
                            reset=True,
                        )
                    )
                    st.rerun()
            with col2:
                if st.button("🛑 End Session"):
                    # Clear everything
                    st.session_state.messages = []
                    st.session_state.thread_id = None
                    st.session_state.patient_id = None
                    st.session_state.patient_name = None
                    st.rerun()

    # Chat interface
    st.header("💬 Chat")
    if not st.session_state.thread_id:
        st.info("Please start a session by entering a valid patient ID in the sidebar.")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if st.session_state.thread_id and (
        prompt := st.chat_input(
            "Ask about providers, availability, or patient information..."
        )
    ):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response with streaming
        with st.chat_message("assistant"):
            # Use Streamlit's built-in streaming display
            full_response = st.write_stream(
                stream_chat_response(prompt, thread_id=st.session_state.thread_id)
            )

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
    elif not st.session_state.thread_id:
        st.stop()


if __name__ == "__main__":
    main()
