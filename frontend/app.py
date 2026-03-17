import os
import uuid

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def main():
    st.set_page_config(page_title="Adaptive RAG Chatbot", page_icon="🤖", layout="wide")
    st.title("Adaptive RAG Chatbot")

    session_id = get_session_id()

    with st.sidebar:
        st.header("Session")
        st.write(f"Session ID: `{session_id}`")

        st.header("Upload documents")
        uploaded_file = st.file_uploader(
            "Upload a PDF or text file",
            type=["pdf", "txt"],
        )
        if uploaded_file is not None:
            with st.spinner("Uploading and ingesting document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"session_id": session_id}
                try:
                    resp = requests.post(f"{BACKEND_URL}/upload", files=files, data=data, timeout=60)
                    resp.raise_for_status()
                    payload = resp.json()
                    st.success(
                        f"Ingested {payload.get('num_chunks', 0)} chunks using {payload.get('backend', 'unknown')}."
                    )
                except Exception as exc:
                    st.error(f"Failed to upload document: {exc}")

        st.markdown("---")
        if st.button("Reset conversation"):
            st.session_state.get("messages", [])
            st.session_state.messages = []
            st.experimental_rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Prepare recent messages to send as lightweight history
                    recent_messages = st.session_state.messages[-10:]
                    resp = requests.post(
                        f"{BACKEND_URL}/chat",
                        json={
                            "session_id": session_id,
                            "message": prompt,
                            "history_limit": 50,
                            "messages": recent_messages,
                        },
                        timeout=120,
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                    answer = payload.get("answer", "")
                    route = payload.get("route", "general")
                    st.markdown(answer)
                    st.caption(f"Route: **{route}**")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as exc:
                    st.error(f"Request failed: {exc}")


if __name__ == "__main__":
    main()

