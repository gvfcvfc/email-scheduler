import streamlit as st
import requests

st.set_page_config(page_title="Reset Password", page_icon="🔒")
st.title("Reset Password")

token = st.query_params.get("token")
if not token:
    st.error("Missing reset token.")
    st.stop()

new_password = st.text_input("New Password", type="password")
confirm_password = st.text_input("Confirm New Password", type="password")

if st.button("Reset Password"):
    if new_password != confirm_password:
        st.error("Passwords do not match.")
    elif not new_password:
        st.error("Password cannot be empty.")
    else:
        response = requests.post(
            "http://app:8000/auth/reset-password",
            json={"token": token, "new_password": new_password},
            timeout=15)
        
        if response.ok:
            st.success("Password updated successfully🥳🎉🎉")
        else:
            st.error(response.text)
    
