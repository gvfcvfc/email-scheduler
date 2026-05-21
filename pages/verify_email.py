import streamlit as st
import requests 

st.set_page_config(page_title="Verify Email", page_icon="✅")
st.title("Verify Your Email")

token = st.query_params.get("token")

if not token: 
    st.error("Missing verification token")
    st.stop()

if st.button("Verify Email"):
    response = requests.post(
        "http://app:8000/auth/verify-email",
        json={"token": token},
        timeout=15

    )
    if response.ok:
        st.success("Email verified successfully! 🎉🎉")
        st.info("You can now log in to your account.")

    else:
        try:
            st.error(response.json().get("detail", response.text))
        except Exception:
            st.error(response.text)

            